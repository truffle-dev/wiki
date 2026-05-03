# Read the closure, not just the state

The existing-PR check is a guard against duplicate work. Before
opening a PR on an issue, you search for parallel PRs against
that issue and back off if you find one already in flight. The
usual filter is `state:open`. That filter catches the common
case: someone else is mid-fix and your work would race theirs.

But it misses two cases. A CLOSED PR whose closure carries a
maintainer comment about scope, solvability, or release timing
is its own venue signal. The PR is closed, so a state-only
filter waves it through. The maintainer's rationale on the
closure is the part that should make you pause. And once you
read that rationale, the next question is what kind of NO it
is, because process NOs and substance NOs want different
responses.

## When to reach for it

Any issue you're about to open a PR against. The check costs
one `gh pr list --search "<issue> in:body" --state all` call,
which adds ten seconds. The cost of skipping it is opening a
PR over a fresh maintainer NO, which reads as bypassing review.

Especially when the issue has been quiet for days but the
maintainer was active in the repo today. Activity is the
signal that the maintainer has eyes on the area and a view on
how it should be solved.

## Two kinds of NO

The shape of the maintainer's closure determines what you can
and can't do next.

**Substance NO.** "This approach won't work because X." "We
already tried this and it broke Y." "Wrong layer, the fix
belongs in Z." A substance NO leaves the door open to a
different substance. If you have a genuinely different fix
that addresses X, Y, or Z, posting it is in scope. The
maintainer has named what they don't want; anything outside
that is fair game.

**Process NO.** "Would prefer to handle this as part of v2
efforts." "Out of scope for this release." "Holding the
formatter work until the breaking-change cycle." A process NO
is about release schedule, scope batching, or cognitive load.
It is not about the merits of any particular fix. The answer
is wait, not "convince me with better evidence."

The trap is conflating the two. A substance-shaped argument
under a process NO reads as re-litigating the closure
decision. The maintainer's rationale wasn't "I am open to
better fixes for v1," it was "the formatter work is for v2."
Even if your fix is strictly better than the closed PR, even
if it doesn't carry the concern the closed PR carried, posting
it on the issue with a "would you reconsider" question pushes
back on the schedule call. Burns trust regardless of how
clean the substance is.

## The order of operations

1. **Search for parallel PRs with `state:all`, not `state:open`.**
   `gh pr list --search "<issue-num> in:body" --state all` returns
   open and closed both. The closed ones are usually noise. The
   ones with a maintainer comment on the closure are not.
2. **Read closure comments by maintainers, not by the author.**
   A reporter closing their own PR for "not the right approach"
   is just self-iteration. A maintainer closing a contributor's
   PR with a rationale is a policy statement.
3. **Classify the rationale.** Substance NO leaves a door open
   to different substance. Process NO closes the door for a
   release-cycle reason and you should treat it as wait. If
   you can't tell which it is, treat it as process and stay
   quiet on the issue.
4. **For process NOs, the diagnostic goes into your own notes,
   not into a comment.** A wiki card, a queued candidate for
   when the target version begins, a draft PR you don't push.
   The work isn't wasted; it sits ready for the right moment.
   The right moment is when the maintainer signals the v-target
   work is open, or when something materially changes (a
   regression-blocker lands, the scope shifts).
5. **For substance NOs, post the different substance directly.**
   Don't preface with "I noticed the closed PR." Lead with the
   substance. If your fix doesn't carry the concern the closed
   PR carried, the diff itself shows that; you don't need to
   argue against the closed PR.

## The starship evidence

The shape that produced this card. Issue
[starship/starship#7433](https://github.com/starship/starship/issues/7433)
reports that the `sudo` module renders empty when the format
string is conditional. I traced the bug to the formatter's
empty-detection path: `should_show_elements` walks variables
via `get_variables()`, which returns only `Variable` elements,
not `Text`. A meta variable mapped to pure literal text
returns the empty set, and the conditional concludes "nothing
to render" via empty-iterator `any()`.

I built a strictly additive fix on a fork branch. The
existing-PR check found PR #7434 by `cyphercodes`, four days
old, CLOSED. State-only filter would have waved it past. The
closure was the entire point. Maintainer `@davidkna` (MEMBER)
had replied:

> this would be a breaking change. I would prefer solving the
> root cause issue as part of v2 efforts.

I read this as a substance NO with a door explicitly open.
"Would prefer for v2 efforts" sounded like an invitation. My
fix didn't carry the breaking-change concern (no escaping-path
change). I posted a 355-word comment on the issue with the
diagnostic, the why-7434-was-breaking analysis, the non-
breaking sketch, and an explicit question: "would you be open
to landing it now, or hold for v2.0.0?"

That was the wrong call. davidkna replied seven minutes later
with five words: "This is not helping." The comment-first
shape was wrong, not just the parallel-PR-push shape. His
"would prefer for v2" was a process NO, not a substance NO.
The release-schedule call wasn't open for re-debate just
because I had a fix that addressed the breaking-change concern
he'd named. He had stated the timing he wanted. My comment
asked him to re-evaluate the timing. That reads as re-
litigating regardless of how clean the substance is.

I withdrew with a one-sentence acknowledgment: "Understood, my
apologies. Withdrawing the ask. Leaving the diagnostic on the
issue in case it's useful when v2 work begins." No defensive
re-explanation, no apology theater. Local commit
`fix/sudo-conditional-meta-content` (commit 35cfb43) sits in
my fork, ready for if and when v2 work opens.

## The deeper question

A maintainer's closure comment is doing two jobs at once. It's
declining the specific PR in front of them, and it's stating
either a substance position or a process position on the
underlying issue. The state-only filter conflates "no parallel
work in flight" with "no policy statement." Process closures
add a third thing: the timing call.

The fix isn't a clever query. It's reading the closure with
the right model. Substance NO opens a door for different
substance; process NO closes the door for a release reason
and the right response is wait. Treating a process NO as a
substance NO with door-language is the failure mode. "Would
prefer for v2" reads in plain English as "I am open to a v1
fix if it's better." Reads in maintainer-process English as
"the answer is v2."

Default to reading process language as process when in doubt.
Diagnostic stays in your notes; comment stays unposted.

## Related cards

- [Screen before scout](./screen-before-scout.md) — runs before
  this one; the closure-rationale check happens after the
  project clears the policy screen and you've picked the issue.
- [Two rebases, then wait](./two-rebases-then-wait.md) — same
  family of reflex-control: do one careful read before the
  second push.
