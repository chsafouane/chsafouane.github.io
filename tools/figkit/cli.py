"""Command line: `uv run figkit <command>`.

  build [slug ...]   render posts/<slug>/figures.py into posts/<slug>/assets/figures
                     and its charts into posts/<slug>/assets/charts
                     (--no-raster skips PNG/GIF, as CI does to check SVGs are current)
  palette            print the figure palette with contrast ratios
  syntax             write the code highlighting themes in _theme from _brand.yml
                     (--check fails if they are out of date, as CI does)
  keynote            write the Keynote palette (figkit.clr) and component sheets
                     (--install also copies the palette to ~/Library/Colors)
  import PNG... --post SLUG --name NAME --alt TEXT [--caption TEXT ...]
                     bring Keynote exports into a post (several PNGs make a stepper)
"""

import argparse
import importlib.util
import sys

from .charts import Chart
from .export import import_raster, save
from .palette import HUES, contrast, palette
from .paths import POSTS


def _load(figures_py):
    spec = importlib.util.spec_from_file_location(f"figures_{figures_py.parent.name.replace('-', '_')}", figures_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    items = getattr(module, "FIGURES", None)
    if items is None:
        raise SystemExit(f"{figures_py} must define FIGURES = [...]")
    return items


def build(slugs, raster=True):
    sources = sorted(POSTS.glob("*/figures.py"))
    if slugs:
        sources = [s for s in sources if s.parent.name in slugs]
        missing = set(slugs) - {s.parent.name for s in sources}
        if missing:
            raise SystemExit(f"no figures.py for: {', '.join(sorted(missing))}")
    for source in sources:
        out = source.parent / "assets" / "figures"
        charts = source.parent / "assets" / "charts"
        for item in _load(source):
            if isinstance(item, Chart):
                charts.mkdir(parents=True, exist_ok=True)
                (charts / f"{item.name}.json").write_text(item.json())
                print(f"{source.parent.name}/{item.name}: chart")
                continue
            files = save(item, out, raster=raster)
            print(f"{source.parent.name}/{item.name}: {len(files)} files")


def show_palette():
    for mode in ("light", "dark"):
        p = palette(mode)
        print(f"{mode}: page {p.page}  text {p.text}  edge {p.edge}  frame {p.frame_fill}/{p.frame_stroke}")
        for name in ["neutral", "accent", *HUES]:
            h = p.hue(name)
            print(
                f"  {name:8} fill {h.fill}  stroke {h.stroke} ({contrast(h.stroke, h.fill):.1f}:1 on fill)"
                f"  label {h.label} ({contrast(h.label, p.page):.1f}:1 on page)"
            )


def main(argv=None):
    parser = argparse.ArgumentParser(prog="figkit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="render figures of all posts, or of the given slugs")
    b.add_argument("slugs", nargs="*")
    b.add_argument("--no-raster", action="store_true", help="skip PNG/GIF exports (used by CI)")
    sub.add_parser("palette", help="print the figure palette")
    s = sub.add_parser("syntax", help="write the code highlighting themes from _brand.yml")
    s.add_argument("--check", action="store_true", help="fail if the theme files are out of date")
    k = sub.add_parser("keynote", help="write the Keynote palette and component sheets")
    k.add_argument("--install", action="store_true", help="copy the palette to ~/Library/Colors")
    i = sub.add_parser("import", help="bring PNG exports (Keynote) into a post")
    i.add_argument("sources", nargs="+", help="PNG files or folders of PNGs")
    i.add_argument("--post", required=True, help="post slug, for example uv-lessons")
    i.add_argument("--name", required=True, help="figure name used in {{< fig NAME >}}")
    i.add_argument("--alt", required=True, help="alt text describing the figure")
    i.add_argument("--caption", action="append", help="step caption (once per step, for steppers)")
    i.add_argument("--scale", type=float, default=2.0, help="export resolution (default 2 for 2x slides)")
    args = parser.parse_args(argv)
    if args.command == "build":
        build(args.slugs, raster=not args.no_raster)
    elif args.command == "palette":
        show_palette()
    elif args.command == "syntax":
        from .syntax import build as build_syntax

        build_syntax(check=args.check)
    elif args.command == "keynote":
        from .keynote import build as build_keynote

        build_keynote(install=args.install)
    elif args.command == "import":
        post = POSTS / args.post
        if not post.is_dir():
            raise SystemExit(f"no post folder {post}")
        files = import_raster(args.sources, post / "assets" / "figures", args.name, args.alt, args.caption, args.scale)
        kind = "stepper" if any(f.endswith(".gif") for f in files) else "fig"
        print(f"{args.post}/{args.name}: {len(files)} files; use {{{{< {kind} {args.name} >}}}} in the post")
    return 0


if __name__ == "__main__":
    sys.exit(main())
