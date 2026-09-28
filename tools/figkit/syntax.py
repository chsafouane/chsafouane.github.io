"""Code highlighting themes (_theme/syntax-light.theme, syntax-dark.theme).

The colors are the hl-* tokens of _brand.yml, mapped onto Pandoc's (KDE)
token names the way the Jev Field Guide maps them onto Pygments classes:
keywords purple, strings green, comments gray and italic, numbers orange,
function names blue, builtins and decorators teal, everything else the text
color. Every color is checked for 4.5:1 contrast on the code background.

  uv run figkit syntax           write both theme files
  uv run figkit syntax --check   fail if the files are not what this writes
"""

import json

from .palette import _brand_colors, contrast
from .paths import REPO

THEME_DIR = REPO / "_theme"

# Pandoc token name -> (brand role, italic, bold)
TOKENS = {
    "Normal": ("text", False, False),
    "Variable": ("text", False, False),
    "Operator": ("text", False, False),
    "Keyword": ("kw", False, False),
    "ControlFlow": ("kw", False, False),
    "Import": ("kw", False, False),
    "Preprocessor": ("kw", False, False),
    "DataType": ("kw", False, False),
    "Constant": ("kw", False, False),
    "Other": ("kw", False, False),
    "String": ("str", False, False),
    "VerbatimString": ("str", False, False),
    "SpecialString": ("str", False, False),
    "Char": ("str", False, False),
    "SpecialChar": ("str", False, False),
    "Documentation": ("str", False, False),
    "Comment": ("com", True, False),
    "CommentVar": ("com", True, False),
    "Annotation": ("com", True, False),
    "Information": ("com", True, False),
    "RegionMarker": ("com", False, False),
    "DecVal": ("num", False, False),
    "BaseN": ("num", False, False),
    "Float": ("num", False, False),
    "Function": ("fn", False, False),
    "BuiltIn": ("bi", False, False),
    "Extension": ("bi", False, False),
    "Attribute": ("bi", False, False),
    "Warning": ("red", False, False),
    "Alert": ("red", False, True),
    "Error": ("red", False, True),
}


def _colors(mode):
    brand = _brand_colors()
    dark = mode == "dark"

    def pick(name):
        return brand[f"{name}-dark"] if dark else brand[name]

    from .palette import mix

    text = brand["moon"] if dark else brand["ink"]
    return {
        "background": pick("code-bg"),
        "text": text,
        "muted": brand["moon-soft"] if dark else brand["ink-soft"],
        "kw": pick("hl-kw"),
        "str": pick("hl-str"),
        "com": pick("hl-com"),
        "num": pick("hl-num"),
        "fn": pick("hl-fn"),
        "bi": pick("hl-bi"),
        # The brand red, moved toward the text color until it reads on code.
        "red": mix(brand["red"], text, 0.5 if dark else 0.9),
    }


def theme(mode):
    colors = _colors(mode)
    background = colors["background"]
    styles = {}
    for token, (role, italic, bold) in TOKENS.items():
        color = colors[role]
        ratio = contrast(color, background)
        if ratio < 4.5:
            raise ValueError(f"syntax {mode}: {token} ({role} {color}) has contrast {ratio:.2f} on {background}, needs 4.5")
        styles[token] = {
            "text-color": color,
            "background-color": None,
            "bold": bold,
            "italic": italic,
            "underline": False,
        }
    return {
        "text-color": colors["text"],
        "background-color": background,
        "line-number-color": colors["muted"],
        "line-number-background-color": None,
        "_comments": [
            "Written by `uv run figkit syntax` (tools/figkit/syntax.py) from the hl-* colors in _brand.yml; do not edit.",
            "Every token color passes WCAG AA (4.5:1) on the code block background.",
        ],
        "text-styles": styles,
    }


def _text(mode):
    return json.dumps(theme(mode), indent=4) + "\n"


def build(check=False):
    stale = []
    for mode in ("light", "dark"):
        path = THEME_DIR / f"syntax-{mode}.theme"
        text = _text(mode)
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(path.relative_to(REPO))
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)}")
    if stale:
        raise SystemExit(f"out of date: {', '.join(map(str, stale))} (run uv run figkit syntax)")
