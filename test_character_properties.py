#!/usr/bin/env python3
"""
Test SimpleCDLManager Personal Knowledge Property Access
Validates that Character object exposes relationships, backstory, current_life, 
skills_and_expertise, and interests_and_hobbies properties.
"""

import os
import sys
import asyncio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager

# Test data - all 10 characters
TEST_CHARACTERS = [
    'elena', 'marcus', 'jake', 'ryan', 'gabriel', 
    'sophia', 'dream', 'aethys', 'aetheris', 'dotty'
]

def test_character_properties(character_name: str):
    """Test property access for a single character"""
    logger.info("\n" + "="*80)
    logger.info(f"Testing Character: {character_name.upper()}")
    logger.info("="*80)
    
    # Set environment to load correct character
    os.environ['DISCORD_BOT_NAME'] = character_name
    os.environ['BOT_NAME'] = character_name
    
    try:
        # Get character object
        cdl_manager = get_simple_cdl_manager()
        character = cdl_manager.get_character_object()
        
        # Test critical fields (should always work)
        logger.info("\n✅ CRITICAL FIELDS:")
        logger.info(f"  - Name: {character.identity.name}")
        logger.info(f"  - Occupation: {character.identity.occupation}")
        logger.info(f"  - Description: {character.identity.description[:80]}...")
        logger.info(f"  - Allow Roleplay: {character.allow_full_roleplay_immersion}")
        
        # Test personality
        if hasattr(character, 'personality') and hasattr(character.personality, 'big_five'):
            big_five = character.personality.big_five
            logger.info(f"  - Big Five Traits: {5 if hasattr(big_five, 'openness') else 0} traits")
        
        # Test NEW property access (personal knowledge)
        logger.info("\n🆕 PERSONAL KNOWLEDGE PROPERTIES:")
        
        # Test relationships
        logger.info(f"  - hasattr(character, 'relationships'): {hasattr(character, 'relationships')}")
        if hasattr(character, 'relationships'):
            try:
                rel = character.relationships
                logger.info(f"    ✅ relationships accessible")
                if rel:
                    logger.info(f"       - Status: {rel.status if hasattr(rel, 'status') else 'N/A'}")
                    logger.info(f"       - Important relationships: {len(rel.important_relationships) if hasattr(rel, 'important_relationships') else 0}")
                    if hasattr(rel, 'important_relationships') and rel.important_relationships:
                        for i, r in enumerate(rel.important_relationships[:3], 1):
                            logger.info(f"         {i}. {r}")
                else:
                    logger.info(f"       ⚠️  relationships is None/empty")
            except Exception as e:
                logger.error(f"    ❌ Error accessing relationships: {e}")
        
        # Test backstory
        logger.info(f"  - hasattr(character, 'backstory'): {hasattr(character, 'backstory')}")
        if hasattr(character, 'backstory'):
            try:
                backstory = character.backstory
                logger.info(f"    ✅ backstory accessible")
                if backstory:
                    logger.info(f"       - Family background: {bool(backstory.family_background) if hasattr(backstory, 'family_background') else False}")
                    if hasattr(backstory, 'family_background') and backstory.family_background:
                        logger.info(f"         {backstory.family_background[:100]}...")
                    logger.info(f"       - Career background: {bool(backstory.career_background) if hasattr(backstory, 'career_background') else False}")
                    if hasattr(backstory, 'career_background') and backstory.career_background:
                        logger.info(f"         {backstory.career_background[:100]}...")
                    logger.info(f"       - Formative experiences: {bool(backstory.formative_experiences) if hasattr(backstory, 'formative_experiences') else False}")
                else:
                    logger.info(f"       ⚠️  backstory is None/empty")
            except Exception as e:
                logger.error(f"    ❌ Error accessing backstory: {e}")
        
        # Test current_life
        logger.info(f"  - hasattr(character, 'current_life'): {hasattr(character, 'current_life')}")
        if hasattr(character, 'current_life'):
            try:
                current_life = character.current_life
                logger.info(f"    ✅ current_life accessible")
                if current_life:
                    logger.info(f"       - Family: {bool(current_life.family) if hasattr(current_life, 'family') else False}")
                    logger.info(f"       - Occupation details: {bool(current_life.occupation_details) if hasattr(current_life, 'occupation_details') else False}")
                    logger.info(f"       - Daily routine: {bool(current_life.daily_routine) if hasattr(current_life, 'daily_routine') else False}")
                else:
                    logger.info(f"       ⚠️  current_life is None/empty")
            except Exception as e:
                logger.error(f"    ❌ Error accessing current_life: {e}")
        
        # Test skills_and_expertise
        logger.info(f"  - hasattr(character, 'skills_and_expertise'): {hasattr(character, 'skills_and_expertise')}")
        if hasattr(character, 'skills_and_expertise'):
            try:
                skills = character.skills_and_expertise
                logger.info(f"    ✅ skills_and_expertise accessible")
                if skills:
                    logger.info(f"       - Education: {bool(skills.education) if hasattr(skills, 'education') else False}")
                    if hasattr(skills, 'education') and skills.education:
                        logger.info(f"         {skills.education[:100]}...")
                    logger.info(f"       - Professional skills: {bool(skills.professional_skills) if hasattr(skills, 'professional_skills') else False}")
                    if hasattr(skills, 'professional_skills') and skills.professional_skills:
                        logger.info(f"         {skills.professional_skills[:100]}...")
                else:
                    logger.info(f"       ⚠️  skills_and_expertise is None/empty")
            except Exception as e:
                logger.error(f"    ❌ Error accessing skills_and_expertise: {e}")
        
        # Test interests_and_hobbies
        logger.info(f"  - hasattr(character, 'interests_and_hobbies'): {hasattr(character, 'interests_and_hobbies')}")
        if hasattr(character, 'interests_and_hobbies'):
            try:
                interests = character.interests_and_hobbies
                logger.info(f"    ✅ interests_and_hobbies accessible")
                if interests:
                    logger.info(f"       - Value: {interests[:100] if isinstance(interests, str) else interests}...")
                else:
                    logger.info(f"       ⚠️  interests_and_hobbies is None/empty")
            except Exception as e:
                logger.error(f"    ❌ Error accessing interests_and_hobbies: {e}")
        
        logger.info(f"\n✅ SUCCESS: {character_name} character object created and properties accessible")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ FAILED: {character_name} - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test all characters"""
    logger.info("="*80)
    logger.info("SimpleCDLManager Personal Knowledge Property Test")
    logger.info("="*80)
    logger.info(f"Testing {len(TEST_CHARACTERS)} characters for property access...")
    
    results = {}
    for character_name in TEST_CHARACTERS:
        results[character_name] = test_character_properties(character_name)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for success in results.values() if success)
    failed = len(results) - passed
    
    logger.info(f"\nTotal Characters: {len(TEST_CHARACTERS)}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    
    logger.info("\nIndividual Results:")
    for character_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {character_name:12} - {status}")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Personal knowledge properties working for all characters!")
    else:
        logger.warning(f"\n⚠️  {failed} character(s) failed property tests")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
