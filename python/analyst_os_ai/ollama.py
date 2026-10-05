"""Minimal loopback-only Ollama client for offline analysis."""

import json
import math
import re
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
ALLOWED_HOSTS = {"127.0.0.1", "::1"}
MAX_TIMEOUT_SECONDS = 300.0
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OllamaSecurityError("Ollama redirects are forbidden")


def local_response(request, timeout):
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:  # noqa: S310
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Ollama response exceeds bounded limit")
    return json.loads(raw.decode("utf-8"))


def model_digest(model, base_url=DEFAULT_OLLAMA_URL):
    if not MODEL_PATTERN.fullmatch(model) or "cloud" in model.lower():
        raise OllamaSecurityError("invalid Ollama model name")
    base = validate_local_ollama_url(base_url)
    data = local_response(Request(base + "/api/tags"), 30)  # noqa: S310
    matches = [m for m in data.get("models", []) if m.get("name") == model]
    if len(matches) != 1 or not re.fullmatch(r"[a-f0-9]{64}", matches[0].get("digest", "")):
        raise ValueError("requested exact local model tag/digest is unavailable")
    installed = matches[0]
    if (
        not isinstance(installed.get("size"), int)
        or installed["size"] <= 0
        or installed.get("details", {}).get("format") != "gguf"
        or installed.get("remote_host")
        or installed.get("remote_model")
    ):
        raise OllamaSecurityError(
            "model must have installed local GGUF weights, not cloud metadata"
        )
    return matches[0]["digest"]


class OllamaSecurityError(ValueError):
    """Raised when Ollama configuration violates the local-only boundary."""


def validate_local_ollama_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_HOSTS:
        raise OllamaSecurityError("Ollama URL must use HTTP on a loopback IP only")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OllamaSecurityError("Ollama URL may not contain credentials, query, or fragment")
    if parsed.path not in {"", "/"}:
        raise OllamaSecurityError("Ollama base URL must not include an application path")
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise OllamaSecurityError("Ollama URL contains an invalid port") from exc
    if parsed_port is not None and not 1 <= parsed_port <= 65535:
        raise OllamaSecurityError("Ollama URL contains an invalid port")
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

    if not MODEL_PATTERN.fullmatch(model) or "cloud" in model.lower():
        raise OllamaSecurityError("invalid Ollama model name")
    if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise OllamaSecurityError("Ollama timeout is outside the allowed range")

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
    request = Request(  # noqa: S310 - URL was restricted to literal loopback HTTP above
        f"{base}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Do not inherit HTTP(S)_PROXY or other proxy environment settings.
    outer = local_response(request, timeout_seconds)

    model_text = outer.get("response")
    if not isinstance(model_text, str):
        raise ValueError("Ollama response did not contain model JSON text")
    decoded = json.loads(model_text)
    if not isinstance(decoded, dict):
        raise ValueError("Ollama model output must be a JSON object")
    return decoded
