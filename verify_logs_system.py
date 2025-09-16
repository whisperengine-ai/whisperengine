#!/usr/bin/env python3
"""
System Logs Feature Verification
Quick test to verify the logs system is working correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def verify_logs_system():
    """Verify the system logs implementation"""

    # Test 1: Check if the logs widget can be imported
    try:
        from src.ui.system_logs_widget import LogEntry, QtLogHandler

    except ImportError:
        return False

    # Test 2: Check if PySide6 is available
    try:
        # Test if PySide6 is available
        import PySide6.QtWidgets  # noqa: F401

    except ImportError:
        return False

    # Test 3: Test log handler creation
    try:
        QtLogHandler(max_entries=100)
    except Exception:
        return False

    # Test 4: Test log entry creation
    try:
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        LogEntry(record)
    except Exception:
        return False

    # Test 5: Check if main app can import the logs widget
    try:
        # This tests the import path used in the main app
        exec("from src.ui.system_logs_widget import SystemLogsWidget")
    except ImportError:
        return False

    return True


if __name__ == "__main__":
    success = verify_logs_system()
    sys.exit(0 if success else 1)
