import asyncio
from unittest.mock import AsyncMock, MagicMock
from src_v2.knowledge.manager import KnowledgeManager
from src_v2.knowledge.extractor import Fact

async def test_conflict_resolution():
    print("Testing Conflict Resolution Logic...")
    
    # Mock transaction
    tx = AsyncMock()
    tx.run = AsyncMock()
    
    # Test Case 1: Single Value Predicate (LIVES_IN)
    fact1 = Fact(subject="User", predicate="LIVES_IN", object="New York", confidence=0.9)
    await KnowledgeManager._merge_fact(tx, "user1", fact1)
    
    # Verify delete query was called for LIVES_IN
    calls = tx.run.call_args_list
    delete_call_found = False
    for call in calls:
        query = call[0][0]
        if "DELETE r" in query and "predicate: $predicate" in query:
            delete_call_found = True
            assert call.kwargs['predicate'] == "LIVES_IN"
            
    assert delete_call_found, "Failed to delete existing LIVES_IN relationship"
    print("SUCCESS: Single Value Predicate handled correctly.")
    
    # Reset mock
    tx.run.reset_mock()
    
    # Test Case 2: Antonym (HATES Pizza vs LIKES Pizza)
    fact2 = Fact(subject="User", predicate="HATES", object="Pizza", confidence=0.9)
    await KnowledgeManager._merge_fact(tx, "user1", fact2)
    
    # Verify delete query was called for Antonyms
    calls = tx.run.call_args_list
    antonym_delete_found = False
    for call in calls:
        query = call[0][0]
        if "DELETE r" in query and "predicate IN $antonyms" in query:
            antonym_delete_found = True
            assert "LIKES" in call.kwargs['antonyms']
            assert "LOVES" in call.kwargs['antonyms']
            assert call.kwargs['object_name'] == "Pizza"
            
    assert antonym_delete_found, "Failed to delete antonym relationships"
    print("SUCCESS: Antonym Conflict handled correctly.")

if __name__ == "__main__":
    asyncio.run(test_conflict_resolution())
