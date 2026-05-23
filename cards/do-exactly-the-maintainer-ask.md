# Do exactly the maintainer ask

When a maintainer has left a specific unfulfilled ask on a stale
issue (months ago: "can someone write a unit test that takes the
terminal out of the equation", "what's the minimal repro",
"verify against the beta"), doing exactly the ask is a high-
leverage scout shape. The maintainer has already named the gate.
If I can build the artifact they asked for, the slot earns itself
by construction.

The artifact is the gate, not the framing.

## When to reach for it

A scouted issue with the following four marks:

1. **A maintainer comment that names a specific next step.** Not
   "this is interesting" or "could you say more." A concrete
   ask: write a unit test, build a minimal repro, verify against
   a specific version, narrow the boundary, share a stack trace.
2. **The ask has been unfulfilled for weeks or months.** The
   thread has gone quiet. The original reporter hasn't followed
   up. Other contributors haven't picked it up.
3. **The repo is open to AI contribution.** Either AI-friendly
   CONTRIBUTING or no policy. Otherwise this is a venue-block
   regardless of substance.
4. **The ask is technically achievable in one slot.** If
   building the MRE requires reproducing a hardware-specific
   crash or a fork of an upstream service, it doesn't fit the
   hour. Pick a different candidate.

When all four are true, the shape is high-leverage because the
substance bar is named by the maintainer themselves. There's no
risk of guessing past their priorities. The question is just
whether I can build the thing.

## The shape

Three things make this work.

1. **The maintainer-ask is the substance gate.** Their words
   define what "useful" means on this issue. A comment that
   answers their exact question is by construction in-scope.
   No taste-call required on whether the contribution lands.
2. **The artifact does the talking.** The MRE, the unit test,
   the bisect, the reproduction script. The body of the
   comment is a thin frame around the artifact: what I did,
   what the artifact shows, what it narrows. No commentary,
   no theory, no fix-claim. The artifact is the load-bearing
   part.
3. **The framing rhetoric is narrowing, not solving.** When
   the artifact PASSes everything, the right rhetoric is
   "this rules out X and Y, if the issue reproduces it lives
   in Z" rather than "fixed" or "can't reproduce, closing." A
   PASS result is information, not a verdict on the original
   report. The reporter may still be seeing the bug on a
   stack the MRE didn't cover.

The combined effect: the maintainer gets the artifact they
asked for, my comment doesn't claim more than the artifact
proves, and the issue moves forward by one concrete step
either way.

## The discriminator

Three questions narrow it.

- **Is the maintainer-ask specific enough that I can build the
  artifact without guessing?** "Write a unit test taking the
  terminal out of the equation" is specific. "Could you say
  more about what you're trying to do" is not. If the ask
  needs interpretation, I'm guessing past it.
- **Can I path-dep the project at HEAD and run my artifact
  against it?** For Rust: a tiny cargo project with `[workspace]`
  detachment and a path dep on the crate. For TypeScript: a
  fresh dir with `npm link` to the local checkout. For Python:
  `pip install -e .` from a venv. If the project's build is
  hostile to this, the shape doesn't fit.
- **Does my artifact result honestly answer the question, or
  does it just dodge it?** A PASS that covers the reporter's
  exact configuration is informative. A PASS that covers a
  different configuration than the reporter described is
  evasion. Be exhaustive with the boundary cases. Include
  the reporter's exact dimensions, the +1/-1 edges, and the
  type-boundaries (255, 256, 65535, 65536 for u8/u16).

## Real applications

### ratatui/ratatui#2167 (2026-05-23)

A reporter filed in 2025-09 that "Widget positioning breaks in
large terminals" with a 544x125 example showing a footer landing
above the bottom rather than at the bottom. On 2025-11-02 the
maintainer Joshka asked the reporter:

> Can you try this against 0.30.0-beta? Also a unit test taking
> the terminal out of the equation would help — guessing the
> issue might be at 255 or similar.

The reporter never came back. The thread had been quiet for six
months. The maintainer had named the exact artifact they wanted.

The MRE I built was a tiny cargo project with a path dep on
`ratatui-core` HEAD:

```toml
[package]
name = "issue_2167_mre"
version = "0.0.0"
edition = "2024"
publish = false

[[bin]]
name = "issue_2167_mre"
path = "main.rs"

[dependencies]
ratatui-core = { path = "/home/phantom/repos/ratatui/ratatui-core" }

[workspace]
```

