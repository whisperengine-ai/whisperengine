#!/usr/bin/env python3
"""
FOCUSED test: Does summary help with SPECIFIC research question?

This test uses an explicit ocean acidification question to ensure
we retrieve the seeded conversation data and see if summary adds value.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load Elena's environment
env_file = project_root / ".env.elena"
if env_file.exists():
    load_dotenv(env_file)

from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.llm.llm_protocol import create_llm_client

TEST_USER_ID = "672814231002939413"

# SPECIFIC question that should retrieve ocean acidification memories
TEST_MESSAGE = "Elena, I'm struggling with my Acropora coral pH measurements. Should I focus on data analysis or collecting more samples first?"


async def main():
    print("\n" + "="*80)
    print("FOCUSED OCEAN ACIDIFICATION RESEARCH TEST")
    print("="*80)
    print(f"\nTest: Does summary help with SPECIFIC research context?")
    print(f"Message: \"{TEST_MESSAGE}\"\n")
    
    # Initialize
    memory_manager = create_memory_manager(memory_type="vector")
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    llm_client = create_llm_client(llm_client_type="openrouter")
    
    # Check retrieved memories
    print("📚 Checking memory retrieval...")
    memories = await memory_manager.retrieve_relevant_memories(
        user_id=TEST_USER_ID,
        query=TEST_MESSAGE,
        limit=10
    )
    
    print(f"✅ Retrieved {len(memories)} memories\n")
    print("Top 5 memories:")
    for i, mem in enumerate(memories[:5], 1):
        content = mem.get('content', '')[:80]
        semantic_key = mem.get('semantic_key', 'unknown')
        print(f"   {i}. [{semantic_key}] {content}...")
    
    # Test WITH summary
    print("\n" + "-"*80)
    print("TEST: Response WITH Conversation Summary")
    print("-"*80)
    
    prompt_with = await cdl_integration.create_unified_character_prompt(
        user_id=TEST_USER_ID,
        message_content=TEST_MESSAGE
    )
    
    # Extract summary section
    if "📚 CONVERSATION BACKGROUND:" in prompt_with:
        summary_start = prompt_with.find("📚 CONVERSATION BACKGROUND:")
        summary_end = prompt_with.find("\n\n", summary_start)
        summary_text = prompt_with[summary_start:summary_end]
        print(f"\nSummary text:\n{summary_text}\n")
    else:
        print("\n⚠️  No summary found in prompt\n")
    
    response_with = await llm_client.generate_chat_completion_safe(
        messages=[
            {"role": "system", "content": prompt_with},
            {"role": "user", "content": TEST_MESSAGE}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    print("📝 Elena's response WITH summary:")
    print("-" * 70)
    print(response_with)
    print("-" * 70)
    
    # Test WITHOUT summary (minimal prompt)
    print("\n" + "-"*80)
    print("TEST: Response WITHOUT Conversation Summary (CONTROL)")
    print("-"*80)
    
    prompt_without = """You are Elena Rodriguez, a Marine Biologist & Research Scientist.

PERSONALITY: Elena is passionate about ocean conservation and loves sharing her knowledge with enthusiasm.

Respond naturally as this character."""
    
    response_without = await llm_client.generate_chat_completion_safe(
        messages=[
            {"role": "system", "content": prompt_without},
            {"role": "user", "content": TEST_MESSAGE}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    print("📝 Elena's response WITHOUT summary:")
    print("-" * 70)
    print(response_without)
    print("-" * 70)
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS: Does summary provide research context value?")
    print("="*80)
    
    # Check for specific research references
    research_terms = ['ocean acidification', 'pH', 'Acropora', 'coral', 'thesis', 
                      'data analysis', 'samples', 'Indo-Pacific', 'calcium carbonate']
    
    with_refs = sum(1 for term in research_terms if term.lower() in response_with.lower())
    without_refs = sum(1 for term in research_terms if term.lower() in response_without.lower())
    
    print(f"\nResearch-specific terms mentioned:")
    print(f"   WITH summary:    {with_refs}/{len(research_terms)} terms")
    print(f"   WITHOUT summary: {without_refs}/{len(research_terms)} terms")
    
    # Check for thesis/deadline awareness
    context_terms = ['thesis', 'deadline', 'timeline', 'advisor', 'preliminary']
    with_context = sum(1 for term in context_terms if term.lower() in response_with.lower())
    without_context = sum(1 for term in context_terms if term.lower() in response_without.lower())
    
    print(f"\nThesis context awareness:")
    print(f"   WITH summary:    {with_context}/{len(context_terms)} terms")
    print(f"   WITHOUT summary: {without_context}/{len(context_terms)} terms")
    
    print(f"\n{'='*80}")
    if with_refs > without_refs or with_context > without_context:
        print(f"✅ SUMMARY ADDS VALUE: More specific research context")
        print(f"   Summary helped Elena reference actual research details.")
    elif with_refs < without_refs or with_context < without_context:
        print(f"❌ SUMMARY HURTS: Control response more specific")
        print(f"   Summary may be adding noise or confusing context.")
    else:
        print(f"⚠️  NO DIFFERENCE: Both responses equally specific")
        print(f"   Summary not providing measurable value.")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
