:::title A one-page prompt goes here. It is the first thing the reader sees, and it should ask them for something before they start reading.
Study Notebook / XX
Example Book
Every directive and mark in one place, as a working template
Copy this file, delete the prose, keep the shapes.
:::

## How to use this file

This is a template, not a book. It exercises every directive and every inline
mark the pipeline understands, so you can see each one rendered and copy the
syntax. Build it and read the PDF beside this source.

Delete everything and start writing, or keep the section skeleton and replace
the prose.

:::key
The format is a study manual, not a system design template. ==The subject does
not matter.== A language, a paper, a codebase, DSA, a certification syllabus:
if it is something you want to remember under pressure, the shapes here work.
:::

:::toc
:::

:::part I | The shapes
Part dividers get their own page and take a short blurb. Sections belonging to
the part are listed automatically underneath it.
:::

## 1. The five annotation blocks

Each one has a job. Using them for anything else costs you the distinction.

:::ask A question the reader should expect to be asked
The body is the answer. In the Question Bank these become numbered prompts with
the answer at the back, so write the body as something you would actually say
out loud.
:::

:::signal What separates a senior answer from a correct one
Usually one sentence. If you find yourself writing a paragraph here, the point
is somewhere inside it and the rest is padding.
:::

:::trap A plausible answer that is wrong
!!State the wrong thing first!!, in the reader's own voice, then say why. A trap
that opens with the correction is just a "do this" block with extra steps.
:::

:::do The concrete practice
- ++Written as an instruction++, in the form you would apply it.
- Bullets are fine here. Prose is fine too.
:::

:::key
The one thing to carry away from the section. ==One per section at most.== If
everything is a key idea, nothing is.
:::

## 2. Glossing a term

A reader who has to leave the page to look a word up has been failed by the
page. Gloss it where it first appears.

:::term Idempotent
An operation that produces the same result whether it runs once or five times.
Deleting a row by ID is idempotent; incrementing a counter is not. It matters
wherever something can be retried, which is anywhere there is a network.
:::

Every `:::term` in a book is collected into the generated glossary in Appendix
A, alphabetically, each entry linking back to the page where it was defined. You
write the definition once, at the point of need.

## 3. Marks

Four highlighters, which are fields of colour:

- `==x==` peach, ==the sentence to carry away==
- `!!x!!` rose, !!the wrong answer, the thing that bites!!
- `++x++` mint, ++the correct practice++
- `%%x%%` pink, a %%definition%% at the point it is first defined

Four pen marks, which are strokes drawn over the words:

- `__x__` blue underline, __the phrase the sentence turns on__
- `((x))` warm circle, ((the loudest mark)), two to five words only
- `[[x]]` blue box, for a [[term]] you will use again
- `~~x~~` pencil strike, ~~what was true and is not any more~~

++Three or four marks on a page.++ A page with ten marks has none, because
nothing stands out from anything else.

## 4. Code, diagrams and tables

Fenced blocks tagged with a language get light syntax colouring:

```sql
SELECT p.id, p.title, u.name
FROM posts p JOIN users u ON u.id = p.author_id
WHERE p.published_at > now() - interval '7 days'
ORDER BY p.published_at DESC
LIMIT 20;
```

Blocks tagged `text` keep ASCII exactly as written and are inked by role: box
drawing recedes, arrowheads advance, ALL-CAPS labels take full ink, and anything
after a left arrow drops to pencil.

```text
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  CLIENT  │ ─────▶ │   API    │ ─────▶ │ DATABASE │
  └──────────┘        └──────────┘        └──────────┘
                           │
                           └──▶ CACHE      ← check here first
```

Marks do not work inside a fence. Use ALL CAPS or a left-arrow annotation.

| Column | What it holds |
|---|---|
| Left | Table heads are tinted, rows alternate |
| Right | Keep tables narrow; the column is not wide |

## 5. A hand-drawn figure

Figures live in `books/figures/<book>.py` as a `FIGURES` dict of name to SVG,
built with `engine/sketch.py`. The markdown only names the one it wants.

:::figure request-path
The caption is set in the reader's hand. Say what the figure is arguing, not
what it contains: a reader can see what it contains.
:::

++Draw the figures that carry the book, not all of them.++ A sketched figure
costs a few iterations to stop labels colliding; an ASCII one costs nothing. Six
to eight per book is the right budget.

## 6. Recall and redraw

A recall rule is a prompt with ruled lines. The number after the pipe is how
many lines.

:::recall Name the five annotation blocks and say what each one is for. | 5
:::

A redraw plate is a full dot-grid page. The text after the pipe is a hint.

:::redraw Draw the request path from memory. | Client, API, database, cache. Then mark where you would measure.
:::

:::part II | Appendices
The generated glossary, and anything else you want at the back.
:::

## Appendix A. Glossary

:::glossary
:::
