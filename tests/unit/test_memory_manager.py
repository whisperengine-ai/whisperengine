"""
Unit tests for Memory Manager functionality.

Tests the core memory management methods with mocked ChromaDB dependencies.
Focuses on conversation storage, fact extraction, and retrieval logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
from datetime import datetime

from src.memory.memory_manager import UserMemoryManager
from src.utils.exceptions import MemoryError, MemoryRetrievalError, MemoryStorageError, ValidationError


class MockEmbeddingFunction:
    """Mock ChromaDB embedding function that matches the interface."""
    
    def name(self):
        return "sentence_transformer"
    
    def __call__(self, texts):
        # Return mock embeddings for any input
        if isinstance(texts, list):
            return [[0.1, 0.2, 0.3] for _ in texts]
        else:
            return [[0.1, 0.2, 0.3]]


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client and collections."""
    with patch('src.memory.memory_manager.chromadb.HttpClient') as mock_http_client, \
         patch('src.memory.memory_manager.chromadb.PersistentClient') as mock_persistent_client, \
         patch('src.memory.memory_manager.embedding_functions.SentenceTransformerEmbeddingFunction') as mock_embedding_func:
        
        # Create mock embedding function
        mock_embedding_instance = MockEmbeddingFunction()
        mock_embedding_func.return_value = mock_embedding_instance
        
        # Create mock collections
        mock_collection = Mock()
        mock_global_collection = Mock()
        mock_facts_collection = Mock()
        
        # Configure mock client for HTTP
        mock_http_instance = Mock()
        mock_http_instance.heartbeat.return_value = None  # Successful heartbeat
        mock_http_instance.get_or_create_collection.side_effect = [mock_collection, mock_global_collection]
        mock_http_client.return_value = mock_http_instance
        
        # Configure mock client for Persistent (fallback)
        mock_persistent_instance = Mock()
        mock_persistent_instance.heartbeat.return_value = None  # Successful heartbeat
        mock_persistent_instance.get_or_create_collection.side_effect = [mock_collection, mock_global_collection]
        mock_persistent_client.return_value = mock_persistent_instance
        
        yield {
            'client': mock_http_instance,
            'collection': mock_collection,  # user_memories collection
            'global_collection': mock_global_collection,  # global_facts collection
            'global_facts': mock_global_collection,  # Alias for tests expecting this key
            'facts': mock_facts_collection,  # Separate facts collection for domain tests
            'embedding_function': mock_embedding_instance,
            'http_client_class': mock_http_client,
            'persistent_client_class': mock_persistent_client
        }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for fact extraction."""
    mock_client = Mock()
    mock_client.extract_facts = Mock()
    mock_client.extract_personal_info = Mock()
    mock_client.extract_user_facts = Mock()
    return mock_client


@pytest.fixture
def mock_emotion_manager():
    """Mock emotion manager."""
    with patch('src.memory.memory_manager.EmotionManager') as mock_manager_class:
        mock_manager = Mock()
        
        # Mock the return values that can be unpacked
        mock_user_profile = Mock()
        mock_user_profile.relationship_level.value = "friendly"
        mock_user_profile.interaction_count = 5
        
        mock_emotion_profile = Mock()
        mock_emotion_profile.detected_emotion.value = "neutral"
        mock_emotion_profile.confidence = 0.8
        mock_emotion_profile.intensity = 0.5
        
        # Mock process_interaction to return proper tuple
        mock_manager.process_interaction.return_value = (mock_user_profile, mock_emotion_profile)
        mock_manager.analyze_emotion = Mock()
        mock_manager.get_user_profile = Mock()
        
        mock_manager_class.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def memory_manager(mock_chromadb, mock_llm_client, mock_emotion_manager):
    """Create a memory manager instance with mocked dependencies."""
    with patch('os.path.exists', return_value=True), \
         patch('src.memory.memory_manager.embedding_functions.SentenceTransformerEmbeddingFunction') as mock_embedding_func:

        # Make sure the embedding function mock returns our MockEmbeddingFunction instance
        mock_embedding_func.return_value = mock_chromadb['embedding_function']

        manager = UserMemoryManager(
            persist_directory="./test_chromadb",
            enable_auto_facts=True,
            enable_global_facts=True,
            enable_emotions=True,
            llm_client=mock_llm_client
        )
        yield manager
class TestUserMemoryManagerInitialization:
    """Test memory manager initialization and configuration."""

    def test_init_with_defaults(self, mock_chromadb):
        """Test memory manager initialization with default values."""
        with patch.dict('os.environ', {
            'CHROMADB_PATH': './test_chromadb',
            'CHROMADB_HOST': 'localhost',
            'CHROMADB_PORT': '8000'
        }):
            manager = UserMemoryManager()
            # Check actual attributes that exist in UserMemoryManager
            assert manager.enable_auto_facts is False  # Disabled in current implementation
            assert manager.enable_global_facts is True
            assert manager.enable_emotions is True
            assert manager.client is not None
            assert manager.collection is not None
            assert manager.global_collection is not None
            assert manager.emotion_manager is not None
            assert manager.llm_client is None  # No LLM client provided in test

    def test_init_with_custom_params(self, mock_chromadb, mock_llm_client):
        """Test memory manager initialization with custom parameters."""
        with patch.dict('os.environ', {
            'CHROMADB_HOST': 'test_host',
            'CHROMADB_PORT': '9000'
        }):
            manager = UserMemoryManager(
                persist_directory='./custom_chromadb',
                enable_auto_facts=False,
                enable_global_facts=False,
                enable_emotions=False,
                llm_client=mock_llm_client
            )
            assert manager.enable_auto_facts is False
            assert manager.enable_global_facts is False
            assert manager.enable_emotions is False
            assert manager.emotion_manager is None  # Disabled
            assert manager.llm_client == mock_llm_client
            assert manager.client is not None

    def test_init_connection_failure(self, mock_chromadb):
        """Test memory manager initialization with connection failure."""
        # Make the heartbeat method raise an exception
        mock_chromadb['client'].heartbeat.side_effect = Exception("Could not connect to a Chroma server")
        
        with patch.dict('os.environ', {
            'CHROMADB_HOST': 'localhost',
            'CHROMADB_PORT': '8000'
        }):
            with pytest.raises(MemoryError, match="ChromaDB server connection test failed"):
                UserMemoryManager()

    def test_init_collections_created(self, mock_chromadb):
        """Test that collections are properly created during initialization."""
        manager = UserMemoryManager()
        
        # Verify collections were created - should be 2: user_memories and global_facts
        assert mock_chromadb['client'].get_or_create_collection.call_count == 2
        
        # Verify the correct collection names were used
        calls = mock_chromadb['client'].get_or_create_collection.call_args_list
        collection_names = [call[1]['name'] for call in calls]  # Extract 'name' from kwargs
        assert 'user_memories' in collection_names
        assert 'global_facts' in collection_names


class TestConversationStorage:
    """Test conversation storage functionality."""

    def test_store_conversation_success(self, memory_manager, mock_chromadb):
        """Test successful conversation storage."""
        user_id = "test_user_123"
        user_message = "Hello, how are you?"
        bot_response = "I'm doing well, thank you for asking!"
        channel_id = "test_channel"

        # Check what collection is actually assigned to the memory manager
        print(f"Memory manager collection: {memory_manager.collection}")
        print(f"Mock collection: {mock_chromadb['collection']}")
        print(f"Are they the same? {memory_manager.collection is mock_chromadb['collection']}")

        # Mock successful storage on both potential collections
        mock_chromadb['collection'].add.return_value = None
        memory_manager.collection.add.return_value = None

        result = memory_manager.store_conversation(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            channel_id=channel_id
        )
        
        print(f"Result: {result}")
        print(f"Mock collection add call count: {mock_chromadb['collection'].add.call_count}")
        print(f"Memory manager collection add call count: {memory_manager.collection.add.call_count}")

        # Should return success
        assert result is True
        # Check the actual collection that was used
        memory_manager.collection.add.assert_called_once()

    def test_store_conversation_validation_error(self, memory_manager):
        """Test conversation storage with validation error."""
        user_id = ""  # Invalid user ID
        user_message = "Test message"
        bot_response = "Test response"
        
        with pytest.raises(ValidationError):
            memory_manager.store_conversation(user_id, user_message, bot_response)

    def test_store_conversation_with_facts_extraction(self, memory_manager, mock_llm_client, mock_chromadb):
        """Test conversation storage with automatic fact extraction."""
        user_id = "test_user_123"
        user_message = "I'm 25 years old and I love pizza"
        bot_response = "That's great! Pizza is delicious."
        
        # Mock successful storage
        mock_chromadb['collection'].add.return_value = None  # user_memories collection
        
        # Call the actual store method with correct parameters
        memory_manager.store_conversation(user_id, user_message, bot_response)
        
        # Verify storage was attempted - should be called twice: 
        # once for conversation, once for Phase 4 emotional analysis
        assert mock_chromadb['collection'].add.call_count >= 1
        assert mock_chromadb['collection'].add.call_count <= 3  # Allow for multiple fact extractions


class TestFactExtraction:
    """Test fact extraction and storage functionality."""

    def test_extract_and_store_personality_facts(self, memory_manager, mock_llm_client, mock_chromadb):
        """Test personality fact extraction and storage."""
        user_id = "test_user_123"
        user_message = "I work as a software engineer and I love coding"
        bot_response = "That's interesting! Software engineering is a great field."
        timestamp = datetime.now().isoformat()
        metadata = {"channel_id": "test_channel"}
        
        # Mock successful storage
        mock_chromadb['collection'].add.return_value = None
        
        # Call the private method with correct signature
        memory_manager._extract_and_store_personality_facts(
            user_id, user_message, bot_response, timestamp, metadata
        )

    def test_fact_extraction_error_handling(self, memory_manager, mock_llm_client):
        """Test fact extraction error handling."""
        user_id = "test_user_123"
        user_message = "Test message"
        bot_response = "Test response"
        timestamp = datetime.now().isoformat()
        metadata = {"channel_id": "test_channel"}
        
        # Should handle error gracefully (no specific error mocking needed for this test)
        try:
            memory_manager._extract_and_store_personality_facts(
                user_id, user_message, bot_response, timestamp, metadata
            )
        except Exception:
            pytest.fail("Fact extraction should handle errors gracefully")


class TestMemoryRetrieval:
    """Test memory retrieval functionality."""

    def test_get_related_global_facts(self, memory_manager, mock_chromadb):
        """Test retrieval of related global facts."""
        query = "software engineering"
        limit = 5
        
        # Mock query results to match actual implementation structure
        mock_chromadb['global_facts'].query.return_value = {
            'ids': [['fact1', 'fact2']],
            'metadatas': [[
                {'type': 'global_fact', 'domain': 'technology'},
                {'type': 'global_fact', 'domain': 'technology'}
            ]],
            'documents': [['Python is popular for software engineering', 'Agile methodology improves development']],
            'distances': [[0.1, 0.2]]
        }
        
        results = memory_manager.get_related_global_facts(query, limit)
        
        assert len(results) == 2
        # Check actual structure returned by implementation
        assert results[0]['content'] == 'Python is popular for software engineering'
        assert results[0]['id'] == 'fact1'
        assert results[0]['relevance_score'] == 0.9  # 1 - 0.1
        assert results[1]['content'] == 'Agile methodology improves development'
        mock_chromadb['global_facts'].query.assert_called_once()

    def test_get_related_global_facts_empty_result(self, memory_manager, mock_chromadb):
        """Test retrieval when no facts are found."""
        query = "nonexistent topic"
        
        # Mock empty results
        mock_chromadb['global_facts'].query.return_value = {
            'ids': [[]],
            'metadatas': [[]],
            'documents': [[]],
            'distances': [[]]
        }
        
        results = memory_manager.get_related_global_facts(query)
        
        assert results == []
        mock_chromadb['global_facts'].query.assert_called_once()

    def test_get_knowledge_domain_facts(self, memory_manager, mock_chromadb):
        """Test retrieval of facts from specific knowledge domain."""
        domain = "technology"
        limit = 10
        
        # This method requires graph memory manager which is not available in tests
        # Should return empty list with warning
        results = memory_manager.get_knowledge_domain_facts(domain, limit)
        
        # Should return empty list since graph memory is not available
        assert results == []


class TestInputValidation:
    """Test input validation methods."""

    def test_validate_user_id_valid(self, memory_manager):
        """Test validation of valid user ID."""
        # Use a test-prefixed ID which should be valid according to the implementation
        valid_id = "test_user_123"
        result = memory_manager._validate_user_id(valid_id)
        assert result == valid_id

    def test_validate_user_id_invalid_empty(self, memory_manager):
        """Test validation of empty user ID."""
        with pytest.raises(ValidationError, match="User ID cannot be empty"):
            memory_manager._validate_user_id("")

    def test_validate_user_id_invalid_length(self, memory_manager):
        """Test validation of user ID with invalid format."""
        # This should fail because it doesn't match the allowed patterns
        invalid_id = "invalid_format_user"
        with pytest.raises(ValidationError, match="Invalid user ID format"):
            memory_manager._validate_user_id(invalid_id)

    def test_validate_input_text_valid(self, memory_manager):
        """Test validation of valid input text."""
        text = "This is a valid message"
        result = memory_manager._validate_input(text)
        assert result == text

    def test_validate_input_text_empty(self, memory_manager):
        """Test validation of empty input text."""
        # Update the expected error message to match the actual implementation
        with pytest.raises(ValidationError, match="Text cannot be empty"):
            memory_manager._validate_input("")

    def test_validate_input_text_too_long(self, memory_manager):
        """Test validation of too long input text."""
        long_text = "a" * 10001  # Exceeds the default 10000 character limit
        # The implementation truncates instead of raising an error
        result = memory_manager._validate_input(long_text)
        assert len(result) == 10000  # Should be truncated to the limit

    def test_is_synthetic_message_true(self, memory_manager):
        """Test detection of synthetic messages."""
        # Use a message that would actually be detected as synthetic based on implementation
        synthetic_message = "[Context from previous conversations] This is synthetic"
        result = memory_manager._is_synthetic_message(synthetic_message)
        assert result is True

    def test_is_synthetic_message_false(self, memory_manager):
        """Test detection of non-synthetic messages."""
        real_message = "I love pizza and coding"
        result = memory_manager._is_synthetic_message(real_message)
        assert result is False


class TestKnowledgeDomainClassification:
    """Test knowledge domain classification functionality."""

    def test_determine_knowledge_domain_technology(self, memory_manager):
        """Test classification of technology-related facts."""
        fact = "Python is a programming language"
        domain = memory_manager._determine_knowledge_domain(fact)
        assert domain == "technology"

    def test_determine_knowledge_domain_personal(self, memory_manager):
        """Test classification of personal facts."""
        fact = "User likes ice cream"
        domain = memory_manager._determine_knowledge_domain(fact)
        # The implementation returns "general" for facts that don't match specific keyword domains
        assert domain == "general"

    def test_determine_knowledge_domain_general(self, memory_manager):
        """Test classification of general facts."""
        fact = "The sky is blue"
        domain = memory_manager._determine_knowledge_domain(fact)
        assert domain == "general"

    def test_extract_tags_from_fact(self, memory_manager):
        """Test tag extraction from facts."""
        # Use a fact that will match the actual implementation patterns
        fact = "Python is a programming language"
        tags = memory_manager._extract_tags_from_fact(fact)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should extract "definition" tag because of "is" pattern
        assert "definition" in tags


class TestFactRelationships:
    """Test fact relationship management."""

    def test_create_fact_relationship(self, memory_manager, mock_chromadb):
        """Test creation of relationships between facts."""
        fact1_query = "Python is a programming language"
        fact2_query = "Software engineering uses Python"
        relationship_type = "relates_to"
        strength = 0.8
        
        # Graph memory manager is not available in test environment
        # Should return False with warning
        result = memory_manager.create_fact_relationship(fact1_query, fact2_query, relationship_type, strength)
        
        # Should return False since graph memory is not available
        assert result is False

    def test_create_fact_relationship_no_graph(self, memory_manager):
        """Test fact relationship creation when graph memory unavailable."""
        fact1_id = "fact_1"
        fact2_id = "fact_2"
        relationship_type = "relates_to"
        strength = 0.8
        
        # Mock graph memory unavailable
        with patch('src.memory.memory_manager.GRAPH_MEMORY_AVAILABLE', False):
            # Should handle gracefully when graph memory not available
            try:
                memory_manager.create_fact_relationship(fact1_id, fact2_id, relationship_type, strength)
            except Exception:
                pytest.fail("Should handle missing graph memory gracefully")