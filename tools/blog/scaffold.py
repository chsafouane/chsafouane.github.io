"""`blog new`: create a draft post from the template."""

import datetime
import json

from .posts import POSTS, dump_notebook, slugify

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

FIGURES = '''"""Figures for "{title}". Build: uv run figkit build {slug}

Add Figure, Stepper or Plot objects to FIGURES, then show them in the post with
a shortcode on its own line, for example:
    {{{{< fig NAME "Optional caption." >}}}}
    {{{{< stepper NAME >}}}}
See tools/figkit/README.md for the drawing functions and the style rules.
"""

from figkit import Figure, Stepper  # noqa: F401

FIGURES = []
'''


def _cell(cell_id, source):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source.splitlines(keepends=True)}


def new_post(title, slug=None, fmt="ipynb"):
    slug = slug or slugify(title)
    folder = POSTS / slug
    if folder.exists():
        raise SystemExit(f"posts/{slug}/ already exists")
    (folder / "assets" / "figures").mkdir(parents=True)
    front = FRONT_MATTER.format(title=json.dumps(title, ensure_ascii=False), date=datetime.date.today().isoformat())
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
    return folder
