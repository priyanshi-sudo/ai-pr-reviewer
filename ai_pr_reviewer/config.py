"""Load and validate `.ai-review.yml`.

Everything has a sane default so the bot runs in a repo with no config file at
all — the YAML only needs to override what a team wants to change.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ReviewConfig(BaseModel):
    ignore: list[str] = Field(
        default_factory=lambda: ["**/*.lock", "**/__snapshots__/**", "pnpm-lock.yaml"]
    )
    max_comments_per_pr: int = 25
    severity_threshold: str = "info"  # info | warn | error


class LinterConfig(BaseModel):
    python: list[str] = Field(default_factory=lambda: ["ruff"])
    typescript: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.0


class Config(BaseModel):
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    linters: LinterConfig = Field(default_factory=LinterConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


def load_config(path: str | Path = ".ai-review.yml") -> Config:
    p = Path(path)
    if not p.exists():
        return Config()
    data = yaml.safe_load(p.read_text()) or {}
    return Config.model_validate(data)
