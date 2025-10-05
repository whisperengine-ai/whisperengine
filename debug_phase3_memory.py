#!/usr/bin/env python3
"""
Debug Phase 3 issue - check memory manager structure
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Set required environment variables for testing
os.environ['FASTEMBED_CACHE_PATH'] = "/tmp/fastembed_cache"
os.environ['QDRANT_HOST'] = "localhost"
os.environ['QDRANT_PORT'] = "6334"

async def debug_memory_manager():
    """Debug memory manager to understand Phase 3 issue"""
    try:
        from src.memory.memory_protocol import create_memory_manager
        
        print("🔧 Creating memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        
        print(f"Memory manager type: {type(memory_manager)}")
        print(f"Memory manager attributes: {dir(memory_manager)}")
        
        # Check if vector_store attribute exists
        has_vector_store = hasattr(memory_manager, 'vector_store')
        print(f"Has vector_store: {has_vector_store}")
        
        if has_vector_store:
            vector_store = memory_manager.vector_store
            print(f"Vector store type: {type(vector_store)}")
            print(f"Vector store attributes: {dir(vector_store)}")
            
            # Check if the method exists
            has_cluster_method = hasattr(vector_store, 'get_memory_clusters_for_roleplay')
            print(f"Has get_memory_clusters_for_roleplay: {has_cluster_method}")
        
        # Now let's test the Phase 4 integration directly
        print("\n🧪 Testing Phase 4 Integration directly...")
        from src.intelligence.phase4_human_like_integration import Phase4HumanLikeIntegration
        from src.intelligence.simplified_emotion_manager import SimplifiedEmotionManager
        
        emotion_manager = SimplifiedEmotionManager(memory_manager)
        
        phase4_integration = Phase4HumanLikeIntegration(
            simplified_emotion_manager=emotion_manager,
            memory_manager=memory_manager,
            enable_adaptive_mode=True,
            conversation_mode="adaptive"
        )
        
        print("🚀 Testing process_comprehensive_message...")
        result = await phase4_integration.process_comprehensive_message(
            user_id="debug_user",
            message="Hello, how are you?",
            conversation_context=[],
            discord_context=None
        )
        
        print(f"Result type: {type(result)}")
        if hasattr(result, 'phase3_results'):
            print(f"Phase 3 results: {result.phase3_results}")
        else:
            print("No phase3_results attribute")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_memory_manager())