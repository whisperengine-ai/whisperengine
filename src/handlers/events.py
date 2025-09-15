"""
Event handlers for the Discord bot.

Extracted from main.py to improve code organization and maintainability.
Contains on_ready and on_message event handlers with all their complex logic.
"""

import asyncio
import os
import time
import logging
from datetime import datetime, timezone
import discord
from typing import Optional

from src.utils.helpers import (
    is_admin, generate_conversation_summary, process_message_with_images,
    get_current_time_context, add_debug_info_to_response, store_discord_user_info,
    store_discord_server_info, get_message_content, get_message_author_id,
    message_equals_bot_user, fix_message_alternation, extract_text_for_memory_storage,
    get_contextualized_system_prompt
)
from src.security.system_message_security import scan_response_for_system_leakage
from src.utils.exceptions import (
    LLMConnectionError, LLMTimeoutError, LLMRateLimitError, LLMError,
    MemoryRetrievalError, MemoryStorageError, ValidationError
)
from src.security.input_validator import validate_user_input

# Universal Chat Platform Integration
from src.platforms.universal_chat import (
    UniversalChatOrchestrator,
    DiscordChatAdapter,
    ChatPlatform,
    MessageType
)
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager

logger = logging.getLogger(__name__)


class BotEventHandlers:
    """
    Event handlers for the Discord bot.
    
    This class encapsulates all event handling logic that was previously
    in the main.py file, providing better organization and testability.
    """
    
    def __init__(self, bot_core):
        """
        Initialize event handlers with references to bot components.
        
        Args:
            bot_core: DiscordBotCore instance with all initialized components
        """
        self.bot_core = bot_core
        self.bot = bot_core.bot
        
        # Component references for easier access
        self.postgres_pool = getattr(bot_core, 'postgres_pool', None)
        self.memory_manager = getattr(bot_core, 'memory_manager', None)
        self.safe_memory_manager = getattr(bot_core, 'safe_memory_manager', None)
        self.llm_client = getattr(bot_core, 'llm_client', None)
        self.conversation_cache = getattr(bot_core, 'conversation_cache', None)
        self.job_scheduler = getattr(bot_core, 'job_scheduler', None)
        self.voice_manager = getattr(bot_core, 'voice_manager', None)
        self.heartbeat_monitor = getattr(bot_core, 'heartbeat_monitor', None)
        self.image_processor = getattr(bot_core, 'image_processor', None)
        self.personality_profiler = getattr(bot_core, 'personality_profiler', None)
        self.graph_personality_manager = getattr(bot_core, 'graph_personality_manager', None)
        self.phase2_integration = getattr(bot_core, 'phase2_integration', None)
        self.external_emotion_ai = getattr(bot_core, 'external_emotion_ai', None)
        
        # Configuration flags - unified AI system always enabled
        self.voice_support_enabled = getattr(bot_core, 'voice_support_enabled', False)
        
        # Initialize Universal Chat Orchestrator
        self.chat_orchestrator = None
        # Note: Universal Chat will be initialized asynchronously in setup_universal_chat()
        
        # Register event handlers
        self._register_events()
    
    async def setup_universal_chat(self):
        """Setup Universal Chat Orchestrator for proper layered architecture"""
        try:
            logger.info("🌐 Setting up Universal Chat Orchestrator for Discord integration...")
            
            # Create configuration and database managers
            config_manager = AdaptiveConfigManager()
            db_manager = DatabaseIntegrationManager(config_manager)
            
            # Create universal chat orchestrator
            self.chat_orchestrator = UniversalChatOrchestrator(
                config_manager=config_manager,
                db_manager=db_manager
            )
            
            # Initialize the orchestrator
            success = await self.chat_orchestrator.initialize()
            if not success:
                logger.warning("Failed to initialize Universal Chat Orchestrator")
                self.chat_orchestrator = None
                return False
            
            # Setup Discord adapter and set bot instance
            if hasattr(self.chat_orchestrator, 'adapters') and ChatPlatform.DISCORD in self.chat_orchestrator.adapters:
                discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                if hasattr(discord_adapter, 'set_bot_instance'):
                    discord_adapter.set_bot_instance(self.bot)
                    logger.info("✅ Discord adapter configured with bot instance")
            
            logger.info("✅ Universal Chat Orchestrator setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Universal Chat Orchestrator: {e}")
            logger.warning("Falling back to direct LLM client calls")
            self.chat_orchestrator = None
            return False
    
    def _register_events(self):
        """Register event handlers with the Discord bot."""
        @self.bot.event
        async def on_ready():
            return await self.on_ready()
        
        @self.bot.event
        async def on_message(message):
            return await self.on_message(message)
    
    async def on_ready(self):
        """
        Handle bot ready event.
        
        Initializes PostgreSQL pool, starts job scheduler, sets up heartbeat monitoring,
        and configures bot presence.
        """
        logger.info(f"{self.bot.user} has connected to Discord!")
        logger.info(f"Bot is connected to {len(self.bot.guilds)} guilds")
        
        # Initialize PostgreSQL pool if not already done
        if self.postgres_pool is None:
            try:
                logger.info("Initializing PostgreSQL connection pool...")
                import asyncpg
                from src.utils.postgresql_user_db import PostgreSQLUserDB
                
                postgres_db = PostgreSQLUserDB()
                await postgres_db.initialize()
                self.postgres_pool = postgres_db.pool
                
                # Update bot_core reference
                self.bot_core.postgres_pool = self.postgres_pool
                
                # Also update memory managers that might need the pool
                if hasattr(self.bot_core, 'context_memory_manager'):
                    self.bot_core.context_memory_manager.postgres_pool = self.postgres_pool
                
                logger.info("✅ PostgreSQL connection pool initialized successfully")
                
                # Database tables are automatically initialized by PostgreSQLUserDB.initialize()
                logger.info("✅ Database tables initialized/verified")
                
            except ConnectionError as e:
                # Clean error message for PostgreSQL connection failures
                logger.error(f"PostgreSQL connection failed: {e}")
                logger.warning("Bot will continue without PostgreSQL support")
            except Exception as e:
                logger.error(f"Unexpected error initializing PostgreSQL: {e}")
                logger.warning("Bot will continue without PostgreSQL support")
        
        # Initialize Redis conversation cache if using Redis
        if self.conversation_cache and hasattr(self.conversation_cache, 'initialize'):
            try:
                logger.info("Initializing Redis conversation cache...")
                await self.conversation_cache.initialize()
                logger.info("✅ Redis conversation cache initialized successfully")
            except ConnectionError as e:
                # Clean error message for Redis connection failures
                logger.error(f"Redis connection failed: {e}")
                logger.warning("Bot will continue with in-memory conversation cache")
            except Exception as e:
                logger.error(f"Unexpected error initializing Redis conversation cache: {e}")
                logger.warning("Bot will continue with limited conversation cache functionality")
        
        # Start job scheduler if available
        if self.job_scheduler:
            try:
                await self.job_scheduler.start()
                logger.info("✅ Job scheduler started successfully")
            except Exception as e:
                logger.error(f"Failed to start job scheduler: {e}")
        
        # Initialize Universal Chat Orchestrator
        if self.chat_orchestrator is None:
            try:
                logger.info("🌐 Initializing Universal Chat Orchestrator...")
                success = await self.setup_universal_chat()
                if success:
                    logger.info("✅ Universal Chat Orchestrator ready for Discord integration")
                else:
                    logger.warning("⚠️ Universal Chat Orchestrator initialization failed - using fallback")
            except Exception as e:
                logger.error(f"Failed to initialize Universal Chat Orchestrator: {e}")
        
        # Start heartbeat monitor
        if self.heartbeat_monitor:
            try:
                self.heartbeat_monitor.start()
                logger.info("✅ Heartbeat monitor started successfully")
            except Exception as e:
                logger.error(f"Failed to start heartbeat monitor: {e}")
        
        # Set bot presence
        try:
            activity = discord.Activity(type=discord.ActivityType.listening, name="...")
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            logger.info("✅ Bot presence set successfully")
        except Exception as e:
            logger.warning(f"Failed to set bot presence: {e}")
        
        # Check LLM connection
        if self.llm_client:
            try:
                connection_ok = await self.llm_client.check_connection_async()
                if connection_ok:
                    logger.info(f"✅ LLM connection verified ({self.llm_client.service_name})")
                else:
                    logger.warning(f"⚠️ LLM connection failed ({self.llm_client.service_name})")
            except Exception as e:
                logger.error(f"Error checking LLM connection: {e}")
        
        # Log successful startup
        logger.info("🚀 Bot initialization complete - ready to chat!")
    
    async def on_message(self, message):
        """
        Handle incoming messages.
        
        Processes both DM and guild messages with comprehensive logic including:
        - Security validation
        - Memory retrieval and storage
        - AI analysis (personality, emotional intelligence)
        - LLM response generation
        - Voice responses
        - Cache management
        
        Args:
            message: Discord message object
        """
        # Skip bot messages unless they're to be cached
        if message.author.bot:
            # Add bot messages to cache for conversation context
            if self.conversation_cache and message.author == self.bot.user:
                # Handle both sync and async cache implementations
                if hasattr(self.conversation_cache, 'add_message'):
                    if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                        await self.conversation_cache.add_message(str(message.channel.id), message)
                    else:
                        self.conversation_cache.add_message(str(message.channel.id), message)
            return
        
        logger.debug(f"Received message from {message.author.name} ({message.author.id}) in {message.channel.name if message.guild else 'DM'}")
        
        # Check if the message is a DM
        if message.guild is None:
            await self._handle_dm_message(message)
        else:
            await self._handle_guild_message(message)
    
    async def _handle_dm_message(self, message):
        """Handle direct message to the bot."""
        # Check if this is a command first
        if message.content.startswith('!'):
            await self.bot.process_commands(message)
            return
        
        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.debug(f"Processing DM from {message.author.name}")
        
        # Security validation
        validation_result = validate_user_input(message.content, user_id, "dm")
        if not validation_result['is_safe']:
            logger.error(f"SECURITY: Unsafe input detected from user {user_id} in DM")
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            await reply_channel.send("⚠️ Your message contains content that could not be processed for security reasons. Please rephrase your message.")
            return
        
        # Use sanitized content
        sanitized_content = validation_result['sanitized_content']
        if validation_result['warnings']:
            logger.warning(f"SECURITY: Input warnings for user {user_id} in DM: {validation_result['warnings']}")
        
        # Replace original message content with sanitized version
        message.content = sanitized_content
        
        # Initialize variables early
        enhanced_system_prompt = None
        phase4_context = None
        comprehensive_context = None
        
        # Get relevant memories with context-aware filtering
        try:
            message_context = self.memory_manager.classify_discord_context(message)
            logger.debug(f"DM context classified: {message_context.context_type.value} (security: {message_context.security_level.value})")
            
            relevant_memories = self.memory_manager.retrieve_context_aware_memories(
                user_id, message.content, message_context, limit=20
            )
            
            # Get emotion context if available
            emotion_context = ""
            if hasattr(self.memory_manager, 'get_emotion_context'):
                emotion_context = self.memory_manager.get_emotion_context(user_id)
                
        except (MemoryRetrievalError, ValidationError) as e:
            logger.warning(f"Could not retrieve memories for user {user_id}: {e}")
            relevant_memories = []
            emotion_context = ""
        except Exception as e:
            logger.error(f"Unexpected error retrieving memories: {e}")
            relevant_memories = []
            emotion_context = ""
        
        # Get recent conversation history
        recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
        
        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, enhanced_system_prompt
        )
        
        # External API emotion analysis (always available when configured)
        external_emotion_data = None
        if self.external_emotion_ai:
            external_emotion_data = await self._analyze_external_emotion(
                message.content, user_id, conversation_context
            )
        
        # Phase 2: Emotional Intelligence Analysis (always available when configured)
        phase2_context = None
        current_emotion_data = None
        if self.phase2_integration:
            phase2_context, current_emotion_data = await self._analyze_phase2_emotion(
                user_id, message.content, message
            )
        
        # Phase 4: Human-Like Conversation Intelligence
        if hasattr(self.memory_manager, 'process_with_phase4_intelligence'):
            phase4_context, comprehensive_context, enhanced_system_prompt = await self._process_phase4_intelligence(
                user_id, message, recent_messages, external_emotion_data, phase2_context
            )
        
        # Process message with images
        conversation_context = await process_message_with_images(
            message.content, message.attachments, conversation_context, 
            self.llm_client, self.image_processor
        )
        
        # Generate and send response
        await self._generate_and_send_response(
            reply_channel, message, user_id, conversation_context, 
            current_emotion_data, external_emotion_data, phase2_context,
            phase4_context, comprehensive_context
        )
    
    async def _handle_guild_message(self, message):
        """Handle guild (server) message."""
        # Check for bot mentions first
        if self.bot.user in message.mentions:
            await self._handle_mention_message(message)
        else:
            # Process commands as normal
            await self.bot.process_commands(message)
    
    async def _handle_mention_message(self, message):
        """Handle message where bot is mentioned."""
        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.debug(f"Bot mentioned by {message.author.name} in {message.channel.name}")
        
        # Remove mentions from content
        content = message.content
        for mention in message.mentions:
            if mention == self.bot.user:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '').strip()
        
        if not content:
            await self.bot.process_commands(message)
            return
        
        # Security validation for guild messages
        validation_result = validate_user_input(content, user_id, "server_channel")
        if not validation_result['is_safe']:
            logger.error(f"SECURITY: Unsafe input detected from user {user_id} in server {message.guild.name}")
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            await reply_channel.send(f"⚠️ {message.author.mention} Your message contains content that could not be processed for security reasons. Please rephrase your message.")
            return
        
        content = validation_result['sanitized_content']
        if validation_result['warnings']:
            logger.warning(f"SECURITY: Input warnings for user {user_id} in server {message.guild.name}: {validation_result['warnings']}")
        
        # Get relevant memories with context-aware filtering
        try:
            message_context = self.memory_manager.classify_discord_context(message)
            logger.debug(f"Server context classified: {message_context.context_type.value} (security: {message_context.security_level.value}, server: {message.guild.name})")
            
            relevant_memories = self.memory_manager.retrieve_context_aware_memories(
                user_id, content, message_context, limit=20
            )
            
            emotion_context = ""
            if hasattr(self.memory_manager, 'get_emotion_context'):
                emotion_context = self.memory_manager.get_emotion_context(user_id)
                
        except (MemoryRetrievalError, ValidationError) as e:
            logger.warning(f"Could not retrieve memories for user {user_id}: {e}")
            relevant_memories = []
            emotion_context = ""
        except Exception as e:
            logger.error(f"Unexpected error retrieving memories: {e}")
            relevant_memories = []
            emotion_context = ""
        
        # Get recent conversation history (guild-specific)
        recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
        
        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, None, content
        )
        
        # External emotion analysis for guild message (always available when configured)
        external_emotion_data = None
        if self.external_emotion_ai:
            external_emotion_data = await self._analyze_external_emotion(
                content, user_id, conversation_context
            )
        
        # Phase 2 emotional intelligence for guild message (always available when configured)
        phase2_context = None
        current_emotion_data = None
        if self.phase2_integration:
            phase2_context, current_emotion_data = await self._analyze_phase2_emotion(
                user_id, content, message, context_type='guild_message'
            )
        
        # Process message with images (content with mentions removed)
        conversation_context = await process_message_with_images(
            content, message.attachments, conversation_context,
            self.llm_client, self.image_processor
        )
        
        # Generate and send response for guild mention
        await self._generate_and_send_response(
            reply_channel, message, user_id, conversation_context,
            current_emotion_data, external_emotion_data, phase2_context,
            None, None, original_content=content
        )
    
    async def _get_recent_messages(self, channel, user_id, exclude_message_id):
        """Get recent conversation messages for context."""
        if self.conversation_cache:
            # Use cache with user-specific filtering
            recent_messages = await self.conversation_cache.get_user_conversation_context(
                channel, 
                user_id=int(user_id),
                limit=15,
                exclude_message_id=exclude_message_id
            )
            
            # Supplement with ChromaDB if insufficient
            if len(recent_messages) < 8:
                logger.debug(f"Supplementing {len(recent_messages)} cached messages with ChromaDB history for user {user_id}")
                try:
                    chromadb_memories = self.safe_memory_manager.retrieve_relevant_memories(
                        user_id, 
                        query="conversation history recent messages",
                        limit=15
                    )
                    
                    # Process ChromaDB memories into message format
                    conversation_count = 0
                    for memory in reversed(chromadb_memories):
                        metadata = memory.get('metadata', {})
                        
                        if 'user_message' in metadata and 'bot_response' in metadata:
                            # Add user message
                            recent_messages.append({
                                'content': metadata['user_message'][:500],
                                'author_id': user_id,
                                'author_name': metadata.get('user_name', 'User'),
                                'timestamp': metadata.get('timestamp', ''),
                                'bot': False,
                                'from_chromadb': True
                            })
                            # Add bot response
                            recent_messages.append({
                                'content': metadata['bot_response'][:500],
                                'author_id': str(self.bot.user.id) if self.bot.user else 'bot',
                                'author_name': self.bot.user.display_name if self.bot.user else 'Bot',
                                'timestamp': metadata.get('timestamp', ''),
                                'bot': True,
                                'from_chromadb': True
                            })
                            
                            conversation_count += 1
                            if conversation_count >= 5:
                                break
                    
                    if conversation_count > 0:
                        recent_messages = recent_messages[-20:]
                        logger.debug(f"Enhanced context with {conversation_count} ChromaDB conversations: now have {len(recent_messages)} messages")
                        
                except Exception as e:
                    logger.warning(f"Could not supplement with ChromaDB conversations: {e}")
            
            return recent_messages
        else:
            # Fallback to Discord history
            logger.warning(f"Conversation cache unavailable, pulling directly from Discord history for channel {channel.id}")
            current_user_id = int(user_id)
            all_messages = [msg async for msg in channel.history(limit=50)]
            
            # Filter for current user and bot messages only
            user_filtered_messages = []
            for msg in all_messages:
                if msg.id == exclude_message_id:
                    continue
                
                if msg.author.id == current_user_id or msg.author.bot:
                    user_filtered_messages.append(msg)
            
            user_filtered_messages.reverse()
            return user_filtered_messages[-15:] if len(user_filtered_messages) >= 15 else user_filtered_messages
    
    async def _build_conversation_context(self, message, relevant_memories, emotion_context, recent_messages, enhanced_system_prompt, content=None):
        """Build conversation context for LLM."""
        conversation_context = []
        
        # Store Discord user information
        store_discord_user_info(message.author, self.memory_manager)
        if message.guild:
            store_discord_server_info(message.guild, self.memory_manager)
        
        # Start with system message
        time_context = get_current_time_context()
        from src.core.config import get_system_prompt
        system_prompt_content = enhanced_system_prompt if enhanced_system_prompt else get_system_prompt()
        conversation_context.append({"role": "system", "content": system_prompt_content})
        
        # Add time and emotion context
        conversation_context.append({"role": "system", "content": f"Current time: {time_context}"})
        
        if emotion_context:
            conversation_context.append({"role": "system", "content": f"User relationship and emotional context: {emotion_context}"})
            logger.debug(f"Added emotion context for user {message.author.id}: {emotion_context}")
        
        # Add relevant memories
        if relevant_memories:
            memory_context = "Previous conversation context:\n"
            
            # Separate global and user-specific memories
            global_facts = [m for m in relevant_memories if m['metadata'].get('is_global', False)]
            user_memories = [m for m in relevant_memories if not m['metadata'].get('is_global', False)]
            
            if global_facts:
                memory_context += "\nGlobal Facts (about the world, relationships, and the bot):\n"
                for memory in global_facts:
                    if memory['metadata'].get('type') == 'global_fact':
                        memory_context += f"- {memory['metadata']['fact']}\n"
            
            if user_memories:
                memory_context += "\nUser-specific information:\n"
                for memory in user_memories:
                    if 'user_message' in memory['metadata']:
                        memory_context += f"- User previously mentioned: {memory['metadata']['user_message'][:500]}\n"
                        memory_context += f"- Your response was about: {memory['metadata']['bot_response'][:500]}\n"
                    elif memory['metadata'].get('type') == 'user_fact':
                        memory_context += f"- User fact: {memory['metadata']['fact']}\n"
            
            conversation_context.append({"role": "system", "content": memory_context})
        
        # Generate conversation summary
        conversation_summary = generate_conversation_summary(recent_messages, str(message.author.id))
        if conversation_summary:
            conversation_context.append({"role": "system", "content": f"Recent conversation summary: {conversation_summary}"})
            logger.debug(f"Added conversation summary for user {message.author.id}")
        
        # Add recent messages with proper alternation
        user_assistant_messages = []
        filtered_messages = list(reversed(recent_messages[1:]))  # Skip current message
        
        # Filter out commands and responses
        skip_next_bot_response = False
        for msg in filtered_messages:
            msg_content = get_message_content(msg)
            if msg_content.startswith('!'):
                logger.debug(f"Skipping command from conversation history: {msg_content[:50]}...")
                skip_next_bot_response = True
                continue
            
            if message_equals_bot_user(msg, self.bot.user) and skip_next_bot_response:
                logger.debug(f"Skipping bot response to command: {msg_content[:50]}...")
                skip_next_bot_response = False
                continue
            
            if not message_equals_bot_user(msg, self.bot.user):
                skip_next_bot_response = False
            
            role = "assistant" if message_equals_bot_user(msg, self.bot.user) else "user"
            user_assistant_messages.append({"role": role, "content": msg_content})
        
        # Apply alternation fix
        fixed_history = fix_message_alternation(user_assistant_messages)
        conversation_context.extend(fixed_history)
        
        return conversation_context
    
    async def _analyze_external_emotion(self, content, user_id, conversation_context):
        """Analyze emotion using external API."""
        try:
            logger.debug("Running External API Emotion AI analysis (full capabilities)...")
            
            conversation_history = [msg['content'] for msg in conversation_context[-10:] if msg['role'] == 'user']
            
            if not hasattr(self.external_emotion_ai, 'session') or self.external_emotion_ai.session is None:
                await self.external_emotion_ai.initialize()
            
            external_emotion_data = await self.external_emotion_ai.analyze_emotion_cloud(
                text=content,
                user_id=user_id,
                conversation_history=conversation_history
            )
            
            logger.debug(f"External emotion analysis completed: {external_emotion_data.get('primary_emotion', 'unknown')} "
                       f"(confidence: {external_emotion_data.get('confidence', 0):.2f})")
            
            if external_emotion_data.get('analysis_time_ms'):
                logger.debug(f"Emotion analysis took {external_emotion_data['analysis_time_ms']:.1f}ms "
                           f"({external_emotion_data.get('api_calls_made', 0)} API calls)")
            
            return external_emotion_data
            
        except Exception as e:
            logger.error(f"External API Emotion AI analysis failed: {e}")
            return None
    
    async def _analyze_phase2_emotion(self, user_id, content, message, context_type='discord_conversation'):
        """Analyze emotion using Phase 2 integration."""
        try:
            logger.debug("Running Phase 2 emotional intelligence analysis...")
            
            phase2_context = {
                'topic': 'general',
                'communication_style': 'casual',
                'user_id': user_id,
                'message_length': len(content),
                'timestamp': datetime.now().isoformat(),
                'context': context_type
            }
            
            if message.guild:
                phase2_context['guild_id'] = str(message.guild.id)
                phase2_context['channel_id'] = str(message.channel.id)
            
            phase2_results = await self.phase2_integration.process_message_with_emotional_intelligence(
                user_id=user_id,
                message=content,
                conversation_context=phase2_context
            )
            
            logger.debug("Phase 2 emotional intelligence analysis completed")
            return phase2_results, None  # Return results and placeholder for current_emotion_data
            
        except Exception as e:
            logger.error(f"Phase 2 emotional intelligence analysis failed: {e}")
            return None, None
    
    async def _process_phase4_intelligence(self, user_id, message, recent_messages, external_emotion_data, phase2_context):
        """Process Phase 4 human-like conversation intelligence."""
        try:
            logger.debug("Running Phase 4: Human-Like Conversation Intelligence...")
            
            discord_context = {
                'channel_id': str(message.channel.id),
                'guild_id': str(message.guild.id) if message.guild else None,
                'channel_type': 'dm' if message.guild is None else 'guild',
                'user_display_name': message.author.display_name,
                'external_emotion_data': external_emotion_data,
                'phase2_results': phase2_context
            }
            
            phase4_context = await self.memory_manager.process_with_phase4_intelligence(
                user_id=user_id,
                message=message.content,
                conversation_context=recent_messages,
                discord_context=discord_context
            )
            
            comprehensive_context = None
            enhanced_system_prompt = None
            
            if hasattr(self.memory_manager, 'get_phase4_response_context'):
                comprehensive_context = self.memory_manager.get_phase4_response_context(phase4_context)
                
                from src.intelligence.phase4_integration import create_phase4_enhanced_system_prompt
                from src.core.config import get_system_prompt
                enhanced_system_prompt = create_phase4_enhanced_system_prompt(
                    phase4_context=phase4_context,
                    base_system_prompt=get_system_prompt(),
                    comprehensive_context=comprehensive_context
                )
                
                phases_executed = []
                if hasattr(phase4_context, 'processing_metadata'):
                    if isinstance(phase4_context.processing_metadata, dict):
                        phases_executed = phase4_context.processing_metadata.get('phases_executed', [])
                    elif isinstance(phase4_context.processing_metadata, list):
                        phases_executed = phase4_context.processing_metadata
                    else:
                        phases_executed = []
                
                # Handle different Phase4Context versions (simple vs full integration)
                conversation_mode = getattr(phase4_context, 'conversation_mode', None)
                conversation_mode_str = conversation_mode.value if conversation_mode else 'unknown'
                
                logger.debug(f"Phase 4 analysis completed: {conversation_mode_str} mode, "
                           f"{phase4_context.interaction_type.value} interaction, "
                           f"{len(phases_executed)} phases executed")
            
            return phase4_context, comprehensive_context, enhanced_system_prompt
            
        except Exception as e:
            logger.error(f"Phase 4 human-like intelligence processing failed: {e}")
            return None, None, None
    
    async def _generate_and_send_response(self, reply_channel, message, user_id, conversation_context, 
                                         current_emotion_data, external_emotion_data, phase2_context,
                                         phase4_context=None, comprehensive_context=None, original_content=None):
        """Generate AI response and send to channel using Universal Chat Architecture."""
        # Show typing indicator
        async with reply_channel.typing():
            logger.debug("Started typing indicator - simulating thinking and typing process")
            try:
                logger.debug("Processing message through Universal Chat Orchestrator...")
                
                # Use Universal Chat Orchestrator if available
                if self.chat_orchestrator:
                    logger.debug("Using Universal Chat Orchestrator for proper layered architecture")
                    
                    # Convert Discord message to universal format
                    if hasattr(self.chat_orchestrator, 'adapters') and ChatPlatform.DISCORD in self.chat_orchestrator.adapters:
                        discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                        universal_message = discord_adapter.discord_message_to_universal_message(message)
                        
                        # Get or create conversation
                        conversation = await self.chat_orchestrator.get_or_create_conversation(universal_message)
                        
                        # Generate AI response through orchestrator
                        ai_response = await self.chat_orchestrator.generate_ai_response(universal_message, conversation)
                        
                        response = ai_response.content
                        logger.debug(f"Universal Chat response: {len(response)} characters")
                        logger.debug(f"Model used: {ai_response.model_used}, Tokens: {ai_response.tokens_used}")
                        
                    else:
                        logger.warning("Discord adapter not found in orchestrator, falling back to direct LLM")
                        response = await self._fallback_direct_llm_response(conversation_context)
                        
                else:
                    logger.warning("Universal Chat Orchestrator not available, falling back to direct LLM")
                    response = await self._fallback_direct_llm_response(conversation_context)
                
                # Security scan for system leakage
                leakage_scan = scan_response_for_system_leakage(response)
                if leakage_scan['has_leakage']:
                    logger.error(f"SECURITY: System message leakage detected in response to user {user_id}")
                    logger.error(f"SECURITY: Leaked patterns: {leakage_scan['leaked_patterns']}")
                    response = leakage_scan['sanitized_response']
                    logger.info("SECURITY: Response sanitized to remove system message leakage")
                
                # Store conversation in memory
                await self._store_conversation_memory(
                    message, user_id, response, current_emotion_data, 
                    external_emotion_data, phase2_context, phase4_context, 
                    comprehensive_context, original_content
                )
                
                # Add debug information if needed
                response_with_debug = add_debug_info_to_response(response, user_id, self.memory_manager, str(message.id))
                
                # Send response (chunked if too long)
                await self._send_response_chunks(reply_channel, response_with_debug)
                
                # Send voice response if applicable
                await self._send_voice_response(message, response)
                
                # Add user message to cache after successful processing
                if self.conversation_cache:
                    if hasattr(self.conversation_cache, 'add_message'):
                        if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                            await self.conversation_cache.add_message(str(reply_channel.id), message)
                        else:
                            self.conversation_cache.add_message(str(reply_channel.id), message)
                    logger.debug("Added user message to conversation cache after successful processing")
                
            except LLMConnectionError:
                logger.warning("LLM connection error")
                await reply_channel.send("*The pathways between realms have grown dim...* I cannot reach the source of wisdom at this moment. Pray, try again shortly.")
            except LLMTimeoutError:
                logger.warning("LLM timeout error")
                await reply_channel.send("*Time moves strangely in the realm of dreams...* Thy words have taken too long to reach me. Speak again, if thou wilt.")
            except LLMRateLimitError:
                logger.warning("LLM rate limit error")
                await reply_channel.send("*The flow of dreams grows heavy with too many seekers...* Grant me a moment's respite, then we may speak once more.")
            except LLMError as e:
                logger.error(f"LLM error: {e}")
                await reply_channel.send("*The threads of thought grow tangled for a moment...* Please, speak again, and I shall attend to thy words more clearly.")
            except Exception as e:
                logger.error(f"Unexpected error processing message through Universal Chat: {e}")
                await reply_channel.send("*Something stirs in the darkness beyond my understanding...* Perhaps we might try this exchange anew?")
    
    async def _fallback_direct_llm_response(self, conversation_context):
        """Fallback to direct LLM client when Universal Chat is unavailable."""
        if self.llm_client is None:
            logger.error("LLM client is not initialized")
            return "The threads of consciousness are not yet woven. My deeper mind remains unreachable for now."
            
        # Check LLM connection
        if not await self.llm_client.check_connection_async():
            logger.warning("LLM connection unavailable when trying to respond")
            return "⚠️ I can't connect to the LLM server right now. Make sure your LLM provider is running."
        
        logger.debug("Sending request to LLM (fallback)...")
        logger.debug(f"Conversation context: {len(conversation_context)} messages")
        
        # Get response from LLM directly
        response = await self.llm_client.generate_chat_completion_safe(conversation_context)
        logger.debug(f"Received LLM response (fallback): {len(response)} characters")
        
        return response
    
    async def _store_conversation_memory(self, message, user_id, response, current_emotion_data, 
                                       external_emotion_data, phase2_context, phase4_context, 
                                       comprehensive_context, original_content=None):
        """Store conversation in memory with all AI analysis data."""
        try:
            # Extract content for storage
            content_to_store = original_content if original_content else message.content
            storage_content = extract_text_for_memory_storage(content_to_store, message.attachments)
            
            # Skip empty content
            if not storage_content or not storage_content.strip():
                logger.warning(f"Empty storage content detected for user {user_id}")
                logger.info("Skipping conversation storage due to empty content")
                return
            
            logger.debug(f"Storage content length: {len(storage_content)} characters")
            
            # Prepare emotion metadata
            emotion_metadata = None
            if current_emotion_data:
                user_profile, emotion_profile = current_emotion_data
                emotion_metadata = {}
                
                if emotion_profile.detected_emotion:
                    emotion_metadata["detected_emotion"] = emotion_profile.detected_emotion.value
                if emotion_profile.confidence is not None:
                    emotion_metadata["confidence"] = float(emotion_profile.confidence)
                if emotion_profile.intensity is not None:
                    emotion_metadata["intensity"] = float(emotion_profile.intensity)
                if user_profile.relationship_level:
                    emotion_metadata["relationship_level"] = user_profile.relationship_level.value
                if user_profile.interaction_count is not None:
                    emotion_metadata["interaction_count"] = int(user_profile.interaction_count)
                
                logger.debug(f"Passing pre-analyzed emotion data to storage: {emotion_profile.detected_emotion.value if emotion_profile.detected_emotion else 'unknown'}")
            
            # Perform personality analysis
            personality_metadata = await self._analyze_personality_for_storage(user_id, storage_content, message)
            
            # Perform emotional intelligence analysis for storage
            emotional_intelligence_results = await self._analyze_emotional_intelligence_for_storage(
                user_id, storage_content, message, phase2_context, external_emotion_data
            )
            
            # Prepare storage metadata
            storage_metadata = {}
            
            # Add message context metadata
            if hasattr(self.memory_manager, 'classify_discord_context'):
                message_context = self.memory_manager.classify_discord_context(message)
                if message_context:
                    storage_metadata.update({
                        "context_type": message_context.context_type.value if hasattr(message_context.context_type, 'value') else str(message_context.context_type),
                        "server_id": message_context.server_id,
                        "channel_id": message_context.channel_id,
                        "is_private": message_context.is_private,
                        "security_level": message_context.security_level.value if hasattr(message_context.security_level, 'value') else str(message_context.security_level)
                    })
            
            # Add personality metadata
            if personality_metadata:
                personality_simple = {}
                for key, value in personality_metadata.items():
                    if value is not None:
                        if hasattr(value, 'value'):  # Enum
                            personality_simple[f"personality_{key}"] = value.value
                        elif isinstance(value, (str, int, float, bool)):
                            personality_simple[f"personality_{key}"] = value
                        else:
                            personality_simple[f"personality_{key}"] = str(value)
                storage_metadata.update(personality_simple)
            
            # Add emotional intelligence metadata
            if emotional_intelligence_results:
                emotional_simple = {}
                for key, value in emotional_intelligence_results.items():
                    if value is not None and isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subvalue is not None:
                                if hasattr(subvalue, 'value'):  # Enum
                                    emotional_simple[f"emotional_{key}_{subkey}"] = subvalue.value
                                elif isinstance(subvalue, (str, int, float, bool)):
                                    emotional_simple[f"emotional_{key}_{subkey}"] = subvalue
                                else:
                                    emotional_simple[f"emotional_{key}_{subkey}"] = str(subvalue)
                    elif value is not None:
                        if hasattr(value, 'value'):  # Enum
                            emotional_simple[f"emotional_{key}"] = value.value
                        elif isinstance(value, (str, int, float, bool)):
                            emotional_simple[f"emotional_{key}"] = value
                        else:
                            emotional_simple[f"emotional_{key}"] = str(value)
                storage_metadata.update(emotional_simple)
            
            # Store with thread-safe operations
            storage_success = await self.safe_memory_manager.store_conversation_safe(
                user_id, storage_content, response,
                channel_id=str(message.channel.id),
                pre_analyzed_emotion_data=emotion_metadata,
                metadata=storage_metadata
            )
            
            # Sync cache with storage result
            if self.conversation_cache and hasattr(self.conversation_cache, 'sync_with_storage'):
                import inspect
                if inspect.iscoroutinefunction(self.conversation_cache.sync_with_storage):
                    await self.conversation_cache.sync_with_storage(str(message.channel.id), message, storage_success)
                else:
                    self.conversation_cache.sync_with_storage(str(message.channel.id), message, storage_success)
            
            logger.debug(f"Stored conversation for user {user_id} - original message only")
            
        except (MemoryStorageError, ValidationError) as e:
            logger.warning(f"Could not store conversation: {e}")
        except Exception as e:
            logger.error(f"Unexpected error storing conversation: {e}")
    
    async def _analyze_personality_for_storage(self, user_id, storage_content, message):
        """Analyze personality for conversation storage."""
        personality_metadata = None
        if self.personality_profiler and user_id:
            try:
                recent_messages = [storage_content]
                
                # Get additional recent messages for better analysis
                try:
                    message_context = self.memory_manager.classify_discord_context(message)
                    recent_context = await self.safe_memory_manager.get_recent_conversations(
                        user_id, limit=10, context=message_context
                    )
                    if recent_context and hasattr(recent_context, 'conversations'):
                        for conv in recent_context.conversations[-9:]:
                            if hasattr(conv, 'user_message') and conv.user_message:
                                recent_messages.append(conv.user_message)
                except Exception as e:
                    logger.debug(f"Could not retrieve recent messages for personality analysis: {e}")
                
                if len(recent_messages) >= 1:
                    logger.debug(f"Analyzing personality with {len(recent_messages)} messages for user {user_id}")
                    
                    if self.graph_personality_manager:
                        # Use graph-enhanced personality manager
                        personality_summary = await self.graph_personality_manager.analyze_and_store_personality(
                            user_id, recent_messages, {
                                "channel_id": str(message.channel.id),
                                "guild_id": str(message.guild.id) if message.guild else None,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "context": "discord_conversation"
                            }
                        )
                        if personality_summary:
                            personality_metadata = {
                                "communication_style": personality_summary.get('communication_style', {}).get('primary', 'unknown'),
                                "confidence_level": personality_summary.get('communication_style', {}).get('confidence_level', 'unknown'),
                                "decision_style": personality_summary.get('behavioral_patterns', {}).get('decision_style', 'unknown'),
                                "analysis_confidence": personality_summary.get('analysis_meta', {}).get('confidence', 0.0)
                            }
                            logger.debug(f"Personality analysis: {personality_metadata}")
                    else:
                        # Use standalone personality profiler
                        metrics = self.personality_profiler.analyze_personality(recent_messages, user_id)
                        summary = self.personality_profiler.get_personality_summary(metrics)
                        personality_metadata = {
                            "communication_style": summary.get('communication_style', {}).get('primary', 'unknown'),
                            "confidence_level": summary.get('communication_style', {}).get('confidence_level', 'unknown'),
                            "decision_style": summary.get('behavioral_patterns', {}).get('decision_style', 'unknown'),
                            "analysis_confidence": summary.get('analysis_meta', {}).get('confidence', 0.0)
                        }
                        logger.debug(f"Standalone personality analysis: {personality_metadata}")
                        
            except Exception as e:
                logger.warning(f"Personality analysis failed for user {user_id}: {e}")
                personality_metadata = None
        
        return personality_metadata
    
    async def _analyze_emotional_intelligence_for_storage(self, user_id, storage_content, message, phase2_context, external_emotion_data):
        """Analyze emotional intelligence for conversation storage."""
        emotional_intelligence_results = None
        if self.phase2_integration and user_id:
            try:
                logger.debug(f"Performing emotional intelligence analysis for user {user_id}")
                
                context = {
                    "channel_id": str(message.channel.id),
                    "guild_id": str(message.guild.id) if message.guild else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": "discord_conversation"
                }
                
                # Use existing phase2_context if available, otherwise analyze
                if phase2_context:
                    emotional_intelligence_results = phase2_context
                else:
                    emotional_intelligence_results = await self.phase2_integration.process_message_with_emotional_intelligence(
                        user_id=user_id,
                        message=storage_content,
                        conversation_context=context
                    )
                
                # Enhance with external emotion data
                if emotional_intelligence_results and external_emotion_data:
                    emotional_intelligence_results['external_emotion_analysis'] = external_emotion_data
                    logger.debug(f"Enhanced emotional intelligence with external API data: {external_emotion_data.get('primary_emotion', 'unknown')}")
                elif external_emotion_data and not emotional_intelligence_results:
                    emotional_intelligence_results = {
                        'external_emotion_analysis': external_emotion_data,
                        'primary_emotion_source': 'external_api',
                        'emotion_confidence': external_emotion_data.get('confidence', 0.5),
                        'emotion_tier': external_emotion_data.get('tier_used', 'unknown')
                    }
                    logger.debug(f"Using external emotion data as primary emotional intelligence: {external_emotion_data.get('primary_emotion', 'unknown')}")
                
                if emotional_intelligence_results:
                    logger.debug(f"Emotional intelligence analysis complete: {emotional_intelligence_results}")
                    
            except Exception as e:
                logger.warning(f"Emotional intelligence analysis failed for user {user_id}: {e}")
                emotional_intelligence_results = None
        
        return emotional_intelligence_results
    
    async def _send_response_chunks(self, channel, response):
        """Send response in chunks if it's too long."""
        if len(response) > 2000:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            logger.info(f"Response too long ({len(response)} chars), splitting into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                await channel.send(f"{chunk}" + (f"\n*(continued {i+1}/{len(chunks)})*" if len(chunks) > 1 else ""))
                logger.debug(f"Sent chunk {i+1}/{len(chunks)}")
        else:
            await channel.send(response)
            logger.debug("Sent single message response")
    
    async def _send_voice_response(self, message, response):
        """Send voice response if user is in voice channel."""
        if self.voice_manager and message.guild and self.voice_support_enabled:
            try:
                logger.debug(f"Checking voice response for user {message.author.display_name}")
                
                if isinstance(message.author, discord.Member) and message.author.voice and message.author.voice.channel:
                    user_channel = message.author.voice.channel
                    bot_channel = self.voice_manager.get_current_channel(message.guild.id)
                    
                    logger.debug(f"User in channel: {user_channel.name if user_channel else 'None'}")
                    logger.debug(f"Bot in channel: {bot_channel.name if bot_channel else 'None'}")
                    
                    if bot_channel and user_channel.id == bot_channel.id:
                        # Clean response for TTS
                        clean_response = response.replace('*', '').replace('**', '').replace('`', '')
                        voice_max_length = int(os.getenv('VOICE_MAX_RESPONSE_LENGTH', '300'))
                        if len(clean_response) > voice_max_length:
                            clean_response = clean_response[:voice_max_length] + "..."
                        
                        logger.info(f"🎤 Sending voice response to {message.author.display_name} in voice channel: {clean_response[:50]}...")
                        await self.voice_manager.speak_message(message.guild.id, clean_response)
                    else:
                        logger.debug("Not sending voice response - user and bot not in same channel")
                else:
                    logger.debug("User not in voice channel or not a member")
            except Exception as e:
                logger.error(f"Failed to send voice response: {e}")
                import traceback
                logger.error(f"Voice response error traceback: {traceback.format_exc()}")