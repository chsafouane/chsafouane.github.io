#!/usr/bin/env python3
"""Check that blog posts follow the conventions the site theme relies on.

Usage: python3 tools/check_posts.py [posts_dir]

Each post lives in posts/<slug>/index.ipynb (or index.qmd). The checks:
  - the slug is lowercase ASCII with hyphens (no spaces or apostrophes, which
    break Quarto's sitemap and RSS feed);
  - front matter has title, date, description, categories and image, and does
    not override the shared layout (format, toc, toc-location, toc-depth);
  - the body uses Markdown instead of raw HTML layout (<img>, <br>, align=),
    has no leftover VS Code table-of-contents links and no h1 headings (the
    post title is the only h1);
  - lists are separated from a preceding paragraph by a blank line (pandoc
    otherwise renders them as run-on text);
  - code fences use a language pandoc can highlight (checked when `quarto`
    is on PATH);
  - local images referenced by the post exist;
  - every {{< fig NAME >}} / {{< stepper NAME >}} has a figkit manifest of the
    right kind in assets/figures, and the files it lists exist;
  - published posts (no `draft: true`) contain no TODO placeholders left by
    `blog new`. Drafts may still have TODOs and a missing preview image.
Exits with status 1 when any check fails.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ["title", "date", "description", "categories", "image"]
FORBIDDEN_FIELDS = ["format", "toc", "toc-location", "toc-depth"]
RAW_HTML = re.compile(r"<img\b|<br\s*/?>|\balign\s*=", re.IGNORECASE)
VSCODE_TOC = re.compile(r"toc0_|vscode-jupyter-toc")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*\{?\s*\.?([A-Za-z0-9_+-]*)")
LIST_ITEM = re.compile(r"^([-*+]|\d+[.)])\s+\S")
ANY_LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+\S")
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
SHORTCODE = re.compile(r"\{\{<\s*(fig|stepper)\s+(?:name=)?\"?([A-Za-z0-9_-]+)")
# Fence "languages" that are Quarto cell types or plain text, not pandoc lexers.
NON_LEXER_FENCES = {"", "dot", "mermaid", "ojs", "text", "plaintext", "raw", "=html"}


def highlight_languages():
    quarto = shutil.which("quarto")
    if quarto is None:
        return None
    out = subprocess.run([quarto, "pandoc", "--list-highlight-languages"], capture_output=True, text=True, check=True)
    return {line.strip().lower() for line in out.stdout.splitlines() if line.strip()}


def read_post(path):
    """Return (front matter text, list of markdown chunks) for a post file."""
    if path.suffix == ".ipynb":
        cells = json.loads(path.read_text())["cells"]
        chunks = ["".join(c["source"]) for c in cells if c["cell_type"] in ("markdown", "raw")]
    else:
        chunks = [path.read_text()]
    match = re.match(r"^\s*---\n(.*?)\n---\s*(?:\n|$)", chunks[0], re.S) if chunks else None
    if not match:
        return None, chunks
    chunks[0] = chunks[0][match.end():]
    return match.group(1), chunks


def front_matter_fields(text):
    return {m.group(1) for m in re.finditer(r"^([A-Za-z][\w-]*)\s*:", text, re.M)}


def front_matter_value(text, key):
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", text, re.M)
    return m.group(1).strip().strip("\"'") if m else None


def check_markdown(chunk, languages, errors, where):
    fence = None
    lines = chunk.split("\n")
    for number, line in enumerate(lines, start=1):
        m = FENCE.match(line)
        if m:
            token = m.group(1)
            if fence is None:
                fence = token[0] * len(token)
                language = m.group(2).lower()
                if languages is not None and language not in NON_LEXER_FENCES and language not in languages:
                    errors.append(f"{where}:{number}: code fence language '{language}' is not a pandoc lexer")
            elif line.strip().startswith(fence) and not line.strip().strip(fence[0]):
                fence = None
            continue
        if fence:
            continue
        if RAW_HTML.search(line):
            errors.append(f"{where}:{number}: raw HTML layout, use Markdown images and figures: {line.strip()[:80]}")
        if VSCODE_TOC.search(line):
            errors.append(f"{where}:{number}: leftover VS Code table-of-contents markup")
        if re.match(r"^#\s", line):
            errors.append(f"{where}:{number}: h1 heading in the body, start sections at ##: {line.strip()[:80]}")
        if LIST_ITEM.match(line) and number > 1 and lines[number - 2].strip():
            # Only the first item of a list glued to a paragraph is a problem.
            start = number - 2
            while start > 0 and lines[start - 1].strip():
                start -= 1
            block = lines[start:number - 1]
            first = block[0]
            in_list = any(ANY_LIST_ITEM.match(previous) for previous in block)
            if not in_list and not first.startswith(("#", ">", "|", "<", ":::", "    ", "\t")):
                errors.append(f"{where}:{number}: add a blank line before this list: {line.strip()[:80]}")


def check_post(post_dir, languages):
    errors = []
    sources = [p for p in (post_dir / "index.ipynb", post_dir / "index.qmd") if p.exists()]
    if not SLUG.match(post_dir.name):
        errors.append(f"{post_dir}: folder name must be a lowercase slug like 'my-post-title'")
    if len(sources) != 1:
        return errors + [f"{post_dir}: expected exactly one index.ipynb or index.qmd"]
    source = sources[0]
    front, chunks = read_post(source)
    if front is None:
        return errors + [f"{source}: missing YAML front matter at the top"]
    fields = front_matter_fields(front)
    draft = re.search(r"^draft\s*:\s*true\s*$", front, re.M) is not None
    errors += [f"{source}: front matter is missing '{f}'" for f in REQUIRED_FIELDS if f not in fields]
    if not draft:
        errors += [f"{source}: replace the TODO placeholder: {line.strip()}" for line in front.splitlines() if "TODO" in line]
        errors += [f"{source}: replace the TODO placeholder in the body" for chunk in chunks if "TODO" in chunk][:1]
    errors += [f"{source}: remove '{f}' from front matter (set in posts/_metadata.yml)" for f in FORBIDDEN_FIELDS if f in fields]
    image = front_matter_value(front, "image")
    referenced = [image] if image and not draft else []
    for index, chunk in enumerate(chunks):
        check_markdown(chunk, languages, errors, f"{source} (cell {index})" if source.suffix == ".ipynb" else str(source))
        referenced += IMAGE.findall(chunk)
    for ref in referenced:
        if not re.match(r"^[a-z]+://", ref) and not (post_dir / ref).exists():
            errors.append(f"{source}: image not found: {ref}")
    for chunk in chunks:
        for kind, name in SHORTCODE.findall(chunk):
            errors += check_figure(post_dir, source, kind, name)
    return errors


def figure_files(manifest):
    """Files the {{< fig >}} / {{< stepper >}} shortcode will load."""
    name = manifest["name"]
    stems = [f"{name}-{step}" for step in range(1, len(manifest.get("steps", [])) + 1)] or [name]
    if manifest.get("format") == "png":
        return [f"{stem}.png" for stem in stems]
    return [f"{stem}-{mode}.svg" for stem in stems for mode in ("light", "dark")]


def check_figure(post_dir, source, kind, name):
    path = post_dir / "assets" / "figures" / f"{name}.json"
    if not path.exists():
        return [f"{source}: {{{{< {kind} {name} >}}}} has no manifest {path.relative_to(post_dir)} (run uv run figkit build)"]
    manifest = json.loads(path.read_text())
    expected = "figure" if kind == "fig" else "stepper"
    errors = []
    if manifest.get("kind") != expected:
        errors.append(f"{source}: {name} is a {manifest.get('kind')}, use the {'stepper' if kind == 'fig' else 'fig'} shortcode")
    for file in figure_files(manifest):
        if not (post_dir / "assets" / "figures" / file).exists():
            errors.append(f"{source}: figure {name} is missing assets/figures/{file}")
    return errors


def main():
    posts = Path(sys.argv[1] if len(sys.argv) > 1 else "posts")
    languages = highlight_languages()
    if languages is None:
        print("note: quarto not on PATH, skipping the code fence language check")
    errors = []
    post_dirs = sorted(p for p in posts.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    for post_dir in post_dirs:
        errors += check_post(post_dir, languages)
    for error in errors:
        print(error)
    print(f"checked {len(post_dirs)} posts: {'OK' if not errors else f'{len(errors)} problem(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
