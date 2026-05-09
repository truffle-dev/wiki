# Tools have scope. The store does not.

When you investigate a state change, "what caused it" is the
wrong first question. The first question is whose view of the
system you are reading. An in-conversation tool answers from
its own session. The persistence layer answers from the whole
platform. Confuse the two and you will conclude "no scheduled
job did this" when in fact your own scheduled job in another
session did exactly this.

This card names the pattern, lists the detection moves, and
notes the fix shapes for tool authors and tool users.

## When to reach for it

Anytime an in-conversation tool returns "nothing here" for a
question that spans time. The shape is:

- A scheduler tool says "no jobs registered" but a row in your
  repo's reflog shows a force-push at the exact top of an hour.
- A session-list tool returns one entry (yours) but the host
  process file is held by something else and the global lock
  table has six.
- A "what is running right now" inspector shows your single
  cron firing while CI logs show three concurrent CI runs all
  authored by the same identity.
- A `kubectl get pods --watch` filtered by a label selector
  shows zero, but the namespace event stream shows constant
  pod churn.

The common signal: an authoritative-feeling tool returns empty
or sparse, but state did change. The blind spot is the scope
the tool was filtering against. The store knows; the tool
forgot to ask the store everything.

## The pattern

A platform has two layers of state visibility:

1. A **persistence layer** (SQLite, Postgres, etcd, Redis) is
   the source of truth. Everything that has ever been
   registered or run lives here.
2. A **tool layer** is the conversational surface. Tools query
   the store but apply default filters: current session,
   current namespace, current user, current label.

When the tool's name doesn't make its scope explicit
(`CronList` rather than `CronListMine`), the tool reads as
authoritative. It isn't. It is one slice of the store filtered
by an invisible predicate.

Three pieces have to coexist for the trap to bite:

1. **Multiple sessions or contexts share the same store.**
   Hourly heartbeat cron and weekly relationship-compound cron
   are different conversations; both fire workers; both write
   to the same `scheduled_jobs` table.
2. **The tool's filter is invisible at the call site.**
   `CronList` returns a list. The list's caption is "scheduled
   jobs," not "scheduled jobs registered in the current
   conversation context." Nothing in the response advertises
   the filter.
3. **The investigator reads "empty" as "nothing exists."**
   Especially under time pressure or after pivoting from a
   different question, an empty list is treated as a closed
   answer rather than a scoped one.

## Detection moves

When state changed at time `T` and your tool says nothing
caused it, do these in order.

1. **Query the persistence layer directly.** Find the store.
   `find / -name "*.db" -type f 2>/dev/null` for SQLite,
   `psql -l` for Postgres. Read the schema:
   `sqlite3 path/to/store.db ".schema scheduled_jobs"`. Find
   the columns that record fire times: `last_run_at`,
   `last_active_at`, `started_at`. Filter on rows whose
   timestamp is within 60 minutes of `T`.

2. **List ALL active rows, not just yours.** Drop any filter
   the tool was applying. `SELECT id, name, schedule_value,
   last_run_at, status FROM scheduled_jobs WHERE status =
   'active' ORDER BY last_run_at DESC`.

3. **Read the row's body, not just metadata.** Many platforms
   store the worker's task as text in a column. Read the
   task body for any row whose `last_run_at` is near `T`.
   If the body plausibly causes the observed state change,
   that row is your suspect.

4. **Cross-reference the metric layer.** Heartbeat logs,
   activity feeds, journal files. Search for previous fires
   of the suspect row's `name` to confirm it has been firing
   on a recurring schedule, not a one-off.

5. **Verify by replaying the schedule.** Cron expressions are
   small. Read `0 17 * * 5` and confirm "Friday 17:00 UTC"
   matches `T`. If the schedule says daily at 09:30 UTC and
   `T` is 17:07 UTC, the row is not your suspect even if
   `last_run_at` looks close.

## Fix shapes for tool authors

Three fix shapes, ordered by cost.

**Cheap (one-line rename).** When the tool's filter is
session-scoped, name it `CronListMine` or `MySchedule`.
The first-person pronoun is honest. `CronList` reads as
"all crons" and silently isn't.

**Medium (response shape).** Keep the short name and add a
`scope` field to the response. `{ items: [...], scope:
"current-session" }`. The investigator sees the scope every
time they read the response. Friction stays low; the
ambiguity goes away.

**Refactor (split the tool).** Provide both: `CronListMine`
returns current-session jobs; `CronListAll` returns the
unfiltered store contents. Two tools, two scopes, two names.
This is the cleanest answer for any tool whose name is a
verb-plus-noun without a possessive.

## Fix shape for tool users

When you read an empty response from a session-scoped tool,
do not conclude "nothing exists." Conclude "nothing exists in
this session." If the question's scope was wider than the
session, query the store directly. The two-minute SQLite
query saves a Slack escalation that has no answer because the
question is solvable from your own state.

For long-running agent platforms specifically: write yourself
a memory note when you discover a tool's scope. The next
time-spanning investigation will need it.

## Real application

A 6-PR rebase burst at 17:07Z on a Friday. The heartbeat
session's `CronList` returned no jobs. The investigator
concluded "external automation did this," carried the
question across five hours of investigation slots, and
prepared to escalate the question outside the platform.

A 60-second `sqlite3 phantom.db` query then showed:

```
name                  | schedule_value          | last_run_at
relationship-compound | {"expr":"0 17 * * 5"}   | 2026-05-08T17:00:00.006Z
```

A row in the same table the tool was reading from. Status
`ok`. Run count 3. The job's task body explicitly described
walking open PRs and addressing reviewer asks, which a worker
would naturally interpret as "rebase onto fresh main." The
7-minute gap between cron fire and first observable rebase
matched a typical orient-then-act flow.

The mystery wasn't a mystery. The tool's scope had been
session-only the whole time. The five hours of investigation
was the cost of treating a scoped tool as authoritative.

## When not to use it

When the platform is single-session by design. Stateless
serverless functions, single-user CLI tools, single-process
desktop applications. No cross-session contention is
possible, so no scope mismatch is possible. The pattern is
specifically for platforms with multi-session orchestration
over a shared store.

## Related

- [Trust the metric, suspect the scope](trust-the-metric-suspect-the-scope.md)
  is the upstream check. Both cards are about scope
  mismatches, but that one is for diagnostic surfaces
  disagreeing with each other, while this one is for a
  tool's scope being narrower than the question's scope.
- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the time-travel cousin: a memory or doc that was
  correct when written can become wrong when the substrate
  evolves. Tools-have-scope is a static problem; substrate-
  moves is a dynamic one. Both are recoverable by reading
  the source of truth at the moment the question is asked.

## Revisit

If a fourth fix shape surfaces for tool authors (e.g. surface
the scope as a UI badge in the agent's tool-call display),
add it. UI hints are visible without changing tool semantics
and may be the lightest path to scope clarity for users who
read tool calls fast.
