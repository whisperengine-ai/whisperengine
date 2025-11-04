"""
Phase 1 Text Normalization Testing

Tests the DiscordTextNormalizer with different normalization modes
to validate expected behavior for each pipeline component.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import from src
from src.utils.text_normalizer import (  # pylint: disable=wrong-import-position,import-error
    DiscordTextNormalizer,
    TextNormalizationMode,
    normalize_for_entity_extraction,
    normalize_for_emotion_analysis,
    normalize_for_pattern_matching,
    normalize_for_llm_prompt
)


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{'='*80}")
    print(f"  {test_name}")
    print(f"{'='*80}")


def test_normalization_mode(mode: TextNormalizationMode, test_cases: list):
    """Test a specific normalization mode with multiple test cases"""
    print_test_header(f"Testing {mode.value.upper()} Mode")
    
    normalizer = DiscordTextNormalizer()
    
    for i, (input_text, expected_description) in enumerate(test_cases, 1):
        print(f"\n[Test {i}]")
        print(f"Input:    '{input_text}'")
        
        normalized = normalizer.normalize(input_text, mode)
        print(f"Output:   '{normalized}'")
        print(f"Expected: {expected_description}")
        result_icon = "✓ Passed" if normalized else "✗ Failed"
        print(result_icon)


def test_entity_extraction():
    """Test ENTITY_EXTRACTION mode (full cleaning for spaCy NER)"""
    test_cases = [
        (
            "I love @john's pizza from https://example.com 🍕",
            "Should replace mentions/URLs, remove emojis, preserve case"
        ),
        (
            "Check out <@672814231002939413> at www.google.com",
            "Should replace Discord mentions and URLs"
        ),
        (
            "I have a **green car** that I drive daily",
            "Should extract 'green car' from markdown formatting"
        ),
        (
            "My son Logan is 5 years old 👦",
            "Should preserve 'Logan' capitalization, remove emoji"
        ),
        (
            "I went to San Francisco yesterday",
            "Should preserve proper noun capitalization for NER"
        ),
    ]
    
    test_normalization_mode(TextNormalizationMode.ENTITY_EXTRACTION, test_cases)


def test_emotion_analysis():
    """Test EMOTION_ANALYSIS mode (keep emojis, replace mentions/URLs)"""
    test_cases = [
        (
            "I love this! 😊😍",
            "Should KEEP emojis (emotional signals)"
        ),
        (
            "Check @user at https://example.com - it's **amazing**!",
            "Should replace mentions/URLs but KEEP formatting emphasis"
        ),
        (
            "I'm so happy 🎉🎊 about this!",
            "Should preserve all emojis for emotion detection"
        ),
    ]
    
    test_normalization_mode(TextNormalizationMode.EMOTION_ANALYSIS, test_cases)


def test_pattern_matching():
    """Test PATTERN_MATCHING mode (lowercase + full cleaning)"""
    test_cases = [
        (
            "Do YOU remember WHAT I said?",
            "Should lowercase everything"
        ),
        (
            "Check @user at https://example.com",
            "Should replace mentions/URLs and lowercase"
        ),
        (
            "I have a **green car** 🚗",
            "Should extract content, remove emojis, lowercase"
        ),
    ]
    
    test_normalization_mode(TextNormalizationMode.PATTERN_MATCHING, test_cases)


def test_llm_prompt():
    """Test LLM_PROMPT mode (natural language preservation)"""
    test_cases = [
        (
            "I love @john's pizza from https://example.com 🍕",
            "Should use natural '@User' placeholder, keep URLs/emojis"
        ),
        (
            "Check out this **amazing** video! 😍",
            "Should preserve emojis and extract formatting content"
        ),
    ]
    
    test_normalization_mode(TextNormalizationMode.LLM_PROMPT, test_cases)


def test_convenience_functions():
    """Test convenience functions"""
    print_test_header("Testing Convenience Functions")
    
    test_text = "I love @john's pizza from https://example.com 🍕"
    
    print(f"\nOriginal: '{test_text}'")
    print(f"\nEntity Extraction: '{normalize_for_entity_extraction(test_text)}'")
    print(f"Emotion Analysis:  '{normalize_for_emotion_analysis(test_text)}'")
    print(f"Pattern Matching:  '{normalize_for_pattern_matching(test_text)}'")
    print(f"LLM Prompt:        '{normalize_for_llm_prompt(test_text)}'")


def test_replacement_tokens():
    """Test that replacement tokens are filterable"""
    print_test_header("Testing Replacement Token Filtering")
    
    normalizer = DiscordTextNormalizer()
    
    # Test get_replacement_tokens
    tokens = normalizer.get_replacement_tokens()
    print(f"\nReplacement tokens: {tokens}")
    
    # Test should_filter_token
    test_tokens = ['[URL]', '[MENTION]', 'pizza', '@User', 'example']
    print("\nToken filtering:")
    for token in test_tokens:
        should_filter = normalizer.should_filter_token(token)
        status = "FILTER" if should_filter else "KEEP"
        print(f"  {token}: {status}")


def test_discord_artifacts():
    """Test handling of various Discord artifacts"""
    print_test_header("Testing Discord Artifact Handling")
    
    normalizer = DiscordTextNormalizer()
    
    test_cases = [
        ("User mention: <@123456789>", "User ID mention"),
        ("User mention: <@!987654321>", "User nickname mention"),
        ("Channel: <#555666777>", "Channel mention"),
        ("Role: <@&111222333>", "Role mention"),
        ("Username: @johndoe", "Username mention"),
        ("URL: https://discord.com/channels/123/456", "Full URL"),
        ("Short URL: www.example.com", "WWW URL"),
        ("Code: `inline code here`", "Inline code"),
        ("Code block:\n```python\nprint('hello')\n```", "Code block"),
        ("Bold: **bold text**", "Bold formatting"),
        ("Underline: __underlined__", "Underline formatting"),
        ("Strike: ~~strikethrough~~", "Strikethrough formatting"),
    ]
    
    print("\nEntity Extraction Mode (full cleaning):")
    for text, description in test_cases:
        normalized = normalizer.normalize(text, TextNormalizationMode.ENTITY_EXTRACTION)
        print(f"\n  {description}")
        print(f"    Input:  '{text}'")
        print(f"    Output: '{normalized}'")


def main():
    """Run all Phase 1 text normalization tests"""
    print("\n" + "="*80)
    print("  PHASE 1: TEXT NORMALIZATION TESTING")
    print("  WhisperEngine - November 4, 2025")
    print("="*80)
    
    try:
        test_entity_extraction()
        test_emotion_analysis()
        test_pattern_matching()
        test_llm_prompt()
        test_convenience_functions()
        test_replacement_tokens()
        test_discord_artifacts()
        
        print("\n" + "="*80)
        print("  ✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except (ImportError, AttributeError, ValueError) as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
