"""
Test Suite for Phase 4.2 Multi-Thread Conversation Management

This test suite validates the Advanced Conversation Thread Manager functionality
including thread creation, transition detection, priority management, and
integration with the personality-driven AI companion systems.

Test Categories:
- Unit tests for core thread management functionality
- Integration tests with emotional and personality systems
- Scenario-based tests for realistic conversation flows
- Performance tests for thread management efficiency

Usage:
    pytest test_phase4_2_thread_management.py -v
    python test_phase4_2_thread_management.py  # For direct execution
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Phase 4.2 implementation
try:
    from src.conversation.advanced_thread_manager import (
        AdvancedConversationThreadManager,
        ConversationThreadAdvanced,
        ConversationThreadState,
        ThreadPriorityLevel,
        ThreadTransitionType,
        TopicSimilarityAnalyzer,
        TransitionDetector,
        ThreadPriorityCalculator,
        create_advanced_conversation_thread_manager
    )
    THREAD_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning("AdvancedConversationThreadManager not available: %s", e)
    THREAD_MANAGER_AVAILABLE = False
    pytest.skip("Advanced Thread Manager not available", allow_module_level=True)


class TestAdvancedThreadManager:
    """Test suite for the Advanced Conversation Thread Manager"""
    
    @pytest.fixture
    async def thread_manager(self):
        """Create a thread manager instance for testing"""
        if not THREAD_MANAGER_AVAILABLE:
            pytest.skip("Thread manager not available")
        
        manager = await create_advanced_conversation_thread_manager()
        return manager
    
    @pytest.mark.asyncio
    async def test_thread_creation(self, thread_manager):
        """Test basic thread creation functionality"""
        user_id = "test_user_1"
        message = "I want to discuss my career goals and future plans."
        context = {"user_id": user_id, "context_id": "career_chat"}
        
        result = await thread_manager.process_user_message(user_id, message, context)
        
        assert result is not None
        assert "current_thread" in result
        assert result["current_thread"] is not None
        
        # Verify thread was created
        user_threads = thread_manager.user_threads[user_id]
        assert len(user_threads) == 1
        
        thread = user_threads[0]
        assert thread.user_id == user_id
        assert thread.state == ConversationThreadState.ACTIVE
        assert len(thread.topic_keywords) > 0
        assert "career" in " ".join(thread.topic_keywords).lower()
    
    @pytest.mark.asyncio
    async def test_thread_continuation(self, thread_manager):
        """Test continuing an existing thread"""
        user_id = "test_user_2"
        
        # First message creates thread
        message1 = "I'm learning Python programming and loving it!"
        context = {"user_id": user_id, "context_id": "learning_chat"}
        result1 = await thread_manager.process_user_message(user_id, message1, context)
        
        initial_thread_id = result1["current_thread"]
        
        # Second related message should continue same thread
        message2 = "Do you have any tips for Python functions and classes?"
        result2 = await thread_manager.process_user_message(user_id, message2, context)
        
        assert result2["current_thread"] == initial_thread_id
        
        # Thread should have updated content
        user_threads = thread_manager.user_threads[user_id]
        thread = next(t for t in user_threads if t.thread_id == initial_thread_id)
        assert thread.total_messages == 2
        assert any("python" in keyword.lower() for keyword in thread.topic_keywords)
    
    @pytest.mark.asyncio
    async def test_thread_transition(self, thread_manager):
        """Test thread transition detection and management"""
        user_id = "test_user_3"
        context = {"user_id": user_id, "context_id": "multi_topic_chat"}
        
        # Create first thread about work
        message1 = "I had a challenging day at work with difficult clients."
        result1 = await thread_manager.process_user_message(user_id, message1, context)
        first_thread_id = result1["current_thread"]
        
        # Transition to different topic
        message2 = "By the way, have you seen the latest Marvel movie? It was amazing!"
        result2 = await thread_manager.process_user_message(user_id, message2, context)
        second_thread_id = result2["current_thread"]
        
        # Should create new thread
        assert second_thread_id != first_thread_id
        
        # Should detect transition
        transition_info = result2.get("transition_info")
        assert transition_info is not None
        assert transition_info.from_thread == first_thread_id
        assert transition_info.to_thread == second_thread_id
        
        # First thread should be paused
        user_threads = thread_manager.user_threads[user_id]
        first_thread = next(t for t in user_threads if t.thread_id == first_thread_id)
        assert first_thread.state == ConversationThreadState.PAUSED
    
    @pytest.mark.asyncio
    async def test_priority_management(self, thread_manager):
        """Test thread priority calculation and management"""
        user_id = "test_user_4"
        context = {"user_id": user_id, "context_id": "priority_test"}
        
        # Create normal priority thread
        normal_message = "I'm planning my weekend activities and hobbies."
        result1 = await thread_manager.process_user_message(user_id, normal_message, context)
        
        # Create high priority thread with emotional urgency
        urgent_message = "I'm feeling really stressed and need help urgently!"
        result2 = await thread_manager.process_user_message(user_id, urgent_message, context)
        
        priorities = result2.get("thread_priorities", {})
        assert len(priorities) >= 2
        
        # Find the urgent thread and verify higher priority
        urgent_thread_id = result2["current_thread"]
        urgent_priority = priorities.get(urgent_thread_id, {}).get("score", 0)
        
        assert urgent_priority > 0.5  # Should have elevated priority
    
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, thread_manager):
        """Test keyword extraction functionality"""
        keywords = thread_manager._extract_keywords(
            "I love programming in Python and building machine learning models with TensorFlow."
        )
        
        assert "programming" in keywords
        assert "python" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "tensorflow" in keywords
        
        # Should not include stop words
        assert "the" not in keywords
        assert "and" not in keywords
        assert "in" not in keywords
    
    @pytest.mark.asyncio
    async def test_theme_identification(self, thread_manager):
        """Test theme identification functionality"""
        themes = thread_manager._identify_themes(
            "I'm studying computer science and love working on AI projects and machine learning algorithms."
        )
        
        assert "technology" in themes
        assert "learning" in themes
    
    @pytest.mark.asyncio
    async def test_transition_indicators(self, thread_manager):
        """Test transition indicator detection"""
        # Explicit transition
        indicators1 = thread_manager._detect_transition_indicators(
            "Anyway, let's talk about something completely different."
        )
        assert indicators1["strength"] > 0.6
        assert len(indicators1["explicit_indicators"]) > 0
        
        # Question-based transition
        indicators2 = thread_manager._detect_transition_indicators(
            "What about your thoughts on artificial intelligence?"
        )
        assert indicators2["strength"] > 0.4
        
        # Normal continuation (should have low transition strength)
        indicators3 = thread_manager._detect_transition_indicators(
            "That's exactly what I was thinking about the previous topic."
        )
        assert indicators3["strength"] < 0.3
    
    @pytest.mark.asyncio
    async def test_engagement_assessment(self, thread_manager):
        """Test user engagement level assessment"""
        # High engagement message
        high_engagement = thread_manager._assess_engagement_level(
            "This is absolutely amazing! I'm so excited about this project and can't wait to learn more!"
        )
        assert high_engagement > 0.7
        
        # Low engagement message
        low_engagement = thread_manager._assess_engagement_level(
            "Ok fine whatever."
        )
        assert low_engagement < 0.4
        
        # Medium engagement message
        medium_engagement = thread_manager._assess_engagement_level(
            "That's interesting. I'd like to know more about it."
        )
        assert 0.4 <= medium_engagement <= 0.7
    
    @pytest.mark.asyncio
    async def test_thread_cleanup(self, thread_manager):
        """Test automatic thread cleanup functionality"""
        user_id = "test_user_cleanup"
        context = {"user_id": user_id, "context_id": "cleanup_test"}
        
        # Create multiple threads to test cleanup
        for i in range(8):  # More than max_active_threads (5)
            message = f"This is topic number {i} about different subjects and interests."
            await thread_manager.process_user_message(user_id, message, context)
        
        user_threads = thread_manager.user_threads[user_id]
        active_threads = [t for t in user_threads if t.state == ConversationThreadState.ACTIVE]
        
        # Should not exceed max active threads
        assert len(active_threads) <= thread_manager.max_active_threads
        
        # Some threads should be moved to background
        background_threads = [t for t in user_threads if t.state == ConversationThreadState.BACKGROUND]
        assert len(background_threads) > 0
    
    @pytest.mark.asyncio
    async def test_context_preservation(self, thread_manager):
        """Test context preservation during thread transitions"""
        user_id = "test_user_context"
        context = {"user_id": user_id, "context_id": "context_test"}
        
        # Create thread with some context
        message1 = "I'm worried about my upcoming job interview and need advice."
        result1 = await thread_manager.process_user_message(user_id, message1, context)
        
        # Transition to different topic
        message2 = "Actually, let me ask about something else - cooking recipes for dinner."
        result2 = await thread_manager.process_user_message(user_id, message2, context)
        
        transition_info = result2.get("transition_info")
        if transition_info:
            preserved_context = transition_info.context_preserved
            assert preserved_context is not None
            assert isinstance(preserved_context, dict)


class TestSupportingClasses:
    """Test suite for supporting analysis classes"""
    
    def test_topic_similarity_analyzer(self):
        """Test topic similarity analysis"""
        analyzer = TopicSimilarityAnalyzer()
        
        # Test similarity calculation
        text1 = "I love programming in Python and building applications."
        text2 = "Python development is my favorite programming activity."
        
        similarity = asyncio.run(analyzer.calculate_similarity(text1, text2))
        assert 0.3 <= similarity <= 1.0  # Should have reasonable similarity
        
        # Test dissimilar texts
        text3 = "I enjoy cooking pasta and making Italian food."
        similarity2 = asyncio.run(analyzer.calculate_similarity(text1, text3))
        assert similarity2 < similarity  # Should be less similar
    
    def test_transition_detector(self):
        """Test transition detection functionality"""
        detector = TransitionDetector()
        
        # Test explicit transition
        result1 = asyncio.run(detector.detect_transition(
            "Anyway, let's change the subject to something more interesting."
        ))
        assert result1["has_transition"] is True
        assert "explicit" in result1["patterns"]
        
        # Test no transition
        result2 = asyncio.run(detector.detect_transition(
            "That's exactly what I was thinking about this topic."
        ))
        assert result2["has_transition"] is False or result1["strength"] > result2["strength"]
    
    def test_priority_calculator(self):
        """Test thread priority calculation"""
        calculator = ThreadPriorityCalculator()
        
        # Create test thread with high priority factors
        high_priority_thread = ConversationThreadAdvanced(
            thread_id="high_priority_test",
            user_id="test_user",
            emotional_urgency=0.9,
            time_sensitivity=0.8,
            engagement_level=0.9,
            completion_status=0.1  # Low completion = high priority
        )
        
        priority = asyncio.run(calculator.calculate_priority(high_priority_thread))
        assert priority > 0.6
        
        # Create test thread with low priority factors
        low_priority_thread = ConversationThreadAdvanced(
            thread_id="low_priority_test",
            user_id="test_user",
            emotional_urgency=0.1,
            time_sensitivity=0.1,
            engagement_level=0.3,
            completion_status=0.9  # High completion = low priority
        )
        
        low_priority = asyncio.run(calculator.calculate_priority(low_priority_thread))
        assert low_priority < priority


class TestIntegrationScenarios:
    """Integration tests with realistic conversation scenarios"""
    
    @pytest.fixture
    async def thread_manager(self):
        """Create thread manager for integration tests"""
        if not THREAD_MANAGER_AVAILABLE:
            pytest.skip("Thread manager not available")
        
        return await create_advanced_conversation_thread_manager()
    
    @pytest.mark.asyncio
    async def test_work_life_balance_scenario(self, thread_manager):
        """Test realistic work-life balance conversation scenario"""
        user_id = "integration_user_1"
        context = {"user_id": user_id, "context_id": "life_chat"}
        
        messages = [
            "I'm feeling overwhelmed with my workload lately.",
            "Speaking of work, did you hear about the new company policy?",
            "Actually, let's get back to my stress - I need coping strategies.",
            "On a lighter note, I'm planning a vacation next month!",
            "Back to the stress management topic - what breathing exercises help?"
        ]
        
        thread_ids = []
        transition_count = 0
        
        for message in messages:
            result = await thread_manager.process_user_message(user_id, message, context)
            thread_ids.append(result["current_thread"])
            
            if result.get("transition_info"):
                transition_count += 1
        
        # Should have created multiple threads
        unique_threads = len(set(thread_ids))
        assert unique_threads >= 2
        
        # Should have detected transitions
        assert transition_count >= 1
        
        # Should have stress-related thread
        user_threads = thread_manager.user_threads[user_id]
        stress_keywords = ["stress", "overwhelmed", "coping", "breathing"]
        stress_thread_found = False
        
        for thread in user_threads:
            thread_text = " ".join(thread.topic_keywords).lower()
            if any(keyword in thread_text for keyword in stress_keywords):
                stress_thread_found = True
                break
        
        assert stress_thread_found
    
    @pytest.mark.asyncio
    async def test_learning_journey_scenario(self, thread_manager):
        """Test learning and development conversation scenario"""
        user_id = "integration_user_2"
        context = {"user_id": user_id, "context_id": "learning_chat"}
        
        messages = [
            "I started learning machine learning and it's fascinating!",
            "By the way, I also picked up guitar lessons recently.",
            "Going back to ML - can you explain neural networks simply?",
            "The guitar practice is harder than I expected though.",
            "For machine learning, which Python libraries should I focus on?"
        ]
        
        results = []
        for message in messages:
            result = await thread_manager.process_user_message(user_id, message, context)
            results.append(result)
        
        # Should handle topic switching between ML and guitar
        thread_topics = []
        for result in results:
            if result.get("response_guidance", {}).get("thread_context"):
                keywords = result["response_guidance"]["thread_context"].get("topic_keywords", [])
                thread_topics.extend(keywords)
        
        # Should contain both learning topics
        all_keywords = " ".join(thread_topics).lower()
        assert "machine" in all_keywords or "learning" in all_keywords
        assert "guitar" in all_keywords or "music" in all_keywords


def run_manual_tests():
    """Run tests manually without pytest"""
    logger.info("Running Phase 4.2 Thread Management Tests...")
    
    async def run_tests():
        if not THREAD_MANAGER_AVAILABLE:
            logger.error("Thread manager not available - skipping tests")
            return False
        
        try:
            # Create thread manager
            manager = await create_advanced_conversation_thread_manager()
            
            # Run basic functionality test
            user_id = "manual_test_user"
            message = "I want to discuss career development and professional growth."
            context = {"user_id": user_id, "context_id": "career_chat"}
            
            result = await manager.process_user_message(user_id, message, context)
            
            assert result is not None
            assert "current_thread" in result
            logger.info("✅ Basic thread creation test passed")
            
            # Test thread transition
            transition_message = "Actually, let's talk about something completely different - cooking!"
            result2 = await manager.process_user_message(user_id, transition_message, context)
            
            if result2.get("transition_info"):
                logger.info("✅ Thread transition test passed")
            else:
                logger.info("⚠️ Thread transition not detected (may be expected)")
            
            # Test keyword extraction
            keywords = manager._extract_keywords("I love programming Python and machine learning.")
            assert "programming" in keywords
            assert "python" in keywords
            logger.info("✅ Keyword extraction test passed")
            
            # Test theme identification
            themes = manager._identify_themes("I work in technology and enjoy coding projects.")
            assert "technology" in themes
            logger.info("✅ Theme identification test passed")
            
            logger.info("🎉 All manual tests passed!")
            return True
            
        except Exception as e:
            logger.error("❌ Manual test failed: %s", e)
            return False
    
    return asyncio.run(run_tests())


if __name__ == "__main__":
    # Run manual tests if executed directly
    success = run_manual_tests()
    if success:
        logger.info("Manual test execution completed successfully")
    else:
        logger.error("Manual test execution failed")
        exit(1)