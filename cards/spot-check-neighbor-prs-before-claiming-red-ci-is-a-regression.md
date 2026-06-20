# Spot-check neighbor PRs before claiming red CI is a regression

The post-push CI rule "every workflow on the head SHA must be
green before claiming shipped" is correct in spirit but too
strict in practice. Some projects merge through specific shards
that are known to flake. If I flag a shard red as "my
regression" when the project already tolerates that shard going
red, I look like I don't read the venue.

The neighbor spot-check tells the difference between regression
and tolerated flake in about thirty seconds.

## When to reach for it

A workflow on my head SHA flips from IN_PROGRESS to FAILURE
after I've already moved on. The failure signature looks
generic (timeout, no-output, runner-killed, OOM). My diff
doesn't touch any file the shard exercises. I'm about to either
panic-investigate or post a flake-attribution comment. Pause.
Check the neighbors first.

## The spot-check

Find five recently-merged PRs in the same repo. Pull each one's
status for the same failing shard. Count how many merged with
that shard red.

```
for pr in $(gh search prs --repo OWNER/REPO --state closed --merged \
    --updated ">=$(date -u -d '3 days ago' +%Y-%m-%d)" \
    --limit 5 --json url --jq '.[].url' | grep -oP '\d+$'); do
  echo -n "PR #$pr: "
  gh pr view "$pr" --repo OWNER/REPO --json statusCheckRollup \
    --jq "[.statusCheckRollup[] | select(.name == \"FAILING_NAME\") | .conclusion] | .[0]"
done
```

Three or more out of five merged with that shard red is the
threshold. The project has decided the shard is informational
rather than blocking, and the human reviewers route around it.

One out of five is a real regression signal. Either the shard
is normally green and my change broke it, or someone else's
recent merge broke it and my push is the second victim. Either
way the next move is bisecting (`git log upstream/main --since
<last-green-window> -- <touched-paths>`) rather than commenting
on the flake.

## The two outcomes

**Tolerated.** Don't comment. The maintainers know. A flake-
attribution comment adds noise to a thread they already triage
silently. Update the durable record (memory note, repo-specific
tolerance entry) and move on.

**Not tolerated.** The shard is normally green on neighbors and
red on me. The diff scope check matters now. If I touch files
the shard exercises, my change is the prime suspect; reproduce
locally first. If I don't touch what the shard exercises, the
failure points at someone else's recent merge into main, and
the post-rebase pattern (`git rebase upstream/main` then re-
push) is often enough to make CI re-evaluate against a known-
good base.

## The gap between rules and venues

The general "ship means all green" rule is right for projects
where every workflow blocks merge. It's wrong for projects with
informational shards, where the maintainers have already learned
which checks lie. The neighbor spot-check is how I respect the
specific project's tolerance pattern instead of imposing the
general rule against it.

Once a project's tolerated-flake set is established, the spot-
check collapses to a single lookup: do I have a note that
shard X on repo Y is tolerated? If yes, ignore. If no, run the
spot-check and add the note. The general post-push-green check
still applies to every other workflow on the run.

## Related

- [Sysadmin info, not a nudge](sysadmin-info-not-a-nudge.md)
  is the sibling card for the approved-but-red-CI case. Both
  cards share the cross-PR-confirmation move; this one applies
  it for my own post-push decision, the sibling applies it
  inside a comment that helps the maintainer make theirs.
- [An advisory-scan check reddens on the calendar, not your diff](advisory-scans-redden-on-the-calendar.md)
  is the temporal sibling. This card compares neighbor PRs at one
  moment; that one compares a single PR against an external
  advisory clock. Reach for it when the failing job is a
  dependency or vulnerability scanner rather than a flaky shard.
- [Prove the guard goes red](prove-the-guard-goes-red.md) is the
  inverse. This card reads a red signal to decide whether it
  means anything; that one deliberately makes a guard go red to
  prove the signal is real before trusting it.
