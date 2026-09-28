"""Interactive charts for posts, in the style of the Jev Field Guide.

A chart is described here, in a post's figures.py, and drawn in the browser by
_extensions/chartkit (hand-written SVG with tooltips, redrawn on resize, colors
from the site's CSS variables so dark mode needs nothing). `figkit build`
writes each chart to posts/<slug>/assets/charts/<name>.json, and the post
shows it with {{< chart name >}}.

    from figkit import Axis, LineChart, Series, Table

    FIGURES = [
        LineChart(
            "relu-vs-swish",
            title="ReLU against Swish",
            alt="...",
            x=Axis((-4, 4), ticks=[-4, -2, 0, 2, 4], title="Input x"),
            y=Axis((-1, 4), ticks=[-1, 0, 1, 2, 3, 4]),
            series=[Series("ReLU", points, color="person"), Series("Swish", points2, label="Swish")],
        ),
    ]

Colors are roles, not values: 1 (blue), 2 (orange), 3 (green) and "person"
(the gray of a reference or baseline series).

Every chart needs a title and alt text, and carries a data table ("Show the
numbers") that is the accessible version of the chart and what Medium and
Substack get instead of the drawing. Tables are built from the data unless
one is given; keep them short, since they are part of the page.
"""

import json
import math
from dataclasses import dataclass, field

COLORS = (1, 2, 3, "person")


def _round(value, digits):
    if value is None:
        return None
    if isinstance(value, (bool, int)):
        return value
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"chart values must be finite numbers, got {value}")
    rounded = round(value, digits)
    return 0.0 if rounded == 0 else rounded


def _color(color):
    if color not in COLORS:
        raise ValueError(f"chart color must be one of {COLORS}, got {color!r}")
    return color


def _drop_none(data):
    return {key: value for key, value in data.items() if value is not None and not (isinstance(value, (list, dict)) and not value)}


@dataclass
class Format:
    """How numbers are printed on axes and in tooltips: 1.5k, +0.25, 83%."""

    decimals: int = 0
    prefix: str = ""
    suffix: str = ""
    signed: bool = False
    thousands: bool = False
    trim: bool = False  # drop trailing zeros: 1.8 and 0.025 with decimals=3

    def spec(self):
        return _drop_none({
            "decimals": self.decimals,
            "prefix": self.prefix or None,
            "suffix": self.suffix or None,
            "signed": self.signed or None,
            "thousands": self.thousands or None,
            "trim": self.trim or None,
        })

    def __call__(self, value):
        if value is None:
            return ""
        v = abs(value)
        unit = ""
        if self.thousands and v >= 1000:
            v, unit = v / 1000, "k"
        text = f"{v:,.{self.decimals}f}"
        if self.trim and "." in text:
            text = text.rstrip("0").rstrip(".")
        sign = "" if float(text.replace(",", "")) == 0 else ("−" if value < 0 else ("+" if self.signed else ""))
        return f"{sign}{self.prefix}{text}{unit}{self.suffix}"


@dataclass
class Axis:
    domain: tuple
    ticks: list | None = None
    title: str | None = None
    name: str | None = None  # how tooltips name the value (defaults to the title)
    format: Format = field(default_factory=Format)  # tooltips and the data table
    tick_format: Format | None = None  # tick labels, when they need fewer decimals
    log: bool = False

    def spec(self):
        return _drop_none({
            "domain": [_round(v, 6) for v in self.domain],
            "ticks": [_round(v, 6) for v in self.ticks] if self.ticks is not None else None,
            "title": self.title,
            "name": self.name,
            "format": self.format.spec(),
            "tickFormat": self.tick_format.spec() if self.tick_format else None,
            "log": self.log or None,
        })


@dataclass
class Series:
    """A line: points are (x, y) pairs; None (or y None) breaks the line."""

    name: str
    points: list
    color: object = 1
    width: float | None = None
    dash: bool = False
    label: str | None = None  # direct label at the right end of the line
    dots: bool = False
    intervals: list | None = None  # (low, high) per point, drawn as whiskers

    def spec(self, digits):
        points = [None if p is None else [_round(p[0], digits), _round(p[1], digits)] for p in self.points]
        intervals = None
        if self.intervals is not None:
            intervals = [None if iv is None else [_round(iv[0], digits), _round(iv[1], digits)] for iv in self.intervals]
        return _drop_none({
            "name": self.name,
            "color": _color(self.color),
            "points": points,
            "width": self.width,
            "dash": self.dash or None,
            "label": self.label,
            "dots": self.dots or None,
            "intervals": intervals,
        })


@dataclass
class Bars:
    """One bar per category, for a BarChart."""

    name: str
    values: list
    color: object = 1

    def spec(self, digits):
        return {"name": self.name, "color": _color(self.color), "values": [_round(v, digits) for v in self.values]}


