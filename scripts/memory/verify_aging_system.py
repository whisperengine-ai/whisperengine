#!/usr/bin/env python3
"""Verification script for memory aging system functionality."""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', '..', 'src')
sys.path.insert(0, src_path)

from src.memory.aging.aging_policy import MemoryAgingPolicy
from src.memory.aging.aging_runner import MemoryAgingRunner
from src.memory.aging.consolidator import MemoryConsolidator


class MemoryAgingVerifier:
    """Verification suite for memory aging functionality."""

    def __init__(self):
        self.results = {}
        self.errors = []

    def verify_policy_scoring(self):
        """Verify policy scoring logic."""
        print("🧠 Verifying policy scoring logic...")
        
        policy = MemoryAgingPolicy()
        
        # Test cases
        now = datetime.utcnow().timestamp()
        
        # High-value memory
        high_value = {
            'created_at': now - 3600,  # 1 hour old
            'importance_score': 0.9,
            'decay_score': 0.1,
            'emotional_intensity': 0.7,
            'access_count': 10
        }
        
        # Low-value memory
        low_value = {
            'created_at': now - 2592000,  # 30 days old
            'importance_score': 0.1,
            'decay_score': 0.8,
            'emotional_intensity': 0.1,
            'access_count': 1
        }
        
        try:
            high_score = policy.compute_retention_score(high_value)
            low_score = policy.compute_retention_score(low_value)
            
            assert high_score > low_score, "High-value memory should score higher"
            assert high_score > policy.prune_threshold, "High-value should exceed threshold"
            assert 0.0 <= high_score <= 1.0, "Score should be in valid range"
            assert 0.0 <= low_score <= 1.0, "Score should be in valid range"
            
            self.results['policy_scoring'] = 'PASS'
            print("✅ Policy scoring verification passed")
            
        except (AssertionError, ValueError, TypeError) as e:
            self.errors.append(f"Policy scoring failed: {e}")
            self.results['policy_scoring'] = 'FAIL'
            print(f"❌ Policy scoring verification failed: {e}")

    def verify_safety_checks(self):
        """Verify safety check logic."""
        print("🛡️ Verifying safety checks...")
        
        policy = MemoryAgingPolicy()
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        test_cases = [
            {
                'name': 'high_emotional_intensity',
                'memory': {
                    'created_at': old_timestamp,
                    'emotional_intensity': 0.8,
                    'importance_score': 0.1
                },
                'should_be_prunable': False
            },
            {
                'name': 'intervention_outcome',
                'memory': {
                    'created_at': old_timestamp,
                    'emotional_intensity': 0.2,
                    'intervention_outcome': 'success',
                    'importance_score': 0.1
                },
                'should_be_prunable': False
            },
            {
                'name': 'recent_memory',
                'memory': {
                    'created_at': datetime.utcnow().timestamp(),
                    'emotional_intensity': 0.1,
                    'importance_score': 0.1
                },
                'should_be_prunable': False
            }
        ]
        
        try:
            for case in test_cases:
                is_prunable = policy.is_prunable(case['memory'])
                expected = case['should_be_prunable']
                
                assert is_prunable == expected, f"Safety check failed for {case['name']}"
            
            self.results['safety_checks'] = 'PASS'
            print("✅ Safety checks verification passed")
            
        except (AssertionError, ValueError, TypeError) as e:
            self.errors.append(f"Safety checks failed: {e}")
            self.results['safety_checks'] = 'FAIL'
            print(f"❌ Safety checks verification failed: {e}")

    async def verify_runner_integration(self):
        """Verify runner integration."""
        print("🏃 Verifying runner integration...")
        
        # Mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memories_by_user = AsyncMock()
        mock_memory_manager.delete_specific_memory = AsyncMock()
        
        policy = MemoryAgingPolicy()
        runner = MemoryAgingRunner(
            memory_manager=mock_memory_manager,
            policy=policy
        )
        
        # Test data
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        memories = [
            {
                'id': 'test_memory_1',
                'created_at': old_timestamp,
                'importance_score': 0.9,
                'emotional_intensity': 0.3,
                'access_count': 5
            },
            {
                'id': 'test_memory_2',
                'created_at': datetime.utcnow().timestamp(),
                'importance_score': 0.1,
                'emotional_intensity': 0.1,
                'access_count': 1
            }
        ]
        
        mock_memory_manager.get_memories_by_user.return_value = memories
        
        try:
            # Test dry run
            results = await runner.run(user_id="test_user", dry_run=True)
            
            assert 'scanned' in results, "Results should include scanned count"
            assert 'flagged' in results, "Results should include flagged count" 
            assert 'pruned' in results, "Results should include pruned count"
            assert 'preserved' in results, "Results should include preserved count"
            assert results['dry_run'] is True, "Dry run flag should be set"
            assert results['scanned'] == 2, "Should scan both memories"
            
            # Verify no deletions in dry run
            mock_memory_manager.delete_specific_memory.assert_not_called()
            
            self.results['runner_integration'] = 'PASS'
            print("✅ Runner integration verification passed")
            
        except (AssertionError, ValueError, TypeError, AttributeError) as e:
            self.errors.append(f"Runner integration failed: {e}")
            self.results['runner_integration'] = 'FAIL'
            print(f"❌ Runner integration verification failed: {e}")

    def verify_consolidator_basic(self):
        """Verify basic consolidator functionality."""
        print("🔄 Verifying consolidator basics...")
        
        try:
            mock_embedding_manager = Mock()
            consolidator = MemoryConsolidator(
                embedding_manager=mock_embedding_manager,
                similarity_threshold=0.92
            )
            
            assert consolidator.embedding_manager is not None
            assert consolidator.similarity_threshold == 0.92
            
            self.results['consolidator_basic'] = 'PASS'
            print("✅ Consolidator basic verification passed")
            
        except (AssertionError, ValueError, TypeError, AttributeError) as e:
            self.errors.append(f"Consolidator basic failed: {e}")
            self.results['consolidator_basic'] = 'FAIL'
            print(f"❌ Consolidator basic verification failed: {e}")

    async def verify_consolidator_functionality(self):
        """Verify consolidator functionality."""
        print("🔄 Verifying consolidator functionality...")
        
        try:
            mock_embedding_manager = Mock()
            consolidator = MemoryConsolidator(
                embedding_manager=mock_embedding_manager
            )
            
            # Test empty consolidation
            result = await consolidator.consolidate([])
            assert result == [], "Empty consolidation should return empty list"
            
            # Test single memory
            single_memory = [{'id': 'test1', 'content': 'test'}]
            result = await consolidator.consolidate(single_memory)
            assert len(result) == 1, "Single memory should return single result"
            
            # Test multiple memories
            multiple_memories = [
                {'id': 'test1', 'content': 'test1'},
                {'id': 'test2', 'content': 'test2'}
            ]
            result = await consolidator.consolidate(multiple_memories)
            assert len(result) > 0, "Multiple memories should produce result"
            
            self.results['consolidator_functionality'] = 'PASS'
            print("✅ Consolidator functionality verification passed")
            
        except (AssertionError, ValueError, TypeError, AttributeError) as e:
            self.errors.append(f"Consolidator functionality failed: {e}")
            self.results['consolidator_functionality'] = 'FAIL'
            print(f"❌ Consolidator functionality verification failed: {e}")

    def verify_configuration_flexibility(self):
        """Verify configuration flexibility."""
        print("⚙️ Verifying configuration flexibility...")
        
        try:
            # Test different policy configurations
            conservative = MemoryAgingPolicy(
                importance_weight=0.8,
                recency_weight=0.1,
                access_weight=0.1,
                decay_lambda=0.005,
                prune_threshold=0.1
            )
            
            aggressive = MemoryAgingPolicy(
                importance_weight=0.5,
                recency_weight=0.2,
                access_weight=0.1,
                decay_lambda=0.02,
                prune_threshold=0.4
            )
            
            # Verify configurations are applied
            assert conservative.importance_weight == 0.8
            assert conservative.prune_threshold == 0.1
            assert aggressive.importance_weight == 0.5
            assert aggressive.prune_threshold == 0.4
            
            self.results['configuration_flexibility'] = 'PASS'
            print("✅ Configuration flexibility verification passed")
            
        except (AssertionError, ValueError, TypeError, AttributeError) as e:
            self.errors.append(f"Configuration flexibility failed: {e}")
            self.results['configuration_flexibility'] = 'FAIL'
            print(f"❌ Configuration flexibility verification failed: {e}")

    async def run_all_verifications(self):
        """Run all verification tests."""
        print("🔍 Starting Memory Aging System Verification")
        print("=" * 50)
        
        # Run synchronous verifications
        self.verify_policy_scoring()
        self.verify_safety_checks()
        self.verify_consolidator_basic()
        self.verify_configuration_flexibility()
        
        # Run asynchronous verifications
        await self.verify_runner_integration()
        await self.verify_consolidator_functionality()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result == 'PASS')
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print("\n🚨 ERRORS ENCOUNTERED:")
            for error in self.errors:
                print(f"  • {error}")
        
        if failed_tests == 0:
            print("\n🎉 All verifications passed! Memory aging system is ready.")
            return True
        else:
            print(f"\n⚠️ {failed_tests} verification(s) failed. Please review.")
            return False


async def main():
    """Main verification entry point."""
    verifier = MemoryAgingVerifier()
    success = await verifier.run_all_verifications()
    
    if success:
        print("\n✨ Memory aging system verification completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Memory aging system verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())