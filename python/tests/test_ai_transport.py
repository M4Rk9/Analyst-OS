import json

import pytest
from analyst_os_ai import ollama


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), 0, 301])
def test_nonfinite_and_out_of_bounds_timeout_rejected(timeout):
    with pytest.raises(ollama.OllamaSecurityError, match="timeout"):
        ollama.generate_json(
            model="test:1", system_prompt="", user_prompt="", timeout_seconds=timeout
        )


def test_redirect_to_nonlocal_endpoint_is_rejected():
    with pytest.raises(ollama.OllamaSecurityError, match="redirects"):
        ollama.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")


def test_response_limit_and_no_proxy_inheritance(monkeypatch):
    handlers = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return b"x" * limit

    class Opener:
        def open(self, *args, **kwargs):
            return Response()

    def opener(*supplied):
        handlers.extend(supplied)
        return Opener()

    monkeypatch.setattr(ollama, "build_opener", opener)
    with pytest.raises(ValueError, match="bounded limit"):
        ollama.generate_json(model="test:1", system_prompt="", user_prompt="")
    assert handlers[0].proxies == {}
    assert isinstance(handlers[1], ollama.NoRedirect)


def test_model_digest_requires_exact_installed_tag(monkeypatch):
    monkeypatch.setattr(
        ollama,
        "local_response",
        lambda *_: {
            "models": [
                {"name": "test:1", "digest": "b" * 64, "size": 1000, "details": {"format": "gguf"}}
            ]
        },
    )
    assert ollama.model_digest("test:1") == "b" * 64
    with pytest.raises(ValueError, match="exact local model"):
        ollama.model_digest("test")


def test_cli_driver_errors_do_not_expose_credentials(monkeypatch, tmp_path, capsys):
    from scripts import ai_insights

    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_insights",
            "receipt",
            "--ssl-root-cert",
            "test.pem",
            "--output-dir",
            str(tmp_path / "new"),
            "--receipt-import-id",
            "00000000-0000-0000-0000-000000000001",
        ],
    )

    def broken(*_):
        raise RuntimeError("postgresql://SECRET_PASSWORD@example.invalid")

    monkeypatch.setattr(ai_insights, "connect", broken)
    assert ai_insights.main() == 1
    assert "SECRET_PASSWORD" not in capsys.readouterr().err


def test_local_json_remains_an_object(monkeypatch):
    monkeypatch.setattr(ollama, "local_response", lambda *_: {"response": json.dumps([])})
    with pytest.raises(ValueError, match="JSON object"):
        ollama.generate_json(model="test:1", system_prompt="", user_prompt="")
