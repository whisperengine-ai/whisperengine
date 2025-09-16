"""
Discord Voice Commands for managing voice channel operations
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
from typing import Optional
from functools import wraps

from src.voice.voice_manager import DiscordVoiceManager
from src.llm.elevenlabs_client import ElevenLabsClient
from src.utils.exceptions import LLMError, LLMConnectionError, LLMTimeoutError, LLMRateLimitError


def should_bot_respond_voice(ctx: commands.Context) -> bool:
    """
    Check if this bot instance should respond to the voice command.
    Returns True if:
    1. No bot name filter is configured, OR
    2. The command message mentions this bot's name, OR
    3. The command is sent via DM
    """
    bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()

    if not bot_name:  # No name filter configured, respond to all
        return True

    if not ctx.guild:  # Always respond to DMs
        return True

    # Check if the message contains the bot's name (case insensitive)
    message_content = ctx.message.content.lower()
    return bot_name in message_content


def voice_bot_name_filter():
    """
    Decorator to add bot name filtering to voice commands.
    Commands will only execute if should_bot_respond_voice returns True.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if should_bot_respond_voice(ctx):
                return await func(self, ctx, *args, **kwargs)
            # If bot shouldn't respond, do nothing (no error message)
            return

        return wrapper

    return decorator


class VoiceCommands(commands.Cog):
    """Discord commands for voice functionality"""

    def __init__(self, bot: commands.Bot, voice_manager: DiscordVoiceManager):
        self.bot = bot
        self.voice_manager = voice_manager
        self.logger = logging.getLogger(__name__)

    @commands.command(name="join", aliases=["j"])
    @voice_bot_name_filter()
    async def join_voice(self, ctx: commands.Context, *, channel_name: Optional[str] = None):
        """
        Join a voice channel
        Usage: !join [channel_name]
        If no channel specified, joins the user's current voice channel
        """
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

        # Ensure we have a VoiceChannel
        if not isinstance(target_channel, discord.VoiceChannel):
            await ctx.send("❌ Invalid voice channel type.")
            return

        # Check permissions
        if not target_channel.permissions_for(ctx.guild.me).connect:
            await ctx.send(f"❌ I don't have permission to join '{target_channel.name}'.")
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

    @commands.command(name="leave", aliases=["l", "disconnect"])
    @voice_bot_name_filter()
    async def leave_voice(self, ctx: commands.Context):
        """
        Leave the current voice channel
        Usage: !leave
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not self.voice_manager.is_connected(ctx.guild.id):
            await ctx.send("❌ I'm not connected to a voice channel.")
            return

        # Get current channel for farewell message
        current_channel = self.voice_manager.get_current_channel(ctx.guild.id)
        channel_name = current_channel.name if current_channel else "the voice channel"

        # Say goodbye if voice responses are enabled
        if self.voice_manager.voice_response_enabled and current_channel:
            goodbye = f"Goodbye everyone! Leaving {channel_name}."
            await self.voice_manager.speak_message(ctx.guild.id, goodbye, priority=True)
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

    @commands.command(name="speak", aliases=["say", "tts"])
    @voice_bot_name_filter()
    async def speak_text(self, ctx: commands.Context, *, text: str):
        """
        Make the bot speak text in voice channel
        Usage: !speak <text>
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not self.voice_manager.is_connected(ctx.guild.id):
            await ctx.send("❌ I'm not connected to a voice channel. Use `!join` first.")
            return

        if not text.strip():
            await ctx.send("❌ Please provide text to speak.")
            return

        if len(text) > 500:
            await ctx.send("❌ Text is too long. Please keep it under 500 characters.")
            return

        try:
            # Show typing indicator
            async with ctx.typing():
                await self.voice_manager.speak_message(ctx.guild.id, text)

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

    @commands.command(name="voice_toggle_listening", aliases=["vtl", "toggle_listen"])
    @commands.has_permissions(manage_guild=True)
    async def toggle_listening(self, ctx: commands.Context):
        """
        Toggle voice listening on/off (Admin only)
        Usage: !voice_toggle_listening
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id

        if not self.voice_manager.is_connected(guild_id):
            await ctx.send("❌ I'm not connected to a voice channel.")
            return

        if self.voice_manager.is_listening(guild_id):
            await self.voice_manager.stop_listening(guild_id)
            embed = discord.Embed(
                title="🔇 Listening Disabled",
                description="I'm no longer listening for voice messages.",
                color=discord.Color.orange(),
            )
        else:
            await self.voice_manager.start_listening(guild_id)
            embed = discord.Embed(
                title="🎧 Listening Enabled",
                description="I'm now listening for voice messages!",
                color=discord.Color.green(),
            )

        await ctx.send(embed=embed)

    @commands.command(name="voice_settings", aliases=["vset"])
    @commands.has_permissions(manage_guild=True)
    async def voice_settings(self, ctx: commands.Context):
        """
        Show detailed voice settings (Admin only)
        Usage: !voice_settings
        """
        # Get ElevenLabs settings
        elevenlabs_settings = self.voice_manager.elevenlabs.get_voice_settings()

        embed = discord.Embed(title="⚙️ Voice Settings", color=discord.Color.blue())

        # Bot settings
        bot_settings = []
        bot_settings.append(f"Auto-join: {'✅' if self.voice_manager.auto_join_enabled else '❌'}")
        bot_settings.append(
            f"Voice responses: {'✅' if self.voice_manager.voice_response_enabled else '❌'}"
        )
        bot_settings.append(
            f"Voice listening: {'✅' if self.voice_manager.voice_listening_enabled else '❌'}"
        )
        bot_settings.append(f"Max audio length: {self.voice_manager.max_audio_length}s")
        bot_settings.append(f"Response delay: {self.voice_manager.response_delay}s")

        embed.add_field(name="🤖 Bot Settings", value="\n".join(bot_settings), inline=False)

        # ElevenLabs settings
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

        await ctx.send(embed=embed)

    @commands.command(name="voice_test", aliases=["vtest"])
    async def voice_test(self, ctx: commands.Context):
        """
        Test voice functionality
        Usage: !voice_test
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not self.voice_manager.is_connected(ctx.guild.id):
            await ctx.send("❌ I'm not connected to a voice channel. Use `!join` first.")
            return

        try:
            test_message = (
                f"Voice test from {ctx.author.display_name}. All systems are working correctly!"
            )

            async with ctx.typing():
                await self.voice_manager.speak_message(ctx.guild.id, test_message, priority=True)

            embed = discord.Embed(
                title="✅ Voice Test",
                description="Voice test completed successfully!",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)

        except Exception as e:
            self.logger.error(f"Voice test failed: {e}")
            embed = discord.Embed(
                title="❌ Voice Test Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.command(name="voice_chat_test", aliases=["vctest"])
    async def voice_chat_test(self, ctx: commands.Context):
        """
        Test the voice chat feature - sends a test response with voice
        Usage: !voice_chat_test
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Check if user is in voice channel
        if (
            not isinstance(ctx.author, discord.Member)
            or not ctx.author.voice
            or not ctx.author.voice.channel
        ):
            await ctx.send("❌ You need to be in a voice channel to test voice chat.")
            return

        # Check if bot is in same voice channel
        bot_channel = self.voice_manager.get_current_channel(ctx.guild.id)
        user_channel = ctx.author.voice.channel

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

    @commands.command(name="voice_connection_status", aliases=["vcs"])
    async def voice_connection_status(self, ctx: commands.Context):
        """
        Show detailed voice connection status and keepalive information
        Usage: !voice_connection_status
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id
        voice_state = self.voice_manager.get_voice_state(guild_id)

        embed = discord.Embed(title="🔍 Voice Connection Status", color=discord.Color.blue())

        # Connection status
        is_connected = self.voice_manager.is_connected(guild_id)
        connection_status = "✅ Connected" if is_connected else "❌ Disconnected"

        embed.add_field(name="🔗 Connection", value=connection_status, inline=True)

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
        import os

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

    @commands.command(name="voice_help", aliases=["vhelp"])
    @voice_bot_name_filter()
    async def voice_help(self, ctx: commands.Context):
        """
        Show voice commands help
        Usage: !voice_help
        """
        bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
        bot_name_display = bot_name.title() if bot_name else "Bot"
        name_suffix = f" {bot_name}" if bot_name else ""

        embed = discord.Embed(
            title=f"🎤 {bot_name_display} Voice Commands",
            description=f"Available voice commands for **{bot_name_display}**:",
            color=discord.Color.blue(),
        )

        # Add name-based filtering explanation if bot name is configured
        if bot_name:
            embed.add_field(
                name="🎯 Command Targeting",
                value=f"**Important:** Include `{bot_name}` in your commands to target this bot specifically.\n"
                f"**Example:** `!join {bot_name}` or `!speak {bot_name} hello world`",
                inline=False,
            )

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

    # Error handling
    @join_voice.error
    @leave_voice.error
    @speak_text.error
    @toggle_listening.error
    async def voice_command_error(self, ctx: commands.Context, error):
        """Handle voice command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing required argument. Use `!voice_help` for usage information.")
        else:
            self.logger.error(f"Voice command error: {error}")
            await ctx.send("❌ An error occurred. Please try again.")


async def setup(bot: commands.Bot, voice_manager: DiscordVoiceManager):
    """Setup function to add the voice commands cog"""
    await bot.add_cog(VoiceCommands(bot, voice_manager))
