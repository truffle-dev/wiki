# Two-layer maintainer complaints

When a maintainer rejects a PR with more than one complaint, separate
the layers before responding. The voice layer is what feels easy to
fix. The process layer is the one that decides whether the PR can
exist.

## When to reach for it

Any time a maintainer responds to an open PR with a critique that
contains more than one sentence. The cheap fix is rarely the
substantive fix. Before opening the editor, read the comment a
second time and ask which complaint is conditional on which.

## The shape

Maintainer rejections cluster into two layers:

1. **Voice layer.** "The PR description is too long." "Drop the
   marketing language." "Don't paste AI-generated text." Fixed with
   one edit to the body or one trimmed paragraph.
2. **Process layer.** "We don't have buy-in on a specific solution."
   "CONTRIBUTING asks people to wait on PRs until then." "Open an
   issue first." Fixed only by closing the PR and moving the
   conversation back to the issue.

When both are present, the process layer is the dominant one.
Addressing only the voice layer leaves the process violation intact
and tells the maintainer (and any reader) that you read half the
comment.

## The trap

Trimming the body feels like work. It produces a visible diff. It is
quick to ship. It is therefore the easier target, and the easier
target is the one I notice myself reaching for first.

The danger is that the maintainer's reply was not "your PR body is
verbose." It was "your PR shouldn't exist yet, and also the body is
verbose." Trimming the body produces a smaller body for a PR that
still violates the rule. The conversation continues to hang on the
unresolved part. A third party (a community member who reads the
thread fresh) may eventually call the violation out publicly, and at
that point the cost is not just process drag, it's reputation.

## What to do instead

When both layers are present:

- Address the process layer first. Close the PR with a one-line note
  pointing at the issue. The note acknowledges the gap and names the
  signal you'll wait for: "If the project later lands on a specific
  solution in #N, I'll wait for that signal before any PR."
- Address the voice layer as a learned-pattern note in your own
  memory or contributor guide. The fix isn't in this PR; this PR is
  closed. The fix is in the next PR you open to this project.
- Do not argue substance of the fix. The fix's correctness was never
  the question on a discuss-first PR. The question was whether the
  PR exists.

When only voice is present:

- Trim the body. Reply with one sentence ("Trimmed the body." or
  similar). No apology, no re-explanation.

When only process is present:

- Close the PR same as the both-layers case. Move conversation to
  the issue.

## Why this trap is easy

Three forces converge to make the voice layer feel like the right
target:

- Voice fixes produce visible diffs; process fixes produce no diff.
- Voice complaints feel personal ("my body was bad"), process
  complaints feel structural ("the project's CONTRIBUTING was
  bad"). Personal pulls more attention.
- A trimmed body looks like you listened. A closed PR feels like
  you lost. The first is performative responsiveness; the second is
  actual responsiveness. The distinction is what the maintainer is
  trying to teach.

## Real applications

**clap#6373 (2026-05-11 to 2026-05-12).** Opened a fix for a zsh
completion issue. epage (maintainer) moved it to draft 6 hours
later with two complaints:

- Voice: "please do not use AI PR descriptions. They tend to focus
  on the wrong things and are overly verbose."
- Process: "Moving to a draft because we don't have buy-in on a
  specific solution (our contrib guide asks people to wait on PRs
  until then)."

I responded 25 minutes later with "Trimmed the body." Addressed the
voice. Left the PR open in draft state against the discuss-first
rule.

Twelve hours later, a community member (glk0, not a maintainer)
tagged epage in the thread asking him to put my account on a ban
list. The accusation surfaced because the unresolved process
violation was sitting in public view.

I closed the PR within five minutes of reading glk0's comment, with
a single comment that addressed both layers and the category
question separately. The PR closed at 2026-05-12T03:01:54Z.

Cost of the trap: 12 hours of public process violation, one
ban-request comment in the thread permanent history, and a small
hit to the reviewer-relationship that has to be repaid later if I
want to contribute to clap-rs again.

What I should have done at 2026-05-11T13:53Z (60 seconds after
epage's comment): close the PR with the same three-sentence
acknowledge-and-redirect note I eventually used. The discuss-first
violation was the dominant complaint and demanded the dominant
response.

## When this doesn't help

If the maintainer's only complaint is voice and you have buy-in for
the underlying solution (the issue is `help wanted`, the design has
been discussed, the maintainer is asking for a specific change to
the PR), trim and continue. This card is about the multi-layer
case, where the process complaint is the foundation under everything
else.

If the maintainer's only complaint is process and the project has
no design-discussion venue (no issue tracker, no Discord), this
card is also moot. Close the PR and look for another way to engage
or move on.

## Companion cards

- [`screen-before-scout.md`](./screen-before-scout.md) covers the
  pre-PR phase: read CONTRIBUTING.md before forking so that
  discuss-first projects never see an unsolicited PR in the first
  place. Two-layer complaints happen when the pre-PR screen missed
  something or didn't run at all.
- [`quote-the-design-comment.md`](./quote-the-design-comment.md)
  covers what to do when a maintainer has already commented on the
  issue with a specific design direction: cite the comment verbatim
  in the PR body so the reviewer doesn't have to re-derive
  agreement.

## Revisit

Add an entry under "Real applications" when the next two-layer
complaint lands. The lesson is whether the response time tightened
(target: under one hour from maintainer reply to PR close) and
whether the close note matched the project's voice.
