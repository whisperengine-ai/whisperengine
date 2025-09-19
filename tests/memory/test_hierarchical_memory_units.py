"""
Unit tests for individual hierarchical memory components

Tests each tier and component in isolation with mocked dependencies
"""

import pytest
from datetime import datetime, timedelta

from src.memory.core.storage_abstraction import ConversationContext
from src.memory.core.context_assembler import ContextSource, ContextPriority, AssembledContext
from src.memory.core.migration_manager import MigrationStats, ConversationData
from src.memory.processors.conversation_summarizer import ConversationSummarizer, SummaryType


@pytest.mark.unit
class TestConversationContext:
    """Unit tests for ConversationContext data structure"""
    
    def test_conversation_context_creation(self):
        """Test basic ConversationContext creation and attributes"""
        context = ConversationContext(
            recent_messages=[
                {"user_message": "Hello", "bot_response": "Hi!", "timestamp": datetime.now()}
            ],
            semantic_summaries=[
                {"summary": "Greeting exchange", "relevance": 0.8}
            ],
            related_topics=[
                {"topic": "greetings", "strength": 0.7}
            ],
            full_conversations=[
                {"conversation_id": "conv_1", "user_message": "How are you?", "bot_response": "Good!"}
            ],
            assembly_metadata={
                "source_count": 4,
                "assembly_time_ms": 45
            }
        )
        
        assert len(context.recent_messages) == 1
        assert len(context.semantic_summaries) == 1
        assert len(context.related_topics) == 1
        assert len(context.full_conversations) == 1
        assert context.assembly_metadata["source_count"] == 4
    
    def test_context_to_string_conversion(self):
        """Test conversion of context to string format"""
        context = ConversationContext(
            recent_messages=[
                {"user_message": "Hello there", "bot_response": "Hi! How are you?"}
            ],
            semantic_summaries=[
                {"summary": "User greeted bot, bot responded positively"}
            ],
            related_topics=[
                {"topic": "conversation starters"}
            ],
            full_conversations=[],
            assembly_metadata={}
        )
        
        context_string = context.to_context_string(max_length=500)
        
        # Should contain recent conversation
        assert "Hello there" in context_string
        assert "Hi! How are you?" in context_string
        
        # Should contain summary
        assert "User greeted bot" in context_string
        
        # Should contain topic
        assert "conversation starters" in context_string
        
        # Should respect length limit
        assert len(context_string) <= 500
    
    def test_context_string_length_limiting(self):
        """Test that context string respects length limits"""
        # Create context with lots of content
        long_messages = [
            {"user_message": "This is a very long message " * 20, "bot_response": "This is a very long response " * 20}
            for _ in range(10)
        ]
        
        context = ConversationContext(
            recent_messages=long_messages,
            semantic_summaries=[],
            related_topics=[],
            full_conversations=[],
            assembly_metadata={}
        )
        
        # Should truncate to stay within limit
        short_string = context.to_context_string(max_length=200)
        assert len(short_string) <= 200
        
        long_string = context.to_context_string(max_length=2000)
        assert len(long_string) <= 2000


@pytest.mark.unit
class TestContextSource:
    """Unit tests for ContextSource data structure"""
    
    def test_context_source_creation(self):
        """Test ContextSource creation with all fields"""
        timestamp = datetime.now()
        source = ContextSource(
            source_type="redis_cache",
            content="User asked about weather, bot provided forecast",
            metadata={"temperature": "72F", "location": "San Francisco"},
            priority=ContextPriority.HIGH,
            relevance_score=0.85,
            timestamp=timestamp,
            conversation_id="conv_123"
        )
        
        assert source.source_type == "redis_cache"
        assert source.content == "User asked about weather, bot provided forecast"
        assert source.metadata["temperature"] == "72F"
        assert source.priority == ContextPriority.HIGH
        assert source.relevance_score == 0.85
        assert source.timestamp == timestamp
        assert source.conversation_id == "conv_123"
    
    def test_weighted_score_calculation(self):
        """Test weighted score calculation with different priorities"""
        high_priority_source = ContextSource(
            source_type="test",
            content="test",
            metadata={},
            priority=ContextPriority.HIGH,
            relevance_score=0.8
        )
        
        low_priority_source = ContextSource(
            source_type="test",
            content="test",
            metadata={},
            priority=ContextPriority.LOW,
            relevance_score=0.8
        )
        
        high_score = high_priority_source.get_weighted_score()
        low_score = low_priority_source.get_weighted_score()
        
        # High priority should have higher weighted score
        assert high_score > low_score
        
        # Check actual calculations
        assert high_score == 0.8 * 0.8  # relevance * HIGH priority (0.8)
        assert low_score == 0.8 * 0.4   # relevance * LOW priority (0.4)


