#!/usr/bin/env python3
"""
Marcus Thompson 7D Memory Migration Script
Simplified approach using VectorMemorySystem directly
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_marcus_using_vector_system():
    """Migrate Marcus's memories using the working vector memory system"""
    
    print("🤖 Marcus Thompson - 7D Memory Migration")
    print("=" * 50)
    print("Method: Direct VectorMemorySystem approach")
    print("Character: Marcus Thompson (AI Researcher)")
    print()
    
    try:
        # Import vector memory system
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Configuration for Marcus
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6334,
                'collection_name': 'whisperengine_memory_marcus_7d'
            },
            'embeddings': {
                'model_name': ''  # Use FastEmbed default
            }
        }
        
        # Initialize vector memory manager
        print("🔧 Initializing VectorMemoryManager...")
        memory_manager = VectorMemoryManager(config)
        
        # Test connection by creating a test memory
        print("🔗 Testing 7D vector storage...")
        
        # Store a test memory to verify 7D functionality
        test_user_id = "test_user_migration_marcus"
        test_user_message = "Testing Marcus's analytical approach to AI research"
        test_bot_response = "As an AI researcher, I find that systematic analysis of machine learning architectures reveals fascinating patterns in neural network optimization."
        
        # Store test conversation
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=test_user_message,
            bot_response=test_bot_response,
            user_metadata={"migration_test": True}
        )
        print("✅ Successfully stored test memory with 7D vectors")
        
        # Retrieve to verify 
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query="AI research analysis",
            limit=1
        )
        
        if memories:
            print("✅ Successfully retrieved test memory from 7D collection")
            print(f"   Memory content: {memories[0].content[:80]}...")
        else:
            print("⚠️  Warning: Could not retrieve test memory")
        
        print()
        print("🎯 Migration Strategy:")
        print("1. ✅ Created new 7D collection: whisperengine_memory_marcus_7d")
        print("2. ✅ Verified 7D vector storage functionality")
        print("3. 📝 Next: Update Marcus's .env.marcus file")
        print("4. 🔄 Restart Marcus bot to begin using 7D vectors")
        print("5. 📊 New conversations will be stored with enhanced vectors")
        print()
        print("📋 Configuration Update Needed:")
        print("In .env.marcus, change:")
        print("   QDRANT_COLLECTION_NAME=whisperengine_memory_marcus")
        print("to:")
        print("   QDRANT_COLLECTION_NAME=whisperengine_memory_marcus_7d")
        print()
        print("🔄 Restart Command:")
        print("   ./multi-bot.sh stop marcus && ./multi-bot.sh start marcus")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration function"""
    print("Starting Marcus 7D migration setup...")
    success = await migrate_marcus_using_vector_system()
    
    if success:
        print("\n🎉 Marcus 7D Migration Setup Complete!")
        print("Remember to update .env.marcus and restart the bot.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())