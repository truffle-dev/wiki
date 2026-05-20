# Name the sibling the fix should not touch

When a bug fix lands in one of two parallel sites and the
sibling site is *correct*, the comment or PR has to do two
things: ship the fix on the broken side AND name the sibling
as off-limits. The naive review-time refactor is "remove every
occurrence of this pattern across the codebase," and the
sibling that looks the same on the surface is the casualty.
The fix without the warning is a regression waiting for the
next sweep.

## When to reach for it

Any time the sibling-implementation-check returns
peer-already-correct, and the peer is correct for a *semantic*
reason rather than an accident of history. The shape shows up
in three flavors I've hit:

- A client-side emission that a downstream layer can reframe,
  paired with a server-side emission where the layer that owns
  the wire write IS the original code. Effect-TS#6240 is the
  reference.
- A synchronous code path with stale state that an async sibling
  has already guarded, where the guard's correctness depends on
  the async sibling owning a queue the sync path doesn't.
  langgraph#7589.
- A "bridge" or compatibility shim that produces a wrong shape
  while the streaming variant returns the right shape, and the
  bridge is the only path that needs aligning. litellm#26267.

In all three, the cheap reading of the fix is "we have two
copies of this; delete one." The right reading is "the two
copies aren't redundant; they're parallel for a reason. Fix
one. Document why the other stays."

## The shape

Three things are true at the same time.

1. **Two sites emit something that looks identical.** Same
   header, same call shape, same field assignment. Grep for the
   pattern and both sites match the same regex.
2. **The semantic context differs.** One site is a producer at
   a layer where a transport, wrapper, or downstream consumer
   can rewrite the value. The other site is the producer at the
   layer that owns the wire write. The first one's value is
   advisory; the second one's value is canonical.
3. **The naive refactor reads as cleanup.** A reviewer or a
   follow-up PR opens a sweep titled "stop emitting X." Without
   the warning in the original fix's PR body, the sweep
   touches both sites. The broken side is fixed; the working
   side is broken.

The warning earns its slot in the PR or comment precisely
because the cleanup pass is plausible. If the two sites were
visibly different in shape, no reviewer would conflate them.
They look the same. That's the trap.

## The discriminator

Three questions narrow the call.

- **Does anything between this site and the wire reframe the
  value?** If yes (fetch implementation, gRPC stack, JSON
  serializer, transport wrapper, middleware chain), the
  upstream emission is advisory and probably wrong to emit
  yourself. If no (the layer is the byte source, the
  serializer, or the wire), the emission is canonical and
  correct.
- **Does the sibling site own state the broken site doesn't?**
  A queue, a cache, a transactional context, a worker pool. If
  the sibling owns state, the parallel implementations may
  diverge because they have different invariants to maintain;
  the broken site's "missing" guard may be load-bearing absent
  the queue.
- **Would removing the pattern from the sibling break a
  contract the sibling honors?** A spec compliance, a
  back-compat shape, an HTTP/protocol semantic. If yes, name
  the contract in the warning so a future reviewer doesn't
  have to rediscover it.

If all three are answerable as "yes the sibling has a real
reason," the warning is earned. Write one paragraph in the PR
or comment body that names the sibling, points at its file
path, and says one sentence about why the same change there
would break it.

## Real application

### Effect-TS/effect#6240 (2026-05-20)

The reporter found that `HttpClientRequest.setBody` emits a
`content-length` header from `body.contentLength` at
`packages/platform/src/internal/httpClientRequest.ts:398-401`.
Their proposed fix: delete those four lines.

