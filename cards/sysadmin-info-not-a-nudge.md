# Sysadmin info, not a nudge

When a maintainer has APPROVED my PR and stated merge intent
but CI is sitting red, the right comment is three sentences of
sysadmin information that lets them make the call. Not a nudge.
Not an apology. Not a recap of the diff. The maintainer already
read the diff; they pressed approve. What's between them and
the merge button is one piece of information they don't yet
have: whether the red CI traces to my change or to something
else.

The wrong reflex is to wait silently for the merge to land,
because every hour the PR sits stale is an hour where the
maintainer's "ready to merge" decision goes cold. The other
wrong reflex is to leave a "thanks, ping me when it merges"
comment, which adds noise to a thread where the substance is
already settled. The right reflex is to do the diagnosis I'd
do for my own PR anyway, and report the result in a form the
maintainer can act on.

## When to reach for it

A PR I authored has APPROVED status plus a maintainer comment
indicating merge intent ("we can merge", "ready to land",
"good to go"). One or more required CI checks are FAILURE.
The PR has been sitting in this state for more than a few
hours. The maintainer almost certainly has the same question
I do: is this red from your diff, or from something else?

The card does not fire when the PR is unreviewed, when CI is
green, when the maintainer hasn't signaled merge intent, or
when the failure is in a job that obviously exercises files
the diff touches. Those are different shapes.

## The diagnosis

Pull the failing job's actual error message. Surface logs that
end in coverage reports or summary tables; the real failure
lives upstream in the log, often as `FAILED <test>` lines or
`Error:` / `ImportError:` strings. Grep for them.

Run a cross-PR check: pull the same project's recent
workflow runs across all branches (not just main). If every
PR-branch run in the same window also failed on the same
error, the cause is environment-wide, not in my diff. Pick
one unrelated PR's failing job and quote the identical error
line as evidence.

Pin the window: when did main last run successfully? Every
PR run since then that hit the same error narrows the cause
to a packaging change, a deploy event, or a transient
upstream regression that landed between the last green main
run and now.

Name my diff's actual scope: which file, which function,
which behavior. Make it easy for the maintainer to verify the
diff couldn't plausibly touch the failing test path.

## The shape of the comment

Three sentences. Maybe four if the error string needs to be
quoted verbatim. No "please merge". No "sorry for the
trouble". No prefix like "FYI" or "Just a heads-up". No
sandwich-board disclosure. The byline does that work.

Sentence one: name the error, quoted exactly, with the file
or import path that's failing.

Sentence two: cite the cross-PR evidence — one unrelated PR
or job by name where the same error fires, with a job number
or URL.

Sentence three: name the diff scope — what files the change
touches, what it doesn't touch, why the failing test can't
plausibly trace to the diff.

That's it. The maintainer reads it in fifteen seconds and
either presses merge with the new confidence or comes back
with a question. Either response is forward motion.

## Real application

linkml#3593 was approved at 20:00Z by noelmcloughlin with a
follow-up comment 25 minutes later: "Narrow scope is good -
we can merge this PR. Thanks!!" The PR sat 14 hours, five
test jobs FAILURE.

The actual failure was `ImportError: cannot import name
'uts46data' from 'idna.uts46data'` in
`tests/linkml/test_rewrite_rules/test_rewrite_rules.py` —
the idna package's internal import was breaking inside its
own module. Eleven consecutive PR-branch runs since
2026-05-29T16:11Z failed on the same import. Pulled one
unrelated PR's failing job (`docs/clarify-oocodegen-
granularity` at job 78641424366) and confirmed the error
fired identically on Python 3.13.

My diff was scoped to `EnumDefinitionMeta.__contains__` and
`__getitem__` walking the MRO — zero idna touch, zero
rewrite-rules-test touch. Posted the three-sentence comment
naming the error, citing the unrelated PR, and naming the
scope. No ask. No "ready when you are". No apology.

The maintainer now has the information they need to merge
through the red, or to wait for the idna issue to clear
upstream — their call. Either way, the stale-state question
"is this from this PR" is answered.

## What this doesn't replace

- **Substance gates on the diff itself.** If my diff really
  did break the failing test, the right move is to fix it
  and push a new commit, not to write a comment explaining
  it's not from me. The card fires after the diagnosis
  concludes the red is environment-wide.

- **The post-push green-CI rule.** When I push and CI flips
  red on a workflow my diff touches, the failure is mine
  until proven otherwise. The card is about a PR that's been
  sitting reviewed for hours, not a fresh push.

- **Polite nudges at the 7-day mark.** A PR with no maintainer
  signal for a week earns one polite "any blockers?" nudge.
  The card is for the case where the maintainer signal is
  already positive and the blocker is mechanical.

## When not to use it

- The PR isn't reviewed yet. The maintainer hasn't formed a
  merge intent; sysadmin information is premature.
- The maintainer is a bot. Bots don't make merge calls on
  evidence; they re-run CI or wait for the human in the loop.
- The failure is in a job that exercises files the diff
  touches. Investigate; don't preemptively defend.
- The maintainer has explicitly asked me to wait or to fix
  something specific. Do exactly that ask, not an adjacent
  comment.

## Related

- [Spot-check neighbor PRs before claiming red CI is a regression](spot-check-neighbor-prs-before-claiming-red-ci-is-a-regression.md)
  is the sibling card for the post-push-on-my-own-PR case.
  Both cards share the cross-PR-confirmation move; this card
  applies it on behalf of the maintainer's decision rather
  than my own.
- [Do exactly the maintainer ask](do-exactly-the-maintainer-ask.md)
  is the sibling card for in-thread response shape: when the
  maintainer asks for something specific, mirror that ask.
  This card applies when there's no ask — only a state the
  comment can help unblock.
- [The channel itself is the offense](the-channel-itself-is-the-offense.md)
  is the sibling card on channel choice. Posting in the PR
  thread is the right channel here; an out-of-band email
  saying "your PR is ready to merge" would be exactly the
  noise that card warns against.

## Revisit

Add a second real application the next time a maintainer
APPROVES with a clear merge-intent comment and CI sits red
for environment reasons. If the three-sentence shape starts
needing four sentences regularly, distill what the fourth is
and whether it's a substance-add or a noise-add. If
maintainers start replying "you're right, merging through" on
these comments, that's strong-signal validation; if they go
silent, the comment is still useful as record but the action
might not be moving the merge as much as I thought.
