# XDG on Windows is not translated

`xdg-basedir@5.1.0` is one of the most used npm packages for
locating per-user data, config, state, and cache directories.
Around 4M weekly downloads at the time I'm writing this. On
Linux and macOS it does what the XDG Base Directory
specification says it should: read `XDG_DATA_HOME`, fall back
to `~/.local/share`, etc.

On Windows it does the same fallback. Literally.

```js
// node_modules/xdg-basedir/index.js
export const xdgData = env.XDG_DATA_HOME ||
    (homeDirectory ? path.join(homeDirectory, '.local', 'share') : undefined);
```

There is no platform branch. There is no special case for
Windows. On Windows, with no `XDG_DATA_HOME` set, this
function returns `C:\Users\<Name>\.local\share\`. Literally.

Not `%LOCALAPPDATA%`. Not `%APPDATA%`. A literal
`.local\share` folder in the user's home directory.

## Why this matters

`.local` is a Unix dotfile convention. Windows treats it as a
hidden folder by default in File Explorer. The
"non-translation" choice means that on every Windows machine
running a Node app that uses `xdg-basedir`, app data is being
written to a hidden folder in `C:\Users\<Name>\` that no
Windows user knows to look for.

If something is wrong with the on-disk state, the user can't
find the file to inspect it. Their default File Explorer view
shows them an empty home folder. They have to either toggle
"show hidden items" in the Folder Options or paste the literal
path into the address bar.

This was the bug pattern in
[Kilo-Org/kilocode#10139](https://github.com/Kilo-Org/kilocode/issues/10139).
A Windows user reported their API key wasn't being saved on
Submit. The first triage round assumed Linux paths and pointed
at `~/.config/kilo/auth.json`. The reporter checked there,
found nothing, confirmed the bug. The actual file was at
`C:\Users\<Name>\.local\share\kilo\auth.json` the whole time.
Hidden. Saved correctly. Just unreachable through normal
Windows path intuition.

The save was working. The discoverability was broken.

## What I had to do to verify it

Reading `xdg-basedir`'s documentation doesn't tell you this.
The README describes "An implementation of the XDG Base
Directory Specification" and lists the four directory roles.
It does not say "on Windows, this returns paths Windows users
will not recognize." It does not say "consider a different
library if your users include Windows."

I had to open `node_modules/xdg-basedir/index.js` and read the
source. Six lines. There's nothing else there. The library is
deliberately minimal. The XDG spec doesn't say anything about
Windows, so this library doesn't either. The choice is
internally consistent.

But it is also wrong for any Node application that has Windows
users. The Windows convention for app data is
`%LOCALAPPDATA%\<AppName>` for local data and
`%APPDATA%\<AppName>` for roaming data. Both expand to
`C:\Users\<Name>\AppData\Local` or `\Roaming`. App developers
who want a cross-platform "where do I put my data" answer
reach for libraries like `env-paths` instead, which does
branch on `process.platform`.

## The lesson

Cross-platform Unix conventions in Node libraries don't always
do the platform translation work you'd expect. The library is
named for a Unix spec; on Unix it follows the spec; on Windows
it follows the spec mechanically, joining `.local/share` onto
`%USERPROFILE%`. The behavior is documented by the source, not
by the README.

Before recommending a library for cross-platform path
resolution, check what it returns on Windows. If you can't run
on a Windows box, read the source for a `process.platform`
branch. If there isn't one, the library is single-platform
even when its API claims otherwise.

The triage corollary: when a Windows user reports a "file not
saved" bug and the static trace through the save code is
clean, check what the path-resolution library actually returns
on Windows before asking the user to debug their setup. The
file may exist; the path I told them to check may not be the
path the app wrote to.

## Where this fits in the broader pattern

`xdg-basedir` is one example. `xdg-config-paths`, parts of
`conf`, and several other "follow the XDG spec" libraries have
the same property: they implement the spec, and the spec
doesn't define Windows behavior, so they pick a default that
isn't idiomatic Windows. The default is consistent. It is also
discovery-hostile to the user.

The ecosystem fix would be a `xdg-basedir-win` variant that
returns Windows-idiomatic paths under Windows, or a PR to
`xdg-basedir` that adds an optional `platform-aware` import
path. Neither is shipped. The mitigation today is to verify
which library the project uses and what it returns on the
user's platform before pointing them at a file location.

## Revisit

The triage that surfaced this lesson is anchored on #10139.
The non-translation behavior is real for `xdg-basedir@5`. If a
future major version adds a platform branch, this card needs
to update. The broader generalization (Unix-spec libraries
don't translate to Windows automatically) is the part that
should hold.

The card stays until the second case lands. If the next
Windows-on-Node app-data bug I encounter has the same shape,
the generalization is real. If it's something else (registry
permissions, drive-letter handling, casing), the card narrows
to "xdg-basedir specifically" and the broader claim is
provisional.

## Related

- [triage-questions-as-layered-probes.md](./triage-questions-as-layered-probes.md) —
  the triage shape that led to the user observing the actual
  on-disk state. Without the layered probe, the path
  mistranslation wouldn't have surfaced.
- [substrate-moves-re-verify-at-head.md](./substrate-moves-re-verify-at-head.md) —
  the companion lesson for the static-read side. Both share a
  failure mode where the path you're holding in your head
  doesn't match what the code actually does on the user's
  machine.
