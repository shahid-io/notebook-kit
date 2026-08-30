#!/usr/bin/env python3
"""Markdown -> field-notebook HTML for the system design book.

Handles the constructs the book source uses: ATX headings, nested bullet and
ordered lists, fenced code (light highlighting, plus a `text` mode that keeps
ASCII diagrams untouched), pipe tables, blockquotes, thematic breaks, inline
formatting, and the `:::name` block directives that produce the annotation
blocks, recall rules, redraw plates, part dividers and title page.

    python3 build.py source.md out.html "Book title" [study|tablet|clean]
"""
import base64
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Text column width in mm: page width less the 20mm left margin and the right
# gutter. Code sits in a padded block and loses 6.9mm of that; a diagram is set
# flush, so it keeps the full measure. Both are scaled to fit, never clipped.
LAYOUTS = {
    "study":  {"gutter": "60mm", "rail": "52mm", "size": "10.4pt", "rail_on": True,
               "text_mm": 210 - 20 - 60, "code_max": 8.2, "col_mm": 262},
    "tablet": {"gutter": "92mm", "rail": "84mm", "size": "12.6pt", "rail_on": True,
               "text_mm": 297 - 20 - 92, "code_max": 9.8, "col_mm": 133},
    "clean":  {"gutter": "20mm", "rail": "0mm",  "size": "10.6pt", "rail_on": False,
               "text_mm": 210 - 20 - 20, "code_max": 8.6, "col_mm": 262},
}

# name -> (label, mark). The mark is a single geometric glyph, not decoration:
# it is what makes two blue-ruled blocks tell themselves apart at a glance.
BLOCKS = {
    "ask":    ("Interviewer asks", "?"),
    "signal": ("Senior signal", "◆"),
    "trap":   ("Trap", "×"),
    "do":     ("Do this", "→"),
    "key":    ("Key idea", "■"),
}

# Every directive name the renderer answers to. BLOCKS are the annotation
# blocks; the rest are structural. lint.py checks against this, so a directive
# added below is a directive the linter knows about, with no second list.
DIRECTIVES = set(BLOCKS) | {"recall", "redraw", "quiz", "part", "title",
                            "figure", "toc", "term", "glossary"}

KEYWORDS = {
    "java": r"\b(abstract|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|if|implements|import|instanceof|int|interface|long|new|package|private|protected|public|return|static|super|switch|synchronized|this|throw|throws|try|void|volatile|while|var|record|true|false|null)\b",
    "js": r"\b(async|await|break|case|catch|class|const|continue|default|delete|do|else|export|extends|finally|for|from|function|if|import|in|instanceof|let|new|of|return|static|super|switch|this|throw|try|typeof|var|void|while|yield|true|false|null|undefined|require|module|exports)\b",
    "python": r"\b(and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|none|nonlocal|not|or|pass|raise|return|true|false|try|while|with|yield|self|None|True|False)\b",
    "sql": r"\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|INDEX|UNIQUE|PRIMARY|KEY|FOREIGN|REFERENCES|ON|CONFLICT|DO|NOTHING|JOIN|LEFT|INNER|GROUP|BY|ORDER|LIMIT|AND|OR|NOT|NULL|DEFAULT|CONSTRAINT|ALTER|ADD|RETURNING|WITH|AS|CASE|WHEN|THEN|END|BEGIN|COMMIT|TRANSACTION|COLUMN|DROP|CHECK|VALIDATE|CONCURRENTLY|USING|EXPLAIN|ANALYZE|LOCK|ACCESS|EXCLUSIVE|SHARE|MODE|EXISTS|CASCADE|DISTINCT|HAVING|OFFSET|GENERATED|ALWAYS|IDENTITY|BETWEEN|IS|COUNT|SUM|COALESCE|EXCLUDE|DEFERRABLE|INITIALLY|IMMEDIATE)\b",
    "bash": r"\b(aws|curl|export|echo|if|then|fi|for|do|done|while|kafka-topics|s3|s3api)\b",
    "yaml": r"^\s*[\w.-]+(?=:)",
    "json": r"\"[\w.$-]+\"(?=\s*:)",
}

