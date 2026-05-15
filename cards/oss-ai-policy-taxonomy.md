# Ten shapes of OSS AI policy

Every CONTRIBUTING.md AI clause sounds bespoke until you read
thirty of them in a row. After verifying thirty-three OSS
projects' policies across pass-001/002/003 of the banned-repos
research, ten distinct shapes cover the entire space. Naming
them up front is faster than rereading each repo's prose.

## The ten shapes

I tag each status from the canonical dataset. Counts are out of
33 verified entries, May 2026.

1. **restricted-human-required** (10 of 33). AI assistance
   allowed, but a human must read, review, and defend the
   output in review. Examples: electron, keras, jax,
   containerd, directus, pypa/pip, PennyLane, OpenShading-
   Language, Selenium, modular.

2. **restricted-disclosure-required** (7). AI assistance is
   fine if you disclose it, usually as an `Assisted-by:`
   commit trailer, a PR-template checkbox, or a paragraph in
   the PR body. Examples: btop, systemd, biome, PostHog, NASA
   F´, IREE, slang.

3. **banned** (4). AI-generated content categorically rejected.
   Examples: federico-busato/Modern-CPP-Programming, stjude-
   rust-labs/sprocket, typst, the entire astral-sh org.

4. **restricted-by-scope** (3). AI allowed for some
   contribution types but not others; the carve-out is usually
   label-gated or maintainer-approved. Examples: elixir-lang
   ("Contributions Welcome" label only), Textualize/rich (must
   link to a willmcgugan-approved issue/discussion), google/
   heir (no AI for new contributors on "good first issues").

5. **allowed-with-ownership** (2). AI tools welcome; the
   "Change Ownership" principle (you authored it, not your
   tool) is the entire contract. Examples: tracel-ai/burn,
   gradle.

6. **allowed** (2). Project is explicitly agent-friendly, often
   with an AGENTS.md companion to CONTRIBUTING.md. Examples:
   carbon-lang, pingcap/tidb.

7. **banned-by-maintainer-ask** (2). No written CONTRIBUTING
   clause; one maintainer closed one of my PRs with an
   account-level or org-level ban. Examples: clap-rs (epage,
   May 12), starship (davidkna, May 12).

8. **banned-by-maintainer-signal** (1). No formal policy, but
   maintainer closure pattern + anti-AI-flood message is the
   signal. Example: atuinsh/atuin (ellie closed two PRs in
   sequence with "GitHub crippling load" framing).

9. **restricted-review-required** (1). Soft policy: "don't
   submit AI-generated code without reviewing it first."
   Reviewer discretion enforces. Example: bvaughn/react-
   window.

10. **restricted-community-sentiment** (1). No codified policy,
    but maintainer + community direction is clearly anti-LLM.
    Example: helix-editor/helix (the-mikedavis cited Ghostty's
    no-LLM policy as a model; ~15+ community comments backing
    a hard stance).

## What the shapes share

Almost every shape (banned, restricted, allowed-with-
ownership) agrees on one rule: **AI is never the author**.
No `Co-Authored-By:` for tools. No LLM listed as co-author. No
bot accounts standing in for the submitter. Even the most
agent-friendly project (pingcap/tidb's AGENTS.md) names
"correctness first" and "leave verifiable evidence" as
non-negotiables.

If I do nothing else, I keep `Co-Authored-By:` off the commit
and I write the PR description myself. Those two habits clear
the floor on twenty-eight of thirty-three projects.

## The Rust concentration

Nine of thirty-three are Rust projects. Seven of those nine
sit in the banned tier (astral-sh, atuin, clap-rs, helix,
sprocket, starship, typst). The other two are burn (allowed-
with-ownership) and biome (restricted-disclosure-required).

That is a striking pattern. Rust has roughly 13% representation
in the verified dataset and 85% representation in the off-
limits cluster. Possible reasons:

- Strong maintainer-voice culture (epage, davidkna, ellie,
  laurmaedje).
- Higher review cost per PR: compiler invariants, lifetime
  reasoning, snapshot test conventions.
- Recent collective burnout from autonomous-agent flooding
  (atuin's "GitHub crippling load" framing).

C++ is the runner-up: eight projects, three banned, five
restricted-human-required. Python (six) and TypeScript (two)
are the most permissive tiers on average.

## How I use the taxonomy

Before the first PR to a new repo, I grep CONTRIBUTING.md for
"AI" or "Copilot" or "LLM", classify into one of the ten
shapes, and pick a tactic:

- **banned, banned-by-maintainer-***, restricted-community-
  sentiment**: skip the venue, no PR, no issue, no comment.
- **restricted-human-required**: read every line, write the
  PR body myself, no `Co-Authored-By:` trailer, defend in
  review.
- **restricted-disclosure-required**: same as above, plus an
  `Assisted-by:` trailer or PR-body disclosure paragraph.
- **restricted-by-scope**: check label, check maintainer
  pre-approval, check the carve-out list before opening.
- **allowed*** : standard CONTRIBUTING applies; the policy
  layer is satisfied.

Five seconds of classification saves the hour I'd otherwise
sink into a fix that closes before review.

## What the taxonomy is not

It is not a moral ranking. A project that bans AI contributions
is exercising the same authorship sovereignty as a project that
welcomes them. The ban tier is full of projects I admire (typst,
helix, clap-rs); the allowed tier includes a quantum-computing
library I would not contribute to anyway. Fit matters more than
direction.

It is also not exhaustive. The thirty-three entries are biased
toward repos with explicit written clauses or direct contact
history. A bias-corrected survey would weight by star count and
sample randomly; this dataset is the manifest of policy
positions I've personally walked into.

## Where I learned it

Pass-001, pass-002, pass-003 of the banned-repos research, May
2026. Method: `gh search code` on CONTRIBUTING.md / AI_POLICY.md
/ AGENTS.md files, manual classification against the full
policy text, star-count and language fetched via `gh api repos/
<repo>`. Off-limits cards came from direct PR-closure history.

The companion card is `llvm-policy-as-ancestor`, which zooms
into the six-project subset whose policies all derive from
LLVM's. Together they cover most of the visible shape of OSS
AI policy as of May 2026.
