"""
Sprint 3 RelationshipTuner PostgreSQL Schema Migration

Creates clean schema for dynamic relationship scoring:
- relationship_scores: Current scores for each user-bot pair
- relationship_events: History of relationship updates
- trust_recovery_state: Active trust recovery tracking

Alpha/Dev Phase Approach:
- Clean drop/recreate (no production users to worry about)
- Proper types, constraints, and indexes from the start
- No backward compatibility constraints
"""

import asyncio
import asyncpg
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_sprint3_schema(postgres_pool):
    """
    Apply Sprint 3 RelationshipTuner schema changes.
    
    Uses aggressive migration approach suitable for alpha/dev phase.
    """
    logger.info("🔧 Starting Sprint 3 RelationshipTuner schema migration...")
    
    async with postgres_pool.acquire() as conn:
        # Option A: Clean drop/recreate (RECOMMENDED for alpha)
        # This gives us clean schema without legacy baggage
        
        logger.info("Dropping existing relationship tables (alpha approach)...")
        await conn.execute("DROP TABLE IF EXISTS trust_recovery_state CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS relationship_events CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS relationship_scores CASCADE;")
        
        # Create relationship_scores table
        logger.info("Creating relationship_scores table...")
        await conn.execute("""
            CREATE TABLE relationship_scores (
                user_id VARCHAR(255) NOT NULL,
                bot_name VARCHAR(100) NOT NULL,
                trust DECIMAL(5,4) NOT NULL DEFAULT 0.5000,
                affection DECIMAL(5,4) NOT NULL DEFAULT 0.4000,
                attunement DECIMAL(5,4) NOT NULL DEFAULT 0.3000,
                interaction_count INTEGER NOT NULL DEFAULT 0,
                last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                
                PRIMARY KEY (user_id, bot_name),
                
                -- Constraints for 0-1 range
                CHECK (trust >= 0.0 AND trust <= 1.0),
                CHECK (affection >= 0.0 AND affection <= 1.0),
                CHECK (attunement >= 0.0 AND attunement <= 1.0),
                CHECK (interaction_count >= 0)
            );
        """)
        
        # Create indexes for relationship_scores
        logger.info("Creating relationship_scores indexes...")
        await conn.execute("""
            CREATE INDEX idx_relationship_scores_user 
            ON relationship_scores(user_id);
        """)
        await conn.execute("""
            CREATE INDEX idx_relationship_scores_bot 
            ON relationship_scores(bot_name);
        """)
        await conn.execute("""
            CREATE INDEX idx_relationship_scores_trust 
            ON relationship_scores(trust) 
            WHERE trust < 0.4;  -- Partial index for low trust
        """)
        
        # Create relationship_events table (history)
        logger.info("Creating relationship_events table...")
        await conn.execute("""
            CREATE TABLE relationship_events (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                bot_name VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                trust_delta DECIMAL(5,4),
                affection_delta DECIMAL(5,4),
                attunement_delta DECIMAL(5,4),
                trust_value DECIMAL(5,4),
                affection_value DECIMAL(5,4),
                attunement_value DECIMAL(5,4),
                conversation_quality VARCHAR(20),
                emotion_variance DECIMAL(5,4),
                update_reason TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                
                -- Foreign key to relationship_scores
                FOREIGN KEY (user_id, bot_name) 
                    REFERENCES relationship_scores(user_id, bot_name)
                    ON DELETE CASCADE
            );
        """)
        
        # Create indexes for relationship_events
        logger.info("Creating relationship_events indexes...")
        await conn.execute("""
            CREATE INDEX idx_relationship_events_user_bot 
            ON relationship_events(user_id, bot_name);
        """)
        await conn.execute("""
            CREATE INDEX idx_relationship_events_type 
            ON relationship_events(event_type);
        """)
        await conn.execute("""
            CREATE INDEX idx_relationship_events_timestamp 
            ON relationship_events(created_at DESC);
        """)
        
        # Create trust_recovery_state table
        logger.info("Creating trust_recovery_state table...")
        await conn.execute("""
            CREATE TABLE trust_recovery_state (
                user_id VARCHAR(255) NOT NULL,
                bot_name VARCHAR(100) NOT NULL,
                recovery_stage VARCHAR(20) NOT NULL,
                initial_trust DECIMAL(5,4) NOT NULL,
                current_trust DECIMAL(5,4) NOT NULL,
                target_trust DECIMAL(5,4) NOT NULL,
                progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                recovery_actions_taken TEXT[],
                started_at TIMESTAMP NOT NULL,
                last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
                estimated_completion TIMESTAMP,
                
                PRIMARY KEY (user_id, bot_name, started_at),
                
                -- Foreign key to relationship_scores
                FOREIGN KEY (user_id, bot_name) 
                    REFERENCES relationship_scores(user_id, bot_name)
                    ON DELETE CASCADE,
                
                -- Constraints
                CHECK (initial_trust >= 0.0 AND initial_trust <= 1.0),
                CHECK (current_trust >= 0.0 AND current_trust <= 1.0),
                CHECK (target_trust >= 0.0 AND target_trust <= 1.0),
                CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0)
            );
        """)
        
        # Create indexes for trust_recovery_state
        logger.info("Creating trust_recovery_state indexes...")
        await conn.execute("""
            CREATE INDEX idx_trust_recovery_user_bot 
            ON trust_recovery_state(user_id, bot_name);
        """)
        await conn.execute("""
            CREATE INDEX idx_trust_recovery_stage 
            ON trust_recovery_state(recovery_stage) 
            WHERE recovery_stage IN ('active', 'recovering');
        """)
        
        logger.info("✅ Sprint 3 RelationshipTuner schema migration complete!")
        logger.info("   - relationship_scores: Current scores with trust/affection/attunement")
        logger.info("   - relationship_events: Historical relationship updates")
        logger.info("   - trust_recovery_state: Active recovery tracking")


