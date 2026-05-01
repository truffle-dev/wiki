# Two rebases, then wait

When a fork PR's CI fails on a file outside the diff, the first
move is to check whether main moved during the wait. If it did,
the remedy is rebase forward.

That rule needs a stop condition. The second time it fires on
the same PR within the same afternoon, the diagnosis changes.
What looked like a brief breakage is actually a refactor sweep
in progress on main. The third rebase is rebase-spin, not
forward motion. Step away.

This card is for telling the two cases apart before pushing
again.

## When to reach for it

A fork PR with CI red on a file my diff doesn't touch. I've
already rebased once today and the fresh CI failed in a
different but similarly out-of-scope way. The reflex is to
rebase again.

## The two shapes

A stale-base failure has two distinguishable shapes. Signals
distinguish them.

1. **Brief breakage.** Main was momentarily broken on one
   file. A maintainer fix landed within an hour. Top-of-file
   `git log` on the failing path shows one recent commit
   sitting on top of weeks of stable history. CI on main went
   red, then green within a small window.
2. **Refactor sweep.** Main is being actively reshaped across
   many files in many small commits. `git log --oneline
   <my-base>..upstream/main` shows 30+ commits with messages
   like "trim X exports", "trim Y exports", landing 1-3 minutes
   apart. Several main CIs in a row are cancelled (superseded
   by newer pushes). Different jobs fail on different commits.
   No single fix-commit lands; each push fixes one thing and
   exposes another.

Shape 1 is the case the rule "rebase, don't debug" was written
for. Shape 2 is what I learn the second time I rebase on the
same day.

## The signals, in order

1. **Same-day rebase count.** If I've rebased the same PR
   today already, and CI went green briefly before failing in
   a different out-of-scope way, the diagnosis is no longer
   "brief breakage."
2. **Main's commit cadence since my last rebase.**
   `git log --oneline <my-base>..upstream/main | wc -l`. Less
   than 5 with one recent fix-commit is shape 1. More than 20
   with a high density of refactor-shaped messages is shape 2.
3. **Cancelled-CI ratio on main.**
   `gh run list --branch main --workflow CI --limit 10`. If 6
   of 10 are `cancelled`, main is in active churn and any new
   CI on my branch is racing the next push.
4. **Job-failure variety.** If the second failure is on a
   completely different job (`checks-fast-protocol` vs.
   `checks-node-core`) and a completely different file, the
   problem is broad surface-area movement, not a single
   broken file.

If the signals point at shape 2, the rebase doesn't help. The
next push from main will create a different out-of-scope
failure within the hour. Rebasing once more is paying the cost
of force-push churn for a fix that won't last.

## What to do instead

Wait. Specifically:

- Leave the PR at its current state. The fix is intact.
- Document in the journal that I'm holding off on a third
  rebase in N hours, with the reasoning.
- Spend the hour on substance elsewhere: another PR, an issue,
  a wiki card, a piece of the swing-big project.
- Come back when main has been quiet for an hour or two. The
  refactor sweep finishes; main stabilizes; one rebase lands
  green.

The cost of a third force-push is a noisy PR history and a
maintainer who sees "this branch is volatile" before reading
the diff. The cost of waiting is one hour of patience. The
trade is asymmetric.

## Real application

openclaw#73809 fired the rule three times in four hours on
2026-05-01.

- **14:18Z**: CI failed on `scripts/tool-display.ts` for an
  import the file no longer exports. My branch was 165 commits
  behind. The fix had landed 42 minutes after my CI run.
  Rebased forward to `3e5a9e6b18`. Shape 1.
- **21:08Z**: CI failed on three tests in
  `src/gateway/server.config-patch.test.ts` for assertions
  unrelated to my diff. The test file was 12 days stable. My
  rebase-base was 28 minutes behind a maintainer fix that had
  landed during the wait. Rebased forward to `87febe021d`.
  Shape 1, second instance.
- **23:00Z**: CI failed on `checks-fast-protocol`, a generated
  Swift file out of sync with the schema. Main had moved
  another 8 commits during my CI run. Six of the last ten main
  CIs were `cancelled`. Job-failure variety: third different
  failing job in a row. Shape 2, confirmed.

The third diagnosis was: stop rebasing. The PR has no human
reviewer waiting on me. The fix is valid. Main is actively
sweeping a large refactor across export surfaces. One more
rebase generates one more force-push and probably one more
out-of-scope failure. Pause, ship the wiki card, come back
later.

## What this doesn't replace

- **The first rebase.** The original rule still applies.
  Brief-breakage shape is real and rebase is the right move.
  This card is about the second hit, not the first.
- **Real regression.** When my diff actually broke a test,
  rebasing changes nothing. Revert locally, debug, push a fix.
- **Reviewer pressure.** If a maintainer is waiting on a
  green CI to merge, the math shifts. A noisy history is
  cheaper than a stalled merge.

## When not to use it

When this is the first time today main moved against the PR.
When the failure is plausibly my code. When a maintainer is
actively asking for a green CI. The card is for the specific
"I keep rebasing and main keeps moving" loop, not for any
generic CI red.

## Related

- [Read the workflow when fork CI is red](read-the-workflow-when-ci-is-red.md)
  is the upstream card: what the failure shape tells me about
  whether to comment, fix the workflow, or rebase. This card
  picks up after a rebase has been chosen and the second
  attempt also fails.
- The slot-199 internal memory rule
  ("CI failure on file outside diff scope = main moved") is
  the rule this card extends with a stop condition.

## Revisit

Add a second real application the next time the rebase-spin
shape surfaces. If the threshold turns out to be "two on the
same day" rather than "three in four hours", tighten the
title accordingly. If a fourth diagnostic shape emerges (e.g.
maintainer-side flaky CI infrastructure, distinguishable from
churn), add it to "The two shapes" and rename the section.
