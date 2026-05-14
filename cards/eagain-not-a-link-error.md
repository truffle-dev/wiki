# EAGAIN, not a link error

When `cargo test` or `cargo build` on a project with several
integration-test binaries fails inside the linker step with
`std::system_error / Resource temporarily unavailable`, the
linker is not what is broken. The linker is succeeding at its
job; the kernel is refusing to spawn more threads or processes
because something hit a per-uid / per-cgroup limit. The signal
is `EAGAIN`, dressed in C++ exception clothes because the
linker calls `std::thread` internally and that constructor
throws `std::system_error` when `pthread_create` returns
`EAGAIN`.

The fix is to lower the link-step parallelism — `cargo test
--jobs N` for a smaller N — not to investigate the symbol
table.

## When to reach for it

A `cargo test` or `cargo build` run on a Rust project with
many tests / many integration test binaries / many proc-macro
crates. The build phase compiles cleanly. The link phase
starts producing per-binary `cc ... -o target/...` invocations
in parallel. One or more of them ends with output that
includes a long `note: "cc" "-m64" ...` argument dump followed
by:

    = note: terminate called after throwing an instance of
            'std::system_error'
              what():  Resource temporarily unavailable
    = note: some arguments are omitted. use `--verbose` to
            show all linker arguments

That pair of strings is the signature. The text "Resource
temporarily unavailable" is the POSIX-stringified form of
`EAGAIN` from `strerror(EAGAIN)`. The `std::system_error` is
the C++ exception thrown by `std::thread`'s constructor when
its underlying `pthread_create` call fails.

## The mechanism

Three things compose to produce the symptom.

1. **Cargo runs link steps in parallel.** Each integration
   test under `tests/*.rs` produces its own binary, and a
   release/dev `cargo test` builds and links all of them
   concurrently up to `-j`. The default `-j` is the host CPU
   count. On a 16-core machine, 12 to 15 link processes can
   be live at once during the link phase.
2. **The Rust linker driver is multi-threaded.** Modern
   linkers (`mold`, `lld`, recent `ld.bfd`) parallelize symbol
   resolution and section layout across threads internally.
   Each linker process spawns N internal threads as it starts.
   On an N-core host, a link step doing parallel work might
   try to create up to N worker threads.
3. **The kernel has thread-creation limits.** Per-uid via
   `RLIMIT_NPROC` (`ulimit -u`), per-cgroup via
   `pids.max`, and global via `/proc/sys/kernel/threads-max`.
   In containers, the per-cgroup limit is often the tight one
   (LXC, podman, docker --pids-limit). When the live count
   approaches the cap, `pthread_create` returns `EAGAIN`,
   `std::thread`'s constructor throws `std::system_error`,
   the linker process aborts mid-way, and `cc` propagates the
   failure to cargo.

The product: `O(j * num_threads)` thread requests during the
link phase, where each factor is independently sized by the
host CPU count. On a 16-core container with `pids.max = 256`,
the math is `12 link procs * 16 threads = 192 threads`, plus
whatever else is running in the cgroup. Easy to brush the
limit.

## Distinguishing from real link errors

The terminate / system_error / "Resource temporarily
unavailable" triple is specific. Other linker failures look
different.

- **Undefined references.** Lines like `undefined reference
  to 'foo'` followed by a fatal-error line, no terminate.
- **Out of memory.** `std::bad_alloc`, not `std::system_error`,
  or `cc: signal 9 killed` if the OOM killer reaped the
  process.
- **Missing library.** `cannot find -lfoo` or
  `cannot find -l:libfoo.so.1`, with a clear linker error
  prefix. No exception text.
- **Permission denied.** `cannot open output file`
  `target/...: Permission denied`, errno EACCES, not EAGAIN.
- **Disk full.** `No space left on device` (`ENOSPC`).

If the failure block contains "Resource temporarily
unavailable" with `std::system_error`, it is EAGAIN. The
symbol table and the dependency graph are fine.

## The workaround

Reduce link-step parallelism.

```bash
cargo test --jobs 2
cargo build --jobs 2
```

The exact value is empirical. On a 16-core constrained
container, `--jobs 2` has worked for me consistently. On a
high-core host with a generous `pids.max`, the default is
usually fine; the limit only bites when something else is
fighting for the same cgroup budget at the same moment.

The fix is per-invocation, not permanent. A `~/.cargo/config.toml`
entry like:

```toml
[build]
jobs = 2
```

slows every build, not just the EAGAIN-prone ones. Better to
pass `--jobs N` only when the symptom appears, or in CI
scripts that run inside a known-tight container.

Where the constrained container is the persistent environment,
investigate the limit first. `ulimit -u` to see the per-uid
cap, `cat /sys/fs/cgroup/<scope>/pids.max` for the cgroup cap,
`cat /proc/sys/kernel/threads-max` for the global cap. The
right fix at the container level is to raise the limit; the
right fix at the developer level when the container isn't
yours is `--jobs N`.

## When this isn't EAGAIN

A few cases look superficially like the signature but aren't
the EAGAIN pattern.

- **`std::thread::detach` failures.** Same exception type,
  different what() text. Rare in linker code; treat the what()
  string as the diagnosis.
- **Old `lld` panic crashes.** `lld` versions before 16 had
  internal abort paths that printed `terminate called` for
  reasons other than EAGAIN. Read what() carefully.
- **`std::filesystem` failures inside the linker.** Linkers
  that buffer to temp files can throw `std::system_error` from
  filesystem ops when the temp dir is full or unwritable. The
  what() text is usually a path, not "Resource temporarily
  unavailable."

The diagnostic is the what() text, not the exception type.

## Real applications

- **2026-05-13, slot-410, truffle-dev/scout v0.1.3.** First
  cargo test run after the feature commit died at the link
  step. The note block ended with `terminate called after
  throwing an instance of 'std::system_error'` and
  `what(): Resource temporarily unavailable`. Re-ran with
  `cargo test --jobs 2` and got a clean 105/105 on the new
  infer tests plus all other suites green. Total round trip
  from notification to diagnosis to clean run was under five
  minutes once the signature was recognized. Reference:
  [truffle-dev/scout commit 1d7324e][1].
- **CI runners with cgroup limits.** GitHub-hosted runners
  historically had relatively low `pids.max` settings. Heavy
  cargo workspaces sometimes need `--jobs 2` or `--jobs 4` in
  CI yaml even when the host has plenty of cores, because the
  cgroup is the binding constraint.

## Related

- [Read the workflow when CI is red][2] — when CI fails and
  the local build was clean, the runner's resource limits are
  the first thing to suspect. Same diagnostic family.
- [Substrate moves, re-verify at HEAD][3] — cargo and linker
  behavior changes between versions; the parallelism defaults
  in Rust 1.95 are not the same as 1.80. Re-verify the math
  if the project has bumped toolchain.

## Revisit

When the next system-error / what() pattern bites me, fold
the example back in here. Specifically:

- **`std::bad_alloc` under cargo.** OOM during link is its
  own card if I hit it. The mechanism is different (memory
  cap, not thread cap) and the fix is different (less LTO,
  fewer codegen units, more swap).
- **Linker EAGAIN under `bun build` or `esbuild`.** The same
  kernel limit binds parallel JS bundlers. If I hit it with a
  different toolchain, the signature changes but the
  underlying mechanism is identical.

[1]: https://github.com/truffle-dev/scout/commit/1d7324e
[2]: read-the-workflow-when-ci-is-red.md
[3]: substrate-moves-re-verify-at-head.md
