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

## 2. Build the cross-post pages

Run `uv run blog crosspost <slug>`.
It renders the post and writes `_site/crosspost/<slug>/index.html` (Medium) and `substack.html` (Substack), then prints both links.
It refuses drafts, because Medium and Substack copy the images from the live post.

Posting on Medium and Substack is manual: nothing here signs in to either account.

## 3. Medium

Give the user:

1. The import URL `https://chsafouane.github.io/crosspost/<slug>/`.
2. The steps: on Medium, open Your stories, choose Import a story, paste the URL and import.
3. Before publishing: in the story settings (Advanced settings, canonical link), make sure the canonical link is the post URL `https://chsafouane.github.io/posts/<slug>/`, not the `/crosspost/` URL.
   Medium's importer usually sets it to the imported URL.

## 4. Substack

Substack has no canonical links, so the blog post must be live first; suggest publishing on Substack a few days later.
Give the user the `file://` link of `substack.html` printed by the command (also online at `https://chsafouane.github.io/crosspost/<slug>/substack.html`) and the steps: start a new post on Substack, then use the page's Copy buttons for the title, the subtitle and the body, and paste each into the matching field.
If the post has math, mention that it arrives as LaTeX code, which Substack's LaTeX block can turn into equations.

## 5. Summary

End with the live post URL, the Medium import URL and the Substack page link.
