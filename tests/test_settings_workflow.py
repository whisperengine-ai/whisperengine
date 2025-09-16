#!/usr/bin/env python3
"""
Test the complete settings workflow in the enhanced universal app
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import logging


def test_settings_workflow():
    """Test the complete settings workflow"""

    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger = logging.getLogger(__name__)

    app = QApplication(sys.argv)

    try:
        # Import and create the universal app
        from universal_native_app import WhisperEngineUniversalApp

        logger.info("Creating WhisperEngine Universal App...")
        universal_app = WhisperEngineUniversalApp()

        # Show the main window
        universal_app.show()
        logger.info("✅ Main window shown")

        # Test settings manager
        settings_manager = universal_app.settings_manager
        if not settings_manager:
            logger.error("❌ Settings manager not initialized")
            app.quit()
            return 1

        logger.info("✅ Settings manager accessible")

        # Test getting current settings
        all_configs = settings_manager.get_all_configs()

        logger.info("✅ All settings configs retrieved successfully")
        logger.info(f"   LLM Model: {all_configs['llm'].model_name}")
        logger.info(f"   UI Theme: {all_configs['ui'].theme}")
        logger.info(f"   System Tray: {all_configs['platform'].system_tray}")
        logger.info(f"   Privacy Mode: {all_configs['privacy'].privacy_mode}")
        logger.info(f"   Debug Enabled: {all_configs['advanced'].debug_enabled}")

        # Test platform adapter (the actual available platform integration)
        platform_adapter = universal_app.platform_adapter
        if platform_adapter:
            logger.info("✅ Platform adapter accessible")
            logger.info(f"   Is macOS: {platform_adapter.is_macos}")
            logger.info(f"   Is Windows: {platform_adapter.is_windows}")
            logger.info(f"   Is Linux: {platform_adapter.is_linux}")
        else:
            logger.warning("⚠️ Platform adapter not available")

        # Test opening settings dialog programmatically
        def test_settings_dialog():
            logger.info("Testing settings dialog...")
            try:
                universal_app.show_settings_dialog()
                logger.info("✅ Settings dialog opened successfully")

                # Close after a moment
                QTimer.singleShot(3000, lambda: close_settings_and_exit(universal_app))

            except Exception as e:
                logger.error(f"❌ Failed to open settings dialog: {e}")
                app.quit()

        def close_settings_and_exit(app_instance):
            """Close settings dialog and exit cleanly"""
            try:
                if hasattr(app_instance, "settings_dialog") and app_instance.settings_dialog:
                    app_instance.settings_dialog.close()
                    logger.info("✅ Settings dialog closed")
                app.quit()
                logger.info("✅ Application exiting cleanly")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                app.quit()

        # Schedule settings dialog test
        QTimer.singleShot(2000, test_settings_dialog)

        logger.info("🚀 Starting application event loop...")
        logger.info("   The app will automatically open settings in 2 seconds")
        logger.info("   Then close everything after 5 seconds total")

        # Run the app
        return app.exec()

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_settings_workflow())
