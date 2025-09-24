#!/usr/bin/env python3
"""
Integration Test: LLM-Powered CDL Self-Memory with CDL Prompt Integration

Quick test to verify the LLM-powered self-memory system integrates correctly
with the CDL prompt system.
"""

import asyncio
import logging
import sys
sys.path.append('.')

from src.llm.llm_protocol import create_llm_client
from src.memory.memory_protocol import create_memory_manager
from src.memory.llm_powered_bot_memory import create_llm_powered_bot_memory
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_llm_self_memory_integration():
    """Test LLM-powered self-memory integration with CDL prompts"""
    logger.info("🧪 Testing LLM-Powered Self-Memory Integration")
    
    try:
        # Initialize components
        llm_client = create_llm_client("openrouter")
        memory_manager = create_memory_manager("vector")
        
        # Create Elena's LLM-powered self-memory
        elena_memory = create_llm_powered_bot_memory("elena", llm_client, memory_manager)
        
        # First, extract some knowledge (this would normally be done once during setup)
        logger.info("📖 Extracting Elena's personal knowledge...")
        extraction_result = await elena_memory.extract_cdl_knowledge_with_llm("elena-rodriguez.json")
        
        if extraction_result.total_items > 0:
            logger.info(f"✅ Extracted {extraction_result.total_items} knowledge items")
            
            # Now test CDL prompt integration with self-knowledge
            logger.info("🎭 Testing CDL prompt integration with self-knowledge...")
            
            cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
            
            # Test with a personal question that should trigger self-knowledge
            test_message = "Do you have a boyfriend or girlfriend?"
            test_user_id = "test_user_123"
            
            prompt = await cdl_integration.create_character_aware_prompt(
                character_file="elena-rodriguez.json",
                user_id=test_user_id,
                message_content=test_message,
                user_name="TestUser"
            )
            
            # Check if self-knowledge was integrated
            if "PERSONAL KNOWLEDGE" in prompt:
                logger.info("✅ Self-knowledge successfully integrated into CDL prompt!")
                logger.info("🔍 Relevant sections found in prompt:")
                
                lines = prompt.split('\n')
                in_personal_knowledge = False
                knowledge_lines = []
                
                for line in lines:
                    if "PERSONAL KNOWLEDGE" in line:
                        in_personal_knowledge = True
                        knowledge_lines.append(line)
                    elif in_personal_knowledge and line.strip():
                        if line.startswith('- [') or line.startswith('RESPONSE GUIDANCE') or line.startswith('AUTHENTICITY TIPS'):
                            knowledge_lines.append(line)
                        elif not line.startswith(' ') and not line.startswith('-'):
                            break
                
                for line in knowledge_lines[:5]:  # Show first 5 lines
                    logger.info(f"   {line}")
                
                if len(knowledge_lines) > 5:
                    logger.info(f"   ... and {len(knowledge_lines) - 5} more lines")
                    
            else:
                logger.warning("⚠️ Self-knowledge not found in CDL prompt")
                
            # Test with a different question
            logger.info("\n🧪 Testing with research question...")
            research_prompt = await cdl_integration.create_character_aware_prompt(
                character_file="elena-rodriguez.json",
                user_id=test_user_id,
                message_content="Tell me about your research work",
                user_name="TestUser"  
            )
            
            if "PERSONAL KNOWLEDGE" in research_prompt:
                logger.info("✅ Research-related self-knowledge also integrated!")
            else:
                logger.info("ℹ️ No specific research knowledge found (may be normal)")
                
        else:
            logger.warning("⚠️ No knowledge extracted - integration test incomplete")
            
        logger.info("\n🎉 LLM-Powered Self-Memory Integration Test Complete!")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm_self_memory_integration())