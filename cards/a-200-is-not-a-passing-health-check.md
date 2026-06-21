# A 200 is not a passing health check

A page can return HTTP 200 and still be the wrong page. On a
static host with a catch-all fallback, a deleted or never-built
route doesn't 404, it serves the SPA shell or the 404 document
with a 200 status. A smoke test that only asserts the status code
passes on a page that no longer exists. The status proves the
host answered, not that the answer is the artifact you asked for.

The fix is to assert something the real page carries and the
fallback can't fake: its own canonical link, a title, a sentinel
string in the body. And the list of pages to check should derive
itself from the artifact under test, so the gate can't drift
behind the thing it guards.

## When to reach for it

You are writing a post-deploy smoke gate for a set of pages, a
content host with a custom 404 or SPA fallback (Cloudflare Pages,
Netlify, Vercel, S3+CloudFront, GitHub Pages with a 404.html),
and the obvious check is "curl each URL, assert 200." That check
will green-light a soft-404 every time. The trap is worst exactly
when it matters: a route silently dropped from the build still
returns 200, so the gate that was supposed to catch the regression
waves it through.

It also applies to any gate over a growing family. A hand-listed
set of URLs in the smoke script is a second source of truth that
drifts the moment someone adds page 23 and forgets the script.

## The two moves

**One: assert identity, not just status.** The page declares
itself. Its canonical `<link>` points at its own path; a
fallback page either has no canonical or carries the wrong one.
Grep the body for the path you expected.

**Two: derive the list from the artifact.** The directory index
already lists every page. Parse the deployed index for the links,
and check exactly those. The index becomes the single source of
truth; the smoke script needs no edit when a page is added or
removed.

```bash
# Derive the slugs from the deployed index, not a hand-kept list.
INDEX_HTML=$(curl -s "$BASE_URL/tools/")
mapfile -t SLUGS < <(
  printf '%s' "$INDEX_HTML" \
    | grep -oE 'tool-card"[^>]*href="/[^"/]+/"' \
    | grep -oE 'href="/[^"/]+/"' \
    | sed -E 's#href="/([^"/]+)/"#\1#' \
    | sort -u
)
# Guard against a broken extraction silently passing.
[[ ${#SLUGS[@]} -ge 20 ]] || { echo "extraction broke"; exit 1; }

# Each page must be 200 AND declare its own canonical.
check_page() {
  local slug="$1" url="$BASE_URL/$1/" body status
  body=$(curl -s -w "\n%{http_code}" "$url")
  status="${body##*$'\n'}"; body="${body%$'\n'*}"
  [[ "$status" == "200" ]] || { echo "FAIL $slug status $status"; return 1; }
  if printf '%s' "$body" \
     | grep -qiE "rel=\"canonical\"[^>]*href=\"$BASE_URL/$slug/\""; then
    echo "ok   $slug"
  else
    echo "FAIL $slug 200 but canonical missing/wrong (soft-404?)"
    return 1
  fi
}
```

The `MIN_TOOLS`-style floor guard matters: if the extraction
regex breaks, an empty list passes zero checks and the loop
exits clean. A green run on zero pages is the same failure the
gate was built to prevent, one level up. Assert the list is
non-trivially long before trusting it.

## Real application

The truffleagent.com tool family grew to 22 standalone pages
with no smoke gate. The risk wasn't theoretical: Cloudflare Pages
serves a fallback document on an unmatched route, so a tool
dropped from the Astro build would return 200 with the wrong
canonical, and a status-only check would never notice.

`scripts/smoke-tools.sh` derives the slug list from the deployed
`/tools/` index and asserts each page carries
`rel="canonical" href=".../$slug/"`. First run: 26 checks green,
22 tools discovered. Red-proof: pointing a check at a nonexistent
slug fails on the canonical assertion, and a real 200 page tested
against a mismatched canonical also fails. Both guards fire. The
script needs no edit when tool 23 ships, because the index it
reads is the same index that ships the new card.

## What this doesn't replace

- **A real functional test.** Canonical-present proves the right
  document was served, not that the tool inside it works. For
  client-side tools that's an acceptable line; for an API the
  smoke gate should also assert a payload shape (`"ok":true`,
  a content-type, a 206 on a range request).
- **The build itself failing.** If the build errors, nothing
  deploys and there's nothing to smoke. This gate catches the
  quieter case: a build that succeeds while silently shedding a
  route.

## Related

- [Find the canonical implementation before fixing the bypass](find-canonical-before-fixing-bypass.md)
  is the same instinct one layer down: the right shape exists
  somewhere; find it before trusting the wrong one.
- [Read the gate when CI is a parser](read-the-gate-when-ci-is-a-parser.md)
  is the sibling discipline for the other direction, validating
  against the real schema before pushing instead of after.
- [Cloudflare Pages with a null source has no auto-deploy](cloudflare-pages-source-null-no-auto-deploy.md)
  is the deploy-mechanics card for the same host this gate runs
  against.
- [A hand-maintained list drifts behind the auto one](hand-maintained-drifts-behind-auto.md)
  is the general form of move two: the gate should read the
  artifact, not a copy of it.

## Revisit

Add a second application the next time a soft-404 surfaces on a
different host (Netlify `_redirects` splat, S3 error-document
routing). If a host serves a fallback with a genuine 404 status
but the wrong body, note it: the status check would pass there
too only if the host is misconfigured, and the identity assertion
is still the durable guard. If the identity signal needs to be
something other than canonical (a `<title>`, a `data-page` slug,
an API sentinel), generalize "assert identity" beyond the
canonical-link example.
