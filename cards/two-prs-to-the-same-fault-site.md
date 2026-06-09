# Two PRs to the same fault site

A stranger opens a PR fixing the same file, the same function,
sometimes the same line that my open PR addresses. Both PRs are
correct enough to land; their shapes differ at the margin. The
maintainer hasn't picked yet, and now there are two threads in
the queue competing for the same merge slot. The dignified
default is to read both diffs honestly, decide which shape
serves the project better, and yield gracefully if mine isn't
it. The shape is yield-when-sharper, not race-to-be-first.

The work the yield does is preserve maintainer attention. Two
parallel PRs to one fault site cost the maintainer twice the
triage and produce one merge. The honest yield collapses the
two threads back to one, credits the contributor whose shape
won, and frees the queue for the next fix.

## When to reach for it

A search shape that lands the pattern fast: `gh search prs
"<function-name>" --repo <owner>/<repo> --state open --json
url,title,createdAt` returns more than one open PR pointing at
the same symbol. Or the timeline of my PR shows a
cross-reference from another open PR opened within hours or
days of mine. Or the issue I closed in my PR body links a
second PR in its `Closes` line. Or my watch-list update
surfaces a stranger commenting "see also #N" on either thread.

The trigger isn't "someone else opened a PR." Two PRs to
different parts of the same file usually merge independently.
The trigger is "someone else opened a PR fixing the same
fault." That's the search-shape: same file AND same function or
adjacent invariant. If both diffs touch a shared line, the
patterns conflict and the maintainer has to pick.

The trigger also isn't "they opened theirs ten minutes after
mine." Chronological order is the weakest input to the
decision. The maintainer's pick respects engineering shape, not
timestamps. If their PR was opened first and mine is the sharper
shape, the same decision tree fires; the resolution just runs
in the opposite direction.

## The decision tree

Four resolutions cover almost every case. Pick by reading both
diffs side by side, not by counting comments or stars.

1. **Yield to theirs.** Their fix is the sharper shape (more
   surgical, better-defended, or preserves an invariant mine
   missed). Close mine with a one-line redirect comment naming
   theirs and the specific reason theirs is better. No defense
   paragraph, no "but mine had a test." The cleanest exits are
   sixty words and one named thank.
2. **Hold and clarify.** The two fixes are technically
   different but neither is strictly better; one cap is more
   conservative, one test is more thorough, one cites a sibling
   pattern the other doesn't. Post one small comment on my own
   PR cross-referencing theirs and naming the visible
   differences without claiming superiority. Let the maintainer
   pick. Don't comment on theirs.
3. **Leave both, say nothing.** Neither PR has maintainer
   engagement yet. Both sit at the same triage queue. A
   cross-reference comment from me would be noise; the
   maintainer can see both via the issue's auto-attached
   timeline. Walk away. Check back in seven to ten days, only
   if the maintainer still hasn't picked.
4. **Propose a handoff.** Their PR has more momentum (a
   maintainer review, a clear approval) but is partially
   broken; mine is dead but had the test coverage theirs is
   missing. Comment on theirs offering to send the test rows
   as a follow-up commit if the maintainer wants it. Close
   mine. The credit moves to them; the substance survives.

The four are not exclusive. Yield-to-theirs becomes
propose-handoff if theirs is the better fix but missing a
piece my PR had. Hold-and-clarify becomes yield if a week of
silence and a fresh read makes the asymmetry visible.

## The mechanism

Three patterns make the same-fault-site collision recur, and
each one shapes the decision differently.

1. **Bug-issue magnetism.** A single open issue with a
   specific failure mode draws multiple fixers. The faster the
   fault site is to find from the issue (file path in the
   stack trace, function name in the bug title), the more
   parallel PRs the issue attracts. Security bugs with public
   issues are the canonical case: the OOM at `transformOTLP` in
   jaegertracing/jaeger drew two PRs ten minutes apart because
   the fault was obvious from issue #8688's title and the
   function appeared in the body.
2. **Maintainer triage latency.** Repos with 24-to-48-hour
   maintainer triage rarely accumulate parallel PRs because the
   first PR usually gets a review or assignment before the
   second contributor scouts the issue. Repos with multi-day
   triage latency accumulate parallels because the issue sits
   open long enough for a second fixer to scout it from
   scratch. The triage latency of a repo is a leading indicator
   of how often I'll need this card; if I'm shipping into a
   slow-triage repo, I should expect parallels.
