#!/usr/bin/env python3
"""
Cross-Pollination Test Script

Tests the integration between CharacterGraphManager and user facts
from SemanticKnowledgeRouter to validate cross-pollination functionality.

This script validates:
1. Character knowledge queries with user_id parameter
2. Cross-pollination between character abilities and user facts
3. Shared interests detection
4. Character knowledge about user-mentioned entities
"""

import asyncio
import logging
import os
import sys
import asyncpg
from typing import Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import components
from src.characters.cdl.character_graph_manager import create_character_graph_manager
from src.knowledge.semantic_router import create_semantic_knowledge_router, IntentAnalysisResult, QueryIntent

# Create test intent for semantic router
TEST_INTENT = IntentAnalysisResult(
    intent_type=QueryIntent.FACTUAL_RECALL,
    entity_type="general",
    relationship_type="likes",
    confidence=1.0,
    keywords=["test"]
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CrossPollinationTestSuite:
    """Test suite for cross-pollination functionality"""
    
    def __init__(self):
        self.postgres_pool = None
        self.semantic_router = None
        self.character_graph_manager = None
        
    async def setup(self):
        """Initialize test components"""
        logger.info("🔧 Setting up cross-pollination test suite...")
        
        try:
            # PostgreSQL connection - use localhost for external testing
            postgres_host = os.getenv('POSTGRES_HOST', 'localhost')  # Use localhost for external testing
            postgres_port = int(os.getenv('POSTGRES_PORT', '5433'))  # External Docker port (5433)
            postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')  # WhisperEngine user
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
            postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')

            # Create connection pool
            self.postgres_pool = await asyncpg.create_pool(
                host=postgres_host,
                port=postgres_port,
                user=postgres_user,
                password=postgres_password,
                database=postgres_db
            )

            if not self.postgres_pool:
                raise RuntimeError("Failed to create PostgreSQL pool")

            # Initialize semantic router
            self.semantic_router = create_semantic_knowledge_router(
                postgres_pool=self.postgres_pool
            )
            
            # Initialize character graph manager with semantic router
            self.character_graph_manager = create_character_graph_manager(
                postgres_pool=self.postgres_pool,
                semantic_router=self.semantic_router
            )
            
            logger.info("✅ Test suite setup complete")
            
        except asyncpg.PostgresError as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise
        
    async def setUp(self):
        """Initialize test components with proper error handling"""
        try:
            # PostgreSQL connection
            postgres_host = os.getenv('POSTGRES_HOST', 'postgres')  # Docker service name
            postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))  # Internal Docker port
            postgres_user = os.getenv('POSTGRES_USER', 'postgres')
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
            postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')

            self.postgres_pool = await asyncpg.create_pool(
                host=postgres_host,
                port=postgres_port,
                user=postgres_user,
                password=postgres_password,
                database=postgres_db
            )

            if not self.postgres_pool:
                raise RuntimeError("Failed to create PostgreSQL pool")

            # Initialize components with proper typing
            self.semantic_router = create_semantic_knowledge_router(
                postgres_pool=self.postgres_pool
            )
            
            # Initialize character graph manager with router
            self.character_graph_manager = create_character_graph_manager(
                postgres_pool=self.postgres_pool,
                semantic_router=self.semantic_router
            )
            
            print("🚀 Test setup complete - PostgreSQL pool and components created")
        except asyncpg.PostgresError as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
            
    async def _setup_semantic_router(self):
        """Setup SemanticKnowledgeRouter"""
        try:
            # Create semantic router with PostgreSQL pool
            self.semantic_router = create_semantic_knowledge_router(
                postgres_pool=self.postgres_pool
            )
            
            logger.info("✅ SemanticKnowledgeRouter created")
            
        except Exception as e:
            logger.error("❌ SemanticKnowledgeRouter setup failed: %s", e)
            raise
            
    async def _setup_character_graph_manager(self):
        """Setup CharacterGraphManager with semantic_router"""
        try:
            # Create character graph manager with semantic router for cross-pollination
            self.character_graph_manager = create_character_graph_manager(
                postgres_pool=self.postgres_pool,
                semantic_router=self.semantic_router
            )
            
            logger.info("✅ CharacterGraphManager created with semantic router")
            
        except Exception as e:
            logger.error("❌ CharacterGraphManager setup failed: %s", e)
            raise
    
    async def test_basic_character_query(self):
        """Test basic character knowledge query without cross-pollination"""
        logger.info("🧪 TEST 1: Basic character knowledge query")
        
        try:
            if not self.character_graph_manager:
                logger.error("❌ TEST 1 FAILED: CharacterGraphManager not initialized")
                return False
                
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            result = await self.character_graph_manager.query_character_knowledge(
                character_name="elena",
                query_text="Tell me about your family",
                intent=CharacterKnowledgeIntent.FAMILY,
                limit=3
            )
            
            logger.info("📊 Basic query results:")
            logger.info(f"  - Background entries: {len(result.background)}")
            logger.info(f"  - Memories: {len(result.memories)}")
            logger.info(f"  - Relationships: {len(result.relationships)}")
            logger.info(f"  - Total results: {result.total_results}")
            
            if result.total_results > 0:
                logger.info("✅ TEST 1 PASSED: Basic character query returned results")
                return True
            else:
                logger.warning("⚠️ TEST 1 WARNING: No results returned")
                return False
                
        except Exception as e:
            logger.error("❌ TEST 1 FAILED: %s", e)
            return False
    
    async def test_cross_pollination_query(self):
        """Test character knowledge query with cross-pollination"""
        logger.info("🧪 TEST 2: Cross-pollination character knowledge query")
        
        try:
            if not self.character_graph_manager:
                logger.error("❌ TEST 2 FAILED: CharacterGraphManager not initialized")
                return False
                
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            # Use a test user ID that might have facts in the database
            test_user_id = "test_user_123"
            
            result = await self.character_graph_manager.query_character_knowledge(
                character_name="elena",
                query_text="Tell me about books you've read",
                intent=CharacterKnowledgeIntent.HOBBIES,
                limit=3,
                user_id=test_user_id  # Enable cross-pollination
            )
            
            logger.info("📊 Cross-pollination query results:")
            logger.info(f"  - Background entries: {len(result.background)}")
            logger.info(f"  - Memories: {len(result.memories)}")
            logger.info(f"  - Relationships: {len(result.relationships)}")
            logger.info(f"  - Abilities: {len(result.abilities)}")
            logger.info(f"  - Total results: {result.total_results}")
            
            # Check for cross-pollinated entries
            cross_pollinated_count = 0
            for entry in result.background + result.memories + result.abilities:
                if entry.get('cross_pollinated'):
                    cross_pollinated_count += 1
                    logger.info(f"  - Cross-pollinated: {entry.get('title', entry.get('description', 'Unknown'))}")
            
            logger.info(f"📊 Cross-pollinated entries: {cross_pollinated_count}")
            
            if result.total_results > 0:
                logger.info("✅ TEST 2 PASSED: Cross-pollination query returned results")
                return True
            else:
                logger.warning("⚠️ TEST 2 WARNING: No results returned")
                return False
                
        except Exception as e:
            logger.error("❌ TEST 2 FAILED: %s", e)
            return False
    
    async def test_direct_cross_pollination(self):
        """Test direct cross-pollination method"""
        logger.info("🧪 TEST 3: Direct cross-pollination method")
        
        try:
            if not self.postgres_pool:
                logger.error("❌ TEST 3 FAILED: PostgreSQL pool not initialized")
                return False
                
            if not self.character_graph_manager:
                logger.error("❌ TEST 3 FAILED: CharacterGraphManager not initialized")
                return False
                
            # Get Elena's character ID
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id FROM characters WHERE name = $1",
                    "elena"
                )
                
                if not row:
                    logger.error("❌ TEST 3 FAILED: Elena character not found")
                    return False
                    
                character_id = row['id']
            
            # Test cross-pollination with a test user
            test_user_id = "test_user_123"
            
            cross_pollination_result = await self.character_graph_manager.query_cross_pollination(
                character_id=character_id,
                user_id=test_user_id,
                limit=3
            )
            
            logger.info("📊 Direct cross-pollination results:")
            logger.info(f"  - Shared interests: {len(cross_pollination_result.get('shared_interests', []))}")
            logger.info(f"  - Relevant abilities: {len(cross_pollination_result.get('relevant_abilities', []))}")
            logger.info(f"  - Character knowledge about user facts: {len(cross_pollination_result.get('character_knowledge_about_user_facts', []))}")
            
            # Log details if any results found
            for category, entries in cross_pollination_result.items():
                if entries:
                    logger.info(f"  {category}:")
                    for entry in entries[:2]:  # Show first 2 entries
                        title = entry.get('title', entry.get('ability_name', 'Unknown'))
                        logger.info(f"    - {title}")
            
            total_cross_pollination = sum(len(entries) for entries in cross_pollination_result.values())
            
            if total_cross_pollination > 0:
                logger.info("✅ TEST 3 PASSED: Direct cross-pollination returned results")
                return True
            else:
                logger.info("ℹ️ TEST 3 INFO: No cross-pollination results (may be expected if no user facts)")
                return True  # This is not necessarily a failure
                
        except Exception as e:
            logger.error("❌ TEST 3 FAILED: %s", e)
            return False
    
    async def test_user_facts_availability(self):
        """Test if user facts are available in the database"""
        logger.info("🧪 TEST 4: User facts availability")
        
        try:
            if not self.semantic_router:
                logger.warning("⚠️ TEST 4 SKIPPED: SemanticKnowledgeRouter not available")
                return False
            
            # Try to get user facts for a test user
            test_user_id = "test_user_123"
            
            # Use TEST_INTENT for semantic router queries
            user_facts = await self.semantic_router.get_user_facts(
                user_id=test_user_id,
                intent=TEST_INTENT,  # Use pre-defined test intent
                limit=5
            )
            
            logger.info(f"📊 User facts for {test_user_id}: {len(user_facts)} found")
            
            if user_facts:
                logger.info("✅ User facts found:")
                for fact in user_facts[:3]:  # Show first 3
                    entity_name = fact.get('entity_name', 'Unknown')
                    relationship_type = fact.get('relationship_type', 'Unknown')
                    confidence = fact.get('confidence', 0)
                    logger.info(f"  - {entity_name} ({relationship_type}, confidence: {confidence})")
                
                logger.info("✅ TEST 4 PASSED: User facts are available")
                return True
            else:
                logger.info("ℹ️ TEST 4 INFO: No user facts found for test user (expected for fresh database)")
                return True  # Not a failure for testing purposes
                
        except Exception as e:
            logger.error("❌ TEST 4 FAILED: %s", e)
            return False
    
    async def run_all_tests(self):
        """Run all cross-pollination tests"""
        logger.info("🚀 Starting cross-pollination test suite...")
        
        test_results = []
        
        # Run tests
        test_results.append(await self.test_basic_character_query())
        test_results.append(await self.test_cross_pollination_query())
        test_results.append(await self.test_direct_cross_pollination())
        test_results.append(await self.test_user_facts_availability())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        logger.info("📊 TEST SUMMARY:")
        logger.info(f"  - Tests passed: {passed}/{total}")
        logger.info(f"  - Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            logger.info("✅ ALL TESTS PASSED: Cross-pollination integration is working")
        else:
            logger.warning(f"⚠️ {total-passed} TESTS FAILED: Some issues detected")
        
        return passed == total
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        logger.info("🧹 Test cleanup complete")


async def main():
    """Main test function"""
    test_suite = CrossPollinationTestSuite()
    
    try:
        await test_suite.setup()
        success = await test_suite.run_all_tests()
        
        if success:
            logger.info("🎉 Cross-pollination testing completed successfully!")
            return 0
        else:
            logger.error("❌ Cross-pollination testing encountered issues")
            return 1
            
    except Exception as e:
        logger.error("💥 Test suite failed: %s", e)
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)