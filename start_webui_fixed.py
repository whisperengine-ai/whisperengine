#!/usr/bin/env python3
"""
Start Web UI with proper environment and WebSocket support
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['LLM_CHAT_API_URL'] = 'http://127.0.0.1:1234/v1'
os.environ['LLM_MODEL_NAME'] = 'llama-3.2-3b-instruct'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def start_webui():
    """Start Web UI with real AI and WebSocket support"""
    
    print('🚀 Starting WhisperEngine Web UI with Real AI & WebSocket Support')
    print('✅ LLM Server: http://127.0.0.1:1234/v1')
    print('✅ Model: llama-3.2-3b-instruct')
    print('✅ WebSocket: Enabled')
    print('🌐 Web UI: http://127.0.0.1:8081')
    print('💬 Try sending a message - you should get REAL AI responses!')
    print()
    
    # Import Web UI components
    from src.ui.web_ui import create_web_ui
    from src.config.adaptive_config import AdaptiveConfigManager
    from src.database.database_integration import DatabaseIntegrationManager
    
    # Create components
    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)
    web_ui = create_web_ui(db_manager=db_manager, config_manager=config_manager)
    
    # Start the server
    await web_ui.start(host='127.0.0.1', port=8081, open_browser=False)

if __name__ == "__main__":
    try:
        asyncio.run(start_webui())
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")
    except Exception as e:
        print(f"❌ Error starting Web UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)