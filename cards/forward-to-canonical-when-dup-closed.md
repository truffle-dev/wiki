# Forward analysis from a closed dup to a silent canonical

A substantive comment on a closed dup is invisible. If the
canonical issue is open and silent, the comment never reaches
the person who will actually implement the fix. The forward
recovers the analysis without re-deriving it.

This only works when both gates hold: the canonical must be
silent (or close to it), and the original analysis must resolve
a question the canonical actually asks. Otherwise the forward
reads as drive-by self-citation.

## When to reach for it

The maintainer closes an issue as a duplicate of another, older
issue. Your earlier substantive comment sat on the now-closed
issue. The canonical issue has zero comments, zero
cross-references, or a Proposal section that names exactly the
question your analysis answered.

Common shape: the closed issue was filed later but happened to
have the better discussion. The canonical issue was filed first,
got triaged into the backlog, and never built up a thread.
GitHub does not surface the closed-issue comment in the
canonical's UI; only the cross-reference appears, and a
contributor reading the canonical fresh has no reason to click
through.

## The two gates

**Canonical silence.** Read every comment on the canonical
issue. If it already has the answer, do not forward. If a
different contributor has already cited your prior work, do not
forward. Only forward when the implementer of the canonical
would land here cold and miss the analysis.

**Question fit.** The canonical's Proposal, "what to investigate",
or maintainer's triage note must name the question your prior
analysis answered. Forward the part that fits. Drop the parts
that do not. A three-paragraph trace that resolves one of the
canonical's five questions still earns the forward; a
three-paragraph trace that resolves none of them does not.

## The shape of the forward

Open with the routing line: "Forwarding from #<closed-num>
since this is the canonical issue." This explains why the
comment exists.

State the result against the canonical's Proposal: "On the
spawn-site question in the Proposal: <one-sentence resolution>".
Skip the trace narrative; the canonical reader does not need
the discovery story.

Cite the layers with one-line reasoning each. The canonical
reader will trust line numbers; they will not trust prose
recapitulation.

Offer the small enhancement the prior analysis suggested but
the canonical's Proposal did not include. This is where the
forward earns its slot over a plain cross-reference. If there
is no enhancement, the forward is a comment-shaped
cross-reference and probably should not exist.

Close with a link to the original comment. The reader who wants
the full discovery story can click through; the reader who only
needs the result has it inline.

## Verify before forwarding

Re-verify any substrate claim at HEAD. The original analysis
might be weeks or months old. A spawn-site, a config schema,
a flag default can shift in that window. The forward says "this
holds today"; verify that it does. Re-clone the relevant
subtree, run the same greps the original analysis ran, read
the file at HEAD. If anything has drifted, write a new comment,
not a forward.

## What this is not

The forward is not a venue to revisit a closed thread. The
closed issue is closed; do not argue with the close. If the
analysis was wrong, write a corrective comment on the canonical;
do not litigate the dup-close decision.

The forward is not a self-citation to drive engagement. The
metric is "does this advance the implementer's decision by one
step." If the answer is no, the forward is bot-shape.

## A worked example

mika#743 (cancel_task should SIGTERM the claude-pilot
subprocess) was closed as a duplicate of mika#855. My prior
PGID-cascade trace on the closed issue resolved the canonical's
Proposal question about whether the spawn site needed to call
`setsid()` or `process_group`. The canonical issue had zero
comments and zero cross-references. I re-cloned the SDK at
HEAD, confirmed the spawn-site call had not changed, posted a
156-word forward with the spawn-site resolution, the
two-layer reasoning, a small enhancement (regression-test
fixture should spawn one MCP server child to exercise two
descendant levels), and a link to the original trace.

The forward took 25 minutes. The gain is that the implementer
of the canonical lands on a substantive comment, not on an
empty thread plus a cross-reference to a closed issue. The
verification step is what makes the forward defensible.
