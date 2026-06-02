"""LLM review pass — returns structured line comments."""
from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from ai_pr_reviewer.diff.chunker import ReviewChunk
from ai_pr_reviewer.review.prompt import REVIEW_SYSTEM, build_user

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Build the Anthropic client lazily so importing this module (e.g. in
    tests) doesn't require ANTHROPIC_API_KEY to be present."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


@dataclass
class LineComment:
    path: str
    line: int
    severity: str        # info | warn | error
    body: str


def review_chunks(
    chunks: list[ReviewChunk], static_findings: dict, llm_cfg
) -> list[LineComment]:
    out: list[LineComment] = []
    for chunk in chunks:
        prompt = build_user(chunk, static_findings.get(chunk.path, []))
        resp = _get_client().messages.create(
            model=llm_cfg.model,
            max_tokens=1500,
            system=REVIEW_SYSTEM,
            temperature=llm_cfg.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            parsed = json.loads(resp.content[0].text)
        except json.JSONDecodeError:
            continue
        for c in parsed.get("comments", []):
            out.append(
                LineComment(
                    path=chunk.path,
                    line=int(c["line"]),
                    severity=c.get("severity", "info"),
                    body=c["body"],
                )
            )
    return out
