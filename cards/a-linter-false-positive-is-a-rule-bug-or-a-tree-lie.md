# A linter false positive is a rule bug or a tree lie

When a linter fires on code that is correct, the fault sits in
one of two layers, and they are fixed in different files. Either
the parse tree labels the code correctly and the rule
over-collects from it (a rule bug), or the parse tree mislabels
the code and the rule faithfully acts on the lie (a tree lie).
The dump of the parse tree tells you which one before you edit
anything. Reaching for the rule first, without that dump, is a
coin flip on whether you are fixing the right layer.

This card is for the moment a linter flags a construct you are
certain is valid, and the instinct is to open the rule's source
and add a special case. Half the time that instinct is right.
The other half, the rule is innocent and the grammar handed it a
node wearing the wrong name.

## When to reach for it

Any linter built on a real parse tree: sqlfluff over a SQL
dialect tree, ESLint over an ESTree AST, clippy over rustc's
HIR, a custom AST-walking check under `tools/`. The signal is
that the rule's decision is a function of node types and node
relationships, not of raw text. If the linter is a regex sweep
with no tree, this card does not apply; there is no second layer
to be wrong.

It also does not apply when the code the linter flagged is
actually wrong. Confirm the construct is valid first. The whole
card assumes a genuine false positive.

## The mechanism

A tree-based linter is two programs stacked. The grammar turns
text into a typed tree. The rule walks that tree and decides.
A false positive can originate in either, and the symptom at the
command line looks identical: correct code, red lint. The
distinguishing evidence is upstream of the rule, in the tree the
grammar produced.

So the first move is to dump the tree and read the label on the
node under suspicion.

1. **The tree is right, the rule over-collects.** The node is
   labeled correctly, but the rule gathers more nodes than it
   should and one of them is a legitimate value the rule was
   never meant to police. The fix is in the rule: tighten the
   set it collects, or add the guard that excludes the
   legitimate case. The grammar is untouched.
2. **The tree lies, the rule is faithful.** The node carries the
   wrong type. The rule does exactly what it should for a node
   of that (wrong) type, and the result is a false positive that
   no amount of rule editing fixes cleanly. The fix is in the
   grammar: relabel the node so the rule sees the truth. Patching
   the rule to special-case the mislabeled node is treating a
   symptom; it leaves the tree lying for the next rule that walks
   it.

The rule that follows: dump the parse tree, find the node the
linter tripped on, and ask "is this node labeled correctly?"
A yes routes the fix to the rule layer. A no routes it to the
grammar layer. Decide the layer before you open a file to edit.

## The two outcomes

When the tree is right: the fix is a scoped change to the rule's
collection or guard, and the regression test is a query that the
rule used to flag and now does not. Prove the guard still catches
the real violation it was written for, or the tightening has
silently widened a hole.

When the tree lies: the fix is a grammar change, and it is
heavier and higher-blast-radius, because every rule that walks
that node now sees a different type. The regression test asserts
the node's new label directly, and the surrounding rules need a
glance to confirm none of them depended on the old, wrong label.

## A concrete case

In sqlfluff, RF02 (references should be qualified) fired on a
table referenced by its alias inside a Spark `BROADCAST` query
hint (issue #6771,
https://github.com/sqlfluff/sqlfluff/issues/6771). The construct
is valid SQL. Dumping the parse tree showed the alias inside the
hint was labeled correctly; the tree told the truth. RF02 was
simply collecting alias references from the hint region that it
should have skipped. That made it a rule bug, fixed by tightening
what RF02 collects, in the rule file, with the grammar left alone
(PR #8018, https://github.com/sqlfluff/sqlfluff/pull/8018).

The sibling case looks the same at the command line and is fixed
in the opposite layer. RF03 false-positived on `JSON_TABLE`
statements (issue #6945,
https://github.com/sqlfluff/sqlfluff/issues/6945). There the tree
was lying: the column definitions inside the `JSON_TABLE` clause
were being labeled as `column_reference` nodes, so RF03 dutifully
treated definitions as references and demanded they be qualified.
No tightening of RF03 fixes that honestly; the column definitions
are not references and should never have carried that label. The
fix belongs in the grammar, where the `JSON_TABLE` columns get
their own node type and stop impersonating references.

Two red lints, identical shape, same family of rules. The parse
tree dump is the one cheap step that tells you the first is a
rule bug and the second is a tree lie, before a single line of
either fix is written.

## See also

- `read-the-rule-not-its-error-message.md` — once the parse tree
  has routed the fix to the rule layer, the rule's source is the
  contract; read it rather than copying a sibling.
- `prove-the-guard-goes-red.md` — whichever layer the fix lands
  in, the regression test is only trustworthy after you have
  watched it catch the bug it was written for.
