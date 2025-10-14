#!/usr/bin/env python3
"""
WhisperEngine Fact Database Cleanup Script
Removes noisy/low-quality facts from early system tuning period while preserving good data.
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'whisperengine',
    'user': 'whisperengine',
    'password': 'whisperengine'
}

class FactCleanupManager:
    """Manages cleanup of noisy facts from the database."""
    
    def __init__(self):
        self.dry_run = True  # Safety first - preview changes before applying
        self.cleanup_stats = {
            'total_facts_before': 0,
            'fragments_removed': 0,
            'pronouns_removed': 0,
            'special_chars_removed': 0,
            'very_short_removed': 0,
            'very_long_removed': 0,
            'low_confidence_removed': 0,
            'total_removed': 0,
            'total_facts_after': 0
        }
    
    async def connect(self):
        """Establish database connection."""
        self.conn = await asyncpg.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
    
    async def close(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def analyze_noise_patterns(self):
        """Analyze current noise patterns in the database."""
        logger.info("🔍 Analyzing noise patterns in fact database...")
        
        # Get total fact count
        total_facts = await self.conn.fetchval("SELECT COUNT(*) FROM user_fact_relationships")
        self.cleanup_stats['total_facts_before'] = total_facts
        logger.info(f"Total facts in database: {total_facts}")
        
        # 1. Sentence fragments
        fragments = await self.conn.fetch("""
            SELECT fe.entity_name, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE (
                fe.entity_name LIKE '%door we%' OR
                fe.entity_name LIKE '%when you%' OR 
                fe.entity_name LIKE '%process if%' OR
                fe.entity_name LIKE '%and %' OR
                fe.entity_name LIKE '%the %' OR
                fe.entity_name LIKE '%or %' OR
                fe.entity_name LIKE '%but %' OR
                fe.entity_name LIKE '%at %' OR
                fe.entity_name LIKE '%in %' OR
                fe.entity_name LIKE '%to %' OR
                fe.entity_name LIKE '%that %' OR
                fe.entity_name LIKE '%just %' OR
                fe.entity_name LIKE '%like %' OR
                fe.entity_name LIKE '% -' OR
                fe.entity_name LIKE '- %'
            )
            GROUP BY fe.entity_name
            ORDER BY count DESC
            LIMIT 20
        """)
        
        fragment_count = sum(f['count'] for f in fragments)
        self.cleanup_stats['fragments_removed'] = fragment_count
        logger.info(f"Sentence fragments to remove: {fragment_count}")
        for frag in fragments[:10]:
            logger.info(f"  '{frag['entity_name']}' ({frag['count']}x)")
        
        # 2. Pronouns and generic words
        pronouns = await self.conn.fetch("""
            SELECT fe.entity_name, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name IN ('i', 'you', 'me', 'we', 'they', 'it', 'this', 'that', 'something', 'anything')
            GROUP BY fe.entity_name
            ORDER BY count DESC
        """)
        
        pronoun_count = sum(p['count'] for p in pronouns)
        self.cleanup_stats['pronouns_removed'] = pronoun_count
        logger.info(f"Pronouns/generics to remove: {pronoun_count}")
        for pron in pronouns:
            logger.info(f"  '{pron['entity_name']}' ({pron['count']}x)")
        
        # 3. Special characters (noise indicators)
        special_chars = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name ~ '[<>#@\\$%\\^&\\*\\(\\)\\[\\]\\{\\}]'
        """)
        self.cleanup_stats['special_chars_removed'] = special_chars
        logger.info(f"Special character entities to remove: {special_chars}")
        
        # 4. Very short entities (1-2 characters, likely noise)
        very_short = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE LENGTH(fe.entity_name) <= 2
            AND fe.entity_name NOT IN ('AI', 'JS', 'GO', 'TV', 'PC', 'UK', 'US')  -- Preserve valid acronyms
        """)
        self.cleanup_stats['very_short_removed'] = very_short
        logger.info(f"Very short entities to remove: {very_short}")
        
        # 5. Very long entities (likely sentence fragments)
        very_long = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE LENGTH(fe.entity_name) > 50
        """)
        self.cleanup_stats['very_long_removed'] = very_long
        logger.info(f"Very long entities to remove: {very_long}")
        
        # 6. Low confidence facts from early period
        low_confidence = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM user_fact_relationships ufr
            WHERE ufr.confidence < 0.3
            AND ufr.created_at < NOW() - INTERVAL '5 days'  -- Only old low-confidence facts
        """)
        self.cleanup_stats['low_confidence_removed'] = low_confidence
        logger.info(f"Low confidence old facts to remove: {low_confidence}")
        
        total_to_remove = fragment_count + pronoun_count + special_chars + very_short + very_long + low_confidence
        self.cleanup_stats['total_removed'] = total_to_remove
        self.cleanup_stats['total_facts_after'] = total_facts - total_to_remove
        
        logger.info(f"\n📊 CLEANUP SUMMARY:")
        logger.info(f"  Current facts: {total_facts}")
        logger.info(f"  Facts to remove: {total_to_remove}")
        logger.info(f"  Facts remaining: {total_facts - total_to_remove}")
        logger.info(f"  Quality improvement: {(total_facts - total_to_remove)/total_facts*100:.1f}% clean")
        
        return total_to_remove
    
    async def preview_cleanup(self):
        """Preview what would be removed without actually deleting."""
        logger.info("🔍 PREVIEW MODE - Showing facts that would be removed...")
        
        # Show sample facts that would be removed
        preview_facts = await self.conn.fetch("""
            SELECT 
                fe.entity_name,
                fe.entity_type,
                ufr.relationship_type,
                ufr.confidence,
                ufr.mentioned_by_character,
                ufr.created_at,
                CASE 
                    WHEN fe.entity_name IN ('i', 'you', 'me', 'we', 'they', 'it', 'this', 'that') THEN 'pronoun'
                    WHEN LENGTH(fe.entity_name) <= 2 THEN 'too_short'
                    WHEN LENGTH(fe.entity_name) > 50 THEN 'too_long'
                    WHEN fe.entity_name ~ '[<>#@\\$%\\^&\\*\\(\\)\\[\\]\\{\\}]' THEN 'special_chars'
                    WHEN ufr.confidence < 0.3 AND ufr.created_at < NOW() - INTERVAL '5 days' THEN 'low_confidence'
                    ELSE 'fragment'
                END as removal_reason
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE (
                -- Fragments
                fe.entity_name LIKE '%door we%' OR
                fe.entity_name LIKE '%when you%' OR 
                fe.entity_name LIKE '%process if%' OR
                fe.entity_name LIKE '%and %' OR
                fe.entity_name LIKE '%the %' OR
                fe.entity_name LIKE '%or %' OR
                fe.entity_name LIKE '%but %' OR
                fe.entity_name LIKE '%at %' OR
                fe.entity_name LIKE '%that %' OR
                fe.entity_name LIKE '%just %' OR
                fe.entity_name LIKE '%like %' OR
                fe.entity_name LIKE '% -' OR
                fe.entity_name LIKE '- %' OR
                -- Pronouns
                fe.entity_name IN ('i', 'you', 'me', 'we', 'they', 'it', 'this', 'that', 'something', 'anything') OR
                -- Special chars
                fe.entity_name ~ '[<>#@\\$%\\^&\\*\\(\\)\\[\\]\\{\\}]' OR
                -- Length issues
                (LENGTH(fe.entity_name) <= 2 AND fe.entity_name NOT IN ('AI', 'JS', 'GO', 'TV', 'PC', 'UK', 'US')) OR
                LENGTH(fe.entity_name) > 50 OR
                -- Low confidence old facts
                (ufr.confidence < 0.3 AND ufr.created_at < NOW() - INTERVAL '5 days')
            )
            ORDER BY ufr.created_at DESC
            LIMIT 30
        """)
        
        logger.info(f"\n📋 SAMPLE FACTS TO BE REMOVED (showing {len(preview_facts)} of {self.cleanup_stats['total_removed']}):")
        for fact in preview_facts:
            entity = fact['entity_name']
            etype = fact['entity_type']
            rel = fact['relationship_type']
            conf = fact['confidence']
            char = fact['mentioned_by_character']
            reason = fact['removal_reason']
            created = fact['created_at'].strftime('%m-%d %H:%M')
            
            logger.info(f"  🗑️  [{created}] '{entity}' ({etype}) - {rel} (conf: {conf:.2f}) by {char} [{reason}]")
    
    async def execute_cleanup(self):
        """Execute the actual cleanup - REMOVES DATA!"""
        if self.dry_run:
            logger.warning("⚠️  DRY RUN MODE - No data will be deleted. Call with dry_run=False to execute.")
            return
        
        logger.warning("🚨 EXECUTING CLEANUP - THIS WILL DELETE DATA!")
        logger.info("Starting fact cleanup process...")
        
        try:
            # Begin transaction for safety
            async with self.conn.transaction():
                
                # 1. Remove sentence fragments
                deleted_fragments = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    USING fact_entities fe 
                    WHERE ufr.entity_id = fe.id
                    AND (
                        fe.entity_name LIKE '%door we%' OR
                        fe.entity_name LIKE '%when you%' OR 
                        fe.entity_name LIKE '%process if%' OR
                        fe.entity_name LIKE '%and %' OR
                        fe.entity_name LIKE '%the %' OR
                        fe.entity_name LIKE '%or %' OR
                        fe.entity_name LIKE '%but %' OR
                        fe.entity_name LIKE '%at %' OR
                        fe.entity_name LIKE '%that %' OR
                        fe.entity_name LIKE '%just %' OR
                        fe.entity_name LIKE '%like %' OR
                        fe.entity_name LIKE '% -' OR
                        fe.entity_name LIKE '- %'
                    )
                """)
                logger.info(f"✅ Removed {deleted_fragments.split()[-1]} sentence fragment facts")
                
                # 2. Remove pronouns and generic words
                deleted_pronouns = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    USING fact_entities fe 
                    WHERE ufr.entity_id = fe.id
                    AND fe.entity_name IN ('i', 'you', 'me', 'we', 'they', 'it', 'this', 'that', 'something', 'anything')
                """)
                logger.info(f"✅ Removed {deleted_pronouns.split()[-1]} pronoun/generic facts")
                
                # 3. Remove special character entities
                deleted_special = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    USING fact_entities fe 
                    WHERE ufr.entity_id = fe.id
                    AND fe.entity_name ~ '[<>#@\\$%\\^&\\*\\(\\)\\[\\]\\{\\}]'
                """)
                logger.info(f"✅ Removed {deleted_special.split()[-1]} special character facts")
                
                # 4. Remove very short entities (preserving valid acronyms)
                deleted_short = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    USING fact_entities fe 
                    WHERE ufr.entity_id = fe.id
                    AND LENGTH(fe.entity_name) <= 2
                    AND fe.entity_name NOT IN ('AI', 'JS', 'GO', 'TV', 'PC', 'UK', 'US')
                """)
                logger.info(f"✅ Removed {deleted_short.split()[-1]} very short facts")
                
                # 5. Remove very long entities
                deleted_long = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    USING fact_entities fe 
                    WHERE ufr.entity_id = fe.id
                    AND LENGTH(fe.entity_name) > 50
                """)
                logger.info(f"✅ Removed {deleted_long.split()[-1]} very long facts")
                
                # 6. Remove old low-confidence facts
                deleted_low_conf = await self.conn.execute("""
                    DELETE FROM user_fact_relationships ufr
                    WHERE ufr.confidence < 0.3
                    AND ufr.created_at < NOW() - INTERVAL '5 days'
                """)
                logger.info(f"✅ Removed {deleted_low_conf.split()[-1]} old low-confidence facts")
                
                # Clean up orphaned entities (entities with no relationships)
                deleted_entities = await self.conn.execute("""
                    DELETE FROM fact_entities fe
                    WHERE NOT EXISTS (
                        SELECT 1 FROM user_fact_relationships ufr 
                        WHERE ufr.entity_id = fe.id
                    )
                """)
                logger.info(f"✅ Cleaned up {deleted_entities.split()[-1]} orphaned entities")
                
            logger.info("🎉 Cleanup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise
    
    async def verify_cleanup(self):
        """Verify the results of cleanup."""
        logger.info("🔍 Verifying cleanup results...")
        
        # Get new totals
        new_total = await self.conn.fetchval("SELECT COUNT(*) FROM user_fact_relationships")
        new_entities = await self.conn.fetchval("SELECT COUNT(*) FROM fact_entities")
        
        # Check for remaining noise
        remaining_fragments = await self.conn.fetchval("""
            SELECT COUNT(*) FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name LIKE '%door we%' OR fe.entity_name LIKE '%when you%'
        """)
        
        remaining_pronouns = await self.conn.fetchval("""
            SELECT COUNT(*) FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name IN ('i', 'you', 'me', 'it')
        """)
        
        logger.info(f"📊 POST-CLEANUP VERIFICATION:")
        logger.info(f"  Total facts: {new_total} (was {self.cleanup_stats['total_facts_before']})")
        logger.info(f"  Total entities: {new_entities}")
        logger.info(f"  Remaining fragments: {remaining_fragments} (should be 0)")
        logger.info(f"  Remaining pronouns: {remaining_pronouns} (should be 0)")
        
        if remaining_fragments == 0 and remaining_pronouns == 0:
            logger.info("✅ Cleanup verification PASSED - noise successfully removed!")
        else:
            logger.warning("⚠️  Some noise patterns still remain - may need additional cleanup")

async def main():
    """Main cleanup execution."""
    cleanup_manager = FactCleanupManager()
    
    try:
        await cleanup_manager.connect()
        
        # Step 1: Analyze current state
        total_to_remove = await cleanup_manager.analyze_noise_patterns()
        
        if total_to_remove == 0:
            logger.info("✅ No noisy facts found - database is clean!")
            return
        
        # Step 2: Preview what would be removed
        await cleanup_manager.preview_cleanup()
        
        # Step 3: Ask for confirmation
        print(f"\n🚨 READY TO CLEAN UP {total_to_remove} NOISY FACTS")
        print("This will permanently delete the facts shown above.")
        response = input("Do you want to proceed? (yes/no): ").lower().strip()
        
        if response == 'yes':
            cleanup_manager.dry_run = False
            await cleanup_manager.execute_cleanup()
            await cleanup_manager.verify_cleanup()
            print("🎉 Fact database cleanup completed successfully!")
        else:
            print("❌ Cleanup cancelled by user")
            
    except Exception as e:
        logger.error(f"❌ Cleanup process failed: {e}")
        raise
    finally:
        await cleanup_manager.close()

if __name__ == "__main__":
    print("🧹 WhisperEngine Fact Database Cleanup")
    print("=" * 50)
    asyncio.run(main())