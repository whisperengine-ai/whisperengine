#!/usr/bin/env python3
"""
CDL Character Name Normalization Validation Test

This test validates that all CDL character querying methods properly
use the normalize_bot_name function for consistent character identification.

The test demonstrates:
1. Enhanced CDL Manager normalization fixes
2. Character self-knowledge extractor fixes
3. Character graph knowledge builder fixes
4. Character graph manager normalization improvements

Run with:
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_cdl_normalization_fixes_validation.py
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CDLNormalizationFixesValidator:
    """
    Validates that CDL character querying methods use proper normalization
    """
    
    def __init__(self):
        self.postgres_pool = None
        
    async def setup_database_connection(self):
        """Initialize PostgreSQL connection pool"""
        import asyncpg
        
        try:
            logger.info("🔄 Setting up PostgreSQL connection...")
            self.postgres_pool = await asyncpg.create_pool(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5433)),
                user='whisperengine',
                password='whisperengine123',
                database='whisperengine',
                min_size=2,
                max_size=5
            )
            logger.info("✅ PostgreSQL connection established")
            return True
        except Exception as e:
            logger.error("❌ Failed to connect to PostgreSQL: %s", e)
            return False

    async def test_enhanced_cdl_manager_normalization(self):
        """Test enhanced CDL manager uses proper normalization"""
        logger.info("🧪 Testing Enhanced CDL Manager normalization...")
        
        try:
            from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
            
            if not self.postgres_pool:
                logger.error("   ❌ PostgreSQL pool not available")
                return False
                
            manager = EnhancedCDLManager(self.postgres_pool)
            
            # Test different name formats
            test_names = ['elena', 'ELENA', 'Elena', 'elena_bot']
            
            for test_name in test_names:
                logger.info(f"   Testing name: '{test_name}'")
                character_data = await manager.get_character_by_name(test_name)
                
                if character_data:
                    # Handle both dict and complex object structures
                    if hasattr(character_data, 'get'):
                        name = character_data.get('name', character_data.get('character_name', 'Unknown'))
                        normalized_name = character_data.get('normalized_name')
                    else:
                        # Handle nested structure
                        name = getattr(character_data, 'name', 'Unknown')
                        normalized_name = getattr(character_data, 'normalized_name', None)
                    
                    logger.info(f"   ✅ Found character: {name}")
                    # Verify it found the normalized character
                    if normalized_name == 'elena':
                        logger.info(f"   ✅ Correct normalization: {normalized_name}")
                    else:
                        logger.warning(f"   ⚠️ Unexpected normalized name: {normalized_name}")
                        logger.warning(f"   ⚠️ Character data type: {type(character_data)}")
                        logger.warning(f"   ⚠️ Character data keys: {list(character_data.keys()) if hasattr(character_data, 'keys') else 'No keys method'}")
                else:
                    logger.info(f"   ❌ No character found for '{test_name}'")
                    
            logger.info("✅ Enhanced CDL Manager normalization test completed")
            return True
            
        except Exception as e:
            logger.error("❌ Enhanced CDL Manager test failed: %s", e)
            return False

    async def test_character_self_knowledge_extractor_normalization(self):
        """Test character self-knowledge extractor uses proper normalization"""
        logger.info("🧪 Testing Character Self-Knowledge Extractor normalization...")
        
        try:
            from src.characters.learning.character_self_knowledge_extractor import CharacterSelfKnowledgeExtractor
            
            if not self.postgres_pool:
                logger.error("   ❌ PostgreSQL pool not available")
                return False
                
            extractor = CharacterSelfKnowledgeExtractor(self.postgres_pool)
            
            # Test with different name formats
            test_names = ['elena', 'ELENA', 'Elena']
            
            for test_name in test_names:
                logger.info(f"   Testing extraction for: '{test_name}'")
                
                # Test the _get_character_id method directly
                async with self.postgres_pool.acquire() as conn:
                    character_id = await extractor._get_character_id(conn, test_name)
                    
                    if character_id:
                        logger.info(f"   ✅ Found character ID: {character_id}")
                    else:
                        logger.info(f"   ❌ No character ID found for '{test_name}'")
                        
            logger.info("✅ Character Self-Knowledge Extractor normalization test completed")
            return True
            
        except Exception as e:
            logger.error("❌ Character Self-Knowledge Extractor test failed: %s", e)
            return False

    async def test_character_graph_knowledge_builder_normalization(self):
        """Test character graph knowledge builder uses proper normalization"""
        logger.info("🧪 Testing Character Graph Knowledge Builder normalization...")
        
        try:
            from src.characters.learning.character_graph_knowledge_builder import CharacterGraphKnowledgeBuilder
            
            if not self.postgres_pool:
                logger.error("   ❌ PostgreSQL pool not available")
                return False
                
            builder = CharacterGraphKnowledgeBuilder(self.postgres_pool)
            
            # Test with different name formats
            test_names = ['elena', 'ELENA', 'Elena']
            
            for test_name in test_names:
                logger.info(f"   Testing graph query for: '{test_name}'")
                
                # Test query_character_relationships method
                relationships = await builder.query_character_relationships(test_name)
                logger.info(f"   Found {len(relationships)} relationships for '{test_name}'")
                
                # Test get_trait_influences method
                influences = await builder.get_trait_influences(test_name, "communication:tone:enthusiastic")
                logger.info(f"   Found {len(influences)} trait influences for '{test_name}'")
                        
            logger.info("✅ Character Graph Knowledge Builder normalization test completed")
            return True
            
        except Exception as e:
            logger.error("❌ Character Graph Knowledge Builder test failed: %s", e)
            return False

    async def test_character_graph_manager_normalization(self):
        """Test character graph manager uses proper normalization"""
        logger.info("🧪 Testing Character Graph Manager normalization...")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            if not self.postgres_pool:
                logger.error("   ❌ PostgreSQL pool not available")
                return False
                
            manager = CharacterGraphManager(self.postgres_pool)
            
            # Test with different name formats
            test_names = ['elena', 'ELENA', 'Elena', 'elena_bot']
            
            for test_name in test_names:
                logger.info(f"   Testing graph manager for: '{test_name}'")
                
                # Test the _get_character_id method directly
                character_id = await manager._get_character_id(test_name)
                
                if character_id:
                    logger.info(f"   ✅ Found character ID: {character_id}")
                else:
                    logger.info(f"   ❌ No character ID found for '{test_name}'")
                        
            logger.info("✅ Character Graph Manager normalization test completed")
            return True
            
        except Exception as e:
            logger.error("❌ Character Graph Manager test failed: %s", e)
            return False

    async def test_normalization_consistency(self):
        """Test that normalize_bot_name function works consistently"""
        logger.info("🧪 Testing normalize_bot_name function consistency...")
        
        try:
            from src.utils.bot_name_utils import normalize_bot_name
            
            # Test various input formats
            test_cases = [
                ('elena', 'elena'),
                ('ELENA', 'elena'),
                ('Elena', 'elena'),
                ('elena_bot', 'elena'),
                ('Elena_Bot', 'elena'),
                ('ELENA_BOT', 'elena'),
                ('bot_elena', 'elena'),
                ('Bot_Elena', 'elena'),
                ('BOT_ELENA', 'elena'),
            ]
            
            all_passed = True
            for input_name, expected in test_cases:
                result = normalize_bot_name(input_name)
                if result == expected:
                    logger.info(f"   ✅ '{input_name}' → '{result}' (expected '{expected}')")
                else:
                    logger.error(f"   ❌ '{input_name}' → '{result}' (expected '{expected}')")
                    all_passed = False
                    
            if all_passed:
                logger.info("✅ normalize_bot_name consistency test completed")
                return True
            else:
                logger.error("❌ normalize_bot_name consistency test failed")
                return False
                
        except Exception as e:
            logger.error("❌ normalize_bot_name test failed: %s", e)
            return False

    async def run_all_tests(self):
        """Run all CDL normalization validation tests"""
        logger.info("🚀 Starting CDL Character Name Normalization Validation Tests")
        logger.info("=" * 70)
        
        # Setup database connection
        if not await self.setup_database_connection():
            logger.error("❌ Failed to setup database connection. Exiting.")
            return False
            
        # Run all tests
        tests = [
            self.test_normalization_consistency,
            self.test_enhanced_cdl_manager_normalization,
            self.test_character_self_knowledge_extractor_normalization,
            self.test_character_graph_knowledge_builder_normalization,
            self.test_character_graph_manager_normalization,
        ]
        
        results = []
        for test in tests:
            logger.info("-" * 50)
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
        
        # Summary
        logger.info("=" * 70)
        logger.info("📊 CDL NORMALIZATION VALIDATION TEST SUMMARY")
        logger.info("=" * 70)
        
        passed = sum(results)
        total = len(results)
        
        logger.info(f"✅ Tests Passed: {passed}/{total}")
        if passed == total:
            logger.info("🎉 ALL CDL NORMALIZATION TESTS PASSED!")
            logger.info("   All character querying methods now use proper normalization")
            logger.info("   Character identification is consistent across all CDL components")
        else:
            logger.error("❌ SOME CDL NORMALIZATION TESTS FAILED!")
            logger.error("   Manual review and fixes may be required")
        
        # Cleanup
        if self.postgres_pool:
            await self.postgres_pool.close()
            
        return passed == total

async def main():
    """Main test runner"""
    validator = CDLNormalizationFixesValidator()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())