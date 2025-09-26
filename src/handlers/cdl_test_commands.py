"""
CDL Character Integration Test

Simple test to enable character roleplay using the CDL integration system.
"""

import logging
import discord

logger = logging.getLogger(__name__)


class CDLTestCommands:
    """Test commands for CDL character integration."""
    
    def __init__(self, bot):
        self.bot = bot
        self.current_character = None  # Track active character per user
        self.user_characters = {}  # user_id -> character_file mapping
        
    def register_commands(self):
        """Register CDL test commands."""
        
        @self.bot.command(name='roleplay', aliases=['character', 'be'])
        async def set_character(ctx, character_name: str = None):
            """Switch to roleplay as a specific character."""
            try:
                if not character_name:
                    # Show available characters
                    embed = discord.Embed(
                        title="🎭 Available Characters",
                        description="Choose a character to roleplay as:",
                        color=0xff69b4
                    )
                    embed.add_field(
                        name="Elena Rodriguez",
                        value="Marine biologist and environmental scientist\n`!roleplay elena`",
                        inline=False
                    )
                    embed.add_field(
                        name="Marcus Chen", 
                        value="Tech entrepreneur and innovator\n`!roleplay marcus`",
                        inline=False
                    )
                    embed.add_field(
                        name="Default Bot",
                        value="Return to normal bot personality\n`!roleplay off`",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    return
                
                user_id = str(ctx.author.id)
                character_name = character_name.lower()
                
                if character_name in ['off', 'none', 'default', 'stop']:
                    # Disable character roleplay
                    if user_id in self.user_characters:
                        del self.user_characters[user_id]
                    
                    # Clear conversation history when switching back to default
                    channel_id = str(ctx.channel.id)
                    if hasattr(self.bot, 'conversation_history') and self.bot.conversation_history:
                        self.bot.conversation_history.clear_channel(channel_id)
                    if hasattr(self.bot, 'conversation_cache') and self.bot.conversation_cache:
                        self.bot.conversation_cache.clear_channel_cache(channel_id)
                    
                    # Clear user-specific memory to prevent cross-character contamination
                    if hasattr(self.bot, 'memory_manager') and self.bot.memory_manager:
                        if hasattr(self.bot.memory_manager, 'clear_user_data'):
                            await self.bot.memory_manager.clear_user_data(user_id)
                            logger.info(f"🎭 Cleared user memory for {user_id} when disabling roleplay")
                    
                    logger.info(f"🎭 Cleared conversation history when disabling roleplay in channel {channel_id}")
                    
                    await ctx.send("🎭 **Character roleplay disabled.** I'm back to my normal personality!")
                    return
                
                # Map character names to files - use bot's CDL_DEFAULT_CHARACTER if available,
                # otherwise fall back to standard character files
                import os
                default_character = os.getenv('CDL_DEFAULT_CHARACTER')
                
                character_files = {
                    'elena': 'characters/examples/elena-rodriguez.json',
                    'marcus': 'characters/examples/marcus-thompson.json', 
                    'ryan': 'characters/examples/ryan-chen.json'
                }
                
                # If this bot has a CDL_DEFAULT_CHARACTER set and the user requests that bot's character,
                # use the environment variable instead
                bot_name = os.getenv('DISCORD_BOT_NAME', '').lower()
                if default_character and bot_name in character_files:
                    character_files[bot_name] = default_character
                
                if character_name not in character_files:
                    await ctx.send(f"❌ **Character '{character_name}' not found.** Use `!roleplay` to see available characters.")
                    return
                
                # Set character for this user
                character_file = character_files[character_name]
                self.user_characters[user_id] = character_file
                
                # Clear conversation history to prevent cross-character contamination
                channel_id = str(ctx.channel.id)
                if hasattr(self.bot, 'conversation_history') and self.bot.conversation_history:
                    self.bot.conversation_history.clear_channel(channel_id)
                if hasattr(self.bot, 'conversation_cache') and self.bot.conversation_cache:
                    self.bot.conversation_cache.clear_channel_cache(channel_id)
                
                # Clear user-specific memory to prevent cross-character contamination
                if hasattr(self.bot, 'memory_manager') and self.bot.memory_manager:
                    if hasattr(self.bot.memory_manager, 'clear_user_data'):
                        await self.bot.memory_manager.clear_user_data(user_id)
                        logger.info(f"🎭 Cleared user memory for {user_id} when switching to {character_name}")
                
                logger.info(f"🎭 Cleared conversation history for character switch to {character_name} in channel {channel_id}")
                
                # Test character loading
                try:
                    from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
                    cdl_integration = CDLAIPromptIntegration()
                    character = await cdl_integration.load_character(character_file)
                    
                    # Success message in character
                    embed = discord.Embed(
                        title=f"🎭 Now Roleplaying: {character.identity.name}",
                        description=character.identity.description,
                        color=0x00ff88
                    )
                    embed.add_field(
                        name="Character Info",
                        value=f"**Age:** {character.identity.age}\n**Occupation:** {character.identity.occupation}\n**Location:** {character.identity.location}",
                        inline=True
                    )
                    embed.add_field(
                        name="Personality",
                        value=character.get_personality_summary()[:100] + "...",
                        inline=True
                    )
                    embed.set_footer(text="All your messages will now be responded to as this character!")
                    
                    await ctx.send(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Failed to load character {character_file}: {e}")
                    await ctx.send(f"❌ **Failed to load character:** {e}")
                    
            except Exception as e:
                logger.error(f"Error in roleplay command: {e}")
                await ctx.send(f"❌ **Error:** {e}")
        
        @self.bot.command(name='character_info', aliases=['who'])
        async def character_info(ctx):
            """Show current active character."""
            user_id = str(ctx.author.id)
            
            if user_id not in self.user_characters:
                await ctx.send("🎭 **No character active.** Use `!roleplay <character>` to start roleplaying!")
                return
            
            try:
                from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
                cdl_integration = CDLAIPromptIntegration()
                character = await cdl_integration.load_character(self.user_characters[user_id])
                
                embed = discord.Embed(
                    title=f"🎭 Current Character: {character.identity.name}",
                    description=character.identity.description,
                    color=0xff69b4
                )
                
                # Basic info
                embed.add_field(
                    name="📋 Basic Info",
                    value=f"**Full Name:** {character.identity.full_name}\n**Age:** {character.identity.age}\n**Occupation:** {character.identity.occupation}\n**Location:** {character.identity.location}",
                    inline=False
                )
                
                # Personality overview
                if character.personality and character.personality.big_five:
                    big_five = character.personality.big_five
                    embed.add_field(
                        name="🧠 Personality (Big Five)",
                        value=f"**Openness:** {big_five.openness:.1f}\n**Conscientiousness:** {big_five.conscientiousness:.1f}\n**Extraversion:** {big_five.extraversion:.1f}\n**Agreeableness:** {big_five.agreeableness:.1f}\n**Neuroticism:** {big_five.neuroticism:.1f}",
                        inline=True
                    )
                
                # Voice and communication
                if character.identity.voice:
                    voice = character.identity.voice
                    embed.add_field(
                        name="🎤 Voice & Style",
                        value=f"**Tone:** {voice.tone}\n**Pace:** {voice.pace}\n**Accent:** {voice.accent}",
                        inline=True
                    )
                
                # Current projects/goals
                if hasattr(character, 'current_life') and character.current_life:
                    embed.add_field(
                        name="🎯 Current Focus",
                        value=character.current_life.overview if hasattr(character.current_life, 'overview') else "Pursuing various goals",
                        inline=False
                    )
                
                embed.set_footer(text="Use !roleplay off to disable character roleplay")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error getting character info: {e}")
                await ctx.send(f"❌ **Error loading character info:** {e}")
    
    def get_user_character(self, user_id: str) -> str:
        """Get the current character file for a user."""
        return self.user_characters.get(user_id)