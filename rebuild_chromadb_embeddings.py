#!/usr/bin/env python3
"""
Rebuild ChromaDB embeddings from existing PostgreSQL conversations
This script fixes the missing embeddings issue discovered during the ChatGPT import debugging
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.memory.core.storage_abstraction import HierarchicalMemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChromaDBEmbeddingRebuilder:
    """Rebuild missing ChromaDB embeddings from PostgreSQL conversation data"""
    
    def __init__(self):
        self.memory_manager = None
        
    async def initialize(self):
        """Initialize memory manager and database connections"""
        try:
            # Create memory manager configuration for Docker environment
            config = {
                'redis': {
                    'url': 'redis://whisperengine-redis:6379',
                    'ttl': 1800
                },
                'postgresql': {
                    'url': 'postgresql://bot_user:securepassword123@whisperengine-postgres:5432/whisper_engine'
                },
                'chromadb': {
                    'host': 'whisperengine-chromadb',
                    'port': 8000
                },
                'neo4j_enabled': False  # Disable for this script
            }
            
            # Initialize hierarchical memory manager
            self.memory_manager = HierarchicalMemoryManager(config)
            await self.memory_manager.initialize()
            logger.info("✅ Memory manager initialized")
            
        except Exception as e:
            logger.error("❌ Failed to initialize: %s", e)
            raise
    
    async def get_all_conversations(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all conversations from PostgreSQL"""
        try:
            if not self.memory_manager.tier2_archive:
                raise Exception("PostgreSQL archive not available")
            
            # Use the connection pool to query directly
            async with self.memory_manager.tier2_archive.pool.acquire() as conn:
                if limit:
                    query = """
                        SELECT conversation_id as id, user_id, user_message, bot_response, 
                               timestamp, session_id, channel_id, user_metadata, processing_metadata
                        FROM conversations 
                        ORDER BY timestamp DESC 
                        LIMIT $1
                    """
                    rows = await conn.fetch(query, limit)
                else:
                    query = """
                        SELECT conversation_id as id, user_id, user_message, bot_response, 
                               timestamp, session_id, channel_id, user_metadata, processing_metadata
                        FROM conversations 
                        ORDER BY timestamp DESC
                    """
                    rows = await conn.fetch(query)
            
            # Convert to list of dicts
            conversations = []
            for row in rows:
                conv_dict = dict(row)
                # Convert UUID to string
                if conv_dict['id']:
                    conv_dict['id'] = str(conv_dict['id'])
                if conv_dict.get('session_id'):
                    conv_dict['session_id'] = str(conv_dict['session_id'])
                
                # Combine metadata
                metadata = {}
                if conv_dict.get('user_metadata'):
                    metadata.update(conv_dict['user_metadata'])
                if conv_dict.get('processing_metadata'):
                    metadata.update(conv_dict['processing_metadata'])
                if conv_dict.get('channel_id'):
                    metadata['channel_id'] = conv_dict['channel_id']
                if conv_dict.get('session_id'):
                    metadata['session_id'] = conv_dict['session_id']
                
                conv_dict['metadata'] = metadata
                conversations.append(conv_dict)
            
            logger.info("📊 Found %d conversations in PostgreSQL", len(conversations))
            return conversations
            
        except Exception as e:
            logger.error("❌ Failed to get conversations: %s", e)
            return []
    
    async def check_chromadb_status(self) -> Dict[str, Any]:
        """Check current ChromaDB collection status"""
        try:
            # Access the ChromaDB tier directly
            if not self.memory_manager.tier3_semantic:
                return {"error": "ChromaDB tier not available"}
            
            chromadb_tier = self.memory_manager.tier3_semantic
            
            # Get collection counts
            summaries_count = chromadb_tier.summaries_collection.count()
            topics_count = chromadb_tier.topics_collection.count() if chromadb_tier.topics_collection else 0
            
            return {
                "summaries_collection_count": summaries_count,
                "topics_collection_count": topics_count,
                "status": "operational"
            }
            
        except Exception as e:
            logger.error("❌ Failed to check ChromaDB status: %s", e)
            return {"error": str(e)}
    
    async def rebuild_embeddings_for_conversation(
        self, 
        conversation: Dict[str, Any]
    ) -> bool:
        """Rebuild embeddings for a single conversation"""
        try:
            conversation_id = conversation['id']
            user_id = conversation['user_id']
            user_message = conversation['user_message']
            bot_response = conversation['bot_response']
            metadata = conversation.get('metadata', {})
            
            # Generate summary using the memory manager's logic
            summary = await self.memory_manager._generate_conversation_summary(
                user_message, bot_response
            )
            
            # Store the summary in ChromaDB
            if self.memory_manager.tier3_semantic:
                await self.memory_manager.tier3_semantic.store_summary(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    summary=summary,
                    metadata=metadata
                )
                
                logger.debug("✅ Rebuilt embedding for conversation %s", conversation_id)
                return True
            else:
                logger.warning("⚠️ ChromaDB tier not available for conversation %s", conversation_id)
                return False
                
        except Exception as e:
            logger.error("❌ Failed to rebuild embedding for conversation %s: %s", 
                        conversation.get('id', 'unknown'), e)
            return False
    
    async def rebuild_all_embeddings(
        self, 
        batch_size: int = 50,
        max_conversations: Optional[int] = None
    ) -> Dict[str, Any]:
        """Rebuild all missing embeddings in batches"""
        start_time = datetime.now()
        stats = {
            "total_conversations": 0,
            "processed_conversations": 0,
            "successful_embeddings": 0,
            "failed_embeddings": 0,
            "errors": []
        }
        
        try:
            # Check initial ChromaDB status
            initial_status = await self.check_chromadb_status()
            logger.info("📊 Initial ChromaDB status: %s", initial_status)
            
            # Get conversations that need embeddings
            conversations = await self.get_all_conversations(limit=max_conversations)
            stats["total_conversations"] = len(conversations)
            
            if not conversations:
                logger.info("ℹ️ No conversations found to process")
                return stats
            
            logger.info("🚀 Starting embedding rebuild for %d conversations", len(conversations))
            
            # Process in batches to avoid overwhelming the system
            for i in range(0, len(conversations), batch_size):
                batch_start = i
                batch_end = min(i + batch_size, len(conversations))
                batch = conversations[batch_start:batch_end]
                
                batch_num = batch_start//batch_size + 1
                logger.info("📦 Processing batch %d: conversations %d-%d", 
                           batch_num, batch_start+1, batch_end)
                
                # Process batch
                batch_results = await asyncio.gather(
                    *[self.rebuild_embeddings_for_conversation(conv) for conv in batch],
                    return_exceptions=True
                )
                
                # Count results
                for result in batch_results:
                    stats["processed_conversations"] += 1
                    if isinstance(result, Exception):
                        stats["failed_embeddings"] += 1
                        stats["errors"].append(str(result))
                    elif result:
                        stats["successful_embeddings"] += 1
                    else:
                        stats["failed_embeddings"] += 1
                
                # Small delay between batches
                if batch_end < len(conversations):
                    await asyncio.sleep(0.5)
                
                # Progress update
                progress = (batch_end / len(conversations)) * 100
                logger.info("📈 Progress: %.1f%% (%d successful, %d failed)", 
                           progress, stats['successful_embeddings'], stats['failed_embeddings'])
            
            # Final status check
            final_status = await self.check_chromadb_status()
            logger.info("📊 Final ChromaDB status: %s", final_status)
            
            # Calculate timing
            duration = (datetime.now() - start_time).total_seconds()
            stats["duration_seconds"] = duration
            stats["conversations_per_second"] = stats["processed_conversations"] / duration if duration > 0 else 0
            
            logger.info("🎉 Embedding rebuild complete!")
            logger.info("📊 Stats: %d/%d successful in %.1f seconds", 
                       stats['successful_embeddings'], stats['total_conversations'], duration)
            
            return stats
            
        except Exception as e:
            logger.error("❌ Fatal error during embedding rebuild: %s", e)
            stats["errors"].append(str(e))
            return stats
    
    async def verify_embeddings(self) -> Dict[str, Any]:
        """Verify that embeddings are working by testing semantic search"""
        try:
            logger.info("🔍 Verifying embeddings with sample searches...")
            
            # Test searches that should find Tyler conversations
            test_queries = [
                "art mentor Tyler",
                "Tyler art advice", 
                "drawing tips",
                "art guidance",
                "creative mentor"
            ]
            
            verification_results = {
                "test_queries": len(test_queries),
                "successful_searches": 0,
                "total_results": 0,
                "sample_results": []
            }
            
            for query in test_queries:
                try:
                    # Use memory manager to search for relevant conversations
                    context = await self.memory_manager.get_conversation_context(
                        user_id="test_user",  # Use generic ID for testing
                        current_query=query
                    )
                    
                    # Count semantic results
                    semantic_results = context.semantic_summaries if hasattr(context, 'semantic_summaries') else []
                    result_count = len(semantic_results)
                    
                    verification_results["total_results"] += result_count
                    if result_count > 0:
                        verification_results["successful_searches"] += 1
                        
                        # Store sample for analysis
                        verification_results["sample_results"].append({
                            "query": query,
                            "result_count": result_count,
                            "sample_summaries": semantic_results[:3]  # First 3 results
                        })
                    
                    logger.info("🔍 Query '%s': %d results", query, result_count)
                    
                except Exception as e:
                    logger.warning("⚠️ Search verification failed for '%s': %s", query, e)
            
            success_rate = verification_results["successful_searches"] / verification_results["test_queries"] * 100
            logger.info("✅ Verification complete: %.1f%% success rate", success_rate)
            
            return verification_results
            
        except Exception as e:
            logger.error("❌ Verification failed: %s", e)
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up connections"""
        try:
            # Memory manager cleanup is handled automatically
            logger.info("🧹 Cleanup complete")
        except Exception as e:
            logger.warning("⚠️ Cleanup warning: %s", e)

async def main():
    """Main execution function"""
    rebuilder = ChromaDBEmbeddingRebuilder()
    
    try:
        # Initialize
        await rebuilder.initialize()
        
        # Check current status
        logger.info("🔍 Checking current ChromaDB status...")
        initial_status = await rebuilder.check_chromadb_status()
        logger.info("Initial status: %s", initial_status)
        
        # Rebuild embeddings
        logger.info("🚀 Starting embedding rebuild process...")
        rebuild_stats = await rebuilder.rebuild_all_embeddings(
            batch_size=25,  # Smaller batches for stability
            max_conversations=None  # Process all conversations
        )
        
        logger.info("📊 Rebuild completed with stats: %s", rebuild_stats)
        
        # Verify embeddings are working
        logger.info("🔍 Verifying embeddings with test searches...")
        verification_results = await rebuilder.verify_embeddings()
        logger.info("🎯 Verification results: %s", verification_results)
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 EMBEDDING REBUILD SUMMARY")
        print("="*60)
        print("Total conversations processed: {}".format(rebuild_stats.get('processed_conversations', 0)))
        print("Successful embeddings: {}".format(rebuild_stats.get('successful_embeddings', 0)))
        print("Failed embeddings: {}".format(rebuild_stats.get('failed_embeddings', 0)))
        print("Duration: {:.1f} seconds".format(rebuild_stats.get('duration_seconds', 0)))
        print("Verification success rate: {}/{}".format(
            verification_results.get('successful_searches', 0),
            verification_results.get('test_queries', 0)
        ))
        print("="*60)
        
    except Exception as e:
        logger.error("❌ Fatal error: %s", e)
        return 1
    
    finally:
        await rebuilder.cleanup()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("❌ Unexpected error: %s", e)
        sys.exit(1)