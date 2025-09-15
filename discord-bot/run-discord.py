#!/usr/bin/env python3
"""
Discord Bot Launcher
Launches WhisperEngine as a Discord bot with cloud API configuration.
"""

import os
import sys
from pathlib import Path

# Set the working directory to the parent (main repo root)
os.chdir(Path(__file__).parent.parent)

# Set environment file for this deployment
os.environ['DOTENV_PATH'] = str(Path(__file__).parent / '.env')

# Import and run the main bot
from src.main import sync_main

if __name__ == "__main__":
    print("🤖 Starting WhisperEngine Discord Bot...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"⚙️  Config: {os.environ.get('DOTENV_PATH', 'default')}")
    sys.exit(sync_main())