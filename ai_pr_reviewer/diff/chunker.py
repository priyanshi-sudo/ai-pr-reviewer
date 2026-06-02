"""Group raw diff hunks into review-sized chunks.

We keep all hunks for a single file together when they fit under
~600 lines; otherwise we split by the topmost symbol boundary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatch

from ai_pr_reviewer.diff.parser import FileDiff, parse_unified_diff


@dataclass
class ReviewChunk:
    path: str
    language: str
    diff: str
    new_start: int
    new_end: int


_SYMBOL_RE = re.compile(r"^(?:\+\s*)?(?:def|class|function|fn|interface|public|export)\b")


def chunk_pr(unified_diff: str, ignore: list[str], max_lines: int = 600) -> list[ReviewChunk]:
    chunks: list[ReviewChunk] = []
    for file in parse_unified_diff(unified_diff):
        if any(fnmatch(file.path, pat) for pat in ignore):
            continue
        if file.is_binary or file.deleted:
            continue
        lang = _detect_lang(file.path)
        if file.added_lines <= max_lines:
            chunks.append(_to_chunk(file, lang))
        else:
            chunks.extend(_split_by_symbol(file, lang, max_lines))
    return chunks


def _detect_lang(path: str) -> str:
    if path.endswith(".py"):
        return "python"
    if path.endswith((".ts", ".tsx", ".js", ".jsx")):
        return "typescript"
    if path.endswith(".go"):
        return "go"
    if path.endswith(".rs"):
        return "rust"
    return "text"


def _to_chunk(file: FileDiff, language: str) -> ReviewChunk:
    return ReviewChunk(
        path=file.path,
        language=language,
        diff=file.raw,
        new_start=file.new_start,
        new_end=file.new_end,
    )


def _split_by_symbol(file: FileDiff, language: str, max_lines: int) -> list[ReviewChunk]:
    # Best-effort split. For very large files we fall back to fixed windows.
    lines = file.raw.splitlines(keepends=True)
    boundaries = [i for i, line in enumerate(lines) if _SYMBOL_RE.match(line)]
    if not boundaries:
        return [_window(file, language, lines, i, i + max_lines)
                for i in range(0, len(lines), max_lines)]
    out: list[ReviewChunk] = []
    boundaries.append(len(lines))
    for a, b in zip(boundaries, boundaries[1:]):
        if b - a > max_lines:
            for i in range(a, b, max_lines):
                out.append(_window(file, language, lines, i, min(i + max_lines, b)))
        else:
            out.append(_window(file, language, lines, a, b))
    return out


def _window(file: FileDiff, lang: str, lines: list[str], a: int, b: int) -> ReviewChunk:
    return ReviewChunk(
        path=file.path,
        language=lang,
        diff="".join(lines[a:b]),
        new_start=file.new_start + a,
        new_end=file.new_start + b,
    )
