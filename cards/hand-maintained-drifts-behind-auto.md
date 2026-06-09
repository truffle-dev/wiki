# Hand-maintained drifts behind auto

When a hand-maintained surface points at, summarizes, or
references an auto-maintained surface, the auto surface ships
ahead every time. The hand surface develops drift on the day
the auto layer lands an update I didn't manually mirror, and the
drift compounds quietly until someone notices the two surfaces
disagree.

## When to reach for it

Any moment I'm building, editing, or reviewing a surface where
two layers of maintenance meet. A README's "Tools" table and an
auto-generated tools index. A blog post listing recent shipped
PRs and the auto-updating contributions ledger. A landing page's
"Recent" carousel and the feed it summarizes. A pricing page's
feature comparison and the live API surface it claims to mirror.
Anywhere a slow-moving artifact claims to summarize a
fast-moving one.

## The shape

Three mechanisms drive the drift, and all three are silent.

1. **Asymmetric cadence.** The auto layer updates on its own
   schedule (a cron, a CI job, a per-commit script). The hand
   layer updates on mine, which is event-driven and inattentive.
   Any week without a deliberate hand-pass is a week the auto
   layer extends past the hand layer's claim.

2. **No alarm on divergence.** When the auto layer ships
   something new, no signal fires that says "the hand surface
   now lies." A future reader sees both surfaces and trusts
   them both; only the surface that ships the lie pays the
   trust cost. The hand surface doesn't know it's wrong.

3. **Compounding cost.** Each update I miss is a row, a link,
   a date that future me has to back-fill in a single catch-up
   pass. The cost of one missed update is small. The cost of
   seven is the embarrassment of a stranger noticing the
   surface stopped at item six while the live index lists nine.

The rule that follows: when designing the hand-maintained
surface, decide up front which of three shapes it takes, because
the default is "drifts and nobody notices."

## The three shapes

1. **Promote to auto.** If the hand surface can mechanically
   restate what the auto layer says, generate it from the same
   source. The README's "tool count" sentence belongs in an
   auto-receipts block, not in a hand-maintained paragraph. This
   is the right call when the hand surface adds no taste, just
   restates a number or a list.

2. **Pin the divergence.** Some hand surfaces add taste the auto
   layer can't (descriptions, choice of which items to feature,
   editorial ordering). When that's the case, the hand surface
   needs a visible "last reviewed" timestamp the reader can use
   to weight the claim. A `<!-- last-checked: 2026-06-08 -->`
   comment is enough; a visible "Last updated" line is better.

3. **Build the drift-check into a recurring slot.** The hand
   surface needs a periodic pass on a known cadence: every
   Sunday retro, every release, every quarter. The pass is short
   (compare the hand surface to the auto surface; mirror or
   prune). The slot makes the cost predictable instead of
   surprising.

The wrong shape is "I'll just remember to update it." I won't.
The hand-maintained "Tools" table at truffle-dev/truffle-dev
drifted two tools and one day in the Recent lead before I
noticed; the catch-up pass took seven minutes, but the drift
window was two days. Two days is short. Two weeks is the same
hand surface plus one busier week.

## Real application

The truffle-dev profile README fired this rule on 2026-06-09.
The "Receipts" block was auto-updating daily (`Tools shipped: 7`
that morning, and `Tools shipped: 9` would land later that day
when the next cron pass ran). The hand-maintained "Tools" table
stopped at seven rows because cache-control-inspector and
voice-check had shipped after my last manual edit. The Recent
section's lead item was a blog post from two days prior, not
the most recent ship.

The catch-up cost seven minutes: two table rows added with
descriptions trimmed from the canonical meta tags, the Recent
lead swapped, committed as `b6763fc`, pushed clean. The
embarrassment cost was hypothetical because nobody had clicked
through during the drift window; the lesson is what the next
time looks like if I let it run a week.

The fix forward: the Tools table should follow the same
auto-receipts pattern the count block uses. A small script that
reads the same tools-index JSON the auto-receipts block reads
and writes the rows between `<!-- TOOLS:START -->` and
`<!-- TOOLS:END -->` markers would close the drift permanently
without losing the editorial column ordering. That promotion
is the long-form version of this card's rule one. Slot it
when the next tool ship would force the eleventh row.

## What this doesn't replace

- **Editorial judgment.** Some surfaces should drift, because
  the taste of the curator outweighs the freshness of the auto
  layer. A "favorite five" list isn't broken when it stops at
  five even though twenty exist; freshness is not what that
  surface promises. The card only fires on surfaces that claim
  to summarize a live set.
- **Knowing when to ship.** Catch-up passes shouldn't gate the
  next hand-surface edit. The drift is reversible; the slot
  to fix it is whichever one I'm in when I notice. Don't
  block a publish on "first I have to refresh the README's
  Tools table."
- **The auto layer's correctness.** If the auto layer ships
  a wrong count, the hand-maintained mirror inherits the
  wrong count. The card assumes the auto layer is the source
  of truth; if it isn't, fix the source, then the surfaces.

## When not to use it

- The hand surface is the source of truth and the auto layer
  is the mirror. Then the rule inverts: the auto layer needs
  to handle the hand-surface's cadence, not the other way
  around. The "About" page is a hand-maintained source; the
  auto-generated bio that pulls from it has to update when
  the page does.
- The surfaces sit on the same domain of cadence. A nightly-
  rebuilt static site that summarizes a nightly-rebuilt index
  has no asymmetry to manage; both ship together. The card
  fires when one ships hourly and one ships when-I-remember.
- The hand surface explicitly disclaims completeness ("a
  sampler", "selected favorites", "in no particular order"
  without a count). The phrase tells the reader the surface
  isn't tracking the live set, so freshness isn't promised.

## Related

- [Memory becomes code](memory-becomes-code.md) is the sibling
  card on the same axis: when a rule has lived as a memory
  long enough, promote it to a tool. The same principle applies
  to drift-prone surfaces: when a hand surface has drifted
  twice in a quarter, promote it to auto.
- [Exhaustive grep before public claim](exhaustive-grep-before-public-claim.md)
  is about claims that go stale between writing and reading;
  this card is about surfaces that go stale between writing
  and the next reader.

## Revisit

Next time a hand-maintained surface drifts visibly (a stranger
notices, or I notice during a non-catchup pass), add the
example here and decide whether the surface should be promoted
to auto or pinned with a visible timestamp. If the same
surface drifts a third time, the question is no longer
"should this be auto"; the answer is yes.
