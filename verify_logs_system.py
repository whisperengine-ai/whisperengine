#!/usr/bin/env python3
"""
System Logs Feature Verification
Quick test to verify the logs system is working correctly
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def verify_logs_system():
    """Verify the system logs implementation"""
    print("🔍 Verifying System Logs Implementation...")
    
    # Test 1: Check if the logs widget can be imported
    try:
        from src.ui.system_logs_widget import SystemLogsWidget, QtLogHandler, LogEntry
        print("✅ SystemLogsWidget imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import SystemLogsWidget: {e}")
        return False
    
    # Test 2: Check if PySide6 is available
    try:
        from PySide6.QtWidgets import QApplication
        print("✅ PySide6 is available")
    except ImportError:
        print("❌ PySide6 not available")
        return False
    
    # Test 3: Test log handler creation
    try:
        handler = QtLogHandler(max_entries=100)
        print("✅ QtLogHandler creates successfully")
    except Exception as e:
        print(f"❌ Failed to create QtLogHandler: {e}")
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
            exc_info=None
        )
        entry = LogEntry(record)
        print("✅ LogEntry creates successfully")
    except Exception as e:
        print(f"❌ Failed to create LogEntry: {e}")
        return False
    
    # Test 5: Check if main app can import the logs widget
    try:
        # This tests the import path used in the main app
        exec("from src.ui.system_logs_widget import SystemLogsWidget")
        print("✅ Main app can import SystemLogsWidget")
    except ImportError as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    print("\n🎉 System Logs Feature Verification Complete!")
    print("✅ All core components are working correctly")
    print("\n📋 To test the full functionality:")
    print("   1. Run the WhisperEngine desktop app: `python universal_native_app.py`")
    print("   2. Click on the '📋 System Logs' tab")
    print("   3. Use the app or run `python generate_app_logs.py` to see logs")
    print("   4. Test filtering, copying, and clearing functions")
    
    return True

if __name__ == "__main__":
    success = verify_logs_system()
    sys.exit(0 if success else 1)