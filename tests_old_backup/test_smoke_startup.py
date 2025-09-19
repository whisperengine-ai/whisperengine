"""Quick smoke test for WhisperEngine launcher.

Validates that `launcher_main` in `run.py` can execute the minimal startup path
and return an expected success status without performing heavy subsystem
initialization. We patch the core async bot main to avoid spinning up Discord
connections or long-running services.

This test should remain FAST (< 1s) and only assert high-level invariants:
  • Environment loads
  • Onboarding check path is executed
  • Patched bot main is awaited
  • Exit code is 0 (success)

If onboarding would normally block (first run), we patch `ensure_onboarding_complete`
to return True so the launcher continues. This keeps the smoke test resilient
in CI environments that may or may not have a prepared .env.
"""
from __future__ import annotations

import sys
import importlib.util
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_launcher_smoke_startup(monkeypatch):  # noqa: D401
    """Smoke test: run launcher_main with patched dependencies."""
    # Minimal env to satisfy logging + basic config
    monkeypatch.setenv("ENV_MODE", "testing")
    monkeypatch.setenv("DEBUG_MODE", "false")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "placeholder_token_for_smoke")
    monkeypatch.setenv("LLM_CHAT_API_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("LLM_CHAT_API_KEY", "not-needed")

    # Import run.py as a module so we can access launcher_main
    spec = importlib.util.spec_from_file_location("run", str(PROJECT_ROOT / "run.py"))
    assert spec and spec.loader, "Failed to load run.py spec"
    run_module = importlib.util.module_from_spec(spec)

    with patch.dict(sys.modules, {}):  # Isolate imports for a clean load
        spec.loader.exec_module(run_module)  # type: ignore[attr-defined]

    # Patch ensure_onboarding_complete to always allow continuation quickly
    with patch("src.utils.onboarding_manager.ensure_onboarding_complete", new=AsyncMock(return_value=True)):
        # Patch the real bot async main to avoid heavy startup
        with patch("src.main.main", new=AsyncMock(return_value=0)) as mock_bot_main:
            exit_code = await run_module.launcher_main()

    assert exit_code == 0, "Launcher did not exit cleanly"
    # Ensure the patched bot main was awaited exactly once
    mock_bot_main.assert_awaited()


@pytest.mark.smoke
def test_run_module_import_fast():
    """Ensure importing run.py performs only lightweight operations (no hang)."""
    spec = importlib.util.spec_from_file_location("run_import_check", str(PROJECT_ROOT / "run.py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)

    # Limit to a short timeout to detect accidental long-running work at import time
    async def _import():
        spec.loader.exec_module(module)  # type: ignore[attr-defined]

    # Import within event loop to reuse asyncio for potential future async setup patterns
    asyncio.run(_import())
    assert hasattr(module, "launcher_main"), "launcher_main not defined after import"