@dataclass
class Row:
    """One row of a DotChart: a value with an optional interval, or two values."""

    label: str
    value: float
    lo: float | None = None
    hi: float | None = None
    value2: float | None = None
    group: str | None = None
    color: object = 1
    color2: object = 2

    def spec(self, digits):
        return _drop_none({
            "group": self.group,
            "label": self.label,
            "value": _round(self.value, digits),
            "lo": _round(self.lo, digits),
            "hi": _round(self.hi, digits),
            "value2": _round(self.value2, digits),
            "color": _color(self.color),
            "color2": _color(self.color2) if self.value2 is not None else None,
        })


@dataclass
class Band:
    """A shaded x range, like the guide's "flat up to ~100"."""

    x: tuple
    label: str | None = None

    def spec(self):
        return _drop_none({"x": [_round(v, 6) for v in self.x], "label": self.label})


@dataclass
class Ref:
    """A dashed reference line at x or at y."""

    x: float | None = None
    y: float | None = None
    label: str | None = None
    strong: bool = False

    def spec(self):
        return _drop_none({"x": _round(self.x, 6), "y": _round(self.y, 6), "label": self.label, "strong": self.strong or None})


@dataclass
class Note:
    """A text label at a data point (dx, dy in pixels)."""

    text: str
    x: float
    y: float
    anchor: str = "start"
    dx: float = 0
    dy: float = 0

    def spec(self):
        return _drop_none({
            "text": self.text, "x": _round(self.x, 6), "y": _round(self.y, 6), "anchor": self.anchor,
            "dx": _round(self.dx, 2) or None, "dy": _round(self.dy, 2) or None,
        })


@dataclass
class Table:
    columns: list
    rows: list
    numeric: list | None = None  # per column: right-align as numbers
    summary: str = "Show the numbers"

    def spec(self):
        numeric = self.numeric if self.numeric is not None else [i > 0 for i in range(len(self.columns))]
        for row in self.rows:
            if len(row) != len(self.columns):
                raise ValueError(f"table row {row} has {len(row)} cells for {len(self.columns)} columns")
        return {
            "columns": list(self.columns),
            "rows": [[str(cell) for cell in row] for row in self.rows],
            "numeric": numeric,
            "summary": self.summary,
        }


class Chart:
    """Fields shared by every chart type."""

    type = None
    legend_kind = "dot"

    def __init__(self, name, *, title, alt, sub=None, kicker="Chart", source=None, height=280, table=None, digits=4):
        if not title:
            raise ValueError(f"chart '{name}' needs a title")
        if not alt:
            raise ValueError(f"chart '{name}' needs alt text")
        self.name = name
        self.title = title
        self.alt = alt
        self.sub = sub
        self.kicker = kicker
        self.source = source
        self.height = height
        self.table = table
        self.digits = digits

    def legend(self):
        return []

    def default_table(self):
        return None

    def body(self):
        return {}

    def spec(self):
        table = self.table or self.default_table()
        return _drop_none({
            "version": 1,
            "name": self.name,
            "type": self.type,
            "kicker": self.kicker,
            "title": self.title,
            "sub": self.sub,
            "alt": self.alt,
            "source": self.source,
            "height": self.height,
            "legend": self.legend(),
            **self.body(),
            "table": table.spec() if table else None,
        })

    def json(self):
        return json.dumps(self.spec(), ensure_ascii=False, separators=(",", ":")) + "\n"


class LineChart(Chart):
    """Lines over a numeric x axis.

    hover="x" shows every series at the x nearest the pointer (a crosshair,
    for dense curves); hover="nearest" shows the one point nearest to it.
    table_x lists the x values the data table shows (all points by default).
    """

    type = "line"

    def __init__(self, name, *, x, y, series, bands=(), refs=(), notes=(), hover="x", table_x=None, **kwargs):
        super().__init__(name, **kwargs)
        self.x, self.y = x, y
        self.series = list(series)
        self.bands, self.refs, self.notes = list(bands), list(refs), list(notes)
        if hover not in ("x", "nearest"):
            raise ValueError("hover must be 'x' or 'nearest'")
        self.hover = hover
        self.table_x = table_x

    def legend(self):
        return [{"name": s.name, "color": s.color, "kind": "dash" if s.dash else ("dot" if s.dots else "line")} for s in self.series]

    def default_table(self):
        xs = self.table_x
        if xs is None:
            xs = sorted({p[0] for s in self.series for p in s.points if p is not None and p[1] is not None})

        def value_at(series, x):
            best = None
            for p in series.points:
                if p is None or p[1] is None:
                    continue
                if best is None or abs(p[0] - x) < abs(best[0] - x):
                    best = p
            return self.y.format(best[1]) if best is not None and math.isclose(best[0], x, abs_tol=1e-9) else "–"

        columns = [self.x.name or self.x.title or "x", *[s.name for s in self.series]]
        rows = [[self.x.format(x), *[value_at(s, x) for s in self.series]] for x in xs]
        return Table(columns, rows)

    def body(self):
        return _drop_none({
            "x": self.x.spec(),
            "y": self.y.spec(),
            "series": [s.spec(self.digits) for s in self.series],
            "bands": [b.spec() for b in self.bands],
            "refs": [r.spec() for r in self.refs],
            "notes": [n.spec() for n in self.notes],
            "hover": self.hover,
        })


