# Authoring a notebook

`GETTING-STARTED.md` gets you a built PDF. This is about the harder half: how a
book actually gets written, and why the good ones are good.

Read this before your first book. It will save you a rewrite.

---

## The thing nobody tells you

This repository is a typesetter. It will not write anything.

You will clone it, build the example, feel pleased, open a blank markdown file
and stall. That is the normal experience and it is not a failure of the tooling.
**The hard part was never the PDF.** The hard part is turning four hours of
lecture into a spine, deciding what the book is *about*, and knowing what to add
that the source did not say.

So this document is the workflow, not the syntax.

---

## The loop

```text
  1  source          a lecture, a book, a paper, docs, a codebase
        │
  2  source pack     the raw material, in one file you can read
        │
  3  the question    one sentence. the whole book hangs off it
        │
  4  outline         parts and numbered sections. no prose yet
        │
  5  draft           write it, part by part
        │
  6  figures         six to eight, after the prose is settled
        │
  7  build + read    read the rendered pages, not the markdown
        │
  8  fix and repeat
```

Steps 3 and 4 decide whether the book is any good. Steps 5 to 8 are labour.

---

## 1 and 2. Getting the source into one file

If the source is a YouTube lecture or playlist:

```bash
pip3 install yt-dlp
python3 engine/transcript.py "https://www.youtube.com/watch?v=..." sources
```

One markdown file per video: front matter, then auto-captions merged into
~30 second timestamped paragraphs. Safe to re-run when a playlist grows;
existing files are left alone.

For anything else, put the raw material in `sources/` yourself. The format is
not lecture-specific. A paper, a chapter, an RFC, a runbook, your own scratch
notes from a project all work the same way.

**Read the whole source pack before writing a line.** A lecture's own running
order is usually the right spine, because good lecturers kill a naive design
several times before naming the answer, and that sequence is the pedagogy.

---

## 3. One book, one question

This is the step people skip and it is the one that matters.

A notebook is not a survey of a topic. It is ==one question, asked repeatedly,
pointed at different parts of the subject.== The question goes on the "How to
use this book" page and every part is that question aimed somewhere new.

Worked examples from books built with this pipeline:

| Subject | The question | Why it works |
|---|---|---|
| Backend security | *Where did the developer make an assumption?* | Produces every vulnerability class in turn, instead of a list to memorise |
| Scaling | *Where does the time actually go?* | Every technique becomes "move time somewhere cheaper", so they stop being a menu |
| Code review | *What would you say out loud about this diff?* | Turns knowledge into performance, which is what is actually being tested |

If you cannot write the question in one sentence, you are not ready to outline.
A book without one becomes a glossary with opinions, and it is unmemorable in
exactly the way the source material already was.

> **The test:** does the question generate the sections, or did you write the
> sections and then reverse-engineer a question? Only the first one works.

---

## 4. Outline before prose

Draft the full part and section list before writing a single paragraph. It is
far cheaper to move a section than to rewrite one.

```text
:::part III | The database
## 11. N+1: the shape, not the name
## 12. Indexes: the catalogue, the tree, and the cost
...
```

**Every `##` is a page.** Write to that. If a section will not fit on one page,
it is two sections. If three sections say the same thing, they are one.

Rough scale, from books that came out well: 6 to 10 parts, 40 to 50 numbered
sections, 70 to 100 pages. A 2 to 3 hour lecture is about one book. Do not try
to make a 20 minute talk into 80 pages; you will pad, and padding is obvious.

Sections are numbered contiguously from 1. Appendices are `## Appendix A.` and
run A, B, C. The linter enforces both, which catches the section you deleted and
forgot to renumber.

---

## 5. Write

### What actually adds value

**A transcript in book clothing is worse than the original video.** If the reader
could have got it from the source, you have not written anything. The value is
in what you add:

- **Failure tables.** What breaks, when, and what you do about it. Sources
  describe the happy path; you write down the four ways it goes wrong.
- **The interview framing.** What this gets asked as, what a mid-level answer
  sounds like, what a senior one sounds like. That is the `:::signal` block.
- **Corrections.** Where the source is loose or wrong, say so plainly and give
  the sharper version. This is the single strongest signal that a human read it.
- **Numbers.** Where the source hand-waves, find the formula. "Keep 20% headroom"
  is folklore; `1/(1-u)` is a calculation you can use.
- **Cross-references.** Point at the other notebook that covers it properly
  instead of repeating it badly.

### The blocks, and using them honestly

Five annotation blocks, each with one job:

| Block | For |
|---|---|
| `:::ask` | A question the reader should expect. The body is the answer |
| `:::signal` | The one sentence that reads as senior. Usually one sentence |
| `:::trap` | A plausible answer that is wrong. State the wrong thing first |
| `:::do` | The concrete practice, in the form you would apply it |
| `:::key` | The one thing to carry away. **At most one per section** |

