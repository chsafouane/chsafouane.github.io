"""`blog crosspost`: Medium- and Substack-ready versions of rendered posts.

For every published post rendered in _site, write:
  _site/crosspost/<slug>/index.html  a plain page for Medium's "Import a story"
                                     (Medium sets the canonical link and date)
  _site/crosspost/<slug>/post.md     Markdown for a Substack draft (substack-mcp)
  _site/crosspost/<slug>/meta.json   title, subtitle and URLs for both

Both platforms get what they can display: figures as PNG (steppers as one
image per step, with a link to the interactive version), code as plain code
blocks, callouts as quotes, and math as LaTeX in code (neither renders math).
The pages carry noindex and a canonical link to the post, so they never
compete with it in search. CI runs this after `quarto render`.
"""

import json
import re
import shutil
import subprocess
from html import escape
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString

from .posts import REPO, SITE_URL, all_posts

SITE = REPO / "_site"
KEEP_ATTRS = {"a": {"href"}, "img": {"src", "alt"}, "code": {"class"}, "th": {"colspan", "rowspan"}, "td": {"colspan", "rowspan"}}
CALLOUT_TITLES = {"note": "Note", "tip": "Tip", "warning": "Warning", "important": "Important", "caution": "Caution"}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<style>
body {{ max-width: 680px; margin: 3rem auto; padding: 0 1rem; font: 18px/1.65 Georgia, serif; color: #1c1b19; }}
img {{ max-width: 100%; }} figure {{ margin: 2rem 0; }} figcaption {{ font-size: 0.85em; color: #5e5a53; }}
pre {{ background: #f4f3f0; padding: 0.8rem; overflow-x: auto; font-size: 0.8em; }}
blockquote {{ border-left: 3px solid #6761c5; margin-left: 0; padding-left: 1rem; }}
</style>
</head>
<body>
<article>
{body}
</article>
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


def _replace(tag, new_nodes):
    for node in new_nodes:
        tag.insert_before(node)
    tag.decompose()


def transform(html, post_url):
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


def _markdown(body_html):
    """Substack Markdown: figures as images whose alt text is the caption."""
    soup = BeautifulSoup(body_html, "html.parser")
    for figure in soup.find_all("figure"):
        img = figure.find("img")
        caption = figure.find("figcaption")
        paragraph = soup.new_tag("p")
        paragraph.append(soup.new_tag("img", src=img["src"], alt=caption.get_text(" ", strip=True) if caption else ""))
        figure.replace_with(paragraph)
    quarto = shutil.which("quarto")
    if quarto is None:
        raise SystemExit("quarto is needed to convert HTML to Markdown (quarto pandoc)")
    result = subprocess.run(
        [quarto, "pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
        input=str(soup), capture_output=True, text=True, check=True,
    )
    return result.stdout.strip() + "\n"


def build(slugs=None, site=SITE):
    written = []
    for post in all_posts():
        if slugs and post.slug not in slugs:
            continue
        meta = post.meta()
        rendered = site / "posts" / post.slug / "index.html"
        if meta.get("draft") or not rendered.exists():
            continue
        body = transform(rendered.read_text(), post.url)
        title, description = str(meta.get("title", "")), str(meta.get("description", ""))
        origin = f'<p><em>Originally published at <a href="{post.url}">{post.url}</a>.</em></p>'
        out = site / "crosspost" / post.slug
        out.mkdir(parents=True, exist_ok=True)
        page_body = f"<h1>{escape(title)}</h1>\n<p><em>{escape(description)}</em></p>\n{origin}\n{body}"
        (out / "index.html").write_text(PAGE.format(title=escape(title), description=escape(description, quote=True), url=post.url, body=page_body))
        (out / "post.md").write_text(_markdown(f"{origin}\n{body}"))
        (out / "meta.json").write_text(json.dumps({
            "slug": post.slug,
            "title": title,
            "subtitle": description,
            "post_url": post.url,
            "medium_import_url": f"{SITE_URL}/crosspost/{post.slug}/",
            "substack_markdown_url": f"{SITE_URL}/crosspost/{post.slug}/post.md",
        }, indent=2, ensure_ascii=False) + "\n")
        written.append(post.slug)
    return written
