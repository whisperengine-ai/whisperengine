"""
Test script for Discord Status Footer functionality.

Validates:
1. Footer generation from ai_components metadata
2. Footer stripping before memory storage
3. Environment variable control
4. Format correctness and Discord compatibility
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_footer_generation():
    """Test footer generation with various ai_components scenarios."""
    from src.utils.discord_status_footer import generate_discord_status_footer
    
    print("🧪 TEST 1: Footer Generation")
    print("=" * 60)
    
    # Test scenario 1: Rich ai_components with all data
    rich_ai_components = {
        'character_learning_moments': {
            'learning_moments_detected': 3,
            'moments': [
                {'type': 'growth_insight', 'suggested_response': 'Character growth detected'},
                {'type': 'user_observation', 'suggested_response': 'User preference noted'},
                {'type': 'memory_surprise', 'suggested_response': 'Unexpected connection'}
            ]
        },
        'conversation_intelligence': {
            'relationship_level': 'friend'
        },
        'bot_emotion': {
            'emotion': 'joy',
            'roberta_confidence': 0.87,
            'intensity': 0.75
        },
        'emotion_data': {  # User emotion
            'primary_emotion': 'curiosity',
            'intensity': 0.82,
            'confidence': 0.91
        },
        'bot_emotional_state': {  # Emotional trajectory
            'trajectory_direction': 'improving',
            'current_emotion': 'joy'
        }
    }
    
    # Enable footer for test
    os.environ['DISCORD_STATUS_FOOTER'] = 'true'
    
    footer = generate_discord_status_footer(
        ai_components=rich_ai_components,
        processing_time_ms=1234,
        memory_count=8
    )
    
    print("\n📊 Rich AI Components Footer:")
    print(footer)
    print()
    
    # Validate footer structure
    assert '──────' in footer, "Footer should contain separator line"
    assert 'Learning' in footer, "Footer should mention learning moments"
    assert 'Memory' in footer, "Footer should mention memory count"
    assert 'Relationship' in footer, "Footer should mention relationship status"
    assert 'Bot Emotion' in footer, "Footer should mention bot emotion"
    assert 'User Emotion' in footer, "Footer should mention user emotion"
    assert 'Emotional Trajectory' in footer, "Footer should mention emotional trajectory"
    assert 'Processed' in footer, "Footer should mention processing time"
    assert '1234ms' in footer, "Footer should show processing time"
    
    print("✅ Rich AI components footer generated successfully")
    
    # Test scenario 2: Minimal ai_components
    minimal_ai_components = {
        'conversation_intelligence': {
            'relationship_level': 'acquaintance'
        }
    }
    
    footer = generate_discord_status_footer(
        ai_components=minimal_ai_components,
        processing_time_ms=567,
        memory_count=2
    )
    
    print("\n📊 Minimal AI Components Footer:")
    print(footer)
    print()
    
    assert 'Relationship' in footer, "Minimal footer should still show relationship"
    assert 'Memory' in footer, "Minimal footer should show memory count"
    
    print("✅ Minimal AI components footer generated successfully")
    
    # Test scenario 3: Footer disabled
    os.environ['DISCORD_STATUS_FOOTER'] = 'false'
    
    footer = generate_discord_status_footer(
        ai_components=rich_ai_components,
        processing_time_ms=1234,
        memory_count=8
    )
    
    assert footer == "", "Footer should be empty when disabled"
    print("✅ Footer disabled correctly via environment variable")
    
    # Re-enable for remaining tests
    os.environ['DISCORD_STATUS_FOOTER'] = 'true'


def test_footer_stripping():
    """Test that footer is correctly stripped from responses before storage."""
    from src.utils.discord_status_footer import strip_footer_from_response
    
    print("\n🧪 TEST 2: Footer Stripping")
    print("=" * 60)
    
    # Test scenario 1: Response WITH footer
    response_with_footer = """Hey! I'm doing wonderful, thank you for asking!