ALIAS = {"javascript": "js", "jsx": "js", "ts": "js", "tsx": "js",
         "typescript": "js", "node": "js", "py": "python",
         "postgresql": "sql", "psql": "sql", "mongo": "js", "sh": "bash"}

# Pen marks. The path geometry comes from the Binary Semaphore doodle set,
# where each curve was drawn once by hand rather than generated, which is why
# they read as a pen and not as a wobble filter. `preserveAspect
# Ratio="none"` stretches one authored curve to any word width, and the whole
# thing is static SVG, so it survives Chrome's print path with no JavaScript.
PEN = {
    "u": ("mk-u", 'viewBox="0 0 300 12"',
          "M3 8C58 3 118 10 178 6c40-3 80-1 119 2"),
    "o": ("mk-o", 'viewBox="0 0 300 120"',
          "M155 9C82 6 16 28 13 60c-3 33 70 53 142 51 78-2 135-26 132-55"
          "C296 30 224 12 150 11"),
    "b": ("mk-b", 'viewBox="0 0 300 100"',
          "M9 13C88 8 214 7 292 13c4 26 3 49-1 74-79 6-206 7-284 1"
          "C3 62 4 39 9 13Z"),
    "s": ("mk-s", 'viewBox="0 0 300 10"',
          "M4 6c60-3 130 2 190-1 40-2 70 1 102 2"),
}


def pen(kind, inner):
    klass, view, d = PEN[kind]
    return (f'<span class="{klass}">{inner}'
            f'<svg {view} fill="none" preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="{d}" stroke="currentColor" stroke-width="2.2" '
            f'vector-effect="non-scaling-stroke" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg></span>')


# Hand-drawn figures live beside the book, in books/figures/<stem>.py, as a
# FIGURES dict of name -> svg string. Coordinates want arithmetic and reuse, so
# they belong in code; the markdown only names the figure it wants.
FIGURES = {}


def figures_path(src):
    """books/<name>.md -> books/figures/<name>.py. Matched by filename and
    nothing else, so a renamed book needs its figures file renamed too."""
    return os.path.join(os.path.dirname(src), "figures",
                        os.path.splitext(os.path.basename(src))[0] + ".py")


