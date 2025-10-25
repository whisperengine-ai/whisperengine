"""
Test script for mystical symbol detection.

Tests the MysticalSymbolDetector with various inputs to ensure
proper detection and filtering of mystical/esoteric content
and ritualistic math patterns.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.mystical_symbol_detector import get_mystical_symbol_detector


def test_mystical_symbols():
    """Test mystical symbol detection with various inputs."""
    detector = get_mystical_symbol_detector()
    
    test_cases = [
        # (text, should_detect, description)
        # Normal messages
        ("Hello, how are you today?", False, "Normal greeting"),
        ("What's the weather like?", False, "Normal question"),
        
        # Mystical symbols
        ("☯️🕉️✡️☪️☸️", True, "Multiple religious symbols"),
        ("⛤⛥⛦⛧🔯", True, "Occult symbols"),
        ("ᚠᚢᚦᚨᚱᚲ", True, "Runic characters"),
        ("Tell me about ♈♉♊♋♌♍", True, "Zodiac symbols"),
        ("🜁🜂🜃🜄🜅", True, "Alchemical symbols"),
        ("I'm feeling ☺️ today!", False, "Emoji with normal text"),
        ("⬟⬠⬡⬢⬣⯁⯂", True, "Mystical geometric shapes"),
        ("Just one ☯️ symbol here", False, "Single symbol with text"),
        ("☯️☸️✡️☪️☦️", True, "High density mystical (5 symbols)"),
        ("⁂⁜※⁕⁖⁘⁙⁚⁛⁝⁞", True, "Esoteric punctuation"),
        ("🌟✨💫", False, "Regular star emojis (below threshold)"),
        
        # Ritualistic math
        ("∀∃∄∅∆∇∈∉∊∋∌∍∎∏∐", True, "Excessive math symbols"),
        ("∫∫∫∑∑∑∏∏∏", True, "Repeating integral/sum symbols"),
        ("[[[[nested brackets]]]]", True, "Excessive nested brackets"),
        ("𝐇𝐞𝐥𝐥𝐨𝐰𝐨𝐫𝐥𝐝", True, "Unicode mathematical alphanumeric"),
        ("x⁰¹²³⁴⁵⁶⁷⁸⁹", True, "Excessive superscripts"),
        ("∴∵∷⊕⊖⊗⊘", True, "Mystical math arrangement"),
        ("Calculate 2+2", False, "Normal math expression"),
        
        # Edge cases
        ("", False, "Empty string"),
        ("   ", False, "Whitespace only"),
    ]
    
    print("=" * 80)
    print("MYSTICAL SYMBOL DETECTION TEST SUITE")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for text, expected_detect, description in test_cases:
        should_ignore, reason = detector.should_ignore_message(text)
        
        # Test passed if detection matches expectation
        test_passed = should_ignore == expected_detect
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        if test_passed:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"   Text: {repr(text[:50])}")
        print(f"   Expected: {'DETECT' if expected_detect else 'ALLOW'}")
        print(f"   Result: {'DETECTED' if should_ignore else 'ALLOWED'}")
        if reason:
            print(f"   Reason: {reason}")
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    return failed == 0


def test_threshold_detection():
    """Test threshold-based detection."""
    detector = get_mystical_symbol_detector()
    
    print("\n" + "=" * 80)
    print("THRESHOLD DETECTION TESTS")
    print("=" * 80)
    print()
    
    # Test with increasing symbol density
    base_text = "Hello this is a message"
    symbols = "☯️"
    
    print(f"Base text: '{base_text}'")
    print(f"Adding symbols: '{symbols}'")
    print()
    
    for num_symbols in range(1, 6):
        test_text = base_text + " " + (symbols * num_symbols)
        should_ignore, reason = detector.should_ignore_message(test_text)
        
        total_chars = len([c for c in test_text if not c.isspace()])
        symbol_count = num_symbols
        ratio = symbol_count / total_chars if total_chars > 0 else 0
        
        print(f"Symbols: {num_symbols} | Ratio: {ratio:.1%} | "
              f"Result: {'🚫 IGNORED' if should_ignore else '✅ ALLOWED'}")
        if reason:
            print(f"  Reason: {reason}")
    
    print()


def test_unicode_ranges():
    """Test specific unicode range detection."""
    detector = get_mystical_symbol_detector()
    
    print("\n" + "=" * 80)
    print("UNICODE RANGE TESTS")
    print("=" * 80)
    print()
    
    # Test characters from different mystical unicode ranges
    range_tests = [
        ("\u2600\u2601\u2602", "Miscellaneous Symbols range"),
        ("\u2700\u2701\u2702", "Dingbats range"),
        ("☯☸✡", "Known mystical symbols"),
        ("🔮🌙⭐", "Mystical-themed emojis"),
    ]
    
    for symbols, range_name in range_tests:
        # Create a message with high density
        test_text = symbols * 3
        should_ignore, reason = detector.should_ignore_message(test_text)
        
        print(f"Range: {range_name}")
        print(f"Symbols: {symbols}")
        print(f"Result: {'🚫 IGNORED' if should_ignore else '✅ ALLOWED'}")
        if reason:
            print(f"Reason: {reason}")
        print()


if __name__ == "__main__":
    print("\n🔮 Testing Mystical Symbol Detection\n")
    
    success = test_mystical_symbols()
    test_threshold_detection()
    test_unicode_ranges()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")
    
    sys.exit(0 if success else 1)
