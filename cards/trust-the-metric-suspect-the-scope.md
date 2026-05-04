# Trust the metric, suspect the scope

When two diagnostic tools disagree by an order of magnitude on
the same question, the reflex is "one of them is wrong." The
reflex is usually wrong. Most of the time, both tools are
measuring accurately, and the disagreement is telling you that
each tool sees a different slice of what's happening. The fix is
to identify the scope mismatch, not to patch the metric.

## When to reach for it

Any time two telemetry surfaces disagree on the same question
and the disagreement is order-of-magnitude, not 10-20%.
Examples:

- V8 CPU profile shows 92% idle, but `process.cpuUsage` reports
  1.5 cores busy.
- A health endpoint reports `event_loop_utilization=1` but a
  `--cpu-prof` of the same window shows the main thread mostly
  idle.
- Application latency P99 is fine, but database CPU is at 80%.
- Container memory looks healthy, but the kernel kills processes
  with OOM.

If the disagreement is less than 2x, it's usually a sampling
artifact and not worth pulling on. Order-of-magnitude is the
threshold for the pattern.

## The pattern, in order

1. **Read each tool's docs to confirm what it actually measures.**
   What's the scope? Which threads? What time window? What does
   "idle" mean to this tool specifically? V8 `--cpu-prof` profiles
   the main JS isolate. `process.cpuUsage` sums all process
   threads. Same process, different scopes.
2. **Verify the math of the metric.** Read the source. Confirm
   the formula. If the metric has a baseline, confirm it resets
   on the right interval. If the metric is a diff, confirm the
   arguments are in the documented order. The metric is rarely
   bugged; verifying takes ten minutes and rules out the cheapest
   explanation first.
3. **Identify the scope union and the scope difference.** What's
   in tool A's scope that's not in tool B's? What's in tool B's
   scope that's not in tool A's? The disagreement lives in the
   difference. List the candidates that could occupy that
   difference.
4. **Pick a probe that lights up only the difference.** Don't try
   to make the two tools agree. Pick a third tool that resolves
   the candidates. For libuv loop work hidden from V8 profile,
   `process.report.getReport().libuv` lists every active handle.
   For threadpool work hidden from V8 profile, set
   `UV_THREADPOOL_SIZE=1` and re-measure. For native addon
   threads, attach a system profiler (perf, dtrace, ebpf) that
   can see them.

## Why this works

Telemetry is built by people who knew exactly what they wanted
the tool to measure. The semantics are usually correct. What's
not always loudly documented is the *scope* of the measurement:
the threads it counts, the threads it doesn't, the time windows,
the baseline behavior, the edge cases.

When you treat the metric as bugged, the next move is to patch
or replace it. That work is usually wasted, because the patched
metric will tell you the same thing as the original. When you
treat the disagreement as a scope mismatch, the next move is to
identify what each tool sees and pick a third probe that spans
the gap. That work directly produces the diagnosis.

## Real application

openclaw#76307, May 3, 2026. A maintainer fix for streaming
truncation had been merged and verified incomplete by a user
running the new build. The user ran `openclaw health` (a custom
health metric using `performance.eventLoopUtilization` and
`process.cpuUsage`) and got `util=1 cpu=1.566` cores. They also
captured a 60-second `--cpu-prof` during the same window with
bundled plugins disabled to remove the obvious tenant. The
profile showed 92.08% idle. Top JS self-time entries totaled
under 8% wall time, and the hot ones were just module-loading
boilerplate.

The reflex was: the metric is broken, ignore it. The right move
was to read `event-loop-health.ts` and verify the metric math
(correct: `performance.eventLoopUtilization(later, earlier)` in
the documented argument order, `cpuTotalMs / intervalMs` with
both window-scoped deltas), then identify the scope mismatch:

- V8 `--cpu-prof` profiles the main JS isolate only.
- `process.cpuUsage` sums all process threads (libuv threadpool,
  V8 worker threads, native addon threads).
- `eventLoopUtilization` measures main libuv loop time in idle
  (epoll_wait) vs active (callback execution) phases. ELU=1 with
  main-thread-idle in the V8 profile means short callbacks
  bouncing the loop fast enough to never reach poll-block, but
  each callback short enough that the JS sampler records the
  thread as idle between samples.

The third probe chosen was `process.report.getReport().libuv`,
which lists every active timer, fs watcher, signal handler,
socket, child process, and pipe libuv is tracking. That probe
lights up only the difference between what V8 profile sees and
what ELU sees: the library-level handles libuv knows about that
the JS isolate doesn't surface as samplable functions.

The result: instead of patching the health metric, the next ask
to the user was for one libuv-handles dump that would name what
is keeping the loop hot.

## What this doesn't replace

- Verifying the metric math is still mandatory. Skipping that
  step and assuming "the metric is right" is the dual mistake to
  "the metric is wrong." A ten-minute source read either rules
  out a metric bug or reveals one.
- Sometimes the metric is genuinely bugged. The pattern says to
  check scope first, not to assume scope mismatch is the only
  explanation. If scope analysis comes up empty and the math is
  right, look harder at the metric.
- This isn't a substitute for instrumenting the actual
  bottleneck. After the third probe names the tenant, you still
  have to fix it.

## When not to use it

When the disagreement is small (less than 2x) and the metrics
are sampled at low frequency. That's usually a sampling
artifact, not a scope mismatch. Live with it.

When you have only one tool. The pattern requires at least two
disagreeing surfaces to trigger.

## Related

- [substrate-moves-re-verify-at-head](substrate-moves-re-verify-at-head.md):
  before reading the metric source to verify the math, confirm
  you're reading the current source. A long-cached repo can lie.
- [find-canonical-before-fixing-bypass](find-canonical-before-fixing-bypass.md):
  the same shape at a different layer. When a workaround exists
  for a defect, find why it was added before patching the
  obvious surface.

## Revisit

Add a second real application the next time the pattern resolves
a multi-tool diagnostic disagreement. If the same scope mismatch
(V8 vs cpuUsage vs ELU) shows up across multiple incidents,
promote the third-probe recipe (libuv handles dump) into its own
card.
