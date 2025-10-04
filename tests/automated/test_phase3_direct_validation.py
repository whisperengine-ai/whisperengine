#!/usr/bin/env python3
"""
Phase 3 Intelligence Direct Validation Suite

Tests Phase 3 features using direct Python calls to internal APIs instead of HTTP requests.
This provides more reliable testing without network timeouts and direct access to all data structures.

Phase 3 Features:
- Enhanced emotion analysis with vector integration
- Personality-aware responses
- Context-aware emoji reactions
- Memory-enhanced conversation continuity
- Relationship depth analysis
"""

import asyncio
import sys
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import MessageProcessor and related classes
from src.core.message_processor import MessageProcessor, MessageContext, ProcessingResult, create_message_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3DirectValidationSuite:
    """Direct validation of Phase 3 features using internal Python APIs."""
    
    def __init__(self):
        self.message_processor = None
        self.MessageContext = None
        self.test_user_id = "test_user_phase3_direct"
        
    async def initialize(self):
        """Initialize the direct validation environment."""
        logger.info("🔧 Initializing Phase 3 core components...")
        
        try:
            # Import and initialize core components
            from src.memory.memory_protocol import create_memory_manager
            from src.llm.llm_protocol import create_llm_client
            
            logger.info("🔧 Initializing core components...")
            
            # Create memory manager with correct port
            memory_manager = create_memory_manager(memory_type="vector")
            logger.info("✅ Memory manager created")
            
            # Create LLM client
            llm_client = create_llm_client(llm_client_type="openrouter")
            logger.info("✅ LLM client created")
            
            # Use the factory to create a proper MessageProcessor
            self.message_processor = create_message_processor(
                bot_core=None,  # We'll skip bot_core initialization for direct testing
                memory_manager=memory_manager,
                llm_client=llm_client
            )
            logger.info("✅ Message processor created using factory")
            
            # Store MessageContext for later use
            self.MessageContext = MessageContext
            
            return True
            
        except Exception as e:
            logger.error("❌ Initialization failed: %s", e)
            import traceback
            logger.error("Traceback: %s", traceback.format_exc())
            return False
    
    async def test_phase3_feature(self, message: str, test_name: str) -> Dict[str, Any]:
        """Test a specific Phase 3 feature using direct message processing."""
        logger.info("🧪 TEST: %s", test_name)
        logger.info("📤 MESSAGE: %s", message)
        
        try:
            # Create message context
            message_context = self.MessageContext(
                user_id=self.test_user_id,
                content=message,
                platform="direct_test"
            )
            
            # Process message directly
            start_time = datetime.now()
            processing_result = await self.message_processor.process_message(message_context)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            # Extract AI components from metadata
            metadata = processing_result.metadata or {}
            ai_components = metadata.get('ai_components', {})
            
            # Analyze Phase 3 features
            analysis = self._analyze_phase3_features(ai_components, processing_result.response)
            
            result = {
                'test_name': test_name,
                'success': processing_result.success,
                'response': processing_result.response,
                'processing_time_ms': processing_time,
                'ai_components': ai_components,
                'analysis': analysis,
                'metadata': metadata
            }
            
            self._log_analysis_results(analysis, test_name)
            return result
            
        except Exception as e:
            logger.error("❌ Test failed: %s", e)
            import traceback
            logger.error("Traceback: %s", traceback.format_exc())
            return {
                'test_name': test_name,
                'success': False,
                'error': str(e),
                'analysis': self._create_empty_analysis()
            }

    def _analyze_phase3_features(self, ai_components: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Analyze Phase 3 intelligence features in the AI components data."""
        analysis = {
            'features_detected': {},
            'phase3_present': False,
            'total_features': 0,
            'quality_scores': {}
        }
        
        # Feature 1: Enhanced Emotion Analysis
        emotion_analysis = ai_components.get('emotion_analysis')
        if emotion_analysis:
            analysis['features_detected']['enhanced_emotion_analysis'] = {
                'present': True,
                'has_emotions': bool(emotion_analysis.get('emotions')),
                'has_confidence': 'confidence' in emotion_analysis,
                'vector_enhanced': emotion_analysis.get('vector_enhanced', False),
                'emotion_count': len(emotion_analysis.get('emotions', []))
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
        
        # Feature 2: Personality Analysis
        personality_analysis = ai_components.get('personality_analysis')
        if personality_analysis:
            analysis['features_detected']['personality_analysis'] = {
                'present': True,
                'has_traits': bool(personality_analysis.get('traits')),
                'has_big_five': 'big_five' in personality_analysis,
                'trait_count': len(personality_analysis.get('traits', []))
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
            
        # Feature 3: Context Analysis
        context_analysis = ai_components.get('context_analysis')
        if context_analysis:
            analysis['features_detected']['context_analysis'] = {
                'present': True,
                'has_patterns': bool(context_analysis.get('patterns')),
                'has_themes': bool(context_analysis.get('themes')),
                'context_type': context_analysis.get('context_type', 'unknown')
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
            
        # Feature 4: Emoji Intelligence (check for emoji reactions or suggestions)
        emoji_data = ai_components.get('emoji_intelligence') or ai_components.get('emoji_analysis')
        if emoji_data or '😊' in response or '😢' in response or '🤔' in response:
            analysis['features_detected']['emoji_intelligence'] = {
                'present': True,
                'has_emoji_data': emoji_data is not None,
                'response_has_emojis': any(char in response for char in '😊😢🤔❤️💡🌟⚡🎯🔥💪🌈'),
                'emoji_count': sum(1 for char in response if ord(char) > 0x1F600)
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
            
        # Feature 5: Memory Enhancement Detection
        memory_context = ai_components.get('memory_context') or ai_components.get('relevant_memories')
        if memory_context:
            analysis['features_detected']['memory_enhancement'] = {
                'present': True,
                'has_memories': bool(memory_context),
                'memory_type': type(memory_context).__name__,
                'enhanced_retrieval': 'enhanced' in str(memory_context).lower()
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
            
        # Feature 6: Relationship Depth (check for user relationship data)
        relationship_data = ai_components.get('relationship_analysis') or ai_components.get('user_profile')
        if relationship_data:
            analysis['features_detected']['relationship_depth'] = {
                'present': True,
                'has_relationship_data': relationship_data is not None,
                'relationship_type': relationship_data.get('type', 'unknown') if isinstance(relationship_data, dict) else 'data_present'
            }
            analysis['total_features'] += 1
            analysis['phase3_present'] = True
            
        # Calculate quality scores
        analysis['quality_scores'] = {
            'feature_coverage': analysis['total_features'] / 6.0,  # Out of 6 possible features
            'emotional_intelligence': 1.0 if emotion_analysis else 0.0,
            'personality_awareness': 1.0 if personality_analysis else 0.0,
            'context_understanding': 1.0 if context_analysis else 0.0
        }
        
        return analysis

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis structure for failed tests."""
        return {
            'features_detected': {},
            'phase3_present': False,
            'total_features': 0,
            'quality_scores': {
                'feature_coverage': 0.0,
                'emotional_intelligence': 0.0,
                'personality_awareness': 0.0,
                'context_understanding': 0.0
            }
        }

    def _log_analysis_results(self, analysis: Dict[str, Any], test_name: str):
        """Log detailed analysis results."""
        logger.info("🔍 ANALYSIS RESULTS for %s:", test_name)
        logger.info("   Phase 3 Present: %s", analysis['phase3_present'])
        logger.info("   Features Detected: %d/6", analysis['total_features'])
        
        for feature_name, feature_data in analysis['features_detected'].items():
            logger.info("   ✅ %s: %s", feature_name.replace('_', ' ').title(), feature_data)
            
        quality = analysis['quality_scores']
        logger.info("   📊 Quality Scores:")
        logger.info("      Feature Coverage: %.1f%%", quality['feature_coverage'] * 100)
        logger.info("      Emotional Intelligence: %.1f%%", quality['emotional_intelligence'] * 100)
        logger.info("      Personality Awareness: %.1f%%", quality['personality_awareness'] * 100)
        logger.info("      Context Understanding: %.1f%%", quality['context_understanding'] * 100)

    async def run_comprehensive_tests(self) -> bool:
        """Run comprehensive Phase 3 intelligence validation tests."""
        logger.info("🚀 STARTING COMPREHENSIVE PHASE 3 VALIDATION")
        logger.info("=" * 60)
        
        test_scenarios = [
            {
                'message': "I'm feeling really anxious about my upcoming presentation. I tend to overthink things and get stressed easily.",
                'test_name': "Phase 3.1: Emotion + Personality Analysis"
            },
            {
                'message': "Can you help me understand this complex topic? I learn best with examples and visual metaphors.",
                'test_name': "Phase 3.2: Learning Style Detection"
            },
            {
                'message': "I'm excited about this new project! 🎉 It combines my passion for marine biology with technology.",
                'test_name': "Phase 3.3: Emoji + Context Intelligence"
            },
            {
                'message': "I've been talking to you for weeks now. You probably remember my interest in sustainable development.",
                'test_name': "Phase 3.4: Memory + Relationship Continuity"
            },
            {
                'message': "I'm torn between two career paths. Part of me wants stability, but another part craves creative freedom.",
                'test_name': "Phase 3.5: Complex Emotional Analysis"
            }
        ]
        
        results = []
        feature_counts = {
            'enhanced_emotion_analysis': 0,
            'personality_analysis': 0,
            'context_analysis': 0,
            'emoji_intelligence': 0,
            'memory_enhancement': 0,
            'relationship_depth': 0
        }
        
        quality_totals = {
            'feature_coverage': 0.0,
            'emotional_intelligence': 0.0,
            'personality_awareness': 0.0,
            'context_understanding': 0.0
        }
        
        for scenario in test_scenarios:
            logger.info("=" * 60)
            result = await self.test_phase3_feature(scenario['message'], scenario['test_name'])
            results.append(result)
            
            if result.get('success', False):
                analysis = result.get('analysis', {})
                
                # Count feature detections
                for feature in analysis.get('features_detected', {}):
                    if feature in feature_counts:
                        feature_counts[feature] += 1
                        
                # Sum quality scores
                quality_scores = analysis.get('quality_scores', {})
                for metric, score in quality_scores.items():
                    if metric in quality_totals:
                        quality_totals[metric] += score
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Calculate averages
        num_tests = len(test_scenarios)
        avg_quality = {metric: total / num_tests for metric, total in quality_totals.items()}
        
        # Generate summary report
        logger.info("📊 PHASE 3 VALIDATION SUMMARY REPORT")
        logger.info("=" * 50)
        logger.info("Feature Detection Rates:")
        for feature, count in feature_counts.items():
            percentage = (count / num_tests) * 100
            logger.info("  • %s: %d/%d (%.1f%%)", 
                       feature.replace('_', ' ').title(), count, num_tests, percentage)
        
        logger.info("Average Quality Scores:")
        for metric, score in avg_quality.items():
            logger.info("  • %s: %.1f%%", metric.replace('_', ' ').title(), score * 100)
        
        # Determine overall success
        overall_success = (
            avg_quality['feature_coverage'] >= 0.5 and  # At least 50% feature coverage
            avg_quality['emotional_intelligence'] >= 0.6 and  # Strong emotion analysis
            feature_counts['enhanced_emotion_analysis'] >= 3  # Emotion analysis in majority of tests
        )
        
        passed_tests = sum(1 for result in results if result.get('success', False))
        logger.info("📊 FINAL SUMMARY:")
        logger.info("   Tests Passed: %d/%d (%.1f%%)", passed_tests, num_tests, (passed_tests/num_tests)*100)
        logger.info("   Overall Phase 3 Success: %s", "✅ PASS" if overall_success else "❌ FAIL")
        
        return overall_success

async def main():
    """Main function to run Phase 3 direct validation."""
    logger.info("🚀 STARTING PHASE 3 DIRECT VALIDATION SUITE")
    logger.info("=" * 40)
    
    test_suite = Phase3DirectValidationSuite()
    
    try:
        # Initialize the test suite
        success = await test_suite.initialize()
        if not success:
            logger.error("❌ Failed to initialize components")
            return False
            
        # Run comprehensive tests
        success = await test_suite.run_comprehensive_tests()
        
        if success:
            logger.info("✅ Phase 3 validation PASSED")
            return True
        else:
            logger.error("❌ Phase 3 validation FAILED")
            return False
            
    except Exception as e:
        logger.error("❌ Validation suite error: %s", e)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)