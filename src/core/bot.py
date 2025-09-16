#!/usr/bin/env python3
"""
Discord Bot Core Module
Handles bot initialization, setup, and configuration.
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

# Core imports
from env_manager import load_environment
from src.llm.llm_client import LLMClient
from src.memory.backup_manager import BackupManager
from src.memory.conversation_cache import HybridConversationCache
from src.memory.memory_manager import UserMemoryManager
from src.utils.heartbeat_monitor import HeartbeatMonitor
from src.utils.image_processor import ImageProcessor
from src.utils.memory_integration_patch import apply_memory_enhancement_patch

# GRAPH DATABASE INTEGRATION: Import enhanced memory components
try:
    from src.memory.integrated_memory_manager import IntegratedMemoryManager
    from src.utils.graph_integrated_emotion_manager import GraphIntegratedEmotionManager

    GRAPH_MEMORY_AVAILABLE = True
except ImportError:
    GRAPH_MEMORY_AVAILABLE = False
    IntegratedMemoryManager = None
    GraphIntegratedEmotionManager = None

from src.llm.concurrent_llm_manager import ConcurrentLLMManager
from src.memory.context_aware_memory_security import ContextAwareMemoryManager

# MEMORY OPTIMIZATION INTEGRATION: Import optimized memory manager
from src.memory.optimized_memory_manager import create_optimized_memory_manager
from src.memory.redis_conversation_cache import RedisConversationCache
from src.memory.thread_safe_memory import ThreadSafeMemoryManager

# Security and safety components
from src.utils.async_enhancements import (
    cleanup_async_components,
    initialize_async_components,
)
from src.utils.conversation import ConversationHistoryManager

# CRITICAL INTEGRATION: Import new concurrent safety components
from src.utils.graceful_shutdown import GracefulShutdownManager
from src.utils.health_monitor import HealthMonitor

# Voice functionality imports
try:
    from src.llm.elevenlabs_client import ElevenLabsClient
    from src.voice.voice_manager import DiscordVoiceManager

    # from src.voice.voice_commands import VoiceCommands  # Disabled - using VoiceCommandHandlers instead
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    ElevenLabsClient = None
    DiscordVoiceManager = None

VoiceCommands = None  # Explicitly set to None - using VoiceCommandHandlers instead

# External API Emotion AI Integration
try:
    from src.emotion.external_api_emotion_ai import ExternalAPIEmotionAI

    EXTERNAL_EMOTION_AI_AVAILABLE = True
except ImportError:
    EXTERNAL_EMOTION_AI_AVAILABLE = False
    ExternalAPIEmotionAI = None

# Production Optimization Integration
try:
    from src.integration.production_system_integration import WhisperEngineProductionAdapter

    PRODUCTION_OPTIMIZATION_AVAILABLE = True
except ImportError:
    PRODUCTION_OPTIMIZATION_AVAILABLE = False
    WhisperEngineProductionAdapter = None


class DiscordBotCore:
    """Core Discord bot initialization and management class."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the bot core with all necessary components.

        Args:
            debug_mode: Enable debug logging and features
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)

        # Load environment variables
        load_environment()

        # Initialize all components
        self.bot = None
        self.llm_client = None
        self.memory_manager = None
        self.safe_memory_manager = None
        self.conversation_cache = None
        self.image_processor = None
        self.health_monitor = None
        self.backup_manager = None
        self.voice_manager = None
        self.voice_support_enabled = False  # Will be set during voice initialization
        self.external_emotion_ai = None
        self.shutdown_manager = None
        self.heartbeat_monitor = None
        self.conversation_history = None

        # Job scheduler components
        self.job_scheduler = None
        self.postgres_pool = None
        self.postgres_config = None

        # AI enhancement components
        self.personality_profiler = None
        self.graph_personality_manager = None
        self.phase2_integration = None
        self.phase3_memory_networks = None
        self.graph_emotion_manager = None  # Reference to update later with external emotion AI

        # Production optimization components
        self.production_adapter = None

    def initialize_bot(self):
        """Initialize the Discord bot instance with proper configuration."""
        self.logger.info("Initializing Discord bot with default intents")

        # Create intents
        intents = discord.Intents.default()
        intents.message_content = True  # enable if you turned on MESSAGE CONTENT in the dev portal
        intents.reactions = True  # Required for reaction-based commands like !forget_me
        intents.typing = True  # Optional: enables typing event handling (low overhead)

        # Configure heartbeat and connection timeouts
        heartbeat_timeout = float(os.getenv("DISCORD_HEARTBEAT_TIMEOUT", "60.0"))
        chunk_guilds = os.getenv("DISCORD_CHUNK_GUILDS", "false").lower() == "true"

        # Configure command prefix
        command_prefix = os.getenv("DISCORD_COMMAND_PREFIX", "!")
        bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
        self.logger.info(f"Using command prefix: '{command_prefix}', Bot name filter: '{bot_name}'")

        # Create bot instance
        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents,
            heartbeat_timeout=heartbeat_timeout,
            chunk_guilds_at_startup=chunk_guilds,
            help_command=None,  # Remove default help command so we can override it
        )

        self.logger.debug(
            f"Bot instance created with heartbeat_timeout={heartbeat_timeout}s, chunk_guilds={chunk_guilds}"
        )

        # Initialize graceful shutdown manager
        self.shutdown_manager = GracefulShutdownManager(self.bot)
        self.logger.info("Graceful shutdown manager initialized")

    def initialize_llm_client(self):
        """Initialize the LLM client with concurrent safety."""
        self.logger.info("Initializing LLM client")
        base_llm_client = LLMClient()

        # Wrap LLM client with concurrent safety
        safe_llm_client = ConcurrentLLMManager(base_llm_client)
        self.llm_client = safe_llm_client
        self.logger.info("LLM client wrapped with concurrent safety")

    def initialize_memory_system(self):
        """Initialize the memory management system with all enhancements."""
        self.logger.info("Initializing user memory manager")

        if self.llm_client is None:
            raise RuntimeError("LLM client must be initialized before memory system")

        try:
            # Check if graph database integration is enabled
            enable_graph_database = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"

            # Get the base LLM client from the concurrent wrapper
            base_llm_client = getattr(self.llm_client, "base_client", self.llm_client)

            if (
                enable_graph_database
                and GRAPH_MEMORY_AVAILABLE
                and IntegratedMemoryManager is not None
            ):
                self.logger.info("🕸️ Initializing Graph-Enhanced Memory System...")

                # Initialize base memory manager with external embeddings
                base_memory_manager = UserMemoryManager(
                    enable_auto_facts=True, enable_global_facts=True, llm_client=base_llm_client
                )

                # Initialize graph-integrated emotion manager
                # Note: phase2_integration will be set later in initialize_ai_enhancements
                if GRAPH_MEMORY_AVAILABLE and GraphIntegratedEmotionManager is not None:
                    graph_emotion_manager = GraphIntegratedEmotionManager(
                        llm_client=base_llm_client,
                        memory_manager=base_memory_manager,
                        phase2_integration=None,  # Will be updated later
                    )
                    # Store reference to update later
                    self.graph_emotion_manager = graph_emotion_manager
                else:
                    self.graph_emotion_manager = None

                # Initialize integrated memory manager (bridges ChromaDB and Neo4j)
                integrated_memory_manager = IntegratedMemoryManager(
                    memory_manager=base_memory_manager,
                    emotion_manager=graph_emotion_manager,
                    enable_graph_sync=True,
                    llm_client=base_llm_client,
                )

                # Initialize context-aware memory manager
                context_memory_manager = ContextAwareMemoryManager(integrated_memory_manager)
                self.logger.info("✅ Graph-enhanced memory system initialized successfully")

            else:
                if enable_graph_database and not GRAPH_MEMORY_AVAILABLE:
                    self.logger.warning(
                        "⚠️ Graph database enabled but components not available, falling back to standard memory"
                    )

                self.logger.info("📚 Initializing Standard Memory System...")

                # Standard memory manager initialization (fallback)
                base_memory_manager = UserMemoryManager(
                    enable_auto_facts=True, enable_global_facts=True, llm_client=base_llm_client
                )

                # Initialize context-aware memory manager
                context_memory_manager = ContextAwareMemoryManager(base_memory_manager)

            # Wrap memory manager with thread safety
            safe_memory_manager = ThreadSafeMemoryManager(context_memory_manager)
            self.safe_memory_manager = safe_memory_manager
            self.memory_manager = safe_memory_manager

            # Apply optimization patch for better topic recall
            self.memory_manager = apply_memory_enhancement_patch(self.memory_manager)

            self.logger.info("Memory manager wrapped with thread safety and context-aware security")
            self.logger.info("Enhanced memory system patch applied for improved topic recall")

            self.backup_manager = BackupManager()
            self.logger.info("Memory and backup managers initialized successfully")

        except Exception as e:
            self.logger.error("Memory system initialization failed: %s", str(e))
            # Fallback to basic memory manager
            self.memory_manager = UserMemoryManager(llm_client=self.llm_client)
            self.backup_manager = BackupManager()
            self.logger.warning("Using fallback memory manager")

    async def _update_emotional_context_dependencies(self):
        """Update emotional context engine with dependencies after they're initialized"""
        try:
            # Wait a bit for the emotional context engine to finish initializing
            await asyncio.sleep(1)

            if (
                hasattr(self, "phase2_integration")
                and self.phase2_integration
                and hasattr(self.phase2_integration, "emotional_context_engine")
                and self.phase2_integration.emotional_context_engine
            ):

                engine = self.phase2_integration.emotional_context_engine

                # Update emotional AI if available
                if hasattr(self, "external_emotion_ai") and self.external_emotion_ai:
                    engine.emotional_ai = self.external_emotion_ai
                    self.logger.info(
                        "✅ Updated emotional context engine with External API Emotion AI"
                    )

                # Update personality profiler if available
                if (
                    hasattr(self, "dynamic_personality_profiler")
                    and self.dynamic_personality_profiler
                ):
                    engine.personality_profiler = self.dynamic_personality_profiler
                    self.logger.info(
                        "✅ Updated emotional context engine with Dynamic Personality Profiler"
                    )

                self.logger.info(
                    "🎉 Phase 3.1 Emotional Context Engine fully integrated and operational"
                )

        except Exception as e:
            self.logger.warning(
                "Failed to update emotional context engine dependencies: %s", str(e)
            )

    def initialize_ai_enhancements(self):
        """Initialize advanced AI enhancement systems."""
        # Initialize Personality Profiler
        self.logger.info("🧠 Initializing Advanced Personality Profiler...")
        try:
            # All AI features are always enabled - unified AI system
            from src.analysis.graph_personality_manager import GraphPersonalityManager
            from src.analysis.personality_profiler import PersonalityProfiler

            self.personality_profiler = PersonalityProfiler()
            self.logger.info("✅ Personality profiler initialized (always active)")

            # Initialize graph-enhanced personality manager if graph DB is available
            enable_graph_database = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"
            if enable_graph_database and GRAPH_MEMORY_AVAILABLE:
                neo4j_uri = f"bolt://{os.getenv('NEO4J_HOST', 'localhost')}:{os.getenv('NEO4J_PORT', '7687')}"
                neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
                neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j_password_change_me")

                self.graph_personality_manager = GraphPersonalityManager(
                    neo4j_uri, neo4j_user, neo4j_password
                )
                self.logger.info("✅ Graph-enhanced personality manager initialized")
            else:
                self.graph_personality_manager = None
                self.logger.info("📊 Using standalone personality profiler (no graph database)")

        except Exception as e:
            self.logger.error(f"Failed to initialize personality profiler: {e}")
            self.logger.warning("⚠️ Continuing without personality profiling features")

        # Initialize Dynamic Personality Profiler
        self.logger.info("🎭 Initializing Dynamic Personality Profiler...")
        try:
            # Check if dynamic personality profiling is enabled
            enable_dynamic_personality = (
                os.getenv("ENABLE_DYNAMIC_PERSONALITY", "true").lower() == "true"
            )

            if enable_dynamic_personality:
                from src.intelligence.dynamic_personality_profiler import (
                    PersistentDynamicPersonalityProfiler,
                )

                self.dynamic_personality_profiler = PersistentDynamicPersonalityProfiler()
                self.logger.info("✅ Dynamic personality profiler initialized (always active)")
            else:
                self.dynamic_personality_profiler = None
                self.logger.info("📊 Dynamic personality profiler disabled by configuration")

        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic personality profiler: {e}")
            self.logger.warning("⚠️ Continuing without dynamic personality profiling features")
            self.dynamic_personality_profiler = None

        # Initialize Predictive Emotional Intelligence
        self.logger.info("🎯 Initializing Predictive Emotional Intelligence...")
        try:
            # All AI features are always enabled - unified AI system
            from src.intelligence import Phase2Integration

            self.logger.info("🧠 Emotional Intelligence Mode: Full Capabilities Always Active")

            # Phase 3.1 Integration: Provide dependencies for EmotionalContextEngine
            graph_personality_manager = getattr(self, "graph_personality_manager", None)
            conversation_cache = getattr(self, "conversation_cache", None)

            self.phase2_integration = Phase2Integration(
                bot_instance=self,
                graph_personality_manager=graph_personality_manager,
                conversation_cache=conversation_cache,
            )
            self.logger.info(
                "✅ Predictive Emotional Intelligence initialized with Phase 3.1 support"
            )

            # Update emotion manager with phase2_integration if it exists
            if hasattr(self, "graph_emotion_manager") and self.graph_emotion_manager:
                self.graph_emotion_manager.phase2_integration = self.phase2_integration
                self.logger.info("✅ Updated emotion manager with Phase 2 integration")

            # Also update the memory manager's emotion manager if it exists
            if (
                hasattr(self, "memory_manager")
                and self.memory_manager
                and hasattr(self.memory_manager, "emotion_manager")
                and self.memory_manager.emotion_manager
            ):
                self.memory_manager.emotion_manager.phase2_integration = self.phase2_integration
                self.logger.info(
                    "✅ Updated memory manager's emotion manager with Phase 2 integration"
                )

            # Use the new update method for consistency
            if (
                hasattr(self, "memory_manager")
                and self.memory_manager
                and hasattr(self.memory_manager, "update_phase2_integration")
            ):
                self.memory_manager.update_phase2_integration(self.phase2_integration)

        except Exception as e:
            self.logger.error(f"Failed to initialize emotional intelligence: {e}")
            self.logger.warning("⚠️ Continuing without emotional intelligence features")

        # Initialize External API Emotion AI
        self.logger.info("🌐 Initializing External API Emotion AI...")
        try:
            # All AI features are always enabled - unified AI system

            if EXTERNAL_EMOTION_AI_AVAILABLE and ExternalAPIEmotionAI is not None:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

                # Pass LLM client to enable proper emotion model configuration
                self.external_emotion_ai = ExternalAPIEmotionAI(
                    llm_client=self.llm_client,
                    openai_api_key=openai_api_key,
                    huggingface_api_key=huggingface_api_key,
                    logger=self.logger,
                )

                self.logger.info("✅ External API Emotion AI initialized (full capabilities)")

                # Phase 3.1 Integration: Update emotional context engine with emotion AI
                if hasattr(self, "phase2_integration") and self.phase2_integration:
                    # Give the emotional context engine time to initialize, then update dependencies
                    asyncio.create_task(self._update_emotional_context_dependencies())

            else:
                self.logger.info("🌐 External API Emotion AI disabled or not available")

        except Exception as e:
            self.logger.error(f"Failed to initialize External API Emotion AI: {e}")
            self.logger.warning("⚠️ Continuing without External API Emotion AI features")

        # Initialize Phase 3 Memory Networks
        self.logger.info("🕸️ Initializing Phase 3: Multi-Dimensional Memory Networks...")
        try:
            # All AI features are always enabled - unified AI system
            from src.memory.phase3_integration import Phase3MemoryNetworks

            self.logger.info("🕸️ Memory Network Mode: Full Capabilities Always Active")

            self.phase3_memory_networks = Phase3MemoryNetworks()
            self.logger.info("✅ Phase 3: Multi-Dimensional Memory Networks initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize Phase 3 memory networks: {e}")
            self.logger.warning("⚠️ Continuing without Phase 3 memory network features")

        # Initialize Phase 4.1: Memory-Triggered Personality Moments
        self.logger.info("💭 Initializing Phase 4.1: Memory-Triggered Personality Moments...")
        try:
            # All AI features are always enabled - unified AI system
            from src.personality.memory_moments import MemoryTriggeredMoments

            if self.memory_manager and (
                hasattr(self, "phase2_integration") and self.phase2_integration
            ):
                self.memory_moments = MemoryTriggeredMoments(
                    memory_manager=self.memory_manager,
                    emotional_context_engine=(
                        self.phase2_integration.emotional_context_engine
                        if hasattr(self.phase2_integration, "emotional_context_engine")
                        else None
                    ),
                    personality_profiler=getattr(self, "personality_profiler", None),
                )
                self.logger.info("✅ Phase 4.1: Memory-Triggered Personality Moments initialized")
            else:
                self.logger.warning(
                    "⚠️ Cannot initialize Memory Moments - missing memory manager or Phase 2 integration"
                )
                self.memory_moments = None

        except Exception as e:
            self.logger.error(f"Failed to initialize Phase 4.1 memory moments: {e}")
            self.logger.warning("⚠️ Continuing without memory-triggered personality features")
            self.memory_moments = None

        # Initialize Phase 4 Human-Like Intelligence
        self.logger.info("🤖 Initializing Phase 4: Human-Like Conversation Intelligence...")
        try:
            # All AI features are always enabled - unified AI system
            if self.memory_manager and self.llm_client:
                from src.intelligence.phase4_integration import apply_phase4_integration_patch

                # Get AI behavior configuration from unified variables
                memory_optimization = os.getenv("AI_MEMORY_OPTIMIZATION", "true").lower() == "true"
                emotional_resonance = os.getenv("AI_EMOTIONAL_RESONANCE", "true").lower() == "true"
                adaptive_mode = os.getenv("AI_ADAPTIVE_MODE", "true").lower() == "true"
                (os.getenv("AI_PERSONALITY_ANALYSIS", "true").lower() == "true")

                # Use full configuration for Phase 4
                phase4_config = {
                    "memory_optimization": memory_optimization,
                    "emotional_resonance": emotional_resonance,
                    "adaptive_mode": adaptive_mode,
                    "max_memory_queries": 30,
                    "max_conversation_history": 50,
                    "relationship_tracking": "comprehensive",
                    "query_optimization": True,
                }
                self.logger.info(
                    "🎛️ AI Configuration: Full Capabilities - System prompt handles conversation adaptation"
                )

                # Get the base LLM client from the concurrent wrapper
                base_llm_client = getattr(self.llm_client, "base_client", self.llm_client)

                # Apply Phase 4 integration patch to memory manager
                self.memory_manager = apply_phase4_integration_patch(
                    memory_manager=self.memory_manager,
                    phase2_integration=self.phase2_integration,
                    phase3_memory_networks=self.phase3_memory_networks,
                    llm_client=base_llm_client,
                    **phase4_config,
                )

                self.logger.info("✅ Phase 4: Human-Like Conversation Intelligence integrated")

                # Log Phase 4 status
                try:
                    phase4_status = self.memory_manager.get_phase4_status()
                    self.logger.info(
                        f"🧠 Phase 4 Integration Health: {phase4_status['integration_health']}"
                    )
                except Exception as status_error:
                    self.logger.debug(f"Could not retrieve Phase 4 status: {status_error}")
            else:
                self.logger.warning(
                    "⚠️ Cannot initialize AI system - missing memory manager or LLM client"
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize Phase 4 human-like intelligence: {e}")
            self.logger.warning("⚠️ Continuing without Phase 4 human-like intelligence features")

    def initialize_conversation_cache(self):
        """Initialize the conversation cache system."""
        self.logger.info("Initializing conversation cache")

        try:
            cache_timeout = int(os.getenv("CONVERSATION_CACHE_TIMEOUT_MINUTES", "15"))
            bootstrap_limit = int(os.getenv("CONVERSATION_CACHE_BOOTSTRAP_LIMIT", "20"))
            max_local_messages = int(os.getenv("CONVERSATION_CACHE_MAX_LOCAL", "50"))

            use_redis = os.getenv("USE_REDIS_CACHE", "true").lower() == "true"

            if use_redis:
                self.logger.info("Attempting to initialize Redis-based conversation cache")
                self.conversation_cache = RedisConversationCache(
                    cache_timeout_minutes=cache_timeout,
                    bootstrap_limit=bootstrap_limit,
                    max_local_messages=max_local_messages,
                )
                self.logger.info(
                    "Redis conversation cache initialized (connection will be established on bot start)"
                )
            else:
                self.logger.info("Using in-memory conversation cache (Redis disabled)")
                self.conversation_cache = HybridConversationCache(
                    cache_timeout_minutes=cache_timeout,
                    bootstrap_limit=bootstrap_limit,
                    max_local_messages=max_local_messages,
                )

            self.logger.info("Conversation cache initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize conversation cache: {e}")
            self.conversation_cache = None

    def initialize_health_monitor(self):
        """Initialize the health monitoring system."""
        self.logger.info("Initializing health monitor")

        try:
            emotion_mgr = (
                getattr(self.memory_manager, "emotion_manager", None)
                if hasattr(self.memory_manager, "emotion_manager")
                else None
            )
            self.health_monitor = HealthMonitor(
                memory_manager=self.memory_manager,
                llm_client=self.llm_client,
                conversation_cache=self.conversation_cache,
                emotion_manager=emotion_mgr,
                backup_manager=self.backup_manager,
            )
            self.logger.info("Health monitor initialized successfully")

        except Exception as e:
            self.logger.warning(f"Failed to initialize health monitor: {e}")
            self.health_monitor = None

    def initialize_image_processor(self):
        """Initialize the image processing system."""
        self.logger.info("Initializing image processor")

        try:
            self.image_processor = ImageProcessor()
            self.logger.info("Image processor initialized successfully")

        except Exception as e:
            self.logger.critical(f"Failed to initialize image processor: {e}")
            raise

    def initialize_voice_system(self):
        """Initialize the voice functionality if available."""
        self.voice_support_enabled = os.getenv("VOICE_SUPPORT_ENABLED", "true").lower() == "true"

        if (
            VOICE_AVAILABLE
            and self.voice_support_enabled
            and ElevenLabsClient is not None
            and DiscordVoiceManager is not None
            and self.bot is not None
        ):
            try:
                self.logger.info("Initializing voice functionality...")

                # Initialize ElevenLabs client
                elevenlabs_client = ElevenLabsClient()
                self.logger.info("ElevenLabs client initialized")

                # Initialize voice manager
                self.voice_manager = DiscordVoiceManager(
                    self.bot, elevenlabs_client, self.llm_client, self.memory_manager
                )
                self.logger.info("Voice manager initialized")

                self.logger.info("✅ Voice functionality initialized successfully!")

            except Exception as e:
                self.logger.error(f"Failed to initialize voice functionality: {e}")
                self.logger.warning("Bot will continue without voice features")
                self.voice_manager = None
        elif VOICE_AVAILABLE and not self.voice_support_enabled:
            self.logger.info(
                "Voice functionality disabled by configuration (VOICE_SUPPORT_ENABLED=false)"
            )
        else:
            self.logger.info("Voice functionality not available - missing dependencies")

    def initialize_production_optimization(self):
        """Initialize the production optimization system if available."""
        enable_production_optimization = (
            os.getenv("ENABLE_PRODUCTION_OPTIMIZATION", "true").lower() == "true"
        )

        if (
            PRODUCTION_OPTIMIZATION_AVAILABLE
            and enable_production_optimization
            and WhisperEngineProductionAdapter is not None
        ):
            try:
                self.logger.info("Initializing production optimization system...")

                # Initialize production adapter with bot core
                self.production_adapter = WhisperEngineProductionAdapter(bot_core=self)

                # Initialize production mode asynchronously
                # Note: This will be called during bot startup
                self.logger.info("✅ Production optimization adapter initialized successfully!")
                self.logger.info("🚀 Production mode will be enabled during bot startup")

            except Exception as e:
                self.logger.error(f"Failed to initialize production optimization adapter: {e}")
                self.logger.warning("Bot will continue with standard performance")
                self.production_adapter = None
        else:
            if not enable_production_optimization:
                self.logger.info(
                    "Production optimization system disabled via ENABLE_PRODUCTION_OPTIMIZATION"
                )
            else:
                self.logger.info("Production optimization system dependencies not available")
            self.production_adapter = None

    def initialize_postgres_config(self):
        """Initialize PostgreSQL configuration for job scheduler."""
        self.logger.info("Setting up PostgreSQL configuration")

        try:
            import asyncpg

            self.postgres_config = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "discord_bot"),
                "user": os.getenv("POSTGRES_USER", "bot_user"),
                "password": os.getenv("POSTGRES_PASSWORD", "bot_password_change_me"),
                "min_size": int(os.getenv("POSTGRES_MIN_CONNECTIONS", "5")),
                "max_size": int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20")),
            }

            self.logger.info("PostgreSQL configuration prepared for async initialization")

        except ImportError:
            self.logger.warning("asyncpg not available, PostgreSQL features disabled")
            self.postgres_config = None
        except Exception as e:
            self.logger.error(f"Failed to prepare PostgreSQL configuration: {e}")
            self.postgres_config = None

    def initialize_supporting_systems(self):
        """Initialize supporting systems like heartbeat monitor and conversation history."""
        # Initialize conversation history manager
        self.conversation_history = ConversationHistoryManager(
            max_channels=100, max_messages_per_channel=100
        )
        self.logger.debug("Conversation history manager initialized")

        # Initialize heartbeat monitor
        if self.bot is not None:
            heartbeat_check_interval = float(os.getenv("DISCORD_HEARTBEAT_CHECK_INTERVAL", "10.0"))
            self.heartbeat_monitor = HeartbeatMonitor(
                self.bot, check_interval=heartbeat_check_interval
            )
            self.logger.debug(
                f"Heartbeat monitor initialized with {heartbeat_check_interval}s check interval"
            )

        # Initialize async enhancements
        if self.memory_manager and self.llm_client and self.image_processor:
            try:
                # Get the base LLM client from the concurrent wrapper
                base_llm_client = getattr(self.llm_client, "base_client", self.llm_client)
                initialize_async_components(
                    self.memory_manager, base_llm_client, self.image_processor
                )
                self.logger.info("✅ Async enhancements initialized for concurrent users!")
            except Exception as e:
                self.logger.error(f"Failed to initialize async enhancements: {e}")
                self.logger.warning(
                    "Bot will continue with standard (non-optimized) async operations"
                )

    def register_cleanup_functions(self):
        """Register cleanup functions with the shutdown manager."""
        if self.shutdown_manager is None:
            self.logger.warning("Shutdown manager not initialized, skipping cleanup registration")
            return

        try:
            self.shutdown_manager.register_cleanup(cleanup_async_components, priority=100)

            if self.memory_manager and hasattr(self.memory_manager, "cleanup"):
                self.shutdown_manager.register_cleanup(self.memory_manager.cleanup, priority=90)

            if self.llm_client and hasattr(self.llm_client, "cleanup"):
                self.shutdown_manager.register_cleanup(self.llm_client.cleanup, priority=85)

            if self.heartbeat_monitor and hasattr(self.heartbeat_monitor, "stop"):
                self.shutdown_manager.register_cleanup(
                    lambda hm=self.heartbeat_monitor: hm.stop(), priority=80
                )

            # Register emotion manager cleanup if available
            if (
                self.memory_manager
                and hasattr(self.memory_manager, "emotion_manager")
                and self.memory_manager.emotion_manager
                and hasattr(self.memory_manager.emotion_manager, "cleanup")
            ):
                self.shutdown_manager.register_cleanup(
                    self.memory_manager.emotion_manager.cleanup, priority=75
                )

            self.logger.info("Cleanup functions registered with shutdown manager")

        except Exception as e:
            self.logger.error(f"Failed to register cleanup functions: {e}")

    def initialize_all(self):
        """Initialize all bot components in the correct order."""
        self.logger.info("Starting bot core initialization...")

        # Core components
        self.initialize_bot()
        self.initialize_llm_client()
        self.initialize_memory_system()

        # Supporting systems
        self.initialize_conversation_cache()
        self.initialize_health_monitor()
        self.initialize_image_processor()
        self.initialize_supporting_systems()

        # Optional enhancements
        self.initialize_ai_enhancements()
        self.initialize_voice_system()
        self.initialize_production_optimization()
        self.initialize_postgres_config()

        # Cleanup registration
        self.register_cleanup_functions()

        self.logger.info("✅ Bot core initialization completed successfully!")

    def get_bot(self):
        """Get the initialized Discord bot instance."""
        if self.bot is None:
            raise RuntimeError("Bot not initialized. Call initialize_all() first.")
        return self.bot

    def get_components(self):
        """Get all initialized bot components as a dictionary."""

        # Create optimized memory manager if components are available
        optimized_memory_manager = self.memory_manager
        try:
            if hasattr(self, "llm_client") and self.llm_client and self.memory_manager:
                # Try to find embedding manager from memory manager
                embedding_manager = None
                if (
                    hasattr(self.memory_manager, "embedding_manager")
                    and self.memory_manager.embedding_manager
                ):
                    embedding_manager = self.memory_manager.embedding_manager
                elif (
                    hasattr(self.memory_manager, "memory_manager")
                    and self.memory_manager.memory_manager
                    and hasattr(self.memory_manager.memory_manager, "embedding_manager")
                ):
                    embedding_manager = self.memory_manager.memory_manager.embedding_manager

                optimized_memory_manager = create_optimized_memory_manager(
                    llm_client=self.llm_client,
                    embedding_manager=embedding_manager,
                    memory_manager=self.memory_manager,
                )

                # Use logging if available
                try:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info("✅ Memory optimization integrated successfully")
                except:
                    pass
            else:
                try:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info("ℹ️ Using standard memory manager (LLM client not available)")
                except:
                    pass
        except Exception as e:
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Memory optimization initialization failed, using standard manager: {e}"
                )
            except:
                pass
            optimized_memory_manager = self.memory_manager

        return {
            "bot": self.bot,
            "llm_client": self.llm_client,
            "memory_manager": optimized_memory_manager,
            "conversation_cache": self.conversation_cache,
            "image_processor": self.image_processor,
            "health_monitor": self.health_monitor,
            "backup_manager": self.backup_manager,
            "voice_manager": self.voice_manager,
            "external_emotion_ai": self.external_emotion_ai,
            "shutdown_manager": self.shutdown_manager,
            "heartbeat_monitor": self.heartbeat_monitor,
            "conversation_history": self.conversation_history,
            "postgres_config": self.postgres_config,
            "personality_profiler": self.personality_profiler,
            "dynamic_personality_profiler": getattr(self, "dynamic_personality_profiler", None),
            "graph_personality_manager": self.graph_personality_manager,
            "phase2_integration": self.phase2_integration,
            "phase3_memory_networks": self.phase3_memory_networks,
            "memory_moments": getattr(self, "memory_moments", None),
            "production_adapter": self.production_adapter,
        }
