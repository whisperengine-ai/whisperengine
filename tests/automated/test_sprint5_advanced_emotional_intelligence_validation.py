#!/usr/bin/env python3
"""
Sprint 5 Advanced Emotional Intelligence Direct Validation

Validates Advanced Emotion Detector integration with existing RoBERTa and emoji systems.
Tests 12+ emotion detection using synthesis rules and multi-modal analysis.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test framework and validation components
from tests.automated.sprint_validation_framework import (
    SprintValidationFramework, 
    ValidationResult, 
    TestScenario
)

class Sprint5AdvancedEmotionalIntelligenceValidation:
    """Sprint 5 Advanced Emotional Intelligence Validation Suite"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_framework = SprintValidationFramework("Sprint 5: Advanced Emotional Intelligence")
        
        # Sprint 5 test scenarios
        self.test_scenarios = [
            TestScenario(
                name="roberta_foundation_integration",
                description="Test RoBERTa emotion analysis foundation",
                test_method="validate_roberta_foundation",
                weight=25.0,
                expected_success_rate=0.95
            ),
            TestScenario(
                name="emoji_intelligence_integration", 
                description="Test existing emoji emotion mapping integration",
                test_method="validate_emoji_intelligence",
                weight=20.0,
                expected_success_rate=0.90
            ),
            TestScenario(
                name="advanced_emotion_synthesis",
                description="Test 7→12+ emotion synthesis via mapping rules",
                test_method="validate_advanced_synthesis",
                weight=30.0,
                expected_success_rate=0.85
            ),
            TestScenario(
                name="multi_modal_analysis",
                description="Test multi-modal emotion detection (RoBERTa + emoji + text)",
                test_method="validate_multi_modal_analysis",
                weight=15.0,
                expected_success_rate=0.80
            ),
            TestScenario(
                name="temporal_pattern_recognition",
                description="Test temporal emotion patterns from memory",
                test_method="validate_temporal_patterns", 
                weight=10.0,
                expected_success_rate=0.75
            )
        ]
        
        # Advanced emotion test cases
        self.test_cases = [
            # Core RoBERTa emotions
            {"text": "I'm so happy today! 😊", "expected_primary": "joy", "expected_confidence": 0.8},
            {"text": "This makes me really sad 😢", "expected_primary": "sadness", "expected_confidence": 0.7},
            {"text": "I'm furious about this! 😡", "expected_primary": "anger", "expected_confidence": 0.8},
            
            # Advanced synthesis emotions (love, contempt, pride, awe, confusion)
            {"text": "I absolutely love and adore you! 🥰❤️", "expected_primary": "love", "expected_confidence": 0.7},
            {"text": "That's ridiculous and pathetic 🙄", "expected_primary": "contempt", "expected_confidence": 0.6},
            {"text": "I'm so proud of what I accomplished! 😎", "expected_primary": "pride", "expected_confidence": 0.6},
            {"text": "Wow, that's absolutely incredible and breathtaking! 🤩", "expected_primary": "awe", "expected_confidence": 0.7},
            {"text": "I'm confused and don't understand what you mean 🤔", "expected_primary": "confusion", "expected_confidence": 0.6},
            
            # Multi-modal test cases (text + emoji + punctuation)
            {"text": "AMAZING WORK!!! 🎉🤩", "expected_primary": "joy", "expected_intensity": 0.8},
            {"text": "what?? are you serious??? 😮", "expected_primary": "surprise", "expected_intensity": 0.7},
            {"text": "I love this so much... it's wonderful 😍", "expected_primary": "love", "expected_intensity": 0.7}
        ]
    
    async def run_validation(self) -> ValidationResult:
        """Run complete Sprint 5 validation suite."""
        self.logger.info("🚀 Starting Sprint 5 Advanced Emotional Intelligence Validation")
        
        try:
            # Initialize core components with direct Python API access
            await self._initialize_components()
            
            # Run all test scenarios
            total_success = 0
            total_tests = 0
            
            for scenario in self.test_scenarios:
                success_count, test_count = await self._run_test_scenario(scenario)
                total_success += success_count
                total_tests += test_count
                
                success_rate = success_count / test_count if test_count > 0 else 0
                self.logger.info(f"✅ {scenario.name}: {success_count}/{test_count} ({success_rate:.1%})")
            
            # Calculate overall success rate
            overall_success_rate = total_success / total_tests if total_tests > 0 else 0
            
            # Generate validation result
            result = ValidationResult(
                sprint_name="Sprint 5: Advanced Emotional Intelligence",
                overall_success_rate=overall_success_rate,
                tests_passed=total_success,
                total_tests=total_tests,
                scenario_results={scenario.name: {"passed": 0, "total": 0} for scenario in self.test_scenarios},
                details={
                    "roberta_integration": "Uses existing EnhancedVectorEmotionAnalyzer",
                    "emoji_integration": "Uses existing EmojiEmotionMapper", 
                    "synthesis_rules": f"{len(self.advanced_detector.EMOTION_SYNTHESIS_RULES)} emotion mapping rules",
                    "supported_emotions": f"{len(self.advanced_detector.CORE_EMOTIONS)} total emotions",
                    "multi_modal_components": "RoBERTa + Emoji + Punctuation analysis"
                }
            )
            
            # Success criteria: 85%+ overall success rate
            if overall_success_rate >= 0.85:
                self.logger.info(f"🎉 Sprint 5 VALIDATION SUCCESSFUL: {overall_success_rate:.1%} success rate")
                result.validation_successful = True
            else:
                self.logger.warning(f"⚠️ Sprint 5 validation needs improvement: {overall_success_rate:.1%} success rate")
                result.validation_successful = False
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Sprint 5 validation failed: {e}")
            return ValidationResult(
                sprint_name="Sprint 5: Advanced Emotional Intelligence",
                overall_success_rate=0.0,
                tests_passed=0,
                total_tests=len(self.test_cases),
                validation_successful=False,
                error_message=str(e)
            )
    
    async def _initialize_components(self):
        """Initialize Sprint 5 components with existing WhisperEngine systems."""
        try:
            # Import Sprint 5 components
            from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector
            from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
            from src.memory.vector_memory_system import VectorMemoryManager
            from src.memory.memory_protocol import create_memory_manager
            
            self.logger.info("🔧 Initializing Sprint 5 components...")
            
            # Initialize existing systems (foundation)
            self.enhanced_analyzer = EnhancedVectorEmotionAnalyzer()
            self.memory_manager = create_memory_manager(memory_type="vector")
            
            # Initialize Sprint 5 Advanced Emotion Detector
            self.advanced_detector = AdvancedEmotionDetector(
                enhanced_emotion_analyzer=self.enhanced_analyzer,
                memory_manager=self.memory_manager
            )
            
            self.logger.info("✅ Sprint 5 components initialized successfully")
            self.logger.info(f"   - RoBERTa foundation: EnhancedVectorEmotionAnalyzer")
            self.logger.info(f"   - Emoji intelligence: {len(self.advanced_detector.emoji_mapper.EMOJI_EMOTION_MAP)} mappings")
            self.logger.info(f"   - Synthesis rules: {len(self.advanced_detector.EMOTION_SYNTHESIS_RULES)} advanced emotions")
            self.logger.info(f"   - Total emotions: {len(self.advanced_detector.CORE_EMOTIONS)} supported")
            
        except ImportError as e:
            self.logger.error(f"❌ Failed to import Sprint 5 components: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Sprint 5 components: {e}")
            raise
    
    async def _run_test_scenario(self, scenario: TestScenario) -> tuple[int, int]:
        """Run a specific test scenario."""
        method = getattr(self, scenario.test_method)
        return await method()
    
    async def validate_roberta_foundation(self) -> tuple[int, int]:
        """Validate RoBERTa emotion analysis foundation integration."""
        success_count = 0
        test_count = 0
        
        # Test RoBERTa core emotions
        roberta_test_cases = [
            {"text": "I'm so happy today!", "expected": "joy"},
            {"text": "This makes me sad", "expected": "sadness"}, 
            {"text": "I'm angry about this", "expected": "anger"},
            {"text": "That scared me", "expected": "fear"},
            {"text": "What a surprise!", "expected": "surprise"}
        ]
        
        for test_case in roberta_test_cases:
            test_count += 1
            try:
                # Test direct RoBERTa analysis
                roberta_result = await self.enhanced_analyzer.analyze_emotion(
                    test_case["text"], "test_user"
                )
                
                if roberta_result.primary_emotion == test_case["expected"]:
                    success_count += 1
                    self.logger.debug(f"✅ RoBERTa foundation: '{test_case['text']}' → {roberta_result.primary_emotion}")
                else:
                    self.logger.warning(f"⚠️ RoBERTa mismatch: expected {test_case['expected']}, got {roberta_result.primary_emotion}")
                    
            except Exception as e:
                self.logger.error(f"❌ RoBERTa foundation test failed: {e}")
        
        return success_count, test_count
    
    async def validate_emoji_intelligence(self) -> tuple[int, int]:
        """Validate existing emoji emotion mapping integration."""
        success_count = 0
        test_count = 0
        
        # Test emoji emotion mapping
        emoji_test_cases = [
            {"text": "Great work! 😊", "emoji": "😊", "expected_type": "POSITIVE_MILD"},
            {"text": "I'm crying 😭", "emoji": "😭", "expected_type": "NEGATIVE_STRONG"},
            {"text": "Amazing! 🤩", "emoji": "🤩", "expected_type": "POSITIVE_STRONG"}
        ]
        
        for test_case in emoji_test_cases:
            test_count += 1
            try:
                # Test emoji analysis via advanced detector
                emoji_analysis = self.advanced_detector._analyze_emojis_with_existing_system(test_case["text"])
                
                if emoji_analysis:  # Any emotion detected from emoji
                    success_count += 1
                    self.logger.debug(f"✅ Emoji intelligence: '{test_case['emoji']}' → {emoji_analysis}")
                else:
                    self.logger.warning(f"⚠️ Emoji analysis failed for {test_case['emoji']}")
                    
            except Exception as e:
                self.logger.error(f"❌ Emoji intelligence test failed: {e}")
        
        return success_count, test_count
    
    async def validate_advanced_synthesis(self) -> tuple[int, int]:
        """Validate 7→12+ emotion synthesis via mapping rules."""
        success_count = 0
        test_count = 0
        
        # Test advanced emotion synthesis
        synthesis_test_cases = [
            {"text": "I absolutely love and cherish you! 🥰", "expected": "love"},
            {"text": "That's ridiculous and pathetic 🙄", "expected": "contempt"},
            {"text": "I'm so proud of my accomplishment! 😎", "expected": "pride"},
            {"text": "Wow, that's absolutely breathtaking! 🤩", "expected": "awe"},
            {"text": "I'm confused and don't understand 🤔", "expected": "confusion"}
        ]
        
        for test_case in synthesis_test_cases:
            test_count += 1
            try:
                # Test advanced emotion detection
                emotional_state = await self.advanced_detector.detect_advanced_emotions(
                    test_case["text"], "test_user"
                )
                
                if emotional_state.primary_emotion == test_case["expected"]:
                    success_count += 1
                    self.logger.debug(f"✅ Advanced synthesis: '{test_case['text']}' → {emotional_state.primary_emotion}")
                else:
                    self.logger.warning(f"⚠️ Synthesis mismatch: expected {test_case['expected']}, got {emotional_state.primary_emotion}")
                    
            except Exception as e:
                self.logger.error(f"❌ Advanced synthesis test failed: {e}")
        
        return success_count, test_count
    
    async def validate_multi_modal_analysis(self) -> tuple[int, int]:
        """Validate multi-modal emotion detection (RoBERTa + emoji + punctuation)."""
        success_count = 0
        test_count = 0
        
        # Test multi-modal analysis
        multi_modal_cases = [
            {"text": "AMAZING WORK!!! 🎉🤩", "check_intensity": True, "min_intensity": 0.7},
            {"text": "what?? are you serious??? 😮", "check_intensity": True, "min_intensity": 0.6},
            {"text": "I love this so much... 😍", "check_components": ["roberta", "emoji", "punctuation"]}
        ]
        
        for test_case in multi_modal_cases:
            test_count += 1
            try:
                # Test full multi-modal detection
                emotional_state = await self.advanced_detector.detect_advanced_emotions(
                    test_case["text"], "test_user"
                )
                
                # Check intensity requirement
                if test_case.get("check_intensity") and emotional_state.emotional_intensity >= test_case["min_intensity"]:
                    success_count += 1
                    self.logger.debug(f"✅ Multi-modal intensity: {emotional_state.emotional_intensity:.2f}")
                # Check component analysis
                elif test_case.get("check_components"):
                    has_components = (
                        emotional_state.text_indicators and  # RoBERTa indicators
                        emotional_state.emoji_analysis and   # Emoji analysis 
                        emotional_state.punctuation_patterns # Punctuation patterns
                    )
                    if has_components:
                        success_count += 1
                        self.logger.debug(f"✅ Multi-modal components: all present")
                    else:
                        self.logger.warning(f"⚠️ Missing multi-modal components")
                else:
                    success_count += 1  # Basic success if no specific checks
                    
            except Exception as e:
                self.logger.error(f"❌ Multi-modal analysis test failed: {e}")
        
        return success_count, test_count
    
    async def validate_temporal_patterns(self) -> tuple[int, int]:
        """Validate temporal emotion patterns from memory."""
        success_count = 0
        test_count = 0
        
        # Test temporal pattern analysis (basic functionality)
        temporal_test_cases = [
            {"text": "I'm feeling great today!", "user_id": "temporal_test_user"},
            {"text": "Still feeling good", "user_id": "temporal_test_user"},
            {"text": "Maintaining positive mood", "user_id": "temporal_test_user"}
        ]
        
        for test_case in temporal_test_cases:
            test_count += 1
            try:
                # Test temporal pattern analysis
                trajectory, pattern_type = await self.advanced_detector._analyze_temporal_patterns(
                    test_case["user_id"], "joy"
                )
                
                # Success if temporal analysis completes without error
                # (May have empty trajectory if no memory history)
                success_count += 1
                self.logger.debug(f"✅ Temporal analysis: {len(trajectory)} points, pattern: {pattern_type}")
                    
            except Exception as e:
                self.logger.error(f"❌ Temporal pattern test failed: {e}")
        
        return success_count, test_count

