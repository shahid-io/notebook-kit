# Study Notebooks

Printed study manuals, built from markdown into annotatable PDFs. One pipeline,
one design, many books. A notebook is built around a single question, because
one question worked properly teaches more than a survey does.

| # | Book | Source | What it is |
|---|---|---|---|
| XX | Example Book | `books/example.md` | The template. Every directive and mark, rendered |
| 00 | Question Bank | `books/question-bank.md` | Generated once you have books to collect from |

New here? Read **`GETTING-STARTED.md`** to get a PDF out of it, then
**`AUTHORING.md`** before you write your first book. The second one matters
more: this repository is a typesetter, and the hard part is deciding what the
book is about.

## Build

```bash
bash build.sh                        # every book, Reading edition
bash build.sh example                # one book, Reading edition
bash build.sh example tablet         # one book, one named edition
bash build.sh all                    # every book, every edition
```

Arguments may name a book slug, an edition (`study`, `tablet`, `clean`), `all`,
or one of each in either order. **Only the Reading edition builds by default**:
Print and Tablet cost a third of the wall clock each, so name one when you want
it. Requires Google Chrome and Python 3, no third-party packages.

Every build regenerates the question bank and lints every book before rendering.
A lint error fails the build.

### Adding a book

1. Write `books/<slug>.md`.
2. Add one line to the `BOOKS` array at the top of `build.sh`:
   `slug|source|title|running head|number|output stem`.

That is all. The subject does not matter: system design, a language, DSA, a
paper. The format is a study manual, not a system design template.

Source transcripts for books built from lectures live in `sources/`, with
`sources/MANIFEST.md` holding the video-to-book mapping and what to write next.

## Layout

```text
books/           the source markdown, one file per book
sources/         lecture transcripts + MANIFEST.md, the writing queue
engine/          build.py, pdf.py, theme.css, fonts   (shared by every book)
engine/transcript.py   pulls a YouTube playlist into sources/
engine/sketch.py       hand-drawn SVG primitives for figures
engine/lint.py         checks the book markdown, run before every build
engine/questions.py    collects the question bank out of the other books
share.sh               packages the pipeline as a standalone repo for others
GETTING-STARTED.md     zero to a built PDF, for someone who has not seen this
html/            intermediate HTML, regenerated, not tracked
pdf/NN-slug/     output, Reading edition by default, not tracked
build.sh         the book list and the page geometry
```

| Edition | File | Layout | For |
|---|---|---|---|
| study | `*-Print.pdf` | A4 portrait, 52mm dot-grid rail | Printing and annotating with a pen |
| tablet | `*-Tablet.pdf` | 16:9 landscape, 84mm rail, larger type | iPad, GoodNotes, Notability |
| clean | `*-Reading.pdf` | A4 portrait, full width | Screen reading |

The tablet edition is **16:9** (11.69 x 6.58in), not A4 landscape, so it fills a
tablet held horizontally with no letterboxing. Chrome is given portrait
dimensions and the `landscape` flag rotates them, so `build.sh` passes
`6.576 x 11.69`. Change `T169W`/`T169H` for a different screen (4:3 is
`8.768 x 11.69`, 3:2 is `7.793 x 11.69`). Horizontal metrics are unchanged, so
on-screen type size matches the print edition; only the page height differs, and
`LAYOUTS["tablet"]["col_mm"]` in `engine/build.py` tracks it.

## Pipeline

```text
books/<book>.md
        │  engine/build.py   markdown + :::directives -> HTML, fonts inlined
        ▼
html/<book>-<edition>.html
        │  engine/pdf.py     Chrome DevTools Protocol, running header and footer
        ▼
pdf/<NN-slug>/<Stem>-<Edition>.pdf
```

`engine/pdf.py` speaks CDP over a hand-rolled WebSocket so the running header and
footer can carry real page numbers, which `chrome --print-to-pdf` cannot
template. It falls back to `--print-to-pdf` (no page numbers) if that path fails.

## Writing content

Standard markdown, plus block directives:

```text
:::ask     A follow-up question to expect        ?  pencil rule
:::signal  The sentence that reads as senior     ◆  blue rule
:::do      The concrete practice                 →  blue rule
:::trap    A plausible answer that is wrong      ×  warm rule
:::key     The one thing to carry away           ■  heavy ink rule
:::term    Sharding        a gloss, at the word's first use
:::glossary                every :::term in the book, alphabetical
:::recall  Prompt | 6      ruled recall box, 6 lines
:::quiz    Q7 | 05 / 12 | 6   numbered prompt; the question bank only
:::redraw  Prompt | hint   full dot-grid page for redrawing from memory
:::part    II | Title      part divider page, body is the blurb
:::title                   title page; body lines are eyebrow/title/sub/meta
:::toc                     generated contents, placed wherever this appears
```

Inline: `**bold**`, `*italic*`, `` `code` ``, `[link](url)`, plus nine marks.

**Four highlighters**, which are fields of colour:

