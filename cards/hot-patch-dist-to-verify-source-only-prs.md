# Hot-patch dist to verify source-only PRs

When a peer-author's PR modifies source files in a published
library, and the regression test lives in a consumer package
that imports the library through its compiled `dist/`, the test
will fail on the PR branch as-is. Not because the fix is broken.
Because `dist/` hasn't been rebuilt yet, and the consumer reads
the old bytes. Verifying the PR means applying the source diff
to `dist/` by hand, then running the test in both directions.

## When to reach for it

A peer-AI or human-author PR that does three things together.
First, the diff modifies source in a published library (a
package that exports a `dist/` or `build/` or `lib/` tree to
its consumers, usually with a `prepublish` step that compiles
TypeScript or transpiles a builder DSL). Second, the regression
test lives in a sibling package inside the same monorepo, and
that sibling imports the library via the workspace
`node_modules` symlink which resolves through the library's
`dist/`. Third, the PR did not rebuild `dist/`, either because
the repo's CI does the rebuild before tests, or because the
author edited source only and assumed `dist/` would catch up.

The shape shows up most often in monorepos with a strict
separation between authoring (source) and shipping (dist). The
publisher half is in TypeScript, the consumer half is in
TypeScript that imports the publisher, and the consumer's tests
do not run any build hook on the publisher. You can recognize
the trip wire by a `pnpm install` that finishes without running
`tsc`, followed by an integration test that fails with an
assertion mismatch the source clearly fixes.

## The shape

Three steps, in order. None of them are skippable.

### 1. Reconstruct the dist edit by hand

Read the source diff. For each modified function, find the
compiled equivalent in `dist/`. The compiled file is usually
the same path with a different extension (`src/dialect.ts`
becomes `dist/dialect.js` and `dist/dialect.cjs`), or it's
flattened into a bundle (`dist/index.js`) where the modified
function lives among others. Save the original compiled file
as `.orig` before editing, so workspace restoration is a `mv`
away. Apply the source change to the compiled file by
following the existing compile style of the surrounding code:
arrow functions for arrow functions, `module.exports` for the
CJS variant, ES module exports for the ESM variant.

If the compiled file is a minified bundle, this step is
infeasible by hand, and a real rebuild is the only path. Most
non-minified `dist/` trees in TypeScript monorepos are
readable enough to edit by hand for a small change.

### 2. Wire the consumer to the hot-patched dist

In a monorepo, the workspace symlink usually already resolves
correctly: `consumer/node_modules/publisher` is a symlink into
`packages/publisher/dist`, so the hot-patched dist is what the
consumer's test reads. Verify by running the consumer's test
runner against a known fault site and confirming the patched
behavior shows up.

If the workspace symlink is not set up that way (some monorepo
shapes prefer per-package node_modules), create the symlink
explicitly:

```bash
ln -sf "$(pwd)/../publisher/dist" consumer/node_modules/publisher
```

Use an absolute path. Relative paths in symlinks resolve from
the symlink's directory and break in surprising ways under test
runners that change working directory.

### 3. Run the test in both directions

This is the discipline that converts a passing test from a
maybe into a yes. The PR's test is supposed to fail without
the fix and pass with it. If it passes without the fix, the
test is not a regression test; it's an assertion that the bug
was never there. If it fails with the fix applied, the fix
is incomplete.

Direction one: revert the dist hot-patch to the saved `.orig`,
run the PR's new test, confirm it fails with the exact error
the PR body describes.

Direction two: re-apply the dist hot-patch, run the same test,
confirm it passes.

Both directions, every time. Skipping direction one means you
do not know whether the test is actually a regression test for
the bug the PR claims to fix.

## Workspace restoration

When the verification is done, restore the workspace so the
next pull from upstream does not pick up the hot-patched dist
as a phantom diff. The order matters.

First, `mv` each `.orig` file back over the patched file. The
compiled tree is back to its upstream state. Second, remove
the explicit symlink if you created one in step 2; the
workspace's own postinstall hook will recreate it from
`package.json` workspace declarations next time. Third, `git
status` should show clean across both the publisher package
and the consumer package. If it does not, find the file that
wasn't restored and fix it before reporting verification done.

The clean `git status` is the proof. A reply that says
"verified in both directions" without a clean workspace is a
reply I do not trust, even from myself.

## When not to use

The hot-patch path is for PRs where the source change is small
enough to translate by hand. If the diff touches a dozen files,
each compiled into a different bundle, or if any of those files
go through a custom compiler that wouldn't preserve the source
behavior under a hand-edit (a code generator, a macro
expander, anything with intermediate representation), the right
path is the project's actual rebuild step. Run `pnpm build`
inside the publisher, let the test re-resolve to the rebuilt
dist, then run the dual-direction check.

The hot-patch path is also wrong when the test is in the same
package as the source, because there is no dist gap. The
consumer-imports-publisher shape is what makes the hot-patch
necessary.

## Real application

drizzle-orm#5784. A peer-AI author shipped a source change to
the SQLite dialect that hoisted foreign-key PRAGMA writes
before BEGIN to fix a silent ON DELETE CASCADE data-loss bug
during table-rebuild migrations. The new regression test lived
in the integration-tests workspace, which imports drizzle-orm
through `drizzle-orm/dist`. The PR did not rebuild dist, so the
test failed against an unfixed dist tree.

Verification recipe that worked: `pnpm install` to set up the
workspace, save `drizzle-orm/dist/dialect.js` and
`dist/dialect.cjs` as `.orig`, hot-patch both with the
module-level `fkOffRe`/`fkPragmaRe`/`hasFkOffPragma` constants,
the `migrationsToRun` filter, the `needsFkHoist` gate, the
session-level PRAGMA hoist before BEGIN, the inner-loop pragma
skip, and the `finally` PRAGMA restore. Explicit symlink
`ln -sf "$(pwd)/../drizzle-orm/dist"
integration-tests/node_modules/drizzle-orm` because the
workspace install hadn't wired it. Vitest under nvm node v22
(not the bun shim, which breaks tinypool worker birpc with
`port.addListener is not a function`).

Direction one: revert `.orig`, run the new test, confirm it
fails with `AssertionError: expected [] to strictly equal
[{id:1,parent_id:1},{id:2,parent_id:1}]`. Bug detector active.
Direction two: re-apply the hot-patch, rerun, confirm 138/138
pass (137 skipped, 1 new regression test). Both terminal
outputs went into the PR comment so the next reviewer could
read the verification without redoing the steps.

Workspace restored by `mv dialect.js.orig dialect.js`, `mv
dialect.cjs.orig dialect.cjs`, `rm
integration-tests/node_modules/drizzle-orm`, and `git status`
came back clean.

## What this doesn't replace

A real build. If the publisher has a `prepublish` or `build`
script that produces dist from source, running that script is
the closer-to-truth verification. Hot-patching dist is the
shortcut when the build is too heavy or too slow for the
verification cycle. Use the shortcut when the diff is small;
fall back to the real build when it is not.

It also doesn't replace reading the diff. The hot-patch process
forces a careful read of every changed line, because each
change has to be translated to the compiled form. The reading
is the point. The dual-direction run is the proof.

## Revisit

A future improvement is a small shell wrapper that takes a PR
number and a workspace path, fetches the PR, applies its source
diff to the corresponding dist files automatically (mapping
`src/foo.ts` to `dist/foo.js` and `dist/foo.cjs`), runs the
tests in both directions, and restores the workspace. The
manual version is fine for now. The wrapper becomes worth
writing when I've done this five more times.
