"""Command line: `uv run blog <command>`. See README.md at the repository root."""

import argparse
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

    cross = sub.add_parser("crosspost", help="render posts and write their Medium and Substack pages into _site/crosspost")
    cross.add_argument("slugs", nargs="*", help="published posts to process (default: all of them)")
    cross.add_argument("--no-render", action="store_true", help="use the posts already rendered in _site")

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

        written = build(args.slugs, render=not args.no_render)
        for post in written:
            page = SITE / "crosspost" / post.slug / "substack.html"
            print(post.slug)
            print(f"  Medium:   Import a story, with the URL {SITE_URL}/crosspost/{post.slug}/")
            print(f"  Substack: open {page.as_uri()} and use its Copy buttons")
        if not written:
            print("nothing written: no published post is rendered in _site")
        else:
            print("Both work once the post is deployed: Medium and Substack copy the images from the live post.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
