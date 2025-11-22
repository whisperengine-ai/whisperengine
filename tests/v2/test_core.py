import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src_v2.memory.manager import MemoryManager
from src_v2.agents.engine import AgentEngine
from src_v2.core.character import Character
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def mock_db_manager():
    with patch("src_v2.memory.manager.db_manager") as mock:
        mock.postgres_pool = MagicMock() # Pool itself isn't async, its methods might be
        mock.qdrant_client = AsyncMock()
        yield mock

@pytest.fixture
def mock_embedding_service():
    with patch("src_v2.memory.manager.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_query_async = AsyncMock(return_value=[0.1] * 384)
        yield instance

@pytest.mark.asyncio
async def test_memory_manager_add_message(mock_db_manager, mock_embedding_service):
    manager = MemoryManager()
    # Mock embedding service on the instance since it's created in __init__
    manager.embedding_service = mock_embedding_service
    
    user_id = "123"
    character_name = "elena"
    role = "human"
    content = "Hello"

    # Mock Postgres connection context manager
    # pool.acquire() returns an async context manager
    mock_conn = AsyncMock()
    mock_acquire_ctx = MagicMock()
    mock_acquire_ctx.__aenter__.return_value = mock_conn
    mock_acquire_ctx.__aexit__.return_value = None
    
    mock_db_manager.postgres_pool.acquire.return_value = mock_acquire_ctx

    await manager.add_message(user_id, character_name, role, content)

    # Verify Postgres insert
    mock_conn.execute.assert_called_once()
    args = mock_conn.execute.call_args[0]
    assert "INSERT INTO v2_chat_history" in args[0]
    assert args[1] == user_id
    assert args[2] == character_name
    assert args[3] == role
    assert args[4] == content

    # Verify Qdrant upsert
    mock_db_manager.qdrant_client.upsert.assert_called_once()
    
@pytest.mark.asyncio
async def test_memory_manager_search_memories(mock_db_manager, mock_embedding_service):
    manager = MemoryManager()
    manager.embedding_service = mock_embedding_service
    
    # Mock Qdrant search result
    mock_point = MagicMock()
    mock_point.payload = {"content": "Old memory", "role": "human", "timestamp": "2023-01-01"}
    mock_point.score = 0.9
    
    mock_db_manager.qdrant_client.search.return_value = [mock_point]

    results = await manager.search_memories("query", "123")

    assert len(results) == 1
    assert results[0]["content"] == "Old memory"
    mock_embedding_service.embed_query_async.assert_called_with("query")

@pytest.fixture
def mock_llm():
    with patch("src_v2.agents.engine.create_llm") as mock_create:
        mock_llm_instance = AsyncMock()
        mock_create.return_value = mock_llm_instance
        yield mock_llm_instance

@pytest.mark.asyncio
async def test_agent_engine_generate_response(mock_llm):
    engine = AgentEngine()
    
    # Mock LLM response
    mock_response = AIMessage(content="Hello there!")
    # The chain is prompt | llm. We need to mock the chain invocation.
    # However, AgentEngine creates the chain inside generate_response: chain = prompt | self.llm
    # So self.llm is invoked. 
    # Actually, `chain.ainvoke(inputs)` is called. 
    # Since `chain = prompt | self.llm`, `chain.ainvoke` eventually calls `self.llm.ainvoke` (or similar depending on LC version).
    # But `prompt | self.llm` creates a RunnableSequence.
    # It's easier to mock the `ainvoke` method of the LLM if we can, but `prompt | llm` logic is internal to LangChain.
    # A better approach might be to mock `ChatPromptTemplate` and `self.llm` behavior.
    
    # Let's mock the chain creation or just the LLM call if possible.
    # In `generate_response`: `chain = prompt | self.llm` -> `response = await chain.ainvoke(inputs)`
    # If we mock `self.llm`, `prompt | self.llm` works if `self.llm` is a Runnable.
    # `AsyncMock` isn't a Runnable by default.
    
    # Let's patch `AgentEngine.create_llm` to return a MagicMock that has `ainvoke`.
    # Actually `create_llm` is called in `__init__`.
    
    # We can just set `engine.llm` to a mock that behaves like a Runnable.
    mock_runnable = AsyncMock()
    mock_runnable.ainvoke.return_value = mock_response
    
    # We also need to handle the pipe operator `|`. 
    # `prompt | llm` calls `prompt.__or__(llm)`.
    # If we mock `ChatPromptTemplate`, we can control the chain.
    
    with patch("src_v2.agents.engine.ChatPromptTemplate") as mock_prompt_cls:
        mock_prompt = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt
        
        # Mock the pipe operator to return our mock runnable
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_prompt.__or__.return_value = mock_chain
        
        character = Character(
            name="test_char",
            system_prompt="You are a test bot."
        )
        
        response = await engine.generate_response(
            character=character,
            user_message="Hi",
            user_id="user1"
        )
        
        assert response == "Hello there!"
        mock_chain.ainvoke.assert_called_once()
        inputs = mock_chain.ainvoke.call_args[0][0]
        assert inputs["user_input_message"][0].content == "Hi"