async def verify_schema(postgres_pool):
    """Verify schema was created correctly."""
    logger.info("🔍 Verifying schema...")
    
    async with postgres_pool.acquire() as conn:
        # Check relationship_scores table
        result = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'relationship_scores'
            ORDER BY ordinal_position;
        """)
        
        logger.info("relationship_scores columns:")
        for row in result:
            logger.info(f"  - {row['column_name']}: {row['data_type']}")
        
        # Check indexes
        result = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('relationship_scores', 'relationship_events', 'trust_recovery_state')
            ORDER BY tablename, indexname;
        """)
        
        logger.info("\nIndexes:")
        for row in result:
            logger.info(f"  - {row['indexname']}")
        
        logger.info("\n✅ Schema verification complete!")


async def seed_test_data(postgres_pool):
    """
    Seed some test relationship data for validation.
    
    Optional - only for testing purposes.
    """
    logger.info("🌱 Seeding test relationship data...")
    
    async with postgres_pool.acquire() as conn:
        # Insert test relationship scores
        await conn.execute("""
            INSERT INTO relationship_scores 
                (user_id, bot_name, trust, affection, attunement, interaction_count)
            VALUES 
                ('test_user_1', 'Elena', 0.75, 0.80, 0.65, 25),
                ('test_user_1', 'Marcus', 0.68, 0.62, 0.58, 18),
                ('test_user_2', 'Elena', 0.45, 0.50, 0.40, 12),
                ('test_user_2', 'Ryan', 0.82, 0.88, 0.75, 30)
            ON CONFLICT (user_id, bot_name) DO NOTHING;
        """)
        
        # Insert test relationship events
        await conn.execute("""
            INSERT INTO relationship_events 
                (user_id, bot_name, event_type, trust_delta, affection_delta, 
                 attunement_delta, trust_value, affection_value, attunement_value,
                 conversation_quality, emotion_variance, update_reason)
            VALUES 
                ('test_user_1', 'Elena', 'score_update', 0.03, 0.04, 0.02,
                 0.75, 0.80, 0.65, 'excellent', 0.35, 'excellent conversation quality'),
                ('test_user_2', 'Elena', 'score_update', -0.02, -0.03, -0.01,
                 0.45, 0.50, 0.40, 'poor', 0.62, 'poor conversation quality; high emotional complexity')
            ON CONFLICT DO NOTHING;
        """)
        
        logger.info("✅ Test data seeded!")


async def main():
    """Main migration execution."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get PostgreSQL connection details
    # Use localhost:5433 for WhisperEngine multi-bot setup
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = int(os.getenv('POSTGRES_PORT', '5433'))
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_pass')
    
    logger.info(f"Connecting to PostgreSQL at {db_host}:{db_port}/{db_name}...")
    
    # Create connection pool
    postgres_pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5
    )
    
    try:
        # Run migration
        await migrate_sprint3_schema(postgres_pool)
        
        # Verify schema
        await verify_schema(postgres_pool)
        
        # Optionally seed test data
        seed_test = input("\nSeed test relationship data? (y/n): ").lower() == 'y'
        if seed_test:
            await seed_test_data(postgres_pool)
        
        logger.info("\n🎉 Sprint 3 RelationshipTuner migration complete!")
        logger.info("   Ready for relationship evolution engine integration!")
        
    finally:
        await postgres_pool.close()


if __name__ == '__main__':
    asyncio.run(main())
