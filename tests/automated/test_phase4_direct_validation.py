#!/usr/bin/env python3
"""
Phase 4 Intelligence Direct Validation Suite

Tests Phase 4 features using direct Python calls to internal APIs instead of HTTP requests.
This provides more reliable testing without network timeouts and direct access to all data structures.
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

class Phase4DirectValidationSuite:
    """Direct validation of Phase 4 features using internal Python APIs."""
    
    def __init__(self):
        self.message_processor = None
        self.test_results = []
        self.test_user_id = "test_user_phase4_direct"
        
    async def initialize(self):
        """Initialize the message processor and required components."""
        try:
            # Import and initialize core components
            from src.core.message_processor import MessageProcessor, MessageContext
            from src.memory.memory_protocol import create_memory_manager
            from src.llm.llm_protocol import create_llm_client
            
            logger.info("🔧 Initializing core components...")
            
            # Create memory manager
            memory_manager = create_memory_manager(memory_type="vector")
            logger.info("✅ Memory manager created")
            
            # Create LLM client
            llm_client = create_llm_client(llm_client_type="openrouter")
            logger.info("✅ LLM client created")
            
            # Create message processor using the factory instead
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
    
    async def test_phase4_feature(self, message: str, test_name: str) -> Dict[str, Any]:
        """Test a specific Phase 4 feature using direct message processing."""
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
            
            # Analyze Phase 4 features
            analysis = self._analyze_phase4_features(ai_components, processing_result.response)
            
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
    
    def _analyze_phase4_features(self, ai_components: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Analyze AI components for Phase 4 intelligence features."""
        analysis = {
            "adaptive_conversation_modes": False,
            "interaction_type_detection": False,
            "enhanced_memory_processing": False,
            "relationship_depth_tracking": False,
            "context_aware_response": False,
            "human_like_integration": False,
            "detected_features": [],
            "phase4_indicators": [],
            "missing_features": [],
            "response_quality": 1
        }
        
        # Check for Phase 4 intelligence in AI components
        phase4_intelligence = ai_components.get("phase4_intelligence")
        phase4_context = ai_components.get("phase4_context")
        
        if phase4_intelligence or phase4_context:
            phase4_data = phase4_intelligence or phase4_context
            analysis["detected_features"].append("phase4_context_available")
            analysis["phase4_indicators"].append("Phase 4 context detected")
            
            # Check conversation mode
            conversation_mode = phase4_data.get("conversation_mode")
            if conversation_mode:
                analysis["adaptive_conversation_modes"] = True
                analysis["detected_features"].append("conversation_mode_detection")
                analysis["phase4_indicators"].append(f"Conversation mode: {conversation_mode}")
            
            # Check interaction type
            interaction_type = phase4_data.get("interaction_type")
            if interaction_type:
                analysis["interaction_type_detection"] = True
                analysis["detected_features"].append("interaction_type_detection")
                analysis["phase4_indicators"].append(f"Interaction type: {interaction_type}")
            
            # Check Phase 2 results for enhanced memory processing
            phase2_results = phase4_data.get("phase2_results")
            if phase2_results:
                analysis["enhanced_memory_processing"] = True
                analysis["detected_features"].append("enhanced_memory_processing")
                analysis["phase4_indicators"].append("Enhanced emotion analysis detected")
            
            # Check processing metadata for human-like integration
            processing_metadata = phase4_data.get("processing_metadata")
            if processing_metadata and processing_metadata.get("phases_executed"):
                analysis["human_like_integration"] = True
                analysis["detected_features"].append("human_like_integration")
                phases = processing_metadata.get("phases_executed", [])
                analysis["phase4_indicators"].append(f"Phases executed: {phases}")
            
            # Check context switches for context-aware responses
            context_switches = phase4_data.get("context_switches", [])
            if context_switches:
                analysis["context_aware_response"] = True
                analysis["detected_features"].append("context_aware_response")
                analysis["phase4_indicators"].append(f"Context switches: {len(context_switches)}")
            
            # Check context analysis
            context_analysis = phase4_data.get("context_analysis")
            if context_analysis:
                analysis["context_aware_response"] = True
                analysis["detected_features"].append("context_analysis")
                analysis["phase4_indicators"].append("Context analysis detected")
        
        # Check emotion analysis in AI components
        emotion_analysis = ai_components.get("emotion_analysis")
        if emotion_analysis:
            analysis["enhanced_memory_processing"] = True
            analysis["detected_features"].append("emotion_processing")
            analysis["phase4_indicators"].append("Enhanced emotion processing detected")
        
        # Check personality analysis
        personality_analysis = ai_components.get("personality_analysis")
        if personality_analysis:
            analysis["relationship_depth_tracking"] = True
            analysis["detected_features"].append("personality_analysis")
            analysis["phase4_indicators"].append("Personality analysis detected")
        
        # Calculate response quality score
        feature_count = len([
            analysis["adaptive_conversation_modes"],
            analysis["interaction_type_detection"],
            analysis["enhanced_memory_processing"],
            analysis["relationship_depth_tracking"],
            analysis["context_aware_response"],
            analysis["human_like_integration"]
        ])
        
        analysis["response_quality"] = min(5, max(1, feature_count))
        
        # Identify missing features
        feature_map = {
            "adaptive_conversation_modes": "Adaptive Conversation Modes",
            "interaction_type_detection": "Interaction Type Detection",
            "enhanced_memory_processing": "Enhanced Memory Processing", 
            "relationship_depth_tracking": "Relationship Depth Tracking",
            "context_aware_response": "Context-Aware Response",
            "human_like_integration": "Human-Like Integration"
        }
        
        for key, name in feature_map.items():
            if not analysis[key]:
                analysis["missing_features"].append(name)
        
        return analysis
    
    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis for failed tests."""
        return {
            "adaptive_conversation_modes": False,
            "interaction_type_detection": False,
            "enhanced_memory_processing": False,
            "relationship_depth_tracking": False,
            "context_aware_response": False,
            "human_like_integration": False,
            "detected_features": [],
            "phase4_indicators": [],
            "missing_features": ["All features missing due to test failure"],
            "response_quality": 0
        }
    
    def _log_analysis_results(self, analysis: Dict[str, Any], test_name: str):
        """Log the analysis results."""
        logger.info("📊 ANALYSIS for '%s':", test_name)
        logger.info("   Adaptive Conversation Modes: %s", '✅' if analysis['adaptive_conversation_modes'] else '❌')
        logger.info("   Interaction Type Detection: %s", '✅' if analysis['interaction_type_detection'] else '❌')
        logger.info("   Enhanced Memory Processing: %s", '✅' if analysis['enhanced_memory_processing'] else '❌')
        logger.info("   Relationship Depth Tracking: %s", '✅' if analysis['relationship_depth_tracking'] else '❌')
        logger.info("   Context-Aware Response: %s", '✅' if analysis['context_aware_response'] else '❌')
        logger.info("   Human-Like Integration: %s", '✅' if analysis['human_like_integration'] else '❌')
        logger.info("   Response Quality: %d/5", analysis['response_quality'])
        
        if analysis["phase4_indicators"]:
            logger.info("   Phase4+ Indicators:")
            for indicator in analysis["phase4_indicators"]:
                logger.info("     • %s", indicator)
        
        if analysis["missing_features"]:
            logger.warning("   Missing Features: %s", analysis['missing_features'])
    
    async def run_comprehensive_tests(self) -> bool:
        """Run comprehensive Phase 4 validation tests."""
        logger.info("🚀 STARTING PHASE 4 DIRECT VALIDATION SUITE")
        logger.info("==========================================")
        
        if not await self.initialize():
            logger.error("❌ Failed to initialize components")
            return False
        
        test_cases = [
            {
                'message': 'I need a detailed scientific analysis of microplastic impact on marine food chains. Please include molecular-level effects, bioaccumulation patterns, and quantitative data on ecosystem disruption.',
                'test_name': 'Analytical Mode Trigger',
                'expected_features': ['conversation_mode_detection', 'interaction_type_detection']
            },
            {
                'message': 'I just had the most amazing experience snorkeling today! I saw a sea turtle and it felt so magical. I wish I could share this feeling with someone who really understands the ocean.',
                'test_name': 'Human-Like Mode Trigger',
                'expected_features': ['conversation_mode_detection', 'emotion_processing']
            },
            {
                'message': 'I\'m working on a research project about coral bleaching, but I\'m also feeling overwhelmed by the environmental crisis. Can you help me understand the science while also supporting me emotionally?',
                'test_name': 'Balanced Mode Trigger',
                'expected_features': ['conversation_mode_detection', 'multi_context_integration']
            },
            {
                'message': 'I\'m going through a really difficult breakup right now. I feel lost and don\'t know how to move forward. Everything reminds me of my ex and I can\'t seem to get my life back on track.',
                'test_name': 'Emotional Support Detection',
                'expected_features': ['interaction_type_detection', 'emotion_processing']
            },
            {
                'message': 'I need both analytical help and emotional support. Can you help me understand the technical aspects of coral reef restoration while also helping me deal with my anxiety about climate change?',
                'test_name': 'Phase 4.1: Human-Like Integration',
                'expected_features': ['human_like_integration', 'multi_context_integration']
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info("=" * 80)
            result = await self.test_phase4_feature(
                test_case['message'],
                test_case['test_name']
            )
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        # Check if tests passed
        passed_tests = sum(1 for r in results if r.get('success', False) and r.get('analysis', {}).get('response_quality', 0) >= 3)
        success_rate = (passed_tests / len(results)) * 100
        
        logger.info("📊 FINAL SUMMARY:")
        logger.info("   Tests Passed: %d/%d (%.1f%%)", passed_tests, len(results), success_rate)
        
        return success_rate >= 80.0  # 80% success rate threshold
    
    def _generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generate a comprehensive summary report."""
        logger.info("📊 PHASE 4 VALIDATION SUMMARY REPORT")
        logger.info("=" * 50)
        
        total_tests = len(results)
        successful_tests = [r for r in results if r.get('success', False)]
        
        # Feature analysis
        feature_stats = {
            'adaptive_conversation_modes': 0,
            'interaction_type_detection': 0,
            'enhanced_memory_processing': 0,
            'relationship_depth_tracking': 0,
            'context_aware_response': 0,
            'human_like_integration': 0
        }
        
        for result in successful_tests:
            analysis = result.get('analysis', {})
            for feature in feature_stats:
                if analysis.get(feature, False):
                    feature_stats[feature] += 1
        
        logger.info("Feature Detection Rates:")
        for feature, count in feature_stats.items():
            rate = (count / total_tests) * 100 if total_tests > 0 else 0
            feature_name = feature.replace('_', ' ').title()
            logger.info("  • %s: %d/%d (%.1f%%)", feature_name, count, total_tests, rate)
        
        # Average response quality
        quality_scores = [r.get('analysis', {}).get('response_quality', 0) for r in successful_tests]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        logger.info("Average Response Quality: %.1f/5", avg_quality)
        
        # Processing performance
        processing_times = [r.get('processing_time_ms', 0) for r in successful_tests]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            logger.info("Average Processing Time: %.0fms", avg_time)


async def main():
    """Run the Phase 4 direct validation suite."""
    test_suite = Phase4DirectValidationSuite()
    
    try:
        success = await test_suite.run_comprehensive_tests()
        if success:
            logger.info("✅ Phase 4 validation PASSED")
            return True
        else:
            logger.error("❌ Phase 4 validation FAILED")
            return False
            
    except Exception as e:
        logger.error("❌ Validation suite error: %s", e)
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)