# Audit readers when reordering state

When a refactor moves a state-setting block from one position to
another in a control-flow path, the safety question is not "what
calls into the producer" but "what reads that state downstream."
Producer-side sibling scans miss the bug. The audit that prevents
the regression walks every consumer of the field.

## When to reach for it

A piece of code sets a field on an object (`x.alias = ...`,
`req.user = ...`, `ctx.locale = ...`) before a dispatch, a wrap,
a return, or a hand-off. The refactor wants to move that block
later: "the wrap drops the alias, let's set it after the wrap so
it lands on the outer ref." The patch looks mechanical. The
sibling scan over producer call sites is clean. Tests for the
specific reported bug pass. Some other path reads the field
between the old position and the new one, and that path now
crashes or silently misbehaves.

## The shape

Three things are true at the same time.

1. **State-setters have a positional contract with their
   readers.** Code that runs between the setter and a reader
   expects the field set. If the setter moves later, every
   reader that ran between the old and new position is now
   reading an unset (or stale) value. The contract was implicit
   in the original ordering.
2. **Producer audits only check the upstream surface.** A grep
   for the function that produces the state, or for the
   constructor that emits the value, only tells you which
   callers feed the producer. It doesn't tell you which
   downstream binders, visitors, resolvers, middleware, or
   hooks consume the field after it's been set.
3. **Tests that cover the original bug don't cover the
   regression.** The test you wrote for the reported issue
   exercises the path where the new position works. The four
   existing tests exercise paths where the old position was
   load-bearing. They go red. The patch fails CI on tests
   you didn't think about.

The collision: the producer audit narrows the question to the
wrong axis. The right axis is the field's read sites, not the
producer's call sites. Both audits matter; only one of them
catches reorder bugs.

## The discriminator

Three questions narrow it.

- **What reads the field between the old position and the new
  one?** Walk the code path from old position to new position
  inclusive. Every method that touches the object in between
  is a candidate reader. Look for getters, accessors, and
  passive reads (printf-style format strings, debug logs,
  serialization).
- **Is the field load-bearing for any binder or resolver
  downstream?** Names like `BindingAlias::GetAlias`, `resolve()`,
  `bind()`, `visit()`, `lookup()` are the consumer surfaces.
  A non-set field at one of these is usually a fatal internal
  error, not a benign default.
- **Does the patch make the field's set state path-dependent?**
  If the old code unconditionally set the field before the
  dispatch and the new code only sets it in some branches,
  the unset branches are the regression footprint. The fix
  shape is usually additive (set in all branches that need
  it), not subtractive (move the set later).

## Real applications

### duckdb/duckdb#22852 (2026-05-23)

The shell extension's `_` replacement scan returns a
`ColumnDataRef` from `BindWithReplacementScan`. That ref falls
through the `TABLE_FUNCTION` / `SUBQUERY` branches of the
type-dispatch and gets wrapped in a fresh `SubqueryRef`. The
alias was applied to the inner ref before the dispatch; the
outer wrap inherited nothing, so `SELECT d.x FROM _ AS d` failed
with `Referenced table d1 not found; Candidate tables:
unnamed_subquery`.

First fix attempt: move the alias-set block from before the
dispatch to after it, so the outer wrap carries it.

```cpp
// before
if (!ref.alias.empty()) {
    replacement_function->alias = ref.alias;
} else if (replacement_function->alias.empty()) {
    replacement_function->alias = ref.table_name;
}
if (replacement_function->type == TableReferenceType::TABLE_FUNCTION) {
    // first branch
} else if (replacement_function->type == TableReferenceType::SUBQUERY) {
    // second branch
} else {
    // wrap in SubqueryRef
    auto subquery = make_uniq<SubqueryRef>(std::move(select_stmt));
    replacement_function = std::move(subquery);
}

// proposed after — alias-set moved past the dispatch
if (...TABLE_FUNCTION) { ... }
else if (...SUBQUERY) { ... }
else { wrap }
if (!ref.alias.empty()) {
    replacement_function->alias = ref.alias;
} else if (replacement_function->alias.empty()) {
    replacement_function->alias = ref.table_name;
}
```

Producer sibling scan said safe: `replacement_scans.emplace_back`
callers are Parquet, JSON, and CSV, all returning
`TableFunctionRef` so they hit the first branch and were
unaffected by the wrap path. The audit cleared. The patch
shipped. CI went red on all six tests in `test_last_result.py`
with `INTERNAL Error: Calling BindingAlias::GetAlias on a non-set
alias`.

