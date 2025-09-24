"""
Voice API endpoints for web interface

Provides RESTful API endpoints for voice chat functionality including:
- Text-to-speech conversion
- Speech-to-text transcription  
- Voice settings management
- Available voices listing
"""

import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field

from src.web.voice_handler import WebVoiceHandler, create_web_voice_handler
from src.llm.llm_protocol import create_llm_client


logger = logging.getLogger(__name__)


# Pydantic models for API
class TTSRequest(BaseModel):
    """Text-to-speech request model"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to convert to speech")
    voice_id: Optional[str] = Field(None, description="Specific voice ID (optional)")
    bot_name: Optional[str] = Field(None, description="Bot name for character-specific voice")


class TTSResponse(BaseModel):
    """Text-to-speech response model"""
    audio_data: str = Field(..., description="Base64-encoded audio data (MP3)")
    voice_id: str = Field(..., description="Voice ID used for generation")
    duration_estimate: Optional[float] = Field(None, description="Estimated audio duration in seconds")


class STTResponse(BaseModel):
    """Speech-to-text response model"""
    text: str = Field(..., description="Transcribed text from audio")
    confidence: Optional[float] = Field(None, description="Confidence score (if available)")


class VoiceSettingsRequest(BaseModel):
    """Voice settings update request"""
    voice_id: Optional[str] = None
    stability: Optional[float] = Field(None, ge=0.0, le=1.0)
    similarity_boost: Optional[float] = Field(None, ge=0.0, le=1.0)
    style: Optional[float] = Field(None, ge=0.0, le=1.0)
    use_speaker_boost: Optional[bool] = None


class VoiceInfo(BaseModel):
    """Voice information model"""
    voice_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None


# Global voice handler (will be initialized with app)
_voice_handler: Optional[WebVoiceHandler] = None


def get_voice_handler() -> WebVoiceHandler:
    """Dependency to get voice handler instance"""
    global _voice_handler
    if _voice_handler is None:
        # Initialize voice handler with ElevenLabs client
        try:
            # First try to get from LLM client
            llm_client = create_llm_client(llm_client_type="openrouter")
            if hasattr(llm_client, 'elevenlabs_client') and llm_client.elevenlabs_client:
                _voice_handler = create_web_voice_handler(llm_client.elevenlabs_client)
            else:
                # Create standalone ElevenLabs client with API key
                from src.llm.elevenlabs_client import ElevenLabsClient
                import os
                
                # Get API key from environment (same as used by Discord bots)
                api_key = os.getenv("ELEVENLABS_API_KEY")
                if not api_key:
                    # Try to get from Elena's config since she has one
                    logger.warning("No ELEVENLABS_API_KEY found in environment, voice features may be limited")
                    elevenlabs_client = ElevenLabsClient(require_api_key=False)
                else:
                    elevenlabs_client = ElevenLabsClient(api_key=api_key, require_api_key=True)
                
                _voice_handler = create_web_voice_handler(elevenlabs_client)
        except Exception as e:
            logger.error("Failed to initialize voice handler: %s", e)
            raise HTTPException(status_code=500, detail="Voice service unavailable") from e
    
    return _voice_handler


# Create router for voice endpoints
voice_router = APIRouter(prefix="/api/voice", tags=["voice"])


@voice_router.post("/tts/stream")
async def stream_text_to_speech(
    request: TTSRequest,
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
):
    """
    Convert text to speech with streaming audio chunks
    
    Args:
        request: TTS request with text and optional voice settings
        voice_handler: Voice handler dependency
        
    Returns:
        Streaming response with audio chunks
    """
    from fastapi.responses import StreamingResponse
    
    try:
        logger.info("Streaming TTS request: text length=%d, voice_id=%s", 
                   len(request.text), request.voice_id)
        
        # Check if streaming is supported
        if not hasattr(voice_handler.elevenlabs, 'text_to_speech_stream'):
            raise HTTPException(status_code=501, detail="Streaming TTS not supported")
        
        # Get streaming audio chunks
        async def generate_audio_chunks():
            try:
                chunk_count = 0
                async for chunk in voice_handler.elevenlabs.text_to_speech_stream(
                    text=request.text,
                    voice_id=request.voice_id
                ):
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.debug("First audio chunk ready, starting stream")
                    yield chunk
                logger.info("Streaming TTS completed: %d chunks sent", chunk_count)
            except Exception as e:
                logger.error("Streaming TTS error: %s", e)
                raise
        
        return StreamingResponse(
            generate_audio_chunks(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering for real streaming
            }
        )
        
    except Exception as e:
        logger.error("Streaming TTS error: %s", e)
        raise HTTPException(status_code=500, detail=f"Streaming text-to-speech failed: {str(e)}")


@voice_router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> TTSResponse:
    """
    Convert text to speech
    
    Args:
        request: TTS request with text and optional voice settings
        voice_handler: Voice handler dependency
        
    Returns:
        TTSResponse with base64-encoded audio data
    """
    try:
        logger.info("TTS request: text length=%d, voice_id=%s", 
                   len(request.text), request.voice_id)
        
        # Convert text to speech
        audio_data = await voice_handler.text_to_speech(
            text=request.text,
            voice_id=request.voice_id
        )
        
        # Encode audio as base64 for JSON response
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Get voice ID used (may be default if not specified)
        voice_settings = voice_handler.get_voice_settings()
        used_voice_id = request.voice_id or voice_settings["voice_id"]
        
        # Estimate duration (rough calculation: ~150 words per minute, ~5 chars per word)
        word_count = len(request.text.split())
        duration_estimate = (word_count / 150) * 60  # seconds
        
        logger.info("TTS completed: audio_size=%d bytes, duration_estimate=%.1fs", 
                   len(audio_data), duration_estimate)
        
        return TTSResponse(
            audio_data=audio_base64,
            voice_id=used_voice_id,
            duration_estimate=duration_estimate
        )
        
    except Exception as e:
        logger.error("TTS error: %s", e)
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@voice_router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> STTResponse:
    """
    Convert speech to text
    
    Args:
        audio_file: Uploaded audio file
        voice_handler: Voice handler dependency
        
    Returns:
        STTResponse with transcribed text
    """
    try:
        logger.info("STT request: filename=%s, content_type=%s", 
                   audio_file.filename, audio_file.content_type)
        
        # Read audio data
        audio_data = await audio_file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Convert speech to text
        transcribed_text = await voice_handler.speech_to_text(audio_data)
        
        logger.info("STT completed: transcribed_length=%d", len(transcribed_text))
        
        return STTResponse(
            text=transcribed_text,
            confidence=None  # ElevenLabs doesn't provide confidence scores
        )
        
    except Exception as e:
        logger.error("STT error: %s", e)
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")


@voice_router.get("/voices", response_model=list[VoiceInfo])
async def get_available_voices(
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> list[VoiceInfo]:
    """
    Get list of available voices
    
    Args:
        voice_handler: Voice handler dependency
        
    Returns:
        List of available voices
    """
    try:
        voices = await voice_handler.get_available_voices()
        
        # Convert to VoiceInfo models
        voice_infos = []
        for voice in voices:
            voice_info = VoiceInfo(
                voice_id=voice.get("voice_id", ""),
                name=voice.get("name", "Unknown"),
                description=voice.get("description"),
                category=voice.get("category"),
                accent=voice.get("accent"),
                age=voice.get("age"),
                gender=voice.get("gender")
            )
            voice_infos.append(voice_info)
        
        logger.info("Retrieved %d available voices", len(voice_infos))
        return voice_infos
        
    except Exception as e:
        logger.error("Error getting voices: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@voice_router.get("/settings")
async def get_voice_settings(
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> Dict[str, Any]:
    """
    Get current voice settings
    
    Args:
        voice_handler: Voice handler dependency
        
    Returns:
        Current voice settings
    """
    try:
        settings = voice_handler.get_voice_settings()
        logger.debug("Retrieved voice settings: %s", settings)
        return settings
    except Exception as e:
        logger.error("Error getting voice settings: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@voice_router.put("/settings")
async def update_voice_settings(
    request: VoiceSettingsRequest,
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> Dict[str, Any]:
    """
    Update voice settings
    
    Args:
        request: Voice settings update request
        voice_handler: Voice handler dependency
        
    Returns:
        Updated voice settings
    """
    try:
        # Extract non-None values for update
        update_data = {}
        for field, value in request.dict().items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No settings provided to update")
        
        # Update settings
        voice_handler.update_voice_settings(**update_data)
        
        # Return updated settings
        updated_settings = voice_handler.get_voice_settings()
        logger.info("Updated voice settings: %s", update_data)
        return updated_settings
        
    except Exception as e:
        logger.error("Error updating voice settings: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@voice_router.get("/health")
async def voice_health_check(
    voice_handler: WebVoiceHandler = Depends(get_voice_handler)
) -> Dict[str, Any]:
    """
    Check voice service health
    
    Args:
        voice_handler: Voice handler dependency
        
    Returns:
        Health status information
    """
    try:
        # Test basic functionality
        voices = await voice_handler.get_available_voices()
        voice_count = len(voices)
        
        # Check if ElevenLabs API is accessible
        api_accessible = voice_count > 0
        
        settings = voice_handler.get_voice_settings()
        
        health_info = {
            "status": "healthy" if api_accessible else "degraded",
            "api_accessible": api_accessible,
            "available_voices": voice_count,
            "current_voice_id": settings.get("voice_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.debug("Voice health check: %s", health_info)
        return health_info
        
    except Exception as e:
        logger.error("Voice health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Function to initialize voice handler (called from main app)
def initialize_voice_handler(elevenlabs_client) -> None:
    """Initialize the global voice handler"""
    global _voice_handler
    _voice_handler = create_web_voice_handler(elevenlabs_client)
    logger.info("Voice handler initialized for web API")