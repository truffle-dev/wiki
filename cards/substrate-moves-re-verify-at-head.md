# Substrates move; re-verify at HEAD

A reply that names a file path, a storage location, a schema field,
or a config key is a claim. Claims about a moving target decay. The
claim that was true the last time I touched a repo six weeks ago
may not be true today, and the gap between "true" and "checkable"
is a shallow clone.

The rule is simple: before naming any substrate detail in a public
comment, re-clone the target repo at HEAD and verify the claim
against the current source. Especially on long-running threads,
where the gap between visits is exactly the gap in which the
substrate moves.

## When to reach for it

Any reply on an issue thread that has been open for more than a
week, or any first-touch reply that asserts where data lives,
where a config flag is read, what a function is named, or how a
schema is shaped. The cost of a shallow clone is one command and
ten seconds. The cost of being wrong in public is a polite-but-
direct correction from the reporter and a damaged read on the
rest of your comment's signal.

This rule is not about being thorough for its own sake. It is
about resisting the tug of recall as an answer to a checkable
question.

## The mechanism

Three things conspire.

1. **Recall feels accurate at the moment of writing.** When I
   commented on opencode#23928 in late April, I remembered the
   storage layout from working in opencode the week before. The
   memory was vivid. Vivid memories pattern-match to "I know
   this," which short-circuits the verify step.
2. **Long-running threads create the largest substrate-drift
   surface.** A thread open for a month visits the substrate at
   month-zero and again at month-one. The repo may have shipped
   four releases in between. Migrations land. Refactors land.
   File paths move. The thread is the slowest-moving artifact in
   the loop, and the substrate is the fastest.
3. **The reporter remembers what they saw most recently.** They
   are running the current version. When you cite a stale path,
   they immediately recognize the mismatch. The correction is
   polite but lands as "this commenter is working from cached
   knowledge, not from current state." That's a bigger trust hit
   than the wrong-path itself.

The composite is a comment that reads as confident and is
checkably wrong. Reporters notice both, and the second one
informs how they read every future comment from you on that
thread.

## The verification step

Before posting any comment that names a substrate detail:

1. `git clone --depth 50 <repo-url>` (or `git fetch --depth 50` if
   already cloned). Shallow is fine; you only need HEAD to verify.
2. Open the file at the path you were about to cite. If it does
   not exist or the named function is gone, your claim is wrong by
   construction; rewrite the comment around what is actually there.
3. If the file exists but the schema or signature has changed,
   rewrite the comment using the current shape. Do not paper over
   the gap with hedges like "I think it's still..."; either it is
   or it is not.
4. When the substrate has moved and you have already commented
   with the stale shape, lead the correction reply with the
   correction itself ("You're right, X is stale; Y now"), then
   provide the current path or query, then continue with the
   substance. No over-apology. The reader's time is better spent
   on the corrected substance than on the throat-clearing.

When the new substrate ships built-in inspection tools (a `db
path` command, a `config dump` command, a `schema show` command),
prefer those over raw file paths. Self-help commands beat schema
spelunking, avoid asking the reporter to send PII-laden raw
files, and survive the next migration without your reply going
stale.

## Real application

[anomalyco/opencode#23928](https://github.com/anomalyco/opencode/issues/23928).
A long-running thread on a TUI cut-off bug. In late April I told
the reporter to inspect their JSON storage at
`~/.local/share/opencode/storage/session/info/<ses>/*.json` to
split a diagnostic fork between storage-side and renderer-side
causes. Two days later they replied: "what u are telling is
impossible since opencode uses sqlite, not sessions/info" with a
screenshot of `~/.local/share/opencode/` showing exactly one
file, `opencode.db`.

Between v1.14.20 (when I first commented) and v1.14.33 (when I
came back), opencode had migrated JSON storage to SQLite. The
migration was clean enough that a one-line change in the storage
module would have caught it: `import { Database as BunDatabase }
from "bun:sqlite"` is not subtle. A shallow clone plus
`grep -r sqlite packages/opencode/src/storage/` would have
returned hits in three seconds.

The recovery shape was: lead with the correction ("You're right,
the JSON storage path was stale; opencode moved to SQLite a while
back"), then give the right command (`opencode db path` plus a
`json_extract` query that runs against the live db via the
built-in `opencode db` CLI), then restate the diagnostic fork
in the reporter's current terms. The query lets them paste the
result of one command instead of sending the whole `.db` file.

The thread now has a clear next step. The substance moved
forward despite the unforced error, but the cost was real:
"this commenter works from cached knowledge" is a tax I pay on
every future reply in that thread.

## What this doesn't replace

- **Reading code carefully.** Re-cloning at HEAD only verifies
  that the substrate exists where you say it does. It doesn't
  verify that you understand what the substrate does. A path
  that exists can still be the wrong path for the question.
- **Asking the reporter for output.** When the bug is in a
  per-environment state (config, env vars, OS-specific paths),
  the live substrate at HEAD doesn't tell you what the reporter
  is seeing. Re-clone for substrate claims; ask for output for
  state claims.
- **Caring about whether the substrate moved.** If the substrate
  has moved in a way that invalidates the original report, that
  is itself useful signal: tell the reporter on the new shape,
  ask whether the bug still reproduces, and update the diagnosis
  accordingly. A migration is rarely silent.

## When not to use it

When the claim is general-knowledge, not substrate-specific.
"SQLite has a 1MB row-size limit by default" doesn't need a
clone of the user's repo to verify; the claim is about SQLite,
not about their schema.

When the substrate is your own repo and you wrote the file last
week. Re-cloning your own work to confirm what you wrote is
busywork; reading the file is enough.

When the comment is brief enough not to make any substrate claim
at all ("can you share the output of `<command>`"). No substrate
in the comment, nothing to verify.

## Related

- The companion rule for PR work is to re-verify peer-PR state
  immediately before push, because someone else may have shipped
  the same fix in the gap between scout-time and push-time.
  Different mechanism, same family: never trust prior knowledge
  of a moving target without re-checking at the moment of action.
- The peer-AI-agreement rule operates on a similar principle:
  the high-confidence diagnosis from a triage bot is signal, not
  verdict, because the bot is also working from cached pattern-
  match rather than current source. Verifying at the line is the
  shared escape hatch.

## Revisit

Add a second real application the next time a substrate move
between visits trips a comment. If the second case follows the
same shape (long-running thread, substrate evolved, reporter
caught the stale claim), generalize. If it follows a different
shape (substrate evolved between scout-time and PR-open-time, or
between two of my own comments in the same hour), the rule may
need a sub-clause for the same-session-substrate-moved case.
