import discord
from discord.ext import commands
from loguru import logger
import asyncio
from typing import Optional, Dict, cast
import io

class VoiceManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # We don't strictly need to track voice_clients manually as bot.voice_clients exists,
        # but it helps for quick lookup by guild_id if needed.
        # Actually, guild.voice_client is the best way.

    async def join_channel(self, channel: discord.VoiceChannel) -> Optional[discord.VoiceClient]:
        """Joins a voice channel."""
        try:
            if channel.guild.voice_client:
                # Cast to VoiceClient to access specific methods/attributes
                vc = cast(discord.VoiceClient, channel.guild.voice_client)
                if vc.channel.id == channel.id:
                    return vc
                await vc.move_to(channel)
                return vc
            
            voice_client = await channel.connect()
            logger.info(f"Joined voice channel: {channel.name} in {channel.guild.name}")
            return voice_client
        except Exception as e:
            logger.error(f"Failed to join voice channel: {e}")
            return None

    async def leave_channel(self, guild: discord.Guild):
        """Leaves the voice channel in the specified guild."""
        if guild.voice_client:
            await guild.voice_client.disconnect(force=False)
            logger.info(f"Left voice channel in guild {guild.name}")

    async def speak(self, guild: discord.Guild, audio_data: bytes):
        """Plays audio bytes in the voice channel."""
        if not guild.voice_client:
            logger.warning(f"Not connected to voice in guild {guild.name}")
            return

        voice_client = cast(discord.VoiceClient, guild.voice_client)
        if voice_client.is_playing():
            voice_client.stop()

        # Convert bytes to AudioSource
        # FFmpegPCMAudio is usually used for files/streams.
        # For bytes, we can use a pipe or write to a temp file.
        # Or use discord.FFmpegOpusAudio if we have opus data.
        # ElevenLabs returns mp3 by default.
        
        # We need ffmpeg installed on the system.
        try:
            audio_source = discord.FFmpegPCMAudio(io.BytesIO(audio_data), pipe=True)
            voice_client.play(audio_source, after=lambda e: logger.error(f"Player error: {e}") if e else None)
            logger.info(f"Started playing audio in guild {guild.name}")
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")

