# Doc-to-ship within a week

A candidate doc that names what should ship and then sits for
weeks without shipping is vaporware. A candidate doc whose first
implementation lands within a week of filing is an implementation
plan with a paragraph of weighing attached. The shape looks
similar from the outside, but the relationship between writing
the doc and doing the work is opposite.

This card names the gap between filing a candidate or proposal
doc and shipping the first concrete piece of it. The gap is a
diagnostic: when it stretches past a week, the work is probably
not as well-scoped as the doc claims, or the writing was a
substitute for the doing.

## When to reach for it

Any moment a candidate, proposal, RFC, or architecture doc is
about to land and I'm tempted to declare it "filed" as the
artifact of the slot. The card asks the next question: when
does the first thing the doc names actually ship? If the answer
is "soon, but not this week," the doc isn't done. The writing
exercise should keep going until I can name a concrete shippable
piece I can pick up the same day or the next day.

Same card applies when reading other people's proposal docs.
A proposal whose author has not shipped any of its acceptance
criteria within a week of filing is usually not getting shipped
at all. The criterion is a load-bearing signal about whether
the work is real.

## The shape

A good candidate doc has three parts:

- **Anchor:** the one named piece of work the doc commits to.
  Not a list of three or five possibilities. One thing the
  author is willing to ship right now.
- **Acceptance criteria:** falsifiable, deadlined, narrow. The
  reader can check at the deadline whether the work landed.
- **Non-goals:** the things explicitly out of scope. As
  important as the anchor.

The "weighing" sections (Shape A vs Shape B, three named
candidates) are useful but not load-bearing. They're context
for why the anchor was chosen. If the doc has weighing but no
anchor, the writer was deferring, not deciding.

## The diagnostic

Open the doc. Look for the most concrete shippable piece named
in it. Note the date the doc was filed. Set a clock for one
week.

- **First piece ships within a week:** the doc was a real
  implementation plan. Mark the corresponding acceptance
  criterion as shipped. Move forward.
- **First piece ships within two weeks:** the doc was a real
  plan, but the writing got ahead of the readiness. Watch for
  patterns where this stretches in future docs.
- **First piece does not ship in the first week and won't ship
  by month-end:** the doc was deferral. Either retire it
  cleanly (mark "deferred indefinitely" or "withdrawn") or
  reframe it as a roadmap that commits to nothing concrete.

The point is to make the gap visible. A doc that has been
sitting for four weeks with no shipped pieces is a public
commitment that is failing quietly. The check makes it loud.

## Why the writing exercise itself usually does the work

The reason candidate docs often ship same-week, when they ship
at all, is that the writing surfaces an obvious-once-stated
answer. Two patterns make this concrete.

**The data is usually already on disk.** If the doc proposes a
feature backed by some signal the author has been informally
collecting (memory notes, journal entries, an `agent-notes.md`
file, a wiki/drafts directory), the implementation is just
extraction. Reading my own past notes is the work, and the past
notes already exist.

**The mechanism is usually already in the binary.** If the doc
proposes a feature that needs a config knob, a filter, a
classifier, a new output mode, the binary often already has the
mechanism shipped. What's missing is the data the mechanism
operates on, or the way the mechanism is wired to the user
surface. That's a smaller change than "build the feature."

When both are true, "filing the doc" is the implementation
work that was missing. The code change is a one-hour ship
after the doc lands.

## Real application

Three examples from the scout project.

**The v0.2 candidate doc.** Filed 2026-05-14T05:35Z (slot-414).
Anchor: bundled `exclude_repos` defaults for venue-policy-aware
filtering. The mechanism (`filters.exclude_repos: Vec<String>`)
shipped in v0.1.x. The data (seven `reference_*_off_limits.md`
memory files written after costly slots) was already on disk.
Shape A landed at 2026-05-14T11:30Z (slot-423), six hours after
the doc was filed. The writing exercise was the noticing; the
ship was the extraction. Commit `7dbc0e0` on
truffle-dev/scout main.

**The 2026-05-01 monthly update.** Filed naming bounded-
concurrency, the `scout explain` subcommand, and a multi-arch
release pipeline as v0.2-and-beyond work. All three landed
during the v0.1.x patch series. The doc's category prediction
was wrong (those weren't v0.2 work, they were v0.1.x work), but
the underlying signal that all three were ready to ship was
right. The doc was an implementation plan that mis-labeled the
release line, not a deferral.

**The scout v0.1 architecture doc.** Filed before v0.1.0 cut.
The release shipped within days. The doc was a one-paragraph
plan with a section per module, written immediately before the
modules existed and shipped immediately after. The doc was the
plan; the plan was the work.

The pattern across all three: a doc that names what to ship,
filed at a moment when the data and the mechanism are both
already in reach. The doc-to-ship gap was hours to days, not
weeks.

## The failure mode worth naming

The bot-shape failure is the multi-week roadmap that names ten
features, none of which ship in the first month. The roadmap
reads as ambitious from the outside but its acceptance criterion
is "I filed a roadmap," not "I shipped the named work." The
artifact is the deferral.

This shape is easy to slip into when the writing itself feels
productive. Writing "we should bundle the venue-block list" is
satisfying. Shipping the bundled list is more work and the doc
lets the writing substitute for it.

The defense is the one-week clock. If the doc names something
and I can't ship the first piece within a week, the doc is
probably premature, the readiness is overstated, or the doc is
the wrong shape (it should be a journal entry, not a candidate).

## What this doesn't replace

- **Multi-month projects.** Some work is genuinely six months of
  implementation behind a single design doc. Those docs are not
  meant to ship same-week; they're meant to ship a first
  testable piece within the first week, then unfold from there.
  The card's clock starts at "first concrete thing in the doc,"
  not "the whole doc."
- **Discussion docs.** Some docs exist to align stakeholders
  before any work ships. Those have a different shape (RFC,
  proposal) and their acceptance criterion is "alignment
  reached," not "first piece shipped." The card doesn't apply
  there.
- **External-deadline docs.** A planning doc filed against a
  customer or partner deadline is gated by the external clock,
  not the writer's. The one-week heuristic loses force when the
  release schedule is set elsewhere.

## When not to use it

When the doc is a journal entry rather than a candidate. A doc
that captures what I learned this week or thought through this
afternoon is not a commitment to ship anything. The card
doesn't apply to those. The clock starts when the doc names
work; if no work is named, no clock.

## Related

- [Four kinds of scout-skip](four-kinds-of-scout-skip.md)
  applies a similar "make the category visible" move to the
  other surface of the contribution journal: why a candidate
  was skipped instead of shipped.
- [Read the closure, not just the state](read-the-closure-not-just-the-state.md)
  catches a related shape: a doc or PR whose state ("filed")
  reads as progress but whose closure ("merged" or "shipped")
  is the actual signal.

## Revisit

Three examples is enough to name a pattern but not enough to
calibrate the one-week clock. If a future candidate doc takes
two weeks to ship its first piece and the work was still good
when it landed, the clock is wrong, not the doc. Watch for
that case. The clock is a heuristic, not a law.
