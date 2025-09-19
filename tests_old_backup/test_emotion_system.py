#!/usr/bin/env python3
"""
Test the emotion and relationship management system

This script demonstrates the emotion detection, relationship progression,
and contextual response system for the Discord bot.
"""

import logging
import os
import sys

import pytest

from env_manager import load_environment

# Load environment variables using centralized manager
load_environment()

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emotion_manager import EmotionManager
from memory_manager import UserMemoryManager


def setup_test_logging():
    """Set up logging for the test"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


@pytest.mark.unit
def test_emotion_detection_mock(mock_llm_client, temp_profiles_file):
    """Test emotion detection with mock LLM client"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_emotion_detection_test(emotion_manager)


@pytest.mark.integration
def test_emotion_detection_real(real_llm_client, temp_profiles_file):
    """Test emotion detection with real LLM client (integration test)"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_emotion_detection_test(emotion_manager)


def _run_emotion_detection_test(emotion_manager):
    """Common test logic for both mock and real LLM tests"""

    test_messages = [
        ("Hi there!", "neutral greeting"),
        ("I'm so excited about this new project!", "excited state"),
        ("This is really frustrating, nothing works!", "frustrated state"),
        ("I love this! It's amazing!", "happy/positive state"),
        ("I'm feeling really sad today", "sad state"),
        ("Thank you so much for your help!", "grateful state"),
        ("How does this work? I'm curious about the process", "curious state"),
        ("I'm worried this won't work out", "worried state"),
        ("This is absolutely terrible and I hate it!", "angry state"),
        ("My name is Alice and I work at Google", "personal info sharing"),
        ("I trust you with this secret information", "trust building"),
        ("Can you help me? I really need someone to talk to", "seeking support"),
    ]

    user_id = "test_user_emotion"

    for _i, (message, _description) in enumerate(test_messages, 1):

        profile, emotion = emotion_manager.process_interaction(user_id, message)
        emotion_manager.get_emotion_context(user_id)


@pytest.mark.unit
def test_relationship_progression_mock(mock_llm_client, temp_profiles_file):
    """Test relationship progression with mock LLM client"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_relationship_progression_test(emotion_manager)


@pytest.mark.integration
def test_relationship_progression_real(real_llm_client, temp_profiles_file):
    """Test relationship progression with real LLM client"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_relationship_progression_test(emotion_manager)


def _run_relationship_progression_test(emotion_manager):
    """Common test logic for relationship progression"""  # Simulate a user's journey from stranger to close friend
    progression_messages = [
        # Stranger phase
        "Hello, I'm new here",
        "Can you help me with something?",
        "This is interesting",
        # Building acquaintance (multiple interactions)
        "Hi again, I'm back with another question",
        "I remember talking to you before",
        "My name is Bob, by the way",
        # Building friendship (personal info sharing)
        "I work as a software engineer at Microsoft",
        "I live in Seattle and I love hiking",
        "I'm 28 years old and I enjoy reading sci-fi books",
        "I really appreciate your help, you're very understanding",
        # Building close friendship (trust and deep sharing)
        "I trust you with this personal information",
        "Can I tell you something private?",
        "You've been really helpful, I feel comfortable talking to you",
        "I'm going through a difficult time and could use some advice",
        "You understand me better than most people",
        "Thanks for always being there to listen",
    ]

    user_id = "test_user_progression"

    for i, message in enumerate(progression_messages, 1):

        profile, emotion = emotion_manager.process_interaction(user_id, message)

        if i in [3, 6, 10, 16]:  # Show full context at key milestones
            emotion_manager.get_emotion_context(user_id)


@pytest.mark.unit
def test_escalation_handling_mock(mock_llm_client, temp_profiles_file):
    """Test emotional escalation and de-escalation with mock LLM client"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_escalation_handling_test(emotion_manager)


@pytest.mark.integration
def test_escalation_handling_real(real_llm_client, temp_profiles_file):
    """Test emotional escalation and de-escalation with real LLM client"""

    emotion_manager = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_escalation_handling_test(emotion_manager)


def _run_escalation_handling_test(emotion_manager):
    """Common test logic for escalation handling"""

    escalation_sequence = [
        "I'm having some trouble with this",
        "This is getting frustrating",
        "I'm really annoyed now, nothing is working!",
        "I'm so angry! This is completely broken!",
        "Thank you for being patient with me",
        "I feel much better now, your help was amazing!",
    ]

    user_id = "test_user_escalation"

    for _i, message in enumerate(escalation_sequence, 1):

        profile, emotion = emotion_manager.process_interaction(user_id, message)

        if profile.escalation_count >= 3:
            pass


@pytest.mark.unit
def test_memory_integration_mock(mock_llm_client):
    """Test integration with the memory manager using mock LLM client"""

    _run_memory_integration_test(mock_llm_client)


@pytest.mark.integration
def test_memory_integration_real(real_llm_client):
    """Test integration with the memory manager using real LLM client"""

    _run_memory_integration_test(real_llm_client)


def _run_memory_integration_test(llm_client):
    """Common test logic for memory integration"""
    try:
        # Initialize with emotion support
        memory_manager = UserMemoryManager(
            persist_directory="./test_emotion_chromadb", enable_emotions=True, llm_client=llm_client
        )

        user_id = "test_user_memory"

        test_conversations = [
            ("Hello! My name is Carol and I'm excited to try this bot!", "Hi Carol! Welcome!"),
            (
                "I'm working on a Python project and feeling a bit overwhelmed",
                "I understand. Programming can be challenging sometimes.",
            ),
            ("Thank you so much! You're really helpful", "I'm glad I could help you, Carol."),
            ("I'm frustrated with this bug I can't fix", "Let's work through it step by step."),
        ]

        for _i, (user_msg, bot_response) in enumerate(test_conversations, 1):

            # Store conversation (this will process emotions automatically)
            memory_manager.store_conversation(user_id, user_msg, bot_response)

            # Get emotion context
            memory_manager.get_emotion_context(user_id)

            # Get user profile
            profile = memory_manager.get_user_emotion_profile(user_id)
            if profile:
                pass

        # Test emotion-aware context retrieval
        memory_manager.get_emotion_aware_context(user_id, "help with programming", limit=3)

        # Get stats
        memory_manager.get_collection_stats()

    except Exception:
        import traceback

        traceback.print_exc()


def main():
    """Run all tests using pytest"""
    setup_test_logging()


if __name__ == "__main__":
    main()
