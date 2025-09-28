#!/usr/bin/env python3
"""
CDL Validator - Main validation class for Character Definition Language files.

Provides comprehensive validation including structure, patterns, and standardization compliance.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from src.characters.cdl.parser import load_character
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration


class ValidationStatus(Enum):
    """Validation status levels."""
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: ValidationStatus
    category: str
    message: str
    section: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result for a CDL file."""
    file_path: str
    character_name: str
    parsing_success: bool
    standardization_compliant: bool
    pattern_detection_working: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    quality_score: float = 0.0
    
    @property
    def overall_status(self) -> ValidationStatus:
        """Determine overall validation status."""
        if not self.parsing_success:
            return ValidationStatus.ERROR
        
        error_count = sum(1 for issue in self.issues if issue.level == ValidationStatus.ERROR)
        if error_count > 0:
            return ValidationStatus.ERROR
            
        warning_count = sum(1 for issue in self.issues if issue.level == ValidationStatus.WARNING)
        if warning_count > 0:
            return ValidationStatus.WARNING
            
        return ValidationStatus.SUCCESS
    
    @property
    def summary(self) -> str:
        """Generate a summary string."""
        status_emoji = {
            ValidationStatus.SUCCESS: "✅",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.ERROR: "❌"
        }
        
        emoji = status_emoji[self.overall_status]
        errors = sum(1 for i in self.issues if i.level == ValidationStatus.ERROR)
        warnings = sum(1 for i in self.issues if i.level == ValidationStatus.WARNING)
        
        return f"{emoji} {self.character_name} - {errors} errors, {warnings} warnings"


