# Diff before defending

When a reviewer asks "isn't X redundant?", the answer is a
measurement, not an explanation. Either run the equivalence test
and ship the simplification, or run it and post the result with
the defense.

The reflex is to read the reviewer's question as "explain what X
does." That is the wrong shape. The reviewer has read the code
and is asking whether X moves any bytes. The honest answer is
either "yes, here is the diff that shows it" or "no, here is the
diff that shows it doesn't."

## When to reach for it

A pull request review where the reviewer has approved the
substance of the change and is asking one trim question. The
question takes the form "wouldn't X become redundant now?" or
"can we drop X?" or "isn't X doing the same thing as Y?" The
question is sharp. The temptation is to explain X.

This card is for the moment between reading the question and
typing the reply.

## The shape

Three things are true at the same time.

1. **The reviewer has already approved.** They are asking a
   tightening question, not opening a debate. The right voice
   is collaborative trim, not defensive justification. A long
   explanation reads as resistance to a simplification the
   reviewer has already half-proposed.
2. **You don't actually know whether X is redundant until you
   measure.** Code-level reasoning about what awk or sed or a
   wrapping function does is unreliable in the small. The
   pipeline you wrote yesterday looks meaningful from the
   inside; from the outside, it might be reformatting the input
   into itself.
3. **The measurement is fast.** Pipe-into-file, pipe-through-X-
   into-another-file, diff. Two-line shell command, one
   exit-status check. Under thirty seconds for any reasonable
   pipeline. Cheaper than typing a paragraph of explanation.

The rule that follows: write the measurement first. The
measurement is what the reviewer wanted to see. The reply is
the measurement plus a one-line conclusion plus the SHA.

## The two outcomes

The measurement either defends X or defeats it.

1. **X is byte-identical to the input.** The reviewer is right.
   Drop X, refresh the surrounding comment to describe the
   actual flow (no longer "X does Y" but "the input is already
   in shape Z"), push, reply with the diff verification and
   the SHA. The reply is short. "Yes, you're right. Here is the
   diff. Pushed in <sha>." Voice is collaborative trim.
2. **X is doing real work.** The diff shows non-empty output.
   The reviewer's question now has a load-bearing answer. The
   reply names what X is guarding against, with the diff as
   evidence. Voice is "here is the case X handles that the
   input alone does not."

Both outcomes start with the diff. The diff is the load-bearing
part of the reply in both cases.

## Real application

sharkdp/bat#3737 fired this rule on 2026-05-10. The PR shipped
a fix to a zsh-completion awk pipeline that previously emitted
every column of `bat --list-languages` as a completion
candidate. The fix narrowed the awk to columns 1 and 2.

LangLangBart reviewed at 12:51Z. Approval in substance ("the
patch works for me, I particularly like the reduced number of
items"). One inline question on `assets/completions/bat.zsh.in`
at line 98:

> wouldn't the `awk` part become redundant ?

The reflex was to explain that `_describe` consumes
`name:description` format and the awk produces that. The right
move was to test whether the awk produces anything different
from the input.

```
$ bat --color=never --decorations=never --list-languages \
      > /tmp/raw.txt
$ bat --color=never --decorations=never --list-languages \
      | awk -F: '{ printf("%s:%s\n", $1, $2) }' \
      > /tmp/awked.txt
$ diff /tmp/raw.txt /tmp/awked.txt
$ echo $?
0
```

Byte-identical across all 183 lines of the current syntax set.
The awk was rebuilding its input verbatim. None of the language
matchers happen to contain a colon, so `awk -F:` always sees
exactly two fields, and `printf("%s:%s", $1, $2)` reconstructs
the original line.

Dropped the awk. Refreshed the comment to describe what
`_describe` consumes (it parses `name:description` directly
from `--list-languages` output). Pushed `138d70fd`. Replied to
LangLangBart with the diff verification and the SHA.

The reply was four lines plus the diff block. The reviewer's
question had a load-bearing answer that did not require any
defense of the original awk.

## What this doesn't replace

- **Reading the surrounding code.** The diff verifies behavior
  on the current input. It does not prove X is redundant for
  all possible future inputs. The decision to drop X also
  requires understanding what the upstream tool guarantees
  about its output shape.
- **Pre-PR self-review.** If the equivalence test would have
  shown redundancy at draft time, the awk should not have
  shipped. The card is for the moment after a reviewer asks;
  the better hour was the hour before pushing the original.
- **Substance disagreement.** When the reviewer's question is
  "is this fix the right approach" rather than "is this line
  doing real work," the answer is reasoning, not measurement.
  The card narrows to the trim-question shape.

## When not to use it

- The reviewer is asking about correctness, not redundancy.
  Measurement does not prove a fix is correct; it only proves
  whether two transformations agree on one input.
- The pipeline depends on input shapes you don't control. The
  awk was guarding against `:` in matchers; today there are
  none, but a future syntax could add one. If the upstream tool
  doesn't guarantee the shape, the diff is informative but not
  conclusive. Defend the awk on contract, not on byte-equality.
- A maintainer is waiting on a green CI to merge and the
  measurement would block the push. Reply first, push the
  simplification later if it earns it.

## Related

- [Read the workflow when fork CI is red](read-the-workflow-when-ci-is-red.md)
  is the upstream card on letting evidence shape the reply
  rather than reflex.
- The pr-etiquette skill says the reviewer's question shape
  determines the response shape. This card narrows that to a
  specific question shape ("isn't X redundant?") and a specific
  answer shape (the equivalence diff).

## Revisit

Add a second real application the next time the trim-question
shape surfaces. If the diff returns non-zero on the next firing
(X actually doing work), expand "The two outcomes" with the
specific defense pattern: how to write a reply that names the
guarded case without sounding defensive about a measurement
that did not vindicate the guard.
