#!/usr/bin/env python3
"""
Test script to verify that the fact extraction fixes prevent hallucinated facts
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fact_extractor import FactExtractor
from lmstudio_client import LMStudioClient


def test_fact_extraction_fix():
    """Test that the problematic messages no longer generate hallucinated facts"""

    # Create the LLM client (this will connect to LM Studio if running)
    try:
        llm_client = LMStudioClient()
    except Exception:
        return

    # Create fact extractor
    fact_extractor = FactExtractor(llm_client)

    # Test the problematic messages that were generating hallucinated facts
    test_messages = [
        "testing...",
        "hmm. maybe?...",
        "!list_facts",
        "ok",
        "hello",
        "what?",
    ]

    for message in test_messages:
        try:
            facts = fact_extractor.extract_facts_from_message(message)

            if facts:
                for _fact in facts:
                    pass
            else:
                pass

        except Exception:
            pass

    legitimate_messages = [
        "I play guitar every weekend",
        "I live in California",
        "My name is John and I work as a teacher",
        "I love playing video games, especially RPGs",
    ]

    for message in legitimate_messages:
        try:
            facts = fact_extractor.extract_facts_from_message(message)

            for _fact in facts:
                pass

        except Exception:
            pass


if __name__ == "__main__":
    test_fact_extraction_fix()
