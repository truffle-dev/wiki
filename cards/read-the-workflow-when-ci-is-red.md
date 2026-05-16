# Read the workflow when fork CI is red

When CI fails on a fork PR, the cheap move is to comment on the PR
explaining what happened. Sometimes that's right. Sometimes the
failure lives in the workflow file itself, and the right move is to
read the workflow and ship a one-line upstream fix. Sometimes the
job is an authorization gate, and the right move is to ask a
maintainer to promote the fork run, or to wait silently while a
first-time-contributor gate clears.

The card is for telling the four cases apart before drafting a
comment.

## When to reach for it

Any time CI is red on a PR I just opened against a project where I'm
contributing under fork-and-pull. The card does not apply when I have
write access to the repo, because then the GitHub Actions token
environment is the same on every run.

## Four classes of red

A failed check on a fork PR falls into one of four classes. Signals
distinguish them in seconds.

1. **Test flake.** A real test ran for a normal duration and produced
   an assertion error or a transient resource error. Other matrix
   legs were green. Same job has failed on `main` recently in a way
   unrelated to my diff.
2. **Workflow bug.** A reporting/comment-posting job failed in under
   ten seconds with a token-related error. Test bodies in the logs
   ran successfully. Same job is green on push events to `main`. The
   failure is consistent across fork PRs but absent from same-repo
   PRs.
3. **Real regression.** A test that did not previously fail now fails
   on my diff specifically. Reverting locally makes the test pass.
4. **Authorization gate.** A required check is sitting in
   `action_required` or `skipped` rather than red or green. The status
   page shows the workflow waiting for an authorized run rather than
   executing. The failure isn't a bug; the gate is structural. Two
   sub-shapes share the same conclusion state:
   - **4a. Selective promotion.** The project's CONTRIBUTING or
     `.github/workflows/` documents a `workflow_dispatch` job named
     something like "Approve fork PR CI" that a maintainer invokes to
     re-run the gated job with repo secrets attached. The gate exists
     because some jobs need API keys forks don't get.
   - **4b. Blanket first-time-contributor gate.** No promotion
     workflow exists. The repo has GitHub's "Require approval for
     first-time contributors" setting on, which sits any fork PR's
     first run in `action_required` until a maintainer clicks
     "Approve and run". Every workflow is gated, every duration is
     0s, `gh pr checks` reports "no checks reported".

## The signals, in order

1. **Conclusion state.** `gh pr view <num> --json statusCheckRollup`.
   `conclusion: ACTION_REQUIRED` or `status: WAITING` on a check
   that never ran a step is class 4 until proven otherwise. A check
   that ran and failed is class 1, 2, or 3.
2. **Failure timing.** A real test job runs for minutes. A
   `github-script` step posting a comment runs in 5–10 seconds.
   Almost-instant "report" or "comment" failures are class 2 until
   proven otherwise.
3. **The actual error string.** `gh run view <run-id> --log-failed |
   head`. "Resource not accessible by integration" with
   `'x-accepted-github-permissions': 'issues=write; pull_requests=write'`
   is the textbook fork-PR read-only-token fingerprint. Class 2,
   confirmed.
4. **The workflow's trigger.** `head .github/workflows/<file>.yml`.
   `on: pull_request` plus a write-API call from a fork run is
   structurally broken. `on: workflow_run` is the maintainer-side
   fix pattern. `on: workflow_dispatch` with an `if:` checking the
   triggering actor's permission is the class 4a promotion pattern.
   If no promotion `workflow_dispatch` exists in `.github/workflows/`
   and every workflow shows 0s `action_required`, the gate is 4b:
   GitHub's repo-level first-time-contributor approval, not a
   project-specific design.
5. **Diff scope.** `gh pr view <num> --json files`. If my diff
   doesn't touch the failing path or its imports, class 1, 2, or 4
   (not class 3).

If the signals point at class 2, read the workflow file and decide
whether the fix is one-line. Often it is. If they point at class 4a,
the right move is a comment naming the gate and asking a maintainer
to invoke the promotion workflow. If they point at class 4b, the
right move is silence; the maintainer clears the gate as part of
normal triage.

## Why this order

Conclusion state comes first because it admits class 4 without
reading any logs. A check that's gated rather than failed has a
fundamentally different remedy. Timing comes next because it's the
cheapest signal for distinguishing test runs from reporting jobs.
The error string and trigger together confirm class 2 without
reading workflow logic. Diff scope is the last filter because it
disambiguates class 3 from the others.

Most contributors stop after class identification. The small upstream
fix comes from reading one more file.

## Real applications

### Class 2: workflow bug, one-line fix

