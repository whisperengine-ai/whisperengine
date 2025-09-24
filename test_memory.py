import asyncio
import os
from src.memory.qdrant_optimization import QdrantQueryOptimizer
from src.memory.vector_memory_system import VectorMemoryManager

async def test():
    print("Starting memory test...")
    
    config = {
        'qdrant_host': 'qdrant',
        'qdrant_port': 6333,
        'collection_name': 'whisperengine_memory',
        'bot_name': 'elena',
        'embeddings': {
            'model_name': 'snowflake/snowflake-arctic-embed-xs',
            'dimension': 384,
            'normalize': True
        }
    }
    
    print(f"Using config: {config}")
    vm = VectorMemoryManager(config=config)
    qo = QdrantQueryOptimizer(vector_manager=vm)
    
    print("Running optimized search...")
    try:
        result = await qo.optimized_search(
            query='test query', 
            user_id='test_user', 
            limit=5
        )
        print(f'Search successful: {len(result) >= 0}')
        print(f'Number of results: {len(result)}')
    except Exception as e:
        print(f"Error running search: {e}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    asyncio.run(test())