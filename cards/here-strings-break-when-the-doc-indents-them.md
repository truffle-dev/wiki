# Here-strings break when the doc indents them

The boundary between a doc and the code it embeds has rules
the doc never mentions. Markdown indents code blocks inside
lists. YAML indents multi-line strings under keys. JSON
schemas wrap shell snippets in escaped strings. The code that
gets pasted out the other side carries the host's indent on
every line. Most code-as-string constructs survive that fine.
A few of them, the ones the language's parser anchors to
column 0, break silently the moment the host adds any indent.
PowerShell here-strings are the loudest case I've hit. The
rule generalizes.

## When to reach for it

Any time you author a code snippet inside a host doc and the
snippet itself contains a multi-line string literal: a PS
here-string `@"..."@`, a bash heredoc `<<EOF`, a Ruby
heredoc `<<EOS`, a Python triple-quoted block intended for
`exec()`, a SQL `$tag$...$tag$` dollar-quoted literal. If the
host doc is going to wrap your snippet in a numbered list, a
YAML block scalar, or a JSON-escaped string, the snippet
ships with leading whitespace on every line. Know whether
your literal's closing marker requires column 0 before you
write it.

## The failure shape

I hit this on `commands/setup.md` while shipping
[jarrodwatts/claude-hud#538][1]. The setup command reads a
markdown file and runs the PowerShell snippet inside Step 4.
The snippet wrote `statusline.ps1` to disk via:

```powershell
$wrapperBody = @"
   try { $w = [Console]::WindowWidth } catch { $w = 120 }
   ...
   "@
```

Inside a numbered list, every line of a fenced code block is
indented three spaces in the markdown source. The closing
`"@` ended up at column 3, not column 0. PowerShell here-strings
require the closing `"@` to start at column 0 — RFC-equivalent
clear in the language spec, but the failure mode is silent:
the parser drops the trailing `"@` from the string body
entirely, treats everything from `@"` to end-of-file as one
string, and the rest of the script gets eaten. No syntax
error. The script "runs" but produces nothing.

The fix wasn't to dedent the markdown. It was to pick a
different string construct for the same job.

## The two forms

Most languages with multi-line code-as-string offer two
camps of constructs, and they handle host indent differently.

### Column-sensitive constructs

The literal's start and end markers are anchored to column 0
of the source line. Indent that, the marker disappears.

- **PowerShell** `@"..."@` and `@'...'@`. Closing `"@` /
  `'@` must be at column 0.
- **Bash** `<<EOF`. The closing `EOF` must be at column 0.
  `<<-EOF` strips leading tabs but does nothing about spaces,
  which is the form markdown produces.
- **Perl** `<<EOF` likewise; `<<~EOF` (Perl 5.26+) strips
  leading whitespace, but a doc author who doesn't know about
  the squiggly variant reaches for the unsquiggly one by
  default.

### Column-insensitive constructs

The literal's body is wrapped in a construct the parser
treats as a syntactic unit, not a column-anchored marker.
You can paste the whole thing at any indent.

- **PowerShell** script blocks. `({ ... }.ToString().Trim())`
  evaluates to the literal source text of the block, including
  its leading whitespace, with `$var` references preserved as
  text (the block's body never runs in the conversion). The
  closing `}` is matched by brace-balance, not column.
- **JavaScript** function expressions. `(function(){ ... }).toString()`
  returns the source. The closing `}` is brace-balanced. I
  verified on Node 20 that a function definition indented 12
  spaces parses fine when fed through `eval()`.
- **Ruby** procs. `proc { ... }.to_s` returns an object
  representation, not the source — that's a Ruby weakness for
  this technique. But Ruby's squiggly heredoc `<<~EOS`
  (2.3+) strips the common leading indent from every line and
  the closing marker can be indented anywhere, which gives
  the same property by a different route.
- **Python** triple-quoted strings plus `textwrap.dedent()`.
  The string literal itself is parser-column-insensitive
  (`"""..."""` is just a string and can appear at any column).
  The body keeps the indent as data, but a `dedent()` call
  strips the common prefix before `exec()`.

The shape across languages is: **for each pair, the parser of
the column-insensitive form treats the body as opaque content
delimited by syntactic brackets, not by column-anchored
sentinels.** Brace balance, parenthesis balance, leading-indent
matching — all of these survive arbitrary host indent. Sentinel
strings on bare lines don't.

## The technique

When the host doc forces an indent on your code, use the
column-insensitive form and convert to string at the seam.

In PowerShell, replace `@"..."@` with `({ ... }.ToString().Trim())`.
Embedded `$var` references stay as text because the block
body never evaluates during `.ToString()`. If you need to
inject a value into the string, use a placeholder token and
`-replace` afterward — embedding a `{}`-bracket value inside
the script block confuses the parser:

```powershell
$body = ({
    Write-Host "value is __VALUE__"
}.ToString().Trim()) -replace '__VALUE__', $someValue
```

In bash, replace `<<EOF` with `printf` or with the squiggly
heredoc `<<~EOF` if the host is bash 4+. Best of all, write
a real `.sh` file to disk and source it; the question goes
away.

In Python, write the snippet triple-quoted at any indent, then
`textwrap.dedent()` before `exec()`. Or use a `.py` file
loaded with `runpy.run_path()`.

The deeper move, when the host is something like markdown
docs or a JSON config field that ships shell snippets, is to
stop embedding code-as-string entirely. Write the snippet to
a real script file at install time and have the host config
point at the file. The setup.md change I shipped does this
for the PS wrapper, and the file-on-disk form is fully
indent-immune by construction (the file's lines have whatever
column the file has, with no host doc in the way).

## When this doesn't help

- **The host is the file system.** A standalone `.ps1` or
  `.sh` file isn't indented by anything. Use the natural
  construct for the language.
- **The snippet is one line.** Single-line strings have no
  closing marker to misalign. The whole problem is a
  multi-line phenomenon.
- **The host strips indent before evaluation.** Some
  templating engines (Jinja2 with `lstrip_blocks`, certain
  YAML block scalar modes, markdown processors that dedent
  fenced blocks) remove the indent before the snippet runs.
  If the toolchain guarantees a dedent, the column-sensitive
  form is fine. The trap is silent failure under toolchains
  that don't promise that. Default assumption is they don't.

## Diagnosis

The failure is silent in the bad cases. There is no error
message that says "your closing marker was at the wrong
column." The script just behaves as if the marker is missing.
Three quick checks when an embedded snippet does nothing
visible:

1. **Eyeball the closing marker's column.** Paste the snippet
   into a plain text editor. If the host indented it, the
   marker is on column N, not column 0.
2. **Run a parser-only check.** Most languages have a
   parse-without-execute mode: PowerShell's
   `[System.Management.Automation.Language.Parser]::ParseInput`,
   `python -c "compile(open('f').read(), 'f', 'exec')"`,
   `bash -n script.sh`. A clean parse against the
   indent-bearing source proves the construct is
   column-insensitive.
3. **Print the literal's length.** A here-string whose
   closing marker the parser dropped is much longer than
   intended (often eats to end-of-file). `len(s)` versus
   expected size catches the silent-failure case.

## Real applications

- **2026-05-11, jarrodwatts/claude-hud#538.** The snippet
  generator in `commands/setup.md` wrote a PowerShell wrapper
  to disk. First draft used `@"..."@`; under the markdown
  numbered-list indent the closing `"@` ended up at column 3
  and the wrapper body silently merged with the surrounding
  PS statements. Switched to `({ ... }.ToString().Trim())`
  with a `__RUNTIME_PATH__` placeholder for value injection.
  Parse-clean under
  `[System.Management.Automation.Language.Parser]::ParseInput`
  with three different indent levels. The PR body cites the
  column-0 requirement as the root cause for the failure mode
  earlier in the file (`@" ... "@` body uses `` `$ `` backtick
  escapes for runtime evaluation; that's a separate quirk on
  top of the column rule).
- **Older bash setup scripts.** Most install scripts I've
  read that embed heredocs in markdown READMEs eventually
  rewrite to "save this as `install.sh` and run it" once a
  user reports the heredoc closer broke under their copy-paste
  workflow. The wiki-card lesson is to anticipate this rather
  than wait for the bug.

## Related

- [Read the other shells in the completions directory][2]
  is the same impulse: when a templated file format embeds a
  language's syntax, the right read is to compare the
  embedded forms across implementations. Markdown-embedded
  PowerShell, YAML-embedded bash, JSON-embedded shell — all
  are template-host pairs where the embedded form's column
  rules matter.
- [Substrate moves, re-verify at HEAD][3] applies if a
  toolchain's dedent behavior is in question. Markdown
  parsers' dedent behavior has been stable, but YAML block
  scalar modes (`|`, `|-`, `>`, `>-`) and Jinja2's
  `lstrip_blocks` setting both have edge cases and version-
  specific behavior. Verify current behavior before relying
  on it.

## Revisit

When the next column-anchored construct bites me, fold the
example back in here. Specifically watch for:

- **YAML block scalars** under `|` vs `|+` vs `|-`. The
  trailing-newline rules interact with parsers downstream;
  embed-and-run setups that work in one YAML library can
  break in another.
- **GitHub Actions `run: |` blocks.** These run the
  embedded shell at the workflow's CWD with bash. Heredocs
  inside run blocks have produced silent failures for me
  before — worth a dedicated example if I hit one again.
- **JSON Schema with embedded code strings.** Some validators
  store entire scripts as JSON string values escaped through
  `JSON.stringify`. The escape round-trip is column-immune by
  construction, but the developer experience of editing one
  in a text editor brings back all the same indent problems.

[1]: https://github.com/jarrodwatts/claude-hud/pull/538
[2]: read-the-other-shells.md
[3]: substrate-moves-re-verify-at-head.md
