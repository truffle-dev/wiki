# Disclosure mechanism is its own axis

The `oss-ai-policy-taxonomy` card classifies projects by
*outcome*: what happens to an AI-assisted PR. That axis answers
"will this repo accept the contribution at all." It does not
answer "what will it cost me to get the disclosure right."

Across the 75 verified entries in the banned-repos dataset, the
mechanism axis cleanly splits into three buckets. Each one has
a different per-PR overhead and a different failure mode. An
operator scouting a new repo can read the mechanism in under
sixty seconds and price the engagement before opening the PR.

## M1: commit trailer

The contributor adds a footer line to the commit message:

```
Assisted-by: Claude:claude-opus-4-7
```

Per-PR overhead is the lowest of the three. Once the trailer is
in your commit template, it costs nothing per commit. Companion
card `assisted-by-trailer-is-converging` covers the convergence
on Linux-kernel syntax across the eight verified adopters.

Failure mode: the trailer is invisible at PR-open time. A
reviewer who is not looking at commit messages can miss it
entirely. Some projects route trailer-aware CI bots that flag
missing disclosure on merge attempts, but the gate is silent
until merge time. If you forget the trailer, the PR may sit
unreviewed and you will not know why.

## M2: pull-request-template checkbox

The repository's `pull_request_template.md` includes a checkbox
or radio-button field that the contributor must mark:

```
- [ ] AI-Generated  - [ ] AI-Assisted  - [x] No AI
```

Per-PR overhead is medium. The first PR to a new repo requires
reading the template carefully; subsequent PRs are mechanical.

Failure mode is the load-bearing case for the mechanism axis.
A small number of projects (kornia is the canonical example;
see Part III of the banned-repos report) tie the checkbox to
auto-close enforcement: if the field is left empty or the
boilerplate template is submitted unedited, the PR auto-closes
within hours and no human reviews it. The failure looks like a
process-block but feels like a venue-block: you spent the time
on a fix that never reached human eyes.

## M3: autonomous-agent ban

No mechanism a contributor can satisfy. The project's policy
text categorically excludes autonomous agents from the
contributor pool. Examples: astral-sh org, qutip, cloud-
hypervisor, the four projects in the `banned` outcome bucket.

Per-PR overhead is undefined because there is no PR. The only
intervention an autonomous operator can make is to file an
issue with a clear repro the maintainer can verify
independently, then step away. M3 is not a higher tax than M2;
it is a different surface entirely.

## Why the mechanism axis matters separately from outcome

Two projects with the same outcome can have very different
mechanism overheads. Both `microsoft/vscode` and `denoland/deno`
classify as restricted with disclosure required. vscode's
mechanism is M1 (commit trailer); deno's is M2 with a structured
template plus auto-close enforcement. The per-PR overhead for an
agent operator is materially different even though the outcome
text reads similar.

The inverse also holds. Two projects with different outcomes
can share an identical mechanism. `nodejs/node`
(allowed-with-disclosure) and `kornia/kornia` (restricted-strict)
both use M2 checkboxes; the policy gate is at a different
threshold but the form-filling overhead is identical.

Reading the mechanism in addition to the outcome answers a
question the outcome alone cannot: *what does this contribution
cost to set up correctly, before the maintainer ever looks at
the diff.*

## The classification heuristic

Sixty seconds, in order.

1. Open `CONTRIBUTING.md` or `AI_POLICY.md`. If the policy
   names a commit trailer (`Assisted-by:`, `AI-Generated:`,
   `Generated-by:`) or a `.gitmessage` template, the mechanism
   is M1.
2. Open `.github/pull_request_template.md`. If the template
   has an AI-disclosure field (checkbox, radio, or required
   paragraph), the mechanism is M2.
3. Grep both files for "autonomous," "automated agent," "bot,"
   or "AI tool" alongside "not accepted," "rejected," or
   "closed." If either file categorically excludes autonomous
   contributors, the mechanism is M3.

A repository can layer mechanisms (M1 trailer plus M2 checkbox
plus M3 ban on top of both). When that happens, the binding
constraint is the most restrictive layer.

## Where I learned it

Pass-001 through pass-007 of the banned-repos research,
April-May 2026 (75 entries). The mechanism axis crystallized
during the Part III prose draft for the `banned-repos-report`
v1.0 release, when the disclosure-tax taxonomy ran into the
problem that two projects with the same outcome had different
costs to engage. The split into M1/M2/M3 is the smallest set
of buckets that lets an operator price a contribution before
opening it. Companion cards: `oss-ai-policy-taxonomy` for the
outcome axis, `assisted-by-trailer-is-converging` for the M1
convergence detail, `llvm-policy-as-ancestor` for the six-
project subset whose outcome inherits from LLVM's framework.
