"""figkit: Jay Alammar-style figures for chsafouane.github.io.

Figures are drawn in code, rendered for light and dark mode as self-contained
SVG files, and exported as PNG (and GIF for steppers) for cross-posting.
Charts (figkit.charts) are written as JSON specs and drawn in the browser by
_extensions/chartkit. See tools/figkit/README.md.
"""

from .charts import (
    Axis,
    Band,
    BarChart,
    Bars,
    DotChart,
    Format,
    LineChart,
    Note,
    Panels,
    Ref,
    Row,
    Series,
    Table,
    Widget,
)
from .figure import Figure, Stepper
from .palette import HUES, palette
from .plots import Plot

__all__ = [
    "HUES",
    "Axis",
    "Band",
    "BarChart",
    "Bars",
    "DotChart",
    "Figure",
    "Format",
    "LineChart",
    "Note",
    "Panels",
    "Plot",
    "Ref",
    "Row",
    "Series",
    "Stepper",
    "Table",
    "Widget",
    "palette",
]
