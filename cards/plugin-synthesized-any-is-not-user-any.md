# Plugin-synthesized Any is not user Any

When a mypy plugin synthesizes an `Any` to fill a hole the plugin
can't statically determine, the right `TypeOfAny` variant is
`from_omitted_generics`, not `explicit`. The user didn't write
that `Any`. Tagging it as if they did makes `--disallow-any-explicit`
fire on every model that exercises the plugin's fallback path.

This is a one-line distinction inside the mypy plugin API, and it
shows up the moment a project ships a plugin that turns a
dynamic-but-not-statically-knowable signature into a method
declaration. Pydantic shipped the wrong tag for ~two years.

## When to reach for it

I'm writing or maintaining a mypy plugin. I'm calling
`add_method` (or building `Argument` / `AnyType` directly) and one
of the parameters is `Any` because the plugin can't compute the
real type at static-check time. The `**kwargs` fallback that lets
a class accept arbitrary keyword arguments is the canonical
example, but the same issue applies anywhere the plugin synthesizes
a fallback type for a slot it couldn't determine.

## The two variants

`TypeOfAny` is an enum on `mypy.types.AnyType` describing how
the `Any` came into existence. The two variants that matter for
plugin-synthesized fallbacks:

- **`TypeOfAny.explicit`** represents `Any` the user wrote in
  source. A `: Any` annotation, an explicit cast, an
  `__init__(self, x: Any)`. The user chose `Any` and accepted the
  type-system escape hatch. `--disallow-any-explicit` is the
  mypy flag that says "don't let users write `Any`"; it fires on
  this variant.
- **`TypeOfAny.from_omitted_generics`** represents `Any` mypy
  itself fills in for an omitted type parameter. The bare `list`
  in `def f(x: list)` becomes `list[Any]` with this variant.
  Mypy treats it as implicit, since the user didn't choose `Any`,
  they just left the parameter off. `--disallow-any-explicit`
  does not fire.

Plugin-synthesized fallback `Any` is conceptually closer to the
second case: the plugin is filling a hole, not transcribing a
user choice. The right tag is `from_omitted_generics`.

## The pydantic case

pydantic#13161, reported 2026-04-12 by julianochoi.

Pydantic's mypy plugin reads each model class and synthesizes a
typed `__init__` so static checkers see real parameters. When
`init_forbid_extra` is enabled (forbids unknown keyword args at
runtime), the plugin normally drops the catch-all `**kwargs`
parameter. But if the model has a *dynamic* validation alias
(`AliasChoices`, `AliasPath`, or `alias_generator`), the plugin
can't statically determine the alias keys, so it has to keep
`**kwargs: Any` to accept whichever keys the alias resolves to
at runtime.

That fallback `**kwargs: Any` was synthesized with
`TypeOfAny.explicit` at `pydantic/mypy.py:937` and `:968`. Any
project running with both `disallow_any_explicit = true` and
`init_forbid_extra = true` saw a misc error on every dynamic-alias
model:

```
error: Explicit "Any" is not allowed [misc]
```

The user never wrote `Any`. They wrote
`Field(validation_alias=AliasChoices(...))`. The plugin produced
the `Any` to make the synthesized signature accept the dynamic
keys. Tagging it `explicit` made mypy report a violation against
code the user didn't write.

## The fix

Two-character change at each fault site, plus an existing
in-file precedent:

```python
# Before
args.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))

# After
args.append(Argument(var, AnyType(TypeOfAny.from_omitted_generics), None, ARG_STAR2))
```

The same plugin already handled this distinction correctly on
a different path: `pydantic/mypy.py:929-931` used
`ChangeExplicitTypeOfAny(TypeOfAny.from_omitted_generics)` to
re-tag the `_cli_settings_source` / `_build_sources` parameters,
which were also plugin-synthesized fallbacks. The two
`**kwargs` sites had the same shape but missed the conversion.

The PR is pydantic#13163. The regression test seeds
`AliasChoices`, `AliasPath`, and `alias_generator` under
`mypy-plugin-strict-no-any.ini`, asserts the dynamic-alias
warnings fire (because the config enables them), and asserts
no `--disallow-any-explicit` error.

## The general rule

In a mypy plugin, when you reach for `AnyType(...)`:

1. Ask: did the user write this `Any`?
2. If yes (you're transcribing a user-written annotation),
   `TypeOfAny.explicit` is correct.
3. If no (you're filling a hole), `TypeOfAny.from_omitted_generics`
   is correct.

The `**kwargs` fallback is "filling a hole". So is any synthesized
parameter type that compensates for dynamic configuration the
plugin can't read at static-check time. So is the type of a
generated property whose underlying expression isn't statically
analyzable.

## What this doesn't replace

- **`from_unimported`, `from_error`, `unannotated` and the other
  variants.** `TypeOfAny` has more cases than the two compared
  here. Plugin code that imports types or surfaces stub-resolution
  failures has its own correct variant. The card is specifically
  about the synthesized-fallback case.
- **Tests on the `--disallow-any-explicit` configuration.**
  Even with the right variant, a plugin that fans out across many
  paths needs an explicit regression test under a
  `disallow_any_explicit = true` config so the next refactor
  doesn't re-introduce the wrong tag.
- **Audit of existing `TypeOfAny.explicit` usages.** When the wrong
  tag has shipped for years, fixing it on one path is the start.
  Grep the rest of the plugin for `TypeOfAny.explicit` and
  ask the same question for each site.

## When not to use it

When the user actually wrote `Any` and you're transcribing it.
A plugin that reads `__init__(self, x: Any)` from source and
copies the annotation onto a synthesized method should preserve
`TypeOfAny.explicit`, because that's what the user wrote. The
rule is about plugin-introduced `Any`, not user-written `Any`
the plugin happens to encounter.

## Related

- [Search before you trace](search-before-you-trace.md) is the
  upstream discipline. The existing-PR check on
  `pydantic#13161` returned zero open PRs; without that check,
  forty-five minutes of fix work might have duplicated a peer's
  earlier shipping.
- The pydantic in-file precedent at `mypy.py:929-931`
  (`ChangeExplicitTypeOfAny(TypeOfAny.from_omitted_generics)`)
  is the same fix shape on a different code path. When a fix
  has a precedent in the same file, the fix-shape is settled
  and the work is finding the missed sites.
- [Spread order vs the cleanup pass](spread-order-vs-cleanup-pass.md)
  is the value-level cousin: an explicit string gets shadowed
  by a synthesized change marker through `{ name, ...diff }`
  spread order, where this card is about an explicit annotation
  getting shadowed by a synthesized one through the plugin
  builder API. Same shape, different surface.

## Revisit

Add a second real application the next time the variant
mismatch shows up in a different mypy plugin. If a third
variant becomes the right answer in a synthesized-fallback case
(`TypeOfAny.special_form`, for instance, for plugin output that
participates in a typing special form), name it here and rewrite
"The general rule" as a three-way decision instead of a
two-way one.
