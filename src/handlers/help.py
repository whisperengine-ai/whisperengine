"""
Help command handler for Discord bot
Provides comprehensive help and command listings
"""

import logging

import discord

logger = logging.getLogger(__name__)


class HelpCommandHandlers:
    """Handles help-related commands"""

    def __init__(
        self,
        bot,
        bot_name,
        voice_manager,
        voice_support_enabled,
        personality_profiler,
        is_demo_bot=False,
    ):
        self.bot = bot
        self.bot_name = bot_name
        self.voice_manager = voice_manager
        self.voice_support_enabled = voice_support_enabled
        self.personality_profiler = personality_profiler
        self.is_demo_bot = is_demo_bot

    def register_commands(self, bot_name_filter, is_admin):
        """Register help commands"""

        # Capture self reference for nested functions
        help_handler_instance = self

        # Standard help command (following Discord conventions - works without bot name)
        @self.bot.command(name="help")
        async def help_command(ctx):
            """Show all available bot commands (standard Discord help command)"""
            logger.debug(f"Help command called by {ctx.author.name} - standard Discord help")
            await help_handler_instance._custom_help_handler(ctx, is_admin)

        # Alternative help commands with bot name filtering for consistency
        @self.bot.command(name="commands", aliases=["help_custom"])
        @bot_name_filter()
        async def custom_help(ctx):
            """Show all available bot commands with descriptions"""
            await help_handler_instance._detailed_help_handler(ctx, is_admin)

        # Short alias following Discord conventions
        @self.bot.command(name="h")
        async def help_short(ctx):
            """Quick help command (short alias)"""
            await help_handler_instance._custom_help_handler(ctx, is_admin)

        # Discovery help commands (alternative names for discoverability)
        @self.bot.command(name="bot_help", aliases=["bothelp"])
        async def discovery_help(ctx):
            """Show bot commands (works without bot name for discovery)"""
            logger.debug(f"Discovery help command called by {ctx.author.name}")
            await help_handler_instance._discovery_help_handler(ctx, is_admin)

        @self.bot.command(name="bot_commands", aliases=["botcommands"])
        async def discovery_commands(ctx):
            """Show bot commands (works without bot name for discovery)"""
            await help_handler_instance._discovery_help_handler(ctx, is_admin)

    async def _custom_help_handler(self, ctx, is_admin):
        """Handle main help command - minimal and actually useful"""
        bot_name_display = self.bot_name.title() if self.bot_name else "WhisperEngine"
        name_suffix = f" {self.bot_name}" if self.bot_name else ""
        
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} Commands",
            description="Essential commands only:",
            color=0x3498DB,
        )

        # Core commands that actually work
        commands = [
            f"`!ping{name_suffix}` - Test connectivity",
            f"`!bot_status{name_suffix}` - Bot health check",
            f"`!join{name_suffix}` - Join voice channel",
            f"`!leave{name_suffix}` - Leave voice channel"
        ]
        
        # No more hidden admin commands - all enterprise bloat removed!

        embed.add_field(
            name="Available Commands", 
            value="\n".join(commands), 
            inline=False
        )
        
        if self.bot_name and ctx.guild:
            embed.set_footer(text=f"💡 Tip: Commands need '{self.bot_name}' in servers, optional in DMs")

        await ctx.send(embed=embed)

    async def _detailed_help_handler(self, ctx, is_admin):
        """Handle detailed help command - just redirect to simple help"""
        # No need for detailed help anymore - everything is streamlined
        await self._custom_help_handler(ctx, is_admin)

    async def _discovery_help_handler(self, ctx, is_admin):
        """Handle discovery help commands - simplified version for users who don't know bot name"""
        bot_name_display = self.bot_name.title() if self.bot_name else "WhisperEngine"
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} - Quick Help",
            description=f"Welcome! Here's how to use **{bot_name_display}**:",
            color=0x3498DB,
        )

        # Demo bot warning (if applicable)
        if self.is_demo_bot:
            embed.add_field(
                name="⚠️ Demo Bot Notice",
                value="**This is a demo/testing bot:**\n"
                "• Your conversations may be reviewed by developers for troubleshooting\n"
                "• All data is regularly purged - don't expect production-level persistence\n"
                "• For production use, please use our main bot instance",
                inline=False,
            )

        # Bot discovery explanation
        if self.bot_name and ctx.guild:
            embed.add_field(
                name="🎯 Bot Discovery",
                value=f"**This bot responds to:** `{self.bot_name}` or `whisperengine`\n"
                f"**Standard Discord help:** `!help` (works without bot name)\n"
                f"**Targeted help:** `!commands {self.bot_name}` or `!help {self.bot_name}`\n"
                f"**Quick test:** Try `!ping {self.bot_name}` or mention @{bot_name_display}",
                inline=False,
            )
        elif self.bot_name:  # In DM
            embed.add_field(
                name="🎯 Bot Discovery",
                value=f"**Bot name:** `{self.bot_name}` (optional in DMs)\n"
                f"**Standard help:** `!help` (works everywhere)\n"
                f"**Quick start:** Just say hello or try `!ping`",
                inline=False,
            )
        else:
            embed.add_field(
                name="🎯 Bot Discovery",
                value="**This bot responds to:** `whisperengine`\n"
                "**Standard help:** `!help` (works without bot name)\n"
                "**Quick start:** Try `!ping whisperengine` or mention the bot",
                inline=False,
            )

        # Essential commands
        name_suffix = f" {self.bot_name}" if self.bot_name else " whisperengine"
        essential_commands = [
            ("!help", "Show complete command list (standard Discord command)"),
            (f"!ping{name_suffix}", "Test if bot is responding"),
            (f"!bot_status{name_suffix}", "Check bot health and status"),
        ]

        essential_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in essential_commands])
        embed.add_field(name="✨ Essential Commands", value=essential_text, inline=False)

        # Quick start guide
        if ctx.guild:
            quick_start = (
                f"1. Try: `!help` (standard Discord help)\n"
                f"2. Test bot: `!ping {self.bot_name or 'whisperengine'}`\n"
                "3. Chat by mentioning the bot\n"
                f"4. Use voice with `!join {self.bot_name or 'whisperengine'}`"
            )
        else:
            quick_start = (
                "1. Try: `!help` (works everywhere)\n"
                "2. Test bot: `!ping` (bot name optional in DMs)\n"
                "3. Just type messages to chat\n"
                "4. Use `!join` for voice features"
            )

        embed.add_field(name="⚡ Quick Start", value=quick_start, inline=False)
        embed.set_footer(
            text="Standard Discord help: !help • This discovery help also works without bot name"
        )
        await ctx.send(embed=embed)