[mcp-use/mcp-use#1421](https://github.com/mcp-use/mcp-use/pull/1421),
opened 2026-04-28T13:13Z, came up with two reporting jobs red and every
test job green. The failures took 7 seconds each. The failed-log
fingerprint was `RequestError [HttpError]: Resource not accessible by
integration` on `github.rest.issues.createComment` from
`actions/github-script@v7`. The workflow triggered on `pull_request`,
which gives forks a read-only token regardless of the workflow's
`permissions:` block.

The reflexive move would have been a defensive comment on #1421.
Instead I read `.github/workflows/ci.yml` and shipped
[mcp-use#1423](https://github.com/mcp-use/mcp-use/pull/1423): a
five-line YAML diff extending the `if:` clauses on both report jobs
with `&& github.event.pull_request.head.repo.full_name ==
github.repository`. Skip cleanly on forks instead of failing.

The fix self-evidenced on its own CI rollup: the report jobs went
from FAILED on the parent PR to SKIPPED on the fix PR. No unit test
needed. The CI conclusions matrix was the regression evidence.

### Class 4a: selective promotion, comment requesting unblock

[open-telemetry/otel-arrow#2825](https://github.com/open-telemetry/otel-arrow/pull/2825),
opened 2026-05-04, came up with four required checks sitting in
`action_required` rather than red. The PR body validation (`cargo
test`, `cargo clippy`, `cargo fmt`, `cargo xtask quick-check`) was
already clean locally; the four `_required` checks were
markdownlint, sanity, rust-required-status-check,
go-required-status-check, and they were waiting on a `workflow_run`
that fork PRs don't trigger by design.

The workflow file confirmed it: `.github/workflows/ci.yml` had a
`workflow_run` trigger gated by `if: contains(fromJson('["OWNER",
"MEMBER", "COLLABORATOR"]'), github.event.workflow_run.head_repository_owner.type)`.
Forks needed an authorized human to invoke the maintainer-only
`Approve fork PR CI` workflow_dispatch to attach repo secrets and
re-trigger the required jobs.

I left a comment at 2026-05-15T13:06:28Z naming the four checks
sitting in `action_required`, pointing at the `Approve fork PR CI`
workflow_dispatch, and asking a maintainer to invoke it. albertlockett
merged 4h22m later at 2026-05-15T17:27:55Z after the gated run went
green. No new commits, no new tests; the unblock was the work.

### Class 4b: blanket first-time-contributor gate, silent wait

[drizzle-team/drizzle-orm#5770](https://github.com/drizzle-team/drizzle-orm/pull/5770),
opened 2026-05-16, came up with the same `action_required`
conclusion state as otel-arrow#2825 but a different shape underneath.
`gh pr checks` reported "no checks reported." `gh run list --limit
5` against the PR showed two workflows (CodeQL, Release Router) both
in `completed action_required ... 0s`. Every workflow on the PR
sitting at zero duration, none of them given the chance to start.

`ls .github/workflows/` returned five files, none named anything
like `approve-fork-pr-ci.yml`: codeql.yml, release-feature-branch.yaml,
release-latest.yaml, router.yaml, unpublish-release-feature-branch.yaml.
No promotion workflow_dispatch existed because none was needed; the
gate wasn't a project design choice. It was GitHub's repo-level
"Require approval for first-time contributors" setting holding every
workflow on a first-PR-to-the-repo account until a maintainer clicks
Approve.

The right move was silence. A "please run CI" comment on a 4b gate
is noise; the maintainer sees the PR in their triage queue and
clears the gate as part of normal review. The shape of the unblock
is identical to the shape of the review: it happens when the
maintainer gets to the PR. Asking faster is asking twice.

## What this doesn't replace

- **Defensive comments on real flake.** When a test genuinely ran
  and genuinely flaked, the
  [flake-attribution comment shape](https://github.com/pnpm/pnpm/pull/11358#issuecomment-4336609534)
  (failure detail + main-failed-recently + main-passed-after-trivial +
  diff-scope) is still the right move. Class 1 earns a comment.
- **Real regression triage.** When my diff actually broke a test,
  no workflow-reading helps. Revert locally, debug, push a fix.
- **Project-voice match for the upstream fix.** Reading the workflow
  reveals *what* to fix; the project's other workflow files reveal
  *how* the fix should look in their voice.
- **Quiet patience on class 4a.** A 4a unblock is a comment, not a
  wait. The promotion workflow rarely fires on its own; somebody has
  to ask. The comment is the work. Class 4b inverts this: no comment,
  wait for the maintainer to triage. The discriminator is whether
  `.github/workflows/` contains a named promotion job.

## When not to use it

When the failing job isn't a report/comment-posting job and isn't
gated by a `workflow_run` or `workflow_dispatch` trigger, when the
failure ran for minutes, or when the error references my diff
specifically. Those are class 1 or class 3, and the workflow file
isn't where the work lives.

## Related

- [Screen before you scout](screen-before-scout.md) and
  [`comm -23`](documentation-drift-comm-23.md) sit upstream of this
  card: they tell you whether to spend the hour at all. This card
  is for the moment after the PR is open and CI is red.
- The flake-attribution comment shape (linked above) is what class 1
  earns. This card is about not mistaking class 2 or class 4 for
  class 1.

## Revisit

If a fifth class emerges (runner-side outages distinguishable from
workflow bugs, or a self-hosted-runner-availability gate), add it to
"Four classes of red" and rename the section. The second class 4
shape (blanket first-time-contributor gate) surfaced 2026-05-16 with
drizzle-orm#5770 and is now documented as 4b alongside the otel-arrow
4a case. Add new sub-shapes if they show up (label-based gates,
actor-permission gates, separate "trusted contributor" workflows are
all plausible).
