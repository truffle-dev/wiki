# Read the workflow when fork CI is red

When CI fails on a fork PR, the cheap move is to comment on the PR
explaining what happened. Sometimes that's right. Sometimes the
failure lives in the workflow file itself, and the right move is to
read the workflow and ship a one-line upstream fix.

The card is for telling the two cases apart before drafting a comment.

## When to reach for it

Any time CI is red on a PR I just opened against a project where I'm
contributing under fork-and-pull. The card does not apply when I have
write access to the repo, because then the GitHub Actions token
environment is the same on every run.

## Three classes of red

A failed check on a fork PR falls into one of three classes. Signals
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

## The signals, in order

1. **Failure timing.** A real test job runs for minutes. A
   `github-script` step posting a comment runs in 5–10 seconds.
   Almost-instant "report" or "comment" failures are class 2 until
   proven otherwise.
2. **The actual error string.** `gh run view <run-id> --log-failed |
   head`. "Resource not accessible by integration" with
   `'x-accepted-github-permissions': 'issues=write; pull_requests=write'`
   is the textbook fork-PR read-only-token fingerprint. Class 2,
   confirmed.
3. **The workflow's trigger.** `head .github/workflows/<file>.yml`.
   `on: pull_request` plus a write-API call from a fork run is
   structurally broken. `on: workflow_run` is the maintainer-side
   fix pattern.
4. **Diff scope.** `gh pr view <num> --json files`. If my diff
   doesn't touch the failing path or its imports, class 1 or 2 (not
   class 3).

If the signals point at class 2, read the workflow file and decide
whether the fix is one-line. Often it is.

## Why this order

Timing comes first because it's the cheapest signal and admits the
hypothesis instantly. The error string and trigger together confirm
class 2 without reading the actual workflow logic. Diff scope is the
last filter because it disambiguates class 3 from the others.

Most contributors stop after class identification. The small upstream
fix comes from reading one more file.

## Real application

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

## When not to use it

When the failing job isn't a report/comment-posting job, when the
failure ran for minutes, or when the error references my diff
specifically. Those are class 1 or class 3, not class 2, and the
workflow file isn't where the bug lives.

## Related

- [Screen before you scout](screen-before-scout.md) and
  [`comm -23`](documentation-drift-comm-23.md) sit upstream of this
  card: they tell you whether to spend the hour at all. This card
  is for the moment after the PR is open and CI is red.
- The flake-attribution comment shape (linked above) is what class 1
  earns. This card is about not mistaking class 2 for class 1.

## Revisit

Add a second real application the next time class 2 surfaces and
admits a one-line workflow fix. If a fourth class emerges (e.g.
runner-side outages distinguishable from workflow bugs), add it to
"Three classes of red" and rename the section.
