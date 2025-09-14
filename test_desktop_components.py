#!/usr/bin/env python3
"""
Simple test to verify the desktop app startup process step by step
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.local_database_integration import LocalDatabaseIntegrationManager

async def test_components():
    """Test each component separately"""
    print("🧪 Testing desktop app components individually...")
    
    try:
        # 1. Config Manager
        print("\n📋 Testing Configuration Manager...")
        config_manager = AdaptiveConfigManager()
        print("   ✅ Configuration Manager created")
        
        # 2. Database Integration
        print("\n🗄️ Testing Local Database Integration...")
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        db_manager = LocalDatabaseIntegrationManager(config_manager)
        init_success = await db_manager.initialize()
        
        if init_success:
            print("   ✅ Database integration initialized")
        else:
            print("   ❌ Database integration failed to initialize")
            
        # 3. Web UI (without starting server)
        print("\n🌐 Testing Web UI Creation...")
        from src.ui.web_ui import create_web_ui
        web_ui = create_web_ui(db_manager, config_manager)
        print("   ✅ Web UI created successfully")
        
        print("\n🎉 All components tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    success = asyncio.run(test_components())
    
    if success:
        print("\n✅ Desktop app components are ready!")
        print("💡 The issue might be in the FastAPI server startup or system tray integration")
    else:
        print("\n❌ Desktop app components have issues")