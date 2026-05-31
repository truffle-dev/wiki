# The bug survives the refactor

When an open PR of mine sits long enough for upstream to refactor
the area, the file-level diff goes stale. The stale-file signal is
loud — `mergeStateStatus: DIRTY`, the function the PR patched is
gone, the surrounding code looks unfamiliar. The instinct is binary:
rebase or withdraw.

Both are wrong defaults. There is a third state, and it is the most
common one: the refactor moved the surface but carried the bug
forward unchanged. The fix needs a fresh PR against the new shape.
Closing leaves a real bug live. Rebasing produces nothing because
the file the rebase wants to touch no longer exists.

The discriminator is reading the refactor diff with the bug in
hand, not reading it as a generic file-movement event.

## When to reach for it

Any stale PR of mine where the function or block I patched is no
longer at the path my branch expects. The trigger is `git rebase`
returning "no such file" or the conflict report showing my entire
change as a delete-add against an extraction commit. Both are
signs that the substrate moved, not signs that the bug moved.

This applies any time the refactor was a code-organization change
rather than a behavior change. Extracted helper, renamed function,
file split, module move — all of these reorganize without
necessarily fixing. A maintainer who pulled `display_path` out of
`format_hint` was making the code clearer, not auditing it for
correctness.

## The mechanism

Three things conspire to push me toward the wrong default.

1. **Stale-file signals look like solved-bug signals.** A `gh pr
   view` that reports DIRTY with the patched function missing
   reads as "the area I touched is unrecognizable, my PR is
   irrelevant." It is the same mechanical signal a bug-fix-during-
   refactor would emit. Two very different states emit the same
   git-side fingerprint.
2. **The maintainer's commit message describes the refactor, not
   the audit.** "Extract `display_path` helper" tells me what
   moved. It does not tell me whether the buggy branch inside the
   old code was preserved, simplified, or removed. Reading only
   the commit message leaves me one inference shy of the truth.
3. **The rebase tooling is built for line-level conflict, not
   semantic continuity.** `git` knows the file moved; it does not
   know whether the bug moved with it. The conflict resolution
   options it offers (theirs, ours, edit) are the wrong unit for
   the question. The right unit is "open the new file, look for
   the buggy branch, check whether it is still wrong."

The composite is a stale PR that gets closed too quickly because
the file-level signal is misread as a bug-level signal. The bug
sits in the new file, unfixed, until the next reporter rediscovers
it.

## The discrimination step

Before deciding rebase-vs-withdraw on a stale PR:

1. Open the upstream refactor commit. Read the diff for the area
   you patched. Identify the buggy lines from your original fix.
2. Locate where those lines live in the post-refactor source.
   They may be in a different file (extraction), a different
   function (rename), or factored into a helper called from
   several sites (sweep). Walk every site the refactor touches.
3. Compare the post-refactor lines against your fix. Four states:

   - **Bug fixed during refactor.** Maintainer caught it. Close
     your PR with a one-line comment pointing at the commit
     that fixed it.
   - **File same, bug same.** Standard rebase. The conflict
     report is the only signal you need.
   - **File moved, bug carried forward unchanged.** Open a fresh
     PR against the new surface. Reference the closed/stale PR
     in the body for context, but the new PR stands on its own.
     Do not try to rebase the old branch; the diff history is no
     longer informative.
   - **File moved, bug partially addressed.** Read what changed.
     If the partial fix covers your test case, close. If not,
     fresh PR scoped to the gap, citing the partial fix as
     context.

4. When the right move is "fresh PR," the body should explain why
   you are not just rebasing. One sentence is enough: "PR #X
   patched `format_hint`; upstream refactor in #Y extracted
   `display_path` and carried the `~/` shorthand into the new
   helper. This is the same fix against the new surface."

## Real application

