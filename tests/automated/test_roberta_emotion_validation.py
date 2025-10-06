#!/usr/bin/env python3
"""
Sprint 2 RoBERTa Metadata Validation Test
==========================================

Validates the Sprint 2 modernization that replaced keyword-based emotional impact
calculation with stored RoBERTa transformer metadata.

Tests:
1. RoBERTa instance is shared (performance optimization)
2. RoBERTa analysis is thread-safe (concurrent execution)
3. Memory effectiveness uses RoBERTa metadata (not keywords)
4. Payload is properly passed through pipeline
5. Emotional impact scoring improved (RoBERTa vs keywords)
6. Fallback works when RoBERTa metadata unavailable

Usage:
    python tests/automated/test_roberta_emotion_validation.py
"""

import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure environment
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('QDRANT_COLLECTION_NAME', 'test_roberta_emotion')
os.environ.setdefault('DISCORD_BOT_NAME', 'TestBot')

from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
from src.memory.memory_effectiveness import MemoryEffectivenessAnalyzer
from src.memory.memory_protocol import create_memory_manager


class Sprint2RobertaValidator:
    """Validates Sprint 2 RoBERTa metadata integration."""
    
    def __init__(self):
        self.memory_manager = None
        self.emotion_analyzer = None
        self.effectiveness_analyzer = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'details': []
        }
        
    async def initialize(self):
        """Initialize components for testing."""
        print("🔧 Initializing test components...")
        
        try:
            # Create memory manager
            self.memory_manager = create_memory_manager(memory_type="vector")
            print("✅ Memory manager initialized")
            
            # Create emotion analyzer
            self.emotion_analyzer = EnhancedVectorEmotionAnalyzer(
                vector_memory_manager=self.memory_manager
            )
            print("✅ Emotion analyzer initialized")
            
            # Create effectiveness analyzer
            self.effectiveness_analyzer = MemoryEffectivenessAnalyzer(
                memory_manager=self.memory_manager
            )
            print("✅ Effectiveness analyzer initialized")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def record_test(self, test_name: str, passed: bool, details: str = ""):
        """Record test result."""
        self.test_results['total'] += 1
        if passed:
            self.test_results['passed'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed'] += 1
            status = "❌ FAIL"
        
        self.test_results['details'].append({
            'test': test_name,
            'status': status,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"  → {details}")
    
    async def test_shared_roberta_instance(self) -> bool:
        """Test 1: Verify RoBERTa instance is shared across analyzer instances."""
        print("\n🧪 Test 1: Shared RoBERTa Instance")
        
        try:
            # Create multiple analyzer instances
            analyzer1 = EnhancedVectorEmotionAnalyzer()
            analyzer2 = EnhancedVectorEmotionAnalyzer()
            
            # Analyze with both to trigger RoBERTa initialization
            await analyzer1.analyze_emotion("I feel happy today!", "test_user_1")
            await analyzer2.analyze_emotion("I'm feeling sad", "test_user_2")
            
            # Check if they share the same classifier
            has_shared_classifier = (
                hasattr(EnhancedVectorEmotionAnalyzer, '_shared_roberta_classifier') and
                EnhancedVectorEmotionAnalyzer._shared_roberta_classifier is not None
            )
            
            if has_shared_classifier:
                self.record_test(
                    "Shared RoBERTa Instance",
                    True,
                    "RoBERTa classifier is shared across instances (performance optimized)"
                )
                return True
            else:
                self.record_test(
                    "Shared RoBERTa Instance",
                    False,
                    "RoBERTa classifier not properly shared"
                )
                return False
                
        except Exception as e:
            self.record_test("Shared RoBERTa Instance", False, f"Error: {e}")
            return False
    
    async def test_concurrent_roberta_analysis(self) -> bool:
        """Test 2: Verify RoBERTa analysis is thread-safe under concurrent load."""
        print("\n🧪 Test 2: Concurrent RoBERTa Analysis (Thread Safety)")
        
        try:
            test_messages = [
                "I'm so happy and excited!",
                "This makes me really angry",
                "I feel very sad today",
                "I'm scared and worried",
                "What a wonderful surprise!",
                "I'm grateful for everything",
                "This is frustrating",
                "I feel anxious about this"
            ]
            
            # Run analyses concurrently
            start_time = time.time()
            tasks = [
                self.emotion_analyzer.analyze_emotion(msg, f"user_{i}")
                for i, msg in enumerate(test_messages)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed_time = time.time() - start_time
            
            # Check for errors
            errors = [r for r in results if isinstance(r, Exception)]
            successful = len(results) - len(errors)
            
            if len(errors) == 0:
                self.record_test(
                    "Concurrent RoBERTa Analysis",
                    True,
                    f"Successfully analyzed {successful}/{len(test_messages)} messages concurrently in {elapsed_time:.2f}s"
                )
                return True
            else:
                self.record_test(
                    "Concurrent RoBERTa Analysis",
                    False,
                    f"Encountered {len(errors)} errors during concurrent analysis"
                )
                return False
                
        except Exception as e:
            self.record_test("Concurrent RoBERTa Analysis", False, f"Error: {e}")
            return False
    
    async def test_roberta_metadata_storage(self) -> bool:
        """Test 3: Verify RoBERTa metadata is properly stored in memory payload."""
        print("\n🧪 Test 3: RoBERTa Metadata Storage")
        
        try:
            # Analyze emotion to generate RoBERTa metadata
            test_message = "I'm feeling incredibly excited and happy about this!"
            emotion_result = await self.emotion_analyzer.analyze_emotion(
                test_message, 
                "test_user_metadata"
            )
            
            # Check if emotion_result has expected RoBERTa fields
            has_confidence = hasattr(emotion_result, 'confidence') and emotion_result.confidence > 0
            has_all_emotions = hasattr(emotion_result, 'all_emotions') and len(emotion_result.all_emotions) > 0
            has_mixed_emotions = hasattr(emotion_result, 'mixed_emotions')
            
            # Simulate storage (what vector_memory_system does)
            simulated_payload = {
                'roberta_confidence': emotion_result.confidence,
                'all_emotions': emotion_result.all_emotions,
                'primary_emotion': emotion_result.primary_emotion,
                'intensity': emotion_result.intensity,
                'is_multi_emotion': len(emotion_result.mixed_emotions) > 0 if has_mixed_emotions else False
            }
            
            # Verify key fields present
            required_fields = ['roberta_confidence', 'all_emotions', 'primary_emotion', 'intensity']
            all_fields_present = all(field in simulated_payload for field in required_fields)
            
            if has_confidence and has_all_emotions and all_fields_present:
                self.record_test(
                    "RoBERTa Metadata Storage",
                    True,
                    f"All required fields present (confidence={emotion_result.confidence:.3f}, emotions={len(emotion_result.all_emotions)})"
                )
                return True
            else:
                self.record_test(
                    "RoBERTa Metadata Storage",
                    False,
                    f"Missing fields: confidence={has_confidence}, all_emotions={has_all_emotions}, complete={all_fields_present}"
                )
                return False
                
        except Exception as e:
            self.record_test("RoBERTa Metadata Storage", False, f"Error: {e}")
            return False
    
    async def test_emotional_impact_calculation(self) -> bool:
        """Test 4: Verify emotional impact uses RoBERTa metadata instead of keywords."""
        print("\n🧪 Test 4: Emotional Impact Calculation (RoBERTa vs Keywords)")
        
        try:
            # Test message with complex emotions (not simple keywords)
            test_content = "The presentation went amazingly well, exceeding all expectations!"
            
            # Create mock RoBERTa payload
            roberta_payload = {
                'roberta_confidence': 0.92,
                'emotion_variance': 0.35,
                'emotion_dominance': 0.85,
                'emotional_intensity': 0.88,
                'is_multi_emotion': True
            }
            
            # Test with RoBERTa metadata
            emotional_impact_roberta = await self.effectiveness_analyzer._calculate_emotional_impact(
                memory_content=test_content,
                user_id="test_user",
                bot_name="test_bot",
                memory_payload=roberta_payload
            )
            
            # Test without RoBERTa metadata (fallback to keywords)
            emotional_impact_keywords = await self.effectiveness_analyzer._calculate_emotional_impact(
                memory_content=test_content,
                user_id="test_user",
                bot_name="test_bot",
                memory_payload=None  # Force keyword fallback
            )
            
            # RoBERTa-based should be significantly better for this content
            roberta_better = emotional_impact_roberta > emotional_impact_keywords
            roberta_score_reasonable = 0.3 <= emotional_impact_roberta <= 1.0
            
            if roberta_better and roberta_score_reasonable:
                self.record_test(
                    "Emotional Impact Calculation",
                    True,
                    f"RoBERTa score ({emotional_impact_roberta:.3f}) > Keyword score ({emotional_impact_keywords:.3f})"
                )
                return True
            else:
                self.record_test(
                    "Emotional Impact Calculation",
                    False,
                    f"RoBERTa score ({emotional_impact_roberta:.3f}) not better than keywords ({emotional_impact_keywords:.3f})"
                )
                return False
                
        except Exception as e:
            self.record_test("Emotional Impact Calculation", False, f"Error: {e}")
            return False
    
    async def test_payload_pipeline_integration(self) -> bool:
        """Test 5: Verify payload is passed through entire pipeline."""
        print("\n🧪 Test 5: Payload Pipeline Integration")
        
        try:
            # Mock memory result with payload (simulates what Qdrant returns)
            mock_memory_result = {
                'id': 'test_memory_123',
                'content': 'I absolutely love this amazing experience!',
                'memory_type': 'conversation',
                'payload': {  # This is what Qdrant returns
                    'roberta_confidence': 0.95,
                    'emotion_variance': 0.22,
                    'emotion_dominance': 0.91,
                    'emotional_intensity': 0.93,
                    'is_multi_emotion': False,
                    'primary_emotion': 'joy'
                }
            }
            
            # Simulate relevance_optimizer extracting payload
            memory_payload = mock_memory_result.get('payload', None)
            
            # Call score_memory_quality with payload
            quality_score = await self.effectiveness_analyzer.score_memory_quality(
                memory_id=mock_memory_result['id'],
                user_id='test_user',
                bot_name='test_bot',
                memory_content=mock_memory_result['content'],
                memory_type=mock_memory_result['memory_type'],
                memory_payload=memory_payload  # Sprint 2 enhancement
            )
            
            # Verify quality score was computed
            has_emotional_impact = quality_score.emotional_impact > 0
            has_combined_score = quality_score.combined_score > 0
            
            if has_emotional_impact and has_combined_score:
                self.record_test(
                    "Payload Pipeline Integration",
                    True,
                    f"Payload successfully passed through (emotional_impact={quality_score.emotional_impact:.3f})"
                )
                return True
            else:
                self.record_test(
                    "Payload Pipeline Integration",
                    False,
                    f"Payload not properly utilized (impact={quality_score.emotional_impact}, score={quality_score.combined_score})"
                )
                return False
                
        except Exception as e:
            self.record_test("Payload Pipeline Integration", False, f"Error: {e}")
            return False
    
    async def test_roberta_performance_benchmark(self) -> bool:
        """Test 6: Benchmark RoBERTa analysis performance."""
        print("\n🧪 Test 6: RoBERTa Performance Benchmark")
        
        try:
            test_messages = [
                "This is wonderful!",
                "I'm feeling sad",
                "What an exciting day",
                "I'm worried about this",
                "That's frustrating"
            ]
            
            # Warm-up run
            await self.emotion_analyzer.analyze_emotion(test_messages[0], "warmup_user")
            
            # Benchmark runs
            start_time = time.time()
            for i, message in enumerate(test_messages):
                await self.emotion_analyzer.analyze_emotion(message, f"bench_user_{i}")
            elapsed_time = time.time() - start_time
            
            avg_time_ms = (elapsed_time / len(test_messages)) * 1000
            
            # Performance target: < 200ms per message (reasonable for RoBERTa)
            performance_acceptable = avg_time_ms < 200
            
            if performance_acceptable:
                self.record_test(
                    "RoBERTa Performance Benchmark",
                    True,
                    f"Average analysis time: {avg_time_ms:.1f}ms per message (target: <200ms)"
                )
                return True
            else:
                self.record_test(
                    "RoBERTa Performance Benchmark",
                    False,
                    f"Average analysis time: {avg_time_ms:.1f}ms exceeds 200ms target"
                )
                return False
                
        except Exception as e:
            self.record_test("RoBERTa Performance Benchmark", False, f"Error: {e}")
            return False
    
    async def test_fallback_mechanism(self) -> bool:
        """Test 7: Verify keyword fallback works when RoBERTa metadata unavailable."""
        print("\n🧪 Test 7: Keyword Fallback Mechanism")
        
        try:
            # Test with explicit None payload (simulates old memories)
            emotional_impact = await self.effectiveness_analyzer._calculate_emotional_impact(
                memory_content="I love this happy wonderful experience!",
                user_id="test_user",
                bot_name="test_bot",
                memory_payload=None  # No RoBERTa metadata
            )
            
            # Should still get reasonable score from keyword fallback
            fallback_works = 0.1 <= emotional_impact <= 1.0
            
            if fallback_works:
                self.record_test(
                    "Keyword Fallback Mechanism",
                    True,
                    f"Fallback produced valid score: {emotional_impact:.3f}"
                )
                return True
            else:
                self.record_test(
                    "Keyword Fallback Mechanism",
                    False,
                    f"Fallback score invalid: {emotional_impact:.3f}"
                )
                return False
                
        except Exception as e:
            self.record_test("Keyword Fallback Mechanism", False, f"Error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("SPRINT 2 ROBERTA VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.test_results['total']}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"Success Rate: {(self.test_results['passed']/self.test_results['total']*100):.1f}%")
        print("="*70)
        
        print("\nDetailed Results:")
        for result in self.test_results['details']:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"  → {result['details']}")
        
        print("\n" + "="*70)
        if self.test_results['failed'] == 0:
            print("✅ ALL TESTS PASSED - Sprint 2 RoBERTa integration validated!")
        else:
            print(f"⚠️  {self.test_results['failed']} test(s) failed - review details above")
        print("="*70)
    
    async def run_all_tests(self):
        """Run complete test suite."""
        print("="*70)
        print("SPRINT 2 ROBERTA METADATA VALIDATION")
        print("="*70)
        print("Testing RoBERTa transformer metadata integration")
        print("Validates keyword → RoBERTa migration improvements")
        print("="*70)
        
        # Initialize
        if not await self.initialize():
            print("❌ Initialization failed - cannot proceed with tests")
            return False
        
        # Run tests
        await self.test_shared_roberta_instance()
        await self.test_concurrent_roberta_analysis()
        await self.test_roberta_metadata_storage()
        await self.test_emotional_impact_calculation()
        await self.test_payload_pipeline_integration()
        await self.test_roberta_performance_benchmark()
        await self.test_fallback_mechanism()
        
        # Print summary
        self.print_summary()
        
        return self.test_results['failed'] == 0


async def main():
    """Main test execution."""
    validator = Sprint2RobertaValidator()
    success = await validator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
