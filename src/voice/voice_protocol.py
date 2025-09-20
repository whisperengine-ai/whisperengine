"""
Voice Service Protocol and Factory for WhisperEngine

Provides a clean, extensible interface for voice functionality with factory pattern
for simplified dependency injection and configuration management.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


def create_voice_service(
    voice_service_type: Optional[str] = None,
    bot: Optional[Any] = None,
    llm_client: Optional[Any] = None,
    memory_manager: Optional[Any] = None
) -> Any:  # Use Any to avoid protocol complexity
    """
    Factory function to create voice service instances.
    
    Args:
        voice_service_type: Type of voice service ('discord_elevenlabs', 'disabled', 'mock')
        bot: Discord bot instance
        llm_client: LLM client instance  
        memory_manager: Memory manager instance
        
    Returns:
        Voice service implementation
    """
    if voice_service_type is None:
        voice_service_type = os.getenv("VOICE_SERVICE_TYPE", "discord_elevenlabs")
    
    voice_service_type = voice_service_type.lower()
    
    logger.info("Creating voice service: %s", voice_service_type)
    
    if voice_service_type == "disabled":
        return NoOpVoiceService()
    
    elif voice_service_type == "discord_elevenlabs":
        try:
            from src.llm.elevenlabs_client import ElevenLabsClient
            from src.voice.voice_manager import DiscordVoiceManager
            
            if bot is None:
                logger.warning("Discord bot instance required for discord_elevenlabs voice service")
                return NoOpVoiceService()
            
            # Initialize ElevenLabs client
            elevenlabs_client = ElevenLabsClient()
            logger.info("ElevenLabs client initialized")
            
            # Initialize voice manager
            voice_manager = DiscordVoiceManager(
                bot, elevenlabs_client, llm_client, memory_manager
            )
            logger.info("Discord voice manager initialized")
            
            return voice_manager
            
        except ImportError as e:
            logger.warning("Failed to import voice dependencies: %s", e)
            logger.info("Falling back to disabled voice service")
            return NoOpVoiceService()
        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Failed to initialize voice service: %s", e)
            logger.info("Falling back to disabled voice service")
            return NoOpVoiceService()
    
    elif voice_service_type == "mock":
        # For testing - could implement a mock voice service
        logger.info("Mock voice service not implemented, using disabled")
        return NoOpVoiceService()
    
    else:
        logger.warning("Unknown voice service type: %s, using disabled", voice_service_type)
        return NoOpVoiceService()


class NoOpVoiceService:
    """No-operation voice service for when voice functionality is disabled."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def join_voice_channel(self, channel: Any) -> bool:
        """No-op join voice channel."""
        _ = channel  # Unused argument
        self.logger.debug("Voice service disabled - join_voice_channel no-op")
        return False
    
    async def leave_voice_channel(self, guild_id: int) -> bool:
        """No-op leave voice channel."""
        _ = guild_id  # Unused argument
        self.logger.debug("Voice service disabled - leave_voice_channel no-op")
        return False
    
    async def speak_message(self, guild_id: int, text: str, priority: bool = False) -> None:
        """No-op speak message."""
        _ = guild_id, text, priority  # Unused arguments
        self.logger.debug("Voice service disabled - speak_message no-op")
        return None
    
    def get_current_channel(self, guild_id: int) -> Optional[Any]:
        """No-op get current channel."""
        _ = guild_id  # Unused argument
        self.logger.debug("Voice service disabled - get_current_channel no-op")
        return None
    
    @property
    def voice_listening_enabled(self) -> bool:
        """Voice listening always disabled for no-op service."""
        return False
    
    @property
    def voice_response_enabled(self) -> bool:
        """Voice responses always disabled for no-op service."""
        return False