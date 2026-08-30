# Getting started

Zero to a printed study notebook. About ten minutes, most of it reading.

## 1. What you need

| | Why | Check |
|---|---|---|
| **Python 3.9+** | The whole pipeline. No packages to install | `python3 --version` |
| **Google Chrome** | Renders HTML to PDF, and supplies the page numbers | Chrome installed anywhere standard |
| `yt-dlp` *(optional)* | Only if you build books from lecture transcripts | `pip install yt-dlp` |

There are no dependencies beyond the standard library. Nothing to `npm
install`, no virtualenv, no build step. Clone it and run it.

## 2. Build what is already here

```bash
bash build.sh
```

Every book, Reading edition, into `pdf/<NN-slug>/`. First run takes a couple of
minutes because Chrome starts once per book.

```bash
bash build.sh example          # just the template book
bash build.sh example tablet   # the tablet edition of it
bash build.sh all              # every book, all three editions
```

Open `pdf/XX-example/Example-Book-Reading.pdf`. That is the template, and it
demonstrates every directive and mark in the system. Read it next to
`books/example.md` and the syntax will make sense in about five minutes.

## 3. Write your own

```bash
cp books/example.md books/my-book.md
cp books/figures/example.py books/figures/my-book.py    # only if you want figures
```

Figures are found by filename: `books/my-book.md` looks for
`books/figures/my-book.py` and nothing else. If you skip the second line, delete
the `:::figure` block from your copy, or the linter will stop the build and tell
you exactly this.

Then add one line to the `BOOKS` array at the top of `build.sh`:

```bash
"my-book|books/my-book.md|My Book|MY BOOK|07|My-Book"
#  slug  |    source      | title  | running head | number | output stem
```

And build it:

```bash
bash build.sh my-book
```

That is the entire setup. There is no configuration file and no registry beyond
that one line.

## 4. The loop you will actually use

```bash
# edit books/my-book.md, then:
bash build.sh my-book && open pdf/07-my-book/My-Book-Reading.pdf
```

The linter runs first and refuses to build if you left a highlighter unclosed,
named a figure that does not exist, or skipped a section number. Read its output
rather than the traceback; it points at a line.

## 5. Where to look when you want more

| I want to | Read |
|---|---|
| Know every directive and mark | `books/example.md`, then `README.md` |
| Understand the colours | `README.md`, the Design section |
| Draw a figure by hand | `README.md`, Hand-drawn figures, and `engine/sketch.py` |
| Change the page size | `build.sh`, the `A4W`/`T169W` block |
| Pull a lecture transcript | `python3 engine/transcript.py "<url>" sources` |
| Know what the linter checks | `README.md`, the Lint section |

## Next: how a book actually gets written

Everything above is mechanics. **`AUTHORING.md`** is the workflow: how to turn a
lecture or a paper into a spine, why every book needs one question, what to add
that the source did not say, and how these books are written with an AI
assistant. Read it before your first book.

The short version follows.

## Writing advice, which matters more than the tooling

**One book, one question.** The books that work are built around a single
question asked repeatedly, not a survey of a topic. "Where did the developer
make an assumption?" produced a better security book than a list of
vulnerabilities would have. Decide the question before the outline.

**Every `##` is a page.** Write to that. If a section will not fit on a page,
it is two sections.

**Draft the part and section list before any prose.** It is much cheaper to
move a section than to rewrite one.

**The value is what is not in the source.** If you are working from a lecture or
a book, a transcript in book clothing is worse than the original. What you add
is the failure table, the interview framing, the correction where the source is
loose, and the pointer to the other notebook that covers it properly.

**Three or four marks on a page.** A page with ten marks has none.

**Gloss the words.** If a reader has to open a search tab, the page failed. Use
`:::term` at first use; the glossary builds itself.

## Troubleshooting

**"Chrome not found"** — `engine/pdf.py` looks in the standard install
locations. If yours is elsewhere, set `CHROME=/path/to/chrome` in the
environment.

**PDFs have no page numbers** — the CDP path failed and it fell back to
`--print-to-pdf`. Usually another Chrome instance is holding the debug port.
Quit Chrome and rebuild.

**Diagrams look slightly too wide or narrow** — you do not have JetBrains Mono
installed. Code blocks are measured using its advance width. Nothing clips.
See `engine/fonts/NOTICE.md`.

**A build fails with a lint error** — that is the linter doing its job. It names
the file, the line and the problem.
