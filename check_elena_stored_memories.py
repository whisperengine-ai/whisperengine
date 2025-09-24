#!/usr/bin/env python3
"""
Check Elena's actual stored memories and conversations
"""
import asyncio
import logging
from src.memory.memory_protocol import create_memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_elena_stored_memories():
    """Check what's actually stored in Elena's memories"""
    logger.info("🔍 CHECKING: Elena's Actual Stored Memories")
    
    user_id = "672814231002939413"
    
    try:
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Get broader search for all memories
        logger.info("=== Searching for ALL user memories ===")
        all_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="conversation discussion talk topics",
            limit=20
        )
        
        logger.info(f"Found {len(all_memories)} total memories")
        
        # Analyze memory types and content
        conversation_memories = []
        question_memories = []
        substantive_memories = []
        
        for i, memory in enumerate(all_memories):
            content = memory.get('content', '')
            memory_type = memory.get('memory_type', 'unknown')
            role = memory.get('metadata', {}).get('role', 'unknown') if 'metadata' in memory else 'unknown'
            
            logger.info(f"\nMemory {i+1}:")
            logger.info(f"  Type: {memory_type}")
            logger.info(f"  Role: {role}")
            logger.info(f"  Content: {content[:200]}...")
            
            # Categorize memory
            if content.strip().endswith('?'):
                question_memories.append(memory)
            elif memory_type == 'conversation':
                conversation_memories.append(memory)
            elif len(content.split()) > 5:  # More substantial content
                substantive_memories.append(memory)
        
        logger.info(f"\n=== Memory Analysis ===")
        logger.info(f"Total memories: {len(all_memories)}")
        logger.info(f"Question memories: {len(question_memories)}")
        logger.info(f"Conversation memories: {len(conversation_memories)}")
        logger.info(f"Substantive memories: {len(substantive_memories)}")
        
        # Check for any memories with ocean/marine topics
        logger.info(f"\n=== Topic Analysis ===")
        marine_topics = ['ocean', 'marine', 'sea', 'water', 'fish', 'coral', 'diving', 'snorkeling', 'research', 'biology']
        found_topics = {}
        
        for memory in all_memories:
            content = memory.get('content', '').lower()
            for topic in marine_topics:
                if topic in content:
                    if topic not in found_topics:
                        found_topics[topic] = []
                    found_topics[topic].append(content[:100])
        
        if found_topics:
            logger.info("Found marine-related topics:")
            for topic, contents in found_topics.items():
                logger.info(f"  {topic}: {len(contents)} mentions")
                for content in contents[:2]:  # Show first 2 examples
                    logger.info(f"    - {content}...")
        else:
            logger.info("❌ No marine biology topics found in memories!")
        
        return {
            'total_memories': len(all_memories),
            'question_memories': len(question_memories),
            'conversation_memories': len(conversation_memories),
            'substantive_memories': len(substantive_memories),
            'marine_topics_found': len(found_topics)
        }
        
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(check_elena_stored_memories())