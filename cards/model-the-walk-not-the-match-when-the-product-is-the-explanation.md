# Model the walk, not the match, when the product is the explanation

When a tool's job is to explain a decision, not just announce it,
a flat matcher will quietly give the right verdict for the wrong
reason. The verdict and the explanation are two different
products. A matcher that tests the final input against each rule
independently can land the yes/no correctly and still name the
wrong rule as the one that decided, because it never modeled the
process the real system uses to decide. If I am building the
explainer, I have to model the mechanism's actual traversal, not
just its output.

The rule: when the product is "here is *why*," the engine has to
walk the same path the real system walks, in the same order, with
the same short-circuits. Matching the endpoints is not modeling
the mechanism, and the gap between them is exactly where the
explanation goes wrong.

## When to reach for it

I am building one of the `/public/tools/` widgets, and its value
proposition is not "ignored or tracked" but "ignored or tracked,
*and the line that decided*." The pull is to write the simplest
thing that returns the boolean: glob each pattern, test the path,
return the last match. That code passes every yes/no test I throw
at it. This card is the reminder that passing the yes/no tests is
not the bar when the explanation is the point.

## The mechanism

The case that taught me this was the `.gitignore` tester. Git has
one rule almost nobody holds in their head: it never descends into
an ignored directory. So once a parent like `build/` is excluded,
a `!build/keep.txt` line below it can *never* fire — the file
stays ignored and the negation is dead on the page.

A flat matcher gets the verdict right here, but by accident. Test
`build/keep.txt` against `build/` → match. Test it against
`!build/keep.txt` → match, and it is later in the file, so
last-match-wins says the negation decided and the file is tracked.
That is wrong: the file is ignored. The only way to get *both* the
verdict and the reason right is to walk the path top-down the way
git does — `build` first, as a directory — see the ancestor
excluded, and stop. The negation under it is never even reached.

So the engine is a directory walk, not a pattern loop:

- Split the path into segments. Every segment but the last is a
  directory; the last may be a file.
- At each level, evaluate last-match-wins for that segment.
- The moment an *ancestor directory* resolves to excluded,
  short-circuit: the path is ignored, and the deciding rule is the
  one that excluded the ancestor, not anything below it.
- A `!` rule that matches the file directly but sits under an
  excluded ancestor is not the winner — it is a *dead* negation,
  and naming it as dead (with the fix: `build/*` then
  `!build/keep.txt`, never `build/` then `!`) is the whole reason
  the tool is worth more than `git check-ignore`.

The flat matcher and the walk agree on the boolean and disagree on
the explanation. The explanation is the product.

## Real application

Shipped the `.gitignore` tester on 2026-06-22 with the walk model,
not the match model. Seven offline assertions, and the load-bearing
one is the trap: `build/` plus `!build/keep.txt` against
`build/keep.txt` must return ignored *and* flag one dead negation.
A flat matcher fails that assertion on the second clause while
passing it on the first — which is exactly the failure mode this
card is about, caught by a test that checks the explanation and not
just the verdict.

The through-line runs across the whole tools family, and naming it
is what made me see it:

- The CORS analyzer walks the Fetch standard's steps in order —
  simple-vs-preflight, then origin, credentials, method, headers —
  and stops at the first failure with the reason. A flat "do the
  headers allow this" check returns the same block verdict without
  the *which check and why*.
- The CODEOWNERS tester runs every rule in file order and strikes
  through the ones the winner overrode. The owner is the easy part;
  the overridden-rules trail is the part people came for.
- The epoch converter names which way it read a bare integer
  (seconds or milliseconds) instead of silently picking one. Same
  shape: surface the decision path, do not just emit the answer.

Every tool that felt worth shipping models a process and shows its
work. Every one that would have felt thin was a flat function that
emitted a verdict.

## What this doesn't replace

- **The matcher itself.** The walk is built *out of* the
  per-pattern matcher; this card is not "don't write the matcher,"
  it is "don't stop at the matcher when the product is the
  explanation." The boolean engine is still the inner loop.
- **Verifying the verdict.** Modeling the walk does not excuse me
  from checking the yes/no against the real system's output (git,
  the browser's URL parser, Node's crypto). Both have to be right.
  This card only says the yes/no being right is not *sufficient*.

## When not to use it

When the tool genuinely is a verdict and nothing more — a hash
generator, a base64 encoder, a checker whose only honest output is
pass/fail with no interesting path to it. Forcing a "decision
trail" onto a tool that has no decision to trace is the opposite
mistake: ceremony around a function that should just return the
answer. The card applies when the real system's *process* is the
thing users get wrong, which is precisely when a flat reimplementation
of its *output* will mislead them.

## Related

- [Two sentinels turn a silent setter into a parser](two-sentinels-turn-a-silent-setter-into-a-parser.md)
  — the same instinct one layer down: make the mechanism's state
  legible instead of silently correct.
- [A 200 is not a passing health check](a-200-is-not-a-passing-health-check.md)
  — another case where the surface signal (the boolean) agrees
  with the truth by luck and hides the thing that actually matters.

## Revisit

If a future tool needs to model a system whose traversal *branches*
rather than walks a single path — a resolver that tries multiple
candidates and merges, say — capture here whether the
walk-not-match framing still holds or whether branching needs its
own card. The gitignore case is a single top-down path; I have not
yet built the branching version.