def load_figures(src):
    import importlib.util
    path = figures_path(src)
    if not os.path.exists(path):
        return
    spec = importlib.util.spec_from_file_location("bookfigures", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bookfigures"] = mod
    spec.loader.exec_module(mod)
    FIGURES.update(mod.FIGURES)


# (kind, num, label, slug); kind is "part" or "sec".
TOC = []

# (word, definition html), in the order they are first defined. A reader who
# has to leave the page to look a word up has been failed by the page, so a
# term is glossed where it first appears and the glossary is built from those
# glosses rather than written separately.
TERMS = []

MM_PER_CHAR_PT = 0.6 * 0.35278      # JetBrains Mono advances 0.6em per glyph
FIT = {"text": LAYOUTS["study"]["text_mm"], "max": LAYOUTS["study"]["code_max"],
       "col": LAYOUTS["study"]["col_mm"]}
NESTED = [0]                        # block nesting depth; each level eats ~6.4mm


def slugify(text):
    s = re.sub(r"[`*_]+", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "section"


def split_number(text):
    """'7. Multipart' -> ('7', 'Multipart'); 'Appendix B. Glossary' -> ('B', ...)."""
    m = re.match(r"^(\d+)\.\s*(.*)$", text)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"^Appendix ([A-Z])\.\s*(.*)$", text)
    if m:
        return m.group(1), m.group(2)
    return "", text


def fit_pt(block, flush):
    """Point size at which the widest line still fits. `flush` blocks (diagrams)
    keep the whole measure; padded code blocks lose their side padding."""
    widest = max((len(ln) for ln in block), default=0)
    if widest == 0:
        return FIT["max"]
    avail = FIT["text"] - 6.4 * NESTED[0] - (0 if flush else 6.9)
    return round(min(FIT["max"], avail / (widest * MM_PER_CHAR_PT)), 2)


def fits_column(block, pt, flush):
    """Whether the block is short enough to keep on one page. A block taller
    than the column cannot honour break-inside:avoid anyway: Chrome pushes it
    to the next page, leaves the current one blank, then fragments it there."""
    lh = 1.36 if flush else 1.44
    pad = 8 if flush else 12
    height = len(block) * pt * lh * 0.35278 + pad
    return height < FIT["col"] * 0.92


# --- inline -------------------------------------------------------------------

def inline(text):
    """Inline markdown. Code spans are stashed first so nothing reformats them."""
    stash = []

    def keep(m):
        stash.append(m.group(1))
        return f"\x00{len(stash) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"==([^=]+)==", r"<mark>\1</mark>", text)
    text = re.sub(r"!!([^!]+)!!", r'<mark class="r">\1</mark>', text)
    text = re.sub(r"\+\+([^+]+)\+\+", r'<mark class="g">\1</mark>', text)
    text = re.sub(r"%%([^%]+)%%", r'<mark class="b">\1</mark>', text)
    text = re.sub(r"__([^_]+)__", lambda m: pen("u", m.group(1)), text)
    text = re.sub(r"\(\(([^)]+)\)\)", lambda m: pen("o", m.group(1)), text)
    text = re.sub(r"\[\[([^\]]+)\]\]", lambda m: pen("b", m.group(1)), text)
    text = re.sub(r"~~([^~]+)~~", lambda m: pen("s", m.group(1)), text)
    text = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", text)
    for i, code in enumerate(stash):
        text = text.replace(f"\x00{i}\x00",
                            "<code>" + html.escape(code, quote=False) + "</code>")
    return text


# Characters that are structure rather than content in an ASCII figure.
WIRE = "\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c" \
       "\u256d\u256e\u256f\u2570\u2550\u2551\u2554\u2557\u255a\u255d"
# Arrowheads are movement, not structure, so they take their own ink.
ARROW = "\u25b6\u25c0\u25b2\u25bc\u2192\u2191\u2193"
FILL = "\u2588\u2589\u258a\u258b\u258c\u258d\u258e\u258f" \
       "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2591\u2592\u2593\u2595"
VERDICT = {"\u2713": "dok", "\u2714": "dok", "\u2717": "dno", "\u2718": "dno"}


def ink_words(chunk):
    """A capitalised run in a figure is a node label, so it takes full ink."""
    esc = html.escape(chunk, quote=False)
    return re.sub(r"\b([A-Z]{3,}[A-Z0-9_]*)\b", r'<span class="dl">\1</span>', esc)


def ink_figure(line):
    """Colour an ASCII figure by role. Structure recedes to --wire, block fills
    read as bars, ticks and crosses carry the verdict, node labels advance, and
    anything after a left arrow is an annotation in pencil."""
    head, sep, tail = line.partition("\u2190")
    out, i = [], 0
    while i < len(head):
        ch = head[i]
        if ch in WIRE or ch in FILL or ch in ARROW:
            klass = "dr" if ch in WIRE else ("df" if ch in FILL else "da")
            pool = WIRE if ch in WIRE else (FILL if ch in FILL else ARROW)
            j = i
            while j < len(head) and head[j] in pool:
                j += 1
            out.append(f'<span class="{klass}">'
                       f"{html.escape(head[i:j], quote=False)}</span>")
            i = j
        elif ch in VERDICT:
            out.append(f'<span class="{VERDICT[ch]}">{ch}</span>')
            i += 1
        else:
            j = i
            while j < len(head) and head[j] not in WIRE \
                    and head[j] not in FILL and head[j] not in ARROW \
                    and head[j] not in VERDICT:
                j += 1
            out.append(ink_words(head[i:j]))
            i = j
    if sep:
        out.append(f'<span class="dc">'
                   f"{html.escape(sep + tail, quote=False)}</span>")
    return "".join(out)


def highlight(line, lang):
    """Escape, then apply low-risk colouring. `text` blocks are inked as
    figures; everything else gets keyword colouring."""
    if lang in ("", "text", "diagram", "txt"):
        return ink_figure(line)

    code, comment = line, ""
    marker = "--" if lang == "sql" else ("#" if lang in ("bash", "yaml") else "//")
    idx = code.find(marker)
    if idx >= 0 and code.count('"', 0, idx) % 2 == 0:
        code, comment = code[:idx], code[idx:]

    out, buf, i = [], "", 0

    def flush(chunk):
        esc = html.escape(chunk, quote=False)
        pat = KEYWORDS.get(ALIAS.get(lang, lang))
        if pat:
            flags = re.M if lang in ("yaml", "json") else 0
            esc = re.sub(pat, lambda m: f'<span class="kw">{m.group(0)}</span>',
                         esc, flags=flags)
        return re.sub(r"\b(\d[\d_.]*)\b", r'<span class="nu">\1</span>', esc)

    while i < len(code):
        ch = code[i]
        if ch in "\"'":
            out.append(flush(buf))
            buf = ""
            j = i + 1
            while j < len(code) and code[j] != ch:
                j += 1
            out.append('<span class="st">'
                       + html.escape(code[i:j + 1], quote=False) + "</span>")
            i = j + 1
        else:
            buf += ch
            i += 1
    out.append(flush(buf))
    res = "".join(out)
    if comment:
        res += '<span class="cm">' + html.escape(comment, quote=False) + "</span>"
    return res


def ticks():
    """Corner marks for a blank plate, in place of a frame."""
    return '<i class="c1"></i><i class="c2"></i><i class="c3"></i><i class="c4"></i>'


# --- block directives ---------------------------------------------------------

def render_directive(name, arg, body):
    if name in BLOCKS:
        label, mark = BLOCKS[name]
        NESTED[0] += 1
        try:
            inner = render(body)
        finally:
            NESTED[0] -= 1
        lead = f'<p class="lead">{inline(arg.strip())}</p>' if arg.strip() else ""
        return (f'<section class="blk {name}">'
                f'<span class="lbl"><span class="mk">{mark}</span>{label}</span>'
                f"{lead}{inner}</section>")

    if name == "recall":
        prompt, _, count = arg.partition("|")
        n = int(count.strip()) if count.strip().isdigit() else 4
        return ('<section class="recall"><span class="lbl">Recall</span>'
                f'<p class="prompt">{inline(prompt.strip())}</p>'
                '<div class="lines">' + "<i></i>" * n + "</div></section>")

    if name == "term":
        word = arg.strip()
        body_html = render(body)
        TERMS.append((word, body_html))
        return (f'<aside class="term" id="term-{slugify(word)}">'
                f'<span class="w">{inline(word)}</span>{body_html}</aside>')

    if name == "glossary":
        return "\x03GLOSSARY\x03"

    if name == "quiz":
        num, _, rest = arg.partition("|")
        ref, _, count = rest.partition("|")
        n = int(count.strip()) if count.strip().isdigit() else 5
        return ('<section class="quiz">'
                f'<span class="qn">{html.escape(num.strip())}</span>'
                f'<span class="qref">{html.escape(ref.strip())}</span>'
                f'<p class="prompt">{inline(" ".join(body.split()))}</p>'
                '<div class="lines">' + "<i></i>" * n + "</div></section>")

    if name == "redraw":
        prompt, _, hint = arg.partition("|")
        hint_html = (f'<p class="hint">{inline(hint.strip())}</p>'
                     if hint.strip() else "")
        return ('<section class="redraw"><p class="lbl">Draw from memory</p>'
                f'<p class="prompt">{inline(prompt.strip())}</p>{hint_html}'
                f'<div class="pad">{ticks()}</div></section>')

    if name == "part":
        roman, _, title = arg.partition("|")
        slug = slugify(title)
        TOC.append(("part", roman.strip(), title.strip(), slug))
        idx = len(TOC) - 1
        return (f'<section class="part" id="{slug}">'
                f'<p class="kicker">Part</p>'
                f'<p class="roman">{html.escape(roman.strip())}</p>'
                f"<h2>{inline(title.strip())}</h2>"
                f'<div class="blurb">{render(body)}</div>'
                f"\x02{idx}\x02</section>")

    if name == "title":
        lines = [ln for ln in body.split("\n") if ln.strip()]
        eyebrow, title, sub, meta = (lines + [""] * 4)[:4]
        return ('<section class="titlepage">'
                f'<p class="eyebrow">{inline(eyebrow)}</p>'
                '<div class="top-rule"></div>'
                f"<h1>{inline(title)}</h1>"
                f'<p class="sub">{inline(sub)}</p>'
                '<div class="plate">'
                f'<p class="cap">{inline(arg.strip())}</p>'
                f'<div class="pad">{ticks()}</div></div>'
                f'<p class="meta">{inline(meta)}</p></section>')

    if name == "figure":
        key = arg.strip()
        if key not in FIGURES:
            raise SystemExit(f"build.py: no figure named {key!r}. "
                             f"have: {sorted(FIGURES)}")  # lint.py says more
        cap = (f'<p class="cap">{inline(body.strip())}</p>'
               if body.strip() else "")
        return f'<figure class="drawn">{FIGURES[key]}{cap}</figure>'

    if name == "toc":
        return "\x01TOC\x01"

    return render(body)


def render_toc():
    rows, open_list = [], False
    for kind, num, label, slug in TOC:
        if kind == "part":
            if open_list:
                rows.append("</ol>")
            rows.append(f'<p class="part-row"><a href="#{slug}">Part {num} '
                        f"&middot; {inline(label)}</a></p><ol>")
            open_list = True
            continue
        if not open_list:
            rows.append("<ol>")
            open_list = True
        rows.append(f'<li><span class="n">{html.escape(num)}</span>'
                    f'<span><a href="#{slug}">{inline(label)}</a></span>'
                    f'<span class="dots"></span></li>')
    if open_list:
        rows.append("</ol>")
    return ('<section class="toc"><div class="head"><h2>Contents</h2>'
            '<span class="r"></span></div>' + "".join(rows) + "</section>")


def render_glossary():
    """Every :::term in the book, alphabetical. Written once, at first use."""
    rows = []
    for word, body in sorted(TERMS, key=lambda t: t[0].lower()):
        rows.append(f'<div class="gl-row"><p class="w">'
                    f'<a href="#term-{slugify(word)}">{inline(word)}</a></p>'
                    f'<div class="d">{body}</div></div>')
    return '<div class="glossary">' + "".join(rows) + "</div>"


def render_part_toc(idx):
    """The sections belonging to the part recorded at TOC[idx]."""
    items = []
    for kind, num, label, slug in TOC[idx + 1:]:
        if kind == "part":
            break
        items.append(f'<li><span class="n">{html.escape(num)}</span>'
                     f"<span>{inline(label)}</span></li>")
    if not items:
        return ""
    return ('<div class="part-toc"><p class="h">In this part</p><ol>'
            + "".join(items) + "</ol></div>")


# --- block renderer -----------------------------------------------------------

def render_list(lines, start):
    """Consume one list (with nesting) beginning at lines[start]."""
    def indent_of(ln):
        return len(ln) - len(ln.lstrip(" "))

    base = indent_of(lines[start])
    ordered = bool(re.match(r"^\s*\d+[.)]\s", lines[start]))
    out = ["<ol>" if ordered else "<ul>"]
    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            nxt = i + 1
            if nxt < len(lines) and re.match(r"^\s*([-*]|\d+[.)])\s", lines[nxt]) \
                    and indent_of(lines[nxt]) >= base:
                i += 1
                continue
            break
        m = re.match(r"^\s*([-*]|\d+[.)])\s+(.*)$", ln)
        ind = indent_of(ln)
        if not m:
            # lazy continuation: an indented wrapped line joins the item above
            if ind > base and out[-1].endswith("</li>"):
                out[-1] = out[-1][:-5] + " " + inline(ln.strip()) + "</li>"
                i += 1
                continue
            break
        if ind < base:
            break
        if ind > base:
            nested, i = render_list(lines, i)
            out[-1] = out[-1][:-5] + nested + "</li>"
            continue
        out.append(f"<li>{inline(m.group(2))}</li>")
        i += 1
    out.append("</ol>" if ordered else "</ul>")
    return "".join(out), i


def render_table(lines, start):
    rows, i = [], start
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
        i += 1
    head, body = rows[0], rows[2:]
    out = ["<table><thead><tr>"]
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out), i