| Syntax | Colour | Means |
|---|---|---|
| `==x==` | peach | The sentence to carry away |
| `!!x!!` | rose | The wrong answer, the thing that bites |
| `++x++` | mint | The correct practice |
| `%%x%%` | pink | A definition, at the point it is first defined |

**Four pen marks**, which are strokes drawn over the words:

| Syntax | Mark | Means |
|---|---|---|
| `__x__` | blue underline | The phrase the sentence turns on. The quietest |
| `((x))` | warm circle | The thing you will be asked about. The loudest |
| `[[x]]` | blue box | A term you will use again |
| `~~x~~` | pencil strike | What was true and is not any more |

The pen geometry is one hand-authored curve per mark, taken from the Binary
Semaphore site's `doodle.tsx`, stretched to the wrapped text with
`preserveAspectRatio="none"` and drawn with `vector-effect="non-scaling-stroke"`
so a wide span does not thin the line. Static SVG, no JavaScript, so it survives
Chrome's print path.

**Circle two to five words only.** One authored ellipse stretched across a whole
sentence flattens into a line through the text. The other three take any width.

If a page carries more than three or four marks, it carries none.

Highlighters do not work inside a fenced block. Inside a figure, use ALL CAPS
(it takes full ink) or a `←` annotation (it drops to pencil).

Fenced blocks tagged `text` keep ASCII diagrams exactly as written and are
auto-scaled to fit the column. `sql`, `java`, `js`, `python`, `json`, `bash` and
`yaml` get light syntax colouring, with the usual aliases (`ts`, `tsx`, `py`,
`postgresql`, `sh`).

### Hand-drawn figures

A book may carry sketched figures alongside its ASCII ones. They live in
`books/figures/<book>.py` as a `FIGURES` dict of name to SVG, built with
`engine/sketch.py`, and the markdown only names the one it wants:

```text
:::figure request-path
The caption, set in the reader's hand.
:::
```

`engine/sketch.py` gives you `node`, `rect`, `line`, `arrow`, `circle`,
`highlight` and `text`. Every stroke is drawn two or three times from jittered
endpoints with bowed control points, which is what makes a line read as pen
rather than as a border. Randomness is seeded from each shape's own
coordinates, so **a rebuild is byte-identical**: a book that redrew itself every
build would be unreviewable.

Coordinates are in a 700-wide viewBox and scale into the column, so type and
stroke inside a figure shrink by about 5x. `TYPE_SCALE` and `STROKE_SCALE` in
`sketch.py` lift both back to the weight of the page.

**Draw the figures that carry the book, not all of them.** A sketched figure
costs a few iterations to stop labels colliding, where an ASCII one costs
nothing. Six to eight per book is the right budget.

Every `##` heading starts a new page and becomes a contents entry. Number them
(`## 7. Multipart and resumable upload`) to get the section badge.

### Glossing terms

**A reader who has to open a search tab has been failed by the page.** Any word
a reader might not know gets a gloss where it first appears:

```text
:::term Sharding
Splitting one logical table across several physical databases, so that each one
holds a different subset of the rows. Also called horizontal partitioning.
:::
```

It renders as a quiet dictionary entry, deliberately lighter than the five
annotation blocks: those are the argument, this is a footnote standing where the
reader hit the word. Put `:::glossary` in an appendix and every term in the book
is collected there alphabetically, each entry linking back to the page it was
defined on. **The definition is written once, at the point of need.**

Gloss a word when the prose does not already define it in the same breath. Not
every noun; the page has a budget.

## Sharing this with someone

```bash
bash share.sh ~/Desktop/notebook-kit
```

Copies the engine, `build.sh`, the docs and the template book into a new git
repository with one commit. ==It deliberately leaves out the written books, the
lecture transcripts and every PDF==, so what you hand over is the pipeline
rather than your notes.

The result builds immediately (`bash build.sh example`) with no dependencies
beyond Python 3 and Chrome. Push it with
`gh repo create <name> --private --source=<dir> --push`, or zip it.

Font licensing for redistribution is in `engine/fonts/NOTICE.md`. Both embedded
faces are SIL OFL and free to pass on.

## Lint

```bash
python3 engine/lint.py books/*.md
```

`build.sh` runs this before rendering and a failure stops the build. Every check
is here because the defect it catches reached a printed page once:

- a highlighter or pen mark opened and never closed, which turns the rest of the
  paragraph into literal `==` characters
- `==`, `!!`, `%%` or `~~` stranded inside a `text` fence, where inline
  formatting does not run. Code fences are exempt, because `a == b` and `i++`
  are not marks
- an unknown `:::directive`, an unclosed one, or a stray `:::`
- `:::figure` naming a drawing that does not exist in `books/figures/`
- a gap in `##` section or appendix numbering
- as a note rather than an error, a `((circle))` or `[[box]]` wrapping more than
  five words, which flattens the stroke

The directive list lives in `engine/build.py` as `DIRECTIVES`, so a directive
added to the renderer is one the linter already knows.

