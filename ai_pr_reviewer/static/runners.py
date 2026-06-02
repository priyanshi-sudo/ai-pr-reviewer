"""Run static analysis tools and normalise their output.

The LLM is told to only flag what these tools miss, so the value here is
breadth, not depth: run whatever linters the repo configured, collect
`{line, tool, message}` findings per file, and never hard-fail if a tool is
absent (CI runners vary).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections import defaultdict

from ai_pr_reviewer.diff.chunker import ReviewChunk


def run_static(chunks: list[ReviewChunk], linters) -> dict[str, list[dict]]:
    """Return {path: [{line, tool, message}, ...]} for the reviewed files."""
    findings: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        tools = _tools_for(chunk.language, linters)
        for tool in tools:
            runner = _RUNNERS.get(tool)
            if runner is None or shutil.which(tool.split()[0]) is None:
                continue
            findings[chunk.path].extend(runner(chunk.path))
    return dict(findings)


def _tools_for(language: str, linters) -> list[str]:
    if language == "python":
        return list(linters.python)
    if language == "typescript":
        return list(linters.typescript)
    return []


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _ruff(path: str) -> list[dict]:
    proc = _run(["ruff", "check", "--output-format=json", path])
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []
    return [
        {
            "line": (it.get("location") or {}).get("row", 0),
            "tool": "ruff",
            "message": f"{it.get('code', '')} {it.get('message', '')}".strip(),
        }
        for it in items
    ]


def _mypy(path: str) -> list[dict]:
    proc = _run(["mypy", "--no-error-summary", "--no-color-output", path])
    out: list[dict] = []
    for line in proc.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) >= 4 and parts[1].isdigit():
            out.append({"line": int(parts[1]), "tool": "mypy", "message": parts[3].strip()})
    return out


def _eslint(path: str) -> list[dict]:
    proc = _run(["eslint", "-f", "json", path])
    try:
        report = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []
    out: list[dict] = []
    for file_report in report:
        for msg in file_report.get("messages", []):
            out.append(
                {
                    "line": msg.get("line", 0),
                    "tool": "eslint",
                    "message": f"{msg.get('ruleId', '')} {msg.get('message', '')}".strip(),
                }
            )
    return out


_RUNNERS = {
    "ruff": _ruff,
    "mypy": _mypy,
    "eslint": _eslint,
}
