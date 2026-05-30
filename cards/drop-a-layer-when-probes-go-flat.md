# Drop a layer when probes go flat

When the symptom is at one layer but the producing substitution
is at another, same-layer probes return the same answer no
matter how I vary them. The honest move is to recognize the
flat probe as the signal and drop a layer down the stack.

This card is for the moment when CSS overrides change nothing
about a visual bug, or when shell flags change nothing about a
process behavior, or when query parameters change nothing about
a request outcome. Probes that ought to move the result and
don't are pointing at the wrong layer.

## When to reach for it

I'm debugging something visible (a rendered glyph, a CLI
output, an API response) and I'm probing at the layer the
symptom shows up in. Each probe either confirms the bug is
present or comes back identical. The probes are not narrowing
the problem; they're echoing the same answer. The reflex is to
try one more probe at the same layer. The fix is to step down a
layer.

## The shape

The web rendering stack reads top to bottom like this:

1. **Text source.** The MDX, JSX, HTML, or template that
   declared the literal characters.
2. **DOM tree.** What the document looks like after parsers and
   frameworks run. `document.querySelector` reaches this layer.
3. **CSS layer.** Element styling: width, padding, font-family,
   color, font-feature-settings, font-variant-ligatures,
   text-rendering. Probes here are CSS overrides.
4. **OpenType shaping.** GSUB lookups (`liga`, `dlig`, `clig`,
   `calt`, `rlig`, `ccmp`) translate sequences of input
   codepoints into one or more glyph IDs. CSS hands off to the
   shaper before the glyph reaches the painter. Probes here
   are font-feature-settings toggles per feature.
5. **Font binary.** `cmap` maps codepoints to glyph IDs;
   the glyph table holds the outlines; the `name` table holds
   PostScript names. Hardcoded mappings (a codepoint mapped to
   the "wrong" glyph in cmap) live here and can't be reached
   by CSS or feature flags.

When a CSS override doesn't change the visible behavior, the
substitution happened before CSS saw the glyph. That's layer
4 or 5. The fix at the CSS layer can still be valid (turning
off `liga` is a perfectly real fix for a `liga` bug), but the
explanation is wrong if I claim the bug is "a CSS issue."

The same ladder exists for other stacks:

- **Shell pipelines.** Source script → shell expansion → env
  inheritance → child process → libc → syscall. When changing
  the script doesn't change behavior, drop to shell expansion
  (`set -x`). When that's flat, drop to env. When that's flat,
  drop to libc (`strace`).
- **HTTP requests.** Application code → HTTP client → TLS layer
  → TCP layer. When the client retries identically, drop to TLS
  to check certificate or SNI mismatch. When that's clean, drop
  to TCP to check route or MTU.

The point isn't the specific stacks. It's the recognition that
when probes don't move the answer, the answer is being made at
a layer the probes don't reach.

## The probe-to-fix gap

Probing finds the layer. Fixing happens wherever the smallest
durable change is. These are usually the same layer, but not
always.

A `liga` GSUB bug discovered via OpenType-feature toggle can be
fixed three places:

1. **CSS layer.** `font-feature-settings: "liga" 0` in a
   site-wide stylesheet. Fast, defensive, doesn't depend on
   font shipping a fix.
2. **Font source.** Remove the substitution from the GSUB
   table in the source repo. Slow, but the right durable fix
   for everyone using the font.
3. **Font binary.** Rebuild and republish so consumers get the
   shipped fix. The source revert is useless if the binary
   still has the old lookup.

In a real chain, fixing the source layer doesn't help downstream
until the binary republishes. So the discovery of the producing
layer is one thing; the recommendation of where to fix is
another. Both belong in the report.

## The two outcomes

Either the dropped-layer probe identifies the producing
substitution, in which case the report and the fix both name it
honestly, or the dropped-layer probe is also flat, in which
case drop another layer. The signal is the same at every level:
flat probes mean wrong layer.

The failure mode is settling for a fix without naming the
producing layer. The fix may even be correct, but the report is
a guess dressed as a finding. A maintainer who reads "X CSS
class fixed it" and a maintainer who reads "the X CSS class
disables the `liga` GSUB lookup that produced the visible
substitution at the shaper layer; the fix is fine as
defense-in-depth while the font binary is rebuilt" make
different decisions about how long to keep the fix in place.
