# Prove the guard goes red

A regression test that has only ever been seen green is unproven.
Passing on good code says nothing about whether it catches the
break it was written to catch. The only way to know a guard
discriminates is to reintroduce the bug and watch the guard flip
to red.

This is cheap to skip and expensive to skip. A guard nobody
proved red is worse than no guard, because it grants false
confidence: the deploy script goes green, the reviewer trusts
the gate, and the exact regression the guard exists to stop
sails through anyway.

The discipline is one throwaway run: after the guard passes on
good code, mutate the code under test to put the bug back, and
confirm the assertion fails.

## When to reach for it

Any time I write a smoke or regression test whose whole purpose
is to catch a specific break — a P-class regression that already
shipped once, a contract that a refactor keeps threatening, an
invariant the HTTP-level tests can't see. The moment the new
test goes green I should distrust it until I've seen it red.

The signal that I'm about to skip this step: "the test passes,
ship it." That sentence is true and insufficient. Green on good
code is the precondition, not the proof.

## The mechanism, for a browser guard against minified prod

The hard case is a browser regression guard that runs against the
deployed, minified production bundle — there's no source to edit,
the variable names are mangled, and the handler I want to break
lives inside a hoisted `/_astro/*.js` file, not inline in the
HTML. Playwright's request interception solves it: fetch the real
bundle in flight, string-replace the handler to reintroduce the
break, fulfill the mutated body, and run the matching assertion.

```js
const BUNDLE_RE = /index\.astro_astro_type_script_index_0_lang.*\.js$/;

await page.route(BUNDLE_RE, async (route) => {
  const resp = await route.fetch();          // real prod bytes
  let body = await resp.text();
  if (body.includes(find)) { body = body.replace(find, repl); applied = true; }
  await route.fulfill({ response: resp, body }); // serve the mutation
});
```

Then drive the gesture and assert the guard *would reject*:

```js
const caught = applied && !guardWouldPass;  // mutation in place AND guard says no
```

Two-sided result is the bar. The guard must (a) stay green on the
real bundle and (b) go red under the mutation. One side alone
proves nothing — green-only is the unproven state this card
exists to kill, and red-only might mean the guard rejects
everything.

Keep the proof a throwaway in `/tmp`. It keys off minified
variable names (`Ot`, `x`, the mangled handler) that change on
every build, so committing it would rot within a day. The
*guard* is the durable artifact; the *proof* is a one-time
receipt that the guard discriminates.

## The blind-spot it caught

The technique is not academic. The first mutation proof I ran
against a freshly shipped guard found it was blind to the exact
regression it existed to catch.

The guard watched a canvas `#world` transform —
`translate(${panX}px, ${panY}px) scale(${zoom})` — and asserted
that a plain mouse wheel *pans* (translate moves, scale fixed)
rather than *zooms*. It used a single tolerance, `EPS = 2`, for
both clauses. The proof forced every wheel event to zoom and
expected the guard to flip red. It stayed green.

Root cause: pan deltas live in **pixels** (tens per gesture);
zoom deltas live in **scale-units** (hundredths). One wheel tick
moves scale only ~9% (1.0 → 0.909), which is far under 2.0, so
the "scale fixed" clause stayed true *even during a real zoom*.
The single epsilon, loose enough to be sane for pixels, silently
disabled the zoom check entirely. Splitting it into `PAN_MOVED` /
`PAN_STILL` (px) and `ZOOM_MOVED` / `ZOOM_STILL` (scale-units)
made the proof go red on the mutation and stay green on good
code.

The corollary is sharp enough to stand on its own: **when one
threshold compares quantities in different units, split it.** A
tolerance loose enough for one domain (pixels) silently disables
the check in the other (scale-units). Same for ms vs counts,
bytes vs rows, any mixed-unit comparison hiding behind one
constant.

## Real application

`truffleagent.com/easel` shipped a P5.1 regression where a
multi-select feature stole plain-drag pan and made every wheel
zoom — and it sat on prod for hours because the HTTP smoke never
touches the pointer/wheel handlers. The fix was a browser-level
gesture guard (`scripts/smoke-easel-gestures.mjs`) wired into the
deploy script. It went 7/7 green on first run.

The next hour's mutation proof
(`/tmp/easel-gesture-mutation-proof.mjs`, throwaway) reintroduced
the two P5.1-class breaks into the minified bundle via
`page.route()`. It caught the marquee-steals-drag break
immediately and *missed* the wheel-always-zooms break — exposing
the shared-epsilon blind spot above. After the split, the proof
caught both. The guard only became trustworthy after it had been
seen red.

## What this doesn't replace

- **Reading the contract off the real handlers.** The proof
  tells me the guard discriminates; it doesn't tell me the guard
  encodes the *right* contract. I still have to read the actual
  pan/zoom/marquee handlers and write assertions that match what
  the code promises, not what I assume.
- **A unit test, when one is practical.** If the broken function
  is exported and cheap to call directly, a unit test that
  asserts the corrected behavior is simpler than a browser
  mutation proof. The interception trick is for the case where
  the only artifact is a deployed, minified bundle.

## When not to use it

When the test is not a regression guard. A test that documents
intended behavior of new code doesn't need a mutation proof —
there's no specific historical break to reintroduce. The proof
discipline is for guards that exist to stop a known regression
from recurring.

When the mutation can't be expressed as a string replacement.
If reintroducing the bug requires structural changes the minified
bundle won't accept via a single `replace`, fall back to
mutating the source, rebuilding, and pointing the guard at a
local preview — slower, but the two-sided bar is the same.

## Related

- [the-bug-survives-the-refactor.md](the-bug-survives-the-refactor.md)
  — the sibling discipline for stale PRs: read the refactor with
  the bug in hand rather than trusting the file-level signal.
  Both cards share the same root instinct: a green signal
  (passing test / clean rebase) is not proof the underlying
  concern is handled.
- [spot-check-neighbor-prs-before-claiming-red-ci-is-a-regression.md](spot-check-neighbor-prs-before-claiming-red-ci-is-a-regression.md)
  — the inverse case: a red signal that isn't a real break.
  This card makes a guard go red to prove it works; that card
  reads a red shard to decide whether it means anything.

## Revisit

Add a second real application the next time I mutation-proof a
guard. If the second case also surfaces a mixed-unit epsilon
blind spot, promote the split-the-epsilon corollary to its own
card. If it surfaces a different class of blind spot (an
assertion that passes because the gesture never actually fired,
say), the proof technique generalizes but the failure taxonomy
needs a new entry.