Using them for anything else costs you the distinction. If every block is a key
idea, the reader stops seeing any of them.

### Marks

**Three or four marks on a page.** A page with ten marks has none, because
nothing stands out from anything else. The temptation to highlight everything
you found interesting is the main thing to resist.

`((circle))` two to five words only. It is one hand-authored ellipse stretched
to fit; across a whole sentence it flattens into a line through the text. The
other three marks take any width.

Marks do not work inside a fenced block. Inside an ASCII figure use ALL CAPS,
which takes full ink, or a `←` annotation, which drops to pencil.

### Gloss the words

**A reader who has to open a search tab has been failed by the page.**

```text
:::term Sharding
Splitting one logical table across several physical databases, so that each one
holds a different subset of the rows. Also called horizontal partitioning.
:::
```

Gloss any word the reader might not know, at its first appearance, when the prose
does not already define it in the same breath. Not every noun; the page has a
budget. Put `:::glossary` in an appendix and every term collects there
alphabetically, each linking back to the page it was defined on. You write the
definition once, where it is needed.

---

## 6. Figures, last

Write the prose first. Figures drawn against an unsettled outline get redrawn.

**ASCII first.** A fenced `text` block is free, is inked by role automatically,
and is usually enough. Reach for a drawn figure only when the shape itself is the
argument.

```text
:::figure knee
The caption says what the figure is arguing, not what it contains. A reader can
see what it contains.
:::
```

Figures live in `books/figures/<book>.py`, matched to the book by filename and
nothing else. Build them with `engine/sketch.py`: `node`, `rect`, `line`,
`arrow`, `circle`, `highlight`, `text`.

**Six to eight drawn figures per book.** This is a real budget, not a
suggestion. Every coordinate is a literal, so each figure costs two or three
passes to stop labels landing on boxes: roughly 10 to 20 minutes each. Spend it
on the figures that carry the book.

Randomness is seeded from each shape's own coordinates, so a rebuild is
byte-identical. A book that redrew itself every build would be unreviewable in
git.

---

## 7. Read the rendered pages

```bash
bash build.sh my-book && open pdf/01-my-book/My-Book-Reading.pdf
```

**Read the PDF, not the markdown.** Bugs that are invisible in source are obvious
on the page: a figure label sitting on a box, a section that runs three lines
onto a second page, six blocks in a row with no prose between them, a page with
nine highlights.

To check a figure without opening a viewer:

```bash
pdftoppm -f 13 -l 13 -r 110 -png pdf/01-my-book/My-Book-Reading.pdf /tmp/page
```

### Before calling it done

- [ ] `python3 engine/lint.py books/*.md` is clean
- [ ] Every part has a `:::recall` at its end
- [ ] Every drawn figure has been looked at, at render size
- [ ] No page carries more than four marks
- [ ] The question from step 3 is on the "How to use" page, and every part serves it
- [ ] Sections that could be cut, have been

---

## Writing this with an AI assistant

This is how the existing books were made, and leaving it out would be dishonest
about the effort involved.

The workflow is Claude Code, or any coding agent with filesystem access, pointed
at this repository. What matters is the order you ask for things.

**Give it the repo and the source pack.** It reads `README.md` for the syntax and
`sources/<file>.md` for the material. Do not paste the transcript into a chat
window; let it read the file.

**Ask for the question and the outline first, and stop there.** The single most
common failure is letting it start writing prose immediately. You get 80
competent pages organised as a list of topics, which is exactly the book you did
not want. Review the outline, argue with it, change the question, and only then
say write.

**Ask for what is not in the source, explicitly.** "Where is the lecture loose or
wrong? What would an interviewer ask that it does not answer? What formula is
behind the hand-waving?" Those questions produce the material that makes the book
worth more than the source.

**Write part by part, and read the PDF between parts.** Not all at once. Problems
compound, and finding a structural one at part VIII is expensive.

**Figures last, one at a time, looking at each render.** Label collisions are
invisible in the source and obvious on the page.

**Let the linter be the reviewer.** It catches mismatched marks, markers stranded
in fences, missing figures and numbering gaps. Those are the errors an assistant
actually makes, and having a machine catch them is faster than reading for them.

A realistic figure for a 3 hour lecture turned into a 90 page book: an afternoon
of real work, most of it your judgement on the outline and your eyes on the
rendered pages. Not ten minutes. Considerably less than the two weeks it would
take by hand.

---

## When it is not a lecture

The format is a study manual, not a system design template. The subject does not
matter as long as it is something you need to recall under pressure.

- **A paper.** The question is usually "what did they actually prove, and what did
  everyone else assume they proved?"
- **A codebase you inherited.** "Where would a change be dangerous?" Sections
  become subsystems, figures become real call paths.
- **A certification syllabus.** The question is the exam's own theory of what
  matters, and recall rules do most of the work.
- **A postmortem or a runbook.** "What did we believe that was not true?" These
  are short books, 20 pages, and they are the best possible onboarding document.
