"""Find posts and read or edit their front matter (notebooks and .qmd files)."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
POSTS = REPO / "posts"
SITE_URL = "https://chsafouane.github.io"
FRONT_MATTER = re.compile(r"\A(\s*---\n)(.*?)(\n---\s*)", re.S)


def dump_notebook(nb):
    """Serialize like Jupyter/VS Code do, so edits give minimal diffs."""
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


@dataclass
class Post:
    slug: str
    source: Path

    @property
    def dir(self):
        return self.source.parent

    @property
    def url(self):
        return f"{SITE_URL}/posts/{self.slug}/"

    def _read_block(self):
        """Return (container, key, text) of the front matter block."""
        if self.source.suffix == ".ipynb":
            nb = json.loads(self.source.read_text())
            return nb, 0, "".join(nb["cells"][0]["source"])
        return None, None, self.source.read_text()

    def meta(self):
        _, _, text = self._read_block()
        match = FRONT_MATTER.match(text)
        if not match:
            raise SystemExit(f"{self.source}: no front matter")
        return yaml.safe_load(match.group(2)) or {}

    def update_meta(self, set_fields=None, drop_fields=()):
        """Edit top-level front matter lines in place, keeping the rest verbatim."""
        container, _, text = self._read_block()
        match = FRONT_MATTER.match(text)
        lines = match.group(2).split("\n")
        kept = [line for line in lines if not any(re.match(rf"^{re.escape(f)}\s*:", line) for f in drop_fields)]
        for field, value in (set_fields or {}).items():
            if isinstance(value, bool):
                shown = "true" if value else "false"
            elif isinstance(value, str):
                shown = json.dumps(value, ensure_ascii=False)
            else:
                shown = value
            rendered = f"{field}: {shown}"
            for i, line in enumerate(kept):
                if re.match(rf"^{re.escape(field)}\s*:", line):
                    kept[i] = rendered
                    break
            else:
                kept.append(rendered)
        new_text = match.group(1) + "\n".join(kept) + match.group(3) + text[match.end():]
        if container is None:
            self.source.write_text(new_text)
        else:
            parts = re.split(r"(?<=\n)", new_text)
            container["cells"][0]["source"] = [p for p in parts if p]
            self.source.write_text(dump_notebook(container))


def find(slug):
    folder = POSTS / slug
    for name in ("index.ipynb", "index.qmd"):
        if (folder / name).exists():
            return Post(slug, folder / name)
    raise SystemExit(f"no post at posts/{slug}/ (expected index.ipynb or index.qmd)")


def all_posts():
    posts = []
    for folder in sorted(p for p in POSTS.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        for name in ("index.ipynb", "index.qmd"):
            if (folder / name).exists():
                posts.append(Post(folder.name, folder / name))
                break
    return posts


def slugify(title):
    slug = title.lower().replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return re.sub(r"-{2,}", "-", slug)
