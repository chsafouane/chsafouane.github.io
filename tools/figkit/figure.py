"""Figure primitives in the style of Jay Alammar's illustrated guides.

A Figure is a fixed-size canvas. Elements are described with roles (a hue
name, a style) instead of colors, and are rendered once per mode, which gives
a light and a dark SVG of the same drawing. Coordinates are in CSS pixels at
the figure's natural width; the page scales the figure down on small screens.

Style rules (see README.md):
  - one hue per concept, used the same way in every figure;
  - pastel fills with a darker stroke of the same hue, dark text on fills;
  - rounded boxes (radius 10), strokes of 1.75px, solid arrowheads;
  - small uppercase gray titles on group frames;
  - Inter for labels, JetBrains Mono for code, tokens and file names.
"""

import math
from dataclasses import dataclass

from .palette import palette
from .text import layout, num

LAYERS = {"frame": 0, "edge": 1, "node": 2, "label": 3}
STROKE = 1.75
RADIUS = 10


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _point(target):
    if isinstance(target, Node):
        return (target.x, target.y)
    return (float(target[0]), float(target[1]))


def _toward(node, point, gap):
    """Point on `node`'s outline in the direction of `point`, pushed out by `gap`."""
    if not isinstance(node, Node):
        return _point(node)
    cx, cy = node.x, node.y
    dx, dy = point[0] - cx, point[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    distance = math.hypot(dx, dy)
    ux, uy = dx / distance, dy / distance
    if node.shape == "circle":
        r = node.w / 2 + gap
        return (cx + ux * r, cy + uy * r)
    half_w, half_h = node.w / 2 + gap, node.h / 2 + gap
    scale = min(half_w / abs(ux) if ux else math.inf, half_h / abs(uy) if uy else math.inf)
    return (cx + ux * scale, cy + uy * scale)


def _rounded_polyline(points, radius):
    """SVG path through `points`, rounding interior corners."""
    if len(points) == 2 or radius <= 0:
        return "M" + " L".join(f"{num(x)} {num(y)}" for x, y in points)
    d = [f"M{num(points[0][0])} {num(points[0][1])}"]
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]
        l1, l2 = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
        r = min(radius, l1 / 2, l2 / 2)
        ax, ay = x1 - (x1 - x0) / l1 * r, y1 - (y1 - y0) / l1 * r
        bx, by = x1 + (x2 - x1) / l2 * r, y1 + (y2 - y1) / l2 * r
        d.append(f"L{num(ax)} {num(ay)} Q{num(x1)} {num(y1)} {num(bx)} {num(by)}")
    d.append(f"L{num(points[-1][0])} {num(points[-1][1])}")
    return " ".join(d)


def _color(p, role):
    """Resolve a text/line color role for palette `p`."""
    if role in (None, "text"):
        return p.text
    if role == "muted":
        return p.muted
    if role == "edge":
        return p.edge
    if role == "soft":
        return p.edge_soft
    return p.hue(role).label


# ---------------------------------------------------------------------------
# Elements
# ---------------------------------------------------------------------------


