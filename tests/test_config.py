from ai_pr_reviewer.config import load_config


def test_defaults_when_missing(tmp_path):
    cfg = load_config(tmp_path / "nope.yml")
    assert cfg.review.max_comments_per_pr == 25
    assert cfg.llm.model == "claude-sonnet-4-6"
    assert "pnpm-lock.yaml" in cfg.review.ignore


def test_overrides_from_file(tmp_path):
    p = tmp_path / ".ai-review.yml"
    p.write_text(
        "review:\n"
        "  max_comments_per_pr: 5\n"
        "llm:\n"
        "  model: claude-opus-4-8\n"
        "  temperature: 0.3\n"
    )
    cfg = load_config(p)
    assert cfg.review.max_comments_per_pr == 5
    assert cfg.llm.model == "claude-opus-4-8"
    assert cfg.llm.temperature == 0.3
