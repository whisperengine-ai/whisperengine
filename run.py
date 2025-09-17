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
environment = os.getenv("ENVIRONMENT", "development")
log_dir = os.getenv("LOG_DIR", "logs")
app_name = os.getenv("LOG_APP_NAME", "discord_bot")

setup_logging(debug=debug_mode, environment=environment, log_dir=log_dir, app_name=app_name)

# Import and run the main function (logging is now configured)
import asyncio
from src.main import sync_main
from src.utils.onboarding_manager import ensure_onboarding_complete

async def main():
    """Main entry point with onboarding check"""
     Check if onboarding is needed
    should_continue = await ensure_onboarding_complete()
    if not should_continue:
        return 1
    
    # Run the main application
    return sync_main()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
