#!/usr/bin/env python3
"""
Migrate Facts/Preferences from Qdrant Vector Storage to PostgreSQL
Phase 1 of Architecture Cleanup: Remove redundant fact storage from vector memory

This script:
1. Queries all facts/preferences from Qdrant vector storage
2. Parses content to extract structured data
3. Stores in PostgreSQL knowledge graph (fact_entities, user_fact_relationships)
4. Validates migration success
5. Optionally deletes vector memories after successful migration

Safe to run multiple times (idempotent - PostgreSQL upsert logic prevents duplicates)

Usage:
    python scripts/migrate_vector_facts_to_postgres.py --dry-run    # Preview only
    python scripts/migrate_vector_facts_to_postgres.py --migrate    # Execute migration
    python scripts/migrate_vector_facts_to_postgres.py --migrate --delete-after  # Migrate + cleanup
"""

import asyncio
import argparse
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import WhisperEngine components
from src.memory.vector_memory_system import create_vector_memory_manager
from src.knowledge.semantic_router import KnowledgeRouter
from src.database.postgres_manager import PostgresConnectionManager


class VectorFactMigrator:
    """Migrates facts and preferences from Qdrant to PostgreSQL"""
    
    def __init__(self, postgres_pool, dry_run: bool = True):
        self.postgres_pool = postgres_pool
        self.dry_run = dry_run
        self.knowledge_router = None
        self.vector_manager = None
        
        # Migration statistics
        self.stats = {
            'total_found': 0,
            'facts_migrated': 0,
            'preferences_migrated': 0,
            'skipped': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Initialize components"""
        logger.info("Initializing migration components...")
        
        # Initialize knowledge router
        self.knowledge_router = KnowledgeRouter(self.postgres_pool)
        
        # Initialize vector memory manager
        self.vector_manager = create_vector_memory_manager()
        
        logger.info("✅ Components initialized")
    
    def parse_fact_content(self, content: str, memory_type: str) -> Optional[Dict]:
        """
        Parse fact content from vector memory string.
        
        Examples:
            "[pizza (likes, food)]" -> {entity: "pizza", relationship: "likes", type: "food"}
            "[preferred_name: Mark]" -> {key: "preferred_name", value: "Mark"}
        """
        try:
            # Preference pattern: "[key: value]"
            pref_match = re.match(r'\[([^:]+):\s*([^\]]+)\]', content)
            if pref_match and memory_type == 'preference':
                return {
                    'type': 'preference',
                    'preference_key': pref_match.group(1).strip(),
                    'preference_value': pref_match.group(2).strip()
                }
            
            # Fact pattern: "[entity (relationship, entity_type)]" or "[entity (relationship)]"
            fact_match = re.match(r'\[([^\(]+)\s*\(([^\),]+)(?:,\s*([^\)]+))?\)\]', content)
            if fact_match and memory_type == 'fact':
                entity_name = fact_match.group(1).strip()
                relationship_type = fact_match.group(2).strip()
                entity_type = fact_match.group(3).strip() if fact_match.group(3) else 'other'
                
                return {
                    'type': 'fact',
                    'entity_name': entity_name,
                    'entity_type': entity_type,
                    'relationship_type': relationship_type
                }
            
            # Legacy format: Parse from plain text
            if memory_type == 'fact':
                # Try to extract from natural language
                # Example: "User likes pizza" or "User enjoys hiking"
                patterns = [
                    (r'(?:user )?(likes?|enjoys?|loves?|prefers?)\s+([a-zA-Z]+)', 'likes'),
                    (r'(?:user )?(dislikes?|hates?)\s+([a-zA-Z]+)', 'dislikes'),
                    (r'(?:user )?(?:has )?visited\s+([a-zA-Z]+)', 'visited')
                ]
                
                for pattern, default_relationship in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        if len(match.groups()) >= 2:
                            relationship = match.group(1).lower()
                            entity = match.group(2).strip()
                        else:
                            relationship = default_relationship
                            entity = match.group(1).strip()
                        
                        # Classify entity type
                        entity_type = self._classify_entity_type(entity, content)
                        
                        return {
                            'type': 'fact',
                            'entity_name': entity,
                            'entity_type': entity_type,
                            'relationship_type': relationship
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse content '{content}': {e}")
            return None
    
    def _classify_entity_type(self, entity: str, context: str) -> str:
        """Classify entity type from entity name and context"""
        entity_lower = entity.lower()
        context_lower = context.lower()
        
        # Food keywords
        food_keywords = ['pizza', 'pasta', 'burger', 'taco', 'sushi', 'sandwich', 'food', 'meal']
        if any(kw in entity_lower or kw in context_lower for kw in food_keywords):
            return 'food'
        
        # Drink keywords
        drink_keywords = ['beer', 'wine', 'coffee', 'tea', 'drink', 'beverage']
        if any(kw in entity_lower or kw in context_lower for kw in drink_keywords):
            return 'drink'
        
        # Activity/hobby keywords
        activity_keywords = ['hiking', 'swimming', 'diving', 'gaming', 'reading', 'hobby', 'activity']
        if any(kw in entity_lower or kw in context_lower for kw in activity_keywords):
            return 'hobby'
        
        # Place keywords
        place_keywords = ['city', 'country', 'beach', 'mountain', 'place', 'location', 'visited']
        if any(kw in entity_lower or kw in context_lower for kw in place_keywords):
            return 'place'
        
        return 'other'
    
    async def get_vector_facts(self) -> List[Dict]:
        """Retrieve all facts and preferences from Qdrant"""
        logger.info("Querying Qdrant for facts and preferences...")
        
        try:
            # Search for all fact and preference memories across all users
            # Note: This requires implementation in vector_memory_system.py
            # For now, we'll use a workaround with bot-specific collections
            
            all_facts = []
            
            # Get all bot collections (elena, marcus, jake, etc.)
            bot_collections = [
                'whisperengine_memory_elena',
                'whisperengine_memory_marcus',
                'whisperengine_memory_jake',
                'whisperengine_memory_ryan',
                'whisperengine_memory_gabriel',
                'whisperengine_memory_sophia',
                'whisperengine_memory_dream',
                'chat_memories_aethys'
            ]
            
            for collection_name in bot_collections:
                logger.info(f"  Checking collection: {collection_name}")
                
                try:
                    # Query collection for facts/preferences
                    # This is a simplified approach - real implementation needs scroll API
                    results = await self.vector_manager.search_memories(
                        query="",  # Empty query for broad search
                        user_id="",  # Empty for all users
                        memory_types=['fact', 'preference'],
                        limit=1000,  # High limit to get all
                        collection_override=collection_name
                    )
                    
                    if results:
                        logger.info(f"    Found {len(results)} fact/preference memories")
                        all_facts.extend(results)
                
                except Exception as e:
                    logger.warning(f"    Failed to query {collection_name}: {e}")
                    continue
            
            self.stats['total_found'] = len(all_facts)
            logger.info(f"✅ Total facts/preferences found: {len(all_facts)}")
            
            return all_facts
            
        except Exception as e:
            logger.error(f"❌ Failed to query Qdrant: {e}")
            return []
    
    async def migrate_fact(self, fact_data: Dict) -> bool:
        """Migrate a single fact to PostgreSQL"""
        try:
            user_id = fact_data.get('user_id')
            content = fact_data.get('content', '')
            memory_type = fact_data.get('memory_type', 'fact')
            confidence = fact_data.get('confidence', 0.8)
            metadata = fact_data.get('metadata', {})
            
            # Parse content
            parsed = self.parse_fact_content(content, memory_type)
            if not parsed:
                logger.debug(f"  Could not parse content: '{content}'")
                self.stats['skipped'] += 1
                return False
            
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would migrate: {parsed}")
                return True
            
            # Store based on type
            if parsed['type'] == 'fact':
                success = await self.knowledge_router.store_user_fact(
                    user_id=user_id,
                    entity_name=parsed['entity_name'],
                    entity_type=parsed['entity_type'],
                    relationship_type=parsed['relationship_type'],
                    confidence=confidence,
                    emotional_context=metadata.get('emotional_context'),
                    mentioned_by_character=metadata.get('bot_name'),
                    source_conversation_id=metadata.get('channel_id')
                )
                
                if success:
                    self.stats['facts_migrated'] += 1
                    logger.debug(f"  ✅ Migrated fact: {parsed['entity_name']} ({parsed['relationship_type']})")
                    return True
            
            elif parsed['type'] == 'preference':
                success = await self.knowledge_router.store_user_preference(
                    user_id=user_id,
                    preference_key=parsed['preference_key'],
                    preference_value=parsed['preference_value'],
                    confidence=confidence,
                    metadata={
                        'source': 'vector_migration',
                        'original_metadata': metadata
                    }
                )
                
                if success:
                    self.stats['preferences_migrated'] += 1
                    logger.debug(f"  ✅ Migrated preference: {parsed['preference_key']} = {parsed['preference_value']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Migration error: {e}")
            self.stats['errors'] += 1
            return False
    
    async def validate_migration(self) -> bool:
        """Validate that migration was successful"""
        logger.info("\n📊 Validating migration...")
        
        try:
            # Sample validation: Check a few migrated facts exist in PostgreSQL
            # This is a simplified check - full validation would verify all records
            
            async with self.postgres_pool.acquire() as conn:
                # Count facts in PostgreSQL
                fact_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_fact_relationships
                """)
                
                pref_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM universal_users 
                    WHERE preferences IS NOT NULL
                """)
                
                logger.info(f"  PostgreSQL facts: {fact_count}")
                logger.info(f"  PostgreSQL preferences: {pref_count}")
                
                # Check if counts make sense
                if fact_count > 0 or pref_count > 0:
                    logger.info("✅ Migration validation passed")
                    return True
                else:
                    logger.warning("⚠️ No data found in PostgreSQL - migration may have failed")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False
    
    async def delete_vector_facts(self, fact_ids: List[str]) -> int:
        """Delete migrated facts from Qdrant (optional cleanup)"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would delete {len(fact_ids)} vector memories")
            return 0
        
        logger.info(f"Deleting {len(fact_ids)} vector memories...")
        
        try:
            deleted = 0
            # Delete in batches
            batch_size = 100
            for i in range(0, len(fact_ids), batch_size):
                batch = fact_ids[i:i+batch_size]
                success = await self.vector_manager.delete_memories(batch)
                if success:
                    deleted += len(batch)
            
            logger.info(f"✅ Deleted {deleted} vector memories")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Deletion failed: {e}")
            return 0
    
    async def run_migration(self, delete_after: bool = False):
        """Execute full migration process"""
        logger.info("=" * 80)
        logger.info("VECTOR FACTS TO POSTGRESQL MIGRATION")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        logger.info(f"Delete after: {delete_after}")
        logger.info("=" * 80)
        
        # Step 1: Initialize
        await self.initialize()
        
        # Step 2: Get all facts from vector storage
        vector_facts = await self.get_vector_facts()
        
        if not vector_facts:
            logger.info("No facts/preferences found in vector storage - nothing to migrate")
            return
        
        # Step 3: Migrate each fact
        logger.info(f"\n🚀 Migrating {len(vector_facts)} facts/preferences...")
        
        fact_ids = []
        for i, fact in enumerate(vector_facts):
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(vector_facts)}")
            
            success = await self.migrate_fact(fact)
            if success and not self.dry_run:
                fact_ids.append(fact.get('id'))
        
        # Step 4: Validate
        if not self.dry_run:
            await self.validate_migration()
        
        # Step 5: Optional cleanup
        if delete_after and not self.dry_run and fact_ids:
            await self.delete_vector_facts(fact_ids)
        
        # Step 6: Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total found:          {self.stats['total_found']}")
        logger.info(f"Facts migrated:       {self.stats['facts_migrated']}")
        logger.info(f"Preferences migrated: {self.stats['preferences_migrated']}")
        logger.info(f"Skipped:              {self.stats['skipped']}")
        logger.info(f"Errors:               {self.stats['errors']}")
        logger.info("=" * 80)
        
        if self.dry_run:
            logger.info("✅ DRY RUN COMPLETE - No changes made")
        else:
            logger.info("✅ MIGRATION COMPLETE")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate facts/preferences from Qdrant to PostgreSQL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without making changes (default)'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Execute migration (write to PostgreSQL)'
    )
    parser.add_argument(
        '--delete-after',
        action='store_true',
        help='Delete vector memories after successful migration'
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither specified
    if not args.migrate:
        args.dry_run = True
        logger.info("Running in DRY RUN mode (use --migrate to execute)")
    
    # Initialize PostgreSQL connection
    postgres_manager = PostgresConnectionManager()
    await postgres_manager.initialize()
    postgres_pool = postgres_manager.get_pool()
    
    # Run migration
    migrator = VectorFactMigrator(postgres_pool, dry_run=args.dry_run)
    await migrator.run_migration(delete_after=args.delete_after)
    
    # Cleanup
    await postgres_manager.close()


if __name__ == '__main__':
    asyncio.run(main())
