#!/usr/bin/env python3
"""
Test System Tray Integration for WhisperEngine Desktop App
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.system_tray import create_system_tray, is_tray_available


class MockApp:
    """Mock app instance for testing"""

    def __init__(self):
        self.running = True


def test_tray_availability():
    """Test if system tray is available"""
    print("🧪 Testing System Tray Availability...")

    available = is_tray_available()
    if available:
        print("✅ System tray dependencies available (pystray, Pillow)")
    else:
        print("❌ System tray dependencies missing")
        print("   Install with: pip install pystray Pillow")

    return available


def test_tray_creation():
    """Test system tray creation"""
    print("\n🧪 Testing System Tray Creation...")

    if not is_tray_available():
        print("⏭️  Skipping - dependencies not available")
        return False

    try:
        mock_app = MockApp()
        tray = create_system_tray(mock_app, "127.0.0.1", 8080)

        if tray:
            print("✅ System tray instance created successfully")
            print(f"   Host: {tray.host}")
            print(f"   Port: {tray.port}")

            # Test icon creation
            icon = tray.create_tray_icon()
            if icon:
                print("✅ Tray icon created successfully")
            else:
                print("❌ Failed to create tray icon")
                return False

            # Test menu creation
            menu = tray.create_menu()
            if menu:
                print("✅ Tray menu created successfully")
            else:
                print("❌ Failed to create tray menu")
                return False

            return True

        else:
            print("❌ Failed to create system tray instance")
            return False

    except Exception as e:
        print(f"❌ Error creating system tray: {e}")
        return False


def test_tray_background_start():
    """Test starting system tray in background"""
    print("\n🧪 Testing System Tray Background Start...")

    if not is_tray_available():
        print("⏭️  Skipping - dependencies not available")
        return False

    try:
        mock_app = MockApp()
        tray = create_system_tray(mock_app, "127.0.0.1", 8080)

        if not tray:
            print("❌ Could not create tray instance")
            return False

        # Test setup
        setup_success = tray.setup_tray()
        if setup_success:
            print("✅ System tray setup successful")
        else:
            print("❌ System tray setup failed")
            return False

        print("⚠️  Background start test requires GUI environment")
        print("   In a GUI environment, tray icon should appear")

        # Don't actually start in background for automated testing
        # since it requires GUI environment
        return True

    except Exception as e:
        print(f"❌ Error in background start test: {e}")
        return False


def main():
    """Run system tray tests"""
    print("🤖 WhisperEngine System Tray Test Suite")
    print("=" * 50)

    tests = [
        ("Tray Availability", test_tray_availability),
        ("Tray Creation", test_tray_creation),
        ("Background Start", test_tray_background_start),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System tray integration ready.")
    else:
        print("⚠️  Some tests failed. Check dependencies and environment.")

    print("\n💡 To test in GUI environment:")
    print("   1. Run desktop app: python universal_native_app.py")
    print("   2. Look for WhisperEngine icon in system tray")
    print("   3. Right-click for context menu")


if __name__ == "__main__":
    main()