## Question bank

Notebook 00 is not written, it is collected. `engine/questions.py` walks the
other books, pulls every `:::ask`, `:::recall` and `:::redraw`, and emits
`books/question-bank.md`, which then builds like any other book.

```text
:::ask     -> a prompt with ruled lines, and its body becomes the answer key
:::recall  -> a prompt with ruled lines, self-graded against its section
:::redraw  -> a full dot-grid plate
```

Prompts are grouped by source part and every one carries the notebook and
section it came from, printed small beside its number, so a blank is never a
dead end. The last part holds the written answers, one section per notebook.

**Never edit `books/question-bank.md`.** It is regenerated on every build. Edit
the notebook the prompt came from.

The point is that **a question answered next to its own answer proves nothing**.
Gathered here, the same prompts can be worked cold, which is the only condition
an interview actually tests.

## Design

A printed engineering manual, not a web page. Rules and whitespace carry the
structure; colour carries the meaning. Every block, table head and code plate is
a field of colour with an accent edge, so a spread reads as coloured at arm's
length and you can find the trap on a page without reading it. Blocks keep the
inset legend, and the mark distinguishes the two blue ones. Diagrams are set
flush between rules as figures.

Each face has one job, and the split is semantic: Caveat for titles (the book's
hand), Patrick Hand for anything addressed to the reader as a prompt (their
hand), JetBrains Mono for the machine, Charter for prose.

### Colour

Two ramps, and nothing outside them. Every value in `engine/theme.css` and in
the header and footer templates in `build.sh` comes from these ten:

```text
cool   #0d1b2a   #1b263b   #415a77   #778da9   #e0e1dd
warm   #9d8189   #f4acb7   #ffcad4   #ffe5d9   #d8e2dc
```

The cool ramp is the book: body ink, secondary ink, structure (section numbers,
`signal`, `do`), pencil for labels and annotations, stock for rules and code
tint. The warm ramp is the reader's hand: the four highlighters above, plus
`#9d8189` as the one warm ink, reserved for traps and wrong answers.

Each colour is also used as a wash (`--wash-*`, the same hex at reduced alpha)
so that structures become fields rather than outlines:

| Element | Field | Edge |
|---|---|---|
| `:::ask`, `:::signal` | cool | pencil / blue |
| `:::do` | mint | blue |
| `:::trap` | pink | warm ink |
| `:::key` | peach | full ink |
| `:::recall` | peach | warm ink |
| Part divider | cool, full page | 3px blue |
| Table head | cool | heavy rule, blue caps |
| Table rows | alternating cool | hairline |
| Code and figures | stock | 2.5px blue |

Section openers carry a filled numeral chip, `h3` and the small-caps labels are
blue, inline `code` is blue, and bold is deep navy, so body text is not one ink.

Colour is semantic, never decorative. `engine/build.py` also inks ASCII figures
by role, so a diagram is read by shape before it is read by word: box drawing
recedes to `--wire`, flow arrowheads advance to `--arrow`, block-fill characters
(bars, meters) take `--bar`, ALL-CAPS node labels take full ink, `✓` and `✗`
carry the verdict, and everything after a `←` drops to pencil as a margin note.

## No alpha, anywhere

An `rgba()` fill, an SVG `opacity`, a `transparent` gradient stop or an emoji
all make Chrome emit a PDF **soft mask** or **transparency group**. A page
carrying one is rasterised rather than drawn as vectors by most tablet note
apps and several viewers, which is what "the PDF looks soft" turns out to be.

So every translucent thing in this design is composited at build time instead:

| Was | Now |
|---|---|
| `--wash-*: rgba(r,g,b,a)` | The same colour pre-blended over white paper |
| SVG `opacity="0.55"` | `sketch.solid(colour, 0.55)`, an opaque hex |
| `linear-gradient(180deg,transparent 9%,...)` | `var(--paper)` in place of `transparent` |
| An emoji in a figure | A glyph from the figure set, or plain text |

Recompute a blend with `round(c * a + 255 * (1 - a))` per channel, or call
`engine/sketch.solid()`.

`build.sh` asserts on every PDF it produces and fails if a soft mask or a
transparency group appears, so this cannot silently regress. `engine/lint.py`
rejects emoji in book source for the same reason, and because house style bans
them anyway.

## Layout notes

Two Chrome print behaviours are worked around deliberately, both commented in
`engine/theme.css`:

- An element that `break-inside: avoid` pushes to a new page is rendered 0.207in
  above the content box, and a block at the foot of a page may spill about as
  far below it. Both strips fall inside the header/footer margin bands, so
  neither template paints the 0.22in nearest the text and a fixed `.paper`
  backdrop supplies it instead. Content landing there stays visible rather than
  vanishing under an opaque bar.
- A heading landing in the last millimetres of a page gets fragmented despite
  `break-inside: avoid`, which is one more reason every section starts fresh.

Code blocks are measured at build time and scaled to the widest line, so column
width changes between editions never clip a diagram.
