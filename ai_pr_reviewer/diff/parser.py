"""A small, dependency-free unified-diff parser.

We only need the slice of the diff format that review tooling cares about:
the new-file path, whether the file was added/deleted/binary, the raw text of
the file's diff, and the line range the new side spans.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_DIFF_GIT = re.compile(r"^diff --git a/(?P<a>.+?) b/(?P<b>.+)$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


@dataclass
class FileDiff:
    path: str
    raw: str = ""
    is_binary: bool = False
    deleted: bool = False
    added: bool = False
    new_start: int = 0
    new_end: int = 0
    _lines: list[str] = field(default_factory=list, repr=False)

    @property
    def added_lines(self) -> int:
        """Count of added (`+`) lines, excluding the `+++` file header."""
        return sum(
            1
            for line in self._lines
            if line.startswith("+") and not line.startswith("+++")
        )


def parse_unified_diff(unified_diff: str) -> list[FileDiff]:
    """Split a multi-file unified diff into per-file :class:`FileDiff` objects."""
    files: list[FileDiff] = []
    current: FileDiff | None = None

    def finalize(fd: FileDiff | None) -> None:
        if fd is None:
            return
        fd.raw = "\n".join(fd._lines)
        files.append(fd)

    for line in unified_diff.splitlines():
        m = _DIFF_GIT.match(line)
        if m:
            finalize(current)
            current = FileDiff(path=m.group("b"))
            current._lines.append(line)
            continue
        if current is None:
            continue

        current._lines.append(line)

        if line.startswith("Binary files"):
            current.is_binary = True
        elif line.startswith("deleted file mode"):
            current.deleted = True
        elif line.startswith("new file mode"):
            current.added = True
        elif line.startswith("+++ "):
            # `+++ /dev/null` means the new side is empty → file deleted.
            if line.strip() == "+++ /dev/null":
                current.deleted = True
            else:
                current.path = line[4:].removeprefix("b/").strip()
        else:
            hunk = _HUNK.match(line)
            if hunk:
                start = int(hunk.group("start"))
                count = int(hunk.group("count") or 1)
                if current.new_start == 0:
                    current.new_start = start
                current.new_end = max(current.new_end, start + count)

    finalize(current)
    return files
