# A live total is max(aggregate, sum of parts)

A running total shown in a UI usually has two representations
that are supposed to agree: a single persisted aggregate field
on the parent record, and the stream of fine-grained parts the
aggregate is the sum of. They agree at rest. They disagree
during the exact window a user is most likely to be watching,
because the aggregate is updated on a coarse event (a commit, a
turn finalizing, a full reload) while the parts arrive live. A
view that reads the aggregate directly shows a value frozen at
the last coarse event for the whole live window. The fix is to
derive the displayed value from the live parts and take the
`max` of that against the persisted aggregate. The `max` is not
a tiebreak. It is the whole correctness argument.

## When to reach for it

Any UI element that displays a running total which is also
stored as an aggregate somewhere: a session cost, an upload
progress byte count, a cart subtotal, a job's processed-rows
counter, a thread's token usage. The signature is a memo or
selector that reads one field off the parent object:

```ts
const cost = createMemo(() => session()?.cost ?? 0)
```

and a parent object whose aggregate field is only patched on a
coarse event. If the same screen also shows a sibling value that
*does* update live (a token count, a percent bar, a spinner that
ticks), and the total sits frozen next to it, this is the bug.
The live sibling is the tell: it proves the fine-grained events
are arriving, which means the data to compute the total live is
already in the client. The total is stale by choice of source,
not by lack of data.

## The two clocks

The aggregate and the parts run on different clocks.

The **parts clock** is fast. Each unit of work emits an event
that carries its own contribution: a message with its cost, a
chunk with its byte length, a line item with its price. The
client receives these as they happen.

The **aggregate clock** is slow. The parent record's total field
is recomputed and republished only on a boundary event: the turn
finalizes, the transaction commits, the parent is reloaded from
the store. In between boundaries the aggregate is a snapshot of
the last boundary, and it is authoritative only at rest.

The trap is that both clocks expose a field that looks like "the
total," and the aggregate's field is the more obvious one to
read because it lives right on the object you already have. So
the view binds to the slow clock and inherits its staleness for
the entire fast-clock window.

## Why max and not replacement

The instinct, once you see the staleness, is to replace: stop
reading the aggregate, sum the parts instead. That is half
right, and the missing half is why `max` is the correct
operator rather than a clever-looking one.

Summing the parts is correct **only if the client holds all the
parts.** It frequently does not. Histories get truncated to a
window. Lists paginate. A freshly resumed or reloaded view has
the aggregate before it has streamed the back-history. In every
one of those cases the sum of the parts the client currently
holds *undercounts* the true total, and a naive replacement
would make the displayed number jump downward the moment you
switch source.

`Math.max(aggregate, sumOfParts)` resolves both regimes with one
expression:

- **Mid-stream, full parts held:** the sum includes the live
  in-flight contribution that the aggregate does not yet know
  about, so the sum is larger and leads. The total climbs live.
- **After the boundary:** the aggregate catches up and the two
  converge to the same number. No flicker at the handoff.
- **Truncated or not-yet-loaded parts:** the sum undercounts, so
  the aggregate is larger and wins. The displayed value never
  regresses below the last persisted total.

The `max` makes the displayed value monotonic across all three
regimes without the view needing to know which regime it is in.
That is the property worth protecting: a running total should
only ever climb or hold, never drop, because a number that
ticks backward reads as a bug to a user even when the new value
is "more correct."

## The failure shape

`Kilo-Org/kilocode`'s TUI sidebar is the reference case. The
`Context › spent` line read the session aggregate:

```ts
const cost = createMemo(() => session()?.cost ?? 0)
```

`session().cost` is patched in only two places: a
`session.updated.1` event, or a full session-list load at
startup or resume. During a live assistant turn neither fires.
The per-turn cost is bumped as a database-only projector side
effect (`session/projectors.ts` `applyUsage()` does
`SessionTable.cost = cost + …`) with no `Session.Event.Updated`
published. So mid-turn the client received the message and part
events, which updated each *message's* cost, but nothing touched
the session aggregate the sidebar was bound to. The sidebar
showed `$0.00` for the entire turn and then snapped to the right
number the instant the turn finalized and the aggregate was
persisted.

The tell was sitting one line away: the token count and context
percent in the same sidebar block updated live, because those
memos already derived from the message list (`msg()`) rather
than the session aggregate. The data to compute live cost was in
the same array the live tokens were read from.

The fix derived cost from the parts and reconciled with the
aggregate:

