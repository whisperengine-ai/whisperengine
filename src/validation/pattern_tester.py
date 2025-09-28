#!/usr/bin/env python3
"""
CDL Pattern Tester - Specialized testing for CDL conversation flow patterns.

Validates pattern detection, conversation flow, and character-specific response triggers.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Union, Tuple, Optional
from dataclasses import dataclass, field

from src.characters.cdl.parser import load_character
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration


@dataclass
class PatternTestCase:
    """Represents a pattern detection test case."""
    test_message: str
    expected_patterns: List[str]
    expected_keywords: List[str]
    character_specific: bool = False
    description: str = ""


@dataclass
class PatternTestResult:
    """Result of pattern detection testing."""
    test_case: PatternTestCase
    detected_patterns: List[str] = field(default_factory=list)
    success: bool = False
    issues: List[str] = field(default_factory=list)
    response_quality: str = "UNKNOWN"
    
    @property
    def pattern_match_score(self) -> float:
        """Calculate pattern matching success rate."""
        if not self.test_case.expected_patterns:
            return 1.0 if self.detected_patterns else 0.0
        
        matched = sum(1 for pattern in self.test_case.expected_patterns 
                     if pattern in self.detected_patterns)
        return matched / len(self.test_case.expected_patterns)


@dataclass
class CharacterPatternTestResult:
    """Complete pattern testing result for a character."""
    file_path: str
    character_name: str
    parsing_success: bool
    test_results: List[PatternTestResult] = field(default_factory=list)
    pattern_coverage: float = 0.0
    conversation_flow_working: bool = False
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall pattern detection success rate."""
        if not self.test_results:
            return 0.0
        
        return sum(result.pattern_match_score for result in self.test_results) / len(self.test_results)
    
    @property
    def working_tests(self) -> int:
        """Count of successful test cases."""
        return sum(1 for result in self.test_results if result.success)


