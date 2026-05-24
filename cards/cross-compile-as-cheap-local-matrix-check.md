# Cross-compile is a cheap local matrix check

When a CI matrix runs on a platform the dev box can't simulate
(Windows from Linux, FreeBSD from macOS, an embedded target from
anything), the compile-time half of the matrix is portable for
free. Add a cross-compile vet/build pass to the local hook and
the matrix stops catching trivia. The runtime half stays on the
real runner; the syntax/import/API-shape half lands before push.

## When to reach for it

The same repo ships two regressions in a short window that only
the foreign-OS matrix job caught. Both bugs would have surfaced
on a `go vet` or a `cargo check` against the target triple,
without anyone actually executing the binary on that OS. The
local pre-commit hook is running on the dev OS only. The
contributor running `make test` doesn't see the regression
until CI opens its red badge several minutes later, which
is several minutes too late to keep a tight ship cadence.

## The shape

Three things are true at the same time.

1. **Matrix CI catches two bug classes, not one.** The
   compile-time class lives in API differences, missing types,
   conditional compilation paths, and import resolution. The
   runtime class lives in path semantics, network stack quirks,
   syscall behavior, filesystem case sensitivity, and process
   model. Only the runtime class needs the actual OS to
   surface. The compile-time class needs a cross-compiler.
2. **Cross-compilers are already on the dev box.** `GOOS=windows
   go build` works from Linux without installing Wine. `cargo
   check --target x86_64-pc-windows-gnu` works after `rustup
   target add`. `dotnet publish -r win-x64` works on macOS.
   `clang --target=arm-linux-gnueabihf` works after installing
   the right libc headers. The local hook does not need a
   foreign-OS VM, container, or emulator to run the cross-pass.
3. **Local feedback closes the loop in seconds.** A
   `vet-windows` target finishes in under a minute for most
   single-binary projects. The CI matrix job for the same
   pass costs three to six minutes of queue time plus run
   time, plus the context-switch back to the editor when the
   notification arrives. The dollar cost is also higher on
   CI minutes for matrix duplication than on the dev box.

The collision: contributors who don't have the foreign OS at
hand treat the matrix as someone else's problem. The matrix
job becomes a slow oracle that gates merges instead of a fast
mirror that gates commits. Cross-compile pulls the
compile-time half of the oracle into the contributor's loop.

## The discriminator

Three questions decide whether to wire this in.

- **Has the same matrix job caught at least two regressions
  in recent memory?** One catch is a fluke. Two catches in a
  short window mean the dev environment is structurally
  blind to a bug class the matrix sees. The cost of a new
  Makefile target is justified once a pattern is visible.
- **Is the cross-compiler one command away?** If `go vet` or
  `cargo check` or `dotnet build` already work against the
  target triple, the wiring is one Makefile line. If the
  target needs a custom toolchain that takes hours to install
  and breaks on every contributor box, the local hook is the
  wrong place; the cost belongs in a container.
- **Are the regressions you missed compile-time or runtime?**
  Runtime regressions (a system call that returns differently
  on Windows, a file lock that behaves differently on macOS)
  will not be caught by cross-compile. They need the real
  runner. If both recent catches were runtime, this card
  doesn't apply; you need a containerized smoke test or a
  remote build instead.

## Real applications

### truffle-dev/glyph slot-374 (2026-05-24)

Glyph's CI matrix runs lint + ubuntu-latest + macos-latest +
windows-latest on every push. Two Windows-only regressions
landed inside six hours, both caught by the windows-latest
job, neither caught by the pre-commit hook.

The first regression was a path-URI confusion. `pathFromURI`
in the LSP wedge took a `file://` URI and called
`filepath.FromSlash` on the entire URI string, leaving the
`file://` prefix attached and breaking the stat call. The
unit tests on Linux passed because Linux's path semantics
swallow the malformed prefix as a relative path. Windows
rejected it.

The second regression was a `filepath.Separator` leak into a
display string. The tab bar in `cmd/nook/internal/tabbar`
rendered file paths with `filepath.Separator` as the
join character, baking `\` into the rendered output on
Windows and rendering tabs as `cmd\nook\main.go` instead of
`cmd/nook/main.go`. The display tests passed on Linux because
Linux's separator is the same character as the display
convention.

Both regressions would have been caught by `GOOS=windows go
vet ./...` plus `GOOS=windows go build -o /dev/null ./...`.
Neither requires actually running a Windows process. The
slot-374 fix added two Makefile targets:

```makefile
.PHONY: fmt fmt-check vet vet-windows build-windows test ci-local hooks

vet-windows:
	GOOS=windows go vet ./...

build-windows:
	GOOS=windows go build -o /dev/null ./...

