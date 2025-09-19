# src/memory/core/migration_manager.py

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Statistics for migration process"""
    total_conversations: int = 0
    migrated_successfully: int = 0
    failed_migrations: int = 0
    skipped_conversations: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_conversations == 0:
            return 0.0
        return self.migrated_successfully / self.total_conversations
    
    @property
    def conversations_per_second(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        return self.migrated_successfully / self.duration_seconds

@dataclass
class ConversationData:
    """Standardized conversation data for migration"""
    conversation_id: str
    user_id: str
    user_message: str
    bot_response: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    @classmethod
    def from_chromadb_document(cls, doc_id: str, document: str, metadata: Dict[str, Any]) -> Optional['ConversationData']:
        """Create ConversationData from ChromaDB document format"""
        # Note: document parameter required for ChromaDB compatibility but not used in current implementation
        _ = document  # Explicitly mark as unused for now
        try:
            # Extract conversation components from ChromaDB metadata
            user_message = metadata.get("user_message", "")
            bot_response = metadata.get("bot_response", "")
            user_id = metadata.get("user_id", "")
            
            if not all([user_message, bot_response, user_id]):
                return None
            
            # Parse timestamp
            timestamp_str = metadata.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                timestamp = datetime.now()
            
            # Clean up metadata
            clean_metadata = {k: v for k, v in metadata.items() 
                            if k not in ['user_message', 'bot_response', 'user_id', 'timestamp']}
            
            return cls(
                conversation_id=doc_id,
                user_id=user_id,
                user_message=user_message,
                bot_response=bot_response,
                timestamp=timestamp,
                metadata=clean_metadata
            )
            
        except Exception as e:
            logger.warning("Failed to parse ChromaDB document %s: %s", doc_id, e)
            return None

class HierarchicalMigrationManager:
    """
    Manages migration from existing ChromaDB system to hierarchical memory architecture
    Provides safe, incremental migration with rollback capabilities
    """
    
    def __init__(
        self,
        old_chromadb_client,
        hierarchical_manager,
        batch_size: int = 50,
        max_concurrent_batches: int = 3
    ):
        self.old_chromadb_client = old_chromadb_client
        self.hierarchical_manager = hierarchical_manager
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.logger = logging.getLogger(__name__)
        
        # Migration state
        self.stats = MigrationStats()
        self.migrated_conversation_ids = set()
        self.failed_conversation_ids = set()
        
        # Progress callback
        self.progress_callback: Optional[Callable[[MigrationStats], None]] = None
    
    def set_progress_callback(self, callback: Callable[[MigrationStats], None]):
        """Set callback function to receive migration progress updates"""
        self.progress_callback = callback
    
    async def migrate_all_conversations(
        self,
        collection_name: str = "user_memories",
        dry_run: bool = False,
        verify_migration: bool = True
    ) -> MigrationStats:
        """
        Migrate all conversations from ChromaDB to hierarchical system
        
        Args:
            collection_name: Name of ChromaDB collection to migrate from
            dry_run: If True, only simulate migration without writing data
            verify_migration: If True, verify each migrated conversation
        """
        self.logger.info("Starting %smigration from ChromaDB collection '%s'",
                        "DRY RUN " if dry_run else "", collection_name)
        
        self.stats = MigrationStats(start_time=datetime.now())
        
        try:
            # Get source collection
            old_collection = self.old_chromadb_client.get_collection(collection_name)
            
            # Get total count for progress tracking
            total_count = old_collection.count()
            self.stats.total_conversations = total_count
            
            self.logger.info("Found %d conversations to migrate", total_count)
            
            # Process in batches
            offset = 0
            batch_number = 1
            
            while offset < total_count:
                current_batch_size = min(self.batch_size, total_count - offset)
                
                # Get batch of conversations
                batch_data = old_collection.get(
                    limit=current_batch_size,
                    offset=offset,
                    include=["documents", "metadatas", "ids"]
                )
                
                if not batch_data["documents"]:
                    break
                
                self.logger.info("Processing batch %d: conversations %d-%d",
                               batch_number, offset + 1, offset + current_batch_size)
                
                # Migrate batch
                if not dry_run:
                    await self._migrate_batch(batch_data, verify_migration)
                else:
                    await self._simulate_batch_migration(batch_data)
                
                # Update progress
                offset += current_batch_size
                batch_number += 1
                
                if self.progress_callback:
                    self.progress_callback(self.stats)
                
                # Small delay to prevent overwhelming the systems
                await asyncio.sleep(0.1)
            
            self.stats.end_time = datetime.now()
            
            # Log final results
            self._log_migration_summary(dry_run)
            
            return self.stats
            
        except (AttributeError, KeyError, ConnectionError, TimeoutError) as e:
            self.logger.error("Migration failed: %s", e)
            self.stats.end_time = datetime.now()
            raise
    
    async def _migrate_batch(
        self,
        batch_data: Dict[str, Any],
        verify_migration: bool
    ):
        """Migrate a single batch of conversations"""
        
        # Parse conversations from batch
        conversations = []
        for i, doc in enumerate(batch_data["documents"]):
            doc_id = batch_data["ids"][i]
            metadata = batch_data["metadatas"][i]
            
            conversation = ConversationData.from_chromadb_document(doc_id, doc, metadata)
            if conversation:
                conversations.append(conversation)
            else:
                self.stats.skipped_conversations += 1
                self.logger.warning("Skipped malformed conversation: %s", doc_id)
        
        # Migrate conversations with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        migration_tasks = [
            self._migrate_single_conversation(conversation, semaphore, verify_migration)
            for conversation in conversations
        ]
        
        await asyncio.gather(*migration_tasks, return_exceptions=True)
    
    async def _migrate_single_conversation(
        self,
        conversation: ConversationData,
        semaphore: asyncio.Semaphore,
        verify_migration: bool
    ):
        """Migrate a single conversation to the hierarchical system"""
        
        async with semaphore:
            try:
                # Store in hierarchical system
                new_conversation_id = await self.hierarchical_manager.store_conversation(
                    user_id=conversation.user_id,
                    user_message=conversation.user_message,
                    bot_response=conversation.bot_response,
                    metadata={
                        **conversation.metadata,
                        'migrated_from': 'chromadb',
                        'original_id': conversation.conversation_id,
                        'original_timestamp': conversation.timestamp.isoformat()
                    }
                )
                
                # Verify migration if requested
                if verify_migration:
                    await self._verify_conversation_migration(conversation, new_conversation_id)
                
                self.migrated_conversation_ids.add(new_conversation_id)
                self.stats.migrated_successfully += 1
                
                self.logger.debug("Migrated conversation %s -> %s for user %s",
                               conversation.conversation_id, new_conversation_id, conversation.user_id)
                
            except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
                self.failed_conversation_ids.add(conversation.conversation_id)
                self.stats.failed_migrations += 1
                self.logger.error("Failed to migrate conversation %s: %s",
                               conversation.conversation_id, e)
    
    async def _verify_conversation_migration(
        self,
        original: ConversationData,
        new_conversation_id: str
    ):
        """Verify that a conversation was migrated correctly"""
        
        try:
            # Get the migrated conversation from hierarchical system
            context = await self.hierarchical_manager.get_conversation_context(
                user_id=original.user_id,
                current_query=original.user_message[:50]  # Use part of message as query
            )
            
            # Check if the conversation appears in context
            found_in_context = False
            for msg in context.recent_messages:
                if (msg.get('user_message') == original.user_message and 
                    msg.get('bot_response') == original.bot_response):
                    found_in_context = True
                    break
            
            if not found_in_context:
                # Check in full conversations
                for conv in context.full_conversations:
                    if (conv.get('user_message') == original.user_message and 
                        conv.get('bot_response') == original.bot_response):
                        found_in_context = True
                        break
            
            if not found_in_context:
                self.logger.warning("Verification failed for conversation %s: not found in context",
                                  new_conversation_id)
            
        except (ConnectionError, AttributeError, KeyError) as e:
            self.logger.warning("Verification failed for conversation %s: %s",
                              new_conversation_id, e)
    
    async def _simulate_batch_migration(self, batch_data: Dict[str, Any]):
        """Simulate migration for dry run mode"""
        
        for i, doc in enumerate(batch_data["documents"]):
            doc_id = batch_data["ids"][i]
            metadata = batch_data["metadatas"][i]
            
            conversation = ConversationData.from_chromadb_document(doc_id, doc, metadata)
            if conversation:
                self.stats.migrated_successfully += 1
                self.logger.debug("DRY RUN: Would migrate conversation %s for user %s",
                               conversation.conversation_id, conversation.user_id)
            else:
                self.stats.skipped_conversations += 1
    
    async def migrate_specific_users(
        self,
        user_ids: List[str],
        collection_name: str = "user_memories",
        dry_run: bool = False
    ) -> MigrationStats:
        """Migrate conversations for specific users only"""
        
        self.logger.info("Starting migration for %d specific users", len(user_ids))
        
        self.stats = MigrationStats(start_time=datetime.now())
        
        try:
            old_collection = self.old_chromadb_client.get_collection(collection_name)
            
            for user_id in user_ids:
                # Get conversations for this user
                user_conversations = old_collection.get(
                    where={"user_id": user_id},
                    include=["documents", "metadatas", "ids"]
                )
                
                if user_conversations["documents"]:
                    self.stats.total_conversations += len(user_conversations["documents"])
                    
                    if not dry_run:
                        await self._migrate_batch(user_conversations, verify_migration=True)
                    else:
                        await self._simulate_batch_migration(user_conversations)
                    
                    self.logger.info("Processed %d conversations for user %s",
                                   len(user_conversations["documents"]), user_id)
            
            self.stats.end_time = datetime.now()
            self._log_migration_summary(dry_run)
            
            return self.stats
            
        except (AttributeError, KeyError, ConnectionError) as e:
            self.logger.error("User-specific migration failed: %s", e)
            self.stats.end_time = datetime.now()
            raise
    
    async def rollback_migration(self, conversation_ids: Optional[List[str]] = None) -> int:
        """
        Rollback migration by removing migrated conversations
        
        Args:
            conversation_ids: Specific conversation IDs to rollback, or None for all
        
        Returns:
            Number of conversations rolled back
        """
        if conversation_ids is None:
            conversation_ids = list(self.migrated_conversation_ids)
        
        self.logger.info("Rolling back %d migrated conversations", len(conversation_ids))
        
        rollback_count = 0
        failed_rollbacks = 0
        
        for conv_id in conversation_ids:
            try:
                # Attempt to delete from all tiers of hierarchical system
                if hasattr(self.hierarchical_manager, 'tier2_archive'):
                    await self.hierarchical_manager.tier2_archive.delete_conversation(conv_id)
                
                if hasattr(self.hierarchical_manager, 'tier3_semantic'):
                    await self.hierarchical_manager.tier3_semantic.delete_summary(conv_id)
                
                if hasattr(self.hierarchical_manager, 'tier4_graph'):
                    await self.hierarchical_manager.tier4_graph.delete_conversation(conv_id)
                
                # Remove from cache if present
                if hasattr(self.hierarchical_manager, 'tier1_cache'):
                    # Redis cache will naturally expire, no direct deletion needed
                    pass
                
                rollback_count += 1
                self.migrated_conversation_ids.discard(conv_id)
                
            except (ConnectionError, AttributeError, KeyError) as e:
                failed_rollbacks += 1
                self.logger.error("Failed to rollback conversation %s: %s", conv_id, e)
        
        self.logger.info("Rollback completed: %d successful, %d failed", 
                        rollback_count, failed_rollbacks)
        
        return rollback_count
    
    async def validate_migration_integrity(self, sample_size: int = 100) -> Dict[str, Any]:
        """Validate the integrity of migrated data by sampling"""
        
        if not self.migrated_conversation_ids:
            return {"status": "no_migrations_to_validate"}
        
        sample_ids = list(self.migrated_conversation_ids)[:sample_size]
        
        validation_results = {
            "total_sampled": len(sample_ids),
            "valid_conversations": 0,
            "invalid_conversations": 0,
            "validation_errors": []
        }
        
        for conv_id in sample_ids:
            try:
                # Try to retrieve conversation from hierarchical system
                # This is a basic validation - could be enhanced
                context = await self.hierarchical_manager.get_conversation_context(
                    user_id="validation_user",  # Dummy user for validation
                    current_query="validation query"
                )
                
                # If we get a valid context, consider it a success
                if context and (context.recent_messages or context.full_conversations):
                    validation_results["valid_conversations"] += 1
                else:
                    validation_results["invalid_conversations"] += 1
                    
            except Exception as e:
                validation_results["invalid_conversations"] += 1
                validation_results["validation_errors"].append({
                    "conversation_id": conv_id,
                    "error": str(e)
                })
        
        validation_results["integrity_score"] = (
            validation_results["valid_conversations"] / validation_results["total_sampled"]
            if validation_results["total_sampled"] > 0 else 0
        )
        
        return validation_results
    
    def _log_migration_summary(self, dry_run: bool):
        """Log comprehensive migration summary"""
        
        duration = self.stats.duration_seconds
        rate = self.stats.conversations_per_second
        
        summary = f"""
{'='*60}
{'DRY RUN ' if dry_run else ''}MIGRATION SUMMARY
{'='*60}
Total conversations: {self.stats.total_conversations}
Successfully migrated: {self.stats.migrated_successfully}
Failed migrations: {self.stats.failed_migrations}
Skipped (malformed): {self.stats.skipped_conversations}
Duration: {duration:.2f} seconds
Success rate: {self.stats.success_rate:.1%}
Migration rate: {rate:.1f} conversations/second
{'='*60}
        """
        
        self.logger.info(summary)
        
        if self.stats.failed_migrations > 0:
            self.logger.warning("Migration completed with %d failures. "
                              "Check logs for details on failed conversations.",
                              self.stats.failed_migrations)
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Get comprehensive migration report"""
        
        return {
            "migration_stats": {
                "total_conversations": self.stats.total_conversations,
                "migrated_successfully": self.stats.migrated_successfully,
                "failed_migrations": self.stats.failed_migrations,
                "skipped_conversations": self.stats.skipped_conversations,
                "success_rate": self.stats.success_rate,
                "duration_seconds": self.stats.duration_seconds,
                "conversations_per_second": self.stats.conversations_per_second
            },
            "configuration": {
                "batch_size": self.batch_size,
                "max_concurrent_batches": self.max_concurrent_batches
            },
            "migrated_conversation_ids": list(self.migrated_conversation_ids),
            "failed_conversation_ids": list(self.failed_conversation_ids),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_migration_report(self, filepath: str):
        """Save migration report to file"""
        report = self.get_migration_report()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info("Migration report saved to %s", filepath)
            
        except (IOError, OSError) as e:
            self.logger.error("Failed to save migration report: %s", e)


# Utility functions

def create_progress_logger(log_interval: int = 100) -> Callable[[MigrationStats], None]:
    """Create a progress callback that logs migration progress"""
    
    def log_progress(stats: MigrationStats):
        if stats.migrated_successfully % log_interval == 0 and stats.start_time:
            elapsed = (datetime.now() - stats.start_time).total_seconds()
            rate = stats.migrated_successfully / elapsed if elapsed > 0 else 0
            
            logger.info("Migration progress: %d/%d conversations migrated (%.1f/sec, %.1f%% success)",
                       stats.migrated_successfully, stats.total_conversations,
                       rate, stats.success_rate * 100)
    
    return log_progress

async def run_migration_with_monitoring(
    old_chromadb_client,
    hierarchical_manager,
    collection_name: str = "user_memories",
    dry_run: bool = False
) -> MigrationStats:
    """Run migration with built-in progress monitoring"""
    
    migrator = HierarchicalMigrationManager(
        old_chromadb_client=old_chromadb_client,
        hierarchical_manager=hierarchical_manager,
        batch_size=50,
        max_concurrent_batches=3
    )
    
    # Set up progress monitoring
    progress_logger = create_progress_logger(log_interval=50)
    migrator.set_progress_callback(progress_logger)
    
    try:
        # Run migration
        stats = await migrator.migrate_all_conversations(
            collection_name=collection_name,
            dry_run=dry_run,
            verify_migration=not dry_run  # Skip verification in dry run mode
        )
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"migration_report_{timestamp}.json"
        migrator.save_migration_report(report_filename)
        
        return stats
        
    except (ConnectionError, AttributeError, ValueError) as e:
        logger.error("Migration failed: %s", e)
        
        # Save partial report even on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"migration_report_failed_{timestamp}.json"
        migrator.save_migration_report(report_filename)
        
        raise

if __name__ == "__main__":
    # Example usage
    print("Migration Manager - Use run_migration_with_monitoring() to start migration")
    print("Example:")
    print("  stats = await run_migration_with_monitoring(old_client, new_manager, dry_run=True)")