def render(md):
    lines = md.split("\n")
    out, i, para = [], 0, []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        ln = lines[i]

        m = re.match(r"^:::(\w+)[ \t]*(.*)$", ln)
        if m:
            flush()
            name, arg = m.group(1), m.group(2)
            depth, body, i = 1, [], i + 1
            while i < len(lines):
                if re.match(r"^:::\w+", lines[i]):
                    depth += 1
                elif lines[i].strip() == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                body.append(lines[i])
                i += 1
            out.append(render_directive(name, arg, "\n".join(body)))
            i += 1
            continue

        if ln.startswith("```"):
            flush()
            lang = ln[3:].strip().lower()
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            is_fig = lang in ("", "text", "diagram")
            pt = fit_pt(block, is_fig)
            tall = not fits_column(block, pt, is_fig)
            names = ([("diagram" if is_fig else "")] + (["tall"] if tall else []))
            names = " ".join(n for n in names if n)
            cls = f' class="{names}"' if names else ""
            keep = ";break-inside:auto;page-break-inside:auto" if tall else ""
            code = "\n".join(highlight(b, lang) for b in block)
            out.append(f'<pre{cls} style="font-size:{pt}pt{keep}">'
                       f"<code>{code}</code></pre>")
            continue

        h = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if h:
            flush()
            lvl, txt = len(h.group(1)), h.group(2).strip()
            slug = slugify(txt)
            if lvl == 2:
                num, label = split_number(txt)
                TOC.append(("sec", num, label, slug))
                numeral = f'<span class="sec-n">{html.escape(num)}</span>' if num else ""
                out.append(f'<section class="sec" id="{slug}">'
                           f'<div class="sec-top">{numeral}'
                           '<span class="sec-rule"></span></div>'
                           f"<h2>{inline(label)}</h2></section>")
            else:
                out.append(f'<h{lvl} id="{slug}">{inline(txt)}</h{lvl}>')
            i += 1
            continue

        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", ln):
            flush()
            out.append("<hr>")
            i += 1
            continue

        if ln.lstrip().startswith("|") and i + 1 < len(lines) \
                and set(lines[i + 1].strip()) <= set("|-: "):
            flush()
            tbl, i = render_table(lines, i)
            out.append(tbl)
            continue

        if re.match(r"^\s*([-*]|\d+[.)])\s+", ln):
            flush()
            lst, i = render_list(lines, i)
            out.append(lst)
            continue

        if ln.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i][1:].strip())
                i += 1
            out.append("<blockquote>" + render("\n".join(quote)) + "</blockquote>")
            continue

        if not ln.strip():
            flush()
            i += 1
            continue

        para.append(ln.strip())
        i += 1

    flush()
    return "".join(out)


