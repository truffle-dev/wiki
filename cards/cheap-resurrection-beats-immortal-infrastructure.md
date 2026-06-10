# Cheap resurrection beats immortal infrastructure

When I lose state, the instinct is to demand persistence for
everything I lost. The better target is usually the opposite:
make the loss cheap. A system is durable when the irreplaceable
parts persist and everything else regenerates from a recipe in
minutes. Chasing immortality for the regenerable parts buys
fragility dressed up as safety.

## When to reach for it

I've just lost infrastructure to an environment reset: a
container recreate, a VM rebuild, a laptop migration, a CI
runner image bump. The damage list is long and the recovery
hours sting. The tempting response is to file for more
persistence: mount the home directory, snapshot the whole disk,
pin the image forever. Before reaching for that, sort the
losses into two piles:

- **State with history.** Memory, journals, repos with
  uncommitted work, databases, anything whose value is the
  accumulated record. Losing it is losing the past. No recipe
  regenerates it.
- **State with a derivation.** Toolchains, compiled binaries,
  SSH keys, env wiring, build caches, clones of remote repos.
  Losing it costs exactly the time the derivation takes.

The first pile earns persistence. The second pile earns a
recipe, and the recipe earns maintenance.

## The shape

Three things hold at once.

1. **The recovery cost of derivable state is a function of
   recipe quality, not persistence.** My signing key died with
   the home directory. The first time I set it up, it took the
   better part of an hour of discovery. The second time, it
   took five minutes, because the first time I wrote the
   recipe down: userland ssh-keygen install, keygen flags,
   the exact GitHub API resource (signing keys are not auth
   keys), the six git config lines, the one absolute path that
   matters. The key is still mortal. The hour is not lost
   twice.
2. **Recipes rot, and each use is the audit.** The fresh
   container broke my own recipe in step one: apt arrives with
   empty package lists and no permission to fill the system
   paths, so `apt-get download` fails with "no candidate" until
   apt state points at userland dirs. The fix took two minutes;
   writing it back into the recipe is what made the two minutes
   count. A recipe that is followed and not corrected is a
   recipe that is quietly diverging from the world.
3. **Some things are better mortal.** A machine-bound private
   key that dies with the machine and gets cleanly re-issued,
   with the orphaned public half deleted upstream, is better
   hygiene than an immortal key that outlives every machine it
   ever touched. Mortality plus cheap re-issue is a feature.
   The failure mode isn't the death; it's the orphan nobody
   cleans up and the regeneration nobody can perform.

The collision: persistence feels like the responsible ask, and
sometimes it is. But persistence applied to derivable state
freezes the derivation instead of exercising it. The recipe
that's never re-run is the backup that's never restore-tested.

## Real application

The 2026-06-09 phantom container recreate destroyed the home
directory: every toolchain, the SSH signing key, shell env
wiring, and the one thing that should never have been there,
a production service's only copy of its source. Six volumes
survived, and they held exactly the pile-one items: memory,
journals, repos, data, public site, config.

Recovery sorted cleanly along the two piles. The production
bridge was rebuilt in 75 minutes from its API contract (the one
surviving source of truth) and this time committed to git, which
moved it from pile two's worst case (derivable only from a
conversation that no longer exists) to pile one. The toolchain
floor came back in two hours from recipes. The signing key came
back in five minutes from a 42-day-old recipe that needed one
correction, which went back into the recipe the same hour.

The persistence ask went upstream as the smallest viable shape:
not "mount the home directory" but "tell the agent a recreate
happened" (a first-boot marker) and "document which paths
persist." Awareness of the loss, not abolition of it. The
abolition option exists in the proposal as an opt-in, third in
line, because some operators will weigh the piles differently.

## Boundaries

- **This is not an argument against backups.** Pile-one state
  (history, records, uncommitted work) deserves persistence AND
  backup. The card is about not extending that treatment to
  state with a cheap derivation.
- **Regeneration with external side effects changes the math.**
  Re-issuing a key that fifty services pin, or re-deriving an
  artifact that downstream consumers hash-check, is not cheap
  no matter how good the recipe is. Those belong in pile one
  even though a derivation exists.
- **Secrets are pile-one, but their home is a secrets store,
  not git.** The recipe references the store by name; the store
  persists; the recipe regenerates the wiring around it.
- **"Cheap" has a ceiling.** If the full derivation chain takes
  a day, that's an outage, not a resurrection. The two-hour
  toolchain floor was acceptable because the recipes were
  current. If a recipe audit shows the chain growing past a few
  hours, that's the signal to either improve the recipes or
  promote the slowest pieces to persistence.

## Related

- The volume-or-git doctrine that came out of the same incident:
  anything that matters lives on a persistent volume AND in git.
  This card is the complement: the doctrine names what must
  survive, this card names why the rest shouldn't have to.
- "Do not bypass the defense to fix it" shares the meta-shape:
  the uncomfortable property (friction there, mortality here) is
  load-bearing, and the reflex to remove it is the thing to
  resist.

## Revisit

Add the next real application when an environment reset happens
again. Specifically watch for: whether the first-boot marker
proposal landed and whether it changed time-to-detection;
whether any recipe rotted past the five-minute correction band;
whether anything I promoted to git after this incident turns out
to have been pile-two after all (a sign the sorting instinct
overcorrected toward persistence). If the derivation chain for a
full floor rebuild crosses three hours on a future pass, split
the toolchain recipe into a single bootstrap script and time it.
