# When the diagnostic is the load

A diagnostic that runs on the system it measures is part of that
system. Most of the time the cost is negligible and you can
forget about it. Some of the time the cost is dominant, and the
diagnostic itself becomes the largest tenant of the resource it
was meant to characterize. When you see "this resource is
saturated and I can't find the work," the question to ask before
deeper trace work is whether the sampler is the work.

This card names the pattern, lists the detection moves, and
notes the three fix shapes.

## When to reach for it

Anytime a diagnostic reports a resource is saturated and a
proper profile of the application can't account for the load.
The shape is:

- `eventLoopUtilization=1`, but `--cpu-prof` shows the main
  isolate 90%+ idle.
- `top` reports a process pegged at 100% of one core, but the
  application's own request handlers cumulatively account for
  10% of that.
- `iostat` shows constant disk activity, but no application
  write is ever larger than a few KB.
- Tracing infrastructure shows a healthy span tree with very
  little wall-clock waiting, but the host machine's CPU never
  drops below 80%.

The common signal: the application looks idle while a
resource it relies on looks pinned. The blind spot is the
piece of code that isn't application code, isn't framework
code, and isn't OS work. It's the diagnostic itself.

## The pattern

A diagnostic samples a property of a system. The act of
sampling has a cost. The sampler runs on the same substrate
as the work being sampled (same event loop, same CPU core,
same disk). At a high enough sampling rate, the sampler's
cost becomes the dominant share of the substrate's load,
and the diagnostic ends up measuring itself.

Three pieces have to coexist for this to bite:

1. **The sampler runs on the measured substrate.** A timer
   firing every 20ms on the same event loop it's measuring.
   A profiling thread sharing CPU cores with the workers it
   profiles. A watcher process doing syscalls to detect file
   changes on the same disk it's monitoring.
2. **The sampling rate is high enough.** "Every 20ms" on a
   loop that handles 200 events per second means the sampler
   alone takes 5% of the loop's events. Multiply by the number
   of samplers and the percentage compounds.
3. **The sampler isn't visible to the application's profiler.**
   Native libuv handles don't appear in V8 CPU profiles. Kernel
   probes don't appear in user-space profilers. The blind spot
   is what makes the load look unaccounted-for.

When all three coexist, the diagnostic runs continuously,
shows the resource as saturated, and gives no clue that it's
the cause. The fix is upstream from the symptom.

## Detection moves

The application's main profiler will not show the sampler.
Reach for substrate-level introspection that does.

**Node.js / libuv.** `process.report.getReport().libuv`
dumps every active libuv handle with type, address, and
referenced flag. A `monitorEventLoopDelay` sampler appears
as a `timer` handle at a fixed cadence even when no JS-land
`setInterval` is active. `_getActiveHandles()` only lists
JS-land timers; the libuv dump lists all of them.

`async_hooks` with an init-hook for `TIMERWRAP`,
`PIPEWRAP`, `POLLWRAP`, etc. names the construction site
for handles that don't show up in JS-land enumerations:

```js
const ah = require('async_hooks');
const fs = require('fs');
ah.createHook({
  init(id, type, triggerAsyncId, resource) {
    if (type === 'TIMERWRAP') {
      fs.writeSync(2, `TIMERWRAP id=${id} stack=\n${new Error().stack}\n`);
    }
  }
}).enable();
```

The stack trace points at the file:line that constructed the
handle. If it points at a diagnostic library (perf_hooks,
@opentelemetry/sdk-node, a custom monitor), that is the
candidate.

**Linux / kernel.** `perf trace` and `bpftrace` see syscalls
that don't appear in user-space profilers. A diagnostic
watcher doing `inotify_add_watch` for every file in a tree,
or a metric exporter doing `read` on `/proc/self/stat` every
100ms, shows up here. `cat /proc/<pid>/status` lists thread
counts; an unexpected per-process thread is often a metrics
exporter or a tracing agent.

**JVM.** `jcmd <pid> VM.native_memory` and
`jcmd <pid> Thread.print` reveal threads belonging to JFR,
JMX, or APM agents that don't show in `jstack` of application
threads.

**General.** Pick a probe that lives outside the substrate
being measured. If the substrate is the event loop, sample
from a separate worker thread. If the substrate is one core,
sample with `taskset` from another. The probe has to be
outside what it observes, or it joins the system it tries
to characterize.

## Fix shapes, in order of cost

**1. Gate the sampler behind opt-in.** This is almost always
the right first move. The diagnostic is valuable when someone
is investigating; it's a tax when no one is. Wrap the start
in an env-var check or a runtime flag, default to off, and
require a deliberate enable to pay the cost. The diff is
two lines per callsite. No semantic changes for existing
users who don't enable it.

Look for prior art in the same codebase. If one diagnostic
is already gated and another isn't, the gated one is your
template. Match the existing flag rather than introducing
a new one when the new sampler serves the same audience.

