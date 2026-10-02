"""`blog chart-images`: PNG snapshots of a post's charts, for its Medium and Substack versions.

Charts are drawn in the browser by chartkit.js, so the cross-post pages can't show them as they are.
This renders the post, opens it in a headless browser and saves every chart, in light mode at 2x, to
posts/<slug>/assets/charts/<name>.png; `blog crosspost` then shows that image instead of the chart's
data table. Each PNG records the SHA-256 of the chart spec it was taken from (a tEXt chunk named
chart-spec-sha256), and tools/check_posts.py fails when the spec has changed since, so a stale image
can't be published.

Needs Playwright and a Chromium-based browser (Brave or Chrome, or `playwright install chromium`):
    uv run --with playwright blog chart-images SLUG
"""

import hashlib
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .crosspost import SITE, render
from .posts import find

HASH_KEY = "chart-spec-sha256"
BROWSERS = [  # tried in order; Playwright's own Chromium is the fallback
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def spec_hash(spec_path):
    return hashlib.sha256(Path(spec_path).read_bytes()).hexdigest()


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _serve(directory):
    """Serve `directory` on a free local port; returns (server, base URL)."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_QuietHandler, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def snapshot(slugs, render_first=True):
    """Save a PNG of every chart in the given posts; returns the paths written."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("needs Playwright: uv run --with playwright blog chart-images SLUG") from None
    posts = [find(slug) for slug in slugs]
    if render_first:
        render(posts)
    server, base = _serve(SITE)
    written = []
    try:
        with sync_playwright() as p:
            executable = next((b for b in BROWSERS if Path(b).exists()), None)
            browser = p.chromium.launch(executable_path=executable) if executable else p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2, color_scheme="light")
            for post in posts:
                page.goto(f"{base}/posts/{post.slug}/", wait_until="networkidle")
                # The data table and tooltips are for the interactive page; the image shows the chart itself.
                page.add_style_tag(content=".chartkit .w-data, .chartkit .tip { display: none !important; }")
                charts_dir = post.dir / "assets" / "charts"
                for box in page.locator(".chartkit[id^='chart-']").all():
                    name = box.get_attribute("id").removeprefix("chart-")
                    spec = charts_dir / f"{name}.json"
                    if not spec.exists():
                        continue
                    box.locator("svg").first.wait_for()
                    box.scroll_into_view_if_needed()
                    page.wait_for_timeout(300)
                    out = charts_dir / f"{name}.png"
                    tmp = out.with_suffix(".tmp.png")
                    box.screenshot(path=str(tmp))
                    info = PngInfo()
                    info.add_text(HASH_KEY, spec_hash(spec))
                    with Image.open(tmp) as image:
                        image.save(out, pnginfo=info, optimize=True)
                    tmp.unlink()
                    written.append(out)
            browser.close()
    finally:
        server.shutdown()
    return written

