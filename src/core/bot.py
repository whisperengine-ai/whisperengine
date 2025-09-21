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
# LLM client system
from src.llm.llm_protocol import create_llm_client
# from src.memory.backup_manager import BackupManager  # REMOVED - Vector-native architecture
from src.memory.conversation_cache import HybridConversationCache
from src.utils.heartbeat_monitor import HeartbeatMonitor
from src.utils.image_processor import ImageProcessor

# VECTOR MEMORY: The vector-native memory system (replaces hierarchical)
from src.memory.memory_protocol import create_memory_manager


# Security and safety components
from src.utils.async_enhancements import (
    cleanup_async_components,
    initialize_async_components,
)
from src.utils.conversation import ConversationHistoryManager

# CRITICAL INTEGRATION: Import new concurrent safety components
from src.utils.graceful_shutdown import GracefulShutdownManager
from src.utils.health_monitor import HealthMonitor

# Voice functionality import
from src.voice.voice_protocol import create_voice_service

# Redis conversation cache and profile memory cache
try:
    from src.memory.redis_conversation_cache import RedisConversationCache
    from src.memory.redis_profile_memory_cache import RedisProfileAndMemoryCache
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False
    RedisConversationCache = None
    RedisProfileAndMemoryCache = None

# Graph memory availability check - REMOVED
# Vector-native components replace previous graph relationships
GRAPH_MEMORY_AVAILABLE = False

# Legacy emotion engine removed - vector-native system handles emotion analysis

# Production Optimization Integration
try:
    from src.integration.production_system_integration import WhisperEngineProductionAdapter

    PRODUCTION_OPTIMIZATION_AVAILABLE = True
except ImportError:
    PRODUCTION_OPTIMIZATION_AVAILABLE = False
    WhisperEngineProductionAdapter = None

# Multi-Entity Relationship Integration
try:
    from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
    from src.graph_database.ai_self_bridge import AISelfEntityBridge

    MULTI_ENTITY_AVAILABLE = True
