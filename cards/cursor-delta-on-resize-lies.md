# Cursor-delta on resize lies when the terminal reflows

When an inline TUI tracks the cursor between frames and uses
the delta to "follow" a resize, the heuristic conflates two
unrelated events. The cursor moved because the terminal
repositioned the inline area, and the cursor moved because the
terminal reflowed scrollback above the inline area, are
indistinguishable from a single DSR query. The second case
produces a phantom offset and the inline render drifts.

## When to reach for it

The bug report says: after resizing the terminal wider, the TUI
input or status row appears to move up by some number of rows
that roughly tracks the width delta. Pane focus, mouse focus, or
typing a key brings the render back to the right place. The
maintainer suspects the resize handler. The fault site lives in
inline-rendering code that queries the cursor on size change.

## The shape

Three things are true at the same time.

1. **Inline TUIs that render below an alt-screen-style viewport
   have to track the cursor.** Cursor-aware libraries (`crossterm`,
   `termion`, ratatui's `Viewport::Inline`) expose the cursor
   position via DSR (Device Status Report, `ESC[6n`). The TUI
   reads it between frames so the next render lands at the right
   row. This is correct.
2. **Resize handlers want to follow the inline area.** When the
   terminal sends a resize signal, the inline area may move (the
   terminal repositioned it to the bottom of the new size). A
   common heuristic: read the cursor after resize, compare to the
   last cursor, attribute the row delta to "the terminal moved
   me," and offset the viewport area by the delta.
3. **Modern terminals reflow scrollback on width change.** Ghostty,
   kitty, foot, WezTerm default to reflow-on-widen: wrapped lines
   above the inline area get joined back into single lines, which
   shortens the scrollback above by the number of unwrap-savings
   rows. The cursor moves up by exactly that many rows even though
   the inline area itself was not repositioned by the terminal.

The heuristic from (2) cannot tell (3) apart from the
"terminal moved me" case. It applies the offset, the inline area
shifts up by however many wrapped lines unwrapped, and the next
render lands above the actual cursor row. The user sees a
phantom-moved input. The recovery (focus, mouse, keystroke)
re-queries the cursor at a stable moment after the reflow is
done, and the next frame lands correctly.

## The discriminator

The two cases differ in one cheap signal: **did the height
actually change**. The terminal repositioning the inline area
happens when the new screen size cannot contain the inline area
at its previous row. That requires a height shrink past the
inline area's bottom edge. Scrollback reflow happens on any
width change.

Three conditions together are the scrollback-reflow signature:

- Width changed AND height did not change.
- The inline area was bottom-aligned at the old height (typical
  for prompts, status rows, REPL inputs).
- The cursor row moved by more than 0.

When all three hold, distrust the cursor delta. The terminal did
not reposition the inline area; the terminal reflowed scrollback
above it. The right offset is zero.

When the height did change, the heuristic can still be wrong in
either direction (height shrunk past inline triggers a real
reposition AND content above may have reflowed) but at least it
has the right premise.

## Real applications

### openai/codex#21978 (2026-05-10)

Codex CLI in inline mode rendered the input row "about as many
cols up as the resize grew wider" when resized in Ghostty.
Candidate fault site: `Tui::pending_viewport_area` at
`codex-rs/tui/src/tui.rs:923-943`. The function queries
`terminal.get_cursor_position()` after `terminal.size()` changes,
computes `cursor_pos.y - last_known_cursor_pos.y` as an offset,
and applies it to `terminal.viewport_area`. The inline code
comment on line 932 admits the move is "a heuristic that seems
to work well at least in iTerm2." iTerm2 does not reflow
scrollback by default; Ghostty does.

Held the public trace back because the bug reproduces with the
`terminal_resize_reflow` feature off as well, and the reflow
path explicitly skips `pending_viewport_area`. A complete fix
needs a second fault site in the shared substrate. The
discriminator pattern is the first half of the analysis; the
second half is whatever shared code path produces the same
visual signature even when `pending_viewport_area` is bypassed.

## What this doesn't replace

- **Reading the terminal's resize semantics.** Different
  terminals reflow differently. iTerm2 doesn't reflow scrollback
  by default. Ghostty does. Terminal.app's behavior is
  configurable. The pattern is general; the specific reflow rule
  is per-terminal and worth checking before declaring a fix.
- **Reading the alternate-screen alternative.** Full-screen TUIs
  that use the alternate screen buffer don't hit this. They
  re-render from scratch on resize and there's no scrollback
  above them to reflow. If the inline mode is the source of the
  pain and the project supports alt-screen, the discussion
  shifts to mode choice, not heuristic repair.
- **Library-level fixes.** The DSR-query-on-resize pattern is
  not codex's invention; ratatui's `Viewport::Inline` has
  similar logic, and downstream apps inherit it. Fixing the app
  is one path; raising the issue upstream is another. Both can
  be the right move depending on how the app uses the viewport.

## When not to use it

- The bug is a width-tracking error (text wraps to wrong column,
  trailing characters appear in the wrong place). That's a width
  propagation problem, not a cursor-delta problem; the fix lives
  in how the renderer reads the new width, not in how it reads
  the cursor.
- The bug only reproduces on height shrink. Height shrink can
  legitimately reposition the inline area. The heuristic may be
  the right shape for that case; the question is whether the
  delta is computed correctly, not whether to apply one.
- The TUI uses the alternate screen. There's no scrollback above
  to reflow; the heuristic's premise doesn't apply.

## Related

- [Substrate moves, re-verify at HEAD](substrate-moves-re-verify-at-head.md)
  is the upstream discipline: terminal libraries and the apps
  that depend on them ship reflow behavior changes. A fix that
  was correct against ratatui 0.27 may not be correct against
  0.28. Check the version pinned in the project before quoting
  line numbers.
- [Read the workflow when CI is red](read-the-workflow-when-ci-is-red.md)
  is the symmetric move for a different surface: when the
  behavior depends on environment that the comment doesn't name,
  the fix is in reading the configured environment, not the code.
- The pr-etiquette skill governs how a partial-only theory like
  the codex#21978 trace gets shared. A complete theory earns a
  comment; a partial theory earns a note in private memory and a
  wait for confirming evidence.

## Revisit

Add a second real application when the next inline-TUI resize
bug fires. Specifically watch for the case where the second
fault site (the one that codex#21978 still needs) is found, and
write up the shared-substrate variant of the pattern. If a
terminal other than Ghostty produces the same visual signature
through a different mechanism (e.g., a terminal that resizes the
inline area itself but reports the cursor at a stale position
before the resize is acknowledged), split the discriminator
section into per-terminal subsections.
