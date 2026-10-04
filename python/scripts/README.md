# Local scripts

Milestone-specific ingestion, analytics, AI-generation, validation, and publishing entrypoints belong here. Scripts must read privileged credentials from environment variables or hidden terminal prompts, validate all untrusted input, avoid printing secrets, and fail closed on malformed data. Connection secrets must not appear in command arguments or output artifacts.

`preview_loaded_analytics.py` captures fresh native evidence and prepares read-only, definition-bound calculations. See [the workspace bridge runbook](../../docs/M3_WORKSPACE_BRIDGE.md). It has no apply mode.
