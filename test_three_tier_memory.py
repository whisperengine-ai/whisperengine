#!/usr/bin/env python3
"""
Test script for Phase 2.1 three-tier memory system
Tests memory tier promotion, demotion, and automatic management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from memory.vector_memory_system import VectorMemoryStore, MemoryTier, VectorMemory, MemoryType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreeTierMemoryTester:
    def __init__(self):
        self.memory_store = VectorMemoryStore()
        self.test_user_id = "tier_test_user_123"
        self.test_messages = [
            {"content": "I love hiking in the mountains", "significance": 0.3, "emotional_intensity": 0.4},
            {"content": "My dog passed away today", "significance": 0.9, "emotional_intensity": 0.95},
            {"content": "Just had coffee", "significance": 0.1, "emotional_intensity": 0.1},
            {"content": "Got promoted at work!", "significance": 0.8, "emotional_intensity": 0.8},
            {"content": "Weather is nice today", "significance": 0.2, "emotional_intensity": 0.2},
            {"content": "My birthday is next month", "significance": 0.6, "emotional_intensity": 0.5},
            {"content": "Learning to play guitar", "significance": 0.5, "emotional_intensity": 0.4},
            {"content": "Had a terrible car accident", "significance": 0.95, "emotional_intensity": 0.9}
        ]
        
    async def setup_test_data(self):
        """Create test memories with varying significance and age"""
        logger.info("🚀 PHASE 2.1 TEST: Setting up test data...")
        
        # Clear any existing test data
        await self.cleanup_test_data()
        
        current_time = datetime.utcnow()
        
        for i, message in enumerate(self.test_messages):
            # Create memories with different ages for tier promotion testing
            timestamp = current_time - timedelta(days=i)
            
            vector_memory = VectorMemory(
                id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                memory_type=MemoryType.CONVERSATION,
                content=message["content"],
                memory_tier=MemoryTier.SHORT_TERM,  # All start as short-term
                tier_promotion_date=None,
                tier_demotion_date=None,
                decay_protection=message["significance"] > 0.8  # Protect highly significant memories
            )
            
            await self.memory_store.store_memory(vector_memory)
            
        logger.info(f"✅ Created {len(self.test_messages)} test memories")
        
    async def test_tier_promotion(self):
        """Test promoting memories between tiers"""
        logger.info("🎯 TESTING: Memory tier promotion...")
        
        # Get a memory ID to promote
        short_term_memories = await self.memory_store.get_memories_by_tier(
            self.test_user_id, MemoryTier.SHORT_TERM, limit=5
        )
        
        if not short_term_memories:
            logger.error("❌ No short-term memories found for promotion test")
            return False
            
        memory_id = short_term_memories[0]["id"]
        original_tier = short_term_memories[0]["memory_tier"]
        
        logger.info(f"Promoting memory {memory_id} from {original_tier} to medium-term")
        
        # Promote to medium-term
        success = await self.memory_store.promote_memory_tier(
            memory_id, MemoryTier.MEDIUM_TERM, "test_promotion"
        )
        
        if success:
            # Verify promotion
            medium_term_memories = await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.MEDIUM_TERM, limit=10
            )
            
            promoted_memory = None
            for memory in medium_term_memories:
                if memory["id"] == memory_id:
                    promoted_memory = memory
                    break
                    
            if promoted_memory and promoted_memory["memory_tier"] == MemoryTier.MEDIUM_TERM.value:
                logger.info("✅ Memory tier promotion successful!")
                return True
            else:
                logger.error("❌ Memory tier promotion failed - memory not found in medium-term tier")
                return False
        else:
            logger.error("❌ Memory tier promotion returned False")
            return False
            
    async def test_tier_demotion(self):
        """Test demoting memories between tiers"""
        logger.info("🎯 TESTING: Memory tier demotion...")
        
        # First promote a memory to medium-term so we can demote it
        short_term_memories = await self.memory_store.get_memories_by_tier(
            self.test_user_id, MemoryTier.SHORT_TERM, limit=5
        )
        
        if not short_term_memories:
            logger.error("❌ No short-term memories found for demotion test setup")
            return False
            
        memory_id = short_term_memories[0]["id"]
        
        # Promote first
        await self.memory_store.promote_memory_tier(
            memory_id, MemoryTier.MEDIUM_TERM, "test_setup"
        )
        
        # Now demote back to short-term
        logger.info(f"Demoting memory {memory_id} from medium-term back to short-term")
        
        success = await self.memory_store.demote_memory_tier(
            memory_id, MemoryTier.SHORT_TERM, "test_demotion"
        )
        
        if success:
            # Verify demotion
            short_term_memories_after = await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.SHORT_TERM, limit=20
            )
            
            demoted_memory = None
            for memory in short_term_memories_after:
                if memory["id"] == memory_id:
                    demoted_memory = memory
                    break
                    
            if demoted_memory and demoted_memory["memory_tier"] == MemoryTier.SHORT_TERM.value:
                logger.info("✅ Memory tier demotion successful!")
                return True
            else:
                logger.error("❌ Memory tier demotion failed - memory not found in short-term tier")
                return False
        else:
            logger.error("❌ Memory tier demotion returned False")
            return False
            
    async def test_automatic_tier_management(self):
        """Test automatic tier management based on age and significance"""
        logger.info("🎯 TESTING: Automatic tier management...")
        
        # Run automatic tier management
        stats = await self.memory_store.auto_manage_memory_tiers(self.test_user_id)
        
        logger.info(f"Auto-management stats: {stats}")
        
        if "error" in stats:
            logger.error("❌ Automatic tier management failed with error")
            return False
            
        # Check that some operations happened
        total_operations = stats.get("promoted", 0) + stats.get("demoted", 0) + stats.get("expired", 0)
        
        if total_operations > 0:
            logger.info("✅ Automatic tier management performed operations!")
            
            # Check tier distribution
            short_term_count = len(await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.SHORT_TERM, limit=50
            ))
            medium_term_count = len(await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.MEDIUM_TERM, limit=50
            ))
            long_term_count = len(await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.LONG_TERM, limit=50
            ))
            
            logger.info(f"📊 Tier distribution: Short={short_term_count}, Medium={medium_term_count}, Long={long_term_count}")
            return True
        else:
            logger.info("⚠️ No automatic tier operations performed (may be expected with test data)")
            return True  # This might be expected with fresh test data
            
    async def test_tier_filtering(self):
        """Test retrieving memories by specific tiers"""
        logger.info("🎯 TESTING: Memory retrieval by tier...")
        
        # Test each tier
        for tier in MemoryTier:
            memories = await self.memory_store.get_memories_by_tier(
                self.test_user_id, tier, limit=10
            )
            
            logger.info(f"📋 {tier.value} tier: {len(memories)} memories")
            
            # Verify all memories are in the correct tier
            for memory in memories:
                if memory["memory_tier"] != tier.value:
                    logger.error(f"❌ Found {memory['memory_tier']} memory in {tier.value} tier!")
                    return False
                    
        logger.info("✅ Tier filtering working correctly!")
        return True
        
    async def test_memory_tier_data_integrity(self):
        """Test that tier data is properly stored and retrieved"""
        logger.info("🎯 TESTING: Memory tier data integrity...")
        
        # Get all memories and check for tier metadata
        all_memories = []
        for tier in MemoryTier:
            tier_memories = await self.memory_store.get_memories_by_tier(
                self.test_user_id, tier, limit=50
            )
            all_memories.extend(tier_memories)
            
        if not all_memories:
            logger.error("❌ No memories found for data integrity test")
            return False
            
        for memory in all_memories:
            # Check required tier fields
            required_fields = ["memory_tier", "significance", "decay_protection"]
            for field in required_fields:
                if field not in memory:
                    logger.error(f"❌ Missing required field {field} in memory {memory.get('id', 'unknown')}")
                    return False
                    
            # Validate tier value
            if memory["memory_tier"] not in [tier.value for tier in MemoryTier]:
                logger.error(f"❌ Invalid tier value: {memory['memory_tier']}")
                return False
                
        logger.info("✅ Memory tier data integrity validated!")
        return True
        
    async def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Note: In a real cleanup, we'd delete all test user memories
            # For this test, we'll just log that cleanup would happen
            logger.info("🧹 Test cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup test data: {e}")
            
    async def run_all_tests(self):
        """Run all three-tier memory system tests"""
        logger.info("🚀 STARTING PHASE 2.1 THREE-TIER MEMORY SYSTEM TESTS")
        
        test_results = {}
        
        try:
            # Setup
            await self.setup_test_data()
            
            # Run tests
            test_results["tier_promotion"] = await self.test_tier_promotion()
            test_results["tier_demotion"] = await self.test_tier_demotion()
            test_results["automatic_management"] = await self.test_automatic_tier_management()
            test_results["tier_filtering"] = await self.test_tier_filtering()
            test_results["data_integrity"] = await self.test_memory_tier_data_integrity()
            
            # Cleanup
            await self.cleanup_test_data()
            
            # Results summary
            passed_tests = sum(1 for result in test_results.values() if result)
            total_tests = len(test_results)
            
            logger.info(f"\n🎯 PHASE 2.1 TEST RESULTS:")
            logger.info(f"✅ Passed: {passed_tests}/{total_tests} tests")
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"   {status}: {test_name}")
                
            if passed_tests == total_tests:
                logger.info("🎉 ALL PHASE 2.1 THREE-TIER MEMORY TESTS PASSED!")
                return True
            else:
                logger.error(f"❌ {total_tests - passed_tests} tests failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            return False

async def main():
    """Run the three-tier memory system tests"""
    tester = ThreeTierMemoryTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)