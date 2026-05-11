# The wrap is the caller

When you wrap a script body in an anonymous function to scope
runtime options, the wrap becomes the immediate caller of every
identity-introspecting check inside it. Any line that asks "who
called me?" sees the wrap, not the real top level. Caller-identity
checks have to live outside the wrap, even when everything else
they coordinate with lives inside.

## When to reach for it

A script needs to scope a runtime option locally (zsh's
`emulate -L`, bash's `local`-with-options pattern, Python's
context manager around globals, Lua's environment swap, JS's
strict-mode wrap). The natural shape is an immediately-invoked
function: define a wrapper, set the option at the top of it, do
the work, the function returns, the caller's environment snaps
back. Inside the wrap there is also a piece of logic that
introspects "am I being autoloaded vs sourced," "am I the
top-level entry," "what's the caller's file," and dispatches
based on that. The dispatch breaks the moment the wrap goes on
and nothing else in the wrap's body explains why.

## The shape

Three things are true at the same time.

1. **An IIFE creates a new call frame.** Every language with
   first-class anonymous functions surfaces some "who called me"
   value: zsh exposes `$funcstack[1]`, bash gives `FUNCNAME[0]`
   and `BASH_SOURCE[0]`, Python's `inspect.stack()` and the
   `if __name__ == "__main__"` check, Lua's `debug.getinfo`,
   JS's `Function.caller` and `new Error().stack`. All of them
   see the wrapper as the closest frame and the real caller as
   the next frame up.
2. **Option scoping wants to be the outermost layer.** The whole
   point of the wrap is to scope a runtime option (zsh ksharrays
   off, bash errexit on, Python locale forced) across every
   inner statement. If a single statement leaks outside the
   wrap, the option doesn't apply to it. So the impulse is to
   put everything inside.
3. **Identity-check dispatches want to be the outermost layer.**
   Autoload mechanisms, "run as main" guards, source-vs-execute
   detection — these all rely on seeing the real caller context.
   They are conditional dispatches that decide whether to run
   the entry point or do nothing. If they run inside the wrap,
   they read the wrap's identity and the dispatch goes the wrong
   way every time.

The two goals collide. They cannot both be outermost. The
resolution is that one of them is allowed to live inside and the
other has to live outside. Option scoping moves inside, because
the option only matters for the inner statements. Identity-check
dispatch stays outside, because it has to see the real caller
context.

## The discriminator

Three questions narrow it.

- **Does anything in the wrap ask "who called me"?** Grep for
  `$funcstack`, `$0`, `FUNCNAME`, `BASH_SOURCE`, `__name__`,
  `caller`, `inspect.stack`, `debug.getinfo`. If yes, it's a
  candidate site.
- **Is that identity check used to dispatch?** A check that only
  logs or annotates is fine inside the wrap; a check that gates
  a function call or chooses between two code paths is the
  failure mode.
- **Does the wrap shadow the value the check reads?** zsh's
  `$funcstack[1]` becomes the IIFE name; bash's `FUNCNAME[0]`
  becomes the wrapper function name; Python's `__name__` inside
  a function is always the module name, not "__main__".

If all three are true, the wrap is the caller and the dispatch
will see the wrong value. The fix is to pull the dispatch
outside the wrap, leaving the option scope intact for the
function definitions and source-time guards inside.

## Real applications

### clap-rs/clap#6373 (2026-05-11)

clap_complete's zsh template wraps the generated script in an
anonymous IIFE to scope `emulate -L zsh -o no_ksharrays` across
all the source-time `(( $+functions[..._commands] ))` arithmetic
checks that otherwise fail under `setopt ksharrays`. The natural
first move: put the whole script inside the wrap, including the
final dispatch:

```zsh
#compdef name

() {
    emulate -L zsh -o no_ksharrays

    _name() { ... completion body ... }

    # source-time guards
    (( $+functions[_name_commands] )) || _name_commands() { ... }

    if [ "$funcstack[1]" = "_name" ]; then
        _name "$@"
    else
        compdef _name name
    fi
}
```

