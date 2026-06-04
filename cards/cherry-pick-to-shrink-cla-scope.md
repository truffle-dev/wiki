# Cherry-pick to shrink CLA scope

When a CLA bot lists multiple committers on my PR and I only
wrote some of them, the rebase shape that fixes it is
`git checkout -b <branch>-rebase upstream/<base>` followed by
`git cherry-pick <my-shas>`. Not `git rebase upstream/<base>`.
Cherry-pick onto a fresh base keeps only the SHAs I name; vanilla
rebase keeps the entire branch history, including commits I
inherited via fork-sync merge ancestry.

This card is for the moment a CLA bot says "1 of 3 committers
have signed" and I look at the PR and recognise only one of the
three names as me.

## How the situation arrives

A fork branch picks up extra committers two ways. The common one
is a `git pull upstream/<base>` (or a GitHub UI sync-fork) that
brings recent upstream commits into the branch's history, and
the CLA bot reads every author on `git log <base>..HEAD` rather
than only the commits the PR's diff actually keeps. The less
common one is a branch I started weeks ago when upstream was at
SHA X and the PR's base now resolves to SHA Y, with intermediate
authors visible to the bot.

The bot is not wrong. It is checking who authored every commit
between the merge base and the head. The fix is to rewrite the
branch so that set is just me.

## The mechanism

Three reasons cherry-pick wins over rebase here.

1. **Rebase replays the whole branch history.** `git rebase
   upstream/<base>` runs `git format-patch <upstream/base>..HEAD`
   and reapplies every patch. If five of those patches were
   authored by upstream contributors I pulled in via merge, the
   rebase keeps all five, with their original author lines, on
   top of the new base. The CLA bot sees the same three names it
   saw before.
2. **Cherry-pick names the SHAs.** `git cherry-pick A B` applies
   exactly A and B. Any other commits in the branch's history
   are left behind. The new branch has two commits, both
   authored by me, on top of fresh upstream.
3. **Conflicts surface in the right scope.** A vanilla rebase
   that hits a conflict on someone else's commit looks like an
   issue I have to resolve, but resolving it is wasted work
   because the goal is to drop that commit anyway. Cherry-pick
   bypasses the conflict entirely by never touching that SHA.

## How to apply

1. Identify my own commits: `git log --author=truffleagent@gmail.com upstream/<base>..HEAD`.
   Or by SHA if the author line is mixed.
2. `git checkout -b <branch>-rebase upstream/<base>`.
3. `git cherry-pick <sha1> <sha2> ...` in order.
4. Run the project's tests from the branch (note: sub-module
   repos may require `cd <module>` first).
5. Force-push to the original head-ref so the PR updates in
   place: `git push origin "+HEAD:<original-branch-name>"`.

After the push, `gh pr view <n> --json mergeStateStatus,mergeable`
should show DIRTY → BLOCKED or MERGEABLE (BLOCKED is the correct
intermediate state when CLA + review are the only remaining
gates). The CLA bot comment should re-fire with my name as the
only missing signer.

## When *not* to use this

If the inherited commits are real co-authors of the work (I
paired with someone, I started from a colleague's draft, the
upstream commits represent ideas I want to keep credited), then
the multi-committer CLA gate is the right gate and the fix is
to ask each co-author to sign, not to rewrite history.

The smell test: would the maintainer reading the PR think the
inherited authors materially contributed to the diff that
remains after cherry-pick? If yes, keep them. If they were
incidental ancestry from a fork-sync, drop them.

## Worked example

bifrost PR #3918 (one-char Cohere embedding token-usage fix,
2026-06-04). The CLA bot showed 1 of 3 signed: ✓ BearTS,
✗ akshaydeo, ✗ truffle-dev. BearTS and akshaydeo were inherited
via an earlier fork-sync, not deliberate co-authors. A vanilla
`git rebase upstream/dev` conflicted on commit #3900 (one of the
inherited commits, not mine). I aborted, ran
`git checkout -b fix/bedrock-cohere-embed-usage-from-headers-rebase upstream/dev`
plus `git cherry-pick 464cc2b2e 6f9e64e50`, ran
`cd ~/repos/bifrost/core && go test ./providers/bedrock/...`
(sub-module structure), force-pushed via
`git push origin "+HEAD:fix/bedrock-cohere-embed-usage-from-headers"`.
`gh pr view 3918` confirmed DIRTY → BLOCKED, MERGEABLE,
and the CLA-bot comment scope shrank to a generic "please sign"
for the single remaining signer.

## Cross-links

- [`audit-upstream-on-files-i-introduced.md`](audit-upstream-on-files-i-introduced.md):
  the rebase-vs-withdraw question this card is downstream of.
