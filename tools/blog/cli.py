"""Command line: `uv run blog <command>`. See README.md at the repository root."""

import argparse
import json
import sys

from .posts import REPO, SITE_URL


def main(argv=None):
    parser = argparse.ArgumentParser(prog="blog", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="start a draft post with a figures.py stub")
    new.add_argument("title")
    new.add_argument("--slug", help="folder name (default: derived from the title)")
    new.add_argument("--qmd", action="store_true", help="write index.qmd instead of index.ipynb")

    preview = sub.add_parser("preview", help="quarto preview, with figures rebuilt on save")
    preview.add_argument("slug", nargs="?", help="preview only this post (default: the whole site)")
    preview.add_argument("--no-browser", action="store_true", help="do not open a browser")

    publish = sub.add_parser("publish", help="un-draft, check, render, commit and push a post")
    publish.add_argument("slug")
    publish.add_argument("--no-push", action="store_true", help="commit but do not push")
    publish.add_argument("--keep-date", action="store_true", help="keep the date in the front matter")
    publish.add_argument("--allow-branch", action="store_true", help="allow publishing from a branch other than master")

    cross = sub.add_parser("crosspost", help="write Medium and Substack versions of rendered posts into _site/crosspost")
    cross.add_argument("slugs", nargs="*", help="posts to process (default: all published posts)")

    args = parser.parse_args(argv)
    if args.command == "new":
        from .scaffold import new_post

        folder = new_post(args.title, args.slug, "qmd" if args.qmd else "ipynb")
        rel = folder.relative_to(REPO)
        print(f"created {rel}/ (draft). Next: uv run blog preview {folder.name}")
    elif args.command == "preview":
        from .preview import preview

        preview(args.slug, browser=not args.no_browser)
    elif args.command == "publish":
        from .publish import publish

        publish(args.slug, push=not args.no_push, keep_date=args.keep_date, allow_branch=args.allow_branch)
    elif args.command == "crosspost":
        from .crosspost import SITE, build

        if not (SITE / "index.html").exists():
            raise SystemExit("render the site first: quarto render")
        written = build(args.slugs)
        for slug in written:
            meta = json.loads((SITE / "crosspost" / slug / "meta.json").read_text())
            print(f"{slug}\n  Medium import URL: {meta['medium_import_url']}\n  Substack Markdown: _site/crosspost/{slug}/post.md")
        if not written:
            print("nothing written: are the posts published and rendered in _site?")
        print(f"(URLs are live after the next deploy of {SITE_URL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
