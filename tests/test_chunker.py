from pathlib import Path

from ai_pr_reviewer.diff.chunker import chunk_pr

DIFF = (Path(__file__).parent / "fixtures" / "sample.diff").read_text()


def test_chunks_only_reviewable_files():
    chunks = chunk_pr(DIFF, ignore=["pnpm-lock.yaml"])
    paths = [c.path for c in chunks]
    # lockfile ignored, binary skipped, deleted skipped — only the .py remains.
    assert paths == ["app/math.py"]
    assert chunks[0].language == "python"


def test_glob_ignore_patterns():
    chunks = chunk_pr(DIFF, ignore=["*.yaml", "*.py"])
    assert chunks == []
