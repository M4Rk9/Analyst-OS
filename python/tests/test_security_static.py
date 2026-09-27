import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"

FORBIDDEN_BROWSER_PATTERNS = (
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML",
    "document.write",
    "eval(",
    "new Function(",
)


def tracked_files() -> set[str]:
    git = shutil.which("git")
    assert git is not None, "git executable is required for tracked-file security tests"
    result = subprocess.run(  # noqa: S603 - resolved git path + constant arguments only
        [git, "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def test_local_secret_files_are_not_tracked() -> None:
    tracked = tracked_files()
    assert ".env" not in tracked
    assert "web/js/config.js" not in tracked
    assert not any(path.startswith(".env.") and path != ".env.example" for path in tracked)


def test_browser_code_avoids_unsafe_dom_execution_patterns() -> None:
    for path in sorted((WEB / "js").glob("*.js")):
        content = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_BROWSER_PATTERNS:
            assert pattern not in content, f"{pattern} is forbidden in {path.relative_to(ROOT)}"


def test_privileged_supabase_key_name_never_appears_in_web_assets() -> None:
    for path in WEB.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        assert "SUPABASE_SERVICE_ROLE_KEY" not in content, f"privileged key marker found in {path}"


def test_cloudflare_headers_define_strict_browser_policy() -> None:
    headers = (WEB / "_headers").read_text(encoding="utf-8")
    required = (
        "Content-Security-Policy:",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
        "form-action 'none'",
        "Referrer-Policy: strict-origin-when-cross-origin",
        "X-Content-Type-Options: nosniff",
        "Permissions-Policy:",
    )
    for directive in required:
        assert directive in headers
    assert "'unsafe-inline'" not in headers
    assert "'unsafe-eval'" not in headers


def test_frontend_matches_hardened_ai_evidence_schema() -> None:
    company_js = (WEB / "js" / "company.js").read_text(encoding="utf-8")
    assert "evidence,model_name,prompt_version" in company_js
    assert "source_page,source_section" not in company_js
    assert 'url.protocol === "https:"' in company_js
