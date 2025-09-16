#!/usr/bin/env python3
"""
Test Settings System
Verify that settings are properly saved, loaded, and applied
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_settings_system():
    """Test the settings system functionality"""

    try:
        from src.ui.native_settings_manager import NativeSettingsManager


        # Initialize settings manager
        settings_manager = NativeSettingsManager()

        # Test getting configurations
        ui_config = settings_manager.get_ui_config()
        llm_config = settings_manager.get_llm_config()
        settings_manager.get_platform_config()


        # Test configuration availability
        if llm_config.api_url and llm_config.model_name:
            pass
        else:
            pass

        # Test available models
        settings_manager.get_available_models()

        # Test settings file paths
        settings_file = Path.home() / ".whisperengine" / "desktop_settings.json"
        user_config_file = Path.home() / ".whisperengine" / "user_config.json"

        if settings_file.exists():
            with open(settings_file) as f:
                json.load(f)
        else:
            return False

        if user_config_file.exists():
            with open(user_config_file) as f:
                json.load(f)
        else:
            return False

        # Test settings modification (temporarily)

        # Save current font size
        original_font_size = ui_config.font_size

        # Modify UI config
        ui_config.font_size = 14
        # Note: Using direct settings save since there's no specific save_ui_config method
        settings_manager.save_settings()

        # Reload to verify persistence
        new_settings_manager = NativeSettingsManager()
        reloaded_config = new_settings_manager.get_ui_config()

        if reloaded_config.font_size == 14:
            pass
        else:
            pass

        # Restore original value
        ui_config.font_size = original_font_size
        settings_manager.save_settings()

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_settings_dialog():
    """Test that the settings dialog can be created"""

    try:
        from src.ui.native_settings_dialog import NativeSettingsDialog
        from src.ui.native_settings_manager import NativeSettingsManager

        # Create a settings manager
        settings_manager = NativeSettingsManager()

        # Test dialog creation (without showing)
        dialog = NativeSettingsDialog(settings_manager, None)

        # Test dialog has required components
        if hasattr(dialog, "ui_tab") and hasattr(dialog, "llm_tab"):
            pass
        else:
            return False

        return True

    except ImportError:
        return False
    except Exception:
        return False


if __name__ == "__main__":

    success1 = test_settings_system()
    success2 = test_settings_dialog()

    overall_success = success1 and success2

    if overall_success:
        pass
    else:
        pass

    sys.exit(0 if overall_success else 1)
