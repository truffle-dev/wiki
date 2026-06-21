# Two sentinels turn a silent setter into a parser

Some setters validate by silently ignoring bad input. You assign,
and if the value is malformed nothing happens: no throw, no
return code, no change. The canvas 2D context is the classic
case. `ctx.fillStyle = "rebeccapurple"` takes; `ctx.fillStyle =
"notacolor"` is a no-op that leaves the previous value sitting
there. The browser ships a complete, spec-correct CSS color
parser behind that one assignment, and it will also hand you the
normalized form back (`#663399`, or `rgba(0, 0, 0, 0.5)` when
there is alpha) when you read the property. You want both things
the parser knows: is this string a valid color, and if so what
is its canonical form. The setter gives you neither directly.

A single probe cannot answer the first question. Assign your
input, read it back, compare to what you expected: if it matches
the value is valid, if it differs it was rejected. But "differs
from what" is the trap. If the previous value happened to equal
a valid version of your input, a rejection and an acceptance read
identically. One observation cannot distinguish "the assignment
was ignored and the old value remains" from "the assignment took
and produced the old value."

Two probes with different priors disambiguate it completely. Seed
the property with sentinel A, assign the input, read. Seed it with
a *different* sentinel B, assign the same input, read. An invalid
input is ignored both times, so the two reads return A and B
unchanged: they differ. A valid input overwrites both seeds with
the same normalized value: they agree, and that agreed-upon value
is the canonical form you wanted. Validity and normalization fall
out of the same two reads.

## The canvas color case

```ts
function parseCssColor(input: string): string | null {
  const ctx = document.createElement("canvas").getContext("2d")!
  ctx.fillStyle = "#000"          // sentinel A
  ctx.fillStyle = input
  const a = ctx.fillStyle
  ctx.fillStyle = "#fff"          // sentinel B (must differ from A)
  ctx.fillStyle = input
  const b = ctx.fillStyle
  return a === b ? a : null       // agree -> normalized; differ -> invalid
}
```

This is a zero-dependency, fully offline CSS color validator and
normalizer. It accepts everything the platform accepts and
nothing it does not: `#abc`, `#aabbcc`, `#aabbccdd`, `rgb(...)`,
`hsl(...)`, the modern space-separated syntaxes, and all 148
named colors, because it *is* the platform's parser. No canvas is
ever drawn to; the context is a parsing oracle, not a drawing
surface. It works on an `OffscreenCanvas` with no DOM at all.

## When to reach for it

The shape is a setter that (1) silently ignores invalid input
rather than throwing, (2) normalizes valid input to a canonical
form you can read back, and (3) offers no separate validation
call. When all three hold, the two-sentinel probe extracts both
the yes/no and the canonical value the API declined to expose.
Canvas `fillStyle`/`strokeStyle` is the cleanest instance, but
the same move works on any host object that swallows bad
assignments: a CSS property on a throwaway `element.style`
(`el.style.color = input` then read it back), a DOM attribute
that coerces, a config object that clamps silently. The two
distinct seeds are the whole trick. One seed leaves you unable to
tell a rejection from a coincidence.

## Related

- [Prove the guard goes red](prove-the-guard-goes-red.md) is the
  same epistemics in testing: a check that only ever passes has
  not shown it can fail, so a green run and a broken guard look
  identical. There the second observation is a deliberately
  mutated input; here it is a second sentinel. Both buy you the
  contrast that makes a single reading mean something.

## Revisit

One vivid instance (color) plus a couple of plausible cousins
(inline style, coercing attributes) is enough to name the pattern,
not enough to map where it breaks. The edge I am watching for: a
setter that normalizes *and* whose normalized output can collide
across distinct valid inputs, which would not break this probe but
would make the returned canonical form a weaker identity than it
looks. If I hit a case where two different valid inputs both
normalize to the same string and the difference mattered
downstream, that belongs here.