class BarChart(Chart):
    """Grouped bars: one group per category, one bar per Bars series."""

    type = "bar"

    def __init__(self, name, *, categories, series, y, x_title=None, refs=(), labels=True, **kwargs):
        kwargs.setdefault("height", 250)
        super().__init__(name, **kwargs)
        self.categories = list(categories)
        self.series = list(series)
        for s in self.series:
            if len(s.values) != len(self.categories):
                raise ValueError(f"chart '{name}': series {s.name} has {len(s.values)} values for {len(self.categories)} categories")
        self.y = y
        self.x_title = x_title
        self.refs = list(refs)
        self.labels = labels

    def legend(self):
        return [{"name": s.name, "color": s.color, "kind": "dot"} for s in self.series] if len(self.series) > 1 else []

    def default_table(self):
        columns = ["", *[s.name for s in self.series]]
        rows = [[cat, *[self.y.format(s.values[i]) for s in self.series]] for i, cat in enumerate(self.categories)]
        return Table(columns, rows)

    def body(self):
        return _drop_none({
            "categories": self.categories,
            "series": [s.spec(self.digits) for s in self.series],
            "y": self.y.spec(),
            "x": {"title": self.x_title} if self.x_title else None,
            "refs": [r.spec() for r in self.refs],
            "labels": None if self.labels else False,
        })


class DotChart(Chart):
    """One row per value, with a 95% interval or a second value (dumbbell)."""

    type = "dot"

    def __init__(self, name, *, rows, x, names=None, refs=(), legend=None, label_width=70, **kwargs):
        super().__init__(name, **kwargs)
        self.rows = list(rows)
        self.x = x
        self.names = names  # the two values of a dumbbell, for tooltips
        self.refs = list(refs)
        self._legend = legend or []
        self.label_width = label_width
        self.height = None  # computed from the rows in the browser

    def legend(self):
        return self._legend

    def default_table(self):
        if any(r.value2 is not None for r in self.rows):
            a, b = self.names or ("Value", "Second value")
            columns = ["", a, b]
            rows = [[" · ".join(filter(None, [r.group, r.label])), self.x.format(r.value), self.x.format(r.value2)] for r in self.rows]
        else:
            columns = ["", "Value", "95% interval"]
            rows = [
                [" · ".join(filter(None, [r.group, r.label])), self.x.format(r.value),
                 f"{self.x.format(r.lo)} to {self.x.format(r.hi)}" if r.lo is not None else "–"]
                for r in self.rows
            ]
        return Table(columns, rows)

    def body(self):
        return _drop_none({
            "rows": [r.spec(self.digits) for r in self.rows],
            "x": self.x.spec(),
            "names": list(self.names) if self.names else None,
            "refs": [r.spec() for r in self.refs],
            "labelWidth": self.label_width,
        })


class Panels(Chart):
    """Small multiples: several charts side by side, sharing one card.

    Each panel is a chart without its own card (its title becomes the panel
    title); the legend and the table are the Panels' own.
    """

    type = "panels"

    def __init__(self, name, *, panels, legend=None, **kwargs):
        super().__init__(name, **kwargs)
        self.panels = list(panels)
        self._legend = legend

    def legend(self):
        if self._legend is not None:
            return self._legend
        seen, items = set(), []
        for panel in self.panels:
            for item in panel.legend():
                if item["name"] not in seen:
                    seen.add(item["name"])
                    items.append(item)
        return items

    def default_table(self):
        columns, rows = None, []
        for panel in self.panels:
            table = panel.table or panel.default_table()
            if table is None:
                continue
            columns = columns or ["Panel", *table.columns]
            rows += [[panel.title, *row] for row in table.rows]
        return Table(columns, rows) if columns else None

    def body(self):
        panels = []
        for panel in self.panels:
            spec = panel.spec()
            for key in ("version", "name", "kicker", "sub", "source", "legend", "table", "alt"):
                spec.pop(key, None)
            panels.append(spec)
        return {"panels": panels}


class Widget(Chart):
    """A custom chart drawn by Chartkit.register(widget, draw) in posts/<slug>/charts.js.

    `data` is passed to the draw function as the spec (spec.data)."""

    type = None

    def __init__(self, name, *, widget, data=None, legend=None, **kwargs):
        super().__init__(name, **kwargs)
        self.widget = widget
        self.data = data or {}
        self._legend = legend or []

    def legend(self):
        return self._legend

    def body(self):
        return {"widget": self.widget, "data": self.data}


CHART_TYPES = (LineChart, BarChart, DotChart, Panels, Widget)
