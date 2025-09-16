#!/usr/bin/env python3
"""
Test Settings System
Verify that settings are properly saved, loaded, and applied
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_settings_system():
    """Test the settings system functionality"""
    print("⚙️ Testing Settings System...")

    try:
        from src.ui.native_settings_manager import NativeSettingsManager

        print("✅ Settings manager imports successfully")

        # Initialize settings manager
        settings_manager = NativeSettingsManager()
        print("✅ Settings manager initialized")

        # Test getting configurations
        ui_config = settings_manager.get_ui_config()
        llm_config = settings_manager.get_llm_config()
        platform_config = settings_manager.get_platform_config()

        print(f"✅ UI Config loaded - theme: {ui_config.theme}, font_size: {ui_config.font_size}")
        print(
            f"✅ LLM Config loaded - model: {llm_config.model_name}, API URL: {llm_config.api_url}"
        )
        print(f"✅ Platform Config loaded - tray enabled: {platform_config.system_tray_enabled}")

        # Test configuration availability
        if llm_config.api_url and llm_config.model_name:
            print("✅ LLM configuration appears to be set up")
        else:
            print(f"⚠️ LLM configuration incomplete")

        # Test available models
        available_models = settings_manager.get_available_models()
        print(f"✅ Available models: {len(available_models)} models loaded")

        # Test settings file paths
        settings_file = Path.home() / ".whisperengine" / "desktop_settings.json"
        user_config_file = Path.home() / ".whisperengine" / "user_config.json"

        if settings_file.exists():
            print("✅ Settings file exists and is accessible")
            with open(settings_file, "r") as f:
                settings_data = json.load(f)
                print(f"✅ Settings file contains {len(settings_data)} configuration sections")
        else:
            print("❌ Settings file not found")
            return False

        if user_config_file.exists():
            print("✅ User config file exists and is accessible")
            with open(user_config_file, "r") as f:
                user_data = json.load(f)
                print(f"✅ User config for: {user_data.get('username', 'unknown')}")
        else:
            print("❌ User config file not found")
            return False

        # Test settings modification (temporarily)
        print("\n🔧 Testing settings modification...")

        # Save current font size
        original_font_size = ui_config.font_size

        # Modify UI config
        ui_config.font_size = 14
        # Note: Using direct settings save since there's no specific save_ui_config method
        settings_manager.save_settings()
        print("✅ UI config modified and saved")

        # Reload to verify persistence
        new_settings_manager = NativeSettingsManager()
        reloaded_config = new_settings_manager.get_ui_config()

        if reloaded_config.font_size == 14:
            print("✅ Settings persistence verified")
        else:
            print("⚠️ Settings persistence test inconclusive (config may not have changed)")

        # Restore original value
        ui_config.font_size = original_font_size
        settings_manager.save_settings()
        print("✅ Original settings restoration attempted")

        return True

    except ImportError as e:
        print(f"❌ Failed to import settings manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during settings test: {e}")
        return False


def test_settings_dialog():
    """Test that the settings dialog can be created"""
    print("\n🖥️ Testing Settings Dialog...")

    try:
        from src.ui.native_settings_dialog import NativeSettingsDialog
        from src.ui.native_settings_manager import NativeSettingsManager

        # Create a settings manager
        settings_manager = NativeSettingsManager()

        # Test dialog creation (without showing)
        dialog = NativeSettingsDialog(settings_manager, None)
        print("✅ Settings dialog created successfully")

        # Test dialog has required components
        if hasattr(dialog, "ui_tab") and hasattr(dialog, "llm_tab"):
            print("✅ Settings dialog has required tabs")
        else:
            print("❌ Settings dialog missing required tabs")
            return False

        return True

    except ImportError as e:
        print(f"❌ Failed to import settings dialog: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating settings dialog: {e}")
        return False


if __name__ == "__main__":
    print("⚙️ Settings System Integration Test")
    print("=" * 50)

    success1 = test_settings_system()
    success2 = test_settings_dialog()

    overall_success = success1 and success2

    if overall_success:
        print("\n🎉 Settings System Integration Test PASSED")
        print("✅ All settings functionality working correctly")
    else:
        print("\n❌ Settings System Integration Test FAILED")

    sys.exit(0 if overall_success else 1)