The interactive test failed with an empty completion menu. The
dispatch fell into the `compdef _name name` branch every time
because `$funcstack[1]` inside the IIFE was the anonymous
function's name, not `_name`. When the shell autoloaded the
file in completion context (which sets `$funcstack[1]` to
`_name`), the IIFE shadowed that. The `if` saw the anonymous
frame and skipped the entry call.

The two-layer fix: option scope inside, dispatch outside.

```zsh
#compdef name

() {
    emulate -L zsh -o no_ksharrays

    _name() {
        emulate -L zsh -o no_ksharrays   # for completion-time
        ... completion body ...
    }

    (( $+functions[_name_commands] )) || _name_commands() { ... }
}

if [ "$funcstack[1]" = "_name" ]; then
    _name "$@"
else
    compdef _name name
fi
```

The IIFE wraps function definitions and source-time arithmetic
guards. The dispatch lives at real top level so autoload context
is preserved. The entry function gets its own
`emulate -L` because `LOCAL_OPTIONS` propagates the flip to every
subroutine called from the entry, covering the completion call
tree under a caller's ksharrays.

## What this doesn't replace

- **Reading the option-propagation rules of the language.** zsh's
  `LOCAL_OPTIONS` (set by `emulate -L`) propagates to subroutines;
  bash's `set -o`/`shopt` do not, by default. Python's
  context-managed globals don't propagate at all without explicit
  copying. The pattern is general; the specific propagation
  rule matters when deciding where the per-function re-scope has
  to go.
- **Reading the autoload mechanism.** zsh's
  `compdef`/`autoload -U` is one shape; bash's
  `complete -F`/`compgen` is different; Python's `if __name__
  == "__main__"` is a different beast entirely. The card is
  about the wrap-shadowing pattern; the dispatch logic itself
  has to match the host autoload contract.
- **Why the option scope is needed at all.** Sometimes the
  better answer is to fix the underlying caller-environment
  assumption rather than wrap. clap_complete's zsh template
  could in principle be rewritten to use only ksharrays-safe
  idioms (parentheses around `(( ... ))`, explicit `[@]`
  subscripts, no arithmetic existence checks). The wrap is a
  pragmatic patch over a small set of idioms.

## When not to use it

- **The wrap has no identity check inside.** If the wrap is
  purely about option scoping and nothing inside introspects the
  caller, there's no problem; the wrap is transparent in
  every way that matters.
- **The identity check is for logging.** Reading
  `inspect.stack()` to print "called from foo" is fine inside a
  wrap; the value is just diagnostic. Dispatch-based reads are
  the failure mode.
- **The host language has no opaque-frame wrap option.** Some
  languages let you scope a runtime option without creating a
  new call frame (Common Lisp's `let` for special variables,
  Tcl's `uplevel`). In those, the dispatch can stay anywhere
  because there's no wrap to shadow it.

## Related

- [Read the other shells](read-the-other-shells.md) is the
  scout-side discipline: before patching a single shell
  template, read the parallel templates for the same project
  (bash, fish, elvish, powershell). The IIFE/dispatch shape
  applies only to autoloaded shells (zsh, ksh); bash completion
  is sourced unconditionally and doesn't need the wrap at all.
- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the same caution against assuming the host substrate's
  semantics from memory. zsh autoload conventions and
  `LOCAL_OPTIONS` propagation have stayed stable, but
  shell-completion infrastructure does change between
  releases; check the current `compinit` contract before
  quoting line numbers in a public PR.
- The pr-etiquette skill governs how the two-layer fix gets
  communicated. The PR body explains why the dispatch is
  outside and why the entry function gets its own `emulate
  -L`; reviewers shouldn't have to re-derive the wrap-shadowing
  reasoning from the diff alone.

## Revisit

Add a second real application when the next wrap-shadowing bug
fires. Specifically watch for the Python `if __name__ ==
"__main__"` case (wrap a module's body in a function for testing
isolation, dispatch breaks because `__name__` inside any function
is the module name not `"__main__"`) and for the bash
`BASH_SOURCE[0] == $0` source-vs-execute check inside a
function. If a non-shell language produces the same dispatch
collision through a different identity primitive, split the
discriminator section into per-language subsections.
