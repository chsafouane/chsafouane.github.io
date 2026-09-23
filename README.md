# chsafouane.github.io

Source of [chsafouane.github.io](https://chsafouane.github.io), a Quarto blog about LLM systems, evaluation, search and Python tooling.

## Setup (once)

- [Quarto](https://quarto.org/docs/download/) 1.10.18, the version CI uses.
- [uv](https://docs.astral.sh/uv/), then `uv sync --all-extras` in this folder (installs `figkit` and `blog`).
- `brew install librsvg` for the PNG exports of figures.

## Writing a post

```bash
uv run blog new "Why RoPE works"        # creates posts/why-rope-works/ as a draft
uv run blog preview why-rope-works      # live preview; figures rebuild when figures.py is saved
uv run blog publish why-rope-works      # checks, removes the draft flag, commits and pushes
```

1. **Start.**
   `blog new` creates `posts/<slug>/index.ipynb` (or `index.qmd` with `--qmd`) with front matter to fill in, marked `draft: true`, and a `figures.py` for the post's figures.
   Drafts can be committed and pushed: the live site does not render them, while the preview shows them.
2. **Write and draw.**
   Write in the notebook as usual.
   Draw figures in `posts/<slug>/figures.py` with figkit (see [tools/figkit/README.md](tools/figkit/README.md)) and show them in the post with `{{< fig name >}}` or `{{< stepper name >}}`.
   `blog preview` rebuilds a post's figures every time its `figures.py` is saved.
   Hand-drawn Keynote figures come in with `uv run figkit import`.
3. **Publish.**
   `blog publish <slug>` removes the draft flag, sets today's date, rebuilds the figures, runs `tools/check_posts.py` and a full render, then commits the post and pushes.
   If anything fails, the post goes back to draft and nothing is committed.
   The checks refuse `TODO` placeholders, a missing description or preview image, raw HTML layout, h1 headings in the body, lists glued to a paragraph, and figures whose files are missing.
   After the push, GitHub Actions checks the posts and figures again, renders the site and deploys it (about a minute).
4. **Cross-post.**
   Once the post is live, `uv run blog crosspost <slug>` renders it and prints its Medium import URL and its Substack page (see [Cross-posting](#cross-posting)).
   In Claude Code, `/publish-post <slug>` does steps 3 and 4: it publishes, waits for the deploy and gives the same two links.

## Cross-posting

`uv run blog crosspost <slug>` renders the post and writes two pages to `_site/crosspost/<slug>/`:

- `index.html`, for **Medium**.
  Medium has no API for new accounts, so you use its importer: on Medium, choose Import a story and paste `https://chsafouane.github.io/crosspost/<slug>/`.
  Medium sets the original date and a canonical link to the imported page; check in the story's advanced settings that the canonical link is the post URL, then publish.
- `substack.html`, for **Substack**.
  Open it in a browser: the command prints its `file://` link, and it is also online at `https://chsafouane.github.io/crosspost/<slug>/substack.html`.
  Start a new post on Substack, then use the page's Copy buttons for the title, the subtitle and the body, and paste each into the matching field.
  Substack has no canonical links, so publish on the blog first and on Substack a few days later; the body starts with an "Originally published at" link to the post.

Both pages contain what the two platforms can display: figures as PNG, steppers as one image per step with a link back to the interactive version, code as plain code blocks, callouts as quotes, tables as lists, and math as LaTeX code.
Neither platform renders math; on Substack, the LaTeX block can turn the code back into equations.
Images point to the live post, which Medium and Substack copy them from, so the command refuses drafts: cross-post once the post is published and deployed.
The pages are marked `noindex` and point to the post as canonical, so they never compete with it in search.
CI builds them for every post on each deploy, so the Medium URL works without running anything locally.

The same pages work for posts published before this workflow: re-import them on Medium, or replace figures by hand with the PNG files in `posts/<slug>/assets/figures/`.

## Layout

| Path | What it is |
|---|---|
| `posts/<slug>/` | a post: `index.ipynb` or `index.qmd`, `figures.py`, `assets/` |
| `_brand.yml`, `_theme/` | colors and fonts, SCSS theme, templates, filters |
| `_extensions/figkit/` | the `fig` and `stepper` shortcodes |
| `tools/figkit/` | the figure kit (`uv run figkit`) |
| `tools/blog/` | this workflow (`uv run blog`) |
| `tools/check_posts.py` | post conventions, also run in CI |
| `.claude/skills/publish-post/` | the `/publish-post` command for Claude Code |
| `.github/workflows/publish.yml` | checks, render, cross-post pages and deploy |
