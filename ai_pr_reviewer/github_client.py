"""Minimal GitHub REST client scoped to what the reviewer needs."""
from __future__ import annotations

import json
import os

import httpx

API = "https://api.github.com"


class GH:
    def __init__(self, token: str, repo: str):
        self.repo = repo  # "owner/name"
        self._client = httpx.Client(
            base_url=API,
            headers={
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ai-pr-reviewer",
            },
            timeout=30,
        )

    # -- reads ---------------------------------------------------------------

    def detect_pr_from_event(self) -> int | None:
        """Pull the PR number out of the Action's event payload, if present."""
        path = os.environ.get("GITHUB_EVENT_PATH")
        if not path or not os.path.exists(path):
            return None
        with open(path) as fh:
            event = json.load(fh)
        pr = event.get("pull_request") or {}
        number = pr.get("number") or event.get("number")
        return int(number) if number else None

    def get_pr_diff(self, pr: int) -> str:
        resp = self._client.get(
            f"/repos/{self.repo}/pulls/{pr}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        resp.raise_for_status()
        return resp.text

    def get_pr_head_sha(self, pr: int) -> str:
        resp = self._client.get(f"/repos/{self.repo}/pulls/{pr}")
        resp.raise_for_status()
        return resp.json()["head"]["sha"]

    # -- writes --------------------------------------------------------------

    def create_review(self, pr: int, commit_id: str, comments: list[dict], body: str) -> None:
        """Post a single review carrying all line comments."""
        resp = self._client.post(
            f"/repos/{self.repo}/pulls/{pr}/reviews",
            json={
                "commit_id": commit_id,
                "event": "COMMENT",
                "body": body,
                "comments": comments,
            },
        )
        resp.raise_for_status()
