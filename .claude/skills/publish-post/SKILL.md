---
name: publish-post
description: Publish a draft post of chsafouane.github.io and prepare its Medium and Substack cross-posts, or prepare cross-posts for a post that is already live. Use when the user asks to publish, release or cross-post a blog post.
---

# Publish a post and cross-post it

The argument is a post slug (a folder under `posts/`). Without one, list the drafts (front matter `draft: true`) and ask which post to publish.
The workflow and its commands are described in `README.md` at the repository root.

## 1. Publish on the blog (skip if the post is already live)

1. Check the post: show its title, description, categories and preview image, and run `python3 tools/check_posts.py`.
   A draft may still contain `TODO` placeholders from `blog new`; list them so the user can fill them in first.
2. Publishing makes the post public and pushes to master.
   Ask the user to confirm before running it.
3. Run `uv run blog publish <slug>`.
   It removes `draft: true`, sets today's date, rebuilds the figures, runs the checks and a full render, commits and pushes.
   If it stops, show why; it puts the draft flag back on failure.
4. Wait for the deploy: `gh run watch <id> --repo chsafouane/chsafouane.github.io --exit-status` for the newest run on master.
   Then check that the post URL and `https://chsafouane.github.io/crosspost/<slug>/` both return 200.

## 2. Build the cross-post versions

Run `quarto render` if `_site` is missing or older than the post, then `uv run blog crosspost <slug>`.
This writes `_site/crosspost/<slug>/meta.json`, `post.md` (Substack) and `index.html` (Medium).

## 3. Substack draft

Substack has no canonical links, so the blog post must be live first; suggest publishing on Substack a few days later.

1. If the `substack` MCP tools are not available, point the user to the "Substack" section of `README.md` (one-time login) and give them the path of `post.md`. Stop this step there.
2. Read `meta.json` and `post.md`.
   Call `create_draft` with the title, the subtitle and `post.md` as the Markdown body.
3. If it returns `unsupported_markdown`, show the diagnostics (tables and math end up as code blocks).
   Retry with `allow_unsupported: true` only after the user agrees.
4. Run `preflight_draft` on the draft and report its findings and the editor link.
   The server cannot publish long-form posts: the user reviews and publishes in Substack's editor.

## 4. Medium

Medium's API no longer gives out tokens, so the last step is manual. Give the user:

1. The import URL from `meta.json` (`medium_import_url`).
2. The steps: on Medium, open Your stories, choose Import a story, paste the URL and import.
3. Before publishing: in the story settings (Advanced settings, canonical link), make sure the canonical link is the post URL (`post_url` in `meta.json`), not the `/crosspost/` URL.
   Medium's importer usually sets it to the imported URL.

## 5. Summary

End with the live post URL, the Substack draft link (or why it was skipped) and the Medium import URL.
