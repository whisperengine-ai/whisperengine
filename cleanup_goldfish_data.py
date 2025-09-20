#!/usr/bin/env python3
"""
Goldfish Data Cleanup Script

This script uses the FactValidator to clean up corrupted goldfish data
and establish "Bubbles" as the correct goldfish name.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from memory.fact_validator import FactValidator, initialize_fact_validation_tables
from utils.postgresql_user_db import PostgreSQLUserDB
from utils.logger import logger
from env_manager import env_manager


async def cleanup_goldfish_data():
    """Clean up corrupted goldfish data and establish Bubbles as correct name"""
    
    print("🐠 Starting goldfish data cleanup...")
    
    try:
        # Initialize PostgreSQL database
        postgres_db = PostgreSQLUserDB()
        await postgres_db.initialize()
        print("✅ PostgreSQL database initialized")
        
        # Initialize fact validation tables
        await initialize_fact_validation_tables(postgres_db)
        print("✅ Fact validation tables initialized")
        
        # Create fact validator
        fact_validator = FactValidator(postgres_db)
        print("✅ Fact validator created")
        
        # Test user ID (replace with actual user ID that had goldfish issues)
        user_id = "test_user_123"  # Replace with actual user ID from Discord
        
        # Get existing facts to see what we have
        print(f"\n📊 Checking existing facts for user {user_id}...")
        existing_facts = await fact_validator.get_validated_facts(user_id, subject="goldfish")
        
        if existing_facts:
            print(f"Found {len(existing_facts)} existing goldfish facts:")
            for fact in existing_facts:
                print(f"  - {fact.subject} {fact.predicate} {fact.object} (confidence: {fact.confidence})")
        else:
            print("No existing goldfish facts found")
        
        # Resolve goldfish conflict - establish "Bubbles" as correct name
        print("\n🔧 Resolving goldfish conflict to establish 'Bubbles' as correct name...")
        await fact_validator.resolve_goldfish_conflict(user_id, "Bubbles")
        print("✅ Goldfish conflict resolved")
        
        # Verify the fix
        print("\n✅ Verifying goldfish facts after cleanup...")
        updated_facts = await fact_validator.get_validated_facts(user_id, subject="goldfish")
        
        if updated_facts:
            print(f"Found {len(updated_facts)} goldfish facts after cleanup:")
            for fact in updated_facts:
                print(f"  - {fact.subject} {fact.predicate} {fact.object} (confidence: {fact.confidence})")
        else:
            print("No goldfish facts found after cleanup")
        
        # Test fact extraction and validation
        print("\n🧪 Testing fact extraction with goldfish message...")
        test_message = "My goldfish is named Bubbles and he loves swimming around his bowl"
        facts, conflicts = await fact_validator.process_message(test_message, user_id)
        
        print(f"Extracted {len(facts)} facts from test message:")
        for fact in facts:
            print(f"  - {fact.subject} {fact.predicate} {fact.object} (confidence: {fact.confidence})")
            
        if conflicts:
            print(f"Detected {len(conflicts)} conflicts:")
            for conflict in conflicts:
                print(f"  - Conflict: {conflict.old_fact.object} vs {conflict.new_fact.object} (resolution: {conflict.resolution})")
        else:
            print("No conflicts detected ✅")
        
        print("\n🎉 Goldfish data cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during goldfish cleanup: {e}")
        logger.error(f"Goldfish cleanup failed: {e}")
        raise
    finally:
        # Clean up database connection
        if 'postgres_db' in locals():
            await postgres_db.close()
            print("✅ Database connection closed")


if __name__ == "__main__":
    print("🚀 WhisperEngine Goldfish Data Cleanup")
    print("======================================")
    
    # Load environment
    env_manager.load_environment()
    
    # Run cleanup
    asyncio.run(cleanup_goldfish_data())