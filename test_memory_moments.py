"""
Test suite for Memory-Triggered Personality Moments system

This test suite validates the functionality of creating meaningful memory moments
that connect past conversations in natural, relationship-building ways.

Test Categories:
1. Memory Connection Discovery - Finding meaningful connections between conversations
2. Memory Moment Generation - Creating appropriate moments from connections
3. Natural Callback Generation - Generating natural-sounding memory references
4. Relationship Appropriateness - Ensuring moments fit the relationship level
5. Timing and Cooldown - Managing when moments can be triggered
6. Integration Testing - Working with emotional context and personality systems
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import the system under test
from src.personality.memory_moments import (
    MemoryTriggeredMoments,
    MemoryConnection,
    MemoryMoment,
    ConversationContext,
    MemoryConnectionType,
    MemoryMomentType,
    MemoryMomentTiming,
    create_memory_triggered_moments
)

# Import dependencies for integration testing
try:
    from src.intelligence.emotional_context_engine import EmotionalState
    EMOTIONAL_CONTEXT_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_AVAILABLE = False

# Simple mock classes for testing
class EmotionalState:
    JOY = "joy"
    SADNESS = "sadness"
    TRUST = "trust"
    FEAR = "fear"

class EmotionalContext:
    def __init__(self, primary_emotion):
        self.primary_emotion = primary_emotion


class TestMemoryTriggeredMoments:
    """Test the core Memory-Triggered Moments functionality"""
    
    @pytest.fixture
    def memory_system(self):
        """Create a memory system instance for testing"""
        return MemoryTriggeredMoments(
            connection_retention_days=30,
            max_connections_per_user=100,
            moment_cooldown_hours=12
        )
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return "test_user_123"
    
    @pytest.fixture
    def sample_conversation_context(self, sample_user_id):
        """Sample conversation context for testing"""
        return ConversationContext(
            user_id=sample_user_id,
            context_id="test_context_1",
            current_message="I've been working on my programming skills lately",
            topic_keywords=["programming", "skills", "learning"],
            emotional_state=EmotionalState.JOY,
            conversation_phase="middle",
            recent_messages=["Hello!", "How are you?", "I've been working on my programming skills lately"],
            conversation_length=3,
            current_relationship_depth=0.6,
            current_trust_level=0.7,
            current_engagement_level=0.8,
            time_since_last_conversation=timedelta(days=1),
            conversation_frequency=0.5,
            recently_triggered_moments=[]
        )
    
    @pytest.mark.asyncio
    async def test_analyze_conversation_for_memories_basic(self, memory_system, sample_user_id):
        """Test basic conversation analysis for memory creation"""
        # First conversation
        connections1 = await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I love programming and building web applications",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Should have no connections initially
        assert len(connections1) == 0
        
        # Second conversation with similar theme
        connections2 = await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_2", 
            message="Today I finished a great programming project",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Should now find thematic connections
        assert len(connections2) > 0
        assert any(conn.connection_type == MemoryConnectionType.THEMATIC_SIMILARITY for conn in connections2)
        
        # Check that connection has proper keywords
        thematic_conn = next(conn for conn in connections2 if conn.connection_type == MemoryConnectionType.THEMATIC_SIMILARITY)
        assert "programming" in thematic_conn.pattern_keywords
    
    @pytest.mark.asyncio
    async def test_emotional_resonance_connections(self, memory_system, sample_user_id):
        """Test that emotional resonance connections are properly detected"""
        # First conversation with joy
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I'm so happy about my new job",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Second conversation with similar emotion
        connections = await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_2",
            message="I feel amazing after that workout",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Should find emotional resonance
        emotional_connections = [conn for conn in connections if conn.connection_type == MemoryConnectionType.EMOTIONAL_RESONANCE]
        assert len(emotional_connections) > 0
        
        # Check emotional significance
        assert emotional_connections[0].emotional_significance > 0.5
    
    @pytest.mark.asyncio
    async def test_memory_moment_generation(self, memory_system, sample_user_id, sample_conversation_context):
        """Test generation of memory moments from connections"""
        # Create some conversation history first
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I've been learning Python programming",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_2",
            message="Programming is becoming my favorite hobby",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Generate moments for current context about programming
        moments = await memory_system.generate_memory_moments(sample_user_id, sample_conversation_context)
        
        assert len(moments) > 0
        
        # Check moment properties
        moment = moments[0]
        assert moment.user_id == sample_user_id
        assert moment.callback_text != ""
        assert moment.context_setup != ""
        assert moment.expected_relationship_impact > 0
    
    @pytest.mark.asyncio
    async def test_moment_appropriateness_filtering(self, memory_system, sample_user_id):
        """Test that moments are filtered for appropriateness"""
        # Create a context with low relationship depth
        low_relationship_context = ConversationContext(
            user_id=sample_user_id,
            context_id="test_context",
            current_message="Programming is fun",
            topic_keywords=["programming"],
            emotional_state=EmotionalState.JOY,
            conversation_phase="opening",
            recent_messages=["Hello!"],
            conversation_length=1,
            current_relationship_depth=0.2,  # Very low
            current_trust_level=0.1,  # Very low
            current_engagement_level=0.3,
            time_since_last_conversation=None,
            conversation_frequency=0.1,
            recently_triggered_moments=[]
        )
        
        # Create conversation history
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I love advanced programming techniques",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Generate moments - should be filtered out due to low relationship
        moments = await memory_system.generate_memory_moments(sample_user_id, low_relationship_context)
        
        # Should have fewer or no moments due to relationship depth filtering
        assert len(moments) <= 1  # May have some basic moments but not deep ones
    
    @pytest.mark.asyncio
    async def test_memory_moment_triggering(self, memory_system, sample_user_id, sample_conversation_context):
        """Test triggering memory moments and cooldown functionality"""
        # Set up memory history
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I completed my first programming project",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_2",
            message="Programming gives me so much satisfaction",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Generate moments
        moments = await memory_system.generate_memory_moments(sample_user_id, sample_conversation_context)
        assert len(moments) > 0
        
        # Trigger the first moment
        moment = moments[0]
        callback_text = await memory_system.trigger_memory_moment(moment, sample_conversation_context)
        
        assert callback_text != ""
        assert moment.usage_count == 1
        assert moment.last_used is not None
        
        # Try to trigger again immediately - should be blocked by cooldown
        callback_text_2 = await memory_system.trigger_memory_moment(moment, sample_conversation_context)
        assert callback_text_2 == ""  # Empty due to cooldown
    
    def test_keyword_extraction(self, memory_system):
        """Test keyword extraction functionality"""
        text = "I love programming and building web applications with Python"
        keywords = memory_system._extract_keywords(text)
        
        assert "programming" in keywords
        assert "building" in keywords
        assert "applications" in keywords
        assert "python" in keywords
        
        # Should filter out stop words
        assert "and" not in keywords
        assert "with" not in keywords
    
    def test_theme_identification(self, memory_system):
        """Test theme identification in conversations"""
        # Work theme
        work_text = "I had a meeting with my boss about the project deadline"
        work_themes = memory_system._identify_themes(work_text)
        assert "work" in work_themes
        
        # Hobby theme
        hobby_text = "I love playing music and reading books in my free time"
        hobby_themes = memory_system._identify_themes(hobby_text)
        assert "hobbies" in hobby_themes
        
        # Achievement theme
        achievement_text = "I'm so proud of finishing this difficult goal"
        achievement_themes = memory_system._identify_themes(achievement_text)
        assert "achievements" in achievement_themes
    
    def test_moment_type_determination(self, memory_system, sample_conversation_context):
        """Test correct determination of memory moment types"""
        # Achievement connection
        achievement_connection = MemoryConnection(
            connection_id="test_conn_1",
            user_id="test_user",
            connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
            primary_memory={"message": "I completed my project", "keywords": ["achievement", "completed"]},
            related_memories=[],
            connection_strength=0.8,
            emotional_significance=0.7,
            thematic_relevance=0.9,
            temporal_proximity=0.8,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.6,
            pattern_frequency=1,
            pattern_keywords=["achievement", "completed", "project"],
            created_at=datetime.now()
        )
        
        moment_type = memory_system._determine_moment_type(achievement_connection, sample_conversation_context)
        assert moment_type == MemoryMomentType.ACHIEVEMENT_CALLBACK
        
        # Emotional resonance connection
        emotional_connection = MemoryConnection(
            connection_id="test_conn_2", 
            user_id="test_user",
            connection_type=MemoryConnectionType.EMOTIONAL_RESONANCE,
            primary_memory={"message": "I feel happy", "keywords": ["happy"]},
            related_memories=[],
            connection_strength=0.7,
            emotional_significance=0.9,
            thematic_relevance=0.5,
            temporal_proximity=0.8,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.6,
            pattern_frequency=1,
            pattern_keywords=["joy"],
            created_at=datetime.now()
        )
        
        moment_type = memory_system._determine_moment_type(emotional_connection, sample_conversation_context)
        assert moment_type == MemoryMomentType.CELEBRATION_ECHO  # Since conversation context has JOY
    
    def test_callback_text_generation(self, memory_system):
        """Test generation of natural callback text"""
        connection = MemoryConnection(
            connection_id="test_conn",
            user_id="test_user",
            connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
            primary_memory={"message": "I completed my coding bootcamp"},
            related_memories=[],
            connection_strength=0.8,
            emotional_significance=0.7,
            thematic_relevance=0.9,
            temporal_proximity=0.8,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.6,
            pattern_frequency=1,
            pattern_keywords=["programming", "learning"],
            created_at=datetime.now()
        )
        
        # Test achievement callback
        callback = memory_system._generate_callback_text(connection, MemoryMomentType.ACHIEVEMENT_CALLBACK)
        assert "remind" in callback.lower() or "wonderful" in callback.lower()
        assert len(callback) > 20  # Should be meaningful text
        
        # Test interest development callback
        callback = memory_system._generate_callback_text(connection, MemoryMomentType.INTEREST_DEVELOPMENT)
        assert "passionate" in callback.lower() or "topic" in callback.lower()
    
    @pytest.mark.asyncio
    async def test_memory_moment_prompt_generation(self, memory_system, sample_user_id, sample_conversation_context):
        """Test generation of prompts for AI companions"""
        # Create conversation history
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I've been studying programming for months",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Generate moments
        moments = await memory_system.generate_memory_moments(sample_user_id, sample_conversation_context)
        
        if moments:  # Only test if we have moments
            prompt = await memory_system.get_memory_moment_prompt(moments, sample_conversation_context)
            
            assert "MEMORY" in prompt or len(prompt) == 0  # Should have memory guidance or be empty
            if prompt:
                assert "INTEGRATION" in prompt  # Should have integration guidance
    
    @pytest.mark.asyncio
    async def test_user_memory_summary(self, memory_system, sample_user_id):
        """Test generation of user memory summaries"""
        # Create some conversation history
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_1",
            message="I love programming and solving problems",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        await memory_system.analyze_conversation_for_memories(
            user_id=sample_user_id,
            context_id="context_2",
            message="Programming projects make me feel accomplished",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        # Get summary
        summary = await memory_system.get_user_memory_summary(sample_user_id)
        
        assert "total_connections" in summary
        assert "total_moments" in summary
        assert "connection_types" in summary
        assert isinstance(summary["total_connections"], int)
    
    def test_connection_id_generation_uniqueness(self, memory_system):
        """Test that connection IDs are unique"""
        entry1 = {"timestamp": datetime.now(), "message": "test1"}
        entry2 = {"timestamp": datetime.now() + timedelta(seconds=1), "message": "test2"}
        
        id1 = memory_system._generate_connection_id("user1", entry1, entry2)
        id2 = memory_system._generate_connection_id("user1", entry2, entry1)  # Swapped order
        id3 = memory_system._generate_connection_id("user2", entry1, entry2)  # Different user
        
        # All should be different
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3
        assert len(id1) == 12  # Should be 12 character hash


class TestMemorySystemIntegration:
    """Test integration with other personality systems"""
    
    @pytest.mark.asyncio
    async def test_create_memory_system_factory(self):
        """Test the factory function for creating memory systems"""
        system = await create_memory_triggered_moments()
        
        assert isinstance(system, MemoryTriggeredMoments)
        assert system.retention_period.days == 365  # Default retention
        assert system.max_connections == 1000  # Default max connections
    
    @pytest.mark.asyncio
    async def test_memory_system_with_mocked_dependencies(self):
        """Test memory system with mocked emotional and personality systems"""
        # Mock dependencies
        mock_emotional_engine = Mock()
        mock_personality_profiler = Mock()
        mock_memory_manager = Mock()
        mock_fact_classifier = Mock()
        
        system = MemoryTriggeredMoments(
            emotional_context_engine=mock_emotional_engine,
            personality_profiler=mock_personality_profiler,
            memory_tier_manager=mock_memory_manager,
            personality_fact_classifier=mock_fact_classifier
        )
        
        # Should initialize without error
        assert system.emotional_context_engine == mock_emotional_engine
        assert system.personality_profiler == mock_personality_profiler
        assert system.memory_tier_manager == mock_memory_manager
        assert system.personality_fact_classifier == mock_fact_classifier
    
    def test_emotional_tone_mapping(self, memory_system):
        """Test appropriate emotional tone selection for different moment types"""
        # Achievement moments should be congratulatory
        tone = memory_system._determine_emotional_tone(MemoryMomentType.ACHIEVEMENT_CALLBACK)
        assert "congratulatory" in tone
        
        # Support moments should be encouraging
        tone = memory_system._determine_emotional_tone(MemoryMomentType.SUPPORT_FOLLOW_UP)
        assert "encouraging" in tone
        
        # Interest development should be enthusiastic
        tone = memory_system._determine_emotional_tone(MemoryMomentType.INTEREST_DEVELOPMENT)
        assert "enthusiastic" in tone


class TestMemorySystemPerformance:
    """Test performance and scalability aspects"""
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_functionality(self, memory_system):
        """Test that old memories are properly cleaned up"""
        user_id = "test_user"
        
        # Create old connection (beyond retention period)
        old_connection = MemoryConnection(
            connection_id="old_conn",
            user_id=user_id,
            connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
            primary_memory={"message": "old memory"},
            related_memories=[],
            connection_strength=0.5,
            emotional_significance=0.5,
            thematic_relevance=0.5,
            temporal_proximity=0.5,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.5,
            pattern_frequency=1,
            pattern_keywords=["old"],
            created_at=datetime.now() - timedelta(days=400)  # Very old
        )
        
        # Add to system
        memory_system.memory_connections[user_id].append(old_connection)
        
        # Trigger cleanup
        await memory_system._cleanup_old_connections(user_id)
        
        # Old connection should be removed
        assert len(memory_system.memory_connections[user_id]) == 0
    
    @pytest.mark.asyncio 
    async def test_connection_limit_enforcement(self, memory_system):
        """Test that connection limits are enforced"""
        memory_system.max_connections = 5  # Set low limit for testing
        user_id = "test_user"
        
        # Create more connections than the limit
        for i in range(10):
            connection = MemoryConnection(
                connection_id=f"conn_{i}",
                user_id=user_id,
                connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
                primary_memory={"message": f"memory {i}"},
                related_memories=[],
                connection_strength=0.5 + (i * 0.05),  # Varying strengths
                emotional_significance=0.5,
                thematic_relevance=0.5,
                temporal_proximity=0.5,
                relationship_depth_at_creation=0.5,
                trust_level_at_creation=0.5,
                pattern_frequency=1,
                pattern_keywords=[f"keyword_{i}"],
                created_at=datetime.now() - timedelta(minutes=i)  # Varying ages
            )
            memory_system.memory_connections[user_id].append(connection)
        
        # Trigger cleanup
        await memory_system._cleanup_old_connections(user_id)
        
        # Should be limited to max_connections
        assert len(memory_system.memory_connections[user_id]) <= memory_system.max_connections
        
        # Should keep the highest strength connections
        remaining_connections = memory_system.memory_connections[user_id]
        if remaining_connections:
            # Check that remaining connections have higher strengths
            min_strength = min(conn.connection_strength for conn in remaining_connections)
            assert min_strength >= 0.5  # Should keep stronger connections


class TestMemoryMomentDataStructures:
    """Test the data structures used in the memory system"""
    
    def test_memory_connection_creation(self):
        """Test MemoryConnection data structure"""
        connection = MemoryConnection(
            connection_id="test_id",
            user_id="user_123",
            connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
            primary_memory={"message": "test message"},
            related_memories=[{"message": "related message"}],
            connection_strength=0.8,
            emotional_significance=0.7,
            thematic_relevance=0.9,
            temporal_proximity=0.6,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.6,
            pattern_frequency=1,
            pattern_keywords=["test", "keywords"],
            created_at=datetime.now()
        )
        
        assert connection.connection_id == "test_id"
        assert connection.user_id == "user_123"
        assert connection.connection_type == MemoryConnectionType.THEMATIC_SIMILARITY
        assert connection.connection_strength == 0.8
        assert "test" in connection.pattern_keywords
    
    def test_memory_moment_creation(self):
        """Test MemoryMoment data structure"""
        connection = MemoryConnection(
            connection_id="test_conn",
            user_id="user_123",
            connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
            primary_memory={"message": "test"},
            related_memories=[],
            connection_strength=0.8,
            emotional_significance=0.7,
            thematic_relevance=0.9,
            temporal_proximity=0.6,
            relationship_depth_at_creation=0.5,
            trust_level_at_creation=0.6,
            pattern_frequency=1,
            pattern_keywords=["test"],
            created_at=datetime.now()
        )
        
        moment = MemoryMoment(
            moment_id="test_moment",
            user_id="user_123",
            moment_type=MemoryMomentType.ACHIEVEMENT_CALLBACK,
            primary_connection=connection,
            callback_text="Test callback text",
            context_setup="Test context",
            emotional_tone="warm",
            expected_relationship_impact=0.7,
            expected_emotional_response=EmotionalState.JOY
        )
        
        assert moment.moment_id == "test_moment"
        assert moment.user_id == "user_123"
        assert moment.moment_type == MemoryMomentType.ACHIEVEMENT_CALLBACK
        assert moment.callback_text == "Test callback text"
        assert moment.expected_emotional_response == EmotionalState.JOY
    
    def test_conversation_context_creation(self):
        """Test ConversationContext data structure"""
        context = ConversationContext(
            user_id="user_123",
            context_id="context_456",
            current_message="Hello world",
            topic_keywords=["hello", "world"],
            emotional_state=EmotionalState.JOY,
            conversation_phase="opening",
            recent_messages=["Hello", "How are you?"],
            conversation_length=2,
            current_relationship_depth=0.5,
            current_trust_level=0.6,
            current_engagement_level=0.7,
            time_since_last_conversation=timedelta(hours=24),
            conversation_frequency=0.5,
            recently_triggered_moments=[]
        )
        
        assert context.user_id == "user_123"
        assert context.context_id == "context_456"
        assert context.current_message == "Hello world"
        assert "hello" in context.topic_keywords
        assert context.emotional_state == EmotionalState.JOY
        assert context.conversation_length == 2


if __name__ == "__main__":
    # Run basic functionality test
    async def main():
        print("🧠 Testing Memory-Triggered Moments System...")
        
        # Create system
        system = await create_memory_triggered_moments()
        print("✅ Memory system created successfully")
        
        # Test basic functionality
        user_id = "test_user"
        
        # Add some conversations
        await system.analyze_conversation_for_memories(
            user_id=user_id,
            context_id="context_1",
            message="I love learning about artificial intelligence",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        await system.analyze_conversation_for_memories(
            user_id=user_id,
            context_id="context_2", 
            message="AI and machine learning fascinate me so much",
            emotional_context=EmotionalContext(EmotionalState.JOY)
        )
        
        print("✅ Conversation analysis completed")
        
        # Test moment generation
        context = ConversationContext(
            user_id=user_id,
            context_id="test_context",
            current_message="I'm working on a new AI project",
            topic_keywords=["ai", "project", "working"],
            emotional_state=EmotionalState.JOY,
            conversation_phase="middle",
            recent_messages=["Hello!", "I'm working on a new AI project"],
            conversation_length=2,
            current_relationship_depth=0.6,
            current_trust_level=0.7,
            current_engagement_level=0.8,
            time_since_last_conversation=timedelta(days=1),
            conversation_frequency=0.5,
            recently_triggered_moments=[]
        )
        
        moments = await system.generate_memory_moments(user_id, context)
        print(f"✅ Generated {len(moments)} memory moments")
        
        if moments:
            # Test prompt generation
            prompt = await system.get_memory_moment_prompt(moments, context)
            print(f"✅ Generated memory prompt: {len(prompt)} characters")
            
            # Test triggering
            callback = await system.trigger_memory_moment(moments[0], context)
            print(f"✅ Triggered memory moment: {callback[:50]}...")
        
        # Test summary
        summary = await system.get_user_memory_summary(user_id)
        print(f"✅ User memory summary: {summary['total_connections']} connections")
        
        print("🎉 Memory-Triggered Moments system test completed successfully!")
    
    # Run the test
    asyncio.run(main())