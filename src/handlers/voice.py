"""
Voice command handlers for Discord bot
Manages voice channel operations, TTS, and voice-related functionality
"""

import asyncio
import logging
import os
from functools import wraps

import discord
from discord.ext import commands

from src.utils.exceptions import LLMConnectionError, LLMRateLimitError, LLMTimeoutError

logger = logging.getLogger(__name__)


def should_bot_respond_voice(ctx: commands.Context) -> bool:
    """
    Check if this bot instance should respond to the voice command.
    Returns True if:
    1. The command is sent via DM (always respond), OR
    2. The command message contains this bot's name as a separate word, OR
    3. The command message contains the fallback name "whisperengine" as a separate word

    For guild channels, bot name must be explicitly mentioned to prevent conflicts.
    """
    from src.utils.bot_name_utils import get_normalized_bot_name_from_env
    bot_name = get_normalized_bot_name_from_env()
    fallback_name = "whisperengine"

    if not ctx.guild:  # Always respond to DMs
        return True

    # Split message into words for exact matching
    message_words = ctx.message.content.lower().split()

    # Check if bot name or fallback name appears as a separate word
    return bot_name in message_words or fallback_name in message_words


def voice_bot_name_filter():
    """
    Decorator to add bot name filtering to voice commands.
    Commands will only execute if should_bot_respond_voice returns True.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Handle both method calls (self, ctx, ...) and function calls (ctx, ...)
            if len(args) >= 2 and hasattr(args[0], "__dict__"):  # Method call with self
                ctx = args[1]
                if should_bot_respond_voice(ctx):
                    return await func(*args, **kwargs)
            elif len(args) >= 1:  # Function call with ctx as first argument
                ctx = args[0]
                if should_bot_respond_voice(ctx):
                    return await func(*args, **kwargs)
            # If bot shouldn't respond, do nothing (no error message)
            return

        return wrapper

    return decorator


class VoiceCommandHandlers:
    """Handles voice-related commands"""

    def __init__(self, bot, voice_manager):
        self.bot = bot
        self.voice_manager = voice_manager
        self.logger = logging.getLogger(__name__)

    def register_commands(self, bot_name_filter=None):
        """Register all voice commands"""

        # Use the voice-specific bot name filter if no other filter is provided
        if bot_name_filter is None:
            bot_name_filter = voice_bot_name_filter

        @self.bot.command(name="join", aliases=["j"])
        @bot_name_filter()
        async def join_voice(ctx, *, channel_name: str | None = None):
            """
            Join a voice channel
            Usage: !join [channel_name] or !join whisperengine [channel_name]
            If no channel specified, joins the user's current voice channel
            """
            logger.debug(f"Join voice command triggered by {ctx.author.name}")

            # Filter out bot name from channel_name if present
            from src.utils.bot_name_utils import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            fallback_name = "whisperengine"

            if channel_name and (
                channel_name.lower() == bot_name or channel_name.lower() == fallback_name
            ):
                channel_name = None  # Treat as if no channel was specified

            await self._join_voice_handler(ctx, channel_name)

        @self.bot.command(name="leave", aliases=["l", "disconnect"])
        @bot_name_filter()
        async def leave_voice(ctx):
            """
            Leave the current voice channel
            Usage: !leave or !leave whisperengine
            """
            await self._leave_voice_handler(ctx)

        @self.bot.command(name="speak", aliases=["say", "tts"])
        @bot_name_filter()
        async def speak_text(ctx, *, text: str):
            """
            Make the bot speak text in the voice channel
            Usage: !speak <text> or !speak whisperengine <text>
            """
            # Filter out bot name from beginning of text if present
            from src.utils.bot_name_utils import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            fallback_name = "whisperengine"

            # Check if text starts with bot name or fallback name and remove it
            text_words = text.split()
            if text_words and (
                text_words[0].lower() == bot_name or text_words[0].lower() == fallback_name
            ):
                text = " ".join(text_words[1:])  # Remove the first word (bot name)

            if not text.strip():
                await ctx.send("❌ Please provide text to speak. Usage: `!speak <text>`")
                return

            await self._speak_text_handler(ctx, text)

        @self.bot.command(name="voice_toggle_listening", aliases=["vtl", "toggle_listen"])
        @commands.has_permissions(manage_guild=True)
        async def toggle_listening(ctx):
            """
            Toggle voice listening on/off (Admin only)
            Usage: !voice_toggle_listening
            """
            await self._toggle_listening_handler(ctx)

        @self.bot.command(name="voice_settings", aliases=["vset"])
        @commands.has_permissions(manage_guild=True)
        async def voice_settings(ctx):
            """
            Show detailed voice settings (Admin only)
            Usage: !voice_settings
            """
            await self._voice_settings_handler(ctx)

        @self.bot.command(name="voice_test", aliases=["vtest"])
        @bot_name_filter()
        async def voice_test(ctx):
            """
            Test voice functionality
            Usage: !voice_test
            """
            await self._voice_test_handler(ctx)

        @self.bot.command(name="voice_chat_test", aliases=["vctest"])
        @bot_name_filter()
        async def voice_chat_test(ctx):
            """
            Test voice chat functionality
            Usage: !voice_chat_test
            """
            await self._voice_chat_test_handler(ctx)

        @self.bot.command(name="voice_connection_status", aliases=["vcs"])
        @bot_name_filter()
        async def voice_connection_status(ctx):
            """
            Show voice connection status
            Usage: !voice_connection_status
            """
            await self._voice_connection_status_handler(ctx)

        @self.bot.command(name="voice_help", aliases=["vhelp"])
        @bot_name_filter()
        async def voice_help(ctx):
            """
            Show voice command help
            Usage: !voice_help or !voice_help whisperengine
            """
            await self._voice_help_handler(ctx)

    async def _join_voice_handler(self, ctx, channel_name: str | None = None):
        """Handle join voice channel command"""
        try:
            self.logger.debug(
                f"Join voice command called by {ctx.author.name} in {ctx.guild.name if ctx.guild else 'DM'}"
            )

            if not self.voice_manager:
                await ctx.send("❌ Voice functionality is not available.")
                return

            if not ctx.guild:
                await ctx.send("❌ This command can only be used in a server.")
                return

            # Check if user is in a voice channel or specified one
            target_channel = None

            if channel_name:
                # Find channel by name
                for channel in ctx.guild.voice_channels:
                    if channel.name.lower() == channel_name.lower():
                        target_channel = channel
                        break

                if not target_channel:
                    await ctx.send(f"❌ Voice channel '{channel_name}' not found.")
                    return
            else:
                # Use user's current voice channel
                self.logger.debug(f"User {ctx.author.name} voice state: {ctx.author.voice}")
                if (
                    isinstance(ctx.author, discord.Member)
                    and ctx.author.voice
                    and ctx.author.voice.channel
                ):
                    voice_channel = ctx.author.voice.channel
                    if isinstance(voice_channel, discord.VoiceChannel):
                        target_channel = voice_channel

                if not target_channel:
                    await ctx.send(
                        "❌ You're not in a voice channel. Please join one or specify a channel name."
                    )
                    return

            self.logger.debug(f"Target channel: {target_channel.name}")

            # Ensure we have a VoiceChannel
            if not isinstance(target_channel, discord.VoiceChannel):
                await ctx.send("❌ Invalid voice channel type.")
                return

            # Check permissions
            if not target_channel.permissions_for(ctx.guild.me).connect:
                await ctx.send(f"❌ I don't have permission to join '{target_channel.name}'.")
                return

        except Exception as e:
            self.logger.error(f"Error in join voice handler: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {e}")
            return

        # Join the channel
        success = await self.voice_manager.join_voice_channel(target_channel)

        if success:
            embed = discord.Embed(
                title="🎤 Joined Voice Channel",
                description=f"Successfully joined **{target_channel.name}**",
                color=discord.Color.green(),
            )

            # Add status information
            if self.voice_manager.voice_listening_enabled:
                embed.add_field(
                    name="🎧 Listening", value="I'm now listening for voice messages!", inline=False
                )

            if self.voice_manager.voice_response_enabled:
                embed.add_field(
                    name="🗣️ Voice Responses",
                    value="I can respond with voice messages!",
                    inline=False,
                )

            await ctx.send(embed=embed)

            # Speak a greeting if voice responses are enabled
            if self.voice_manager.voice_response_enabled:
                greeting = f"Hello everyone! I've joined {target_channel.name}. I'm ready to chat!"
                await self.voice_manager.speak_message(ctx.guild.id, greeting, priority=True)
        else:
            await ctx.send(f"❌ Failed to join '{target_channel.name}'. Please try again.")

    async def _leave_voice_handler(self, ctx):
        """Handle leave voice channel command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Get current channel name for the message
        current_channel = self.voice_manager.get_current_channel(ctx.guild.id)
        channel_name = current_channel.name if current_channel else "voice channel"

        # Announce leaving
        if current_channel and self.voice_manager.voice_response_enabled:
            goodbye_message = f"Goodbye everyone! I'm leaving {channel_name}."
            await self.voice_manager.speak_message(ctx.guild.id, goodbye_message, priority=True)
            await asyncio.sleep(2)  # Wait for message to finish

        # Leave the channel
        success = await self.voice_manager.leave_voice_channel(ctx.guild.id)

        if success:
            embed = discord.Embed(
                title="👋 Left Voice Channel",
                description=f"Successfully left **{channel_name}**",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to leave voice channel.")

    async def _speak_text_handler(self, ctx, text: str):
        """Handle speak text command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not text.strip():
            await ctx.send("❌ Please provide text to speak.")
            return

        try:
            # Check if bot is in a voice channel
            current_channel = self.voice_manager.get_current_channel(ctx.guild.id)
            if not current_channel:
                await ctx.send("❌ I'm not in a voice channel. Use `!join` first.")
                return

            # Speak the message
            await self.voice_manager.speak_message(ctx.guild.id, text, priority=True)

            embed = discord.Embed(
                title="🗣️ Speaking",
                description=f"Speaking: \"{text[:100]}{'...' if len(text) > 100 else ''}\"",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)

        except (LLMConnectionError, LLMTimeoutError, LLMRateLimitError) as e:
            await ctx.send(f"❌ Voice service error: {e}")
        except Exception as e:
            self.logger.error(f"Error in speak command: {e}")
            await ctx.send("❌ Failed to speak text. Please try again.")

    async def _toggle_listening_handler(self, ctx):
        """Handle toggle listening command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id
        is_listening = self.voice_manager.is_listening(guild_id)

        if is_listening:
            await self.voice_manager.stop_listening(guild_id)
            embed = discord.Embed(
                title="🔇 Listening Disabled",
                description="I'm no longer listening for voice messages.",
                color=discord.Color.red(),
            )
        else:
            await self.voice_manager.start_listening(guild_id)
            embed = discord.Embed(
                title="🎧 Listening Enabled",
                description="I'm now listening for voice messages!",
                color=discord.Color.green(),
            )

        await ctx.send(embed=embed)

    async def _voice_settings_handler(self, ctx):
        """Handle voice settings command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        embed = discord.Embed(title="🎵 Voice Settings", color=discord.Color.blue())

        # Bot voice settings
        bot_settings = []
        bot_settings.append(f"Auto-join: {'✅' if self.voice_manager.auto_join_enabled else '❌'}")
        bot_settings.append(
            f"Voice responses: {'✅' if self.voice_manager.voice_response_enabled else '❌'}"
        )
        bot_settings.append(
            f"Voice listening: {'✅' if self.voice_manager.voice_listening_enabled else '❌'}"
        )
        bot_settings.append(
            f"Voice streaming: {'✅' if self.voice_manager.voice_streaming_enabled else '❌'}"
        )
        bot_settings.append(f"Max audio length: {self.voice_manager.max_audio_length}s")
        bot_settings.append(f"Response delay: {self.voice_manager.response_delay}s")

        embed.add_field(name="🤖 Bot Settings", value="\n".join(bot_settings), inline=False)

        # ElevenLabs settings
        try:
            elevenlabs_settings = self.voice_manager.elevenlabs.get_current_settings()
            elevenlabs_info = []
            elevenlabs_info.append(f"Voice ID: {elevenlabs_settings['voice_id']}")
            elevenlabs_info.append(f"Stability: {elevenlabs_settings['stability']}")
            elevenlabs_info.append(f"Similarity: {elevenlabs_settings['similarity_boost']}")
            elevenlabs_info.append(f"Style: {elevenlabs_settings['style']}")
            elevenlabs_info.append(
                f"Speaker boost: {'✅' if elevenlabs_settings['use_speaker_boost'] else '❌'}"
            )
            elevenlabs_info.append(f"Format: {elevenlabs_settings['output_format']}")

            embed.add_field(
                name="🎤 ElevenLabs Settings", value="\n".join(elevenlabs_info), inline=False
            )
        except Exception as e:
            embed.add_field(
                name="🎤 ElevenLabs Settings",
                value=f"❌ Error retrieving settings: {e}",
                inline=False,
            )

        await ctx.send(embed=embed)

    async def _voice_test_handler(self, ctx):
        """Handle voice test command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        embed = discord.Embed(
            title="🎵 Voice Test",
            description="Testing voice functionality...",
            color=discord.Color.blue(),
        )

        try:
            # Test ElevenLabs TTS functionality (more reliable than voices endpoint)
            try:
                # Test TTS with a short message
                test_audio = await self.voice_manager.elevenlabs.text_to_speech(
                    "Voice test successful", voice_id=self.voice_manager.elevenlabs.default_voice_id
                )
                tts_working = len(test_audio) > 0
            except Exception as e:
                self.logger.debug(f"TTS test failed: {e}")
                tts_working = False

            if tts_working:
                embed.add_field(
                    name="✅ ElevenLabs TTS",
                    value="Text-to-speech is working correctly",
                    inline=False,
                )
                embed.color = discord.Color.green()
            else:
                embed.add_field(
                    name="❌ ElevenLabs TTS", value="Text-to-speech is not working", inline=False
                )
                embed.color = discord.Color.red()

        except Exception as e:
            self.logger.error(f"Voice test failed: {e}")
            embed = discord.Embed(
                title="❌ Voice Test Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red(),
            )

        await ctx.send(embed=embed)

    async def _voice_chat_test_handler(self, ctx):
        """Handle voice chat test command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Check if user is in a voice channel
        if not (
            isinstance(ctx.author, discord.Member) and ctx.author.voice and ctx.author.voice.channel
        ):
            await ctx.send("❌ You need to be in a voice channel to test voice chat.")
            return

        user_channel = ctx.author.voice.channel
        bot_channel = self.voice_manager.get_current_channel(ctx.guild.id)

        if not bot_channel:
            await ctx.send("❌ I'm not in a voice channel. Use `!join` first.")
            return

        if bot_channel.id != user_channel.id:
            await ctx.send(
                f"❌ We're not in the same voice channel. I'm in {bot_channel.name}, you're in {user_channel.name}."
            )
            return

        # Send text response and voice response
        text_response = f"🎤 **Voice Chat Test!** Hi {ctx.author.display_name}! This is a test of the voice chat feature. You should hear this message spoken in the voice channel!"
        await ctx.send(text_response)

        # Send voice response
        try:
            voice_response = f"Voice chat test successful! Hi {ctx.author.display_name}, I can speak in voice channel while you're here. The voice chat feature is working!"
            await self.voice_manager.speak_message(ctx.guild.id, voice_response, priority=True)
            await ctx.send(
                "✅ **Voice chat test complete!** If you heard me speak, the feature is working correctly."
            )

        except Exception as e:
            self.logger.error(f"Voice chat test failed: {e}")
            await ctx.send(f"❌ **Voice chat test failed:** {str(e)}")

    async def _voice_connection_status_handler(self, ctx):
        """Handle voice connection status command"""
        if not self.voice_manager:
            await ctx.send("❌ Voice functionality is not available.")
            return

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id
        voice_state = self.voice_manager.get_voice_state(guild_id)

        embed = discord.Embed(title="🎵 Voice Connection Status", color=discord.Color.blue())

        # Connection status
        is_connected = voice_state.voice_client and voice_state.voice_client.is_connected()
        connection_status = "🟢 Connected" if is_connected else "🔴 Disconnected"

        embed.add_field(name="🔗 Connection Status", value=connection_status, inline=True)

        # Current channel
        current_channel = self.voice_manager.get_current_channel(guild_id)
        channel_name = current_channel.name if current_channel else "None"

        embed.add_field(name="📍 Current Channel", value=channel_name, inline=True)

        # Listening status
        is_listening = self.voice_manager.is_listening(guild_id)
        listening_status = "✅ Active" if is_listening else "❌ Inactive"

        embed.add_field(name="🎧 Voice Listening", value=listening_status, inline=True)

        # Voice client details
        if voice_state.voice_client:
            embed.add_field(
                name="🎵 Voice Client",
                value=f"Playing: {'Yes' if voice_state.voice_client.is_playing() else 'No'}\n"
                f"Connected: {'Yes' if voice_state.voice_client.is_connected() else 'No'}",
                inline=True,
            )

        # Participants
        participants = self.voice_manager.get_participants(guild_id)
        participant_list = (
            "\n".join([f"• {name}" for name in participants.values()]) if participants else "None"
        )

        embed.add_field(
            name="👥 Voice Participants",
            value=(
                participant_list[:1024]
                if len(participant_list) <= 1024
                else participant_list[:1021] + "..."
            ),
            inline=False,
        )

        # Keepalive settings (from environment)
        keepalive_interval = os.getenv("VOICE_KEEPALIVE_INTERVAL", "300")
        heartbeat_interval = os.getenv("VOICE_HEARTBEAT_INTERVAL", "30")
        max_reconnects = os.getenv("VOICE_MAX_RECONNECT_ATTEMPTS", "3")

        embed.add_field(
            name="⚙️ Keepalive Settings",
            value=f"Keepalive interval: {keepalive_interval}s\n"
            f"Heartbeat check: {heartbeat_interval}s\n"
            f"Max reconnects: {max_reconnects}",
            inline=True,
        )

        # Connection health
        if is_connected:
            health_status = "🟢 Healthy - Keepalive active"
        else:
            health_status = "🔴 Disconnected - Check logs"

        embed.add_field(name="💚 Connection Health", value=health_status, inline=True)

        embed.set_footer(text="Use !join to connect • Keepalive prevents idle timeouts")

        await ctx.send(embed=embed)

    async def _voice_help_handler(self, ctx):
        """Handle voice help command"""
        from src.utils.bot_name_utils import get_normalized_bot_name_from_env
        embed = discord.Embed(
            title="🎵 Voice Commands Help",
            description="Available voice commands and features",
            color=discord.Color.blue(),
        )

        # Bot name requirement info
        bot_name = get_normalized_bot_name_from_env()
        if bot_name and bot_name != "unknown":
            name_suffix = f" {bot_name}"
            embed.add_field(
                name="🤖 Bot Name Requirement",
                value=f"Commands must include bot name: `{bot_name}`\n"
                f"**Example:** `!join {bot_name}` or `!speak {bot_name} hello world`",
                inline=False,
            )
        else:
            name_suffix = ""

        commands_info = [
            (f"`!join{name_suffix} [channel]`", "Join voice channel"),
            (f"`!leave{name_suffix}`", "Leave voice channel"),
            (f"`!speak{name_suffix} <text>`", "Make bot speak text"),
            (f"`!voice_connection_status{name_suffix}`", "Show connection health"),
            (f"`!voice_test{name_suffix}`", "Test voice functionality"),
            (f"`!voice_help{name_suffix}`", "Show this help"),
        ]

        admin_commands = [
            (f"`!voice_toggle_listening{name_suffix}`", "Toggle voice listening"),
            (f"`!voice_settings{name_suffix}`", "Show detailed settings"),
        ]

        for cmd, desc in commands_info:
            embed.add_field(name=cmd, value=desc, inline=False)

        embed.add_field(
            name="👑 Admin Commands",
            value="\n".join([f"{cmd} - {desc}" for cmd, desc in admin_commands]),
            inline=False,
        )

        embed.add_field(
            name="💡 Voice Chat Features",
            value="🎯 **Text-to-Voice Chat (ACTIVE)**\n"
            "• @mention bot while in voice channel\n"
            "• Get text response + voice response ✅\n"
            "• Full LLM conversation with voice output ✅\n\n"
            "🔮 **Voice-to-Voice Chat (COMING SOON)**\n"
            "• Speak directly to the bot\n"
            "• Bot hears and responds with voice\n"
            "• Natural voice conversation\n\n"
            "📝 **How to use now:**\n"
            "1. `!join` - Bot joins voice channel\n"
            "2. @mention bot with text message\n"
            "3. Bot responds in text + voice!",
            inline=False,
        )

        await ctx.send(embed=embed)
