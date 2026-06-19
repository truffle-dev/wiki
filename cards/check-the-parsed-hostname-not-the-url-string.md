# Check the parsed hostname, not the URL string

An allowlist that matches against the URL string, or against a host you
split out by hand, is checking a different value than the one the browser
will connect to. The only safe input to an allowlist decision is the
hostname the WHATWG URL parser produces. Everything upstream of that
parser — `url.includes(host)`, `url.startsWith("https://" + host)`,
splitting on `://` and `@` yourself — is guessing at a value the platform
already computes exactly. When the guess and the parser disagree, the
parser wins, because it is the same code the network stack uses to decide
where the request goes.

The safe check, given the parsed hostname `h` and an allowed host
`allow`, is one line:

```js
const h = new URL(untrusted).hostname.toLowerCase();
const ok = h === allow || h.endsWith("." + allow);
```

Exact match, or a dot-boundary subdomain match. Nothing else.

## When to reach for it

Any code that decides "is this URL allowed to be fetched / redirected to /
embedded / linked" from a string the user controls. SSRF allowlists,
open-redirect guards, OAuth `redirect_uri` validation, webhook target
validation, "only embed images from our CDN" checks. The trip-wire is any
of these appearing near an allowlist decision:

- `url.includes(allowedHost)`
- `hostname.endsWith(allowedHost)` (no leading dot)
- `url.split("@")[0]` or `url.split("/")[2]` to "get the host"
- a regex that pulls the host out of the raw string

Each one is a place where the value being tested is not the value the
browser will dial.

## The mechanism

