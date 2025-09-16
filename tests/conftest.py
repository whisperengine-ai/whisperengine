"""
Test configuration and fixtures for the WhisperEngine project
"""

import pytest
import os
import tempfile
from unittest.mock import patch

# Use centralized environment management instead of direct dotenv
from env_manager import load_environment

# Mock imports commented out until test_mocks.py is updated for LLMClient
# from tests.test_mocks import (
#     MockLLMClient,
#     create_mock_llm_client,
#     create_disconnected_mock_llm_client,
#     HAPPY_EMOTION_RESPONSES,
#     PERSONAL_INFO_RESPONSES,
#     TRUST_INDICATOR_RESPONSES,
#     USER_FACTS_RESPONSES
# )


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client that works and has default responses"""
    return create_mock_llm_client(connection_works=True)


@pytest.fixture
def disconnected_mock_llm_client():
    """Provide a mock LLM client that simulates connection failure"""
    return create_disconnected_mock_llm_client()


@pytest.fixture
def happy_emotion_mock_llm_client():
    """Provide a mock LLM client with predefined happy emotion responses"""
    return create_mock_llm_client(connection_works=True, emotion_responses=HAPPY_EMOTION_RESPONSES)


@pytest.fixture
def personal_info_mock_llm_client():
    """Provide a mock LLM client with predefined personal info responses"""
    return create_mock_llm_client(
        connection_works=True, personal_info_responses=PERSONAL_INFO_RESPONSES
    )


@pytest.fixture
def comprehensive_mock_llm_client():
    """Provide a mock LLM client with all predefined responses"""
    return create_mock_llm_client(
        connection_works=True,
        emotion_responses=HAPPY_EMOTION_RESPONSES,
        personal_info_responses=PERSONAL_INFO_RESPONSES,
        trust_responses=TRUST_INDICATOR_RESPONSES,
        user_facts_responses=USER_FACTS_RESPONSES,
    )


@pytest.fixture
def real_llm_client():
    """Provide a real LLM client if environment is configured for integration testing"""
    load_environment()

    # Only return real client if explicitly requested via environment variable
    if os.getenv("USE_REAL_LLM", "false").lower() in ("true", "1", "yes"):
        try:
            from src.llm.llm_client import LLMClient

            client = LLMClient()
            if client.check_connection():
                return client
        except Exception:
            pass

    # Default to mock client for unit tests
    return create_mock_llm_client(connection_works=True)


@pytest.fixture
def temp_profiles_file():
    """Provide a temporary file for user profiles during testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def test_environment():
    """Set up test environment variables"""
    original_env = os.environ.copy()

    # Set test-specific environment variables
    # Note: Using shorter timeouts for tests to avoid slow test runs
    # Production defaults are higher (90s/120s) for LM Studio compatibility
    test_env = {
        "LLM_MAX_TOKENS_EMOTION": "200",
        "LLM_MAX_TOKENS_FACT_EXTRACTION": "500",
        "LLM_REQUEST_TIMEOUT": "30",  # Shorter for tests vs 90s production default
        "LLM_CONNECTION_TIMEOUT": "5",  # Shorter for tests vs 10s production default
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(params=["mock", "real"])
def llm_client_mode(request):
    """Parametrized fixture that provides both mock and real LLM clients"""
    if request.param == "mock":
        return create_mock_llm_client(connection_works=True)
    else:
        # Only use real client if environment supports it
        load_environment()
        if os.getenv("USE_REAL_LLM", "false").lower() in ("true", "1", "yes"):
            try:
                from src.llm.llm_client import LLMClient

                client = LLMClient()
                if client.check_connection():
                    return client
            except Exception:
                pass

        # Skip real LLM tests if not available
        pytest.skip("Real LLM client not available or not enabled")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real LLM"
    )
    config.addinivalue_line("markers", "unit: mark test as unit test using mocks")
    config.addinivalue_line("markers", "llm: mark test as requiring LLM functionality")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their content"""
    for item in items:
        # Mark tests that use real LLM client as integration tests
        if "real_llm_client" in item.fixturenames:
            item.add_marker(pytest.mark.integration)

        # Mark tests that use mock clients as unit tests
        if any(
            fixture in item.fixturenames
            for fixture in [
                "mock_llm_client",
                "disconnected_mock_llm_client",
                "happy_emotion_mock_llm_client",
                "personal_info_mock_llm_client",
            ]
        ):
            item.add_marker(pytest.mark.unit)

        # Mark all tests that deal with LLM functionality
        if (
            any(
                fixture in item.fixturenames
                for fixture in ["mock_llm_client", "real_llm_client", "llm_client_mode"]
            )
            or "llm" in item.name.lower()
        ):
            item.add_marker(pytest.mark.llm)
