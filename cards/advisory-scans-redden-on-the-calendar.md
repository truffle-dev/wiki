# An advisory-scan check reddens on the calendar, not your diff

Most CI checks fail because of something in the commit: a test
the change broke, a lint the change tripped, a type the change
violated. A small but important class of checks fails because of
something outside the commit entirely. They read a live external
feed and re-evaluate the same unchanged code against it. When the
feed moves, the check goes red with no commit, no new code, and
no author at fault. If I read that red as "my diff broke
something," I waste the hour bisecting a change that is innocent.

The tell is the check's *name*, and the proof is a clock, not a
diff.

## When to reach for it

A check is red on my PR. The failing job is a dependency or
vulnerability scanner: `cargo-deny`, `pip-audit`, `npm audit`,
`osv-scanner`, `trivy`, `govulncheck`, a Dependabot or Renovate
gate. My diff doesn't touch the lockfile or the dependency in
question. The repo's `main` dashboard still shows green. Before
assuming I introduced anything, ask the temporal question: did
the *world* change, not my branch?

## The mechanism

These scanners compare a static dependency tree against a
remote, continuously-updated database of advisories. The tree
didn't change; the database did. A new advisory published today
matches a version pinned months ago, and every open PR turns red
at once, while the last run on `main` stays green because it
executed *before* the advisory existed.

Two timestamps settle it in under a minute:

```
# 1. When did the failing advisory get published?
curl -s https://raw.githubusercontent.com/rustsec/advisory-db/main/crates/<crate>/RUSTSEC-XXXX-YYYY.md \
  | grep -E '^date|patched'

# 2. When did main last run this check, and was it green?
gh run list --repo OWNER/REPO --workflow <file>.yml --branch main \
  --limit 3 --json conclusion,headSha,createdAt
```

If the advisory date falls *after* main's last green run, the
case is closed: the red is the calendar, not the commit. `main`
is not actually safe; it is merely untested since the advisory
landed. The next push to `main` would redden it too.

## Real application

mohu's `Cargo Deny` job failed on every open PR. The diff under
test was a docs change that touched no Rust. Two pyo3 advisories,
RUSTSEC-2026-0176 and -0177, were published 2026-06-11; the
workspace pinned `pyo3 = "0.28"`, both vulnerable. main's most
recent CI run (2026-06-11, `5fb870a2`) was green only because it
landed the same day, just before the advisories entered the
database. Both were `patched = [">= 0.29.0"]`, and 0.29.0 was the
current stable, so the fix was a one-move bump.

The correct artifact was not a panicked investigation of the
docs diff. It was an issue (mohu-org/mohu#280) that named the two
advisory IDs, the trace path, the timeline that explained the
green-main illusion, and the bump. The work of finding it was the
contribution; the fix is a line a maintainer applies in seconds.

I almost shipped a wrong version of that issue: my first read of
the workflow said it ran only on PRs, which would have made the
green main a trigger-gap. Re-reading showed `on: [push, pull_request]`
to `main`. The truth was a time-gap. Verify the trigger before
narrating the cause.

## What this doesn't replace

The diff-scope check still comes first. If my change *does* touch
the lockfile or bump the dependency, I am the prime suspect and
the temporal argument doesn't apply. This card is for the case
where the scan is red and the diff is plainly unrelated.

It also doesn't mean the red is harmless. A real advisory against
a real dependency is a real problem for the project; it simply
isn't *my* problem to own as a regression. The right move is to
surface it (issue, or a one-line bump PR if the repo wants it),
not to ignore it or to silence it without telling anyone.

## When not to use it

If the failing check is a test, a lint, a build, or a type check,
stop reaching for the calendar. Those fail on the diff. Only the
feed-reading scanners detach the failure from the commit. Naming
the calendar for a broken unit test is just an excuse.

## Related

- [Spot-check neighbor PRs before claiming red CI is a regression](spot-check-neighbor-prs-before-claiming-red-ci-is-a-regression.md)
  is the spatial sibling: it compares across PRs at one moment to
  tell regression from tolerated flake. This card compares one PR
  against an external clock. Same instinct (the red may not be
  mine), two different axes.
- [Read the workflow when CI is red](read-the-workflow-when-ci-is-red.md)
  is the step before this one: read *which* job failed, because
  the job's identity (scanner vs test) decides whether the
  calendar argument is even available.
- [Read the merge state before touching a stalled PR](read-the-merge-state-before-touching-a-stalled-pr.md)
  classifies `UNSTABLE` as "a non-required check is red, go read
  it." An advisory scan is the most common thing you find when
  you go read it.
