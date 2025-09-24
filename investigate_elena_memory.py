#!/usr/bin/env python3
"""
Deep investigation into Elena's memory integration issue
"""
import asyncio
import os
import logging
import json
from datetime import datetime
from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def investigate_elena_memory_integration():
    """Deep investigation into Elena's memory integration"""
    
    # Set environment for Elena
    os.environ["DISCORD_BOT_NAME"] = "Elena"
    os.environ["QDRANT_HOST"] = "qdrant"
    os.environ["QDRANT_PORT"] = "6333"
    os.environ["QDRANT_COLLECTION_NAME"] = "whisperengine_memory"
    
    user_id = "672814231002939413"  # MarkAnthony's user ID
    
    try:
        logger.info("🔍 DEEP INVESTIGATION: Elena's Memory Integration")
        
        # Create memory manager
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Test 1: CDL Integration
        logger.info("\n=== Test 1: CDL Character Integration ===")
        cdl_integration = CDLAIPromptIntegration()
        
        # Test query that should trigger memory about conversation patterns
        test_message = "Elena, can you analyze our conversation history and tell me what patterns you notice in our interactions?"
        
        # Get memories first
        relevant_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=test_message,
            limit=5
        )
        
        logger.info(f"Retrieved {len(relevant_memories) if relevant_memories else 0} memories for context")
        
        # Test character-aware prompt creation
        character_prompt = await cdl_integration.create_character_aware_prompt(
            character_file='characters/examples/elena-rodriguez.json',
            user_id=user_id,
            message_content=test_message,
            pipeline_result=None
        )
        
        logger.info(f"Character prompt created: {len(character_prompt)} characters")
        logger.info(f"Character prompt preview: {character_prompt[:200]}...")
        
        # Test 2: Memory Context Building
        logger.info("\n=== Test 2: Memory Context Building ===")
        
        if relevant_memories:
            # Check if memories have the expected format
            for i, memory in enumerate(relevant_memories[:3]):
                logger.info(f"Memory {i+1} structure: {list(memory.keys())}")
                logger.info(f"Memory {i+1} content preview: {memory.get('content', '')[:100]}...")
                logger.info(f"Memory {i+1} metadata: {memory.get('metadata', {})}")
                logger.info(f"Memory {i+1} timestamp: {memory.get('timestamp', 'N/A')}")
                logger.info(f"Memory {i+1} score: {memory.get('score', 'N/A')}")
                logger.info("---")
        
        # Test 3: Check conversation history format
        logger.info("\n=== Test 3: Conversation History Format ===")
        
        conversation_history = await memory_manager.get_conversation_history(
            user_id=user_id,
            limit=3
        )
        
        if conversation_history:
            for i, entry in enumerate(conversation_history):
                logger.info(f"Conversation {i+1} structure: {list(entry.keys())}")
                logger.info(f"Conversation {i+1} role: {entry.get('role', 'N/A')}")
                logger.info(f"Conversation {i+1} content: {entry.get('content', '')[:100]}...")
                logger.info("---")
        
        # Test 4: Context-aware memories with different queries
        logger.info("\n=== Test 4: Context-Aware Memory Queries ===")
        
        test_queries = [
            "what do you know about my interests",
            "tell me about our previous conversations", 
            "what patterns have you noticed about me",
            "conversation history analysis"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            
            if hasattr(memory_manager, 'retrieve_context_aware_memories'):
                memories = await memory_manager.retrieve_context_aware_memories(
                    user_id=user_id,
                    query=query,
                    max_memories=3,
                    context={"type": "conversation_analysis"},
                    emotional_context="general conversation"
                )
                
                logger.info(f"  → Retrieved {len(memories) if memories else 0} memories")
                if memories:
                    for memory in memories[:2]:
                        content = memory.get('content', '')[:80] + '...' if len(memory.get('content', '')) > 80 else memory.get('content', '')
                        logger.info(f"    - {content}")
            else:
                memories = await memory_manager.retrieve_relevant_memories(
                    user_id=user_id,
                    query=query,
                    limit=3
                )
                logger.info(f"  → Retrieved {len(memories) if memories else 0} memories (basic)")
        
        # Test 5: Check for memory integration flags
        logger.info("\n=== Test 5: Memory Integration Flags ===")
        
        memory_flags = {
            "ENABLE_CONVERSATION_MEMORY": os.getenv("ENABLE_CONVERSATION_MEMORY", "Not set"),
            "ENABLE_EPISODIC_MEMORY": os.getenv("ENABLE_EPISODIC_MEMORY", "Not set"),
            "ENABLE_SEMANTIC_MEMORY": os.getenv("ENABLE_SEMANTIC_MEMORY", "Not set"),
            "ENABLE_HIERARCHICAL_MEMORY": os.getenv("ENABLE_HIERARCHICAL_MEMORY", "Not set"),
            "ENABLE_ADVANCED_MEMORY_FEATURES": os.getenv("ENABLE_ADVANCED_MEMORY_FEATURES", "Not set"),
            "ENABLE_CONVERSATION_INTELLIGENCE": os.getenv("ENABLE_CONVERSATION_INTELLIGENCE", "Not set"),
            "MEMORY_SYSTEM_TYPE": os.getenv("MEMORY_SYSTEM_TYPE", "Not set"),
        }
        
        for flag, value in memory_flags.items():
            logger.info(f"  {flag}: {value}")
        
        # Test 6: Check if memories contain conversation analysis content
        logger.info("\n=== Test 6: Memory Content Analysis ===")
        
        analysis_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="conversation patterns interactions analysis history",
            limit=10
        )
        
        if analysis_memories:
            logger.info(f"Found {len(analysis_memories)} memories about conversation analysis")
            
            for i, memory in enumerate(analysis_memories[:5]):
                content = memory.get('content', '')
                if 'pattern' in content.lower() or 'conversation' in content.lower() or 'interaction' in content.lower():
                    logger.info(f"  Analysis Memory {i+1}: {content[:150]}...")
                    logger.info(f"    → Timestamp: {memory.get('timestamp', 'N/A')}")
                    logger.info(f"    → Score: {memory.get('score', 'N/A')}")
                    logger.info("    ---")
        
        logger.info("\n🔍 INVESTIGATION COMPLETE!")
        
    except Exception as e:
        logger.error(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_elena_memory_integration())