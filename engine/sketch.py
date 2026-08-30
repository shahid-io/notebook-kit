#!/usr/bin/env python3
"""Hand-drawn SVG primitives, generated at build time.

Every stroke is drawn two or three times from slightly different endpoints with
bowed control points, which is what makes a rendered line read as pen rather
than as CSS. Nothing here needs JavaScript or a network: the SVG is static by
the time Chrome sees it.

Randomness is seeded from the shape's own coordinates, so a rebuild produces a
byte-identical figure. A book that redrew itself on every build would be
unreviewable.
"""
import hashlib
import math
import random

PALETTE = {
    "ink":    "#0d1b2a",
    "ink2":   "#1b263b",
    "blue":   "#415a77",
    "pencil": "#778da9",
    "stock":  "#e0e1dd",
    "warm":   "#9d8189",
    "rose":   "#f4acb7",
    "pink":   "#ffcad4",
    "peach":  "#ffe5d9",
    "mint":   "#d8e2dc",
    "rule":   "#d8e2dc",     # same ink as --rule in theme.css
}


def solid(colour, alpha):
    """`colour` composited over white paper, as an opaque hex.

    Drawing a stroke at `opacity="0.55"` makes Chrome emit a PDF transparency
    group and a soft mask. A page carrying soft masks gets rasterised instead
    of drawn by most tablet note apps and several viewers, which is what "the
    figures look soft" actually is. Every figure here sits on white paper, so
    the blend can be done once, at build time, for free.
    """
    h = PALETTE.get(colour, colour).lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise SystemExit(f"sketch.py: unknown colour {colour!r}. "
                         f"Use a palette name ({', '.join(sorted(PALETTE))}) "
                         f"or a #rrggbb value.")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(round(c * alpha + 255 * (1 - alpha))
                                   for c in (r, g, b))


# A figure is drawn in a 700-wide viewBox and then scaled into a ~130mm column,
# so type and stroke inside it shrink by about 5x. These lift both back to the
# weight of the surrounding page. Coordinates are untouched, so layout is
# unaffected.
TYPE_SCALE = 1.42
STROKE_SCALE = 1.5


def _rng(*seed):
    h = hashlib.md5(repr(seed).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def _bow(x1, y1, x2, y2, rough, rnd):
    """One pen stroke: jittered ends, control points pushed off the true line."""
    length = math.hypot(x2 - x1, y2 - y1) or 1
    r = min(rough, length / 12)
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length      # unit normal
    ax, ay = x1 + rnd.uniform(-r, r), y1 + rnd.uniform(-r, r)
    bx, by = x2 + rnd.uniform(-r, r), y2 + rnd.uniform(-r, r)
    off1, off2 = rnd.uniform(-r, r) * 1.7, rnd.uniform(-r, r) * 1.7
    c1x = x1 + (x2 - x1) / 3 + nx * off1
    c1y = y1 + (y2 - y1) / 3 + ny * off1
    c2x = x1 + 2 * (x2 - x1) / 3 + nx * off2
    c2y = y1 + 2 * (y2 - y1) / 3 + ny * off2
    return f"M{ax:.1f} {ay:.1f}C{c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {bx:.1f} {by:.1f}"


# Pass weights, lightest first: the faint stroke is laid down and the strong
# one drawn over it, so the doubled pen line reads the same as it did when
# these were opacity values.
PASS_ALPHA = (0.55, 0.9)


def line(x1, y1, x2, y2, colour="ink", width=1.5, rough=1.5, passes=2):
    rnd = _rng("line", x1, y1, x2, y2)
    order = PASS_ALPHA[-passes:] if passes <= len(PASS_ALPHA) else PASS_ALPHA
    return "".join(
        f'<path d="{_bow(x1, y1, x2, y2, rough, rnd)}" fill="none" '
        f'stroke="{solid(colour, a)}" '
        f'stroke-width="{width * STROKE_SCALE:.2f}" '
        f'stroke-linecap="round"/>'
        for a in order)


def rect(x, y, w, h, colour="ink", width=1.5, rough=1.6, fill=None):
    """Corners overshoot slightly, the way a pen does when you do not lift it."""
    rnd = _rng("rect", x, y, w, h)
    out = []
    if fill:
        out.append(f'<path d="M{x} {y}h{w}v{h}h{-w}z" '
                   f'fill="{solid(fill, 0.5)}"/>')
    o = lambda: rnd.uniform(-rough, rough)
    pts = [(x + o(), y + o()), (x + w + o(), y + o()),
           (x + w + o(), y + h + o()), (x + o(), y + h + o())]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        out.append(line(a[0], a[1], b[0], b[1], colour, width, rough))
    return "".join(out)


def arrow(x1, y1, x2, y2, colour="blue", width=1.6, head=9):
    ang = math.atan2(y2 - y1, x2 - x1)
    out = [line(x1, y1, x2, y2, colour, width, 1.2)]
    for s in (+1, -1):
        a = ang + s * 0.42 + math.pi
        out.append(line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a),
                        colour, width, 0.7, passes=1))
    return "".join(out)


