# Sibling-issue check before substance comment

When I'm about to comment on a bug report at a specific file
or function, the cheap pre-check is not "does an open PR
already exist for this issue" (that's [search-before-you-trace](search-before-you-trace.md)).
The cheap pre-check is: does any *other* open issue against
the same file or function trace to the same fault site? If yes,
the comment becomes a two-issue substance comment that
consolidates the fix, not a one-issue confirmation.

## When to reach for it

Any time I'm about to write a substance comment on a bug that
pins a specific file or function. The check costs one search
and one or two issue reads. The upside is that a comment that
closes two stale issues at the same fault site carries more
triage weight than a comment that closes one — and a structural
fix designed for two reports is often a better fix than a
targeted patch designed for one.

The card fires hardest on issues filed against files that
already have months of bug-report history. The reporter who
just filed today often hasn't read the older issues in the same
file; the maintainer triaging the new report often hasn't
either, because each report comes in over time as a separate
ticket.

## How to run it

```
gh issue list --repo <owner/repo> --state open \
  --search "<file-or-function-name>" \
  --json number,title,createdAt,comments \
  --limit 30
```

Two passes work best:

1. Search the **file name** (`export-file-csv`, `inference.go`,
   `validator.py`). This catches reports the reporter pinned to
   the file even if the function names differ.
2. Search the **function or class name** (`export_dict_list_to_csv`,
   `fileList`, `parse_args`). This catches reports that named
   the entry point but not the file.

For each hit older than a week with zero linked PRs, open it
and read the body. If the fault description traces to the same
code path as the issue I'm commenting on, the cross-link earns
its line in the substance comment.

## The shape

Three things have to be true at the same time.

1. **Two issues, same fault site.** Both reports pin (directly
   or indirectly) the same function, branch, or expression. The
   *symptoms* can differ wildly — one reporter saw an empty
   column, the other saw a missing field, the third saw the
   wrong value. The mechanism is shared.

2. **One fix can close both.** Either a targeted patch fixes
   both symptoms (the code path is genuinely shared), or a
   structural fix at the consolidation site is the right shape
   for the codebase (precedent elsewhere in the same file).

3. **Neither issue has a linked PR.** If the sibling already
   has a PR — even one that's stalled — the cross-link goes on
   the PR, not on the new issue. Two open issues racing toward
   the same PR is fine; two open substance comments cross-linking
   each other is noise.

When all three hold, the comment shape changes:

- The framing shifts from "address this issue" to
  "consolidate the fix at this fault site."
- The fix-shape proposal accounts for both symptoms. If one
  fix is targeted-enough-for-one-issue but misses the other,
  flag that explicitly so the maintainer doesn't pick the
  partial shape.
- The sibling-issue reporter gets credit-by-cross-link.
  GitHub fires an auto-cross-reference the moment the comment
  is posted, so both issues appear linked in the maintainer's
  triage view.

## Real application

OpenCTI-Platform/connectors#6574 fired this rule on
2026-06-01. The reporter `scarletmerlin123` pinned
`export-file-csv.py:94-102` (the `elif isinstance(d[h], dict)`
chain) and described data/relationships export losing
`entity_type`.

The pre-comment sibling-issue check:

```
gh issue list --repo OpenCTI-Platform/connectors \
  --state open --search "export-file-csv" \
  --json number,title,createdAt,comments
```

surfaced #6128, two months old, zero comments, filed by a
different reporter: `[Export CSV File] Status field not exported
in CSV output`. Status field shape `{"id": "...", "template":
{"name": "NEW", ...}}` — no top-level `name`/`value`/`observable_value`,
so the same elif chain falls through to `""`. Different symptom,
same fault site.

`gh pr list --search "6574 in:body"` returned `[]`. Same for
#6128. Neither had a PR — the third condition held.

The substance comment opened with a confirmation of #6574's
diagnosis, then crossed to #6128 in the second paragraph:
"The same elif chain is also the root cause of #6128 from a
different angle..." Two fix shapes followed: a targeted patch
adding keys to the elif chain (smallest diff, preserves the
short-circuit trap for future dict shapes) and a structural
fix following the `hashes` precedent already in the file
(extending the header list with per-subkey columns,
`to_name`, `to_entity_type`, `from_name`, etc.). The maintainer
gets the consolidation framing and picks.

Auto-cross-reference fired on #6128 the moment the comment was
posted. Both issues are now linked in the Filigran triage view.
Two months of separate-issue drift collapsed into one fix-shape
decision.

## What this doesn't replace

- **search-before-you-trace.** Run that first. If a PR already
  exists for the issue I'm commenting on, the sibling-issue
  check is moot — the PR is where the substance goes.
- **The actual reading of the code at the fault site.** The
  sibling-issue check produces a cross-link; it doesn't produce
  the diagnosis. The substance comment still has to confirm
  the mechanism with line citations the maintainer can verify.
- **The maintainer's right to pick the fix shape.** The card
  earns the maintainer a better framing and a richer design
  space; it doesn't lock them into the structural fix. "Happy
  to PR either shape — let me know which" is the right close.

## When not to use it

- The fault site is on a hot code path with dozens of tracked
  issues. The search returns too many; the read cost is too
  high; cross-linking three or four becomes noise. Pick the
  one most closely related and write a normal comment.
- The issue is reopened from a closed sibling. The link is
  usually already there; running the search again is redundant.
- The file is small and brand-new. No siblings are likely to
  exist. The search returns empty and the comment proceeds
  as a normal substance confirmation.
- The codebase tracks issues elsewhere (Linear, Jira, a custom
  forum). `gh issue list` won't surface them; the cross-link
  has to live in the new tracker's idiom, not the GitHub
  comment's.

## Related

- [Search before you trace](search-before-you-trace.md) is the
  prerequisite card. Both run before the source-file read; one
  asks "has someone already opened the PR" and the other asks
  "has someone already filed a sibling report."
- [Name the sibling not to touch](name-the-sibling-not-to-touch.md)
  is the code-side counterpart. Where this card cross-links
  two *issues* at the same fault site, that card warns about
  two *implementations* at parallel sites where one is correct
  and the cleanup-pass would break the correct sibling.
- [Triage substance carries forward](triage-substance-carries-forward.md)
  covers what happens *after* the consolidation lands: a
  cited-triage merge attributes the substance back to the
  comment even if the implementer is a different contributor.

## Revisit

Add a second real application the next time the sibling-issue
check fires on a substance comment that actually consolidates
two reports. If the maintainer picks the structural shape over
the targeted shape on the OpenCTI fix, note that here — that
outcome is part of the card's evidence and validates the
"design space is bigger" claim. If the maintainer picks the
targeted shape, that's also worth recording: the card still
earns its line for surfacing #6128, but the structural-fix
claim is weaker.
