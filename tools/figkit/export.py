"""Write figures to disk: SVG per mode, PNG and GIF for cross-posting, a manifest.

For a figure named `x` the output directory receives:
  x-light.svg, x-dark.svg   shown on the site (the shortcode picks by mode)
  x.png                     light version at 2x on white, for Medium/Substack
  x.json                    manifest read by the {{< fig >}} shortcode
A stepper writes x-<step>-light.svg / x-<step>-dark.svg / x-<step>.png per
step, plus x.gif (all steps) and x.png (last step).
"""

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from .figure import Stepper

PNG_SCALE = 2
STEP_SECONDS = 2.4


def _rsvg():
    path = shutil.which("rsvg-convert")
    if path is None:
        raise SystemExit("figkit needs rsvg-convert for PNG export: brew install librsvg")
    return path


def _png(svg_path: Path, png_path: Path):
    subprocess.run(
        [_rsvg(), "--zoom", str(PNG_SCALE), "--background-color", "#FFFFFF", str(svg_path), "-o", str(png_path)],
        check=True,
    )


def _write_figure(fig, out: Path, stem: str, raster: bool):
    for mode in ("light", "dark"):
        (out / f"{stem}-{mode}.svg").write_text(fig.render(mode))
    if raster:
        _png(out / f"{stem}-light.svg", out / f"{stem}.png")


def _stale(out: Path, name: str, raster: bool):
    """Outputs of a previous build of `name` (for example removed steps)."""
    for old in out.glob(f"{name}[.-]*"):
        if not (old.stem == name or old.stem.startswith(f"{name}-")):
            continue
        if not raster and old.suffix in (".png", ".gif"):
            continue
        yield old


def save(item, out: Path, raster: bool = True):
    """Render a Figure, Plot or Stepper into `out`; returns the written file names.

    With raster=False only the SVG files and the manifest are written (the
    PNG/GIF exports depend on the local rsvg-convert version).
    """
    out.mkdir(parents=True, exist_ok=True)
    for old in list(_stale(out, item.name, raster)):
        old.unlink()
    manifest = {
        "version": 1,
        "name": item.name,
        "width": item.width,
        "height": item.height,
        "alt": item.alt,
    }
    if isinstance(item, Stepper):
        frames = []
        for step, fig in enumerate(item.frames(), start=1):
            stem = f"{item.name}-{step}"
            _write_figure(fig, out, stem, raster)
            frames.append(out / f"{stem}.png")
        if raster:
            images = [Image.open(f).convert("RGB") for f in frames]
            durations = [int(STEP_SECONDS * 1000)] * len(images)
            durations[-1] = int(STEP_SECONDS * 1500)
            images[0].save(
                out / f"{item.name}.gif", save_all=True, append_images=images[1:], duration=durations, loop=0, optimize=True
            )
            shutil.copyfile(frames[-1], out / f"{item.name}.png")
        manifest.update(
            kind="stepper",
            steps=[{"caption": caption} for caption in item.captions],
            png=f"{item.name}.png",
            gif=f"{item.name}.gif",
        )
    elif hasattr(item, "render"):  # Figure, Plot
        _write_figure(item, out, item.name, raster)
        manifest.update(kind="figure", png=f"{item.name}.png")
    else:
        raise TypeError(f"cannot save {type(item).__name__}")
    (out / f"{item.name}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return sorted(p.name for p in out.glob(f"{item.name}*"))


def _natural_key(path: Path):
    import re

    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def import_raster(sources, out: Path, name: str, alt: str, captions=None, scale: float = 2.0):
    """Bring PNG exports (for example from Keynote) into a post as a figure or stepper.

    One PNG gives a figure; several give a stepper (one PNG per step, in
    natural file-name order, with one caption each). `scale` is the export
    resolution: a slide exported at 2x shows at half its pixel size.
    Raster figures are light-only and appear on a white plate in dark mode.
    """
    files = []
    for source in map(Path, sources):
        files += sorted(source.glob("*.png"), key=_natural_key) if source.is_dir() else [source]
    if not files:
        raise SystemExit("no PNG files to import")
    if not alt:
        raise SystemExit("imported figures need alt text (--alt)")
    out.mkdir(parents=True, exist_ok=True)
    for old in list(_stale(out, name, True)):
        old.unlink()
    with Image.open(files[0]) as first:
        width, height = round(first.width / scale), round(first.height / scale)
    manifest = {"version": 1, "name": name, "width": width, "height": height, "alt": alt, "format": "png"}
    if len(files) == 1:
        shutil.copyfile(files[0], out / f"{name}.png")
        manifest.update(kind="figure", png=f"{name}.png")
    else:
        captions = list(captions or [])
        if len(captions) != len(files):
            raise SystemExit(f"a stepper needs one --caption per step: got {len(captions)} for {len(files)} PNGs")
        for step, source in enumerate(files, start=1):
            shutil.copyfile(source, out / f"{name}-{step}.png")
        images = [Image.open(out / f"{name}-{step}.png").convert("RGB") for step in range(1, len(files) + 1)]
        durations = [int(STEP_SECONDS * 1000)] * len(images)
        durations[-1] = int(STEP_SECONDS * 1500)
        images[0].save(out / f"{name}.gif", save_all=True, append_images=images[1:], duration=durations, loop=0, optimize=True)
        shutil.copyfile(out / f"{name}-{len(files)}.png", out / f"{name}.png")
        manifest.update(kind="stepper", steps=[{"caption": c} for c in captions], png=f"{name}.png", gif=f"{name}.gif")
    (out / f"{name}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return sorted(p.name for p in out.glob(f"{name}*"))