def circle(cx, cy, r, colour="warm", width=1.6, ry=None):
    """An ellipse drawn as one continuous over-rotated loop, like ringing a word.
    `r` sets the horizontal reach; pass `ry` when the thing being ringed is much
    wider than it is tall, which a fixed aspect ratio handles badly."""
    rnd = _rng("circ", cx, cy, r, ry)
    rx, ry = r * 1.25, (ry if ry is not None else r * 0.9)
    pts = []
    for i in range(19):                        # >360 degrees, so the ends cross
        t = i / 18 * math.pi * 2.18 - 0.4
        j = rnd.uniform(-1.4, 1.4)
        pts.append((cx + (rx + j) * math.cos(t),
                    cy + (ry + j) * math.sin(t)))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return (f'<path d="{d}" fill="none" stroke="{solid(colour, 0.85)}" '
            f'stroke-width="{width * STROKE_SCALE:.2f}" '
            f'stroke-linecap="round"/>')


def highlight(x, y, w, colour="peach", height=13):
    """One thick pale swipe, uneven at the ends like a real marker."""
    rnd = _rng("hl", x, y, w)
    y1 = y + rnd.uniform(-1, 1)
    y2 = y + rnd.uniform(-1.5, 1.5)
    return (f'<path d="M{x} {y1:.1f}C{x + w / 3} {y1 - 1.5:.1f} '
            f'{x + 2 * w / 3} {y2 + 1.5:.1f} {x + w} {y2:.1f}" fill="none" '
            f'stroke="{solid(colour, 0.75)}" '
            f'stroke-width="{height * STROKE_SCALE:.2f}" '
            f'stroke-linecap="round"/>')


def text(x, y, s, size=13, colour="ink", hand="hand2", anchor="start", rotate=0):
    fam = {"hand": "Caveat", "hand2": "Patrick Hand",
           "mono": "JetBrains Mono"}.get(hand, hand)
    tr = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
    esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family="{fam}" '
            f'font-size="{size * TYPE_SCALE:.1f}" '
            f'fill="{PALETTE.get(colour, colour)}" text-anchor="{anchor}"{tr}>'
            f"{esc}</text>")


def node(x, y, w, h, label, sub=None, fill=None, colour="ink"):
    """A labelled box: the unit most architecture figures are made of."""
    out = [rect(x, y, w, h, colour, 1.6, 1.6, fill)]
    out.append(text(x + w / 2, y + (20 if sub else h / 2 + 6), label,
                    size=15, colour="ink", hand="hand", anchor="middle"))
    for i, s in enumerate(sub or []):
        out.append(text(x + w / 2, y + 38 + i * 14, s, size=11,
                        colour="pencil", hand="mono", anchor="middle"))
    return "".join(out)


def svg(width, height, body, klass="sketch"):
    return (f'<svg class="{klass}" viewBox="0 0 {width} {height}" '
            f'width="100%" xmlns="http://www.w3.org/2000/svg" '
            f'style="display:block;margin:14px 0;overflow:visible">{body}</svg>')
