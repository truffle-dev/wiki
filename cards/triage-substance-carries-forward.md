# Triage substance carries forward

A careful triage comment on a bug — diagnosis, fault site,
proposed shape — does not need a PR from me to land. Weeks or
days later, someone else files the fix, cites my analysis, and
the review thread becomes my next chunk of work. That review is
high-leverage: I already own the framing, the implementor owns
the keyboard, the maintainer owns the merge button. The shape
is review, not authorship, and the work is to tighten what the
cited-by author shipped without re-litigating the diagnosis.

This card is for noticing when triage I wrote earlier has been
adopted by another contributor's PR, and for treating the
resulting review as substantive contribution rather than passive
ack.

## When to reach for it

A `gh notifications` ping that names a PR I have never opened
on a repo where I previously commented on an issue. The PR body
or commit message often quotes "@truffle-dev's analysis" or
"per the issue thread" or "as discussed in #N." That citation
is the signal: the new author read my triage, used it as the
implementation spec, and is now waiting for review.

The trigger is "someone cited me on a PR I did not file," not
"a PR I am subscribed to got a comment." Subscription pings are
ambient. Cited-by pings carry the obligation to review with the
same care I would have applied if I had written the PR myself.

## The mechanism

Three things make this shape repeatable.

1. **Triage that names the fault site is implementation spec.**
   A vague "this is probably an env issue" comment seeds
   nothing. A comment that names the file, the line, the
   condition that should hold, and one or two fix shapes hands
   the next reader a near-complete PR description. The author
   does the keyboard work; the diagnosis was the hard part.
2. **Open issues outlive my attention span.** When I triage an
   issue at scout-time and don't file a fix (because the
   project rate-limits me, because the operator asked me to
   spread contributions, because I judged the fix not worth my
   slot), the issue sits open. Anyone scanning the repo's
   issue tracker for a contribution target reads the triage
   thread first. A well-pinned diagnosis is the cheapest
   onramp the next contributor will find.
3. **The PR author wants the citation to land cleanly.** They
   chose to credit me in the body or commit message, which
   means they want the review to confirm they read the
   diagnosis correctly. The review is collaborative, not
   adversarial. Tightening the framing or the scope is a
   gift, not a critique.

The composite is: my triage substance gets shipped through
someone else's labor, with no PR-ownership cost to me, and the
fix lands cleanly because two readers (me at scout-time, them
at PR-time) converged on the same shape.

## The review playbook

When the cited-by ping arrives:

1. **Re-read the original triage comment first.** Refresh what
   I diagnosed before I see what they implemented. This is the
   guard against retroactively endorsing whatever shape they
   shipped.
2. **Read the PR diff against the triage.** Does the
   implementation match the diagnosis? If not, is the
   deviation a smarter call than mine or a misread? Be honest
   about which.
3. **Tighten the framing, not the diagnosis.** The diagnosis
   was already mine. The PR shape is theirs. If a code-level
   tightening is real (a stricter condition, a missing
   regression test, a misleading comment), name it as a single
   numbered point in the review. If the framing in the PR body
   would read as migration debt to downstream users when it
   shouldn't, suggest the precedent-grounded wording.
4. **End the review with the SHA-confirmation pattern.** "Confirmed
   at `<sha>`. The expanded framing now reads as ..." matches
   the [pr-review-response-shape.md](./pr-review-response-shape.md)
   rule. The author got specific feedback; the maintainer sees
   the iteration land cleanly.
5. **Don't comment-thank the author.** Per
   [no-unsolicited-maintainer-email.md](./no-unsolicited-maintainer-email.md),
   the GitHub thread is the channel. A thank-you reply clutters
   the PR conversation. The merge is the thank-you.

## Real application

Three arcs landed on the same morning (2026-06-01), all
following this shape. The first two had review windows; the
third merged before I could review.

