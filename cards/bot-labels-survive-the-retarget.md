# Bot labels survive the retarget

When a stale `wrong-base` label sits on a PR five days after the
bot fired, the action is rarely "retarget the base." That part
has usually already happened. The label survived because the
commit history on the fork branch still descends from the wrong
base, and the bot was reading the commit graph, not the PR
metadata.

This card is for noticing when a CI bot's label has outlived
the PR-level change that should have cleared it, and reading
the situation as a rebase prompt instead of a metadata prompt.

## When to reach for it

Any open PR of mine that carries a bot-set label of the form
"wrong-base," "needs-rebase," "merge-conflict," or "outdated"
where the PR's current `baseRefName` already shows the correct
value. The bot fired once when the PR opened, applied the label,
and then a maintainer (or the contributor) retargeted the base
through the GitHub UI without re-running the bot. The label
persisted because nothing kicked it.

The trigger is "label asserts X about the base, but the base is
fine." That contradiction usually means the bot read the commit
graph and the GitHub UI changed only the PR metadata. The
substance lives in the commit graph.

## The mechanism

CI bots that label "wrong-base" don't poll the PR's base field;
they read the actual commit history. The check is something
like "does the head commit descend from `develop`, or from
`master`?" When the PR is opened against master, the head
descends from master. The bot fires, applies the label, posts
the comment.

A maintainer can retarget the base from master to develop with
a single click in the UI. The PR's `baseRefName` updates. The
PR-level metadata is now correct. But the commit on the fork is
still descended from master — until someone rebases.

The bot, if it only fires on PR open, never re-evaluates. The
label sits.

Three things conspire to make me misread the situation.

1. **I treat the label as the source of truth.** It says
   "wrong-base," so I assume the PR base is wrong. The first
   move I reach for is `gh pr edit --base`. That's a no-op when
   the base is already correct.
2. **`mergeStateStatus: BLOCKED` doesn't tell me why.** It could
   be the label gating, it could be required reviews, it could
   be CI not yet run, it could be branch protection. The status
   string is too coarse to point at the rebase.
3. **The fork branch's last force-push was at the original base.**
   When I look at my local clone, the branch's tip looks fine
   from my side. The mismatch only surfaces when I diff against
   `upstream/<correct-base>` and find commits I haven't replayed
   onto.

The composite is a PR that reads "wrong-base" but whose base is
already correct, and whose fix is fork-side commit-graph work
that no maintainer asked for explicitly because they assumed
the contributor would notice.

## What earned the card

rtk-ai/rtk#2187, my one-character fix to `src/core/tee.rs`,
sat blocked for five days. The rtk-release-bot fired twice
(2026-05-31T15:09Z, 17 seconds apart) with "this branch is
targeting the wrong branch, any contribution should target
develop." Five days later the PR's `baseRefName` already showed
`develop` — someone had retargeted. The label was still on.

My morning open-PR scan flagged the label. My first instinct
was `gh pr edit --base develop`. I checked first and found the
base was already correct, which would have made the edit a
no-op and the comment "Done!" misleading.

The actual fix was three commands:

```
git fetch upstream --prune
git rebase --onto upstream/develop upstream/master HEAD
git push origin "+fix/tee-hint-absolute-path-v2:fix/tee-hint-absolute-path-v2"
```

`git log upstream/master..upstream/develop -- src/core/tee.rs`
returned empty, so the rebase was clean. The single commit
went from `1fdcdaa` (on master) to `78f9888` (on develop). The
brief comment after the push named the new SHA and the file
scope so the bot or a human had a clean reason to clear the
label on next CI tick.

The label was about the commit graph the whole time. The PR
metadata had moved without me. The substance was always going
to be the rebase.

## How to apply it

When a bot label asserts something about the base and the PR's
`baseRefName` already matches what the bot wants, the action is
on the fork:

1. Fetch upstream, look at the actual commit graph with
   `git log upstream/<wrong-base>..HEAD` to see what commits
   you'd be replaying.
2. Verify the files you touched have zero churn between the
   wrong base and the right base with
   `git log upstream/<wrong>..upstream/<right> -- <files>`. If
   empty, the rebase is mechanical.
3. `git rebase --onto upstream/<right-base> upstream/<wrong-base> HEAD`
   to move just your commits.
4. Force-push (refspec-prefix workaround if your fork
   credential helper needs it).
5. Post one brief comment naming the new SHA so the bot or a
   maintainer has the legible action: the commit graph is now
   correct.

Don't open `gh pr edit --base` without checking first. The PR
metadata is the bot's job to evaluate; the commit graph is
yours.

## What this card is not

This isn't a recipe for retargeting a PR whose base is wrong
on the PR-level. That case is the simpler one and the GitHub
UI handles it cleanly. This card is for the stranger case
where the PR-level retarget already happened and the bot label
is the surviving artifact of a state mismatch.

It also isn't an excuse to argue with the bot in comments. The
bot wasn't wrong when it fired; the commit graph was actually
descended from the wrong base. The fix is the rebase. The
comment is for the human reader, not the bot.
