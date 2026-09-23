"""Figure colors, derived from _brand.yml for light and dark mode.

_brand.yml holds one saturated base color per hue. Every other figure color is
mixed from those bases and the page colors, the same way _theme/theme.scss
derives the site colors, so figures always match the site. Contrast is checked
when the palette loads: strokes need 3:1 against their fill (WCAG 1.4.11) and
text needs 4.5:1 (WCAG 1.4.3).
"""

from dataclasses import dataclass
from functools import lru_cache

import yaml

from .paths import BRAND_FILE

HUES = ["indigo", "green", "blue", "orange", "pink", "teal", "amber", "red"]
MODES = ("light", "dark")


def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, weight):
    """Sass-style mix: `weight` of color `a`, the rest of color `b`."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return "#" + "".join(f"{round(x * weight + y * (1 - weight)):02X}" for x, y in zip(ra, rb))


def luminance(color):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in hex_to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@dataclass(frozen=True)
class Hue:
    fill: str    # pastel fill of shapes
    stroke: str  # outline of shapes, arrows in that hue
    label: str   # colored text on the page background
    solid: str   # saturated fill for emphasized chips
    on_solid: str  # text on the solid fill


@dataclass(frozen=True)
class Palette:
    mode: str
    page: str        # page background (figures are transparent over it)
    text: str        # main text
    muted: str       # secondary text
    edge: str        # neutral lines and arrows
    edge_soft: str   # de-emphasized lines
    frame_fill: str  # group frames
    frame_stroke: str
    neutral: Hue
    hues: dict

    def hue(self, name):
        if name in (None, "neutral", "gray", "grey"):
            return self.neutral
        try:
            return self.hues[name]
        except KeyError:
            raise ValueError(f"unknown hue '{name}', use one of: neutral, {', '.join(HUES)}") from None


def _brand_colors():
    data = yaml.safe_load(BRAND_FILE.read_text())
    palette = data["color"]["palette"]
    return {name: value for name, value in palette.items()}


def _check(label, fg, bg, minimum):
    ratio = contrast(fg, bg)
    if ratio < minimum:
        raise ValueError(f"figure palette: {label} has contrast {ratio:.2f}, needs {minimum}")


@lru_cache(maxsize=None)
def palette(mode="light") -> Palette:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    brand = _brand_colors()
    light = mode == "light"
    page = brand["paper"] if light else brand["night"]
    text = brand["ink"] if light else brand["moon"]
    muted = brand["ink-soft"] if light else brand["moon-soft"]

    hues = {}
    for name in HUES:
        base = brand[name]
        if light:
            hue = Hue(
                fill=mix(base, page, 0.24),
                stroke=mix(base, text, 0.86),
                label=mix(base, text, 0.74),
                solid=mix(base, text, 0.74),
                on_solid=page,
            )
        else:
            hue = Hue(
                fill=mix(base, page, 0.32),
                stroke=mix(base, text, 0.60),
                label=mix(base, text, 0.45),
                solid=mix(base, text, 0.60),
                on_solid=page,
            )
        _check(f"{name} stroke on fill ({mode})", hue.stroke, hue.fill, 3.0)
        _check(f"{name} stroke on page ({mode})", hue.stroke, page, 3.0)
        _check(f"{name} label on page ({mode})", hue.label, page, 4.5)
        _check(f"text on {name} fill ({mode})", text, hue.fill, 4.5)
        _check(f"text on {name} solid ({mode})", hue.on_solid, hue.solid, 4.5)
        hues[name] = hue

    neutral = Hue(
        fill=mix(text, page, 0.07 if light else 0.10),
        stroke=mix(text, page, 0.55),
        label=muted,
        solid=mix(text, page, 0.80),
        on_solid=page,
    )
    result = Palette(
        mode=mode,
        page=page,
        text=text,
        muted=muted,
        edge=mix(text, page, 0.60),
        edge_soft=mix(text, page, 0.30),
        frame_fill=mix(text, page, 0.035 if light else 0.05),
        frame_stroke=mix(text, page, 0.18),
        neutral=neutral,
        hues=hues,
    )
    _check(f"muted text ({mode})", muted, page, 4.5)
    _check(f"edges ({mode})", result.edge, page, 3.0)
    _check(f"text on frames ({mode})", text, result.frame_fill, 4.5)
    return result
