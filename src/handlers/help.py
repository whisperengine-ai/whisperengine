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
    
    def __init__(self, bot, bot_name, voice_manager, voice_support_enabled, VOICE_AVAILABLE, personality_profiler):
        self.bot = bot
        self.bot_name = bot_name
        self.voice_manager = voice_manager
        self.voice_support_enabled = voice_support_enabled
        self.VOICE_AVAILABLE = VOICE_AVAILABLE
        self.personality_profiler = personality_profiler
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register help commands"""
        
        @self.bot.command(name='help')
        @bot_name_filter()
        async def help_command(ctx):
            """Show all available bot commands (overrides default help)"""
            logger.debug(f"Help command called by {ctx.author.name} - redirecting to custom commands")
            await self._custom_help_handler(ctx, is_admin)

        @self.bot.command(name='commands', aliases=['help_custom'])
        @bot_name_filter()
        async def custom_help(ctx):
            """Show all available bot commands with descriptions"""
            await self._custom_help_handler(ctx, is_admin)
    
    async def _custom_help_handler(self, ctx, is_admin):
        """Handle custom help command with better formatting"""
        bot_name_display = self.bot_name.title() if self.bot_name else "Bot"
        embed = discord.Embed(
            title=f"🤖 {bot_name_display} Commands",
            description=f"Available commands for **{bot_name_display}**:",
            color=0x3498db
        )
        
        # Add name-based filtering explanation if bot name is configured
        if self.bot_name:
            embed.add_field(
                name="🎯 Command Targeting",
                value=f"**Important:** Include `{self.bot_name}` in your commands to target this bot specifically.\n"
                      f"**Example:** `!ping {self.bot_name}` or `!join {self.bot_name}`",
                inline=False
            )
        
        # Basic Commands
        name_suffix = f" {self.bot_name}" if self.bot_name else ""
        basic_commands = [
            (f"!ping{name_suffix}", "Simple ping command"),
            (f"!bot_status{name_suffix}", "Check Discord bot status and connection health"),
            (f"!llm_status{name_suffix}", "Check if the LLM server is running"),
            (f"!voice_status{name_suffix}", "Check voice support status and configuration"),
            (f"!clear_chat{name_suffix}", "Clear conversation history in this channel")
        ]
        
        basic_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in basic_commands])
        embed.add_field(name="📝 Basic Commands", value=basic_text, inline=False)
        
        # AI Chat Information
        embed.add_field(
            name="🧠 AI Chat", 
            value="💬 **Chat directly with the bot:**\n• Send a DM to chat naturally\n• Mention the bot in any channel\n• No commands needed - just start talking!", 
            inline=False
        )
        
        # Vision Commands
        vision_commands = [
            ("!vision_status", "Check if the bot supports image processing"),
            ("!test_image", "Test image processing (attach an image to the command)"),
        ]
        
        vision_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in vision_commands])
        embed.add_field(name="🖼️ Image Processing", value=vision_text, inline=False)
        
        # Voice Commands (if available and enabled)
        if self.voice_manager and self.voice_support_enabled:
            voice_commands = [
                (f"!join{name_suffix} [channel]", "Join voice channel"),
                (f"!leave{name_suffix}", "Leave voice channel"),
                (f"!speak{name_suffix} <text>", "Make bot speak text"),
                (f"!voice_connection_status{name_suffix}", "Show voice connection health"),
                (f"!voice_help{name_suffix}", "Show voice commands help")
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
            (f"!followup_settings{name_suffix} [on|off|status]", "🧪 Experimental: Manage follow-up messages"),
        ]
        
        memory_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in memory_commands])
        embed.add_field(name="💾 Memory Management", value=memory_text, inline=False)
        
        # AI Analysis Commands
        analysis_commands = []
        if self.personality_profiler:
            analysis_commands.append((f"!personality{name_suffix}", "🧠 View your AI personality profile"))
        
        if analysis_commands:
            analysis_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in analysis_commands])
            embed.add_field(name="🧠 AI Analysis", value=analysis_text, inline=False)
        
        # Automatic Fact Extraction Commands (User Facts Only)
        auto_fact_commands = [
            (f"!auto_facts{name_suffix} [on/off]", "Toggle automatic user fact extraction"),
            (f"!auto_extracted_facts{name_suffix}", "View automatically discovered user facts"),
            (f"!extract_facts{name_suffix} <message>", "Test fact extraction on a message"),
        ]
        
        auto_fact_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in auto_fact_commands])
        embed.add_field(name="🤖 Auto User Fact Discovery", value=auto_fact_text, inline=False)
        
        # DM-Only Commands
        dm_commands = [
            ("!sync_check", "Check if DM conversations are stored (DM only)"),
            ("!import_history [limit]", "Import old conversations to memory (DM only)")
        ]
        
        dm_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in dm_commands])
        embed.add_field(name="📱 DM Commands", value=dm_text, inline=False)
        
        # Data Control Commands
        data_commands = [
            ("!forget_me", "Delete all your stored data (with confirmation)"),
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
            ("!health", "Check overall system health"),
            ("!cache_stats", "Show conversation cache statistics")
        ]
        
        health_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in health_commands])
        embed.add_field(name="📊 Health & Stats", value=health_text, inline=False)
        
        # Admin Commands (if user is admin)
        if is_admin(ctx):
            admin_commands = [
                ("!debug [on|off|status]", "Toggle debug logging"),
                ("!memory_stats", "Show memory system statistics"),
                ("!system_status", "Show comprehensive system status"),
                ("!add_global_fact <fact>", "Add a global fact (admin only)"),
                ("!list_global_facts", "List all global facts (admin only)"),
                ("!remove_global_fact <search_term>", "Remove a global fact (admin only)"),
                ("!schedule_followup @user [hours]", "Schedule a follow-up message for a user"),
                ("!job_status [job_id]", "Check job scheduler status or specific job"),
                ("!emotional_intelligence", "Check emotional intelligence system status"),
            ]
            
            admin_text = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in admin_commands])
            embed.add_field(name="⚙️ Admin Commands", value=admin_text, inline=False)
        
        embed.set_footer(text="Use !help or !commands to see this help message")
        
        await ctx.send(embed=embed)