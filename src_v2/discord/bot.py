from langchain_core.messages import HumanMessage
import discord
from typing import Union
from datetime import datetime
from discord.ext import commands
from loguru import logger
from src_v2.config.settings import settings
from src_v2.agents.engine import AgentEngine
from src_v2.core.character import character_manager
from src_v2.memory.manager import memory_manager
from src_v2.memory.session import session_manager
from src_v2.memory.summarizer import SummaryManager
from src_v2.knowledge.manager import knowledge_manager
from src_v2.knowledge.documents import document_processor
from src_v2.voice.player import play_text
from src_v2.core.database import db_manager
from src_v2.evolution.feedback import feedback_analyzer
from src_v2.evolution.goals import goal_analyzer
from src_v2.evolution.trust import trust_manager
from src_v2.intelligence.reflection import reflection_engine
from influxdb_client.client.write.point import Point

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
        self.summary_manager = SummaryManager()
        
        # Validate Bot Identity
        if not settings.DISCORD_BOT_NAME:
            raise ValueError("DISCORD_BOT_NAME is not set. Please set it in your .env file or environment variables.")
            
        self.character_name = settings.DISCORD_BOT_NAME

    def _chunk_message(self, text: str, max_length: int = 2000) -> list[str]:
        """
        Splits a long message into chunks that fit Discord's character limit.
        Tries to split on sentence boundaries when possible.
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences (basic approach)
        sentences = text.replace("\n\n", "\n\n<BREAK>").replace(". ", ".<BREAK>").split("<BREAK>")
        
        for sentence in sentences:
            # If adding this sentence would exceed the limit
            if len(current_chunk) + len(sentence) > max_length:
                # If current chunk has content, save it
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If the sentence itself is too long, force split by words
                if len(sentence) > max_length:
                    words = sentence.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > max_length:
                            chunks.append(current_chunk.strip())
                            current_chunk = word + " "
                        else:
                            current_chunk += word + " "
                else:
                    current_chunk = sentence
            else:
                current_chunk += sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

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

        logger.info("WhisperEngine is ready and listening.")

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

                    # 0. Session Management
                    user_id = str(message.author.id)
                    session_id = await session_manager.get_active_session(user_id, self.character_name)
                    if not session_id:
                        session_id = await session_manager.create_session(user_id, self.character_name)

                    # Clean the message (remove mention)
                    user_message = message.content.replace(f"<@{self.user.id}>", "").strip()
                    
                    # Handle Replies (Context Injection)
                    if message.reference:
                        try:
                            ref_msg = None
                            if message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
                                ref_msg = message.reference.resolved
                            elif message.reference.message_id:
                                try:
                                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                                except:
                                    pass # Message might be deleted or inaccessible

                            if ref_msg and ref_msg.content:
                                ref_text = ref_msg.content[:100] + "..." if len(ref_msg.content) > 100 else ref_msg.content
                                ref_author = ref_msg.author.display_name
                                user_message = f"[Replying to {ref_author}: \"{ref_text}\"]\n{user_message}"
                                logger.info(f"Injected reply context: {user_message}")
                        except Exception as e:
                            logger.warning(f"Failed to resolve reply reference: {e}")

                    user_id = str(message.author.id)
                    channel_id = str(message.channel.id)
                    
                    # Check for attachments (Images & Documents)
                    image_urls = []
                    file_content = None
                    
                    if message.attachments:
                        processed_files = []
                        file_count = 0
                        MAX_FILES = 5
                        MAX_SIZE_MB = 5
                        MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

                        for attachment in message.attachments:
                            # Image Handling (Collect all images)
                            if attachment.content_type and attachment.content_type.startswith("image/"):
                                image_urls.append(attachment.url)
                                logger.info(f"Detected image attachment: {attachment.url}")
                            
                            # Document Handling (PDF, Txt, etc.)
                            else:
                                if file_count >= MAX_FILES:
                                    logger.warning(f"Skipping attachment {attachment.filename}: Max file limit ({MAX_FILES}) reached.")
                                    continue
                                
                                if attachment.size > MAX_SIZE_BYTES:
                                    logger.warning(f"Skipping attachment {attachment.filename}: Size ({attachment.size} bytes) exceeds limit ({MAX_SIZE_MB}MB).")
                                    await message.channel.send(f"⚠️ Skipping {attachment.filename}: File too large (Max {MAX_SIZE_MB}MB).")
                                    continue

                                logger.info(f"Detected document attachment: {attachment.filename}")
                                await message.channel.send(f"📄 Reading {attachment.filename}...")
                                
                                try:
                                    extracted_text = await document_processor.process_attachment(attachment.url, attachment.filename)
                                    if extracted_text:
                                        # Truncate individual file content if too massive
                                        if len(extracted_text) > 10000:
                                            extracted_text = extracted_text[:10000] + "\n...[Content Truncated]..."
                                        
                                        processed_files.append(f"--- File: {attachment.filename} ---\n{extracted_text}")
                                        file_count += 1
                                        logger.info(f"Processed document content: {len(extracted_text)} chars")
                                except Exception as e:
                                    logger.error(f"Failed to process {attachment.filename}: {e}")
                                    await message.channel.send(f"❌ Failed to read {attachment.filename}.")

                        if processed_files:
                            file_content = "\n\n".join(processed_files)
                    
                    # 1. Retrieve Context (RAG & History) BEFORE saving current message
                    # This prevents "Echo Chamber" (finding current msg in vector search)
                    # and "Double Speak" (finding current msg in chat history)
                    
                    # Retrieve relevant memories
                    formatted_memories = "No relevant memories found."
                    try:
                        memories = await memory_manager.search_memories(user_message, user_id)
                        formatted_memories = "\n".join([f"- {m['content']}" for m in memories]) if memories else "No relevant memories found."
                    except Exception as e:
                        logger.error(f"Failed to search memories: {e}")

                    # Get History
                    chat_history = []
                    try:
                        chat_history = await memory_manager.get_recent_history(user_id, character.name, channel_id=channel_id)
                    except Exception as e:
                        logger.error(f"Failed to retrieve chat history: {e}")

                    # Retrieve Knowledge Graph facts
                    knowledge_facts = ""
                    try:
                        knowledge_facts = await knowledge_manager.get_user_knowledge(user_id)
                    except Exception as e:
                        logger.error(f"Failed to retrieve knowledge facts: {e}")

                    # Retrieve Past Summaries (Long-term Context)
                    past_summaries = ""
                    try:
                        summaries = await memory_manager.search_summaries(user_message, user_id, limit=3)
                        if summaries:
                            past_summaries = "\n".join([f"- {s['content']} (Meaningfulness: {s['meaningfulness']})" for s in summaries])
                    except Exception as e:
                        logger.error(f"Failed to retrieve summaries: {e}")

                    # 2. Save User Message & Extract Knowledge
                    try:
                        await memory_manager.add_message(user_id, character.name, 'human', user_message, channel_id=channel_id, message_id=str(message.id))
                        
                        # Log Message Event to InfluxDB
                        if db_manager.influxdb_write_api:
                            point = Point("message_event") \
                                .tag("user_id", user_id) \
                                .tag("bot_name", self.character_name) \
                                .tag("channel_type", "dm" if is_dm else "guild") \
                                .field("length", len(user_message)) \
                                .time(datetime.utcnow())
                            db_manager.influxdb_write_api.write(bucket=settings.INFLUXDB_BUCKET, record=point)

                    except Exception as e:
                        logger.error(f"Failed to save user message to memory: {e}")

                    # Fire-and-forget knowledge extraction
                    try:
                        await knowledge_manager.process_user_message(user_id, user_message)
                    except Exception as e:
                        logger.error(f"Failed to process knowledge extraction: {e}")

                    # 2.5 Check for Summarization
                    if session_id:
                        self.loop.create_task(self._check_and_summarize(session_id, user_id))

                    # Determine Location Context
                    location_context = "Direct Message"
                    if message.guild:
                        if isinstance(message.channel, discord.Thread):
                            parent_name = message.channel.parent.name if message.channel.parent else "unknown"
                            location_context = f"Thread '{message.channel.name}' (in #{parent_name})"
                        else:
                            location_context = f"Channel #{message.channel.name}"

                    # 3. Generate response
                    context_vars = {
                        "user_name": message.author.display_name,
                        "time_of_day": datetime.now().strftime("%H:%M"),
                        "location": location_context,
                        "recent_memories": formatted_memories,
                        "knowledge_context": knowledge_facts,
                        "past_summaries": past_summaries
                    }
                    
                    # Inject file content if present
                    if file_content:
                        context_vars["file_content"] = file_content
                        user_message += f"\n\n[Attached File Content]:\n{file_content}"

                    response = await self.agent_engine.generate_response(
                        character=character,
                        user_message=user_message,
                        chat_history=chat_history,
                        context_variables=context_vars,
                        user_id=user_id,
                        image_urls=image_urls
                    )
                    
                    # 4. Save AI Response
                    try:
                        # Split response into chunks if it's too long
                        message_chunks = self._chunk_message(response)
                        
                        # Send all chunks
                        sent_messages = []
                        for chunk in message_chunks:
                            sent_msg = await message.channel.send(chunk)
                            sent_messages.append(sent_msg)
                        
                        # Save the full response to memory (not chunked)
                        # Use the last message ID as the primary reference
                        await memory_manager.add_message(
                            user_id, 
                            character.name, 
                            'ai', 
                            response, 
                            channel_id=channel_id, 
                            message_id=str(sent_messages[-1].id)
                        )
                        
                        # 4.5 Goal Analysis (Fire-and-forget)
                        # Analyze the interaction (User Message + AI Response)
                        interaction_text = f"User: {user_message}\nAI: {response}"
                        self.loop.create_task(
                            goal_analyzer.check_goals(user_id, character.name, interaction_text)
                        )
                        
                        # 4.6 Trust Update (Engagement Reward)
                        # Small trust increase for every positive interaction
                        self.loop.create_task(
                            trust_manager.update_trust(user_id, character.name, 1)
                        )
                        
                        # 5. Voice Playback (use full response, not chunked)
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
                        logger.error(f"Failed to send/save AI response: {e}")

                except Exception as e:
                    logger.exception(f"Critical error in on_message: {e}")
                    await message.channel.send("I'm having a bit of trouble processing that right now. Please try again later.")

    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        """
        Handles reactions added to messages.
        Used for user feedback (e.g., thumbs up/down) to adjust memory importance.
        """
        if user.bot:
            return

        # Only care if the reaction is on a message sent by THIS bot
        if reaction.message.author.id != self.user.id:
            return

        try:
            message_id = str(reaction.message.id)
            user_id = str(user.id)
            emoji = str(reaction.emoji)
            message_length = len(reaction.message.content)
            
            logger.info(f"User {user.name} reacted with {emoji} to message {message_id}")

            # Log to InfluxDB via FeedbackAnalyzer
            await feedback_analyzer.log_reaction_to_influx(
                user_id=user_id,
                message_id=message_id,
                reaction=emoji,
                bot_name=self.character_name,
                message_length=message_length
            )
            
            # Get feedback score and adjust memory importance
            feedback = await feedback_analyzer.get_feedback_score(message_id, user_id)
            if feedback and feedback["score"] != 0:
                # Adjust memory importance in Qdrant
                collection_name = f"whisperengine_memory_{self.character_name}"
                score_delta = feedback["score"] * 0.2  # Scale to ±0.2 adjustment
                
                await feedback_analyzer.adjust_memory_score_by_message_id(
                    message_id=message_id,
                    collection_name=collection_name,
                    score_delta=score_delta
                )
                
                # Update Trust based on feedback
                # Positive feedback increases trust significantly
                # Negative feedback decreases trust
                trust_delta = 5 if feedback["score"] > 0 else -5
                self.loop.create_task(
                    trust_manager.update_trust(user_id, self.character_name, trust_delta)
                )
                
                logger.info(f"Feedback score for message: {feedback['score']} (adjusted memory importance)")

        except Exception as e:
            logger.error(f"Error handling reaction: {e}")

    async def _check_and_summarize(self, session_id: str, user_id: str):
        """
        Checks if summarization is needed and runs it.
        """
        try:
            # 1. Get session start time
            start_time = await session_manager.get_session_start_time(session_id)
            if not start_time:
                return

            # 2. Count messages
            message_count = await memory_manager.count_messages_since(user_id, self.character_name, start_time)
            
            # 3. Check threshold (e.g., 20 messages)
            SUMMARY_THRESHOLD = 20
            if message_count >= SUMMARY_THRESHOLD:
                logger.info(f"Session {session_id} reached {message_count} messages. Triggering summarization.")
                
                # Fetch messages
                messages = await memory_manager.get_recent_history(user_id, self.character_name, limit=message_count)
                # Convert to dict format expected by SummaryManager
                msg_dicts = [{"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content} for m in messages]
                
                # Generate Summary
                summary_manager = SummaryManager() 
                result = await summary_manager.generate_summary(msg_dicts)
                
                if result:
                    await summary_manager.save_summary(session_id, result)
                    logger.info(f"Session {session_id} summarized successfully.")
                    
                    # Trigger Reflection
                    logger.info("Triggering reflection analysis...")
                    await reflection_engine.analyze_user_patterns(user_id, self.character_name)
                    
                    # Ideally we should mark these messages as summarized or close the session to start a fresh one.
                    # For now, we just log it.
                    
        except Exception as e:
            logger.error(f"Error in _check_and_summarize: {e}")


# Global bot instance
bot = WhisperBot()
