#!/usr/bin/env python3
"""
Historical Conversation Reprocessing Script for WhisperEngine

This script reprocesses existing conversations to add graph memory storage
and full emotion/relationship context that was missing from initial imports.

Usage:
    python scripts/reprocess_historical_conversations.py --user-id 672814231002939413
    python scripts/reprocess_historical_conversations.py --user-id 672814231002939413 --dry-run
    python scripts/reprocess_historical_conversations.py --user-id 672814231002939413 --limit 100
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_manager import UserMemoryManager
from src.memory.integrated_memory_manager import IntegratedMemoryManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HistoricalConversationReprocessor:
    """Reprocess historical conversations for full context storage"""
    
    def __init__(self):
        self.memory_manager = None
        self.integrated_manager = None
        self.processed_count = 0
        self.error_count = 0
        
    async def initialize(self):
        """Initialize memory managers"""
        try:
            self.memory_manager = UserMemoryManager()
            self.integrated_manager = IntegratedMemoryManager()
            await self.integrated_manager.initialize()
            logger.info("Memory managers initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory managers: {e}")
            raise
            
    async def get_user_conversations(self, user_id: str, limit: int | None = None) -> List[Dict[str, Any]]:
        """Retrieve existing conversations for a user"""
        try:
            # Try to get conversations from ChromaDB
            conversations = []
            
            # Search with broad queries to get all conversations
            search_queries = ["", "conversation", "chat", "message", "talk"]
            
            for query in search_queries:
                try:
                    if hasattr(self.memory_manager, 'search_memories'):
                        results = await self.memory_manager.search_memories(
                            user_id, query or "conversation", limit=limit or 1000
                        )
                        conversations.extend(results)
                    elif hasattr(self.memory_manager, 'retrieve_relevant_memories'):
                        results = await self.memory_manager.retrieve_relevant_memories(
                            user_id, query or "conversation", limit=limit or 1000
                        )
                        conversations.extend(results)
                except Exception as e:
                    logger.debug(f"Search query '{query}' failed: {e}")
                    continue
                    
            # Remove duplicates based on content
            unique_conversations = []
            seen_content = set()
            
            for conv in conversations:
                content_key = None
                if isinstance(conv, dict):
                    content_key = conv.get('user_message', '') + conv.get('bot_response', '')
                    
                if content_key and content_key not in seen_content:
                    unique_conversations.append(conv)
                    seen_content.add(content_key)
                    
            logger.info(f"Found {len(unique_conversations)} unique conversations for user {user_id}")
            return unique_conversations[:limit] if limit else unique_conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversations for user {user_id}: {e}")
            return []
            
    async def reprocess_conversation(self, conversation: Dict[str, Any], user_id: str, dry_run: bool = False) -> bool:
        """Reprocess a single conversation with full context"""
        try:
            user_message = conversation.get('user_message', '')
            bot_response = conversation.get('bot_response', conversation.get('response', ''))
            
            if not user_message or not bot_response:
                logger.debug("Skipping conversation with missing message or response")
                return False
                
            if dry_run:
                logger.info(f"[DRY RUN] Would reprocess: {user_message[:50]}...")
                return True
                
            # Use full context storage to add graph memory and emotion processing
            result = self.integrated_manager.store_conversation_with_full_context(
                user_id=user_id,
                message=user_message,
                response=bot_response,
                display_name=None  # No display name for historical data
            )
            
            if result:
                self.processed_count += 1
                logger.debug(f"Reprocessed conversation: {user_message[:50]}...")
                return True
            else:
                logger.warning(f"Failed to reprocess conversation: {user_message[:50]}...")
                return False
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error reprocessing conversation: {e}")
            return False
            
    async def reprocess_user_conversations(self, user_id: str, limit: int | None = None, dry_run: bool = False):
        """Reprocess all conversations for a user"""
        logger.info(f"Starting reprocessing for user {user_id} (limit: {limit}, dry_run: {dry_run})")
        
        # Get existing conversations
        conversations = await self.get_user_conversations(user_id, limit)
        
        if not conversations:
            logger.warning(f"No conversations found for user {user_id}")
            return
            
        logger.info(f"Found {len(conversations)} conversations to reprocess")
        
        # Process conversations in batches to avoid overwhelming the system
        batch_size = 10
        total_batches = (len(conversations) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(conversations))
            batch = conversations[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch)} conversations)")
            
            # Process batch
            for conv in batch:
                await self.reprocess_conversation(conv, user_id, dry_run)
                
            # Small delay between batches to avoid overwhelming the system
            if not dry_run and batch_num < total_batches - 1:
                await asyncio.sleep(0.5)
                
        logger.info(f"Reprocessing complete: {self.processed_count} processed, {self.error_count} errors")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Reprocess historical conversations for full context')
    parser.add_argument('--user-id', '-u', required=True, help='Discord user ID')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of conversations to process')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be processed without storing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Initialize reprocessor
        reprocessor = HistoricalConversationReprocessor()
        await reprocessor.initialize()
        
        # Run reprocessing
        start_time = time.time()
        await reprocessor.reprocess_user_conversations(
            user_id=args.user_id,
            limit=args.limit,
            dry_run=args.dry_run
        )
        
        duration = time.time() - start_time
        logger.info(f"Reprocessing completed in {duration:.2f} seconds")
        
        return 0
        
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))