@dataclass
class Node:
    """A labeled shape. (x, y) is its center; w and h its size."""

    label: str
    x: float
    y: float
    w: float
    h: float
    hue: str = "neutral"
    style: str = "solid"  # solid, strong, outline, filled, muted, ghost
    shape: str = "box"    # box, circle, pill
    size: float = 14
    weight: int = 500
    family: str = "sans"
    radius: float = RADIUS
    text_color: str | None = None

    @property
    def left(self):
        return self.x - self.w / 2

    @property
    def right(self):
        return self.x + self.w / 2

    @property
    def top(self):
        return self.y - self.h / 2

    @property
    def bottom(self):
        return self.y + self.h / 2

    def render(self, p, defs):
        shape, text = self._shape(p)
        block = layout(self.label, self.size, self.family, self.weight)
        return shape + block.svg(self.x, self.y - block.height / 2, text, defs)

    def _shape(self, p):
        """SVG of the outline and fill, plus the text color that goes on it."""
        hue = p.hue(self.hue)
        fill, stroke, text, width, dash = hue.fill, hue.stroke, p.text, STROKE, None
        if self.style == "strong":
            width = STROKE * 1.7
        elif self.style == "outline":
            fill, text = "none", hue.label
        elif self.style == "filled":
            fill, stroke, text = hue.solid, "none", hue.on_solid
        elif self.style == "muted":
            fill, stroke, text, dash = "none", p.edge_soft, p.muted, "5 4"
        elif self.style == "ghost":
            fill, stroke = p.frame_fill, p.frame_stroke
        elif self.style != "solid":
            raise ValueError(f"unknown node style '{self.style}'")
        if self.text_color:
            text = _color(p, self.text_color)
        stroke_attrs = "" if stroke == "none" else f' stroke="{stroke}" stroke-width="{num(width)}"'
        if dash:
            stroke_attrs += f' stroke-dasharray="{dash}"'
        if self.shape == "circle":
            shape = f'<circle cx="{num(self.x)}" cy="{num(self.y)}" r="{num(self.w / 2)}" fill="{fill}"{stroke_attrs}/>'
        else:
            r = self.h / 2 if self.shape == "pill" else self.radius
            shape = (
                f'<rect x="{num(self.left)}" y="{num(self.top)}" width="{num(self.w)}" height="{num(self.h)}" '
                f'rx="{num(r)}" fill="{fill}"{stroke_attrs}/>'
            )
        return shape, text


CARD_PAD = (16, 14)
CARD_GAP = 6
BODY_SIZE = 12.5


@dataclass
class Card(Node):
    """A box with a bold title, a body text and an optional numbered badge."""

    body: str = ""
    badge: str | None = None
    align: str = "middle"

    def blocks(self):
        title = layout(self.label, self.size, self.family, 600, self.align)
        body = layout(self.body, BODY_SIZE, "sans", 400, self.align, line_height=1.4) if self.body else None
        return title, body

    def render(self, p, defs):
        shape, text = self._shape(p)
        title, body = self.blocks()
        height = title.height + (CARD_GAP + BODY_SIZE * 0.35 + body.height if body else 0)
        top = self.y - height / 2
        x = {"start": self.left + CARD_PAD[0], "middle": self.x, "end": self.right - CARD_PAD[0]}[self.align]
        out = shape + title.svg(x, top, text, defs)
        if body:
            out += body.svg(x, top + title.height + CARD_GAP + BODY_SIZE * 0.35, text, defs)
        if self.badge:
            hue = p.hue(self.hue)
            r = 11
            cx, cy = self.left + 2, self.top + 2
            out += f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{r}" fill="{hue.solid}"/>'
            mark = layout(self.badge, 11.5, "sans", 700)
            out += mark.svg(cx, cy - mark.height / 2, hue.on_solid, defs)
        return out


@dataclass
class Frame:
    x: float
    y: float
    w: float
    h: float
    title: str | None = None
    hue: str | None = None
    dashed: bool = False
    title_align: str = "start"

    def render(self, p, defs):
        if self.hue:
            fill, stroke = p.hue(self.hue).fill, p.frame_stroke
            fill_opacity = ' fill-opacity="0.35"'
        else:
            fill, stroke, fill_opacity = p.frame_fill, p.frame_stroke, ""
        if self.dashed:
            fill, fill_opacity = "none", ""
        dash = ' stroke-dasharray="6 5"' if self.dashed else ""
        out = (
            f'<rect x="{num(self.x)}" y="{num(self.y)}" width="{num(self.w)}" height="{num(self.h)}" rx="14" '
            f'fill="{fill}"{fill_opacity} stroke="{stroke}" stroke-width="1.25"{dash}/>'
        )
        if self.title:
            anchor = {"start": "start", "middle": "middle", "end": "end"}[self.title_align]
            tx = {"start": self.x + 14, "middle": self.x + self.w / 2, "end": self.x + self.w - 14}[anchor]
            block = layout(self.title, 10.5, "sans", 600, anchor, tracking=0.08, upper=True)
            out += block.svg(tx, self.y + 12, p.muted, defs)
        return out


