#!/usr/bin/env python3
"""
Test Tyler Art Advice Discovery in ChromaDB
Verify that Tyler's enhanced summaries make his art advice discoverable
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.memory.core.storage_abstraction import HierarchicalMemoryManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TylerAdviceDiscoveryTester:
    """Test Tyler's art advice discovery through ChromaDB semantic search"""
    
    def __init__(self):
        self.memory_manager = None
        
    async def initialize(self):
        """Initialize memory manager with ChromaDB connection"""
        config = {
            'redis_enabled': False,
            'postgresql_enabled': False,
            'chromadb': {
                'host': 'whisperengine-chromadb',
                'port': 8000,
                'collection_name': 'hierarchical_conversations'
            },
            'neo4j_enabled': False
        }
        
        self.memory_manager = HierarchicalMemoryManager(config)
        
        # Initialize only ChromaDB tier for testing
        await self.memory_manager._init_tier3_semantic()
        
    async def test_tyler_discovery(self):
        """Test discovering Tyler's art advice through semantic search"""
        if not self.memory_manager.tier3_semantic:
            logger.error("ChromaDB not initialized - cannot test discovery")
            return
            
        # Test queries that should find Tyler's art advice
        tyler_queries = [
            "Tyler art composition advice",
            "digital art mentorship tips",
            "rule of thirds art techniques", 
            "art mentor guidance",
            "composition improvement techniques",
            "silhouette art advice"
        ]
        
        logger.info("🎯 Testing Tyler Art Advice Discovery")
        logger.info("=" * 50)
        
        total_tyler_results = 0
        
        for query in tyler_queries:
            logger.info(f"\n🔍 Searching: '{query}'")
            
            try:
                # Search ChromaDB for Tyler-related content
                results = await self.memory_manager.tier3_semantic.search_similar_summaries(
                    query=query,
                    limit=3
                )
                
                if results:
                    logger.info(f"  Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        summary = result.get('summary', 'No summary')
                        score = result.get('score', result.get('distance', 'Unknown'))
                        
                        # Check if this looks like Tyler/instructional content
                        is_tyler_content = any(keyword in summary.lower() for keyword in [
                            'tyler', 'mentor', 'step', 'technique', 'composition', 
                            'assignment', 'practice', 'guide'
                        ])
                        
                        # Check for enhanced summary length (should be longer for Tyler)
                        is_enhanced = len(summary) > 150
                        
                        status = "✅ TYLER/ENHANCED" if is_tyler_content and is_enhanced else "📝 Regular"
                        
                        logger.info(f"    {i}. {status} (score: {score})")
                        logger.info(f"       Length: {len(summary)} chars")
                        logger.info(f"       Summary: {summary[:200]}...")
                        
                        if is_tyler_content:
                            total_tyler_results += 1
                            
                else:
                    logger.info("  No results found")
                    
            except Exception as e:
                logger.error(f"  Error searching for '{query}': {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"🎯 DISCOVERY TEST RESULTS")
        logger.info(f"Total Tyler/instructional results found: {total_tyler_results}")
        
        if total_tyler_results > 0:
            logger.info("✅ SUCCESS: Tyler's art advice is discoverable!")
            logger.info("🎨 Enhanced summaries are working for semantic search")
        else:
            logger.info("⚠️ Tyler content not found - may need to check import or rebuild")
            
        return total_tyler_results
        
    async def test_collection_stats(self):
        """Check ChromaDB collection statistics"""
        if not self.memory_manager.tier3_semantic:
            logger.error("ChromaDB not initialized")
            return
            
        try:
            # Try to get collection info
            collection = self.memory_manager.tier3_semantic.collection
            count = collection.count()
            
            logger.info(f"\n📊 ChromaDB Collection Stats:")
            logger.info(f"  Total conversations: {count}")
            
            # Get a sample to check summary quality
            if count > 0:
                sample = collection.get(limit=5)
                if sample and sample.get('documents'):
                    logger.info(f"  Sample summaries:")
                    for i, doc in enumerate(sample['documents'][:3], 1):
                        length = len(doc)
                        is_enhanced = length > 150
                        logger.info(f"    {i}. {length} chars {'(Enhanced)' if is_enhanced else '(Standard)'}: {doc[:100]}...")
                        
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
    
    async def run_test(self):
        """Run the complete Tyler discovery test"""
        try:
            await self.initialize()
            await self.test_collection_stats()
            tyler_results = await self.test_tyler_discovery()
            
            if tyler_results > 0:
                logger.info("\n🎉 Tyler Art Advice Discovery Test PASSED!")
                logger.info("Your enhanced summarization is working perfectly!")
            else:
                logger.info("\n⚠️ No Tyler content found - check if conversations need reimport")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

async def main():
    """Run Tyler discovery test"""
    tester = TylerAdviceDiscoveryTester()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())