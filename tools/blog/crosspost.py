"""`blog crosspost`: Medium and Substack versions of published posts.

For each post, render it and write:
  _site/crosspost/<slug>/medium-<version>.html  a plain page for Medium's "Import a story"
                                        (Medium sets the canonical link and date; the name
                                        changes with every version, see medium_name)
  _site/crosspost/<slug>/substack.html  the same post with Copy buttons for the
                                        title, subtitle and body, to paste into
                                        Substack's editor

Both platforms get what they can display: figures as PNG (steppers as one
image per step, with a link to the interactive version), charts as the PNG
snapshot `blog chart-images` made of them (or as their data table when there
is none) with a link to the interactive chart, code as plain code
blocks, callouts as quotes, tables as lists, and math as LaTeX in code
(neither renders math). Images point to the live post, which Medium and
Substack copy them from, so cross-post a post once it is published and
deployed. The pages carry noindex and a canonical link to the post, so they
never compete with it in search. CI builds them, after
`quarto render`, for the posts with `crosspost: true` in their front matter.
"""

import hashlib
import json
import re
import shutil
import subprocess
from html import escape
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .posts import REPO, all_posts, find

SITE = REPO / "_site"
KEEP_ATTRS = {"a": {"href"}, "img": {"src", "alt"}, "code": {"class"}}
CALLOUT_TITLES = {"note": "Note", "tip": "Tip", "warning": "Warning", "important": "Important", "caution": "Caution"}

STYLE = """\
:root { color-scheme: light; }
body { max-width: 760px; margin: 3rem auto; padding: 0 1rem; font: 17px/1.68 "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif; color: #1a1c20; background: #fff; }
a { color: #1d5fb4; }
img { max-width: 100%; } figure { margin: 2rem 0; } figcaption { font-size: 0.85em; color: #686d77; }
code { font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: 0.85em; }
pre { background: #f4f4f0; padding: 0.8rem; overflow-x: auto; font-size: 0.8em; } pre code { font-size: 1em; }
blockquote { border-left: 3px solid #2a78d6; margin-left: 0; padding-left: 1rem; }"""

MEDIUM_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image}">
<style>
{style}
</style>
</head>
<body>
<article>
<h1>{title}</h1>
<p><em>{description}</em></p>
{body}
</article>
</body>
</html>
"""

SUBSTACK_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} (for Substack)</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<style>
{style}
.copy-bar {{ font: 15px/1.5 system-ui, sans-serif; background: #f0f0eb; border: 1px solid #e1e1da; border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 2.5rem; }}
.copy-bar p {{ margin: 0 0 0.6rem; }}
.copy-bar .note {{ margin: 0.8rem 0 0; color: #686d77; font-size: 0.9em; }}
.copy-row {{ display: flex; gap: 0.8rem; align-items: baseline; padding: 0.45rem 0; border-top: 1px solid #e1e1da; }}
.copy-row .label {{ flex: 0 0 4.5rem; color: #686d77; }}
.copy-row .value {{ flex: 1; min-width: 0; }}
.copy-bar button {{ font: inherit; font-size: 0.9em; padding: 0.2rem 0.8rem; border: 1px solid #c7c7bf; border-radius: 999px; background: #fff; color: #464b54; cursor: pointer; }}
.copy-bar button:hover, .copy-bar button:focus-visible {{ background: #1a1c20; border-color: #1a1c20; color: #fff; }}
@media (max-width: 480px) {{ .copy-row {{ flex-wrap: wrap; gap: 0.2rem 0.8rem; }} .copy-row .label {{ flex-basis: 100%; }} }}
</style>
</head>
<body>
<div class="copy-bar">
<p>On Substack, start a new post, then copy each part here and paste it into the matching field.</p>
<div class="copy-row"><span class="label">Title</span><span class="value" id="title">{title}</span><button type="button" data-copy="title">Copy</button></div>
<div class="copy-row"><span class="label">Subtitle</span><span class="value" id="subtitle">{description}</span><button type="button" data-copy="subtitle">Copy</button></div>
<div class="copy-row"><span class="label">Body</span><span class="value">everything below this box</span><button type="button" data-copy="body" data-rich>Copy</button></div>
<p class="note">Substack copies the images from the live post. Math is shown as LaTeX code; Substack's LaTeX block can turn it into equations.</p>
</div>
<article id="body">
{body}
</article>
<script>
for (const button of document.querySelectorAll("button[data-copy]")) {{
  button.addEventListener("click", async () => {{
    const source = document.getElementById(button.dataset.copy);
    try {{
      const parts = {{ "text/plain": new Blob([source.innerText.trim()], {{ type: "text/plain" }}) }};
      if (button.hasAttribute("data-rich")) parts["text/html"] = new Blob([source.innerHTML], {{ type: "text/html" }});
      await navigator.clipboard.write([new ClipboardItem(parts)]);
    }} catch {{
      // Browsers without the async clipboard API: copy a selection instead.
      const range = document.createRange();
      range.selectNodeContents(source);
      getSelection().removeAllRanges();
      getSelection().addRange(range);
      document.execCommand("copy");
      getSelection().removeAllRanges();
    }}
    button.textContent = "Copied";
    setTimeout(() => (button.textContent = "Copy"), 1500);
  }});
}}
</script>
</body>
</html>
"""


