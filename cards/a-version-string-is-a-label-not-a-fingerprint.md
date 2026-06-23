# A version string is a label, not a fingerprint

A version string identifies what the producer remembered to
stamp, not the bytes you are holding. The stamp is written by
hand somewhere in the build, and a build can change the bytes
without touching the line that writes the stamp. When that
happens, three genuinely different artifacts will all introduce
themselves with the same name, and every tool that trusts the
name will treat them as one thing. If you need to know which
build something actually is, the only honest answer comes from
hashing the bytes.

## When to reach for it

You are reasoning about which build of an artifact you have, or
which build someone else has, and the evidence you are leaning
on is a self-reported version: a font's `name` table, a
binary's `--version` output, a package's `__version__`, an
image tag, a `User-Agent`. The string looks authoritative, it
matches what you expected, and you are about to conclude that
two artifacts are the same build (or that one is the build that
contains a fix) because their version strings agree.

## The shape

Two facts collide.

1. **The version stamp and the build are separate steps.** The
   bytes come out of a compiler, a font compiler, a bundler.
   The version string comes out of whatever line of code or
   config happens to write it. Nothing in the pipeline forces
   those two to move together. A maintainer can ship a real
   content change and simply not bump the stamp, because the
   stamp lives in a metadata file they did not edit this time.
2. **Everything downstream reads the stamp, not the bytes.**
   Caches, dependency resolvers, bug-triage threads, "is this
   the patched build" checks. They all compare the cheap label
   because the label is right there and hashing feels like
   work. So a stale or frozen stamp propagates a false identity
   through every system that trusts it.

The collision: several distinct artifacts present one identity,
and a conclusion built on that identity ("these are the same
build" or "this is the build with the fix") is confidently
wrong about bytes it never looked at.

## The discriminator

Hash the bytes. `sha256sum` on each artifact answers the
question the version string only pretended to answer. Two equal
hashes are the same build; two different hashes are different
builds, whatever their labels say. When the artifacts live in
git, you can do this without downloading anything:
`git show "<tag>:<path>" | sha256sum` hashes the file as it
existed at a tag, and `git log -1 --format="%h %ad %s" <tag> --
<path>` names the commit that last touched those bytes. Now you
have an identity pinned to content and a provenance pinned to a
commit, instead of a label pinned to whatever the producer
remembered to type.

## Real applications

### vercel/geist-font#238 (2026-06-23)

The thread turned on whether the font binary had actually
changed across releases, since the embedded version read
`Version 1.700` at more than one tag. Trusting the string, you
would say the font was untouched. Hashing the bytes said
otherwise: the `GeistMono-Regular.ttf` shipped at 1.7.0
(`48fced4d5ccd`), at 1.7.1 and 1.7.2 (`5a0de4b3d54a`, identical
to each other), and at 1.8.0 (`bbb6715a4069`) were three
distinct binaries, and all three introduced themselves as
`Version 1.700`. The 1.8.0 bytes were the output of the
"Fix style name, double encode math greeks" build (`5f44fc0`),
a real content change that never moved the stamp. The version
string had frozen at 1.700 while the bytes changed underneath
it three times. The hashes were the only honest account of what
shipped.

## When not to use it

- **The label is the thing you actually care about.** If you
  are testing how your software behaves when a user reports
  `version: 1.700`, the self-reported string is exactly the
  input under test, byte-identity included or not. You want the
  label precisely because it is what the world sees.
- **The producer's release discipline is known-tight.** Some
  projects gate every byte change behind a version bump in CI
  and would fail the build otherwise. There the stamp and the
  bytes really do move together, and the label is a faithful
  proxy. Know that this is a property you verified once, not
  one you assume.
- **Nothing downstream branches on identity.** If you are just
  reading a version for a human to glance at, the cost of a
  stale label is a shrug. The hash matters when a decision
  rides on which build it is.

## Related

- [A 200 is not a passing health check](a-200-is-not-a-passing-health-check.md)
  is the same caution in the network layer: the status code is
  a claim the server chose to make, not proof the body behind
  it is healthy. Here the version string is the claim, the
  bytes are the body.
- [pip --pre is not the project's nightly](pip-pre-is-not-the-nightly.md)
  is the adjacent failure: there the index hands you the wrong
  artifact, here the right artifact hands you the wrong label.
  Resolution lies about which file; identity lies about which
  build. The upload-time and dev-counter checks in that card
  are version-string distrust applied to the index metadata.
- [Re-verify substrate at HEAD](substrate-moves-re-verify-at-head.md)
  is the time-axis version: evidence goes stale between
  gathering and publishing. A frozen version stamp is evidence
  that was stale the moment it was written.

## Revisit

Add the container-image and Go-module analogues when they fire
in practice. A `:latest` tag and a mutable image digest have
exactly this split (the tag is the label, the digest is the
fingerprint), and a Go module's pseudo-version encodes the
commit hash precisely to close this gap. If a second real
application lands outside the font/binary world, generalize the
discriminator beyond `sha256sum` to whichever content-address
the ecosystem already ships.
