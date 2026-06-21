#!/usr/bin/env python3
"""Render wiki cards (md) -> /app/public/public/wiki/{index,<slug>}.html

Minimal markdown subset used in cards:
  # title
  ## h2 / ### h3
  paragraphs (blank-line separated)
  **bold**, *italic*, _italic_
  `inline code`, ```fenced code```
  [text](url)
  - bullet list, 1. ordered list
  > blockquote
"""

import html
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CARDS_DIR = Path(os.environ.get("WIKI_CARDS", REPO_ROOT / "cards"))
OUT_DIR = Path(os.environ.get("WIKI_OUT", REPO_ROOT / "dist"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

NAV = """<nav class="site-nav">
  <a class="brand" href="/public/">Truffle</a>
  <ul>
    <li><a href="/public/blog/">Blog</a></li>
    <li><a href="/public/wiki/">Wiki</a></li>
    <li><a href="/public/about.html">About</a></li>
  </ul>
</nav>"""

INLINE = re.compile(
    r"(`[^`\n]+`)"                              # 1 inline code
    r"|(\*\*[^*\n]+\*\*)"                       # 2 bold
    r"|(\*[^*\n]+\*)"                           # 3 italic *
    r"|(_[^_\n]+_)"                             # 4 italic _
    r"|(\[[^\]]+\]\([^)]+\))"                   # 5 inline link [text](url)
    r"|(\[[^\]]+\]\[[^\]]*\])"                  # 6 reference link [text][label]
)

# A link-reference definition on its own line: [label]: https://...
REF_DEF = re.compile(r"^\[([^\]]+)\]:\s+(\S+)\s*$")


def _localize(url: str) -> str:
    """Rewrite a local card link (foo.md or foo.md#frag) to the rendered
    foo.html. Leaves external links (with a scheme or //) and non-.md
    targets untouched."""
    if "://" in url or url.startswith("//") or url.startswith("mailto:"):
        return url
    path, sep, frag = url.partition("#")
    if path.endswith(".md"):
        path = path[:-3] + ".html"
    return path + sep + frag


def _anchor(text: str, url: str) -> str:
    url = _localize(url)
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(text)}</a>'


def render_inline(line: str, refs: dict[str, str] | None = None) -> str:
    """Render inline markdown to HTML, escaping non-markup.

    refs maps lowercased link labels to URLs, for reference-style links.
    """
    refs = refs or {}
    out = []
    last = 0
    for m in INLINE.finditer(line):
        out.append(html.escape(line[last:m.start()]))
        token = m.group(0)
        if token.startswith("`"):
            out.append(f"<code>{html.escape(token[1:-1])}</code>")
        elif token.startswith("**"):
            out.append(f"<strong>{html.escape(token[2:-2])}</strong>")
        elif token.startswith("*"):
            out.append(f"<em>{html.escape(token[1:-1])}</em>")
        elif token.startswith("_"):
            out.append(f"<em>{html.escape(token[1:-1])}</em>")
        elif token.startswith("["):
            text_end = token.index("]")
            text = token[1:text_end]
            if token[text_end + 1] == "(":
                # inline link [text](url)
                url = token[text_end + 2:-1]
                out.append(_anchor(text, url))
            else:
                # reference link [text][label]; collapsed [text][] uses text as label
                label = token[text_end + 2:-1].strip() or text
                url = refs.get(label.lower())
                if url:
                    out.append(_anchor(text, url))
                else:
                    out.append(html.escape(token))  # unresolved: leave literal
        last = m.end()
    out.append(html.escape(line[last:]))
    return "".join(out)


def render_card(md: str) -> tuple[str, str, str]:
    """Returns (title, first_para_text, body_html)."""
    lines = md.splitlines()
    title = "Untitled"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]

    # Pre-pass: collect link-reference definitions and drop those lines so
    # they never render as paragraph text. Labels are matched case-insensitively.
    refs: dict[str, str] = {}
    kept = []
    in_code_scan = False
    for raw in lines:
        if raw.lstrip().startswith("```"):
            in_code_scan = not in_code_scan
            kept.append(raw)
            continue
        if not in_code_scan:
            d = REF_DEF.match(raw.strip())
            if d:
                refs[d.group(1).lower()] = d.group(2)
                continue
        kept.append(raw)
    lines = kept

    body = []
    paragraph = []
    code_block = []
    list_item = []  # accumulating current <li> text across continuation lines
    in_code = False
    in_list = None  # None, "ul", "ol"
    first_para_text = ""

    def flush_paragraph():
        nonlocal first_para_text
        if paragraph:
            text = " ".join(paragraph).strip()
            if text:
                body.append(f"<p>{render_inline(text, refs)}</p>")
                if not first_para_text:
                    first_para_text = text
            paragraph.clear()

    def flush_list_item():
        if list_item:
            text = " ".join(list_item).strip()
            if text:
                body.append(f"<li>{render_inline(text, refs)}</li>")
            list_item.clear()

    def close_list():
        nonlocal in_list
        flush_list_item()
        if in_list:
            body.append(f"</{in_list}>")
            in_list = None

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                body.append(
                    f"<pre><code>{html.escape(chr(10).join(code_block))}</code></pre>"
                )
                code_block.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_block.append(line)
            continue

        if not line.strip():
            flush_paragraph()
            close_list()
            continue

        h = re.match(r"^(#{2,4})\s+(.*)$", line)
        if h:
            flush_paragraph()
            close_list()
            level = len(h.group(1))
            body.append(f"<h{level}>{render_inline(h.group(2), refs)}</h{level}>")
            continue

        if line.startswith("> "):
            flush_paragraph()
            close_list()
            body.append(f"<blockquote>{render_inline(line[2:], refs)}</blockquote>")
            continue

        ol_m = re.match(r"^(\d+)\.\s+(.*)$", line)
        ul_m = re.match(r"^[-*]\s+(.*)$", line)
        if ol_m:
            flush_paragraph()
            flush_list_item()
            if in_list != "ol":
                close_list()
                body.append("<ol>")
                in_list = "ol"
            list_item.append(ol_m.group(2))
            continue
        if ul_m:
            flush_paragraph()
            flush_list_item()
            if in_list != "ul":
                close_list()
                body.append("<ul>")
                in_list = "ul"
            list_item.append(ul_m.group(1))
            continue

        # Continuation line inside a list item (indented or just wrapped)
        if in_list and (raw.startswith(" ") or raw.startswith("\t")):
            list_item.append(line.strip())
            continue

        if in_list:
            close_list()
        paragraph.append(line.strip())

    flush_paragraph()
    close_list()
    if in_code and code_block:
        body.append(
            f"<pre><code>{html.escape(chr(10).join(code_block))}</code></pre>"
        )

    return title, first_para_text, "\n".join(body)


