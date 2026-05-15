# Spread order vs the cleanup pass

When a function merges a polymorphic diff payload onto a canonical
record with `{ name, ...diff }`, the spread order is the contract,
not the cleanup pass that runs three call frames downstream.
If the diff can shadow `name`, the cleanup pass is only a safety
net in the common case where nothing else changed; add one
adjacent field that differs and the bad shape escapes cleanup,
reaches a schema validator, and fails with an error that looks
like nothing in the diff merge.

## When to reach for it

A bug report where a downstream schema validator (Zod, Pydantic,
JSON Schema) rejects a record with "expected string, received
object" or "expected X, received `{ __old: …, __new: … }`", and
the reporter has correctly traced back to a normalization step
that wrote `{ name, schema, ...diff }` and expected `name` and
`schema` to be strings. The diff-merge primitive looks correct;
the validator looks correct; the cleanup pass between them looks
correct. The bug is in the order of `{ explicit, ...spread }` vs
`{ ...spread, explicit }`, and the cleanup pass was masking it
for every input that wasn't this particular shape.

## The shape

Three things are true at the same time.

1. **The diff library is polymorphic at the leaf.** Whatever
   `json-diff` (or your local equivalent) emits per field is
   either the raw value (when unchanged) or a change marker
   like `{ __old: 'foo', __new: 'bar' }` (when changed). The
   marker's keys are the discriminator the downstream consumer
   has to handle.
2. **The merge function over-spreads the diff.** Code like
   `{ name, schema, ...tableDiff }` looks like it puts the
   explicit strings in first and the diff on top of them. That's
   exactly the problem. ES2018 spread keeps the *last* value for
   any duplicate key, so when `tableDiff.name` or
   `tableDiff.schema` exists (because that field itself changed),
   the spread silently replaces the explicit string with the
   change marker.
3. **The cleanup pass gates on `Object.keys(entry).length === N`.**
   The function filters "nothing-really-changed" entries by
   asserting that after the merge, the entry has exactly the
   fields the merge put in (often `name` + `schema`, so N = 2).
   This works because if only `name`/`schema` changed, the merge
   produces a 2-key object and the cleanup deletes it before any
   downstream consumer sees it. The cleanup pass *masks the bug
   on the common path*. The bug surfaces only when one more
   field also differs and survives the `length === N` gate.

The error surfaces three call frames downstream, at the schema
validator, and reads as a data-shape complaint about the
unrelated third field's adjacent record. Nobody points at the
merge function because the merge function "obviously" returns a
string for `name`.

## The discriminator

Three questions narrow it.

- **Does the merge function's return shape look like
  `{ explicit, ...polymorphic }`?** Grep for the pattern across
  the file. Anywhere a literal `, ...x }` follows explicit field
  names is a candidate.
- **Is the spread source a diff library or another polymorphic
  emitter?** Anything that can emit a change marker for the same
  field name as one of the explicit keys is at risk. Diff
  libraries, deep-merge libraries, optimistic update reducers,
  CRDT change sets all qualify.
- **Is there a downstream cleanup pass keyed on `length === N`?**
  If yes, the cleanup is masking the bug on the happy path; the
  surface is bugs that fire only when an unrelated adjacent field
  also differs. Cleanup passes keyed on field-set equality
  (`hasOnly(['name', 'schema'])`) are slightly more honest but
  still mask the duplicate-key collision shape; they just throw
  a different error when they catch it.

If all three are true, flip the spread order: `{ ...polymorphic,
explicit }`. The cleanup pass keeps doing its job for genuinely
empty diffs; the explicit strings win the duplicate-key
collision; the downstream validator sees the right shape.

## Real application

### drizzle-team/drizzle-orm#5761 (2026-05-15)

`drizzle-kit generate` crashed with the misleading
`Cannot read properties of undefined (reading 'value')` on a
particular shape of postgres snapshot diff: a table whose
`schema` field changed (`""` → `"public"`) at the same time
its partial index's `where`-clause was re-serialized with the
schema qualifier (`"deleted_at" IS NULL` →
`"public"."widgets"."deleted_at" IS NULL`).

Three sites in `drizzle-kit/src/jsonDiffer.js` had the same
spread shape:

```js
// before
return [
    tableEntry[0],
    { name: table.name, schema: table.schema, ...tableEntry[1] },
];
```

In the common case where only `name` or `schema` changed,
`tableEntry[1]` was `{ name: { __old, __new } }` (or
`{ schema: { __old, __new } }`) and *nothing else*. The spread
replaced the explicit string with the change marker, the merged
entry had exactly two keys, the cleanup pass at lines 265-271
asserted `Object.keys(table).length === 2` and deleted it. Bug
masked. Every existing snapshot transition stayed green.

