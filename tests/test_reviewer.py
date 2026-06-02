import json
from types import SimpleNamespace

from ai_pr_reviewer.diff.chunker import ReviewChunk
from ai_pr_reviewer.review import reviewer


class _FakeMessages:
    def __init__(self, payload):
        self._payload = payload

    def create(self, **_kw):
        text = json.dumps(self._payload)
        return SimpleNamespace(content=[SimpleNamespace(text=text)])


class _FakeClient:
    def __init__(self, payload):
        self.messages = _FakeMessages(payload)


def _chunk():
    return ReviewChunk(
        path="app/math.py", language="python", diff="+def divide(a, b):\n+    return a / b",
        new_start=1, new_end=7,
    )


def test_parses_model_comments(monkeypatch):
    payload = {"comments": [{"line": 6, "severity": "error", "body": "ZeroDivisionError risk"}]}
    monkeypatch.setattr(reviewer, "_get_client", lambda: _FakeClient(payload))

    out = reviewer.review_chunks([_chunk()], {}, SimpleNamespace(model="m", temperature=0.0))
    assert len(out) == 1
    assert out[0].path == "app/math.py"
    assert out[0].severity == "error"
    assert out[0].line == 6


def test_handles_non_json(monkeypatch):
    class BadClient:
        messages = SimpleNamespace(
            create=lambda **_k: SimpleNamespace(content=[SimpleNamespace(text="not json")])
        )

    monkeypatch.setattr(reviewer, "_get_client", lambda: BadClient())
    out = reviewer.review_chunks([_chunk()], {}, SimpleNamespace(model="m", temperature=0.0))
    assert out == []
