"""Turn LineComment objects into a single GitHub PR review."""
from __future__ import annotations

from ai_pr_reviewer.github_client import GH
from ai_pr_reviewer.review.reviewer import LineComment

_SEVERITY_EMOJI = {"error": "🔴", "warn": "🟡", "info": "🔵"}


def _format(comment: LineComment) -> dict:
    badge = _SEVERITY_EMOJI.get(comment.severity, "🔵")
    return {
        "path": comment.path,
        "line": comment.line,
        "side": "RIGHT",
        "body": f"{badge} **{comment.severity}** — {comment.body}",
    }


def post_comments(gh: GH, pr: int, comments: list[LineComment]) -> None:
    if not comments:
        return
    head_sha = gh.get_pr_head_sha(pr)
    payload = [_format(c) for c in comments]
    counts = {sev: sum(1 for c in comments if c.severity == sev)
              for sev in ("error", "warn", "info")}
    summary = (
        "🤖 **AI review** — "
        f"{counts['error']} error · {counts['warn']} warn · {counts['info']} info"
    )
    gh.create_review(pr, head_sha, payload, summary)
