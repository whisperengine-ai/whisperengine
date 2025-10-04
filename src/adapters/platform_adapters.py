"""
Platform Adapters for WhisperEngine.

Provides clean adapter interfaces for converting between platform-agnostic
MessageContext and platform-specific formats (Discord message objects, etc.).

This eliminates the need for inline mock object creation and provides
a centralized, maintainable way to bridge platforms.
"""

from typing import List, Optional, Any, Dict
from dataclasses import dataclass


class DiscordAuthorAdapter:
    """
    Adapts user_id to Discord author format.
    
    Provides the .id and .name attributes expected by Discord-specific components.
    """
    
    def __init__(self, user_id: str, username: Optional[str] = None):
        self.id = user_id
        self.name = username or f"user_{user_id}"
        
    def __str__(self):
        return self.name


class DiscordMessageAdapter:
    """
    Adapts MessageContext to Discord message format.
    
    Provides the .content and .author attributes expected by components
    that were originally designed for Discord messages (security validator,
    personality profiler, Phase 4 intelligence, etc.).
    
    Usage:
        message_context = MessageContext(user_id="123", content="Hello")
        discord_message = create_discord_message_adapter(message_context)
        await security_validator.validate_input(discord_message)
    """
    
    def __init__(self, user_id: str, content: str, username: Optional[str] = None):
        self.content = content
        self.author = DiscordAuthorAdapter(user_id, username)
        
    @classmethod
    def from_message_context(cls, message_context):
        """
        Create adapter from MessageContext.
        
        Args:
            message_context: MessageContext instance from core.message_processor
            
        Returns:
            DiscordMessageAdapter instance
        """
        return cls(
            user_id=message_context.user_id,
            content=message_context.content,
            username=message_context.metadata.get('username') if message_context.metadata else None
        )


class DiscordAttachmentAdapter:
    """
    Adapts attachment dictionaries to Discord attachment format.
    
    Provides the .url, .filename, and .content_type attributes expected
    by image processing utilities.
    
    Usage:
        attachment_dict = {"url": "...", "filename": "image.jpg"}
        discord_attachment = DiscordAttachmentAdapter.from_dict(attachment_dict)
        await process_message_with_images(..., [discord_attachment], ...)
    """
    
    def __init__(self, url: str, filename: str, content_type: Optional[str] = None):
        self.url = url
        self.filename = filename
        self.content_type = content_type or self._infer_content_type(filename)
        
    @staticmethod
    def _infer_content_type(filename: str) -> str:
        """Infer content type from filename extension."""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    @classmethod
    def from_dict(cls, attachment_dict: Dict[str, Any]):
        """
        Create adapter from attachment dictionary.
        
        Args:
            attachment_dict: Dict with 'url', 'filename', optional 'content_type'
            
        Returns:
            DiscordAttachmentAdapter instance
        """
        return cls(
            url=attachment_dict.get('url', ''),
            filename=attachment_dict.get('filename', 'unknown'),
            content_type=attachment_dict.get('content_type')
        )


# Factory functions for convenience

def create_discord_message_adapter(message_context) -> DiscordMessageAdapter:
    """
    Factory function to create Discord message adapter from MessageContext.
    
    Args:
        message_context: MessageContext instance
        
    Returns:
        DiscordMessageAdapter ready to use with Discord-specific components
    """
    return DiscordMessageAdapter.from_message_context(message_context)


def create_discord_attachment_adapters(attachments: List[Dict[str, Any]]) -> List[DiscordAttachmentAdapter]:
    """
    Factory function to create Discord attachment adapters from attachment dicts.
    
    Args:
        attachments: List of attachment dictionaries
        
    Returns:
        List of DiscordAttachmentAdapter instances
    """
    return [DiscordAttachmentAdapter.from_dict(attachment) for attachment in attachments]