class CDLPatternTester:
    """
    Specialized CDL pattern tester for conversation flow validation.
    
    Usage:
        tester = CDLPatternTester()
        result = tester.test_character_patterns('path/to/character.json')
        tester.print_pattern_report(result)
    """
    
    def __init__(self):
        """Initialize the pattern tester."""
        self.cdl_integration = CDLAIPromptIntegration()
        
        # Standard test cases applicable to most characters
        self.standard_test_cases = [
            PatternTestCase(
                test_message="consciousness expansion",
                expected_patterns=["mystical", "transcendent", "spiritual"],
                expected_keywords=["consciousness", "expansion", "transcendent"],
                description="Spiritual/mystical content detection"
            ),
            PatternTestCase(
                test_message="had a dream last night",
                expected_patterns=["dream", "sleep", "vision"],
                expected_keywords=["dream", "sleep", "night"],
                description="Dream and sleep-related content"
            ),
            PatternTestCase(
                test_message="you have beautiful eyes",
                expected_patterns=["romantic", "compliment", "attractive"],
                expected_keywords=["beautiful", "eyes", "attractive"],
                description="Romantic/compliment detection"
            ),
            PatternTestCase(
                test_message="can you teach me about science",
                expected_patterns=["education", "learning", "academic"],
                expected_keywords=["teach", "learn", "science"],
                description="Educational content detection"
            ),
            PatternTestCase(
                test_message="marine biology is fascinating",
                expected_patterns=["science", "environmental", "ocean"],
                expected_keywords=["marine", "biology", "science"],
                description="Scientific field recognition"
            ),
            PatternTestCase(
                test_message="let's code together",
                expected_patterns=["collaboration", "creative", "programming"],
                expected_keywords=["code", "together", "programming"],
                description="Collaborative coding detection"
            ),
            PatternTestCase(
                test_message="what's your favorite game",
                expected_patterns=["game", "development", "entertainment"],
                expected_keywords=["game", "favorite", "play"],
                description="Gaming discussion detection"
            )
        ]
        
        # Character-specific test cases
        self.character_specific_tests = {
            'gabriel': [
                PatternTestCase(
                    test_message="I need spiritual guidance",
                    expected_patterns=["spiritual", "guidance", "divine"],
                    expected_keywords=["spiritual", "guidance", "divine"],
                    character_specific=True,
                    description="Gabriel spiritual guidance"
                ),
                PatternTestCase(
                    test_message="questions about faith",
                    expected_patterns=["faith", "theological", "religious"],
                    expected_keywords=["faith", "religious", "theological"],
                    character_specific=True,
                    description="Gabriel faith discussions"
                ),
                PatternTestCase(
                    test_message="theological discussion",
                    expected_patterns=["theological", "discussion", "divine"],
                    expected_keywords=["theological", "discussion"],
                    character_specific=True,
                    description="Gabriel theological content"
                )
            ],
            'elena': [
                PatternTestCase(
                    test_message="ocean conservation efforts",
                    expected_patterns=["environmental", "conservation", "marine"],
                    expected_keywords=["ocean", "conservation", "marine"],
                    character_specific=True,
                    description="Elena marine biology expertise"
                ),
                PatternTestCase(
                    test_message="coral reef research",
                    expected_patterns=["research", "marine", "environmental"],
                    expected_keywords=["coral", "reef", "research"],
                    character_specific=True,
                    description="Elena research specialization"
                )
            ],
            'marcus': [
                PatternTestCase(
                    test_message="artificial intelligence research",
                    expected_patterns=["research", "academic", "technical"],
                    expected_keywords=["artificial", "intelligence", "research"],
                    character_specific=True,
                    description="Marcus AI expertise"
                ),
                PatternTestCase(
                    test_message="machine learning algorithms",
                    expected_patterns=["technical", "academic", "research"],
                    expected_keywords=["machine", "learning", "algorithms"],
                    character_specific=True,
                    description="Marcus technical discussions"
                )
            ],
            'jake': [
                PatternTestCase(
                    test_message="game development process",
                    expected_patterns=["development", "creative", "technical"],
                    expected_keywords=["game", "development", "process"],
                    character_specific=True,
                    description="Jake game development"
                ),
                PatternTestCase(
                    test_message="indie game design",
                    expected_patterns=["creative", "development", "design"],
                    expected_keywords=["indie", "game", "design"],
                    character_specific=True,
                    description="Jake indie focus"
                )
            ],
            'dream': [
                PatternTestCase(
                    test_message="realm of dreams and nightmares",
                    expected_patterns=["dream", "mystical", "transcendent"],
                    expected_keywords=["realm", "dreams", "nightmares"],
                    character_specific=True,
                    description="Dream mythological nature"
                ),
                PatternTestCase(
                    test_message="stories and imagination",
                    expected_patterns=["creative", "mystical", "storytelling"],
                    expected_keywords=["stories", "imagination", "creative"],
                    character_specific=True,
                    description="Dream storytelling focus"
                )
            ]
        }
    
    def test_character_patterns(self, file_path: Union[str, Path]) -> CharacterPatternTestResult:
        """
        Test pattern detection for a specific character.
        
        Args:
            file_path: Path to the CDL JSON file
            
        Returns:
            CharacterPatternTestResult with detailed pattern analysis
        """
        file_path = Path(file_path)
        
        # Initialize result
        result = CharacterPatternTestResult(
            file_path=str(file_path),
            character_name="Unknown",
            parsing_success=False
        )
        
        # Load character
        try:
            character = load_character(str(file_path))
            result.character_name = character.identity.name
            result.parsing_success = True
        except Exception as e:
            result.issues.append(f"Failed to load character: {e}")
            return result
        
        # Determine test cases to use
        character_key = self._get_character_key(file_path.name)
        test_cases = self.standard_test_cases.copy()
        
        # Add character-specific tests if available
        if character_key in self.character_specific_tests:
            test_cases.extend(self.character_specific_tests[character_key])
        
        # Run pattern detection tests
        test_results = []
        for test_case in test_cases:
            test_result = self._run_pattern_test(character, test_case)
            test_results.append(test_result)
        
        result.test_results = test_results
        
        # Calculate metrics
        result.pattern_coverage = self._calculate_pattern_coverage(test_results)
        result.conversation_flow_working = result.working_tests > 0
        
        # Generate analysis
        result.issues.extend(self._identify_pattern_issues(test_results))
        result.recommendations.extend(self._generate_pattern_recommendations(result))
        
        return result
    
    def _get_character_key(self, filename: str) -> str:
        """Extract character key from filename for specific test matching."""
        filename = filename.lower()
        
        # Character name mappings
        character_mappings = {
            'gabriel': 'gabriel',
            'elena': 'elena',
            'marcus': 'marcus', 
            'jake': 'jake',
            'dream': 'dream',
            'aethys': 'aethys',
            'ryan': 'ryan',
            'sophia': 'sophia'
        }
        
        for key, char_key in character_mappings.items():
            if key in filename:
                return char_key
        
        return 'unknown'
    
    def _run_pattern_test(self, character, test_case: PatternTestCase) -> PatternTestResult:
        """Run a single pattern detection test."""
        result = PatternTestResult(test_case=test_case)
        
        try:
            # Use the CDL integration to detect patterns
            scenarios = self.cdl_integration._detect_communication_scenarios(
                test_case.test_message, character, 'test_user_id'
            )
            
            if scenarios:
                result.detected_patterns = list(scenarios.keys())
                result.success = True
                result.response_quality = self._assess_response_quality(scenarios)
            else:
                result.success = False
                result.issues.append("No patterns detected")
        
        except Exception as e:
            result.success = False
            result.issues.append(f"Pattern detection failed: {e}")
        
        return result
    
    def _assess_response_quality(self, scenarios: Dict) -> str:
        """Assess the quality of detected scenarios."""
        if not scenarios:
            return "NONE"
        
        scenario_count = len(scenarios)
        total_guidance_length = sum(len(str(guidance)) for guidance in scenarios.values())
        
        if scenario_count >= 3 and total_guidance_length > 200:
            return "EXCELLENT"
        elif scenario_count >= 2 and total_guidance_length > 100:
            return "GOOD"
        elif scenario_count >= 1 and total_guidance_length > 50:
            return "BASIC"
        else:
            return "MINIMAL"
    
    def _calculate_pattern_coverage(self, test_results: List[PatternTestResult]) -> float:
        """Calculate pattern detection coverage percentage."""
        if not test_results:
            return 0.0
        
        total_score = sum(result.pattern_match_score for result in test_results)
        return (total_score / len(test_results)) * 100
    
    def _identify_pattern_issues(self, test_results: List[PatternTestResult]) -> List[str]:
        """Identify common pattern detection issues."""
        issues = []
        
        failed_tests = [r for r in test_results if not r.success]
        if len(failed_tests) > len(test_results) * 0.5:
            issues.append("Pattern detection failing for majority of test cases")
        
        no_patterns = [r for r in test_results if not r.detected_patterns]
        if len(no_patterns) > len(test_results) * 0.3:
            issues.append("Many tests not detecting any patterns - check message_pattern_triggers")
        
        low_quality = [r for r in test_results if r.response_quality in ['MINIMAL', 'NONE']]
        if len(low_quality) > len(test_results) * 0.4:
            issues.append("Low quality pattern responses - enhance conversation_flow_guidance")
        
        return issues
    
    def _generate_pattern_recommendations(self, result: CharacterPatternTestResult) -> List[str]:
        """Generate recommendations for improving pattern detection."""
        recommendations = []
        success_rate = result.overall_success_rate
        
        if success_rate < 0.3:
            recommendations.append("🔧 Major pattern system issues - verify message_pattern_triggers structure")
            recommendations.append("📝 Ensure conversation_flow_guidance matches trigger patterns")
        elif success_rate < 0.6:
            recommendations.append("⚡ Improve pattern detection by adding more specific trigger keywords")
            recommendations.append("🎯 Enhance conversation_flow_guidance with detailed response strategies")
        elif success_rate < 0.8:
            recommendations.append("✨ Fine-tune existing patterns for better coverage")
            recommendations.append("🔍 Add character-specific pattern triggers for domain expertise")
        else:
            recommendations.append("🎉 Pattern detection working well - consider advanced conversation features")
        
        # Character-specific recommendations
        character_key = self._get_character_key(Path(result.file_path).name)
        if character_key in self.character_specific_tests:
            char_specific_results = [r for r in result.test_results if r.test_case.character_specific]
            if char_specific_results:
                char_success = sum(r.pattern_match_score for r in char_specific_results) / len(char_specific_results)
                if char_success < 0.5:
                    recommendations.append(f"🎭 Improve {character_key.title()}-specific pattern detection for domain expertise")
        
        return recommendations
    
    def test_batch_patterns(self, directory_path: Union[str, Path], 
                           pattern: str = "*.json") -> List[CharacterPatternTestResult]:
        """
        Test pattern detection for multiple characters in a directory.
        
        Args:
            directory_path: Path to directory containing CDL files
            pattern: File pattern to match
            
        Returns:
            List of CharacterPatternTestResult objects
        """
        directory_path = Path(directory_path)
        results = []
        
        if not directory_path.exists():
            return results
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file():
                result = self.test_character_patterns(file_path)
                results.append(result)
        
        return results
    
    def print_pattern_report(self, result: CharacterPatternTestResult, verbose: bool = False):
        """
        Print a detailed pattern testing report.
        
        Args:
            result: CharacterPatternTestResult to report on
            verbose: Include detailed test case information
        """
        print(f"\n🔍 PATTERN TESTING: {result.character_name}")
        print("=" * 60)
        
        # Overall metrics
        print(f"📊 Overall Success Rate: {result.overall_success_rate:.1%}")
        print(f"📊 Pattern Coverage: {result.pattern_coverage:.1f}%")
        print(f"📊 Working Tests: {result.working_tests}/{len(result.test_results)}")
        print(f"📊 Conversation Flow: {'✅ Working' if result.conversation_flow_working else '❌ Issues'}")
        
        # Test results summary
        if verbose and result.test_results:
            print(f"\n📋 Test Results:")
            
            for i, test_result in enumerate(result.test_results, 1):
                status = "✅" if test_result.success else "❌"
                print(f"   {i:2d}. {status} {test_result.test_case.description}")
                print(f"       Message: '{test_result.test_case.test_message}'")
                
                if test_result.detected_patterns:
                    print(f"       Detected: {', '.join(test_result.detected_patterns)}")
                else:
                    print(f"       Detected: None")
                
                if test_result.issues:
                    for issue in test_result.issues:
                        print(f"       ⚠️  {issue}")
                print()
        
        # Issues and recommendations
        if result.issues:
            print(f"\n⚠️ Issues Identified:")
            for issue in result.issues:
                print(f"   • {issue}")
        
        if result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   • {rec}")
        
        print()
    
    def print_batch_summary(self, results: List[CharacterPatternTestResult]):
        """Print a summary report for batch pattern testing."""
        if not results:
            print("No pattern test results to report.")
            return
        
        print(f"\n🎯 PATTERN TESTING BATCH SUMMARY")
        print("=" * 80)
        
        total = len(results)
        avg_success = sum(r.overall_success_rate for r in results) / total
        avg_coverage = sum(r.pattern_coverage for r in results) / total
        working_flow = sum(1 for r in results if r.conversation_flow_working)
        
        print(f"📊 Characters Tested: {total}")
        print(f"📊 Average Success Rate: {avg_success:.1%}")
        print(f"📊 Average Pattern Coverage: {avg_coverage:.1f}%")
        print(f"📊 Working Conversation Flow: {working_flow}/{total}")
        
        # Performance ranking
        print(f"\n🏆 Pattern Detection Performance:")
        sorted_results = sorted(results, key=lambda r: r.overall_success_rate, reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            status_emoji = "✅" if result.conversation_flow_working else "❌"
            print(f"   {i:2d}. {status_emoji} {result.character_name:<20} - {result.overall_success_rate:.1%} success, {result.working_tests:2d} working tests")
        
        # Common issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        if all_issues:
            from collections import defaultdict
            issue_counts = defaultdict(int)
            for issue in all_issues:
                issue_counts[issue] += 1
            
            print(f"\n🔍 Most Common Issues:")
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"   • {issue} ({count} characters)")
        
        print()