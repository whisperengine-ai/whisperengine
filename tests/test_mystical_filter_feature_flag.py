"""
Test mystical symbol filter feature flag integration.

Verifies that the ENABLE_MYSTICAL_SYMBOL_FILTER environment variable
correctly controls whether messages are filtered.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_feature_flag_disabled():
    """Test that mystical filter is disabled by default."""
    from src.core.message_processor import MessageContext
    
    # Ensure flag is disabled
    os.environ['ENABLE_MYSTICAL_SYMBOL_FILTER'] = 'false'
    
    # Create a mock security validator that always passes
    class MockSecurityValidator:
        async def validate_input(self, message):
            return {
                "is_safe": True,
                "sanitized_content": message.content,
                "warnings": []
            }
    
    # Import after setting env var
    from src.core.message_processor import MessageProcessor
    
    # Create minimal processor
    processor = MessageProcessor(
        bot_core=None,
        memory_manager=None,
        llm_client=None,
        security_validator=MockSecurityValidator()
    )
    
    # Test with mystical symbols (should NOT be filtered when disabled)
    mystical_message = MessageContext(
        user_id="test_user",
        content="☯️🕉️✡️☪️☸️",
        platform="test"
    )
    
    result = await processor._validate_security(mystical_message)
    
    assert result["is_safe"] == True, "Message should pass when filter is disabled"
    assert "Mystical" not in str(result.get("warnings", [])), "No mystical warnings when disabled"
    
    print("✅ PASS: Feature flag disabled - mystical messages allowed")


async def test_feature_flag_enabled():
    """Test that mystical filter works when enabled."""
    from src.core.message_processor import MessageContext
    
    # Enable the flag
    os.environ['ENABLE_MYSTICAL_SYMBOL_FILTER'] = 'true'
    
    # Create a mock security validator that always passes
    class MockSecurityValidator:
        async def validate_input(self, message):
            return {
                "is_safe": True,
                "sanitized_content": message.content,
                "warnings": []
            }
    
    # Import after setting env var
    from src.core.message_processor import MessageProcessor
    
    # Create minimal processor
    processor = MessageProcessor(
        bot_core=None,
        memory_manager=None,
        llm_client=None,
        security_validator=MockSecurityValidator()
    )
    
    # Test with mystical symbols (should be filtered when enabled)
    mystical_message = MessageContext(
        user_id="test_user",
        content="☯️🕉️✡️☪️☸️",
        platform="test"
    )
    
    result = await processor._validate_security(mystical_message)
    
    assert result["is_safe"] == False, "Message should be blocked when filter is enabled"
    assert "Mystical" in str(result.get("warnings", [])), "Mystical warning expected when enabled"
    
    print("✅ PASS: Feature flag enabled - mystical messages blocked")


async def test_feature_flag_normal_message():
    """Test that normal messages pass regardless of flag setting."""
    from src.core.message_processor import MessageContext
    
    # Test both enabled and disabled
    for flag_value in ['true', 'false']:
        os.environ['ENABLE_MYSTICAL_SYMBOL_FILTER'] = flag_value
        
        # Create a mock security validator that always passes
        class MockSecurityValidator:
            async def validate_input(self, message):
                return {
                    "is_safe": True,
                    "sanitized_content": message.content,
                    "warnings": []
                }
        
        # Import after setting env var
        from src.core.message_processor import MessageProcessor
        
        # Create minimal processor
        processor = MessageProcessor(
            bot_core=None,
            memory_manager=None,
            llm_client=None,
            security_validator=MockSecurityValidator()
        )
        
        # Test with normal message
        normal_message = MessageContext(
            user_id="test_user",
            content="Hello, how are you?",
            platform="test"
        )
        
        result = await processor._validate_security(normal_message)
        
        assert result["is_safe"] == True, f"Normal message should pass (flag={flag_value})"
        
        print(f"✅ PASS: Normal message allowed with flag={flag_value}")


async def main():
    """Run all feature flag tests."""
    print("=" * 80)
    print("MYSTICAL FILTER FEATURE FLAG TESTS")
    print("=" * 80)
    print()
    
    try:
        await test_feature_flag_disabled()
        await test_feature_flag_enabled()
        await test_feature_flag_normal_message()
        
        print()
        print("=" * 80)
        print("✅ ALL FEATURE FLAG TESTS PASSED")
        print("=" * 80)
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        return 1
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
