#!/usr/bin/env python3
"""
Test Marcus bot memory integration
"""
import asyncio
import logging
import os
from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_marcus_memory():
    """Test Marcus's memory integration"""
    logger.info("🔍 TESTING: Marcus Bot Memory Integration")
    
    # Test configuration
    user_id = "672814231002939413"
    test_message = "Marcus, what do you remember about our AI discussions?"
    
    try:
        # Initialize components
        memory_manager = create_memory_manager(memory_type="vector")
        cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
        
        # Test memory integration in CDL prompt
        character_file = "characters/examples/marcus-thompson.json"
        system_prompt = await cdl_integration.create_character_aware_prompt(
            character_file=character_file,
            user_id=user_id,
            message_content=test_message
        )
        
        # Check for memory integration
        memory_section_found = "CONVERSATION MEMORY & CONTEXT" in system_prompt
        logger.info(f"✅ Marcus memory integration working: {memory_section_found}")
        logger.info(f"✅ Marcus system prompt length: {len(system_prompt)} characters")
        
        if memory_section_found:
            # Show memory section
            lines = system_prompt.split('\n')
            memory_start = None
            for i, line in enumerate(lines):
                if 'CONVERSATION MEMORY & CONTEXT' in line:
                    memory_start = i
                    break
            
            if memory_start:
                logger.info("🧠 Memory section found:")
                for i in range(memory_start, min(memory_start + 10, len(lines))):
                    logger.info(f"  {lines[i]}")
        
        return memory_section_found
        
    except Exception as e:
        logger.error(f"Marcus test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_marcus_memory())