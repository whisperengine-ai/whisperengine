"""
Web Voice Handler for ElevenLabs Integration

Handles voice chat functionality for the web interface using existing
ElevenLabs infrastructure, adapted for web audio (not Discord voice channels).
"""

import logging
from typing import Optional, Dict, Any

from src.llm.elevenlabs_client import ElevenLabsClient
from src.utils.exceptions import LLMConnectionError, LLMRateLimitError, LLMTimeoutError


class WebVoiceHandler:
    """Handles voice operations for web interface using ElevenLabs"""

    def __init__(self, elevenlabs_client: ElevenLabsClient):
        """
        Initialize Web Voice Handler
        
        Args:
            elevenlabs_client: Configured ElevenLabs client
        """
        self.elevenlabs = elevenlabs_client
        self.logger = logging.getLogger(__name__)
        
        # Voice settings (can be customized per bot/user)
        self.voice_settings = {
            "voice_id": self.elevenlabs.default_voice_id,
            "stability": self.elevenlabs.voice_stability,
            "similarity_boost": self.elevenlabs.voice_similarity_boost,
            "style": self.elevenlabs.voice_style,
            "use_speaker_boost": self.elevenlabs.voice_use_speaker_boost
        }
        
        self.logger.info("Web Voice Handler initialized")

    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """
        Convert text to speech audio bytes
        
        Args:
            text: Text to convert to speech
            voice_id: Optional specific voice ID (uses default if not provided)
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            # Use provided voice ID or default
            target_voice_id = voice_id or self.voice_settings["voice_id"]
            
            self.logger.debug("Converting text to speech: '%s...' with voice %s", 
                            text[:50], target_voice_id)
            
            # Prepare voice settings for ElevenLabs client
            voice_settings_dict = {
                "stability": self.voice_settings["stability"],
                "similarity_boost": self.voice_settings["similarity_boost"],
                "style": self.voice_settings["style"],
                "use_speaker_boost": self.voice_settings["use_speaker_boost"]
            }
            
            # Use ElevenLabs client for TTS with proper parameters
            audio_data = await self.elevenlabs.text_to_speech(
                text=text,
                voice_id=target_voice_id,
                voice_settings=voice_settings_dict
            )
            
            self.logger.debug("Generated %d bytes of audio", len(audio_data))
            return audio_data
            
        except Exception as e:
            self.logger.error("Text-to-speech error: %s", e)
            raise

    async def speech_to_text(self, audio_data: bytes) -> str:
        """
        Convert speech audio to text
        
        Args:
            audio_data: Audio data as bytes
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.debug("Converting %d bytes of audio to text", len(audio_data))
            
            # Use ElevenLabs client for STT
            text = await self.elevenlabs.speech_to_text(audio_data)
            
            self.logger.debug("Transcribed text: '%s'", text)
            return text
            
        except Exception as e:
            self.logger.error("Speech-to-text error: %s", e)
            raise

    async def get_available_voices(self) -> list[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs
        
        Returns:
            List of voice dictionaries
        """
        try:
            voices = await self.elevenlabs.get_available_voices()
            self.logger.debug("Retrieved %d available voices", len(voices))
            return voices
        except (LLMConnectionError, LLMRateLimitError, LLMTimeoutError) as e:
            self.logger.error("Error getting voices: %s", e)
            return []

    def update_voice_settings(self, **settings):
        """
        Update voice settings
        
        Args:
            **settings: Voice setting key-value pairs
        """
        for key, value in settings.items():
            if key in self.voice_settings:
                self.voice_settings[key] = value
                self.logger.debug("Updated voice setting %s: %s", key, value)

    def get_voice_settings(self) -> Dict[str, Any]:
        """Get current voice settings"""
        return self.voice_settings.copy()


def create_web_voice_handler(elevenlabs_client: ElevenLabsClient) -> WebVoiceHandler:
    """
    Factory function to create WebVoiceHandler
    
    Args:
        elevenlabs_client: Configured ElevenLabs client
        
    Returns:
        WebVoiceHandler instance
    """
    return WebVoiceHandler(elevenlabs_client)