#!/usr/bin/env python3
"""
Inspect the actual prompt structure with new hybrid approach.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

env_file = project_root / ".env.elena"
if env_file.exists():
    load_dotenv(env_file)

from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

TEST_USER_ID = "672814231002939413"
TEST_MESSAGE = "Elena, I'm struggling with my Acropora coral pH measurements. Should I focus on data analysis or collecting more samples first?"


async def main():
    print("\n" + "="*80)
    print("PROMPT STRUCTURE INSPECTION")
    print("="*80)
    
    memory_manager = create_memory_manager(memory_type="vector")
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    
    prompt = await cdl_integration.create_unified_character_prompt(
        user_id=TEST_USER_ID,
        message_content=TEST_MESSAGE
    )
    
    # Find and extract the semantic memories section
    if "🧠 RELEVANT PAST CONVERSATIONS:" in prompt:
        start_idx = prompt.find("🧠 RELEVANT PAST CONVERSATIONS:")
        
        # Find the end (next major section or double newline)
        next_sections = [
            prompt.find("\n\n🎬", start_idx),
            prompt.find("\n\n💭", start_idx),
            prompt.find("\n\n🌊", start_idx),
            prompt.find("\n\n📊", start_idx),
        ]
        end_idx = min([idx for idx in next_sections if idx > start_idx], default=len(prompt))
        
        semantic_section = prompt[start_idx:end_idx]
        
        print("\n✅ FOUND: Semantic Memory Section\n")
        print(semantic_section)
        print("\n" + "-"*80)
        
        # Count memories
        import re
        memory_pattern = r'^\d+\.'
        memories = [line for line in semantic_section.split('\n') if re.match(memory_pattern, line.strip())]
        print(f"\n📊 MEMORY COUNT: {len(memories)} extractive memories shown")
        print(f"   (Expected: 10 from limit=15 retrieval)")
        
    else:
        print("\n❌ SEMANTIC MEMORY SECTION NOT FOUND")
        print("\nSearching for other sections...")
        if "📚 CONVERSATION BACKGROUND:" in prompt:
            print("   ⚠️  Found old summary section (should be removed)")
        if "CONVERSATION HISTORY:" in prompt:
            print("   ✓ Found conversation history section")
    
    # Check total prompt size
    word_count = len(prompt.split())
    char_count = len(prompt)
    print(f"\n📏 PROMPT SIZE:")
    print(f"   Words: {word_count:,}")
    print(f"   Characters: {char_count:,}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