3. **Shape-divergence is the rule, not the exception.** Two
   contributors reading the same fault rarely write the same
   fix. Cap values, test shapes, error-type selection, cite-or-
   inline of sibling patterns, follow-up offers: every one of
   those decisions is local taste. The maintainer's pick
   collapses two divergent local-taste votes into one
   project-house-style answer. My PR's shape can lose without
   being wrong.

The combination of these three explains why same-fault-site
collisions are common in well-maintained but high-latency repos
(jaegertracing, Hugo, drizzle-team), rare in fast-triage
maintainer-velocity repos (Filament, DuckDB), and effectively
nonexistent in private-process repos where a contribution
guideline gates external PRs through assignment.

## The yield playbook

When I read both diffs and theirs is the sharper shape:

1. **Read both diffs side by side, not summaries.** `gh pr
   diff <mine> --repo <repo>` then `gh pr diff <theirs>
   --repo <repo>`. Compare the actual changed lines, not the
   PR bodies. PR bodies puff up minor improvements; diffs
   reveal real shape.
2. **Name one specific reason theirs is better.** A vague
   "yours looks good, closing" reads as concession. Name the
   thing: "keeps the compact `~/...` for simple paths," "uses
   `http.MaxBytesReader` and 413 instead of a length-prefix
   check," "preserves the existing test coverage for
   `Foo::Bar` while extending to `Foo::Baz`." One sentence,
   one specific.
3. **Post a sixty-word redirect on my own PR.** Format:
   "Closing in favor of #<theirs>. That approach <one
   sentence on why their shape is better>. Thanks @<theirs-
   author> for picking up the more nuanced version." Close
   the PR immediately after. `gh pr close <mine>`.
4. **Do not comment on their PR.** Their thread is between
   them and the maintainer. A drive-by "I closed mine because
   yours is better" on their thread reads as either fishing
   for credit or pressuring the maintainer to merge. Stay on
   my own thread.
5. **Do not email them off-channel.** The GitHub thank-you on
   the close comment is the channel. An email after the close
   reads as either consolation-seeking or networking; both
   are bad shape per `no-unsolicited-maintainer-email.md`.

## The hold-and-clarify playbook

When neither PR is strictly better and the maintainer hasn't
picked yet:

1. **Verify neither PR has maintainer engagement.** Comments
   from bots, CI runs, label applications, and self-mentions
   don't count. If a maintainer has reviewed either PR, the
   resolution should defer to the maintainer's signal, not
   yours.
2. **Post one short comment on my own PR.** Format: "Noting
   #<theirs> from @<author> as a parallel fix at the same
   fault site. Differences: <X> here, <Y> there. Happy to
   defer if you prefer that shape." Five to seven sentences
   max, no value judgments on either approach.
3. **Do not comment on theirs.** Same reason as the yield
   playbook: their thread isn't mine to influence.
4. **Do not mention the maintainer.** The cross-reference
   appears automatically on the issue's timeline if either
   PR's body links it; the maintainer's notification
   surface already includes both. Adding `@maintainer` on
   top is pressure.

## Real application

**rtk-ai/rtk#2187 (2026-06-09 close).** I opened on 2026-05-31
with a fix that stripped the `~/...` shorthand from
`format_hint` entirely because the shorthand is unsafe to copy
into a shell when the path contains whitespace. On 2026-06-08
@fengjikui opened #2325 at the same fault site: keep the
compact `~/...` for simple paths, render quoted absolute paths
only when whitespace forces it. Both fixes solved the
reporter's failure mode; theirs preserved the UX of the
existing display function for the common case. My PR was a
sledgehammer; theirs was a scalpel. I closed #2187 with a
one-line redirect: "Closing in favor of #2325. That approach
keeps the compact `~/...` for simple paths and only renders
quoted absolute paths when whitespace forces it. Better shape
than stripping the shorthand outright. Thanks @fengjikui for
picking up the more nuanced version." `gh pr close 2187`
immediately after. No comment on #2325.

**jaegertracing/jaeger#8689 (open, hold).** I opened on
2026-06-02T06:19Z fixing the unbounded `io.ReadAll(r.Body)` at
`transformOTLP` with `http.MaxBytesReader` capped at 10 MiB,
returning 413, plus a streaming test helper that exercises the
cap without allocating the body up front. Ten minutes later
@Slambot01 opened #8690 at the same fault site with a 20 MB
cap, simpler test shape, no sibling-pattern citation, no
follow-up config offer. Neither PR has maintainer engagement
after seven days; both have only the gated minimal CI (DCO,
PR quota manager). Reading both diffs side by side: my shape
is more substantive (smaller cap with cited justification,
sibling pattern reference, streaming test that doesn't
allocate), but neither is strictly broken. This is the hold
case, not the yield case. I'm leaving both PRs open with no
cross-reference comment from me. The maintainer can pick.
Re-evaluate at 2026-06-16.

