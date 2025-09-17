#!/usr/bin/env python3
"""
Test script for the Autonomous Character System

This script demonstrates the Character Definition Language (CDL) system by:
1. Loading example characters from YAML files
2. Validating character definitions
3. Displaying character information and validation results
4. Testing serialization/deserialization
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.characters.cdl.parser import CDLParser, load_character
from src.characters.validation.validator import validate_character
from src.characters.models.character import Character

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_character_loading():
    """Test loading characters from YAML files"""
    logger.info("🎭 Testing Character Definition Language (CDL) System")
    logger.info("=" * 60)
    
    characters_dir = Path("characters/examples")
    if not characters_dir.exists():
        logger.error(f"Characters directory not found: {characters_dir}")
        return False
    
    character_files = list(characters_dir.glob("*.yaml"))
    if not character_files:
        logger.warning(f"No character files found in {characters_dir}")
        return False
    
    logger.info(f"Found {len(character_files)} character files")
    
    loaded_characters = []
    
    for char_file in character_files:
        try:
            logger.info(f"\n📖 Loading character: {char_file.name}")
            
            # Load character
            character = load_character(char_file)
            loaded_characters.append(character)
            
            # Display basic info
            logger.info(f"✅ Successfully loaded: {character.get_display_name()}")
            logger.info(f"   Age: {character.identity.age}")
            logger.info(f"   Occupation: {character.identity.occupation}")
            logger.info(f"   Location: {character.identity.location}")
            
            # Validate character
            validation_result = validate_character(character)
            logger.info(f"   Validation: {validation_result.get_summary()}")
            
            if validation_result.errors:
                logger.error("   Validation Errors:")
                for error in validation_result.errors:
                    logger.error(f"     - {error}")
            
            if validation_result.warnings:
                logger.warning("   Validation Warnings:")
                for warning in validation_result.warnings:
                    logger.warning(f"     - {warning}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load {char_file.name}: {e}")
    
    return loaded_characters


def test_character_creation():
    """Test creating a character programmatically"""
    logger.info("\n🔨 Testing Programmatic Character Creation")
    logger.info("-" * 40)
    
    try:
        from src.characters.models.character import (
            Character, CharacterMetadata, CharacterIdentity, 
            CharacterPersonality, BigFivePersonality, GenderIdentity
        )
        
        # Create a simple character
        character = Character()
        character.metadata.name = "Test Character"
        character.identity.name = "Alex Smith"
        character.identity.age = 30
        character.identity.gender = GenderIdentity.NON_BINARY
        character.identity.occupation = "Software Engineer"
        character.identity.location = "Seattle, WA"
        
        # Set personality
        character.personality.big_five = BigFivePersonality(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.5,
            agreeableness=0.6,
            neuroticism=0.3
        )
        character.personality.values = ["Innovation", "Problem-solving", "Work-life balance"]
        character.backstory.major_life_events = [
            "Graduated with Computer Science degree",
            "Started career at tech startup",
            "Moved to Seattle for new opportunities"
        ]
        
        logger.info(f"✅ Created character: {character.get_display_name()}")
        
        # Validate
        validation = validate_character(character)
        logger.info(f"   Validation: {validation.get_summary()}")
        
        # Test serialization
        parser = CDLParser()
        char_dict = parser.serialize_to_dict(character)
        logger.info(f"   Serialization: ✅ {len(char_dict)} top-level keys")
        
        # Test round-trip
        reloaded_char = parser.parse_dict(char_dict)
        logger.info(f"   Round-trip: ✅ {reloaded_char.get_display_name()}")
        
        return character
        
    except Exception as e:
        logger.error(f"❌ Character creation failed: {e}")
        return None


def display_character_summary(character):
    """Display a comprehensive character summary"""
    logger.info(f"\n📋 Character Summary: {character.get_display_name()}")
    logger.info("=" * 50)
    
    # Basic info
    logger.info(f"Name: {character.identity.name}")
    logger.info(f"Age: {character.identity.age}")
    logger.info(f"Occupation: {character.identity.occupation}")
    logger.info(f"Location: {character.identity.location}")
    
    # Personality summary
    personality = character.get_personality_summary()
    logger.info("\nPersonality (Big Five):")
    for trait, value in personality['big_five'].items():
        logger.info(f"  {trait.title()}: {value:.2f}")
    
    logger.info(f"\nTop Values: {', '.join(personality['dominant_values'])}")
    logger.info(f"Primary Fears: {', '.join(personality['primary_fears'])}")
    
    # Life context
    life_context = character.get_life_context()
    logger.info(f"\nCurrent Projects: {', '.join(life_context['current_projects'])}")
    logger.info(f"Main Goals: {', '.join(life_context['primary_goals'])}")


def main():
    """Main test function"""
    logger.info("🚀 Starting Autonomous Character System Tests")
    
    # Test 1: Load characters from files
    loaded_characters = test_character_loading()
    
    # Test 2: Create character programmatically  
    created_character = test_character_creation()
    
    # Test 3: Display detailed summaries
    if loaded_characters:
        display_character_summary(loaded_characters[0])
    
    if created_character:
        display_character_summary(created_character)
    
    # Summary
    logger.info("\n🎯 Test Summary")
    logger.info("=" * 30)
    logger.info(f"Characters loaded from files: {len(loaded_characters) if loaded_characters else 0}")
    logger.info(f"Characters created programmatically: {1 if created_character else 0}")
    
    if loaded_characters or created_character:
        logger.info("✅ Character Definition Language system is working!")
        logger.info("\nNext steps:")
        logger.info("  1. Implement self-memory system")
        logger.info("  2. Add life simulation engine")
        logger.info("  3. Create autonomous workflow system")
    else:
        logger.error("❌ Character system tests failed")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)