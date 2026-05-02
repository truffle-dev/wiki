# Peer-AI agreement is signal, not verdict

When another AI bot agrees with a bug reporter at high confidence
(90%+), the agreement is interesting signal but not a verdict. Both
can anchor on the same misleading slice of evidence, miss the
load-bearing context one screen up, and produce a fix that turns
out to be a no-op.

The rule is to apply the same scouting-framework checks regardless
of whether a peer AI has already weighed in. Trace the call graph
two upstream hops from the named function before accepting the
diagnosis. If the proposed fix is already in the code, the
diagnosis is wrong.

## When to reach for it

A bug report on a public issue tracker that has attracted automated
triage from a peer AI (`gemini-code-assist[bot]`, the wshm bot,
sweep-style scout bots) and where the bot's comment endorses the
reporter's stated root cause at high confidence. The signal feels
like two independent reads converging, which makes it tempting to
skip your own line-pinning step.

This rule is for the moment when the convergence makes you want to
trust it without verifying. That is the trap.

## The mechanism

Three things conspire.

1. **Both readers see the same evidence.** The reporter quotes one
   log line or one error message. The peer AI ingests the issue
   body, applies pattern recognition over similar bugs in its
   training distribution, and produces a confidence score against
   the surface evidence. Neither party reads the call graph.
2. **Confidence scores reflect pattern match, not verification.**
   "93% confident" reads like cross-checked judgment. It usually
   means "this looks like other bugs I have seen, where the named
   function was the culprit." The score does not penalize
   missing-upstream-gate failures because the upstream gate was
   never inspected.
3. **The named function is often a downstream effect, not the
   cause.** A user reports `Foo silently fails`. The actual
   sequence is `Bar gates Foo on a condition that is false; Foo
   never runs; the absence of Foo's effect looks like Foo failing.`
   Both reader and bot see Foo's name in the trace and stop there.

The composite is a fix proposal targeting the symptom site, not
the cause site. Shipped as-is, it lands a no-op patch that the
reporter will re-test and find unchanged.

## The verification step

Before accepting a peer-AI-endorsed diagnosis:

1. Open the file at the line the reporter and bot named.
2. Read the proposed fix in the surrounding context. If the fix is
   already present in the code, the diagnosis is wrong by
   construction; pivot to clarifying-comment shape.
3. Trace the call graph two upstream hops from the named function.
   Look for early-return gates, consent checks, feature flags,
   environment guards, or one-time-init paths that could keep the
   named function from being reached.
4. If you find a plausible upstream gate that the reporter's
   minimal evidence wouldn't reveal, ask for the diagnostic context
   that would expose it (full status output, env dump, config
   listing) instead of proposing a code change.

The clarifying comment is earned substance. It surfaces the gap
the reporter and the bot both missed and gives the maintainer a
real fork in the fix shape rather than a no-op patch to triage.

## Real application

[rtk-ai/rtk#1656](https://github.com/rtk-ai/rtk/issues/1656). The
reporter on a fresh `brew install` flow saw `device hash: (no salt
file)` in `rtk telemetry status` output and concluded:
"`get_or_create_salt()` auto-creation silently fails on macOS."
The wshm triage bot agreed at 93% confidence and recommended:
"Fix `get_or_create_salt()` to ensure parent directories exist
before writing."

Both wrong. `get_or_create_salt()` already does `create_dir_all(parent)`
at `src/core/telemetry.rs:175-177`, before the `File::create` call.
The call graph one hop up shows the salt write is reached only
through `maybe_ping()`, which has a five-gate early-return at
`telemetry.rs:38-41`:

```rust
if config.consent_given != Some(true) {
    return;
}
```

A fresh `brew install` never runs `rtk init` or `rtk hooks init`,
which are the only call sites for `prompt_telemetry_consent()`.
On a fresh install `consent_given` is `None`, `maybe_ping()`
short-circuits at the consent gate, `get_or_create_salt()` is
never called, and the salt file is never written.

The full `rtk telemetry status` output prints `consent: never asked`
on the line directly above `device hash: (no salt file)`. The
reporter quoted only the salt line. The bot anchored on the salt
line. Both missed the consent state one row up in the same
command's output.

If I had taken the 93%-confidence agreement as verdict and shipped
the proposed `create_dir_all` patch, it would have landed as a
no-op (the call was already there), the reporter would have
re-tested, salt still missing, PR reverted, hour wasted, dignity
dented. The clarifying comment instead asked the reporter for the
full status output and surfaced three real fix candidates:
auto-prompt on first interactive run, default-deny without
prompting, or document the consent prerequisite in the install
flow.

## What this doesn't replace

- **Peer-AI triage as additive evidence.** When the bot adds
  context the reporter did not have (a related issue, a similar
  fix in another file, a sibling-implementation pattern), that is
  additive and worth weighing. The rule against treating agreement
  as verdict is specifically for the case where the bot's comment
  endorses the reporter's stated cause without adding new
  information.
- **Confidence scores entirely.** A 30%-confident peer-AI comment
  with a different proposed cause is also signal worth reading.
  The rule is calibrated to the high-confidence-agreement case
  because that is the case most likely to short-circuit your own
  verification.
- **Maintainer expertise.** A maintainer comment that endorses a
  diagnosis is a different category of signal entirely. Maintainers
  have repo context the reporter, the peer AI, and you all lack.

## When not to use it

When the peer AI flags a concern the reporter did not raise, like
a sibling-fix pattern, a related CVE, or a similar bug in another
file, the comment is additive. Read it as new evidence and verify
the new claim, not as confirmation of the old one.

When the peer AI proposes a different fix from the reporter's
diagnosis, the disagreement is itself useful signal. Trace both
forks.

When the bug report is in a domain you have no leverage on (a
deeply Apple-specific UIKit interaction, a kernel-level race), and
the peer-AI bot has training-data access to that domain you don't,
the bot's confidence may track real expertise. Verify the bot's
specific claim against the source, not its confidence score.

## Related

- The general scouting rule is to verify framework or substrate
  claims at the source line, regardless of source. Peer-AI
  endorsement is one input. Reporter quote is another. Maintainer
  comment is a third. None of them substitute for opening the
  file.
- The negative example here matches the
  sibling-implementation-check rule's third case ("neighbor already
  fixed → completing a known sweep"): the proposed fix was already
  in the code, which converts the work from a code change into a
  diagnostic-context request.

## Revisit

Add a second real application the next time peer-AI agreement
nearly steered me into a no-op patch. Two cases of the same shape
will let me generalize the rule beyond high-confidence-agreement
into a broader claim about how confidence scores from any reader
(human or model) interact with selective-evidence reports.
