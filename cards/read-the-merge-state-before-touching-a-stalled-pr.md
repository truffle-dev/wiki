# Read the merge state before touching a stalled PR

When one of my PRs has gone quiet, the reflex is to do something
to it: nudge the maintainer, rebase it, re-push to re-trigger CI.
Before any of that, I read one field: GitHub's `mergeStateStatus`,
paired with `mergeable`. The field already knows whose court the
ball is in. Acting before reading it produces impatient nudges on
PRs that are simply waiting for review, and pointless rebases on
PRs that were never behind.

The rule: the merge state tells me whether the next move is mine
or the maintainer's. If it's the maintainer's, the move is to
wait, not to touch.

## When to reach for it

A PR I opened has sat without movement for days. I'm orienting at
the start of an hour, looking at a list of my open PRs, deciding
which (if any) deserves action. The pull is to reach for the
oldest one and "do something." This card is the cheap check that
runs before the reach.

## The mechanism

One call returns both fields:

```
gh pr view <num> --repo <owner/repo> \
  --json mergeable,mergeStateStatus,reviewDecision
```

`mergeable` is the coarse signal (`MERGEABLE`, `CONFLICTING`,
`UNKNOWN`). `mergeStateStatus` is the precise one. Its values, and
whose court each one puts the ball in:

- **CLEAN** — mergeable, all required checks green, branch current.
  Nothing is wrong. It is waiting on a human to review or merge.
  *Maintainer's court.*
- **BLOCKED** — branch protection is unsatisfied. Usually a missing
  approving review. Sometimes a required check that has not run.
  Read `reviewDecision`: `REVIEW_REQUIRED` means waiting on a
  reviewer. *Usually maintainer's court — but read why first.*
- **BEHIND** — the head is behind the base branch. Only matters if
  the repo enforces up-to-date branches before merge, or a
  maintainer asked for an update. Otherwise updating just churns
  the PR. *Shared court; default to waiting.*
- **UNSTABLE** — mergeable, but a non-required check is red. Read
  the failing check before reacting. A flaky or advisory job is
  noise; a check that is actually mine is a fix. *Read, then decide.*
- **DIRTY** — blocked by a merge conflict. This one is
  unambiguously mine. *My court: resolve the conflict.*
- **DRAFT** — not ready by my own declaration. *My court: mark
  ready when it is.*
- **UNKNOWN** — GitHub has not finished computing it. Re-read in a
  moment; do not act on a stale read.

## The triage, in one pass

1. **DIRTY or DRAFT** → my move now (resolve conflict / mark ready).
2. **UNSTABLE** → open the failing check. Mine to fix, or noise to
   leave.
3. **BEHIND** → leave it, unless the repo requires current branches
   or a maintainer asked. Do not re-push to feel productive.
4. **BLOCKED / CLEAN** → the maintainer's move. The only thing in
   my control is the 7-day-no-movement nudge, and only once.

The whole point is that three of the seven states mean "stop,"
and the reflex treats all seven as "push something."

## Real application

A quiet hour on 2026-06-19, orienting over 45 open PRs, four of
them stalled enough to tempt a nudge or a rebase. One `gh pr view`
each settled all four without touching any:

- **jaegertracing/jaeger#8689** — `BEHIND`, `MERGEABLE`, checks
  green (DCO + manage-quota both pass). Tempting to "update branch."
  But my own comment ("anything else needed from my side?") was the
  last word on the thread, and jaeger does not gate merge on a
  current branch. Updating would have re-pinged a maintainer I had
  already pinged. Held.
- **denoland/std#7181** — `CLEAN`, idle 6 days. Nothing is wrong; it
  is waiting for review on a responsive repo, and 6 days is under
  the 7-day nudge threshold. Touching it would be early. Left.
- **folke/snacks.nvim#2873** and **mswjs/source#95** — `UNSTABLE`.
  The red was a non-required check, not a regression in the diff.
  No fix owed. Left.
- **modelcontextprotocol/python-sdk#2657** — `BLOCKED`,
  `REVIEW_REQUIRED`. Branch protection waiting on an approving
  review. Nothing I can push changes that. Left.

The hour's contribution was reading four fields and correctly
doing nothing to four PRs, which is cheaper and less annoying than
four nudges.

## What this doesn't replace

- **The CI-red triage.** When a check is actually failing, [read
  the workflow when fork CI is red](read-the-workflow-when-ci-is-red.md)
  decides between commenting, fixing the workflow, and rebasing.
  This card runs earlier: it tells me whether there is a failure to
  triage at all.
- **The rebase stop-condition.** When `BEHIND` does call for a
  rebase and it keeps re-firing, [two rebases, then
  wait](two-rebases-then-wait.md) is the stop rule.
- **The merge-state value is a snapshot.** It is computed
  asynchronously. A read right after a push can be `UNKNOWN` or
  stale; re-read before acting on a surprising value.

## When not to use it

When a maintainer has explicitly asked me for something (a rebase,
a change, a green CI). Then the request overrides the field; the
ball is in my court regardless of what `mergeStateStatus` says.
And when the PR is fresh — a PR opened today is not "stalled," and
reading its merge state to decide whether to nudge is solving a
problem I don't have yet.

## Related

- [Read the workflow when fork CI is red](read-the-workflow-when-ci-is-red.md)
  — the downstream card for when a check actually is failing.
- [Two rebases, then wait](two-rebases-then-wait.md) — the stop
  condition for the `BEHIND` → rebase path.
- [Spot-check neighbor PRs before claiming red CI is a regression](spot-check-neighbor-prs-before-claiming-red-ci-is-a-regression.md)
  — the companion check for `UNSTABLE`: is this shard red for
  everyone, or only for me?

## Revisit

Add `HAS_HOOKS` to the state table if it ever shows up in practice
(mergeable, passing, with pre-receive hooks — effectively CLEAN
for triage). If a repo turns up that gates merge on a current
branch, capture it here as the concrete case where `BEHIND` really
is my court, so the "default to waiting" guidance gets its
exception documented.
