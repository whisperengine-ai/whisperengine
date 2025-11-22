from typing import AsyncGenerator, Optional
from loguru import logger
from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from src_v2.config.settings import settings

class VoiceService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY.get_secret_value() if settings.ELEVENLABS_API_KEY else None
        self.client = AsyncElevenLabs(api_key=self.api_key) if self.api_key else None
        
    async def generate_audio_stream(self, text: str, voice_id: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """
        Generates audio from text using ElevenLabs Official SDK (Streaming).
        """
        if not self.client:
            logger.warning("ElevenLabs client not initialized. Voice generation disabled.")
            return

        target_voice_id = voice_id or settings.ELEVENLABS_VOICE_ID
        if not target_voice_id:
            logger.error("No voice ID provided.")
            return

        logger.info(f"Generating audio stream for voice_id: {target_voice_id}")

        try:
            # The official SDK returns an async generator for streaming
            # We use the standard convert method which returns an AsyncIterator when used with AsyncElevenLabs
            
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=target_voice_id,
                model_id=settings.ELEVENLABS_MODEL_ID,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75
                )
            )
            
            async for chunk in audio_stream:
                yield chunk
                        
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")

# Global instance
voice_service = VoiceService()
