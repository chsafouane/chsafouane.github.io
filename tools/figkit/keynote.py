"""Keynote support: a macOS color palette and component sheets.

Hand-drawn figures (Jay Alammar's Keynote workflow) use the same colors,
strokes and fonts as code-drawn ones:

  - figkit.clr: the light-mode figure palette as a macOS color list; installed
    in ~/Library/Colors it shows up in Keynote's color picker as "figkit";
  - components/*.svg: sheets of ready-made pieces (boxes, chips, cells,
    arrows, frames, cards) with editable text. Drag one onto a slide, then
    Format > Shapes and Lines > Break Apart to get native Keynote shapes.

Keynote figures are exported as PNG (or several PNGs for a stepper) and
brought into a post with `figkit import`. They are light-only, so the site
shows them on a white plate in dark mode.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from .figure import Figure
from .palette import HUES, hex_to_rgb, palette
from .paths import REPO

KEYNOTE_DIR = REPO / "tools" / "figkit" / "keynote"


def palette_entries():
    """(name, hex) pairs of the light-mode figure palette, in picker order."""
    p = palette("light")
    entries = [
        ("text", p.text),
        ("muted text", p.muted),
        ("edge", p.edge),
        ("soft edge", p.edge_soft),
        ("frame fill", p.frame_fill),
        ("frame stroke", p.frame_stroke),
        ("neutral fill", p.neutral.fill),
        ("page", p.page),
    ]
    for name in HUES:
        hue = p.hue(name)
        entries += [(f"{name} fill", hue.fill), (f"{name} stroke", hue.stroke), (f"{name} label", hue.label)]
    return entries


def write_palette(path: Path):
    """Write the palette as a macOS .clr color list (uses the system Swift)."""
    swift = shutil.which("swift")
    if swift is None:
        raise SystemExit("writing a .clr color list needs Swift (xcode-select --install)")
    lines = ["import AppKit", 'let list = NSColorList(name: "figkit")']
    for name, color in palette_entries():
        r, g, b = (c / 255 for c in hex_to_rgb(color))
        lines.append(f'list.setColor(NSColor(srgbRed: {r:.6f}, green: {g:.6f}, blue: {b:.6f}, alpha: 1), forKey: "{name}")')
    lines.append(f'try! list.write(to: URL(fileURLWithPath: "{path}"))')
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False) as script:
        script.write("\n".join(lines) + "\n")
    try:
        subprocess.run([swift, script.name], check=True)
    finally:
        Path(script.name).unlink()


def _sheet_nodes():
    fig = Figure("nodes", 720, 330, alt="figkit node components")
    fig.title("Boxes, one per hue", 20, 14)
    for i, hue in enumerate(HUES):
        fig.node(hue, 60 + i * 86, 60, hue=hue, size=13, w=74)
    fig.title("Styles", 20, 100)
    for i, style in enumerate(["solid", "strong", "outline", "filled", "muted", "ghost"]):
        fig.node(style, 70 + i * 106, 146, hue="indigo", style=style, size=13, w=90)
    fig.title("Pills and circles", 20, 190)
    for i, hue in enumerate(HUES[:4]):
        fig.node(f"{hue} pill", 76 + i * 118, 236, hue=hue, shape="pill", size=13, w=104)
    for i, hue in enumerate(HUES[4:]):
        fig.node("A", 520 + i * 50, 236, hue=hue, shape="circle", w=40, size=15, weight=600)
    fig.node("pyproject.toml", 20, 296, hue="blue", family="mono", size=13, anchor="start")
    fig.node("code or file name", 200, 296, style="ghost", family="mono", size=13, weight=400, anchor="start")
    return fig


def _sheet_tokens():
    fig = Figure("tokens", 720, 250, alt="figkit token and vector components")
    fig.title("Token chips", 20, 14)
    fig.chips(["Hello", " there", "!"], 20, 58, hue="teal", anchor="start")
    fig.chips(["15496", "612"], 300, 58, hue="orange", anchor="start")
    fig.title("Vectors as cells", 20, 100)
    for i, hue in enumerate(["green", "indigo", "orange", "blue"]):
        fig.cells(20 + i * 170, 146, 6, hue)
    fig.title("Values and intensities", 20, 180)
    fig.cells(20, 222, 6, "pink", labels=[3, 1, 4, 1, 5, 9])
    fig.cells(200, 222, 6, "blue", shades=[0.1, 0.9, 0.4, 0.2, 0.7, 0.5])
    return fig


def _sheet_lines():
    fig = Figure("lines", 720, 260, alt="figkit arrow and edge components")
    fig.title("Arrows", 20, 14)
    a = fig.node("step", 70, 60, hue="neutral", w=90)
    b = fig.node("step", 280, 60, hue="neutral", w=90)
    fig.arrow(a, b, label="label")
    c = fig.node("step", 420, 60, hue="blue", w=90)
    d = fig.node("step", 640, 60, hue="blue", w=90)
    fig.arrow(c, d, color="blue", width=2.4, label="emphasis", label_color="blue")
    fig.title("Graph edges", 20, 110)
    n1 = fig.node("A", 60, 170, hue="green", shape="circle", w=40, size=15, weight=600)
    n2 = fig.node("B", 200, 170, hue="green", shape="circle", w=40, size=15, weight=600)
    n3 = fig.node("C", 340, 170, hue="blue", shape="circle", w=40, size=15, weight=600)
    fig.link(n1, n2, weight="thick", color="green")
    fig.link(n2, n3)
    n4 = fig.node("D", 480, 170, style="muted", shape="circle", w=40, size=15)
    fig.link(n3, n4, dashed=True, color="soft")
    fig.text("thick: same group · thin: similarity · dashed: removed", 20, 228, size=12, color="muted", anchor="start")
    return fig


def _sheet_frames():
    fig = Figure("frames", 720, 330, alt="figkit frame and card components")
    fig.frame(16, 12, 216, 150, title="Frame")
    fig.frame(248, 12, 216, 150, title="Tinted frame", hue="green")
    fig.frame(480, 12, 224, 150, title="Considered / removed", dashed=True)
    fig.card("Card title", "body text on one\nor two lines", 130, 252, 220, hue="amber", badge="1")
    fig.card("Problem", "what goes wrong", 370, 252, 200, hue="red", style="strong", badge="!")
    fig.icon("warning", 540, 252, 20)
    fig.text("warning icon", 560, 252, size=12, color="muted", anchor="start")
    return fig


SHEETS = [_sheet_nodes, _sheet_tokens, _sheet_lines, _sheet_frames]


def write_components(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for make in SHEETS:
        fig = make()
        path = out / f"{fig.name}.svg"
        path.write_text(fig.render("light", editable_text=True))
        written.append(path)
    return written


def build(install=False):
    KEYNOTE_DIR.mkdir(parents=True, exist_ok=True)
    clr = KEYNOTE_DIR / "figkit.clr"
    write_palette(clr)
    sheets = write_components(KEYNOTE_DIR / "components")
    print(f"wrote {clr.relative_to(REPO)} and {len(sheets)} component sheets in {(KEYNOTE_DIR / 'components').relative_to(REPO)}")
    if install:
        target = Path.home() / "Library" / "Colors" / "figkit.clr"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(clr, target)
        print(f"installed the palette in {target} (restart Keynote to see it)")
