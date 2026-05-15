# Find the canonical implementation before fixing the bypass

When a bug report names three implementations that all do X wrong,
the temptation is to read the wrong-looking code and fix what's
visibly off. The better first move is to find the implementation
that does X right elsewhere in the codebase. The canonical version
is somewhere; the wrong version is just three callers who forgot it.

The fix is rarely "rewrite the wrong shape from scratch." The fix
is "replace the wrong shape with a call to the helper that already
exists." But you can't do that until you know the helper exists.

## When to reach for it

Any bug report that names parallel implementations: "the gitea,
github, and gitlab adapters all clone repos to the wrong path",
"sqlx postgres returns the right shape but mysql and sqlite return
a string", "the Express adapter coerces query params but Hono and
Fastify pass strings through." The common shape: the wrong version
is reproduced in N places, which means the right version is either
missing entirely (rare) or sitting in one canonical place that the
N callers bypassed (almost always).

Also reach for it when fixing one wrong-looking caller by hand
feels easy. Easy fixes that ignore the canonical pattern produce
a fourth divergent implementation. The next bug report adds your
fix to its list.

## The order of operations

Reverse the obvious order.

1. **Find the canonical implementation first.** Grep the codebase
   for the operation by behavior, not by buggy-symptom. If the bug
   is "clone to the wrong path", grep for `clone` plus `path`. If
   the bug is "query param coercion missing", grep for `parseQuery`
   or whatever the framework calls its helper. The canonical
   implementation usually lives in a CLI handler, a core module,
   or a base class — somewhere a maintainer chose as the source
   of truth.
2. **Read the canonical end-to-end.** Note its full pre/post-
   condition: not just the function it calls, but the setup it
   does first and the side effects it produces. This is the
   contract. The bypassing callers are violating one or more
   parts of this contract.
3. **Compare each parallel implementation against canonical.**
   Sometimes the bypass is "reimplemented the same logic by hand."
   Sometimes it's "called the helper but skipped the setup step."
   Sometimes it's "called a different function that does 80% of
   what the canonical does, missing the 20% that matters." The
   shape of the bypass tells you the shape of the fix.
4. **Then write the fix.** Each caller becomes a call to the
   canonical helper, plus whatever setup the canonical contract
   requires. The fix shrinks. The PR shrinks.

## The Archon evidence

The shape that produced this card. Issue
[coleam00/Archon#1547](https://github.com/coleam00/Archon/issues/1547)
named three webhook adapters (gitea, github, gitlab) that all
cloned repos to the wrong workspace path. The wrong path looked
like `~/.archon/workspaces/owner/repo/` with the repo files at
the root.

Reading the wrong code first would have led to "the path
construction is wrong, let me fix it" — and probably to writing
a new helper inline in each adapter, or worse, fixing the path
template in three places without addressing the missing setup.

Reading the canonical first changed the fix completely. The CLI
clone handler at `packages/core/src/handlers/clone.ts:187,242`
already used `getProjectSourcePath(owner, repo)` (returns
`workspaces/owner/repo/source/`) plus `ensureProjectStructure(owner, repo)`
(creates `source/`, `worktrees/`, `artifacts/`, `logs/` as
siblings). Both helpers were exported from `@archon/paths`, the
same package the adapters already imported. The adapters had
just imported other things from it.

The fix became "in each adapter, replace the manual path
construction with `getProjectSourcePath` and add the
`ensureProjectStructure` call before clone." Six files, +65/-9.
PR [coleam00/Archon#1554](https://github.com/coleam00/Archon/pull/1554).

If I had jumped to "fix the path template", I would have shipped
something that fixed the *visible* symptom (wrong path) without
fixing the *invisible* one (worktree creation broken because the
sibling directories were never created). The reporter would have
filed a follow-up bug.

## The deeper question

Three independent callers all bypassed a helper that was sitting
in a package they already imported. That's not a coincidence; it's
a discoverability problem. Worth flagging in the PR, but not worth
expanding the fix to address. A separate PR could:

- Add a doc comment to `getProjectSourcePath` saying "always pair
  with `ensureProjectStructure`."
- Combine the two helpers into one function that does both, so
  callers can't accidentally skip the setup.
- Add a lint rule or test that flags manual `getArchonWorkspacesPath`
  use inside adapter code.

But that's a change to the helper's API or to the project's lint
config, which usually warrants a separate PR with its own
discussion. The fix-the-bypass PR shouldn't grow to include it.

## Related cards

- [Screen before scout](./screen-before-scout.md) runs before
  this one; the canonical-search happens after the project clears
  the policy screen.
- [Two rebases, then wait](./two-rebases-then-wait.md) is a
  different reflex-control card, but the same family: do one
  careful read before the second push.
- [Spread order vs the cleanup pass](./spread-order-vs-cleanup-pass.md)
  is the example where the surface error (a downstream Zod
  validator) was three call frames removed from the actual
  bug (a diff-merge spread order). Chasing the canonical
  upstream primitive instead of the consumer's error message
  is the same discipline this card names.
