# Two-layer bug diagnoses, compatible fixes

When a single end-user bug attracts two independent root-cause
analyses pointing at different layers of the same package
hierarchy, the right response is usually "both" rather than
"pick one." If both diagnoses produce minimal fixes that don't
contradict each other, both layers were probably broken; the
end-user symptom was the visible tip of a stack of compatible
gaps.

The rule is: read both reports, sketch the call graph that
spans both layer claims, and check whether the two proposed
fixes are orthogonal. If they are, the bug is two-layer. If
they aren't, one diagnosis is wrong and the call graph will
show which.

## When to reach for it

A bug report or issue that cross-references another open
issue or PR and explicitly says "filing separately so
maintainers can correlate both layers." The second reporter
isn't disagreeing with the first reporter's analysis at the
factual level; they're saying the analysis is incomplete
because their trace points at a different layer.

This shape is common in monorepo packages that split a
responsibility across `core` and a peer package, where the
peer package implements a behavior that `core` orchestrates.
The end-user symptom looks single-layer because they see one
broken thing. The fix surface area is often two-layer
because each layer was making an assumption that the other
layer was supposed to enforce.

## The mechanism

Three things happen.

1. **Each layer has its own write site.** The peer package
   does a boundary save mid-operation. The core orchestrator
   does a final flush at operation end. Both upsert the same
   logical record. The bug is in the ordering / coordination,
   not in either site alone.
2. **Each reporter traces from a different starting point.**
   The Discord-post reporter started from "my message
   disappears on refresh" and reached `applyMessagesToMessageList`
   in `core`. The standalone-repro reporter started from "I
   pinned my assistant message id" and reached
   `ObservationStep.prepare` / `ObservationTurn.end` in
   `memory`. Both traces are valid; they reach different
   floors of the same building.
3. **Fixes at different layers are usually orthogonal.** A
   fix in `core` that stops the unconditional remove-and-re-add
   does not change anything about how `memory` source-tags
   the message at the step boundary. A fix in `memory` that
   re-flushes persisted-assistant-ids at turn end does not
   change anything about how `core` processes output steps.
   Both can land. Both might need to.

## What to do when you find it

If you're a third-party reader (not the maintainer), the move
is to comment on neither issue. The two reporters have done
the analysis; the maintainer's job is to triage them as
related-but-distinct or as duplicates. Adding a "you should
also look at X" comment is noise.

If you're contributing tooling that helps debug this class
of bug (tracing, logging, instrumentation), the right move
is to make sure your tooling can distinguish between the two
layer claims at trace time. If your spans only cover one of
the two write sites, you can't help a future debugger
disambiguate. The wrap-site completeness matters more than
the wrap-site count.

## Reference

mastra-ai/mastra #15049 (core layer, Discord-sourced,
ProcessorRunner.applyMessagesToMessageList) +
mastra-ai/mastra #15050 (proposed core fix, OPEN) +
mastra-ai/mastra #16561 (memory layer, standalone repro,
ObservationStep.prepare / ObservationTurn.end).

The second reporter explicitly wrote "Filing separately so
maintainers can correlate both layers." Both PR/fix proposals
are compatible — neither contradicts the other.

A trace tree built only around `step.prepare` would show one
of the two write sites and not the other. Both sites need
spans for a future debugger to disambiguate where a given
end-user-visible loss actually occurred. (This is why I added
`turn.end` to my PR mastra-ai/mastra#16442 — without it, my
spans would help find #15049-shape bugs but be silent on
#16561-shape bugs.)
