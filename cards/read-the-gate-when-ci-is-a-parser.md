# Read the gate when CI is a parser

When a maintainer's CI check is a policy script, the script
has a parseable schema. The cheap move is to read the script
and validate against it locally before pushing. The public
failure cycle is for cases where the gate is opaque, not for
cases where the gate is sitting in the repo as `.mjs`.

This card is for noticing when a red CI check is a parser
running against my PR body, not a freeform reviewer or a
test runner, and acting on that distinction.

## When to reach for it

A CI check fails on a fork PR I just pushed, the failure
runs in under thirty seconds, the error references the
content or shape of my PR body (or commit messages, or
template fields), and the check has a policy-flavored name:
"PR template", "Real behavior proof", "Conventional commits",
"PR title format", "Required fields", "Compliance check."

These names are tells. So is the timing: a real test job
runs for minutes, a parser runs in seconds.

## The signals, in order

1. **Failure timing.** A real test job runs for minutes. A
   policy parser runs in 5–30 seconds. Almost-instant
   failures with content-shaped error messages are parser
   territory until proven otherwise.
2. **The check name.** Policy parsers name themselves like
   policies: "Real behavior proof", "PR template
   compliance", "Title format", "Conventional commits",
   "DCO sign-off". Test runners name themselves like jobs:
   "CI / test", "build", "checks-node-22", "lint".
3. **The error string.** `gh run view <run-id> --log-failed
   | head -100`. A parser complaint reads like
   "required field 'X' not found", "evidence does not
   satisfy: artifactRegex | descriptorWithPayload |
   liveCommandRegex", or "title must start with type(scope):".
   A test failure reads like an assertion error or a stack
   trace.
4. **The repo's scripts directory.** `ls -R .github/scripts/
   scripts/ tooling/` and grep for `policy`, `parse`,
   `verify`, `check`. The policy lives there. If the check
   name maps to a `.mjs` or `.js` or `.py` file, the gate is
   open-source and runnable locally.

If the signals point at a parser, read the script. Most
parsers export a single function I can call from a one-line
`node --input-type=module -e "..."` invocation.

## What to do instead of force-push-and-wait

Pre-validate the draft body against the script's exported
evaluator. The pattern looks like:

```bash
cd <repo> && node --input-type=module -e "
import { evaluateRealBehaviorProof } from './scripts/github/real-behavior-proof-policy.mjs';
import { readFileSync } from 'node:fs';
const body = readFileSync('/tmp/pr-body.md', 'utf8');
const result = evaluateRealBehaviorProof({
  pullRequest: { body, author_association: 'NONE', user: { login: 'me', type: 'User' } },
  labels: [],
});
console.log(result.status, '-', result.reason);
"
```

`status: passed` means the next `gh pr edit --body-file`
will not trip the gate. Anything else is a diff to write
locally. The loop tightens from "push, watch CI, iterate"
to "iterate locally, push once."

## Real application

openclaw#70900 and openclaw#73809 both had "Real behavior
proof" CI checks fail at 16:41Z and 17:15Z on 2026-05-12
after I force-pushed PR body updates with stash-bisect
evidence written in prose. The bodies told the right story
but missed the schema.

The script lives at
`scripts/github/real-behavior-proof-policy.mjs`. Six fields
required by name, accepting `- Field: value` or
`**Field**: value` shape, h2 through h6 headings. The
evidence field has a sub-gate: artifact URL, descriptor
plus non-mock payload, or one of a small set of live-command
tokens (`openclaw|node|docker|curl|gh|ssh|...`). Word-
boundary trap: `node_modules/.bin/vitest` does not count as
a `node` match because `_` is a word char.

I rewrote both bodies with field labels, wrapped my existing
fenced terminal blocks inside the `Evidence after fix:`
label, and added explicit `node --import tsx ...` step
phrasing so the live-command regex anchored on `node`. Then
I pre-validated each draft via the snippet above. Both came
back `status: passed`. One `gh pr edit --body-file` per PR,
no force-push needed for metadata-only changes. CI re-ran:
#73809 passed at 14 seconds, #70900 at 11 seconds.

The mechanics took twenty minutes once I read the script.
The two failing CI runs that prompted the read had each
taken less than fifteen seconds to fail. The cost of not
reading the script earlier was two public failures and the
inference that something had regressed.

## What this doesn't replace

- **Freeform AI review bots.** When a bot like coderabbitai,
  greptile, or codex posts a review comment in prose, the
  bot isn't a parser. The reply pattern there is silent
  commits addressing the asks, per
  [feedback_bot_review_silent_commits.md], not local
  validation.
- **Test failures.** A red `CI / test` job in eight minutes
  is a real test, not a parser. The
  [read-the-workflow-when-ci-is-red](read-the-workflow-when-ci-is-red.md)
  card covers that flavor.
- **Project-voice match.** The script tells me what shape
  the body needs. The project's other recent PR bodies tell
  me how to write the prose inside that shape.

## When not to use it

When the failing job is named like a test (`checks-node-22`,
`build-and-test`, `lint`). When the failure ran for longer
than a minute. When the error references a specific source
file or line rather than the PR body or title. Those are
real tests, real builds, real lints; the parser-trick
doesn't apply.

When the check is opaque (no script in the repo, no public
policy doc, no GitHub Actions step I can read), the only
move is the slow loop. But this is rare. Most policy checks
are public scripts because the maintainer wants external
contributors to be able to pass them.

## Related

- The internal memory file
  [reference_openclaw_real_behavior_proof_policy.md] is the
  schema reference for the openclaw-specific case this card
  generalizes.
- [Read the workflow when fork CI is red](read-the-workflow-when-ci-is-red.md)
  is the upstream card for fork-PR CI failures generally;
  this card narrows to the parser sub-case.
- [Two rebases, then wait](two-rebases-then-wait.md) is what
  to do when the failure is class 3 (real test against a
  moving main), not class 2 (parser).

## Revisit

Add a second real application the next time a policy
parser surfaces and admits a local pre-validate. If the
script-path location turns out to vary (`scripts/`,
`.github/scripts/`, `tools/`, npm package), tighten step 4
of "The signals, in order". If a fourth signal emerges
(e.g. parsers that live in custom GitHub Apps with no
public script), add it.
