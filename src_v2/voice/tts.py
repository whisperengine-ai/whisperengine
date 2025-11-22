import os
from typing import Optional, AsyncGenerator
from loguru import logger
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import Voice, VoiceSettings

from src_v2.config.settings import settings

class TTSManager:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY.get_secret_value() if settings.ELEVENLABS_API_KEY else None
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not set. TTS will be disabled.")
            self.client = None
        else:
            self.client = AsyncElevenLabs(api_key=self.api_key)
            logger.info("TTSManager initialized with ElevenLabs")

    async def generate_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Generates speech from text using ElevenLabs.
        Returns the audio bytes.
        """
        if not self.client:
            logger.warning("TTS requested but ElevenLabs client is not initialized.")
            return None

        target_voice_id = voice_id or settings.ELEVENLABS_VOICE_ID
        if not target_voice_id:
            logger.error("No voice_id provided for TTS.")
            return None

        try:
            logger.info(f"Generating speech for text: '{text[:30]}...' with voice {target_voice_id}")
            
            # Use text_to_speech.convert
            # Note: convert returns an AsyncIterator, so we don't await the call itself
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=target_voice_id,
                model_id=settings.ELEVENLABS_MODEL_ID
            )
            
            # Collect all chunks into a single bytes object
            audio_data = b""
            async for chunk in audio_stream:
                audio_data += chunk
                
            return audio_data

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            return None

# Global instance
tts_manager = TTSManager()
