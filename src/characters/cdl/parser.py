"""
Character Definition Language (CDL) Parser

This module handles parsing and serialization of character definitions from JSON format
following the CDL specification.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import asdict

from src.characters.models.character import (
    Character,
    CharacterMetadata,
    CharacterIdentity,
    CharacterPersonality,
    CharacterBackstory,
    CharacterCurrentLife,
    CharacterCommunication,
    BigFivePersonality,
    Appearance,
    Voice,
    LifePhase,
    CurrentProject,
    DailyRoutine,
    LicenseType,
    GenderIdentity,
)

logger = logging.getLogger(__name__)


class CDLParseError(Exception):
    """Exception raised when CDL parsing fails"""
    pass


class CDLParser:
    """Character Definition Language parser for JSON/YAML format (JSON preferred)"""
    
    CDL_VERSION = "1.0"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_file(self, file_path: Union[str, Path]) -> Character:
        """
        Parse a character definition from a JSON file.
        
        Args:
            file_path: Path to the CDL JSON file
            
        Returns:
            Character: Parsed character object
            
        Raises:
            CDLParseError: If parsing fails
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise CDLParseError(f"Character file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"Loading character from JSON: {file_path}")
            
            return self.parse_dict(data, source_file=str(file_path))
            
        except json.JSONDecodeError as e:
            raise CDLParseError(f"JSON parsing error in {file_path}: {e}")
        except Exception as e:
            raise CDLParseError(f"Error parsing character file {file_path}: {e}")
    
    def parse_dict(self, data: Dict[str, Any], source_file: Optional[str] = None) -> Character:
        """
        Parse a character definition from a dictionary.
        
        Args:
            data: Dictionary containing character definition
            source_file: Optional source file path for error reporting
            
        Returns:
            Character: Parsed character object
            
        Raises:
            CDLParseError: If parsing fails
        """
        try:
            # Validate CDL version
            cdl_version = data.get('cdl_version', '1.0')
            if cdl_version != self.CDL_VERSION:
                self.logger.warning(f"CDL version mismatch: expected {self.CDL_VERSION}, got {cdl_version}")
            
            character_data = data.get('character', {})
            if not character_data:
                raise CDLParseError("Missing 'character' section in CDL")
            
            # Parse each section
            metadata = self._parse_metadata(character_data.get('metadata', {}))
            identity = self._parse_identity(character_data.get('identity', {}))
            
            # Handle both old 'personality' and new 'core_personality' formats
            personality_data = character_data.get('personality', {})
            if not personality_data and 'core_personality' in character_data:
                personality_data = character_data['core_personality']
                
            personality = self._parse_personality(personality_data)
            backstory = self._parse_backstory(character_data.get('backstory', {}))
            current_life = self._parse_current_life(character_data.get('current_life', {}))
            communication = self._parse_communication(character_data.get('communication', {}))
            
            # Handle CDL v1.0 format with separate appearance and voice sections
            if 'appearance' in character_data:
                identity.appearance = self._parse_appearance(character_data['appearance'])
                # Extract description from appearance for easy access
                if identity.appearance and hasattr(identity.appearance, 'description'):
                    identity.description = identity.appearance.description
            
            if 'voice' in character_data:
                identity.voice = self._parse_voice(character_data['voice'])
            
            character = Character(
                metadata=metadata,
                identity=identity,
                personality=personality,
                backstory=backstory,
                current_life=current_life,
                communication=communication
            )
            
            # Validate the parsed character
            is_valid, errors = character.is_valid()
            if not is_valid:
                error_msg = f"Character validation failed: {'; '.join(errors)}"
                if source_file:
                    error_msg += f" (from {source_file})"
                raise CDLParseError(error_msg)
            
            self.logger.info(f"Successfully parsed character: {character.get_display_name()}")
            return character
            
        except CDLParseError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error parsing character: {e}"
            if source_file:
                error_msg += f" (from {source_file})"
            raise CDLParseError(error_msg)
    
    def _parse_metadata(self, data: Dict[str, Any]) -> CharacterMetadata:
        """Parse character metadata section"""
        metadata = CharacterMetadata()
        
        if 'character_id' in data:
            metadata.character_id = str(data['character_id'])
        if 'name' in data:
            metadata.name = str(data['name'])
        if 'version' in data:
            metadata.version = str(data['version'])
        if 'created_by' in data:
            metadata.created_by = str(data['created_by'])
        if 'created_date' in data:
            metadata.created_date = self._parse_datetime(data['created_date'])
        if 'last_modified' in data:
            metadata.last_modified = self._parse_datetime(data['last_modified'])
        if 'license' in data:
            metadata.license = LicenseType(data['license'])
        if 'tags' in data:
            metadata.tags = [str(tag) for tag in data['tags']]
        
        return metadata
    
    def _parse_identity(self, data: Dict[str, Any]) -> CharacterIdentity:
        """Parse character identity section"""
        identity = CharacterIdentity()
        
        if 'name' in data:
            identity.name = str(data['name'])
        if 'age' in data:
            identity.age = int(data['age'])
        if 'gender' in data:
            identity.gender = GenderIdentity(data['gender'])
        if 'occupation' in data:
            identity.occupation = str(data['occupation'])
        if 'location' in data:
            identity.location = str(data['location'])
        if 'timezone' in data:
            identity.timezone = str(data['timezone'])
        if 'nickname' in data:
            identity.nickname = str(data['nickname'])
        if 'full_name' in data:
            identity.full_name = str(data['full_name'])
        
        # Parse appearance
        if 'appearance' in data:
            identity.appearance = self._parse_appearance(data['appearance'])
            # Extract description from appearance for easy access
            if identity.appearance and hasattr(identity.appearance, 'description'):
                identity.description = identity.appearance.description
        
        # Parse voice
        if 'voice' in data:
            identity.voice = self._parse_voice(data['voice'])
        
        return identity
    
    def _parse_appearance(self, data: Dict[str, Any]) -> Appearance:
        """Parse appearance section"""
        appearance = Appearance()
        
        for field in ['height', 'build', 'hair_color', 'eye_color', 'style', 'description']:
            if field in data:
                setattr(appearance, field, str(data[field]))
        
        if 'distinctive_features' in data:
            appearance.distinctive_features = [str(f) for f in data['distinctive_features']]
        
        return appearance
    
    def _parse_voice(self, data: Dict[str, Any]) -> Voice:
        """Parse voice section"""
        voice = Voice()
        
        for field in ['tone', 'pace', 'volume', 'accent', 'vocabulary_level']:
            if field in data:
                setattr(voice, field, str(data[field]))
        
        if 'speech_patterns' in data:
            voice.speech_patterns = [str(p) for p in data['speech_patterns']]
        
        # Handle both 'favorite_phrases' and 'common_phrases' (CDL v1.0)
        phrases = []
        if 'favorite_phrases' in data:
            phrases = [str(p) for p in data['favorite_phrases']]
        elif 'common_phrases' in data:
            phrases = [str(p) for p in data['common_phrases']]
        # Note: Voice model needs to support favorite_phrases attribute
        
        return voice
    
    def _parse_personality(self, data: Dict[str, Any]) -> CharacterPersonality:
        """Parse personality section"""
        personality = CharacterPersonality()
        
        # Parse Big Five
        if 'big_five' in data:
            big_five_data = data['big_five']
            personality.big_five = BigFivePersonality(
                openness=float(big_five_data.get('openness', 0.5)),
                conscientiousness=float(big_five_data.get('conscientiousness', 0.5)),
                extraversion=float(big_five_data.get('extraversion', 0.5)),
                agreeableness=float(big_five_data.get('agreeableness', 0.5)),
                neuroticism=float(big_five_data.get('neuroticism', 0.5))
            )
        
        # Parse other personality fields
        if 'custom_traits' in data:
            personality.custom_traits = {k: float(v) for k, v in data['custom_traits'].items()}
        if 'values' in data:
            personality.values = [str(v) for v in data['values']]
        if 'fears' in data:
            personality.fears = [str(f) for f in data['fears']]
        if 'dreams' in data:
            personality.dreams = [str(d) for d in data['dreams']]
        if 'quirks' in data:
            personality.quirks = [str(q) for q in data['quirks']]
        if 'moral_alignment' in data:
            personality.moral_alignment = str(data['moral_alignment'])
        if 'core_beliefs' in data:
            personality.core_beliefs = [str(b) for b in data['core_beliefs']]
        
        return personality
    
    def _parse_backstory(self, data: Dict[str, Any]) -> CharacterBackstory:
        """Parse backstory section"""
        backstory = CharacterBackstory()
        
        if 'childhood' in data:
            backstory.childhood = self._parse_life_phase(data['childhood'])
        if 'education' in data:
            backstory.education = self._parse_life_phase(data['education'])
        if 'career' in data:
            backstory.career = self._parse_life_phase(data['career'])
        
        if 'relationships' in data:
            backstory.relationships = [str(r) for r in data['relationships']]
        if 'major_life_events' in data:
            backstory.major_life_events = [str(e) for e in data['major_life_events']]
        if 'defining_moments' in data:
            backstory.defining_moments = [str(m) for m in data['defining_moments']]
        if 'family_background' in data:
            backstory.family_background = str(data['family_background'])
        if 'cultural_background' in data:
            backstory.cultural_background = str(data['cultural_background'])
        
        if 'additional_phases' in data:
            backstory.additional_phases = [
                self._parse_life_phase(phase) for phase in data['additional_phases']
            ]
        
        return backstory
    
    def _parse_life_phase(self, data: Dict[str, Any]) -> LifePhase:
        """Parse a life phase section"""
        phase = LifePhase()
        
        if 'phase_name' in data:
            phase.phase_name = str(data['phase_name'])
        if 'age_range' in data:
            phase.age_range = str(data['age_range'])
        if 'emotional_impact' in data:
            phase.emotional_impact = str(data['emotional_impact'])
        
        if 'key_events' in data:
            phase.key_events = [str(e) for e in data['key_events']]
        if 'important_people' in data:
            phase.important_people = [str(p) for p in data['important_people']]
        if 'formative_experiences' in data:
            phase.formative_experiences = [str(e) for e in data['formative_experiences']]
        
        return phase
    
    def _parse_current_life(self, data: Dict[str, Any]) -> CharacterCurrentLife:
        """Parse current life section"""
        current_life = CharacterCurrentLife()
        
        if 'projects' in data:
            current_life.projects = [
                self._parse_current_project(proj) for proj in data['projects']
            ]
        
        if 'daily_routine' in data:
            # Handle both dictionary format (structured) and string format (simple)
            routine_data = data['daily_routine']
            if isinstance(routine_data, str):
                # Simple string format - create a basic routine object
                current_life.daily_routine = DailyRoutine()
                current_life.daily_routine.morning_routine = routine_data
            else:
                # Dictionary format - parse structured routine
                current_life.daily_routine = self._parse_daily_routine(routine_data)
        
        if 'current_goals' in data:
            current_life.current_goals = [str(g) for g in data['current_goals']]
        if 'current_challenges' in data:
            current_life.current_challenges = [str(c) for c in data['current_challenges']]
        if 'living_situation' in data:
            current_life.living_situation = str(data['living_situation'])
        if 'social_circle' in data:
            current_life.social_circle = [str(p) for p in data['social_circle']]
        if 'hobbies' in data:
            current_life.hobbies = [str(h) for h in data['hobbies']]
        if 'current_mood_baseline' in data:
            current_life.current_mood_baseline = str(data['current_mood_baseline'])
        
        return current_life
    
    def _parse_current_project(self, data: Dict[str, Any]) -> CurrentProject:
        """Parse a current project"""
        project = CurrentProject()
        
        if 'name' in data:
            project.name = str(data['name'])
        if 'description' in data:
            project.description = str(data['description'])
        if 'progress' in data:
            project.progress = float(data['progress'])
        if 'importance' in data:
            project.importance = str(data['importance'])
        if 'deadline' in data:
            project.deadline = self._parse_datetime(data['deadline'])
        if 'daily_time_allocation' in data:
            project.daily_time_allocation = str(data['daily_time_allocation'])
        
        return project
    
    def _parse_daily_routine(self, data: Dict[str, Any]) -> DailyRoutine:
        """Parse daily routine section"""
        routine = DailyRoutine()
        
        # Handle the correct field names that match the model
        for field in ['morning_routine', 'work_schedule', 'evening_routine', 'sleep_schedule']:
            if field in data:
                setattr(routine, field, str(data[field]))
        
        if 'habits' in data:
            routine.habits = [str(h) for h in data['habits']]
        
        # Legacy support for old format (morning, afternoon, evening as lists)
        for time_period in ['morning', 'afternoon', 'evening']:
            if time_period in data:
                setattr(routine, time_period, [str(a) for a in data[time_period]])
        
        # Support for weekend_activities if present
        if 'weekend_activities' in data:
            routine.weekend_activities = [str(a) for a in data['weekend_activities']]
        
        # Legacy field mapping
        if 'leisure_activities' in data:
            routine.habits.extend([str(a) for a in data['leisure_activities']])
        
        return routine
    
    def _parse_datetime(self, value: Any) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            # Try parsing ISO format
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                # Fallback to current time with warning
                self.logger.warning(f"Could not parse datetime '{value}', using current time")
                return datetime.now()
        else:
            self.logger.warning(f"Invalid datetime format: {value}, using current time")
            return datetime.now()
    
    def _parse_communication(self, data: Dict[str, Any]) -> CharacterCommunication:
        """Parse communication section with typical responses and emotional expressions"""
        communication = CharacterCommunication()
        
        # Parse typical_responses section
        if 'typical_responses' in data:
            typical_responses = data['typical_responses']
            for scenario_type, responses in typical_responses.items():
                if isinstance(responses, list):
                    communication.typical_responses[scenario_type] = [str(r) for r in responses]
                elif isinstance(responses, str):
                    communication.typical_responses[scenario_type] = [responses]
        
        # Parse emotional_expressions section
        if 'emotional_expressions' in data:
            emotional_expressions = data['emotional_expressions']
            for emotion, expression in emotional_expressions.items():
                communication.emotional_expressions[emotion] = str(expression)
        
        # Parse response style settings
        if 'response_length' in data:
            communication.response_length = str(data['response_length'])
        
        if 'communication_style' in data:
            communication.communication_style = str(data['communication_style'])
        
        return communication
    
    def serialize_to_dict(self, character: Character) -> Dict[str, Any]:
        """
        Serialize a character to a dictionary suitable for YAML export.
        
        Args:
            character: Character object to serialize
            
        Returns:
            Dict containing CDL-formatted character data
        """
        # Convert character to dict, handling special types
        char_dict = asdict(character)
        
        # Remove runtime state
        char_dict.pop('_runtime_state', None)
        
        # Convert enums to their values
        char_dict['metadata']['license'] = character.metadata.license.value
        char_dict['identity']['gender'] = character.identity.gender.value
        
        # Convert datetime objects to ISO strings
        char_dict['metadata']['created_date'] = character.metadata.created_date.isoformat()
        char_dict['metadata']['last_modified'] = character.metadata.last_modified.isoformat()
        
        # Handle project deadlines
        for project in char_dict['current_life']['projects']:
            if project.get('deadline'):
                project['deadline'] = project['deadline'].isoformat()
        
        # Wrap in CDL structure
        return {
            'cdl_version': self.CDL_VERSION,
            'character': char_dict
        }
    
    def serialize_to_file(self, character: Character, file_path: Union[str, Path]) -> None:
        """
        Serialize a character to a YAML file.
        
        Args:
            character: Character object to serialize
            file_path: Output file path
        """
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.serialize_to_dict(character)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Character '{character.get_display_name()}' saved to {file_path}")


# Convenience functions for common operations
def load_character(file_path: Union[str, Path]) -> Character:
    """Load a character from a CDL file"""
    parser = CDLParser()
    return parser.parse_file(file_path)


def save_character(character: Character, file_path: Union[str, Path]) -> None:
    """Save a character to a CDL file"""
    parser = CDLParser()
    parser.serialize_to_file(character, file_path)


def load_character_from_dict(data: Dict[str, Any]) -> Character:
    """Load a character from a dictionary"""
    parser = CDLParser()
    return parser.parse_dict(data)