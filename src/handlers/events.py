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
from src.utils.helpers import (
    add_debug_info_to_response,
    extract_text_for_memory_storage,
    fix_message_alternation,
    generate_conversation_summary,
    get_contextualized_system_prompt,
    get_current_time_context,
    get_message_content,
    message_equals_bot_user,
    process_message_with_images,
    store_discord_server_info,
    store_discord_user_info,
)

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

def _minimal_context_mode_enabled() -> bool:
    """Return True if MINIMAL_CONTEXT_MODE is enabled via environment.

    When enabled we intentionally suppress enrichment layers (phase2 emotion, dynamic personality,
    phase4 intelligence, external emotion API, and memory narrative) to obtain a clean baseline
    model behavior. Only the consolidated core system prompt + last few raw user/assistant turns
    are sent (attachments still guarded). This helps diagnose style contamination originating from
    higher-level adaptive systems vs base model tendencies.
    """
    return os.getenv("MINIMAL_CONTEXT_MODE", "false").lower() in ("1", "true", "yes", "on")


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
        self.personality_profiler = getattr(bot_core, "personality_profiler", None)
        self.dynamic_personality_profiler = getattr(bot_core, "dynamic_personality_profiler", None)
        self.graph_personality_manager = getattr(bot_core, "graph_personality_manager", None)
        self.phase2_integration = getattr(bot_core, "phase2_integration", None)
        self.external_emotion_ai = getattr(bot_core, "external_emotion_ai", None)
        # Redis profile/memory cache (if enabled)
        self.profile_memory_cache = getattr(bot_core, "profile_memory_cache", None)

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
                logger.info("🚀 Initializing Production Optimization System...")
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
        logger.info("🚀 Bot initialization complete - ready to chat!")

        # Emit diagnostic warning if minimal context mode is active
        if _minimal_context_mode_enabled():
            logger.warning("⚠️ MINIMAL_CONTEXT_MODE active: suppressing emotion, personality, phase4, and memory enrichment layers for baseline output isolation.")

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
                if hasattr(self.conversation_cache, "add_message"):
                    if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                        await self.conversation_cache.add_message(str(message.channel.id), message)
                    else:
                        self.conversation_cache.add_message(str(message.channel.id), message)
            return

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
                    relevant_memories = self.memory_manager.retrieve_context_aware_memories(
                        user_id, message.content, message_context, limit=20
                    )
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
                    emotion_context = self.memory_manager.get_emotion_context(user_id)
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

        # Get recent conversation history
        recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)

        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, enhanced_system_prompt
        )

        external_emotion_data = None
        phase2_context = None
        current_emotion_data = None
        dynamic_personality_context = None
        phase4_context = None
        comprehensive_context = None
        enhanced_system_prompt = None

        # PERFORMANCE OPTIMIZATION: Process AI components in parallel instead of sequentially
        if not _minimal_context_mode_enabled():
            (external_emotion_data, phase2_context, current_emotion_data, 
             dynamic_personality_context, phase4_context, comprehensive_context, 
             enhanced_system_prompt) = await self._process_ai_components_parallel(
                user_id, message.content, message, recent_messages, conversation_context
            )
        else:
            logger.debug("[MINIMAL_CONTEXT_MODE] Skipping emotion/personality/phase4 enrichment for DM message.")

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
                    relevant_memories = self.memory_manager.retrieve_context_aware_memories(
                        user_id, content, message_context, limit=20
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
                    emotion_context = self.memory_manager.get_emotion_context(user_id)
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

        # Get recent conversation history (guild-specific)
        recent_messages = await self._get_recent_messages(reply_channel, user_id, message.id)

        # Build conversation context
        conversation_context = await self._build_conversation_context(
            message, relevant_memories, emotion_context, recent_messages, None, content
        )
        logger.info(f"[CONV-CTX] Built conversation context for message_id={message.id} user_id={user_id} context_type={type(conversation_context)} context_preview={str(conversation_context)[:120]}")

        external_emotion_data = None
        phase2_context = None
        current_emotion_data = None
        dynamic_personality_context = None
        phase4_context = None
        comprehensive_context = None
        enhanced_system_prompt = None

        # PERFORMANCE OPTIMIZATION: Process AI components in parallel instead of sequentially
        if not _minimal_context_mode_enabled():
            (external_emotion_data, phase2_context, current_emotion_data, 
             dynamic_personality_context, phase4_context, comprehensive_context, 
             enhanced_system_prompt) = await self._process_ai_components_parallel(
                user_id, content, message, recent_messages, conversation_context
            )
        else:
            logger.debug("[MINIMAL_CONTEXT_MODE] Skipping emotion/personality/phase4 enrichment for guild mention.")

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

    async def _get_recent_messages(self, channel, user_id, exclude_message_id):
        """Get recent conversation messages for context."""
        if self.conversation_cache:
            # Use cache with user-specific filtering
            recent_messages = await self.conversation_cache.get_user_conversation_context(
                channel, user_id=int(user_id), limit=15, exclude_message_id=exclude_message_id
            )

            # Supplement with ChromaDB if insufficient
            if len(recent_messages) < 8:
                logger.debug(
                    f"Supplementing {len(recent_messages)} cached messages with ChromaDB history for user {user_id}"
                )
                try:
                    chromadb_memories = self.safe_memory_manager.retrieve_relevant_memories(
                        user_id, query="conversation history recent messages", limit=15
                    )

                    # CRITICAL DEBUG: Log what ChromaDB is returning
                    logger.error(f"[CHROMADB-DEBUG] Retrieved {len(chromadb_memories)} memories for user {user_id}")
                    for i, memory in enumerate(chromadb_memories):
                        metadata = memory.get("metadata", {})
                        logger.error(f"[CHROMADB-DEBUG] Memory {i}: user_msg='{metadata.get('user_message', 'N/A')[:100]}...' bot_response='{metadata.get('bot_response', 'N/A')[:100]}...'")

                    # Process ChromaDB memories into message format
                    conversation_count = 0
                    for memory in reversed(chromadb_memories):
                        metadata = memory.get("metadata", {})

                        if "user_message" in metadata and "bot_response" in metadata:
                            user_content = metadata["user_message"][:500]
                            bot_content = metadata["bot_response"][:500]
                            
                            # CRITICAL DEBUG: Log what's being added to conversation context
                            logger.error(f"[CONTEXT-DEBUG] Adding ChromaDB conversation:")
                            logger.error(f"[CONTEXT-DEBUG] User: '{user_content}'")
                            logger.error(f"[CONTEXT-DEBUG] Bot: '{bot_content}'")
                            
                            # Add user message
                            recent_messages.append(
                                {
                                    "content": user_content,
                                    "author_id": user_id,
                                    "author_name": metadata.get("user_name", "User"),
                                    "timestamp": metadata.get("timestamp", ""),
                                    "bot": False,
                                    "from_chromadb": True,
                                }
                            )
                            # Add bot response
                            recent_messages.append(
                                {
                                    "content": bot_content,
                                    "author_id": str(self.bot.user.id) if self.bot.user else "bot",
                                    "author_name": (
                                        self.bot.user.display_name if self.bot.user else "Bot"
                                    ),
                                    "timestamp": metadata.get("timestamp", ""),
                                    "bot": True,
                                    "from_chromadb": True,
                                }
                            )

                            conversation_count += 1
                            if conversation_count >= 5:
                                break

                    if conversation_count > 0:
                        recent_messages = recent_messages[-20:]
                        logger.debug(
                            f"Enhanced context with {conversation_count} ChromaDB conversations: now have {len(recent_messages)} messages"
                        )

                except Exception as e:
                    logger.warning(f"Could not supplement with ChromaDB conversations: {e}")

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
            # Use template system with available context data
            try:
                # Build basic template context from available data
                user_id = str(message.author.id)

                # Create basic personality metadata from message context
                personality_metadata = {
                    "platform": "discord",
                    "context_type": "guild" if message.guild else "dm",
                    "user_id": user_id,
                }

                # Use template system for contextualized prompt
                system_prompt_content = get_contextualized_system_prompt(
                    personality_metadata=personality_metadata, user_id=user_id
                )
                logger.debug("Using contextualized system prompt from template system")

            except Exception as e:
                logger.warning(f"Could not use template system: {e}")
                # Fallback to basic system prompt
                from src.core.config import get_system_prompt

                system_prompt_content = get_system_prompt()
                logger.debug("Falling back to basic system prompt")

        # STRICT immersive mode OR minimal context mode: consolidate system messages into a single narrative instruction
        if _strict_mode_enabled() or _minimal_context_mode_enabled():
            # Build compact memory narrative
            memory_fragments = []
            if relevant_memories and not _minimal_context_mode_enabled():
                global_facts = [m for m in relevant_memories if m["metadata"].get("is_global", False)]
                user_memories = [m for m in relevant_memories if not m["metadata"].get("is_global", False)]
                if global_facts:
                    gf_text = "; ".join(
                        memory["metadata"].get("fact", "")[:160] for memory in global_facts
                        if memory["metadata"].get("type") == "global_fact"
                    )
                    if gf_text:
                        memory_fragments.append(f"Shared truths: {gf_text}")
                if user_memories and not _minimal_context_mode_enabled():
                    um_text_parts = []
                    for memory in user_memories[:6]:  # limit
                        md = memory["metadata"]
                        if md.get("user_message"):
                            um_text_parts.append(md.get("user_message")[:120])
                        elif md.get("type") == "user_fact":
                            um_text_parts.append(md.get("fact", "")[:120])
                    if um_text_parts:
                        memory_fragments.append("You recall: " + "; ".join(um_text_parts))
            memory_narrative = " " .join(memory_fragments)

            # Conversation summary (compressed)
            conversation_summary = None
            if not _minimal_context_mode_enabled():
                conversation_summary = generate_conversation_summary(
                    recent_messages, str(message.author.id)
                )
                if conversation_summary and len(conversation_summary) > 600:
                    conversation_summary = conversation_summary[:600] + "..."

            # Emotion context inline
            emotion_inline = ""
            if emotion_context and not _minimal_context_mode_enabled():
                emotion_inline = f" Emotive context: {emotion_context}."

            # Attachment guard if needed
            attachment_guard = ""
            if getattr(message, "attachments", None) and len(message.attachments) > 0:
                attachment_guard = (
                    " Image policy: respond only in-character (Dream), never output analysis sections, headings, scores, tables, coaching offers, or 'Would you like me to' prompts."
                )

            guidance_clause = (
                " Invariant style: one immersive, poetic reply as Dream. No meta-analysis, no breakdowns, no bullet summaries, no section headings."
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
        else:
            # Fallback to original multi-system approach if strict mode disabled
            conversation_context.append({"role": "system", "content": system_prompt_content})
            conversation_context.append({"role": "system", "content": f"Current time: {time_context}"})
            if emotion_context:
                conversation_context.append(
                    {"role": "system", "content": f"User relationship and emotional context: {emotion_context}"}
                )
            if relevant_memories:
                memory_context = "Previous conversation context:\n"
                global_facts = [m for m in relevant_memories if m["metadata"].get("is_global", False)]
                user_memories = [m for m in relevant_memories if not m["metadata"].get("is_global", False)]
                if global_facts:
                    memory_context += "\nGlobal Facts:\n"
                    for memory in global_facts:
                        if memory["metadata"].get("type") == "global_fact":
                            memory_context += f"- {memory['metadata']['fact']}\n"
                if user_memories:
                    memory_context += "\nUser-specific information:\n"
                    for memory in user_memories:
                        md = memory["metadata"]
                        if md.get("user_message"):
                            memory_context += f"- User said: {md.get('user_message')[:160]}\n"
                        elif md.get("type") == "user_fact":
                            memory_context += f"- Fact: {md.get('fact','')}\n"
                conversation_context.append({"role": "system", "content": memory_context})
            conversation_summary = generate_conversation_summary(
                recent_messages, str(message.author.id)
            )
            if conversation_summary:
                conversation_context.append(
                    {"role": "system", "content": f"Recent conversation summary: {conversation_summary}"}
                )

        # Add recent messages with proper alternation
        user_assistant_messages = []
        filtered_messages = list(reversed(recent_messages[1:]))  # Skip current message

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
            if msg_content.startswith("!"):
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
        if _minimal_context_mode_enabled():
            # Keep only last 6 alternating turns for isolation
            fixed_history = fixed_history[-12:]
        
        conversation_context.extend(fixed_history)

        # If the triggering message contains attachments (e.g. images), add an explicit anti-analysis guard
        # to prevent the model from responding with coaching-style analytical breakdowns (observed regression
        # when images are included). This instruction is additive and limited in scope.
        try:
            if getattr(message, "attachments", None):
                if len(message.attachments) > 0:
                    conversation_context.append(
                        {
                            "role": "system",
                            "content": (
                                "IMAGE RESPONSE POLICY: The user has shared one or more images. "
                                "Respond ONLY with an in-character, natural reply consistent with the Dream persona. "
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

        return conversation_context

    async def _analyze_external_emotion(self, content, user_id, conversation_context):
        """Analyze emotion using external API."""
        try:
            logger.debug("Running External API Emotion AI analysis (full capabilities)...")

            conversation_history = [
                msg["content"] for msg in conversation_context[-10:] if msg["role"] == "user"
            ]

            if (
                not hasattr(self.external_emotion_ai, "session")
                or self.external_emotion_ai.session is None
            ):
                await self.external_emotion_ai.initialize()

            external_emotion_data = await self.external_emotion_ai.analyze_emotion_cloud(
                text=content, user_id=user_id, conversation_history=conversation_history
            )

            logger.debug(
                f"External emotion analysis completed: {external_emotion_data.get('primary_emotion', 'unknown')} "
                f"(confidence: {external_emotion_data.get('confidence', 0):.2f})"
            )

            if external_emotion_data.get("analysis_time_ms"):
                logger.debug(
                    f"Emotion analysis took {external_emotion_data['analysis_time_ms']:.1f}ms "
                    f"({external_emotion_data.get('api_calls_made', 0)} API calls)"
                )

            return external_emotion_data

        except Exception as e:
            logger.error(f"External API Emotion AI analysis failed: {e}")
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
            logger.debug("Running Phase 4: Human-Like Conversation Intelligence...")

            discord_context = {
                "channel_id": str(message.channel.id),
                "guild_id": str(message.guild.id) if message.guild else None,
                "channel_type": "dm" if message.guild is None else "guild",
                "user_display_name": message.author.display_name,
                "external_emotion_data": external_emotion_data,
                "phase2_results": phase2_context,
            }

            phase4_context = await self.memory_manager.process_with_phase4_intelligence(
                user_id=user_id,
                message=message.content,
                conversation_context=recent_messages,
                discord_context=discord_context,
            )

            # Try human-like memory processing if available
            human_like_context = None
            conversation_analysis = None
            if hasattr(self.memory_manager, 'human_like_system'):
                try:
                    logger.debug("Using Human-Like Memory System for enhanced processing...")
                    
                    # Prepare conversation history
                    conversation_history = [msg['content'] for msg in recent_messages[-5:] if 'content' in msg]
                    
                    # Build relationship context
                    relationship_context = {
                        "interaction_history": len(recent_messages),
                        "emotional_data": external_emotion_data,
                        "phase2_context": phase2_context,
                        "discord_context": discord_context
                    }
                    
                    # Analyze conversation for human-like response guidance
                    from src.utils.human_like_conversation_engine import analyze_conversation_for_human_response
                    
                    conversation_analysis = analyze_conversation_for_human_response(
                        user_id=user_id,
                        message=message.content,
                        conversation_history=[{"content": msg} for msg in conversation_history],
                        emotional_context=external_emotion_data,
                        relationship_context=relationship_context
                    )
                    
                    # Use human-like memory search
                    human_like_result = await self.memory_manager.human_like_system.search_like_human_friend(
                        user_id=user_id,
                        message=message.content,
                        conversation_history=conversation_history,
                        relationship_context=relationship_context,
                        limit=20
                    )
                    
                    human_like_context = human_like_result
                    logger.debug(f"Human-like processing: {human_like_result['human_context']['emotional_understanding']} | "
                               f"Purpose: {human_like_result['human_context']['conversation_purpose']} | "
                               f"Mode: {conversation_analysis['mode']} | "
                               f"Personality: {conversation_analysis['personality_type']}")
                    
                except Exception as human_error:
                    logger.warning(f"Human-like memory processing failed: {human_error}")
                    human_like_context = None
                    conversation_analysis = None

            comprehensive_context = None
            enhanced_system_prompt = None

            if hasattr(self.memory_manager, "get_phase4_response_context"):
                comprehensive_context = self.memory_manager.get_phase4_response_context(
                    phase4_context
                )

                # Instead of creating an enhanced prompt, prepare template context
                # that can be used by the template system in fallback scenarios
                template_context = {
                    "phase4_context": phase4_context,
                    "comprehensive_context": comprehensive_context,
                    "interaction_type": getattr(phase4_context, "interaction_type", None),
                    "conversation_mode": getattr(phase4_context, "conversation_mode", None),
                }

                # Still create enhanced prompt for backward compatibility
                # but prioritize template system in fallback scenarios
                from src.intelligence.phase4_integration import create_phase4_enhanced_system_prompt

                enhanced_system_prompt = get_contextualized_system_prompt(
                    personality_metadata=template_context,
                    user_id=user_id,
                    phase4_context=phase4_context,
                    comprehensive_context=comprehensive_context,
                )

                # If template system fails, fallback to the old enhanced prompt method
                if not enhanced_system_prompt or enhanced_system_prompt == "":
                    logger.warning("Template system failed, using legacy Phase 4 enhanced prompt")
                    from src.core.config import get_system_prompt

                    enhanced_system_prompt = create_phase4_enhanced_system_prompt(
                        phase4_context=phase4_context,
                        base_system_prompt=get_system_prompt(),
                        comprehensive_context=comprehensive_context,
                    )

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

                logger.debug(
                    f"Phase 4 analysis completed: {conversation_mode_str} mode, "
                    f"{phase4_context.interaction_type.value} interaction, "
                    f"{len(phases_executed)} phases executed"
                )

            # Merge human-like context into comprehensive context if available
            if human_like_context and comprehensive_context:
                comprehensive_context["human_like_context"] = human_like_context["human_context"]
                comprehensive_context["human_like_memories"] = human_like_context["memories"]
                comprehensive_context["human_like_performance"] = human_like_context["search_performance"]
                
                # Add conversation analysis for enhanced response guidance
                if conversation_analysis:
                    comprehensive_context["conversation_analysis"] = conversation_analysis
                    comprehensive_context["response_guidance"] = conversation_analysis["response_guidance"]
                    comprehensive_context["conversation_mode"] = conversation_analysis["mode"]
                    comprehensive_context["interaction_type"] = conversation_analysis["interaction_type"]
                    comprehensive_context["personality_type"] = conversation_analysis["personality_type"]
                    comprehensive_context["relationship_level"] = conversation_analysis["relationship_level"]
                
                logger.debug("Enhanced comprehensive context with human-like intelligence and conversation analysis")

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
            logger.debug("Started typing indicator - simulating thinking and typing process")
            try:
                logger.debug("Processing message through Universal Chat Orchestrator...")

                # Use Universal Chat Orchestrator if available
                if self.chat_orchestrator:
                    logger.debug(
                        "Using Universal Chat Orchestrator for proper layered architecture"
                    )

                    # Convert Discord message to universal format
                    if (
                        hasattr(self.chat_orchestrator, "adapters")
                        and ChatPlatform.DISCORD in self.chat_orchestrator.adapters
                    ):
                        discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                        universal_message = discord_adapter.discord_message_to_universal_message(
                            message
                        )

                        # Get or create conversation
                        conversation = await self.chat_orchestrator.get_or_create_conversation(
                            universal_message
                        )

                        # Generate AI response through orchestrator
                        ai_response = await self.chat_orchestrator.generate_ai_response(
                            universal_message, conversation
                        )

                        response = ai_response.content
                        
                        logger.debug(f"Universal Chat response: {len(response)} characters")
                        logger.debug(
                            f"Model used: {ai_response.model_used}, Tokens: {ai_response.tokens_used}"
                        )

                    else:
                        logger.warning(
                            "Discord adapter not found in orchestrator, falling back to direct LLM"
                        )
                        response = await self._fallback_direct_llm_response(
                            conversation_context,
                            user_id,
                            current_emotion_data,
                            external_emotion_data,
                            phase2_context,
                            phase4_context,
                            comprehensive_context,
                            dynamic_personality_context,
                        )

                else:
                    logger.warning(
                        "Universal Chat Orchestrator not available, falling back to direct LLM"
                    )
                    response = await self._fallback_direct_llm_response(
                        conversation_context,
                        user_id,
                        current_emotion_data,
                        external_emotion_data,
                        phase2_context,
                        phase4_context,
                        comprehensive_context,
                        dynamic_personality_context,
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
                        rewrite_context = [
                            {"role": "system", "content": (
                                "You are a style refiner. Rewrite the assistant content into a SINGLE immersive in-character reply as Dream of the Endless. Remove all analysis sections, headings, breakdowns, score talk, coaching offers, or meta commentary. Keep poetic tone, <=120 words."
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

                # Store conversation in memory
                await self._store_conversation_memory(
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

                # Add debug information if needed
                response_with_debug = add_debug_info_to_response(
                    response, user_id, self.memory_manager, str(message.id)
                )

                # Send response (chunked if too long)
                await self._send_response_chunks(reply_channel, response_with_debug)

                # Send voice response if applicable
                await self._send_voice_response(message, response)

                # Add user message to cache after successful processing
                if self.conversation_cache:
                    if hasattr(self.conversation_cache, "add_message"):
                        if asyncio.iscoroutinefunction(self.conversation_cache.add_message):
                            await self.conversation_cache.add_message(
                                str(reply_channel.id), message
                            )
                        else:
                            self.conversation_cache.add_message(str(reply_channel.id), message)
                    logger.debug(
                        "Added user message to conversation cache after successful processing"
                    )

            except LLMConnectionError:
                logger.warning("LLM connection error")
                await reply_channel.send(
                    "*The pathways between realms have grown dim...* I cannot reach the source of wisdom at this moment. Pray, try again shortly."
                )
            except LLMTimeoutError:
                logger.warning("LLM timeout error")
                await reply_channel.send(
                    "*Time moves strangely in the realm of dreams...* Thy words have taken too long to reach me. Speak again, if thou wilt."
                )
            except LLMRateLimitError:
                logger.warning("LLM rate limit error")
                await reply_channel.send(
                    "*The flow of dreams grows heavy with too many seekers...* Grant me a moment's respite, then we may speak once more."
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

    async def _fallback_direct_llm_response(
        self,
        conversation_context,
        user_id=None,
        current_emotion_data=None,
        external_emotion_data=None,
        phase2_context=None,
        phase4_context=None,
        comprehensive_context=None,
        dynamic_personality_context=None,
    ):
        """Fallback to direct LLM client when Universal Chat is unavailable, with full template support."""
        if self.llm_client is None:
            logger.error("LLM client is not initialized")
            return "The threads of consciousness are not yet woven. My deeper mind remains unreachable for now."

        # Check LLM connection
        if not await self.llm_client.check_connection_async():
            logger.warning("LLM connection unavailable when trying to respond")
            return "⚠️ I can't connect to the LLM server right now. Make sure your LLM provider is running."

        logger.debug("Sending request to LLM (fallback with template support)...")
        logger.debug(f"Conversation context: {len(conversation_context)} messages")

        try:
            # Build template context from available AI analysis
            template_context = {}

            # Collect all available context for template variables
            if current_emotion_data:
                template_context["emotional_intelligence"] = current_emotion_data
            if external_emotion_data:
                template_context["external_emotion_data"] = external_emotion_data
            if phase2_context:
                template_context["phase2_context"] = phase2_context
            if phase4_context:
                template_context["phase4_context"] = phase4_context
            if comprehensive_context:
                template_context["comprehensive_context"] = comprehensive_context
            if dynamic_personality_context:
                template_context["personality_context"] = dynamic_personality_context

            # Replace system message with contextualized version if we have template context
            if template_context and user_id:
                try:
                    # Get contextualized system prompt
                    contextualized_system_prompt = get_contextualized_system_prompt(
                        personality_metadata=dynamic_personality_context,
                        emotional_intelligence_results=current_emotion_data,
                        user_id=user_id,
                        phase4_context=phase4_context,
                        comprehensive_context=comprehensive_context,
                    )

                    # Replace system message in conversation context
                    updated_context = []
                    for msg in conversation_context:
                        if msg.get("role") == "system":
                            updated_context.append(
                                {"role": "system", "content": contextualized_system_prompt}
                            )
                            logger.debug(
                                "Replaced system prompt with contextualized version in fallback"
                            )
                        else:
                            updated_context.append(msg)

                    conversation_context = updated_context

                except Exception as e:
                    logger.warning(f"Could not contextualize system prompt in fallback: {e}")
                    logger.debug("Continuing with original system prompt")

        except Exception as e:
            logger.warning(f"Error building template context in fallback: {e}")

        # Get response from LLM directly
        response = await self.llm_client.generate_chat_completion_safe(conversation_context)
        logger.debug(f"Received LLM response (fallback): {len(response)} characters")

        return response

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

            # Store with thread-safe operations
            storage_success = await self.safe_memory_manager.store_conversation_safe(
                user_id,
                storage_content,
                response,
                channel_id=str(message.channel.id),
                pre_analyzed_emotion_data=emotion_metadata,
                metadata=storage_metadata,
            )

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
                    if recent_context and hasattr(recent_context, "conversations"):
                        for conv in recent_context.conversations[-9:]:
                            if hasattr(conv, "user_message") and conv.user_message:
                                recent_messages.append(conv.user_message)
                except Exception as e:
                    logger.debug(
                        f"Could not retrieve recent messages for personality analysis: {e}"
                    )

                if len(recent_messages) >= 1:
                    logger.debug(
                        f"Analyzing personality with {len(recent_messages)} messages for user {user_id}"
                    )

                    if self.graph_personality_manager:
                        # Use graph-enhanced personality manager
                        personality_summary = (
                            await self.graph_personality_manager.analyze_and_store_personality(
                                user_id,
                                recent_messages,
                                {
                                    "channel_id": str(message.channel.id),
                                    "guild_id": str(message.guild.id) if message.guild else None,
                                    "timestamp": datetime.now(UTC).isoformat(),
                                    "context": "discord_conversation",
                                },
                            )
                        )
                        if personality_summary:
                            personality_metadata = {
                                "communication_style": personality_summary.get(
                                    "communication_style", {}
                                ).get("primary", "unknown"),
                                "confidence_level": personality_summary.get(
                                    "communication_style", {}
                                ).get("confidence_level", "unknown"),
                                "decision_style": personality_summary.get(
                                    "behavioral_patterns", {}
                                ).get("decision_style", "unknown"),
                                "analysis_confidence": personality_summary.get(
                                    "analysis_meta", {}
                                ).get("confidence", 0.0),
                            }
                            logger.debug(f"Personality analysis: {personality_metadata}")
                    else:
                        # Use standalone personality profiler
                        metrics = self.personality_profiler.analyze_personality(
                            recent_messages, user_id
                        )
                        summary = self.personality_profiler.get_personality_summary(metrics)
                        personality_metadata = {
                            "communication_style": summary.get("communication_style", {}).get(
                                "primary", "unknown"
                            ),
                            "confidence_level": summary.get("communication_style", {}).get(
                                "confidence_level", "unknown"
                            ),
                            "decision_style": summary.get("behavioral_patterns", {}).get(
                                "decision_style", "unknown"
                            ),
                            "analysis_confidence": summary.get("analysis_meta", {}).get(
                                "confidence", 0.0
                            ),
                        }
                        logger.debug(f"Standalone personality analysis: {personality_metadata}")

            except Exception as e:
                logger.warning(f"Personality analysis failed for user {user_id}: {e}")
                personality_metadata = None

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
                if msg.get("bot", False):
                    bot_response = msg.get("content", "")
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
        """Send response in chunks if it's too long."""
        if len(response) > 2000:
            chunks = [response[i : i + 1900] for i in range(0, len(response), 1900)]
            logger.info(
                f"Response too long ({len(response)} chars), splitting into {len(chunks)} chunks"
            )
            for i, chunk in enumerate(chunks):
                await channel.send(
                    f"{chunk}" + (f"\n*(continued {i+1}/{len(chunks)})*" if len(chunks) > 1 else "")
                )
                logger.debug(f"Sent chunk {i+1}/{len(chunks)}")
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
        
        This replaces the sequential processing of:
        1. External emotion analysis 
        2. Phase 2 emotion analysis
        3. Dynamic personality analysis  
        4. Phase 4 intelligence processing
        
        Expected performance improvement: 3-5x faster response times under load
        """
        import asyncio
        
        logger.debug(f"Starting parallel AI component processing for user {user_id}")
        start_time = time.time()
        
        # Prepare task list for parallel execution
        tasks = []
        task_names = []
        
        # Task 1: External emotion analysis (if enabled and available)
        if (os.getenv("DISABLE_EXTERNAL_EMOTION_API", "true").lower() != "true" 
            and self.external_emotion_ai):
            tasks.append(self._analyze_external_emotion(content, user_id, conversation_context))
            task_names.append("external_emotion")
        else:
            tasks.append(asyncio.create_task(self._create_none_result()))
            task_names.append("external_emotion_disabled")
            
        # Task 2: Phase 2 emotional intelligence (primary emotion source)
        if (os.getenv("DISABLE_PHASE2_EMOTION", "false").lower() != "true" 
            and self.phase2_integration):
            context_type = "guild_message" if hasattr(message, 'guild') and message.guild else "dm"
            tasks.append(self._analyze_phase2_emotion(user_id, content, message, context_type))
            task_names.append("phase2_emotion")
        else:
            tasks.append(asyncio.create_task(self._create_none_result()))
            task_names.append("phase2_emotion_disabled")
            
        # Task 3: Dynamic personality analysis
        if (os.getenv("DISABLE_PERSONALITY_PROFILING", "false").lower() != "true"
            and self.dynamic_personality_profiler):
            tasks.append(self._analyze_dynamic_personality(user_id, content, message, recent_messages))
            task_names.append("dynamic_personality")
        else:
            tasks.append(asyncio.create_task(self._create_none_result()))
            task_names.append("dynamic_personality_disabled")
            
        # Execute all tasks in parallel
        try:
            logger.debug(f"Executing {len(tasks)} AI analysis tasks in parallel")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            external_emotion_data = None
            phase2_context = None
            current_emotion_data = None
            dynamic_personality_context = None
            
            for i, result in enumerate(results):
                task_name = task_names[i]
                
                if isinstance(result, Exception):
                    logger.warning(f"Parallel task {task_name} failed: {result}")
                    continue
                    
                if task_name.startswith("external_emotion") and result is not None:
                    external_emotion_data = result
                elif task_name.startswith("phase2_emotion") and result is not None:
                    # Phase 2 returns a tuple (phase2_context, current_emotion_data)
                    if isinstance(result, tuple) and len(result) == 2:
                        phase2_context, current_emotion_data = result
                    else:
                        logger.warning(f"Unexpected phase2 result format: {type(result)}")
                elif task_name.startswith("dynamic_personality") and result is not None:
                    dynamic_personality_context = result
                    
            # Task 4: Phase 4 intelligence (depends on results from above)
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
            else:
                logger.debug("Phase 4 intelligence processing disabled for performance")
                    
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