──────────────────────────────────────────────────
🎯 **Learning**: 🌱Growth • 🧠 **Memory**: 8 memories (established) • 😊 **Relationship**: Friend (Trust: 70, Affection: 65, Attunement: 75)
──────────────────────────────────────────────────"""
    
    clean_response = strip_footer_from_response(response_with_footer)
    
    print("\n📝 Original Response (with footer):")
    print(response_with_footer)
    print("\n✂️ Cleaned Response (footer stripped):")
    print(clean_response)
    print()
    
    assert '──────' not in clean_response, "Separator should be removed"
    assert 'Learning' not in clean_response, "Learning status should be removed"
    assert 'Memory' not in clean_response, "Memory status should be removed"
    assert 'Relationship' not in clean_response, "Relationship status should be removed"
    assert "Hey! I'm doing wonderful" in clean_response, "Original content should remain"
    
    print("✅ Footer stripped correctly from response")
    
    # Test scenario 2: Response WITHOUT footer
    response_without_footer = "Hey! I'm doing wonderful, thank you for asking!"
    
    clean_response = strip_footer_from_response(response_without_footer)
    
    assert clean_response == response_without_footer, "Response without footer should be unchanged"
    
    print("✅ Response without footer unchanged")
    
    # Test scenario 3: Empty/None responses
    assert strip_footer_from_response("") == "", "Empty string should remain empty"
    # Note: strip_footer_from_response expects string, not None
    
    print("✅ Edge cases handled correctly")


def test_footer_length_limits():
    """Test that footer respects Discord's message length limits."""
    from src.utils.discord_status_footer import generate_discord_status_footer
    
    print("\n🧪 TEST 3: Footer Length Limits")
    print("=" * 60)
    
    os.environ['DISCORD_STATUS_FOOTER'] = 'true'
    
    # Test with maximum ai_components
    max_ai_components = {
        'character_learning_moments': {
            'learning_moments_detected': 6,
            'moments': [
                {'type': 'growth_insight', 'suggested_response': 'Growth'},
                {'type': 'user_observation', 'suggested_response': 'Observation'},
                {'type': 'memory_surprise', 'suggested_response': 'Surprise'},
                {'type': 'knowledge_evolution', 'suggested_response': 'Knowledge'},
                {'type': 'emotional_growth', 'suggested_response': 'Emotional'},
                {'type': 'relationship_awareness', 'suggested_response': 'Relationship'}
            ]
        },
        'conversation_intelligence': {
            'relationship_level': 'close_friend'
        },
        'bot_emotion': {
            'emotion': 'excitement',
            'roberta_confidence': 0.95,
            'intensity': 0.88
        },
        'emotion_data': {
            'primary_emotion': 'joy',
            'intensity': 0.93,
            'confidence': 0.96
        },
        'bot_emotional_state': {
            'trajectory_direction': 'positive',
            'current_emotion': 'excitement'
        }
    }
    
    footer = generate_discord_status_footer(
        ai_components=max_ai_components,
        processing_time_ms=12345,
        memory_count=25
    )
    
    footer_length = len(footer)
    
    print(f"\n📏 Maximum Footer Length: {footer_length} characters")
    print(footer)
    print()
    
    # Discord limit is 2000 characters per message
    # Footer should be reasonable (< 500 chars typically)
    assert footer_length < 500, f"Footer too long: {footer_length} chars (should be < 500)"
    
    print(f"✅ Footer length reasonable: {footer_length} chars")
    
    # Test that footer + typical response fits in Discord limit
    typical_response = "This is a typical response from the bot. " * 20  # ~800 chars
    total_length = len(typical_response) + footer_length
    
    assert total_length < 2000, f"Response + footer exceeds Discord limit: {total_length} chars"
    
    print(f"✅ Response + footer fits in Discord limit: {total_length} chars")


def test_memory_storage_safeguard():
    """Test that footer is NEVER stored in vector memory (critical test)."""
    print("\n🧪 TEST 4: Memory Storage Safeguard (CRITICAL)")
    print("=" * 60)
    
    from src.utils.discord_status_footer import (
        generate_discord_status_footer,
        strip_footer_from_response
    )
    
    os.environ['DISCORD_STATUS_FOOTER'] = 'true'
    
    # Simulate complete flow
    ai_components = {
        'character_learning_moments': {
            'learning_moments_detected': 2,
            'moments': [
                {'type': 'growth_insight', 'suggested_response': 'Growth'},
                {'type': 'user_observation', 'suggested_response': 'Observation'}
            ]
        },
        'conversation_intelligence': {
            'relationship_level': 'friend'
        },
        'bot_emotion': {
            'emotion': 'joy',
            'roberta_confidence': 0.87
        },
        'emotion_data': {
            'primary_emotion': 'curiosity',
            'intensity': 0.75,
            'confidence': 0.88
        },
        'bot_emotional_state': {
            'trajectory_direction': 'stable',
            'current_emotion': 'joy'
        }
    }
    
    # Step 1: Generate response (simulated)
    bot_response = "I'm so glad you asked! Let me share my thoughts on that."
    
    # Step 2: Generate footer for Discord display
    footer = generate_discord_status_footer(
        ai_components=ai_components,
        processing_time_ms=1000,
        memory_count=5
    )
    
    # Step 3: Create display response (what goes to Discord)
    display_response = bot_response + footer
    
    print("\n📤 Display Response (sent to Discord):")
    print(display_response)
    print()
    
    # Step 4: Strip footer before memory storage (CRITICAL)
    storage_response = strip_footer_from_response(display_response)
    
    print("💾 Storage Response (saved to vector memory):")
    print(storage_response)
    print()
    
    # Validate footer NOT in storage response
    assert '──────' not in storage_response, "🚨 CRITICAL: Footer separator found in storage!"
    assert 'Learning' not in storage_response, "🚨 CRITICAL: Learning status found in storage!"
    assert 'Memory' not in storage_response, "🚨 CRITICAL: Memory status found in storage!"
    assert 'Relationship' not in storage_response, "🚨 CRITICAL: Relationship status found in storage!"
    assert 'Emotion' not in storage_response, "🚨 CRITICAL: Emotion status found in storage!"
    assert 'Processed' not in storage_response, "🚨 CRITICAL: Processing time found in storage!"
    
    # Validate original content IS in storage response
    assert bot_response in storage_response, "Original response should be in storage"
    
    print("✅ ✅ ✅ CRITICAL TEST PASSED: Footer NEVER stored in vector memory!")


def run_all_tests():
    """Run all footer tests."""
    print("\n" + "=" * 60)
    print("🧪 DISCORD STATUS FOOTER TEST SUITE")
    print("=" * 60)
    
    try:
        test_footer_generation()
        test_footer_stripping()
        test_footer_length_limits()
        test_memory_storage_safeguard()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🎉 Discord Status Footer implementation validated successfully!")
        print("\n📝 To enable in production:")
        print("   1. Add DISCORD_STATUS_FOOTER=true to .env or .env.{bot_name}")
        print("   2. Restart bot: ./multi-bot.sh restart-bot {bot_name}")
        print("   3. Test with a Discord message")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except (ImportError, RuntimeError, ValueError) as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
