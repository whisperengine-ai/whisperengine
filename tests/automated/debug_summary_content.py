#!/usr/bin/env python3
"""
Debug script to inspect actual summary content being generated.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager


async def inspect_summary():
    """Check what the summary function actually returns."""
    print("\n" + "="*80)
    print("🔍 DEBUGGING CONVERSATION SUMMARY CONTENT")
    print("="*80 + "\n")
    
    test_user_id = "test_summary_user_001"
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Get conversation history
    print("1️⃣ Retrieving conversation history...")
    history = await memory_manager.get_conversation_history(
        user_id=test_user_id,
        limit=20
    )
    print(f"   ✅ Retrieved {len(history)} messages\n")
    
    # Generate summary
    print("2️⃣ Generating conversation summary...")
    summary_result = await memory_manager.get_conversation_summary_with_recommendations(
        user_id=test_user_id,
        conversation_history=history,
        limit=5  # Request 5 summary sentences
    )
    
    print(f"   ✅ Summary generated\n")
    
    # Display full summary result
    print("="*80)
    print("📊 FULL SUMMARY RESULT")
    print("="*80 + "\n")
    
    print("Keys in result:")
    for key in summary_result.keys():
        print(f"  • {key}")
    print()
    
    # Display topic_summary field
    topic_summary = summary_result.get('topic_summary', '')
    print("📝 topic_summary field:")
    print("-" * 80)
    print(topic_summary)
    print("-" * 80)
    print(f"Length: {len(topic_summary)} characters\n")
    
    # Display conversation_themes
    themes = summary_result.get('conversation_themes', [])
    print(f"🎯 conversation_themes: {themes}\n")
    
    # Display method
    method = summary_result.get('method', 'unknown')
    print(f"🔧 method: {method}\n")
    
    # Display other fields
    print("📦 Other fields:")
    for key, value in summary_result.items():
        if key not in ['topic_summary', 'conversation_themes', 'method']:
            print(f"  • {key}: {value}")
    
    print()
    
    # Analyze why it might be short
    print("="*80)
    print("🔍 ANALYSIS: WHY IS SUMMARY SHORT?")
    print("="*80 + "\n")
    
    sentences = topic_summary.split('. ')
    print(f"Number of sentences: {len(sentences)}")
    print(f"Requested sentences: 5")
    print()
    
    if len(sentences) < 5:
        print("⚠️  Summary has fewer sentences than requested!")
        print("\nPossible causes:")
        print("  1. Not enough conversation turns to extract from")
        print("  2. Centrality scoring only found 1-2 highly representative sentences")
        print("  3. Extractive method is too selective")
        print("  4. Content similarity made other sentences redundant")
        print()
    
    print("Individual sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"  {i}. {sentence.strip()}")
        print(f"     Length: {len(sentence.strip())} chars")
        print()


async def main():
    try:
        await inspect_summary()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
