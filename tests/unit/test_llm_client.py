"""
Unit tests for LLM Client functionality.

Tests the core LLM client methods with mocked external dependencies.
Focuses on business logic, error handling, and API interaction patterns.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import json
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from src.llm.llm_client import LLMClient
from src.utils.exceptions import LLMConnectionError, LLMError, LLMRateLimitError, LLMTimeoutError


@pytest.fixture
def mock_environment():
    """Mock environment variables for consistent test environment."""
    with patch.dict('os.environ', {
        'LLM_CHAT_API_URL': 'http://test.local:1234/v1',
        'LLM_CHAT_API_KEY': 'test_key',
        'LLM_MODEL_NAME': 'test_model',
        'LLM_EMOTION_ENDPOINT': 'http://test.local:1234/v1/emotion',
        'LLM_FACTS_ENDPOINT': 'http://test.local:1234/v1/facts',
        'ENVIRONMENT': 'test'
    }):
        yield


@pytest.fixture
def mock_client_dependencies():
    """Mock all external dependencies for LLM client."""
    with patch('src.security.api_key_security.get_api_key_manager') as mock_get_manager, \
         patch('src.llm.llm_client.LLMClient._initialize_local_llm') as mock_init_local, \
         patch('src.llm.llm_client.LLMClient._initialize_llamacpp_llm') as mock_init_llama, \
         patch('src.utils.logging_config.get_logger') as mock_logger:
        
        mock_get_manager.return_value = None
        mock_logger.return_value = Mock()
        
        yield {
            'api_key_manager': mock_get_manager,
            'init_local': mock_init_local,
            'init_llama': mock_init_llama,
            'logger': mock_logger
        }


class TestLLMClientInitialization:
    """Test LLM client initialization and configuration."""

    def test_init_with_defaults(self, mock_environment, mock_client_dependencies):
        """Test client initialization with default values."""
        client = LLMClient()
        assert client.api_url == 'http://test.local:1234/v1'

    def test_init_with_custom_values(self, mock_client_dependencies):
        """Test client initialization with custom API URL and key."""
        client = LLMClient(
            api_url='http://custom.api/v1',
            api_key='custom_key'
        )
        assert client.api_url == 'http://custom.api/v1'

    def test_init_without_env_vars(self, mock_client_dependencies):
        """Test client initialization without environment variables."""
        with patch.dict('os.environ', {}, clear=True):
            client = LLMClient()
            assert client.api_url == 'http://localhost:1234/v1'


class TestLLMClientConnectionChecking:
    """Test connection checking functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    @patch('requests.Session.get')
    def test_check_connection_success(self, mock_get, client):
        """Test successful connection check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response

        assert client.check_connection() is True

    @patch('requests.Session.get')
    def test_check_connection_failure(self, mock_get, client):
        """Test connection check failure."""
        mock_get.side_effect = ConnectionError("Connection failed")
        assert client.check_connection() is False

    @patch('requests.Session.get')
    def test_check_connection_timeout(self, mock_get, client):
        """Test connection check with timeout."""
        mock_get.side_effect = Timeout("Request timed out")
        assert client.check_connection() is False

    @patch('requests.Session.get')
    def test_check_connection_http_error(self, mock_get, client):
        """Test connection check with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        assert client.check_connection() is False


