#!/usr/bin/env python3
"""
Test Gabriel's system prompt to verify rich data integration
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

# Set environment for Gabriel
os.environ['DISCORD_BOT_NAME'] = 'gabriel'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'

from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client
import asyncpg

async def test_gabriel_prompt():
    """Test Gabriel's prompt generation with rich data"""
    
    print("🎭 Testing Gabriel Prompt Generation with Rich Data")
    print("=" * 80)
    
    # Create PostgreSQL pool
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='whisperengine',
        password='whisperengine_pass',
        database='whisperengine',
        min_size=1,
        max_size=10
    )
    
    # Create memory manager and LLM client
    memory_manager = create_memory_manager(memory_type="vector")
    llm_client = create_llm_client(llm_client_type="openrouter")
    
    # Create CDL integration with enhanced manager
    from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
    enhanced_manager = create_enhanced_cdl_manager(pool)
    
    cdl_integration = CDLAIPromptIntegration(
        memory_manager=memory_manager,
        llm_client=llm_client,
        postgres_pool=pool,
        enhanced_manager=enhanced_manager
    )
    
    # Test with a message from Cynthia to trigger relationship context
    print("\n📝 Generating system prompt for test message from Cynthia...")
    prompt = await cdl_integration.create_unified_character_prompt(
        user_id="test_user_cynthia",
        message_content="Hello Gabriel, how are you?",
        user_name="Cynthia",
        character_file="gabriel"
    )
    
    print("\n" + "=" * 80)
    print("📜 GENERATED SYSTEM PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Check for key rich data markers
    print("\n🔍 VALIDATION CHECKS:")
    checks = {
        "Contains 'Cynthia'": "Cynthia" in prompt or "cynthia" in prompt.lower(),
        "Contains 'RELATIONSHIP CONTEXT'": "RELATIONSHIP CONTEXT" in prompt or "💕" in prompt,
        "Contains 'BEHAVIORAL TRIGGERS'": "BEHAVIORAL TRIGGERS" in prompt or "⚡" in prompt,
        "Contains 'SPEECH PATTERNS'": "SPEECH PATTERNS" in prompt or "💬" in prompt,
        "Contains 'CONVERSATION FLOW'": "CONVERSATION FLOW" in prompt or "🗣️" in prompt,
        "Contains 'devoted'": "devoted" in prompt.lower(),
        "Contains 'signature expressions'": "signature" in prompt.lower(),
    }
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(checks.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 SUCCESS: All rich data integration checks passed!")
        print("Gabriel's system prompt now includes Cynthia relationship context!")
    else:
        print("⚠️  WARNING: Some rich data elements missing from prompt")
        print("Check the prompt above for missing sections")
    print("=" * 80)
    
    await pool.close()
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_gabriel_prompt())
    sys.exit(0 if success else 1)