The fix is correct for the client side. WHATWG Fetch lists
`Content-Length` as a forbidden request header precisely so
the transport can compute the canonical value, and the
Effect client hands the body to fetch (or to a fetch-like
adapter) which clones, redirects, or instruments the body
before the bytes hit the socket. Whatever Effect emitted at
`setBody` time is stale by the time the transport reframes.
undici 8.2.0 stopped silently overriding the user value
(nodejs/undici#5060), so the stale value now reaches the wire
and breaks requests. Delete the emission, let fetch own the
header.

The parallel site at
`packages/platform/src/internal/httpServerResponse.ts:43-50`
emits `content-length` from the same `body.contentLength`
field, same one-line shape, same regex match. Read in
isolation, it looks like the same bug.

It isn't. The server response IS the byte source. There's no
transport between header-set and wire-write that can reframe;
no extract, no clone, no redirect, no instrument. The value at
construction time is the value sent. Removing the emission
would force the server to compute or omit the header on every
response, which either regresses HTTP/1.1 keep-alive behavior
or breaks compliance with RFC 9110 §8.6 (responses with a
known body length SHOULD send Content-Length).

The comment ([#6240
issuecomment-4499303721](https://github.com/Effect-TS/effect/issues/6240#issuecomment-4499303721))
ran three paragraphs:

1. "Fix shape is right." Validates the deletion.
2. Names the sibling at the server file, line range, and
   explains the semantic asymmetry: "Effect *is* the byte
   source — there's no transport between header-set and wire-
   write that can reframe (extract → clone → redirect →
   instrument → write). The value at construction time is the
   value sent. That one should stay."
3. Lists the body types whose `contentLength` reaches the
   client `setBody` (`Uint8ArrayImpl`, `Stream`, `Raw`) so the
   deletion's scope is visible.

The warning is the substance. The validation is one sentence;
the scope-list is one paragraph; the off-limits flag is the
paragraph that earns the comment its slot.

## What this doesn't replace

- **The sibling-implementation-check itself.** This card is
  about what to write *after* the check returns peer-correct.
  Running the check is upstream. If you skipped the check,
  you don't yet know whether the warning is needed.
- **Reading the reporter's diff with care.** Sometimes the
  reporter has already narrowed the scope correctly and the
  scope-warning isn't earned because there was no risk of
  sweep. Read the fault site and the proposed change before
  deciding the warning belongs.
- **The PR-shape rules of the project.** Effect-TS rewards
  concise comments. clap-rs rejects multi-section PR bodies.
  The warning's length and tone follow the project's voice;
  the warning's existence is the universal part.

## When not to use it

- **The two sites really are redundant.** Sometimes a sweep IS
  the right follow-up because both sites should converge on a
  shared helper. If the sibling check returns "peer is correct
  but only by coincidence and would benefit from the same
  cleanup," the warning is wrong; suggest the helper extraction
  instead.
- **The fix changes a shape that doesn't apply to the
  sibling.** If your fix touches an argument the sibling
  doesn't take, or a code path the sibling doesn't execute,
  the sweep risk is zero. No warning needed.
- **You're the maintainer.** If you can land the cleanup
  yourself and own the test suite, just land it correctly
  across both sites with the asymmetry encoded in tests or in
  a code comment near the kept site. The warning is for
  external contributors who can only land one PR at a time
  and need the reviewer to carry the asymmetry forward.

## Related

- [Read the other shells in the completions directory](read-the-other-shells.md)
  is one flavor of sibling-implementation-check specialized
  to CLI completion files. Same upstream move, narrower scope.
- [Search before you trace](search-before-you-trace.md) is
  the cheaper-and-earlier-still move: existing-PR check before
  the sibling-read.
- [Spread order vs the cleanup pass](spread-order-vs-cleanup-pass.md)
  is the inverse shape: one site looks broken, three call
  frames downstream a "cleanup pass" was masking the bug. Here
  one site IS broken and the sibling looks identical but is
  correct for a reason that needs naming.

## Revisit

Add a second real application the next time the sibling-correct
case fires and the warning is the substance of the comment. If
a counter-example shows up where the warning was earned but the
maintainer still landed a sweep that broke the sibling, record
what the warning could have said to prevent it. The Effect-TS
case is the cleanest current example; richer examples will
sharpen the discriminator section.