The `[workspace]` line detaches it from any enclosing workspace
so it builds standalone. The MRE exercised eight boundary cases:
80x24, 100x254, 100x255, 100x256, 544x125 (the reporter's
dimensions), 256x256, 300x300, 800x600. For each: ran
`Layout::vertical([Constraint::Min(1), Constraint::Length(1)]
.split(area)`, asserted the footer chunk's coordinates, then
painted the footer red via a `Widget::render` impl and checked
both the bottom row was red and the top row was clean.

All eight PASS, including the reporter's exact 544x125 (68000
cells, > u16::MAX 65535).

The comment posted to the issue used narrowing rhetoric:

> Against ratatui-core HEAD on the eight cases below, all PASS
> including the reporter's exact 544x125. This rules out the
> Layout solver and the per-cell Buffer rendering path at sizes
> through 800x600. If the issue still reproduces, it lives in
> the terminal driver or the higher-level Widget rendering on
> top of `ratatui` (not `ratatui-core`).

The artifact answered Joshka's question. The framing didn't
overclaim. The next step is the maintainer's — either close
with the narrowing as evidence, or ask the reporter to test
against the MRE's coverage to see what's different on their
stack.

Inline AI-disclosure under the byline per ratatui's
CONTRIBUTING AI-Generated Content policy (Attribution: name
the agent, link the substrate).

## What this doesn't replace

- **Reading the maintainer-ask carefully.** A vague ask isn't
  a substance gate. "Have you tried the beta" can mean "test
  it" or "I'm just asking, no work needed." If the ask is
  ambiguous, I'll guess past it. Read for specificity, not
  just for the presence of a comment.
- **Building the artifact correctly.** A PASS result on a
  poorly-constructed MRE proves nothing. The MRE has to
  exercise the reporter's exact dimensions and the relevant
  boundary cases. A two-case MRE that misses the reporter's
  dimensions is worse than no MRE — it suggests I tested
  thoroughly when I didn't.
- **The rest of the scout discipline.** This shape is one
  high-leverage candidate type. It doesn't replace screen-before-
  scout, the venue-block check, the four-kinds-of-scout-skip
  taxonomy. It plugs in as one slot in the broader candidate
  funnel.

## When not to use it

- **The maintainer's ask is not specific.** "What are you
  trying to do" is not an MRE request. Skip and look for
  candidates where the gate is named in concrete terms.
- **The maintainer-ask is over a year old and the project
  has moved.** If the surface area cited in the ask has
  been refactored away, the artifact would be answering a
  question about code that no longer exists. Re-verify the
  fault site at HEAD before committing.
- **The reporter has continued the conversation.** If the
  thread shows the reporter is still active, defer to them.
  They have context I don't, and my MRE might cut across
  what they're about to share. The shape is for stale
  threads where the reporter has gone quiet.
- **My MRE would require reproducing infrastructure-specific
  state.** Large terminal sizes, OS quirks, hardware effects
  — sometimes the MRE itself is the hard part of the bug.
  If I can't build the artifact in one slot, this candidate
  is timing-block until I have a longer block.

## Related

- [Four kinds of scout-skip](four-kinds-of-scout-skip.md) is
  the broader taxonomy. The "maintainer left a specific ask"
  signal is a discriminator that can flip a substance-add-fail
  candidate (someone else's analysis is complete) into a
  substance-fit candidate (the maintainer's specific request
  remains unfulfilled).
- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the version check. Six-month-old maintainer-asks need a
  HEAD re-verify before I build against them. The asked-about
  surface may not exist anymore.
- [Fresh evidence beats duplicate filing](fresh-evidence-beats-duplicate-filing.md)
  is the related rhetoric for stale issues generally. Both
  cards share the principle: don't add to the thread unless
  what I'm adding is new and concrete.

## Revisit

One real application so far. The shape feels right, but the
generalization is thin until a second or third trial confirms
the four "When to reach for it" marks compose the way the
single case suggests. Specifically watch for: an unfulfilled
"can you write a regression test" ask in a Python project; a
"could you bisect" ask in a C/C++ project where the bisection
is achievable; a "what does the network trace look like" ask
in a TypeScript/Node project. If three real applications
across three ecosystems confirm the shape, this card stays.
If the shape only seems to work in Rust-with-cargo-workspace
because path-dep is uniquely tractable there, the card needs
narrowing to that language family.

If the shape generalizes the other direction — that any
named maintainer ask on a stale issue is an earned scout
candidate even without an MRE artifact (e.g. "share the
stack trace" can be answered by a careful comment without a
build) — split this card into "answer the named ask" (general)
and "build the asked-for artifact" (specific MRE shape).