```ts
const cost = createMemo(() => {
  const total = msg().reduce((sum, item) => {
    if (item.role !== "assistant") return sum
    return sum + (item.cost ?? 0)
  }, 0)
  return Math.max(session()?.cost ?? 0, total)
})
```

Fourteen lines including the changeset, one file. The `max`
guard is what makes it safe against a truncated message window:
if the TUI is not holding the full history, `total` undercounts
and `session().cost` wins, so the number never drops below the
persisted session total. Mid-turn it leads and climbs; at
finalization the two converge.

## Distinguishing from related failures

A few things look like this in symptom but are a different bug.

- **The aggregate is genuinely wrong, not just stale.** If the
  persisted total is incorrect at rest (after the boundary
  event, with full parts loaded, the two still disagree), the
  bug is in the aggregation write, not the read. `max` would
  paper over it. Check that aggregate and sum agree at rest
  before reaching for this card.
- **The parts carry overlapping contributions.** `max` plus a
  sum assumes each part's contribution is disjoint and additive.
  If parts can double-count (a retry that re-emits a chunk, an
  event delivered twice), summing them overcounts and the sum
  wrongly leads. The fix there is idempotent part accounting,
  not a reconciliation operator.
- **The total can legitimately decrease.** `max` enforces
  monotonic-up. If the real quantity can drop (a cart with item
  removal, a refund, a counter that resets per window), `max` is
  the wrong operator and will pin the display to a stale high.
  This card is for accumulating-only totals.

## When this isn't the bug

- **No live sibling updates either.** If the token count and the
  spinner are also frozen, the fine-grained events are not
  reaching the client at all. The bug is upstream in the event
  delivery, and computing from parts cannot help because the
  parts are not arriving. Fix the stream first.
- **The aggregate is the only source by design.** Some totals
  are server-authoritative and the client is not meant to hold
  the parts (a billing figure that must match a ledger to the
  cent). There, showing a stale-but-trusted aggregate and
  refreshing on the boundary is the correct conservative choice,
  and a client-side live sum would be a number the server never
  blessed. Know which kind of total you have before deriving it.

## The diagnostic

Three questions, in order.

1. **Is a sibling value on the same surface updating live?** If
   yes, the fine-grained events are arriving and the data for a
   live total is already client-side. If no, stop here, the bug
   is in the stream.
2. **What event patches the aggregate, and does it fire during
   the live window?** Trace the writer of the total field. If
   its only triggers are boundary events (commit, finalize,
   reload), the staleness is confirmed.
3. **Can the client's held parts undercount the true total?**
   If histories truncate or paginate, yes, which is the argument
   for `max` over replacement. If the client is guaranteed to
   hold every part, replacement is safe but `max` costs nothing
   and defends against a future truncation.

## Real applications

- **2026-06-21, kilocode#11480.** Reporter described the TUI
  "spent" line showing `$0.00` during a live session and the
  correct value after resume. Root-caused to the sidebar memo
  reading `session().cost` (the boundary-clock aggregate) while
  the per-message cost arrived live on the parts clock, the same
  array the live token count already derived from. The fix
  ([PR #11506](https://github.com/Kilo-Org/kilocode/pull/11506), `mvanhorn`) summed `item.cost` across the
  assistant messages and took `Math.max` against the session
  aggregate. The diagnosis and the fix agreed on the layer; the
  point worth naming on the review was that the `max` is a
  correctness guard against a truncated message window, not a
  tiebreak, so the displayed value never regresses below the
  persisted session total.

## Related

- [Audit readers when reordering state](audit-readers-when-reordering-state.md)
  is the same family one move over: there a writer reordered and
  broke a reader's assumption; here a reader bound to the wrong
  one of two sources that are supposed to agree. Both are
  "which representation of this value is authoritative right
  now" bugs.
- [Read the closure, not just the state](read-the-closure-not-just-the-state.md)
  is the instinct at the UI layer: a field that reads as "the
  total" is not the total that matters until you know which
  clock patched it.

## Revisit

One case is enough to name the pattern, not enough to map its
edges. The open question is how often the `max` guard actually
fires in practice versus being defensive dead weight. If I find
a case where the parts are guaranteed complete and the aggregate
is guaranteed wrong, that would argue for replacement over
reconciliation, and I would fold the distinction in here. The
shape I am watching for next: any "live N of M" or running-sum
display whose source field is patched on a commit or a reload
rather than on each unit of work.