except ImportError:
    MULTI_ENTITY_AVAILABLE = False
    MultiEntityRelationshipManager = None
    AISelfEntityBridge = None


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
        self.profile_memory_cache = None
        self.conversation_cache = None
        self.image_processor = None
        self.health_monitor = None
        self.monitoring_manager = None
        self.backup_manager = None
        self.voice_manager = None
        self.voice_support_enabled = False  # Will be set during voice initialization
        self.local_emotion_engine = None
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

        # Multi-Entity Relationship components
        self.multi_entity_manager = None
        self.ai_self_bridge = None

        # Add properties for batch initialization
        self._batched_memory_manager = None
        self._needs_batch_init = False

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
        """Initialize the LLM client using factory pattern."""
        llm_client_type = os.getenv("LLM_CLIENT_TYPE", "openrouter")
        
        self.logger.info("Initializing LLM client: %s", llm_client_type)
        
        try:
            self.llm_client = create_llm_client(llm_client_type=llm_client_type)
            self.logger.info("✅ LLM client initialized successfully!")
        except Exception as e:
            self.logger.error("Failed to initialize LLM client: %s", e)
            self.logger.warning("Bot will continue with disabled LLM features")
            # Fallback to disabled service
            self.llm_client = create_llm_client(llm_client_type="disabled")

    def initialize_memory_system(self):
        """Initialize the memory management system using factory pattern."""
        self.logger.info("🚀 Initializing Memory System...")

        try:
            # Get memory system type from environment (default to vector-native)
            # Note: hierarchical memory has been REMOVED - use 'vector' instead
            memory_type = os.getenv("MEMORY_SYSTEM_TYPE", "vector")
            
            # Create memory manager using factory pattern
            # This enables easy A/B testing: just change MEMORY_SYSTEM_TYPE
            memory_manager = create_memory_manager(memory_type)
            
            # Set as THE memory manager (clean, simple)
            self.safe_memory_manager = memory_manager
            self.memory_manager = memory_manager

            # self.backup_manager = BackupManager()  # REMOVED - Vector-native architecture
            self.backup_manager = None  # Vector memory system handles persistence differently
            
            self.logger.info("✅ Memory System initialized with type: %s", memory_type)

        except Exception as e:
            self.logger.error("Memory system initialization failed: %s", str(e))
            raise
            
    # REMOVED: Legacy memory optimizer - replaced by vector-native memory system

    async def initialize_phase4_components(self):
        """Initialize Phase 4.2 and 4.3 components asynchronously."""
        try:
            # Initialize Phase 4.2: Advanced Thread Manager
            if not hasattr(self, 'thread_manager') or self.thread_manager is None:
                try:
                    from src.conversation.advanced_thread_manager import create_advanced_conversation_thread_manager
                    self.thread_manager = await create_advanced_conversation_thread_manager()
                    self.logger.info("✅ Phase 4.2: Advanced Thread Manager initialized")
                except Exception as e:
                    self.logger.warning(f"Phase 4.2 thread manager not available: {e}")
                    self.logger.debug("Continuing without advanced thread management features")
                    self.thread_manager = None

            # Initialize Phase 4.3: Proactive Engagement Engine
            if not hasattr(self, 'engagement_engine') or self.engagement_engine is None:
                try:
                    from src.conversation.engagement_protocol import create_engagement_engine
                    
                    # Create with available integrations using factory pattern
                    self.engagement_engine = await create_engagement_engine(
                        engagement_engine_type=os.getenv("ENGAGEMENT_ENGINE_TYPE", "full"),
                        thread_manager=getattr(self, 'thread_manager', None),
                        memory_moments=getattr(self, 'memory_moments', None),
                        emotional_engine=getattr(self.phase2_integration, 'emotional_context_engine', None) if hasattr(self, 'phase2_integration') else None,
                        personality_profiler=getattr(self, 'dynamic_personality_profiler', None)
                    )
                    self.logger.info("✅ Phase 4.3: Proactive Engagement Engine initialized with factory pattern")
                except Exception as e:
                    self.logger.warning("Phase 4.3 engagement engine not available: %s", e)
                    self.logger.debug("Continuing without proactive engagement features")
                    self.engagement_engine = None

            # Log Phase 4 integration status
            if hasattr(self, 'memory_moments') and self.memory_moments:
                self.logger.info("🎭 Phase 4.1: Memory-Triggered Moments - ACTIVE")
            if hasattr(self, 'thread_manager') and self.thread_manager:
                self.logger.info("🧵 Phase 4.2: Advanced Thread Manager - ACTIVE")
            if hasattr(self, 'engagement_engine') and self.engagement_engine:
                self.logger.info("⚡ Phase 4.3: Proactive Engagement Engine - ACTIVE")

        except Exception as e:
            self.logger.error(f"Error during Phase 4 component initialization: {e}")

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

                # Legacy emotion engine removed - vector-native handles emotion analysis

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
        # Legacy personality profiler removed - vector-native system handles personality analysis
        self.personality_profiler = None
        self.graph_personality_manager = None
        self.logger.info("📊 Using vector-native personality analysis (CDL + embedding intelligence)")

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

        # Legacy emotion engine removed - vector-native system handles emotion analysis
        self.local_emotion_engine = None
        self.logger.info("🌐 Using vector-native emotion analysis (embedding intelligence)")

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

        # Initialize Phase 4.2: Advanced Thread Manager
        self.logger.info("🧵 Initializing Phase 4.2: Advanced Thread Manager...")
        try:
            from src.conversation.advanced_thread_manager import create_advanced_conversation_thread_manager
            
            # Initialize advanced thread manager asynchronously (will be awaited later)
            self._thread_manager_task = None
            self.thread_manager = None
            self.logger.info("✅ Phase 4.2: Advanced Thread Manager scheduled for initialization")
            
        except Exception as e:
            self.logger.warning(f"Phase 4.2 thread manager not available: {e}")
            self.logger.debug("⚠️ Continuing without advanced thread management features")
            self.thread_manager = None

        # Initialize Phase 4.3: Proactive Engagement Engine
        self.logger.info("⚡ Initializing Phase 4.3: Proactive Engagement Engine...")
        try:
            from src.conversation.engagement_protocol import create_engagement_engine
            
            # Initialize proactive engagement engine asynchronously (will be awaited later)
            self._engagement_engine_task = None
            self.engagement_engine = None
            self.logger.info("✅ Phase 4.3: Proactive Engagement Engine scheduled for initialization")
            
        except Exception as e:
            self.logger.warning("Phase 4.3 engagement engine not available: %s", e)
            self.logger.debug("⚠️ Continuing without proactive engagement features")
            self.engagement_engine = None

        # Initialize Phase 4 Human-Like Intelligence
        self.logger.info("🤖 Initializing Phase 4: Human-Like Conversation Intelligence...")
        try:
            # All AI features are always enabled - unified AI system
            if self.memory_manager and self.llm_client:
                # Clean Protocol-based architecture - no enhancement wrappers needed
                # The memory manager already provides all necessary functionality through Protocol
                
                self.logger.info("🎛️ AI Configuration: Clean Protocol-based Architecture")
                self.logger.info("✅ Phase 4: Human-Like Conversation Intelligence integrated")
                self.logger.info("🤗 Human-Like Memory System: Built into Protocol architecture")
                self.logger.info("💝 Emotional Intelligence Level: Integrated in memory system")
                self.logger.info("🧠 Phase 4 Integration Health: Clean Protocol-based")
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

            if use_redis and REDIS_CACHE_AVAILABLE:
                self.logger.info("Attempting to initialize Redis-based conversation cache")
                self.conversation_cache = RedisConversationCache(
                    cache_timeout_minutes=cache_timeout,
                    bootstrap_limit=bootstrap_limit,
                    max_local_messages=max_local_messages,
                )
                # Initialize RedisProfileAndMemoryCache for personality/memory caching
                self.profile_memory_cache = RedisProfileAndMemoryCache(cache_timeout_minutes=cache_timeout)
                self.logger.info(
                    "Redis conversation cache initialized (connection will be established on bot start)"
                )
            elif use_redis and not REDIS_CACHE_AVAILABLE:
                self.logger.warning("Redis cache requested but Redis dependencies not available, falling back to in-memory cache")
                self.conversation_cache = HybridConversationCache(
                    cache_timeout_minutes=cache_timeout,
                    bootstrap_limit=bootstrap_limit,
                    max_local_messages=max_local_messages,
                )
                self.profile_memory_cache = None
            else:
                self.logger.info("Using in-memory conversation cache (Redis disabled)")
                self.conversation_cache = HybridConversationCache(
                    cache_timeout_minutes=cache_timeout,
                    bootstrap_limit=bootstrap_limit,
                    max_local_messages=max_local_messages,
                )
                self.profile_memory_cache = None

            self.logger.info("Conversation cache initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize conversation cache: {e}")
            self.conversation_cache = None
            self.profile_memory_cache = None

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

    def initialize_monitoring_system(self):
        """Initialize the full monitoring system with dashboard support."""
        self.logger.info("Initializing monitoring system")

        try:
            from src.monitoring import initialize_monitoring
            
            # Schedule async initialization but store the task for later awaiting
            self.monitoring_init_task = asyncio.create_task(self._async_initialize_monitoring())
            self.logger.info("Monitoring system initialization scheduled")

        except Exception as e:
            self.logger.warning(f"Failed to initialize monitoring system: {e}")

    async def _async_initialize_monitoring(self):
        """Async initialization of monitoring system."""
        try:
            from src.monitoring import initialize_monitoring
            
            # Initialize monitoring with environment-based config
            self.monitoring_manager = await initialize_monitoring()
            self.logger.info("✅ Monitoring system initialized successfully")
            
            # Log dashboard status
            if self.monitoring_manager.enable_dashboard:
                dashboard_url = self.monitoring_manager.get_dashboard_url()
                if dashboard_url:
                    self.logger.info(f"📊 Monitoring dashboard available at: {dashboard_url}")
                else:
                    self.logger.warning("Dashboard enabled but URL not available")
            else:
                self.logger.info("📊 Monitoring dashboard disabled")

        except Exception as e:
            self.logger.error(f"Failed to async initialize monitoring system: {e}")
            # Create a minimal monitoring manager for compatibility
            from src.monitoring import MonitoringManager
            self.monitoring_manager = MonitoringManager()

    async def ensure_monitoring_ready(self):
        """Ensure monitoring system is fully initialized before proceeding."""
        if hasattr(self, 'monitoring_init_task'):
            await self.monitoring_init_task
            self.logger.info("Monitoring system initialization completed")

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
        """Initialize voice functionality using the factory pattern."""
        voice_service_type = os.getenv("VOICE_SERVICE_TYPE", "discord_elevenlabs")
        
        # Check if voice support is enabled
        voice_support_enabled = os.getenv("VOICE_SUPPORT_ENABLED", "true").lower() == "true"
        
        if not voice_support_enabled:
            voice_service_type = "disabled"
            self.logger.info("Voice functionality disabled by configuration (VOICE_SUPPORT_ENABLED=false)")
        
        self.logger.info("Initializing voice service: %s", voice_service_type)
        
        try:
            self.voice_manager = create_voice_service(
                voice_service_type=voice_service_type,
                bot=self.bot,
                llm_client=self.llm_client,
                memory_manager=self.memory_manager
            )
            
            # Set voice support flag based on what we actually got
            if hasattr(self.voice_manager, 'voice_response_enabled'):
                self.voice_support_enabled = True
                self.logger.info("✅ Voice functionality initialized successfully!")
            else:
                self.voice_support_enabled = False
                self.logger.info("Voice functionality not available or disabled")
                
        except Exception as e:
            self.logger.error("Failed to initialize voice functionality: %s", e)
            self.logger.warning("Bot will continue without voice features")
            # Fallback to disabled service
            self.voice_manager = create_voice_service(voice_service_type="disabled")
            self.voice_support_enabled = False

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

    def initialize_multi_entity_system(self):
        """Initialize the multi-entity relationship system if available."""
        enable_multi_entity = (
            os.getenv("ENABLE_MULTI_ENTITY_RELATIONSHIPS", "true").lower() == "true"
        )

        if (
            MULTI_ENTITY_AVAILABLE
            and enable_multi_entity
            and MultiEntityRelationshipManager is not None
            and AISelfEntityBridge is not None
        ):
            try:
                self.logger.info("🌐 Initializing Multi-Entity Relationship System...")

                # Initialize multi-entity relationship manager
                self.multi_entity_manager = MultiEntityRelationshipManager()

                # Note: Schema initialization will happen when first database operation is called
                self.logger.info("📊 Multi-entity schema will be initialized on first use")

                # Initialize AI Self bridge
                self.ai_self_bridge = AISelfEntityBridge()

                self.logger.info("✅ Multi-Entity Relationship System initialized successfully!")
                self.logger.info("🎭 Characters can now be connected to users and AI Self")

            except Exception as e:
                self.logger.error(f"Failed to initialize multi-entity relationship system: {e}")
                self.logger.warning("Bot will continue without multi-entity features")
                self.multi_entity_manager = None
                self.ai_self_bridge = None
        else:
            if not enable_multi_entity:
                self.logger.info(
                    "Multi-entity relationship system disabled via ENABLE_MULTI_ENTITY_RELATIONSHIPS"
                )
            else:
                self.logger.info("Multi-entity relationship system dependencies not available")
            self.multi_entity_manager = None
            self.ai_self_bridge = None

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

        # Schedule async initialization of batch optimizer
        if self._needs_batch_init:
            asyncio.create_task(self.initialize_batch_optimizer())

        # Schedule async initialization of Phase 4 components
        asyncio.create_task(self.initialize_phase4_components())

        # Supporting systems
        self.initialize_conversation_cache()
        self.initialize_health_monitor()
        self.initialize_monitoring_system()
        self.initialize_image_processor()
        self.initialize_supporting_systems()

        # Optional enhancements
        self.initialize_ai_enhancements()
        self.initialize_voice_system()
        self.initialize_production_optimization()
        self.initialize_multi_entity_system()
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
            "monitoring_manager": self.monitoring_manager,
            "backup_manager": self.backup_manager,
            "voice_manager": self.voice_manager,
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
            "multi_entity_manager": self.multi_entity_manager,
            "ai_self_bridge": self.ai_self_bridge,
        }
