#!/usr/bin/env python3
"""
Test if Elena's Universal Chat Orchestrator can now access the bot_core correctly
"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_bot_core_access():
    """Test if the Universal Chat condition now passes"""
    print("🔍 Testing if Elena's Universal Chat can now access bot_core...")
    
    # Look for the specific logging that shows the condition check
    import subprocess
    
    try:
        # Trigger a message to Elena through a test (this would normally be done via Discord)
        # For now, just check if the system is set up correctly
        
        result = subprocess.run([
            'docker', 'exec', 'whisperengine-elena-bot',
            'python', '-c',
            '''
import os
import sys
sys.path.insert(0, "/app")

# Test if we can import the Universal Chat and check the condition
try:
    from src.platforms.universal_chat import UniversalChatOrchestrator
    from src.database.database_integration import DatabaseIntegrationManager
    
    print("✅ Can import Universal Chat Orchestrator")
    
    # Create a test orchestrator
    db_manager = DatabaseIntegrationManager()
    orchestrator = UniversalChatOrchestrator(db_manager=db_manager)
    
    print(f"✅ Orchestrator created, bot_core type: {type(orchestrator.bot_core)}")
    
    # Check if it has memory_manager when bot_core is set
    if orchestrator.bot_core and hasattr(orchestrator.bot_core, "memory_manager"):
        print("✅ bot_core has memory_manager - will use _generate_full_ai_response")
    else:
        print("❌ bot_core missing or no memory_manager - will use _generate_basic_ai_response")
        print(f"   bot_core: {orchestrator.bot_core}")
        if orchestrator.bot_core:
            attrs = [attr for attr in dir(orchestrator.bot_core) if not attr.startswith('_')]
            print(f"   available attributes: {attrs[:10]}...")  # Show first 10
    
except Exception as e:
    print(f"❌ Error testing condition: {e}")
    import traceback
    traceback.print_exc()
'''
        ], capture_output=True, text=True, check=False)
        
        print("🔍 Container test output:")
        print(result.stdout)
        if result.stderr:
            print("⚠️ Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running container test: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_core_access())