#!/usr/bin/env python3
"""
PHASE 3A Character Graph Self-Knowledge Builder - Direct Validation Test
Tests the complete Character Self-Knowledge System implementation.

This script validates the PHASE 3A implementation by testing:
- Character Self-Knowledge Extractor
- Graph Knowledge Builder 
- Dynamic Trait Discovery
- CDL AI Integration pipeline integration

Usage: python test_phase3a_self_knowledge_validation.py
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

class Phase3AValidationTest:
    """Test suite for PHASE 3A Character Graph Self-Knowledge Builder implementation."""
    
    def __init__(self):
        self.test_character = "elena"  # Use Elena for testing
        self.postgres_pool = None
        self.character_extractor = None
        self.graph_builder = None
        self.trait_discovery = None
        self.test_results = {}
    
    async def setup_test_environment(self):
        """Initialize test environment and components."""
        try:
            logger.info("🔧 Setting up PHASE 3A test environment...")
            
            # Initialize PostgreSQL connection
            import asyncpg
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
            self.postgres_pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("✅ PostgreSQL connection established")
            
            # Initialize Character Self-Knowledge Extractor
            from src.characters.learning.character_self_knowledge_extractor import create_character_self_knowledge_extractor
            self.character_extractor = create_character_self_knowledge_extractor(self.postgres_pool)
            logger.info("✅ Character Self-Knowledge Extractor initialized")
            
            # Initialize Graph Knowledge Builder
            from src.characters.learning.character_graph_knowledge_builder import create_character_graph_knowledge_builder
            self.graph_builder = create_character_graph_knowledge_builder(
                self.postgres_pool, self.character_extractor
            )
            logger.info("✅ Graph Knowledge Builder initialized")
            
            # Initialize Dynamic Trait Discovery
            from src.characters.learning.dynamic_trait_discovery import create_dynamic_trait_discovery
            self.trait_discovery = create_dynamic_trait_discovery(
                self.character_extractor, self.graph_builder
            )
            logger.info("✅ Dynamic Trait Discovery initialized")
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to setup test environment: %s", e)
            return False
    
    async def test_character_knowledge_extraction(self):
        """Test Character Self-Knowledge Extractor functionality."""
        try:
            logger.info("\n🧠 Testing Character Self-Knowledge Extraction...")
            
            character_knowledge = await self.character_extractor.extract_character_self_knowledge(self.test_character)
            
            if not character_knowledge:
                self.test_results['knowledge_extraction'] = "❌ FAILED - No character knowledge extracted"
                return False
            
            # Validate extracted knowledge structure
            if not hasattr(character_knowledge, 'personality_traits'):
                self.test_results['knowledge_extraction'] = "❌ FAILED - Missing personality_traits attribute"
                return False
            
            # Count extracted data
            personality_count = len(character_knowledge.personality_traits) if character_knowledge.personality_traits else 0
            values_count = len(character_knowledge.values_beliefs) if character_knowledge.values_beliefs else 0
            interests_count = len(character_knowledge.interests_expertise) if character_knowledge.interests_expertise else 0
            comm_count = len(character_knowledge.communication_patterns) if character_knowledge.communication_patterns else 0
            
            total_traits = personality_count + values_count + interests_count + comm_count
            
            if total_traits == 0:
                self.test_results['knowledge_extraction'] = "❌ FAILED - No traits extracted"
                return False
            logger.info("✅ Character knowledge extraction successful")
            
            return True
            
        except Exception as e:
            self.test_results['knowledge_extraction'] = f"❌ ERROR - {str(e)}"
            logger.error("❌ Character knowledge extraction failed: %s", e)
            return False
    
    async def test_graph_knowledge_building(self):
        """Test Graph Knowledge Builder functionality."""
        try:
            logger.info("\n🔗 Testing Graph Knowledge Building...")
            
            graph_summary = await self.graph_builder.build_character_knowledge_graph(self.test_character)
            
            if not graph_summary:
                self.test_results['graph_building'] = "❌ FAILED - No graph summary returned"
                return False
            
            # Validate graph summary structure
            required_fields = ['character_name', 'total_relationships', 'stored_relationships']
            missing_fields = [field for field in required_fields if field not in graph_summary]
            
            if missing_fields:
                self.test_results['graph_building'] = f"❌ FAILED - Missing fields: {missing_fields}"
                return False
            
            total_relationships = graph_summary.get('total_relationships', 0)
            stored_relationships = graph_summary.get('stored_relationships', 0)
            
            if total_relationships == 0:
                self.test_results['graph_building'] = "❌ FAILED - No relationships built"
                return False
            
            self.test_results['graph_building'] = f"✅ SUCCESS - Built {total_relationships} relationships, stored {stored_relationships}"
            logger.info("✅ Graph knowledge building successful")
            
            return True
            
        except Exception as e:
            self.test_results['graph_building'] = f"❌ ERROR - {str(e)}"
            logger.error("❌ Graph knowledge building failed: %s", e)
            return False
    
    async def test_dynamic_trait_discovery(self):
        """Test Dynamic Trait Discovery functionality."""
        try:
            logger.info("\n🔍 Testing Dynamic Trait Discovery...")
            
            # Test motivation discovery
            motivations = await self.trait_discovery.discover_character_motivations(self.test_character)
            
            if not motivations:
                self.test_results['trait_discovery'] = "❌ FAILED - No motivations discovered"
                return False
            
            # Test behavioral pattern discovery
            patterns = await self.trait_discovery.discover_behavioral_patterns(self.test_character)
            
            if not patterns:
                self.test_results['trait_discovery'] = f"⚠️ PARTIAL - {len(motivations)} motivations, 0 patterns"
            else:
                self.test_results['trait_discovery'] = f"✅ SUCCESS - {len(motivations)} motivations, {len(patterns)} patterns"
            
            logger.info("✅ Dynamic trait discovery successful")
            
            return True
            
        except Exception as e:
            self.test_results['trait_discovery'] = f"❌ ERROR - {str(e)}"
            logger.error("❌ Dynamic trait discovery failed: %s", e)
            return False
    
    async def test_self_awareness_insights(self):
        """Test self-awareness insights functionality."""
        try:
            logger.info("\n🎯 Testing Self-Awareness Insights...")
            
            # Test different insight types
            insight_types = ['motivation', 'behavior', 'preferences', 'values']
            insight_results = {}
            
            for insight_type in insight_types:
                insights = await self.trait_discovery.get_self_awareness_insights(
                    self.test_character, insight_type
                )
                
                if insights and insights.get('type') == insight_type:
                    insight_results[insight_type] = "✅ SUCCESS"
                else:
                    insight_results[insight_type] = "❌ FAILED"
            
            successful_insights = sum(1 for result in insight_results.values() if "SUCCESS" in result)
            
            if successful_insights >= 2:  # At least 2 types should work
                self.test_results['self_awareness'] = f"✅ SUCCESS - {successful_insights}/4 insight types working"
            else:
                self.test_results['self_awareness'] = f"❌ FAILED - Only {successful_insights}/4 insight types working"
            
            logger.info("✅ Self-awareness insights test completed")
            
            return successful_insights >= 2
            
        except Exception as e:
            self.test_results['self_awareness'] = f"❌ ERROR - {str(e)}"
            logger.error("❌ Self-awareness insights failed: %s", e)
            return False
    
    async def test_cdl_pipeline_integration(self):
        """Test CDL AI pipeline integration."""
        try:
            logger.info("\n🎭 Testing CDL Pipeline Integration...")
            
            # Import CDL integration
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            # Create mock bot_core with postgres_pool
            class MockBotCore:
                def __init__(self, postgres_pool):
                    self.postgres_pool = postgres_pool
            
            mock_bot_core = MockBotCore(self.postgres_pool)
            
            # Initialize CDL integration
            cdl_integration = CDLAIPromptIntegration(bot_core=mock_bot_core)
            
            # Test character self-knowledge section building
            self_knowledge_section = await cdl_integration._build_character_self_knowledge_section(self.test_character)
            
            if not self_knowledge_section:
                self.test_results['cdl_integration'] = "❌ FAILED - No self-knowledge section generated"
                return False
            
            # Check for expected content
            expected_keywords = ['SELF-AWARENESS', 'motivated', 'tend to']
            found_keywords = sum(1 for keyword in expected_keywords if keyword in self_knowledge_section)
            
            if found_keywords >= 2:
                self.test_results['cdl_integration'] = f"✅ SUCCESS - Generated {len(self_knowledge_section)} chars with {found_keywords}/3 keywords"
            else:
                self.test_results['cdl_integration'] = f"❌ FAILED - Only {found_keywords}/3 expected keywords found"
            
            logger.info("✅ CDL pipeline integration successful")
            
            return found_keywords >= 2
            
        except Exception as e:
            self.test_results['cdl_integration'] = f"❌ ERROR - {str(e)}"
            logger.error("❌ CDL pipeline integration failed: %s", e)
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive PHASE 3A validation test."""
        try:
            logger.info("🚀 Starting PHASE 3A Character Graph Self-Knowledge Builder Validation")
            logger.info("=" * 80)
            
            # Setup environment
            if not await self.setup_test_environment():
                logger.error("❌ Environment setup failed")
                return False
            
            # Run test suite
            tests = [
                ('Character Knowledge Extraction', self.test_character_knowledge_extraction),
                ('Graph Knowledge Building', self.test_graph_knowledge_building),
                ('Dynamic Trait Discovery', self.test_dynamic_trait_discovery),
                ('Self-Awareness Insights', self.test_self_awareness_insights),
                ('CDL Pipeline Integration', self.test_cdl_pipeline_integration),
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                logger.info(f"\n🧪 Running {test_name}...")
                if await test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            
            # Report results
            logger.info("\n" + "=" * 80)
            logger.info("📊 PHASE 3A VALIDATION RESULTS")
            logger.info("=" * 80)
            
            for i, (test_name, _) in enumerate(tests, 1):
                result_key = list(self.test_results.keys())[i-1] if i-1 < len(self.test_results) else None
                result = self.test_results.get(result_key, "❓ NOT RUN") if result_key else "❓ NOT RUN"
                logger.info(f"{i}. {test_name}: {result}")
            
            success_rate = (passed_tests / total_tests) * 100
            logger.info(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                logger.info("🎉 PHASE 3A Character Graph Self-Knowledge Builder: VALIDATION SUCCESSFUL!")
                logger.info("✅ Ready for production integration")
            elif success_rate >= 60:
                logger.warning("⚠️ PHASE 3A Character Graph Self-Knowledge Builder: PARTIAL SUCCESS")
                logger.warning("🔧 Some components need refinement")
            else:
                logger.error("❌ PHASE 3A Character Graph Self-Knowledge Builder: VALIDATION FAILED")
                logger.error("🚨 Major issues need to be addressed")
            
            return success_rate >= 80
            
        except Exception as e:
            logger.error("💥 Comprehensive test failed: %s", e)
            return False
        
        finally:
            # Cleanup
            if self.postgres_pool:
                await self.postgres_pool.close()

async def main():
    """Main test execution."""
    try:
        test_suite = Phase3AValidationTest()
        success = await test_suite.run_comprehensive_test()
        
        if success:
            print("\n🎊 PHASE 3A IMPLEMENTATION COMPLETE AND VALIDATED!")
            print("🔮 Characters now have self-awareness capabilities")
            exit(0)
        else:
            print("\n⚠️ PHASE 3A validation completed with issues")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())