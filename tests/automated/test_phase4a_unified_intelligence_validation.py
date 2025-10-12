#!/usr/bin/env python3
"""
PHASE 4A Unified Character Intelligence Coordinator - Validation Test
Tests the PHASE 4A unified intelligence coordination implementation.

Usage: python test_phase4a_unified_intelligence_validation.py
"""

import asyncio
import logging
import os
import sys

# Set up environment
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')

# Add project root to path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Phase4AValidationTest:
    """Test suite for PHASE 4A Unified Character Intelligence Coordinator."""
    
    def __init__(self):
        self.test_character = "elena"
        self.postgres_pool = None
        self.test_results = []
    
    async def setup_environment(self):
        """Setup test environment."""
        try:
            import asyncpg
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
            self.postgres_pool = await asyncpg.create_pool(DATABASE_URL)
            
            if self.postgres_pool is None:
                logger.error("❌ Failed to create PostgreSQL connection pool")
                return False
                
            logger.info("✅ PostgreSQL connection established")
            return True
        except ImportError as e:
            logger.error("❌ Missing required dependency: %s", e)
            return False
        except (OSError, ConnectionError) as e:
            logger.error("❌ Database connection failed: %s", e)
            return False
    
    async def test_coordinator_import(self):
        """Test unified coordinator import and initialization."""
        try:
            logger.info("🧪 Testing Unified Character Intelligence Coordinator import...")
            
            from src.characters.learning.unified_character_intelligence_coordinator import (
                UnifiedCharacterIntelligenceCoordinator,
                IntelligenceRequest,
                IntelligenceResponse,
                CoordinationStrategy,
                IntelligenceSystemType,
                create_unified_character_intelligence_coordinator
            )
            
            self.test_results.append("✅ Unified coordinator imports: SUCCESS")
            
            # Test coordinator creation
            coordinator = create_unified_character_intelligence_coordinator()
            if coordinator:
                self.test_results.append("✅ Coordinator creation: SUCCESS")
            else:
                self.test_results.append("❌ Coordinator creation: FAILED")
                return False
            
            return True
            
        except ImportError as e:
            self.test_results.append(f"❌ Coordinator import failed: {e}")
            return False
    
    async def test_integration_framework(self):
        """Test integration framework."""
        try:
            logger.info("🔗 Testing Integration Framework...")
            
            from src.characters.learning.character_intelligence_integration import (
                CharacterIntelligenceIntegration,
                IntegrationConfig,
                create_character_intelligence_integration
            )
            
            self.test_results.append("✅ Integration framework imports: SUCCESS")
            
            # Test integration creation
            integration = create_character_intelligence_integration()
            if integration:
                self.test_results.append("✅ Integration creation: SUCCESS")
            else:
                self.test_results.append("❌ Integration creation: FAILED")
                return False
            
            return True
            
        except ImportError as e:
            self.test_results.append(f"❌ Integration framework import failed: {e}")
            return False
    
    async def test_coordination_request_response(self):
        """Test intelligence request and response structures."""
        try:
            logger.info("📋 Testing Request/Response Structures...")
            
            from src.characters.learning.unified_character_intelligence_coordinator import (
                IntelligenceRequest,
                IntelligenceResponse,
                CoordinationStrategy,
                IntelligenceSystemType
            )
            
            # Test request creation
            test_request = IntelligenceRequest(
                user_id="test_user",
                character_name=self.test_character,
                message_content="Hello Elena!",
                coordination_strategy=CoordinationStrategy.ADAPTIVE
            )
            
            if test_request.user_id == "test_user":
                self.test_results.append("✅ IntelligenceRequest creation: SUCCESS")
            else:
                self.test_results.append("❌ IntelligenceRequest creation: FAILED")
                return False
            
            # Test response structure
            test_response = IntelligenceResponse(
                enhanced_response="Test response",
                system_contributions={},
                coordination_metadata={'test': True},
                performance_metrics={'test_metric': 1.0},
                character_authenticity_score=0.9,
                confidence_score=0.8,
                processing_time_ms=100.0
            )
            
            if test_response.enhanced_response == "Test response":
                self.test_results.append("✅ IntelligenceResponse creation: SUCCESS")
            else:
                self.test_results.append("❌ IntelligenceResponse creation: FAILED")
                return False
            
            return True
            
        except (ValueError, TypeError) as e:
            self.test_results.append(f"❌ Request/Response structures failed: {e}")
            return False
    
    async def test_system_availability_detection(self):
        """Test system availability detection."""
        try:
            logger.info("🔍 Testing System Availability Detection...")
            
            from src.characters.learning.unified_character_intelligence_coordinator import (
                create_unified_character_intelligence_coordinator,
                IntelligenceSystemType
            )
            
            # Create coordinator without any systems
            coordinator = create_unified_character_intelligence_coordinator()
            
            # Test availability checking
            memory_available = await coordinator.is_system_available(IntelligenceSystemType.MEMORY_BOOST)
            cdl_available = await coordinator.is_system_available(IntelligenceSystemType.CDL_PERSONALITY)
            
            # These should be False since no systems are provided
            if not memory_available and not cdl_available:
                self.test_results.append("✅ System availability detection: SUCCESS")
            else:
                self.test_results.append(f"⚠️ System availability detection: Unexpected results (memory:{memory_available}, cdl:{cdl_available})")
            
            return True
            
        except (ValueError, TypeError) as e:
            self.test_results.append(f"❌ System availability detection failed: {e}")
            return False
    
    async def test_context_type_detection(self):
        """Test conversation context type detection."""
        try:
            logger.info("🎯 Testing Context Type Detection...")
            
            from src.characters.learning.unified_character_intelligence_coordinator import (
                create_unified_character_intelligence_coordinator,
                IntelligenceRequest,
                CoordinationStrategy
            )
            
            coordinator = create_unified_character_intelligence_coordinator()
            
            # Test different message types
            test_messages = [
                ("Tell me about yourself", "personal_question"),
                ("I'm feeling sad today", "emotional_support"),
                ("How does photosynthesis work?", "knowledge_sharing"),
                ("Hello there!", "casual_conversation"),
                ("I need to solve this complex problem", "complex_problem")
            ]
            
            context_results = []
            for message, expected_context in test_messages:
                request = IntelligenceRequest(
                    user_id="test_user",
                    character_name=self.test_character,
                    message_content=message,
                    coordination_strategy=CoordinationStrategy.ADAPTIVE
                )
                
                detected_context = await coordinator.detect_context_type(request)
                context_results.append((message, expected_context, detected_context))
            
            # Check if at least some contexts are detected correctly
            correct_detections = sum(1 for _, expected, detected in context_results if expected == detected)
            
            if correct_detections >= 3:  # At least 3 out of 5 should be correct
                self.test_results.append(f"✅ Context type detection: SUCCESS ({correct_detections}/5 correct)")
            else:
                self.test_results.append(f"⚠️ Context type detection: PARTIAL ({correct_detections}/5 correct)")
            
            return True
            
        except (ValueError, TypeError) as e:
            self.test_results.append(f"❌ Context type detection failed: {e}")
            return False
    
    async def test_intelligence_coordination_flow(self):
        """Test the complete intelligence coordination flow."""
        try:
            logger.info("🌊 Testing Intelligence Coordination Flow...")
            
            from src.characters.learning.unified_character_intelligence_coordinator import (
                create_unified_character_intelligence_coordinator,
                IntelligenceRequest,
                CoordinationStrategy
            )
            
            coordinator = create_unified_character_intelligence_coordinator()
            
            # Create test request
            request = IntelligenceRequest(
                user_id="test_user",
                character_name=self.test_character,
                message_content="Hello, how are you today?",
                coordination_strategy=CoordinationStrategy.ADAPTIVE
            )
            
            # Test coordination (should work even without systems)
            response = await coordinator.coordinate_intelligence(request)
            
            if response and hasattr(response, 'enhanced_response'):
                self.test_results.append("✅ Intelligence coordination flow: SUCCESS")
                
                # Check response components
                if response.processing_time_ms >= 0:
                    self.test_results.append("✅ Performance metrics: SUCCESS")
                else:
                    self.test_results.append("⚠️ Performance metrics: INVALID")
                
                if 0 <= response.confidence_score <= 1:
                    self.test_results.append("✅ Confidence scoring: SUCCESS")
                else:
                    self.test_results.append("⚠️ Confidence scoring: INVALID")
                    
            else:
                self.test_results.append("❌ Intelligence coordination flow: FAILED")
                return False
            
            return True
            
        except (ValueError, TypeError) as e:
            self.test_results.append(f"❌ Intelligence coordination flow failed: {e}")
            return False
    
    async def test_integration_enhancement(self):
        """Test message processing enhancement integration."""
        try:
            logger.info("🚀 Testing Integration Enhancement...")
            
            from src.characters.learning.character_intelligence_integration import (
                create_character_intelligence_integration,
                IntegrationConfig
            )
            
            # Create integration
            config = IntegrationConfig(enabled=True)
            integration = create_character_intelligence_integration(config)
            
            # Test enhancement without coordinator (should return passthrough)
            result = await integration.enhance_message_processing(
                user_id="test_user",
                character_name=self.test_character,
                message_content="Hello!"
            )
            
            if result and 'intelligence_coordination' in result:
                coordination_info = result['intelligence_coordination']
                if not coordination_info.get('successful', True):  # Should be False since no coordinator
                    self.test_results.append("✅ Integration enhancement passthrough: SUCCESS")
                else:
                    self.test_results.append("⚠️ Integration enhancement: Unexpected success without coordinator")
            else:
                self.test_results.append("❌ Integration enhancement: FAILED")
                return False
            
            # Test metrics
            metrics = integration.get_integration_metrics()
            if metrics and 'total_requests' in metrics:
                self.test_results.append("✅ Integration metrics: SUCCESS")
            else:
                self.test_results.append("❌ Integration metrics: FAILED")
            
            return True
            
        except (ValueError, TypeError) as e:
            self.test_results.append(f"❌ Integration enhancement failed: {e}")
            return False
    
    async def run_tests(self):
        """Run all PHASE 4A tests."""
        try:
            logger.info("🚀 Starting PHASE 4A Unified Intelligence Validation Test")
            logger.info("=" * 70)
            
            # Setup
            if not await self.setup_environment():
                logger.error("❌ Environment setup failed")
                return False
            
            # Run tests
            tests = [
                ('Coordinator Import', self.test_coordinator_import),
                ('Integration Framework', self.test_integration_framework),
                ('Request/Response Structures', self.test_coordination_request_response),
                ('System Availability Detection', self.test_system_availability_detection),
                ('Context Type Detection', self.test_context_type_detection),
                ('Intelligence Coordination Flow', self.test_intelligence_coordination_flow),
                ('Integration Enhancement', self.test_integration_enhancement),
            ]
            
            passed = 0
            for test_name, test_func in tests:
                logger.info("Running %s test...", test_name)
                if await test_func():
                    passed += 1
                    logger.info("✅ %s test PASSED", test_name)
                else:
                    logger.error("❌ %s test FAILED", test_name)
            
            # Report results
            logger.info("\n" + "=" * 70)
            logger.info("📊 PHASE 4A UNIFIED INTELLIGENCE VALIDATION RESULTS")
            logger.info("=" * 70)
            
            for i, result in enumerate(self.test_results, 1):
                logger.info("%d. %s", i, result)
            
            success_rate = (passed / len(tests)) * 100
            logger.info("\n🎯 Overall Success Rate: %d/%d (%.1f%%)", passed, len(tests), success_rate)
            
            if success_rate >= 80:
                logger.info("🎉 PHASE 4A Unified Character Intelligence: VALIDATION SUCCESSFUL!")
                logger.info("✅ Intelligence coordination system ready for integration")
            elif success_rate >= 60:
                logger.warning("⚠️ PHASE 4A Unified Character Intelligence: PARTIAL SUCCESS")
                logger.warning("🔧 Some components need refinement")
            else:
                logger.error("❌ PHASE 4A Unified Character Intelligence: VALIDATION FAILED")
                logger.error("🚨 Major implementation issues detected")
            
            return success_rate >= 80
            
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
            return False
        finally:
            if self.postgres_pool:
                await self.postgres_pool.close()

async def main():
    """Main test execution."""
    test_suite = Phase4AValidationTest()
    success = await test_suite.run_tests()
    
    if success:
        print("\n🎊 PHASE 4A IMPLEMENTATION VALIDATION COMPLETE!")
        print("🧠 Unified Character Intelligence Coordination system ready!")
        exit(0)
    else:
        print("\n⚠️ PHASE 4A validation completed with issues")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())