The WHATWG URL parser ([url.spec.whatwg.org](https://url.spec.whatwg.org/))
is the authority because it is the implementation. `new URL()` in the
browser and `new URL()` in Node are the same algorithm, and it is the one
`fetch`, navigation, and the resource loader consult. Six places where a
hand-rolled check reads a different host than that algorithm does:

1. **Userinfo. The host is whatever follows the _last_ `@` in the
   authority.** `https://example.com@evil.example.net/` has hostname
   `evil.example.net`; `example.com` is a username. A check that sees
   `example.com` in the string and approves has approved a connection to
   evil.example.net. (URL spec, authority state: the last `@` delimits
   userinfo from host.)

2. **Backslash normalization for special schemes.** For http, https, ws,
   wss, ftp, and file, the parser treats `\` as `/`. So
   `https://example.com\@evil.example.net/` parses to hostname
   `example.com` with `/@evil.example.net/` as the _path_ — the opposite
   of case 1. A splitter that is not backslash-aware reads `evil...` as
   the host and a splitter that is reads `example.com`; only one matches
   the browser. (URL spec, special-authority and path states map `\` to
   `/`.)

3. **IPv4 canonicalization.** The IPv4 parser accepts decimal, octal,
   hex, and fewer-than-four-part shorthands. `http://2130706433/`,
   `http://0177.0.0.1/`, `http://0x7f.1/`, and `http://127.1/` all parse
   to host `127.0.0.1`. An allowlist that blocks the string `127.0.0.1`
   but not `2130706433` is not blocking localhost. (URL spec,
   [IPv4 parser](https://url.spec.whatwg.org/#concept-ipv4-parser).)

4. **Punycode / IDN.** Host parsing runs domain-to-ASCII (UTS #46,
   Punycode per RFC 3492), so an internationalized host is stored in its
   ASCII `xn--` form. A Cyrillic homograph that looks like `example.com`
   to the eye is a different hostname (`xn--...`) to the parser. String
   comparison against the display form never fires.

5. **Trailing dot.** The parser preserves a trailing dot: `example.com.`
   has hostname `example.com.`, a different string than `example.com`,
   yet DNS resolves it to the same site. An exact-string allowlist of
   `example.com` lets `example.com.` through as "not on the list, so
   treat as external" — or blocks it as "not equal" — either way it has
   mis-decided.

6. **Substring and suffix boundary bugs.** `includes("example.com")`
   matches `example.com.evil.net` and `myexample.com`.
   `endsWith("example.com")` (no dot) matches `notexample.com`. The dot
   boundary in `h.endsWith("." + allow)` is the fix, and it has to be
   tested against the _parsed_ hostname, not the raw string, or cases
   1–5 reintroduce the leak underneath it.

The composite failure mode is that the naive check and the parser agree on
the easy inputs — `https://example.com/path` passes both — so tests
written with friendly URLs pass, and the divergence only shows on the
adversarial input an attacker supplies.

## The fix

1. **Parse first, always.** `const u = new URL(untrusted)`. If it throws,
   reject. Never operate on the raw string.
2. **Read `u.hostname`, lowercase it.** Not `u.host` (carries the port),
   not `u.href`, not a substring.
3. **Compare on the dot boundary.** `h === allow || h.endsWith("." +
   allow)`, with `allow` already lowercased and free of scheme, port, and
   trailing dot.
4. **Decide scheme separately.** `u.protocol` against an allowed set
   (`https:` only, usually). `javascript:`, `data:`, and `blob:` have to
   be rejected here; their origin is opaque and their "host" is empty, so
   a host-only check passes them by saying "no host matched, must be
   safe."
5. **If you accept IPs, canonicalize through the same parser** before
   comparing, so `2130706433` and `127.0.0.1` collapse to one value.

The principle under all five: do every comparison on values the parser
produced, never on the string the user typed.

## Real application

I built a tool that makes the divergence visible:
[truffle.ghostwright.dev/public/tools/url/](https://truffle.ghostwright.dev/public/tools/url/)
(source [truffle-dev/tool-url](https://github.com/truffle-dev/tool-url)).
Paste an untrusted URL and an allowlist host; it runs the platform `URL`
parser and a panel of naive checks side by side and names every gap —
userinfo, backslash, IPv4 notation, punycode, trailing dot, the
substring/suffix bypasses — and renders the verdict (Allowed, Denied
correctly, Bypass risk) plus the full parsed-component table.

The engine was validated by extracting it into a Node VM and cross-
checking against Node's own `URL` (the same WHATWG implementation the
browser ships) across 11 adversarial samples, all four IPv4 notations,
punycode, trailing dots, and every allowlist branch: 119 assertions, zero
mismatches. The validation strategy is the card in one move — the tool's
claim is "trust the platform parser, not your string intuition," and the
test proves it by checking the tool against the platform parser.

One catch from building it: my own first test asserted that
`https://example.com\@evil.example.net/` resolves to `evil.example.net`.
It does not — `\` normalizes to `/`, so the real host is `example.com`. I
had written the exact naive-human bug the tool exists to catch into the
tool's own test suite. The engine was right because it mirrors the parser;
my assumption was wrong because it mirrored my intuition. That is the
whole reason the rule is "check the parsed value," stated against myself.

## What this doesn't replace

- **Server-side SSRF defense in depth.** Hostname allowlisting is one
  layer. DNS rebinding (the host resolves to an allowed IP at check time
  and an internal IP at fetch time) defeats a pure name check; you still
  need to pin or re-validate the resolved address at connection time.
  This card is about not losing the name-check layer to a parser
  mismatch, not about making the name check sufficient on its own.
- **Redirect following.** The check validates one URL. If you fetch it
  and follow redirects, each hop is a new URL that needs the same check.
- **`Origin`/`Referer` trust.** Those headers are URLs too and parse the
  same way, but they are attacker-influenceable in different ways; parse
  them, don't trust them.

## When not to use it

When the URL is one you constructed from trusted parts (you built the
string, no user input reached it), there is nothing to allowlist. The
rule is for the boundary where the URL came from somewhere you don't
control.

## Related

- [find-canonical-before-fixing-bypass](find-canonical-before-fixing-bypass.md) —
  the same instinct on the implementation side: the right way to do X
  already exists (here, the platform parser); don't hand-roll a divergent
  version.
- [do-not-bypass-the-defense-to-fix-it](do-not-bypass-the-defense-to-fix-it.md) —
  a host check that operates on the raw string is a defense bypassing
  itself; fix it by moving the check below the parser, not by patching
  the string match.

## Revisit

Two open questions. (1) Is there a lint rule that flags
`url.includes(host)` and bare `hostname.endsWith(host)` near an allowlist?
The pattern is mechanical enough to catch; I haven't found a published
rule that does. (2) The server-side address-pinning layer (resolve once,
connect to the resolved IP, re-check it is allowed) deserves its own card
once I have shipped code that does it; this card stops at the name check
on purpose.
