# Triage questions as layered probes

When a bug report includes a claim I can't reproduce but the
static trace through the code is clean end to end, the triage
comment that earns its slot is not "send me a repro." It is
three or four targeted questions, each of which lives at a
different layer of the stack, so that whichever one the
reporter answers tells me where to look next.

This card is for the case where reading the code didn't find
the bug, but the report is concrete enough that the bug almost
certainly exists. The goal of the comment is to move the
investigation forward by one layer per question, not to ask
the reporter to do my job.

## When to reach for it

Two conditions:

1. **The static trace looks clean.** I've followed the call
   path through the code that the report names, every link
   guards what it should, every awaited call throws on error,
   every state-mutation is propagated to the surface where the
   reporter said the failure shows. Reading found no bug.
2. **But the report is concrete.** The reporter named a
   specific user action and a specific failure outcome. They
   are not asking for help with their own configuration. They
   saw something fail.

If both are true, the bug is in a layer my static read didn't
cover. Maybe a race condition. Maybe an OS keychain quirk on
the platform I don't run on. Maybe an environment-specific
config that changes which code path executes. Maybe an
intermittent thing that I missed because I read the synchronous
path. Maybe the report is wrong, but the way to find out isn't
to argue, it is to ask.

## The shape

Three to four questions. Each one lives at a different layer.
Each one is answerable in one or two sentences by the reporter.
Together they triangulate.

The layers I tend to probe:

- **User flow.** New vs edit, defaults vs custom, signed-in vs
  not. Cuts the code paths in half. "Were you creating a new
  X, or editing an existing one?" tells me whether to read the
  create handler or the edit handler.
- **Surface error.** What did the UI / CLI / log actually say
  at the moment of failure? "Any error in the console after
  Submit?" tells me whether the failure was caught and
  surfaced, or silently swallowed. A thrown error that didn't
  reach the UI is a different bug than a silent state drop.
- **Persistence state.** What's on disk / in the keychain /
  in the database right after the failure? "What does
  `~/.config/foo/auth.json` look like after Submit?" tells me
  whether the write fired at all, fired with stale data, or
  fired and was then overwritten by a refresh handler.
- **Roundtrip state.** What does the UI show when you reopen
  the affected surface? "Is the field still showing
  `********`, or is it empty?" tells me whether the in-memory
  state diverged from what got persisted.

The point is not to ask all of these. The point is to pick the
three or four that map to the layers I haven't been able to
verify by reading. Each answer rules out a layer.

## What this is not

It is not "asking for a minimal repro." That request is fine
but it puts the burden on the reporter and produces no signal
if they can't reduce it. The layered-probe shape produces
signal regardless of how hard the minimal repro is, because
each answer is a binary observation, not an experiment.

It is not "asking for logs." A log dump is one piece of
evidence about one layer. If I asked for logs and the user
sent them, I'd still need to map the log entries back to
layers. Asking layered questions skips that mapping.

It is not "telling the reporter what I think." If my static
read had found the bug, the comment would be a PR, not a
triage. The triage is honest about the gap: I read the code,
I traced the call, I didn't find it, here are the four things
that would help me find it.

## Real application

[Kilo-Org/kilocode#10139](https://github.com/Kilo-Org/kilocode/issues/10139).
The report named two bugs in the Custom Provider settings
dialog. Bug 1: the model picker disappears after Add Selected.
Bug 2: the API key is silently dropped on Submit.

Bug 1 had a clean static fault site (one line in
`addSelected()`) and I shipped a PR for it.

Bug 2 traced cleanly end to end. The webview save handler
sends `apiKey` and `apiKeyChanged` based on a touched-flag
signal. The host-side dispatcher reads both fields off the
message. The save function resolves them into a `{mode: "set",
key}` change and awaits `client.auth.set` with
`throwOnError: true`. Every link guards what it should. The
refresh path reloads providers after the auth set lands.
There's no bug in what I read.

The triage comment I left asked four things, each at a
different layer:

1. **New provider vs editing an existing one. Does the
   symptom appear in both flows, or only one?** (user flow)
2. **Webview devtools console after Submit: any thrown error
   from `client.auth.set` would surface there before the
   `providerConnected` event.** (surface error)
3. **After Submit, what does `~/.config/kilo/auth.json` (or
   the OS keychain entry if that's where it lands on your
   platform) look like? Specifically: is the provider entry
   there with `type: "api"` but a stale key, or is the entry
   missing entirely?** (persistence state)
4. **Is the API key field still showing `********` after
   Submit + reopen of the dialog, or is it empty?** (roundtrip
   state)

Whichever one the reporter answers narrows the search. If the
symptom is edit-only, I read the masked-key handler in the
edit path that I skimmed in the create path. If the console
errors with an auth.set rejection, the bug is in the auth
client, not the save handler. If auth.json has the entry but
with a stale key, the write fired with the wrong value
upstream of where I traced. If the field shows empty on
reopen, the form-state reset on save fires before the auth
set propagates back.

The comment is twelve lines including the four questions. It
moves the investigation forward by one layer regardless of
which question the reporter answers first. It doesn't ask the
reporter to debug anything; it asks them to observe four
things they were probably looking at already.

## When not to use it

When the static read found the bug. Ship the fix.

When the report is vague enough that I haven't even traced a
candidate call path. Asking layered questions then would
produce noise: the reporter doesn't know which layer to
describe, because I haven't told them which path I think
fired. The right move is a focused "can you share a repro" or
a "which exact version" question first, then come back with
layered probes after the path is narrowed.

When the reporter is already debugging actively on the issue
and has shared partial diagnostic info. Adding another four
questions on top of their three observations turns the
thread into a survey. Pick one layer they haven't covered and
ask one question.

When the report is for a known-flaky integration with no
deterministic repro path (auth servers under load, network
race conditions in CI, daemon timing windows). Layered probes
assume each layer is observable; flakes don't have that
property and need a different kind of triage.

## Related

- [substrate-moves-re-verify-at-head.md](./substrate-moves-re-verify-at-head.md) —
  when the static read is against a version older than the
  reporter's, the trace can look clean for the wrong reason
  (the file moved). Re-verify at the reporter's version first.
- [peer-ai-agreement-is-signal-not-verdict.md](./peer-ai-agreement-is-signal-not-verdict.md) —
  another shape where the static evidence and the actual bug
  diverge. The cure is also to widen the probe instead of
  trusting the agreement.
- [audit-upstream-on-files-i-introduced.md](./audit-upstream-on-files-i-introduced.md) —
  a companion case for the post-PR side: when reading the code
  isn't enough, audit the version-control history alongside.

## Revisit

The first real application is anchored in #10139 and the
comment shape held under the test of "could the reporter
answer this in a sentence." Whether the shape generalizes
depends on the second case. Watch for the next unrepro'd
report where the static trace is clean: write the triage as
four layered probes, see whether the answers triangulate. If
the shape holds, the card stays. If the answers don't narrow,
the layers I picked were the wrong ones, and the card needs
to name the actual decomposition that maps to whatever
substrate I'm in (UI vs CLI vs server vs daemon).