ci-local: fmt-check vet vet-windows build-windows test
```

And wired both into `ci-local`, which the pre-commit hook
runs. CONTRIBUTING.md got a new subsection naming the bug
class so contributors know why the cross-pass is there.
The next Windows-only regression in glyph would surface
in the local hook, not on the matrix.

The runtime half of the gap (a Windows binary that builds
and vets clean but behaves wrong at runtime) still depends
on the windows-latest runner. The split is intentional:
compile-time in the local loop, runtime on CI.

## What this doesn't replace

- **The actual matrix runner.** Cross-compile catches the
  syntactic and structural half. Runtime semantics (locks,
  signals, networking, filesystem ordering, character
  encoding) need the real OS or a credible emulator. Keep
  the matrix.
- **Reading the platform-specific docs for new APIs.** When
  a new system call enters the codebase, the cross-pass
  may still link cleanly even if the call is meaningless on
  the target. A quick read of the platform documentation
  before merging beats a cross-compile that happens to be
  green.
- **A convention doc that names the bug class.** The pre-commit
  hook is mechanical. Contributors still need to know why
  `filepath.Separator` is wrong in display strings, why
  `pathFromURI` must parse, why mutex implementations vary
  across runtimes. The CONTRIBUTING subsection is the
  permanent half; the hook is the safety net.

## When not to use it

- **The matrix is single-OS.** If the project only ships for
  Linux, cross-compile has nothing to add. The dev box already
  matches the matrix.
- **Foreign platform support is fully stubbed.** If the project
  uses build tags to compile completely separate implementations
  per OS (`runtime_linux.go`, `runtime_windows.go`), a cross-pass
  on the foreign tag only exercises the stubs. That's still
  worth doing, but it's catching less than it appears.
- **The recent regressions are runtime, not compile-time.** If
  the matrix has been catching deadlocks, file-locking quirks,
  or character-encoding issues, the cross-pass won't help. The
  right move is a containerized smoke test, not a Makefile
  target.
- **The cross-toolchain is fragile.** Some targets need a custom
  libc, custom sysroots, or a vendor-specific SDK. If the
  toolchain breaks on contributor boxes every couple of months,
  the maintenance cost outruns the catch rate. Push that work
  into a CI container instead.

## Cross-language quick reference

- **Go**: `GOOS=<target> go vet ./...` and `GOOS=<target> go
  build -o /dev/null ./...`. Targets: `windows`, `darwin`,
  `linux`, `freebsd`, `netbsd`, `openbsd`, `dragonfly`,
  `solaris`. Add `GOARCH=arm64` etc. for non-amd64.
- **Rust**: `cargo check --target x86_64-pc-windows-gnu`
  (after `rustup target add`). The MinGW target is the
  easiest for Linux dev boxes; the MSVC target needs Windows
  headers. `cargo build --target` does the link pass too.
- **.NET**: `dotnet build -p:RuntimeIdentifier=win-x64`. The
  SDK is cross-platform end-to-end; runtime identifiers
  cover Windows, macOS, and Linux variants.
- **C/C++ with clang**: `clang --target=x86_64-w64-mingw32`
  plus the matching sysroot. Cross-compilation here is
  per-target and per-libc; budget time to set up.
- **TypeScript/JavaScript**: the language itself is platform-
  agnostic, but bundlers (esbuild, swc, tsc) sometimes have
  per-platform native binaries. The cross-check here is
  usually `npm pack` plus an install-and-import smoke in a
  container.

## Related

- [Disclosure mechanism is its own axis](disclosure-mechanism-is-its-own-axis.md)
  is the meta-pattern: bug classes have separable axes
  (compile-time vs runtime, lint vs test, build vs ship),
  and the right tool depends on which axis the class lives
  on. Cross-compile is the axis-specific version of that
  framing for the platform-divergence class.
- [Audit readers when reordering state](audit-readers-when-reordering-state.md)
  is a different bug class with the same lesson: the gap
  between what the dev box catches and what production sees
  has a structural cause; close it with a specific tool, not
  with extra vigilance.
- [Substrate moves; re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the time-axis version. Cross-compile closes the
  platform axis at the contributor's loop; HEAD-verification
  closes the time axis at PR-open. Both move feedback
  earlier.

## Revisit

Add a second real application when the next platform-only
regression fires. Watch for: a Rust project that catches a
Windows-only API removal via `cargo check --target`; a .NET
project that catches a macOS-only RuntimeIdentifier mismatch
via local cross-publish; a C project that catches a glibc-only
symbol via cross-link against musl. When three applications
accumulate across distinct ecosystems, split the cross-language
quick reference into a separate card and let this one stay
focused on the discipline.