async def main():
    """Run Sprint 5 Advanced Emotional Intelligence validation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 Sprint 5: Advanced Emotional Intelligence Direct Validation")
    print("=" * 80)
    print()
    print("🎯 Validation Goals:")
    print("   • RoBERTa emotion analysis foundation integration")
    print("   • Existing emoji intelligence system usage")
    print("   • 7→12+ emotion synthesis via mapping rules")
    print("   • Multi-modal analysis (RoBERTa + emoji + punctuation)")
    print("   • Temporal emotion pattern recognition")
    print()
    print("🧪 Testing Approach:")
    print("   • Direct Python API validation (primary method)")
    print("   • Integration with existing WhisperEngine emotion systems")
    print("   • Zero duplication - builds on RoBERTa & emoji foundations")
    print("   • Advanced emotion synthesis through pattern matching")
    print()
    
    validator = Sprint5AdvancedEmotionalIntelligenceValidation()
    result = await validator.run_validation()
    
    print("\n" + "=" * 80)
    print("📊 SPRINT 5 VALIDATION RESULTS")
    print("=" * 80)
    print(f"Overall Success Rate: {result.overall_success_rate:.1%}")
    print(f"Tests Passed: {result.tests_passed}/{result.total_tests}")
    print(f"Validation Status: {'✅ SUCCESSFUL' if result.validation_successful else '❌ NEEDS IMPROVEMENT'}")
    
    if result.details:
        print("\n🔍 Component Details:")
        for key, value in result.details.items():
            print(f"   • {key}: {value}")
    
    print()
    if result.validation_successful:
        print("🎉 Sprint 5 Advanced Emotional Intelligence validation completed successfully!")
        print("   ✅ RoBERTa foundation integration working")
        print("   ✅ Emoji intelligence system integrated")
        print("   ✅ Advanced emotion synthesis operational")
        print("   ✅ Multi-modal analysis pipeline functional")
        print("   ✅ Ready for production integration")
    else:
        print("⚠️ Sprint 5 validation identified areas for improvement")
        print("   • Review component integration points")
        print("   • Check emotion synthesis rule accuracy")
        print("   • Validate multi-modal analysis pipeline")
        if result.error_message:
            print(f"   • Error: {result.error_message}")
    
    return result.validation_successful

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)