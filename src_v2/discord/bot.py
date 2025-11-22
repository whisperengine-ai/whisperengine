import discord
from datetime import datetime
from discord.ext import commands
from loguru import logger
from src_v2.config.settings import settings
from src_v2.agents.engine import AgentEngine
from src_v2.core.character import character_manager
from src_v2.memory.manager import memory_manager
from src_v2.knowledge.manager import knowledge_manager
from src_v2.voice.player import play_text

class WhisperBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read messages
        intents.members = True          # Required to see members
        intents.voice_states = True     # Required for voice
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.agent_engine = AgentEngine()
        
        # Validate Bot Identity
        if not settings.DISCORD_BOT_NAME:
            raise ValueError("DISCORD_BOT_NAME is not set. Please set it in your .env file or environment variables.")
            
        self.character_name = settings.DISCORD_BOT_NAME

    async def setup_hook(self):
        # Load extensions
        try:
            await self.load_extension("src_v2.discord.commands")
            logger.info("Loaded extension: src_v2.discord.commands")
        except Exception as e:
            logger.error(f"Failed to load extension: {e}")

        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Preload character
        char = character_manager.get_character(self.character_name)
        if char:
            logger.info(f"Character '{self.character_name}' loaded successfully.")
        else:
            logger.error(f"Could not load character '{self.character_name}'!")

        logger.info("WhisperBot is ready and listening.")

    async def on_message(self, message: discord.Message):
        # Ignore messages from self and other bots to prevent loops
        if message.author.bot:
            return

        # Process commands first
        await self.process_commands(message)
        
        # Ignore empty messages or system messages
        if not message.content or message.is_system():
            return

        # Determine if we should respond
        # 1. Direct Message (DM)
        # 2. Mentioned in a server
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions
        
        if is_dm or is_mentioned:
            async with message.channel.typing():
                try:
                    # Get the character
                    character = character_manager.get_character(self.character_name)
                    
                    if not character:
                        logger.error(f"Character '{self.character_name}' not loaded.")
                        await message.channel.send("Error: Character not loaded.")
                        return

                    # Clean the message (remove mention)
                    user_message = message.content.replace(f"<@{self.user.id}>", "").strip()
                    user_id = str(message.author.id)
                    
                    # Check for image attachments
                    image_url = None
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.content_type and attachment.content_type.startswith("image/"):
                                image_url = attachment.url
                                logger.info(f"Detected image attachment: {image_url}")
                                break
                    
                    # 1. Save User Message & Extract Knowledge
                    # Note: We currently only save text to memory/knowledge graph
                    try:
                        await memory_manager.add_message(user_id, character.name, 'human', user_message)
                    except Exception as e:
                        logger.error(f"Failed to save user message to memory: {e}")

                    # Fire-and-forget knowledge extraction
                    try:
                        await knowledge_manager.process_user_message(user_id, user_message)
                    except Exception as e:
                        logger.error(f"Failed to process knowledge extraction: {e}")
                    
                    # 2. Get History & Memories (RAG)
                    chat_history = []
                    try:
                        chat_history = await memory_manager.get_recent_history(user_id, character.name)
                    except Exception as e:
                        logger.error(f"Failed to retrieve chat history: {e}")
                    
                    # Retrieve relevant memories
                    formatted_memories = "No relevant memories found."
                    try:
                        memories = await memory_manager.search_memories(user_message, user_id)
                        formatted_memories = "\n".join([f"- {m['content']}" for m in memories]) if memories else "No relevant memories found."
                    except Exception as e:
                        logger.error(f"Failed to search memories: {e}")

                    # Retrieve Knowledge Graph facts
                    knowledge_facts = ""
                    try:
                        knowledge_facts = await knowledge_manager.get_user_knowledge(user_id)
                    except Exception as e:
                        logger.error(f"Failed to retrieve knowledge facts: {e}")

                    # 3. Generate response
                    response = await self.agent_engine.generate_response(
                        character=character,
                        user_message=user_message,
                        chat_history=chat_history,
                        context_variables={
                            "user_name": message.author.display_name,
                            "time_of_day": datetime.now().strftime("%H:%M"),
                            "recent_memories": formatted_memories,
                            "knowledge_context": knowledge_facts
                        },
                        user_id=user_id,
                        image_url=image_url
                    )
                    
                    # 4. Save AI Response
                    try:
                        await memory_manager.add_message(user_id, character.name, 'ai', response)
                    except Exception as e:
                        logger.error(f"Failed to save AI response to memory: {e}")
                    
                    # Send response
                    await message.channel.send(response)
                    
                    # 5. Voice Playback
                    if message.guild and message.guild.voice_client:
                        vc = message.guild.voice_client
                        if vc.is_connected():
                            logger.info(f"Voice connected in {message.guild.name}. Attempting to speak response...")
                            try:
                                await play_text(vc, response)
                            except Exception as e:
                                logger.error(f"Failed to play voice: {e}")
                        else:
                            logger.warning("Voice client exists but is not connected.")
                    else:
                        logger.debug("No active voice client found for this guild.")

                except Exception as e:
                    logger.exception(f"Critical error in on_message: {e}")
                    await message.channel.send("I'm having a bit of trouble processing that right now. Please try again later.")


# Global bot instance
bot = WhisperBot()
