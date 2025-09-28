#!/usr/bin/env python3
"""
Test CDL Standardization - Validate that all active CDL files work with our standardized location
"""

import json
import os
from pathlib import Path
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.characters.cdl.parser import load_character

def test_cdl_parsing_and_patterns():
    """Test CDL parsing and pattern detection for all active bot files."""
    print("🧪 Testing CDL Standardization")
    print("=" * 80)
    
    # All CDL files that should be tested (active and backup files)
    all_cdl_files = [
        'aethys.json', 'aethys-omnipotent-entity.json',
        'dream.json', 'dream_of_the_endless.json', 
        'elena.json', 'elena-rodriguez.json',
        'gabriel.json',
        'jake.json', 'jake-sterling.json',
        'marcus.json', 'marcus-thompson.json',
        'ryan.json', 'ryan-chen.json',
        'sophia.json', 'sophia-blake.json'
    ]
    
    cdl_integration = CDLAIPromptIntegration()
    results = {}
    
    for cdl_file in all_cdl_files:
        bot_name = cdl_file.replace('.json', '').replace('-', '_')
        print(f"\n📋 Testing {bot_name.title()}")
        print("-" * 40)
        
        # Set environment for this bot
        os.environ['DISCORD_BOT_NAME'] = bot_name
        
        try:
            # Test CDL file loading
            character = load_character(f'characters/examples/{cdl_file}')
            print(f"✅ CDL parsing: {character.identity.name}")
            
            # Test pattern detection with sample messages (character-specific)
            test_messages = []
            if 'gabriel' in cdl_file:
                test_messages = [
                    ("need spiritual guidance", ["spiritual", "guidance"]),
                    ("faith questions", ["spiritual", "guidance"]),
                    ("theological discussion", ["theological", "discussion"])
                ]
            else:
                test_messages = [
                    ("consciousness expansion", ["mystical", "transcendent", "spiritual"]),
                    ("had a dream", ["dream", "sleep", "vision"]),
                    ("beautiful eyes", ["romantic", "compliment", "attractive"]),
                    ("teach me", ["education", "learning", "academic"]),
                    ("marine biology", ["science", "environmental", "ocean"]),
                    ("code together", ["collaboration", "creative", "programming"]),
                    ("gaming discussion", ["game", "development", "technical"])
                ]
            
            patterns_found = []
            for message, _ in test_messages:
                scenarios = cdl_integration._detect_communication_scenarios(message, character, 'test_user')
                if scenarios:
                    patterns_found.extend(list(scenarios.keys()))
            
            # Check CDL structure for standardized locations
            with open(f'characters/examples/{cdl_file}', 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            communication = cdl_data.get('character', {}).get('communication', {})
            has_triggers = 'message_pattern_triggers' in communication
            has_guidance = 'conversation_flow_guidance' in communication
            
            # Check for old locations (should not exist)
            old_location = (cdl_data.get('character', {})
                          .get('personality', {})
                          .get('communication_style', {}))
            has_old_triggers = 'message_pattern_triggers' in old_location
            has_old_guidance = 'conversation_flow_guidance' in old_location
            
            results[bot_name] = {
                'parsing': True,
                'character_name': character.identity.name,
                'patterns_found': patterns_found,
                'has_triggers': has_triggers,
                'has_guidance': has_guidance,
                'has_old_triggers': has_old_triggers,
                'has_old_guidance': has_old_guidance
            }
            
            # Report results
            if patterns_found:
                print(f"✅ Pattern detection: {', '.join(set(patterns_found))}")
            else:
                print("⚠️  No patterns detected")
                
            if has_triggers and has_guidance:
                print("✅ Standardized location: message_pattern_triggers & conversation_flow_guidance in communication")
            else:
                print("❌ Missing standardized sections")
                
            if has_old_triggers or has_old_guidance:
                print("⚠️  WARNING: Old location still has patterns - needs cleanup")
            else:
                print("✅ Clean: No patterns in old location")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[bot_name] = {
                'parsing': False,
                'error': str(e)
            }
    
    # Summary report
    print(f"\n🎯 STANDARDIZATION TEST SUMMARY")
    print("=" * 80)
    
    successful_parsing = sum(1 for r in results.values() if r.get('parsing', False))
    total_bots = len(all_cdl_files)
    
    print(f"📊 CDL Parsing Success: {successful_parsing}/{total_bots} bots")
    
    standardized_bots = sum(1 for r in results.values() 
                           if r.get('has_triggers', False) and r.get('has_guidance', False))
    print(f"📊 Standardized Structure: {standardized_bots}/{successful_parsing} bots")
    
    old_location_bots = sum(1 for r in results.values() 
                          if r.get('has_old_triggers', False) or r.get('has_old_guidance', False))
    print(f"📊 Needs Cleanup: {old_location_bots} bots still have old location patterns")
    
    pattern_detection_bots = sum(1 for r in results.values() 
                               if r.get('patterns_found', []))
    print(f"📊 Pattern Detection: {pattern_detection_bots}/{successful_parsing} bots detecting patterns")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS")
    print("-" * 40)
    for bot_name, result in results.items():
        if result.get('parsing', False):
            status = "✅" if (result.get('has_triggers', False) and 
                           result.get('has_guidance', False) and
                           not result.get('has_old_triggers', False) and
                           not result.get('has_old_guidance', False)) else "⚠️"
            patterns = f"({len(set(result.get('patterns_found', [])))} patterns)" if result.get('patterns_found') else "(no patterns)"
            print(f"{status} {bot_name.title()}: {result.get('character_name', 'Unknown')} {patterns}")
        else:
            print(f"❌ {bot_name.title()}: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    test_results = test_cdl_parsing_and_patterns()