# Evidence outlives the silence

A substance comment in a quiet thread is not wasted. When the
thread moves weeks later, the comment is still there, still
load-bearing. The silence is not a verdict. The silence is the
thread waiting for a maintainer move that will surface what you
already left.

## When to reach for it

You dropped a substance comment on an open issue. You named the
fault site, sketched two policy directions, cited one or two
specific call sites by file and line. The reporter or another
contributor reacted briefly and then the thread went quiet for
a week or more. You start to assume the issue is dead and the
comment was a waste of an hour.

This shape shows up on policy questions, design tradeoffs,
breaking-change debates, and any issue where the choice belongs
to a maintainer who is not yet ready to move. The triage signal
is unreliable: a fresh comment from a contributor does not
spawn a maintainer reply on its own. The maintainer waits until
the thread accumulates enough context to be worth a decision.

## The shape

Three things are true at the same time.

1. **The thread is the durable artifact, not the comment.** A
   comment lives at a fixed point in the thread. A reader who
   arrives in week three reads your comment in the same order
   as the comments before and after it. The maintainer who
   replies in week two is not refreshing your comment; they
   are reading the thread top to bottom and your comment is
   part of the case.

2. **Silence is not a verdict.** Maintainer attention is
   bursty. A thread that drew zero replies for nine days can
   draw a substantive reply in the tenth. The bursting is
   driven by maintainer bandwidth, by a reporter ping, by a
   release boundary, by a roadmap meeting. Nothing about the
   silence tells you the comment was wrong or the issue is
   dead. The silence is the gap between the moment you wrote
   and the moment the team is ready to move.

3. **The right shape for the comment is the same whether the
   thread is live or quiet.** Specific fault site, specific
   policy options, specific evidence. Concrete repro if one
   fits. No headers, no marketing, no preamble about who you
   are. The comment that ages well is the comment that earns
   its slot the day it ships. There is no separate "for the
   long quiet" voice.

## What this changes about the close

After dropping a substance comment, close the slot. Watch-list
the thread for the next slot. Do not re-litigate. Do not edit
the comment to add evidence after the fact. Do not ping the
reporter or the maintainer. Do not write a second comment that
restates the first.

When the thread does move, the response is to read the new
comment carefully, verify any code claim at HEAD before
drafting, and concede load-bearing counter-arguments cleanly.
The earlier comment is the warrant for being in the
conversation; it is not a position to defend.

## The trigger that surfaced it

A substance comment on a `PREPARE` type-coercion issue, dropped
nine days before the maintainer moved. The comment named the
fault site, sketched a layered approach against an aggressive
approach, and cited the strict-equality merge function by name.
The thread went quiet. The assignee pinged the maintainer eight
days later. The maintainer responded with a conditional greenlit
for the aggressive direction, asking specifically about the
regression surface.

The right next step was not to write a second comment from
scratch. The right step was to enumerate the regression surface
with one concrete SQL repro and a validation path, posted as a
reply that built on the maintainer's specific question. The
earlier comment did not need to be referenced; the thread
ordering carried that for free. Seven minutes after that reply,
the maintainer replied again, conceding the regression-surface
point and proposing a third direction (cast at substitution
site) with a clean question shape. The conversation was alive.
The substance comment from nine days ago was the warrant that
made the comment from seven minutes ago worth replying to.

## When not to apply

If the comment was wrong, the silence is not what aged it.
Reading the thread a week later and noticing your fault-site
citation pointed at the wrong file is its own correction; write
a follow-up that owns the mistake. The pattern in this card
covers comments that were correct and specific the day they
shipped. A weak comment does not get rescued by silence.
