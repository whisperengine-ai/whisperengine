#!/usr/bin/env python3
"""
Test conversation summary VALUE PROPOSITION with real Discord messages.

This test sends a follow-up message that REQUIRES past context to answer well.
We compare Elena's response WITH summary vs WITHOUT summary to see if it actually helps.

Test Scenario:
1. Send message referencing past conversation (that Elena should remember)
2. Generate response WITH summary in prompt
3. Generate response WITHOUT summary in prompt  
4. Compare quality: Does Elena reference past topics? Is response more personalized?

Expected Outcome:
- WITH summary: Elena naturally references past research topics, personalized response
- WITHOUT summary: Generic response, no context awareness

This validates if summaries are worth the complexity.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load Elena's environment configuration (OpenRouter API keys, etc.)
env_file = project_root / ".env.elena"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment from {env_file}")

from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.llm.llm_protocol import create_llm_client

# Test user (your Discord ID)
TEST_USER_ID = "672814231002939413"
CHARACTER_NAME = "elena"

# Test message that REQUIRES past context to answer well
# This message is intentionally vague to see if summary provides needed context
TEST_MESSAGE = "Hey Elena, I'm still worried about my research. What should I prioritize to finish on time?"


async def main():
    """Test if conversation summaries actually improve response quality."""
    
    print("\n" + "="*80)
    print("CONVERSATION SUMMARY VALUE VALIDATION TEST")
    print("="*80)
    print(f"\nTest User: {TEST_USER_ID}")
    print(f"Character: {CHARACTER_NAME}")
    print(f"Test Message: \"{TEST_MESSAGE}\"")
    print("\nThis message REQUIRES past context to give a good answer.")
    print("We'll compare Elena's response WITH vs WITHOUT summary.\n")
    
    # Initialize components
    print("🔧 Initializing components...")
    memory_manager = create_memory_manager(memory_type="vector")
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    llm_client = create_llm_client(llm_client_type="openrouter")
    
    # Check if user has conversation history
    print(f"\n📚 Checking conversation history for user {TEST_USER_ID}...")
    memories = await memory_manager.retrieve_relevant_memories(
        user_id=TEST_USER_ID,
        query=TEST_MESSAGE,
        limit=20
    )
    
    if not memories:
        print(f"❌ No conversation history found for user {TEST_USER_ID}")
        print("   You need existing conversations with Elena to test this feature.")
        print("   Please send some Discord messages to Elena first, then run this test.")
        return
    
    print(f"✅ Found {len(memories)} relevant memories")
    print("\nRecent conversation topics:")
    for i, mem in enumerate(memories[:5], 1):
        content = mem.get('content', '')[:80]
        semantic_key = mem.get('semantic_key', 'unknown')
        print(f"   {i}. [{semantic_key}] {content}...")
    
    # Test 1: Generate response WITH summary
    print("\n" + "-"*80)
    print("TEST 1: Response WITH Conversation Summary")
    print("-"*80)
    
    system_prompt_with_summary = await cdl_integration.create_unified_character_prompt(
        user_id=TEST_USER_ID,
        message_content=TEST_MESSAGE
    )
    
    # Check if summary is actually in prompt
    has_summary = "📚 CONVERSATION BACKGROUND:" in system_prompt_with_summary
    print(f"\n✓ Summary in prompt: {'YES' if has_summary else 'NO'}")
    
    if has_summary:
        # Extract summary section
        summary_start = system_prompt_with_summary.find("📚 CONVERSATION BACKGROUND:")
        summary_end = system_prompt_with_summary.find("\n\n", summary_start)
        summary_section = system_prompt_with_summary[summary_start:summary_end]
        print(f"\nSummary content:\n{summary_section}\n")
    
    # Generate response
    print("🤖 Generating Elena's response WITH summary...")
    messages_with = [
        {"role": "system", "content": system_prompt_with_summary},
        {"role": "user", "content": TEST_MESSAGE}
    ]
    
    response_with = await llm_client.generate_chat_completion_safe(
        messages=messages_with,
        max_tokens=500,
        temperature=0.7
    )
    
    print("\n📝 Elena's response WITH summary:")
    print("-" * 60)
    print(response_with)
    print("-" * 60)
    
    # Test 2: Generate response WITHOUT summary (minimal character context)
    print("\n" + "-"*80)
    print("TEST 2: Response WITHOUT Conversation Summary (CONTROL)")
    print("-"*80)
    
    # Build minimal prompt with NO conversation history or summary
    system_prompt_without_summary = """You are Elena Rodriguez, a Marine Biologist & Research Scientist.

PERSONALITY: Elena is passionate about ocean conservation and loves sharing her knowledge with enthusiasm. She's an engaging educator who makes complex marine science accessible.

