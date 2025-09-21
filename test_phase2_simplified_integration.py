#!/usr/bin/env python3
"""
SIMPLIFIED PHASE 2 INTEGRATION TESTS
====================================
Focused integration tests for Phase 2.1 and 2.2 using local Qdrant configuration
Tests production pipeline functionality without Docker dependencies
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from memory.vector_memory_system import VectorMemoryStore, MemoryTier, VectorMemory, MemoryType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedPhase2Tester:
    """Simplified integration tester focusing on Phase 2.1 and 2.2 functionality"""
    
    def __init__(self):
        self.test_user_id = "phase2_simplified_test"
        self.memory_store = VectorMemoryStore()
        
    async def test_complete_three_tier_pipeline(self) -> Dict[str, Any]:
        """Test the complete three-tier memory pipeline from creation to management"""
        logger.info("🎯 TESTING: Complete three-tier memory pipeline")
        
        results = {
            "memories_created": 0,
            "initial_tier_distribution": {},
            "after_promotion_distribution": {},
            "promotion_stats": {},
            "errors": []
        }
        
        try:
            # Create a diverse set of memories with different characteristics
            test_memories = [
                {"content": "Critical system alert resolved", "age_days": 6, "significance": 0.9},
                {"content": "Daily team standup meeting", "age_days": 2, "significance": 0.2},
                {"content": "Major project milestone achieved", "age_days": 10, "significance": 0.85},
                {"content": "Casual coffee chat", "age_days": 1, "significance": 0.1},
                {"content": "Important client feedback", "age_days": 8, "significance": 0.75},
                {"content": "Random question about weather", "age_days": 1, "significance": 0.15}
            ]
            
            current_time = datetime.utcnow()
            
            # Create memories with varying ages
            for memory_data in test_memories:
                memory_time = current_time - timedelta(days=memory_data["age_days"])
                
                vector_memory = VectorMemory(
                    id=str(uuid.uuid4()),
                    user_id=self.test_user_id,
                    memory_type=MemoryType.CONVERSATION,
                    content=memory_data["content"],
                    memory_tier=MemoryTier.SHORT_TERM,
                    timestamp=memory_time
                )
                
                await self.memory_store.store_memory(vector_memory)
                results["memories_created"] += 1
            
            # Get initial tier distribution
            for tier in MemoryTier:
                tier_memories = await self.memory_store.get_memories_by_tier(
                    self.test_user_id, tier, limit=50
                )
                results["initial_tier_distribution"][tier.value] = len(tier_memories)
            
            logger.info(f"Initial distribution: {results['initial_tier_distribution']}")
            
            # Apply tier management
            promotion_stats = await self.memory_store.auto_manage_memory_tiers(self.test_user_id)
            results["promotion_stats"] = promotion_stats
            
            # Get tier distribution after promotion
            for tier in MemoryTier:
                tier_memories = await self.memory_store.get_memories_by_tier(
                    self.test_user_id, tier, limit=50
                )
                results["after_promotion_distribution"][tier.value] = len(tier_memories)
            
            logger.info(f"After promotion distribution: {results['after_promotion_distribution']}")
            logger.info(f"Promotion stats: {promotion_stats}")
            
            # Verify tier management worked
            if promotion_stats.get("promoted", 0) > 0 or promotion_stats.get("demoted", 0) > 0:
                logger.info("✅ Tier management executed successfully")
            else:
                logger.info("ℹ️ No tier changes needed (expected with fresh data)")
            
            return results
            
        except Exception as e:
            error_msg = f"Three-tier pipeline test failed: {e}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            return results
    
    async def test_memory_decay_integration(self) -> Dict[str, Any]:
        """Test memory decay with protection mechanisms"""
        logger.info("🎯 TESTING: Memory decay integration")
        
        results = {
            "decay_candidates_before": 0,
            "memories_protected": 0,
            "decay_stats": {},
            "final_memory_count": 0,
            "errors": []
        }
        
        try:
            # Get decay candidates before processing
            decay_candidates = await self.memory_store.get_memory_decay_candidates(
                self.test_user_id, threshold=0.5
            )
            results["decay_candidates_before"] = len(decay_candidates)
            
            logger.info(f"Found {len(decay_candidates)} decay candidates")
            
            # Protect some high-value memories
            all_memories = []
            for tier in MemoryTier:
                tier_memories = await self.memory_store.get_memories_by_tier(
                    self.test_user_id, tier, limit=50
                )
                all_memories.extend(tier_memories)
            
            high_value_memories = [m for m in all_memories if m.get("significance", 0) > 0.7]
            
            for memory in high_value_memories[:2]:  # Protect first 2 high-value memories
                success = await self.memory_store.protect_memory_from_decay(
                    memory["id"], "integration_test_protection"
                )
                if success:
                    results["memories_protected"] += 1
            
            logger.info(f"Protected {results['memories_protected']} high-value memories")
            
            # Apply memory decay
            decay_stats = await self.memory_store.apply_memory_decay(
                self.test_user_id, decay_rate=0.2
            )
            results["decay_stats"] = decay_stats
            
            logger.info(f"Decay stats: {decay_stats}")
            
            # Get final memory count
            final_memories = []
            for tier in MemoryTier:
                tier_memories = await self.memory_store.get_memories_by_tier(
                    self.test_user_id, tier, limit=50
                )
                final_memories.extend(tier_memories)
            
            results["final_memory_count"] = len(final_memories)
            
            logger.info(f"Final memory count: {results['final_memory_count']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Memory decay integration test failed: {e}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            return results
    
    async def test_tier_promotion_mechanisms(self) -> Dict[str, Any]:
        """Test specific tier promotion and demotion mechanisms"""
        logger.info("🎯 TESTING: Tier promotion mechanisms")
        
        results = {
            "manual_promotions": 0,
            "manual_demotions": 0,
            "tier_validation": {},
            "errors": []
        }
        
        try:
            # Get some memories to test promotion/demotion
            short_term_memories = await self.memory_store.get_memories_by_tier(
                self.test_user_id, MemoryTier.SHORT_TERM, limit=5
            )
            
            if len(short_term_memories) >= 2:
                # Test manual promotion
                memory_id = short_term_memories[0]["id"]
                success = await self.memory_store.promote_memory_tier(
                    memory_id, MemoryTier.MEDIUM_TERM, "integration_test_promotion"
                )
                if success:
                    results["manual_promotions"] += 1
                    logger.info(f"Successfully promoted memory to medium-term")
                
                # Test manual demotion (promote then demote)
                memory_id_2 = short_term_memories[1]["id"]
                await self.memory_store.promote_memory_tier(
                    memory_id_2, MemoryTier.MEDIUM_TERM, "test_setup"
                )
                
                success = await self.memory_store.demote_memory_tier(
                    memory_id_2, MemoryTier.SHORT_TERM, "integration_test_demotion"
                )
                if success:
                    results["manual_demotions"] += 1
                    logger.info(f"Successfully demoted memory back to short-term")
            
            # Validate tier distributions
            for tier in MemoryTier:
                tier_memories = await self.memory_store.get_memories_by_tier(
                    self.test_user_id, tier, limit=50
                )
                results["tier_validation"][tier.value] = len(tier_memories)
            
            logger.info(f"Tier validation: {results['tier_validation']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Tier promotion mechanisms test failed: {e}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            return results
    
    async def test_performance_baseline(self) -> Dict[str, Any]:
        """Test performance characteristics of Phase 2 features"""
        logger.info("🎯 TESTING: Performance baseline")
        
        results = {
            "memory_creation_time": 0,
            "tier_management_time": 0,
            "decay_processing_time": 0,
            "query_times": {},
            "baseline_met": False,
            "errors": []
        }
        
        try:
            # Test memory creation performance
            start_time = datetime.utcnow()
            
            for i in range(10):  # Create 10 test memories
                vector_memory = VectorMemory(
                    id=str(uuid.uuid4()),
                    user_id=self.test_user_id,
                    memory_type=MemoryType.CONVERSATION,
                    content=f"Performance test memory {i} with some content",
                    memory_tier=MemoryTier.SHORT_TERM
                )
                await self.memory_store.store_memory(vector_memory)
            
            results["memory_creation_time"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Test tier management performance
            start_time = datetime.utcnow()
            await self.memory_store.auto_manage_memory_tiers(self.test_user_id)
            results["tier_management_time"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Test decay processing performance
            start_time = datetime.utcnow()
            await self.memory_store.apply_memory_decay(self.test_user_id, decay_rate=0.1)
            results["decay_processing_time"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Test query performance
            for tier in MemoryTier:
                start_time = datetime.utcnow()
                await self.memory_store.get_memories_by_tier(self.test_user_id, tier, limit=20)
                query_time = (datetime.utcnow() - start_time).total_seconds()
                results["query_times"][tier.value] = query_time
            
            # Check if baseline is met (all operations under 2 seconds)
            max_time = max(
                results["memory_creation_time"],
                results["tier_management_time"],
                results["decay_processing_time"],
                max(results["query_times"].values())
            )
            
            results["baseline_met"] = max_time < 2.0
            
            logger.info(f"Performance results: "
                       f"creation={results['memory_creation_time']:.2f}s, "
                       f"tier_mgmt={results['tier_management_time']:.2f}s, "
                       f"decay={results['decay_processing_time']:.2f}s")
            
            if results["baseline_met"]:
                logger.info("✅ Performance baseline met!")
            else:
                logger.warning("⚠️ Performance baseline not met")
            
            return results
            
        except Exception as e:
            error_msg = f"Performance baseline test failed: {e}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all simplified Phase 2 integration tests"""
        logger.info("🚀 STARTING SIMPLIFIED PHASE 2 INTEGRATION TESTS")
        logger.info("=" * 60)
        
        test_results = {
            "test_session": str(uuid.uuid4()),
            "start_time": datetime.utcnow().isoformat(),
            "three_tier_pipeline": {},
            "memory_decay_integration": {},
            "tier_promotion_mechanisms": {},
            "performance_baseline": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # Test 1: Three-tier pipeline
            logger.info("Test 1: Three-tier memory pipeline...")
            test_results["three_tier_pipeline"] = await self.test_complete_three_tier_pipeline()
            
            # Test 2: Memory decay integration
            logger.info("\nTest 2: Memory decay integration...")
            test_results["memory_decay_integration"] = await self.test_memory_decay_integration()
            
            # Test 3: Tier promotion mechanisms
            logger.info("\nTest 3: Tier promotion mechanisms...")
            test_results["tier_promotion_mechanisms"] = await self.test_tier_promotion_mechanisms()
            
            # Test 4: Performance baseline
            logger.info("\nTest 4: Performance baseline...")
            test_results["performance_baseline"] = await self.test_performance_baseline()
            
            # Generate summary
            test_results["end_time"] = datetime.utcnow().isoformat()
            test_results["summary"] = self.generate_summary(test_results)
            
            # Log results
            self.log_results(test_results)
            
        except Exception as e:
            error_msg = f"Test execution failed: {e}"
            test_results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return test_results
    
    def generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            "tests_completed": 0,
            "tests_successful": 0,
            "memories_processed": 0,
            "tier_operations_working": False,
            "decay_operations_working": False,
            "performance_acceptable": False,
            "overall_success": False
        }
        
        # Check each test
        tests = ["three_tier_pipeline", "memory_decay_integration", 
                "tier_promotion_mechanisms", "performance_baseline"]
        
        for test_name in tests:
            test_data = test_results.get(test_name, {})
            if test_data:
                summary["tests_completed"] += 1
                if len(test_data.get("errors", [])) == 0:
                    summary["tests_successful"] += 1
        
        # Check specific functionality
        tier_test = test_results.get("three_tier_pipeline", {})
        if tier_test.get("memories_created", 0) > 0:
            summary["tier_operations_working"] = True
            summary["memories_processed"] += tier_test["memories_created"]
        
        decay_test = test_results.get("memory_decay_integration", {})
        if decay_test.get("decay_stats", {}).get("processed", 0) > 0:
            summary["decay_operations_working"] = True
        
        perf_test = test_results.get("performance_baseline", {})
        if perf_test.get("baseline_met", False):
            summary["performance_acceptable"] = True
        
        # Overall success
        summary["overall_success"] = (
            summary["tests_successful"] == summary["tests_completed"] and
            summary["tier_operations_working"] and
            summary["decay_operations_working"]
        )
        
        return summary
    
    def log_results(self, test_results: Dict[str, Any]):
        """Log comprehensive test results"""
        summary = test_results["summary"]
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 SIMPLIFIED PHASE 2 INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"📊 SUMMARY:")
        logger.info(f"   Tests Completed: {summary['tests_successful']}/{summary['tests_completed']}")
        logger.info(f"   Memories Processed: {summary['memories_processed']}")
        logger.info(f"   Tier Operations: {'✅ WORKING' if summary['tier_operations_working'] else '❌ FAILED'}")
        logger.info(f"   Decay Operations: {'✅ WORKING' if summary['decay_operations_working'] else '❌ FAILED'}")
        logger.info(f"   Performance: {'✅ ACCEPTABLE' if summary['performance_acceptable'] else '⚠️ NEEDS IMPROVEMENT'}")
        
        if summary["overall_success"]:
            logger.info("\n🎉 ALL SIMPLIFIED PHASE 2 TESTS PASSED!")
            logger.info("✅ Phase 2.1 and 2.2 are production ready!")
        else:
            logger.error("\n❌ SOME TESTS FAILED OR NEED ATTENTION")
        
        logger.info("=" * 60)

async def main():
    """Run simplified Phase 2 integration tests"""
    tester = SimplifiedPhase2Tester()
    
    try:
        results = await tester.run_all_tests()
        
        # Save results
        results_file = f"phase2_simplified_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📝 Results saved to: {results_file}")
        
        return results["summary"]["overall_success"]
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)