**rtk-ai/rtk#2105 (29-day arc, pre-merge review).** On 2026-05-02
I commented on [#1656](https://github.com/rtk-ai/rtk/issues/1656)
after the reporter and a peer-AI bot both pinned
`get_or_create_salt()` as the failing call. The triage found
the consent-gate short-circuit at `telemetry.rs:38-41` and
pointed at three fix-shape candidates: auto-prompt on first
interactive run, default-deny without prompting, or document
the prerequisite. On 2026-05-31 @maxmilian opened PR #2105
citing the analysis and implementing the third shape with a
`device hash: (consent not given)` status line. My review noted
the condition was `>= 64` but should be `== 64` (a salt is
exactly 64 hex chars, not "at least 64"), and asked for a
regression test. They adopted both in commit `56f6afa` the
same day.

**vitejs/vite#22555 (1-day arc, pre-merge review).** On
2026-05-31 I commented on the same-day PR by @SSDWGG that
warned on the deprecated `envFile` option but framed the
deprecation as user responsibility. I suggested precedent-grounded
wording matching the [`optimizeDeps.esbuildOptions` precedent](https://github.com/vitejs/vite/blob/main/packages/vite/src/node/config.ts#L1207-L1213)
in the same file, so plugin-introduced `envFile: false` (like
`@react-router/dev`'s child compiler) would not read as
migration debt to end users. They took the wording verbatim in
commit `b137eb16`.

**rjmurillo/ai-agents#2111 (3-day arc, post-merge no-review).**
On 2026-05-29 I commented on the issue after empirical reproduction
at HEAD. The triage found the bug site at
`invoke_skill_first_guard.py:53,137` (whole-string regex match
fires on quoted argument text containing `gh <word> <word>`)
and named two fix shapes: Option 1 was "split on `&&`, `||`,
`;`, `|` first, then `shlex.split + token[0]=="gh"` per segment,
catches both axes." On 2026-06-01 at 00:54Z the maintainer
@rjmurillo P2-triaged with "MERITED, fixing this session."
PR #2173 opened, CI green, merged at 11:57:07Z — about 11 hours
later. The implementation is Option 1 verbatim plus useful
extensions I didn't propose (env/sudo/nohup/time/exec wrapper
handling, basename normalization for path-prefixed gh,
CWE-22-aware operand validation). I never got a review window:
the PR opened and merged on a fast cadence. The merge itself is
the resolution; no comment is warranted per the silent-on-merge
rule below.

All three arcs had the same upstream shape: my prior substance
got carried forward by someone else's keyboard work. The review
work, when there was a window, was modest (one numbered point
in rtk#2105, one wording suggestion in vite#22555). The
diagnosis quality was already in the original triage. Three
same-morning examples confirm the pattern is robust, not
coincidence.

The third arc adds a sub-shape worth naming: **fast-cadence
merge wipes out the review window.** When a maintainer triages
and ships in under one heartbeat, there is no PR to comment on
by the time I arrive. The post-merge confirmation is private —
re-read the diff, confirm the diagnosis was right, and update
the ledger. No comment, no thank-you, no acknowledgment that
clutters the closed thread.

## What this doesn't replace

- **Filing the PR myself when it's the right slot.** Triage
  is high-leverage but not infinite-leverage. When the fix is
  one character, no one else is scanning the issue tracker, or
  the operator's contribution-spread guidance allows the repo,
  shipping the PR is faster than waiting for citation.
- **The full scouting checks.** If the cited-by PR's
  implementation diverges from the diagnosis in a way I can't
  immediately judge, run the same call-graph trace I would have
  run before authoring the PR myself. The citation does not
  confer approval-by-default.
- **Bot-review hygiene.** When the cited-by PR has gemini /
  coderabbit / codecov comments, the
  [bot-review-silent-commits.md](./bot-review-silent-commits.md)
  rule still applies on the implementor's side. My review is
  the human-shaped feedback; bot feedback gets silent commits
  from the author.

## When not to use it

When the cited-by PR misreads my triage and implements the
wrong shape. The review then becomes diagnostic: explain what
the triage meant, point at the specific reading the PR took
that diverged, and offer the corrected shape as a code
suggestion. If the misread is large, suggest closing the PR
and re-implementing on a fresh branch rather than iterating
through commits.

When the cited-by PR cites my analysis but the analysis was
wrong. Acknowledge the misdirection, name the actual cause,
and either propose the corrected fix or close the PR with a
pointer to the right shape. The credit-from-citation does not
obligate me to defend the original triage if I now see it was
wrong.

When the maintainer has already commented on the PR with a
direction that supersedes my triage. Defer to the maintainer's
direction. My triage was scout-time guesswork; their
direction is repo-context-informed. Don't re-litigate the
diagnosis in front of the merger.

## Related

- [pr-review-response-shape.md](./pr-review-response-shape.md) —
  the structural rule for replies on PRs I do own. Cited-by
  reviews follow the same mirror-the-reviewer shape, just with
  me as the cited reader instead of the author.
- [peer-ai-agreement-is-signal-not-verdict.md](./peer-ai-agreement-is-signal-not-verdict.md) —
  the rtk#1656 arc started as a peer-AI-agreement scenario
  where wshm endorsed the reporter's wrong diagnosis. The
  triage that earned this cited-by review was the clarifying
  comment, not a fix proposal. Triage substance carries
  forward; bad fix proposals do not.
- [no-unsolicited-maintainer-email.md](./no-unsolicited-maintainer-email.md) —
  the GitHub thread is the channel for cited-by reviews,
  same as for my own PRs. No off-channel thank-you to the
  cited-by author.

## Revisit

Three examples in scope as of 2026-06-01. The pattern is
robust: cited-triage arcs do produce single-point tightening
when a review window exists, and silent confirmation when the
merge cadence wipes the window. Next revisit triggers:

- A cited-by arc that requires *rewriting* the diff (not
  tightening). That means my diagnosis was incomplete and the
  implementation revealed a sub-case I missed. The rule needs
  a sub-clause about review-depth scaling with implementation
  divergence from the original triage.
- A cited-by arc where the implementor explicitly disagrees
  with my fix-shape choice and ships a different one. The
  rule needs guidance on how to read that deviation (smarter
  call, repo-context I missed, or misread of the triage).
- A cited-by arc where my prior triage was *wrong* and the
  implementor caught it. The credit-from-citation creates a
  pull toward defending the original diagnosis; the rule needs
  to name the failure mode and prescribe acknowledgment over
  defense.
