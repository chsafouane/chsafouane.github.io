"""`blog preview`: quarto preview plus figure rebuilds on save."""

import shutil
import subprocess
import threading
import time
import traceback

from figkit.cli import _load
from figkit.export import save

from .posts import POSTS, REPO

KIT = REPO / "tools" / "figkit"


def _snapshot(paths):
    return {p: p.stat().st_mtime for p in paths if p.exists()}


def _rebuild(sources):
    for source in sources:
        try:
            for item in _load(source):
                save(item, source.parent / "assets" / "figures", raster=False)
            print(f"[figures] rebuilt {source.parent.name}", flush=True)
        except Exception:  # noqa: BLE001 - keep watching after any mistake in figures.py
            print(f"[figures] error in {source.relative_to(REPO)}:", flush=True)
            traceback.print_exc()


def _watch(slug, stop):
    figure_files = sorted(POSTS.glob(f"{slug or '*'}/figures.py"))
    kit_files = sorted(KIT.glob("*.py")) + [REPO / "_brand.yml"]
    seen = _snapshot(figure_files + kit_files)
    while not stop.is_set():
        time.sleep(1)
        figure_files = sorted(POSTS.glob(f"{slug or '*'}/figures.py"))
        now = _snapshot(figure_files + kit_files)
        changed = [p for p in now if now[p] != seen.get(p)]
        seen = now
        if any(p in kit_files for p in changed):
            print("[figures] the kit or the palette changed: rebuilding all figures", flush=True)
            _rebuild(figure_files)
        else:
            _rebuild([p for p in changed if p in figure_files])


def preview(slug=None, browser=True):
    quarto = shutil.which("quarto")
    if quarto is None:
        raise SystemExit("quarto is not installed: https://quarto.org/docs/download/")
    target = []
    if slug:
        from .posts import find

        target = [str(find(slug).source.relative_to(REPO))]
    stop = threading.Event()
    watcher = threading.Thread(target=_watch, args=(slug, stop), daemon=True)
    watcher.start()
    print("[figures] watching figures.py files; press Ctrl-C to stop", flush=True)
    try:
        options = [] if browser else ["--no-browser"]
        subprocess.run([quarto, "preview", *target, *options], cwd=REPO, check=False)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
