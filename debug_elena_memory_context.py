#!/usr/bin/env python3
"""
Deep dive into Elena's memory context integration
"""
import asyncio
import logging
import os
from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_elena_memory_context():
    """Debug Elena's actual memory context in prompt"""
    logger.info("🔍 DEBUGGING: Elena's Memory Context Integration")
    
    user_id = "672814231002939413"
    test_message = "what did we talk about yesterday?"
    
    try:
        # Initialize components
        memory_manager = create_memory_manager(memory_type="vector")
        cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
        
        # Get memories directly first
        logger.info("=== Direct Memory Query ===")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=test_message,
            limit=10
        )
        logger.info(f"Retrieved {len(memories)} memories directly")
        
        for i, memory in enumerate(memories[:3]):
            content = memory.get('content', '')[:100]
            score = memory.get('score', 0)
            timestamp = memory.get('timestamp', '')
            logger.info(f"Memory {i+1}: Score={score:.3f}, Time={timestamp[:19]}")
            logger.info(f"  Content: {content}...")
        
        # Get conversation history
        logger.info("\n=== Direct Conversation History ===")
        conversation_history = await memory_manager.get_conversation_history(
            user_id=user_id,
            limit=5
        )
        logger.info(f"Retrieved {len(conversation_history)} conversation entries")
        
        for i, conv in enumerate(conversation_history):
            role = conv.get('role', 'unknown')
            content = conv.get('content', '')[:100]
            timestamp = conv.get('timestamp', '')
            logger.info(f"Conversation {i+1}: Role={role}, Time={timestamp[:19]}")
            logger.info(f"  Content: {content}...")
        
        # Generate CDL prompt
        logger.info("\n=== CDL Prompt Generation ===")
        character_file = "characters/examples/elena-rodriguez.json"
        system_prompt = await cdl_integration.create_character_aware_prompt(
            character_file=character_file,
            user_id=user_id,
            message_content=test_message
        )
        
        # Extract memory section from prompt
        logger.info(f"System prompt length: {len(system_prompt)} characters")
        
        if "CONVERSATION MEMORY & CONTEXT" in system_prompt:
            logger.info("\n=== Memory Section in Prompt ===")
            lines = system_prompt.split('\n')
            memory_start = None
            for i, line in enumerate(lines):
                if 'CONVERSATION MEMORY & CONTEXT' in line:
                    memory_start = i
                    break
            
            if memory_start:
                # Show the entire memory section
                memory_end = memory_start + 1
                for i in range(memory_start + 1, len(lines)):
                    if lines[i].strip() and lines[i].strip().isupper() and lines[i].strip().endswith(':'):
                        memory_end = i
                        break
                    elif i == len(lines) - 1:
                        memory_end = i + 1
                
                logger.info("Full memory section in prompt:")
                for i in range(memory_start, min(memory_end, len(lines))):
                    logger.info(f"  {lines[i]}")
        else:
            logger.warning("❌ No memory section found in prompt!")
        
        # Check if memories contain yesterday's conversations
        logger.info("\n=== Memory Content Analysis ===")
        yesterday_keywords = ['yesterday', 'snorkeling', 'ocean', 'diving', 'marine']
        relevant_count = 0
        
        for memory in memories:
            content = memory.get('content', '').lower()
            for keyword in yesterday_keywords:
                if keyword in content:
                    relevant_count += 1
                    logger.info(f"Found relevant memory with '{keyword}': {content[:150]}...")
                    break
        
        logger.info(f"Found {relevant_count} potentially relevant memories out of {len(memories)}")
        
        return {
            'memories_retrieved': len(memories),
            'conversations_retrieved': len(conversation_history),
            'memory_section_in_prompt': "CONVERSATION MEMORY & CONTEXT" in system_prompt,
            'relevant_memories_found': relevant_count,
            'system_prompt_length': len(system_prompt)
        }
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(debug_elena_memory_context())