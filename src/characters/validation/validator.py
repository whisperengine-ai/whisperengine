"""
Character Validation System

This module provides comprehensive validation for character definitions,
ensuring consistency, completeness, and adherence to CDL standards.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import fields

from src.characters.models.character import (
    Character,
    CharacterMetadata,
    CharacterIdentity,
    CharacterPersonality,
    CharacterBackstory,
    CharacterCurrentLife,
    BigFivePersonality,
    LicenseType,
    GenderIdentity,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when character validation fails"""
    pass


class ValidationSeverity:
    """Validation severity levels"""
    ERROR = "error"      # Must be fixed - prevents character from being used
    WARNING = "warning"  # Should be fixed - character may work but not optimally
    INFO = "info"       # Nice to have - suggestions for improvement


class ValidationResult:
    """Result of character validation"""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.score: float = 0.0  # Overall quality score (0.0-1.0)
    
    def add_error(self, message: str):
        """Add a validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a validation warning"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add a validation info message"""
        self.info.append(message)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of validation results"""
        if self.is_valid:
            status = "✅ VALID"
        else:
            status = "❌ INVALID"
        
        return (
            f"{status} - Score: {self.score:.1%}\n"
            f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}, "
            f"Suggestions: {len(self.info)}"
        )
    
    def get_detailed_report(self) -> str:
        """Get a detailed validation report"""
        report = [self.get_summary()]
        
        if self.errors:
            report.append("\n🚨 ERRORS (must fix):")
            for i, error in enumerate(self.errors, 1):
                report.append(f"  {i}. {error}")
        
        if self.warnings:
            report.append("\n⚠️  WARNINGS (should fix):")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"  {i}. {warning}")
        
        if self.info:
            report.append("\n💡 SUGGESTIONS (nice to have):")
            for i, info in enumerate(self.info, 1):
                report.append(f"  {i}. {info}")
        
        return "\n".join(report)


class CharacterValidator:
    """Comprehensive character validation system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define validation thresholds
        self.min_backstory_events = 3
        self.min_personality_traits = 3
        self.max_age_realistic = 100
        self.min_name_length = 2
        self.max_name_length = 50
        
        # Content quality keywords for scoring
        self.quality_keywords = {
            'positive': ['passionate', 'dedicated', 'experienced', 'skilled', 'creative'],
            'emotional': ['loves', 'fears', 'dreams', 'believes', 'values'],
            'specific': ['studied', 'worked', 'lived', 'traveled', 'learned']
        }
    
    def validate_character(self, character: Character) -> ValidationResult:
        """
        Perform comprehensive character validation.
        
        Args:
            character: Character object to validate
            
        Returns:
            ValidationResult: Detailed validation results
        """
        result = ValidationResult()
        
        # Core validation checks
        self._validate_metadata(character.metadata, result)
        self._validate_identity(character.identity, result)
        self._validate_personality(character.personality, result)
        self._validate_backstory(character.backstory, result)
        self._validate_current_life(character.current_life, result)
        
        # Cross-section consistency checks
        self._validate_consistency(character, result)
        
        # Content quality assessment
        self._assess_content_quality(character, result)
        
        # Calculate overall score
        result.score = self._calculate_quality_score(character, result)
        
        self.logger.debug(
            "Character validation completed: %s (score: %.1f%%)",
            character.get_display_name(),
            result.score * 100
        )
        
        return result
    
    def _validate_metadata(self, metadata: CharacterMetadata, result: ValidationResult):
        """Validate character metadata"""
        if not metadata.name or len(metadata.name.strip()) < self.min_name_length:
            result.add_error(f"Character name must be at least {self.min_name_length} characters")
        
        if len(metadata.name) > self.max_name_length:
            result.add_warning(f"Character name is very long ({len(metadata.name)} chars)")
        
        if not metadata.version:
            result.add_warning("Character version not specified")
        elif not re.match(r'^\d+\.\d+\.\d+$', metadata.version):
            result.add_info("Consider using semantic versioning (e.g., '1.0.0')")
        
        if not metadata.created_by:
            result.add_info("Consider adding creator attribution")
        
        if not metadata.tags:
            result.add_info("Adding tags helps with character discovery")
        elif len(metadata.tags) > 10:
            result.add_warning("Too many tags may hurt discoverability")
    
    def _validate_identity(self, identity: CharacterIdentity, result: ValidationResult):
        """Validate character identity"""
        if not identity.name or len(identity.name.strip()) < self.min_name_length:
            result.add_error("Character must have a valid name")
        
        if identity.age < 0:
            result.add_error("Character age cannot be negative")
        elif identity.age > 150:
            result.add_error("Character age is unrealistically high (>150)")
        elif identity.age > self.max_age_realistic:
            result.add_warning(f"Character age is high ({identity.age}), consider if realistic")
        
        if not identity.occupation:
            result.add_error("Character must have an occupation")
        elif len(identity.occupation.strip()) < 3:
            result.add_warning("Occupation description is very brief")
        
        if not identity.location:
            result.add_warning("Character location not specified")
        
        # Validate appearance details
        if identity.appearance:
            appearance = identity.appearance
            appearance_fields = [
                appearance.height, appearance.build, appearance.hair_color,
                appearance.eye_color, appearance.style
            ]
            filled_fields = sum(1 for field in appearance_fields if field)
            
            if filled_fields == 0:
                result.add_info("Consider adding physical appearance details")
            elif filled_fields < 3:
                result.add_info("More appearance details would help with character visualization")
        
        # Validate voice characteristics
        if identity.voice:
            voice = identity.voice
            voice_fields = [
                voice.tone, voice.pace, voice.accent, voice.vocabulary_level
            ]
            filled_fields = sum(1 for field in voice_fields if field)
            
            if filled_fields == 0:
                result.add_info("Consider adding voice/speech characteristics")
    
    def _validate_personality(self, personality: CharacterPersonality, result: ValidationResult):
        """Validate character personality"""
        # Validate Big Five scores
        try:
            big_five = personality.big_five
            
            # Check for default values (all 0.5)
            traits = [big_five.openness, big_five.conscientiousness, big_five.extraversion,
                     big_five.agreeableness, big_five.neuroticism]
            
            if all(abs(trait - 0.5) < 0.01 for trait in traits):
                result.add_warning("All Big Five traits are at default values (0.5)")
            
            # Check for extreme values
            extreme_traits = [name for name, value in big_five.__dict__.items() 
                            if value < 0.1 or value > 0.9]
            if extreme_traits:
                result.add_info(f"Extreme personality traits: {', '.join(extreme_traits)}")
            
        except Exception as e:
            result.add_error(f"Invalid Big Five personality scores: {e}")
        
        # Validate personality content
        if not personality.values:
            result.add_error("Character must have at least one core value")
        elif len(personality.values) < self.min_personality_traits:
            result.add_warning(f"Consider adding more core values (current: {len(personality.values)})")
        
        if not personality.fears:
            result.add_warning("Character should have some fears or concerns")
        
        if not personality.dreams:
            result.add_warning("Character should have dreams or aspirations")
        
        if not personality.quirks:
            result.add_info("Character quirks add personality depth")
        
        # Check for content quality
        all_traits = personality.values + personality.fears + personality.dreams + personality.quirks
        if any(len(trait.strip()) < 3 for trait in all_traits):
            result.add_warning("Some personality traits are very brief")
    
    def _validate_backstory(self, backstory: CharacterBackstory, result: ValidationResult):
        """Validate character backstory"""
        total_events = len(backstory.major_life_events)
        total_events += len(backstory.childhood.key_events)
        total_events += len(backstory.education.key_events)
        total_events += len(backstory.career.key_events)
        
        if total_events < self.min_backstory_events:
            result.add_error(
                f"Character needs more backstory events (current: {total_events}, "
                f"minimum: {self.min_backstory_events})"
            )
        
        if not backstory.major_life_events:
            result.add_warning("Character should have major life events")
        
        if not backstory.defining_moments:
            result.add_warning("Character should have defining moments")
        
        # Check life phases
        phases = [backstory.childhood, backstory.education, backstory.career]
        empty_phases = [phase for phase in phases if not phase.key_events]
        
        if len(empty_phases) > 1:
            result.add_warning("Multiple life phases are empty - consider adding more detail")
        
        # Check for family/cultural background
        if not backstory.family_background:
            result.add_info("Consider adding family background details")
        
        if not backstory.cultural_background:
            result.add_info("Consider adding cultural background details")
    
    def _validate_current_life(self, current_life: CharacterCurrentLife, result: ValidationResult):
        """Validate character current life"""
        if not current_life.projects:
            result.add_warning("Character should have current projects or activities")
        else:
            # Check project details
            incomplete_projects = [p for p in current_life.projects if not p.description]
            if incomplete_projects:
                result.add_warning(f"{len(incomplete_projects)} projects lack descriptions")
        
        if not current_life.current_goals:
            result.add_warning("Character should have current goals")
        
        if not current_life.hobbies:
            result.add_info("Consider adding hobbies for character depth")
        
        # Validate daily routine
        routine = current_life.daily_routine
        routine_parts = routine.morning + routine.afternoon + routine.evening
        
        if not routine_parts:
            result.add_warning("Character should have a daily routine")
        elif len(routine_parts) < 3:
            result.add_info("Daily routine could be more detailed")
    
    def _validate_consistency(self, character: Character, result: ValidationResult):
        """Validate cross-section consistency"""
        # Age consistency
        age = character.identity.age
        occupation = character.identity.occupation.lower()
        
        # Check age vs occupation consistency
        if age < 18 and any(word in occupation for word in ['doctor', 'lawyer', 'professor', 'ceo']):
            result.add_error(f"Age {age} inconsistent with occupation '{character.identity.occupation}'")
        
        # Check personality vs backstory consistency
        if character.personality.big_five.extraversion > 0.7:
            social_indicators = ['friends', 'social', 'party', 'group', 'team']
            backstory_text = ' '.join(character.backstory.major_life_events).lower()
            
            if not any(indicator in backstory_text for indicator in social_indicators):
                result.add_info("High extraversion not reflected in backstory events")
        
        # Check current life vs personality
        if character.personality.big_five.conscientiousness > 0.8:
            if not character.current_life.current_goals:
                result.add_warning("Highly conscientious character should have clear goals")
    
    def _assess_content_quality(self, character: Character, result: ValidationResult):
        """Assess overall content quality"""
        # Check for generic content
        generic_phrases = ['very', 'really', 'nice', 'good', 'bad', 'always', 'never']
        
        all_text = []
        all_text.extend(character.personality.values)
        all_text.extend(character.personality.fears)
        all_text.extend(character.backstory.major_life_events)
        
        text_content = ' '.join(all_text).lower()
        generic_count = sum(1 for phrase in generic_phrases if phrase in text_content)
        
        if generic_count > 5:
            result.add_info("Consider using more specific, unique descriptions")
        
        # Check for depth indicators
        depth_indicators = ['because', 'since', 'due to', 'led to', 'resulted in']
        depth_score = sum(1 for indicator in depth_indicators if indicator in text_content)
        
        if depth_score < 2:
            result.add_info("Adding causal relationships would increase character depth")
    
    def _calculate_quality_score(self, character: Character, result: ValidationResult) -> float:
        """Calculate overall character quality score (0.0-1.0)"""
        if not result.is_valid:
            return 0.0
        
        score = 0.0
        max_score = 10.0
        
        # Completeness scoring (40% of total)
        completeness_score = 0.0
        
        # Identity completeness (10 points max)
        identity_fields = [
            character.identity.name, character.identity.occupation,
            character.identity.location, character.identity.appearance.description,
            character.identity.voice.tone
        ]
        completeness_score += sum(2 for field in identity_fields if field) / 10.0
        
        # Personality completeness (10 points max)
        personality_items = (
            len(character.personality.values) + len(character.personality.fears) +
            len(character.personality.dreams) + len(character.personality.quirks)
        )
        completeness_score += min(personality_items / 10.0, 1.0)
        
        # Backstory completeness (10 points max)
        backstory_items = (
            len(character.backstory.major_life_events) +
            len(character.backstory.defining_moments) +
            len(character.backstory.childhood.key_events)
        )
        completeness_score += min(backstory_items / 10.0, 1.0)
        
        # Current life completeness (10 points max)
        current_life_items = (
            len(character.current_life.projects) + len(character.current_life.current_goals) +
            len(character.current_life.hobbies)
        )
        completeness_score += min(current_life_items / 10.0, 1.0)
        
        score += completeness_score * 4.0  # 40% weight
        
        # Quality penalties
        score -= len(result.warnings) * 0.5   # -0.5 per warning
        score -= len(result.info) * 0.1       # -0.1 per suggestion
        
        # Normalize to 0.0-1.0
        return max(0.0, min(1.0, score / max_score))


def validate_character(character: Character) -> ValidationResult:
    """Convenience function for character validation"""
    validator = CharacterValidator()
    return validator.validate_character(character)


def quick_validate(character: Character) -> bool:
    """Quick validation - returns True if character is valid"""
    result = validate_character(character)
    return result.is_valid