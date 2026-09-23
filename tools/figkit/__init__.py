"""figkit: Jay Alammar-style figures for chsafouane.github.io.

Figures are drawn in code, rendered for light and dark mode as self-contained
SVG files, and exported as PNG (and GIF for steppers) for cross-posting.
See tools/figkit/README.md.
"""

from .figure import Figure, Stepper
from .palette import HUES, palette
from .plots import Plot

__all__ = ["Figure", "Plot", "Stepper", "HUES", "palette"]
