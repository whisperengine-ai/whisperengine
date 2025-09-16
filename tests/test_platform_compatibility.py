#!/usr/bin/env python3
"""
Test Platform Compatibility and Adaptations
Verify that platform-specific features and adaptations work correctly
"""

import platform
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_platform_detection():
    """Test platform detection and basic compatibility"""

    current_platform = platform.system()

    # Test that we can detect common platforms
    supported_platforms = ["Darwin", "Windows", "Linux"]
    if current_platform in supported_platforms:
        return True
    else:
        return False


def test_platform_adapter():
    """Test the platform adapter functionality"""

    try:
        from universal_native_app import PlatformAdapter

        adapter = PlatformAdapter()

        # Test platform-specific methods
        adapter.get_window_title()

        adapter.get_default_size()

        # Test styling
        style = adapter.get_platform_style()
        if style and len(style) > 100:  # Basic check that we got some CSS
            pass
        else:
            pass

        # Test platform-specific features
        if (
            hasattr(adapter, "is_macos")
            and hasattr(adapter, "is_windows")
            and hasattr(adapter, "is_linux")
        ):
            pass
        else:
            return False

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_pyside6_compatibility():
    """Test PySide6 compatibility and features"""

    try:
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QFont, QIcon
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget


        # Test application creation
        if not QApplication.instance():
            QApplication([])
        else:
            pass

        # Test widget creation
        widget = QWidget()
        widget.setWindowTitle("Test Widget")

        # Test font availability
        QFont("Arial", 12)

        # Test that we can create the main window type
        QMainWindow()

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_file_system_integration():
    """Test file system integration and permissions"""

    try:
        # Test config directory creation
        config_dir = Path.home() / ".whisperengine"
        if config_dir.exists():
            pass
        else:
            pass

        # Test read permissions
        if config_dir.exists():
            files = list(config_dir.glob("*.json"))

            # Test that we can read a config file
            if files:
                test_file = files[0]
                try:
                    with open(test_file) as f:
                        f.read()
                except Exception:
                    return False

        # Test write permissions (create a temporary file)
        test_file = config_dir / "platform_test.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()  # Delete the test file
        except Exception:
            return False

        return True

    except Exception:
        return False


def test_system_integration():
    """Test system integration features"""

    try:
        # Test environment variable access
        import os

        os.path.expanduser("~")

        # Test that we can get system information
        import getpass

        getpass.getuser()

        # Test network availability (basic check)
        import socket

        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except OSError:
            pass

        return True

    except Exception:
        return False


if __name__ == "__main__":

    # Run all tests
    tests = [
        test_platform_detection,
        test_platform_adapter,
        test_pyside6_compatibility,
        test_file_system_integration,
        test_system_integration,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception:
            results.append(False)

    overall_success = all(results)

    if overall_success:
        pass
    else:
        failed_tests = [test.__name__ for test, result in zip(tests, results, strict=False) if not result]

    sys.exit(0 if overall_success else 1)
