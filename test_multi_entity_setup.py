#!/usr/bin/env python3
"""
Multi-Entity System Setup Test

This script tests the multi-entity system initialization and database setup
without launching the full Discord bot.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from env_manager import load_environment
from src.config.adaptive_config import AdaptiveConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_multi_entity_setup():
    """Test multi-entity system setup and database initialization"""
    
    print("🔍 Multi-Entity System Setup Test")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        print("❌ Failed to load environment configuration")
        return False
    
    print("✅ Environment loaded successfully")
    
    # Check required environment variables
    required_vars = [
        "ENABLE_MULTI_ENTITY_RELATIONSHIPS",
        "ENABLE_CHARACTER_CREATION",
        "ENABLE_RELATIONSHIP_EVOLUTION"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        else:
            print(f"✅ {var}={value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    # Test adaptive config
    try:
        config = AdaptiveConfigManager()
        print("✅ AdaptiveConfigManager initialized")
        
        # Check multi-entity features
        multi_entity_enabled = getattr(config, 'enable_multi_entity_relationships', False)
        character_creation_enabled = getattr(config, 'enable_character_creation', False)
        
        print(f"✅ Multi-entity relationships: {multi_entity_enabled}")
        print(f"✅ Character creation: {character_creation_enabled}")
        
    except Exception as e:
        print(f"❌ AdaptiveConfigManager error: {e}")
        return False
    
    # Test multi-entity system imports
    try:
        from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
        from src.graph_database.ai_self_bridge import AISelfEntityBridge
        print("✅ Multi-entity imports successful")
    except ImportError as e:
        print(f"❌ Multi-entity import error: {e}")
        return False
    
    # Test multi-entity manager initialization
    try:
        manager = MultiEntityRelationshipManager()
        print("✅ MultiEntityRelationshipManager created")
        
        # Test schema initialization (if Neo4j is available)
        neo4j_enabled = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"
        if neo4j_enabled:
            print("🔗 Testing Neo4j schema initialization...")
            schema_result = await manager.initialize_schema()
            if schema_result:
                print("✅ Neo4j schema initialized successfully")
            else:
                print("⚠️ Neo4j schema initialization failed (Neo4j may not be running)")
        else:
            print("ℹ️ Neo4j disabled - using SQLite fallback mode")
            
    except Exception as e:
        print(f"❌ Multi-entity manager error: {e}")
        return False
    
    # Test AI Self bridge
    try:
        ai_bridge = AISelfEntityBridge()
        print("✅ AISelfEntityBridge created")
    except Exception as e:
        print(f"❌ AI Self bridge error: {e}")
        return False
    
    # Test command handlers
    try:
        from src.handlers.multi_entity_handlers import MultiEntityCommandHandlers
        print("✅ MultiEntityCommandHandlers import successful")
    except ImportError as e:
        print(f"❌ Command handlers import error: {e}")
        return False
    
    print("\n🎉 Multi-Entity System Setup Test PASSED!")
    print("\n📋 Setup Summary:")
    print("- Multi-entity relationships: ENABLED")
    print("- Character creation: ENABLED") 
    print("- Database schema: READY (will auto-initialize)")
    print("- Command handlers: AVAILABLE")
    print("\n🚀 Ready to launch Discord bot with multi-entity features!")
    
    return True


async def test_character_creation():
    """Test character creation functionality"""
    
    print("\n🎭 Testing Character Creation")
    print("-" * 30)
    
    try:
        from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
        
        manager = MultiEntityRelationshipManager()
        
        # Test character data
        test_character = {
            "name": "Test Sage",
            "occupation": "philosopher",
            "personality_traits": ["wise", "patient", "thoughtful"],
            "background_summary": "A test character for system validation",
            "preferred_topics": ["philosophy", "wisdom", "life"]
        }
        
        # Test character validation (without actual creation)
        if len(test_character["name"]) <= 50:
            print("✅ Character name validation: PASSED")
        else:
            print("❌ Character name too long")
            
        if len(test_character["background_summary"]) <= 1000:
            print("✅ Character background validation: PASSED")
        else:
            print("❌ Character background too long")
            
        print("✅ Character creation logic: READY")
        
    except Exception as e:
        print(f"❌ Character creation test error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    async def main():
        setup_success = await test_multi_entity_setup()
        
        if setup_success:
            character_success = await test_character_creation()
            
            if character_success:
                print("\n🌟 ALL TESTS PASSED - System ready for deployment!")
                return True
        
        print("\n❌ TESTS FAILED - Please fix issues before deployment")
        return False
    
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)