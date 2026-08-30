#!/usr/bin/env bash
# Build the study notebooks.
#
#   bash build.sh                          every book, Reading edition
#   bash build.sh object-storage           one book, Reading edition
#   bash build.sh object-storage tablet    one book, one named edition
#   bash build.sh all                      every book, every edition
#
# books/<book>.md -> html/<book>-<edition>.html -> pdf/<NN-slug>/<Stem>-<Edition>.pdf
#
# Only the Reading edition builds by default. Print and Tablet are a third of
# the wall clock each and are not being read right now; name one to get it.
#
# Adding a book is one line in BOOKS below plus the markdown file. Nothing
# else in this repo needs to know about it.
set -e
cd "$(dirname "$0")"

# slug | source | title | running head | notebook number | output stem
BOOKS=(
  # add one line per book. nothing else needs to know about it.
)

# The question bank is not written, it is collected: every :::ask, :::recall
# and :::redraw in the notebooks above, gathered so they can be worked cold.
# It regenerates on every build, so editing a notebook is the only way to
# change it.
QUESTION_BANK="questions|books/question-bank.md|Question Bank|QUESTION BANK|00|Question-Bank"

# The template. It exercises every directive and mark, so building it is also
# the smoke test for the engine. It is kept out of the question bank, because
# its prompts are examples rather than material.
EXAMPLE="example|books/example.md|Example Book|EXAMPLE BOOK|XX|Example-Book"

EDITIONS="study tablet clean"

# Arguments may name a book, an edition, or one of each, in either order.
# Naming no edition builds Reading only; `all` builds the three.
ONLY_BOOK=""; ONLY_ED="clean"
for arg in "$@"; do
  case " $EDITIONS " in *" $arg "*) ONLY_ED="$arg"; continue ;; esac
  [ "$arg" = "all" ] && { ONLY_ED=""; continue; }
  ONLY_BOOK="$arg"
done

mkdir -p html

SOURCES=(); SPECS=()
for spec in "${BOOKS[@]}"; do
  IFS='|' read -r _ src title _ num _ <<< "$spec"
  SOURCES+=("$src"); SPECS+=("$num|$title|$src")
