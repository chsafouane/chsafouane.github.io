"""`blog publish`: take a draft live (CI deploys after the push)."""

import datetime
import shutil
import subprocess
import sys

from figkit.cli import build as build_figures

from .posts import REPO, find


def _run(*args, check=True, capture=False):
    return subprocess.run(args, cwd=REPO, check=check, text=True, capture_output=capture)


def _git(*args):
    return _run("git", *args, capture=True).stdout.strip()


def publish(slug, push=True, keep_date=False, allow_branch=False):
    post = find(slug)
    meta = post.meta()
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "master" and not allow_branch:
        raise SystemExit(f"you are on '{branch}': publish from master (or pass --allow-branch)")
    was_draft = bool(meta.get("draft"))
    fields = {} if keep_date else {"date": datetime.datetime.now().astimezone().date().isoformat()}
    post.update_meta(set_fields=fields, drop_fields=("draft",))
    print(f"publishing {slug}: draft flag removed" + ("" if keep_date else f", date set to {fields['date']}"))

    def undo(reason):
        if was_draft:
            post.update_meta(set_fields={"draft": True})
        raise SystemExit(f"not published: {reason}. The post is back to draft.")

    if (post.dir / "figures.py").exists():
        build_figures([slug])
    checks = _run(sys.executable, "tools/check_posts.py", check=False, capture=True)
    print(checks.stdout.strip())
    if checks.returncode != 0:
        undo("tools/check_posts.py found problems (fix the TODOs and missing fields above)")
    quarto = shutil.which("quarto") or undo("quarto is not installed")
    print("rendering the site to check that it builds...")
    render = _run(quarto, "render", check=False, capture=True)
    if render.returncode != 0:
        print(render.stdout[-3000:], render.stderr[-3000:])
        undo("quarto render failed")

    _run("git", "add", "--", f"posts/{slug}")
    title = post.meta().get("title", slug)
    _run("git", "commit", "-m", f'Publish "{title}"', "--", f"posts/{slug}")
    if push:
        _run("git", "push", "origin", branch)
        print(f"pushed: CI deploys {post.url} in about a minute")
    else:
        print("committed; push when ready (git push)")
    print(f"then cross-post: uv run blog crosspost {slug}  (or /publish-post in Claude Code)")
