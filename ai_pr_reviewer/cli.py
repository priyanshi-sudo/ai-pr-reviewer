"""Entry point — runs in the GitHub Action."""
from __future__ import annotations

import os
import sys

import click

from ai_pr_reviewer.config import load_config
from ai_pr_reviewer.diff.chunker import chunk_pr
from ai_pr_reviewer.github_client import GH
from ai_pr_reviewer.review.poster import post_comments
from ai_pr_reviewer.review.reviewer import review_chunks
from ai_pr_reviewer.static.runners import run_static


@click.command()
@click.option("--repo", envvar="GITHUB_REPOSITORY")
@click.option("--pr", envvar="PR_NUMBER", type=int, default=None)
@click.option("--config", default=".ai-review.yml")
def main(repo: str, pr: int | None, config: str):
    cfg = load_config(config)
    gh = GH(token=os.environ["GITHUB_TOKEN"], repo=repo)

    if pr is None:
        pr = gh.detect_pr_from_event()
        if pr is None:
            click.echo("not a PR event — exiting")
            sys.exit(0)

    diff = gh.get_pr_diff(pr)
    chunks = chunk_pr(diff, ignore=cfg.review.ignore)
    if not chunks:
        click.echo("nothing to review")
        return

    static_findings = run_static(chunks, cfg.linters)
    comments = review_chunks(chunks, static_findings, cfg.llm)
    comments = comments[: cfg.review.max_comments_per_pr]
    post_comments(gh, pr, comments)


if __name__ == "__main__":
    main()
