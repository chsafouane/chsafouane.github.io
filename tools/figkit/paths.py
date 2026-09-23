"""Locations inside the blog repository."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRAND_FILE = REPO / "_brand.yml"
POSTS = REPO / "posts"
