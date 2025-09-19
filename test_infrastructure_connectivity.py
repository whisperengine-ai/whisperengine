#!/usr/bin/env python3
"""
Infrastructure Connectivity Test for Hierarchical Memory Architecture
Tests actual connections to all 4 tiers with real infrastructure services
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.core.storage_abstraction import HierarchicalMemoryManager

async def test_infrastructure_connectivity():
    """Test connectivity to all 4 tiers of the hierarchical memory system"""
    
    print("🚀 Testing Hierarchical Memory Infrastructure Connectivity")
    print("=" * 60)
    
    # Configuration for hierarchical memory
    config = {
        'redis': {
            'url': 'redis://localhost:6379',
            'ttl': 1800
        },
        'postgresql': {
            'url': 'postgresql://bot_user:securepassword123@localhost:5432/whisper_engine'
        },
        'chromadb': {
            'host': 'localhost',
            'port': 8000
        },
        'neo4j': {
            'uri': 'bolt://localhost:7687',
            'username': 'neo4j',
            'password': 'neo4j_password_change_me',
            'database': 'neo4j'
        },
        'redis_enabled': True,
        'postgresql_enabled': True,
        'chromadb_enabled': True,
        'neo4j_enabled': True
    }
    
    try:
        # Initialize hierarchical memory manager
        print("🔧 Initializing Hierarchical Memory Manager...")
        manager = HierarchicalMemoryManager(config)
        
        print("⏳ Connecting to all tiers...")
        await manager.initialize()
        
        print("✅ Successfully connected to all tiers!")
        print()
        
        # Test basic operations
        print("🧪 Testing basic operations...")
        
        # Store a test conversation
        conversation_id = await manager.store_conversation(
            user_id="test_user_infra",
            user_message="Testing the new hierarchical memory system",
            bot_response="Great! The 4-tier architecture is working perfectly with real infrastructure!"
        )
        print(f"✅ Stored conversation: {conversation_id}")
        
        # Retrieve context
        context = await manager.get_conversation_context(
            user_id="test_user_infra",
            current_query="hierarchical memory test",
            max_context_length=1000
        )
        print(f"✅ Retrieved context: {len(context.to_context_string())} characters")
        print(f"   Recent messages: {len(context.recent_messages)}")
        print(f"   Assembly metadata: {context.assembly_metadata}")
        
        # Performance validation
        assembly_time = context.assembly_metadata.get('assembly_time_ms', float('inf'))
        if assembly_time < 100:
            print(f"🚀 PERFORMANCE TARGET MET: {assembly_time}ms < 100ms")
        else:
            print(f"⚠️  Performance target missed: {assembly_time}ms > 100ms")
        
        print()
        print("🎉 Infrastructure Connectivity Test PASSED!")
        print("All 4 tiers are connected and working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if 'manager' in locals():
                # Note: Add cleanup method if needed
                pass
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup warning: {cleanup_error}")

if __name__ == "__main__":
    print("Hierarchical Memory Architecture - Infrastructure Test")
    print("=" * 60)
    
    # Check if we're in the right environment
    if not os.path.exists('.env'):
        print("❌ .env file not found. Run from project root directory.")
        sys.exit(1)
    
    # Run the test
    success = asyncio.run(test_infrastructure_connectivity())
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. ✅ Infrastructure setup complete")
        print("2. 🔄 Ready for WhisperEngine integration")
        print("3. 🚀 Deploy with ./bot.sh start dev")
        sys.exit(0)
    else:
        print("\n🔧 Infrastructure needs attention before proceeding")
        sys.exit(1)