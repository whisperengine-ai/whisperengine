#!/usr/bin/env python3
"""
Test script for LLM-based fact extraction
"""
import logging
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fact_extractor import GlobalFactExtractor
from lmstudio_client import LMStudioClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_llm_fact_extraction():
    """Test LLM-based fact extraction"""

    # Test messages with facts
    test_messages = [
        "Paris is the capital of France and has a population of over 2 million people.",
        "My name is John and I work at Google in San Francisco.",
        "The Earth orbits around the Sun once every 365 days.",
        "Apple acquired Beats for $3 billion in 2014.",
        "This bot can process images and analyze emotions using AI.",
        "I love pizza and I'm 25 years old. I live in New York.",
        "World War II ended in 1945.",
        "Just had a great day at the beach!",  # Should extract no facts
    ]


    # Initialize LLM client
    try:
        llm_client = LMStudioClient()

        # Check if LM Studio is running
        if not llm_client.check_connection():
            return False


        # Initialize fact extractor with LLM client
        fact_extractor = GlobalFactExtractor(llm_client=llm_client)

        # Test each message
        total_facts = 0
        for _i, message in enumerate(test_messages, 1):

            try:
                facts = fact_extractor.extract_global_facts_from_message(message)

                if facts:
                    for fact in facts:
                        if "reasoning" in fact:
                            pass
                    total_facts += len(facts)
                else:
                    pass

            except Exception as e:
                logger.error(f"Fact extraction error: {e}", exc_info=True)


        return True

    except Exception as e:
        logger.error(f"LLM client error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_llm_fact_extraction()
    sys.exit(0 if success else 1)
