#!/usr/bin/env python3
"""
WhisperEngine Bot Launcher - Infrastructure Setup
This launcher handles environment loading and logging configuration before delegating to the bot logic.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load appropriate environment configuration
from env_manager import load_environment

if not load_environment():  # Auto-detects development vs production mode
    sys.exit(1)

# Configure logging using the proper logging configuration
from src.utils.logging_config import setup_logging

debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
# Check both ENVIRONMENT and ENV_MODE for compatibility
environment = os.getenv("ENVIRONMENT") or os.getenv("ENV_MODE", "development")
log_dir = os.getenv("LOG_DIR", "logs")
app_name = os.getenv("LOG_APP_NAME", "discord_bot")

setup_logging(debug=debug_mode, environment=environment, log_dir=log_dir, app_name=app_name)

# Import and run the main function (logging is now configured)
import asyncio
from src.main import main as bot_async_main  # Import the real async entry point
from src.utils.onboarding_manager import ensure_onboarding_complete


async def launcher_main():
    """Launcher entry point that performs onboarding then delegates to the core async bot."""
    # Run onboarding / first‑run check
    should_continue = await ensure_onboarding_complete()
    if not should_continue:
        return 1

    # Delegate directly to the bot's async main (avoid nested asyncio.run())
    return await bot_async_main()


def main():  # Keep a sync facade if other tooling imports run:main
    try:
        return asyncio.run(launcher_main())
    except KeyboardInterrupt:
        # If Ctrl+C occurs before internal graceful shutdown handlers are registered
        print("\n🛑 Shutdown requested (Ctrl+C). Attempting graceful cleanup...")
        return 130  # Conventional exit code for SIGINT


if __name__ == "__main__":
    sys.exit(main())
