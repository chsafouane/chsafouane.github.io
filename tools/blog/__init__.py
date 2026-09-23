"""blog: the writing workflow for chsafouane.github.io.

  uv run blog new "Title"       start a post (draft) with a figures.py stub
  uv run blog preview [SLUG]    live preview, figures rebuilt on save
  uv run blog publish SLUG      check, un-draft, commit and push (CI deploys)
  uv run blog crosspost [SLUG]  Medium import page and Substack copy page of a post

See README.md at the repository root.
"""
