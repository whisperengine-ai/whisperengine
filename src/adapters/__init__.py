"""
Platform adapters for WhisperEngine.

Provides clean adapter interfaces for converting between platform-agnostic
data structures and platform-specific formats (Discord, etc.).
"""

from src.adapters.platform_adapters import (
    DiscordMessageAdapter,
    DiscordAttachmentAdapter,
    create_discord_message_adapter,
    create_discord_attachment_adapters
)

__all__ = [
    'DiscordMessageAdapter',
    'DiscordAttachmentAdapter', 
    'create_discord_message_adapter',
    'create_discord_attachment_adapters'
]
