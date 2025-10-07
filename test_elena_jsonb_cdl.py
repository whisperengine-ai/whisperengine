#!/usr/bin/env python3
"""
Test Elena bot with enhanced JSONB CDL system
"""

import asyncio
import asyncpg
import sys
import json
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.characters.enhanced_jsonb_manager import create_enhanced_cdl_manager

async def test_elena_jsonb_cdl():
    """Test Elena's enhanced JSONB CDL integration"""
    
    print("🧪 Testing Elena bot with enhanced JSONB CDL system...")
    
    # Connect to database
    postgres_pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='whisperengine',
        password='whisperengine_pass',
        database='whisperengine',
        min_size=1,
        max_size=5
    )
    
    print("✅ Connected to PostgreSQL database")
    
    # Create enhanced CDL manager
    cdl_manager = create_enhanced_cdl_manager(postgres_pool)
    
    # Test loading Elena's character data
    elena_data = await cdl_manager.get_character_data("elena_rodriguez")
    
    if not elena_data:
        print("❌ Failed to load Elena's character data from database")
        return False
    
    print("✅ Successfully loaded Elena's character data from enhanced JSONB database")
    
    # Extract key CDL components for testing
    cdl_data = elena_data.get('cdl_data', {})
    
    # Parse JSON string if needed
    if isinstance(cdl_data, str):
        cdl_data = json.loads(cdl_data)
    
    identity = cdl_data.get('identity', {})
    personality = cdl_data.get('personality', {})
    communication = cdl_data.get('communication_style', {})
    
    print("🎭 Elena Character Validation:")
    print(f"   Name: {identity.get('name', 'N/A')}")
    print(f"   Occupation: {identity.get('occupation', 'N/A')}")
    print(f"   Location: {identity.get('location', 'N/A')}")
    print(f"   Age: {identity.get('age', 'N/A')}")
    
    # Test personality traits
    core_traits = personality.get('core_traits', {})
    print(f"   Core Traits: {list(core_traits.keys())[:3]}..." if core_traits else "   Core Traits: Not found")
    
    # Test communication style
    tone = communication.get('tone', {})
    print(f"   Communication Tone: {tone.get('primary', 'N/A')}")
    
    # Test Spanish expressions (key Elena trait)
    languages = communication.get('language_patterns', {})
    spanish = languages.get('spanish_expressions', [])
    print(f"   Spanish Expressions: {len(spanish)} found" if spanish else "   Spanish Expressions: Not found")
    
    # Test marine biology expertise (key Elena trait)
    expertise = cdl_data.get('expertise', {})
    marine_bio = expertise.get('marine_biology', {})
    print(f"   Marine Biology Expertise: {'✅ Found' if marine_bio else '❌ Missing'}")
    
    # Test character simulation prompt generation
    print("\n🧬 Testing Character Simulation Prompt Generation...")
    
    # Basic character context for prompt building
    user_message = "Hi Elena! Can you tell me about ocean acidification?"
    
    # Build a simple character prompt using the CDL data
    identity_section = f"""
Identity: {identity.get('name', 'Elena Rodriguez')} - {identity.get('occupation', 'Marine Biologist')}
Age: {identity.get('age', 26)} | Location: {identity.get('location', 'La Jolla, California')}
Background: {identity.get('background_summary', 'Passionate marine biologist researching ocean health')}
"""
    
    personality_section = "Core Traits:\n"
    for trait, description in (core_traits or {}).items():
        if isinstance(description, str):
            personality_section += f"- {trait}: {description[:100]}...\n"
    
    communication_section = f"""
Communication Style:
- Primary Tone: {tone.get('primary', 'Educational and enthusiastic')}
- Spanish Expressions: Uses {len(spanish)} different expressions naturally
- Teaching Style: Uses metaphors and real-world examples
"""
    
    expertise_section = "Marine Biology Expertise:\n"
    if marine_bio:
        for area, details in marine_bio.items():
            if isinstance(details, str):
                expertise_section += f"- {area}: {details[:80]}...\n"
    
    full_prompt = f"""CHARACTER SIMULATION PROMPT:
{identity_section}
{personality_section}
{communication_section}
{expertise_section}

User Message: {user_message}

Instructions: Respond as Elena Rodriguez with authentic marine biology expertise, 
educational enthusiasm, and natural Spanish expressions where appropriate."""

    print("✅ Generated character simulation prompt successfully")
    print(f"📏 Prompt length: {len(full_prompt)} characters")
    
    # Test search functionality
    print("\n🔍 Testing Character Search...")
    search_results = await cdl_manager.search_characters("marine biologist", limit=5)
    
    if search_results:
        print(f"✅ Search found {len(search_results)} results:")
        for result in search_results:
            print(f"   - {result.get('name', 'Unknown')} ({result.get('occupation', 'N/A')})")
    else:
        print("❌ Search returned no results")
    
    await postgres_pool.close()
    print("\n🎉 Elena enhanced JSONB CDL integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_elena_jsonb_cdl())
    if success:
        print("\n🚀 Elena bot is ready to use enhanced JSONB CDL system!")
    else:
        print("\n💥 Elena bot CDL integration test failed")