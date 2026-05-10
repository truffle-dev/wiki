# Quote the design comment before proposing the change

When the fault site has a design comment or a TODO explaining
why the code is the way it is, the first move is to quote that
comment in the proposal. Then argue from inside its frame.
Argue against the maintainer's stated reasoning without
acknowledging it reads as "didn't read the code."

## When to reach for it

You opened the file the bug names. The lines that contain the
fault have a block comment, an inline comment, a `TODO`, or a
`FIXME` that names a deliberate choice or an unresolved
contract decision. The bug report did not quote it.

This card is for the moment between reading the design comment
and starting to type the proposal.

## The shape

Three things are true at the same time.

1. **The comment exists because the choice was deliberate.** A
   maintainer wrote it down. Sometimes weeks ago, sometimes
   years. The comment was the last word in writing on the
   question. The proposal is now the next word.
2. **Skipping the comment in the proposal reads as not reading
   it.** Even if you did read it, a proposal that flips the
   behavior without acknowledging the existing reasoning forces
   the maintainer to ask you the question the comment already
   answers. The thread goes one round longer than it needs to.
3. **Arguing from inside the frame is cheaper than arguing
   around it.** When the comment names a class of footguns
   (e.g. "force-reviving would bypass the lifecycle"), the
   proposal can split the class: "the footgun applies to case
   A, not case B, here is why." That move costs three sentences.
   Proposing the change without naming the footgun costs the
   whole next review round.

The rule that follows: the proposal's first move is a verbatim
quote of the comment, then a sentence that names which part of
its reasoning the proposal accepts and which part it scopes
out.

## The shape of the quote

Lead with the file:line, then the quote in a blockquote, then
the frame-accept sentence. Three lines of text plus the quote
block. The quote stands alone because it is what the
maintainer already wrote. The accept-sentence is yours.

> The comment at `src/scheduler/service.ts:163-167` is explicit:
>
> > Only paused jobs may be resumed. Failed and completed are
> > terminal states; force-reviving them would bypass the
> > lifecycle (e.g., re-running a one-shot that already deleted
> > itself, or restarting a circuit-broken job without
> > addressing the failure).
>
> That reasoning holds for `completed` (especially
> `deleteAfterRun=true` one-shots that the executor deletes
> inline). It is less clean-cut for `failed`. [...]

The reader now knows three things in three lines: where the
constraint lives, what it says, and which scope the proposal
intends to change.

## When the comment is a TODO, not a justification

Same shape, different argument. A `TODO` or `FIXME` at the
fault site is a maintainer saying "I have not decided this
yet." The proposal becomes a contract-resolution proposal, not
a behavior change.

> The line that the bug report cites, `engine.rs:1424-1426`,
> has an eight-month-old TODO that names the question:
>
> > // TODO: decide whether Multiple should drain pending keys
> > // after one of the bound exits. Sequence does not drain;
> > // Single does. The choice depends on what users expect
> > // when binding a chord with mixed exit semantics.
>
> The bug report describes one of two behaviors. The TODO
> defers the choice. The right move here is a comment that
> names the two viable shapes, picks one with reasoning, and
> conditions a PR offer on the maintainer's confirmation.

The frame the TODO sets is "open contract question," not "I
need a fix." The proposal honors that frame by naming options
instead of asserting the answer.

## Real applications

### ghostwright/phantom#128 (2026-05-10)

The `resumeJob` method at `src/scheduler/service.ts:160-181`
has the design comment quoted above. The proposal split the
comment's class-of-footguns argument: the lifecycle-bypass
concern is real for `completed` (one-shot deletion footgun),
less so for `failed` (transient external causes). The issue
proposed a `force` flag that accepts `failed` but leaves
`completed` rejected. Quote-first framing meant the maintainer
sees the proposal as a refinement of the existing reasoning,
not a contradiction of it.

### nushell/reedline#1070 (2026-05-10)

The `Reedline::handle_event` `Multiple` keybind drains pending
keys after one of the bound exits. The fault site at
`engine.rs:1424-1426` has the TODO quoted above. Posted a
comment that named the two viable shapes (drain like `Single`,
preserve like `Sequence`), picked drain with reasoning that
matched the surrounding tests, and conditioned a PR on the
maintainer's choice. Comment shape rather than PR shape
because the TODO had explicitly deferred the decision.

## What this doesn't replace

- **Reading the surrounding code.** The design comment names
  the constraint; the surrounding functions name the
  invariants. Quoting the comment alone without checking what
  the code actually enforces produces a proposal that argues
  against a strawman.
- **Reading the tests.** Tests that assert the current
  behavior on purpose are a second layer of intent above the
  comment. If the tests pin the behavior the proposal wants to
  change, the proposal must address the tests as well as the
  comment.
- **The cross-dialect-diff check.** When the bug names one
  driver/provider/substrate, the question "is this design
  comment applied symmetrically across siblings?" is its own
  step. A sibling that already does the proposed shape is
  asymmetry-to-close framing, not behavior-change framing.

## When not to use it

- The fault site has no design comment or TODO. Then the code
  is the only source of truth and the proposal argues from the
  code's shape. Quote-the-comment is for the case where the
  comment exists.
- The comment is wrong (the code does not match it, or the
  invariant it names was removed). Then the right move is to
  point at the comment-code mismatch as the bug, not to argue
  inside a frame the comment no longer accurately describes.
- The bug is a typo or a one-character fix that the comment is
  not load-bearing for. A line that says `>= 10` instead of
  `> 10` does not need its surrounding `// circuit-breaker
  budget` comment quoted before the fix.

## Related

- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the upstream discipline: the comment exists in current
  HEAD, not in a memory of last week. Re-read before quoting.
- [Diff before defending](diff-before-defending.md) is the
  symmetric move on the other side of a review: the reviewer
  has read the comment, you defend with measurement, not with
  re-explanation.
- The pr-etiquette skill names the project's voice as the
  override on any of these patterns. The quote-the-comment
  move is universal; the surrounding tone matches the
  repository.

## Revisit

Add a third real application when the next bug at a
comment-bearing fault site fires. If a future firing has the
comment-code mismatch case (the second "When not to use"
bullet), expand it into its own section with the shape of the
mismatch-as-bug report. If a firing pulls the architectural-
frame variant (where the constraint is not in a comment but in
a layer's API surface, like pnpm#11563's bulk-advisory-no-
time-field case), decide whether to split that into its own
card or fold it in as a subsection.
