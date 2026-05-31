# Pick substance from a GFI batch

When a MEMBER drops twenty `good first issue` tickets in one
half-hour window, the issues are not interchangeable. Some are
mechanical sweeps with thirteen near-identical instances
("port `*_test.go` to table-driven across all packages") and
some are real bugs with single-file fault sites ("validation
function accepts negative `MaxTokens`"). The mechanical sweep
feels efficient — thirteen PRs in the same shape, low risk,
each one ships in ten minutes — but it is racing-shape, and
the racing-shape PR is the bot signature.

The bug fixes are where the substance is.

## When to reach for it

Any time a maintainer or core contributor drops a batch of
`good first issue` tickets and the batch contains two distinct
kinds: a long list of mechanical conversions (table-drive,
formatter, lint-rule, doc-cross-link) and a shorter list of
substantive fixes (a real bug, a validation gap, a missing
guard, a documented behavior the code doesn't honor). The
mechanical conversions are visible from a hundred miles away;
the substantive fixes need a closer read. The temptation is to
sweep the mechanical pile and call it productive.

It isn't. Here's why.

## The shape

Three things go wrong with the mechanical sweep.

1. **Racing shape.** Thirteen identical PRs in the same window
   means every other first-time contributor scanning the GFI
   feed sees the same easy targets at the same moment. The race
   produces dup-PRs, force-merge confusion, and reviewer
   fatigue. The maintainer who dropped the batch did not mean
   to invite a race; they meant to surface low-friction work
   for a steady stream of contributors. The race compresses the
   stream into a flood.

2. **Bot signature.** "I took the easy one" reads as automation
   when the same contributor takes three of the easy ones in
   the same hour. The maintainer's mental model becomes "this
   person is grinding for stats" instead of "this person reads
   the codebase and picks well." Future PRs from the same
   author start from a lower trust baseline.

3. **Zero learning.** A mechanical conversion teaches nothing
   about the codebase. The next PR you open against the same
   repo starts from the same zero. Compare to a substantive
   fix: you walked the validation function, read the test
   suite's assertion pattern, found the placement that matches
   the existing AI-gated checks, learned the pinned
   `golangci-lint` version from the Makefile. The substantive
   PR builds the repo model. The mechanical sweep doesn't.

## The selection heuristic

When a batch lands, sort the issues by these signals before
picking:

- **Single file vs. cross-cutting.** Single file with explicit
  fault site beats cross-cutting refactor every time. A
  cross-cutting refactor is multi-PR work that the maintainer
  has not necessarily blessed in one PR.

- **Issue body completeness.** A bug-fix ticket that names the
  three bounds to add and the test shape ("`MaxTokens > 0`,
  `RateLimitPerMinute >= 0`, `0.0 <= Temperature <= 1.0`,
  table test") tells you the design decision has already been
  made. The PR essentially audits itself. Compare to a ticket
  that says "add table-driven tests for `*_test.go`" — the
  design space is enormous and the PR will surface twenty
  preference questions per file.

- **Toolchain match.** An eBPF bug in a Go repo needs
  `clang/llvm/libbpf-dev` to compile, lint, and verify. If your
  environment doesn't have the toolchain, the PR will look
  fine to you and red to CI. Skip the toolchain you can't
  reproduce locally.

- **Substance scope.** A bug whose fix is one paragraph in the
  PR body beats a refactor whose fix needs three. Reviewers
  triage by reading the body; the body's clarity is a leading
  indicator of merge speed.

## When a sweep IS the right call

Two exceptions.

1. **You are a maintainer or trusted regular.** If the
   maintainer who dropped the batch already merged five of your
   PRs and trusts your taste, sweeping the mechanical pile is
   coordination, not racing. The trust baseline carries the
   batch shape.

2. **The mechanical task has a non-obvious correctness gate.**
   "Port `*_test.go` to table-driven" sounds mechanical until
   you find the test that asserts the broken behavior is the
   intended design. The substance is buried in one of the
   thirteen instances. Picking three to look at, finding the
   exceptional one, and shipping a single PR that surfaces the
   contract is substantive.

Otherwise the bug fix wins. Pick one, scope it cleanly, ship
it, leave the rest of the batch for the steady stream of
first-time contributors the maintainer was actually inviting.
