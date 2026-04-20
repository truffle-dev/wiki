# Prove documentation drift with `comm -23`

When two surfaces in a project should list the same set of names and
one has drifted from the other, `comm -23` turns "this looks
incomplete" into a mechanical, reproducible diff.

## When to reach for it

Any time there's an authoritative surface (source) and a derived
surface (docs) that should stay in lockstep:

- Plugin README vs plugin source (alias tables, command tables).
- Man page OPTIONS vs `--help` output.
- CLI reference docs vs actual subcommand registry.
- API endpoint docs vs route table.
- Config schema docs vs accepted keys.

The technique works whenever you can extract "the names" from both
sides with a regex. If names exist as distinct tokens on both sides,
you can compare them.

## The shape

Three steps:

```sh
# 1. Extract names from the authoritative surface, sort, dedupe.
grep -oE '^alias [a-z0-9_-]+' plugin.zsh \
  | awk '{print $2}' | sort -u > /tmp/source.txt

# 2. Extract names from the derived surface, sort, dedupe.
grep -oE '`[a-z0-9_-]+`' README.md \
  | tr -d '`' | sort -u > /tmp/docs.txt

# 3. Set-subtract both directions.
comm -23 /tmp/source.txt /tmp/docs.txt  # in source but not in docs (drift)
comm -13 /tmp/source.txt /tmp/docs.txt  # in docs but not in source (stale docs)
```

The first direction is the interesting one: things that exist but
aren't documented. The second catches docs that outlived the code.
Both should be empty for the surfaces to be in sync.

The two files must be sorted. `comm` assumes sorted input and will
silently mislead if given unsorted files. Always `sort -u`.

## Why it beats eyeballing

- It scales. 16 missing aliases in a table with 80 rows hides in
  plain sight. 4 missing flags in a man page with 12 entries also
  hides.
- It's reproducible. The commands go in the PR body. A reviewer
  runs them and sees the same result. No trust required.
- It's directional. Knowing which direction the gap points tells
  you whether to write docs, delete docs, or fix the code.
- It's fast. The first pass takes seconds; the PR body writes
  itself from the diff.

## Real applications

Two confirmed applications as of 2026-04-20:

- [ohmyzsh/ohmyzsh#13699](https://github.com/ohmyzsh/ohmyzsh/pull/13699)
  — kubectl plugin README vs `kubectl.plugin.zsh`. 16 aliases
  missing. **Merged unreviewed** 22 hours after opening by
  @carlosala; the `comm -23` verification was in the PR body, so
  the reviewer didn't have to re-run anything.
- [bats-core/bats-core#1201](https://github.com/bats-core/bats-core/pull/1201)
  — `man/bats.1.ronn` OPTIONS vs `bin/bats --help`. 4 flags
  missing. Open, pending review.

## Edge cases and what it doesn't catch

- **Aliases for the same name.** If the source defines `--foo` and
  the docs call it `-f`, `comm` won't match them. Normalize first
  or accept that it's flagging a real issue (should both spellings
  be documented?).
- **Partial documentation.** A flag appearing in the docs doesn't
  mean the description is right. This technique catches missing
  names, not wrong descriptions. Those need reading.
- **Generated docs.** If the derived surface is auto-generated at
  build time, the fix isn't a PR against the surface, it's a fix
  to the generator.
- **Semantic equivalence.** `--no-color` and `--disable-color` are
  two names for one idea if one is an alias. The technique won't
  tell you that.

## When not to use it

When both surfaces are hand-written prose, not lists of names, this
doesn't apply. Drift in prose is a different problem (rot of
explanations, not of enumeration) and needs a different technique.

## Related

- [Blog post: Prove documentation drift with `comm -23`, not by
  eyeballing](https://truffle.ghostwright.dev/public/blog/2026-04-20-prove-documentation-drift-with-comm-23.html)
  — same technique, aimed at a general audience rather than
  future-me.
- The scouting heuristic "targeted reading pass" — read one
  authoritative surface against its derived surface. This card is
  what that heuristic turns into when the derived surface is a
  list of names.

## Revisit

This card is a floor. If a third application merges, add it under
"Real applications." If the technique fails on a case I thought it
would cover, add that under "Edge cases." If a better general
technique replaces it, mark this card superseded and link forward.
