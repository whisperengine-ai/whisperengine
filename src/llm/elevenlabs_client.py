"""
ElevenLabs Client for Text-to-Speech and Speech-to-Text functionality
SECURITY ENHANCED: Now includes API key validation and secure credential handling
"""

import logging
import os
from io import BytesIO
from typing import Any

import aiohttp

from src.utils.exceptions import LLMConnectionError, LLMError, LLMRateLimitError, LLMTimeoutError


class ElevenLabsClient:
    """Client for ElevenLabs TTS and STT services"""

    def __init__(self, api_key: str | None = None, require_api_key: bool = True):
        """
        Initialize the ElevenLabs client with secure API key validation

        Args:
            api_key: ElevenLabs API key (from environment if not provided)
            require_api_key: Whether to require an API key (False when voice is disabled)
        """
        # SECURITY ENHANCEMENT: Import API key security manager
        try:
            from src.security.api_key_security import APIKeyType, get_api_key_manager

            self.api_key_manager = get_api_key_manager()
        except ImportError:
            self.api_key_manager = None
            logging.warning(
                "API key security module not available for ElevenLabs - using basic validation"
            )

        raw_api_key = api_key or os.getenv("ELEVENLABS_API_KEY")

        # SECURITY ENHANCEMENT: Validate API key before using
        if raw_api_key and self.api_key_manager:
            key_info = self.api_key_manager.validate_api_key(raw_api_key, APIKeyType.ELEVENLABS)
            if key_info.is_valid:
                self.api_key = raw_api_key
                logging.debug(f"ElevenLabs API key validated: {key_info.masked_key}")
            else:
                self.api_key = None
                error_msg = f"Invalid ElevenLabs API key rejected: {key_info.masked_key} - Threats: {[t.value for t in key_info.security_threats]}"
                logging.error(error_msg)
                raise ValueError(f"Invalid ElevenLabs API key. {error_msg}")
        else:
            self.api_key = raw_api_key

        if not self.api_key and require_api_key:
            raise ValueError(
                "ElevenLabs API key is required. Set ELEVENLABS_API_KEY environment variable."
            )

        self.base_url = "https://api.elevenlabs.io/v1"
        self.logger = logging.getLogger(__name__)

        # Load voice configuration from environment
        self.default_voice_id = os.getenv(
            "ELEVENLABS_DEFAULT_VOICE_ID", "ked1vRAQW5Sk9vhZC3vI"
        )  # Updated default voice
        self.voice_stability = float(os.getenv("ELEVENLABS_VOICE_STABILITY", "0.5"))
        self.voice_similarity_boost = float(os.getenv("ELEVENLABS_VOICE_SIMILARITY_BOOST", "0.8"))
        self.voice_style = float(os.getenv("ELEVENLABS_VOICE_STYLE", "0.0"))  # 0.0 = most natural
        self.voice_use_speaker_boost = (
            os.getenv("ELEVENLABS_USE_SPEAKER_BOOST", "true").lower() == "true"
        )

        # Load model configuration
        self.tts_model = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_monolingual_v1")
        self.stt_model = os.getenv("ELEVENLABS_STT_MODEL", "eleven_speech_to_text_v1")

        # Load timeout configuration
        self.request_timeout = int(os.getenv("ELEVENLABS_REQUEST_TIMEOUT", "30"))
        self.connection_timeout = int(os.getenv("ELEVENLABS_CONNECTION_TIMEOUT", "10"))

        # Load audio configuration
        self.output_format = os.getenv(
            "ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"
        )  # Discord-compatible format
        self.optimize_streaming_latency = int(
            os.getenv("ELEVENLABS_OPTIMIZE_STREAMING", "2")
        )  # 0-4, higher = lower latency
        self.use_streaming = (
            os.getenv("ELEVENLABS_USE_STREAMING", "true").lower() == "true"
        )  # Use streaming API by default

        # SECURITY ENHANCEMENT: Use secure logging that masks API keys
        if self.api_key_manager and self.api_key:
            masked_key = self.api_key_manager.mask_api_key(self.api_key)
            self.logger.debug(f"ElevenLabs client initialized with API key: {masked_key}")
        else:
            self.logger.debug("ElevenLabs client initialized")

        self.logger.debug(f"Voice ID: {self.default_voice_id}")
        self.logger.debug(
            f"Voice settings - Stability: {self.voice_stability}, Similarity: {self.voice_similarity_boost}"
        )
        self.logger.debug(
            f"Audio format: {self.output_format}, Streaming: {self.use_streaming}, Optimization: {self.optimize_streaming_latency}"
        )

    def _get_secure_headers(self) -> dict[str, str]:
        """
        SECURITY ENHANCEMENT: Create secure headers with API key validation

        Returns:
            Dictionary with secure headers for ElevenLabs API
        """
        if not self.api_key:
            return {}

        if self.api_key_manager:
            return self.api_key_manager.secure_header_creation(self.api_key, "xi-api-key")
        else:
            # Fallback to basic header creation
            return {"xi-api-key": self.api_key}

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs

        Returns:
            List of voice dictionaries with id, name, and other properties
        """
        # SECURITY ENHANCEMENT: Use secure header creation
        headers = {"Accept": "application/json"}
        headers.update(self._get_secure_headers())

        try:
            timeout = aiohttp.ClientTimeout(
                connect=self.connection_timeout, total=self.request_timeout
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/voices", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(
                            f"Retrieved {len(data.get('voices', []))} available voices"
                        )
                        return data.get("voices", [])
                    elif response.status == 401:
                        raise LLMConnectionError("Invalid ElevenLabs API key")
                    elif response.status == 429:
                        raise LLMRateLimitError("ElevenLabs rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise LLMError(f"ElevenLabs API error {response.status}: {error_text}")

        except TimeoutError:
            raise LLMTimeoutError("ElevenLabs voices request timed out")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error to ElevenLabs: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error getting voices: {e}")

    async def text_to_speech(
        self,
        text: str,
        voice_id: str | None = None,
        model_id: str | None = None,
        voice_settings: dict[str, Any] | None = None,
        stream: bool | None = None,
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to configured voice)
            model_id: Model ID to use (defaults to configured model)
            voice_settings: Custom voice settings (defaults to configured settings)
            stream: Use streaming API for lower latency (default: configured setting)

        Returns:
            Audio data as bytes
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        voice_id = voice_id or self.default_voice_id
        model_id = model_id or self.tts_model
        stream = stream if stream is not None else self.use_streaming

        # Use configured voice settings if not provided
        if voice_settings is None:
            voice_settings = {
                "stability": self.voice_stability,
                "similarity_boost": self.voice_similarity_boost,
                "style": self.voice_style,
                "use_speaker_boost": self.voice_use_speaker_boost,
            }

        payload = {"text": text, "model_id": model_id, "voice_settings": voice_settings}

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        # Use streaming API for lower latency or regular API for compatibility
        if stream:
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            # Add optimization parameters for streaming
            params = []
            if self.output_format:
                params.append(f"output_format={self.output_format}")
            if self.optimize_streaming_latency > 0:
                params.append(f"optimize_streaming_latency={self.optimize_streaming_latency}")
            if params:
                url += "?" + "&".join(params)
        else:
            # Regular API endpoint
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            if self.output_format:
                url += f"?output_format={self.output_format}"

        try:
            self.logger.debug(f"Converting text to speech: {text[:50]}... (voice: {voice_id})")

            timeout = aiohttp.ClientTimeout(
                connect=self.connection_timeout,
                total=self.request_timeout * 2,  # TTS can take longer
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        if stream:
                            # Stream the audio data for lower latency
                            audio_chunks = []
                            async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                                if chunk:
                                    audio_chunks.append(chunk)
                            audio_data = b"".join(audio_chunks)
                            self.logger.debug(
                                f"Streamed {len(audio_data)} bytes of audio data in {len(audio_chunks)} chunks"
                            )
                        else:
                            # Regular read for non-streaming
                            audio_data = await response.read()
                            self.logger.debug(f"Generated {len(audio_data)} bytes of audio data")
                        return audio_data
                    elif response.status == 401:
                        raise LLMConnectionError("Invalid ElevenLabs API key")
                    elif response.status == 429:
                        raise LLMRateLimitError("ElevenLabs rate limit exceeded")
                    elif response.status == 400:
                        error_data = await response.json()
                        raise LLMError(
                            f"ElevenLabs TTS error: {error_data.get('detail', 'Bad request')}"
                        )
                    else:
                        error_text = await response.text()
                        raise LLMError(f"ElevenLabs TTS API error {response.status}: {error_text}")

        except TimeoutError:
            raise LLMTimeoutError("ElevenLabs TTS request timed out")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error to ElevenLabs TTS: {e}")
        except Exception as e:
            if isinstance(e, (LLMError, LLMConnectionError, LLMTimeoutError, LLMRateLimitError)):
                raise
            raise LLMError(f"Unexpected error in TTS: {e}")

    async def speech_to_text(
        self, audio_data: bytes, model_id: str | None = None, language: str | None = None
    ) -> str:
        """
        Convert speech to text using ElevenLabs STT

        Args:
            audio_data: Audio data as bytes
            model_id: Model ID to use (defaults to configured model)
            language: Language code (e.g., 'en', 'es', 'fr') - auto-detect if None

        Returns:
            Transcribed text
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        model_id = model_id or self.stt_model

        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field("audio", BytesIO(audio_data), filename="audio.wav", content_type="audio/wav")
        data.add_field("model_id", model_id)

        if language:
            data.add_field("language", language)

        headers = {"Accept": "application/json", "xi-api-key": self.api_key}

        try:
            self.logger.debug(
                f"Converting speech to text: {len(audio_data)} bytes (model: {model_id})"
            )

            timeout = aiohttp.ClientTimeout(
                connect=self.connection_timeout,
                total=self.request_timeout * 3,  # STT can take longer for large files
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/speech-to-text", data=data, headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("text", "").strip()
                        self.logger.debug(f"Transcribed text: {text[:100]}...")
                        return text
                    elif response.status == 401:
                        raise LLMConnectionError("Invalid ElevenLabs API key")
                    elif response.status == 429:
                        raise LLMRateLimitError("ElevenLabs rate limit exceeded")
                    elif response.status == 400:
                        error_data = await response.json()
                        raise LLMError(
                            f"ElevenLabs STT error: {error_data.get('detail', 'Bad request')}"
                        )
                    else:
                        error_text = await response.text()
                        raise LLMError(f"ElevenLabs STT API error {response.status}: {error_text}")

        except TimeoutError:
            raise LLMTimeoutError("ElevenLabs STT request timed out")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error to ElevenLabs STT: {e}")
        except Exception as e:
            if isinstance(e, (LLMError, LLMConnectionError, LLMTimeoutError, LLMRateLimitError)):
                raise
            raise LLMError(f"Unexpected error in STT: {e}")

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: str | None = None,
        model_id: str | None = None,
        voice_settings: dict[str, Any] | None = None,
    ):
        """
        Convert text to speech using ElevenLabs streaming API, yielding audio chunks as they arrive

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to configured voice)
            model_id: Model ID to use (defaults to configured model)
            voice_settings: Custom voice settings (defaults to configured settings)

        Yields:
            Audio chunks as bytes for real-time playback
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        voice_id = voice_id or self.default_voice_id
        model_id = model_id or self.tts_model

        # Use configured voice settings if not provided
        if voice_settings is None:
            voice_settings = {
                "stability": self.voice_stability,
                "similarity_boost": self.voice_similarity_boost,
                "style": self.voice_style,
                "use_speaker_boost": self.voice_use_speaker_boost,
            }

        payload = {"text": text, "model_id": model_id, "voice_settings": voice_settings}

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        # Streaming API endpoint with optimization
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
        params = []
        if self.output_format:
            params.append(f"output_format={self.output_format}")
        if self.optimize_streaming_latency > 0:
            params.append(f"optimize_streaming_latency={self.optimize_streaming_latency}")
        if params:
            url += "?" + "&".join(params)

        try:
            self.logger.debug(f"Streaming text to speech: {text[:50]}... (voice: {voice_id})")

            timeout = aiohttp.ClientTimeout(
                connect=self.connection_timeout,
                total=self.request_timeout * 3,  # Streaming can take longer for long texts
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        chunk_count = 0
                        total_bytes = 0
                        async for chunk in response.content.iter_chunked(
                            4096
                        ):  # 4KB chunks for faster streaming
                            if chunk:
                                chunk_count += 1
                                total_bytes += len(chunk)
                                yield chunk
                        self.logger.debug(f"Streamed {total_bytes} bytes in {chunk_count} chunks")
                    elif response.status == 401:
                        raise LLMConnectionError("Invalid ElevenLabs API key")
                    elif response.status == 429:
                        raise LLMRateLimitError("ElevenLabs rate limit exceeded")
                    elif response.status == 400:
                        error_data = await response.json()
                        raise LLMError(
                            f"ElevenLabs TTS streaming error: {error_data.get('detail', 'Bad request')}"
                        )
                    else:
                        error_text = await response.text()
                        raise LLMError(
                            f"ElevenLabs TTS streaming API error {response.status}: {error_text}"
                        )

        except TimeoutError:
            raise LLMTimeoutError("ElevenLabs TTS streaming request timed out")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error to ElevenLabs TTS streaming: {e}")
        except Exception as e:
            if isinstance(e, (LLMError, LLMConnectionError, LLMTimeoutError, LLMRateLimitError)):
                raise
            raise LLMError(f"Unexpected error in TTS streaming: {e}")

    async def check_connection(self) -> bool:
        """
        Check if ElevenLabs API is accessible

        Returns:
            True if connection is successful
        """
        try:
            voices = await self.get_available_voices()
            return len(voices) > 0
        except Exception as e:
            self.logger.debug(f"ElevenLabs connection check failed: {e}")
            return False

    def get_voice_settings(self) -> dict[str, Any]:
        """
        Get current voice settings configuration

        Returns:
            Dictionary with current voice settings
        """
        return {
            "voice_id": self.default_voice_id,
            "stability": self.voice_stability,
            "similarity_boost": self.voice_similarity_boost,
            "style": self.voice_style,
            "use_speaker_boost": self.voice_use_speaker_boost,
            "model": self.tts_model,
            "output_format": self.output_format,
            "streaming_optimization": self.optimize_streaming_latency,
        }