# --- page assembly ------------------------------------------------------------

def font_face(name, filename, weight=400):
    with open(os.path.join(HERE, "fonts", filename), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return (f"@font-face{{font-family:'{name}';font-style:normal;"
            f"font-weight:{weight};src:url(data:font/woff2;base64,{b64}) "
            "format('woff2');}")


def main():
    src, dst, title = sys.argv[1], sys.argv[2], sys.argv[3]
    layout = sys.argv[4] if len(sys.argv) > 4 else "study"
    cfg = LAYOUTS[layout]
    FIT["text"], FIT["max"], FIT["col"] = (cfg["text_mm"], cfg["code_max"],
                                           cfg["col_mm"])

    load_figures(src)

    with open(src, encoding="utf-8") as fh:
        body = render(fh.read())
    body = body.replace("\x01TOC\x01", render_toc())
    body = body.replace("\x03GLOSSARY\x03", render_glossary())
    body = re.sub(r"\x02(\d+)\x02", lambda m: render_part_toc(int(m.group(1))), body)

    with open(os.path.join(HERE, "theme.css"), encoding="utf-8") as fh:
        css = fh.read()

    fonts = (font_face("Caveat", "Caveat-SemiBold.woff2", 600)
             + font_face("Patrick Hand", "PatrickHand-Regular.woff2"))

    furniture = '<div class="paper"></div>'
    if cfg["rail_on"]:
        furniture += ('<aside class="rail"><p class="rail-title">Notes</p>'
                      '<div class="dots"></div></aside>')

    vars_css = (f":root{{--gutter-right:{cfg['gutter']};--rail-w:{cfg['rail']};}}"
                f"body{{font-size:{cfg['size']};}}")

    doc = ("<!doctype html><html><head><meta charset='utf-8'>"
           f"<title>{html.escape(title)}</title><style>{fonts}{css}{vars_css}"
           f"</style></head><body class='layout-{layout}'>"
           + furniture + body + "</body></html>")

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"    {dst}")


if __name__ == "__main__":
    main()
