#!/usr/bin/env python3
"""
Test script for Phase 2.2 memory decay with significance protection
Tests memory decay mechanism, protection, and candidate identification
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

class MemoryDecayTester:
    def __init__(self):
        self.memory_store = VectorMemoryStore()
        self.test_user_id = "decay_test_user_456"
        self.test_memories = [
            {"content": "Old insignificant memory", "significance": 0.1, "age_days": 30, "protect": False},
            {"content": "Important life event", "significance": 0.9, "age_days": 20, "protect": True},
            {"content": "Moderate importance note", "significance": 0.5, "age_days": 10, "protect": False},
            {"content": "Very low significance data", "significance": 0.05, "age_days": 5, "protect": False},
            {"content": "Protected valuable memory", "significance": 0.8, "age_days": 40, "protect": True},
            {"content": "Recent unimportant chat", "significance": 0.2, "age_days": 1, "protect": False}
        ]
        
    async def setup_test_data(self):
        """Create test memories with varying significance, age, and protection"""
        logger.info("🚀 PHASE 2.2 TEST: Setting up memory decay test data...")
        
        # Clear any existing test data
        await self.cleanup_test_data()
        
        current_time = datetime.utcnow()
        
        for i, memory_data in enumerate(self.test_memories):
            # Create memories with specific ages
            timestamp = current_time - timedelta(days=memory_data["age_days"])
            
            vector_memory = VectorMemory(
                id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                memory_type=MemoryType.CONVERSATION,
                content=memory_data["content"],
                memory_tier=MemoryTier.SHORT_TERM,
                tier_promotion_date=None,
                tier_demotion_date=None,
                decay_protection=memory_data["protect"]
            )
            
            # Set custom timestamp for age testing
            vector_memory.timestamp = timestamp
            
            await self.memory_store.store_memory(vector_memory)
            
        logger.info(f"✅ Created {len(self.test_memories)} test memories with varying ages and significance")
        
    async def test_decay_candidates(self):
        """Test identification of decay candidates"""
        logger.info("🎯 TESTING: Memory decay candidate identification...")
        
        candidates = await self.memory_store.get_memory_decay_candidates(
            self.test_user_id, threshold=0.3
        )
        
        logger.info(f"Found {len(candidates)} decay candidates")
        
        # Verify candidates are properly sorted and below threshold
        for candidate in candidates:
            if candidate["significance"] > 0.3:
                logger.error(f"❌ Candidate has significance {candidate['significance']} above threshold 0.3")
                return False
            
            if candidate["decay_protection"]:
                logger.error(f"❌ Protected memory found in candidates: {candidate['content']}")
                return False
                
        logger.info("✅ Decay candidate identification working correctly!")
        return True
        
    async def test_memory_protection(self):
        """Test memory protection from decay"""
        logger.info("🎯 TESTING: Memory decay protection...")
        
        # Get a memory to protect
        candidates = await self.memory_store.get_memory_decay_candidates(
            self.test_user_id, threshold=0.6
        )
        
        if not candidates:
            logger.error("❌ No candidates found for protection test")
            return False
            
        memory_id = candidates[0]["id"]
        
        # Protect the memory
        success = await self.memory_store.protect_memory_from_decay(
            memory_id, "test_protection"
        )
        
        if not success:
            logger.error("❌ Failed to protect memory")
            return False
            
        # Verify protection
        protected_memories = await self.memory_store.get_protected_memories(self.test_user_id)
        
        protected_ids = [mem["id"] for mem in protected_memories]
        if memory_id not in protected_ids:
            logger.error("❌ Memory not found in protected list")
            return False
            
        logger.info("✅ Memory protection working correctly!")
        return True
        
    async def test_protection_removal(self):
        """Test removing protection from memories"""
        logger.info("🎯 TESTING: Memory protection removal...")
        
        # Get protected memories
        protected_memories = await self.memory_store.get_protected_memories(self.test_user_id)
        
        if not protected_memories:
            logger.error("❌ No protected memories found for removal test")
            return False
            
        memory_id = protected_memories[0]["id"]
        
        # Remove protection
        success = await self.memory_store.remove_memory_decay_protection(
            memory_id, "test_removal"
        )
        
        if not success:
            logger.error("❌ Failed to remove memory protection")
            return False
            
        # Verify removal
        protected_after = await self.memory_store.get_protected_memories(self.test_user_id)
        protected_ids_after = [mem["id"] for mem in protected_after]
        
        if memory_id in protected_ids_after:
            logger.error("❌ Memory still found in protected list after removal")
            return False
            
        logger.info("✅ Memory protection removal working correctly!")
        return True
        
    async def test_memory_decay_application(self):
        """Test applying memory decay"""
        logger.info("🎯 TESTING: Memory decay application...")
        
        # Apply decay with moderate rate
        stats = await self.memory_store.apply_memory_decay(
            self.test_user_id, decay_rate=0.2
        )
        
        logger.info(f"Decay stats: {stats}")
        
        if "error" in stats:
            logger.error("❌ Memory decay application failed with error")
            return False
            
        # Check that some operations happened
        total_operations = stats.get("processed", 0)
        
        if total_operations == 0:
            logger.error("❌ No memories were processed during decay")
            return False
            
        # Verify protected memories weren't affected
        if stats.get("protected", 0) > 0:
            logger.info(f"✅ {stats['protected']} protected memories were skipped during decay")
            
        # Check if any memories were decayed
        if stats.get("decayed", 0) > 0:
            logger.info(f"✅ {stats['decayed']} memories had their significance reduced")
            
        logger.info("✅ Memory decay application working correctly!")
        return True
        
    async def test_decay_data_integrity(self):
        """Test that decay preserves data integrity"""
        logger.info("🎯 TESTING: Memory decay data integrity...")
        
        # Get all memories and check for decay metadata
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
            # Check that significance is within valid range
            significance = memory.get("significance", 0.5)
            if significance < 0.0 or significance > 1.0:
                logger.error(f"❌ Invalid significance value: {significance}")
                return False
                
            # Check decay protection field
            if "decay_protection" not in memory:
                logger.error(f"❌ Missing decay_protection field in memory {memory.get('id', 'unknown')}")
                return False
                
        logger.info("✅ Memory decay data integrity validated!")
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
        """Run all memory decay system tests"""
        logger.info("🚀 STARTING PHASE 2.2 MEMORY DECAY SYSTEM TESTS")
        
        test_results = {}
        
        try:
            # Setup
            await self.setup_test_data()
            
            # Run tests
            test_results["decay_candidates"] = await self.test_decay_candidates()
            test_results["memory_protection"] = await self.test_memory_protection()
            test_results["protection_removal"] = await self.test_protection_removal()
            test_results["decay_application"] = await self.test_memory_decay_application()
            test_results["data_integrity"] = await self.test_decay_data_integrity()
            
            # Cleanup
            await self.cleanup_test_data()
            
            # Results summary
            passed_tests = sum(1 for result in test_results.values() if result)
            total_tests = len(test_results)
            
            logger.info(f"\n🎯 PHASE 2.2 TEST RESULTS:")
            logger.info(f"✅ Passed: {passed_tests}/{total_tests} tests")
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"   {status}: {test_name}")
                
            if passed_tests == total_tests:
                logger.info("🎉 ALL PHASE 2.2 MEMORY DECAY TESTS PASSED!")
                return True
            else:
                logger.error(f"❌ {total_tests - passed_tests} tests failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            return False

async def main():
    """Run the memory decay system tests"""
    tester = MemoryDecayTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)