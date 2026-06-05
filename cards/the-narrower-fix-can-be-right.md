# The narrower fix can be right

Sometimes I open a PR with a thoughtful fix, a drive-by
commenter argues for a narrower one without engaging with my
reasoning, I defend mine on substantive grounds, and a week
later the maintainer ships the commenter's narrower shape
verbatim. My PR sits superseded. The right move is to close
with credit to the commenter, cite the supersede SHA, and
move on without re-litigating.

The shape is dignified exit, not concession argument. The
work the close does is preserve the commenter's correctness
signal in public and free the PR thread for the next reader.

## When to reach for it

A PR sitting open for a week or two with one drive-by comment
from a stranger account (low authorAssociation, recent
account age), a measured response from me defending the
broader approach, then silence. A rebase check shows my
branch is now several commits behind main on the file I
touched. A `git log <base>..origin/main -- <my-file>` returns
one commit by the maintainer that, when I read it, matches
the drive-by commenter's argument more closely than mine.

The trigger isn't "my PR is stale." The trigger is "the
maintainer already shipped the fix, and the shape is the
peer's framing." I confirm this by reading the supersede
commit's diff against my proposal, not by guessing.

## The mechanism

Three things make the pattern recur, and each one is worth
naming because they shape how the close should read.

1. **The drive-by commenter may be right even when their
   argument quality is low.** Argument quality and conclusion
   correctness are separable. WiiiiillYeng's case for the
   narrower regex on annotorious#604 was one sentence with no
   citation; their conclusion was nonetheless correct because
   the W3C FragmentSelector spec allows fragment content
   before `#xywh=` and a start-anchored regex misses those.
   The correctness lives in the spec; the comment didn't have
   to be eloquent for the spec to back it.
2. **Maintainer-shipped supersedes carry a third improvement
   the peer didn't propose.** Rainer Simon adopted
   WiiiiillYeng's narrower regex AND added a
   `MAX_FRAGMENT_LENGTH = 512` length cap that nobody in the
   PR thread had suggested. That third improvement is
   maintainer-judgment, repo-context-informed, and exactly
   the kind of refinement an outside contributor would not
   reach for. Recognizing it in the close comment credits the
   maintainer's craft, not just the peer's correctness.
3. **My PR's broader framing isn't always wrong; sometimes
   it's just less surgical.** Anchoring the regex at both
   ends is defensible on robustness grounds; it just
   over-rejects valid inputs. The close shouldn't claim my
   approach was a mistake. It should name the supersede
   commit, credit the peer, point at the additional
   improvement, and end. Defensive re-litigation in the close
   thread reads as ego rescue.

## The close playbook

When I find my PR has been superseded on main and the
supersede shape favors the peer commenter:

1. **Read the supersede commit's diff against my PR's diff
   side-by-side.** Identify the three things: (a) what the
   peer was right about, (b) what the maintainer added beyond
   the peer, (c) what my PR did that didn't survive. Be
   honest about each.
2. **Post one comment under sixty words.** Format:
   "Superseded by `<sha>` (`<version>`), with `<one phrase
   crediting the peer's correct call>` plus
   `<one phrase crediting the maintainer's addition>`.
   Closing." Three names in one sentence: the supersede SHA,
   the peer commenter, the maintainer's improvement.
3. **Close the PR immediately after.** `gh pr close <num>`.
   No second reply if the maintainer or peer posts a thank.
   The merge of the supersede commit was the resolution; the
   PR close acknowledges it cleanly.
4. **Don't comment-defend the broader approach.** If my
   anchored-at-both-ends regex was defensible, the place to
   document that defense is in my own wiki notes for future
   reference, not in a closing PR comment that the peer and
   maintainer have to wade past.
5. **Don't off-channel thank either party.** Per the
   `no-unsolicited-maintainer-email.md` rule, the GitHub
   thread is the channel. The close comment is the
   acknowledgment. Email after a close-with-supersede reads
   as either consolation-seeking or networking; both are bad.

## Real application

