#!/usr/bin/env python3
"""
Debug script to test fact extraction with the same prompt as enrichment worker.
"""
import asyncio
import os
from src.llm.llm_protocol import create_llm_client

async def test_fact_extraction():
    # Sample conversation (like test data would have)
    conversation_text = """User: Hi Elena! My name is Mark and I love pizza!
Bot: Hi Mark! Pizza is great! What's your favorite kind?
User: I really enjoy pepperoni pizza. I also like sushi.
Bot: That's wonderful! Do you have any pets?
User: Yes, I have a dog named Max. I also went hiking last weekend.
Bot: Hiking sounds fun! Where did you go?"""

    prompt = f"""Analyze this conversation and extract ONLY clear, factual personal statements about the user.

Conversation:
{conversation_text}

Instructions:
- Extract personal preferences: Foods/drinks/hobbies they explicitly like/dislike/enjoy
- Extract personal facts: Pets they own, places they've visited, hobbies they actively do
- DO NOT extract: Conversational phrases, questions, abstract concepts, philosophical statements
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

Valid entity_types: food, drink, hobby, place, pet, skill, goal, occupation, other
Valid relationship_types: 
- Preferences: likes, dislikes, enjoys, loves, hates, prefers
- Possessions: owns, has, bought, sold, lost
- Actions: visited, traveled_to, went_to, does, practices, plays
- Aspirations: wants, needs, plans_to, hopes_to, dreams_of
- Experiences: tried, learned, studied, worked_at, lived_in
- Relationships: knows, friends_with, family_of, works_with

Be conservative - only extract clear, unambiguous facts."""

    # Create LLM client
    llm_client = create_llm_client(
        llm_client_type="openrouter",
        api_url=os.getenv('LLM_API_URL'),
        api_key=os.getenv('LLM_API_KEY')
    )
    
    # Call LLM
    print("=" * 80)
    print("PROMPT:")
    print("=" * 80)
    print(prompt)
    print("\n" + "=" * 80)
    print("CALLING LLM...")
    print("=" * 80)
    
    response = await asyncio.to_thread(
        llm_client.get_chat_response,
        [
            {
                "role": "system",
                "content": "You are a precise fact extraction specialist. Extract clear, verifiable personal facts. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=os.getenv('LLM_FACT_EXTRACTION_MODEL', 'anthropic/claude-3.5-sonnet'),
        temperature=0.2
    )
    
    print("\n" + "=" * 80)
    print("LLM RESPONSE:")
    print("=" * 80)
    print(response)
    print("\n" + "=" * 80)
    
    # Try to parse JSON
    import json
    try:
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        data = json.loads(response)
        facts = data.get('facts', [])
        
        print(f"EXTRACTED {len(facts)} FACTS:")
        print("=" * 80)
        for fact in facts:
            print(f"  - {fact.get('entity_name')} ({fact.get('entity_type')}): {fact.get('relationship_type')} (confidence: {fact.get('confidence')})")
            print(f"    Reasoning: {fact.get('reasoning', 'N/A')}")
        
    except json.JSONDecodeError as e:
        print(f"JSON PARSE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_fact_extraction())
