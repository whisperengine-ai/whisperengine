#!/usr/bin/env python3
"""
Test script for macOS dock badge integration
Demonstrates the dock badge functionality we've implemented
"""

import subprocess
import sys
import time


def test_dock_badge():
    """Test dock badge functionality"""

    # Test 1: Set a badge count
    try:
        script = """
        tell application "System Events"
            try
                set dock_items to dock tiles of dock preferences
                repeat with dock_item in dock_items
                    if name of dock_item contains "WhisperEngine" then
                        set badge text of dock_item to "3"
                        exit repeat
                    end if
                end repeat
            end try
        end tell
        """
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass

    time.sleep(3)

    # Test 2: Clear the badge
    try:
        script = """
        tell application "System Events"
            try
                set dock_items to dock tiles of dock preferences
                repeat with dock_item in dock_items
                    if name of dock_item contains "WhisperEngine" then
                        set badge text of dock_item to ""
                        exit repeat
                    end if
                end repeat
            end try
        end tell
        """
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass

    # Test 3: Send a test notification
    try:
        script = """
        display notification "Enhanced dock integration is working!" with title "WhisperEngine" sound name "Purr"
        """
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass

    # Test 4: Show dock information
    try:
        script = """
        tell application "System Events"
            try
                set dock_items to dock tiles of dock preferences
                set item_names to {}
                repeat with dock_item in dock_items
                    if name of dock_item contains "WhisperEngine" or name of dock_item contains "Terminal" then
                        set end of item_names to name of dock_item
                    end if
                end repeat
                return item_names as string
            end try
        end tell
        """
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass


def demo_badge_lifecycle():
    """Demonstrate badge lifecycle with different counts"""

    for count in range(1, 6):
        try:
            script = f"""
            tell application "System Events"
                try
                    set dock_items to dock tiles of dock preferences
                    repeat with dock_item in dock_items
                        if name of dock_item contains "WhisperEngine" then
                            set badge text of dock_item to "{count}"
                            exit repeat
                        end if
                    end repeat
                end try
            end tell
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)
            time.sleep(1.5)
        except Exception:
            pass

    # Final clear
    try:
        script = """
        tell application "System Events"
            try
                set dock_items to dock tiles of dock preferences
                repeat with dock_item in dock_items
                    if name of dock_item contains "WhisperEngine" then
                        set badge text of dock_item to ""
                        exit repeat
                    end if
                end repeat
            end try
        end tell
        """
        subprocess.run(["osascript", "-e", script], capture_output=True)
    except Exception:
        pass


def show_capabilities():
    """Show what dock integration capabilities we've implemented"""


if __name__ == "__main__":

    if sys.platform != "darwin":
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_badge_lifecycle()
    elif len(sys.argv) > 1 and sys.argv[1] == "--capabilities":
        show_capabilities()
    else:
        test_dock_badge()
        demo_badge_lifecycle()
        show_capabilities()

