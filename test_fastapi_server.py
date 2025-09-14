#!/usr/bin/env python3
"""
Test FastAPI server startup for WhisperEngine desktop app
"""

import asyncio
import uvicorn
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.web_ui import create_web_ui
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.local_database_integration import LocalDatabaseIntegrationManager

async def test_server():
    """Test FastAPI server startup"""
    print("🌐 Testing FastAPI server startup...")
    
    try:
        # Initialize components
        config_manager = AdaptiveConfigManager()
        db_manager = LocalDatabaseIntegrationManager(config_manager)
        await db_manager.initialize()
        
        # Create web UI
        web_ui = create_web_ui(db_manager, config_manager)
        app = web_ui.app
        
        print("✅ FastAPI app created successfully")
        print("🚀 Starting server on http://127.0.0.1:8080")
        
        # Start server
        config = uvicorn.Config(
            app, 
            host="127.0.0.1", 
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        print("🔄 Server starting...")
        await server.serve()
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run test
    asyncio.run(test_server())