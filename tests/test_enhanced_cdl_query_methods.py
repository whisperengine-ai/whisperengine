#!/usr/bin/env python3
"""
Test Enhanced CDL Manager Query Methods
Validates all 8 new/updated query methods with Elena's data
"""

import os
import sys
import asyncio
import asyncpg

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5433')),
    'user': os.getenv('POSTGRES_USER', 'whisperengine'),
    'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_dev'),
    'database': os.getenv('POSTGRES_DB', 'whisperengine')
}

async def test_query_methods():
    """Test all enhanced CDL manager query methods"""
    
    print("=" * 80)
    print("Enhanced CDL Manager - Query Methods Test")
    print("Testing with: Elena Rodriguez")
    print("=" * 80)
    
    # Create connection pool
    pool = await asyncpg.create_pool(**DB_CONFIG)
    manager = EnhancedCDLManager(pool)
    
    character_name = 'elena'
    
    try:
        # Test 1: Response Guidelines
        print("\n1. Testing get_response_guidelines()...")
        guidelines = await manager.get_response_guidelines(character_name)
        print(f"   ✅ Retrieved {len(guidelines)} response guidelines")
        if guidelines:
            print(f"   Example: {guidelines[0].guideline_type} - {guidelines[0].guideline_name[:50]}...")
        
        # Test 2: Conversation Flows
        print("\n2. Testing get_conversation_flows()...")
        flows = await manager.get_conversation_flows(character_name)
        print(f"   ✅ Retrieved {len(flows)} conversation flows")
        if flows:
            print(f"   Example: {flows[0].flow_type} - {flows[0].flow_name}")
        
        # Test 3: Message Triggers
        print("\n3. Testing get_message_triggers()...")
        triggers = await manager.get_message_triggers(character_name)
        print(f"   ✅ Retrieved {len(triggers)} message triggers")
        if triggers:
            print(f"   Example: {triggers[0].trigger_category} / {triggers[0].trigger_type}: {triggers[0].trigger_value}")
        
        # Test 4: Emoji Patterns (NEW)
        print("\n4. Testing get_emoji_patterns() [NEW]...")
        emojis = await manager.get_emoji_patterns(character_name)
        print(f"   ✅ Retrieved {len(emojis)} emoji patterns")
        if emojis:
            print(f"   Example: {emojis[0].pattern_category} - {emojis[0].pattern_name}")
        
        # Test 5: AI Scenarios (NEW)
        print("\n5. Testing get_ai_scenarios() [NEW]...")
        scenarios = await manager.get_ai_scenarios(character_name)
        print(f"   ✅ Retrieved {len(scenarios)} AI scenarios")
        if scenarios:
            print(f"   Example: {scenarios[0].scenario_type} - {scenarios[0].scenario_name}")
        
        # Test 6: Cultural Expressions (NEW)
        print("\n6. Testing get_cultural_expressions() [NEW]...")
        expressions = await manager.get_cultural_expressions(character_name)
        print(f"   ✅ Retrieved {len(expressions)} cultural expressions")
        if expressions:
            print(f"   Example: {expressions[0].expression_type}: {expressions[0].expression_value[:40]}...")
        
        # Test 7: Voice Traits (NEW)
        print("\n7. Testing get_voice_traits() [NEW]...")
        voice = await manager.get_voice_traits(character_name)
        print(f"   ✅ Retrieved {len(voice)} voice traits")
        if voice:
            print(f"   Example: {voice[0].trait_type}: {voice[0].trait_value}")
        
        # Test 8: Emotional Triggers (NEW)
        print("\n8. Testing get_emotional_triggers() [NEW]...")
        emotional = await manager.get_emotional_triggers(character_name)
        print(f"   ✅ Retrieved {len(emotional)} emotional triggers")
        if emotional:
            print(f"   Example: {emotional[0].trigger_type} - {emotional[0].trigger_content[:40]}...")
        
        # Test 9: Expertise Domains (NEW)
        print("\n9. Testing get_expertise_domains() [NEW]...")
        domains = await manager.get_expertise_domains(character_name)
        print(f"   ✅ Retrieved {len(domains)} expertise domains")
        if domains:
            print(f"   Example: {domains[0].domain_name} (Level: {domains[0].expertise_level})")
        
        # Summary
        print("\n" + "=" * 80)
        print("Test Summary:")
        print("=" * 80)
        print(f"  Response Guidelines:    {len(guidelines):3d} records")
        print(f"  Conversation Flows:     {len(flows):3d} records")
        print(f"  Message Triggers:       {len(triggers):3d} records")
        print(f"  Emoji Patterns:         {len(emojis):3d} records [NEW]")
        print(f"  AI Scenarios:           {len(scenarios):3d} records [NEW]")
        print(f"  Cultural Expressions:   {len(expressions):3d} records [NEW]")
        print(f"  Voice Traits:           {len(voice):3d} records [NEW]")
        print(f"  Emotional Triggers:     {len(emotional):3d} records [NEW]")
        print(f"  Expertise Domains:      {len(domains):3d} records [NEW]")
        print("=" * 80)
        
        total_records = (len(guidelines) + len(flows) + len(triggers) + len(emojis) + 
                        len(scenarios) + len(expressions) + len(voice) + len(emotional) + len(domains))
        print(f"\n✅ All 9 query methods working! Total: {total_records} records retrieved")
        
        # Detailed output for one example
        if guidelines:
            print("\n" + "=" * 80)
            print("Detailed Example - First Response Guideline:")
            print("=" * 80)
            guideline = guidelines[0]
            print(f"  Type:        {guideline.guideline_type}")
            print(f"  Name:        {guideline.guideline_name}")
            print(f"  Content:     {guideline.guideline_content[:100]}...")
            print(f"  Priority:    {guideline.priority}")
            print(f"  Context:     {guideline.context}")
            print(f"  Is Critical: {guideline.is_critical}")
        
    finally:
        await pool.close()
        print("\n🔌 Database connection closed")

if __name__ == '__main__':
    asyncio.run(test_query_methods())