done
# A fresh copy of this pipeline has no books yet, and a question bank
# collected from nothing is not a document. Skip it until there is something
# to collect from.
if [ ${#SPECS[@]} -gt 0 ]; then
  python3 engine/questions.py books/question-bank.md "${SPECS[@]}"
  BOOKS+=("$QUESTION_BANK")
  SOURCES+=("books/question-bank.md")
fi
BOOKS+=("$EXAMPLE")
SOURCES+=("books/example.md")

# Lint before rendering. Every check exists because the defect it catches
# reached a printed page once.
python3 engine/lint.py "${SOURCES[@]}"

MT=0.56            # top margin band, inches
MB=0.60            # bottom margin band, inches
DEAD=0.22in        # strip of each band Chrome can spill content into

# Chrome renders these into the page margins, so they repeat on every page and
# carry the only real page numbers available to us. Neither template paints the
# DEAD strip nearest the text: Chrome puts pushed and overflowing blocks there,
# and the page's own .paper backdrop covers it instead. See engine/theme.css.

header_tpl () {          # $1 = rail offset from right edge ("" for none)
                         # $2 = right inset of the measure
                         # $3 = running head  $4 = notebook number
  local rail_div=""
  [ -n "$1" ] && rail_div="<div style='position:absolute;top:0;bottom:0;right:$1;border-left:.6px solid #d8e2dc;'></div>"
  cat <<HTML
<div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;
            position:relative;width:100%;height:100%;margin:0;
            font-family:'SF Mono',Menlo,monospace;color:#778da9;">
  <div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;
              position:absolute;top:0;left:0;right:0;bottom:$DEAD;
              background:#FFFFFF;"></div>
  $rail_div
  <div style="position:absolute;left:20mm;right:$2;top:2.4mm;
              font-size:5.9pt;letter-spacing:2.6px;">
    $3
    <span style="color:#d8e2dc;">&nbsp;/&nbsp;</span>
    STUDY NOTEBOOK $4
  </div>
  <div style="position:absolute;left:20mm;right:$2;top:6.1mm;
              border-bottom:.5px solid #d8e2dc;"></div>
</div>
HTML
}

footer_tpl () {          # same arguments
  local rail_div=""
  [ -n "$1" ] && rail_div="<div style='position:absolute;top:$DEAD;bottom:0;right:$1;border-left:.6px solid #d8e2dc;'></div>"
  cat <<HTML
<div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;
            position:relative;width:100%;height:100%;margin:0;
            font-family:'SF Mono',Menlo,monospace;color:#778da9;">
  <div style="-webkit-print-color-adjust:exact;print-color-adjust:exact;
              position:absolute;top:$DEAD;left:0;right:0;bottom:0;
              background:#FFFFFF;"></div>
  $rail_div
  <div style="position:absolute;left:20mm;right:$2;bottom:3.4mm;
              display:flex;align-items:baseline;gap:9px;">
    <span style="font-size:5.6pt;letter-spacing:2.2px;white-space:nowrap;">
      QUESTIONS I STILL HAVE
    </span>
    <span style="flex:1;border-bottom:.5px solid #d8e2dc;"></span>
  </div>
  <div style="position:absolute;right:7mm;bottom:3.1mm;
              font-size:7.6pt;font-weight:700;color:#415a77;">
    <span class="pageNumber"></span>
  </div>
</div>
HTML
}

# Paper is given PORTRAIT and the landscape flag rotates it. A4 for the two
# portrait editions; the tablet edition uses 6.576 x 11.69in, which rotates to
# 11.69 x 6.576in, exactly 16:9 so it fills a landscape tablet screen with no
# letterboxing.
A4W=8.27;    A4H=11.69
T169W=6.576; T169H=11.69

build () {   # $1 layout  $2 outfile  $3 orientation  $4 rail offset
             # $5 measure inset  $6 paper width  $7 paper height (portrait, in)
  [ -n "$ONLY_ED" ] && [ "$ONLY_ED" != "$1" ] && return 0
  python3 engine/build.py "$SRC" "html/$SLUG-$1.html" "$TITLE" "$1" >/dev/null
  python3 engine/pdf.py "html/$SLUG-$1.html" "$OUT/$2" \
          "$(header_tpl "$4" "$5" "$RUNHEAD" "$NUM")" \
          "$(footer_tpl "$4" "$5")" "$3" "$MT" "$MB" "$6" "$7"
  # Assert on the artifact, not on the source. An rgba() fill, an SVG opacity
  # or a `transparent` gradient stop all make Chrome emit a PDF soft mask, and
  # a page carrying one is rasterised rather than drawn by most tablet note
  # apps. Checking the PDF catches every cause, including ones not thought of.
  python3 - "$OUT/$2" <<'ALPHA'
import sys
d = open(sys.argv[1], "rb").read()
n, g = d.count(b"/SMask"), d.count(b"/Group")
if n or g:
    sys.exit(f"\n  {sys.argv[1]}: {n} soft masks, {g} transparency groups.\n"
             "  Something in the styling uses alpha: an rgba() fill, an SVG\n"
             "  opacity, a `transparent` gradient stop, or an emoji (a colour\n"
             "  bitmap glyph). Pages carrying these get rasterised by tablet\n"
             "  note apps instead of drawn as vectors.\n"
             "  See the comment beside --wash-cool in engine/theme.css.")
ALPHA
  printf '  %-52s %s\n' "$OUT/$2" "$(du -h "$OUT/$2" | cut -f1)"
}

for spec in "${BOOKS[@]}"; do
  IFS='|' read -r SLUG SRC TITLE RUNHEAD NUM STEM <<< "$spec"
  [ -n "$ONLY_BOOK" ] && [ "$ONLY_BOOK" != "$SLUG" ] && continue
  OUT="pdf/$NUM-$SLUG"; mkdir -p "$OUT"
  echo "Building $TITLE..."
  build study  "$STEM-Print.pdf"    portrait  52mm 60mm "$A4W" "$A4H"
  build tablet "$STEM-Tablet.pdf"   landscape 84mm 92mm "$T169W" "$T169H"
  build clean  "$STEM-Reading.pdf"  portrait  ""   20mm "$A4W" "$A4H"
done
echo "Done."