BACKGROUND: As a marine biologist, Elena conducts research on coral reefs and ocean ecosystems. She's dedicated to understanding and protecting marine life.

Respond naturally as this character. Be authentic and engaging."""
    
    print("\n✓ Using minimal prompt with NO conversation history or summary")
    
    # Generate response
    print("🤖 Generating Elena's response WITHOUT summary...")
    messages_without = [
        {"role": "system", "content": system_prompt_without_summary},
        {"role": "user", "content": TEST_MESSAGE}
    ]
    
    response_without = await llm_client.generate_chat_completion_safe(
        messages=messages_without,
        max_tokens=500,
        temperature=0.7
    )
    
    print("\n📝 Elena's response WITHOUT summary:")
    print("-" * 60)
    print(response_without)
    print("-" * 60)
    
    # Analysis
    print("\n" + "="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)
    
    # Check for context references
    memories_topics = set()
    for mem in memories[:10]:
        semantic_key = mem.get('semantic_key', '')
        if semantic_key and semantic_key != 'unknown':
            memories_topics.add(semantic_key)
    
    print(f"\nConversation Topics from History: {', '.join(memories_topics) if memories_topics else 'None detected'}")
    
    # Analyze WITH summary response
    print(f"\n📊 Response WITH Summary Analysis:")
    with_metrics = {
        'length': len(response_with),
        'references_topics': any(topic.replace('_', ' ') in response_with.lower() for topic in memories_topics),
        'mentions_past': any(word in response_with.lower() for word in ['previous', 'earlier', 'discussed', 'mentioned', 'talked about', 'research', 'studying']),
        'personalized': any(word in response_with.lower() for word in ['your', 'you were', "you've", 'you mentioned'])
    }
    
    print(f"   • Length: {with_metrics['length']} chars")
    print(f"   • References past topics: {'YES ✓' if with_metrics['references_topics'] else 'NO ✗'}")
    print(f"   • Mentions past discussion: {'YES ✓' if with_metrics['mentions_past'] else 'NO ✗'}")
    print(f"   • Personalized response: {'YES ✓' if with_metrics['personalized'] else 'NO ✗'}")
    
    # Analyze WITHOUT summary response
    print(f"\n📊 Response WITHOUT Summary Analysis:")
    without_metrics = {
        'length': len(response_without),
        'references_topics': any(topic.replace('_', ' ') in response_without.lower() for topic in memories_topics),
        'mentions_past': any(word in response_without.lower() for word in ['previous', 'earlier', 'discussed', 'mentioned', 'talked about', 'research', 'studying']),
        'personalized': any(word in response_without.lower() for word in ['your', 'you were', "you've", 'you mentioned'])
    }
    
    print(f"   • Length: {without_metrics['length']} chars")
    print(f"   • References past topics: {'YES ✓' if without_metrics['references_topics'] else 'NO ✗'}")
    print(f"   • Mentions past discussion: {'YES ✓' if without_metrics['mentions_past'] else 'NO ✗'}")
    print(f"   • Personalized response: {'YES ✓' if without_metrics['personalized'] else 'NO ✗'}")
    
    # Calculate improvement score
    with_score = sum([with_metrics['references_topics'], with_metrics['mentions_past'], with_metrics['personalized']])
    without_score = sum([without_metrics['references_topics'], without_metrics['mentions_past'], without_metrics['personalized']])
    
    print(f"\n🎯 QUALITY SCORE:")
    print(f"   WITH summary:    {with_score}/3 metrics passed")
    print(f"   WITHOUT summary: {without_score}/3 metrics passed")
    
    improvement = with_score - without_score
    
    print(f"\n{'='*80}")
    if improvement > 0:
        print(f"✅ SUMMARY ADDS VALUE: +{improvement} quality metrics improved")
        print("   Summary helps Elena reference past conversation context.")
        print("   Recommendation: KEEP conversation summary feature")
    elif improvement < 0:
        print(f"❌ SUMMARY HURTS QUALITY: {improvement} quality metrics degraded")
        print("   Summary may be confusing Elena or adding noise.")
        print("   Recommendation: DISABLE conversation summary feature")
    else:
        print(f"⚠️  NO SIGNIFICANT DIFFERENCE: Both responses similar quality")
        print("   Summary doesn't help or hurt response quality.")
        print("   Recommendation: Consider DISABLING (added complexity without benefit)")
    
    print(f"{'='*80}\n")
    
    # User evaluation prompt
    print("👤 HUMAN EVALUATION:")
    print("   Please read both responses above and answer:")
    print("   1. Which response is more helpful and personalized?")
    print("   2. Does the WITH summary response reference your actual past conversations?")
    print("   3. Is the difference worth the added complexity of summaries?")
    print("\n   Your subjective evaluation matters more than automated metrics!")


if __name__ == "__main__":
    asyncio.run(main())
