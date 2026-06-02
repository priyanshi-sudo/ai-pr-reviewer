from pathlib import Path

from ai_pr_reviewer.diff.parser import parse_unified_diff

DIFF = (Path(__file__).parent / "fixtures" / "sample.diff").read_text()


def test_parses_each_file():
    files = {f.path: f for f in parse_unified_diff(DIFF)}
    assert set(files) == {"app/math.py", "pnpm-lock.yaml", "assets/logo.png", "old.py"}


def test_flags_binary_added_deleted():
    files = {f.path: f for f in parse_unified_diff(DIFF)}
    assert files["assets/logo.png"].is_binary
    assert files["assets/logo.png"].added
    assert files["old.py"].deleted


def test_counts_added_lines_excluding_header():
    files = {f.path: f for f in parse_unified_diff(DIFF)}
    # 3 real additions (blank, blank, def, return) minus the +++ header line.
    assert files["app/math.py"].added_lines == 4
    assert files["app/math.py"].new_start == 1
