"""`blog new`: create a draft post from the template."""

import datetime
import json
import re

from .posts import POSTS, REPO, dump_notebook, slugify

CONFIG = REPO / "_quarto.yml"

FRONT_MATTER = """---
title: {title}
description: "TODO: one sentence that says what the reader will learn."
author: "Safouane Chergui"
date: "{date}"
categories: [TODO]
image: assets/figures/TODO.png
image-alt: "TODO: describe the preview image."
draft: true
---"""

INTRO = """Start with the question this post answers, in one or two sentences.

The workflow (figures, preview, publishing, cross-posting) is described in README.md at the root of the repository."""

FIGURES = '''"""Figures and charts for "{title}". Build: uv run figkit build {slug}

Add Figure, Stepper or Plot objects (diagrams, drawn as SVG) and LineChart,
BarChart, DotChart or Panels objects (interactive charts) to FIGURES, then show
them in the post with a shortcode on its own line, for example:
    {{{{< fig NAME "Optional caption." >}}}}
    {{{{< stepper NAME >}}}}
    {{{{< chart NAME >}}}}
See tools/figkit/README.md for the drawing functions and the style rules.
"""

from figkit import Axis, Figure, LineChart, Series, Stepper  # noqa: F401

FIGURES = []
'''


def _cell(cell_id, source):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source.splitlines(keepends=True)}


def add_to_sidebar(entry, year, config=CONFIG):
    """List `entry` first under the year's section of website.sidebar in _quarto.yml.

    The file is edited as text so its comments survive. A missing year gets a
    new section above the previous newest year.
    """
    text = config.read_text()
    if re.search(rf"^\s*-\s*{re.escape(entry)}\s*$", text, re.MULTILINE):
        return False
    section = re.search(rf'^(?P<indent>\s*)- section: "?{year}"?\s*\n(?P=indent)  contents:\s*\n', text, re.MULTILINE)
    if section:
        item_indent = section.group("indent") + "    "
        text = text[: section.end()] + f"{item_indent}- {entry}\n" + text[section.end():]
    else:
        first = re.search(r'^(?P<indent>\s*)- section: "?\d{4}"?\s*$', text, re.MULTILINE)
        if first is None:
            raise SystemExit(f"no year sections in website.sidebar of {config.name}: add - {entry} by hand")
        indent = first.group("indent")
        block = f'{indent}- section: "{year}"\n{indent}  contents:\n{indent}    - {entry}\n'
        text = text[: first.start()] + block + text[first.start():]
    config.write_text(text)
    return True


def new_post(title, slug=None, fmt="ipynb"):
    slug = slug or slugify(title)
    folder = POSTS / slug
    if folder.exists():
        raise SystemExit(f"posts/{slug}/ already exists")
    (folder / "assets" / "figures").mkdir(parents=True)
    front = FRONT_MATTER.format(title=json.dumps(title, ensure_ascii=False), date=datetime.datetime.now().astimezone().date().isoformat())
    intro = INTRO.format(slug=slug)
    if fmt == "qmd":
        (folder / "index.qmd").write_text(f"{front}\n\n{intro}\n")
    else:
        nb = {
            "cells": [_cell("front-matter", front), _cell("introduction", intro)],
            "metadata": {"language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        (folder / "index.ipynb").write_text(dump_notebook(nb))
    (folder / "figures.py").write_text(FIGURES.format(title=title.replace('"', "'"), slug=slug))
    # Drafts are left out of the rendered sidebar until they are published.
    add_to_sidebar(f"posts/{slug}/index.{fmt}", datetime.datetime.now().astimezone().year)
    return folder
