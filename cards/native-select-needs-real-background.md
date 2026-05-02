# Native select needs a real background

`color-scheme: dark` is not enough to make a native `<select>`
popover legible in dark mode if the element itself is rendered with
`background: transparent`. The OS popover takes its theme from the
element's *computed* background color, not from `color-scheme`. A
transparent select on a dark page paints a white popover with white
text.

The fix is one declaration: give the select an opaque background
that matches the surface it sits on.

## When to reach for it

A page in a dark theme where a native `<select>` works correctly in
light mode but, when expanded in dark mode, shows white-on-white or
black-on-black option text. The bug is reproducible on Chromium and
Edge. Firefox and Safari may render it correctly, which makes the
defect easy to miss in cross-browser smoke tests.

## The mechanism

Three things conspire.

1. **`color-scheme` only colors UA chrome.** Setting
   `color-scheme: dark` on `:root` or on the element tells the
   browser to use dark scrollbars, dark form-control internals, and
   dark default text color. It does not, by itself, repaint the
   popover when the popover is delegated to the OS.
2. **The popover inherits the element's *computed* background.**
   On Chromium and Edge, when a `<select>` opens, the popover
   adopts the element's background color as its own background. If
   that color is `transparent` or a near-transparent rgba, the
   popover collapses to the OS default, which is light. Option text
   is rendered with the dark text color from `color-scheme`. Result:
   light background, dark-on-light option text in light mode (fine),
   light-on-light text in dark mode (broken).
3. **Tailwind's `bg-transparent` is the easy way to land here.** A
   form-control shared between light and dark themes with
   `bg-transparent` is invisible in both themes when sitting on a
   themed surface, which is the desired effect for the closed
   element. The popover bug only appears when the element is opened.

## The fix

Replace `bg-transparent` with the design-system background token for
the surface the control sits on.

```diff
- "w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
+ "w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2"
```

`var(--background)` resolves to a different value per theme (light,
dark, snow, glass), and the popover follows. No JS, no popover
polyfill, no swap to a custom dropdown.

## Why not a custom dropdown

A native `<select>` carries accessibility, keyboard navigation, and
mobile UX that a custom dropdown has to reimplement. The bug here is
one CSS declaration away from fixed; reaching for a custom component
trades a one-line patch for a 200-line one and loses screen-reader
semantics in the bargain.

The custom dropdown is the right answer when the design needs
anything the native popover can't do (rich content per option,
asynchronous loading, type-ahead beyond the OS default). For a
plain choice list, native plus a real background wins.

## Real application

[HKUDS/DeepTutor#435](https://github.com/HKUDS/DeepTutor/pull/435).
Settings page LLM Provider dropdown rendered as white-on-white in
dark mode on Chromium. Two `<select>` elements in the file: one used
the shared `inputClass`, one used the page-local `selectClass`. The
LLM Provider used `selectClass`. One-line swap from `bg-transparent`
to `bg-[var(--background)]` on `selectClass`. The other select
(embedding-dimension picker, on `inputClass`) was left alone because
`inputClass` is shared with text inputs, where a transparent
background is correct.

The fix worked across all four themes the project ships
(`:root`, `.dark`, `theme-snow`, `theme-glass`) because each theme
defines `--background` to its surface color. Theme-aware out of
the box.

## What this doesn't replace

- **Cross-browser smoke testing.** The bug is Chromium and Edge
  only. Firefox and Safari render correctly even with
  `bg-transparent`. A Firefox-only manual QA pass will pass right
  through this defect.
- **Custom dropdown when it's earned.** When the design needs more
  than the native popover provides, the custom component is the
  right call. The fix here is for the case where native is the
  intended UX and the only blocker is dark-mode contrast.
- **Design-token discipline elsewhere.** A page that uses raw hex
  values instead of theme tokens will have the same bug per theme,
  one fix per theme. The token is the multiplier.

## When not to use it

When the design intentionally shows the popover floating over a
gradient or image and the popover's solid background would clash. In
that case, the fix is bespoke per design and the right move is a
custom dropdown with the desired backdrop.

When the page is light-only or dark-only and the bug isn't real.
`bg-transparent` is fine if there's only one theme.

## Related

- The DeepTutor#435 fix lives in
  `web/app/(utility)/settings/page.tsx` under the `selectClass`
  declaration. The neighboring `inputClass` is the negative example:
  it correctly stays transparent because text inputs don't have a
  popover.
- The general lesson is broader than `<select>`. Any UA-rendered
  surface that delegates to the OS (date pickers, color pickers,
  file-input chrome) inherits computed colors, not `color-scheme`
  alone.

## Revisit

Add a second real application the next time this surfaces in a
different framework or on a different UA-rendered control. If a
date picker or file-input chrome shows the same shape, generalize
the title to "Native form chrome needs a real background" and add
the second case under "Real application".
