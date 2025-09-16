#!/usr/bin/env python3
"""
WhisperEngine System Tray Demo
Demonstrates the system tray functionality in action.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.system_tray import create_system_tray, is_tray_available


class DemoApp:
    """Demo app for testing system tray"""

    def __init__(self):
        self.running = True


def main():
    """Run system tray demo"""

    if not is_tray_available():
        return


    # Create demo app
    demo_app = DemoApp()

    # Create system tray
    tray = create_system_tray(demo_app, "127.0.0.1", 8080)

    if not tray:
        return


    # Setup tray
    if not tray.setup_tray():
        return






if __name__ == "__main__":
    main()
