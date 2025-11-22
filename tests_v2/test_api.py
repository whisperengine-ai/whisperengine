import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from src_v2.api.app import app
from src_v2.api.routes import agent_engine, character_manager
from src_v2.config.settings import settings

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    # Mock settings
    with patch.object(settings, 'DISCORD_BOT_NAME', 'TestBot'):
        # Mock character manager
        mock_char = MagicMock()
        mock_char.name = "TestBot"
        mock_char.system_prompt = "You are a test bot."
        
        with patch.object(character_manager, 'get_character', return_value=mock_char):
            # Mock agent engine
            with patch.object(agent_engine, 'generate_response', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = "Hello from API!"
                yield mock_generate

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_endpoint(mock_dependencies):
    payload = {
        "user_id": "user123",
        "message": "Hello API",
        "metadata_level": "standard"
    }
    
    response = client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["response"] == "Hello from API!"
    assert data["bot_name"] == "TestBot"
    assert data["memory_stored"] is True
    
    # Verify engine was called correctly
    mock_dependencies.assert_called_once()
    call_kwargs = mock_dependencies.call_args.kwargs
    assert call_kwargs["user_message"] == "Hello API"
    assert call_kwargs["user_id"] == "user123"

def test_chat_endpoint_missing_bot_name():
    # Test when bot name is not configured
    with patch.object(settings, 'DISCORD_BOT_NAME', None):
        payload = {
            "user_id": "user123",
            "message": "Hello"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 500
        assert "Bot name not configured" in response.json()["detail"]