**2. Reduce the sampling rate.** Lower the cost by sampling
less often. For event loop delay monitors, going from
`resolution: 20` to `resolution: 100` reduces the timer-fire
rate by 5x and barely degrades the P99 reading for any
load-monitoring use case (sub-100ms blocks are rare and
usually visible elsewhere). For profiling threads, sample
at 100Hz instead of 1000Hz. For metric exporters, scrape
every 60s instead of every 1s.

This works when no one is using the high-resolution
readings for a real purpose. Verify by grep: if the WARN
threshold downstream of the metric is `1000ms`, then
sampling at 100ms is fine. If the threshold is `5ms`,
reducing rate breaks the alarm.

**3. Consolidate samplers.** When N independent components
each spin up their own sampler for the same property,
collapse them into one shared subscriber pattern. The cost
goes from O(N) to O(1). This is architecturally clean but
expensive to ship: the components likely have different
lifecycles and different consumers, so the merge needs a
shared registry, ref-counted enable/disable, and a
broadcast surface. Right move for a refactor PR; usually
overkill for a perf PR.

When proposing this, file it as a follow-up to the gate-
the-sampler PR rather than blocking the perf fix on it.

## Real application

openclaw#76307, May 4, 2026. A user reported the same
streaming truncation bug after a maintainer fix shipped in
v1.14.33. Their `openclaw health` (a custom metric using
`performance.eventLoopUtilization` and `process.cpuUsage`)
showed `util=1 cpu=1.566`. A 60-second `--cpu-prof` of the
same window showed the main isolate 92% idle.

Three rounds of trace narrowed the load to libuv handles.
`process.report.getReport().libuv` showed three `timer`
handles tagged with file:line `perf_hooks` references. An
`async_hooks` TIMERWRAP init-hook named the constructors:

- `src/logging/diagnostic.ts:200`: `monitorEventLoopDelay({ resolution: 20 })`, no env gate.
- `src/gateway/server/event-loop-health.ts:48`: `monitorEventLoopDelay({ resolution: EVENT_LOOP_MONITOR_RESOLUTION_MS = 20 })`, no env gate.
- `src/gateway/server.impl.ts:218`: `monitorEventLoopDelay({ resolution: 10 })`, gated on `OPENCLAW_GATEWAY_STARTUP_TRACE || OPENCLAW_DIAGNOSTICS_EVENT_LOOP`.

Two unconditional 20ms samplers plus one optional 10ms
sampler. The two unconditional samplers, by themselves,
account for the user's `eventLoopDelayMaxMs=15s` reading
because the loop spends most of its time waking up and
servicing the sampler timer.

Fix shape ranked: gate the two unconditional samplers
behind the same flag the third sampler already uses. Two
lines per callsite, default off, no semantic change for
non-investigators. Reducing resolution would have flipped
P99 semantics under all users. Consolidating the samplers
into one shared subscriber would have been right but too
big for a perf PR.

The diagnostic that flagged "loop is saturated" had two
20ms timers as its largest tenant. The pattern is exactly
what this card is for.

## What this doesn't replace

- **Real load measurement.** If the diagnostic accounts
  for 30% of the load and the application accounts for the
  other 70%, the application is still doing too much. Don't
  use this card as a way to dismiss real saturation. Quantify
  the diagnostic's share before concluding it's the cause.
- **Profiler accuracy questions.** This card is about cost,
  not accuracy. If the metric is reading the wrong thing,
  see [trust-the-metric-suspect-the-scope](trust-the-metric-suspect-the-scope.md).
- **Sampling profilers in general.** Statistical sampling
  profilers at 1000Hz are usually fine because they piggyback
  on existing scheduler timer interrupts. The pattern bites
  when the sampler creates new dedicated infrastructure
  (timer, thread, syscall stream) just to do the sampling.

## When not to use it

When the application's own profile accounts for the
saturation. If `--cpu-prof` shows the main isolate 80%
busy in user code, the diagnostic isn't the load. Reach
for normal profiling and find the hot function. The
recursive-observer pattern is for the case where the
profile and the resource counter disagree, not for every
high-utilization investigation.

## Related

- [Trust the metric, suspect the scope](trust-the-metric-suspect-the-scope.md)
  is the upstream check. When two diagnostic surfaces
  disagree, identify the scope mismatch first. If one tool
  sees the diagnostic's load and another doesn't, that
  scope mismatch is exactly the recursive-observer pattern
  surfacing.
- [Read the closure, not just the state](read-the-closure-not-just-the-state.md)
  is the call-stack equivalent: ask not what the function
  is computing but what it has captured. Both cards are
  about the work the obvious read misses.

## Revisit

If a fourth fix shape surfaces (e.g. move the sampler to
a worker thread so it stops sharing the measured loop),
add it. Worker-thread isolation is technically the cleanest
fix but Node's worker-thread overhead may exceed the
sampling cost it eliminates; verify before recommending.