Add one adjacent field that genuinely differs. The partial
index `where`-clause picked up the schema qualifier as a follow-
on serialization, contributing an `indexes` key to the diff,
so the entry now has three keys. The cleanup pass skips it.
The entry flows downstream to the `diffResultScheme` Zod check,
which expects `schema: z.string()` and receives
`{ __old, __new }`. Zod reports "expected string, received
object," the surrounding code re-throws it as the
read-properties-of-undefined error, and the user sees nothing
that points at the diff merge.

The fix at all three sites:

```js
// after
return [
    tableEntry[0],
    { ...tableEntry[1], name: table.name, schema: table.schema },
];
```

Explicit strings spread last, win the duplicate-key collision.
The cleanup pass at line 265 keeps gating on `length === 2`,
which is still correct semantics for "nothing else changed", but
when an adjacent field does differ, the entry that survives
cleanup now has the right `name`/`schema` types and the
downstream Zod check sees the shape it expects.

Two files, 63 insertions, 4 deletions. PR
[#5768](https://github.com/drizzle-team/drizzle-orm/pull/5768).
The new unit test exercises exactly the shape the reporter
hit (schema change plus partial-index where-clause change)
and stash-bisects both ways: fails with the fix stashed,
passes with the fix in place.

## What this doesn't replace

- **Reading the diff library's API.** The merge bug isn't
  `json-diff`'s fault; `json-diff` is honestly emitting change
  markers per field. The contract that the caller relied on
  ("the diff won't contain a `name` key") was never written
  down. Diff libraries don't promise to skip fields; consumers
  are responsible for handling polymorphism at every field.
- **Reading the Zod (or equivalent) error in full.** Zod's
  "expected string, received object" with the path
  `tables.public.widgets.schema` would have pointed at the
  bug if the surrounding code hadn't re-thrown it as a property
  lookup failure. Schema validators carry blame information;
  preserving their error surface matters more than the
  surface upstream code wraps them in.
- **The cleanup pass itself.** Filtering empty diffs is the
  right thing to do; the bug is the spread order, not the
  filter. Don't delete the cleanup just because it was masking.
  The filter still has a job for the common case.

## When not to use it

- **The polymorphic source can't produce keys that collide
  with the explicit fields.** If the diff payload is guaranteed
  by construction to omit `name`/`schema` (e.g., a strongly-
  typed schema enforces that at the leaf), the spread order is
  cosmetic. Worth asserting the guarantee in code, not just
  in your head.
- **There is no cleanup pass downstream.** Without the cleanup,
  the bug fires on every change to the field, not on the
  adjacent-field-also-changed combination. The repro is
  trivial, the bug ships in week 1, the issue gets filed
  immediately. The hard-to-find shape is specifically
  cleanup-masked.
- **You're reviewing a PR that adds the spread.** Catch it at
  PR time: any `{ name, ...diff }` for a polymorphic `diff` is
  a smell, regardless of whether a cleanup pass exists yet. The
  cleanup pass is an emergent property of the codebase, not a
  guarantee of correctness.

## Related

- [Two-layer bug diagnoses, compatible fixes](two-layer-bug-diagnoses-compatible-fixes.md)
  is about bugs where two reporters trace from different
  starting points and both are right. This card is about the
  opposite: one reporter, one symptom, one bug, but the
  surface is three call frames removed from the cause.
- [Plugin-synthesized Any is not user Any](plugin-synthesized-any-is-not-user-any.md)
  is the same shape applied to types: an explicit type
  annotation getting shadowed by a synthesized one during
  schema merging, where the shadow only matters in a narrow
  combination.
- [Find canonical before fixing bypass](find-canonical-before-fixing-bypass.md)
  is the scout-side discipline. The drizzle bug was sitting
  behind a misleading downstream error for ~a year (line
  265 cleanup pass landed pre-2.x); the surface error was
  filed at least twice before #5761 by users who couldn't
  reach the merge site. The lesson is to chase the diff
  primitive, not the consumer's error message, when the
  reporter has already done the consumer-side trace.

## Revisit

Add a second real application when the next merge-order bug
fires. Specifically watch for: deep-merge libraries
(`lodash.merge`, `deepmerge`) where the polymorphic source is
the merge result of a user-supplied default with a user-supplied
override; CRDT/optimistic-update layers where the local payload
spreads on top of the server payload (or vice versa) and the
collision shape depends on which side won; and any Redux/Zustand
reducer that returns
`{ ...state, ...updates, computed }`-shaped objects where
`updates` can legally contain a `computed` key from an earlier
optimistic write.

If the next application is in a typed language (TypeScript with
exhaustive type narrowing, Rust with serde's deny_unknown_fields,
Python with TypedDict + total=False), split the discriminator
section into per-language subsections. The type system makes
the polymorphism explicit at one of the two ends and the cleanup
pass either has to move or becomes redundant.
