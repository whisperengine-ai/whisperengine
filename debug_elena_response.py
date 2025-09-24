#!/usr/bin/env python3
"""
Debug Elena's actual response generation with memory integration
"""
import asyncio
import logging
import os
import json
from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.llm.llm_protocol import create_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_elena_response():
    """Debug Elena's complete response pipeline"""
    logger.info("🔍 DEBUGGING: Elena's Complete Response Pipeline")
    
    # Test configuration
    user_id = "672814231002939413"
    test_message = "Elena, what patterns do you notice in our conversations?"
    
    try:
        # 1. Initialize components
        logger.info("=== Step 1: Component Initialization ===")
        memory_manager = create_memory_manager(memory_type="vector")
        cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
        llm_client = create_llm_client(llm_client_type="openrouter")
        
        # 2. Memory retrieval
        logger.info("=== Step 2: Memory Retrieval ===")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=test_message,
            limit=10
        )
        logger.info(f"Retrieved {len(memories)} memories")
        
        # 3. Conversation history
        logger.info("=== Step 3: Conversation History ===")
        conversation_history = await memory_manager.get_conversation_history(
            user_id=user_id,
            limit=5
        )
        logger.info(f"Retrieved {len(conversation_history)} conversation entries")
        
        # 4. CDL prompt creation
        logger.info("=== Step 4: CDL Prompt Creation ===")
        character_file = "characters/examples/elena-rodriguez.json"
        system_prompt = await cdl_integration.create_character_aware_prompt(
            character_file=character_file,
            user_id=user_id,
            message_content=test_message
        )
        logger.info(f"System prompt created: {len(system_prompt)} characters")
        
        # 5. Check memory integration in prompt
        logger.info("=== Step 5: Memory Integration Check ===")
        memory_section_found = "relevant memories" in system_prompt.lower() or "conversation history" in system_prompt.lower()
        logger.info(f"Memory section in prompt: {memory_section_found}")
        
        if memory_section_found:
            # Find memory section
            lines = system_prompt.split('\n')
            memory_lines = [i for i, line in enumerate(lines) if 'memor' in line.lower() or 'conversation' in line.lower()]
            logger.info(f"Memory-related lines found at: {memory_lines[:5]}")
            
            # Show some memory content
            for line_num in memory_lines[:3]:
                if line_num < len(lines):
                    logger.info(f"Line {line_num}: {lines[line_num][:100]}...")
        
        # 6. Create full conversation context
        logger.info("=== Step 6: Full Conversation Context ===")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_message}
        ]
        
        # 7. Generate response
        logger.info("=== Step 7: LLM Response Generation ===")
        try:
            response = await llm_client.generate_response(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            logger.info(f"Generated response: {len(response)} characters")
            logger.info(f"Response preview: {response[:200]}...")
            
            # Check if response mentions memory/patterns
            mentions_memory = any(keyword in response.lower() for keyword in [
                'pattern', 'conversation', 'history', 'remember', 'noticed', 'interactions'
            ])
            logger.info(f"Response mentions memory/patterns: {mentions_memory}")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            response = None
        
        # 8. Summary
        logger.info("=== Step 8: Pipeline Summary ===")
        logger.info(f"✅ Memory retrieval: {len(memories)} memories")
        logger.info(f"✅ Conversation history: {len(conversation_history)} entries")
        logger.info(f"✅ CDL prompt: {len(system_prompt)} chars")
        logger.info(f"{'✅' if memory_section_found else '❌'} Memory integration in prompt: {memory_section_found}")
        logger.info(f"{'✅' if response else '❌'} LLM response: {'Generated' if response else 'Failed'}")
        
        # 9. Detailed memory content analysis
        logger.info("=== Step 9: Memory Content Analysis ===")
        if memories:
            logger.info("Top 3 memory contents:")
            for i, memory in enumerate(memories[:3]):
                content = memory.get('content', '')[:100]
                score = memory.get('score', 0)
                timestamp = memory.get('timestamp', '')
                logger.info(f"  Memory {i+1}: Score={score:.3f}, Time={timestamp[:19]}")
                logger.info(f"    Content: {content}...")
        
        return {
            'memories_count': len(memories),
            'conversation_count': len(conversation_history),
            'prompt_length': len(system_prompt),
            'memory_integrated': memory_section_found,
            'response_generated': response is not None,
            'response_mentions_memory': mentions_memory if response else False
        }
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(debug_elena_response())