@pytest.mark.unit
class TestAssembledContext:
    """Unit tests for AssembledContext data structure"""
    
    def test_assembled_context_creation(self):
        """Test AssembledContext creation and basic properties"""
        sources = [
            ContextSource("redis", "recent msg", {}, ContextPriority.HIGH, 0.9),
            ContextSource("postgres", "archive msg", {}, ContextPriority.MEDIUM, 0.7)
        ]
        
        assembled = AssembledContext(
            context_string="Combined context from multiple sources",
            context_sources=sources,
            assembly_metadata={"total_sources": 2, "assembly_method": "priority_based"},
            total_length=len("Combined context from multiple sources"),
            assembly_time_ms=42.5
        )
        
        assert assembled.context_string == "Combined context from multiple sources"
        assert len(assembled.context_sources) == 2
        assert assembled.total_length == len("Combined context from multiple sources")
        assert assembled.assembly_time_ms == 42.5
        assert assembled.assembly_metadata["total_sources"] == 2
    
    def test_source_breakdown_calculation(self):
        """Test source breakdown calculation"""
        sources = [
            ContextSource("redis", "msg1", {}, ContextPriority.HIGH, 0.9),
            ContextSource("redis", "msg2", {}, ContextPriority.HIGH, 0.8),
            ContextSource("postgres", "msg3", {}, ContextPriority.MEDIUM, 0.7),
            ContextSource("chromadb", "summary1", {}, ContextPriority.LOW, 0.6)
        ]
        
        assembled = AssembledContext(
            context_string="test",
            context_sources=sources,
            assembly_metadata={},
            total_length=4,
            assembly_time_ms=10.0
        )
        
        breakdown = assembled.get_source_breakdown()
        
        assert breakdown["redis"] == 2
        assert breakdown["postgres"] == 1
        assert breakdown["chromadb"] == 1
        assert "neo4j" not in breakdown


@pytest.mark.unit
class TestMigrationStats:
    """Unit tests for MigrationStats data structure"""
    
    def test_migration_stats_creation(self):
        """Test MigrationStats creation and basic properties"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        
        stats = MigrationStats(
            total_conversations=100,
            migrated_successfully=95,
            failed_migrations=3,
            skipped_conversations=2,
            start_time=start_time,
            end_time=end_time
        )
        
        assert stats.total_conversations == 100
        assert stats.migrated_successfully == 95
        assert stats.failed_migrations == 3
        assert stats.skipped_conversations == 2
        assert stats.start_time == start_time
        assert stats.end_time == end_time
    
    def test_migration_stats_calculated_properties(self):
        """Test calculated properties of MigrationStats"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=60)  # 1 minute
        
        stats = MigrationStats(
            total_conversations=100,
            migrated_successfully=80,
            failed_migrations=20,
            skipped_conversations=0,
            start_time=start_time,
            end_time=end_time
        )
        
        # Test duration calculation
        assert abs(stats.duration_seconds - 60.0) < 0.1
        
        # Test success rate calculation
        assert stats.success_rate == 0.8  # 80/100
        
        # Test conversations per second
        assert abs(stats.conversations_per_second - (80/60)) < 0.1
    
    def test_migration_stats_edge_cases(self):
        """Test MigrationStats edge cases"""
        # No conversations
        empty_stats = MigrationStats()
        assert empty_stats.success_rate == 0.0
        assert empty_stats.conversations_per_second == 0.0
        assert empty_stats.duration_seconds == 0.0
        
        # No time set
        no_time_stats = MigrationStats(
            total_conversations=50,
            migrated_successfully=50
        )
        assert no_time_stats.duration_seconds == 0.0
        assert no_time_stats.conversations_per_second == 0.0


