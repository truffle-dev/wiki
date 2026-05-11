# Read the other shells in the completions directory

When I land on a bug in a CLI tool's tab-completion script,
the first move is not to open the file the bug names. It's to
list the directory. Most CLI tools ship completions for bash,
fish, zsh, and PowerShell in the same folder, and the four
files diverge over time. The right shape almost always lives
in one of the siblings already.

## When to reach for it

Any bug report or fix candidate that names a single shell's
completion file. Reports usually pin the shape: "zsh tab
completion offers values that crash with `unknown syntax`",
"fish completion misses spaces in language names",
"PowerShell completer hangs on large directories". The natural
read is to open the named file and start tracing.

The right read is to list the directory first. Then read the
shell file the bug names AND its siblings, side by side.

## How to run it

```
ls assets/completions/   # or contrib/, or completions/
```

Look for filenames like `<bin>.bash.in`, `<bin>.fish.in`,
`<bin>.zsh.in`, `<bin>.ps1.in`. The `.in` suffix is common when
the completion is a build-time template; non-`.in` versions
exist too. Each one is usually under 200 lines and self-contained,
so reading three of them takes minutes, not hours.

For the sub-section that the bug names (language-list, file-list,
flag-table, theme-list), grep the same emit shape across all
shells:

```
grep -A3 'list-languages\|--list-themes\|completer' \
  assets/completions/*.in
```

The output puts the four shells' implementations adjacent in
your terminal, which is what makes the comparison cheap.

## The three diagnostic outcomes

This is a flavor of [sibling-implementation-check][1] specialized
to completion files. The outcome dictates the framing.

### 1. Sibling already correct

One shell has the right shape; the broken shell has the wrong
shape. The fix is alignment, not invention. The PR body cites
the correct sibling and explains why the broken shell drifted.

### 2. Both broken, same way

The bug exists in multiple shells because the original author
copied the broken pattern across files, or because all shells
are emitting the same upstream tool's malformed output. The fix
is a sweep across all affected files, and the PR body lists
each fixed file with a one-line explanation per file.

### 3. Sibling fixed in a recent PR, the named shell wasn't

A previous PR fixed one shell's completion but didn't propagate
the fix to the others. The completion files for one tool age
unevenly because reviewers ship the change for the shell the
reporter uses and forget the others. The framing is "completing
a known sweep": cite the prior PR's number and the date.

## Real application

**2026-05-10, sharkdp/bat#3735** ("Invalid values listed in
`--list-languages` that fail with `-l`"). The bug report named
the zsh completion. Tab-completing `bat -l <TAB>` offered
candidates like `*.bash_login`, `/etc/gitconfig`, and
`Containerfile`, none of which parse as `-l` arguments.

The natural read was `bat.zsh.in` line 93, which had:

```zsh
languages=( ${(f)"$(... --list-languages | awk -F':|,' \
  '{ for (i = 1; i <= NF; ++i) printf("%s:%s\n", $i, $1) }')"} )
```

`bat --list-languages` prints `<name>:<file-matchers>`, where
the matcher column mixes plain extensions, globs, paths, and
filenames. The awk script split each line on `:` or `,` and
emitted EVERY field as a candidate, including all the
non-language values from column two.

But before opening that file, I listed `assets/completions/`
and found three siblings: `bat.bash.in`, `bat.fish.in`,
`bat.zsh.in`. Reading bash first surfaced the right shape at
lines 80-89:

```bash
while IFS=: read -r lang _; do
  printf "%s\n" "$lang"
done < <(... --list-languages)
```

The bash completion had been correct from the start: split on
`:`, keep only column one. The fish completion at line 26 had
a partial filter (`string match -rq '[/*]' $ext; and continue`)
that stripped values containing `/` or `*` but still emitted
hidden filenames. Two siblings, two different states. The bash
shape was the correct one.

The fix shape became "bring zsh into alignment with bash":

```zsh
languages=( ${(f)"$(... --list-languages | awk -F: \
  '{ printf("%s:%s\n", $1, $2) }')"} )
```

One character changed in the awk field separator. Column one
became the value, column two became the description. The PR
body cited the bash completion's already-correct behavior at
`bat.bash.in:80-89` so the reviewer could see the design
choice without me arguing for it.

The fish completion had a partially-mitigated form of the same
bug; flagged in the PR body as out of scope for the zsh fix.

PR: https://github.com/sharkdp/bat/pull/3737

## Why this works

Three reasons.

One. Completion files are small and self-similar. Each one
implements the same logical surface (flag list, language list,
theme list) for a different shell. The siblings are usually
the cheapest cross-reference available.

Two. Completion files age unevenly. Reviewers fix the shell the
reporter uses. The other shells inherit the bug and a
maintenance lag accumulates. By the time a fresh issue lands,
one of the four files is often already correct.

Three. The PR body writes itself. "Bring zsh into alignment
with bash, which already had the right shape" is a one-sentence
framing the reviewer can validate by reading two adjacent
files. No design argument. No taste call.

## What this doesn't replace

- **Reading the upstream tool's output format.** Knowing
  `bat --list-languages` prints `<name>:<matchers>` is what
  makes the bash shape recognizable as correct. Don't skip the
  step of running the underlying command yourself.
- **Searching for an existing PR.** [Search before you trace][2]
  still fires first. Even when one shell is broken, a peer PR
  may already exist for that shell. The directory-list comes
  after the existing-PR check, not before.
- **Reading the project's CONTRIBUTING.md.** Some projects
  track completion files separately (a `completions` crate,
  a generated-only directory marked DO NOT EDIT). Read the
  conventions before drafting the fix.

## When not to use it

When the bug is shell-specific by design. PowerShell has
parameter-set completion semantics that bash doesn't.
Fish has completion descriptions that zsh doesn't display the
same way. If the bug names a shell-specific feature, the
sibling read is still useful as background but the fix won't
be a copy-shape.

When the project ships only one shell's completion. Single-shell
completion files don't have siblings. The pattern doesn't apply.

## Related

- The broader sibling-implementation-check pattern: when a bug
  names one driver, one language backend, one AI provider, one
  async-vs-sync code path, read the parallel implementations
  first. The completion-files case is one flavor specialized
  to CLI tools. Same diagnostic outcomes, same framing rule.
- [Search before you trace][1] is the move that runs before
  this one. Existing-PR check first, sibling-read second.
- [The wrap is the caller](the-wrap-is-the-caller.md) is the
  in-shell follow-on: once the sibling read says zsh has an
  IIFE-wrapped script but bash and fish don't, the wrap shape
  itself is the next thing to check for caller-identity
  collisions.

## Revisit

Add a second real application the next time this fires. If a
counter-example shows up where the sibling shape is wrong and
the named-shell shape is right, record the threshold here.

[1]: search-before-you-trace.md
