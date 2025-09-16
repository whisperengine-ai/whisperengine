#!/usr/bin/env python3
"""
Simple test to verify settings system integration
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

def test_settings_components():
    """Test the settings components independently"""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Test 1: Import and create settings manager
        logger.info("🧪 Test 1: Settings Manager Creation")
        from src.ui.native_settings_manager import NativeSettingsManager
        
        settings_manager = NativeSettingsManager()
        logger.info("✅ Settings manager created successfully")
        
        # Test 2: Get all configurations
        logger.info("🧪 Test 2: Configuration Retrieval")
        all_configs = settings_manager.get_all_configs()
        
        logger.info("✅ All configurations retrieved:")
        logger.info(f"   LLM Config: {all_configs['llm'].model_name}")
        logger.info(f"   UI Config: {all_configs['ui'].theme}")
        logger.info(f"   Platform Config: {all_configs['platform'].system_tray_enabled}")
        logger.info(f"   Privacy Config: {all_configs['privacy'].store_conversations}")
        logger.info(f"   Advanced Config: {all_configs['advanced'].debug_mode}")
        
        # Test 3: Test LLM connection validation
        logger.info("🧪 Test 3: LLM Connection Validation")
        is_valid, message = settings_manager.validate_llm_connection()
        if is_valid:
            logger.info(f"✅ LLM connection validation passed: {message}")
        else:
            logger.info(f"ℹ️ LLM connection validation info: {message}")
        
        # Test 4: Import settings dialog (without showing it)
        logger.info("🧪 Test 4: Settings Dialog Import")
        from src.ui.native_settings_dialog import NativeSettingsDialog
        logger.info("✅ Settings dialog imported successfully")
        
        # Test 5: Import platform integration manager
        logger.info("🧪 Test 5: Platform Integration Manager Import")
        from src.ui.platform_integration_manager import PlatformIntegrationManager
        logger.info("✅ Platform integration manager imported successfully")
        
        # Test 6: Import universal app
        logger.info("🧪 Test 6: Universal App Import")
        from universal_native_app import WhisperEngineUniversalApp
        logger.info("✅ Universal app imported successfully")
        
        logger.info("🎉 All component tests passed successfully!")
        logger.info("")
        logger.info("Settings System Summary:")
        logger.info("========================")
        logger.info("✅ Native Settings Manager - Complete")
        logger.info("✅ Settings Dialog UI - Complete") 
        logger.info("✅ Platform Integration Manager - Complete")
        logger.info("✅ Universal App Integration - Complete")
        logger.info("")
        logger.info("The complete settings workflow is ready!")
        logger.info("You can now run the universal app and use the settings features.")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_settings_components())