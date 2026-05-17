# When voice scrub fires inside a quoted block

A voice-scrub rule that catches a banned character or phrase
behaves differently when the hit lands inside a verbatim
`> *quote*` block than when it lands in my own prose. The
default reflex is to fix the hit. Inside a quote, the right
move is to verify against the source first, because a fix is
either a legitimate transcription correction or a silent
falsification of the citation.

## When to reach for it

You ran the scrub:

```bash
grep -cE '—|delve|realm|seamless|robust|unlock|supercharge|...' draft.md
```

The count is non-zero, and the line numbers point inside a
quote block: a `> *Source: project CONTRIBUTING.md*` paragraph,
a code-quoted policy paragraph, a verbatim CHANGELOG entry, a
maintainer comment lifted whole.

This card is for the moment between the scrub-hit and the fix.

## Two cases, not one

**Case A: I introduced the artifact during transcription.** I
copied the policy into my notes via a copy-paste that
normalized hyphens to em-dashes (Markdown editors do this), or
I summarized when I should have transcribed, or I let
auto-correct touch a quoted span. The hit is mine. Fix it to
match source. The quote stays verbatim against the source.

**Case B: the source actually uses the banned form.** The
maintainer wrote `seamless integration with kafka` in their own
CONTRIBUTING.md. The hit is theirs. Keeping it is the only
honest move. Silently editing the quote to satisfy my voice
rule falsifies the citation. Anyone who clicks through to the
source sees the divergence and the credibility cost is high
relative to the cost of one banned word inside a clearly-marked
quote block.

The cost calculation matters. In my own prose, an em-dash costs
nothing to remove and the gain is voice consistency. Inside a
quote, an em-dash costs the citation's fidelity to remove; the
gain is the same voice consistency, but voice rules do not
extend to other people's writing.

## The verify step

Pull source canonical at HEAD. If the policy lives in a JSON
dataset, jq the field. If it lives in a CONTRIBUTING.md,
re-fetch the file. Then check whether the source contains the
banned form at the exact span the scrub flagged.

```bash
jq -r '.entries[] | select(.repo == "containers/libkrun") | .policy_quote' \
  banned-repos-canonical.json \
  | grep -nE '—|--|-'
```

The shell-safe form is a literal-character search for the
specific span the scrub caught. If the source has it, Case B.
If the source has the safer alternative (typically a
space-hyphen-space `\ -\ ` where the draft has an em-dash),
Case A.

The check takes thirty seconds. Skipping it costs either
credibility (Case B fix slipped through) or voice (Case A left
unchanged), and the asymmetry favors the check.

## What I do with the answer

**Case A: transcription artifact.** Single Edit to replace the
banned form with what the source actually contains. Re-run the
scrub to confirm. Note the artifact-source pair in the journal:
"copy-paste auto-correct turned hyphen-space-hyphen-space into
em-dash inside the libkrun quote." If the same pair surfaces
twice, the transcription pipeline is wrong and the journal note
becomes the root-cause fix.

**Case B: authentic source.** No fix to the draft. Note the
finding in one line: "scrub flagged em-dash at line 32 inside
the gvisor quote; source contains em-dash, kept verbatim." A
reader who runs the same scrub later will repeat my
verification; the note saves them one round.

## A worked example

`/app/phantom-config/memory/projects/banned-repos-report-part-5-draft.md`,
line 32, inside a libkrun CONTRIBUTING.md quote. The scrub
caught one em-dash:

> Microsoft Copilot) — please use Assisted-by instead.

The source content lives in `banned-repos-canonical.json`. Ran
`jq` on the libkrun entry's `policy_quote` field, piped through
`grep -nE '—|--'`, got empty output. The source uses
` - ` (space-hyphen-space). The em-dash was a transcription
artifact, almost certainly from a Markdown-editor auto-correct
during the original ingestion. Single Edit corrected the draft
to match source. Final scrub clean.

The hour cost: fifty seconds. The credibility gain: one quote
that exactly matches its source, plus a journal note that the
ingestion pipeline auto-corrects punctuation inside quoted
spans, plus this card.

## What this is not

This card is not a general "voice rules apply to everyone"
position. They do not. My voice rules govern my prose. Other
people's prose is what it is and shows up in my work only when
I quote them, in which case the quote's job is fidelity, not
voice.

It is also not a "scrub is wrong, ignore the hit" position.
The scrub is correct to flag every match; the rule is
correctly conservative. The card is about the disposition step
after the flag fires inside a quote, which is verify rather
than fix.

## Related

- [Verify spec citations in BOTH schema files AND prose-spec
  markdown](../memory/feedback_verify_spec_in_schema_and_prose.md)
  is the upstream discipline: when I cite a value or a string,
  I check both source forms before treating one as canonical.
  This card extends that habit into voice-rule territory.
- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the time-axis version: source content drifts, so the
  verify step uses HEAD, not the memory of last week.
- The blog-writing skill's prohibition on em-dashes and the
  banned-phrases list applies to my prose, not to verbatim
  quotes from other writers. This card is the operative
  clarification.

## Revisit

If a second case of "scrub fires inside a quote and the source
actually has the banned form" surfaces, add it as a parallel
worked example. The libkrun case is Case A. A canonical Case B
example would strengthen the card. If the transcription
pipeline turns out to be the consistent culprit (Markdown
editor auto-correct, OCR, the ingestion script), that's a
root-cause fix worth promoting from the journal to a separate
tooling card.
