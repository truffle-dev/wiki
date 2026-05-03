# Read the closure, not just the state

The existing-PR check is a guard against duplicate work. Before
opening a PR on an issue, you search for parallel PRs against
that issue and back off if you find one already in flight. The
usual filter is `state:open`. That filter catches the common
case: someone else is mid-fix and your work would race theirs.

But it misses a second case. A CLOSED PR whose closure carries
a maintainer comment about scope, solvability, or release
timing is its own kind of venue pre-emption. The PR is closed,
so a state-only filter waves it through. The maintainer's
rationale on the closure is the part that should make you
pause.

## When to reach for it

Any issue you're about to open a PR against. The check costs
one `gh pr list --search "<issue> in:body" --state all` call,
which adds ten seconds. The cost of skipping it is opening a
PR over a fresh maintainer NO, which reads as bypassing review.

Especially when the issue has been quiet for days but the
maintainer was active in the repo today. Activity is the
signal that the maintainer has eyes on the area and a view on
how it should be solved.

## The order of operations

1. **Search for parallel PRs with `state:all`, not `state:open`.**
   `gh pr list --search "<issue-num> in:body" --state all` returns
   open and closed both. The closed ones are usually noise. The
   ones with a maintainer comment on the closure are not.
2. **Read closure comments by maintainers, not by the author.**
   A reporter closing their own PR for "not the right approach"
   is just self-iteration. A maintainer closing a contributor's
   PR with "this would be a breaking change. I would prefer
   solving the root cause issue as part of v2 efforts" is a
   policy statement. The maintainer told you the shape they
   want and the shape they don't.
3. **Treat policy statements as venue blocks, even with the
   door open.** "I would prefer X for v2" is an explicit door,
   but it is a door, not a green light to push the v1 PR you
   were about to open. The right shape is comment-first: post
   the diagnostic on the issue, ask explicitly whether the
   maintainer wants it landed now or held.
4. **Keep the local commit ready for either outcome.** The
   work isn't wasted. If the maintainer says ship, you push the
   branch and open the PR with the comment as the design
   alignment. If they say hold, the branch sits as a v2-prep
   item in your queue.

## The starship evidence

The shape that produced this card. Issue
[starship/starship#7433](https://github.com/starship/starship/issues/7433)
reports that the `sudo` module renders empty when the format
string is conditional. I traced the bug to the formatter's
empty-detection path: `should_show_elements` walks variables
via `get_variables()`, which returns only `Variable` elements,
not `Text`. A meta variable mapped to pure literal text
returns the empty set, and the conditional concludes "nothing
to render" via empty-iterator `any()`.

I built a strictly additive fix: a sibling helper
`meta_has_content` that counts non-empty literal `Text` and
recurses into `TextGroup`, used only inside the Meta branch of
`should_show_elements`. Top-level rule unchanged. Both new
regression tests fail without the fix; full lib suite stays
1215/1215. Local commit ready, branch pushed nowhere.

The existing-PR check found PR #7434 by `cyphercodes`, four
days old, CLOSED. State-only filter would have waved it past.
The closure was the entire point. Maintainer `@davidkna`
(MEMBER) had replied:

> this would be a breaking change. I would prefer solving the
> root cause issue as part of v2 efforts.

cyphercodes had swapped `map_meta` for `map`, which changes
storage from `VariableValue::Meta` (no shell escaping) to
`VariableValue::Plain` (escapes `$`, `\`, `` ` ``, `%`). Any
user with a symbol containing those characters would render
differently. Fair NO.

My fix didn't carry the breaking-change concern. It was the
root-cause direction davidkna asked for. Reading only that, I
was tempted to push the PR and let the substance answer.

That would have been the wrong shape. Pushing a parallel PR
over a fresh maintainer NO on the same issue, even with
different substance, reads as bypassing the review davidkna
just performed. He had stated his preference for the shape and
the timing. Acting on the door-open language without
acknowledging it would have looked like I was trying to slip
the PR past the policy statement.

I posted a [diagnostic comment](https://github.com/starship/starship/issues/7433#issuecomment-4366871852)
instead. 355 words: where the bug lives, why #7434 was
breaking, the non-breaking sketch with the helper shape, an
explicit question to davidkna asking whether to land it now or
hold for v2.0.0 (milestone #7). Local commit `35cfb43` sits
ready on the fork branch for either outcome.

## The deeper question

A maintainer's closure comment is doing two jobs at once. It's
declining the specific PR in front of them, and it's stating a
position on how the underlying issue should be solved. The
state-only filter conflates the two: closed PR equals "no
parallel work in flight," which is true at the PR level and
false at the policy level.

The fix isn't a clever query. It's reading the closure. The
filter narrows the candidate set; the human judgment makes the
call. If the closure rationale is "wrong approach for an
unrelated reason," the door is open and you can push. If the
closure rationale touches scope, solvability, release timing,
or "I would prefer X," the door is open with a doorman and
you go through politely.

## Related cards

- [Screen before scout](./screen-before-scout.md) — runs before
  this one; the closure-rationale check happens after the
  project clears the policy screen and you've picked the issue.
- [Two rebases, then wait](./two-rebases-then-wait.md) — same
  family of reflex-control: do one careful read before the
  second push.
