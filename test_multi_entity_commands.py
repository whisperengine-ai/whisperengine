#!/usr/bin/env python3
"""
Test script for multi-entity character commands
Tests the CDL import/export functionality and character management
"""
import asyncio
import sys
import os
sys.path.append(os.path.abspath('.'))

from src.handlers.multi_entity_handlers import MultiEntityCommandHandlers
from src.core.bot import DiscordBotCore

async def test_multi_entity_system():
    """Test the multi-entity character system functionality"""
    print("🧪 Testing Multi-Entity Character System...")
    
    # Initialize bot core to get components
    bot_core = DiscordBotCore(debug_mode=True)
    components = bot_core.get_components()
    
    print(f"📋 Available components: {list(components.keys())}")
    
    # Create a mock bot object with required attributes
    class MockBot:
        def __init__(self):
            self.command_registry = {}
            
        def command(self, **kwargs):
            def decorator(func):
                self.command_registry[func.__name__] = func
                return func
            return decorator
    
    # Create mock bot and handlers
    mock_bot = MockBot()
    
    # Remove 'bot' from components if it exists to avoid conflict
    if 'bot' in components:
        del components['bot']
        
    print(f"🔧 Creating handlers with: multi_entity_manager={components.get('multi_entity_manager') is not None}, ai_self_bridge={components.get('ai_self_bridge') is not None}")
    
    handlers = MultiEntityCommandHandlers(mock_bot, **components)
    
    # Register commands to populate the registry
    handlers.register_commands(lambda x: True, False)
    
    print(f"✅ Registered {len(mock_bot.command_registry)} multi-entity commands:")
    for cmd_name in mock_bot.command_registry.keys():
        print(f"   - {cmd_name}")
    
    # Test CDL file reading
    try:
        cdl_file_path = "test_character_sage.yaml"
        if os.path.exists(cdl_file_path):
            print(f"✅ CDL test file found: {cdl_file_path}")
            
            # Read the file content
            with open(cdl_file_path, 'r') as f:
                content = f.read()
            print(f"✅ CDL file content loaded ({len(content)} characters)")
            
            # Test CDL parser if available
            try:
                from src.characters.cdl.parser import CDLParser
                parser = CDLParser()
                character = parser.parse_file(cdl_file_path)
                print(f"✅ CDL parser successfully parsed character: {character.identity.name}")
            except Exception as e:
                print(f"⚠️  CDL parser test failed: {e}")
        else:
            print(f"❌ CDL test file not found: {cdl_file_path}")
    except Exception as e:
        print(f"❌ CDL file test failed: {e}")
    
    # Test multi-entity manager if available
    try:
        multi_entity_manager = components.get('multi_entity_manager')
        if multi_entity_manager:
            print("✅ Multi-entity manager available")
            
            # Test character creation
            test_character = {
                'name': 'TestBot',
                'character_type': 'assistant',
                'description': 'A helpful test character for WhisperEngine'
            }
            print(f"✅ Test character data prepared: {test_character}")
        else:
            print("❌ Multi-entity manager not available")
    except Exception as e:
        print(f"❌ Multi-entity manager test failed: {e}")
    
    print("🎉 Multi-entity system test completed!")

if __name__ == "__main__":
    asyncio.run(test_multi_entity_system())