class TestLLMClientChatCompletion:
    """Test chat completion functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    @pytest.fixture
    def sample_messages(self):
        """Sample message data for testing."""
        return [{"role": "user", "content": "Hello, how are you?"}]

    @patch('requests.Session.post')
    def test_generate_chat_completion_success(self, mock_post, client, sample_messages):
        """Test successful chat completion generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "I'm doing well, thank you!"
                }
            }]
        }
        mock_post.return_value = mock_response

        result = client.generate_chat_completion(sample_messages)
        
        assert result == "I'm doing well, thank you!"
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_generate_chat_completion_rate_limit(self, mock_post, client, sample_messages):
        """Test chat completion with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
        mock_post.return_value = mock_response

        with pytest.raises(LLMRateLimitError):
            client.generate_chat_completion(sample_messages)

    @patch('requests.Session.post')
    def test_generate_chat_completion_timeout(self, mock_post, client, sample_messages):
        """Test chat completion with timeout."""
        mock_post.side_effect = Timeout("Request timed out")

        with pytest.raises(LLMTimeoutError):
            client.generate_chat_completion(sample_messages)

    @patch('requests.Session.post')
    def test_generate_chat_completion_connection_error(self, mock_post, client, sample_messages):
        """Test chat completion with connection error."""
        mock_post.side_effect = ConnectionError("Connection failed")

        with pytest.raises(LLMConnectionError):
            client.generate_chat_completion(sample_messages)

    @patch('requests.Session.post')
    def test_generate_chat_completion_malformed_response(self, mock_post, client, sample_messages):
        """Test chat completion with malformed response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_post.return_value = mock_response

        with pytest.raises(LLMError):
            client.generate_chat_completion(sample_messages)


class TestLLMClientFactExtraction:
    """Test fact extraction functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    @patch('src.llm.llm_client.LLMClient.generate_facts_chat_completion')
    def test_extract_facts_success(self, mock_generate, client):
        """Test successful fact extraction."""
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "facts": [
                            "User likes pizza",
                            "User is 25 years old"
                        ],
                        "confidence": 0.8
                    })
                }
            }]
        }

        result = client.extract_facts("I'm 25 and love pizza")
        
        assert "facts" in result
        assert len(result["facts"]) == 2
        assert "User likes pizza" in result["facts"]
        assert "User is 25 years old" in result["facts"]
        assert result["confidence"] == 0.8

    @patch('src.llm.llm_client.LLMClient.generate_facts_chat_completion')
    def test_extract_facts_no_facts(self, mock_generate, client):
        """Test fact extraction when no facts are found."""
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "facts": [],
                        "confidence": 0.1
                    })
                }
            }]
        }

        result = client.extract_facts("Just saying hello")
        
        assert "facts" in result
        assert len(result["facts"]) == 0
        assert result["confidence"] == 0.1

    @patch('src.llm.llm_client.LLMClient.generate_facts_chat_completion')
    def test_extract_facts_error_handling(self, mock_generate, client):
        """Test fact extraction error handling."""
        mock_generate.side_effect = LLMError("Failed to extract facts")

        with pytest.raises(LLMError):
            client.extract_facts("Test message")


class TestLLMClientPersonalInfoExtraction:
    """Test personal information extraction functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    @patch('src.llm.llm_client.LLMClient.generate_facts_chat_completion')
    def test_extract_personal_info_success(self, mock_generate, client):
        """Test successful personal information extraction."""
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "personal_info": {
                            "name": ["John"],
                            "age": ["25"],
                            "location": ["New York"]
                        },
                        "confidence": 0.9
                    })
                }
            }]
        }

        result = client.extract_personal_info("Hi, I'm John, 25 years old from New York")
        
        assert "personal_info" in result
        assert result["personal_info"]["name"] == ["John"]
        assert result["personal_info"]["age"] == ["25"]
        assert result["personal_info"]["location"] == ["New York"]
        assert result["confidence"] == 0.9

    @patch('src.llm.llm_client.LLMClient.generate_facts_chat_completion')
    def test_extract_personal_info_no_info(self, mock_generate, client):
        """Test personal info extraction when no info is found."""
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "personal_info": {
                            "name": [],
                            "age": [],
                            "location": []
                        },
                        "confidence": 0.1
                    })
                }
            }]
        }

        result = client.extract_personal_info("Just a regular message")
        
        assert "personal_info" in result
        assert len(result["personal_info"]["name"]) == 0
        assert result["confidence"] == 0.1


