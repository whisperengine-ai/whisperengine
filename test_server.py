#!/usr/bin/env python3
"""
Minimal Desktop App Server for Testing
Starts just the FastAPI server without system tray integration to avoid trace trap
"""

import asyncio
import uvicorn
import sys
import logging
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.web_ui import create_web_ui
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.local_database_integration import LocalDatabaseIntegrationManager

async def start_test_server():
    """Start minimal server for testing AI conversation capabilities"""
    print("🧪 Starting WhisperEngine Test Server...")
    print("(Minimal version without system tray to avoid trace trap)")
    
    try:
        # Force SQLite for desktop mode
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        # Initialize configuration manager
        config_manager = AdaptiveConfigManager()
        print("✅ Configuration manager initialized")
        
        # Initialize database manager with local components
        db_manager = LocalDatabaseIntegrationManager(config_manager)
        init_success = await db_manager.initialize()
        
        if init_success:
            print("✅ Local database integration initialized")
        else:
            print("❌ Local database initialization failed")
            return
            
        # Create web UI
        web_ui = create_web_ui(db_manager, config_manager)
        app = web_ui.app
        print("✅ Web UI created")
        
        print("\n🌐 Starting server on http://127.0.0.1:8080")
        print("🔄 Server will run until you press Ctrl+C")
        print("💬 You can now test AI conversations!")
        
        # Start server
        config = uvicorn.Config(
            app, 
            host="127.0.0.1", 
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    asyncio.run(start_test_server())