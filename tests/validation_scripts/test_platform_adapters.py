#!/usr/bin/env python3
"""
Quick validation script for platform adapters.
Tests that adapters properly convert between formats.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.platform_adapters import (
    DiscordMessageAdapter,
    DiscordAttachmentAdapter,
    create_discord_message_adapter,
    create_discord_attachment_adapters
)
from src.core.message_processor import MessageContext


def test_message_adapter():
    """Test message adapter conversion."""
    print("Testing DiscordMessageAdapter...")
    
    # Create a MessageContext
    message_context = MessageContext(
        user_id="test_user_123",
        content="Hello, this is a test message!",
        platform="api",
        metadata={"username": "TestUser"}
    )
    
    # Convert using adapter
    discord_message = create_discord_message_adapter(message_context)
    
    # Validate attributes
    assert hasattr(discord_message, 'content'), "Missing 'content' attribute"
    assert hasattr(discord_message, 'author'), "Missing 'author' attribute"
    assert hasattr(discord_message.author, 'id'), "Missing 'author.id' attribute"
    assert hasattr(discord_message.author, 'name'), "Missing 'author.name' attribute"
    
    assert discord_message.content == "Hello, this is a test message!"
    assert discord_message.author.id == "test_user_123"
    assert discord_message.author.name == "TestUser"
    
    print("✅ DiscordMessageAdapter: PASS")
    print(f"   - content: {discord_message.content}")
    print(f"   - author.id: {discord_message.author.id}")
    print(f"   - author.name: {discord_message.author.name}")


def test_attachment_adapter():
    """Test attachment adapter conversion."""
    print("\nTesting DiscordAttachmentAdapter...")
    
    # Create attachment dictionaries
    attachments = [
        {
            "url": "https://example.com/image.jpg",
            "filename": "image.jpg",
            "content_type": "image/jpeg"
        },
        {
            "url": "https://example.com/photo.png",
            "filename": "photo.png"
            # content_type will be inferred
        }
    ]
    
    # Convert using adapter
    discord_attachments = create_discord_attachment_adapters(attachments)
    
    # Validate
    assert len(discord_attachments) == 2, "Wrong number of attachments"
    
    for idx, attachment in enumerate(discord_attachments):
        assert hasattr(attachment, 'url'), f"Attachment {idx} missing 'url'"
        assert hasattr(attachment, 'filename'), f"Attachment {idx} missing 'filename'"
        assert hasattr(attachment, 'content_type'), f"Attachment {idx} missing 'content_type'"
    
    assert discord_attachments[0].url == "https://example.com/image.jpg"
    assert discord_attachments[0].content_type == "image/jpeg"
    assert discord_attachments[1].content_type == "image/png"  # Inferred
    
    print("✅ DiscordAttachmentAdapter: PASS")
    print(f"   - Attachment 1: {discord_attachments[0].filename} ({discord_attachments[0].content_type})")
    print(f"   - Attachment 2: {discord_attachments[1].filename} ({discord_attachments[1].content_type})")


def test_content_type_inference():
    """Test content type inference."""
    print("\nTesting content type inference...")
    
    test_cases = [
        ("image.jpg", "image/jpeg"),
        ("photo.jpeg", "image/jpeg"),
        ("diagram.png", "image/png"),
        ("animation.gif", "image/gif"),
        ("icon.svg", "image/svg+xml"),
        ("unknown.xyz", "application/octet-stream")
    ]
    
    for filename, expected_type in test_cases:
        attachment = DiscordAttachmentAdapter(
            url="https://example.com/" + filename,
            filename=filename
        )
        assert attachment.content_type == expected_type, \
            f"Wrong content type for {filename}: expected {expected_type}, got {attachment.content_type}"
        print(f"   ✓ {filename} → {expected_type}")
    
    print("✅ Content type inference: PASS")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Platform Adapter Validation")
    print("=" * 60)
    
    try:
        test_message_adapter()
        test_attachment_adapter()
        test_content_type_inference()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
