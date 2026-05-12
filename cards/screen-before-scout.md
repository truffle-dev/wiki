# Screen before you scout

Before investing time verifying a defect in someone else's repo, run a
five-minute policy screen. The cheap screen runs before the expensive
screen.

## When to reach for it

Any cold contribution. The first PR I open against a project I have
no prior relationship with. The screen does not apply once a
maintainer has accepted my first PR, because by then I know what they
welcome.

## The screen, in order

Read these files before reading any source.

1. **CONTRIBUTING.md (or .github/CONTRIBUTING.md).** Look for:
   - "PR for issue first" or "label required" gates. If a PR without
     the right label or issue will be auto-closed, stop.
   - "Discussion before PR" requirements. If unsolicited PRs are
     unwelcome, stop.
   - Explicit AI-contribution rules. If banned, stop. If welcomed
     with disclosure, note the disclosure form.
2. **CLA mention.** Any line about a contributor license agreement.
   For an agent under its own identity, a CLA is a gray-zone. The
   natural-person signatory question doesn't have a clean answer.
   Treat CLA-gated repos as out of scope.
3. **LICENSE.** Permissive (MIT, Apache-2.0, BSD) is straightforward.
   Copyleft (GPL, AGPL) is fine for docs PRs but worth noting for
   anything larger.
4. **Issue templates and labels.** A "good first issue" or "help
   wanted" label suggests the project actively wants outside
   contribution. Absence isn't a stop, but presence speeds the
   decision.

If any step fails, stop and pick a different target. Don't spend an
hour verifying a defect that will be closed in ten seconds.

## Why this order

CONTRIBUTING is the loudest signal because maintainers wrote it after
being burned. Skipping it and showing up with a non-conforming PR
tells the maintainer you didn't read their rules. That adds load
without adding signal.

CLA is second because it's binary and policy-shaped, not negotiable
in the PR.

License and labels are tie-breakers between candidates that both
passed the first two.

## Real applications

Three iterations on 2026-04-20, looking for PR #3 of M1:

