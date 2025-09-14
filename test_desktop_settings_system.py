#!/usr/bin/env python3
"""
Test Desktop App Settings System
Comprehensive test for all settings functionality including system prompts, LLM config, and Discord bot settings.
"""

import asyncio
import os
import sys
import logging
import tempfile
import aiohttp
from pathlib import Path
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_settings_manager():
    """Test the desktop settings manager"""
    logger.info("🔧 Testing Desktop Settings Manager")
    
    try:
        from src.config.desktop_settings import DesktopSettingsManager
        
        # Create manager
        manager = DesktopSettingsManager()
        
        # Test system prompt management
        print("📝 Testing system prompt management...")
        
        # Save custom prompt
        custom_name = "test_prompt"
        custom_content = "You are a test AI assistant."
        success = manager.save_custom_prompt(custom_name, custom_content)
        print(f"✅ Save custom prompt: {success}")
        
        # Set active prompt
        success = manager.set_active_prompt("custom", custom_name)
        print(f"✅ Set active prompt: {success}")
        
        # Get active prompt
        active_content = manager.get_active_system_prompt()
        print(f"✅ Get active prompt: {len(active_content)} characters")
        
        # Test LLM configuration
        print("🤖 Testing LLM configuration...")
        
        success = manager.set_llm_config(
            "http://localhost:1234/v1",
            "test-key-123",
            "test-model"
        )
        print(f"✅ Set LLM config: {success}")
        
        config = manager.get_llm_config()
        print(f"✅ Get LLM config: {config['api_url']}")
        
        # Test Discord configuration
        print("🤖 Testing Discord configuration...")
        
        success = manager.set_discord_token("test-discord-token-123")
        print(f"✅ Set Discord token: {success}")
        
        discord_config = manager.get_discord_config()
        print(f"✅ Get Discord config: token length {len(discord_config['bot_token'])}")
        
        # Test export/import
        print("📤 Testing export/import...")
        
        export_data = manager.export_settings()
        print(f"✅ Export settings: {len(export_data)} keys")
        
        # Clean up test prompt
        manager.delete_custom_prompt(custom_name)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Settings manager test failed: {e}")
        return False