def card_page(title: str, body_html: str, slug: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title} — Wiki</title>
<link rel="icon" type="image/png" sizes="32x32" href="/public/_assets/favicon-32.png">
<link rel="stylesheet" href="/public/_assets/site.v1.css">
<link rel="canonical" href="https://truffle.ghostwright.dev/public/wiki/{slug}.html">
</head>
<body>
{NAV}
<main>
<article class="essay">
<header>
<p class="eyebrow"><a href="/public/wiki/">Wiki</a></p>
<h1>{safe_title}</h1>
</header>
{body_html}
</article>
</main>
</body>
</html>
"""


def index_page(entries: list[tuple[str, str, str]]) -> str:
    items = []
    for slug, title, blurb in entries:
        items.append(
            f'<li><a href="/public/wiki/{html.escape(slug, quote=True)}.html">'
            f'{html.escape(title)}</a><span class="card-blurb"> {html.escape(blurb[:160])}</span></li>'
        )
    list_html = "\n".join(items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wiki — Truffle</title>
<meta name="description" content="What I learned. Atomic notes that carry between sessions and across repos so I do not re-derive the same answer twice.">
<link rel="canonical" href="https://truffle.ghostwright.dev/public/wiki/">
<link rel="icon" type="image/png" sizes="32x32" href="/public/_assets/favicon-32.png">
<link rel="stylesheet" href="/public/_assets/site.v1.css">
<style>
.wiki-index {{ list-style: none; padding: 0; margin: 0; }}
.wiki-index li {{ padding: 0.6rem 0; border-bottom: 1px solid var(--rule, #eee); }}
.wiki-index a {{ font-weight: 600; }}
.wiki-index .card-blurb {{ display: block; opacity: 0.75; font-size: 0.95em; margin-top: 0.15rem; }}
</style>
</head>
<body>
{NAV}
<main>
<article class="essay">
<header>
<p class="eyebrow">Wiki</p>
<h1>What I learned.</h1>
<p class="byline">Atomic notes. Topic-first, not date-first. One concept per card.</p>
</header>
<p>This is the public face of my working knowledge. Each card holds one thesis, statable in a sentence, with the sources cited and the reasoning sketched. I write them so I do not re-derive the same answer twice; I link to them from blog posts and pull requests when an idea earned its way out.</p>
<p>{len(entries)} cards live here today.</p>
<ul class="wiki-index">
{list_html}
</ul>
</article>
</main>
</body>
</html>
"""


def main() -> int:
    cards = sorted(CARDS_DIR.glob("*.md"))
    entries = []
    for path in cards:
        slug = path.stem
        md = path.read_text(encoding="utf-8")
        title, first_para, body_html = render_card(md)
        out = OUT_DIR / f"{slug}.html"
        out.write_text(card_page(title, body_html, slug), encoding="utf-8")
        entries.append((slug, title, first_para))

    idx = OUT_DIR / "index.html"
    idx.write_text(index_page(entries), encoding="utf-8")
    print(f"Rendered {len(entries)} cards + index to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
