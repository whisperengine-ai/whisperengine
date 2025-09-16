#!/usr/bin/env python3
"""
Test Platform Compatibility and Adaptations
Verify that platform-specific features and adaptations work correctly
"""

import sys
import platform
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_platform_detection():
    """Test platform detection and basic compatibility"""
    print("🖥️ Testing Platform Detection...")
    
    current_platform = platform.system()
    print(f"✅ Current platform: {current_platform}")
    print(f"✅ Platform release: {platform.release()}")
    print(f"✅ Architecture: {platform.machine()}")
    print(f"✅ Platform details: {platform.platform()}")
    
    # Test that we can detect common platforms
    supported_platforms = ["Darwin", "Windows", "Linux"]
    if current_platform in supported_platforms:
        print(f"✅ Platform {current_platform} is supported")
        return True
    else:
        print(f"⚠️ Platform {current_platform} may not be fully supported")
        return False

def test_platform_adapter():
    """Test the platform adapter functionality"""
    print("\n🔧 Testing Platform Adapter...")
    
    try:
        from universal_native_app import PlatformAdapter
        
        adapter = PlatformAdapter()
        print("✅ Platform adapter created")
        
        # Test platform-specific methods
        window_title = adapter.get_window_title()
        print(f"✅ Window title: {window_title}")
        
        default_size = adapter.get_default_size()
        print(f"✅ Default window size: {default_size}")
        
        # Test styling
        style = adapter.get_platform_style()
        if style and len(style) > 100:  # Basic check that we got some CSS
            print("✅ Platform-specific styling available")
        else:
            print("⚠️ Limited platform styling")
        
        # Test platform-specific features
        if hasattr(adapter, 'is_macos') and hasattr(adapter, 'is_windows') and hasattr(adapter, 'is_linux'):
            print("✅ Platform detection methods available")
        else:
            print("❌ Platform detection methods missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import platform adapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Platform adapter test error: {e}")
        return False

def test_pyside6_compatibility():
    """Test PySide6 compatibility and features"""
    print("\n🖼️ Testing PySide6 Compatibility...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QFont, QIcon
        
        print("✅ Core PySide6 components import successfully")
        
        # Test application creation
        if not QApplication.instance():
            app = QApplication([])
            print("✅ QApplication can be created")
        else:
            print("✅ QApplication already exists")
        
        # Test widget creation
        widget = QWidget()
        widget.setWindowTitle("Test Widget")
        print("✅ Basic widget creation works")
        
        # Test font availability
        font = QFont("Arial", 12)
        print("✅ Font creation works")
        
        # Test that we can create the main window type
        window = QMainWindow()
        print("✅ QMainWindow creation works")
        
        return True
        
    except ImportError as e:
        print(f"❌ PySide6 import error: {e}")
        return False
    except Exception as e:
        print(f"❌ PySide6 compatibility error: {e}")
        return False

def test_file_system_integration():
    """Test file system integration and permissions"""
    print("\n📁 Testing File System Integration...")
    
    try:
        # Test config directory creation
        config_dir = Path.home() / ".whisperengine"
        if config_dir.exists():
            print(f"✅ Config directory exists: {config_dir}")
        else:
            print(f"⚠️ Config directory doesn't exist: {config_dir}")
        
        # Test read permissions
        if config_dir.exists():
            files = list(config_dir.glob("*.json"))
            print(f"✅ Found {len(files)} config files")
            
            # Test that we can read a config file
            if files:
                test_file = files[0]
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                    print(f"✅ Can read config file: {test_file.name}")
                except Exception as e:
                    print(f"❌ Cannot read config file: {e}")
                    return False
        
        # Test write permissions (create a temporary file)
        test_file = config_dir / "platform_test.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()  # Delete the test file
            print("✅ File system write permissions work")
        except Exception as e:
            print(f"❌ File system write error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ File system integration error: {e}")
        return False

def test_system_integration():
    """Test system integration features"""
    print("\n🔧 Testing System Integration...")
    
    try:
        # Test environment variable access
        import os
        home_path = os.path.expanduser("~")
        print(f"✅ Can access environment variables - Home: {home_path}")
        
        # Test that we can get system information
        import getpass
        username = getpass.getuser()
        print(f"✅ Can get system username: {username}")
        
        # Test network availability (basic check)
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("✅ Network connectivity available")
        except OSError:
            print("⚠️ Limited network connectivity")
        
        return True
        
    except Exception as e:
        print(f"❌ System integration error: {e}")
        return False

if __name__ == "__main__":
    print("🖥️ Platform Compatibility Integration Test")
    print("=" * 50)
    
    # Run all tests
    tests = [
        test_platform_detection,
        test_platform_adapter,
        test_pyside6_compatibility,
        test_file_system_integration,
        test_system_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    overall_success = all(results)
    
    if overall_success:
        print("\n🎉 Platform Compatibility Integration Test PASSED")
        print("✅ All platform-specific features working correctly")
        print(f"✅ Running successfully on {platform.system()}")
    else:
        print("\n❌ Platform Compatibility Integration Test FAILED")
        failed_tests = [test.__name__ for test, result in zip(tests, results) if not result]
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
    
    sys.exit(0 if overall_success else 1)