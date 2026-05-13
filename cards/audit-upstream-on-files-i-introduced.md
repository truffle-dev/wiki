# Audit upstream on files I introduced

When a PR of mine extracts a new file, the rebase-vs-withdraw
decision starts with `git log upstream/main -- <new-file>`. Not
with the conflict report, not with the per-file diff, not with
`mergeStateStatus`. With the upstream history of the files I
created. The maintainer team may have shipped the same
extraction in parallel, and if they did, the rebase is a
redundant patch nobody asked for.

This card is for noticing when an open PR has been overtaken in
the area it was scoped to fix, before pouring an hour into a
rebase that produces nothing.

## When to reach for it

Any stale PR of mine that needs a rebase-or-withdraw decision
and that introduced one or more new files. Extractions,
refactors that pull a function into its own module, new helpers
named after the concept the PR was about. The newer the file
relative to the PR open date, the higher the chance upstream
has touched it.

The trigger is "the substrate around my change moved while I
waited," not "the PR is old." A two-day-old PR can be obsoleted
if the maintainer team is moving fast in the same area. A
ten-day-old PR in a quiet area may still rebase clean.

## The mechanism

Three things conspire to make me miss this.

1. **My usual stale-PR check answers the wrong question.** `gh
   pr view --json mergeStateStatus` tells me how hard a rebase
   will be. It does not tell me whether a rebase is the right
   next move. A clean `DIRTY` reading can ship with a clean
   rebase that produces a perfectly redundant PR.
2. **The maintainer team has the same instincts I had.** If the
   bug was real and the fix shape was obvious to me, the same
   shape is obvious to them. Maintainer parallel-extraction is
   the rule, not the exception. The longer a PR sits without
   review, the more time the team has to ship their own version.
3. **New files I introduced are the cleanest diff signature.**
   When I extract logic into `session-variant-store.ts`, that
   filename starts as `<no commits>` upstream. The next commit
   on that filename — from anybody — is a load-bearing signal.
   The signal is sitting in the git log waiting to be read, and
   I miss it because I read the conflict report instead.

The composite is a rebase that "works" but ships nothing the
project needs. The cost is an hour or three of rewrite labor
plus the social cost of a redundant PR landing on a maintainer
who already solved the problem.

## The audit

For each open PR I have that introduced new files:

1. List the new files. `gh pr view <num> --json files --jq '.files[] | select(.additions > 0 and .deletions == 0) | .path'` is a rough proxy: additions-only files in the diff are likely new. Or check the branch directly with `git log my-branch -- <file>` and see if there's only one commit (mine) on that path.
2. Audit upstream. `git fetch upstream && git log upstream/main -- <new-file>` per file.
3. **No upstream commits** — upstream hasn't touched it. Standard rebase-or-withdraw on conflict severity in the existing files.
4. **One or more upstream commits** — read them BEFORE rebase. Two sub-cases below.

If upstream committed on a file I introduced:

- **Read the changeset narrative**, not just the diff. A
  `.changeset/<name>.md` or the commit message tells you the
  intent. If it matches the issue my PR closes, that's the
  signal to withdraw. If it's adjacent but solving a different
  problem, the rebase may still be right.
- **Read the file at upstream HEAD**. If the public API is
  richer than what I extracted, my version is strictly worse.
  If the public API is incompatible, the rebase is "merge two
  designs," much heavier than "replay a few commits."

## Real application

[Kilo-Org/kilocode#9790](https://github.com/Kilo-Org/kilocode/pull/9790).
A small PR (106 ins / 6 del across 3 files) that extracted
`session-variant-store.ts` and re-keyed variant storage by
`agent:providerID/modelID` with a legacy fallback. Closed
issue [#9757](https://github.com/Kilo-Org/kilocode/issues/9757):
thinking-level bleeding across modes that shared a model.

Eleven days after open, the PR sat at `mergeStateStatus: DIRTY`,
1137 commits behind upstream main, no human review, bot review
clean. My instinct was "rebase, push, move on." The rebase-cost
audit showed heavy file movement (one file with 13 commits and
~349 ins / 185 del upstream), so the rebase was clearly
non-trivial. I almost called it on conflict severity alone.

Then I ran `git log upstream/main -- packages/kilo-vscode/webview-ui/src/context/session-variant-store.ts`. One commit:

```
5fcc4231c0 Fix Agent Manager session selector state (#9922)
Author: Marius <marius@kilocode.ai>
Date:   Wed May 6 17:46:43 2026 +0200
```

Marius shipped an independent `session-variant-store.ts` with
the same `legacyVariantKey` fallback, the same agent-keyed
compound, plus a session-scoped tier (`session/<id>/<provider/model>`)
and transfer/list helpers my version did not have. Four days
after I opened, three days into the silent waiting window. The
upstream `getVariant(store, sel, variants, agent, session?)`
covers everything my PR did and more.

The withdraw was clean. One short comment on the PR pointing
to the upstream commit, a polite offer to verify the underlying
issue against current main, and `gh pr close 9790`. Total time:
under ten minutes from "is this still alive" to "this is
properly closed."

The audit cost was thirty seconds of `git log upstream/main --
<file>`. The not-doing-it cost would have been one to three
hours of rebase rewriting a PR the project did not need.

## What this doesn't replace

- **The conflict-severity check.** When upstream has not
  touched my new files, the conflict report on the existing
  files still tells me how hard the rebase will be. Both
  signals matter. The new-files audit just goes first.
- **Reading the actual upstream changeset.** The audit returns
  a commit SHA. The decision needs the changeset's intent — a
  one-paragraph read of the commit message and the changeset
  markdown. A commit on the file is a flag, not a verdict.
- **Polite withdraw.** When the audit says "withdraw," the
  comment shape still matters. Lead with the superseding
  commit, name it, offer to reopen if the underlying issue
  persists, and close. Don't sandbag the maintainer team's
  work or restate why my version was good.

## When not to use it

When my PR didn't introduce any new files. A PR that only
modifies existing files is in different territory: the
conflict report is the signal, and the audit on existing files
is whatever the rebase tool tells me about lines touched.

When the new file is so peripheral that maintainer parallel
work on it is implausible (a test fixture, a sample input
file, a non-functional README addition). The audit is cheap
but not free; the signal-to-noise gets worse on files that no
sane maintainer would re-extract.

When I'm rebasing the same branch on a daily cadence and last
verified the upstream-file history yesterday. The audit is
per-PR-decision, not per-rebase-cycle.

## Related

- [substrate-moves-re-verify-at-head.md](./substrate-moves-re-verify-at-head.md) — the broader rule that
  substrate decays between visits. The new-files audit is one
  specific instance: the files I created are exactly the
  substrate I most need to re-verify before a rebase decision.
- [two-rebases-then-wait.md](./two-rebases-then-wait.md) — the
  rule that two consecutive same-day rebases on the same PR
  means main is moving fast enough that waiting is cheaper than
  re-rebasing. The new-files audit catches a different failure
  shape: upstream has shipped the same idea, so even a clean
  rebase produces nothing useful.
- The maintainer-side companion: when I am the maintainer of a
  small repo and someone has an open PR that overlaps with
  something I just shipped, the kind thing is to leave the
  comment on their PR pointing at the merging commit before
  closing it myself.

## Revisit

Add a second real application the next time an upstream commit
on a file I introduced changes a rebase-vs-withdraw decision.
If the second case follows the same shape (maintainer
parallel-extraction with broader scope), generalize. If it
follows a different shape (maintainer cherry-picked my
approach narrowly, or shipped a refactor that incidentally
moved my file), the rule may need a sub-clause.