def _figure(soup, src, alt, caption_html=None):
    figure = soup.new_tag("figure")
    figure.append(soup.new_tag("img", src=src, alt=alt))
    if caption_html:
        caption = soup.new_tag("figcaption")
        caption.append(BeautifulSoup(caption_html, "html.parser"))
        figure.append(caption)
    return figure


def _png(src):
    """PNG export of a figkit image: x-light.svg -> x.png (raster figures already are PNG)."""
    return re.sub(r"-(light|dark)\.svg$", ".png", src)


def _figkit(soup, div, post_url):
    blocks = []
    caption = div.select_one(".figkit-caption")
    caption_html = caption.decode_contents().strip() if caption else None
    if "figkit-stepper" in div.get("class", []):
        frames = div.select(".figkit-frame")
        for frame in frames:
            img = frame.select_one("img.light-content, img.figkit-raster")
            step_caption = frame.select_one(".figkit-step-caption")
            number = step_caption.select_one(".figkit-step-number")
            if number:
                number.decompose()
            text = step_caption.decode_contents().strip()
            step = frame.get("data-step")
            blocks.append(_figure(soup, urljoin(post_url, _png(img["src"])), img.get("alt", ""), f"Step {step} of {len(frames)}: {text}"))
        note = BeautifulSoup(
            f'<p><em>This figure is interactive in the <a href="{post_url}">original post</a>, '
            f"where you can step through it.</em></p>",
            "html.parser",
        )
        blocks.append(note)
        if caption_html:
            blocks.append(BeautifulSoup(f"<p><em>{caption_html}</em></p>", "html.parser"))
    else:
        img = div.select_one("img.light-content, img.figkit-raster")
        blocks.append(_figure(soup, urljoin(post_url, _png(img["src"])), img.get("alt", ""), caption_html))
    return blocks


def _chart(soup, div, post_url, post_dir=None):
    """A chartkit chart: its PNG snapshot if `blog chart-images` made one, otherwise its title, subtitle and
    data table (as a list); then a link to the interactive chart."""
    chart_url = f"{post_url}#{div.get('id')}" if div.get("id") else post_url
    note = BeautifulSoup(
        f'<p><em>This chart is interactive in the <a href="{chart_url}">original post</a>.</em></p>', "html.parser")
    name = (div.get("id") or "").removeprefix("chart-")
    if post_dir is not None and name and (Path(post_dir) / "assets" / "charts" / f"{name}.png").exists():
        spec = div.select_one(".w-chart")
        try:
            alt = json.loads(spec["data-spec"]).get("alt", "") if spec is not None else ""
        except (KeyError, ValueError):
            alt = ""
        return [_figure(soup, urljoin(post_url, f"assets/charts/{name}.png"), alt), note]
    blocks = []
    title = div.select_one(".w-title")
    if title:
        blocks.append(BeautifulSoup(f"<p><strong>{title.decode_contents().strip()}</strong></p>", "html.parser"))
    sub = div.select_one(".w-sub")
    if sub:
        blocks.append(BeautifulSoup(f"<p><em>{sub.decode_contents().strip()}</em></p>", "html.parser"))
    table = div.select_one(".w-data table")
    if table is not None:
        blocks += _table(table)
    blocks.append(note)
    source = div.select_one(".w-src")
    if source:
        blocks.append(BeautifulSoup(f"<p><em>{source.decode_contents().strip()}</em></p>", "html.parser"))
    return blocks


