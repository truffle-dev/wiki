# Drop contained spans after coordinate dedup

When a pattern-matching tool runs multiple patterns over the
same text and reports the hits, exact-coordinate dedup is the
first pass. It catches the same pattern firing twice on the
same span. It does not catch a shorter pattern wholly covered
by a longer same-category pattern. Both survive coordinate
dedup because their start indexes differ. The user sees a
duplicate finding.

## When to reach for it

You wrote a regex matcher that walks a string against a list
of patterns and emits a `{category, index, length, text}`
record for every hit. The output list is concatenated across
patterns and sorted by index. You added an exact-coordinate
dedup keyed on `category:index:length`. The first sample input
looks clean. The second sample says the same thing twice, with
different start positions: a long phrase and one of its
constituents both fire. A reader looking at the panel sees the
shorter match nested inside the longer one and reports the
duplicate as a bug.

This shape shows up in voice scrubs, lint rules with overlapping
phrase lists, autocompleters, tokenizers that report alternatives,
and any tool whose pattern list grew by accretion.

## The shape

Three things are true at the same time.

1. **Coordinate dedup catches the same pattern, not the same
   span.** A single pattern that matches the same span twice
   collapses to one record. A long pattern and a short pattern
   that both match an overlapping span produce two records
   with different `index` or `length` fields. The dedup key
   does not collide.

2. **Contained means the shorter range falls entirely inside
   the longer range.** For two hits A and B in the same
   category, B contains A when `B.start <= A.start` and
   `B.start + B.length >= A.start + A.length`. The contained
   span carries no information the container does not. The
   user reads one finding when both are reported.

3. **Drop-contained is per-category, not global.** A marketing
   verb inside an AI-disclosure phrase is not the same finding
   twice. The two categories represent different rules; both
   should fire. The drop pass filters only same-category
   contained hits.

## The pass

After coordinate dedup, walk the hit list. For each hit `h`,
look for another hit `other` such that:

- `other.category === h.category`
- `other.length > h.length` (strictly longer)
- `other.index <= h.index && other.index + other.length >= h.index + h.length`

If any such `other` exists, drop `h`. Sort the result by index.

```javascript
function dropContained(hits) {
  return hits.filter(function (h) {
    var hEnd = h.index + h.length;
    return !hits.some(function (other) {
      if (other === h) return false;
      if (other.category !== h.category) return false;
      if (other.length <= h.length) return false;
      return other.index <= h.index && (other.index + other.length) >= hEnd;
    });
  });
}
```

The strict-longer check is what protects the pass from removing
hits in a tie. Equal-length hits with the same category and the
same range collapse under coordinate dedup; if they survived
that pass, dropping one would lose information.

## When not to drop

Some tools want every hit. A coverage report ("which patterns
fired on this input") needs the full list. A debugger showing
all matches needs the full list. The drop pass is for the user-
facing flagger where the question is "what should I fix" and
the answer for a shorter span inside a longer same-category
span is "fix the longer one and the shorter one goes away."

The decision belongs to the reporting layer, not the matching
layer. Keep the matcher honest; let the renderer drop.

## The trigger that surfaced it

Voice-check, a single-HTML-file tool that flags em-dashes,
marketing verbs, and AI-disclosure phrases in pasted prose.
The disclosure list contained both `as an ai` and `as an ai
assistant`. A bot-voice sample contained the full phrase. The
panel showed two disclosure findings at the same start index,
one ending at the short cutoff and one at the long. Exact-
coordinate dedup did not catch it because the lengths differ.
A drop-contained pass after dedup collapsed the panel to one
finding. The functional test that exercised four samples
before publication was where the bug surfaced; without that
test, a user would have read the duplicate and reported it.

The same pattern applies to any tool whose list grew by
accretion. Add a long phrase that contains a shorter one and
the duplicate appears at the next sample run, not at the
pattern-list edit.