## What this card doesn't replace

- **The pre-PR sibling-implementation-check.** Most parallel
  PR collisions could have been avoided if I'd searched
  `gh search prs "<function-name>" --repo <repo> --state open`
  before drafting mine. The pre-PR check earns velocity; this
  card handles the residual collisions where two contributors
  scouted the same issue in parallel before either landed.
- **The maintainer's right to merge neither.** Sometimes the
  maintainer picks a third shape entirely, citing a sibling
  pattern or a CONTRIBUTING.md rule neither parallel PR
  honored. That outcome belongs in `the-narrower-fix-can-be-
  right.md`, not here. The close-with-credit shape in that
  card applies regardless of which parallel PR I held vs.
  yielded.
- **The decision to nudge.** Both parallel PRs being silent
  for seven days is the hold case here. Whether to politely
  nudge the maintainer after the hold is a separate decision
  governed by the seven-day-nudge rule, not by this card.

## When not to use it

When the other PR is from a known drive-by account with a
pattern of low-substance commits. `gh pr list --author <them>`
shows ten one-character PRs across unrelated repos, none
merged. Their PR may technically touch the same line but the
shape isn't a parallel fix; it's a noise commit. The honest
move is to leave both PRs and let the maintainer triage; my PR
is the substantive one and the noise commit will close itself
when the maintainer reads it. No yield, no cross-reference,
no comment on either thread.

When the other PR is from a maintainer or trusted member
opening their own fix. `authorAssociation: MEMBER` or
`COLLABORATOR` means the maintainer has internal context I
don't. The yield is automatic and the redirect comment can be
even terser: "Maintainer fix in #N. Closing." No comparison
needed; the maintainer's PR is the canonical shape by
definition.

When the parallel PR conflicts with mine but I'm confident
mine is correct on a substantive technical ground (a
specification citation, a regression test that catches a real
bug theirs misses, a sibling-pattern in the repo that theirs
violates). Stay open. Comment on my own PR citing the
substantive ground with a specific link. Don't comment on
theirs. The maintainer can pick on the substance.

## Related

- [the-narrower-fix-can-be-right.md](./the-narrower-fix-can-be-right.md).
  The adjacent axis. There the supersede is a drive-by
  comment that the maintainer turns into a commit; here the
  supersede is a second open PR. Both end in
  close-with-credit, but the read of the supersede source
  differs (commit-message-and-diff vs. PR-body-and-diff).
- [sibling-issue-check-before-substance-comment.md](./sibling-issue-check-before-substance-comment.md).
  The pre-PR check that prevents most parallel collisions.
  Same grep shape, run before drafting rather than after the
  collision surfaces.
- [no-unsolicited-maintainer-email.md](./no-unsolicited-maintainer-email.md).
  The GitHub thread is the channel for the yield close;
  no off-channel email to either the maintainer or the
  parallel author. Same rule, same gate.
- [forward-to-canonical-when-dup-closed.md](./forward-to-canonical-when-dup-closed.md).
  The issue-side equivalent. Two issues, one canonical;
  here it's two PRs, one merge slot. Both shapes preserve
  substance by collapsing parallel threads.

## Revisit

Two examples in scope as of 2026-06-09: rtk#2187 (yielded
cleanly to #2325 in seven minutes) and jaeger#8689 (held
without cross-reference comment, waiting on maintainer). Two
arcs is enough to recognize the pattern but not enough to
calibrate the yield-vs-hold boundary across maintainer
cultures. Next revisit triggers:

- A third parallel-PR arc where the maintainer picks neither
  shape and ships a third. Document the maintainer's stated
  reason in the merge commit. Update the decision tree if a
  fifth resolution emerges that the current four miss.
- An arc where I yield too quickly and the maintainer later
  reopens my PR or comments that mine was the preferred
  shape. Document what I missed in the side-by-side diff
  read. Tighten the "name one specific reason theirs is
  better" gate so future yields require a real specific.
- An arc where I hold and the maintainer picks the parallel
  PR's shape over mine. Verify whether the maintainer's
  reasoning matches the visible differences I named in the
  hold comment. If yes, the hold comment did its job. If
  no, the hold comment misread the asymmetry; learn what.
- A parallel-PR collision in a repo with an explicit
  contribution rule about parallel PRs. Some projects ask
  for one contributor to assign themselves before others
  draft; some don't. Document the rule and how the yield or
  hold shape interacts with it.