@dataclass
class Line:
    points: list
    color: str = "edge"
    width: float = STROKE
    dashed: bool = False
    head: bool = False
    head_size: float = 9
    bend: float = 0.0
    corner: float = 12

    def render(self, p, defs):
        color = p.hue(self.color).stroke if self.color not in ("edge", "soft", "muted", "text") else _color(p, self.color)
        pts = list(self.points)
        head = ""
        if self.head:
            # Shorten the line so it ends at the back of the arrowhead.
            (x0, y0), (x1, y1) = (self._control() if self.bend else pts[-2]), pts[-1]
            length = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / length, (y1 - y0) / length
            size = self.head_size
            back = (x1 - ux * size, y1 - uy * size)
            left = (back[0] - uy * size * 0.55, back[1] + ux * size * 0.55)
            right = (back[0] + uy * size * 0.55, back[1] - ux * size * 0.55)
            head = (
                f'<path d="M{num(x1)} {num(y1)} L{num(left[0])} {num(left[1])} '
                f'L{num(right[0])} {num(right[1])} Z" fill="{color}"/>'
            )
            pts[-1] = (x1 - ux * size * 0.8, y1 - uy * size * 0.8)
        dash = ' stroke-dasharray="6 5"' if self.dashed else ""
        if self.bend and len(pts) == 2:
            cx, cy = self._control()
            d = f"M{num(pts[0][0])} {num(pts[0][1])} Q{num(cx)} {num(cy)} {num(pts[1][0])} {num(pts[1][1])}"
        else:
            d = _rounded_polyline(pts, self.corner)
        path = (
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{num(self.width)}" '
            f'stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
        return path + head

    def _control(self):
        (x0, y0), (x1, y1) = self.points[0], self.points[-1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        return (mx + nx * self.bend * length, my + ny * self.bend * length)


@dataclass
class Text:
    content: str
    x: float
    y: float
    size: float = 13
    weight: int = 400
    family: str = "sans"
    color: str = "text"
    anchor: str = "middle"
    valign: str = "middle"  # top, middle or baseline
    upper: bool = False
    tracking: float = 0.0
    line_height: float = 1.3
    halo: bool = False

    def render(self, p, defs):
        block = layout(self.content, self.size, self.family, self.weight, self.anchor, self.line_height, self.tracking, self.upper)
        if self.valign == "top":
            top = self.y
        elif self.valign == "baseline":
            top = self.y - block.ascent
        else:
            top = self.y - block.height / 2
        out = ""
        if self.halo:
            left = {"start": self.x, "middle": self.x - block.width / 2, "end": self.x - block.width}[self.anchor]
            out = (
                f'<rect x="{num(left - 5)}" y="{num(top - 4)}" width="{num(block.width + 10)}" '
                f'height="{num(block.height + 8)}" rx="4" fill="{p.page}"/>'
            )
        return out + block.svg(self.x, top, _color(p, self.color), defs)


@dataclass
class Cells:
    """A row of square cells, Jay Alammar's picture of a vector."""

    x: float  # left edge
    y: float  # center line
    count: int
    hue: str
    size: float = 22
    labels: list | None = None
    shades: list | None = None  # optional 0..1 intensity per cell

    def render(self, p, defs):
        hue = p.hue(self.hue)
        out = []
        for i in range(self.count):
            left = self.x + i * self.size
            fill = hue.fill
            if self.shades is not None:
                from .palette import mix

                fill = mix(hue.stroke, hue.fill, max(0.0, min(1.0, self.shades[i])))
            out.append(
                f'<rect x="{num(left)}" y="{num(self.y - self.size / 2)}" width="{num(self.size)}" '
                f'height="{num(self.size)}" fill="{fill}" stroke="{p.edge}" stroke-width="1"/>'
            )
            if self.labels:
                block = layout(str(self.labels[i]), self.size * 0.5, "mono", 500)
                out.append(block.svg(left + self.size / 2, self.y - block.height / 2, p.text, defs))
        return "".join(out)


@dataclass
class Icon:
    kind: str
    x: float
    y: float
    size: float = 16
    hue: str = "red"

    def render(self, p, defs):
        color = p.hue(self.hue).stroke
        s = self.size
        if self.kind == "warning":
            h = s * 0.9
            top = (self.x, self.y - h / 2)
            left = (self.x - s / 2, self.y + h / 2)
            right = (self.x + s / 2, self.y + h / 2)
            tri = f'<path d="M{num(top[0])} {num(top[1])} L{num(right[0])} {num(right[1])} L{num(left[0])} {num(left[1])} Z" fill="{color}" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>'
            bar = f'<rect x="{num(self.x - s * 0.06)}" y="{num(self.y - h * 0.12)}" width="{num(s * 0.12)}" height="{num(h * 0.36)}" rx="{num(s * 0.06)}" fill="{p.page}"/>'
            dot = f'<circle cx="{num(self.x)}" cy="{num(self.y + h * 0.34)}" r="{num(s * 0.075)}" fill="{p.page}"/>'
            return tri + bar + dot
        raise ValueError(f"unknown icon '{self.kind}'")


# ---------------------------------------------------------------------------
# Figure and Stepper
# ---------------------------------------------------------------------------


class Figure:
    """A fixed-size drawing rendered for light and dark mode."""

    def __init__(self, name, width, height, alt):
        if not alt:
            raise ValueError(f"figure '{name}' needs alt text")
        self.name = name
        self.width = width
        self.height = height
        self.alt = alt
        self._items = []

    def _add(self, layer, element):
        self._items.append((LAYERS[layer], len(self._items), element))
        return element

    # Shapes ------------------------------------------------------------------

    def node(self, label, x, y, hue="neutral", style="solid", shape="box", w=None, h=None,
             size=14, weight=500, family="sans", pad=(16, 10), radius=RADIUS, text_color=None, anchor="middle"):
        """A labeled box (or circle / pill) at (x, y), sized to its label.

        `anchor` says which part of the node x refers to: start (left edge),
        middle (center) or end (right edge). y is always the vertical center.
        """
        block = layout(label, size, family, weight)
        if shape == "circle":
            diameter = w or max(block.width, block.height) + 2 * max(pad)
            w = h = diameter
        else:
            w = w or block.width + 2 * pad[0]
            h = h or block.height + 2 * pad[1] + size * 0.35
        x = {"start": x + w / 2, "middle": x, "end": x - w / 2}[anchor]
        return self._add("node", Node(label, x, y, w, h, hue, style, shape, size, weight, family, radius, text_color))

    def card(self, title, body, x, y, w, hue="neutral", style="solid", h=None, badge=None, align="middle",
             anchor="middle", size=14):
        """A box with a bold title and body text (newlines split lines) at (x, y)."""
        card = Card(title, 0, y, w, 0, hue, style, "box", size, 600, "sans", RADIUS, None, body, badge, align)
        t, b = card.blocks()
        card.h = h or t.height + (CARD_GAP + BODY_SIZE * 0.35 + b.height if b else 0) + 2 * CARD_PAD[1] + size * 0.35
        card.x = {"start": x + w / 2, "middle": x, "end": x - w / 2}[anchor]
        return self._add("node", card)

    def chips(self, tokens, x, y, hue="neutral", style="solid", family="mono", size=13, gap=6,
              pad=8, h=28, anchor="middle", weight=500):
        """A row of token chips; returns the chip nodes. (x, y) is the row's anchor."""
        widths = [layout(t, size, family, weight).width + 2 * pad for t in tokens]
        total = sum(widths) + gap * (len(tokens) - 1)
        left = {"start": x, "middle": x - total / 2, "end": x - total}[anchor]
        nodes = []
        for token, width in zip(tokens, widths):
            nodes.append(self.node(token, left + width / 2, y, hue, style, "box", width, h, size, weight, family, radius=6))
            left += width + gap
        return nodes

    def cells(self, x, y, count, hue, size=22, labels=None, shades=None):
        """A vector drawn as a row of square cells, left edge at x, centered on y."""
        return self._add("node", Cells(x, y, count, hue, size, labels, shades))

    def frame(self, x, y, w, h, title=None, hue=None, dashed=False, title_align="start"):
        """A rounded group frame with an optional small uppercase title."""
        return self._add("frame", Frame(x, y, w, h, title, hue, dashed, title_align))

    def frame_around(self, nodes, pad=18, title=None, hue=None, dashed=False, top_extra=None, title_align="start"):
        """A frame fitted around `nodes`, with room for the title."""
        extra = (22 if title else 0) if top_extra is None else top_extra
        left = min(n.left for n in nodes) - pad
        right = max(n.right for n in nodes) + pad
        top = min(n.top for n in nodes) - pad - extra
        bottom = max(n.bottom for n in nodes) + pad
        return self.frame(left, top, right - left, bottom - top, title, hue, dashed, title_align)

    # Lines -------------------------------------------------------------------

    def link(self, a, b, weight="thin", color="edge", dashed=False, bend=0.0):
        """An undirected graph edge between two nodes (or points)."""
        start = _toward(a, _point(b), 0)
        end = _toward(b, _point(a), 0)
        width = {"thin": 1.5, "thick": 3.2}[weight]
        return self._add("edge", Line([start, end], color, width, dashed, False, bend=bend))

    def arrow(self, a, b, label=None, color="edge", via=(), bend=0.0, gap=5, width=STROKE,
              dashed=False, label_side=1, label_at=0.5, label_offset=10, label_color="muted", label_size=12):
        """An arrow from a to b, optionally through `via` points, with a label beside it."""
        via = [tuple(v) for v in via]
        first_target = via[0] if via else _point(b)
        last_source = via[-1] if via else _point(a)
        start = _toward(a, first_target, gap)
        end = _toward(b, last_source, gap)
        points = [start, *via, end]
        line = self._add("edge", Line(points, color, width, dashed, True, bend=bend))
        if label:
            # Place the label beside the segment that contains `label_at`.
            lengths = [math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1]) for i in range(len(points) - 1)]
            target = sum(lengths) * label_at
            for i, length in enumerate(lengths):
                if target <= length or i == len(lengths) - 1:
                    t = target / length if length else 0
                    (x0, y0), (x1, y1) = points[i], points[i + 1]
                    break
                target -= length
            mx, my = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if bend and len(points) == 2:
                cx, cy = line._control()
                mx, my = 0.25 * x0 + 0.5 * cx + 0.25 * x1, 0.25 * y0 + 0.5 * cy + 0.25 * y1
            dx, dy = x1 - x0, y1 - y0
            if abs(dx) < abs(dy):  # vertical-ish segment: label to the side
                anchor = "start" if label_side > 0 else "end"
                self.text(label, mx + label_side * label_offset, my, size=label_size, color=label_color, anchor=anchor, weight=500)
            else:  # horizontal-ish segment: label above or below
                self.text(label, mx, my - label_side * (label_offset + 2), size=label_size, color=label_color, weight=500)
        return line

    # Text and icons ----------------------------------------------------------

    def text(self, content, x, y, size=13, weight=400, family="sans", color="text", anchor="middle",
             valign="middle", upper=False, tracking=0.0, line_height=1.3, halo=False):
        return self._add("label", Text(content, x, y, size, weight, family, color, anchor, valign, upper, tracking, line_height, halo))

    def title(self, content, x, y, anchor="start", color="muted"):
        """A small uppercase gray heading, like the ones on group frames."""
        return self.text(content, x, y, 10.5, 600, "sans", color, anchor, "top", True, 0.08)

    def icon(self, kind, x, y, size=16, hue="red"):
        return self._add("label", Icon(kind, x, y, size, hue))

    # Rendering ---------------------------------------------------------------

    def render(self, mode="light", editable_text=False):
        """SVG of the figure. editable_text keeps labels as <text> (fonts must be installed)."""
        p = palette(mode)
        defs = None if editable_text else {}
        body = "".join(element.render(p, defs) for _, _, element in sorted(self._items, key=lambda i: (i[0], i[1])))
        glyphs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in sorted((defs or {}).items()))
        alt = (self.alt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(self.width)}" height="{num(self.height)}" '
            f'viewBox="0 0 {num(self.width)} {num(self.height)}" role="img" aria-label="{alt}">'
            f"<title>{alt}</title><defs>{glyphs}</defs>{body}</svg>\n"
        )


class Stepper:
    """A figure shown in steps. `draw(fig, step)` draws step 1..n on a fresh canvas."""

    def __init__(self, name, width, height, alt, captions, draw):
        if len(captions) < 2:
            raise ValueError(f"stepper '{name}' needs at least two steps")
        self.name = name
        self.width = width
        self.height = height
        self.alt = alt
        self.captions = list(captions)
        self.draw = draw

    def frames(self):
        for step, caption in enumerate(self.captions, start=1):
            fig = Figure(f"{self.name}-{step}", self.width, self.height, f"{self.alt} Step {step}: {caption}")
            self.draw(fig, step)
            yield fig
