"""Matplotlib plots in the site style, saved exactly like figkit figures.

A Plot calls your `draw(fig, p)` once per mode with matplotlib configured for
that mode (palette colors, Inter, transparent background, text as paths), so
plots get the same light/dark SVG, PNG and manifest as drawn figures and are
shown with the same {{< fig >}} shortcode.

Needs the optional dependencies: uv sync --extra plots
"""

from functools import lru_cache
from io import StringIO
from pathlib import Path

from fontTools.ttLib import TTFont

from .palette import palette
from .text import FONT_DIR, FONT_FILES

SERIES_HUES = ["indigo", "orange", "green", "pink", "blue", "teal", "amber", "red"]
DPI = 96  # 1 inch = 96 CSS pixels, so figure sizes match drawn figures


@lru_cache(maxsize=None)
def _register_fonts():
    """Matplotlib cannot read WOFF2: convert the site fonts to TTF once."""
    from matplotlib import font_manager

    cache = Path.home() / ".cache" / "figkit" / "fonts"
    cache.mkdir(parents=True, exist_ok=True)
    for stem in FONT_FILES.values():
        target = cache / f"{stem}.ttf"
        if not target.exists():
            font = TTFont(FONT_DIR / f"{stem}.woff2")
            font.flavor = None
            font.save(target)
        font_manager.fontManager.addfont(str(target))


def rc(mode="light"):
    """Matplotlib rcParams for one mode."""
    from cycler import cycler

    p = palette(mode)
    return {
        "font.family": "Inter",
        "font.size": 11,
        "font.weight": 500,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Inter",
        "mathtext.it": "Inter:italic",
        "text.color": p.text,
        "axes.labelcolor": p.muted,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "axes.titleweight": 600,
        "axes.titlecolor": p.text,
        "axes.titlelocation": "left",
        "axes.edgecolor": p.edge,
        "axes.linewidth": 1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.facecolor": "none",
        "axes.prop_cycle": cycler(color=[p.hue(h).stroke for h in SERIES_HUES]),
        "grid.color": p.frame_stroke,
        "grid.linewidth": 0.8,
        "xtick.color": p.muted,
        "ytick.color": p.muted,
        "xtick.labelcolor": p.muted,
        "ytick.labelcolor": p.muted,
        "lines.linewidth": 2.2,
        "lines.solid_capstyle": "round",
        "legend.frameon": False,
        "legend.labelcolor": p.text,
        "figure.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.transparent": True,
        "svg.fonttype": "path",
        "svg.hashsalt": "figkit",  # deterministic ids, so rebuilds give clean diffs
    }


class Plot:
    """A matplotlib figure rendered for light and dark mode.

    draw(fig, p) receives a matplotlib Figure and the palette of the mode;
    use p.hue("indigo").stroke and friends for colors that must stay fixed.
    """

    def __init__(self, name, width, height, alt, draw):
        if not alt:
            raise ValueError(f"plot '{name}' needs alt text")
        self.name = name
        self.width = width
        self.height = height
        self.alt = alt
        self.draw = draw

    def render(self, mode="light"):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        _register_fonts()
        with plt.rc_context(rc(mode)):
            fig = plt.figure(figsize=(self.width / DPI, self.height / DPI), dpi=DPI)
            self.draw(fig, palette(mode))
            buffer = StringIO()
            fig.savefig(buffer, format="svg", metadata={"Date": None, "Creator": None})
            plt.close(fig)
        return buffer.getvalue()
