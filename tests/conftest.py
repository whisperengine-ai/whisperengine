"""
Test configuration and shared fixtures for WhisperEngine test suite.
"""

import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Ensure test environment is set
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CHROMADB_HOST", "localhost")
os.environ.setdefault("CHROMADB_PORT", "8000")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Test-specific environment
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DISCORD_BOT_TOKEN": "test_token_123",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "CHROMADB_HOST": "localhost",
        "CHROMADB_PORT": "8000",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "ANONYMIZED_TELEMETRY": "false",
        "LOG_LEVEL": "ERROR",  # Suppress logs during tests
    }
    
    os.environ.update(test_env_vars)
    
    yield test_env_vars
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for unit tests."""
    mock_client = Mock()
    mock_client.generate_completion = AsyncMock(return_value="Mocked LLM response")
    mock_client.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3] * 128)  # 384-dim mock
    mock_client.analyze_sentiment = AsyncMock(return_value={"sentiment": "positive", "confidence": 0.8})
    mock_client.extract_facts = AsyncMock(return_value=["User likes pizza", "User is 25 years old"])
    mock_client.detect_emotions = AsyncMock(return_value={"emotions": ["happy", "excited"], "confidence": 0.9})
    return mock_client


@pytest.fixture
def mock_discord_context():
    """Mock Discord context for command tests."""
    mock_ctx = Mock()
    mock_ctx.author.id = 12345
    mock_ctx.author.name = "test_user"
    mock_ctx.channel.id = 67890
    mock_ctx.guild.id = 11111
    mock_ctx.send = AsyncMock()
    return mock_ctx


@pytest.fixture
def mock_discord_message():
    """Mock Discord message for event tests."""
    mock_msg = Mock()
    mock_msg.author.id = 12345
    mock_msg.author.name = "test_user"
    mock_msg.author.bot = False
    mock_msg.content = "Hello, this is a test message"
    mock_msg.channel.id = 67890
    mock_msg.guild.id = 11111
    mock_msg.created_at = datetime.now()
    return mock_msg


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for memory tests."""
    return [
        {
            "user_id": "12345",
            "message": "Hello, my name is Alice",
            "timestamp": "2025-09-18T10:00:00Z",
            "channel_id": "67890"
        },
        {
            "user_id": "12345", 
            "message": "I work as a software developer",
            "timestamp": "2025-09-18T10:01:00Z",
            "channel_id": "67890"
        },
        {
            "user_id": "12345",
            "message": "I love playing guitar in my free time",
            "timestamp": "2025-09-18T10:02:00Z", 
            "channel_id": "67890"
        }
    ]


@pytest.fixture
def sample_user_facts():
    """Sample user facts for memory tests."""
    return [
        "User's name is Alice",
        "User works as a software developer", 
        "User enjoys playing guitar",
        "User lives in San Francisco",
        "User has a cat named Whiskers"
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Fast unit tests with mocked dependencies")
    config.addinivalue_line("markers", "integration: Integration tests requiring real services")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "security: Security validation tests")
    config.addinivalue_line("markers", "slow: Long-running tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)