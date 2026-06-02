# AI PR Reviewer Bot

> A GitHub Action + standalone Python tool that reads a pull request diff, runs static analysis, and posts a structured LLM review as line-anchored PR comments. Built to **save senior engineer time** on first-pass reviews.

![Stack](https://img.shields.io/badge/Python-3.11-yellow) ![Stack](https://img.shields.io/badge/GitHub_Action-ready-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## How this is different from "ChatGPT reviewed my PR"

Most LLM review bots blindly pipe the whole diff into a model. This one:

1. **Parses the diff and chunks by file + symbol** so reviews stay on-target.
2. **Runs lint / type-check first** (`ruff`, `mypy`, `eslint`) and feeds the LLM those findings — the model is told to comment only on what static tools *missed*.
3. **Posts line-anchored review comments**, not a wall-of-text.
4. **Skips files it shouldn't review** (lockfiles, snapshots, migrations) via configurable globs.
5. **Self-rate-limits** with a `max_comments_per_pr` cap.

## How it works

```
PR diff ──► parse_unified_diff ──► chunk_pr (by file/symbol, glob-filtered)
                                       │
                       run_static (ruff/mypy/eslint per file)
                                       │
                       review_chunks (Claude → JSON line comments)
                                       │
                       post_comments ──► single GitHub PR review
```

## Use it in any repo

Drop this in `.github/workflows/ai-review.yml`:

```yaml
name: AI Review
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e .
      - run: ai-pr-review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
```

## CLI

```bash
pip install -e ".[dev]"
ai-pr-review --repo owner/name --pr 42      # or rely on GitHub Action env vars
```

| Env | Purpose |
|---|---|
| `GITHUB_TOKEN` | Read the diff, post the review |
| `ANTHROPIC_API_KEY` | LLM review pass |
| `GITHUB_REPOSITORY`, `PR_NUMBER`, `GITHUB_EVENT_PATH` | Auto-detected in Actions |

## Configuration (`.ai-review.yml`)

Everything has a sane default, so the bot runs with no config at all.

```yaml
review:
  ignore:
    - "**/*.lock"
    - "**/__snapshots__/**"
    - "pnpm-lock.yaml"
    - "**/migrations/**"
  max_comments_per_pr: 25
  severity_threshold: "info"   # info | warn | error
linters:
  python: ["ruff", "mypy"]
  typescript: ["eslint"]
llm:
  model: "claude-sonnet-4-6"
  temperature: 0.0
```

## Project structure

```
ai_pr_reviewer/
  __init__.py
  cli.py                   # entrypoint (click)
  config.py                # .ai-review.yml → pydantic models
  github_client.py         # diff fetch + create-review (httpx)
  diff/
    parser.py              # dependency-free unified-diff parser
    chunker.py             # group hunks into reviewable units
  static/
    runners.py             # ruff / mypy / eslint, normalised findings
  review/
    prompt.py
    reviewer.py            # LLM call + JSON parsing (lazy client)
    poster.py              # severity-badged PR review
tests/
  fixtures/sample.diff
  test_parser.py  test_chunker.py  test_reviewer.py  test_config.py
.github/workflows/
  ci.yml  release.yml
```

## Severity levels

`error` = bug or security issue · `warn` = correctness risk or smell · `info` = nice-to-have. Each posted comment is prefixed with a colour badge.

## Testing

```bash
pip install -e ".[dev]"
pytest -q          # parser, chunker, config, reviewer (mocked LLM)
ruff check ai_pr_reviewer tests
```

CI runs the same on every push/PR; tagging `v*` publishes to PyPI via trusted publishing (`release.yml`).

## Roadmap

- [ ] Self-hosted models (Ollama)
- [ ] Per-team style guide ingestion
- [ ] Auto-suggest patches via `suggestion` blocks

## License

MIT — see [LICENSE](LICENSE).
