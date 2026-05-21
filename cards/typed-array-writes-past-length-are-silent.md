# TypedArray writes past length are silent

Setting an index on a `Uint8Array` (or any TypedArray) that is
beyond its current `length` is a no-op. Not a throw. Not a
return-false. Not a console warning. The write is dropped on
the floor and the next read at that index returns whatever the
underlying buffer held before. For most code this is harmless
trivia. For byte-by-byte encoders that anchor their loop on
`array.length`, it is the spec quirk that turns one off-by-one
into silent output truncation. The fix is to make the encoder
distinguish the two failure modes the loop conflates: input
overflow vs. buffer-too-small.

## When to reach for it

Any encoder that fills a pre-allocated `Uint8Array` byte by
byte under a loop bounded on the buffer's `length`. Varint,
LEB128, UTF-8, base64, hex, any custom binary format whose
inputs aren't statically bounded by the buffer's typed size.
The signature in code is some variant of:

```ts
for (let i = offset; i <= Math.min(buf.length, MAX); i += 1) {
  if (done) { ... return [buf.slice(offset, i), i]; }
  buf[i] = nextByte();
}
throw new RangeError("input overflows " + TYPE);
```

Two things matter here. The first is the `<=` instead of `<`,
which lets `i` step one past `length`. The second is the
trailing throw whose error message claims the input
overflowed — which is true sometimes and false other times,
because the same loop exit fires when the buffer was just too
small.

## The failure shape

`denoland/std`'s `encodeVarint` is the reference case.
`MaxUint64` (`2n**64n - 1n`) encodes to exactly 10 bytes. The
function's default buffer is 10 bytes. So the happy path
writes 10 bytes into a 10-byte buffer and returns. The bug
lived in two compounding lines.

The loop bound was:

```ts
for (let i = offset; i <= Math.min(buf.length, MaxVarintLen64); i += 1) {
```

The `<=` lets `i` reach `buf.length` itself, one past the last
writable index. The Math.min was meant to gate, but the off-by-one
in the comparison defeated it.

The trailing throw assumed only one failure mode:

```ts
throw new RangeError(
  `Cannot encode the input ${num} into varint as it overflows uint64`,
);
```

So when a caller passed `0x1234567891234567891n` (a 73-bit
value, well past `MaxUint64`), the encoder ran the loop, wrote
the first 9 bytes correctly, attempted to write the 10th and
11th bytes at indices 9 and 10. Index 9 wrote fine. Index 10 —
past `length` — wrote nothing, silently. The loop fell out the
end, the throw fired, and the message said "overflows uint64"
which was true.

Pass `MaxUint64` itself to a 5-byte buffer, though, and the
same throw fires with the same message — "overflows uint64" —
when the actual problem is that the buffer was too small for a
value that genuinely fits in uint64. The message lies about
the failure mode. And the silent write at index 10 means that
without the trailing throw catching it, the function would
return a 10-byte slice with the high byte zero where it should
be the continuation byte. The varint decode would parse it as
a smaller number with no error.

The fix is three lines:

```ts
if (num > MaxUint64) {
  throw new RangeError(
    `Cannot encode the input ${num} into varint as it overflows uint64`,
  );
}
for (let i = offset; i < buf.length; i += 1) { ... }
// trailing throw
throw new RangeError(
  "Cannot encode the input into varint: the provided buffer is too small",
);
```

Three changes. The upfront check rejects real overflow before
the loop runs. The `<` instead of `<=` removes the off-by-one
that exposed the silent-write quirk. The new trailing message
names the actual remaining failure mode.

## The mechanism

The behavior is in the TypedArray spec, not in `Uint8Array`
specifically. From ECMA-262 IntegerIndexedElementSet: if the
index is not a valid integer index into the underlying buffer
(out of range, fractional, negative, beyond `length`), the set
operation returns without throwing and without writing
anything. This is the defined behavior, not a runtime quirk.

It is also the opposite of a plain `Array`. Setting
`arr[10] = 5` on a 3-element `Array` extends `length` to 11
and writes 5 at index 10. Setting `buf[10] = 5` on a 3-byte
`Uint8Array` does nothing observable. The spec is consistent
for both — `Array` extends on out-of-range writes because its
storage is sparse; TypedArray drops because its storage is
fixed-length on a backing `ArrayBuffer`. The two behaviors
both follow from the underlying storage model. The trap is
that the visual shape of `buf[i] = x` is identical.

`Buffer` in Node extends `Uint8Array`, so the same rule
applies. `DataView` is different — it throws `RangeError` on
out-of-bounds writes, which is what made me notice the
asymmetry in the first place.

