#!/usr/bin/env python3
"""
Start WhisperEngine Web UI with real AI responses
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set LLM configuration for LM Studio
os.environ['LLM_CHAT_API_URL'] = 'http://127.0.0.1:1234/v1'
os.environ['LLM_MODEL_NAME'] = 'llama-3.2-3b-instruct'

async def start_webui():
    """Start the Web UI with real AI responses"""
    print("🚀 Starting WhisperEngine Web UI with Real AI")
    print("=" * 50)
    print("✅ LLM Server: LM Studio (http://127.0.0.1:1234)")
    print("✅ Model: llama-3.2-3b-instruct")
    print("✅ Architecture: Universal Chat Orchestrator")
    print("✅ Status: Real AI Responses (no more mock messages!)")
    print()
    print("🌐 Web UI will be available at: http://127.0.0.1:8080")
    print("🔥 Press Ctrl+C to stop")
    print()
    
    # Import and start Web UI
    from src.ui.web_ui import create_web_ui
    from src.config.adaptive_config import AdaptiveConfigManager
    from src.database.database_integration import DatabaseIntegrationManager
    
    # Create components
    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)
    web_ui = create_web_ui(db_manager=db_manager, config_manager=config_manager)
    
    # Start the server
    await web_ui.start(host="127.0.0.1", port=8080, open_browser=True)

if __name__ == "__main__":
    try:
        asyncio.run(start_webui())
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")
    except Exception as e:
        print(f"❌ Error starting Web UI: {e}")
        sys.exit(1)