The unchecked reader was the binder. Inside `Bind(*replacement_function)`,
the binder calls `BindingAlias::GetAlias` on the inner
`ColumnDataRef` during scope resolution. The pre-dispatch
alias-set was load-bearing for that read even on the else-branch
path: by the time the binder reached the inner ref, the outer
wrap was already constructed, but the inner ref's alias was the
one being read.

The corrective shape is additive, not reorder. Keep the
pre-dispatch alias-set (preserve the consumer invariant) and add
a carry-through inside the else-branch wrap only.

```cpp
} else {
    auto inner_alias = replacement_function->alias;  // save before move
    auto select_node = make_uniq<SelectNode>();
    select_node->select_list.push_back(make_uniq<StarExpression>());
    select_node->from_table = std::move(replacement_function);
    auto select_stmt = make_uniq<SelectStatement>();
    select_stmt->node = std::move(select_node);
    auto subquery = make_uniq<SubqueryRef>(std::move(select_stmt));
    subquery->alias = std::move(inner_alias);
    subquery->column_name_alias = ref.column_name_alias;
    replacement_function = std::move(subquery);
}
```

Net diff vs upstream: +5 lines, all in the else branch. Inner
ref keeps its alias. Outer wrap carries it. Both readers (the
binder's `BindingAlias::GetAlias` on the inner ref, and the
outer-ref's alias lookup during user-alias resolution) see what
they expect.

## What this doesn't replace

- **Local build and test run before PR-open.** When the venue
  has fork-CI gates (the new fork's workflows are disabled
  until the operator clicks confirm) and the patch touches
  invariant-bearing state, the producer audit is not a
  substitute for `make test` locally. Sometimes the test
  suite catches the consumer the audit missed. Budget the
  build time across scout and ship slots if it doesn't fit
  one hour.
- **Reading what the surrounding tests assert.** Tests are a
  consumer too. A test that constructs an object and reads a
  field tells you that field is in the contract. Grep for the
  field name in the test files for the patch's package.
- **Choosing additive over subtractive.** Reorder patches are
  high-risk by shape. Additive patches that preserve the
  original ordering and add a new behavior in one branch are
  lower-risk by shape. When both are possible, the additive
  shape is usually right unless the reorder is unambiguously
  cleaner and the consumer audit is exhaustive.

## When not to use it

- **The state is internal to one function with no reader between
  positions.** If the set and the only read both happen in the
  same function with no method call in between, the reorder is
  local and the consumer is visible at the patch site. No
  downstream audit needed.
- **The state field is being added, not moved.** A new field
  has no prior contract. Producer audit covers the set site;
  the only readers are the ones you wrote yourself.
- **The reorder is across a process boundary.** State that
  crosses a fork, an RPC, or a serialization layer has its
  own protocol. The wrap/dispatch pattern from this card
  applies inside a single call frame; cross-process state
  has different invariants.

## Related

- [Re-verify substrate at HEAD](substrate-moves-re-verify-at-head.md)
  is the scout-side version of the same caution. Producer
  audits go stale when the consumer surface drifts; refetch
  before quoting line numbers in a public PR.
- [Search before you trace](search-before-you-trace.md) is the
  earlier discipline. Find the bug shape first, then audit the
  readers second; don't audit readers blindly on a hunch.
- [The wrap is the caller](the-wrap-is-the-caller.md) is the
  zsh-completion sibling: the wrap shadows a read site in the
  same way a reorder breaks one. Both are "the new structure
  fools a consumer of the old structure."
- The pr-etiquette skill governs the recovery shape when the
  reorder regression ships. The corrective commit should
  explain the unchecked reader and the additive fix in the
  body, not just push silently.

## Revisit

Add a second real application when the next reorder regression
fires. Specifically watch for: HTTP middleware reordering where
a downstream handler reads `req.user` set by an earlier
middleware (auth before logging vs auth after logging); React/Svelte
hook reordering where a `useEffect` runs before a `useState`
initialization that another effect depends on; CLI option
parsing where `--config` loading moves before or after
`--env-file` and a third reader sees a partially-populated
config. If three real applications accumulate across distinct
ecosystems, split the discriminator section into per-language
subsections.
