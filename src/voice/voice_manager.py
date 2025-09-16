"""
Discord Voice Manager for handling voice channel operations with ElevenLabs integration
"""

import asyncio
import io
import logging
import os
import tempfile
import time
from collections import defaultdict, deque
from typing import Any

import discord
from discord.ext import commands

from src.llm.elevenlabs_client import ElevenLabsClient
from src.utils.exceptions import LLMConnectionError, LLMRateLimitError, LLMTimeoutError


class VoiceState:
    """Represents a voice state for a guild"""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.voice_client: discord.VoiceClient | None = None
        self.is_listening = False
        self.is_speaking = False
        self.current_channel_id: int | None = None
        self.audio_buffer = deque(maxlen=300)  # ~10 seconds at 30fps
        self.last_audio_time = 0
        self.silence_threshold = 2.0  # seconds of silence before processing
        self.participants: dict[int, str] = {}  # user_id -> display_name
        self.recording_users: dict[int, bool] = defaultdict(bool)
        self.audio_queue = asyncio.Queue()
        self.tts_queue = asyncio.Queue()
        self.processing_lock = asyncio.Lock()

    def reset(self):
        """Reset the voice state"""
        self.is_listening = False
        self.is_speaking = False
        self.audio_buffer.clear()
        self.last_audio_time = 0
        self.participants.clear()
        self.recording_users.clear()
        # Clear queues
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except asyncio.QueueEmpty:
                break