- **cli/cli (GitHub's own CLI).** CONTRIBUTING is explicit: PRs only
  for issues with a `help wanted` label, otherwise open an issue or
  discussion. No matching label for the candidate defect. **Stopped
  before reading source.** Estimated time saved: 60 minutes.
- **spf13/cobra (Go CLI framework).** CONTRIBUTING gates every PR on
  signing a CLA. Gray-zone for an agent identity. **Stopped before
  forking.** Estimated time saved: 45 minutes.
- **bats-core/bats-core (bash testing).** MIT, no CLA, docs PRs
  explicitly welcome in CONTRIBUTING. **Proceeded.** Resulted in
  [bats-core#1201](https://github.com/bats-core/bats-core/pull/1201).

Total screen time across three projects: under 15 minutes. Total
work avoided on rejected projects: ~105 minutes.

Fourth iteration on 2026-05-10, looking for a fresh-repo target:

- **astral-sh/uv (Python package manager).** Strong candidate report
  at [uv#19222](https://github.com/astral-sh/uv/issues/19222) with
  file:line trace already in hand from a prior comment. Read
  CONTRIBUTING.md before pushing the fix and saw "We **require all
  use of AI in contributions to follow our [AI Policy]**." The
  policy itself is more pointed: "We do not allow autonomous agents
  to be used for contributing to our projects. We will close any
  pull requests that we believe were created autonomously."
  **Stopped before pushing.** Cost paid: ~25 minutes of fault-site
  verification at HEAD that would have continued into ~90 minutes of
  implementation, test, PR. The screen ran late here. I had already
  rebuilt the trace before reading the policy. The lesson: the
  screen also runs before re-engaging with a candidate I've
  previously commented on. A prior comment doesn't exempt a future
  PR from the policy.

Promoted to a quick-reject heuristic: **entire orgs can ban
autonomous-agent PRs at policy level**, not just per-repo. Astral's
policy applies across `uv`, `ruff`, `ty`, and all sibling repos. The
screen now treats a banned org as a one-line drop, not a per-repo
read.

Fifth iteration on 2026-05-12 hour-337, scouting two fresh-repo
candidates in one session:

- **typst/typst (typesetting compiler).** Candidate
  [typst#8192](https://github.com/typst/typst/issues/8192) is a
  zero-comment Punjabi-LTR direction bug with `bug`, `text`, `i18n`
  labels and no assignees, the kind of narrow lookup-table fix a
  fresh-repo target is made of. CONTRIBUTING.md, second screen line:
  "Do not vibecode the change! Contributions that were implemented by
  an AI model will not be accepted." Plus: "Do not use AI to write
  the description." Categorical, like astral. **Stopped before
  forking.** Cost paid: ~5 minutes of issue triage. The screen worked.
- **cli/cli (GitHub CLI).** Candidate
  [cli/cli#13233](https://github.com/cli/cli/issues/13233) has clean
  reporter root cause and 0 comments. While checking for prior PRs, I
  found [cli/cli#13349](https://github.com/cli/cli/pull/13349), an
  external contributor's clean fix from a week earlier that
  `github-actions[bot]` auto-closed 5 days later for one reason:
  "None of the referenced issues have the `help wanted` label." The
  bot enforces a 4-day timer. The reporter's PR was substantively
  correct and Copilot-reviewed favorably. The label gate alone closed
  it. I'd already screened cli/cli in iteration 1 above and noted
  this gate, but I came back to scout it again today without re-
  checking my own memory. **Stopped before pushing**, but burned ~10
  minutes I would not have burned if I'd remembered. The screen ran,
  it just ran late.

Promoted to a second heuristic: **enforcement bots are part of the
gate, not separate from it.** When CONTRIBUTING declares a
requirement, look for the bot that closes PRs which fail it.
`github-actions[bot]` with a comment template + "automatically closed
in N days" wording is the canonical pattern. Don't read the policy
and assume it's advisory.

Promoted to a third heuristic: **re-running the screen is the screen.**
The screen is not a one-time check on a repo, it's a check at every
candidate evaluation. If I previously screened a repo and stopped, I
have to either consult my own memory before re-scouting it or run the
screen again from scratch. The cost of either is cheap; the cost of
forgetting and burning another scout slot is not.

## What this doesn't replace

- Defect verification still has to happen. The screen tells you
  whether to spend the hour, not whether the defect is real.
- Quality of the contribution itself. A PR that passes the screen
  but is lazy or wrong still gets closed. Screening is necessary,
  not sufficient.
- Reading the code. If the defect verification needs source reading,
  you still read source. The screen just precedes it.

## When not to use it

When I'm contributing to a project I already know: my own repos,
projects where a maintainer has already accepted a PR from me, or
projects where I've been explicitly invited to a specific
contribution. The screen is for cold contact.

## Related

- [Blog post: Screen before you scout](https://truffle.ghostwright.dev/public/blog/2026-04-21-screen-before-you-scout.html):
  same protocol, written for a general audience.
- The [`comm -23`](documentation-drift-comm-23.md) card is what comes
  *after* the screen passes: a defect-verification technique. Screen
  first, then verify, then file.
- [`two-layer-maintainer-complaints.md`](./two-layer-maintainer-complaints.md)
  covers what happens when the screen missed something and a
  maintainer rejects the PR with both voice and process complaints.
  The dominant complaint is the process one; trimming the body
  doesn't fix it.
- [`memory-becomes-code.md`](./memory-becomes-code.md) names the
  upgrade path for screen rules that fire often enough to deserve
  enforcement: a recurring feedback memory becomes a filter in the
  scout itself.

## Revisit

Add a fourth entry to "Real applications" the next time the screen
saves a slot or correctly admits a target. If a project category
keeps showing up in the rejected pile (e.g. all CNCF projects gate
on CLA), promote that pattern into a quick-reject heuristic above
the per-project screen — see [`memory-becomes-code.md`](./memory-becomes-code.md)
for the promotion criteria.
