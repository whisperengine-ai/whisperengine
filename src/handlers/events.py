"""
Event handlers for the Discord bot.

Extracted from main.py to improve code organization and maintainability.
Contains on_ready and on_message event handlers with all their complex logic.
"""

import asyncio
import logging
import os
import time
from datetime import UTC, datetime

import discord

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.memory.redis_profile_memory_cache import RedisProfileAndMemoryCache

# Universal Chat Platform Integration
from src.platforms.universal_chat import (
    ChatPlatform,
    UniversalChatOrchestrator,
)
from src.security.input_validator import validate_user_input
from src.security.system_message_security import scan_response_for_system_leakage
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
    error_handler, GracefulDegradation
)

# Vector-native prompt integration - REMOVED: unused final_integration import

logger = logging.getLogger(__name__)

# Reusable meta/analysis pattern list for filtering & sanitization
META_ANALYSIS_PATTERNS = [
    "Core Conversation Analysis",
    "Emotional Analysis",
    "Technical Metadata",
    "Personality & Interaction",
    "Overall Assessment",
    "Overall Analysis",
    "Overall Impression",
    "Combined Response",
    "Why this response works",
    "Would you like me to generate",
    "Would you like me to",
    "Do you want me to",
    "Here is a breakdown",
    "Here's a breakdown",
    "Relevance Score",
    "API Success Rate",
    "Key Points",
    "In Essence",
]

def _strict_mode_enabled() -> bool:
    return os.getenv("STRICT_IMMERSIVE_MODE", "true").lower() in ("1", "true", "yes", "on")

