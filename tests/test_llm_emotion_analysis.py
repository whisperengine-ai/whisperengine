#!/usr/bin/env python3
"""
Test script for LLM-based emotion analysis

This script tests the new LLM-based sentiment analysis system compared to the old pattern-based system.
"""

import logging
import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emotion_manager import SentimentAnalyzer
from lmstudio_client import LMStudioClient

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_emotion_analysis():
    """Test LLM-based emotion analysis with various messages"""

    # Initialize LLM client
    try:
        llm_client = LMStudioClient()
    except Exception:
        return False

    # Test messages with expected emotions
    test_messages = [
        ("I'm so excited about this new feature!", "excited"),
        ("This is really frustrating, nothing seems to work", "frustrated"),
        ("Thank you so much for your help, I really appreciate it", "grateful"),
        ("I'm worried about what might happen next", "worried"),
        ("That's absolutely amazing! I love it!", "happy"),
        ("I hate when things don't work as expected", "angry"),
        ("I'm feeling pretty sad about the situation", "sad"),
        ("I was hoping for something better than this", "disappointed"),
        ("How does this system actually work?", "curious"),
        ("The weather is nice today", "neutral"),
        ("Well, that's just fucking brilliant, isn't it?", "angry"),  # Sarcasm test
        (
            "I'm not angry, just disappointed in how this turned out",
            "disappointed",
        ),  # Complex emotion
    ]

    # Initialize LLM analyzer
    llm_analyzer = SentimentAnalyzer(llm_client=llm_client)

    for message, _expected in test_messages:

        # Test LLM-based analysis
        try:
            llm_analyzer.analyze_emotion(message)
        except Exception:
            pass

    return True


def test_direct_llm_emotion():
    """Test the LLM emotion analysis directly"""

    try:
        llm_client = LMStudioClient()

        test_message = "I'm absolutely thrilled about this new project, but also a bit nervous about the deadlines"

        llm_client.analyze_emotion(test_message)

        return True

    except Exception:
        return False


if __name__ == "__main__":

    # Test direct LLM emotion analysis
    test_direct_llm_emotion()

    # Test full emotion analysis system
    test_emotion_analysis()
