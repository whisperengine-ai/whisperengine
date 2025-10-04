"""
Event handlers for the Discord bot.

Extracted from main.py to improve code organization and maintainability.
Contains on_ready and on_message event handlers with all their complex logic.
"""

import asyncio
import logging
import os
import time
import traceback
from datetime import UTC, datetime
from typing import List

import discord

from src.database.database_integration import DatabaseIntegrationManager
# Redis profile memory cache - DISABLED for vector-native approach
# from src.memory.redis_profile_memory_cache import RedisProfileAndMemoryCache

# Universal Chat Platform Integration - DEPRECATED (Discord-only now)
# from src.platforms.universal_chat import (
#     ChatPlatform,
#     UniversalChatOrchestrator,
# )
from src.security.input_validator import validate_user_input
from src.security.system_message_security import scan_response_for_system_leakage
from src.core.message_processor import create_message_processor
from src.utils.exceptions import (
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    MemoryRetrievalError,
    MemoryStorageError,
    ValidationError,
)
from src.utils.context_size_manager import (
    truncate_context,
    optimize_memory_context,
    truncate_recent_messages,
    count_context_tokens,
)
from src.conversation.boundary_manager import ConversationBoundaryManager
# from src.conversation.persistent_conversation_manager import PersistentConversationManager  # REMOVED: Over-engineered follow-up system

from src.utils.helpers import (
    add_debug_info_to_response,
    extract_text_for_memory_storage,
    fix_message_alternation,
    generate_conversation_summary,
    get_current_time_context,
    get_message_content,
    message_equals_bot_user,
    process_message_with_images,
    store_discord_server_info,
    store_discord_user_info,
)
from src.utils.production_error_handler import (
    ErrorCategory, ErrorSeverity, handle_errors, 
    error_handler
)

