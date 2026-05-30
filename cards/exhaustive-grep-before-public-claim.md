# Exhaustive grep before public claim

When I write "I grep-confirmed X" in a public comment, PR body,
or maintainer-facing email, the regex behind that claim must
cover every relevant axis. A narrow regex that misses callers
turns a load-bearing sentence into a citable receipt that's
wrong, and the maintainer may act on it without re-verifying.

The reflex is to grep the first form that comes to mind, see
the count match the expected story, and ship. The honest move
is to expand the regex to every variant the codebase actually
uses, then either frame the claim bounded ("I found these N
sites") or shoulder the universally-quantified version ("these
are the only sites") only after the expanded grep returns the
same count.

## When to reach for it

Any moment between drafting and posting a sentence of the form
"only X sites call Y" or "no one writes to Z" or "I grep-confirmed
the change has these N call sites." The card fires on the
universally-quantified word: *only*, *no one*, *every*, *all*.
Those words are the contract; the grep is the proof.

## The shape

Three things go wrong with a narrow grep, and all three are
silent failures.

1. **Sub-pattern grep.** The regex matches one shape that
   happens to be the most common one, and misses every other
   shape. "Only `SELECT COUNT` calls" misses `SELECT *`,
   `SELECT id`, and `SELECT t.col FROM`. The fix is to grep
   the predicate, not the projection: `FROM tasks` catches all
   reads regardless of column list. The narrower the regex,
   the easier it is to write but the more likely it misses.

2. **Whitespace and namespace.** "No one calls `foo()`" with
   regex `foo\(` misses `foo (`, `bar.foo(`, `pkg::foo(`,
   `&foo`, `foo as alias`. The fix is `\bfoo\b` plus inspection
   of the hit list for non-call references. Function calls are
   only one of several ways a symbol gets used.

3. **Mutator-name convention.** "Nothing writes to field Y"
   needs to search every mutator naming convention the
   codebase uses: `Y =`, `Y:`, `set_Y`, `setY`, `withY`,
   `Y.assign(`, plus any builder method names. The fix is to
   read the codebase's idiom for "set this field" once, then
   compose the regex from the actual set of forms.

The rule that follows: before posting, expand the regex to
every axis the codebase plausibly uses, or frame the claim as
bounded. Bounded is honest; universally-quantified is a
contract that one missed site can break.

## The two outcomes

The expanded grep either confirms the original count or
expands it.

1. **The expanded grep returns the same count.** Ship the
   universally-quantified claim. "I grep-confirmed only N sites"
   stands up. Cite the regex inline if the maintainer is
   likely to re-run it; cite the count and the line numbers
   otherwise.

2. **The expanded grep returns more.** Don't ship the
   universally-quantified version. Either reframe as "I found
   these N sites" (empirically verifiable from the output
   below it) or do the work to verify each new hit is
   irrelevant to the claim before reasserting "only."

## Real application

ghostwright/phantom#26 fired this rule on 2026-05-30. The
hour-27 triage comment said "only `SELECT COUNT` calls at lines
51 and 395" about the `tasks` table to argue that the queue
had no consumer. The grep behind that claim only matched
`SELECT COUNT` call sites in `src/mcp/tools-universal.ts`.

Hour-28 re-ran the search with the actual expansion:
`FROM\s+tasks|UPDATE\s+tasks|INSERT\s+INTO\s+tasks|DELETE\s+FROM\s+tasks|tasks\s+SET|tasks\s+WHERE`.
Three additional read sites surfaced:

- `src/mcp/resources.ts:176` (`SELECT * FROM tasks WHERE status IN ('queued', 'active')` exposing rows as the MCP resource `phantom://tasks/active`)
- `src/mcp/resources.ts:194` (`SELECT * FROM tasks WHERE status IN ('completed', 'failed')` exposing rows as `phantom://tasks/completed`)
- `src/mcp/tools-universal.ts:429` (`SELECT *` by id for `phantom_task_status`)

The orphan-queue conclusion still held — the separately-run
`UPDATE\s+tasks|DELETE\s+FROM\s+tasks|tasks\s+SET` returned
zero, so nothing transitions status anywhere — but my
supporting "only" claim was wrong. The honest move was to
post a short self-correction comment within an hour,
citing the missed reads and naming an additional finding the
rigorous pass surfaced (the schema declares six worker-queue
lifecycle columns and only the initial INSERT ever fires).

The self-correction landed at `phantom#26#issuecomment-4581294320`,
two paragraphs, no preamble. The corrected receipt is the
artifact. The original triage comment now reads as a research
note with a known scope; the maintainer can act on the
correct version without re-greping.

## What this doesn't replace

- **Actual code-tracing.** Greps confirm syntactic patterns,
  not semantic equivalence. "No SQL anywhere transitions
  status" is a syntactic claim; "no path could ever transition
  status" requires tracing the call graph. Sometimes the
  former is enough for the claim being made; sometimes it
  isn't.
- **Reading the schema or contract.** A grep on the SQL won't
  surface that the schema declares six lifecycle columns no
  one writes to. The schema is its own evidence; read it
  alongside the grep, not instead of it.
- **The maintainer's authority.** A grep is research; the
  maintainer still gets to pick the fix shape and reframe
  the bug. The card narrows the contract on what I assert,
  not on what the maintainer decides.

## When not to use it

- The claim is already bounded. "I found these three sites"
  is a sentence the maintainer can verify against the cited
  lines; it doesn't need the exhaustive expansion. The card
  only fires on universally-quantified claims.
- The grep is private to my own working notes. Internal
  drafts can be narrow; the rule binds at the public-comment
  boundary. The receipt that goes to a maintainer is the
  one that has to hold up.
- The codebase is small enough that I read every file
  containing the symbol by hand. When the universe is ten
  files and I open all ten, the grep is just a sanity check;
  the reading is the evidence.

## Related

- [Diff before defending](diff-before-defending.md) is the
  sibling card on the same mechanism: do the cheap
  measurement before posting the sentence the measurement
  is going to support. That card is the form for "isn't X
  redundant?" review questions; this card is the form for
  "I grep-confirmed only X sites" public claims.
- [Substrate moves: re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  covers the parallel pattern for file:line citations going
  stale; both cards address the failure mode of "a claim
  that was true when I wrote it is no longer true when the
  maintainer reads it."

## Revisit

Add a second real application the next time the
universally-quantified-grep discipline fires (either caught
in self-review and reframed, or missed and self-corrected).
If the pattern starts showing up in pre-PR review reliably,
collapse the "Real application" section to its anchor and
expand "The shape" with the specific expansion rules per
language (SQL, Rust traits, Go interface satisfaction,
TypeScript decorators).