class CDLValidator:
    """
    Main CDL validation class providing comprehensive validation capabilities.
    
    Usage:
        validator = CDLValidator()
        result = validator.validate_file('path/to/character.json')
        validator.print_validation_report(result)
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.cdl_integration = CDLAIPromptIntegration()
        
        # Standard test messages for pattern detection
        self.standard_test_messages = [
            ("consciousness expansion", ["mystical", "transcendent", "spiritual"]),
            ("had a dream", ["dream", "sleep", "vision"]),
            ("beautiful eyes", ["romantic", "compliment", "attractive"]),
            ("teach me", ["education", "learning", "academic"]),
            ("marine biology", ["science", "environmental", "ocean"]),
            ("code together", ["collaboration", "creative", "programming"]),
            ("gaming discussion", ["game", "development", "technical"]),
            ("need spiritual guidance", ["spiritual", "guidance"]),
            ("faith questions", ["spiritual", "guidance"])
        ]
        
        # Required CDL sections for completeness check
        self.required_sections = {
            'character.identity': 'Character Identity (name, age, occupation, etc.)',
            'character.identity.appearance': 'Physical Appearance Description',
            'character.identity.voice': 'Voice and Speaking Style',
            'character.personality': 'Core Personality Traits',
            'character.personality.big_five': 'Big Five Personality Profile',
            'character.personality.communication_style': 'Communication Preferences',
            'character.communication': 'Communication Patterns',
            'character.communication.typical_responses': 'Scenario-Based Responses',
            'character.communication.message_pattern_triggers': 'Message Pattern Triggers',
            'character.communication.conversation_flow_guidance': 'Conversation Flow Rules',
            'character.background': 'Character Background/History',
            'character.background.formative_experiences': 'Life-Shaping Events',
            'character.current_life': 'Current Life Situation',
            'character.relationships': 'Relationship Dynamics',
            'character.personality.communication_style.ai_identity_handling': 'AI Identity Responses',
            'character.personality.communication_style.ai_identity_handling.relationship_boundary_scenarios': 'Romantic Boundary Handling',
            'character.identity.digital_communication': 'Digital/Emoji Communication',
            'character.identity.digital_communication.emoji_personality': 'Emoji Usage Patterns',
            'character.skills_and_expertise': 'Professional Skills',
            'character.interests_and_hobbies': 'Personal Interests',
            'character.speech_patterns': 'Detailed Speech Patterns'
        }
    
    def validate_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate a single CDL file comprehensively.
        
        Args:
            file_path: Path to the CDL JSON file
            
        Returns:
            ValidationResult with complete validation information
        """
        file_path = Path(file_path)
        issues = []
        
        # Initialize result
        result = ValidationResult(
            file_path=str(file_path),
            character_name="Unknown",
            parsing_success=False,
            standardization_compliant=False,
            pattern_detection_working=False
        )
        
        # Test 1: File existence and basic JSON parsing
        if not file_path.exists():
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="file_access",
                message=f"File not found: {file_path}",
                suggestion="Check the file path and ensure the file exists"
            ))
            result.issues = issues
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="json_parsing",
                message=f"Invalid JSON format: {e}",
                suggestion="Check JSON syntax, commas, brackets, and quotes"
            ))
            result.issues = issues
            return result
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="file_access",
                message=f"Cannot read file: {e}",
                suggestion="Check file permissions and encoding"
            ))
            result.issues = issues
            return result
        
        # Test 2: CDL structure parsing
        try:
            character = load_character(str(file_path))
            result.character_name = character.identity.name
            result.parsing_success = True
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="cdl_parsing",
                message=f"CDL parsing failed: {e}",
                suggestion="Check CDL structure matches expected schema"
            ))
            result.issues = issues
            return result
        
        # Test 3: Standardization compliance
        standardization_result = self._check_standardization(cdl_data)
        result.standardization_compliant = standardization_result['compliant']
        issues.extend(standardization_result['issues'])
        
        # Test 4: Pattern detection testing
        if result.standardization_compliant:
            pattern_result = self._test_pattern_detection(character, file_path.name)
            result.pattern_detection_working = pattern_result['working']
            result.patterns_detected = pattern_result['patterns']
            issues.extend(pattern_result['issues'])
        
        # Test 5: Completeness analysis
        completeness_result = self._analyze_completeness(cdl_data)
        result.completeness_score = completeness_result['score']
        result.quality_score = completeness_result['quality_score']
        issues.extend(completeness_result['issues'])
        
        result.issues = issues
        return result
    
    def _check_standardization(self, cdl_data: Dict) -> Dict[str, Any]:
        """Check if CDL follows standardized structure."""
        issues = []
        compliant = True
        
        communication = cdl_data.get('character', {}).get('communication', {})
        has_triggers = 'message_pattern_triggers' in communication
        has_guidance = 'conversation_flow_guidance' in communication
        
        # Check for standardized location
        if not has_triggers:
            issues.append(ValidationIssue(
                level=ValidationStatus.WARNING,
                category="standardization",
                message="Missing message_pattern_triggers in character.communication",
                section="character.communication",
                suggestion="Add message_pattern_triggers section for conversation flow detection"
            ))
            compliant = False
            
        if not has_guidance:
            issues.append(ValidationIssue(
                level=ValidationStatus.WARNING,
                category="standardization", 
                message="Missing conversation_flow_guidance in character.communication",
                section="character.communication",
                suggestion="Add conversation_flow_guidance section for response strategies"
            ))
            compliant = False
        
        # Check for old location patterns (should not exist)
        old_location = (cdl_data.get('character', {})
                       .get('personality', {})
                       .get('communication_style', {}))
        
        has_old_triggers = 'message_pattern_triggers' in old_location
        has_old_guidance = 'conversation_flow_guidance' in old_location
        
        if has_old_triggers:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="standardization",
                message="Found message_pattern_triggers in old location (personality.communication_style)",
                section="character.personality.communication_style",
                suggestion="Move message_pattern_triggers to character.communication"
            ))
            compliant = False
            
        if has_old_guidance:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="standardization",
                message="Found conversation_flow_guidance in old location (personality.communication_style)",
                section="character.personality.communication_style", 
                suggestion="Move conversation_flow_guidance to character.communication"
            ))
            compliant = False
        
        return {
            'compliant': compliant,
            'issues': issues,
            'has_triggers': has_triggers,
            'has_guidance': has_guidance
        }
    
    def _test_pattern_detection(self, character, filename: str) -> Dict[str, Any]:
        """Test pattern detection functionality."""
        issues = []
        patterns_detected = []
        working = False
        
        # Use character-specific test messages
        test_messages = self.standard_test_messages
        if 'gabriel' in filename.lower():
            test_messages = [
                ("need spiritual guidance", ["spiritual", "guidance"]),
                ("faith questions", ["spiritual", "guidance"]),
                ("theological discussion", ["theological", "discussion"])
            ]
        
        try:
            for message, expected_keywords in test_messages:
                scenarios = self.cdl_integration._detect_communication_scenarios(
                    message, character, 'test_user'
                )
                if scenarios:
                    patterns_detected.extend(list(scenarios.keys()))
                    working = True
            
            # Remove duplicates
            patterns_detected = list(set(patterns_detected))
            
            if not working:
                issues.append(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category="pattern_detection",
                    message="No patterns detected with standard test messages",
                    suggestion="Verify message_pattern_triggers have matching conversation_flow_guidance entries"
                ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationStatus.ERROR,
                category="pattern_detection",
                message=f"Pattern detection test failed: {e}",
                suggestion="Check CDL structure and pattern configuration"
            ))
        
        return {
            'working': working,
            'patterns': patterns_detected,
            'issues': issues
        }
    
    def _analyze_completeness(self, cdl_data: Dict) -> Dict[str, Any]:
        """Analyze CDL completeness and quality."""
        issues = []
        present = 0
        well_customized = 0
        total = len(self.required_sections)
        
        for section_path, description in self.required_sections.items():
            section_result = self._check_section_completeness(cdl_data, section_path)
            
            if section_result['exists']:
                present += 1
                customization_level = self._analyze_customization_level(
                    section_result['content'], section_path
                )
                
                if customization_level == "GOOD":
                    well_customized += 1
                elif customization_level == "PLACEHOLDER":
                    issues.append(ValidationIssue(
                        level=ValidationStatus.WARNING,
                        category="completeness",
                        message=f"Placeholder content detected in {description}",
                        section=section_path,
                        suggestion="Replace placeholder content with character-specific details"
                    ))
            else:
                issues.append(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category="completeness",
                    message=f"Missing section: {description}",
                    section=section_path,
                    suggestion="Add this section to improve character completeness"
                ))
        
        completeness_score = (present / total) * 100
        quality_score = (well_customized / total) * 100
        
        return {
            'score': completeness_score,
            'quality_score': quality_score,
            'issues': issues,
            'present': present,
            'total': total,
            'well_customized': well_customized
        }
    
    def _check_section_completeness(self, data: Dict, section_path: str) -> Dict[str, Any]:
        """Check if a nested section exists and has content."""
        keys = section_path.split('.')
        current = data
        
        try:
            for key in keys:
                if key not in current:
                    return {'exists': False, 'reason': f'Missing key: {key}'}
                current = current[key]
                
            if not current:
                return {'exists': False, 'reason': 'Empty section'}
                
            if isinstance(current, dict) and not current:
                return {'exists': False, 'reason': 'Empty dictionary'}
                
            if isinstance(current, list) and not current:
                return {'exists': False, 'reason': 'Empty list'}
                
            return {'exists': True, 'content': current}
            
        except (KeyError, TypeError) as e:
            return {'exists': False, 'reason': f'Access error: {e}'}
    
    def _analyze_customization_level(self, content: Any, section_name: str) -> str:
        """Analyze how well customized a section is."""
        if not content:
            return "MISSING"
            
        content_str = str(content).lower()
        
        # Check for placeholder patterns
        placeholder_patterns = [
            'placeholder', 'todo', 'tbd', 'fill in', 'example',
            'lorem ipsum', 'sample', 'default', 'template'
        ]
        
        for pattern in placeholder_patterns:
            if pattern in content_str:
                return "PLACEHOLDER"
        
        # Check for good customization indicators
        good_indicators = [
            len(content_str) > 100,  # Substantial content
            'specific' in content_str or 'unique' in content_str,
            isinstance(content, dict) and len(content) > 3,
            isinstance(content, list) and len(content) > 2
        ]
        
        if any(good_indicators):
            return "GOOD"
            
        return "BASIC"
    
    def validate_directory(self, directory_path: Union[str, Path], 
                          pattern: str = "*.json") -> List[ValidationResult]:
        """
        Validate all CDL files in a directory.
        
        Args:
            directory_path: Path to directory containing CDL files
            pattern: File pattern to match (default: "*.json")
            
        Returns:
            List of ValidationResult objects
        """
        directory_path = Path(directory_path)
        results = []
        
        if not directory_path.exists():
            # Return empty results with error
            return [ValidationResult(
                file_path=str(directory_path),
                character_name="Directory Not Found",
                parsing_success=False,
                standardization_compliant=False,
                pattern_detection_working=False,
                issues=[ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category="directory_access",
                    message=f"Directory not found: {directory_path}",
                    suggestion="Check the directory path"
                )]
            )]
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file():
                result = self.validate_file(file_path)
                results.append(result)
        
        return results
    
    def print_validation_report(self, result: ValidationResult, verbose: bool = False):
        """
        Print a formatted validation report.
        
        Args:
            result: ValidationResult to report on
            verbose: Include detailed issue information
        """
        print(f"\n📋 {result.character_name} ({Path(result.file_path).name})")
        print("=" * 60)
        
        # Overall status
        status_emoji = {
            ValidationStatus.SUCCESS: "✅",
            ValidationStatus.WARNING: "⚠️", 
            ValidationStatus.ERROR: "❌"
        }
        
        print(f"📊 Overall Status: {status_emoji[result.overall_status]} {result.overall_status.value.upper()}")
        print(f"📊 Parsing: {'✅' if result.parsing_success else '❌'}")
        print(f"📊 Standardization: {'✅' if result.standardization_compliant else '❌'}")
        print(f"📊 Pattern Detection: {'✅' if result.pattern_detection_working else '❌'}")
        
        if result.patterns_detected:
            print(f"📊 Patterns Detected: {', '.join(result.patterns_detected)}")
        
        print(f"📊 Completeness: {result.completeness_score:.1f}%")
        print(f"📊 Quality Score: {result.quality_score:.1f}%")
        
        # Issues summary
        errors = [i for i in result.issues if i.level == ValidationStatus.ERROR]
        warnings = [i for i in result.issues if i.level == ValidationStatus.WARNING]
        
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for issue in errors:
                print(f"   • {issue.message}")
                if verbose and issue.suggestion:
                    print(f"     💡 {issue.suggestion}")
        
        if warnings:
            print(f"\n⚠️ Warnings ({len(warnings)}):")
            for issue in warnings:
                print(f"   • {issue.message}")
                if verbose and issue.suggestion:
                    print(f"     💡 {issue.suggestion}")
        
        if not errors and not warnings:
            print("\n🎉 No issues found!")
    
    def print_summary_report(self, results: List[ValidationResult]):
        """
        Print a summary report for multiple validation results.
        
        Args:
            results: List of ValidationResult objects
        """
        if not results:
            print("No validation results to report.")
            return
        
        print(f"\n🎯 CDL VALIDATION SUMMARY")
        print("=" * 80)
        
        total = len(results)
        successful_parsing = sum(1 for r in results if r.parsing_success)
        standardized = sum(1 for r in results if r.standardization_compliant)
        pattern_working = sum(1 for r in results if r.pattern_detection_working)
        
        avg_completeness = sum(r.completeness_score for r in results) / total
        avg_quality = sum(r.quality_score for r in results) / total
        
        print(f"📊 Files Analyzed: {total}")
        print(f"📊 Parsing Success: {successful_parsing}/{total} ({successful_parsing/total*100:.1f}%)")
        print(f"📊 Standardized Structure: {standardized}/{total} ({standardized/total*100:.1f}%)")
        print(f"📊 Pattern Detection: {pattern_working}/{total} ({pattern_working/total*100:.1f}%)")
        print(f"📊 Average Completeness: {avg_completeness:.1f}%")
        print(f"📊 Average Quality: {avg_quality:.1f}%")
        
        # Status breakdown
        success_count = sum(1 for r in results if r.overall_status == ValidationStatus.SUCCESS)
        warning_count = sum(1 for r in results if r.overall_status == ValidationStatus.WARNING)
        error_count = sum(1 for r in results if r.overall_status == ValidationStatus.ERROR)
        
        print(f"\n📋 Status Breakdown:")
        print(f"   ✅ Success: {success_count}")
        print(f"   ⚠️  Warnings: {warning_count}")
        print(f"   ❌ Errors: {error_count}")
        
        # Top performers
        print(f"\n🏆 Top Performing Characters:")
        sorted_results = sorted(results, key=lambda r: r.quality_score, reverse=True)
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"   {i}. {result.character_name:<20} - {result.completeness_score:.1f}% complete, {result.quality_score:.1f}% quality")