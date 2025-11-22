import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from typing import cast
from src_v2.memory.manager import memory_manager
from src_v2.core.character import character_manager
from src_v2.config.settings import settings

class CharacterCommands(app_commands.Group):
    def __init__(self):
        # Dynamic name based on the bot (e.g., "elena", "marcus")
        name = settings.DISCORD_BOT_NAME.lower() if settings.DISCORD_BOT_NAME else "bot"
        super().__init__(name=name, description=f"Commands for {name}")

    @app_commands.command(name="memory_wipe", description="Wipe your conversation memory with this character")
    async def memory_wipe(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            user_id = str(interaction.user.id)
            character_name = settings.DISCORD_BOT_NAME or "default"
            
            # Wipe memory
            await memory_manager.clear_memory(user_id, character_name)
            
            await interaction.followup.send(f"Memory wiped for {character_name}.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error wiping memory: {e}")
            await interaction.followup.send("Failed to wipe memory.", ephemeral=True)

    @app_commands.command(name="debug", description="Show debug information")
    async def debug(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            character_name = settings.DISCORD_BOT_NAME or "default"
            char = character_manager.get_character(character_name)
            
            info = f"**Bot Identity:** {character_name}\n"
            if char:
                info += f"**Loaded Character:** {char.name}\n"
            else:
                info += "**Loaded Character:** None (Error)\n"
                
            info += f"**Vision Enabled:** {settings.LLM_SUPPORTS_VISION}\n"
            # Check if voice is configured
            voice_enabled = bool(settings.ELEVENLABS_API_KEY)
            info += f"**Voice Enabled:** {voice_enabled}\n"
            
            await interaction.followup.send(info, ephemeral=True)
        except Exception as e:
            logger.error(f"Error getting debug info: {e}")
            await interaction.followup.send("Failed to get debug info.", ephemeral=True)

    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return

        # Cast user to Member to access voice state
        member = cast(discord.Member, interaction.user)
        
        if not member.voice or not member.voice.channel:
            await interaction.followup.send("You are not in a voice channel.", ephemeral=True)
            return
            
        channel = member.voice.channel
        # Ensure channel is a VoiceChannel (not StageChannel for now, unless supported)
        if not isinstance(channel, discord.VoiceChannel):
             await interaction.followup.send("I can only join standard voice channels.", ephemeral=True)
             return

        try:
            # Use VoiceManager
            from src_v2.discord.voice import VoiceManager
            # Cast client to Bot as VoiceManager expects Bot
            bot = cast(commands.Bot, interaction.client)
            vm = VoiceManager(bot)
            await vm.join_channel(channel)
            await interaction.followup.send(f"Joined {channel.name}!", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to join voice: {e}")
            await interaction.followup.send("Failed to join voice channel.", ephemeral=True)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.followup.send("I am not in a voice channel.", ephemeral=True)
            return
            
        try:
            from src_v2.discord.voice import VoiceManager
            # Cast client to Bot
            bot = cast(commands.Bot, interaction.client)
            vm = VoiceManager(bot)
            await vm.leave_channel(interaction.guild)
            await interaction.followup.send("Left voice channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to leave voice: {e}")
            await interaction.followup.send("Failed to leave voice channel.", ephemeral=True)

    @app_commands.command(name="configure", description="Configure bot behavior")
    @app_commands.describe(
        setting="The setting to configure",
        value="The value to set"
    )
    @app_commands.choices(setting=[
        app_commands.Choice(name="Verbosity (Length)", value="verbosity"),
        app_commands.Choice(name="Style (Tone)", value="style")
    ])
    async def configure(self, interaction: discord.Interaction, setting: str, value: str):
        """
        Configures a specific setting for the bot.
        For verbosity, valid values are: short, medium, long, dynamic.
        For style, valid values are: casual, formal, matching.
        """
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        character_name = settings.DISCORD_BOT_NAME or "default"
        
        # Validate values
        if setting == "verbosity":
            if value.lower() not in ["short", "medium", "long", "dynamic"]:
                await interaction.followup.send("Invalid value for verbosity. Use: short, medium, long, dynamic", ephemeral=True)
                return
        elif setting == "style":
             if value.lower() not in ["casual", "formal", "matching"]:
                await interaction.followup.send("Invalid value for style. Use: casual, formal, matching", ephemeral=True)
                return

        try:
            from src_v2.evolution.trust import trust_manager
            await trust_manager.update_preference(user_id, character_name, setting, value.lower())
            await interaction.followup.send(f"Updated **{setting}** to **{value}**.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to update preference: {e}")
            await interaction.followup.send("Failed to update configuration.", ephemeral=True)

class WhisperCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Register the dynamic group
        self.bot.tree.add_command(CharacterCommands())

async def setup(bot: commands.Bot):
    await bot.add_cog(WhisperCommands(bot))
