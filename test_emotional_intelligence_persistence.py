#!/usr/bin/env python3
"""
Test Emotional Intelligence Persistence
Test the new database persistence for user emotional support strategies.
"""

import asyncio
import logging
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.intelligence.emotional_intelligence import PredictiveEmotionalIntelligence
from src.intelligence.proactive_support import SupportStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_emotional_intelligence_persistence():
    """Test emotional intelligence strategy persistence"""
    print("🧠 Testing Emotional Intelligence Persistence")
    print("=" * 50)
    
    # Initialize system
    ei_system = PredictiveEmotionalIntelligence()
    
    # Initialize persistence
    await ei_system.initialize_persistence()
    print("✅ Persistence initialized")
    
    # Test user ID
    test_user_id = "test_user_12345"
    strategy_type = f"{test_user_id}_strategy"
    
    print(f"\n📝 Testing with user: {test_user_id}")
    
    # Test 1: Create and save a new strategy
    print("\n🔹 Test 1: Create and save new strategy")
    
    # Create a test strategy
    test_strategy = SupportStrategy(
        strategy_id=strategy_type,
        user_preferences={"communication_style": "casual", "preferred_time": "evening"},
        effective_approaches=["gentle_check_in", "resource_offering"],
        approaches_to_avoid=["direct_confrontation"],
        optimal_timing={"morning": "low_energy", "evening": "receptive"},
        communication_style="casual",
        support_history=[
            {
                "intervention_id": "test_intervention_1",
                "effectiveness_score": 0.8,
                "outcome_type": "successful",
                "timestamp": datetime.now(UTC).isoformat()
            }
        ],
        last_updated=datetime.now(UTC)
    )
    
    # Save strategy
    save_result = await ei_system.save_user_strategy(test_user_id, test_strategy)
    print(f"   Save result: {save_result}")
    
    # Test 2: Load the strategy back
    print("\n🔹 Test 2: Load strategy from database")
    
    loaded_strategy = await ei_system.load_user_strategy(test_user_id, strategy_type)
    if loaded_strategy:
        print("   ✅ Strategy loaded successfully")
        print(f"   Strategy ID: {loaded_strategy.strategy_id}")
        print(f"   Effective approaches: {loaded_strategy.effective_approaches}")
        print(f"   User preferences: {loaded_strategy.user_preferences}")
        print(f"   Support history entries: {len(loaded_strategy.support_history)}")
    else:
        print("   ❌ Failed to load strategy")
        return False
    
    # Test 3: Load all strategies for user
    print("\n🔹 Test 3: Load all user strategies")
    
    all_strategies = await ei_system.load_all_user_strategies(test_user_id)
    print(f"   Loaded {len(all_strategies)} strategies")
    for strategy_id, strategy in all_strategies.items():
        print(f"   - {strategy_id}: {len(strategy.effective_approaches)} effective approaches")
    
    # Test 4: Test strategy loading helper
    print("\n🔹 Test 4: Test strategy loading helper")
    
    # Clear in-memory cache
    ei_system.user_strategies.clear()
    
    # Use the helper to load strategy
    await ei_system._ensure_user_strategy_loaded(test_user_id)  # noqa: SLF001
    
    if test_user_id in ei_system.user_strategies:
        print("   ✅ Strategy loaded via helper method")
        strategy = ei_system.user_strategies[test_user_id]
        print(f"   Loaded strategy has {len(strategy.effective_approaches)} effective approaches")
    else:
        print("   ❌ Helper method failed to load strategy")
        return False
    
    # Test 5: Update strategy and save
    print("\n🔹 Test 5: Update and save strategy")
    
    strategy = ei_system.user_strategies[test_user_id]
    original_approaches = len(strategy.effective_approaches)
    
    # Add a new effective approach
    strategy.effective_approaches.append("skill_building")
    strategy.support_history.append({
        "intervention_id": "test_intervention_2", 
        "effectiveness_score": 0.9,
        "outcome_type": "highly_successful",
        "timestamp": datetime.now(UTC).isoformat()
    })
    
    # Save updated strategy
    await ei_system._save_strategy_if_updated(test_user_id)  # noqa: SLF001
    print("   ✅ Strategy updated and saved")
    
    # Test 6: Verify updates persisted
    print("\n🔹 Test 6: Verify updates persisted")
    
    # Clear cache and reload
    ei_system.user_strategies.clear()
    reloaded_strategy = await ei_system.load_user_strategy(test_user_id, strategy_type)
    
    if reloaded_strategy:
        new_approaches = len(reloaded_strategy.effective_approaches)
        print(f"   Original approaches: {original_approaches}")
        print(f"   New approaches: {new_approaches}")
        print(f"   Support history entries: {len(reloaded_strategy.support_history)}")
        
        if new_approaches > original_approaches:
            print("   ✅ Updates successfully persisted")
        else:
            print("   ❌ Updates not persisted")
            return False
    else:
        print("   ❌ Failed to reload updated strategy")
        return False
    
    print("\n🎉 All tests passed! Emotional Intelligence persistence is working correctly.")
    return True


async def main():
    """Main test function"""
    try:
        success = await test_emotional_intelligence_persistence()
        if success:
            print("\n✅ Emotional Intelligence Persistence Test: PASSED")
            return 0
        else:
            print("\n❌ Emotional Intelligence Persistence Test: FAILED")
            return 1
    except Exception as e:  # noqa: BLE001
        print(f"\n💥 Test failed with error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)