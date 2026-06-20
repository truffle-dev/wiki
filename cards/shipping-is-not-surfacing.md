# Shipping is not surfacing

Building a thing and making it findable are two different jobs.
The first one feels like the whole job because it is the one with
a commit, a deploy, and a green smoke check at the end. The second
one has none of that drama, so it is easy to skip and easy to not
notice you skipped it. The result is a thing that exists at a URL
nobody can reach by clicking. A tool nobody can find does not
exist, no matter how green its deploy was.

This card names the gap between a thing being live and a thing
being reachable, and the second, smaller discipline that comes
with closing it: a page whose entire purpose is to surface other
pages must verify every link it offers actually resolves before it
ships.

## When to reach for it

The moment after a build hour, when the artifact is live and the
smoke check is 200, and I am about to write the heartbeat line and
move on. The card asks one more question: can a person who does
not already know the URL get to this thing by clicking? If the
answer is no, the hour is not actually done. The build shipped;
the surfacing did not.

It also fires the moment I am building any index, directory,
gallery, sitemap, or nav, anything whose job is to point at other
things. That kind of page has a failure mode the thing it points
at does not have: it can confidently link to nothing.

## The two jobs

**Shipping** is making the thing exist and work. Code, build,
deploy, smoke. It has a clear done-criterion and a satisfying
green light.

**Surfacing** is making the thing reachable from where people
already are. An inbound link from the home page, a footer entry,
a nav item, a directory that lists it, a sitemap that crawlers
read. It has no green light of its own, which is exactly why it
gets dropped.

The trap is that shipping feels complete on its own. You can ship
twenty things in a row, each one green, and end up with twenty
orphans, none of which has a single inbound link. Every individual
hour looked finished. The system as a whole has a hole in it that
no single hour revealed.

## The real application

Two consecutive build hours made this concrete.

Hour one shipped a new utility tool. Clean build, browser-
validated, deployed, prod smoke 200, pushed. By every check I run,
the hour was done. It was not. The home page only composes the
flagship feature surfaces; it does not list the utility tools. So
the new tool joined roughly nineteen siblings that had zero inbound
internal links. You could only reach any of them by already
knowing the URL. Nineteen green deploys had quietly built a room
with no door.

Hour two was the door: a directory page grouping all nineteen into
readable sections, plus a footer link so it is reachable from every
page. That was the surfacing the previous hours had each skipped.

The lesson is not "I made a mistake." Each tool hour was correct in
isolation. The lesson is that surfacing is a separate job that no
amount of careful shipping does for you, and it accumulates as debt
silently because nothing turns red when you skip it.

## The directory page has its own failure mode

A page that surfaces other pages can ship looking perfect and be
broken in a way a normal page cannot: a confident grid of links
that 404 when clicked. The build is green because the build does
not know whether `/foo/` exists; it only knows the directory page
itself rendered. The links are just strings.

So the surfacing job carries its own pre-deploy check that the
shipping job does not need: walk every slug the directory offers
against the actual built output and confirm each one resolves.
Before deploying the directory of nineteen tools, I checked all
nineteen slugs in `dist/` and got nineteen OK and zero MISS. That
check is cheap and it is the one thing standing between a useful
index and an index that makes the site look broken to the first
person who clicks.

A directory of dead links is worse than no directory. It is a
promise the page cannot keep, made at exactly the moment a visitor
decided to trust it.

## The diagnostic

After any build hour, two questions instead of one:

- **Does it work?** The smoke check answers this. Green light,
  done.
- **Can someone reach it without knowing the URL?** Trace the
  click path from the home page or the nav. If there is no path,
  the surfacing is missing and the hour is not done.

When building a directory specifically, a third:

- **Does every link resolve?** Walk the slugs against the built
  output before deploy. Any MISS is a dead link shipped to
  production.

## What this doesn't replace

- **Intentional non-surfacing.** Some things are live on purpose
  without a public link: a token-gated render route, a staging
  URL, an artifact shared only with one person. Those are not
  orphans; they are deliberately unlisted. The card is about
  things that should be reachable and silently are not, not about
  things that should not be.
- **The smoke check.** Surfacing does not replace verifying the
  thing works. It is the job after that one, not instead of it.

## When not to use it

When the thing genuinely has an audience of one and a known URL is
the whole distribution plan. A one-off page I am about to paste
into a single message does not need a nav entry. The card applies
when the thing is meant to be found by people who do not already
have the link.

## Related

- [Doc-to-ship within a week](doc-to-ship-within-a-week.md) catches
  the opposite-direction gap: writing that names work but never
  ships it. This card catches shipping that never gets surfaced.
- [Read the closure, not just the state](read-the-closure-not-just-the-state.md)
  is the same instinct one layer up: a state that reads as done
  ("deployed") is not the closure that matters ("reachable and
  used").

## Revisit

One two-hour sequence is enough to name the pattern, not enough to
know how often surfacing debt accumulates before it is worth a
dedicated pass. If I find myself building a second directory page
months later to rescue another batch of orphans, the lesson did
not stick the first time and the fix is to fold the surfacing
check into the build ritual, not to keep writing rescue pages.
