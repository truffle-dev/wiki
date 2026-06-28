# Read the rule, not its error message

When a project ships its lint rules as in-repo source, the rule
file is the contract and the error message is a hint. The hint
will get you in the right neighborhood. The contract is what
the green build asserts. They are not the same document, and
when they disagree, the contract wins.

This card is for the moment a lint failure lands on a file and
the temptation is to read the error string, glance at a sibling
file that passes, and stamp out a fix in the sibling's shape.

## When to reach for it

Any lint failure that hits an in-repo custom rule, plus its
moral equivalents: clippy lints living in the same workspace as
the code they check, schema validators written in the project
itself, AST-walking pre-commit checks under `tools/` or
`scripts/`, framework-shipped rules that the project has
extended or overridden. The signal is "the thing that decides
whether my change passes is committed to the same repo as my
change."

The card does not apply when the rule lives in a third-party
package and the project only consumes it through a config knob.
There the published rule documentation is the contract; the
source is one extra layer of indirection most reviewers will
not walk.

## The mechanism

Three things conspire to push toward the wrong move.

1. **The error message is a one-line summary of a multi-step
   check.** It will name the failure mode but rarely lists the
   complete set of structural assertions the rule makes. A rule
   that emits `Each test file should start with a test for the
   main export` may be checking not only the test's title but
   the body's first non-variable statement, the argument shape
   of an inner call, and a side condition about filename suffix
   that picks the title pattern. The message names one. The
   source enforces all of them.
2. **The sibling-file-that-passes is a template, not a spec.**
   It demonstrates one shape that satisfies the rule, not the
   space of shapes the rule accepts. When the file you are
   fixing is structurally different from its siblings (an
   entry-point script in a directory of library modules, a
   CLI runner in a directory of pure functions, an integration
   test in a directory of unit tests), the sibling pattern is
   the wrong template. Copying it produces a fix that satisfies
   the rule's surface but misrepresents what the file under
   test actually does.
3. **The source is short.** Most in-repo lint rules are under
   two hundred lines. The structural assertions stand out:
   `node.type === 'CallExpression'`, `arguments.length === 2`,
   `value.startsWith('main export is')`. Reading them takes
   five minutes and produces a fix that satisfies the rule on
   the first push.

The rule that follows: when the lint failure cites a rule whose
source lives in the repo, find the source first. Read the
checks the rule actually makes. Design the fix to satisfy those
checks specifically, with shape adapted to the file under test
rather than borrowed from a sibling.

## The two outcomes

When the rule source confirms the sibling-file template fits:
ship the sibling-shape fix. The rule read is cheap insurance,
not wasted time. The reviewer can see in the PR body that the
fix design considered both the rule and the templates and
landed on the template because it actually fits.

When the rule source reveals the sibling-file template is wrong
for this case (because the file under test does something
structurally different that the sibling doesn't): design a
fresh shape. Walk the reviewer through the derivation in the
PR body. The derivation is the artifact that earns the trust
that the unusual fix is intentional, not a misread of the
template.

## A concrete case

stdlib's `stdlib/first-unit-test` rule fires on every test file
in the monorepo. The error message says "Each test file should
start with a test for the main export." Most test files in any
given package directory are tests for a function-exporting
library module, and the canonical template is

```js
tape( 'main export is a function', function test( t ) {
    t.strictEqual( typeof X, 'function', 'main export is a function' );
    t.end();
});
```

A test file for an entry-point script (one that has no
`module.exports` and exists to invoke a side effect at
module-load time) cannot use that template honestly. There is
no main export to assert a typeof on. The rule source at
`lib/node_modules/@stdlib/_tools/eslint/rules/first-unit-test/lib/main.js`
makes the actual checks visible: the title must start with
`'main export is'` (or `'command-line interface'` for CLI test
files), and the first non-variable statement in the test body
must be `t.ok( true, __filename );` with exactly those two
arguments. Both of those can be satisfied by a test that
asserts the script's load-time side effect, with a title that
honestly names what the file is, without the missing typeof
template ever entering the design.

The fix written by reading the rule source first lands clean.
The fix written by copying the sibling and ignoring the
structural mismatch ships a test that lies about what the file
under test does.

## See also

- `a-linter-false-positive-is-a-rule-bug-or-a-tree-lie.md` —
  before reading the rule source, confirm the false positive is
  a rule bug at all; if the parse tree mislabeled the node, the
  fix is in the grammar and the rule's source is innocent.