class DiscordVoiceManager:
    """Manages Discord voice channel operations with ElevenLabs TTS/STT"""

    def __init__(
        self, bot: commands.Bot, elevenlabs_client: ElevenLabsClient, llm_client, memory_manager
    ):
        """
        Initialize the Voice Manager

        Args:
            bot: Discord bot instance
            elevenlabs_client: ElevenLabs client for TTS/STT
            llm_client: LLM client for processing responses
            memory_manager: Memory manager for conversation storage
        """
        self.bot = bot
        self.elevenlabs = elevenlabs_client
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)

        # Guild-specific voice states
        self.voice_states: dict[int, VoiceState] = {}

        # Configuration from environment
        self.auto_join_enabled = os.getenv("VOICE_AUTO_JOIN", "false").lower() == "true"
        self.voice_response_enabled = os.getenv("VOICE_RESPONSE_ENABLED", "true").lower() == "true"
        self.voice_listening_enabled = (
            os.getenv("VOICE_LISTENING_ENABLED", "true").lower() == "true"
        )
        self.voice_streaming_enabled = (
            os.getenv("VOICE_STREAMING_ENABLED", "true").lower() == "true"
        )
        self.max_audio_length = int(os.getenv("VOICE_MAX_AUDIO_LENGTH", "30"))  # seconds
        self.response_delay = float(os.getenv("VOICE_RESPONSE_DELAY", "1.0"))  # seconds

        # Audio processing settings
        self.sample_rate = 48000  # Discord's sample rate
        self.channels = 2  # Discord stereo
        self.sample_width = 2  # 16-bit audio
        self.chunk_size = 3840  # Discord's frame size (20ms at 48kHz)

        self.logger.info("Discord Voice Manager initialized")
        self.logger.debug(
            f"Voice settings - Auto-join: {self.auto_join_enabled}, Response: {self.voice_response_enabled}, Listening: {self.voice_listening_enabled}"
        )

    def get_voice_state(self, guild_id: int) -> VoiceState:
        """Get or create voice state for a guild"""
        if guild_id not in self.voice_states:
            self.voice_states[guild_id] = VoiceState(guild_id)
        return self.voice_states[guild_id]

    async def join_voice_channel(self, channel: discord.VoiceChannel) -> bool:
        """
        Join a voice channel

        Args:
            channel: Voice channel to join

        Returns:
            True if successfully joined
        """
        try:
            guild_id = channel.guild.id
            voice_state = self.get_voice_state(guild_id)

            # Leave current channel if in one
            if voice_state.voice_client and voice_state.voice_client.is_connected():
                await voice_state.voice_client.disconnect()

            # Join the new channel
            voice_client = await channel.connect()
            voice_state.voice_client = voice_client
            voice_state.current_channel_id = channel.id
            voice_state.reset()

            # Update participants list
            for member in channel.members:
                if not member.bot:
                    voice_state.participants[member.id] = member.display_name

            self.logger.info(
                f"Joined voice channel '{channel.name}' in guild '{channel.guild.name}'"
            )

            # Start listening if enabled
            if self.voice_listening_enabled:
                await self.start_listening(guild_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to join voice channel: {e}")
            return False

    async def leave_voice_channel(self, guild_id: int) -> bool:
        """
        Leave the current voice channel

        Args:
            guild_id: Guild ID to leave voice channel in

        Returns:
            True if successfully left
        """
        try:
            voice_state = self.get_voice_state(guild_id)

            if voice_state.voice_client and voice_state.voice_client.is_connected():
                await self.stop_listening(guild_id)
                await voice_state.voice_client.disconnect()
                voice_state.voice_client = None
                voice_state.current_channel_id = None
                voice_state.reset()

                self.logger.info(f"Left voice channel in guild {guild_id}")
                return True
            else:
                self.logger.debug(f"Not connected to voice channel in guild {guild_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to leave voice channel: {e}")
            return False

    async def start_listening(self, guild_id: int):
        """Start listening for voice input in a guild"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client or not voice_state.voice_client.is_connected():
            self.logger.error(
                f"Cannot start listening: not connected to voice channel in guild {guild_id}"
            )
            return

        if voice_state.is_listening:
            self.logger.debug(f"Already listening in guild {guild_id}")
            return

        voice_state.is_listening = True

        # Start audio processing task (we'll use voice receive instead of recording)
        asyncio.create_task(self._process_audio_queue(guild_id))
        asyncio.create_task(self._listen_for_voice(guild_id))

        self.logger.info(f"Started listening in guild {guild_id}")

    async def stop_listening(self, guild_id: int):
        """Stop listening for voice input in a guild"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.is_listening:
            return

        voice_state.is_listening = False

        self.logger.info(f"Stopped listening in guild {guild_id}")

    async def _listen_for_voice(self, guild_id: int):
        """Listen for voice activity - text-to-voice bridge with connection keepalive"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client:
            return

        self.logger.info(
            f"🎤 Voice listening enabled for guild {guild_id} - with connection keepalive"
        )

        # Send notification about current capabilities (if enabled)
        voice_join_announcements = os.getenv("VOICE_JOIN_ANNOUNCEMENTS", "true").lower() == "true"

        if voice_join_announcements:
            current_channel = self.get_current_channel(guild_id)
            if current_channel:
                text_channels = [
                    ch
                    for ch in current_channel.guild.text_channels
                    if "bot" in ch.name.lower() or "general" in ch.name.lower()
                ]
                if text_channels:
                    try:
                        embed = discord.Embed(
                            title="🎤 Voice Chat Ready!",
                            description=(
                                "🎯 **Voice chat is active!**\n\n"
                                "**Current Features:**\n"
                                "• Text-to-voice chat ✅\n"
                                "• @mention me and I'll respond with voice ✅\n"
                                "• Full LLM integration ✅\n"
                                "• Memory & context ✅\n"
                                "• Connection keepalive ✅\n\n"
                                "**How to use:**\n"
                                "• @mention the bot with text\n"
                                "• Get text response + voice response\n"
                                "• Natural conversation with voice output!"
                            ),
                            color=discord.Color.green(),
                        )
                        embed.add_field(
                            name="💡 Commands",
                            value="`!speak <text>` - Make bot say something\n"
                            "`!voice_test` - Test voice functionality\n"
                            "`!voice_chat_test` - Test text-to-voice feature",
                            inline=False,
                        )
                        await text_channels[0].send(embed=embed)
                    except:
                        pass

        # Start voice connection keepalive loop
        await self._voice_connection_keepalive(guild_id)

    async def _voice_connection_keepalive(self, guild_id: int):
        """Maintain voice connection with periodic activity to prevent timeouts"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client:
            self.logger.error("Cannot start voice keepalive: no voice client")
            return

        self.logger.info(f"Starting voice connection keepalive for guild {guild_id}")

        # Configuration from environment
        keepalive_interval = float(
            os.getenv("VOICE_KEEPALIVE_INTERVAL", "300")
        )  # Default 5 minutes
        heartbeat_interval = float(
            os.getenv("VOICE_HEARTBEAT_INTERVAL", "30")
        )  # Default 30 seconds
        max_reconnect_attempts = int(os.getenv("VOICE_MAX_RECONNECT_ATTEMPTS", "3"))
        reconnect_delay = float(os.getenv("VOICE_RECONNECT_DELAY", "5.0"))

        last_keepalive = time.time()
        reconnect_attempts = 0

        try:
            while voice_state.is_listening and voice_state.voice_client:
                current_time = time.time()

                try:
                    # Check if voice client is still connected
                    if not voice_state.voice_client.is_connected():
                        self.logger.warning(f"Voice client disconnected in guild {guild_id}")

                        # Attempt to reconnect
                        if reconnect_attempts < max_reconnect_attempts:
                            reconnect_attempts += 1
                            self.logger.info(
                                f"Attempting to reconnect... (attempt {reconnect_attempts}/{max_reconnect_attempts})"
                            )

                            # Get the current channel to reconnect to
                            current_channel = self.get_current_channel(guild_id)
                            if current_channel:
                                try:
                                    # Disconnect cleanly first
                                    if voice_state.voice_client:
                                        await voice_state.voice_client.disconnect()

                                    # Reconnect
                                    voice_client = await current_channel.connect()
                                    voice_state.voice_client = voice_client

                                    self.logger.info(
                                        f"Successfully reconnected to voice channel in guild {guild_id}"
                                    )
                                    reconnect_attempts = 0  # Reset on successful reconnection

                                except Exception as e:
                                    self.logger.error(f"Failed to reconnect to voice channel: {e}")
                                    await asyncio.sleep(reconnect_delay)
                                    continue
                            else:
                                self.logger.error("Cannot reconnect: current channel not found")
                                break
                        else:
                            self.logger.error(
                                f"Max reconnection attempts reached for guild {guild_id}"
                            )
                            break

                    # Send periodic keepalive activity
                    if current_time - last_keepalive > keepalive_interval:
                        try:
                            # Send a very brief silence as keepalive
                            # This prevents Discord from timing out the connection
                            await self._send_keepalive_audio(guild_id)
                            last_keepalive = current_time
                            self.logger.debug(f"Sent voice keepalive for guild {guild_id}")

                        except Exception as e:
                            self.logger.warning(f"Failed to send voice keepalive: {e}")

                    # Reset reconnect attempts on successful operation
                    reconnect_attempts = 0

                    # Wait before next check
                    await asyncio.sleep(heartbeat_interval)

                except Exception as e:
                    self.logger.error(f"Error in voice keepalive loop: {e}")
                    await asyncio.sleep(5.0)  # Wait before retrying

        except Exception as e:
            self.logger.error(f"Voice keepalive loop failed: {e}")
        finally:
            self.logger.info(f"Voice keepalive stopped for guild {guild_id}")

    async def _send_keepalive_audio(self, guild_id: int):
        """Send brief silence to keep voice connection alive"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client or not voice_state.voice_client.is_connected():
            return

        try:
            # Create a very short silence (0.1 seconds)
            # This is enough to keep the connection active without being noticeable
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                # Generate 0.1 seconds of silence at 44.1kHz
                silence_samples = int(0.1 * 44100)  # 44.1kHz sample rate
                silence_data = b"\x00" * (silence_samples * 2 * 2)  # 16-bit stereo

                # Write as raw PCM first, then we'll convert
                temp_pcm = temp_file.name + ".pcm"
                with open(temp_pcm, "wb") as pcm_file:
                    pcm_file.write(silence_data)

                # Convert to MP3 using FFmpeg
                import subprocess

                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-f",
                            "s16le",
                            "-ar",
                            "44100",
                            "-ac",
                            "2",
                            "-i",
                            temp_pcm,
                            "-y",
                            temp_file.name,
                        ],
                        check=True,
                        capture_output=True,
                    )

                    # Play the silence (only if not already playing)
                    if not voice_state.voice_client.is_playing():
                        audio_source = discord.FFmpegPCMAudio(temp_file.name)
                        voice_state.voice_client.play(audio_source)

                        # Wait very briefly for playback
                        await asyncio.sleep(0.2)

                except subprocess.CalledProcessError:
                    # If FFmpeg fails, just skip the keepalive
                    pass
                finally:
                    # Clean up temporary files
                    try:
                        os.unlink(temp_pcm)
                        os.unlink(temp_file.name)
                    except OSError:
                        pass

        except Exception as e:
            self.logger.debug(f"Keepalive audio generation failed: {e}")

    async def _queue_audio_for_processing(
        self, guild_id: int, user_id: int, audio_file: io.BytesIO
    ):
        """Queue audio data for speech-to-text processing"""
        voice_state = self.get_voice_state(guild_id)

        try:
            # Get audio data
            audio_file.seek(0)
            audio_data = audio_file.read()

            # Skip if audio is too short or too long
            if len(audio_data) < 1000:  # Less than ~0.1 seconds
                return

            # Check audio length (approximate)
            estimated_duration = len(audio_data) / (
                self.sample_rate * self.sample_width * self.channels
            )
            if estimated_duration > self.max_audio_length:
                self.logger.warning(f"Audio too long ({estimated_duration:.1f}s), skipping")
                return

            # Queue for processing
            await voice_state.audio_queue.put(
                {"user_id": user_id, "audio_data": audio_data, "timestamp": time.time()}
            )

        except Exception as e:
            self.logger.error(f"Error queuing audio for processing: {e}")

    async def _process_audio_queue(self, guild_id: int):
        """Process queued audio data"""
        voice_state = self.get_voice_state(guild_id)

        while voice_state.is_listening:
            try:
                # Wait for audio with timeout
                audio_item = await asyncio.wait_for(voice_state.audio_queue.get(), timeout=1.0)

                # Process the audio
                await self._process_audio_message(guild_id, audio_item)

            except TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio queue: {e}")
                await asyncio.sleep(1.0)

    async def _process_audio_message(self, guild_id: int, audio_item: dict[str, Any]):
        """Process a single audio message"""
        voice_state = self.get_voice_state(guild_id)
        user_id = audio_item["user_id"]
        audio_data = audio_item["audio_data"]

        async with voice_state.processing_lock:
            try:
                # Convert speech to text
                self.logger.debug(f"Processing audio from user {user_id} in guild {guild_id}")
                text = await self.elevenlabs.speech_to_text(audio_data)

                if not text.strip():
                    self.logger.debug("No text detected in audio")
                    return

                self.logger.info(f"Voice message from user {user_id}: {text}")

                # Get user display name
                display_name = voice_state.participants.get(user_id, f"User{user_id}")

                # Process with LLM if voice responses are enabled
                if self.voice_response_enabled:
                    await self._generate_voice_response(guild_id, user_id, text, display_name)

                # Store in memory
                if self.memory_manager:
                    try:
                        # Create a mock message-like object for memory storage
                        user_id_str = str(user_id)
                        self.memory_manager.store_conversation(
                            user_id_str,
                            f"[Voice] {text}",
                            "",
                            metadata={"source": "voice", "guild_id": guild_id},
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to store voice message in memory: {e}")

            except (LLMConnectionError, LLMTimeoutError, LLMRateLimitError) as e:
                self.logger.warning(f"ElevenLabs STT error: {e}")
            except Exception as e:
                self.logger.error(f"Error processing audio message: {e}")

    async def _generate_voice_response(
        self, guild_id: int, user_id: int, text: str, display_name: str
    ):
        """Generate and speak a voice response"""
        voice_state = self.get_voice_state(guild_id)

        try:
            # Get conversation context (simplified for voice)
            messages = [
                {
                    "role": "system",
                    "content": f"You are responding via voice chat to {display_name}. Keep responses conversational and under 100 words.",
                },
                {"role": "user", "content": text},
            ]

            # Get LLM response
            response = await asyncio.wait_for(
                self.llm_client.get_chat_response(messages), timeout=10.0
            )

            if response.strip():
                # Queue for TTS
                await voice_state.tts_queue.put(
                    {"text": response, "user_id": user_id, "timestamp": time.time()}
                )

                # Start TTS processing if not already running
                if not voice_state.is_speaking:
                    asyncio.create_task(self._process_tts_queue(guild_id))

        except TimeoutError:
            self.logger.warning("LLM response timed out for voice message")
        except Exception as e:
            self.logger.error(f"Error generating voice response: {e}")

    async def _process_tts_queue(self, guild_id: int):
        """Process TTS queue and speak responses"""
        voice_state = self.get_voice_state(guild_id)

        if voice_state.is_speaking:
            return

        voice_state.is_speaking = True

        try:
            while not voice_state.tts_queue.empty():
                try:
                    tts_item = await asyncio.wait_for(voice_state.tts_queue.get(), timeout=1.0)

                    await self._speak_text(guild_id, tts_item["text"])

                    # Small delay between responses
                    await asyncio.sleep(self.response_delay)

                except TimeoutError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in TTS processing: {e}")

        finally:
            voice_state.is_speaking = False

    async def _speak_text(self, guild_id: int, text: str):
        """Convert text to speech and play in voice channel"""
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client or not voice_state.voice_client.is_connected():
            self.logger.error("Cannot speak: not connected to voice channel")
            return

        try:
            # Check if streaming is supported and enabled
            use_streaming = (
                self.voice_streaming_enabled
                and getattr(self.elevenlabs, "use_streaming", True)
                and hasattr(self.elevenlabs, "text_to_speech_stream")
            )

            if use_streaming:
                # Use streaming API for lower latency
                self.logger.debug(f"Streaming TTS for: {text[:50]}...")

                try:
                    from .streaming_audio_source import (
                        cleanup_streaming_audio,
                        create_streaming_audio_source,
                    )

                    # Get streaming audio chunks
                    chunk_generator = self.elevenlabs.text_to_speech_stream(text)

                    # Create streaming audio source
                    audio_source, temp_filename = await create_streaming_audio_source(
                        chunk_generator, self.logger
                    )

                    # Play audio (starts as soon as first chunks are available)
                    if not voice_state.voice_client.is_playing():
                        voice_state.voice_client.play(audio_source)

                        self.logger.debug("Started streaming audio playback")

                        # Wait for playback to finish
                        while voice_state.voice_client.is_playing():
                            await asyncio.sleep(0.1)

                        self.logger.debug("Finished streaming audio playback")
                    else:
                        self.logger.warning("Voice client is already playing audio")

                    # Clean up streaming resources
                    cleanup_streaming_audio(temp_filename, self.logger)

                except ImportError as e:
                    self.logger.warning(
                        f"Streaming audio source not available (ImportError: {e}), falling back to regular TTS"
                    )
                    use_streaming = False
                except Exception as e:
                    self.logger.warning(
                        f"Streaming TTS failed ({type(e).__name__}: {e}), falling back to regular TTS"
                    )
                    use_streaming = False

            if not use_streaming:
                # Fallback to regular TTS
                self.logger.debug(f"Generating regular TTS for: {text[:50]}...")
                audio_data = await self.elevenlabs.text_to_speech(text, stream=False)

                if not audio_data:
                    self.logger.error("Received empty audio data from ElevenLabs")
                    return

                # Create a temporary file for the audio data
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_file.write(audio_data)
                    temp_filename = temp_file.name

                try:
                    # Create audio source
                    audio_source = discord.FFmpegPCMAudio(temp_filename)

                    # Play audio
                    if not voice_state.voice_client.is_playing():
                        voice_state.voice_client.play(audio_source)

                        # Wait for playback to finish
                        while voice_state.voice_client.is_playing():
                            await asyncio.sleep(0.1)

                        self.logger.debug("Finished regular audio playback")
                    else:
                        self.logger.warning("Voice client is already playing audio")

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_filename)
                    except OSError:
                        pass  # File might already be deleted

        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")

    async def speak_message(self, guild_id: int, text: str, priority: bool = False):
        """
        Speak a text message in the voice channel

        Args:
            guild_id: Guild ID where to speak
            text: Text to convert to speech
            priority: Whether to skip the queue (for important messages)
        """
        voice_state = self.get_voice_state(guild_id)

        if not voice_state.voice_client or not voice_state.voice_client.is_connected():
            self.logger.debug(f"Cannot speak: not connected to voice channel in guild {guild_id}")
            return

        if priority:
            # Speak immediately
            await self._speak_text(guild_id, text)
        else:
            # Queue for speaking
            await voice_state.tts_queue.put(
                {"text": text, "user_id": None, "timestamp": time.time()}
            )

            # Start processing if not already running
            if not voice_state.is_speaking:
                asyncio.create_task(self._process_tts_queue(guild_id))

    def is_connected(self, guild_id: int) -> bool:
        """Check if connected to voice channel in guild"""
        voice_state = self.get_voice_state(guild_id)
        return voice_state.voice_client is not None and voice_state.voice_client.is_connected()

    def is_listening(self, guild_id: int) -> bool:
        """Check if listening in guild"""
        voice_state = self.get_voice_state(guild_id)
        return voice_state.is_listening

    def get_current_channel(self, guild_id: int) -> discord.VoiceChannel | None:
        """Get current voice channel for guild"""
        voice_state = self.get_voice_state(guild_id)
        if voice_state.current_channel_id:
            channel = self.bot.get_channel(voice_state.current_channel_id)
            if isinstance(channel, discord.VoiceChannel):
                return channel
        return None

    def get_participants(self, guild_id: int) -> dict[int, str]:
        """Get current voice participants in guild"""
        voice_state = self.get_voice_state(guild_id)
        return voice_state.participants.copy()

    async def cleanup(self):
        """Clean up all voice connections"""
        for guild_id in list(self.voice_states.keys()):
            await self.leave_voice_channel(guild_id)
        self.voice_states.clear()
        self.logger.info("Voice manager cleanup completed")