def _table(table):
    """Neither platform has tables: one list item per row, led by its first cell.

    A row "M | build time | max neighbors" under the header "Parameter | When |
    What it controls" becomes "**M** - When: build time; What it controls: max neighbors".
    """
    blocks = []
    caption = table.find("caption")
    if caption and caption.get_text(strip=True):
        blocks.append(BeautifulSoup(f"<p><em>{caption.decode_contents().strip()}</em></p>", "html.parser"))
    rows = [cells for tr in table.find_all("tr") if (cells := tr.find_all(["th", "td"]))]
    header = []
    if rows and (table.find("thead") or all(cell.name == "th" for cell in rows[0])):
        header = [cell.get_text(" ", strip=True).rstrip(":.…") for cell in rows.pop(0)]
    items = []
    for cells in rows:
        details = []
        for column, cell in enumerate(cells[1:], start=1):
            label = header[column] if column < len(header) else ""
            details.append((f"{label}: " if label else "") + cell.decode_contents().strip())
        lead = f"<strong>{cells[0].decode_contents().strip()}</strong>"
        items.append(f"<li>{lead}{' - ' + '; '.join(details) if details else ''}</li>")
    blocks.append(BeautifulSoup(f"<ul>{''.join(items)}</ul>", "html.parser"))
    return blocks


def _replace(tag, new_nodes):
    for node in new_nodes:
        tag.insert_before(node)
    tag.decompose()