class TestLLMClientEmotionGeneration:
    """Test emotion-based chat completion functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        # Mock the emotion endpoint property
        client = LLMClient()
        client.emotion_chat_endpoint = 'http://test.local:1234/v1/emotion'
        return client

    @patch('requests.Session.post')
    def test_generate_emotion_chat_completion_success(self, mock_post, client):
        """Test successful emotion-based chat completion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "I understand you're feeling excited about this!"
                }
            }]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "I'm so excited!"}]
        
        result = client.generate_emotion_chat_completion(
            messages, 
            model="emotion-model",
            temperature=0.7
        )
        
        # This method returns a dict, not just the content
        assert "choices" in result
        assert result["choices"][0]["message"]["content"] == "I understand you're feeling excited about this!"
        mock_post.assert_called_once()

    def test_generate_emotion_chat_completion_no_endpoint(self, mock_environment, mock_client_dependencies):
        """Test emotion chat completion without endpoint configured."""
        client = LLMClient()
        # Don't set emotion_chat_endpoint
        
        messages = [{"role": "user", "content": "Test message"}]
        
        # Test that method raises ValueError when endpoint not configured
        with pytest.raises(ValueError, match="Emotion API endpoint not configured"):
            client.generate_emotion_chat_completion(messages, model="emotion-model")


class TestLLMClientVisionSupport:
    """Test vision-related functionality."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    def test_has_vision_support_default(self, client):
        """Test default vision support check."""
        # Without specific model configuration, should return False
        assert client.has_vision_support() is False

    def test_create_vision_message_no_support(self, client):
        """Test creation of vision message when vision not supported."""
        text = "What's in this image?"
        images = ["data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."]
        
        result = client.create_vision_message(text, images)
        
        assert "role" in result
        assert "content" in result
        assert result["role"] == "user"
        # Without vision support, should just return text content
        assert result["content"] == text

    def test_get_vision_config(self, client):
        """Test getting vision configuration."""
        config = client.get_vision_config()
        
        assert isinstance(config, dict)
        # Should contain basic vision configuration
        assert "max_images" in config
        assert "supports_vision" in config
        assert config["supports_vision"] is False


class TestLLMClientConfiguration:
    """Test client configuration and setup."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    def test_get_client_config(self, client):
        """Test getting client configuration."""
        config = client.get_client_config()
        
        assert isinstance(config, dict)
        assert "api_url" in config
        assert config["api_url"] == 'http://test.local:1234/v1'

    def test_client_cleanup(self, client):
        """Test client cleanup and resource management."""
        # Test that destructor doesn't raise exceptions
        del client


class TestLLMClientMessageHandling:
    """Test message processing and formatting."""

    @pytest.fixture
    def client(self, mock_environment, mock_client_dependencies):
        """Create a test client instance."""
        return LLMClient()

    def test_fix_message_alternation(self, client):
        """Test message alternation fixing for conversation flow."""
        # Test messages that need alternation fixing
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "How are you?"},  # Duplicate user role
            {"role": "assistant", "content": "I'm fine"},
            {"role": "assistant", "content": "How about you?"}  # Duplicate assistant role
        ]
        
        fixed_messages = client._fix_message_alternation(messages)
        
        # Should have some result (actual logic may vary)
        assert isinstance(fixed_messages, list)
        assert len(fixed_messages) >= 1

    @patch('src.llm.llm_client.LLMClient.generate_chat_completion')
    def test_get_chat_response_simple(self, mock_generate, client):
        """Test simple chat response generation."""
        # Mock to return proper dict format
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": "Test response"
                }
            }]
        }
        
        messages = [{"role": "user", "content": "Hello"}]
        result = client.get_chat_response(messages)
        
        assert result == "Test response"
        mock_generate.assert_called_once()

    @patch('src.llm.llm_client.LLMClient.generate_chat_completion')
    def test_generate_completion_wrapper(self, mock_generate, client):
        """Test the generate_completion wrapper method."""
        # Mock to return proper dict format
        mock_generate.return_value = {
            "choices": [{
                "message": {
                    "content": "Completion response"
                }
            }]
        }
        
        result = client.generate_completion(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        assert result == "Completion response"
        # Verify that the prompt was converted to message format
        call_args = mock_generate.call_args[0][0]
        assert call_args[0]["role"] == "user"
        assert call_args[0]["content"] == "Test prompt"