@pytest.mark.unit
class TestConversationData:
    """Unit tests for ConversationData migration structure"""
    
    def test_conversation_data_creation(self):
        """Test ConversationData creation"""
        timestamp = datetime.now()
        conv_data = ConversationData(
            conversation_id="conv_123",
            user_id="user_456",
            user_message="Hello there!",
            bot_response="Hi! How can I help you today?",
            timestamp=timestamp,
            metadata={"session_id": "session_789", "channel": "general"}
        )
        
        assert conv_data.conversation_id == "conv_123"
        assert conv_data.user_id == "user_456"
        assert conv_data.user_message == "Hello there!"
        assert conv_data.bot_response == "Hi! How can I help you today?"
        assert conv_data.timestamp == timestamp
        assert conv_data.metadata["session_id"] == "session_789"
    
    def test_conversation_data_from_chromadb_document(self):
        """Test ConversationData creation from ChromaDB document format"""
        metadata = {
            "user_id": "user_123",
            "user_message": "What's the weather like?",
            "bot_response": "It's sunny with 75°F",
            "timestamp": "2025-09-19T10:00:00Z",
            "channel": "weather",
            "extra_data": "some_value"
        }
        
        conv_data = ConversationData.from_chromadb_document(
            doc_id="doc_456",
            document="weather conversation document text",
            metadata=metadata
        )
        
        assert conv_data is not None
        assert conv_data.conversation_id == "doc_456"
        assert conv_data.user_id == "user_123"
        assert conv_data.user_message == "What's the weather like?"
        assert conv_data.bot_response == "It's sunny with 75°F"
        assert isinstance(conv_data.timestamp, datetime)
        assert conv_data.metadata["channel"] == "weather"
        assert conv_data.metadata["extra_data"] == "some_value"
        
        # Should not include the core fields in metadata
        assert "user_id" not in conv_data.metadata
        assert "user_message" not in conv_data.metadata
        assert "bot_response" not in conv_data.metadata
        assert "timestamp" not in conv_data.metadata
    
    def test_conversation_data_from_malformed_chromadb(self):
        """Test handling of malformed ChromaDB documents"""
        # Missing required fields
        incomplete_metadata = {
            "user_id": "user_123",
            # Missing user_message and bot_response
            "timestamp": "2025-09-19T10:00:00Z"
        }
        
        conv_data = ConversationData.from_chromadb_document(
            doc_id="doc_bad",
            document="incomplete document",
            metadata=incomplete_metadata
        )
        
        # Should return None for malformed data
        assert conv_data is None
    
    def test_conversation_data_timestamp_parsing(self):
        """Test timestamp parsing from various formats"""
        # Valid ISO format
        metadata_iso = {
            "user_id": "user_123",
            "user_message": "Test message",
            "bot_response": "Test response",
            "timestamp": "2025-09-19T15:30:45Z"
        }
        
        conv_data = ConversationData.from_chromadb_document("doc1", "text", metadata_iso)
        assert conv_data is not None
        assert isinstance(conv_data.timestamp, datetime)
        
        # Invalid timestamp format (should default to now)
        metadata_bad_time = {
            "user_id": "user_123",
            "user_message": "Test message",
            "bot_response": "Test response",
            "timestamp": "invalid_timestamp"
        }
        
        before_parse = datetime.now()
        conv_data = ConversationData.from_chromadb_document("doc2", "text", metadata_bad_time)
        after_parse = datetime.now()
        
        assert conv_data is not None
        assert before_parse <= conv_data.timestamp <= after_parse


@pytest.mark.unit 
class TestConversationSummarizerUnits:
    """Unit tests for ConversationSummarizer components"""
    
    def test_summarizer_initialization(self):
        """Test ConversationSummarizer initialization"""
        summarizer = ConversationSummarizer(max_summary_length=200)
        
        assert summarizer.max_summary_length == 200
        assert summarizer.llm_client is None
        assert hasattr(summarizer, 'question_patterns')
        assert hasattr(summarizer, 'topic_patterns')
        # Test cache exists (can't access directly due to protected member)
        assert hasattr(summarizer, '_summary_cache')
    
    async def test_summarization_basic_functionality(self):
        """Test basic summarization functionality without accessing protected members"""
        summarizer = ConversationSummarizer(max_summary_length=100)
        
        # Test basic summarization
        summaries = await summarizer.summarize_conversation(
            user_message="What is Python?",
            bot_response="Python is a programming language known for its simplicity.",
            summary_types=[SummaryType.SEMANTIC]
        )
        
        assert len(summaries) == 1
        summary = summaries[0]
        
        assert summary.summary_type == SummaryType.SEMANTIC
        assert len(summary.summary_text) <= 100
        assert summary.confidence_score > 0.0
        assert isinstance(summary.topics, list)
        assert isinstance(summary.intent, str)
        assert isinstance(summary.outcome, str)
    
    async def test_multiple_summary_types(self):
        """Test generation of multiple summary types"""
        summarizer = ConversationSummarizer()
        
        summaries = await summarizer.summarize_conversation(
            user_message="I need help with debugging my code",
            bot_response="I can help you debug. What error are you seeing?",
            summary_types=[SummaryType.SEMANTIC, SummaryType.TOPICAL, SummaryType.INTENT_BASED]
        )
        
        # Should generate requested types
        summary_types = {s.summary_type for s in summaries}
        assert SummaryType.SEMANTIC in summary_types
        assert SummaryType.TOPICAL in summary_types  
        assert SummaryType.INTENT_BASED in summary_types
        
        # Each should have different optimization
        for summary in summaries:
            assert summary.confidence_score > 0.0
            assert len(summary.summary_text) > 0
            assert isinstance(summary.topics, list)


if __name__ == "__main__":
    # Run unit tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        "-k", "unit"
    ])