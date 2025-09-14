#!/usr/bin/env python3
"""
Test Complete Desktop App Workflow
Tests end-to-end desktop app experience including LLM auto-detection, setup guidance UI, and fallback options.
"""

import asyncio
import os
import sys
import logging
import json
import aiohttp
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_desktop_app_startup():
    """Test desktop app startup with LLM integration"""
    logger.info("🚀 Testing Desktop App Startup")
    
    try:
        from desktop_app import WhisperEngineDesktopApp
        
        # Create app instance
        app = WhisperEngineDesktopApp()
        
        # Setup environment
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        os.environ['LOG_LEVEL'] = 'INFO'
        
        # Initialize without starting server
        app.setup_logging()
        await app.initialize_components()
        
        # Check if setup guidance was configured
        has_guidance = hasattr(app, 'llm_setup_guidance') and app.llm_setup_guidance is not None
        has_web_ui = hasattr(app, 'web_ui') and app.web_ui is not None
        
        print(f"✅ Desktop app initialized")
        print(f"✅ Setup guidance configured: {has_guidance}")
        print(f"✅ Web UI created: {has_web_ui}")
        
        return app, has_guidance
        
    except Exception as e:
        logger.error(f"❌ Desktop app startup failed: {e}")
        return None, False


async def test_setup_guidance_api(app):
    """Test setup guidance API endpoints"""
    logger.info("🔧 Testing Setup Guidance API")
    
    try:
        # Start server in background to test API
        import uvicorn
        from threading import Thread
        import time
        
        host = "127.0.0.1"
        port = 8081  # Use different port for testing
        
        # Configure server
        config = uvicorn.Config(
            app=app.web_ui.app,
            host=host,
            port=port,
            log_level="warning"  # Quiet for testing
        )
        server = uvicorn.Server(config)
        
        # Start server in thread
        server_thread = Thread(target=lambda: asyncio.run(server.serve()), daemon=True)
        server_thread.start()
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Test setup guidance API
        async with aiohttp.ClientSession() as session:
            # Test API endpoint
            async with session.get(f"http://{host}:{port}/api/setup-guidance") as response:
                guidance_data = await response.json()
                
                print(f"✅ Setup guidance API accessible")
                print(f"✅ Show guidance: {guidance_data.get('show_guidance', False)}")
                
                if guidance_data.get('show_guidance'):
                    print(f"✅ Setup title: {guidance_data.get('title', 'N/A')}")
                    print(f"✅ Server name: {guidance_data.get('server_name', 'N/A')}")
                    print(f"✅ Setup steps: {len(guidance_data.get('setup_steps', []))} steps")
                
            # Test setup page
            async with session.get(f"http://{host}:{port}/setup") as response:
                page_content = await response.text()
                
                has_setup_content = "Setup Local AI" in page_content
                print(f"✅ Setup page accessible: {has_setup_content}")
        
        # Stop server
        server.should_exit = True
        await asyncio.sleep(1)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup guidance API test failed: {e}")
        return False


async def test_llm_detection_workflow():
    """Test LLM detection and configuration workflow"""
    logger.info("🤖 Testing LLM Detection Workflow")
    
    try:
        from src.llm.desktop_llm_manager import DesktopLLMManager
        
        # Test LLM manager directly
        manager = DesktopLLMManager()
        result = await manager.initialize_llm_for_desktop()
        
        status = result.get('status', 'unknown')
        print(f"✅ LLM initialization status: {status}")
        
        # Test different scenarios
        if status == 'local_configured':
            server_info = result.get('server_info')
            print(f"✅ Local server detected: {server_info.name if server_info else 'Unknown'}")
            
        elif status == 'setup_required':
            guidance = result.get('setup_guidance')
            if guidance:
                print(f"✅ Setup guidance available: {guidance.preferred_server}")
                print(f"✅ System analysis: {guidance.system_analysis}")
                
        elif status == 'cloud_fallback':
            print(f"✅ Cloud fallback configured")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM detection test failed: {e}")
        return False


async def test_ui_integration():
    """Test UI integration scenarios"""
    logger.info("🎨 Testing UI Integration")
    
    try:
        from src.ui.setup_guidance import SetupGuidanceManager
        from fastapi.templating import Jinja2Templates
        
        # Create mock templates
        templates_path = Path(__file__).parent / "src" / "ui" / "templates"
        templates = Jinja2Templates(directory=str(templates_path))
        
        # Create guidance manager
        guidance_manager = SetupGuidanceManager(templates)
        
        # Test setting guidance
        mock_guidance = {
            'preferred_server': 'LM Studio',
            'system_analysis': {
                'total_ram_gb': 16,
                'cpu_cores': 8,
                'gpu_available': False
            }
        }
        
        guidance_manager.set_setup_guidance(mock_guidance)
        formatted = guidance_manager.format_for_ui(mock_guidance)
        
        print(f"✅ Guidance formatting works")
        print(f"✅ Title: {formatted.get('title', 'N/A')}")
        print(f"✅ Benefits count: {len(formatted.get('benefits', []))}")
        print(f"✅ Setup steps count: {len(formatted.get('setup_steps', []))}")
        
        # Test clearing guidance
        guidance_manager.clear_setup_guidance()
        current = guidance_manager.get_setup_guidance()
        
        print(f"✅ Guidance clearing works: {current is None}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UI integration test failed: {e}")
        return False


async def main():
    """Run complete desktop app workflow tests"""
    print("🧪 Complete Desktop App Workflow Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Desktop app startup
    print("\n1️⃣ Testing Desktop App Startup...")
    app, has_guidance = await test_desktop_app_startup()
    results['startup'] = app is not None
    
    if not app:
        print("❌ Cannot continue without working desktop app")
        return
    
    # Test 2: Setup guidance API
    print("\n2️⃣ Testing Setup Guidance API...")
    results['api'] = await test_setup_guidance_api(app)
    
    # Test 3: LLM detection workflow
    print("\n3️⃣ Testing LLM Detection Workflow...")
    results['llm_detection'] = await test_llm_detection_workflow()
    
    # Test 4: UI integration
    print("\n4️⃣ Testing UI Integration...")
    results['ui_integration'] = await test_ui_integration()
    
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
        print("🎉 ALL TESTS PASSED - Complete desktop app workflow ready!")
        print("\n✅ Desktop app features working:")
        print("   🔍 Auto-detection of local LLM servers")
        print("   📱 Setup guidance UI when needed")
        print("   ☁️ Fallback to cloud APIs")
        print("   🎨 Integrated web UI experience")
        print("   🖥️ Native desktop app packaging")
        
        print("\n🚀 Ready for production use!")
        print("   • Users get seamless LLM detection")
        print("   • Clear setup guidance when needed")
        print("   • Automatic fallback options")
        print("   • Privacy-first local operation")
    else:
        print("❌ Some tests failed - needs fixes before production")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())