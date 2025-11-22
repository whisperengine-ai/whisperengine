import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src_v2.agents.engine import AgentEngine

@pytest.mark.asyncio
async def test_agent_engine_verbosity_injection():
    """Test that AgentEngine injects the correct instructions for verbosity preferences."""
    
    # Create mocks for dependencies
    mock_trust_manager = MagicMock()
    mock_feedback_analyzer = MagicMock()
    mock_goal_manager = MagicMock()
    mock_llm_client = MagicMock()
    
    # Configure mocks
    # Note: The method is get_relationship_level, not get_relationship
    mock_trust_manager.get_relationship_level = AsyncMock(return_value={
        "level": 1,
        "trust_score": 10,
        "unlocked_traits": [],
        "insights": [],
        "preferences": {
            "verbosity": "short",
            "style": "casual"
        }
    })
    
    mock_feedback_analyzer.analyze_user_feedback_patterns = AsyncMock(return_value={})
    mock_feedback_analyzer.get_current_mood = AsyncMock(return_value="Neutral")
    
    mock_goal_manager.get_active_goals = AsyncMock(return_value=[])
    
    # Mock LLM response
    mock_llm_response = MagicMock()
    mock_llm_response.content = "Test response"
    mock_llm_client.ainvoke = AsyncMock(return_value=mock_llm_response)
    
    # Initialize engine with injected dependencies
    engine = AgentEngine(
        trust_manager_dep=mock_trust_manager,
        feedback_analyzer_dep=mock_feedback_analyzer,
        goal_manager_dep=mock_goal_manager,
        llm_client_dep=mock_llm_client
    )
    
    # Mock router (it's initialized in __init__ but we can override it or mock its methods if needed)
    # For this test, we might need to mock the router if it's used.
    # Looking at engine.py, router is used in step 1.
    mock_router = MagicMock()
    mock_router.route_and_retrieve = AsyncMock(return_value={"context": "", "reasoning": ""})
    engine.router = mock_router

    # Mock character
    mock_character = MagicMock()
    mock_character.name = "TestBot"
    mock_character.style = "helpful"
    mock_character.example_dialogue = []
    mock_character.system_prompt = "You are a helpful assistant."
    
    # Run generate_response
    await engine.generate_response(
        character=mock_character,
        user_message="Hello",
        user_id="user123",
        context_variables={}
    )
    
    # Check if trust_manager.get_relationship_level was called
    mock_trust_manager.get_relationship_level.assert_called_with("user123", "TestBot")
    
    # Inspect the call to the LLM
    # The engine calls chain.ainvoke(inputs)
    # chain = prompt | self.llm
    # Depending on LangChain version and execution, it might call ainvoke, invoke, or the object itself.
    
    call_args = mock_llm_client.ainvoke.call_args
    if call_args is None:
        call_args = mock_llm_client.invoke.call_args
    if call_args is None:
        # Check if the mock itself was called
        call_args = mock_llm_client.call_args
        
    assert call_args is not None, f"LLM was not called. Mock calls: {mock_llm_client.mock_calls}"
    
    invoked_arg = call_args[0][0]
    
    messages = []
    # Handle ChatPromptValue (which is what LangChain passes when using the | operator)
    if hasattr(invoked_arg, 'to_messages'):
        messages = invoked_arg.to_messages()
    # Handle list of messages directly
    elif isinstance(invoked_arg, list):
        messages = invoked_arg
    
    if messages:
        # Find the system message
        system_content = ""
        for msg in messages:
            if msg.type == 'system':
                system_content = msg.content
                break
        
        print(f"System Prompt Content:\n{system_content}")
        
        # Assertions
        assert "RESPONSE LENGTH: Keep responses very concise" in system_content
        assert "TONE: Use casual, relaxed language" in system_content
    else:
        # Fallback for string or other types
        print(f"Invoked arg type: {type(invoked_arg)}")
        print(f"Invoked arg: {invoked_arg}")
        assert "RESPONSE LENGTH: Keep responses very concise" in str(invoked_arg)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_agent_engine_verbosity_injection())
    print("Test passed!")
