#!/usr/bin/env python3
"""
Test LLM Fact Extraction Quality
Tests current extraction on sample messages to demonstrate quality issues.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Load Elena's configuration (which has proper LLM settings)
load_dotenv('.env.elena')

# Override only the local database connections for testing
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['POSTGRES_HOST'] = 'localhost'  
os.environ['POSTGRES_PORT'] = '5433'

# Ensure we have proper LLM configuration
required_env_vars = [
    'LLM_CLIENT_TYPE', 'LLM_CHAT_API_URL', 'LLM_CHAT_API_KEY', 
    'LLM_CHAT_MODEL', 'LLM_FACT_EXTRACTION_MODEL'
]

print("🔧 Environment Configuration Check:")
for var in required_env_vars:
    value = os.environ.get(var, 'NOT SET')
    # Mask API key for security
    if 'API_KEY' in var and value != 'NOT SET':
        value = value[:10] + "..." + value[-10:]
    print(f"  {var}: {value}")

from src.llm.llm_client import LLMClient
from src.llm.llm_protocol import create_llm_client

def test_current_extraction():
    """Test current LLM fact extraction on sample messages."""
    
    # Create LLM client
    llm_client = create_llm_client()
    
    # Check if we got a working client
    if hasattr(llm_client, '__class__') and llm_client.__class__.__name__ == 'NoOpLLMClient':
        print("❌ ERROR: Got NoOpLLMClient - LLM configuration is not working!")
        print("This usually means missing environment variables or client initialization failed.")
        return
    
    print(f"✅ LLM Client initialized: {type(llm_client).__name__}")
    
    # Test messages that demonstrate different quality issues
    test_messages = [
        # Good extraction examples
        "I love pizza and I have a cat named Max",
        "I enjoy hiking on weekends",
        "I work in software development",
        
        # Problematic examples that likely cause fragments
        "Yeah when you get that feeling, it's just amazing how the door we've ever seen",
        "The process if it works, that doesn't wait for anything special",
        "I think that we often overlook the feedback loops - hmmm that's interesting",
        
        # Compound entities
        "I like pizza and sushi, they're both delicious",
        "My hobbies include reading and coding",
        
        # Abstract/conversational (should extract nothing)
        "What do you think about consciousness?",
        "That's an interesting philosophical question",
        "How are you doing today?"
    ]
    
    print("🧪 TESTING CURRENT LLM FACT EXTRACTION")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i} ---")
        print(f"Message: \"{message}\"")
        
        # Build extraction prompt (matching current implementation)
        extraction_prompt = f"""Analyze this user message and extract ONLY clear, factual personal statements about the user.

User message: "{message}"

Instructions:
- Extract personal preferences: Foods/drinks/hobbies they explicitly like/dislike/enjoy
- Extract personal facts: Pets they own, places they've visited, hobbies they actively do
- DO NOT extract: Conversational phrases, questions, abstract concepts, philosophical statements, compliments
- DO NOT extract: Things the user asks about or discusses theoretically - only facts about themselves

Return JSON (return empty list if no clear facts found):
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food", 
            "relationship_type": "likes",
            "confidence": 0.9,
            "reasoning": "User explicitly stated they love pizza"
        }}
    ]
}}

Valid entity_types: food, drink, hobby, place, pet, other
Valid relationship_types: likes, dislikes, enjoys, owns, visited, wants

Be conservative - only extract clear, unambiguous facts."""

        try:
            # Call LLM (matching message processor implementation)
            extraction_context = [
                {
                    "role": "system", 
                    "content": "You are a precise fact extraction specialist. Only extract clear, verifiable personal facts. Return valid JSON only."
                },
                {
                    "role": "user", 
                    "content": extraction_prompt
                }
            ]
            
            response = llm_client.get_chat_response(
                extraction_context,
                temperature=0.2
            )
            
            # Parse response (matching message processor logic)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            facts_data = json.loads(response)
            facts = facts_data.get("facts", [])
            
            if not facts:
                print("✅ No facts extracted (good for conversational messages)")
            else:
                print("📋 Extracted facts:")
                for fact in facts:
                    entity = fact.get('entity_name', 'N/A')
                    entity_type = fact.get('entity_type', 'N/A')
                    relationship = fact.get('relationship_type', 'N/A')
                    confidence = fact.get('confidence', 0)
                    reasoning = fact.get('reasoning', 'N/A')
                    
                    # Quality assessment
                    quality = "🟢"  # Good
                    issues = []
                    
                    # Check for fragment indicators
                    fragment_words = ['and ', 'or ', 'when ', 'if ', 'that ', 'the ', 'at ', 'door ', 'process ']
                    if any(word in entity.lower() for word in fragment_words):
                        quality = "🔴"
                        issues.append("fragment")
                    
                    # Check for pronouns
                    pronouns = ['i', 'you', 'me', 'we', 'they', 'it', 'this', 'that']
                    if entity.lower() in pronouns:
                        quality = "🔴"
                        issues.append("pronoun")
                    
                    # Check for compound entities
                    if ' and ' in entity.lower():
                        quality = "🟡"
                        issues.append("compound")
                    
                    # Check length
                    if len(entity) <= 2 or len(entity) > 30:
                        quality = "🟡"
                        issues.append("length")
                    
                    issue_str = f" [{', '.join(issues)}]" if issues else ""
                    print(f"  {quality} '{entity}' ({entity_type}) - {relationship} (conf: {confidence:.2f}){issue_str}")
                    print(f"     Reasoning: {reasoning}")
                    
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Raw response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Extraction error: {e}")

if __name__ == "__main__":
    test_current_extraction()