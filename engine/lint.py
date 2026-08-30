#!/usr/bin/env python3
"""Check book markdown for the mistakes that only show up in the PDF.

    python3 engine/lint.py books/*.md

Every check here exists because the same defect got through once already: a
highlighter opened and never closed, a marker stranded inside an ASCII figure
where inline formatting does not run, a figure name with no drawing behind it.
Errors fail the build; notes are advice and do not.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build                                            # noqa: E402

DIRECTIVES = build.DIRECTIVES

# Paired inline marks, as build.py's `inline` sees them: an odd count means one
# of them never closed, so the rest of the paragraph renders as literal text.
SYMMETRIC = {"==": "highlight", "!!": "danger highlight", "++": "practice highlight",
             "%%": "definition highlight", "__": "pen underline", "~~": "pen strike"}
ASYMMETRIC = {("((", "))"): "pen circle", ("[[", "]]"): "pen box"}

# A pen circle or box is one authored curve stretched to the span it wraps.
# Past about five words it flattens into a lozenge and stops reading as a pen.
MAX_PEN_WORDS = 5

# Inline marks never run inside a fence. In a code fence that is usually
# harmless (`x == y`, `i++`, `__init__`); in an ASCII figure it is always a
# marker the author meant to be a highlight.
FIGURE_LANGS = {"", "text", "diagram", "txt"}


class Report:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.notes = []

    def error(self, line, msg):
        self.errors.append((line, msg))

    def note(self, line, msg):
        self.notes.append((line, msg))


def strip_code(text):
    """Code spans are stashed before any mark runs, so they cannot unbalance one."""
    return re.sub(r"`[^`]*`", "", text)


def check_marks(rep, lineno, text):
    text = strip_code(text)
    for tok, name in SYMMETRIC.items():
        n = text.count(tok)
        if n % 2:
            rep.error(lineno, f"unclosed {name} `{tok}`: {n} marker(s) in this block")
    for (open_tok, close_tok), name in ASYMMETRIC.items():
        a, b = text.count(open_tok), text.count(close_tok)
        if a != b:
            rep.error(lineno, f"unbalanced {name}: {a} `{open_tok}` vs {b} `{close_tok}`")
    for open_tok, close_tok in (("((", "))"), ("[[", "]]")):
        pat = re.escape(open_tok) + r"([^" + re.escape(close_tok[0]) + r"]+)" \
              + re.escape(close_tok)
        for m in re.finditer(pat, text):
            words = len(m.group(1).split())
            if words > MAX_PEN_WORDS:
                rep.note(lineno, f"pen mark wraps {words} words, flattens past "
                                 f"{MAX_PEN_WORDS}: {m.group(1)[:44]!r}")


def lint(path):
    rep = Report(path)
    build.FIGURES.clear()
    build.load_figures(path)

    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    fence = None            # (lineno, lang) while open
    fence_body = []
    stack = []              # open directives: (lineno, name)
    para, para_at = [], 0
    secs, apps = [], []

    def flush_para():
        if para:
            check_marks(rep, para_at, " ".join(para))
            para.clear()

    for i, ln in enumerate(lines, 1):
        if ln.startswith("```"):
            if fence is None:
                flush_para()
                fence, fence_body = (i, ln[3:].strip().lower()), []
            else:
                if fence[1] in FIGURE_LANGS:
                    body = "\n".join(fence_body)
                    for tok, name in (("==", "highlight"), ("!!", "danger highlight"),
                                      ("%%", "definition highlight"),
                                      ("~~", "pen strike")):
                        if re.search(re.escape(tok) + r"[^\s" + re.escape(tok[0])
                                     + r"][^" + re.escape(tok[0]) + r"]*"
                                     + re.escape(tok), body):
                            rep.error(fence[0], f"{name} `{tok}` inside a figure "
                                                f"fence renders literally")
                fence = None
            continue
        if fence is not None:
            fence_body.append(ln)
            continue

        m = re.match(r"^:::(\w+)[ \t]*(.*)$", ln)
        if m:
            flush_para()
            name, arg = m.group(1), m.group(2)
            if name not in DIRECTIVES:
                rep.error(i, f"unknown directive `:::{name}`, "
                             f"known: {', '.join(sorted(DIRECTIVES))}")
            if name == "figure":
                key = arg.strip()
                if key not in build.FIGURES:
                    have = ", ".join(sorted(build.FIGURES))
                    where = build.figures_path(path)
                    rep.error(i, f"no figure named {key!r}. "
                                 + (f"{where} defines: {have}" if have else
                                    f"{where} does not exist, so this book has "
                                    f"no figures. Create it, or delete the "
                                    f":::figure block."))
            check_marks(rep, i, arg)
            stack.append((i, name))
            continue
        if ln.strip() == ":::":
            flush_para()
            if not stack:
                rep.error(i, "closing `:::` with no directive open")
            else:
                stack.pop()
            continue

        h = re.match(r"^##\s+(.*)$", ln)
        if h:
            flush_para()
            txt = h.group(1).strip()
            num, _ = build.split_number(txt)
            if num.isdigit():
                secs.append((i, int(num)))
            elif num:
                apps.append((i, num))
            check_marks(rep, i, txt)
            continue

        if not ln.strip():
            flush_para()
            continue
        if not para:
            para_at = i
        para.append(ln.strip())

    flush_para()

    if fence is not None:
        rep.error(fence[0], "code fence opened here and never closed")
    for lineno, name in stack:
        rep.error(lineno, f"`:::{name}` opened here and never closed")

    for seq, label, first in ((secs, "section", 1), (apps, "appendix", "A")):
        want = first
        for lineno, got in seq:
            if got != want:
                rep.error(lineno, f"{label} numbering jumps: expected {want}, got {got}")
                want = got
            want = want + 1 if isinstance(want, int) else chr(ord(want) + 1)

    return rep


def main():
    paths = sys.argv[1:]
    if not paths:
        raise SystemExit("usage: lint.py <book.md> [book.md ...]")
    bad = 0
    for path in paths:
        rep = lint(path)
        bad += len(rep.errors)
        for lineno, msg in sorted(rep.errors + rep.notes):
            kind = "error" if (lineno, msg) in rep.errors else "note"
            print(f"{rep.path}:{lineno}: {kind}: {msg}")
    total = len(paths)
    print(f"lint: {total} book{'s' if total != 1 else ''}, "
          f"{bad} error{'s' if bad != 1 else ''}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
