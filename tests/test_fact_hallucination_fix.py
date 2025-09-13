#!/usr/bin/env python3
"""
Test script to verify that the fact extraction fixes prevent hallucinated facts
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fact_extractor import FactExtractor
from lmstudio_client import LMStudioClient
from memory_manager import UserMemoryManager

def test_fact_extraction_fix():
    """Test that the problematic messages no longer generate hallucinated facts"""
    
    print("Testing fact extraction fixes...")
    print("=" * 50)
    
    # Create the LLM client (this will connect to LM Studio if running)
    try:
        llm_client = LMStudioClient()
        print("✓ LLM client created successfully")
    except Exception as e:
        print(f"✗ Could not create LLM client: {e}")
        print("Note: This test requires LM Studio to be running with the sentiment model")
        return
    
    # Create fact extractor
    fact_extractor = FactExtractor(llm_client)
    
    # Test the problematic messages that were generating hallucinated facts
    test_messages = [
        "testing...",
        "hmm. maybe?...", 
        "!list_facts",
        "ok",
        "hello",
        "what?",
    ]
    
    print("\nTesting problematic messages that previously generated hallucinated facts:")
    print("-" * 70)
    
    for message in test_messages:
        try:
            facts = fact_extractor.extract_facts_from_message(message)
            print(f"Message: '{message}' -> {len(facts)} facts extracted")
            
            if facts:
                print("  WARNING: Facts were extracted from this message!")
                for fact in facts:
                    print(f"    - {fact['fact']} (confidence: {fact['confidence']})")
            else:
                print("  ✓ No facts extracted (correct behavior)")
                
        except Exception as e:
            print(f"  ✗ Error extracting facts: {e}")
    
    print("\nTesting legitimate messages that should generate facts:")
    print("-" * 70)
    
    legitimate_messages = [
        "I play guitar every weekend",
        "I live in California", 
        "My name is John and I work as a teacher",
        "I love playing video games, especially RPGs",
    ]
    
    for message in legitimate_messages:
        try:
            facts = fact_extractor.extract_facts_from_message(message)
            print(f"Message: '{message}' -> {len(facts)} facts extracted")
            
            for fact in facts:
                print(f"    - {fact['fact']} (confidence: {fact['confidence']})")
                
        except Exception as e:
            print(f"  ✗ Error extracting facts: {e}")

if __name__ == "__main__":
    test_fact_extraction_fix()
