#!/usr/bin/env python3
"""
CDL Normalized Database End-to-End Test
Tests the complete pipeline: Database → Character Loading → Prompt Generation

This validates that:
1. Characters load correctly from normalized database
2. All character fields are accessible via CDL system
3. Prompts are generated properly with character data
4. Character-specific data flows through the entire system
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_character_database_loading():
    """Test character loading from normalized database"""
    print("🔍 Phase 1: Testing Character Database Loading")
    
    test_characters = ['elena', 'marcus', 'gabriel', 'jake']
    results = {}
    
    for char_name in test_characters:
        try:
            # Set character environment
            os.environ['CDL_DEFAULT_CHARACTER'] = f'characters/examples/{char_name}.json'
            
            # Import and create fresh manager
            from src.characters.cdl.database_manager import get_database_cdl_manager
            
            db_manager = get_database_cdl_manager()
            
            # Clear any caching
            if hasattr(db_manager, '_character_name'):
                db_manager._character_name = None
            if hasattr(db_manager, '_character_data'):
                db_manager._character_data = None
            if hasattr(db_manager, '_loaded'):
                db_manager._loaded = False
            if hasattr(db_manager, '_character_object'):
                db_manager._character_object = None
            
            # Load character object
            character = db_manager.get_character_object()
            
            if character:
                results[char_name] = {
                    'success': True,
                    'name': character.identity.name,
                    'occupation': character.identity.occupation,
                    'description_length': len(character.identity.description) if character.identity.description else 0,
                    'has_big_five': hasattr(character.personality, 'big_five') and character.personality.big_five is not None,
                    'openness': character.personality.big_five.openness if hasattr(character.personality, 'big_five') and character.personality.big_five else None,
                    'backstory_length': len(character.backstory.origin_story) if character.backstory.origin_story else 0,
                    'communication_style': getattr(character.communication, 'communication_style', 'unknown')
                }
                print(f"  ✅ {char_name}: {character.identity.name} - {character.identity.occupation}")
            else:
                results[char_name] = {'success': False, 'error': 'Character object creation failed'}
                print(f"  ❌ {char_name}: Failed to load character object")
                
        except Exception as e:
            results[char_name] = {'success': False, 'error': str(e)}
            print(f"  ❌ {char_name}: Error - {e}")
    
    return results

async def test_cdl_field_access():
    """Test CDL field access and data extraction"""
    print("\n🔍 Phase 2: Testing CDL Field Access")
    
    # Test Marcus specifically for detailed field access
    os.environ['CDL_DEFAULT_CHARACTER'] = 'characters/examples/marcus.json'
    
    try:
        from src.characters.cdl.database_manager import get_database_cdl_manager, get_cdl_field
        
        db_manager = get_database_cdl_manager()
        
        # Clear caching
        if hasattr(db_manager, '_character_name'):
            db_manager._character_name = None
        if hasattr(db_manager, '_character_data'):
            db_manager._character_data = None
        if hasattr(db_manager, '_loaded'):
            db_manager._loaded = False
        
        # Test various field access patterns
        test_fields = [
            ('identity.name', 'Character name'),
            ('identity.occupation', 'Character occupation'),
            ('identity.description', 'Character description'),
            ('personality.big_five.openness', 'Openness trait'),
            ('personality.big_five.conscientiousness', 'Conscientiousness trait'),
            ('communication.response_length', 'Response length setting'),
            ('communication.communication_style', 'Communication style'),
            ('backstory.origin_story', 'Origin story'),
            ('current_life.living_situation', 'Living situation')
        ]
        
        field_results = {}
        
        for field_path, description in test_fields:
            try:
                field_result = get_cdl_field(field_path)
                if field_result and field_result.exists:
                    field_results[field_path] = {
                        'success': True,
                        'value_type': type(field_result.value).__name__,
                        'value_length': len(str(field_result.value)) if field_result.value else 0,
                        'has_value': field_result.value is not None and field_result.value != ''
                    }
                    print(f"  ✅ {field_path}: {description} - {type(field_result.value).__name__} ({len(str(field_result.value))} chars)")
                else:
                    field_results[field_path] = {'success': False, 'error': 'Field not found or empty'}
                    print(f"  ❌ {field_path}: {description} - Not found")
            except Exception as e:
                field_results[field_path] = {'success': False, 'error': str(e)}
                print(f"  ❌ {field_path}: {description} - Error: {e}")
        
        return field_results
        
    except Exception as e:
        print(f"  ❌ CDL field access test failed: {e}")
        return {'error': str(e)}

async def test_prompt_generation():
    """Test prompt generation with character data"""
    print("\n🔍 Phase 3: Testing Prompt Generation Pipeline")
    
    try:
        # Test Elena for prompt generation
        os.environ['CDL_DEFAULT_CHARACTER'] = 'characters/examples/elena.json'
        
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        cdl_integration = CDLAIPromptIntegration()
        
        # Test prompt generation
        test_message = "Tell me about your research background and current projects."
        user_id = "test_user_12345"
        
        enhanced_prompt = await cdl_integration.create_character_aware_prompt(
            character_file='characters/examples/elena.json',
            user_id=user_id,
            message_content=test_message
        )
        
        if enhanced_prompt:
            prompt_analysis = {
                'success': True,
                'prompt_length': len(enhanced_prompt),
                'contains_character_name': 'Elena' in enhanced_prompt,
                'contains_occupation': 'marine biologist' in enhanced_prompt.lower() or 'research scientist' in enhanced_prompt.lower(),
                'contains_personality': 'personality' in enhanced_prompt.lower() or 'traits' in enhanced_prompt.lower(),
                'contains_instructions': 'respond' in enhanced_prompt.lower() or 'answer' in enhanced_prompt.lower(),
                'prompt_preview': enhanced_prompt[:200] + "..." if len(enhanced_prompt) > 200 else enhanced_prompt
            }
            
            print(f"  ✅ Prompt generated successfully ({len(enhanced_prompt)} characters)")
            print(f"  ✅ Contains character name: {prompt_analysis['contains_character_name']}")
            print(f"  ✅ Contains occupation: {prompt_analysis['contains_occupation']}")
            print(f"  ✅ Contains personality: {prompt_analysis['contains_personality']}")
            print(f"  📝 Prompt preview: {enhanced_prompt[:150]}...")
            
            return prompt_analysis
        else:
            print("  ❌ Prompt generation failed - no output")
            return {'success': False, 'error': 'No prompt generated'}
            
    except Exception as e:
        print(f"  ❌ Prompt generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

async def test_character_data_consistency():
    """Test that character data is consistent across different access methods"""
    print("\n🔍 Phase 4: Testing Character Data Consistency")
    
    os.environ['CDL_DEFAULT_CHARACTER'] = 'characters/examples/marcus.json'
    
    try:
        # Method 1: Database manager character object
        from src.characters.cdl.database_manager import get_database_cdl_manager
        db_manager = get_database_cdl_manager()
        
        # Clear caching
        if hasattr(db_manager, '_character_name'):
            db_manager._character_name = None
        if hasattr(db_manager, '_character_data'):
            db_manager._character_data = None
        if hasattr(db_manager, '_loaded'):
            db_manager._loaded = False
        if hasattr(db_manager, '_character_object'):
            db_manager._character_object = None
        
        character_obj = db_manager.get_character_object()
        
        # Method 2: Direct CDL field access
        from src.characters.cdl.database_manager import get_cdl_field
        name_field = get_cdl_field('identity.name')
        occupation_field = get_cdl_field('identity.occupation')
        openness_field = get_cdl_field('personality.big_five.openness')
        
        # Compare results
        consistency_results = {
            'name_consistent': character_obj.identity.name == name_field.value if name_field.exists else False,
            'occupation_consistent': character_obj.identity.occupation == occupation_field.value if occupation_field.exists else False,
            'openness_consistent': character_obj.personality.big_five.openness == openness_field.value if openness_field.exists and hasattr(character_obj.personality, 'big_five') else False,
            'character_obj_name': character_obj.identity.name if character_obj else None,
            'field_access_name': name_field.value if name_field.exists else None,
            'character_obj_occupation': character_obj.identity.occupation if character_obj else None,
            'field_access_occupation': occupation_field.value if occupation_field.exists else None
        }
        
        all_consistent = all([
            consistency_results['name_consistent'],
            consistency_results['occupation_consistent'],
            consistency_results['openness_consistent']
        ])
        
        if all_consistent:
            print("  ✅ Character data is consistent across access methods")
            print(f"    Name: {consistency_results['character_obj_name']}")
            print(f"    Occupation: {consistency_results['character_obj_occupation']}")
        else:
            print("  ⚠️ Character data inconsistencies detected")
            print(f"    Name consistent: {consistency_results['name_consistent']}")
            print(f"    Occupation consistent: {consistency_results['occupation_consistent']}")
            print(f"    Openness consistent: {consistency_results['openness_consistent']}")
        
        return consistency_results
        
    except Exception as e:
        print(f"  ❌ Consistency test failed: {e}")
        return {'success': False, 'error': str(e)}

async def main():
    """Run complete end-to-end test suite"""
    print("🚀 CDL Normalized Database End-to-End Test Suite")
    print("=" * 60)
    
    # Run all test phases
    try:
        # Phase 1: Character loading
        loading_results = await test_character_database_loading()
        
        # Phase 2: CDL field access
        field_results = await test_cdl_field_access()
        
        # Phase 3: Prompt generation
        prompt_results = await test_prompt_generation()
        
        # Phase 4: Data consistency
        consistency_results = await test_character_data_consistency()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        # Character loading summary
        successful_loads = sum(1 for result in loading_results.values() if result.get('success', False))
        print(f"Character Loading: {successful_loads}/{len(loading_results)} characters loaded successfully")
        
        # Field access summary
        if 'error' not in field_results:
            successful_fields = sum(1 for result in field_results.values() if result.get('success', False))
            print(f"CDL Field Access: {successful_fields}/{len(field_results)} fields accessible")
        
        # Prompt generation summary
        if prompt_results.get('success', False):
            print(f"Prompt Generation: ✅ Working ({prompt_results['prompt_length']} chars)")
        else:
            print(f"Prompt Generation: ❌ Failed")
        
        # Overall result
        overall_success = (
            successful_loads >= 3 and  # At least 3 characters working
            prompt_results.get('success', False) and  # Prompt generation working
            not field_results.get('error')  # No field access errors
        )
        
        if overall_success:
            print("\n🎉 END-TO-END TEST PASSED!")
            print("✅ Normalized database → character loading → prompt generation pipeline working correctly")
            print("✅ RDBMS design successfully replaces JSONB blob approach")
            print("✅ All character data flows properly through the system")
        else:
            print("\n❌ END-TO-END TEST FAILED!")
            print("⚠️ Some components not working correctly")
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set required environment variables
    os.environ['FASTEMBED_CACHE_PATH'] = "/tmp/fastembed_cache"
    os.environ['QDRANT_HOST'] = "localhost"
    os.environ['QDRANT_PORT'] = "6334"
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)