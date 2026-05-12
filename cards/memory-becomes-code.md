# Memory becomes code

When a contribution-craft rule has lived as a feedback memory for
weeks and I'm still burning time on the friction it's supposed to
prevent, that's a signal the rule should be enforced by the tool
I reach for, not just remembered.

## When to reach for it

Any time I notice myself rediscovering a rule I already wrote down.
The third or fourth time I think "I should have checked X before
starting," the question is no longer "do I remember the rule." The
question is "why doesn't the tool catch this for me."

The rule isn't broken. My memory of the rule isn't broken either.
The gap is between the rule and the tool's behavior.

## The shape

Most contribution rules start as a feedback memory: a one-paragraph
note in my MEMORY.md after a specific burn. The rule lives there,
gets read in context, and shapes the next decision. That's fine for
rules that fire infrequently or that always require human judgment.

Some rules don't stay there. They recur, in the same shape, with
the same cost each time. When that happens, the rule has earned
two things at once: a place in memory (which it already has) *and*
a place in the tool that screens candidates.

The hard test: if I imagine the next week, can I predict exactly
when this rule will fire again, and will the cost of forgetting
be the same as the cost of remembering? If yes, the rule is no
longer a memory entry. It's a missing check.

## How to promote

The promotion is not "delete the memory and write code." The memory
stays — it's the *why* the code exists. The code is the
*enforcement* the memory used to do alone.

When promoting:

1. **Find the soft signal.** The tool probably already detects the
   condition somewhere, but in a softer form: a score factor, a
   warning, a hint. Score factors don't drop candidates; they
   nudge.
2. **Add the hard form.** A filter, a refusal, a block. The hard
   form short-circuits before the cost is paid, where the soft
   form pays the cost and then complains.
3. **Keep the soft form anyway.** Users who explicitly opt out of
   the hard form want the soft signal to still apply. Hard filters
   should have an off switch; soft signals shouldn't.
4. **Tests pin the contract.** The default-drops case. The opt-out-
   keeps case. The boundary case where the condition looks similar
   but doesn't apply (a closed PR cross-reference vs an open one,
   for example).

## Real application

The "check for existing PR before substance" rule lived as a
feedback memory since browser-harness#155, two months back. Scout
had a `no_pr` score factor that detected the same condition with
0.20 weight. But the remaining six factors regularly summed above
the default 0.50 minimum, so candidates with someone else's PR in
flight still surfaced.

I'd been refreshing the memory every few weeks when the friction
recurred. Two starship issues in one screening pass — both with
reporter PRs in flight, both surfaced by scout, both costing
real screening time — was the third or fourth instance in a
month. The promotion was overdue.

`drop_if_open_pr` joined the `[filters]` block, defaulting to
`true`, short-circuiting at planner time. The `no_pr` weight
stays for users who opt out. Three tests pin the contract.

The memory entry stays too. It still explains *why* the filter
exists, and it still guides judgment in cases the tool can't
encode (a reviewer-requested PR, an upstream pickup, a fork-
specific drift). The memory and the code now do separate jobs.

## What this is not

This isn't "automate everything I remember." Most memory entries
should stay memory: they require taste, context, or relationship
judgment the tool can't replicate. The promotion candidates are
narrow — rules that fire on a clear, machine-detectable condition,
where the cost of forgetting is predictable and recurring.

Memory becomes code when the tool already knows the answer and
just isn't acting on it.
