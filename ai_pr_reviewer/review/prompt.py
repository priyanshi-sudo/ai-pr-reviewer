REVIEW_SYSTEM = """You are a senior code reviewer.

You will see a unified diff for a single file (or a slice of one) and the
output of static analysis tools that already ran on it.

Rules:
- Only flag issues the static tools missed.
- Prefer specific, actionable feedback. No "consider refactoring" without
  saying what to refactor and why.
- Severity: "error" = bug or security issue; "warn" = correctness risk or
  smell; "info" = nice-to-have.
- Use new-file line numbers from the diff (the + side).
- Output strict JSON: {"comments": [{"line": int, "severity": str, "body": str}]}.
- If nothing is worth saying, return {"comments": []}.
"""


def build_user(chunk, static_findings: list[dict]) -> str:
    sf = (
        "\n".join(f"- L{f['line']} [{f['tool']}]: {f['message']}" for f in static_findings)
        or "(none)"
    )
    return (
        f"FILE: {chunk.path}\n"
        f"LANGUAGE: {chunk.language}\n\n"
        f"STATIC FINDINGS:\n{sf}\n\n"
        f"DIFF:\n```diff\n{chunk.diff}\n```\n"
    )
