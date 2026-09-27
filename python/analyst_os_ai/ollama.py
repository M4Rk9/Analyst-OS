"""Minimal localhost-only Ollama client for offline analysis."""

import json
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


class OllamaSecurityError(ValueError):
    """Raised when Ollama configuration violates the local-only boundary."""


def validate_local_ollama_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_HOSTS:
        raise OllamaSecurityError("Ollama URL must use HTTP on localhost only")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OllamaSecurityError("Ollama URL may not contain credentials, query, or fragment")
    if parsed.path not in {"", "/"}:
        raise OllamaSecurityError("Ollama base URL must not include an application path")
    return base_url.rstrip("/")


def generate_json(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    base_url: str = DEFAULT_OLLAMA_URL,
    timeout_seconds: float = 120.0,
) -> dict[str, object]:
    """Call local Ollama and decode its JSON-formatted model response."""

    if not MODEL_PATTERN.fullmatch(model):
        raise OllamaSecurityError("invalid Ollama model name")
    base = validate_local_ollama_url(base_url)
    payload = json.dumps(
        {
            "model": model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = Request(  # noqa: S310 - target base URL is restricted to localhost above
        f"{base}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        outer = json.loads(response.read().decode("utf-8"))

    model_text = outer.get("response")
    if not isinstance(model_text, str):
        raise ValueError("Ollama response did not contain model JSON text")
    decoded = json.loads(model_text)
    if not isinstance(decoded, dict):
        raise ValueError("Ollama model output must be a JSON object")
    return decoded
