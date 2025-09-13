"""
Help command handler for Discord bot
Provides comprehensive help and command listings
"""
import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class HelpCommandHandlers:
    """Handles help-related commands"""
    
    def __init__(self, bot, bot_name, voice_manager, voice_support_enabled, VOICE_AVAILABLE, personality_profiler, is_demo_bot=False):
        self.bot = bot
        self.bot_name = bot_name
        self.voice_manager = voice_manager
        self.voice_support_enabled = voice_support_enabled
        self.VOICE_AVAILABLE = VOICE_AVAILABLE
        self.personality_profiler = personality_profiler
        self.is_demo_bot = is_demo_bot
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register help commands"""
        
        # Capture self reference for nested functions
        help_handler_instance = self
        
        # Standard help command (following Discord conventions - works without bot name)
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show all available bot commands (standard Discord help command)"""
            logger.debug(f"Help command called by {ctx.author.name} - standard Discord help")
            await help_handler_instance._custom_help_handler(ctx, is_admin)
        
        # Alternative help commands with bot name filtering for consistency
        @self.bot.command(name='commands', aliases=['help_custom'])
        @bot_name_filter()
        async def custom_help(ctx):
            """Show all available bot commands with descriptions"""
            await help_handler_instance._detailed_help_handler(ctx, is_admin)
        
        # Short alias following Discord conventions
        @self.bot.command(name='h')
        async def help_short(ctx):
            """Quick help command (short alias)"""
            await help_handler_instance._custom_help_handler(ctx, is_admin)
        
        # Discovery help commands (alternative names for discoverability)
        @self.bot.command(name='bot_help', aliases=['bothelp'])
        async def discovery_help(ctx):
            """Show bot commands (works without bot name for discovery)"""
            logger.debug(f"Discovery help command called by {ctx.author.name}")
            await help_handler_instance._discovery_help_handler(ctx, is_admin)
        
        @self.bot.command(name='bot_commands', aliases=['botcommands'])
        async def discovery_commands(ctx):
            """Show bot commands (works without bot name for discovery)"""
            await help_handler_instance._discovery_help_handler(ctx, is_admin)
    
    async def _custom_help_handler(self, ctx, is_admin):
        """Handle main help command - short and user-friendly"""
        bot_name_display = self.bot_name.title() if self.bot_name else "WhisperEngine"
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} - Quick Help",
            description=f"Hi! I'm **{bot_name_display}**, an AI companion with voice, memory, and conversation features.",
            color=0x3498db
        )
        
        # Demo bot warning (if applicable)
        if self.is_demo_bot:
            embed.add_field(
                name="⚠️ Demo Bot Notice",
                value="**This is a demo/testing bot:**\n"
                      "• Your conversations may be reviewed by developers for troubleshooting\n"
                      "• All data is regularly purged - don't expect production-level persistence\n"
                      "• For production use, please use our main bot instance",
                inline=False
            )
        
        # Quick getting started
        name_suffix = f" {self.bot_name}" if self.bot_name else " whisperengine"
        
        if ctx.guild:  # In a server
            embed.add_field(
                name="🚀 Getting Started",
                value=f"• **Chat:** Mention me or send a DM to talk\n"
                      f"• **Quick test:** `!ping{name_suffix}`\n"
                      f"• **Voice chat:** `!join{name_suffix}` to join your voice channel",
                inline=False
            )
            if self.bot_name:
                embed.add_field(
                    name="🎯 Command Usage",
                    value=f"Most commands need `{self.bot_name}` to target me specifically.\n"
                          f"Example: `!join {self.bot_name}` or `!ping {self.bot_name}`",
                    inline=False
                )
        else:  # In a DM
            embed.add_field(
                name="🚀 Getting Started", 
                value=f"• **Chat:** Just type messages - no commands needed!\n"
                      f"• **Quick test:** `!ping` (bot name optional in DMs)\n"
                      f"• **Voice chat:** `!join` to connect to voice",
                inline=False
            )
        
        # Essential commands only
        essential_commands = [
            (f"`!ping{name_suffix}`", "Test if I'm responding"),
            (f"`!commands{name_suffix}`", "� **See all commands** (detailed list)"),
        ]
        
        # Add voice command if available
        if self.voice_manager and self.voice_support_enabled:
            essential_commands.append((f"`!join{name_suffix}`", "🎤 Join your voice channel"))
        
        essential_text = "\n".join([f"{cmd} - {desc}" for cmd, desc in essential_commands])
        embed.add_field(name="⚡ Essential Commands", value=essential_text, inline=False)
        
        # Feature highlights
        features = []
        features.append("💬 **AI Chat** - Natural conversation with memory")
        features.append("💾 **Memory** - Remembers facts about you across sessions")
        
        if self.voice_manager and self.voice_support_enabled:
            features.append("🎤 **Voice** - Text-to-speech and voice chat")
        
        if self.personality_profiler:
            features.append("🧠 **Personality** - Adapts to your communication style")
        
        features.append("� **Privacy** - Your data stays local and secure")
        
        embed.add_field(
            name="✨ Key Features",
            value="\n".join(features),
            inline=False
        )
        
        embed.set_footer(text=f"For all commands: !commands{name_suffix} • Quick alias: !h")
        
        await ctx.send(embed=embed)
    
    async def _detailed_help_handler(self, ctx, is_admin):
        """Handle detailed help command with complete command listing"""
        bot_name_display = self.bot_name.title() if self.bot_name else "Bot"
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} Commands",
            description=f"Complete command reference for **{bot_name_display}**:",
            color=0x3498db
        )
        
        # Demo bot warning (if applicable)
        if self.is_demo_bot:
            embed.add_field(
                name="⚠️ Demo Bot Notice",
                value="**This is a demo/testing bot:**\n"
                      "• Your conversations may be reviewed by developers for troubleshooting\n"
                      "• All data is regularly purged - don't expect production-level persistence\n"
                      "• For production use, please use our main bot instance",
                inline=False
            )
        
        # Add name-based filtering explanation if bot name is configured
        if self.bot_name:
            if ctx.guild:  # In a server/guild
                embed.add_field(
                    name="🎯 Command Targeting (Server)",
                    value=f"**Most commands require:** `{self.bot_name}` to target this bot specifically.\n"
                          f"**Example:** `!ping {self.bot_name}` or `!join {self.bot_name}`\n"
                          f"**Fallback:** Commands with `whisperengine` also work.\n"
                          f"**Exception:** `!help` and `!h` work without bot name (Discord standard).\n"
                          f"*All examples below include the bot name for easy copy-paste.*",
                    inline=False
                )
            else:  # In a DM
                embed.add_field(
                    name="🎯 Command Targeting (DM)",
                    value=f"**Good news:** Bot name is **optional** in DMs!\n"
                          f"**Copy-paste ready:** `!ping {self.bot_name}` (examples below include bot name)\n"
                          f"**Also works:** `!ping` without the bot name\n"
                          f"*Examples show bot name for easy copy-paste, but it's optional here.*",
                    inline=False
                )
        
        # Basic Commands
        # Always show bot name in examples for easy copy-paste, but explain context
        name_suffix = f" {self.bot_name}" if self.bot_name else " whisperengine"
            
        basic_commands = [
            (f"!ping{name_suffix}", "Simple ping/pong test"),
            (f"!bot_status{name_suffix}", "Check Discord bot status and connection health"),
            (f"!llm_status{name_suffix}", "Check if the LLM server is running"),
            (f"!voice_status{name_suffix}", "Check voice support status and configuration"),
            (f"!clear_chat{name_suffix}", "Clear conversation history in this channel"),
            (f"!cache_stats{name_suffix}", "Show conversation cache statistics")
        ]
        
        basic_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in basic_commands])
        embed.add_field(name="📝 Basic Commands", value=basic_text, inline=False)
        
        # AI Chat Information
        if ctx.guild:  # In a server
            chat_info = "💬 **Chat with the bot:**\n• Mention the bot in any channel to chat\n• Use commands with bot name for specific actions\n• Bot responds to mentions and targeted commands"
        else:  # In a DM
            chat_info = "💬 **Chat directly with the bot:**\n• Send a DM to chat naturally\n• No commands needed - just start talking!\n• Commands work with or without bot name (shown with name for copy-paste)"
            
        embed.add_field(
            name="🧠 AI Chat", 
            value=chat_info, 
            inline=False
        )
        
        # Vision Commands
        vision_commands = [
            (f"!vision_status{name_suffix}", "Check if the bot supports image processing"),
            (f"!test_image{name_suffix}", "Test image processing (attach an image to the command)"),
        ]
        
        vision_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in vision_commands])
        embed.add_field(name="🖼️ Image Processing", value=vision_text, inline=False)
        
        # Voice Commands (if available and enabled)
        if self.voice_manager and self.voice_support_enabled:
            voice_commands = [
                (f"!join{name_suffix} [channel]", "Join voice channel (aliases: !j)"),
                (f"!leave{name_suffix}", "Leave voice channel (aliases: !l, !disconnect)"),
                (f"!speak{name_suffix} <text>", "Make bot speak text (aliases: !say, !tts)"),
                (f"!voice_test{name_suffix}", "Test voice functionality (aliases: !vtest)"),
                (f"!voice_chat_test{name_suffix}", "Test voice chat functionality (aliases: !vctest)"),
                (f"!voice_connection_status{name_suffix}", "Show voice connection status (aliases: !vcs)"),
                (f"!voice_help{name_suffix}", "Show voice commands help (aliases: !vhelp)"),
                ("!voice_toggle_listening", "Toggle voice listening on/off (Admin, aliases: !vtl, !toggle_listen)"),
                ("!voice_settings", "Show detailed voice settings (Admin, aliases: !vset)")
            ]
            
            voice_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in voice_commands])
            embed.add_field(name="🎤 Voice Commands", value=voice_text, inline=False)
        elif self.VOICE_AVAILABLE and not self.voice_support_enabled:
            embed.add_field(
                name="🎤 Voice Commands", 
                value="❌ **Disabled** - Set `VOICE_SUPPORT_ENABLED=true` in .env to enable voice features", 
                inline=False
            )
        else:
            embed.add_field(
                name="🎤 Voice Commands", 
                value="❌ **Unavailable** - Install voice dependencies (PyNaCl, ElevenLabs) to enable", 
                inline=False
            )
        
        # Memory Management Commands
        memory_commands = [
            (f"!add_fact{name_suffix} <fact>", "Add a personal fact to memory"),
            (f"!list_facts{name_suffix}", "View all stored facts about you"),
            (f"!remove_fact{name_suffix} <search>", "Search and remove facts (direct removal)"),
            (f"!remove_fact_by_number{name_suffix} <num> <search>", "Remove a specific fact by number"),
            (f"!my_memory{name_suffix}", "See what the bot remembers about you"),
            (f"!sync_check{name_suffix}", "Check if your DM conversation is in sync with stored memory"),
            (f"!forget_me{name_suffix}", "Delete all stored memories about you"),
            ("!import_history [limit]", "Import existing conversation history into ChromaDB"),
            (f"!followup_settings{name_suffix} [on|off|status]", "🧪 Experimental: Manage follow-up messages"),
        ]
        
        memory_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in memory_commands])
        embed.add_field(name="💾 Memory Management", value=memory_text, inline=False)
        
        # AI Analysis Commands
        analysis_commands = []
        if self.personality_profiler:
            analysis_commands.append((f"!personality{name_suffix} [user]", "🧠 View personality profile (aliases: !profile, !my_personality)"))
        
        if analysis_commands:
            analysis_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in analysis_commands])
            embed.add_field(name="🧠 AI Analysis", value=analysis_text, inline=False)
        
        # Data Control Commands
        data_commands = [
            ("!create_backup", "Create a backup of the memory system (admin only)"),
            ("!list_backups", "List available backups (admin only)")
        ]
        
        data_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in data_commands])
        embed.add_field(name="🗑️ Data Control", value=data_text, inline=False)
        
        # Privacy Commands
        privacy_commands = [
            ("!privacy", "Show privacy information and data handling"),
            ("!privacy_level [level]", "View or set your privacy level"),
            ("!privacy_audit", "Audit your stored data"),
            ("!privacy_help", "Get detailed privacy help")
        ]
        
        privacy_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in privacy_commands])
        embed.add_field(name="🔒 Privacy Commands", value=privacy_text, inline=False)
        
        # Health and Stats Commands
        health_commands = [
            ("!health", "Show system health status (admin only)"),
            ("!memory_stats", "Show memory system statistics (admin only)")
        ]
        
        health_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in health_commands])
        embed.add_field(name="📊 Health & Stats", value=health_text, inline=False)
        
        # Admin Commands (if user is admin)
        if is_admin(ctx):
            admin_commands = [
                ("!debug [on|off|status]", "Toggle debug logging on/off or check status"),
                ("!schedule_followup @user [hours]", "Schedule a follow-up message for a user"),
                ("!job_status [job_id]", "Check job scheduler status or specific job"),
                ("!system_status", "Show comprehensive system status"),
                ("!emotional_intelligence", "Show emotional intelligence system status (aliases: !ei_status, !emotional_status)"),
                ("!add_global_fact <fact>", "Add a global fact about the world or relationships"),
                ("!list_global_facts", "List all global facts"),
                ("!remove_global_fact <search_term>", "Search and remove global facts"),
                ("!remove_global_fact_by_number <num> <search>", "Remove a specific global fact by number"),
            ]
            
            admin_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in admin_commands])
            embed.add_field(name="⚙️ Admin Commands", value=admin_text, inline=False)
        
        embed.set_footer(text="Quick help: !help or !h • This detailed view: !commands with bot name")
        
        await ctx.send(embed=embed)
    
    async def _discovery_help_handler(self, ctx, is_admin):
        """Handle discovery help commands - simplified version for users who don't know bot name"""
        bot_name_display = self.bot_name.title() if self.bot_name else "WhisperEngine"
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} - Quick Help",
            description=f"Welcome! Here's how to use **{bot_name_display}**:",
            color=0x3498db
        )
        
        # Demo bot warning (if applicable)
        if self.is_demo_bot:
            embed.add_field(
                name="⚠️ Demo Bot Notice",
                value="**This is a demo/testing bot:**\n"
                      "• Your conversations may be reviewed by developers for troubleshooting\n"
                      "• All data is regularly purged - don't expect production-level persistence\n"
                      "• For production use, please use our main bot instance",
                inline=False
            )
        
        # Bot discovery explanation
        if self.bot_name and ctx.guild:
            embed.add_field(
                name="🎯 Bot Discovery",
                value=f"**This bot responds to:** `{self.bot_name}` or `whisperengine`\n"
                      f"**Standard Discord help:** `!help` (works without bot name)\n"
                      f"**Targeted help:** `!commands {self.bot_name}` or `!help {self.bot_name}`\n"
                      f"**Quick test:** Try `!ping {self.bot_name}` or mention @{bot_name_display}",
                inline=False
            )
        elif self.bot_name:  # In DM
            embed.add_field(
                name="🎯 Bot Discovery",
                value=f"**Bot name:** `{self.bot_name}` (optional in DMs)\n"
                      f"**Standard help:** `!help` (works everywhere)\n"
                      f"**Quick start:** Just say hello or try `!ping`",
                inline=False
            )
        else:
            embed.add_field(
                name="🎯 Bot Discovery",
                value=f"**This bot responds to:** `whisperengine`\n"
                      f"**Standard help:** `!help` (works without bot name)\n"
                      f"**Quick start:** Try `!ping whisperengine` or mention the bot",
                inline=False
            )
        
        # Essential commands
        name_suffix = f" {self.bot_name}" if self.bot_name else " whisperengine"
        essential_commands = [
            ("!help", "Show complete command list (standard Discord command)"),
            (f"!ping{name_suffix}", "Test if bot is responding"),
            (f"!bot_status{name_suffix}", "Check bot health and status")
        ]
        
        essential_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in essential_commands])
        embed.add_field(name="🚀 Essential Commands", value=essential_text, inline=False)
        
        # Quick start guide
        if ctx.guild:
            quick_start = f"1. Try: `!help` (standard Discord help)\n2. Test bot: `!ping {self.bot_name or 'whisperengine'}`\n3. Chat by mentioning the bot\n4. Use voice with `!join {self.bot_name or 'whisperengine'}`"
        else:
            quick_start = f"1. Try: `!help` (works everywhere)\n2. Test bot: `!ping` (bot name optional in DMs)\n3. Just type messages to chat\n4. Use `!join` for voice features"
        
        embed.add_field(
            name="⚡ Quick Start",
            value=quick_start,
            inline=False
        )
        
        embed.set_footer(text="Standard Discord help: !help • This discovery help also works without bot name")
        
        await ctx.send(embed=embed)