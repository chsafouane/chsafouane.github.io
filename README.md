# chsafouane.github.io

Source of [chsafouane.github.io](https://chsafouane.github.io), a Quarto blog about LLM systems, evaluation, search and Python tooling.

## Setup (once)

- [Quarto](https://quarto.org/docs/download/) 1.10.18, the version CI uses.
- [uv](https://docs.astral.sh/uv/), then `uv sync --all-extras` in this folder (installs `figkit` and `blog`).
- `brew install librsvg` for the PNG exports of figures.
- Optional: Substack drafts from Claude Code, see [Substack](#substack).

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
   In Claude Code, `/publish-post <slug>` does steps 3 and 4: it publishes, waits for the deploy, creates the Substack draft and gives the Medium import link.
   Without Claude Code, `uv run blog crosspost <slug>` after `quarto render` prints the same links.

## Cross-posting

Every deploy also publishes a cross-post version of each post at `https://chsafouane.github.io/crosspost/<slug>/`: figures as PNG, steppers as one image per step with a link back to the interactive version, code as plain code blocks, callouts as quotes, and math as LaTeX code (neither Medium nor Substack renders math).
These pages are marked `noindex` and point to the post as canonical, so they never compete with it in search.

- **Medium** has no API for new accounts, so its last step is manual.
  On Medium, choose Import a story and paste `https://chsafouane.github.io/crosspost/<slug>/`.
  Medium sets the original date and a canonical link to the imported page; check in the story's advanced settings that the canonical link is the post URL, then publish.
- **Substack** has no canonical links, so publish on the blog first and on Substack a few days later.
  `/publish-post` creates a Substack draft from `_site/crosspost/<slug>/post.md`; review and publish it in Substack's editor.
  Tables become code blocks there.

The same pages work for posts published before this workflow: re-import them on Medium, or replace figures by hand with the PNG files in `posts/<slug>/assets/figures/`.

## Substack

Substack drafts use [substack-mcp](https://github.com/conorbronsdon/substack-mcp) (configured in `.mcp.json`, pinned to 1.2.1).
It works with Substack's undocumented API and can only create and edit drafts; publishing stays in Substack's editor.
It signs in with your Substack session, which gives full access to your account, so the session is stored encrypted on your machine and never in this repository.

Sign in once (needs Node.js 22 or newer; a browser window opens for the Substack login):

```bash
mkdir -p ~/.substack-mcp-tools && cd ~/.substack-mcp-tools
npm install @conorbronsdon/substack-mcp@1.2.1 playwright
npx playwright install chromium
npx substack-mcp login https://YOUR-PUBLICATION.substack.com --user-id YOUR_USER_ID
npx substack-mcp doctor --json --check-auth
```

`YOUR_USER_ID` is the numeric ID of your own Substack account (not a post's byline ID); while signed in, it is the `id` field of <https://substack.com/api/v1/user/profile/self>.
Then restart Claude Code and approve the `substack` server from `.mcp.json` when asked.
When the session expires, run the `login` command again.

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