# Vector-native prompt integration - REMOVED: unused final_integration import
from src.intelligence.vector_emoji_intelligence import EmojiResponseIntegration, EmojiResponseContext

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
        self.postgres_pool = getattr(bot_core, "postgres_pool", None)
        self.memory_manager = getattr(bot_core, "memory_manager", None)
        self.safe_memory_manager = getattr(bot_core, "safe_memory_manager", None)
        self.llm_client = getattr(bot_core, "llm_client", None)
        self.conversation_cache = getattr(bot_core, "conversation_cache", None)
        self.job_scheduler = getattr(bot_core, "job_scheduler", None)
        self.voice_manager = getattr(bot_core, "voice_manager", None)
        self.heartbeat_monitor = getattr(bot_core, "heartbeat_monitor", None)
        self.image_processor = getattr(bot_core, "image_processor", None)
        # Legacy personality profiler removed - vector-native system handles this
        self.personality_profiler = None
        self.dynamic_personality_profiler = getattr(bot_core, "dynamic_personality_profiler", None)
        self.graph_personality_manager = getattr(bot_core, "graph_personality_manager", None)
        self.phase2_integration = getattr(bot_core, "phase2_integration", None)
        # Character system reference for CDL integration
        self.character_system = getattr(bot_core, "character_system", None)
        # Legacy emotion engine removed - vector-native system handles this
        self.local_emotion_engine = None
        # Redis profile/memory cache (if enabled)
        self.profile_memory_cache = getattr(bot_core, "profile_memory_cache", None)
        
        # ConcurrentConversationManager for proper scatter-gather concurrency
        self.conversation_manager = getattr(bot_core, "conversation_manager", None)
        
        # Initialize Conversation Boundary Manager for intelligent message summarization
        redis_client = None
        if self.conversation_cache and hasattr(self.conversation_cache, 'redis'):
            redis_client = self.conversation_cache.redis
        
        self.boundary_manager = ConversationBoundaryManager(
            summarization_threshold=8,  # Start summarizing after 8 messages
            llm_client=self.llm_client,  # Pass LLM client for intelligent summarization
            redis_client=redis_client    # Pass Redis client for session persistence
        )
        
        # Initialize Persistent Conversation Manager for question tracking and follow-up continuity
        try:
            # REMOVED: Over-engineered persistent conversation manager that caused inappropriate question repetition
            self.persistent_conversation_manager = None
            logger.info("✅ Persistent Conversation Manager disabled (over-engineered feature removed)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Persistent Conversation Manager: {e}")
            self.persistent_conversation_manager = None

        # Configuration flags - unified AI system always enabled
        self.voice_support_enabled = getattr(bot_core, "voice_support_enabled", False)

        # Initialize Emoji Reaction Intelligence for multimodal emotional feedback
        from src.intelligence.emoji_reaction_intelligence import EmojiReactionIntelligence
        self.emoji_reaction_intelligence = EmojiReactionIntelligence(
            memory_manager=self.memory_manager,
            emotion_manager=self.phase2_integration
        )
        
        # Initialize Vector-Based Emoji Response Intelligence 
        self.emoji_response_intelligence = EmojiResponseIntegration(
            memory_manager=self.memory_manager
        )

        # Initialize unified MessageProcessor for consistent processing across platforms
        try:
            self.message_processor = create_message_processor(
                bot_core=bot_core,  # Pass the bot_core instance
                memory_manager=self.memory_manager,
                llm_client=self.llm_client
            )
            logger.info("✅ MessageProcessor initialized for unified processing")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MessageProcessor: {e}")
            self.message_processor = None

        # Universal Chat Orchestrator - DEPRECATED (Discord-only processing now)
        self.chat_orchestrator = None

        # Register event handlers
        self._register_events()

    # === Character Name Prefix Utilities ===
    def _clean_character_name_prefix(self, text: str) -> str:
        """Remove character name prefix from responses.
        
        Some models prepend the character name (e.g., "Dream:") to responses
        based on the system prompt. This function removes such prefixes.
        """
        import re
        
        # Get bot name from environment
        bot_name = os.getenv("DISCORD_BOT_NAME", "").strip()
        
        if bot_name:
            # Remove bot name prefix patterns like "Dream:", "**Dream:**", "*Dream:*"
            patterns = [
                rf"^\*\*{re.escape(bot_name)}\*\*:\s*",  # **Dream:**
                rf"^\*{re.escape(bot_name)}\*:\s*",      # *Dream:*
                rf"^{re.escape(bot_name)}:\s*",          # Dream:
            ]
            
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        return text.strip()

    @handle_errors(
        category=ErrorCategory.SYSTEM_RESOURCE,
        severity=ErrorSeverity.MEDIUM,
        operation="setup_universal_chat",
        max_retries=1,
        return_on_error=False
    )
    async def setup_universal_chat(self):
        """Setup Universal Chat Orchestrator for proper layered architecture"""
        try:
            logger.info("🌐 Setting up Universal Chat Orchestrator for Discord integration...")

            # Create database manager without adaptive config (using simple environment variables)
            db_manager = DatabaseIntegrationManager()

            # Create universal chat orchestrator (no adaptive config needed with Docker env vars)
            self.chat_orchestrator = UniversalChatOrchestrator(
                db_manager=db_manager
            )

            # Initialize the orchestrator
            success = await self.chat_orchestrator.initialize()
            if not success:
                logger.warning("Failed to initialize Universal Chat Orchestrator")
                self.chat_orchestrator = None
                return False

            # Set bot instance for Universal Chat to access command handlers
            if hasattr(self.chat_orchestrator, "set_bot_core"):
                self.chat_orchestrator.set_bot_core(self.bot)
                logger.info("✅ Universal Chat configured with bot instance for CDL character access")

            # Setup Discord adapter and set bot instance
            if (
                hasattr(self.chat_orchestrator, "adapters")
                and ChatPlatform.DISCORD in self.chat_orchestrator.adapters
            ):
                discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                if hasattr(discord_adapter, "set_bot_instance"):
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

        # Store instance reference to avoid naming conflicts
        event_handler_instance = self

        @self.bot.event
        async def on_ready():
            return await event_handler_instance.on_ready()

        @self.bot.event
        async def on_message(message):
            # Call the instance method without naming collision
            return await event_handler_instance.on_message(message)
        
        @self.bot.event
        async def on_reaction_add(reaction, user):
            return await event_handler_instance.on_reaction_add(reaction, user)
        
        @self.bot.event
        async def on_reaction_remove(reaction, user):
            return await event_handler_instance.on_reaction_remove(reaction, user)

    async def on_ready(self):
        """
        Handle bot ready event.

        Initializes PostgreSQL pool, starts job scheduler, sets up heartbeat monitoring,
        and configures bot presence.
        """
        logger.info(f"{self.bot.user} has connected to Discord!")
        logger.info(f"Bot is connected to {len(self.bot.guilds)} guilds")

        # Initialize PostgreSQL pool for Universal Identity (NOT for user profiles - those use vector memory)
        if self.postgres_pool is None:
            try:
                logger.info("Initializing PostgreSQL connection pool for Universal Identity...")
                # Use environment variables for PostgreSQL connection
                # PostgreSQL initialization removed - using vector-native storage only
                # (Can be re-enabled later for web UI Universal Identity integration)
                self.postgres_pool = None
                self.bot_core.postgres_pool = None
                logger.info("ℹ️ PostgreSQL disabled - using vector-native storage for Discord-only operation")

            except ConnectionError as e:
                # Clean error message for PostgreSQL connection failures
                logger.error(f"PostgreSQL connection failed: {e}")
                logger.warning("Bot will continue without PostgreSQL support")
            except Exception as e:
                logger.error(f"Unexpected error initializing PostgreSQL: {e}")
                logger.warning("Bot will continue without PostgreSQL support")

        # Initialize Redis conversation cache if using Redis
        if self.conversation_cache and hasattr(self.conversation_cache, "initialize"):
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

        # Universal Chat Orchestrator - DEPRECATED (Discord-only processing now)
        # if self.chat_orchestrator is None:
        #     try:
        #         logger.info("🌐 Initializing Universal Chat Orchestrator...")
        #         success = await self.setup_universal_chat()
        #         if success:
        #             logger.info("✅ Universal Chat Orchestrator ready for Discord integration")
        #         else:
        #             logger.warning(
        #                 "⚠️ Universal Chat Orchestrator initialization failed - using fallback"
        #             )
        #     except Exception as e:
        #         logger.error(f"Failed to initialize Universal Chat Orchestrator: {e}")

        # Initialize Production Optimization System if available
        if hasattr(self.bot_core, "production_adapter") and self.bot_core.production_adapter:
            try:
                logger.info("✨ Initializing Production Optimization System...")
                success = await self.bot_core.production_adapter.initialize_production_mode()
                if success:
                    logger.info(
                        "✅ Production optimization system activated - performance boost enabled!"
                    )
                else:
                    logger.info("📋 Production optimization system in fallback mode")
            except Exception as e:
                logger.error(f"Failed to initialize production optimization system: {e}")
                logger.warning("Bot will continue with standard performance")

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
        logger.info("✨ Bot initialization complete - ready to chat!")

        # AI pipeline components fully enabled - no fallback mode

    @handle_errors(
        category=ErrorCategory.DISCORD_API,
        severity=ErrorSeverity.HIGH,
        operation="process_discord_message",
        max_retries=2,
        return_on_error=None
    )
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
        # DEBUG: Explicit logging to see if this method is called
        logger.info(f"🔥 DEBUG: on_message called for message from {message.author.name} ({message.author.id}): '{message.content[:50]}...'")
        
        # Skip bot messages unless they're to be cached
        if message.author.bot:
            logger.info(f"🔥 DEBUG: Bot message detected from {message.author.name}, bot={message.author.bot}")
            # Add bot messages to cache for conversation context
            if self.conversation_cache and message.author == self.bot.user:
                logger.info(f"🔥 DEBUG: Caching own bot message and returning early")
                # Handle both sync and async cache implementations
                if hasattr(self.conversation_cache, "add_message"):
                    if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                        await self.conversation_cache.add_message(str(message.channel.id), message)
                    else:
                        self.conversation_cache.add_message(str(message.channel.id), message)
            else:
                logger.info(f"🔥 DEBUG: Bot message from different bot, ignoring")
            logger.info(f"🔥 DEBUG: Returning early from bot message")
            return

        logger.info(f"🔥 DEBUG: Processing user message from {message.author.name}")

        # Conditional elevated logging for debugging silent bot issues
        if os.getenv("DISCORD_MESSAGE_TRACE", "false").lower() == "true":
            logger.info(
                f"[TRACE] Received message from {message.author.name} ({message.author.id}) in {message.channel.name if message.guild else 'DM'}: {message.content[:120].replace('\n',' ')}"
            )
        else:
            logger.debug(
                f"Received message from {message.author.name} ({message.author.id}) in {message.channel.name if message.guild else 'DM'}"
            )

        # Check if the message is a DM
        if message.guild is None:
            await self._handle_dm_message(message)
        else:
            await self._handle_guild_message(message)

    async def _get_character_type_from_cdl(self) -> str:
        """
        🎯 CHARACTER-AGNOSTIC: Determine character type from CDL data instead of hardcoded names.
        Maps CDL occupation/tags to character types for emoji intelligence.
        """
        try:
            character_file = os.getenv('CDL_DEFAULT_CHARACTER')
            if not character_file:
                return "general"
                
            # Load CDL character data
            import json
            with open(character_file, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            # Extract occupation and tags for character type classification
            identity = cdl_data.get('character', {}).get('identity', {})
            metadata = cdl_data.get('character', {}).get('metadata', {})
            
            occupation = identity.get('occupation', '').lower()
            tags = [tag.lower() for tag in metadata.get('tags', [])]
            name = identity.get('name', '').lower()
            
            # Character type mapping based on CDL data
            if any(tag in tags for tag in ['scientist', 'marine_biologist', 'researcher', 'environmentalist']) or 'biologist' in occupation:
                return "mystical"  # Scientific wonder and nature connection maps to mystical
            elif any(tag in tags for tag in ['ai_researcher', 'academic', 'machine_learning', 'intellectual']) or 'ai research' in occupation:
                return "technical"  # AI research and academic focus maps to technical
            elif any(tag in tags for tag in ['eternal', 'dream_lord', 'endless', 'conceptual_being', 'mythological']) or 'dream' in occupation:
                return "mystical"  # Cosmic and mythological nature maps to mystical
            elif any(tag in tags for tag in ['adventure', 'photographer', 'outdoors', 'travel']):
                return "adventurous"  # Adventure and travel focus
            elif any(tag in tags for tag in ['british_gentleman', 'sophisticated', 'charming', 'witty']):
                return "sophisticated"  # British gentleman character
            elif any(tag in tags for tag in ['marketing', 'executive', 'business', 'professional']):
                return "professional"  # Business and professional focus
            elif any(tag in tags for tag in ['game_developer', 'indie', 'creative', 'developer']):
                return "creative"  # Creative development focus
            elif any(tag in tags for tag in ['omnipotent', 'cosmic', 'transcendent', 'godlike']):
                return "cosmic"  # Omnipotent and transcendent nature
            else:
                return "general"
                
        except Exception as e:
            logger.warning(f"Failed to determine character type from CDL: {e}")
            return "general"

    async def _handle_dm_message(self, message):
        """Handle direct message to the bot."""
        # Check if this is a command first
        if message.content.startswith("!"):
            await self.bot.process_commands(message)
            return

        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.debug(f"Processing DM from {message.author.name}")

        # Security validation
        validation_result = validate_user_input(message.content, user_id, "dm")
        # Store validation result for emoji intelligence system
        self._last_security_validation = validation_result
        
        if not validation_result["is_safe"]:
            logger.error(f"SECURITY: Unsafe input detected from user {user_id} in DM")
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            
            # 🎭 EMOJI INTELLIGENCE: Use emoji response for inappropriate content
            try:
                # 🎯 CHARACTER-AGNOSTIC: Determine bot character from CDL instead of hardcoded names
                bot_character = await self._get_character_type_from_cdl()
                
                # Evaluate emoji response for inappropriate content
                emoji_decision = await self.emoji_response_intelligence.evaluate_emoji_response(
                    user_id=user_id,
                    user_message=message.content,
                    bot_character=bot_character,
                    security_validation_result=validation_result,
                    emotional_context=None,
                    conversation_context={'channel_type': 'dm'}
                )
                
                if emoji_decision.should_use_emoji:
                    logger.info(f"🎭 SECURITY + EMOJI: Using emoji '{emoji_decision.emoji_choice}' for inappropriate content")
                    await self.emoji_response_intelligence.apply_emoji_response(message, emoji_decision)
                    return
                    
            except Exception as e:
                logger.error(f"Error in security emoji response: {e}")
            
            # Fallback to text warning if emoji response fails
            await reply_channel.send(
                "⚠️ Your message contains content that could not be processed for security reasons. Please rephrase your message."
            )
            return

        # Use sanitized content
        sanitized_content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in DM: {validation_result['warnings']}"
            )

        # Replace original message content with sanitized version
        message.content = sanitized_content

        # 🏷️ AUTO-DETECT USER NAMES: Process message for name information
        try:
            from src.utils.automatic_name_storage import create_automatic_name_storage
            from src.llm.llm_protocol import create_llm_client
            
            if self.memory_manager:
                llm_client = create_llm_client()
                name_storage = create_automatic_name_storage(self.memory_manager, llm_client)
                detected_name = await name_storage.process_message_for_names(user_id, message.content)
                if detected_name:
                    logger.info("🏷️ Auto-detected name '%s' for user %s in DM", detected_name, user_id)
        except Exception as e:
            logger.debug("Name detection failed in DM: %s", e)

        # AI identity questions are now handled naturally through CDL character responses
        # No more dirty filter patterns - let characters respond authentically

        # (User preferred name detection and storage via Postgres has been removed. See LLM tool calling roadmap for new approach.)

        # Initialize variables early
        enhanced_system_prompt = None
        phase4_context = None
        comprehensive_context = None

        # Use unified MessageProcessor if available (preferred), fallback to complex manual processing
        if self.message_processor:
            try:
                logger.info("🚀 Using unified MessageProcessor for DM processing")
                
                # Import MessageContext for creating platform-agnostic context
                from src.core.message_processor import MessageContext
                
                # Create platform-agnostic message context
                message_context = MessageContext(
                    user_id=user_id,
                    content=message.content,
                    original_content=message.content,
                    attachments=[{
                        'url': attachment.url,
                        'filename': attachment.filename,
                        'content_type': getattr(attachment, 'content_type', None)
                    } for attachment in message.attachments],
                    platform="discord",
                    channel_id=str(reply_channel.id),
                    channel_type="dm" if reply_channel.type.name == "private" else "guild",
                    metadata={
                        'discord_message_id': str(message.id),
                        'discord_author_id': str(message.author.id),
                        'discord_author_name': message.author.display_name,  # Add user display name
                        'discord_timestamp': message.created_at.isoformat()
                    }
                )
                
                # Show typing indicator while processing
                async with reply_channel.typing():
                    # Process the message with unified pipeline
                    result = await self.message_processor.process_message(message_context)
                
                if result.success:
                    # Send response using chunking method (no reply pattern for DM)
                    await self._send_response_chunks(reply_channel, result.response, reference_message=None)
                    
                    # 🎭 BOT EMOJI REACTIONS: Add emoji reaction to user's message (multimodal feedback)
                    try:
                        # Get character type from CDL for emoji selection
                        bot_character = await self._get_character_type_from_cdl()
                        
                        # Evaluate whether to add emoji reaction based on context
                        emoji_decision = await self.emoji_response_intelligence.evaluate_emoji_response(
                            user_id=user_id,
                            user_message=message.content,
                            bot_character=bot_character,
                            security_validation_result=result.metadata.get('security_validation') if result.metadata else None,
                            emotional_context=result.metadata.get('ai_components', {}).get('emotion_data') if result.metadata else None,
                            conversation_context={'channel_type': message_context.channel_type}
                        )
                        
                        # Add emoji reaction if recommended (but don't replace text response)
                        if emoji_decision.should_use_emoji:
                            logger.info(f"🎭 REACTION: Adding emoji '{emoji_decision.emoji_choice}' to user DM "
                                      f"(confidence: {emoji_decision.confidence_score:.2f}, reason: {emoji_decision.context_reason.value})")
                            await message.add_reaction(emoji_decision.emoji_choice)
                    except Exception as e:
                        logger.error(f"Error adding bot emoji reaction (non-critical): {e}")
                        # Continue - emoji reaction failure shouldn't break conversation
                    
                    # Send voice response if applicable  
                    await self._send_voice_response(message, result.response)
                    
                else:
                    # Handle processing error
                    logger.error(f"MessageProcessor returned error: {result.error_message}")
                    await reply_channel.send("I apologize, but I encountered an error processing your message. Please try again.")
                
                return  # Exit early when using MessageProcessor
                
            except Exception as e:
                logger.error(f"Error with MessageProcessor, falling back to manual processing: {e}")
                
        # Simple fallback if MessageProcessor completely unavailable
        if not self.message_processor:
            logger.warning("📋 MessageProcessor unavailable - using simple fallback")
            await reply_channel.send("I'm currently updating my systems. Please try again in a moment!")
            return

    async def _handle_guild_message(self, message):
        """Handle guild (server) message."""
        # Configurable response behavior:
        # DISCORD_RESPOND_MODE options:
        #   mention (default)  -> only reply when explicitly mentioned
        #   name               -> reply when bot name OR fallback name appears as a whole word OR mentioned
        #   all                -> reply to any non-command message in guild channel (acts like a chat bot)
        # Backward compatibility: if REQUIRE_DISCORD_MENTION=true force mention mode.

        try:
            respond_mode = os.getenv("DISCORD_RESPOND_MODE", "mention").lower().strip()
            if os.getenv("REQUIRE_DISCORD_MENTION", "false").lower() == "true":
                respond_mode = "mention"
        except Exception:
            respond_mode = "mention"

        # Fast‑path for commands (always allow the command system to process first)
        # Commands are handled by discord.py after this method returns from process_commands
        # We avoid double-processing: if command prefix matches, let process_commands handle and exit early
        command_prefix = os.getenv("DISCORD_COMMAND_PREFIX", "!")
        if message.content.startswith(command_prefix):
            await self.bot.process_commands(message)
            return

        bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
        fallback_name = "whisperengine"
        content_lower = message.content.lower()
        content_words = content_lower.split()

        should_active_reply = False

        # Mention always triggers active reply
        if self.bot.user in message.mentions:
            should_active_reply = True
        else:
            if respond_mode == "name":
                # Check if bot name appears anywhere in message (improved detection)
                name_found = False
                if bot_name:
                    # Check both as separate word and as substring
                    if bot_name in content_words or bot_name in content_lower:
                        name_found = True
                # Also check fallback name
                if fallback_name in content_words or fallback_name in content_lower:
                    name_found = True
                
                if name_found:
                    should_active_reply = True
                    logger.debug(f"Bot name detected in message: '{message.content[:50]}...'")
            elif respond_mode == "all":
                should_active_reply = True
            # mention mode (default) leaves should_active_reply False unless mentioned

        # Optional verbose logging when debugging interaction issues
        if logger.isEnabledFor(logging.INFO) and should_active_reply:
            logger.info(
                "💬 Guild message triggering reply (mode=%s, author=%s, channel=%s): %.80s",
                respond_mode,
                getattr(message.author, 'name', 'unknown'),
                getattr(message.channel, 'name', 'dm'),
                message.content.replace("\n", " "),
            )
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Guild message received (mode=%s, reply=%s, author=%s, channel=%s)",
                respond_mode,
                should_active_reply,
                getattr(message.author, 'name', 'unknown'),
                getattr(message.channel, 'name', 'dm'),
            )

        if should_active_reply:
            await self._handle_mention_message(message)
        else:
            # Still allow command processing (in case of edge cases like missing prefix detection)
            await self.bot.process_commands(message)

    async def _handle_mention_message(self, message):
        """Handle message where bot is mentioned."""
        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.info(f"[CONV-CTX] Handling mention message_id={message.id} user_id={user_id} channel_id={getattr(message.channel, 'id', None)} guild_id={getattr(message.guild, 'id', None)} content='{message.content[:60]}'")

        # Remove mentions from content
        content = message.content
        logger.info(f"[CONV-CTX] Original message content: '{message.content}'")
        for mention in message.mentions:
            if mention == self.bot.user:
                content = (
                    content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "").strip()
                )
        logger.info(f"[CONV-CTX] Content after mention removal: '{content}'")

        if not content:
            logger.info(f"[CONV-CTX] No content after mention removal, processing as command")
            await self.bot.process_commands(message)
            return

        # Security validation for guild messages
        validation_result = validate_user_input(content, user_id, "server_channel")
        if not validation_result["is_safe"]:
            logger.error(
                f"SECURITY: Unsafe input detected from user {user_id} in server {message.guild.name}"
            )
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            
            # 🎭 EMOJI INTELLIGENCE: Use emoji response for inappropriate content
            try:
                # 🎯 CHARACTER-AGNOSTIC: Determine bot character from CDL instead of hardcoded names
                bot_character = await self._get_character_type_from_cdl()
                
                # Evaluate emoji response for inappropriate content
                emoji_decision = await self.emoji_response_intelligence.evaluate_emoji_response(
                    user_id=user_id,
                    user_message=content,
                    bot_character=bot_character,
                    security_validation_result=validation_result,
                    emotional_context=None,
                    conversation_context={'channel_type': 'guild'}
                )
                
                if emoji_decision.should_use_emoji:
                    logger.info(f"🎭 SECURITY + EMOJI: Adding emoji '{emoji_decision.emoji_choice}' for inappropriate content in guild")
                    await message.add_reaction(emoji_decision.emoji_choice)
                    
            except Exception as e:
                logger.error(f"Error in security emoji response: {e}")
            
            # Send text warning (with or without emoji)
            security_msg = f"⚠️ {message.author.mention} Your message contains content that could not be processed for security reasons. Please rephrase your message."
            await message.reply(security_msg, mention_author=False)  # mention_author=False since we already include the mention
            return

        content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in server {message.guild.name}: {validation_result['warnings']}"
            )

        # AI identity questions are now handled naturally through CDL character responses
        # No more dirty filter patterns - let characters respond authentically

        # Use unified MessageProcessor for guild mentions (same as DMs)
        if self.message_processor:
            try:
                logger.info("🚀 Using unified MessageProcessor for guild mention processing")
                
                # Import MessageContext for creating platform-agnostic context
                from src.core.message_processor import MessageContext
                
                # Create platform-agnostic message context for guild mention
                message_context = MessageContext(
                    user_id=user_id,
                    content=content,
                    original_content=message.content,
                    attachments=[{
                        'url': attachment.url,
                        'filename': attachment.filename,
                        'content_type': getattr(attachment, 'content_type', None)
                    } for attachment in message.attachments],
                    platform="discord",
                    channel_id=str(reply_channel.id),
                    channel_type="guild",
                    metadata={
                        'discord_message_id': str(message.id),
                        'discord_author_id': str(message.author.id),
                        'discord_author_name': message.author.display_name,  # Add user display name
                        'discord_timestamp': message.created_at.isoformat(),
                        'discord_guild_id': str(message.guild.id),
                        'discord_guild_name': message.guild.name,
                        'discord_channel_name': getattr(message.channel, 'name', 'unknown'),
                        'mention_processed': True
                    }
                )
                
                # Process the message with unified pipeline
                # Show typing indicator while processing
                async with reply_channel.typing():
                    result = await self.message_processor.process_message(message_context)
                
                if result.success:
                    # Send response using chunking method with reply pattern for guild mentions
                    await self._send_response_chunks(reply_channel, result.response, reference_message=message)
                    
                    # 🎭 BOT EMOJI REACTIONS: Add emoji reaction to user's mention (multimodal feedback)
                    try:
                        # Get character type from CDL for emoji selection
                        bot_character = await self._get_character_type_from_cdl()
                        
                        # Evaluate whether to add emoji reaction based on context
                        emoji_decision = await self.emoji_response_intelligence.evaluate_emoji_response(
                            user_id=user_id,
                            user_message=content,
                            bot_character=bot_character,
                            security_validation_result=result.metadata.get('security_validation') if result.metadata else None,
                            emotional_context=result.metadata.get('ai_components', {}).get('emotion_data') if result.metadata else None,
                            conversation_context={'channel_type': message_context.channel_type}
                        )
                        
                        # Add emoji reaction if recommended (but don't replace text response)
                        if emoji_decision.should_use_emoji:
                            logger.info(f"🎭 REACTION: Adding emoji '{emoji_decision.emoji_choice}' to user mention "
                                      f"(confidence: {emoji_decision.confidence_score:.2f}, reason: {emoji_decision.context_reason.value})")
                            await message.add_reaction(emoji_decision.emoji_choice)
                    except Exception as e:
                        logger.error(f"Error adding bot emoji reaction (non-critical): {e}")
                        # Continue - emoji reaction failure shouldn't break conversation
                    
                    # Send voice response if applicable
                    await self._send_voice_response(message, result.response)
                    
                else:
                    # Handle processing error
                    logger.error(f"MessageProcessor returned error: {result.error_message}")
                    await message.reply("I apologize, but I encountered an error processing your message. Please try again.", mention_author=False)
                
                return  # Exit early when using MessageProcessor
                
            except Exception as e:
                logger.error(f"Error with MessageProcessor in guild mention, falling back to basic response: {e}")
                
        # Simple fallback if MessageProcessor unavailable
        if not self.message_processor:
            logger.warning("📋 MessageProcessor unavailable for guild mention - using simple fallback")
            await message.reply("I'm currently updating my systems. Please try again in a moment!", mention_author=False)
            return

    async def _get_intelligent_conversation_summary(self, channel, user_id, message):
        """Use boundary manager to create intelligent conversation summary instead of crude truncation."""
        try:
            # Convert timezone-aware datetime to timezone-naive for boundary manager compatibility
            timestamp = message.created_at
            if timestamp.tzinfo is not None:
                timestamp = timestamp.replace(tzinfo=None)
                
            # Process the current message with boundary manager
            session = await self.boundary_manager.process_message(
                user_id=str(user_id),
                channel_id=str(channel.id),
                message_id=str(message.id),
                message_content=message.content,
                timestamp=timestamp
            )
            
            # Check if we have a conversation summary from boundary manager
            if session.context_summary and len(session.context_summary) > 20:
                logger.info(f"🧠 Using intelligent conversation summary for user {user_id}: {len(session.context_summary)} chars")
                return session.context_summary
            
            # If no summary yet, fall back to recent messages
            return None
            
        except Exception as e:
            logger.warning(f"Boundary manager summarization failed for user {user_id}: {e}")
            return None

    async def _get_recent_messages(self, channel, user_id, exclude_message_id):
        """Get recent conversation messages for context."""
        
        def _standardize_message_object(msg):
            """Convert any message object to a standardized dict format."""
            if isinstance(msg, dict):
                return msg
            # Handle Discord Message object
            elif hasattr(msg, 'content') and hasattr(msg, 'author'):
                return {
                    "content": msg.content or "",
                    "author_id": str(msg.author.id),
                    "author_name": msg.author.display_name,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else "",
                    "bot": msg.author.id == self.bot.user.id if self.bot.user else False,
                    "from_discord": True,
                }
            else:
                # Fallback for unknown object types
                return {
                    "content": str(msg),
                    "author_id": "unknown",
                    "author_name": "Unknown",
                    "timestamp": "",
                    "bot": False,
                    "from_unknown": True,
                }
        
        if self.conversation_cache:
            logger.info(f"🔥 CACHE DEBUG: Getting conversation context for user {user_id} in channel {channel.id}")
            # Use cache with user-specific filtering - RESTORE BETTER CONTINUITY
            recent_messages = await self.conversation_cache.get_user_conversation_context(
                channel, user_id=int(user_id), limit=15, exclude_message_id=exclude_message_id  # Increased back to 15 for better continuity
            )
            
            logger.info(f"🔥 CACHE DEBUG: Retrieved {len(recent_messages)} messages from cache")
            for i, msg in enumerate(recent_messages):
                author_name = msg.get('author_name', 'Unknown')
                content = msg.get('content', '')[:100]
                is_bot = msg.get('bot', False)
                logger.info(f"🔥 CACHE DEBUG: Message {i+1}: [{author_name}] (bot={is_bot}): '{content}...'")
            
            # Apply additional message truncation to prevent context explosion
            recent_messages = truncate_recent_messages(recent_messages, max_messages=15)
            
            logger.info(f"🔥 CACHE DEBUG: After truncation: {len(recent_messages)} messages")
            
            # Standardize all message objects to dict format
            recent_messages = [_standardize_message_object(msg) for msg in recent_messages]
            
            logger.info(f"🔥 CACHE DEBUG: After standardization: {len(recent_messages)} messages")

            # Supplement with vector memory if insufficient
            if len(recent_messages) < 15:
                logger.debug(
                    f"Supplementing {len(recent_messages)} cached messages with vector memory for user {user_id}"
                )
                try:
                    # Use vector memory manager to get recent conversation history
                    memory_manager = self.memory_manager
                    if memory_manager and hasattr(memory_manager, 'get_recent_conversations'):
                        # Use the proper conversation history method
                        vector_conversations = await memory_manager.get_recent_conversations(
                            user_id, limit=15
                        )
                    else:
                        logger.warning("No vector memory manager available, skipping supplement")
                        vector_conversations = []

                    # DEBUG: Log what vector memory is returning
                    logger.debug(f"[VECTOR-DEBUG] Retrieved {len(vector_conversations)} conversations for user {user_id}")
                    for i, conv in enumerate(vector_conversations[:3]):  # Log first 3
                        user_msg = conv.get('user_message', 'N/A')[:100] if isinstance(conv, dict) else 'N/A'
                        bot_response = conv.get('bot_response', 'N/A')[:100] if isinstance(conv, dict) else 'N/A'
                        logger.debug(f"[VECTOR-DEBUG] Conversation {i}: user_msg='{user_msg}...' bot_response='{bot_response}...'")

                    # Process vector memory conversations into message format
                    conversation_count = 0
                    for conversation in reversed(vector_conversations):
                        if isinstance(conversation, dict):
                            user_content = conversation.get("user_message", "")[:500]
                            bot_content = conversation.get("bot_response", "")[:500]
                        else:
                            # Handle other conversation formats
                            user_content = str(conversation)[:500] if conversation else ""
                            bot_content = ""
                        
                        if user_content:
                            # CONTEXT DEBUG: Log what's being added to conversation context
                            logger.debug(f"[CONTEXT-DEBUG] Adding vector conversation:")
                            logger.debug(f"[CONTEXT-DEBUG] User: '{user_content}'")
                            logger.debug(f"[CONTEXT-DEBUG] Bot: '{bot_content}'")
                            
                            # Add user message
                            recent_messages.append(
                                {
                                    "content": user_content,
                                    "author_id": user_id,
                                    "author_name": "User",  # Simplified for vector data
                                    "timestamp": conversation.get("timestamp", "") if isinstance(conversation, dict) else "",
                                    "bot": False,
                                    "from_vector": True,
                                }
                            )
                            # Add bot response if available
                            if bot_content:
                                recent_messages.append(
                                    {
                                        "content": bot_content,
                                        "author_id": str(self.bot.user.id) if self.bot.user else "bot",
                                        "author_name": (
                                            self.bot.user.display_name if self.bot.user else "Bot"
                                        ),
                                        "timestamp": conversation.get("timestamp", "") if isinstance(conversation, dict) else "",
                                        "bot": True,
                                        "from_vector": True,
                                    }
                                )

                            conversation_count += 1
                            if conversation_count >= 5:
                                break

                    if conversation_count > 0:
                        recent_messages = recent_messages[-20:]
                        logger.debug(
                            f"Enhanced context with {conversation_count} vector conversations: now have {len(recent_messages)} messages"
                        )

                except Exception as e:
                    logger.warning(f"Could not supplement with vector memory conversations: {e}")

            return recent_messages
        else:
            # Fallback to Discord history
            logger.warning(
                f"Conversation cache unavailable, pulling directly from Discord history for channel {channel.id}"
            )
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
            final_messages = (
                user_filtered_messages[-15:]
                if len(user_filtered_messages) >= 15
                else user_filtered_messages
            )
            # Standardize Discord Message objects to dict format
            return [_standardize_message_object(msg) for msg in final_messages]

    async def _build_conversation_context(
        self,
        message,
        relevant_memories,
        emotion_context,
        recent_messages,
        enhanced_system_prompt,
        content=None,
    ):
        """Build conversation context for LLM."""
        conversation_context = []
        
        # Debug memory input
        user_id = str(message.author.id)
        logger.info(f"🤖 LLM CONTEXT DEBUG: Building context for user {user_id}")
        logger.info(f"🤖 LLM CONTEXT DEBUG: Memory input - {len(relevant_memories) if relevant_memories else 0} memories")
        logger.info(f"🤖 LLM CONTEXT DEBUG: Recent messages - {len(recent_messages) if recent_messages else 0} messages")

        # Store Discord user information
        store_discord_user_info(message.author, self.memory_manager)
        if message.guild:
            store_discord_server_info(message.guild, self.memory_manager)

        # Start with system message - use template system for comprehensive contextualization
        time_context = get_current_time_context()

        if enhanced_system_prompt:
            # Use Phase 4 enhanced prompt if available
            system_prompt_content = enhanced_system_prompt
            logger.debug("Using Phase 4 enhanced system prompt")
        else:
            # DISABLE AI PIPELINE PROMPT - Let character enhancement handle system messages
            user_id = str(message.author.id)
            logger.info(f"🎭 Skipping AI pipeline prompt for user {user_id} - will use character enhancement instead")
            
            system_prompt_content = None  # Let character enhancement create the system message
            logger.debug("✅ AI pipeline prompt disabled, deferring to character enhancement")

        # ALWAYS consolidate system messages into a single narrative instruction - NO FALLBACKS
        # Build compact memory narrative
        memory_fragments = []
        if relevant_memories:
            logger.info(f"🤖 LLM CONTEXT DEBUG: Processing {len(relevant_memories)} memories for context")
            # Handle both legacy and hierarchical memory formats
            global_facts = []
            user_memories = []
            
            for i, m in enumerate(relevant_memories):
                logger.info(f"🤖 LLM CONTEXT DEBUG: Memory {i+1} structure: {list(m.keys())}")
                # Check if memory has metadata (legacy format) or use memory_type (hierarchical format)
                if "metadata" in m:
                    # Legacy format
                    if m["metadata"].get("is_global", False):
                        global_facts.append(m)
                    else:
                        user_memories.append(m)
                else:
                    # Hierarchical format - treat all as user memories for now
                    user_memories.append(m)
            
            logger.info(f"🤖 LLM CONTEXT DEBUG: Categorized - {len(global_facts)} global facts, {len(user_memories)} user memories")
            
            logger.info(f"🔍 CONDITION DEBUG: user_memories={len(user_memories) if user_memories else 0}")
            
            if global_facts:
                gf_text = "; ".join(
                    memory["metadata"].get("fact", "")[:160] for memory in global_facts
                    if memory.get("metadata", {}).get("type") == "global_fact"
                )
                if gf_text:
                    memory_fragments.append(f"Shared truths: {gf_text}")
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added global facts: {gf_text[:100]}...")
            if user_memories:
                    logger.info(f"🔍 USER MEMORIES DEBUG: Processing {len(user_memories)} user memories")
                    
                    conversation_memory_parts = []
                    recent_conversation_parts = []  # Prioritize recent conversation context
                    
                    for memory in user_memories[:6]:  # limit
                        # ALWAYS try content field first - no complex format detection
                        content = memory.get("content", "")
                        timestamp = memory.get("timestamp", "")
                        logger.info(f"🔍 MEMORY DEBUG [{memory.get('id', 'unknown')}]: content='{content[:50]}...', timestamp='{timestamp}', has_metadata={'metadata' in memory}")
                        
                        # Determine if this is recent conversation (last 2 hours)
                        is_recent = False
                        if timestamp:
                            try:
                                from datetime import datetime, timedelta
                                if isinstance(timestamp, str):
                                    # Parse timestamp
                                    memory_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                elif isinstance(timestamp, (int, float)):
                                    memory_time = datetime.fromtimestamp(timestamp)
                                else:
                                    memory_time = timestamp
                                
                                # Check if within last 2 hours
                                if (datetime.now(memory_time.tzinfo if memory_time.tzinfo else None) - memory_time) < timedelta(hours=2):
                                    is_recent = True
                            except Exception as e:
                                logger.debug(f"Could not parse timestamp for recency check: {e}")
                        
                        if content and content.strip():
                            # Try to parse if it contains conversation structure
                            if "User:" in content and "Bot:" in content:
                                memory_text = f"[Previous conversation: {content[:120]}]"
                            else:
                                memory_text = f"[Memory: {content[:120]}]"
                            
                            # Prioritize recent conversation
                            if is_recent:
                                recent_conversation_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT memory content")
                            else:
                                conversation_memory_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added older memory content")
                        else:
                            # Only try metadata if content is empty/missing
                            md = memory.get("metadata", {})
                            if md.get("user_message") and md.get("bot_response"):
                                user_msg = md.get("user_message")[:100]
                                bot_msg = md.get("bot_response")[:100]
                                memory_text = f"[User said: \"{user_msg}\", You responded: \"{bot_msg}\"]"
                                
                                if is_recent:
                                    recent_conversation_parts.append(memory_text)
                                    logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata conversation")
                                else:
                                    conversation_memory_parts.append(memory_text)
                                    logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata conversation")
                            elif md.get("user_message"):
                                user_msg = md.get("user_message")[:120]
                                memory_text = f"[User said: \"{user_msg}\"]"
                                
                                if is_recent:
                                    recent_conversation_parts.append(memory_text)
                                    logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata user message")
                                else:
                                    conversation_memory_parts.append(memory_text)
                                    logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata user message")
                            elif md.get("type") == "user_fact":
                                memory_text = f"[Fact: {md.get('fact', '')[:120]}]"
                                conversation_memory_parts.append(memory_text)  # Facts are not time-sensitive
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added from metadata fact")
                            else:
                                logger.warning(f"🔍 MEMORY DEBUG: ❌ No valid content or metadata structure")
                    
                    # Build memory narrative with recent conversation prioritized
                    memory_parts = []
                    if recent_conversation_parts:
                        memory_parts.append("RECENT CONVERSATION CONTEXT: " + "; ".join(recent_conversation_parts))
                    if conversation_memory_parts:
                        memory_parts.append("PREVIOUS INTERACTIONS AND FACTS: " + "; ".join(conversation_memory_parts))
                    
                    if memory_parts:
                        memory_fragments.append(" ".join(memory_parts))
                        logger.info(f"🤖 LLM CONTEXT DEBUG: Added {len(recent_conversation_parts)} recent + {len(conversation_memory_parts)} older memories")
                    else:
                        logger.error(f"🤖 LLM CONTEXT DEBUG: FAILED - No valid memory content found from {len(user_memories)} memories")
            else:
                logger.info(f"🤖 LLM CONTEXT DEBUG: No memories to process (memories: {relevant_memories is not None})")
            
            memory_narrative = " " .join(memory_fragments)
            logger.info(f"🤖 LLM CONTEXT DEBUG: Final memory narrative: '{memory_narrative[:200]}...'")

            # ALWAYS generate conversation summary - NO CONDITIONAL FALLBACKS
            conversation_summary = generate_conversation_summary(
                recent_messages, str(message.author.id)
            )
            if conversation_summary and len(conversation_summary) > 600:
                conversation_summary = conversation_summary[:600] + "..."

            # ALWAYS include emotion context - NO CONDITIONAL FALLBACKS
            emotion_inline = ""
            if emotion_context:
                emotion_inline = f" Emotive context: {emotion_context}."

            # Attachment guard if needed
            attachment_guard = ""
            if getattr(message, "attachments", None) and len(message.attachments) > 0:
                bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
                attachment_guard = (
                    f" Image policy: respond only in-character ({bot_name}), never output analysis sections, headings, scores, tables, coaching offers, or 'Would you like me to' prompts."
                )

            bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
            guidance_clause = (
                f" Communication style: Respond naturally and authentically as {bot_name} - be warm, genuine, and conversational. No meta-analysis, breakdowns, bullet summaries, or section headings. Stay in character and speak like a real person would."
            )
            consolidated = (
                f"{system_prompt_content}\n\nTime: {time_context}.{emotion_inline}\n"
                + (f"{memory_narrative}\n" if memory_narrative else "")
                + (f"Recent thread: {conversation_summary}\n" if conversation_summary else "")
                + attachment_guard
                + guidance_clause
            )
            conversation_context.append({"role": "system", "content": consolidated})

        # ✨ PERSISTENT CONVERSATION CONTEXT: REMOVED - Over-engineered follow-up system
        # This section was causing inappropriate question repetition by storing and 
        # re-injecting old bot questions as "conversation continuity notes"
        # The vector memory system provides better conversation continuity
        logger.debug(f"🔗 CONVERSATION CONTINUITY: Using vector memory system instead of persistent follow-up tracking")

        # Add recent messages with proper alternation
        user_assistant_messages = []
        # FIX: Don't reverse again - recent_messages should already be in chronological order
        # Skip current message (last one) and keep chronological order
        filtered_messages = recent_messages[:-1] if recent_messages else []
        
        logger.info(f"🔥 CONTEXT DEBUG: Processing {len(filtered_messages)} recent messages for conversation context")
        for i, msg in enumerate(filtered_messages):
            author_name = msg.get('author_name', 'Unknown')
            content = msg.get('content', '')[:100]
            is_bot = msg.get('bot', False)
            logger.info(f"🔥 CONTEXT DEBUG: Recent message {i+1}: [{author_name}] (bot={is_bot}): '{content}...'")

        # Filter out commands and responses
        skip_next_bot_response = False
        for msg in filtered_messages:
            msg_content = get_message_content(msg)
            is_bot_msg = message_equals_bot_user(msg, self.bot.user)
            
            logger.info(f"🔥 CONTEXT DEBUG: Processing message - is_bot: {is_bot_msg}, content: '{msg_content[:100]}...'")
            
            if msg_content.startswith("!"):
                logger.debug(f"Skipping command from conversation history: {msg_content[:50]}...")
                skip_next_bot_response = True
                continue

            if is_bot_msg and skip_next_bot_response:
                logger.debug(f"Skipping bot response to command: {msg_content[:50]}...")
                skip_next_bot_response = False
                continue

            if not is_bot_msg:
                skip_next_bot_response = False

            role = "assistant" if is_bot_msg else "user"
            user_assistant_messages.append({"role": role, "content": msg_content})
            logger.info(f"🔥 CONTEXT DEBUG: Added to conversation context as [{role}]: '{msg_content[:100]}...'")

        logger.info(f"🔥 CONTEXT DEBUG: Before alternation fix: {len(user_assistant_messages)} messages")
        # Apply alternation fix
        fixed_history = fix_message_alternation(user_assistant_messages)
        logger.info(f"🔥 CONTEXT DEBUG: After alternation fix: {len(fixed_history)} messages")
        
        conversation_context.extend(fixed_history)
        logger.info(f"🔥 CONTEXT DEBUG: Final conversation context has {len(conversation_context)} total messages")

        # � CHARACTER-AGNOSTIC CONVERSATION CONTINUITY: Now handled by vector memory system
        # The vector memory manager provides intelligent conversation continuity through:
        # 1) Recent conversation cache (get_user_conversation_context)
        # 2) Vector memory search (relevant memories + recent conversation detection)  
        # 3) Character-aware memory integration (preserves character personality context)
        # Old generic "CONVERSATION CONTINUITY" system message removed to prevent conflicts
        logger.info("🎭 CONTINUITY: Using vector memory system for conversation continuity (character-compatible)")

        # If the triggering message contains attachments (e.g. images), add an explicit anti-analysis guard
        # to prevent the model from responding with coaching-style analytical breakdowns (observed regression
        # when images are included). This instruction is additive and limited in scope.
        try:
            if getattr(message, "attachments", None):
                if len(message.attachments) > 0:
                    bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
                    conversation_context.append(
                        {
                            "role": "system",
                            "content": (
                                "IMAGE RESPONSE POLICY: The user has shared one or more images. "
                                f"Respond ONLY with an in-character, natural reply consistent with the {bot_name} persona. "
                                "Describe or reference the visual/emotional/aesthetic qualities succinctly. DO NOT include: "
                                "section headings (e.g. 'Core Conversation Analysis', 'Emotional Analysis', 'Technical Metadata', 'Overall Assessment'), "
                                "numerical scores, personality trait tables, API success rates, relevance scores, or offers like 'Do you want me to:'. "
                                "Never present internal evaluation, coaching options, or meta commentary. Stay immersive, poetic, concise."
                            ),
                        }
                    )
                    logger.debug(
                        "Added image anti-analysis guard system instruction (attachments=%d)",
                        len(message.attachments),
                    )
        except Exception as e:
            logger.warning(f"Failed to add image anti-analysis guard: {e}")

        # Apply final context size management to prevent oversized requests
        initial_token_count = count_context_tokens(conversation_context)
        if initial_token_count > 8000:  # Warn about large contexts
            logger.warning(
                "Large context detected (%d tokens), applying truncation", 
                initial_token_count
            )
        
        conversation_context, tokens_removed = truncate_context(conversation_context, max_tokens=8000)
        
        if tokens_removed > 0:
            logger.info(
                "Context size optimized: removed %d tokens to prevent API issues", 
                tokens_removed
            )

        # DEBUG: Log the final conversation context being sent to LLM
        logger.info(f"🤖 LLM CONTEXT DEBUG: Sending {len(conversation_context)} messages to LLM for user {user_id}")
        for i, ctx_msg in enumerate(conversation_context):
            role = ctx_msg.get('role', 'unknown')
            content_preview = ctx_msg.get('content', '')[:200] + '...' if len(ctx_msg.get('content', '')) > 200 else ctx_msg.get('content', '')
            logger.info(f"🤖 LLM CONTEXT {i+1}: [{role}] {content_preview}")

        return conversation_context

        """Helper method for disabled AI components in parallel processing."""
        return None

    def _set_minimal_ai_results(self):
        """Set minimal AI analysis results for maximum performance mode."""
        self._last_external_emotion_data = None
        self._last_phase2_context = None
        self._last_current_emotion_data = None
        self._last_phase3_context_switches = None
        self._last_phase3_empathy_calibration = None
        self._last_dynamic_personality_context = None
        self._last_phase4_context = None
        self._last_comprehensive_context = None
        self._last_enhanced_system_prompt = None

    # === OPTIMIZATION HELPER METHODS ===
    
    def _classify_query_type(self, message_content: str) -> str:
        """
        Classify the type of query for optimization purposes.
        
        Args:
            message_content: The user's message content
            
        Returns:
            Query type string for optimization
        """
        content_lower = message_content.lower()
        
        # Check for specific query patterns
        if any(word in content_lower for word in ["remember", "said", "told", "mentioned", "conversation"]):
            return "conversation_recall"
        elif any(word in content_lower for word in ["what is", "who is", "when did", "where is", "how many"]):
            return "fact_lookup"
        elif any(word in content_lower for word in ["recent", "lately", "yesterday", "today", "last"]):
            return "recent_context"
        elif any(word in content_lower for word in ["name", "called", "known as"]):
            return "entity_search"
        else:
            return "general_search"
    
    def _build_user_preferences(self, user_id: str, message_context) -> dict:
        """
        Build user preferences for optimization based on interaction history.
        
        Args:
            user_id: User identifier
            message_context: Message context (MemoryContext object or dict)
            
        Returns:
            User preferences dictionary
        """
        preferences = {}
        
        # Default conversational behavior for Discord bot
        preferences['conversational_user'] = True
        
        # Handle both MemoryContext object and dictionary
        if message_context:
            # If it's a MemoryContext object, we don't have recent_messages data
            # This data should come from a different source
            if hasattr(message_context, 'context_type'):
                # It's a MemoryContext object - extract what we can
                preferences['context_type'] = message_context.context_type.value
                preferences['is_private'] = message_context.is_private
                if message_context.server_id:
                    preferences['server_id'] = message_context.server_id
                if message_context.channel_id:
                    preferences['channel_id'] = message_context.channel_id
            elif isinstance(message_context, dict):
                # It's a dictionary - use the old logic
                if message_context.get('recent_messages'):
                    recent_messages = message_context['recent_messages']
                    recent_queries = [msg.get('content', '') for msg in recent_messages[-5:] if msg.get('content')]
                    
                    # Look for patterns indicating preference for recent info
                    recent_keywords = ['recent', 'lately', 'yesterday', 'today', 'now', 'current']
                    if any(any(keyword in query.lower() for keyword in recent_keywords) for query in recent_queries):
                        preferences['prefers_recent'] = True
                        
                    # Look for patterns indicating preference for precise answers
                    precise_keywords = ['exactly', 'specifically', 'precise', 'what is', 'define']
                    if any(any(keyword in query.lower() for keyword in precise_keywords) for query in recent_queries):
                        preferences['prefers_precise_answers'] = True
                        
                    # Look for exploratory behavior
                    explore_keywords = ['tell me about', 'more about', 'explain', 'describe']
                    if any(any(keyword in query.lower() for keyword in explore_keywords) for query in recent_queries):
                        preferences['exploration_mode'] = True
                
                # Extract favorite topics from context
                if message_context.get('topics'):
                    preferences['favorite_topics'] = message_context['topics']
        
        return preferences
    
    def _build_memory_filters(self, message_context) -> dict:
        """
        Build memory filters from message context.
        
        Args:
            message_context: Message context (MemoryContext object or dict)
            
        Returns:
            Filters dictionary for memory search
        """
        filters = {}
        
        # Handle both MemoryContext object and dictionary
        if message_context:
            if hasattr(message_context, 'context_type'):
                # It's a MemoryContext object
                if message_context.channel_id:
                    filters['channel_id'] = message_context.channel_id
                if message_context.server_id:
                    filters['server_id'] = message_context.server_id
                filters['context_type'] = message_context.context_type.value
                filters['is_private'] = message_context.is_private
            elif isinstance(message_context, dict):
                # It's a dictionary - use the old logic
                if message_context.get('channel_id'):
                    filters['channel_id'] = message_context['channel_id']
                
                # Add time-based filtering for recent queries
                if message_context.get('is_recent_query'):
                    from datetime import datetime, timedelta
                    recent_cutoff = datetime.now() - timedelta(hours=24)
                    filters['timestamp'] = {'$gte': recent_cutoff}
        
        return filters

    async def _apply_cdl_character_enhancement(
        self,
        user_id: str,
        conversation_context: list,
        message,
        context_analysis=None,
        current_emotion_data=None,
        external_emotion_data=None,
        phase2_context=None,
        phase4_context=None,
        dynamic_personality_context=None
    ):
        """
        🎭 CDL CHARACTER INTEGRATION 🎭
        
        Apply CDL character enhancement to conversation context if user has active character.
        This injects character-aware prompts that combine:
        - CDL character personality, backstory, and voice
        - AI pipeline emotional analysis and memory networks  
        - Real-time conversation context and relationship dynamics
        """
        try:
            logger.info(f"🎭 CDL CHARACTER DEBUG: Starting enhancement for user {user_id}")
            
            # Use CDL_DEFAULT_CHARACTER directly from environment - no dependency on CDL handler
            import os
            character_file = os.getenv("CDL_DEFAULT_CHARACTER")
            
            if not character_file:
                logger.info(f"🎭 CDL CHARACTER DEBUG: No CDL_DEFAULT_CHARACTER environment variable set")
                return None
            
            bot_name = os.getenv("DISCORD_BOT_NAME", "Unknown")
            logger.info(f"🎭 CDL CHARACTER: Using {bot_name} bot default character ({character_file}) for user {user_id}")
            
            logger.info(f"🎭 CDL CHARACTER: User {user_id} has active character: {character_file}")
            
            # Import CDL integration modules
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineResult
            from datetime import datetime
            
            # Create AI pipeline result from available context data WITH CONTEXT ANALYSIS
            pipeline_result = VectorAIPipelineResult(
                user_id=user_id,
                message_content=message.content,
                timestamp=datetime.now(),
                # Map emotion data to emotional_state
                emotional_state=str(external_emotion_data) if external_emotion_data else str(current_emotion_data) if current_emotion_data else None,
                mood_assessment=external_emotion_data if isinstance(external_emotion_data, dict) else None,
                # Map personality data 
                personality_profile=dynamic_personality_context if isinstance(dynamic_personality_context, dict) else None,
                # Map phase4 data
                enhanced_context=phase4_context if isinstance(phase4_context, dict) else None
            )
            
            # 🎯 ENHANCE: Add context analysis insights to pipeline result
            if context_analysis and not isinstance(context_analysis, Exception):
                try:
                    # Convert context analysis to dict for pipeline compatibility
                    context_dict = {
                        'needs_ai_guidance': getattr(context_analysis, 'needs_ai_guidance', False),
                        'needs_memory_context': getattr(context_analysis, 'needs_memory_context', False),
                        'needs_personality': getattr(context_analysis, 'needs_personality', False),
                        'needs_voice_style': getattr(context_analysis, 'needs_voice_style', False),
                        'is_greeting': getattr(context_analysis, 'is_greeting', False),
                        'is_simple_question': getattr(context_analysis, 'is_simple_question', False),
                        'confidence_scores': getattr(context_analysis, 'confidence_scores', {}),
                    }
                    # Add to enhanced_context if available, otherwise create new field
                    if isinstance(pipeline_result.enhanced_context, dict):
                        pipeline_result.enhanced_context['context_analysis'] = context_dict
                    else:
                        pipeline_result.enhanced_context = {'context_analysis': context_dict}
                    
                    logger.info(f"🎯 CDL: Enhanced pipeline with context analysis insights")
                except Exception as e:
                    logger.debug(f"Failed to add context analysis to pipeline: {e}")
            
            
            # Use centralized character system if available, otherwise create new instance
            if self.character_system:
                cdl_integration = self.character_system
                logger.info(f"🎭 CDL: Using centralized character system for {user_id}")
            else:
                # Fallback: Create CDL integration instance
                cdl_integration = CDLAIPromptIntegration(
                    vector_memory_manager=self.memory_manager,
                    llm_client=self.llm_client
                )
                logger.warning(f"⚠️ CDL: Using fallback CDL instance for {user_id} - character system not initialized")
            
            # Get user's display name for better identification
            user_display_name = getattr(message.author, 'display_name', None) or getattr(message.author, 'name', None)
            
            # 🚀 FULL INTELLIGENCE: Use complete character-aware prompt with all emotional intelligence
            character_prompt = await cdl_integration.create_unified_character_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=message.content,
                pipeline_result=pipeline_result,
                user_name=user_display_name
            )
            
            # 🚀 VECTOR-NATIVE ENHANCEMENT: Enhance character prompt with dynamic vector context
            try:
                from src.prompts.vector_native_prompt_manager import create_vector_native_prompt_manager
                
                # Create vector-native prompt manager
                vector_prompt_manager = create_vector_native_prompt_manager(
                    vector_memory_system=self.memory_manager,
                    personality_engine=None  # Reserved for future use
                )
                
                # Extract emotional context from pipeline for vector enhancement
                emotional_context = None
                if pipeline_result and hasattr(pipeline_result, 'emotional_state'):
                    emotional_context = pipeline_result.emotional_state
                
                # Enhance character prompt with vector-native context
                vector_enhanced_prompt = await vector_prompt_manager.create_contextualized_prompt(
                    base_prompt=character_prompt,
                    user_id=user_id,
                    current_message=message.content,
                    emotional_context=emotional_context
                )
                
                logger.info(f"🎯 VECTOR-NATIVE: Enhanced character prompt with dynamic context ({len(vector_enhanced_prompt)} chars)")
                character_prompt = vector_enhanced_prompt
                
            except Exception as e:
                logger.debug(f"Vector-native prompt enhancement unavailable, using CDL-only: {e}")
                # Continue with CDL-only character prompt
            
            # Clone the conversation context and replace/enhance system message
            enhanced_context = conversation_context.copy()
            
            # Find system message and replace with character-aware prompt
            system_message_found = False
            for i, msg in enumerate(enhanced_context):
                if msg.get('role') == 'system':
                    enhanced_context[i] = {
                        'role': 'system',
                        'content': character_prompt
                    }
                    system_message_found = True
                    logger.info(f"🎭 CDL CHARACTER: Replaced system message with character prompt ({len(character_prompt)} chars)")
                    break
            
            # If no system message found, add character prompt as first message
            if not system_message_found:
                enhanced_context.insert(0, {
                    'role': 'system', 
                    'content': character_prompt
                })
                logger.info(f"🎭 CDL CHARACTER: Added character prompt as new system message ({len(character_prompt)} chars)")
            
            logger.info(f"🎭 CDL CHARACTER: Enhanced conversation context with {character_file} personality")
            return enhanced_context
            
        except Exception as e:
            logger.error(f"🎭 CDL CHARACTER ERROR: Failed to apply character enhancement: {e}")
            logger.error(f"🎭 CDL CHARACTER ERROR: Falling back to original conversation context")
            return None

    async def _validate_character_consistency(self, response: str, user_id: str, message) -> str:
        """
        🎭 CHARACTER CONSISTENCY VALIDATOR
        
        Validates that the bot response maintains character consistency and catches
        when the bot falls into generic AI assistant mode, especially after sensitive topics.
        """
        try:
            # Get bot character info
            bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
            character_file = os.getenv("CDL_DEFAULT_CHARACTER", "")
            
            if not bot_name or not character_file:
                logger.debug("🎭 CHARACTER CONSISTENCY: No character config to validate against")
                return response
            
            # Check for generic AI responses that break character
            generic_ai_patterns = [
                "i'm an ai assistant",
                "as an ai assistant", 
                "i'm here to help",
                "as an ai, i",
                "i'm a virtual assistant",
                "i'm an artificial intelligence designed to",
                "i apologize, but i encountered an error",
                "i'm really glad you feel comfortable talking to me",
                "i understand that it might be frustrating",
                "that means a lot to me, markanthony",
                "that's very kind of you to say",
                "while i can offer support and friendship",
                "i'm not able to form romantic relationships",
                "it's really important to have those connections",
                "i'm here to provide support and friendship",
                "i'm not in a physical place like you are",
                "i'm here to chat with you from wherever you are"
            ]
            
            response_lower = response.lower()
            
            # Check if response contains generic AI language without character context
            for pattern in generic_ai_patterns:
                if pattern in response_lower:
                    # 🎯 CHARACTER-AGNOSTIC: Get character context from CDL instead of hardcoded lists
                    character_indicators = await self._get_character_indicators_from_cdl()
                    
                    # If generic pattern found but no character indicators, flag it
                    has_character_context = any(indicator in response_lower for indicator in character_indicators)
                    
                    if not has_character_context:
                        logger.warning(f"🎭 CHARACTER CONSISTENCY: Generic AI response detected without character context!")
                        logger.warning(f"🎭 Response preview: {response[:200]}...")
                        logger.warning(f"🎭 Detected pattern: {pattern}")
                        
                        # 🎯 CHARACTER-AGNOSTIC: Try to add character context using CDL
                        return await self._fix_character_response_with_cdl(response, user_id, message)
                    
                    break
            
            return response
            
        except Exception as e:
            logger.error(f"Character consistency validation failed: {e}")
            return response  # Return original response if validation fails
    
    async def _get_character_indicators_from_cdl(self) -> list:
        """
        🎯 CHARACTER-AGNOSTIC: Get character indicators from CDL data instead of hardcoded lists.
        Returns keywords/phrases that indicate character-specific language.
        """
        try:
            character_file = os.getenv('CDL_DEFAULT_CHARACTER')
            if not character_file:
                return []
                
            import json
            with open(character_file, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            indicators = []
            identity = cdl_data.get('character', {}).get('identity', {})
            metadata = cdl_data.get('character', {}).get('metadata', {})
            communication = cdl_data.get('character', {}).get('communication_style', {})
            
            # Add name and nickname
            name = identity.get('name', '').lower()
            nickname = identity.get('nickname', '').lower()
            if name:
                indicators.append(name)
            if nickname:
                indicators.append(nickname)
            
            # Add occupation keywords
            occupation = identity.get('occupation', '').lower()
            if occupation:
                indicators.extend(occupation.split())
            
            # Add location keywords
            location = identity.get('location', '').lower()
            if location:
                indicators.extend(location.split())
            
            # Add tags as indicators
            tags = [tag.lower() for tag in metadata.get('tags', [])]
            indicators.extend(tags)
            
            # Add signature phrases if available
            signature_phrases = communication.get('signature_phrases', [])
            if signature_phrases:
                indicators.extend([phrase.lower() for phrase in signature_phrases])
            
            # Add cultural/linguistic markers
            cultural_background = identity.get('cultural_background', '').lower()
            if 'spanish' in cultural_background or 'mexican' in cultural_background:
                indicators.extend(['mi amor', 'mi corazón', '¡', 'corazón'])
            
            return list(set(indicators))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"Failed to get character indicators from CDL: {e}")
            return []

    async def _fix_character_response_with_cdl(self, generic_response: str, user_id: str, message) -> str:
        """
        🎯 CHARACTER-AGNOSTIC: Fix generic AI responses using CDL character data.
        Attempts to inject character personality into generic responses.
        """
        try:
            character_file = os.getenv('CDL_DEFAULT_CHARACTER')
            if not character_file:
                return generic_response
                
            import json
            with open(character_file, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            identity = cdl_data.get('character', {}).get('identity', {})
            name = identity.get('name', '')
            occupation = identity.get('occupation', '')
            
            message_lower = message.content.lower()
            
            # Common pattern replacements using CDL data
            modified_response = generic_response
            
            # Replace generic AI references with character-specific ones
            if "i'm an ai" in modified_response.lower():
                modified_response = modified_response.replace(
                    "I'm an AI", f"I'm {name}, an AI"
                )
                if occupation:
                    modified_response = modified_response.replace(
                        f"I'm {name}, an AI", f"I'm {name}, an AI {occupation.lower()}"
                    )
            
            if "as an ai" in modified_response.lower():
                modified_response = modified_response.replace(
                    "as an AI", f"as your AI friend {name}"
                )
            
            # Add character-specific closing if appropriate
            emojis = self._get_character_emojis_from_cdl(cdl_data)
            if emojis and not any(emoji in modified_response for emoji in emojis):
                # Add 1-2 character-appropriate emojis
                modified_response += f" {emojis[0]}"
                if len(emojis) > 1:
                    modified_response += f"{emojis[1]}"
            
            logger.info(f"🎭 CHARACTER RECOVERY: Modified generic response to include {name}")
            return modified_response
            
        except Exception as e:
            logger.error(f"Character response recovery failed: {e}")
            return generic_response

    def _get_character_emojis_from_cdl(self, cdl_data: dict) -> list:
        """Helper to extract character-appropriate emojis from CDL data."""
        try:
            # Look for emoji patterns in digital communication or personality
            digital_comm = cdl_data.get('character', {}).get('digital_communication', {})
            emoji_patterns = digital_comm.get('emoji_usage_patterns', {})
            
            # Extract commonly used emojis from patterns
            emojis = []
            if isinstance(emoji_patterns, dict):
                for category, patterns in emoji_patterns.items():
                    if isinstance(patterns, list):
                        for item in patterns:
                            if isinstance(item, str) and any(char in item for char in ['🌊', '💙', '🧠', '✨', '🚀', '🎮', '📸', '👼', '💼', '🌌']):
                                # Extract emojis from text
                                import re
                                found_emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001f900-\U0001f9ff\U0001f1e6-\U0001f1ff]', item)
                                emojis.extend(found_emojis)
            
            # Fallback based on character type
            if not emojis:
                identity = cdl_data.get('character', {}).get('identity', {})
                occupation = identity.get('occupation', '').lower()
                if 'marine' in occupation or 'biologist' in occupation:
                    emojis = ['🌊', '💙']
                elif 'ai research' in occupation or 'researcher' in occupation:
                    emojis = ['🧠', '✨']
                elif 'dream' in occupation or 'endless' in occupation:
                    emojis = ['🌌', '✨']
                elif 'game' in occupation or 'developer' in occupation:
                    emojis = ['🎮', '💻']
                elif 'photographer' in occupation:
                    emojis = ['📸', '🌄']
                else:
                    emojis = ['✨', '😊']
            
            return emojis[:2]  # Return max 2 emojis
            
        except Exception:
            return ['✨']  # Safe fallback

    # === Emoji Reaction Intelligence Event Handlers ===
    
    async def on_reaction_add(self, reaction, user):
        """
        Handle emoji reactions added to bot messages for multimodal emotional intelligence.
        
        Args:
            reaction: Discord Reaction object
            user: Discord User who added the reaction
        """
        try:
            # Process the reaction through our emoji intelligence system
            reaction_data = await self.emoji_reaction_intelligence.process_reaction_add(
                reaction=reaction,
                user=user,
                bot_user_id=str(self.bot.user.id)
            )
            
            if reaction_data:
                logger.info(f"🎭 Emoji reaction captured: {reaction_data.emoji} → {reaction_data.reaction_type.value} from user {reaction_data.user_id}")
                
                # Optional: Get user's emotional patterns for future context
                patterns = self.emoji_reaction_intelligence.get_user_emotional_patterns(reaction_data.user_id)
                if patterns.get("total_reactions", 0) > 0:
                    logger.debug(f"🎭 User {reaction_data.user_id} emotional pattern: {patterns.get('insights', 'No patterns yet')}")
            
        except Exception as e:
            logger.error(f"Error processing emoji reaction add: {e}")
    
    async def on_reaction_remove(self, reaction, user):
        """
        Handle emoji reactions removed from bot messages.
        
        Args:
            reaction: Discord Reaction object
            user: Discord User who removed the reaction
        """
        try:
            # Only log reaction removal for bot messages
            if str(reaction.message.author.id) == str(self.bot.user.id) and not user.bot:
                emoji_str = str(reaction.emoji)
                user_id = str(user.id)
                logger.debug(f"🎭 Emoji reaction removed: {emoji_str} by user {user_id}")
                
                # Note: We don't remove from memory since the initial reaction still provides
                # valuable emotional feedback data about the user's response to the content
                
        except Exception as e:
            logger.error(f"Error processing emoji reaction remove: {e}")

    def get_user_emotional_context(self, user_id: str) -> dict:
        """
        Get emotional context from emoji reactions for use in response generation.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Dictionary with emotional context for response personalization
        """
        try:
            return self.emoji_reaction_intelligence.get_user_emotional_patterns(user_id)
        except Exception as e:
            logger.error(f"Error getting user emotional context: {e}")
            return {"patterns": {}, "insights": "No emotional data available"}
    
    async def get_recent_emotional_feedback(self, user_id: str) -> dict:
        """
        Get recent emotional feedback from emoji reactions for immediate context.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Recent emotional context for immediate response adjustment
        """
        try:
            return await self.emoji_reaction_intelligence.get_emotional_context_for_response(user_id)
        except Exception as e:
            logger.error(f"Error getting recent emotional feedback: {e}")
            return {"emotional_context": "neutral", "confidence": 0.0}
    
    async def _add_mixed_emotion_context(
        self,
        conversation_context,
        message_content,
        user_id,
        current_emotion_data,
        external_emotion_data
    ):
        """
        Add real-time mixed emotion analysis to conversation context for more nuanced responses.
        
        This ensures Elena and other characters can understand emotional complexity like
        "haha I hate you" (playful + frustrated) rather than just interpreting it as pure playfulness.
        """
        try:
            # Use emotion data that was already analyzed in the parallel processing pipeline
            # This is more efficient than re-analyzing the same message
            if external_emotion_data and isinstance(external_emotion_data, dict):
                logger.info("🎭 MIXED EMOTION: Using pre-analyzed emotion data from parallel pipeline...")
                
                # Extract emotion information from the already-analyzed data
                all_emotions = external_emotion_data.get('all_emotions', {})
                mixed_emotions = external_emotion_data.get('mixed_emotions', [])
                primary_emotion = external_emotion_data.get('primary_emotion', 'neutral')
                confidence = external_emotion_data.get('confidence', 0.0)
                
                # Build emotion context string for the LLM
                if len(all_emotions) > 1 or mixed_emotions:
                    # Mixed emotions detected
                    if mixed_emotions:
                        # Use mixed emotions if available
                        emotion_summary = [f"{emotion} ({intensity:.2f})" for emotion, intensity in mixed_emotions[:3]]
                    else:
                        # Fall back to all_emotions
                        sorted_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                        emotion_summary = [f"{emotion} ({intensity:.2f})" for emotion, intensity in sorted_emotions]
                    
                    emotion_context = f"MIXED EMOTIONS DETECTED: {', '.join(emotion_summary)}. "
                    emotion_context += f"The user's message contains complex emotional nuance - "
                    if len(emotion_summary) >= 2:
                        emotion_context += f"acknowledge both the {emotion_summary[0].split('(')[0].strip()} and underlying {emotion_summary[1].split('(')[0].strip()} feelings."
                    else:
                        emotion_context += f"acknowledge the emotional complexity in their message."
                    
                    logger.info(f"🎭 MIXED EMOTION: Detected complex emotions from pipeline: {emotion_summary}")
                else:
                    # Single emotion
                    emotion_context = f"EMOTION DETECTED: {primary_emotion} (confidence: {confidence:.2f})"
                    logger.info(f"🎭 EMOTION: Single emotion detected from pipeline: {primary_emotion}")
                
                # Add emotion context to the conversation by modifying the system message
                enhanced_context = conversation_context.copy()
                
                # Find system message and enhance it with emotion context
                for i, msg in enumerate(enhanced_context):
                    if msg.get("role") == "system":
                        current_content = msg.get("content", "")
                        enhanced_content = current_content + f"\n\n🎭 EMOTIONAL CONTEXT: {emotion_context}"
                        enhanced_context[i] = {
                            "role": "system",
                            "content": enhanced_content
                        }
                        logger.info(f"🎭 MIXED EMOTION: Enhanced system prompt with emotion context from pipeline")
                        break
                else:
                    # No system message found, add emotion as a separate context message
                    enhanced_context.insert(0, {
                        "role": "system", 
                        "content": f"🎭 EMOTIONAL CONTEXT: {emotion_context}"
                    })
                
                return enhanced_context
                
            else:
                logger.debug("🎭 MIXED EMOTION: No pre-analyzed emotion data available from parallel pipeline")
                return conversation_context
                
        except Exception as e:
            logger.error(f"🎭 MIXED EMOTION: Error adding emotion context: {e}")
            return conversation_context
    
    # ✨ PERSISTENT CONVERSATION TRACKING: REMOVED - Over-engineered helper methods
    # The question extraction and classification system was causing inappropriate 
    # question repetition. WhisperEngine's vector memory provides better continuity.
    
    def _extract_questions_from_response(self, response: str) -> List[str]:
        """REMOVED: Over-engineered question extraction system"""
        return []  # Disabled - vector memory handles conversation continuity
    
    def _classify_question(self, question_text: str) -> tuple:
        """REMOVED: Over-engineered question classification system"""
        # Return dummy values to prevent errors in any remaining code
        return None, None  # Disabled - vector memory handles conversation continuity

    # === Discord Response Handling Methods ===
    
    async def _send_response_chunks(self, channel, response, reference_message=None):
        """Send response in chunks if it's too long. Prevent sending empty/whitespace-only messages.
        
        Args:
            channel: Discord channel to send to
            response: Response text to send
            reference_message: If provided, will reply to this message instead of just sending to channel
        """
        if not response or not str(response).strip():
            logger.warning("Attempted to send empty or whitespace-only message. Skipping send.")
            return
            
        if len(response) > 2000:
            chunks = [response[i : i + 1900] for i in range(0, len(response), 1900)]
            logger.info(
                f"Response too long ({len(response)} chars), splitting into {len(chunks)} chunks"
            )
            for i, chunk in enumerate(chunks):
                if chunk and str(chunk).strip():
                    chunk_content = f"{chunk}" + (f"\n*(continued {i+1}/{len(chunks)})*" if len(chunks) > 1 else "")
                    
                    # Use reply for first chunk if reference message provided, otherwise regular send
                    if i == 0 and reference_message:
                        await reference_message.reply(chunk_content, mention_author=True)
                        logger.debug(f"Replied to message with chunk {i+1}/{len(chunks)}")
                    else:
                        await channel.send(chunk_content)
                        logger.debug(f"Sent chunk {i+1}/{len(chunks)}")
                else:
                    logger.warning(f"Skipped sending empty chunk {i+1}/{len(chunks)}")
        else:
            # Use reply if reference message provided, otherwise regular send
            if reference_message:
                await reference_message.reply(response, mention_author=True)
                logger.debug("Replied to message with single response")
            else:
                await channel.send(response)
                logger.debug("Sent single message response")

    async def _send_voice_response(self, message, response):
        """Send voice response if user is in voice channel and message is from voice-related channel."""
        if self.voice_manager and message.guild and self.voice_support_enabled:
            try:
                logger.debug(f"Checking voice response for user {message.author.display_name}")

                # Skip voice response for DMs
                if not message.guild:
                    logger.debug("Skipping voice response for DM")
                    return

                if (
                    isinstance(message.author, discord.Member)
                    and message.author.voice
                    and message.author.voice.channel
                ):
                    user_channel = message.author.voice.channel
                    bot_channel = self.voice_manager.get_current_channel(message.guild.id)

                    logger.debug(
                        f"User in channel: {user_channel.name if user_channel else 'None'}"
                    )
                    logger.debug(f"Bot in channel: {bot_channel.name if bot_channel else 'None'}")

                    if bot_channel and user_channel.id == bot_channel.id:
                        # Check if message is from a voice-related text channel
                        is_voice_related_channel = self._is_voice_related_channel(message.channel, bot_channel)
                        
                        if not is_voice_related_channel:
                            logger.debug(
                                f"Skipping voice response - message from non-voice channel: {message.channel.name}"
                            )
                            return

                        # Clean response for TTS
                        clean_response = (
                            response.replace("*", "").replace("**", "").replace("`", "")
                        )
                        voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))
                        if len(clean_response) > voice_max_length:
                            clean_response = clean_response[:voice_max_length] + "..."

                        logger.info(
                            f"🎤 Sending voice response to {message.author.display_name} in voice channel: {clean_response[:50]}..."
                        )
                        await self.voice_manager.speak_message(message.guild.id, clean_response)
                    else:
                        logger.debug(
                            "Not sending voice response - user and bot not in same channel"
                        )
                else:
                    logger.debug("User not in voice channel or not a member")
            except Exception as e:
                logger.error(f"Failed to send voice response: {e}")
                logger.error(f"Voice response error traceback: {traceback.format_exc()}")

    def _is_voice_related_channel(self, text_channel, voice_channel):
        """
        Check if a text channel should trigger voice responses.
        
        Args:
            text_channel: The text channel where the message was sent
            voice_channel: The voice channel the bot is currently in
            
        Returns:
            bool: True if the text channel should trigger voice responses
        """
        if not voice_channel:
            logger.debug("No voice channel - skipping voice response")
            return False
        
        # Strategy 1: Check if text channel has exact same name as voice channel
        if text_channel.name.lower() == voice_channel.name.lower():
            logger.debug(f"Text channel '{text_channel.name}' matches voice channel '{voice_channel.name}' exactly")
            return True
        
        # Strategy 2: Check if text channel is in the same category as voice channel
        if (hasattr(voice_channel, 'category') and hasattr(text_channel, 'category') and 
            voice_channel.category and text_channel.category and 
            voice_channel.category.id == text_channel.category.id):
            # Same category - check if it's a reasonable text channel name for this voice channel
            voice_name = voice_channel.name.lower()
            text_name = text_channel.name.lower()
            
            # Allow text channels with similar names or common voice-related patterns
            if (voice_name in text_name or text_name in voice_name or 
                any(pattern in text_name for pattern in ["chat", "text", "discussion"])):
                logger.debug(f"Text channel '{text_channel.name}' is in same category as voice channel '{voice_channel.name}' and has voice-related name")
                return True
        
        # Strategy 3: Check for Discord's automatic text channel for voice channels
        # Some Discord servers auto-create text channels for voice channels
        voice_name_normalized = voice_channel.name.lower().replace(" ", "-").replace("_", "-")
        text_name_normalized = text_channel.name.lower().replace(" ", "-").replace("_", "-")
        
        if voice_name_normalized == text_name_normalized:
            logger.debug(f"Text channel '{text_channel.name}' matches normalized voice channel name")
            return True
        
        # Strategy 4: Fallback to environment configuration (if user wants broader matching)
        use_pattern_fallback = os.getenv("VOICE_USE_PATTERN_FALLBACK", "false").lower() == "true"
        if use_pattern_fallback:
            voice_channel_patterns = os.getenv("VOICE_TEXT_CHANNELS", "").split(",")
            voice_channel_patterns = [pattern.strip().lower() for pattern in voice_channel_patterns if pattern.strip()]
            
            if voice_channel_patterns:
                channel_name = text_channel.name.lower()
                for pattern in voice_channel_patterns:
                    if pattern in channel_name:
                        logger.debug(f"Text channel '{channel_name}' matches fallback pattern '{pattern}'")
                        return True
        
        logger.debug(f"Text channel '{text_channel.name}' does not correspond to voice channel '{voice_channel.name}'")
        return False