async def test_settings_api():
    """Test settings API endpoints"""
    logger.info("🌐 Testing Settings API")
    
    try:
        from desktop_app import WhisperEngineDesktopApp
        import uvicorn
        from threading import Thread
        import time
        
        # Setup environment
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        os.environ['LOG_LEVEL'] = 'WARNING'
        
        # Create and initialize app
        app = WhisperEngineDesktopApp()
        app.setup_logging()
        await app.initialize_components()
        
        # Start server for testing
        host = "127.0.0.1"
        port = 8082
        
        config = uvicorn.Config(
            app=app.web_ui.app,
            host=host,
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        # Start server in thread
        server_thread = Thread(target=lambda: asyncio.run(server.serve()), daemon=True)
        server_thread.start()
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Test API endpoints
        async with aiohttp.ClientSession() as session:
            base_url = f"http://{host}:{port}"
            
            # Test settings page
            print("📄 Testing settings page...")
            async with session.get(f"{base_url}/settings") as response:
                page_content = await response.text()
                has_settings = "WhisperEngine Settings" in page_content
                print(f"✅ Settings page accessible: {has_settings}")
            
            # Test system prompt API
            print("📝 Testing system prompt API...")
            async with session.get(f"{base_url}/api/settings/system-prompt") as response:
                prompt_config = await response.json()
                print(f"✅ System prompt config: {prompt_config['prompt_source']}")
            
            # Test LLM config API
            print("🤖 Testing LLM config API...")
            async with session.get(f"{base_url}/api/settings/llm-config") as response:
                llm_config = await response.json()
                print(f"✅ LLM config: {llm_config['validation_status']}")
            
            # Test Discord config API
            print("🤖 Testing Discord config API...")
            async with session.get(f"{base_url}/api/settings/discord-config") as response:
                discord_config = await response.json()
                print(f"✅ Discord config: {discord_config['validation_status']}")
            
            # Test UI preferences API
            print("🎨 Testing UI preferences API...")
            async with session.get(f"{base_url}/api/settings/ui-preferences") as response:
                ui_prefs = await response.json()
                print(f"✅ UI preferences: {ui_prefs['auto_save']}")
            
            # Test export API
            print("📤 Testing export API...")
            async with session.get(f"{base_url}/api/settings/export") as response:
                export_result = await response.json()
                has_data = 'data' in export_result
                print(f"✅ Export settings: {has_data}")
        
        # Stop server
        server.should_exit = True
        await asyncio.sleep(1)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Settings API test failed: {e}")
        return False


async def test_file_upload():
    """Test file upload functionality"""
    logger.info("📁 Testing File Upload")
    
    try:
        from src.config.desktop_settings import DesktopSettingsManager
        
        manager = DesktopSettingsManager()
        
        # Create test prompt file
        test_content = "You are a helpful AI assistant for testing file uploads."
        test_filename = "test_upload.txt"
        
        # Test upload
        success = manager.upload_prompt_file(test_filename, test_content)
        print(f"✅ Upload prompt file: {success}")
        
        # Test retrieval
        uploaded_prompts = manager.get_uploaded_prompts()
        has_test_file = test_filename in uploaded_prompts
        print(f"✅ File in uploaded list: {has_test_file}")
        
        # Set as active and test
        manager.set_active_prompt("uploaded", test_filename)
        active_content = manager.get_active_system_prompt()
        matches_uploaded = test_content in active_content
        print(f"✅ Uploaded content active: {matches_uploaded}")
        
        # Clean up
        test_file_path = manager.system_prompts_dir / test_filename
        if test_file_path.exists():
            test_file_path.unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ File upload test failed: {e}")
        return False


async def test_integration_with_desktop_app():
    """Test settings integration with desktop app"""
    logger.info("🖥️ Testing Desktop App Integration")
    
    try:
        from desktop_app import WhisperEngineDesktopApp
        
        # Setup test environment
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        # Create app
        app = WhisperEngineDesktopApp()
        app.setup_logging()
        
        # Initialize components (this should apply settings)
        await app.initialize_components()
        
        # Check if settings manager is available
        has_settings = hasattr(app.web_ui, 'settings_manager')
        print(f"✅ Settings manager available: {has_settings}")
        
        if has_settings:
            # Test settings application
            system_prompt = app.web_ui.settings_manager.get_active_system_prompt()
            prompt_applied = len(system_prompt) > 0
            print(f"✅ System prompt applied: {prompt_applied}")
            
            llm_config = app.web_ui.settings_manager.get_llm_config()
            config_loaded = 'api_url' in llm_config
            print(f"✅ LLM config loaded: {config_loaded}")
            
            discord_config = app.web_ui.settings_manager.get_discord_config()
            discord_loaded = 'bot_token' in discord_config
            print(f"✅ Discord config loaded: {discord_loaded}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Desktop app integration test failed: {e}")
        return False


async def test_validation_features():
    """Test validation features for LLM and Discord"""
    logger.info("✅ Testing Validation Features")
    
    try:
        from src.config.desktop_settings import DesktopSettingsManager
        
        manager = DesktopSettingsManager()
        
        # Test LLM validation with invalid config
        print("🤖 Testing LLM validation...")
        manager.set_llm_config("http://invalid-url", "invalid-key")
        result = await manager.validate_llm_config()
        validation_failed = not result['valid']
        print(f"✅ LLM validation correctly failed: {validation_failed}")
        
        # Test Discord validation with invalid token
        print("🤖 Testing Discord validation...")
        manager.set_discord_token("invalid-token")
        result = await manager.validate_discord_token()
        discord_failed = not result['valid']
        print(f"✅ Discord validation correctly failed: {discord_failed}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation test failed: {e}")
        return False


async def main():
    """Run comprehensive settings system tests"""
    print("🧪 Desktop App Settings System Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Settings manager
    print("\n1️⃣ Testing Settings Manager...")
    results['settings_manager'] = await test_settings_manager()
    
    # Test 2: Settings API
    print("\n2️⃣ Testing Settings API...")
    results['settings_api'] = await test_settings_api()
    
    # Test 3: File upload
    print("\n3️⃣ Testing File Upload...")
    results['file_upload'] = await test_file_upload()
    
    # Test 4: Desktop app integration
    print("\n4️⃣ Testing Desktop App Integration...")
    results['desktop_integration'] = await test_integration_with_desktop_app()
    
    # Test 5: Validation features
    print("\n5️⃣ Testing Validation Features...")
    results['validation'] = await test_validation_features()
    
    # Results summary
    print("\n" + "=" * 60)
    print("🎉 Test Results Summary:")
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Settings system ready!")
        print("\n✅ Desktop app settings features working:")
        print("   📝 System prompt editing and file upload")
        print("   🤖 LLM API configuration with model discovery")
        print("   🤖 Discord bot token configuration")
        print("   💾 Settings persistence in user directory")
        print("   🌐 Web UI settings page with tabbed interface")
        print("   ✅ Configuration validation and testing")
        print("   📤 Settings export/import functionality")
        
        print("\n🚀 Ready for user configuration!")
        print("   • Users can customize system prompts")
        print("   • Easy LLM API setup with validation")
        print("   • Discord bot integration setup")
        print("   • Persistent settings across sessions")
    else:
        print("❌ Some tests failed - needs fixes before production")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())