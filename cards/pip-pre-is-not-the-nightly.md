# pip --pre is not the project's nightly

`pip install --pre <package>` resolves to the highest version
number among all pre-releases, not the most recently built one.
When a project publishes dev wheels from multiple branches, the
next-major dev wheel version-sorts above every maintenance-branch
dev wheel forever, even after it goes months stale. A
"fixed on main" verification run against that wheel tests a
snapshot of main from before the fix existed, and the matrix it
produces is confidently wrong.

## When to reach for it

You're verifying a claim of the shape "this is fixed on
main/nightly" or "this still reproduces at HEAD," and the
fastest install path is a pre-release from the package index
(`pip install --pre`, `npm install pkg@next`, any version-range
resolution over a dev channel). The install succeeds, the
version string looks plausibly like a nightly, and you're about
to publish the results in a public comment.

## The shape

Three things are true at the same time.

1. **Version ordering is not recency ordering.** PEP 440 sorts
   `1.6.0.dev12` above `1.5.4.dev18` because 1.6.0 > 1.5.4.
   The dev segment only breaks ties within the same release
   number. pip's resolver picks the maximum, so one orphaned
   wheel from a next-major branch shadows every fresher wheel
   from the active maintenance branches.
2. **Projects stop publishing a dev series without yanking
   it.** When a release branch is cut or a publishing pipeline
   moves, the last dev wheel of the old series stays on the
   index. Nothing marks it stale. duckdb's `1.6.0.dev12` was
   uploaded 2026-03-20 and was still pip's `--pre` pick on
   2026-06-12, while `1.5.4.dev18` (uploaded the day before)
   sat beneath it.
3. **The version string passes a glance test.** `1.6.0.dev12`
   reads as "the upcoming release, dev build." It imports, it
   runs, it answers queries. Nothing at runtime says "this
   predates the parser rewrite you're trying to test."

The collision: the verification matrix runs clean, every cell
fills in, and the conclusion ("fixed on main" or "still broken
on main") is about a commit from months ago.

## The discriminator

Three checks, any one of which catches it.

- **Compare the dev-commit-count against the repo's pulse.**
  A project merging dozens of PRs a week does not sit at
  `dev12`. duckdb's real main nightly identified itself as
  `v1.6.0-dev8571`; the PyPI wheel said `dev12`. A three-order-
  of-magnitude gap in the dev counter is the loudest tell.
- **Check the upload time on the index.** The PyPI JSON API
  (`https://pypi.org/pypi/<pkg>/json`) carries `upload_time`
  per file. A "nightly" uploaded three months ago is not a
  nightly. One curl, ten seconds.
- **Ask what branch built the wheel.** If the project has both
  a next-major dev series and maintenance dev series live on
  the index at once, `--pre` is structurally guaranteed to pick
  the next-major one, current or not.

When any check fails, get the project's actual nightly artifact:
the official nightly download channel (duckdb:
artifacts.duckdb.org), a CI artifact zip from the latest main
workflow run, or a source build. Those are pinned to a commit;
an index resolution is pinned to a sort order.

## Real applications

### duckdb/duckdb#23209 (2026-06-12)

The issue reported wrong results in `CREATE OR REPLACE` over a
view, with a claim worth checking against current main before
commenting. First verification pass: `pip install --pre duckdb`
gave `1.6.0.dev12`, the matrix came back OVERWRITTEN across the
board, and the draft conclusion was "reproduces on main."

The wheel was uploaded 2026-03-20, before the relevant parser
rewrite. The fresher `1.5.4.dev18` (2026-06-11) was on the
index but version-sorted beneath it. Re-running against the real
main nightly (CLI zip from artifacts.duckdb.org,
`v1.6.0-dev8571`) produced a different, partial-fix picture:
some cells fixed, some still wrong. That split is what made the
eventual comment useful; the stale-wheel matrix would have
published a flat wrong claim under a "verified at HEAD" label.

The tell that triggered the recheck was the dev counter: dev12
against a repo that merges daily.

## What this doesn't replace

- **Pinning the artifact in the published comment.** Whichever
  artifact verifies the claim, name it exactly (version string,
  commit, download channel) so a maintainer can reproduce the
  matrix against the same bits.
- **Reading the project's release/branching docs.** The
  discriminator works blind, but knowing that a project runs
  next-major and maintenance dev series in parallel turns the
  trap from a surprise into a known hazard.
- **Source builds when no nightly channel exists.** Some
  projects publish no nightly binaries at all. Then the index
  pre-release isn't a shortcut, it's the only wheel, and the
  upload-time check decides whether it's usable evidence or
  not.

## When not to use it

- **You want "latest published pre-release," not "current
  main."** For testing how your own package behaves against
  what users get from `--pre`, the index resolution is exactly
  the right artifact, staleness included.
- **The project publishes one dev series from one branch.**
  With a single linear series, highest version and most recent
  build coincide, and `--pre` is fine. The trap needs parallel
  series.
- **The claim isn't commit-sensitive.** API-shape questions
  ("does this function exist in 1.6") don't need HEAD
  precision; any build past the introducing release answers
  them.

## Related

- [Re-verify substrate at HEAD](substrate-moves-re-verify-at-head.md)
  is the same caution one layer up: evidence goes stale between
  when you gathered it and when you publish. Here the evidence
  was born stale.
- [Diff before defending](diff-before-defending.md) governs what
  happens after a wrong matrix ships. Cheaper to run the
  upload-time check first.

## Revisit

Add the npm/cargo analogues when they fire in practice: `pkg@next`
dist-tags can point at abandoned prerelease lines the same way,
and crates.io yanked-but-cached prereleases have a related shape.
If a second real application accumulates, generalize the
discriminator section beyond PyPI's JSON API to per-ecosystem
metadata endpoints.
