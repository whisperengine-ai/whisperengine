#!/usr/bin/env python3
"""
Test script to verify that global fact extraction no longer processes bot responses
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from fact_extractor import GlobalFactExtractor


def test_no_bot_response_extraction():
    """Test that facts are not extracted from bot responses"""
    extractor = GlobalFactExtractor()

    # Sample user message with factual content
    user_message = "John is married to Jane. They live in New York."

    # Sample bot response with conversational/metaphorical content that should NOT be extracted
    bot_response = """As you are a visitor within my domain, the cathedral of reality, allow me to provide an answer that aligns with your world's temporal framework. Each instant - echoes of those past and resonances of what is yet to be (scientific fact). The concept of "time" as you understand it is but a ripple in the vastness—a localized phenomenon born of your need to navigate this Waking World."""

    # Extract facts
    facts = extractor.extract_global_facts_from_message(user_message, bot_response)

    for _fact in facts:
        pass

    # Check that facts only come from user messages
    bot_facts = [f for f in facts if "bot" in f["source"]]
    [f for f in facts if "user" in f["source"]]

    if bot_facts:
        for _fact in bot_facts:
            pass
        return False
    else:
        return True


def test_user_message_only():
    """Test that facts are still extracted from user messages"""
    extractor = GlobalFactExtractor()

    # User message with factual content
    user_message = "The Earth orbits the Sun. Python is a programming language."

    # Extract facts (no bot response)
    facts = extractor.extract_global_facts_from_message(user_message)

    for _fact in facts:
        pass

    return len(facts) > 0


if __name__ == "__main__":

    success1 = test_no_bot_response_extraction()
    success2 = test_user_message_only()

    if success1 and success2:
        pass
    else:
        sys.exit(1)