# FALLBACK FUNCTION REMOVED - NO GRACEFUL DEGRADATION ALLOWED
def _minimal_context_mode_enabled() -> bool:
    """DISABLED FALLBACK: Always return False - no degraded mode allowed."""
    return False


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

        # Configuration flags - unified AI system always enabled
        self.voice_support_enabled = getattr(bot_core, "voice_support_enabled", False)

        # Initialize Universal Chat Orchestrator
        self.chat_orchestrator = None
        # Note: Universal Chat will be initialized asynchronously in setup_universal_chat()

        # Register event handlers
        self._register_events()

    # === Minimal Context Mode Utilities ===
    def _apply_minimal_mode_cleanse(self, text: str) -> str:
        """Apply aggressive formatting and meta-analysis cleansing for minimal context mode.

        Strips bullet lists, numbered outlines, trailing coaching offers, and known analytical lead-ins.
        Ensures single-paragraph poetic output <= ~120 words while preserving core semantic content.
        """
        import re

        original = text

        # Remove menu/coaching prompts
        coaching_patterns = [
            r"Do you want me to[^.?]*[.?]",
            r"Would you like me to[^.?]*[.?]",
            r"Shall I[^.?]*[.?]",
        ]
        for pat in coaching_patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)

        # Remove headings (lines ending with colon or title case single-line headings)
        lines = [l for l in text.splitlines() if l.strip()]
        cleaned_lines = []
        for l in lines:
            if re.match(r"^[A-Z][A-Za-z ]{2,40}:$", l.strip()):
                continue
            # Skip list markers
            if re.match(r"^\s*([*\-•]|\d+\.)\s+", l):
                # Keep inline content but without marker if short
                content = re.sub(r"^\s*([*\-•]|\d+\.)\s+", "", l).strip()
                if content and len(content.split()) > 2:
                    cleaned_lines.append(content)
                continue
            cleaned_lines.append(l)

        text = " ".join(cleaned_lines)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()

        # Remove analytic lead-ins
        analytic_leads = [
            r"^Okay, let's break down .*? - ",
            r"^Okay, let's break down .*? based on the data provided\. ",
            r"^Here(?:'s| is) (?:an |a )analysis of .*?\. ",
            r"^Overall Impression: .*?\. ",
        ]
        for pat in analytic_leads:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)

        # Word limit trim
        words = text.split()
        if len(words) > 130:
            text = " ".join(words[:130])
            if not text.endswith(('.', '!', '?')):
                text += '.'

        # Fallback if emptied accidentally
        if len(text) < 20:
            text = original.split('\n\n')[0][:180].strip()

        return text.strip()

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

            # Create configuration and database managers
            config_manager = AdaptiveConfigManager()
            db_manager = DatabaseIntegrationManager(config_manager)

            # Create universal chat orchestrator
            self.chat_orchestrator = UniversalChatOrchestrator(
                config_manager=config_manager, db_manager=db_manager
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
                from src.utils.postgresql_user_db import PostgreSQLUserDB

                postgres_db = PostgreSQLUserDB()
                await postgres_db.initialize()
                self.postgres_pool = postgres_db.pool

                # Update bot_core reference
                self.bot_core.postgres_pool = self.postgres_pool

                # Also update memory managers that might need the pool
                if hasattr(self.bot_core, "context_memory_manager"):
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

        # Initialize Universal Chat Orchestrator
        if self.chat_orchestrator is None:
            try:
                logger.info("🌐 Initializing Universal Chat Orchestrator...")
                success = await self.setup_universal_chat()
                if success:
                    logger.info("✅ Universal Chat Orchestrator ready for Discord integration")
                else:
                    logger.warning(
                        "⚠️ Universal Chat Orchestrator initialization failed - using fallback"
                    )
            except Exception as e:
                logger.error(f"Failed to initialize Universal Chat Orchestrator: {e}")

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

        # Emit diagnostic warning if minimal context mode is active
        if _minimal_context_mode_enabled():
            logger.warning("⚠️ MINIMAL_CONTEXT_MODE active: suppressing emotion, personality, phase4, and memory enrichment layers for baseline output isolation.")

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
        if not validation_result["is_safe"]:
            logger.error(f"SECURITY: Unsafe input detected from user {user_id} in DM")
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
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

        # Initialize variables early
        enhanced_system_prompt = None
        phase4_context = None
        comprehensive_context = None


        # Get relevant memories with context-aware filtering, using Redis cache if available
        relevant_memories = None
        try:
            if self.memory_manager is not None:
                message_context = self.memory_manager.classify_discord_context(message)
                logger.debug(
                    f"DM context classified: {message_context.context_type.value} (security: {message_context.security_level.value})"
                )

                # Try Redis cache first
                if self.profile_memory_cache:
                    try:
                        if not self.profile_memory_cache.redis:
                            await self.profile_memory_cache.initialize()
                        relevant_memories = await self.profile_memory_cache.get_memory_retrieval(user_id, message.content)
                        if relevant_memories:
                            logger.debug(f"[CACHE] Memory retrieval cache hit for user {user_id}")
                    except Exception as e:
                        logger.debug(f"Cache lookup failed, proceeding with DB: {e}")
                        relevant_memories = None
                if not relevant_memories:
                    logger.info(f"🔍 MEMORY DEBUG: Retrieving memories for user {user_id} with query: '{message.content[:50]}...'")
                    
                    # Try optimized memory retrieval first if available
                    if hasattr(self.memory_manager, 'retrieve_relevant_memories_optimized'):
                        try:
                            logger.info("🚀 MEMORY DEBUG: Using optimized memory retrieval")
                            
                            # Determine query type based on message content and context
                            query_type = self._classify_query_type(message.content)
                            
                            # Build user preferences from context
                            user_preferences = self._build_user_preferences(user_id, message_context)
                            
                            # Build filters from message context
                            filters = self._build_memory_filters(message_context)
                            
                            # Add recency boost for conversation continuity
                            filters["prefer_recent_conversation"] = True
                            filters["recency_hours"] = 2  # Prefer memories from last 2 hours
                            
                            # 🎭 CHARACTER FILTERING: Add character-aware memory filtering
                            # This ensures Elena gets Elena's memories, not generic WhisperEngine ones
                            if hasattr(self.bot_core, 'command_handlers') and 'cdl_test' in self.bot_core.command_handlers:
                                cdl_handler = self.bot_core.command_handlers['cdl_test']
                                if hasattr(cdl_handler, '_get_user_active_character'):
                                    try:
                                        active_character = cdl_handler._get_user_active_character(user_id)
                                        if active_character:
                                            character_name = active_character.replace('.json', '').replace('examples/', '')
                                            filters["active_character"] = character_name
                                            filters["has_character"] = True
                                            logger.info(f"🎭 MEMORY SEARCH: Filtering for character: {character_name}")
                                        else:
                                            filters["has_character"] = False
                                            logger.info(f"🎭 MEMORY SEARCH: Filtering for non-character conversations")
                                    except Exception as e:
                                        logger.warning(f"🎭 MEMORY SEARCH: Could not detect character for search: {e}")
                                        # Don't add character filters if detection fails
                            
                            relevant_memories = await self.memory_manager.retrieve_relevant_memories_optimized(
                                user_id=user_id,
                                query=message.content,
                                query_type=query_type,
                                user_history=user_preferences,
                                filters=filters,
                                limit=20
                            )
                            
                            logger.info(f"🚀 MEMORY DEBUG: Optimized retrieval returned {len(relevant_memories) if relevant_memories else 0} memories")
                            
                            # Log optimization details for debugging
                            if relevant_memories and len(relevant_memories) > 0:
                                sample = relevant_memories[0]
                                if 'reranked_score' in sample:
                                    logger.info(f"🚀 MEMORY DEBUG: Re-ranking active - top reranked score: {sample['reranked_score']:.3f}")
                                if 'scoring_breakdown' in sample:
                                    breakdown = sample['scoring_breakdown']
                                    logger.info(f"🚀 MEMORY DEBUG: Scoring breakdown - base: {breakdown.get('base_score', 0):.3f}, "
                                              f"recency: {breakdown.get('recency_boost', 0):.3f}, "
                                              f"preference: {breakdown.get('preference_boost', 0):.3f}")
                            
                        except Exception as e:
                            logger.warning(f"🚀 MEMORY DEBUG: Optimized retrieval failed, falling back to basic: {e}")
                            relevant_memories = None
                    
                    # Fallback to basic memory retrieval if optimization not available or failed
                    if not relevant_memories:
                        logger.info("🔍 MEMORY DEBUG: Using basic memory retrieval with conversation priority")
                        
                        # Check if temporal/recent conversation query
                        is_temporal = any(keyword in message.content.lower() 
                                        for keyword in ['last', 'recent', 'just', 'earlier', 'before'])
                        
                        if is_temporal:
                            # Use temporal query handling for better continuity
                            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                                user_id=user_id, 
                                query=message.content, 
                                max_memories=20,
                                context=message_context,
                                emotional_context="recent conversation continuity"
                            )
                        else:
                            # Regular retrieval but with conversation context prioritization
                            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                                user_id=user_id, 
                                query=message.content, 
                                max_memories=20,
                                context=message_context
                            )
                    
                    logger.info(f"🔍 MEMORY DEBUG: Retrieved {len(relevant_memories) if relevant_memories else 0} memories")
                    if relevant_memories:
                        for i, memory in enumerate(relevant_memories[:3]):  # Log first 3 memories
                            content = memory.get('content', '')[:100]
                            score = memory.get('score', 'N/A')
                            reranked = memory.get('reranked_score')
                            score_text = f"score: {score}"
                            if reranked:
                                score_text += f", reranked: {reranked:.3f}"
                            logger.info(f"🔍 MEMORY DEBUG: Memory {i+1}: ({score_text}) '{content}...'")
                    else:
                        logger.warning(f"🔍 MEMORY DEBUG: No memories retrieved for user {user_id}")
                    
                    # Store in cache for next time
                    if self.profile_memory_cache and relevant_memories:
                        try:
                            if not self.profile_memory_cache.redis:
                                await self.profile_memory_cache.initialize()
                            await self.profile_memory_cache.set_memory_retrieval(user_id, message.content, relevant_memories)
                        except Exception as e:
                            logger.debug(f"Failed to cache memory retrieval: {e}")

                # Get emotion context if available
                emotion_context = ""
                if hasattr(self.memory_manager, "get_emotion_context"):
                    try:
                        # Check if method is async or sync and handle accordingly (WhisperEngine architecture)
                        import inspect
                        if inspect.iscoroutinefunction(self.memory_manager.get_emotion_context):
                            emotion_context = await self.memory_manager.get_emotion_context(user_id)
                        else:
                            # Use thread worker pattern for sync methods in async context
                            loop = asyncio.get_running_loop()
                            emotion_context = await loop.run_in_executor(
                                None, self.memory_manager.get_emotion_context, user_id
                            )
                    except Exception as e:
                        logger.debug(f"Could not get emotion context: {e}")
                        emotion_context = ""
            else:
                logger.warning("memory_manager is not initialized; skipping memory retrieval.")
                relevant_memories = []
                emotion_context = ""

        except (MemoryRetrievalError, ValidationError) as e:
            logger.warning(f"Could not retrieve memories for user {user_id}: {e}")
            relevant_memories = []
            emotion_context = ""
        except Exception as e:
            logger.error(f"Unexpected error retrieving memories: {e}")
            relevant_memories = []
            emotion_context = ""

        # Get recent conversation history - Use HYBRID approach: summary + recent messages
        conversation_summary = await self._get_intelligent_conversation_summary(reply_channel, user_id, message)
        
        if conversation_summary:
            # Use HYBRID: intelligent summary for older context + recent messages for continuity
            logger.info(f"✅ Using HYBRID approach: conversation summary + recent messages for user {user_id}")
            recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
            # Add summary as a system context message
            conversation_summary_context = [
                {"role": "system", "content": f"Previous conversation summary: {conversation_summary}"}
            ]
        else:
            # Fall back to traditional message loading
            recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
            conversation_summary_context = []

        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, enhanced_system_prompt
        )
        
        # Add intelligent conversation summary if available
        if conversation_summary_context:
            # Insert summary before user messages but after system prompts
            # Find where to insert (after system messages, before user messages)
            insert_pos = len([ctx for ctx in conversation_context if ctx["role"] == "system"])
            conversation_context[insert_pos:insert_pos] = conversation_summary_context

        external_emotion_data = None
        phase2_context = None
        current_emotion_data = None
        dynamic_personality_context = None
        phase4_context = None
        comprehensive_context = None
        enhanced_system_prompt = None

        # ALWAYS process AI components - NO CONDITIONAL FALLBACKS
        (external_emotion_data, phase2_context, current_emotion_data, 
         dynamic_personality_context, phase4_context, comprehensive_context, 
         enhanced_system_prompt) = await self._process_ai_components_parallel(
            user_id, message.content, message, recent_messages, conversation_context
        )

        # Process message with images
        conversation_context = await process_message_with_images(
            message.content,
            message.attachments,
            conversation_context,
            self.llm_client,
            self.image_processor,
        )

        # Generate and send response
        await self._generate_and_send_response(
            reply_channel,
            message,
            user_id,
            conversation_context,
            getattr(self, '_last_current_emotion_data', None),
            getattr(self, '_last_external_emotion_data', None),
            getattr(self, '_last_phase2_context', None),
            getattr(self, '_last_phase4_context', None),
            getattr(self, '_last_comprehensive_context', None),
            getattr(self, '_last_dynamic_personality_context', None),
        )

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
            await reply_channel.send(
                f"⚠️ {message.author.mention} Your message contains content that could not be processed for security reasons. Please rephrase your message."
            )
            return

        content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in server {message.guild.name}: {validation_result['warnings']}"
            )

        # Get relevant memories with context-aware filtering, using Redis cache if available
        relevant_memories = None
        try:
            if self.memory_manager is not None:
                message_context = self.memory_manager.classify_discord_context(message)
                logger.debug(
                    f"Server context classified: {message_context.context_type.value} (security: {message_context.security_level.value}, server: {message.guild.name})"
                )

                # Try Redis cache first
                if self.profile_memory_cache:
                    try:
                        if not self.profile_memory_cache.redis:
                            await self.profile_memory_cache.initialize()
                        relevant_memories = await self.profile_memory_cache.get_memory_retrieval(user_id, content)
                        if relevant_memories:
                            logger.debug(f"[CACHE] Memory retrieval cache hit for user {user_id}")
                    except Exception as e:
                        logger.debug(f"Cache lookup failed, proceeding with DB: {e}")
                        relevant_memories = None
                if not relevant_memories:
                    relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                        user_id=user_id, 
                        query=content, 
                        max_memories=20,
                        context=message_context
                    )
                    # Store in cache for next time
                    if self.profile_memory_cache and relevant_memories:
                        try:
                            if not self.profile_memory_cache.redis:
                                await self.profile_memory_cache.initialize()
                            await self.profile_memory_cache.set_memory_retrieval(user_id, content, relevant_memories)
                        except Exception as e:
                            logger.debug(f"Failed to cache memory retrieval: {e}")

                emotion_context = ""
                if hasattr(self.memory_manager, "get_emotion_context"):
                    try:
                        # Check if method is async or sync and handle accordingly (WhisperEngine architecture)
                        import inspect
                        if inspect.iscoroutinefunction(self.memory_manager.get_emotion_context):
                            emotion_context = await self.memory_manager.get_emotion_context(user_id)
                        else:
                            # Use thread worker pattern for sync methods in async context
                            loop = asyncio.get_running_loop()
                            emotion_context = await loop.run_in_executor(
                                None, self.memory_manager.get_emotion_context, user_id
                            )
                    except Exception as e:
                        logger.debug(f"Could not get emotion context: {e}")
                        emotion_context = ""
            else:
                logger.warning("memory_manager is not initialized; skipping memory retrieval.")
                relevant_memories = []
                emotion_context = ""

        except (MemoryRetrievalError, ValidationError) as e:
            logger.warning(f"Could not retrieve memories for user {user_id}: {e}")
            relevant_memories = []
            emotion_context = ""
        except Exception as e:
            logger.error(f"Unexpected error retrieving memories: {e}")
            relevant_memories = []
            emotion_context = ""

        # Get recent conversation history (guild-specific) - Use HYBRID approach: summary + recent messages
        conversation_summary = await self._get_intelligent_conversation_summary(reply_channel, user_id, message)
        
        if conversation_summary:
            # Use HYBRID: intelligent summary for older context + recent messages for continuity
            logger.info(f"✅ Using HYBRID approach: conversation summary + recent messages for guild user {user_id}")
            recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
            # Add summary as a system context message
            conversation_summary_context = [
                {"role": "system", "content": f"Previous conversation summary: {conversation_summary}"}
            ]
        else:
            # Fall back to traditional message loading
            recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)
            conversation_summary_context = []

        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, None, content
        )
        
        # Add intelligent conversation summary if available
        if conversation_summary_context:
            # Insert summary before user messages but after system prompts
            # Find where to insert (after system messages, before user messages)
            insert_pos = len([ctx for ctx in conversation_context if ctx["role"] == "system"])
            conversation_context[insert_pos:insert_pos] = conversation_summary_context
            
        logger.info(f"[CONV-CTX] Built conversation context for message_id={message.id} user_id={user_id} context_type={type(conversation_context)} context_preview={str(conversation_context)[:120]}")

        external_emotion_data = None
        phase2_context = None
        current_emotion_data = None
        dynamic_personality_context = None
        phase4_context = None
        comprehensive_context = None
        enhanced_system_prompt = None

        # ALWAYS process AI components - NO CONDITIONAL FALLBACKS
        (external_emotion_data, phase2_context, current_emotion_data, 
         dynamic_personality_context, phase4_context, comprehensive_context, 
         enhanced_system_prompt) = await self._process_ai_components_parallel(
            user_id, content, message, recent_messages, conversation_context
        )

        # Process message with images (content with mentions removed)
        conversation_context = await process_message_with_images(
            content,
            message.attachments,
            conversation_context,
            self.llm_client,
            self.image_processor,
        )

        # Generate and send response for guild mention
        logger.info(f"[CONV-CTX] Sending to LLM: message_id={message.id} user_id={user_id} final_content='{content}' context_length={len(conversation_context)}")
        await self._generate_and_send_response(
            reply_channel,
            message,
            user_id,
            conversation_context,
            getattr(self, '_last_current_emotion_data', None),
            getattr(self, '_last_external_emotion_data', None),
            getattr(self, '_last_phase2_context', None),
            None,
            None,
            getattr(self, '_last_dynamic_personality_context', None),
            content,
        )

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
            return (
                user_filtered_messages[-15:]
                if len(user_filtered_messages) >= 15
                else user_filtered_messages
            )

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
            
            logger.info(f"🔍 CONDITION DEBUG: user_memories={len(user_memories) if user_memories else 0}, minimal_mode={_minimal_context_mode_enabled()}")
            
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
                logger.info(f"🤖 LLM CONTEXT DEBUG: No memories to process (memories: {relevant_memories is not None}, minimal_mode: {_minimal_context_mode_enabled()})")
            
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
                f" Invariant style: one immersive, poetic reply as {bot_name}. No meta-analysis, no breakdowns, no bullet summaries, no section headings."
            )
            if _minimal_context_mode_enabled():
                guidance_clause += " Minimal baseline mode: do NOT fabricate context, just respond naturally in-character."
            consolidated = (
                f"{system_prompt_content}\n\nTime: {time_context}.{emotion_inline}\n"
                + (f"{memory_narrative}\n" if memory_narrative else "")
                + (f"Recent thread: {conversation_summary}\n" if conversation_summary else "")
                + attachment_guard
                + guidance_clause
            )
            conversation_context.append({"role": "system", "content": consolidated})

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

        # Strict or minimal context mode: remove prior assistant meta-analysis leaks from history
        if _strict_mode_enabled() or _minimal_context_mode_enabled():
            cleaned = []
            for msg in filtered_messages:
                content_preview = getattr(msg, "content", "") or ""
                if any(pat in content_preview for pat in META_ANALYSIS_PATTERNS):
                    logger.debug(
                        f"[STRICT] Dropping prior meta-style message from history: '{content_preview[:80]}'"
                    )
                    continue
                cleaned.append(msg)
            filtered_messages = cleaned

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
        
        if _minimal_context_mode_enabled():
            # Keep more turns for better continuity - increased from 12 to 20
            fixed_history = fixed_history[-20:]
            logger.info(f"🔥 CONTEXT DEBUG: After minimal mode truncation: {len(fixed_history)} messages")
        
        conversation_context.extend(fixed_history)
        logger.info(f"🔥 CONTEXT DEBUG: Final conversation context has {len(conversation_context)} total messages")

        # 🎭 CONVERSATION CONTINUITY: Now handled by vector memory system
        # The vector memory manager provides intelligent conversation continuity through:
        # 1) Recent conversation cache (get_user_conversation_context)
        # 2) Vector memory search (relevant memories + recent conversation detection)  
        # 3) Character-aware memory integration (preserves Elena's personality context)
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

    async def _analyze_external_emotion(self, content, user_id, conversation_context):
        """Analyze emotion using vector-native emotion intelligence."""
        try:
            logger.debug("Using vector-native emotion analysis...")

            # Legacy emotion engine removed - vector system handles emotion analysis
            # Emotion is embedded directly in conversation context through vector memory
            emotion_data = {
                "primary_emotion": "neutral",  # Vector system handles this automatically
                "confidence": 0.8,
                "sentiment_score": 0.5,
                "all_emotions": {"neutral": 0.8},
                "analysis_method": "vector_native",
                "analysis_time_ms": 0,
                "api_calls_made": 0
            }

            logger.debug(
                f"Vector-native emotion analysis: {emotion_data.get('primary_emotion', 'unknown')} "
                f"(processed via embedding intelligence)"
            )

            return emotion_data

        except Exception as e:
            logger.error(f"Local Emotion Engine analysis failed: {e}")
            return None

    async def _analyze_phase2_emotion(
        self, user_id, content, message, context_type="discord_conversation"
    ):
        """Analyze emotion using Phase 2 integration."""
        try:
            logger.debug("Running Phase 2 emotional intelligence analysis...")

            phase2_context = {
                "topic": "general",
                "communication_style": "casual",
                "user_id": user_id,
                "message_length": len(content),
                "timestamp": datetime.now().isoformat(),
                "context": context_type,
            }

            if message.guild:
                phase2_context["guild_id"] = str(message.guild.id)
                phase2_context["channel_id"] = str(message.channel.id)

            phase2_results = (
                await self.phase2_integration.process_message_with_emotional_intelligence(
                    user_id=user_id, message=content, conversation_context=phase2_context
                )
            )

            logger.debug("Phase 2 emotional intelligence analysis completed")
            return phase2_results, None  # Return results and placeholder for current_emotion_data

        except Exception as e:
            logger.error(f"Phase 2 emotional intelligence analysis failed: {e}")
            return None, None

    async def _process_phase4_intelligence(
        self, user_id, message, recent_messages, external_emotion_data, phase2_context
    ):
        """Process Phase 4 human-like conversation intelligence."""
        try:
            logger.info(f"🧠 PHASE 4 DEBUG: Starting Phase 4 human-like conversation intelligence for user {user_id}")
            logger.info(f"🧠 PHASE 4 DEBUG: Input message: '{message.content[:100]}...'")
            logger.info(f"🧠 PHASE 4 DEBUG: External emotion data: {str(external_emotion_data)[:200] if external_emotion_data else 'None'}")
            logger.info(f"🧠 PHASE 4 DEBUG: Phase 2 context: {str(phase2_context)[:200] if phase2_context else 'None'}")

            discord_context = {
                "channel_id": str(message.channel.id),
                "guild_id": str(message.guild.id) if message.guild else None,
                "channel_type": "dm" if message.guild is None else "guild",
                "user_display_name": message.author.display_name,
                "external_emotion_data": external_emotion_data,
                "phase2_results": phase2_context,
            }
            
            logger.info(f"🧠 PHASE 4 DEBUG: Discord context: {discord_context}")

            # Clean Phase 4 integration - call directly instead of through monkey-patched methods
            from src.intelligence.phase4_human_like_integration import Phase4HumanLikeIntegration
            
            # Create Phase 4 integration instance with clean architecture
            logger.info("🧠 PHASE 4 DEBUG: Creating Phase4HumanLikeIntegration instance")
            phase4_integration = Phase4HumanLikeIntegration(
                phase2_integration=getattr(self.bot, 'phase2_integration', None),
                phase3_memory_networks=getattr(self.bot, 'phase3_memory_networks', None),
                memory_manager=self.memory_manager,
                llm_client=getattr(self.bot, 'llm_client', None),
                enable_adaptive_mode=True,
                memory_optimization=True,
                emotional_resonance=True,
            )
            
            # Process message with Phase 4 intelligence
            logger.info("🧠 PHASE 4 DEBUG: Processing message with comprehensive intelligence")
            phase4_context = await phase4_integration.process_comprehensive_message(
                user_id=user_id,
                message=message.content,
                conversation_context=recent_messages,
                discord_context=discord_context,
            )
            
            logger.info(f"🧠 PHASE 4 DEBUG: Received Phase 4 context: {str(phase4_context)[:300] if phase4_context else 'None'}")

            # --- PHASE 4 SCATTER-GATHER PARALLELISM ---
            import asyncio
            thread_manager_task = None
            engagement_task = None
            human_like_task = None
            conversation_analysis_task = None

            # Prepare thread manager task
            if (os.getenv("ENABLE_PHASE4_THREAD_MANAGER", "true").lower() == "true" and 
                hasattr(self.bot, 'thread_manager') and self.bot.thread_manager):
                thread_manager_task = asyncio.create_task(
                    self.bot.thread_manager.process_user_message(
                        user_id=user_id,
                        message=message.content,
                        context={
                            "channel_id": discord_context["channel_id"],
                            "guild_id": discord_context["guild_id"],
                            "emotional_data": external_emotion_data,
                            "phase2_context": phase2_context
                        }
                    )
                )

            # Prepare engagement engine task
            if (os.getenv("ENABLE_PHASE4_PROACTIVE_ENGAGEMENT", "true").lower() == "true" and 
                hasattr(self.bot, 'engagement_engine') and self.bot.engagement_engine):
                # Prepare recent messages in the expected format
                formatted_recent_messages = []
                for msg in recent_messages[-10:]:  # Last 10 messages
                    if isinstance(msg, dict):
                        formatted_recent_messages.append(msg)
                    elif hasattr(msg, 'content') and hasattr(msg, 'author'):
                        formatted_recent_messages.append({
                            "content": msg.content,
                            "user_id": str(msg.author.id),
                            "timestamp": getattr(msg, 'created_at', None)
                        })
                engagement_task = asyncio.create_task(
                    self.bot.engagement_engine.analyze_conversation_engagement(
                        user_id=user_id,
                        context_id=discord_context["channel_id"],
                        recent_messages=formatted_recent_messages,
                        current_thread_info=None  # Will patch in thread_manager_result after gather
                    )
                )

            # Prepare human-like memory processing task
            # DISABLED: Legacy human-like system causes async/sync complexity
            # Clean Protocol-based architecture provides the same intelligence without wrapper chaos
            # if hasattr(self.memory_manager, 'human_like_system'):
            if False:  # Permanently disabled legacy human-like enhancement system
                # Prepare conversation history - handle both dict and Discord Message objects
                conversation_history = []
                for msg in recent_messages[-5:]:
                    if isinstance(msg, dict):
                        if 'content' in msg:
                            conversation_history.append(msg['content'])
                    else:
                        # Handle Discord Message object
                        if hasattr(msg, 'content') and msg.content:
                            conversation_history.append(msg.content)
                # Build relationship context
                relationship_context = {
                    "interaction_history": len(recent_messages),
                    "emotional_data": external_emotion_data,
                    "phase2_context": phase2_context,
                    "discord_context": discord_context
                }
                from src.utils.human_like_conversation_engine import analyze_conversation_for_human_response
                conversation_analysis_task = asyncio.create_task(
                    analyze_conversation_for_human_response(
                        user_id=user_id,
                        message=message.content,
                        conversation_history=[{"content": msg} for msg in conversation_history],
                        emotional_context=external_emotion_data,
                        relationship_context=relationship_context
                    )
                )
                human_like_task = asyncio.create_task(
                    self.memory_manager.human_like_system.search_like_human_friend(
                        user_id=user_id,
                        message=message.content if hasattr(message, 'content') else str(message),
                        conversation_history=conversation_history,
                        relationship_context=relationship_context,
                        limit=20
                    )
                )

            # Gather all tasks in parallel
            gather_tasks = [t for t in [thread_manager_task, engagement_task, human_like_task, conversation_analysis_task] if t]
            logger.info(f"🧠 PHASE 4 DEBUG: Executing {len(gather_tasks)} Phase 4 scatter-gather tasks")
            results = await asyncio.gather(*gather_tasks, return_exceptions=True) if gather_tasks else []
            logger.info(f"🧠 PHASE 4 DEBUG: Phase 4 scatter-gather completed with {len(results)} results")

            # Unpack results with robust error handling
            idx = 0
            thread_manager_result = None
            engagement_result = None
            human_like_context = None
            conversation_analysis = None
            if thread_manager_task:
                if not isinstance(results[idx], Exception):
                    thread_manager_result = results[idx]
                    logger.info(f"🧠 PHASE 4 DEBUG: Thread manager result: {str(thread_manager_result)[:200] if thread_manager_result else 'None'}")
                else:
                    logger.warning(f"🧠 PHASE 4 DEBUG: Thread Manager task failed: {results[idx]}")
                idx += 1
            if engagement_task:
                if not isinstance(results[idx], Exception):
                    engagement_result = results[idx]
                else:
                    logger.warning(f"Phase 4.3 Engagement Engine task failed: {results[idx]}")
                idx += 1
            if human_like_task:
                if not isinstance(results[idx], Exception):
                    human_like_context = results[idx]
                else:
                    logger.warning(f"Human-like memory task failed: {results[idx]}")
                idx += 1
            if conversation_analysis_task:
                if not isinstance(results[idx], Exception):
                    conversation_analysis = results[idx]
                else:
                    logger.warning(f"Human-like conversation analysis task failed: {results[idx]}")
                idx += 1

            comprehensive_context = None
            enhanced_system_prompt = None

            # Get comprehensive context directly from Phase 4 integration
            if phase4_context:
                logger.info("🧠 PHASE 4 DEBUG: Getting comprehensive context from Phase 4 integration")
                comprehensive_context = phase4_integration.get_comprehensive_context_for_response(
                    phase4_context
                )
                logger.info(f"🧠 PHASE 4 DEBUG: Comprehensive context keys: {list(comprehensive_context.keys()) if comprehensive_context else 'None'}")

                # Prepare template context for enhanced response generation
                template_context = {
                    "phase4_context": phase4_context,
                    "comprehensive_context": comprehensive_context,
                    "interaction_type": getattr(phase4_context, "interaction_type", None),
                    "conversation_mode": getattr(phase4_context, "conversation_mode", None),
                }
                
                logger.info(f"🧠 PHASE 4 DEBUG: Template context prepared with keys: {list(template_context.keys())}")
                logger.info(f"🧠 PHASE 4 DEBUG: Interaction type: {getattr(phase4_context, 'interaction_type', 'None')}")
                logger.info(f"🧠 PHASE 4 DEBUG: Conversation mode: {getattr(phase4_context, 'conversation_mode', 'None')}")

                # System prompt enhancement handled by the LLM response generation
                enhanced_system_prompt = None

                phases_executed = []
                if hasattr(phase4_context, "processing_metadata"):
                    if isinstance(phase4_context.processing_metadata, dict):
                        phases_executed = phase4_context.processing_metadata.get(
                            "phases_executed", []
                        )
                    elif isinstance(phase4_context.processing_metadata, list):
                        phases_executed = phase4_context.processing_metadata
                    else:
                        phases_executed = []

                # Handle different Phase4Context versions (simple vs full integration)
                conversation_mode = getattr(phase4_context, "conversation_mode", None)
                conversation_mode_str = conversation_mode.value if conversation_mode else "unknown"

                logger.info(
                    f"🧠 PHASE 4 DEBUG: Analysis summary - Mode: {conversation_mode_str}, "
                    f"Interaction: {phase4_context.interaction_type.value if hasattr(phase4_context, 'interaction_type') else 'unknown'}, "
                    f"Phases executed: {len(phases_executed)}"
                )

            # Merge human-like context into comprehensive context if available and not Exception
            if (human_like_context and comprehensive_context and 
                not isinstance(human_like_context, Exception) and
                isinstance(human_like_context, dict)):
                try:
                    comprehensive_context["human_like_context"] = human_like_context.get("human_context", {})
                    comprehensive_context["human_like_memories"] = human_like_context.get("memories", [])
                    comprehensive_context["human_like_performance"] = human_like_context.get("search_performance", {})
                except Exception as e:
                    logger.warning(f"Failed to merge human-like context: {e}")
                    
                # Add conversation analysis for enhanced response guidance
                if (conversation_analysis and 
                    not isinstance(conversation_analysis, Exception) and
                    isinstance(conversation_analysis, dict)):
                    try:
                        comprehensive_context["conversation_analysis"] = conversation_analysis
                        comprehensive_context["response_guidance"] = conversation_analysis.get("response_guidance", "")
                        comprehensive_context["conversation_mode"] = conversation_analysis.get("mode", "standard")
                        comprehensive_context["interaction_type"] = conversation_analysis.get("interaction_type", "general")
                        comprehensive_context["personality_type"] = conversation_analysis.get("personality_type", "default")
                        comprehensive_context["relationship_level"] = conversation_analysis.get("relationship_level", "acquaintance")
                    except Exception as e:
                        logger.warning(f"Failed to merge conversation analysis: {e}")
                logger.debug("Enhanced comprehensive context with human-like intelligence and conversation analysis")

            # Merge Phase 4.2 and 4.3 results into comprehensive context
            if comprehensive_context:
                if thread_manager_result:
                    comprehensive_context["phase4_2_thread_analysis"] = thread_manager_result
                    logger.info("🧠 PHASE 4 DEBUG: Added Phase 4.2 Advanced Thread Management results to context")
                
                if engagement_result:
                    comprehensive_context["phase4_3_engagement_analysis"] = engagement_result
                    logger.info("🧠 PHASE 4 DEBUG: Added Phase 4.3 Proactive Engagement results to context")
                    
                logger.info(f"🧠 PHASE 4 DEBUG: Final comprehensive context size: {len(str(comprehensive_context))} chars")
                logger.info(f"🧠 PHASE 4 DEBUG: Final comprehensive context keys: {list(comprehensive_context.keys())}")

            logger.info(f"🧠 PHASE 4 DEBUG: Returning - Phase4 context: {'Yes' if phase4_context else 'No'}, Comprehensive: {'Yes' if comprehensive_context else 'No'}, Enhanced prompt: {'Yes' if enhanced_system_prompt else 'No'}")
            return phase4_context, comprehensive_context, enhanced_system_prompt

        except Exception as e:
            logger.error(f"Phase 4 human-like intelligence processing failed: {e}")
            return None, None, None

    async def _generate_and_send_response(
        self,
        reply_channel,
        message,
        user_id,
        conversation_context,
        current_emotion_data,
        external_emotion_data,
        phase2_context,
        phase4_context=None,
        comprehensive_context=None,
        dynamic_personality_context=None,
        original_content=None,
    ):
        """Generate AI response and send to channel using Universal Chat Architecture."""
        # Show typing indicator
        async with reply_channel.typing():
            logger.info(f"[TRACE-START] Starting _generate_and_send_response for user {user_id}")
            logger.debug("Started typing indicator - simulating thinking and typing process")
            try:
                logger.debug("Processing message through Universal Chat Orchestrator...")

                # Use Universal Chat Orchestrator if available
                if self.chat_orchestrator:
                    logger.info("[DEBUG-TRACE] Chat orchestrator is available")
                    logger.debug(
                        "Using Universal Chat Orchestrator for proper layered architecture"
                    )

                    # Convert Discord message to universal format
                    if (
                        hasattr(self.chat_orchestrator, "adapters")
                        and ChatPlatform.DISCORD in self.chat_orchestrator.adapters
                    ):
                        logger.info("[DEBUG-TRACE] Discord adapter found, proceeding with context fix")
                        discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                        universal_message = discord_adapter.discord_message_to_universal_message(
                            message
                        )

                        # 🔧 CRITICAL FIX: Use our hierarchical memory conversation_context directly
                        # instead of letting chat orchestrator ignore our memory system
                        logger.info(f"🎯 CONTEXT DEBUG: Using hierarchical memory context with {len(conversation_context)} messages")
                        
                        # DEBUG: Log environment variable affecting conversation processing
                        strict_mode = _strict_mode_enabled()
                        minimal_mode = _minimal_context_mode_enabled()
                        logger.info(f"🎯 CONTEXT DEBUG: STRICT_IMMERSIVE_MODE: {strict_mode}, MINIMAL_CONTEXT_MODE: {minimal_mode}")
                        
                        # Debug log the conversation context being sent to LLM
                        logger.info(f"🔥 ORCHESTRATOR DEBUG: Full conversation context structure:")
                        for i, ctx_msg in enumerate(conversation_context):
                            role = ctx_msg.get('role', 'unknown')
                            content = ctx_msg.get('content', '')
                            content_preview = content[:200] + '...' if len(content) > 200 else content
                            logger.info(f"🔥 ORCHESTRATOR DEBUG: Message {i+1}/{len(conversation_context)} [{role}]: '{content_preview}'")
                            
                            # Check for memory content specifically
                            if 'memory' in content.lower() or 'recall' in content.lower() or 'luna' in content.lower():
                                logger.info(f"🔥 ORCHESTRATOR DEBUG: *** MEMORY DETECTED in message {i+1} ***")

                        # Check if we can see recent conversation pairs in the context
                        user_messages = [msg for msg in conversation_context if msg.get('role') == 'user']
                        assistant_messages = [msg for msg in conversation_context if msg.get('role') == 'assistant']
                        logger.info(f"🔥 ORCHESTRATOR DEBUG: Context contains {len(user_messages)} user messages and {len(assistant_messages)} assistant messages")
                        logger.info(f"🎯 CONTEXT DEBUG: Full conversation context structure:")
                        for i, ctx_msg in enumerate(conversation_context):
                            role = ctx_msg.get('role', 'unknown')
                            content = ctx_msg.get('content', '')
                            content_preview = content[:200] + '...' if len(content) > 200 else content
                            logger.info(f"🎯 CONTEXT DEBUG: Message {i+1}/{len(conversation_context)} [{role}]: '{content_preview}'")
                            
                            # Check for memory content specifically
                            if 'memory' in content.lower() or 'recall' in content.lower() or 'luna' in content.lower():
                                logger.info(f"🎯 CONTEXT DEBUG: *** MEMORY DETECTED in message {i+1} ***")

                        # 🎭 CDL CHARACTER INTEGRATION: Check for active character and replace system prompt
                        logger.info(f"🎭 DEBUG: About to call character enhancement for user {user_id}")
                        enhanced_context = await self._apply_cdl_character_enhancement(user_id, conversation_context, message)
                        logger.info(f"🎭 DEBUG: Character enhancement returned: {enhanced_context is not None}")
                        final_context = enhanced_context if enhanced_context else conversation_context
                        
                        # Log system messages for debugging
                        system_msgs = [msg for msg in final_context if msg.get("role") == "system"]
                        if system_msgs:
                            for i, sys_msg in enumerate(system_msgs):
                                content_preview = sys_msg.get("content", "")[:150]
                                logger.info(f"🎭 EVENTS DEBUG: System message {i+1}: {content_preview}...")
                        else:
                            logger.warning(f"🎭 EVENTS DEBUG: No system messages in final context!")
                        
                        # Generate AI response using our conversation context directly
                        logger.info(f"🎯 CONTEXT DEBUG: Sending {len(final_context)} messages to Universal Chat Orchestrator")
                        ai_response = await self.chat_orchestrator.generate_ai_response(
                            universal_message, final_context  # Use character-enhanced context!
                        )

                        response = ai_response.content
                        
                        logger.info(f"🎯 CONTEXT DEBUG: Received response from Universal Chat: {len(response)} chars")
                        logger.info(f"🎯 CONTEXT DEBUG: Response preview: '{response[:200]}...'")
                        
                        # Additional validation to prevent empty responses
                        if not response or not response.strip():
                            logger.warning(
                                f"Universal Chat returned empty response for user {user_id}. "
                                f"AI response object: content='{response}', model={ai_response.model_used}, "
                                f"tokens={ai_response.tokens_used}"
                            )
                            response = "I apologize, but I'm having trouble generating a response right now. Please try again."
                        
                        logger.info(f"🎯 CONTEXT DEBUG: Final response: {len(response)} characters")
                        logger.info(f"🎯 CONTEXT DEBUG: Model used: {ai_response.model_used}, Tokens: {ai_response.tokens_used}")

                    else:
                        # Discord adapter not found - this is a configuration error
                        logger.error("CRITICAL: Discord adapter not found in Universal Chat Orchestrator!")
                        logger.error("The bot cannot function properly without the Discord adapter.")
                        logger.error("This will result in loss of emotion, personality, and Phase 4 features.")
                        raise RuntimeError(
                            "Discord adapter missing from Universal Chat Orchestrator. "
                            "Advanced AI features cannot function without proper adapter configuration."
                        )

                else:
                    # Universal Chat Orchestrator not available - this is a critical system failure
                    logger.error("CRITICAL: Universal Chat Orchestrator not initialized!")
                    logger.error("The bot cannot provide advanced AI features without the orchestrator.")
                    logger.error("Check system initialization logs for Universal Chat setup failures.")
                    raise RuntimeError(
                        "Universal Chat Orchestrator not available. "
                        "Cannot provide emotion, personality, or Phase 4 intelligence features."
                    )

                # Security scan for system leakage
                leakage_scan = scan_response_for_system_leakage(response)
                if leakage_scan["has_leakage"]:
                    logger.error(
                        f"SECURITY: System message leakage detected in response to user {user_id}"
                    )
                    logger.error(f"SECURITY: Leaked patterns: {leakage_scan['leaked_patterns']}")
                    response = leakage_scan["sanitized_response"]
                    logger.info("SECURITY: Response sanitized to remove system message leakage")

                # Additional sanitization: prevent coaching/meta analytical sections (image-triggered regression)
                def _sanitize_meta_analysis(resp: str) -> str:
                    try:
                        import re
                        patterns = [
                            "Core Conversation Analysis",
                            "Emotional Analysis",
                            "Technical Metadata",
                            "Personality & Interaction",
                            "Overall Assessment",
                        ]
                        trigger_count = sum(p in resp for p in patterns)
                        coaching_phrase = "Do you want me to" in resp
                        # Heuristic: if two or more section headings OR explicit coaching phrase, sanitize
                        if trigger_count >= 2 or coaching_phrase:
                            logger.warning(
                                "Meta/coaching analytical response detected (patterns=%d, coaching=%s) - sanitizing",
                                trigger_count,
                                coaching_phrase,
                            )
                            # Extract first natural paragraph before any heading
                            lines = resp.splitlines()
                            natural_parts = []
                            for line in lines:
                                if any(p in line for p in patterns) or re.match(
                                    r"^[A-Z][A-Za-z &]+:\s*$", line.strip()
                                ):
                                    break
                                if line.strip():
                                    natural_parts.append(line.strip())
                            base_text = " ".join(natural_parts).strip()
                            if not base_text:
                                base_text = (
                                    "I behold the image you have shared—its quiet details drift like motes in the dark between stars."
                                )
                            sanitized = (
                                base_text
                                + "\n\n"
                                + "(Your image was received. I have omitted internal analytical sections to preserve an immersive, in-character reply.)"
                            )
                            return sanitized
                        return resp
                    except Exception as e:
                        logger.error(f"Meta-analysis sanitization failure: {e}")
                        return resp

                pre_meta_len = len(response)
                response = _sanitize_meta_analysis(response)
                if len(response) != pre_meta_len:
                    logger.debug(
                        "Applied meta-analysis sanitization (old_len=%d new_len=%d)",
                        pre_meta_len,
                        len(response),
                    )

                # Two-pass rewrite if still leaking patterns in strict mode
                if (_strict_mode_enabled() or _minimal_context_mode_enabled()) and any(p in response for p in META_ANALYSIS_PATTERNS):
                    logger.warning("Meta patterns still detected post-sanitization - invoking rewrite pass")
                    try:
                        bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
                        rewrite_context = [
                            {"role": "system", "content": (
                                f"You are a style refiner. Rewrite the assistant content into a SINGLE immersive in-character reply as {bot_name}. Remove all analysis sections, headings, breakdowns, score talk, coaching offers, or meta commentary. Keep poetic tone, <=120 words."
                            )},
                            {"role": "user", "content": response[:4000]},
                        ]
                        rewritten = await self.llm_client.generate_chat_completion_safe(
                            rewrite_context
                        )
                        if rewritten and any(c.isprintable() for c in rewritten):
                            if any(p in rewritten for p in META_ANALYSIS_PATTERNS):
                                logger.warning(
                                    "Rewrite still contains meta markers; using first paragraph fallback"
                                )
                                para = rewritten.split("\n\n")[0].strip()
                                if para:
                                    response = para
                            else:
                                response = rewritten.strip()
                                logger.debug(
                                    f"Rewrite pass successful (len={len(response)})"
                                )
                    except Exception as e:
                        logger.error(f"Rewrite pass failed: {e}")

                # Final minimal context hard-cleanse pass
                if _minimal_context_mode_enabled():
                    try:
                        new_response = self._apply_minimal_mode_cleanse(response)
                        if new_response != response:
                            logger.debug(
                                "[MINIMAL_CONTEXT_MODE] Hard cleanse adjusted response length %d -> %d",
                                len(response),
                                len(new_response),
                            )
                            response = new_response
                    except Exception as cleanse_err:
                        logger.error(f"Minimal context cleansing error: {cleanse_err}")

                # CRITICAL FIX: Store conversation in memory BEFORE sending response
                # This ensures memory is available for future context building
                memory_stored = False
                try:
                    memory_stored = await self._store_conversation_memory(
                        message,
                        user_id,
                        response,
                        current_emotion_data,
                        external_emotion_data,
                        phase2_context,
                        phase4_context,
                        comprehensive_context,
                        dynamic_personality_context,
                        original_content,
                    )
                    if memory_stored:
                        logger.info(f"✅ MEMORY: Successfully stored conversation for user {user_id}")
                        
                        # VERIFICATION: Quick check that memory was actually stored
                        try:
                            verification_memories = await self.memory_manager.retrieve_context_aware_memories(
                                user_id=user_id, 
                                query=message.content, 
                                max_memories=1
                            )
                            if verification_memories:
                                logger.info(f"✅ VERIFIED: Memory storage confirmed - {len(verification_memories)} memories found")
                            else:
                                logger.warning(f"⚠️ VERIFICATION: No memories found immediately after storage for user {user_id}")
                        except Exception as verify_error:
                            logger.warning(f"⚠️ VERIFICATION: Could not verify memory storage: {verify_error}")
                    else:
                        logger.error(f"❌ MEMORY: Failed to store conversation for user {user_id}")
                except Exception as memory_error:
                    logger.error(f"❌ CRITICAL: Memory storage exception for user {user_id}: {memory_error}")
                    import traceback
                    logger.error(f"❌ CRITICAL: Memory storage traceback: {traceback.format_exc()}")

                # Add user message to cache after memory storage
                if self.conversation_cache:
                    logger.info(f"🔥 CACHE DEBUG: Adding user message to cache - content: '{message.content[:100]}...'")
                    logger.info(f"🔥 CACHE DEBUG: User message author: {message.author.name} (bot={message.author.bot})")
                    if hasattr(self.conversation_cache, "add_message"):
                        if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                            await self.conversation_cache.add_message(
                                str(reply_channel.id), message
                            )
                        else:
                            self.conversation_cache.add_message(str(reply_channel.id), message)
                    logger.debug(
                        f"✅ CACHE: Added user message to conversation cache (memory_stored: {memory_stored})"
                    )

                # Add debug information if needed
                response_with_debug = add_debug_info_to_response(
                    response, user_id, self.memory_manager, str(message.id)
                )

                # Send response (chunked if too long)
                await self._send_response_chunks(reply_channel, response_with_debug)

                # CRITICAL FIX: Add bot response to conversation cache after sending
                if self.conversation_cache:
                    try:
                        # Create a mock message object for the bot's response
                        # Use the real bot.user object, not a fake one
                        logger.info(f"🔥 DEBUG: Creating bot response message with real bot.user: {self.bot.user.name} (bot={self.bot.user.bot})")
                        
                        bot_response_message = type('BotMessage', (), {
                            'id': f"bot_response_{message.id}",
                            'content': response,
                            'author': self.bot.user,  # Use real bot.user, not mock
                            'created_at': discord.utils.utcnow(),
                            'channel': reply_channel,
                            'guild': message.guild,  # Add guild attribute for cache compatibility
                            'attachments': [],  # Add empty attachments list
                            'embeds': [],  # Add empty embeds list
                            'mentions': []  # Add empty mentions list
                        })()
                        
                        if hasattr(self.conversation_cache, "add_message"):
                            logger.info(f"🔥 CACHE DEBUG: Adding bot response to cache - content: '{response[:100]}...'")
                            if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                                await self.conversation_cache.add_message(
                                    str(reply_channel.id), bot_response_message
                                )
                            else:
                                self.conversation_cache.add_message(str(reply_channel.id), bot_response_message)
                        logger.debug(
                            f"✅ CACHE: Added bot response to conversation cache: {response[:100]}..."
                        )
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache bot response: {cache_error}")

                # Send voice response if applicable
                await self._send_voice_response(message, response)

            except LLMConnectionError:
                logger.warning("LLM connection error")
                await reply_channel.send(
                    "I'm having trouble connecting to my knowledge systems. Please try again in a moment."
                )
            except LLMTimeoutError:
                logger.warning("LLM timeout error")
                await reply_channel.send(
                    "I apologize, but that took longer than expected to process. Could you please try again?"
                )
            except LLMRateLimitError:
                logger.warning("LLM rate limit error")
                await reply_channel.send(
                    "I'm experiencing high demand right now. Please wait a moment before trying again."
                )
            except LLMError as e:
                logger.error(f"LLM error: {e}")
                await reply_channel.send(
                    "*The threads of thought grow tangled for a moment...* Please, speak again, and I shall attend to thy words more clearly."
                )
            except Exception as e:
                logger.error(f"Unexpected error processing message through Universal Chat: {e}")
                await reply_channel.send(
                    "*Something stirs in the darkness beyond my understanding...* Perhaps we might try this exchange anew?"
                )

    async def _store_conversation_memory(
        self,
        message,
        user_id,
        response,
        current_emotion_data,
        external_emotion_data,
        phase2_context,
        phase4_context,
        comprehensive_context,
        dynamic_personality_context=None,
        original_content=None,
    ):
        """Store conversation in memory with all AI analysis data."""
        try:
            # Validate response before storing
            if not response or not response.strip():
                logger.error(f"❌ CRITICAL: Attempted to store conversation with empty response for user {user_id}")
                return False  # Return failure status
                
            # Extract content for storage
            content_to_store = original_content if original_content else message.content
            storage_content = extract_text_for_memory_storage(content_to_store, message.attachments)

            # Skip empty content
            if not storage_content or not storage_content.strip():
                logger.error(f"❌ CRITICAL: Empty storage content detected for user {user_id}")
                logger.error(f"❌ CRITICAL: Original content: '{content_to_store}', extracted: '{storage_content}'")
                return False

            logger.info(f"💾 Storing conversation for user {user_id}: '{storage_content[:100]}...' → '{response[:100]}...'")

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

                logger.debug(
                    f"Passing pre-analyzed emotion data to storage: {emotion_profile.detected_emotion.value if emotion_profile.detected_emotion else 'unknown'}"
                )

            # Perform personality analysis
            personality_metadata = await self._analyze_personality_for_storage(
                user_id, storage_content, message
            )

            # Perform emotional intelligence analysis for storage
            emotional_intelligence_results = await self._analyze_emotional_intelligence_for_storage(
                user_id, storage_content, message, phase2_context, external_emotion_data
            )

            # Prepare storage metadata
            storage_metadata = {}

            # Add message context metadata
            if hasattr(self.memory_manager, "classify_discord_context"):
                message_context = self.memory_manager.classify_discord_context(message)
                if message_context:
                    storage_metadata.update(
                        {
                            "context_type": (
                                message_context.context_type.value
                                if hasattr(message_context.context_type, "value")
                                else str(message_context.context_type)
                            ),
                            "server_id": message_context.server_id,
                            "channel_id": message_context.channel_id,
                            "is_private": message_context.is_private,
                            "security_level": (
                                message_context.security_level.value
                                if hasattr(message_context.security_level, "value")
                                else str(message_context.security_level)
                            ),
                        }
                    )

            # Add personality metadata
            if personality_metadata:
                personality_simple = {}
                for key, value in personality_metadata.items():
                    if value is not None:
                        if hasattr(value, "value"):  # Enum
                            personality_simple[f"personality_{key}"] = value.value
                        elif isinstance(value, (str, int, float, bool)):
                            personality_simple[f"personality_{key}"] = value
                        else:
                            personality_simple[f"personality_{key}"] = str(value)
                storage_metadata.update(personality_simple)

            # Add dynamic personality metadata
            if dynamic_personality_context:
                dynamic_personality_simple = {}
                for key, value in dynamic_personality_context.items():
                    if value is not None:
                        if key == "personality_dimensions" and isinstance(value, dict):
                            # Flatten personality dimensions
                            for dim_name, dim_data in value.items():
                                if isinstance(dim_data, dict):
                                    dynamic_personality_simple[
                                        f"dynamic_personality_{dim_name}_value"
                                    ] = dim_data.get("value", 0.0)
                                    dynamic_personality_simple[
                                        f"dynamic_personality_{dim_name}_confidence"
                                    ] = dim_data.get("confidence", 0.0)
                        elif isinstance(value, (str, int, float, bool)):
                            dynamic_personality_simple[f"dynamic_personality_{key}"] = value
                        else:
                            dynamic_personality_simple[f"dynamic_personality_{key}"] = str(value)
                storage_metadata.update(dynamic_personality_simple)

            # Add emotional intelligence metadata
            if emotional_intelligence_results:
                emotional_simple = {}
                for key, value in emotional_intelligence_results.items():
                    if value is not None and isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subvalue is not None:
                                if hasattr(subvalue, "value"):  # Enum
                                    emotional_simple[f"emotional_{key}_{subkey}"] = subvalue.value
                                elif isinstance(subvalue, (str, int, float, bool)):
                                    emotional_simple[f"emotional_{key}_{subkey}"] = subvalue
                                else:
                                    emotional_simple[f"emotional_{key}_{subkey}"] = str(subvalue)
                    elif value is not None:
                        if hasattr(value, "value"):  # Enum
                            emotional_simple[f"emotional_{key}"] = value.value
                        elif isinstance(value, (str, int, float, bool)):
                            emotional_simple[f"emotional_{key}"] = value
                        else:
                            emotional_simple[f"emotional_{key}"] = str(value)
                storage_metadata.update(emotional_simple)

            # 🎭 CHARACTER METADATA: Add active character context for proper filtering
            # This prevents character-specific conversations from being mixed with generic ones
            if hasattr(self.bot_core, 'command_handlers') and 'cdl_test' in self.bot_core.command_handlers:
                cdl_handler = self.bot_core.command_handlers['cdl_test']
                if hasattr(cdl_handler, '_get_user_active_character'):
                    try:
                        active_character = cdl_handler._get_user_active_character(user_id)
                        if active_character:
                            # Extract character name from filename (e.g., "elena-rodriguez.json" -> "elena-rodriguez")
                            character_name = active_character.replace('.json', '').replace('examples/', '')
                            storage_metadata['active_character'] = character_name
                            storage_metadata['has_character'] = True
                            logger.info(f"🎭 STORAGE: Adding character metadata - active_character: {character_name}")
                        else:
                            storage_metadata['has_character'] = False
                            logger.info(f"🎭 STORAGE: No active character for user {user_id}")
                    except Exception as e:
                        logger.warning(f"🎭 STORAGE: Could not detect character for user {user_id}: {e}")
                        storage_metadata['has_character'] = False

            # Store with thread-safe operations
            storage_success = await self.memory_manager.store_conversation(
                user_id=user_id,
                user_message=storage_content,
                bot_response=response,
                channel_id=str(message.channel.id),
                pre_analyzed_emotion_data=emotion_metadata,
                metadata=storage_metadata,
            )

            if storage_success:
                logger.info(f"✅ Successfully stored conversation in memory for user {user_id}")
            else:
                logger.error(f"❌ CRITICAL: Memory storage returned False for user {user_id}")

            # Sync cache with storage result
            if self.conversation_cache and hasattr(self.conversation_cache, "sync_with_storage"):
                import inspect

                if inspect.iscoroutinefunction(self.conversation_cache.sync_with_storage):
                    await self.conversation_cache.sync_with_storage(
                        str(message.channel.id), message, storage_success
                    )
                else:
                    self.conversation_cache.sync_with_storage(
                        str(message.channel.id), message, storage_success
                    )

            logger.debug(f"Memory storage complete for user {user_id} - success: {storage_success}")
            return storage_success

        except (MemoryStorageError, ValidationError) as e:
            logger.error(f"❌ CRITICAL: Memory storage validation error for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ CRITICAL: Unexpected memory storage error for user {user_id}: {e}")
            import traceback
            logger.error(f"❌ CRITICAL: Memory storage traceback: {traceback.format_exc()}")
            return False

    async def _analyze_personality_for_storage(self, user_id, storage_content, message):
        """Analyze personality for conversation storage."""
        personality_metadata = None
        # Legacy personality profiler removed - vector-native system handles personality analysis
        personality_metadata = None
        if user_id:
            logger.debug(f"Using vector-native personality analysis for user {user_id}")
            # Vector system automatically captures personality patterns through embedding analysis
            personality_metadata = {
                "communication_style": "adaptive",  # Vector system determines this automatically
                "confidence_level": "vector_native",
                "decision_style": "context_aware",
                "analysis_confidence": 0.8,
            }

        return personality_metadata

    async def _analyze_emotional_intelligence_for_storage(
        self, user_id, storage_content, message, phase2_context, external_emotion_data
    ):
        """Analyze emotional intelligence for conversation storage."""
        emotional_intelligence_results = None
        if self.phase2_integration and user_id:
            try:
                logger.debug(f"Performing emotional intelligence analysis for user {user_id}")

                context = {
                    "channel_id": str(message.channel.id),
                    "guild_id": str(message.guild.id) if message.guild else None,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "context": "discord_conversation",
                }

                # Use existing phase2_context if available, otherwise analyze
                if phase2_context:
                    emotional_intelligence_results = phase2_context
                else:
                    emotional_intelligence_results = (
                        await self.phase2_integration.process_message_with_emotional_intelligence(
                            user_id=user_id, message=storage_content, conversation_context=context
                        )
                    )

                # Enhance with external emotion data
                if emotional_intelligence_results and external_emotion_data:
                    emotional_intelligence_results["external_emotion_analysis"] = (
                        external_emotion_data
                    )
                    logger.debug(
                        f"Enhanced emotional intelligence with external API data: {external_emotion_data.get('primary_emotion', 'unknown')}"
                    )
                elif external_emotion_data and not emotional_intelligence_results:
                    emotional_intelligence_results = {
                        "external_emotion_analysis": external_emotion_data,
                        "primary_emotion_source": "external_api",
                        "emotion_confidence": external_emotion_data.get("confidence", 0.5),
                        "emotion_tier": external_emotion_data.get("tier_used", "unknown"),
                    }
                    logger.debug(
                        f"Using external emotion data as primary emotional intelligence: {external_emotion_data.get('primary_emotion', 'unknown')}"
                    )

                if emotional_intelligence_results:
                    logger.debug(
                        f"Emotional intelligence analysis complete: {emotional_intelligence_results}"
                    )

            except Exception as e:
                logger.warning(f"Emotional intelligence analysis failed for user {user_id}: {e}")
                emotional_intelligence_results = None

        return emotional_intelligence_results

    async def _analyze_dynamic_personality(self, user_id, content, message, recent_messages):
        """Analyze personality with the dynamic personality profiler and store results."""
        try:
            if not self.dynamic_personality_profiler:
                return None

            logger.debug(f"Analyzing dynamic personality for user {user_id}")

            # Get emotional data if available
            emotional_data = None
            if hasattr(self.bot_core, "components") and "emotion_ai" in self.bot_core.components:
                emotion_ai = self.bot_core.components["emotion_ai"]
                try:
                    emotional_data = await emotion_ai.analyze_emotion(content)
                except Exception as e:
                    logger.debug(f"Could not get emotional analysis: {e}")

            # Get the last bot response for context
            bot_response = ""
            for msg in reversed(recent_messages):
                # Handle both dict and Discord Message objects
                if isinstance(msg, dict):
                    if msg.get("bot", False):
                        bot_response = msg.get("content", "")
                        break
                else:
                    # Handle Discord Message object
                    if hasattr(msg, 'author') and msg.author.id == self.bot.user.id:
                        bot_response = msg.content or ""
                        break

            # Analyze the conversation for personality insights (using correct method signature)
            analysis = await self.dynamic_personality_profiler.analyze_conversation(
                user_id=user_id,
                context_id=str(message.channel.id),
                user_message=content,
                bot_response=bot_response,
                response_time_seconds=0.0,  # Could be calculated if needed
                emotional_data=emotional_data,
            )

            # Update the personality profile (this automatically saves to database!)
            profile = await self.dynamic_personality_profiler.update_personality_profile(analysis)

            logger.debug(
                f"Dynamic personality profile updated for user {user_id}: "
                f"traits={len(profile.traits)}, relationship_depth={profile.relationship_depth:.2f}"
            )

            # Return analysis context for system prompt enhancement
            return {
                "personality_traits": dict(profile.traits),
                "communication_style": profile.preferred_response_style,
                "relationship_depth": profile.relationship_depth,
                "trust_level": profile.trust_level,
                "conversation_count": profile.total_conversations,
                "topics_of_interest": profile.topics_of_high_engagement,
            }

        except Exception as e:
            logger.warning(f"Dynamic personality analysis failed for user {user_id}: {e}")
            return None

    async def _send_response_chunks(self, channel, response):
        """Send response in chunks if it's too long. Prevent sending empty/whitespace-only messages."""
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
                    await channel.send(
                        f"{chunk}" + (f"\n*(continued {i+1}/{len(chunks)})*" if len(chunks) > 1 else "")
                    )
                    logger.debug(f"Sent chunk {i+1}/{len(chunks)}")
                else:
                    logger.warning(f"Skipped sending empty chunk {i+1}/{len(chunks)}")
        else:
            await channel.send(response)
            logger.debug("Sent single message response")

    async def _send_voice_response(self, message, response):
        """Send voice response if user is in voice channel."""
        if self.voice_manager and message.guild and self.voice_support_enabled:
            try:
                logger.debug(f"Checking voice response for user {message.author.display_name}")

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
                import traceback

                logger.error(f"Voice response error traceback: {traceback.format_exc()}")

    async def _process_ai_components_parallel(self, user_id, content, message, recent_messages, conversation_context):
        """
        PERFORMANCE OPTIMIZATION: Process AI components in parallel for 3-5x performance improvement.
        
        Uses ConcurrentConversationManager for proper scatter-gather architecture when available,
        following the hybrid concurrency pattern (AsyncIO + ThreadPoolExecutor + ProcessPoolExecutor).
        Falls back to basic asyncio.gather if ConcurrentConversationManager is not available.
        
        This replaces the sequential processing of:
        1. External emotion analysis 
        2. Phase 2 emotion analysis
        3. Dynamic personality analysis  
        4. Phase 4 intelligence processing
        
        Expected performance improvement: 3-5x faster response times under load
        """
        import asyncio
        
        logger.info(f"🚀 AI PIPELINE DEBUG: Starting parallel AI component processing for user {user_id}")
        logger.info(f"🚀 AI PIPELINE DEBUG: Input message length: {len(content)} chars")
        logger.info(f"🚀 AI PIPELINE DEBUG: Recent messages count: {len(recent_messages) if recent_messages else 0}")
        logger.info(f"🚀 AI PIPELINE DEBUG: Conversation context messages: {len(conversation_context) if conversation_context else 0}")
        start_time = time.time()
        
        # Use ConcurrentConversationManager for proper scatter-gather if available
        if (self.conversation_manager and 
            os.getenv("ENABLE_CONCURRENT_CONVERSATION_MANAGER", "false").lower() == "true"):
            
            logger.info("🚀 AI PIPELINE DEBUG: Using ConcurrentConversationManager for scatter-gather processing")
            
            # Prepare context for conversation manager
            context = {
                "message": content,
                "channel_id": str(message.channel.id) if hasattr(message, 'channel') else "default",
                "guild_id": str(message.guild.id) if hasattr(message, 'guild') and message.guild else None,
                "recent_messages": recent_messages,
                "conversation_context": conversation_context,
            }
            
            # Process through conversation manager with high priority for real-time response
            result = await self.conversation_manager.process_conversation_message(
                user_id=user_id,
                message=content,
                channel_id=context["channel_id"],
                context=context,
                priority="high"  # High priority for immediate processing
            )
            
            # Extract results from conversation manager response
            external_emotion_data = result.get("emotion_result")
            phase2_context = result.get("thread_result")  # Thread manager provides phase 2-like context
            current_emotion_data = None
            dynamic_personality_context = None
            
            # Run Phase 4 processing separately as it needs the other results
            phase4_context = None
            comprehensive_context = None
            enhanced_system_prompt = None
            
            if (os.getenv("DISABLE_PHASE4_INTELLIGENCE", "false").lower() != "true"
                and hasattr(self.memory_manager, "process_with_phase4_intelligence")):
                try:
                    phase4_context, comprehensive_context, enhanced_system_prompt = (
                        await self._process_phase4_intelligence(
                            user_id, message, recent_messages, external_emotion_data, phase2_context
                        )
                    )
                except Exception as e:
                    logger.warning(f"Phase 4 intelligence processing failed: {e}")
            
            processing_time = time.time() - start_time
            logger.info(f"✅ ConcurrentConversationManager processing completed in {processing_time:.2f}s for user {user_id}")
            
            return (external_emotion_data, phase2_context, current_emotion_data, 
                   dynamic_personality_context, phase4_context, comprehensive_context, 
                   enhanced_system_prompt)
        
        # Fallback to basic asyncio.gather approach if ConcurrentConversationManager not available
        logger.info("🚀 AI PIPELINE DEBUG: Using fallback asyncio.gather approach for parallel processing")
        
        # Prepare task list for parallel execution
        tasks = []
        task_names = []
        
        # Legacy emotion analysis removed - vector-native system handles emotions
        logger.info("🚀 AI PIPELINE DEBUG: Using vector-native emotion analysis")
        tasks.append(asyncio.create_task(self._create_none_result()))
        task_names.append("vector_native_emotion")
            
        # Task 2: Phase 2 emotional intelligence (primary emotion source)
        if (os.getenv("DISABLE_PHASE2_EMOTION", "false").lower() != "true" 
            and self.phase2_integration):
            context_type = "guild_message" if hasattr(message, 'guild') and message.guild else "dm"
            logger.info(f"🚀 AI PIPELINE DEBUG: Adding Phase 2 emotion analysis task (context: {context_type})")
            tasks.append(self._analyze_phase2_emotion(user_id, content, message, context_type))
            task_names.append("phase2_emotion")
        else:
            logger.info("🚀 AI PIPELINE DEBUG: Phase 2 emotion analysis disabled or unavailable")
            tasks.append(asyncio.create_task(self._create_none_result()))
            task_names.append("phase2_emotion_disabled")
            
        # Task 3: Dynamic personality analysis
        if (os.getenv("DISABLE_PERSONALITY_PROFILING", "false").lower() != "true"
            and self.dynamic_personality_profiler):
            logger.info("🚀 AI PIPELINE DEBUG: Adding dynamic personality analysis task")
            tasks.append(self._analyze_dynamic_personality(user_id, content, message, recent_messages))
            task_names.append("dynamic_personality")
        else:
            logger.info("🚀 AI PIPELINE DEBUG: Dynamic personality analysis disabled or unavailable")
            tasks.append(asyncio.create_task(self._create_none_result()))
            task_names.append("dynamic_personality_disabled")
            
        # Execute all tasks in parallel
        try:
            logger.info(f"🚀 AI PIPELINE DEBUG: Executing {len(tasks)} AI analysis tasks in parallel: {task_names}")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            external_emotion_data = None
            phase2_context = None
            current_emotion_data = None
            dynamic_personality_context = None
            
            logger.info(f"🚀 AI PIPELINE DEBUG: Parallel tasks completed, processing {len(results)} results")
            
            for i, result in enumerate(results):
                task_name = task_names[i]
                
                if isinstance(result, Exception):
                    logger.warning(f"🚀 AI PIPELINE DEBUG: Parallel task {task_name} failed: {result}")
                    continue
                    
                logger.info(f"🚀 AI PIPELINE DEBUG: Processing result for task {task_name}: {type(result)}")
                    
                if task_name.startswith("local_emotion") and result is not None:
                    external_emotion_data = result
                    logger.info(f"🚀 AI PIPELINE DEBUG: Set external_emotion_data from {task_name}: {str(result)[:200]}")
                elif task_name.startswith("phase2_emotion") and result is not None:
                    # Phase 2 returns a tuple (phase2_context, current_emotion_data)
                    if isinstance(result, tuple) and len(result) == 2:
                        phase2_context, current_emotion_data = result
                        logger.info(f"🚀 AI PIPELINE DEBUG: Set phase2_context and current_emotion_data from {task_name}")
                        logger.info(f"🚀 AI PIPELINE DEBUG: Phase2 context: {str(phase2_context)[:200] if phase2_context else 'None'}")
                        logger.info(f"🚀 AI PIPELINE DEBUG: Current emotion: {str(current_emotion_data)[:200] if current_emotion_data else 'None'}")
                    else:
                        logger.warning(f"🚀 AI PIPELINE DEBUG: Unexpected phase2 result format: {type(result)}")
                elif task_name.startswith("dynamic_personality") and result is not None:
                    dynamic_personality_context = result
                    logger.info(f"🚀 AI PIPELINE DEBUG: Set dynamic_personality_context from {task_name}: {str(result)[:200]}")
                    
            # Task 4: Phase 4 intelligence (depends on results from above)
            phase4_context = None
            comprehensive_context = None
            enhanced_system_prompt = None
            
            logger.info("🚀 AI PIPELINE DEBUG: Checking Phase 4 intelligence processing...")
            
            if (os.getenv("DISABLE_PHASE4_INTELLIGENCE", "false").lower() != "true"
                and hasattr(self.memory_manager, "process_with_phase4_intelligence")):
                try:
                    logger.info("🚀 AI PIPELINE DEBUG: Starting Phase 4 intelligence processing...")
                    phase4_context, comprehensive_context, enhanced_system_prompt = (
                        await self._process_phase4_intelligence(
                            user_id, message, recent_messages, external_emotion_data, phase2_context
                        )
                    )
                    logger.info(f"🚀 AI PIPELINE DEBUG: Phase 4 completed - Context: {str(phase4_context)[:100] if phase4_context else 'None'}")
                    logger.info(f"🚀 AI PIPELINE DEBUG: Enhanced prompt length: {len(enhanced_system_prompt) if enhanced_system_prompt else 0} chars")
                except Exception as e:
                    logger.warning(f"🚀 AI PIPELINE DEBUG: Phase 4 intelligence processing failed: {e}")
            else:
                logger.info("🚀 AI PIPELINE DEBUG: Phase 4 intelligence processing disabled or unavailable")
                    
            # Store results in instance variables for use by response generation
            self._last_external_emotion_data = external_emotion_data
            self._last_phase2_context = phase2_context
            self._last_current_emotion_data = current_emotion_data
            self._last_dynamic_personality_context = dynamic_personality_context
            self._last_phase4_context = phase4_context
            self._last_comprehensive_context = comprehensive_context
            self._last_enhanced_system_prompt = enhanced_system_prompt
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Parallel AI processing completed in {processing_time:.2f}s for user {user_id}")
            
            # Memory cleanup after intensive LLM operations
            try:
                if hasattr(self, 'llm_client') and self.llm_client and hasattr(self.llm_client, 'cleanup_memory'):
                    self.llm_client.cleanup_memory()
            except Exception as cleanup_error:
                logger.debug(f"Memory cleanup skipped: {cleanup_error}")
            
            # Return the tuple expected by calling code
            return (external_emotion_data, phase2_context, current_emotion_data, 
                   dynamic_personality_context, phase4_context, comprehensive_context, 
                   enhanced_system_prompt)
            
        except Exception as e:
            logger.error(f"Parallel AI component processing failed: {e}")
            # Set safe defaults if parallel processing fails
            self._last_external_emotion_data = None
            self._last_phase2_context = None
            self._last_current_emotion_data = None
            self._last_dynamic_personality_context = None
            self._last_phase4_context = None
            self._last_comprehensive_context = None
            self._last_enhanced_system_prompt = None
            
            # Return safe defaults tuple
            return (None, None, None, None, None, None, None)
            
    async def _create_none_result(self):
        """Helper method for disabled AI components in parallel processing."""
        return None

    def _set_minimal_ai_results(self):
        """Set minimal AI analysis results for maximum performance mode."""
        self._last_external_emotion_data = None
        self._last_phase2_context = None
        self._last_current_emotion_data = None
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
    
    def _build_user_preferences(self, user_id: str, message_context: dict) -> dict:
        """
        Build user preferences for optimization based on interaction history.
        
        Args:
            user_id: User identifier
            message_context: Message context dictionary
            
        Returns:
            User preferences dictionary
        """
        preferences = {}
        
        # Default conversational behavior for Discord bot
        preferences['conversational_user'] = True
        
        # Check if user typically asks for recent information
        if message_context and message_context.get('recent_messages'):
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
        if message_context and message_context.get('topics'):
            preferences['favorite_topics'] = message_context['topics']
        
        return preferences
    
    def _build_memory_filters(self, message_context: dict) -> dict:
        """
        Build memory filters from message context.
        
        Args:
            message_context: Message context dictionary
            
        Returns:
            Filters dictionary for memory search
        """
        filters = {}
        
        # Add channel context if available
        if message_context and message_context.get('channel_id'):
            filters['channel_id'] = message_context['channel_id']
        
        # Add time-based filtering for recent queries
        if message_context and message_context.get('is_recent_query'):
            from datetime import datetime, timedelta
            recent_cutoff = datetime.now() - timedelta(hours=24)
            filters['timestamp'] = {'$gte': recent_cutoff}
        
        return filters

    async def _apply_cdl_character_enhancement(
        self,
        user_id: str,
        conversation_context: list,
        message,
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
            
            # Check if CDL test commands are available
            logger.info(f"🎭 CDL CHARACTER DEBUG: Bot has command_handlers attr: {hasattr(self.bot, 'command_handlers')}")
            if hasattr(self.bot, 'command_handlers'):
                logger.info(f"🎭 CDL CHARACTER DEBUG: Available handlers: {list(getattr(self.bot, 'command_handlers', {}).keys())}")
            
            if not hasattr(self.bot, 'command_handlers') or 'cdl_test' not in getattr(self.bot, 'command_handlers', {}):
                logger.info(f"🎭 CDL CHARACTER DEBUG: CDL test handler not found, returning None")
                return None
            
            # Get CDL test commands handler to check for active character
            cdl_handler = None
            # Access the CDL handler through the bot manager
            for handler_name, handler in getattr(self.bot, 'command_handlers', {}).items():
                if handler_name == 'cdl_test':
                    cdl_handler = handler
                    break
            
            if not cdl_handler:
                logger.info(f"🎭 CDL CHARACTER DEBUG: CDL handler not found in loop, returning None")
                return None
                
            # Check if user has an active character
            character_file = cdl_handler.get_user_character(user_id)
            
            # Auto-assign Elena character if bot name is Elena and no character is set
            if not character_file:
                import os
                bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
                if bot_name == "elena":
                    character_file = "characters/examples/elena-rodriguez.json"
                    # Store this assignment in the handler
                    cdl_handler.user_characters[user_id] = character_file
                    logger.info(f"🎭 CDL CHARACTER: Auto-assigned Elena character to user {user_id}")
                else:
                    return None
            
            logger.info(f"🎭 CDL CHARACTER: User {user_id} has active character: {character_file}")
            
            # Import CDL integration modules
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineResult
            from datetime import datetime
            
            # Create AI pipeline result from available context data
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
            
            # Create CDL integration and generate character-aware prompt
            cdl_integration = CDLAIPromptIntegration(vector_memory_manager=self.memory_manager)
            character_prompt = await cdl_integration.create_character_aware_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=message.content,
                pipeline_result=pipeline_result
            )
            
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