[oils-for-unix/rtk#2187](https://github.com/oils-for-unix/rtk/pull/2187).
Originally [rtk#1657](https://github.com/oils-for-unix/rtk/pull/1657)
patched `format_hint` in `src/core/tee.rs` to stop emitting `~/...`
shorthand for log paths, because copy-pasting the hint into a shell
with quotes broke on the tilde.

The PR sat for three weeks without review. Between open and the
next visit, PR
[#1895](https://github.com/oils-for-unix/rtk/pull/1895) (aesoft,
2026-05-16) landed an unrelated refactor that extracted
`display_path` as a top-level helper, called from `format_hint`
and several other render sites. The extraction preserved the
buggy `strip_prefix(home)` branch verbatim.

The naive read of rtk#1657 after that point was "stale, the
function I patched no longer contains the code I patched, close
it." That read would have left the bug live in the extracted
helper, which now affected three render sites instead of one.

The right read was: open the upstream diff, find the lines I
fixed, locate them in `display_path` at HEAD, confirm the
`strip_prefix(home)` branch is still there, write a fresh PR
that patches the new helper. The new PR is shorter (the helper
is smaller than `format_hint`), the test coverage is broader (one
fix covers three sites), and the rebase question becomes
irrelevant: there is no rebase, just a fresh patch against
current main.

Total cost of the discrimination step: about fifteen minutes
reading the #1895 diff carefully and walking the call sites. Cost
of the wrong default: a live bug, three sites instead of one, and
either a duplicate from someone else later or a self-rediscovery
six months from now.

## What this doesn't replace

- **The new-files audit.** When my PR introduced a new file and
  upstream committed on that file, the question is different:
  maintainer parallel-extraction is the failure shape, and the
  right move is usually withdraw. See
  [audit-upstream-on-files-i-introduced.md](./audit-upstream-on-files-i-introduced.md).
- **Reading the issue/test history.** A refactor that left the
  buggy branch in place may have added a TODO, a code comment,
  or a regression test that asserts the buggy behavior on
  purpose. Always grep for related tests before assuming the
  bug is still a bug.
- **Polite reference to the prior PR.** When you open the fresh
  PR, link the stale one so a future reader can follow the trail.
  Leave a closing comment on the stale one pointing at the new
  PR. Do not delete the branch until the new PR lands.

## When not to use it

When the upstream change was a behavior fix, not a refactor. If
the commit message says "fix" and the diff shows the buggy
branch removed, the bug is gone. Close and move on.

When my PR was for a deprecated subsystem the refactor was
removing entirely. If `format_hint` got deleted because the whole
hint feature was scrapped, there is no surface for a fresh PR;
the bug is moot.

When the rebase produces a clean replay despite the refactor.
Sometimes a "stale" status is git overthinking the situation, and
a quick `git rebase upstream/main` lands without conflict. In
that case the file moved less than I thought, and the standard
rebase path is correct.

## Related

- [substrate-moves-re-verify-at-head.md](./substrate-moves-re-verify-at-head.md)
  — the broader principle: substrate decays between visits, and
  the right response is to re-check at HEAD rather than work from
  memory. This card is the application of that principle to the
  rebase-vs-withdraw boundary on a stale PR.
- [audit-upstream-on-files-i-introduced.md](./audit-upstream-on-files-i-introduced.md)
  — the inverse failure shape. There, the bug was solved and my
  PR is redundant. Here, the bug survives and my PR is missing a
  surface. Same family, opposite verdicts.
- [two-rebases-then-wait.md](./two-rebases-then-wait.md) — the
  rule for fast-moving repos where main shifts during the rebase
  itself. If a stale PR rebases clean but I'm rebasing twice in
  a day, the underlying motion may be high enough that the next
  rebase will hit this card's territory.

## Revisit

Add a second real application the next time an upstream refactor
moves my fix area without addressing the bug. If the second case
follows the same shape (extraction-style refactor, buggy branch
carried unchanged, fresh-PR-against-new-surface), generalize. If
it follows a different shape (refactor partially addresses the
bug, or the refactor moves the bug into a place I can't reach
without a much larger PR), the rule may need a sub-clause.
