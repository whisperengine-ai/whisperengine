"""
Manual Elena Knowledge Extraction

This script will extract Elena's personal knowledge and store it in the vector memory
so that the Discord commands can access it.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, '/app/src')

from src.memory.llm_powered_bot_memory import create_llm_powered_bot_memory
from src.llm.llm_protocol import create_llm_client
from src.memory.memory_protocol import create_memory_manager


async def manual_extract_elena_knowledge():
    """Manually extract Elena's knowledge for Discord commands"""
    
    print("🧠 Manual Elena Knowledge Extraction")
    print("=" * 50)
    
    try:
        # Create components
        memory_manager = create_memory_manager()
        llm_client = create_llm_client()
        bot_name = 'elena'
        
        # Create LLM-powered bot memory
        llm_bot_memory = create_llm_powered_bot_memory(bot_name, llm_client, memory_manager)
        print(f"✅ Created LLM-powered bot memory for {bot_name}")
        
        # Extract knowledge from Elena's character file
        character_file = 'characters/examples/elena-rodriguez.json'
        print(f"🔍 Extracting knowledge from: {character_file}")
        
        result = await llm_bot_memory.extract_cdl_knowledge_with_llm(character_file)
        
        print(f"✅ Extraction Results:")
        print(f"   📊 Total Items: {result.total_items}")
        print(f"   🎯 Confidence: {result.confidence_score:.2f}")
        print(f"   📂 Categories: {list(result.categories.keys())}")
        
        # Show some examples
        for category, items in result.categories.items():
            if items:
                print(f"\n🔸 {category.upper()}:")
                for i, item in enumerate(items[:2], 1):  # Show first 2 items
                    content = item.get('content', '')[:150]
                    confidence = item.get('confidence', 0.0)
                    print(f"   {i}. {content}... (confidence: {confidence:.2f})")
        
        # Test a few queries
        print(f"\n❓ Testing Personal Questions:")
        
        test_questions = [
            "Do you have a boyfriend?",
            "What is your research about?",
            "What's your daily routine?",
            "Where do you work?"
        ]
        
        for question in test_questions:
            try:
                query_result = await llm_bot_memory.query_personal_knowledge_with_llm(question, limit=2)
                
                if query_result.get('found_relevant_info'):
                    relevant_items = query_result.get('relevant_items', [])
                    print(f"   ✅ {question}")
                    print(f"      📊 Found {len(relevant_items)} relevant items")
                    
                    # Show response guidance
                    response_guidance = query_result.get('response_guidance', '')
                    if response_guidance:
                        print(f"      💡 Guidance: {response_guidance[:100]}...")
                else:
                    print(f"   ❌ {question} - No relevant knowledge found")
                    
            except Exception as e:
                print(f"   ❌ {question} - Error: {e}")
        
        print(f"\n🎉 Knowledge extraction complete!")
        print(f"🚀 Elena should now be able to answer personal questions in Discord!")
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(manual_extract_elena_knowledge())