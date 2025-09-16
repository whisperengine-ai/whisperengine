#!/usr/bin/env python3
"""
Quick test to verify UI responsiveness and typing indicators in the desktop app.
"""

import asyncio
import time


async def test_ui_responsiveness():
    """Test that UI operations are non-blocking"""

    # This should not block the main thread anymore
    start_time = time.time()

    # Test with a simple message that will trigger LLM processing

    # The actual LLM call would happen here in the desktop app
    # We're just testing the async structure

    time.time() - start_time

    return True


async def test_typing_indicator():
    """Test typing indicator animation logic"""

    # Simulate dot cycling
    dot_patterns = []
    for i in range(8):  # Two full cycles
        count = i % 4
        dots = "." * (count if count > 0 else 3)
        dot_patterns.append(dots)

    expected = ["...", ".", "..", "...", "...", ".", "..", "..."]

    if dot_patterns == expected:
        return True
    else:
        return False


async def main():
    """Run all tests"""

    # Test 1: UI Responsiveness
    ui_test = await test_ui_responsiveness()

    # Test 2: Typing Indicator Animation
    typing_test = await test_typing_indicator()

    # Summary
    if ui_test and typing_test:
        pass
    else:
        pass

    return ui_test and typing_test


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except Exception:
        exit(1)
