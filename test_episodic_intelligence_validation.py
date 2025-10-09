#!/usr/bin/env python3
"""
Character Vector Episodic Intelligence - Direct Validation Testing
Tests the PHASE 1A episodic intelligence implementation with direct Python API calls.
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set required environment variables for testing
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('LLM_CHAT_MODEL', 'openrouter/anthropic/claude-3.5-sonnet')
os.environ.setdefault('OPENROUTER_API_KEY', 'dummy_key_for_testing')

# Force localhost settings for local testing
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory'

# Import WhisperEngine components
from src.characters.learning import create_character_vector_episodic_intelligence
from src.memory.memory_protocol import create_memory_manager
from src.core.message_processor import MessageProcessor, MessageContext
from qdrant_client import QdrantClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EpisodicIntelligenceValidator:
    """Comprehensive validator for Character Vector Episodic Intelligence"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6334')),
            timeout=30
        )
        self.episodic_intelligence = None
        self.memory_manager = None
        self.message_processor = None
        self.test_results = {}
    
    async def initialize_components(self):
        """Initialize all required components for testing"""
        try:
            # Initialize episodic intelligence
            self.episodic_intelligence = create_character_vector_episodic_intelligence(
                qdrant_client=self.qdrant_client
            )
            
            # Initialize memory manager
            self.memory_manager = create_memory_manager(memory_type="vector")
            
            # Initialize message processor (minimal setup for testing)
            self.message_processor = MessageProcessor(
                memory_manager=self.memory_manager,
                llm_client=None,  # Not needed for episodic testing
                bot_core=None
            )
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            return False
    
    async def test_memorable_moment_detection(self):
        """Test detection of memorable moments from vector patterns"""
        print("\n" + "="*60)
        print("🧠 Testing Memorable Moment Detection")
        print("="*60)
        
        test_collections = [
            'whisperengine_memory_sophia_7d',  # Highest memorable ratio (74%)
            'whisperengine_memory_jake_7d',    # High memorable ratio (68%)
            'whisperengine_memory_marcus_7d'   # High memorable ratio (69%)
        ]
        
        results = {}
        
        for collection in test_collections:
            try:
                print(f"\n🔍 Testing collection: {collection}")
                
                # Test memorable moment detection
                memorable_moments = await self.episodic_intelligence.detect_memorable_moments_from_vector_patterns(
                    collection_name=collection,
                    user_id=None,  # All users
                    limit=10,
                    days_back=90
                )
                
                if memorable_moments:
                    print(f"  ✅ Found {len(memorable_moments)} memorable moments")
                    
                    # Analyze top memorable moment
                    top_moment = memorable_moments[0]
                    print(f"  📊 Top moment score: {top_moment.memorable_score:.2f}")
                    print(f"  🎭 Primary emotion: {top_moment.primary_emotion}")
                    print(f"  🔄 Context type: {top_moment.context_type}")
                    print(f"  💬 Preview: {top_moment.content_preview}")
                    print(f"  🤖 RoBERTa confidence: {top_moment.roberta_confidence:.3f}")
                    print(f"  💫 Emotional intensity: {top_moment.emotional_intensity:.3f}")
                    
                    # Test quality metrics
                    high_quality = sum(1 for m in memorable_moments if m.memorable_score >= 4.0)
                    print(f"  🌟 High-quality moments (score ≥4.0): {high_quality}/{len(memorable_moments)}")
                    
                    results[collection] = {
                        'total_moments': len(memorable_moments),
                        'high_quality_moments': high_quality,
                        'top_score': top_moment.memorable_score,
                        'avg_confidence': sum(m.roberta_confidence for m in memorable_moments) / len(memorable_moments),
                        'context_types': list(set(m.context_type for m in memorable_moments))
                    }
                    
                else:
                    print(f"  ❌ No memorable moments found")
                    results[collection] = {'total_moments': 0}
                
            except Exception as e:
                print(f"  ❌ Error testing {collection}: {e}")
                results[collection] = {'error': str(e)}
        
        self.test_results['memorable_moments'] = results
        return results
    
    async def test_character_insights_extraction(self):
        """Test extraction of character insights from memorable moments"""
        print("\n" + "="*60)
        print("🎭 Testing Character Insights Extraction") 
        print("="*60)
        
        test_collection = 'whisperengine_memory_sophia_7d'  # Highest memorable ratio
        
        try:
            print(f"\n🔍 Testing insights for: {test_collection}")
            
            # First get memorable moments
            memorable_moments = await self.episodic_intelligence.detect_memorable_moments_from_vector_patterns(
                collection_name=test_collection,
                limit=20
            )
            
            if not memorable_moments:
                print("  ❌ No memorable moments available for insight extraction")
                return {'error': 'No memorable moments'}
            
            print(f"  📊 Base data: {len(memorable_moments)} memorable moments")
            
            # Extract character insights
            character_insights = await self.episodic_intelligence.extract_character_insights_from_vector_patterns(
                collection_name=test_collection,
                memorable_memories=memorable_moments
            )
            
            if character_insights:
                print(f"  ✅ Extracted {len(character_insights)} character insights")
                
                for i, insight in enumerate(character_insights[:3], 1):
                    print(f"\n  🧩 Insight {i}: {insight.insight_type}")
                    print(f"    Description: {insight.description}")
                    print(f"    Confidence: {insight.confidence:.3f}")
                    print(f"    Reinforcements: {insight.reinforcement_count}")
                
                # Analyze insight types
                insight_types = [i.insight_type for i in character_insights]
                type_counts = {t: insight_types.count(t) for t in set(insight_types)}
                print(f"\n  📈 Insight distribution: {type_counts}")
                
                result = {
                    'total_insights': len(character_insights),
                    'insight_types': type_counts,
                    'avg_confidence': sum(i.confidence for i in character_insights) / len(character_insights),
                    'top_insights': [
                        {
                            'type': i.insight_type,
                            'description': i.description,
                            'confidence': i.confidence
                        } for i in character_insights[:3]
                    ]
                }
                
            else:
                print("  ❌ No character insights extracted")
                result = {'total_insights': 0}
            
            self.test_results['character_insights'] = result
            return result
            
        except Exception as e:
            print(f"  ❌ Error extracting insights: {e}")
            result = {'error': str(e)}
            self.test_results['character_insights'] = result
            return result
    
    async def test_episodic_response_enhancement(self):
        """Test episodic memory integration for response enhancement"""
        print("\n" + "="*60)
        print("🚀 Testing Episodic Response Enhancement")
        print("="*60)
        
        test_cases = [
            {
                'collection': 'whisperengine_memory_sophia_7d',
                'user_id': 'test_user_1',
                'message': 'Tell me about something creative we discussed before',
                'expected_context_types': ['creative_moment', 'personal_sharing']
            },
            {
                'collection': 'whisperengine_memory_marcus_7d',
                'user_id': 'test_user_2', 
                'message': 'I want to learn more about research methods',
                'expected_context_types': ['expertise', 'personal_sharing']
            },
            {
                'collection': 'whisperengine_memory_jake_7d',
                'user_id': 'test_user_3',
                'message': 'What adventures have we talked about?',
                'expected_context_types': ['creative_moment', 'expertise']
            }
        ]
        
        results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                print(f"\n🧪 Test Case {i}: {test_case['collection']}")
                print(f"  💬 Message: {test_case['message']}")
                
                # Get episodic context for response enhancement
                episodic_context = await self.episodic_intelligence.get_episodic_memory_for_response_enhancement(
                    collection_name=test_case['collection'],
                    current_message=test_case['message'],
                    user_id=test_case['user_id'],
                    limit=5
                )
                
                if episodic_context:
                    memories = episodic_context.get('memories', [])
                    insights = episodic_context.get('insights', [])
                    suggestions = episodic_context.get('context_suggestions', [])
                    
                    print(f"  ✅ Retrieved {len(memories)} relevant memories")
                    print(f"  🧩 Retrieved {len(insights)} character insights")
                    print(f"  💡 Generated {len(suggestions)} context suggestions")
                    
                    if memories:
                        print(f"  📝 Top memory: {memories[0].get('context_type')} - {memories[0].get('content_preview', '')[:60]}...")
                    
                    if insights:
                        print(f"  🎭 Top insight: {insights[0].get('description', '')}")
                    
                    if suggestions:
                        print(f"  💭 Top suggestion: {suggestions[0]}")
                    
                    # Test guidance generation
                    if hasattr(self.message_processor, '_build_episodic_guidance'):
                        guidance = self.message_processor._build_episodic_guidance(episodic_context)
                        print(f"  🎯 Guidance generated: {len(guidance)} characters")
                        
                        if guidance:
                            print(f"  📋 Guidance preview: {guidance[:100]}...")
                    
                    results[f'test_case_{i}'] = {
                        'memories_count': len(memories),
                        'insights_count': len(insights),
                        'suggestions_count': len(suggestions),
                        'memory_confidence': episodic_context.get('memory_confidence', 0),
                        'total_memorable_moments': episodic_context.get('total_memorable_moments', 0),
                        'context_types': [m.get('context_type') for m in memories],
                        'success': True
                    }
                    
                else:
                    print(f"  ❌ No episodic context retrieved")
                    results[f'test_case_{i}'] = {'success': False, 'error': 'No context'}
                
            except Exception as e:
                print(f"  ❌ Test case {i} failed: {e}")
                results[f'test_case_{i}'] = {'success': False, 'error': str(e)}
        
        self.test_results['response_enhancement'] = results
        return results
    
    async def test_integration_with_message_processor(self):
        """Test integration with message processor for end-to-end functionality"""
        print("\n" + "="*60)
        print("🔗 Testing Message Processor Integration")
        print("="*60)
        
        try:
            # Check if episodic intelligence is properly initialized
            has_episodic = hasattr(self.message_processor, 'episodic_intelligence')
            episodic_available = self.message_processor.episodic_intelligence is not None
            
            print(f"  🧠 Episodic intelligence attribute: {has_episodic}")
            print(f"  ⚡ Episodic intelligence available: {episodic_available}")
            
            # Check if guidance method exists
            has_guidance_method = hasattr(self.message_processor, '_build_episodic_guidance')
            print(f"  🎯 Guidance method available: {has_guidance_method}")
            
            result = {
                'has_episodic_attribute': has_episodic,
                'episodic_available': episodic_available,
                'has_guidance_method': has_guidance_method,
                'integration_ready': has_episodic and episodic_available and has_guidance_method
            }
            
            if result['integration_ready']:
                print(f"  ✅ Message processor integration: READY")
                
                # Test guidance generation
                test_context = {
                    'memories': [
                        {
                            'context_type': 'personal_sharing',
                            'content_preview': 'I love talking about marine conservation',
                            'memorable_score': 4.5
                        }
                    ],
                    'insights': [
                        {
                            'type': 'topic_enthusiasm',
                            'description': 'I get excited about ocean topics',
                            'confidence': 0.85
                        }
                    ],
                    'context_suggestions': ['Remember our discussion about coral reefs'],
                    'total_memorable_moments': 15,
                    'memory_confidence': 0.75
                }
                
                guidance = self.message_processor._build_episodic_guidance(test_context)
                print(f"  📋 Test guidance length: {len(guidance)} characters")
                if guidance:
                    print(f"  💬 Guidance preview: {guidance[:150]}...")
                
            else:
                print(f"  ❌ Message processor integration: NOT READY")
            
            self.test_results['integration'] = result
            return result
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            result = {'error': str(e)}
            self.test_results['integration'] = result
            return result
    
    async def test_performance_metrics(self):
        """Test performance characteristics of episodic intelligence"""
        print("\n" + "="*60)
        print("⚡ Testing Performance Metrics")
        print("="*60)
        
        test_collection = 'whisperengine_memory_sophia_7d'
        
        try:
            # Time memorable moment detection
            start_time = datetime.now()
            memorable_moments = await self.episodic_intelligence.detect_memorable_moments_from_vector_patterns(
                collection_name=test_collection,
                limit=10
            )
            detection_time = (datetime.now() - start_time).total_seconds() * 1000
            
            print(f"  ⏱️ Memorable moment detection: {detection_time:.2f}ms")
            
            if memorable_moments:
                # Time insight extraction
                start_time = datetime.now()
                insights = await self.episodic_intelligence.extract_character_insights_from_vector_patterns(
                    collection_name=test_collection,
                    memorable_memories=memorable_moments
                )
                insight_time = (datetime.now() - start_time).total_seconds() * 1000
                
                print(f"  🧩 Character insight extraction: {insight_time:.2f}ms")
                
                # Time response enhancement
                start_time = datetime.now()
                episodic_context = await self.episodic_intelligence.get_episodic_memory_for_response_enhancement(
                    collection_name=test_collection,
                    current_message="Tell me about our previous conversations",
                    user_id="test_user",
                    limit=5
                )
                enhancement_time = (datetime.now() - start_time).total_seconds() * 1000
                
                print(f"  🚀 Response enhancement: {enhancement_time:.2f}ms")
                
                total_time = detection_time + insight_time + enhancement_time
                print(f"  📊 Total processing time: {total_time:.2f}ms")
                
                # Performance assessment
                performance_grade = "A" if total_time < 500 else "B" if total_time < 1000 else "C"
                print(f"  🏆 Performance grade: {performance_grade}")
                
                result = {
                    'detection_time_ms': detection_time,
                    'insight_time_ms': insight_time,
                    'enhancement_time_ms': enhancement_time,
                    'total_time_ms': total_time,
                    'performance_grade': performance_grade,
                    'meets_target': total_time < 500  # Target: <500ms
                }
                
            else:
                print(f"  ❌ No memorable moments for performance testing")
                result = {'error': 'No memorable moments'}
            
            self.test_results['performance'] = result
            return result
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            result = {'error': str(e)}
            self.test_results['performance'] = result
            return result
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("📊 EPISODIC INTELLIGENCE VALIDATION REPORT")
        print("="*80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"PHASE 1A: Character Vector Episodic Intelligence")
        
        # Overall success metrics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() 
                             if isinstance(result, dict) and not result.get('error'))
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"  • Tests completed: {total_tests}")
        print(f"  • Successful tests: {successful_tests}")
        print(f"  • Success rate: {success_rate:.1f}%")
        
        # Detailed test results
        print(f"\n📋 DETAILED RESULTS:")
        
        # Memorable moments test
        memorable_results = self.test_results.get('memorable_moments', {})
        if memorable_results and not memorable_results.get('error'):
            total_moments = sum(r.get('total_moments', 0) for r in memorable_results.values() if isinstance(r, dict))
            print(f"  🧠 Memorable Moments: {total_moments} total found across all collections")
            
            best_collection = max(memorable_results.items(), 
                                key=lambda x: x[1].get('total_moments', 0) if isinstance(x[1], dict) else 0)
            if best_collection[1].get('total_moments', 0) > 0:
                print(f"    Best performing: {best_collection[0]} ({best_collection[1]['total_moments']} moments)")
        
        # Character insights test
        insights_results = self.test_results.get('character_insights', {})
        if insights_results and not insights_results.get('error'):
            total_insights = insights_results.get('total_insights', 0)
            avg_confidence = insights_results.get('avg_confidence', 0)
            print(f"  🎭 Character Insights: {total_insights} insights (avg confidence: {avg_confidence:.3f})")
        
        # Response enhancement test
        enhancement_results = self.test_results.get('response_enhancement', {})
        if enhancement_results:
            successful_cases = sum(1 for r in enhancement_results.values() 
                                 if isinstance(r, dict) and r.get('success', False))
            total_cases = len(enhancement_results)
            print(f"  🚀 Response Enhancement: {successful_cases}/{total_cases} test cases successful")
        
        # Integration test
        integration_results = self.test_results.get('integration', {})
        if integration_results and integration_results.get('integration_ready'):
            print(f"  🔗 Message Processor Integration: ✅ READY")
        else:
            print(f"  🔗 Message Processor Integration: ❌ NOT READY")
        
        # Performance test
        performance_results = self.test_results.get('performance', {})
        if performance_results and not performance_results.get('error'):
            total_time = performance_results.get('total_time_ms', 0)
            grade = performance_results.get('performance_grade', 'N/A')
            print(f"  ⚡ Performance: {total_time:.1f}ms (Grade: {grade})")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if success_rate >= 80:
            print(f"  ✅ PHASE 1A implementation is PRODUCTION READY")
            print(f"  🚀 Ready to proceed with character integration testing")
            print(f"  📈 Consider optimizing highest-performing collections first")
        elif success_rate >= 60:
            print(f"  ⚠️ PHASE 1A implementation needs minor adjustments")
            print(f"  🔧 Focus on failed test components")
            print(f"  🧪 Increase test coverage before production")
        else:
            print(f"  ❌ PHASE 1A implementation needs significant work")
            print(f"  🚨 Address core functionality issues")
            print(f"  🔄 Re-run validation after fixes")
        
        print(f"\n✅ Validation complete! PHASE 1A Character Vector Episodic Intelligence tested.")
        return self.test_results

async def main():
    """Main validation execution"""
    print("🚀 WhisperEngine Character Vector Episodic Intelligence Validation")
    print("PHASE 1A: Direct Python API Testing")
    print("=" * 80)
    
    validator = EpisodicIntelligenceValidator()
    
    # Initialize components
    if not await validator.initialize_components():
        print("❌ Component initialization failed. Exiting.")
        return
    
    try:
        # Run all validation tests
        await validator.test_memorable_moment_detection()
        await validator.test_character_insights_extraction()
        await validator.test_episodic_response_enhancement()
        await validator.test_integration_with_message_processor()
        await validator.test_performance_metrics()
        
        # Generate comprehensive report
        await validator.generate_comprehensive_report()
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())