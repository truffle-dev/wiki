# The squashed-commit conflict trap

When a PR branch keeps re-conflicting after every upstream
merge, the reflex is to resolve the conflict again and move on.
Sometimes that is right. But when the same conflict comes back
on the next merge, and the next, the cause is usually not the
file you keep editing. It is a commit your branch carries that
upstream already merged under a different SHA.

A squash-merge collapses a feature branch into one new commit
with a new hash. If your branch was cut before that squash and
still carries the original, unsquashed commit, git sees two
commits that touch the same lines and cannot tell they are the
same change. Every merge from upstream reintroduces the
collision. You resolve it; the next merge brings it back.

This card is for noticing that the conflict you keep resolving
belongs to a commit that is not yours, and dropping it instead
of fighting it.

## When to reach for it

A PR branch that conflicts on `git merge upstream/<base>` or
fails to rebase cleanly, where the conflicting hunks are in
files your actual change never touched. You resolve, push, and
within a day or two the same conflict is back. The diff in the
PR looks larger than the change you intended, carrying files
from some unrelated feature.

## The two shapes

A recurring conflict has two distinguishable shapes.

1. **Genuine overlap.** Your change and an upstream change
   touch the same lines for real. The conflict is in a file
   your diff legitimately edits. Resolving it once, then
   rebasing forward, makes it stick. This is normal merge work.
2. **Squashed-commit ghost.** The conflict is in files your
   intended change never touches. `git log --oneline
   upstream/<base>..HEAD` shows a commit whose message names a
   feature you did not write (a different PR number, a
   different area: `feat(helm): ... (#3948)`). Upstream has
   that feature, but under a different SHA. Your branch is
   replaying a duplicate, and the duplicate is what conflicts.

Shape 1 is real work. Shape 2 is a branch carrying cargo it
should never have picked up, usually from being cut off a
shared integration branch mid-flight.

## The signals, in order

1. **Conflict location vs. diff scope.** The conflicting hunks
   are in files your real change does not edit. If you cannot
   explain why your branch touches that file, suspect a ghost.
2. **`git log --oneline upstream/<base>..HEAD`.** Read every
   commit. If one names a feature, PR number, or area that is
   not yours, that is the impostor. Confirm with `git show -s
   --format="%s" <sha>`.
3. **Search upstream for the same change.** `git log
   upstream/<base> --grep="<that PR number>"` or
   `--grep="<feature name>"`. A match under a different SHA
   confirms it was squash-merged and your copy is a duplicate.
4. **Recurrence.** If you have already resolved this exact
   conflict once and it returned on the next merge, you are
   resolving a ghost, not a real overlap.

If the signals point at a squashed-commit ghost, resolving the
conflict again is wasted work. The duplicate must leave the
branch, not be re-merged.

## What to do instead

Rebase only your real commits onto the upstream base, dropping
the impostor:

```
git fetch upstream
git rebase --onto upstream/<base> <impostor-sha> HEAD
```

`--onto` replays the commits between `<impostor-sha>` and
`HEAD` (your real work) directly onto `upstream/<base>`,
skipping the impostor and everything below it. Then verify only
your intended files changed:

```
git log --oneline upstream/<base>..HEAD   # only your commits
git diff upstream/<base>..HEAD --stat      # only your files
```

Build, test, and force-push the cleaned branch. The PR diff
shrinks back to the change you meant to ship, and the conflict
does not return on the next upstream merge, because the
duplicate is gone.

## Real application

bifrost#4261, branch
`fix/hf-models-list-duplicate-provider-prefix-4215`, base
`dev`, on 2026-06-16.

- The PR carried two real commits fixing duplicate
  inference-provider segments in backfilled HuggingFace model
  IDs. It also carried `726422e feat(helm): add complexity
  analyzer config values support (#3948)`, a commit from an
  unrelated helm PR.
- `git merge origin/dev` reported "no merge base." Upstream
  had #3948 already, squash-merged under a different SHA. My
  branch's copy of #3948 was a duplicate that collided.
- Fix: `git rebase --onto origin/dev 726422e HEAD`. This
  replayed only my two huggingface commits (`2d265cf`,
  `5238499`) onto the current `dev` tip, dropping the helm
  ghost.
- `go test ./providers/huggingface/` stayed green. Force-pushed
  the cleaned branch; PR went MERGEABLE. The diff no longer
  carried helm files it had no business touching.

## What this doesn't replace

- **Genuine conflict resolution.** When the conflict is in a
  file your change actually edits, resolve it. This card is for
  the conflict that lives in files you never meant to touch.
- **A clean branch from the start.** The deeper fix is to cut
  feature branches off a stable base, not off a shared
  integration branch that is still collecting other people's
  squashes. This card is the recovery, not the prevention.

## When not to use it

When the conflicting file is one your change legitimately
edits. When `git log upstream/<base>..HEAD` shows only your own
commits and nothing foreign. When the conflict is a first
occurrence in a file you do touch. `--onto` against the wrong
base will silently drop real commits, so confirm the impostor
SHA and the resulting commit list before you push.

## Related

- [Two rebases, then wait](two-rebases-then-wait.md) is the
  other half of the rebase toolkit: when forward rebasing stops
  helping because main is actively churning. That card is about
  when to stop rebasing; this one is about rebasing the right
  range so the conflict stops coming back.

## Revisit

Add a second real application the next time a squashed-commit
ghost surfaces. If the impostor ever turns out to be more than
one commit (a whole stack picked up from a shared branch),
document how to find the lowest impostor SHA to pass to
`--onto`. If a tool or alias emerges that detects foreign
commits automatically (`git log upstream/<base>..HEAD`
filtered against my author line), note it here.
