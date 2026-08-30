"""Figures for the example book. One drawing, showing the pattern.

Copy this file to books/figures/<your-book>.py and replace the contents. The
filename must match the book's markdown filename, because engine/build.py finds
it by name and nothing else.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "engine"))
import sketch as S


def request_path():
    p = [S.node(30, 40, 150, 62, "Client", ["browser"], fill="stock"),
         S.node(275, 40, 150, 62, "API", ["your code"], fill="mint"),
         S.node(520, 40, 150, 62, "Database", ["postgres"], fill="peach")]
    p.append(S.arrow(180, 71, 271, 71, "blue", 1.5))
    p.append(S.arrow(425, 71, 516, 71, "blue", 1.5))
    p.append(S.text(226, 32, "5 ms", size=12, colour="pencil",
                    hand="mono", anchor="middle"))
    p.append(S.text(471, 32, "40 ms", size=12, colour="pencil",
                    hand="mono", anchor="middle"))
    p.append(S.circle(595, 71, 60, "warm", 1.7, ry=34))
    p.append(S.text(350, 150, "the ring is where the time went",
                    size=17, colour="warm", hand="hand", anchor="middle"))
    return S.svg(700, 166, "".join(p))


FIGURES = {
    "request-path": request_path(),
}
