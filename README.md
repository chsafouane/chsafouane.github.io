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
   It also lists the post under the current year in the sidebar (`website.sidebar` in `_quarto.yml`), the site's left column; drafts stay out of it until they are published.
   Drafts can be committed and pushed: the live site does not render them, while the preview shows them.
2. **Write and draw.**
   Write in the notebook as usual.
   Draw figures and interactive charts in `posts/<slug>/figures.py` with figkit (see [tools/figkit/README.md](tools/figkit/README.md)) and show them in the post with `{{< fig name >}}`, `{{< stepper name >}}` or `{{< chart name >}}`.
   `blog preview` rebuilds a post's figures every time its `figures.py` is saved.
   Hand-drawn Keynote figures come in with `uv run figkit import`.
3. **Publish.**
   `blog publish <slug>` removes the draft flag, sets today's date, rebuilds the figures, runs `tools/check_posts.py` and a full render, then commits the post and pushes.
   If anything fails, the post goes back to draft and nothing is committed.
   The checks refuse `TODO` placeholders, a missing description or preview image, raw HTML layout, h1 headings in the body, lists glued to a paragraph, figures or charts whose files are missing, and published posts missing from the sidebar.
   After the push, GitHub Actions checks the posts and figures again, renders the site and deploys it (about a minute).
4. **Cross-post.**
   Once the post is live, add `crosspost: true` to its front matter and push: CI then puts its Medium and Substack pages online.
   `uv run blog crosspost <slug>` prints the Medium import URL and the Substack page (see [Cross-posting](#cross-posting)).
   Once the post is on both platforms, remove the flag and push again: the pages go offline, and only the post stays.
   In Claude Code, `/publish-post <slug>` does steps 3 and 4.

## Cross-posting

`uv run blog crosspost <slug>` renders the post and writes its pages to `_site/crosspost/<slug>/`.
CI publishes them only for posts with `crosspost: true` in their front matter, because Medium's importer needs a public URL; remove the flag once the post is cross-posted.

- `medium-<version>.html`, for **Medium**.
  Medium has no API for new accounts, so you use its importer: on Medium, choose Import a story and paste the URL the command prints.
  Medium caches every import by URL, query string included, so the file name changes whenever the post or the cross-post tool changes.
  In the draft, delete the empty code block Medium adds after each code block (a bug of its importer that no markup avoids); indentation comes through as tabs.
  Medium sets the original date and a canonical link to the imported page; check in the story's advanced settings that the canonical link is the post URL, then publish.
- `substack.html`, for **Substack**.
  Open it in a browser: the command prints its `file://` link (while the post has the flag, it is also online at `https://chsafouane.github.io/crosspost/<slug>/substack.html`).
  Start a new post on Substack, then use the page's Copy buttons for the title, the subtitle and the body, and paste each into the matching field.
  Substack has no canonical links, so publish on the blog first and on Substack a few days later; the body starts with an "Originally published at" link to the post.

Both pages contain what the two platforms can display: figures as PNG, steppers as one image per step with a link back to the interactive version, charts as an image with a link back to the interactive chart, code as plain code blocks, callouts as quotes, tables as lists, and math as LaTeX code.
Charts are drawn in the browser, so their images are snapshots you take once a post's charts are final, and commit with the post:

```bash
uv run --with playwright blog chart-images <slug>   # writes posts/<slug>/assets/charts/<name>.png
```

It uses Brave or Chrome if installed (otherwise run `uv run --with playwright playwright install chromium` once).
Each snapshot records the chart spec it was taken from, and `tools/check_posts.py` fails when the chart changed since, so re-run the command after editing a chart.
A chart without a snapshot shows its data table instead.
Neither platform renders math; on Substack, the LaTeX block can turn the code back into equations.
Images point to the live post, which Medium and Substack copy them from, so the command refuses drafts: cross-post once the post is published and deployed.
The pages are marked `noindex` and point to the post as canonical, so they never compete with it in search.
CI builds them for every post on each deploy, so the Medium URL works without running anything locally.

The same pages work for posts published before this workflow: re-import them on Medium, or replace figures by hand with the PNG files in `posts/<slug>/assets/figures/`.

## Layout

| Path | What it is |
|---|---|
| `posts/<slug>/` | a post: `index.ipynb` or `index.qmd`, `figures.py`, `assets/` |
| `_brand.yml`, `_theme/` | colors and fonts, SCSS theme (the Jev Field Guide look: left sidebar, cards, IBM Plex), templates, filters, `site.html` (sidebar table of contents, drawer button, long code blocks) |
| `_quarto-preview.yml` | the profile `blog preview` uses, so drafts show from the first render (plain `quarto preview` empties them until the first save) |
| `_extensions/figkit/` | the `fig` and `stepper` shortcodes |
| `_extensions/chartkit/` | the `chart` shortcode and the chart drawing code |
| `tools/figkit/` | the figure and chart kit (`uv run figkit`) |
| `tools/blog/` | this workflow (`uv run blog`) |
| `tools/check_posts.py` | post conventions, also run in CI |
| `.claude/skills/publish-post/` | the `/publish-post` command for Claude Code |
| `.github/workflows/publish.yml` | checks, render, cross-post pages and deploy |