def transform(html, post_url, post_dir=None):
    """The article body of a rendered post, simplified for Medium and Substack."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main#quarto-document-content")
    for selector in [
        "header#title-block-header", "a.anchorjs-link", "button.code-copy-button", "script", "style",
        ".glightbox-desc", "#quarto-appendix", "nav", ".figkit-controls",
    ]:
        for tag in main.select(selector):
            tag.decompose()

    for div in main.select("div.figkit"):
        _replace(div, _figkit(soup, div, post_url))

    for div in main.select("div.chartkit"):
        _replace(div, _chart(soup, div, post_url, post_dir))

    # Quarto figures: keep one image and its caption.
    for div in main.select("div.quarto-figure, div.quarto-float"):
        img = div.find("img")
        if img is None:
            continue
        caption = div.find("figcaption")
        caption_html = caption.decode_contents().strip() if caption else None
        _replace(div, [_figure(soup, urljoin(post_url, img["src"]), img.get("alt", ""), caption_html)])

    for link in main.select("a.lightbox"):
        link.unwrap()
    for img in main.find_all("img"):
        img["src"] = urljoin(post_url, img["src"])

    for table in main.find_all("table"):
        _replace(table, _table(table))

    # Code: plain code blocks with a language class (no highlighting spans).
    for block in main.select("div.sourceCode"):
        pre = block.find("pre")
        code = soup.new_tag("code")
        language = next((c for c in pre.get("class", []) if c not in ("sourceCode", "code-with-copy", "number-lines")), None)
        if language:
            code["class"] = f"language-{language}"
        code.string = pre.get_text()
        new_pre = soup.new_tag("pre")
        new_pre.append(code)
        _replace(block, [new_pre])
    for pre in main.find_all("pre"):
        if pre.find("code") is None:
            code = soup.new_tag("code")
            code.string = pre.get_text()
            pre.clear()
            pre.append(code)

    # Callouts become quotes with a bold title.
    for callout in main.select("div.callout"):
        kind = next((c.split("-", 1)[1] for c in callout.get("class", []) if c.startswith("callout-") and c.split("-", 1)[1] in CALLOUT_TITLES), "note")
        header = callout.select_one(".callout-title-container")
        title = header.get_text(" ", strip=True) if header and header.get_text(strip=True) else CALLOUT_TITLES[kind]
        body = callout.select_one(".callout-body-container") or callout
        quote = soup.new_tag("blockquote")
        quote.append(BeautifulSoup(f"<p><strong>{escape(title)}</strong></p>", "html.parser"))
        for child in list(body.children):
            quote.append(child.extract())
        _replace(callout, [quote])

    # Math as LaTeX source in code: neither platform renders math.
    for span in main.select("span.math"):
        latex = span.get_text().strip()
        if "display" in span.get("class", []):
            latex = re.sub(r"^\\\[|\\\]$", "", latex).strip()
            pre = soup.new_tag("pre")
            code = soup.new_tag("code")
            code.string = latex
            pre.append(code)
            parent = span.find_parent("p")
            if parent is not None and parent.get_text(strip=True) == span.get_text(strip=True):
                _replace(parent, [pre])
            else:
                _replace(span, [pre])
        else:
            latex = re.sub(r"^\\\(|\\\)$", "", latex).strip()
            code = soup.new_tag("code")
            code.string = latex
            _replace(span, [code])

    for link in main.find_all("a", href=True):
        link["href"] = urljoin(post_url, link["href"])

    for tag in main.select("section, div, span"):
        tag.unwrap()
    for tag in main.find_all(True):
        allowed = KEEP_ATTRS.get(tag.name, set())
        for attribute in list(tag.attrs):
            if attribute not in allowed:
                del tag[attribute]
        if tag.name == "code" and not str(tag.get("class", "")).startswith("language-"):
            tag.attrs.pop("class", None)
    for p in main.find_all("p"):
        if not p.get_text(strip=True) and p.find("img") is None:
            p.decompose()
    return main.decode_contents().strip()


def _medium_code(body_html):
    """Code blocks in the shape Medium's "Import a story" keeps (tested on Medium, October 2026).

    Its importer collapses the newlines of a <pre> and drops a <pre><code> written with <br>, so each block
    becomes a bare <pre> with <br> between lines. It also collapses runs of spaces and splits a block at an
    empty line, so leading spaces become tabs (one per four spaces, which Python accepts when copied back)
    and an empty line holds a non-breaking space. Medium ignores the language class and guesses the language.
    It still adds an empty code block after each block, which has to be deleted in Medium's editor.
    """
    soup = BeautifulSoup(body_html, "html.parser")
    for pre in soup.find_all("pre"):
        lines = pre.get_text().rstrip("\n").split("\n")
        out = []
        for line in lines:
            if not line.strip():
                out.append("&nbsp;")
                continue
            indent = len(line) - len(line.lstrip(" "))
            out.append("\t" * round(indent / 4) + escape(line[indent:], quote=False))
        pre.replace_with(BeautifulSoup(f"<pre>{'<br>'.join(out)}</pre>", "html.parser"))
    return str(soup).replace("<br/>", "<br>")  # the exact form tested on Medium


def render(posts=None):
    """Render the given posts, or the whole site."""
    quarto = shutil.which("quarto")
    if quarto is None:
        raise SystemExit("quarto is not installed (or not on PATH)")
    commands = [["render", str(post.source.relative_to(REPO))] for post in posts] if posts else [["render"]]
    for args in commands:
        print(f"quarto {' '.join(args)}")
        result = subprocess.run([quarto, *args], cwd=REPO, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(result.stdout[-3000:], result.stderr[-3000:])
            raise SystemExit("quarto render failed")


def medium_name(post):
    """File name of the post's Medium page, which changes whenever the post or this tool changes.

    Medium caches an import per URL, query string included, so re-importing the same URL returns the
    first version. The name hashes the post's files and this module, the same on any machine, so a
    local run and CI agree on the URL.
    """
    digest = hashlib.sha256(Path(__file__).read_bytes())
    files = (p for p in post.dir.rglob("*") if p.is_file())
    # Skip what git doesn't track (caches, hidden files such as .DS_Store), so CI computes the same name.
    for path in sorted(p for p in files if "__pycache__" not in p.parts and not any(part.startswith(".") for part in p.relative_to(post.dir).parts)):
        digest.update(path.relative_to(post.dir).as_posix().encode())
        digest.update(path.read_bytes())
    return f"medium-{digest.hexdigest()[:10]}.html"


def _write(post, rendered, site):
    meta = post.meta()
    body = transform(rendered.read_text(), post.url, post.dir)
    body = f'<p><em>Originally published at <a href="{post.url}">{post.url}</a>.</em></p>\n{body}'
    title = escape(str(meta.get("title", "")))
    description = escape(str(meta.get("description", "")))
    out = site / "crosspost" / post.slug
    out.mkdir(parents=True, exist_ok=True)
    image = urljoin(post.url, str(meta["image"])) if meta.get("image") else ""
    fields = {"title": title, "description": description, "url": post.url, "style": STYLE, "image": escape(image)}
    (out / medium_name(post)).write_text(MEDIUM_PAGE.format(**fields, body=_medium_code(body)))
    (out / "substack.html").write_text(SUBSTACK_PAGE.format(**fields, body=body))


def build(slugs=None, render=True, site=SITE):
    """Write the cross-post pages of the given posts.

    Without slugs (what CI runs), only published posts with `crosspost: true` in their front matter, so
    a post's cross-post pages are online only while it is being cross-posted: Medium's importer needs a
    public URL. With slugs (a local run), the given posts, flagged or not.
    """
    if slugs:
        posts = [find(slug) for slug in slugs]
        drafts = [post.slug for post in posts if post.meta().get("draft")]
        if drafts:
            raise SystemExit(
                "".join(f"{slug} is still a draft: publish it first with uv run blog publish {slug}\n" for slug in drafts)
                + "(Medium and Substack copy the images from the live post.)"
            )
    else:
        posts = [post for post in all_posts() if not post.meta().get("draft") and post.meta().get("crosspost") is True]
    if render:
        render(posts if slugs else None)
    written = []
    for post in posts:
        rendered = site / "posts" / post.slug / "index.html"
        if not rendered.exists():
            if slugs:
                raise SystemExit(f"{rendered.relative_to(REPO)} is missing: run without --no-render")
            continue
        _write(post, rendered, site)
        written.append(post)
    return written
