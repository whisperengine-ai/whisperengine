import asyncio
import os
from src_v2.knowledge.manager import knowledge_manager
from src_v2.tools.memory_tools import LookupFactsTool

# Mock the knowledge manager's query_graph method to avoid needing a real Neo4j connection for this unit test
# However, if we want to test the integration, we might want to see if it actually calls the method.

async def test_lookup_tool():
    print("Testing LookupFactsTool...")
    
    # Initialize tool
    tool = LookupFactsTool(user_id="test_user_123")
    
    # Mock the query_graph method on the global instance
    original_method = knowledge_manager.query_graph
    
    async def mock_query_graph(user_id, question):
        print(f"Mock query_graph called with user_id={user_id}, question='{question}'")
        return "Mocked Result: User likes Pizza"
    
    knowledge_manager.query_graph = mock_query_graph
    
    try:
        # Run the tool
        query = "What do I like?"
        result = await tool._arun(query)
        print(f"Tool Result: {result}")
        
        assert "Mocked Result: User likes Pizza" in result
        print("SUCCESS: Tool called query_graph correctly.")
        
    finally:
        # Restore original method
        knowledge_manager.query_graph = original_method

if __name__ == "__main__":
    asyncio.run(test_lookup_tool())
