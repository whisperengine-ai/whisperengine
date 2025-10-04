"""
Test script for TransactionManager

Tests the roleplay transaction system with a simulated Dotty bartender scenario.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.roleplay.transaction_manager import create_transaction_manager


async def test_transaction_workflow():
    """Test complete transaction workflow for Dotty bartender"""
    
    print("🧪 Testing Roleplay Transaction System\n")
    
    # Initialize transaction manager
    manager = create_transaction_manager()
    await manager.initialize(
        host="localhost",
        port=5433,
        database="whisperengine",
        user="whisperengine",
        password="dev_password_123"
    )
    
    # Test data
    user_id = "test_user_12345"
    bot_name = "dotty"
    
    print("📋 Test 1: Check for pending transactions (should be none)")
    pending = await manager.check_pending_transaction(user_id, bot_name)
    print(f"Result: {pending}\n")
    
    print("📋 Test 2: Create drink order transaction")
    transaction_id = await manager.create_transaction(
        user_id=user_id,
        bot_name=bot_name,
        transaction_type="drink_order",
        context={
            "drink": "whiskey",
            "price": 5,
            "quantity": 1,
            "special_requests": "on the rocks",
            "order_message": "I'll have a whiskey on the rocks"
        },
        state="pending"
    )
    print(f"Created transaction ID: {transaction_id}\n")
    
    print("📋 Test 3: Check for pending transactions (should find order)")
    pending = await manager.check_pending_transaction(user_id, bot_name)
    if pending:
        print(f"Found pending transaction:")
        print(f"  ID: {pending.id}")
        print(f"  Type: {pending.transaction_type}")
        print(f"  State: {pending.state}")
        print(f"  Context: {pending.context}")
        print(f"\n  LLM Context String:")
        print(f"  {pending.to_context_string()}\n")
    
    print("📋 Test 4: Update transaction state to 'awaiting_payment'")
    success = await manager.update_transaction_state(
        transaction_id,
        "awaiting_payment",
        context_updates={"price_confirmed": True}
    )
    print(f"Update success: {success}\n")
    
    print("📋 Test 5: Check pending again (should show awaiting_payment)")
    pending = await manager.check_pending_transaction(user_id, bot_name)
    if pending:
        print(f"State: {pending.state}")
        print(f"Context: {pending.context}\n")
    
    print("📋 Test 6: Complete transaction")
    success = await manager.complete_transaction(
        transaction_id,
        final_context={"payment_received": True, "drink_served": True}
    )
    print(f"Completion success: {success}\n")
    
    print("📋 Test 7: Check pending (should be none - transaction completed)")
    pending = await manager.check_pending_transaction(user_id, bot_name)
    print(f"Pending: {pending}\n")
    
    print("📋 Test 8: Get transaction history")
    history = await manager.get_transaction_history(user_id, bot_name, limit=5)
    print(f"Transaction history ({len(history)} transactions):")
    for txn in history:
        print(f"  - {txn.transaction_type}: {txn.state} (ID: {txn.id})")
    print()
    
    # Create another transaction to test cancellation
    print("📋 Test 9: Create and cancel transaction")
    txn_id = await manager.create_transaction(
        user_id=user_id,
        bot_name=bot_name,
        transaction_type="drink_order",
        context={"drink": "beer", "price": 3},
        state="pending"
    )
    print(f"Created transaction ID: {txn_id}")
    
    success = await manager.cancel_transaction(txn_id, reason="User changed mind")
    print(f"Cancellation success: {success}\n")
    
    # Check history again
    print("📋 Test 10: Final transaction history")
    history = await manager.get_transaction_history(user_id, bot_name, limit=10)
    print(f"Total transactions: {len(history)}")
    for txn in history:
        completed_str = f" (completed {txn.completed_at})" if txn.completed_at else ""
        print(f"  - {txn.transaction_type}: {txn.state}{completed_str}")
    
    # Clean up
    await manager.close()
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_transaction_workflow())
