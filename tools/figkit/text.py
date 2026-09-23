"""Text layout for figures: shape with HarfBuzz, draw glyphs as SVG outlines.

Figures are shown through <img> tags, which cannot use the page's web fonts,
so every label is converted to outlines. The fonts are the site's own files
in assets/fonts, which keeps figures and pages typographically identical.

Each glyph outline is stored once per figure (in font units, inside <defs>)
and placed with <use>, which keeps the SVG files small.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from .paths import REPO

FONT_DIR = REPO / "assets" / "fonts"

# (family, weight) -> file stem in assets/fonts
FONT_FILES = {
    ("sans", 400): "inter-latin-400-normal",
    ("sans", 500): "inter-latin-500-normal",
    ("sans", 600): "inter-latin-600-normal",
    ("sans", 700): "inter-latin-700-normal",
    ("mono", 400): "jetbrains-mono-latin-400-normal",
    ("mono", 500): "jetbrains-mono-latin-500-normal",
    ("serif", 400): "newsreader-latin-400-normal",
    ("serif", 500): "newsreader-latin-500-normal",
}


# CSS family names, used when text stays editable (Keynote components).
CSS_FAMILY = {"sans": "Inter", "mono": "JetBrains Mono", "serif": "Newsreader"}


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def num(value):
    """Compact number formatting for SVG attributes."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


class Face:
    """One font file, ready for shaping and outline extraction."""

    def __init__(self, key, path: Path):
        self.key = f"{key[0]}{key[1]}"
        font = TTFont(path)  # WOFF2 is decompressed by fontTools (brotli)
        font.flavor = None
        buffer = BytesIO()
        font.save(buffer)
        data = buffer.getvalue()
        self.tt = TTFont(BytesIO(data))
        self.glyph_set = self.tt.getGlyphSet()
        self.glyph_order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        os2 = self.tt["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or int(self.upem * 0.7)
        self.x_height = getattr(os2, "sxHeight", 0) or int(self.upem * 0.5)
        self.hb_font = hb.Font(hb.Face(data))
        self._outlines = {}

    def glyph_id(self, glyph):
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", glyph)
        return f"g-{self.key}-{safe}"

    def outline(self, glyph):
        """Path data of a glyph in font units (y up), or '' for blank glyphs."""
        if glyph not in self._outlines:
            pen = SVGPathPen(self.glyph_set, ntos=num)
            self.glyph_set[glyph].draw(pen)
            self._outlines[glyph] = pen.getCommands()
        return self._outlines[glyph]

    def shape(self, text, tracking=0.0):
        """Shape one line. Returns [(glyph name, x, y)] in font units and the advance."""
        if not text:
            return [], 0.0
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self.hb_font, buffer, {"kern": True, "liga": False, "calt": False})
        extra = tracking * self.upem  # tracking is given in em
        x = 0.0
        glyphs = []
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
            if info.codepoint == 0:
                missing = text[info.cluster] if info.cluster < len(text) else "?"
                raise ValueError(f"font {self.key} has no glyph for {missing!r} (U+{ord(missing):04X}) in {text!r}")
            glyphs.append((self.glyph_order[info.codepoint], x + position.x_offset, position.y_offset))
            x += position.x_advance + extra
        if glyphs:
            x -= extra
        return glyphs, x


@lru_cache(maxsize=None)
def face(family="sans", weight=500) -> Face:
    key = (family, weight)
    if key not in FONT_FILES:
        raise ValueError(f"no font file for {key}; available: {sorted(FONT_FILES)}")
    return Face(key, FONT_DIR / f"{FONT_FILES[key]}.woff2")


@dataclass
class TextBlock:
    """A laid-out block of one or more lines, anchored horizontally at a point."""

    face: Face
    size: float
    lines: list  # per line: (glyphs, width, dx) with dx relative to the anchor
    width: float
    height: float  # from the first line's cap height to the last baseline
    line_height: float
    ascent: float  # distance from the block top to the first baseline
    texts: list  # the source text of each line
    tracking: float = 0.0

    def svg(self, x, top, fill, glyph_defs):
        """SVG for the block with its top edge at `top` and anchor at `x`.

        Glyph outlines used by the block are added to `glyph_defs` (id -> path).
        With glyph_defs=None the text stays editable: <text> elements that
        need the fonts installed (used for the Keynote component sheets).
        """
        if glyph_defs is None:
            return self._svg_text(x, top, fill)
        scale = self.size / self.face.upem
        s = f"{scale:.6g}"  # glyph scale needs full precision (14px / 2048 units)
        uses = []
        for index, (glyphs, _width, dx) in enumerate(self.lines):
            baseline = top + self.ascent + index * self.line_height
            for glyph, gx, gy in glyphs:
                outline = self.face.outline(glyph)
                if not outline:
                    continue
                gid = self.face.glyph_id(glyph)
                glyph_defs[gid] = outline
                tx = x + dx + gx * scale
                ty = baseline - gy * scale
                uses.append(f'<use href="#{gid}" transform="translate({num(tx)} {num(ty)}) scale({s} -{s})"/>')
        if not uses:
            return ""
        return f'<g fill="{fill}">{"".join(uses)}</g>'

    def _svg_text(self, x, top, fill):
        family, weight = self.face.key.rstrip("0123456789"), self.face.key.lstrip("abcdefghijklmnopqrstuvwxyz")
        lines = []
        for index, (_glyphs, width, dx) in enumerate(self.lines):
            if not self.texts[index]:
                continue
            baseline = top + self.ascent + index * self.line_height
            spacing = f' letter-spacing="{num(self.tracking * self.size)}"' if self.tracking else ""
            lines.append(
                f'<text x="{num(x + dx)}" y="{num(baseline)}" font-family="{CSS_FAMILY[family]}" '
                f'font-size="{num(self.size)}" font-weight="{weight}"{spacing}>{_escape(self.texts[index])}</text>'
            )
        return f'<g fill="{fill}">{"".join(lines)}</g>' if lines else ""


def layout(text, size=14, family="sans", weight=500, anchor="middle", line_height=1.3, tracking=0.0, upper=False):
    """Lay out `text` (newlines split lines). `anchor` is start, middle or end."""
    f = face(family, weight)
    if upper:
        text = text.upper()
    scale = size / f.upem
    placed = []
    widths = []
    texts = text.split("\n")
    for line in texts:
        glyphs, advance = f.shape(line, tracking)
        width = advance * scale
        widths.append(width)
        dx = {"start": 0.0, "middle": -width / 2, "end": -width}[anchor]
        placed.append((glyphs, width, dx))
    step = size * line_height
    cap = f.cap_height * scale
    height = cap + step * (len(placed) - 1)
    return TextBlock(f, size, placed, max(widths) if widths else 0.0, height, step, cap, texts, tracking)