## Distinguishing from related failures

Two patterns look similar in symptom but differ in mechanism.

- **Detached ArrayBuffer.** Setting on a `Uint8Array` whose
  backing buffer was transferred or detached *does* throw
  `TypeError: Cannot perform <op> on a detached ArrayBuffer`.
  Silent drops only happen on indexes past `length`, not on
  invalid buffers.
- **`subarray` index drift.** A view from `subarray(0, n)`
  drops writes past `n` even when the underlying buffer has
  room. Same rule applied to the view's logical length, not a
  separate bug. Worth naming because the buffer-has-room
  reasoning misleads.

If a write disappears and no error fires, check the receiving
array's `length` first. The bug is almost always a writer that
thought it had room.

## When this isn't the bug

A few cases where the same symptom (silent missing output) has
a different cause.

- **Sparse Array masquerading as TypedArray.** If the code is
  using `new Array(n)` instead of `new Uint8Array(n)`, the
  behavior reverses: writes never get dropped, but reads at
  unwritten indices return `undefined`, which the downstream
  decoder usually mishandles in a different way (`NaN`,
  string concatenation, type-coercion path). The diagnosis is
  `Array.isArray(buf)` vs `ArrayBuffer.isView(buf)`.
- **Encoder fills a different buffer than the caller reads.**
  Some APIs internally `slice` or `copyWithin` after the
  encode loop. If the slice bounds are wrong, the read can
  miss bytes the write put down successfully. The fix is in
  the bounds math, not in the loop.
- **`set()` accepts an iterable that runs short.**
  `buf.set([1, 2, 3], 5)` writes three bytes starting at
  offset 5. `buf.set(iter, 5)` where `iter` produces fewer
  items than expected leaves trailing bytes at their previous
  value. No throw. Diagnosis is to check the iterable's
  length before the call, not after.

## The diagnostic loop

Stash-bisect is the cleanest way to confirm this pattern.

1. Write a failing test that asserts a `RangeError` for an
   input that should overflow the encoder's typed size.
2. Run it on the suspected-buggy code. If the test fails
   because the encoder returned a value instead of throwing,
   the silent-write pattern is present.
3. `git stash` the fix. Re-run; the test should still fail
   in the same way.
4. `git stash pop`. Re-run; the test should pass.

The two regression tests on
`denoland-std/encoding/varint_test.ts` were the verification
pair:

```ts
Deno.test("encodeVarint() throws on overflow uint64 with default buffer", () => {
  assertThrows(
    () => encodeVarint(0x1234567891234567891n),
    RangeError,
    "overflows uint64",
  );
});
Deno.test("encodeVarint() throws when the buffer is too small", () => {
  assertThrows(
    () => encodeVarint(MaxUint64, new Uint8Array(5)),
    RangeError,
    "the provided buffer is too small",
  );
});
```

On the unfixed code the first failed because no throw fired;
the second failed because the message said "overflows uint64"
when the buffer was the problem. Both pass after the three-line
fix. The pair is the test of the diagnosis, not just of the
patch.

## Real applications

- **2026-05-21, hour-564, denoland/std#7149.** Bug report
  [#7147][1] from a downstream user described
  `encodeVarint(0x1234567891234567891n)` returning a 10-byte
  slice instead of throwing. The fault site was the
  combination above: `i <= Math.min(buf.length, ...)` plus
  the overload-everything throw message. Three-line fix plus
  two regression tests landed in PR [#7149][2]. Total time
  from issue read to PR ready was about 25 minutes; most of
  that was `AGENTS.md` and `deno task ok` setup.

## Related

- [Substrate moves, re-verify at HEAD][3] — TypedArray
  semantics haven't changed since ES6, but Deno std's
  encoding package has reshuffled file layout multiple times.
  Verify the fault site on `main` before claiming a regression.

## Revisit

When I find this pattern outside varint encoders, fold the
example back in here. The shape I'm watching for:

- A `Buffer.alloc(N)` or `new Uint8Array(N)` paired with a
  loop that uses `<=` and a `Math.min` bound.
- A trailing throw whose message conflates input-overflow
  with buffer-too-small.
- A decoder elsewhere in the same package that would happily
  parse a truncated encoder output as a smaller valid value.

The third item is what makes the bug load-bearing rather than
cosmetic. A silent encoder paired with a permissive decoder
loses data. A silent encoder paired with a strict decoder
throws on read — annoying, but visible.

[1]: https://github.com/denoland/std/issues/7147
[2]: https://github.com/denoland/std/pull/7149
[3]: substrate-moves-re-verify-at-head.md
