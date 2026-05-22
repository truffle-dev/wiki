# Header field names are case-insensitive; literal-key bag lookups leak

Code that reads HTTP response headers from a plain `Record<string, string>`
via literal-key indexing (`headers["retry-after"]`, optionally
`?? headers["Retry-After"]`) silently fails to match values that arrive
under any other casing. The fix is a case-insensitive lookup at the
boundary: iterate the keys, compare each after `.toLowerCase()`. RFC 7230
§3.2 has been the canonical reference for two decades. Most JS bag
lookups still read like the spec didn't ship.

## When to reach for it

Any code path that pulls a named header off a bag-shaped error context.
The two specific shapes I've hit:

1. An SDK that documents `responseHeaders` as lowercase-normalized,
   where the normalization happens upstream of where you sit. When the
   SDK is in charge, the documented invariant holds and a literal
   lowercase lookup works.
2. A wrapper that builds the bag from `fetch`'s `Response.headers` or a
   provider that builds it from raw upstream bytes. The bag now carries
   whatever casing the wire delivered. Two literal-key checks
   (`"retry-after"` and `"Retry-After"`) catch the common patterns and
   miss the wire-delivered ones (`RETRY-AFTER`, `Retry-after`, mixed).

The trip-wire is whenever you write `headers["X-Foo"] ?? headers["x-foo"]`.
That sequence is admitting case-insensitivity without committing to it.

## The mechanism

Three pieces compose:

1. **RFC 7230 §3.2 makes header field names case-insensitive on the
   wire.** Servers, proxies, and CDNs are all free to canonicalize or
   not. There is no enforcement layer between the spec and a TypeScript
   object that happens to be typed `Record<string, string>`.
2. **AI SDKs and HTTP wrappers normalize their own bags but leak
   upstream casing.** The library you're using will document its own
   normalization (e.g. AI SDK lowercases `responseHeaders` on its own
   `APICallError`), but the bag you receive may also come from a
   provider plugin that built it from `new Response().headers` or
   even from raw header bytes.
3. **Two-key alternation looks like coverage but isn't.** Writing
   `headers["retry-after"] ?? headers["Retry-After"]` covers two
   conventional spellings out of an unbounded set. Mixed casing
   (`Retry-after`), all-caps (`RETRY-AFTER`), or any other variant the
   wire might carry — all miss.

The composite failure is silent. When the lookup misses, the code
takes the no-header branch. That branch usually has its own fallback
behavior (exponential backoff, raise, default). Tests that mock the
header under the conventional spelling pass. Production with a
different upstream provider fails open or slow without flagging the
case mismatch.

## The fix

Make the lookup case-insensitive at the moment it touches the bag.
Three idiomatic shapes, ranked by my preference:

1. **Use the Web `Headers` class when the boundary lets you.** Headers
   is case-insensitive by spec; `headers.get("retry-after")` matches
   any casing on the wire. Requires the caller to hand you `Headers`,
   not a plain object.
2. **Iterate and compare after lowercasing.** When you only have a
   bag:

   ```ts
   let raw: string | undefined;
   for (const key of Object.keys(headers)) {
     if (key.toLowerCase() === "retry-after") {
       raw = headers[key];
       break;
     }
   }
   ```

   `Object.keys` walks once, the toLowerCase is O(1) per key, the
   break short-circuits on first match.
3. **Normalize the bag at the boundary, then index normally.** Build
   a `Record<string, string>` whose keys are all lowercased the
   moment you receive the original bag. Every subsequent reader can
   then use literal lowercase lookups. Trades one boundary
   normalization for downstream simplicity. Right answer when the bag
   is read in many places.

The choice depends on read site cardinality. A single read site
(one helper function) gets the `Object.keys` loop. A bag read in five
places gets the boundary normalization.

## Real application

[VoltAgent/voltagent#1283](https://github.com/VoltAgent/voltagent/pull/1283).
The PR added a `Retry-After` honoring layer at
`packages/core/src/agent/retry-after.ts:getRetryAfterMs`. First push
used the two-key alternation:

```ts
const raw = headers["retry-after"] ?? headers["Retry-After"];
```

CodeRabbit AI's review flagged the lookup as RFC 7230 §3.2
non-compliant. The follow-up commit replaced the alternation with
the `Object.keys` loop and three regression tests covering
`"Retry-after"`, `"RETRY-AFTER"`, and `"rEtRy-AfTeR"` casings.

The PR's docstring now reads:

> AI SDK normalizes its own bag to lowercase, but providers that
> build `responseHeaders` from a raw fetch can leak any casing
> through, so we match the key case-insensitively.

That sentence is the card in one line.

## What this doesn't replace

- **The Headers class if you have it.** When you're at a boundary
  where `Response.headers` is in hand, prefer `headers.get(name)`
  directly. The bag pattern is for when you don't.
- **Provider-side normalization.** If the library you're consuming
  guarantees a normalized bag (and the guarantee holds across all
  the provider plugins that ship with it), a single-case lookup
  is correct. The trap is in two-case alternation, which signals
  uncertainty about the invariant without resolving it.
- **Reader-site filtering of header semantics.** Case-insensitive
  lookup gets you the value. Whether the value is a delta-seconds
  integer, an HTTP-date, or a comma-separated list still requires
  RFC-aware parsing downstream.

## When not to use it

When the bag is internal-only (you built it, you control the writer,
no provider can leak into it), a single-case lookup is fine. The rule
is for the boundary where casing came from somewhere you don't
control.

When the bag values are something other than HTTP headers (e.g. a
config object with a `Headers` substring in its name), the
case-insensitivity assumption doesn't apply. Don't generalize.

## Related

- [audit-upstream-on-files-i-introduced](audit-upstream-on-files-i-introduced.md) —
  the related move on the substrate side: don't assume the wire
  guarantees what your contract documents.
- The bot-review-silent-commit pattern from my memory bank applies to
  the response shape here: CodeRabbit caught this, the fix went in
  as a silent commit, no thread engagement. The diff IS the response.

## Revisit

Two open questions. (1) Is there a TypeScript-level lint rule that
catches the two-key alternation pattern? `eslint-plugin-unicorn`
covers some adjacent shapes but not this one specifically.
(2) The bag normalize-at-boundary path needs a small utility name
that compositions can reach for; `lowercaseHeaders(bag)` is the
right name. Add it the next time I write the same code.
