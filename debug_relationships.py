#!/usr/bin/env python3
"""
Debug script to test the relationship query issue
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_database.multi_entity_manager import MultiEntityRelationshipManager
from env_manager import load_environment

async def test_relationship_query():
    """Test the relationship query to understand the data structure"""
    
    # Load environment
    if not load_environment():
        print("Failed to load environment")
        return
    
    # Initialize the multi-entity manager
    manager = MultiEntityRelationshipManager()
    
    # Test Discord ID from the logs
    discord_id = "672814231002939413"
    
    print(f"Testing get_user_characters for discord_id: {discord_id}")
    
    # Set debug level for the manager's logger
    import logging
    logging.basicConfig(level=logging.DEBUG)
    manager.logger.setLevel(logging.DEBUG)
    
    try:
        # Get user characters
        characters = await manager.get_user_characters(discord_id)
        print(f"Result: {characters}")
        print(f"Number of characters found: {len(characters)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Let's also test the individual components
        print("\n--- Testing individual components ---")
        
        try:
            # Test getting user entity ID
            user_entity_id = await manager.get_user_entity_id_by_discord_id(discord_id)
            print(f"User entity ID: {user_entity_id}")
            
            if user_entity_id:
                # Test getting relationships directly
                from graph_database.multi_entity_models import RelationshipType
                relationships = await manager.get_entity_relationships(
                    user_entity_id, 
                    [RelationshipType.CREATED_BY, RelationshipType.FAVORITE_OF, RelationshipType.TRUSTED_BY]
                )
                print(f"Raw relationships: {relationships}")
                print(f"Number of relationships: {len(relationships)}")
                
                for i, rel in enumerate(relationships):
                    print(f"Relationship {i}: {rel}")
                    print(f"  Type: {type(rel)}")
                    if hasattr(rel, 'keys'):
                        print(f"  Keys: {list(rel.keys())}")
                    
        except Exception as inner_e:
            print(f"Inner error: {inner_e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_relationship_query())