#!/usr/bin/env python3
"""Quick script to check for cat-related memories in Qdrant."""

import asyncio
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

async def check_cat_memories():
    # Initialize clients
    client = QdrantClient(host='localhost', port=6334)
    embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create embedding for cat query
    query = "tell me about my cats Luna and Minerva their personalities and behaviors"
    query_embedding = list(embedding_model.embed([query]))[0].tolist()
    
    # Search Elena's collection
    results = client.search(
        collection_name='whisperengine_memory_elena',
        query_vector=('content', query_embedding),
        limit=10,
        query_filter={
            'must': [
                {'key': 'user_id', 'match': {'value': '672814231002939413'}}
            ]
        }
    )
    
    print(f'\n🔍 Found {len(results)} memories matching cat query\n')
    print('='*80)
    
    for i, result in enumerate(results, 1):
        print(f'\n📝 Memory #{i} (relevance score: {result.score:.3f})')
        print('-'*80)
        
        # Show user message
        content = result.payload.get('content', '')
        print(f'👤 USER: {content[:300]}')
        
        # Show bot response if available
        bot_response = result.payload.get('bot_response', '')
        if bot_response:
            print(f'🤖 ELENA: {bot_response[:300]}')
        
        # Show metadata
        timestamp = result.payload.get('timestamp', 'unknown')
        memory_type = result.payload.get('memory_type', 'unknown')
        print(f'⏰ Time: {timestamp} | Type: {memory_type}')
        
    print('\n' + '='*80)
    
    # Also check total conversation count for this user
    scroll_result = client.scroll(
        collection_name='whisperengine_memory_elena',
        scroll_filter={
            'must': [
                {'key': 'user_id', 'match': {'value': '672814231002939413'}}
            ]
        },
        limit=1
    )
    
    # Get count
    count_result = client.count(
        collection_name='whisperengine_memory_elena',
        count_filter={
            'must': [
                {'key': 'user_id', 'match': {'value': '672814231002939413'}}
            ]
        }
    )
    
    print(f'\n📊 Total memories for user: {count_result.count}')

if __name__ == '__main__':
    asyncio.run(check_cat_memories())