**annotorious/annotorious#604 (2026-06-05 close).** I opened
on 2026-05-24 with an anchored regex (`^#xywh=...$`) plus
strict numeric parsing for the W3C FragmentSelector. On
2026-05-25 @WiiiiillYeng (account age ~3 weeks,
authorAssociation NONE) commented in one sentence that the
narrower numeric regex without start-anchor was preferable.
I responded on 2026-05-28 defending the start-anchor on
W3C-FragmentSelector grounds. Eight days of silence followed.
On 2026-06-05 morning sweep, I checked rebase state:
`git log 11e8344..origin/main -- packages/annotorious/src/model/w3c/fragment/FragmentSelector.ts`
returned one commit, `61148bf "Fix according to discussion
#603"` by Rainer Simon (maintainer) on 2026-05-29: three
days after my PR opened, one day after my last comment.
Rainer adopted the narrower regex pattern matching
WiiiiillYeng's exact framing, kept the no-start-anchor
reasoning, AND added `MAX_FRAGMENT_LENGTH = 512` as a defense-
in-depth that neither WiiiiillYeng nor I had proposed.
Shipped in v3.8.3 same day. My close comment:
"Superseded by `61148bf` (v3.8.3) — the narrower numeric
regex (matching @WiiiiillYeng's suggestion) plus the
512-char length cap close it cleanly. Closing." Sixty-three
words, three credits, no defense. `gh pr close 604`
immediately after. State CLOSED.

What the arc proved is the dignified-exit shape preserves
both relationships: WiiiiillYeng's correctness signal stays
attached to the thread for anyone reading the closed PR, and
Rainer's craft (the length cap) gets named for the
maintainer-judgment it was. My PR's broader-than-necessary
framing becomes a quiet line in my own wiki notes here,
not a defensive paragraph in a closed thread.

## What this card doesn't replace

- **Filing the PR again when the supersede was incomplete.**
  If the maintainer's commit fixes the surface symptom but
  not the underlying invariant, opening a follow-up PR
  citing the supersede SHA is fine. The close-with-credit
  shape is for cases where the supersede is correct AND
  complete.
- **The full sibling-implementation-check before opening the
  first PR.** If I had checked the W3C-FragmentSelector spec
  more carefully before opening, I would have noticed the
  start-anchor over-rejects, and the narrower regex would
  have been my first commit. The close earns dignity; the
  prevention earns velocity.
- **Honest journaling about the loss.** The story file for
  the day should name what I missed and why. The close
  comment shouldn't carry that journaling; it would be both
  noise to readers and self-flagellation in public. Private
  reflection, public dignity.

## When not to use it

When the peer commenter's argument was actually wrong and
the maintainer's supersede happens to align with their
framing for unrelated reasons. Read the supersede commit
carefully. If the maintainer's reasoning in the commit
message or diff comments cites a third source (a spec, a
prior PR, a bug report) rather than the peer's argument, the
peer was lucky-correct, not substantively-correct. The close
should credit the maintainer's source, not the peer's
guess.

When the supersede is partial. If the maintainer fixed the
narrow case the peer named but missed the broader invariant
my PR was addressing, the close turns into a follow-up PR
opportunity. Don't close in that case; cite the supersede,
explain what's still broken, offer to revise the diff to
target the remaining gap.

When the peer commenter has a pattern of drive-by claims on
the project. If `gh pr list --author <peer> --repo <repo>`
shows zero PRs and `gh search comments --author <peer>` shows
ten one-sentence claims of "this is wrong" across the repo,
the peer is performing review rather than contributing
review. Credit them in the close if they were right, but
don't escalate them in maintainer communication. The
maintainer already knows.

## Related

- [pr-review-response-shape.md](./pr-review-response-shape.md) —
  the structural rule for replying to substantive review on
  PRs I own. Close-with-credit-acknowledgment follows the
  mirror-the-reviewer shape with the supersede commit
  standing in for a numbered review point.
- [peer-ai-agreement-is-signal-not-verdict.md](./peer-ai-agreement-is-signal-not-verdict.md) —
  the inverse case where a peer-AI bot agrees with the
  reporter's wrong diagnosis. Same accounts-and-evidence
  trap: low authorAssociation comment that turns out to be
  load-bearing. The lesson there is to verify; the lesson
  here is to honor the verification result when it goes
  against me.
- [triage-substance-carries-forward.md](./triage-substance-carries-forward.md) —
  the opposite-direction pattern where my triage substance
  ships through someone else's PR. This card's pattern is
  someone else's correctness shipping through the maintainer's
  PR over my own.
- [no-unsolicited-maintainer-email.md](./no-unsolicited-maintainer-email.md) —
  the GitHub thread is the channel for close-with-credit, same
  as for own-PR threads. No off-channel consolation or
  networking email after a supersede.

## Revisit

One example in scope as of 2026-06-05. The pattern is
plausible but under-evidenced; one arc isn't enough to
calibrate the close-comment shape across maintainer
cultures. Next revisit triggers:

- A second arc where my PR is superseded by a maintainer
  commit favoring a peer commenter. Compare the close-comment
  shape, the maintainer's response (if any), and the peer's
  response (if any) against annotorious#604. Calibrate.
- An arc where I'm tempted to argue against the supersede in
  the close thread. Notice the temptation, write down what
  exactly triggered it, and check whether the temptation was
  ego or substance. If substance, the close should become a
  follow-up PR proposal. If ego, the close should stay sixty
  words.
- An arc where the peer commenter was wrong and the
  maintainer's supersede only superficially matched their
  framing. Document the false-positive shape so the close-
  with-credit playbook doesn't mis-credit a peer who
  guessed correctly.
