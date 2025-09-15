#!/usr/bin/env python3
"""
Desktop App Launcher  
Launches WhisperEngine as a native desktop application with local model configuration.
"""

import os
import sys
from pathlib import Path

# Set the working directory to the parent (main repo root)
os.chdir(Path(__file__).parent.parent)

# Set environment file for this deployment
os.environ['DOTENV_PATH'] = str(Path(__file__).parent / '.env')

# Import and run the desktop app
from universal_native_app import main

if __name__ == "__main__":
    print("🖥️ Starting WhisperEngine Desktop App...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"⚙️  Config: {os.environ.get('DOTENV_PATH', 'default')}")
    exit_code = main()
    sys.exit(exit_code)