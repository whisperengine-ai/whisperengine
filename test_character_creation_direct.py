#!/usr/bin/env python3
"""
Direct test for multi-entity character creation to reproduce Neo4j error
"""
import asyncio
import sys
import os
sys.path.append(os.path.abspath('.'))

from env_manager import load_environment

async def test_character_creation():
    """Test character creation directly to reproduce Neo4j error"""
    print("🧪 Testing Character Creation with Neo4j...")
    
    # Load environment
    if not load_environment():
        print("❌ Environment loading failed")
        return
    print("✅ Environment loaded")
    
    try:
        from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
        print("✅ MultiEntityRelationshipManager import successful")
        
        # Initialize manager
        manager = MultiEntityRelationshipManager()
        print("✅ Manager initialized")
        
        # Create test character data that should trigger the Neo4j error
        test_character = {
            'name': 'TestChar',
            'character_type': 'assistant',
            'description': 'A test character',
            'personality_traits': ['helpful', 'friendly'],
            'backstory': 'A character created for testing',
            'user_preferences': {},  # This empty dict should trigger the error
            'created_at': '2025-09-17T16:00:00Z'
        }
        
        print(f"✅ Test character data prepared: {test_character}")
        print(f"📋 user_preferences type: {type(test_character['user_preferences'])}")
        
        # Attempt character creation - this should trigger the Neo4j error
        print("🚀 Attempting to create character...")
        character_id = await manager.create_character_entity(
            character_data=test_character,
            creator_user_id="test_user_123"
        )
        
        if character_id:
            print(f"✅ Character created successfully with ID: {character_id}")
        else:
            print("❌ Character creation returned None")
            
    except Exception as e:
        print(f"❌ Character creation failed with error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_character_creation())