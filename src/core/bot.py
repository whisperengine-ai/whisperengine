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

# Redis conversation cache and profile memory cache - DISABLED for vector-native approach
# from src.memory.redis_conversation_cache import RedisConversationCache
# from src.memory.redis_profile_memory_cache import RedisProfileAndMemoryCache

# Graph memory availability check - REMOVED
# Vector-native components replace previous graph relationships
GRAPH_MEMORY_AVAILABLE = False

# Legacy emotion engine removed - vector-native system handles emotion analysis

# Production Optimization Integration - our own local code, always import
from src.integration.production_system_integration import WhisperEngineProductionAdapter

# Multi-Entity Relationship Integration - our own local code, always import  
# Multi-entity relationship management removed - using vector-native memory
# AI Self bridge removed - using vector-native memory


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
        self.image_processor = None
        self.health_monitor = None
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
        self.dynamic_personality_profiler = None
        self.phase2_integration = None
        
        # Character system components
        self.character_system = None
        self.character_file = None
        self.context_switch_detector = None  # Phase 3 Advanced Intelligence
        self.empathy_calibrator = None  # Phase 3 Advanced Intelligence

        # Knowledge management components
        self.knowledge_router = None  # Semantic knowledge router for factual intelligence

        # Roleplay components
        self.transaction_manager = None  # Transaction state manager for roleplay interactions
        self.workflow_manager = None  # Workflow manager for declarative transaction patterns

        # Production optimization components
        self.production_adapter = None

        # Concurrent Conversation Management
        self.conversation_manager = None

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
            
            # Universal Identity Adapter removed - Discord-only operation uses direct vector storage
            # (Can be re-enabled later for web UI integration)
            
            # Set as THE memory manager (clean, simple)
            self.safe_memory_manager = memory_manager
            self.memory_manager = memory_manager
            
            self.logger.info("✅ Memory System initialized with type: %s", memory_type)

        except Exception as e:
            self.logger.debug("Memory system initialization failed: %s", str(e))
            raise
    
    def initialize_character_system(self):
        """Initialize CDL character system for personality-driven responses (database-only)."""
        try:
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            # Database-only CDL loading - ignore CDL_DEFAULT_CHARACTER environment variable
            # Character is determined by DISCORD_BOT_NAME environment variable
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # Initialize CDL AI integration system with required dependencies
            # Enhanced manager will be added asynchronously after postgres pool is ready
            self.character_system = CDLAIPromptIntegration(
                vector_memory_manager=self.memory_manager,
                llm_client=self.llm_client,
                enhanced_manager=None  # Will be set by initialize_enhanced_cdl_manager()
            )
            
            # Set character_file to None to indicate database-only mode
            self.character_file = None
            
            self.logger.info("✅ Character system initialized with database-only CDL for bot: %s", bot_name)
                
        except Exception as e:
            self.logger.error("❌ Character system initialization failed: %s", str(e))
            # Don't raise - character system is optional
    
    async def initialize_enhanced_cdl_manager(self):
        """Initialize enhanced CDL manager for rich character data (requires postgres pool)."""
        try:
            from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
            
            # Wait for postgres pool to be available (max 30 seconds)
            max_wait = 30
            wait_interval = 1
            waited = 0
            
            while not self.postgres_pool and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Check if postgres pool is available
            if not self.postgres_pool:
                self.logger.warning("⚠️ PostgreSQL pool not available after %ds - enhanced CDL manager disabled", max_wait)
                return
            
            # Create enhanced CDL manager
            enhanced_manager = create_enhanced_cdl_manager(self.postgres_pool)
            self.logger.info("✅ Enhanced CDL manager initialized for rich character data")
            
            # 🚨 PRE-FLIGHT CHECK: Validate character exists in database
            await self.validate_character_exists(enhanced_manager)
            
            # Update character system with enhanced manager
            if self.character_system:
                self.character_system.enhanced_manager = enhanced_manager
                # 🐛 FIX: Also update TriggerModeController's enhanced_manager reference
                if hasattr(self.character_system, 'trigger_mode_controller') and self.character_system.trigger_mode_controller:
                    self.character_system.trigger_mode_controller.enhanced_manager = enhanced_manager
                    self.logger.info("✅ TriggerModeController updated with enhanced CDL manager for database-driven mode detection")
                self.logger.info("✅ Character system updated with enhanced CDL manager for relationships, triggers, and speech patterns")
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced CDL manager initialization failed: {e}")
            # Don't raise - enhanced manager is optional enhancement
    
    async def validate_character_exists(self, enhanced_manager):
        """
        Pre-flight check: Validate character exists in database before accepting messages.
        This provides fail-fast feedback at startup instead of silent failure on first message.
        
        Note: Does NOT cache character data - validation only for startup safety.
        """
        try:
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            self.logger.info("🔍 CDL Pre-flight: Validating character '%s' exists in database...", bot_name)
            
            # Quick existence check - just verify character_identity record exists
            character_data = await enhanced_manager.get_character_by_name(bot_name)
            
            if not character_data:
                error_msg = f"❌ STARTUP FAILED: Character '{bot_name}' not found in CDL database!"
                self.logger.error(error_msg)
                self.logger.error("💡 Fix: Import character with 'python batch_import_characters.py' or create CDL entry")
                raise RuntimeError(error_msg)
            
            # Extract character name for confirmation
            identity_data = character_data.get('identity', {})
            character_name = identity_data.get('name', 'Unknown')
            character_occupation = identity_data.get('occupation', '')
            
            self.logger.info("✅ CDL Pre-flight: Character validated - '%s' (%s) ready", 
                           character_name, character_occupation)
            
        except RuntimeError:
            # Re-raise validation failures to stop bot startup
            raise
        except Exception as e:
            self.logger.error("❌ CDL Pre-flight validation failed: %s", e)
            raise RuntimeError(f"Character validation failed: {e}")
    
    async def initialize_knowledge_router(self):
        """Initialize semantic knowledge router for structured factual intelligence."""
        try:
            from src.knowledge.semantic_router import create_semantic_knowledge_router
            
            # Wait for postgres pool to be available (max 30 seconds)
            max_wait = 30
            wait_interval = 1
            waited = 0
            
            while not self.postgres_pool and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Check if postgres pool is available
            if not self.postgres_pool:
                self.logger.warning("⚠️ PostgreSQL pool not available after %ds - knowledge router disabled", max_wait)
                return
            
            # Create knowledge router with all data stores
            self.knowledge_router = create_semantic_knowledge_router(
                postgres_pool=self.postgres_pool,
                qdrant_client=getattr(self.memory_manager, 'client', None) if self.memory_manager else None,
                influx_client=None  # InfluxDB integration optional for Phase 1
            )
            
            self.logger.info("✅ Semantic Knowledge Router initialized with multi-modal intelligence")
            
            # Update character system with knowledge_router if it exists
            if self.character_system and self.knowledge_router:
                self.character_system.knowledge_router = self.knowledge_router
                self.logger.info("✅ Character system updated with knowledge router integration")
            
        except Exception as e:
            self.logger.error(f"❌ Knowledge router initialization failed: {e}")
            # Don't raise - knowledge router is optional enhancement
    
    async def initialize_transaction_manager(self):
        """Initialize roleplay transaction manager for stateful interactions."""
        try:
            from src.roleplay.transaction_manager import create_transaction_manager
            
            # Wait for postgres pool to be available (max 30 seconds)
            max_wait = 30
            wait_interval = 1
            waited = 0
            
            while not self.postgres_pool and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Check if postgres pool is available
            if not self.postgres_pool:
                self.logger.warning("⚠️ PostgreSQL pool not available - transaction manager disabled")
                self.transaction_manager = None
                return
            
            # Create transaction manager
            self.transaction_manager = create_transaction_manager(db_pool=self.postgres_pool)
            
            # Mark as initialized (pool already set)
            self.transaction_manager._initialized = True
            
            self.logger.info("✅ Transaction Manager initialized for roleplay interactions")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Transaction manager initialization failed: {e}")
            self.transaction_manager = None
            # Don't raise - transaction manager is optional for roleplay bots
    
    async def initialize_workflow_manager(self):
        """Initialize workflow manager for declarative transaction patterns."""
        try:
            from src.roleplay.workflow_manager import WorkflowManager
            import os
            
            # Wait for dependencies (max 30 seconds)
            max_wait = 30
            wait_interval = 1
            waited = 0
            
            while (not self.transaction_manager or not self.llm_client) and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Check if dependencies are available
            if not self.transaction_manager:
                self.logger.warning("⚠️ TransactionManager not available - workflow manager disabled")
                self.workflow_manager = None
                return
            
            if not self.llm_client:
                self.logger.warning("⚠️ LLM client not available - workflow manager will skip LLM validation")
            
            # Create workflow manager
            self.workflow_manager = WorkflowManager(
                transaction_manager=self.transaction_manager,
                llm_client=self.llm_client
            )
            
            # Load workflows for this character using bot name from environment
            bot_name = os.getenv("DISCORD_BOT_NAME", "unknown").lower()
            if bot_name and bot_name != "unknown":
                loaded = await self.workflow_manager.load_workflows_for_character(bot_name)
                if loaded:
                    workflow_count = self.workflow_manager.get_workflow_count(bot_name)
                    self.logger.info(
                        f"✅ Workflow Manager initialized with {workflow_count} workflow(s) "
                        f"for character '{bot_name}'"
                    )
                else:
                    self.logger.info(
                        f"ℹ️ Workflow Manager initialized (no workflows configured for character '{bot_name}')"
                    )
            else:
                self.logger.info("ℹ️ Workflow Manager initialized (no DISCORD_BOT_NAME set)")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Workflow manager initialization failed: {e}")
            self.workflow_manager = None
            # Don't raise - workflow manager is optional
    
    def initialize_hybrid_emotion_analyzer(self):
        """🚀 FAST TRACK: Initialize hybrid emotion analyzer for optimal performance"""
        try:
            from src.intelligence.hybrid_emotion_analyzer import create_hybrid_emotion_analyzer
            self.hybrid_emotion_analyzer = create_hybrid_emotion_analyzer()
            self.logger.info("✅ FAST TRACK: Hybrid Emotion Analyzer (RoBERTa+VADER+Keywords) initialized")
        except Exception as e:
            self.logger.warning("⚠️ Hybrid emotion analyzer failed: %s", str(e))
            # Fallback to enhanced vector emotion analyzer
            try:
                from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
                self.hybrid_emotion_analyzer = EnhancedVectorEmotionAnalyzer(
                    vector_memory_manager=self.memory_manager
                )
                self.logger.info("✅ Enhanced Vector Emotion Analyzer initialized as fallback")
            except Exception as fallback_e:
                self.logger.error("❌ No emotion analyzer available: %s", fallback_e)
                self.hybrid_emotion_analyzer = None
    
    # LLM Tool Integration removed as part of memory system simplification
    # Complex memory tools have been removed to focus on core vector memory functionality
            
    # REMOVED: Legacy memory optimizer - replaced by vector-native memory system

    async def initialize_conversation_intelligence(self):
        """Initialize Advanced Thread Management and Conversation Intelligence components asynchronously."""
        try:
            # Advanced Thread Manager removed as phantom feature
            self.thread_manager = None
            self.logger.info("✅ Advanced Thread Manager removed (phantom feature)")

            # Initialize Phase 4.3: Proactive Engagement Engine
            if not hasattr(self, 'engagement_engine') or self.engagement_engine is None:
                try:
                    from src.conversation.engagement_protocol import create_engagement_engine
                    
                    # Create with available integrations using factory pattern
                    # Initialize HYBRID emotion analyzer for engagement engine (FAST TRACK!)
                    emotion_analyzer = None
                    try:
                        from src.intelligence.hybrid_emotion_analyzer import create_hybrid_emotion_analyzer
                        emotion_analyzer = create_hybrid_emotion_analyzer()
                        self.logger.info("✅ FAST TRACK: Hybrid Emotion Analyzer (RoBERTa+VADER) initialized")
                    except Exception as e:
                        self.logger.warning("Hybrid emotion analyzer not available: %s", str(e))
                        
                        # Fallback to enhanced vector emotion analyzer
                        try:
                            from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
                            if hasattr(self, 'memory_manager') and self.memory_manager:
                                emotion_analyzer = EnhancedVectorEmotionAnalyzer(
                                    vector_memory_manager=self.memory_manager
                                )
                                self.logger.info("✅ Enhanced Vector Emotion Analyzer initialized for engagement engine")
                        except Exception as fallback_e:
                            self.logger.warning("Enhanced emotion analyzer not available for engagement: %s", fallback_e)
                    
                    self.engagement_engine = await create_engagement_engine(
                        engagement_engine_type=os.getenv("ENGAGEMENT_ENGINE_TYPE", "full"),
                        thread_manager=getattr(self, 'thread_manager', None),
                        memory_moments=None,  # Memory moments removed (phantom feature)
                        emotional_engine=emotion_analyzer or (getattr(self.phase2_integration, 'emotional_context_engine', None) if hasattr(self, 'phase2_integration') else None),
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

    async def _integrate_advanced_components(self):
        """🚀 CRITICAL INTEGRATION: Attach advanced conversation components to Discord bot instance.
        
        This method bridges the gap between initialized components in bot_core and 
        the event handlers which expect them on the Discord bot instance.
        
        Without this integration, advanced features are initialized but dormant.
        """
        try:
            # Small delay to ensure Phase 4 components are fully initialized
            await asyncio.sleep(2)
            
            self.logger.info("🔗 Integrating advanced conversation components with Discord bot...")
            
            # Phase 3: Context Switch Detection & Empathy
            if hasattr(self, 'context_switch_detector') and self.context_switch_detector:
                self.bot.context_switch_detector = self.context_switch_detector
                self.logger.info("✅ Context Switch Detector integrated with Discord bot")
            else:
                self.logger.warning("⚠️ Context Switch Detector not available for integration")
                
            if hasattr(self, 'empathy_calibrator') and self.empathy_calibrator:
                self.bot.empathy_calibrator = self.empathy_calibrator
                self.logger.info("✅ Empathy Calibrator integrated with Discord bot")
            else:
                self.logger.warning("⚠️ Empathy Calibrator not available for integration")
            
            # Phase 4.1: Memory-Triggered Moments - REMOVED (phantom feature)
            # Memory moments removed - vector memory provides conversation continuity
            self.logger.debug("💭 Memory-Triggered Moments removed (phantom feature) - vector memory provides this functionality")
            
            # Phase 4.2: Advanced Thread Manager - REMOVED (phantom feature)
            # Thread manager was removed as phantom feature - no integration needed
            self.logger.debug("🧵 Advanced Thread Manager removed (phantom feature) - skipping integration")
            
            # Phase 4.3: Proactive Engagement Engine
            if hasattr(self, 'engagement_engine') and self.engagement_engine:
                self.bot.engagement_engine = self.engagement_engine
                self.logger.info("✅ Proactive Engagement Engine integrated with Discord bot")
            else:
                self.logger.warning("⚠️ Proactive Engagement Engine not available for integration")
            
            # Additional components for comprehensive integration
            if hasattr(self, 'dynamic_personality_profiler') and self.dynamic_personality_profiler:
                self.bot.dynamic_personality_profiler = self.dynamic_personality_profiler
                self.logger.info("✅ Dynamic Personality Profiler integrated with Discord bot")
                
            if hasattr(self, 'conversation_manager') and self.conversation_manager:
                self.bot.conversation_manager = self.conversation_manager
                self.logger.info("✅ Concurrent Conversation Manager integrated with Discord bot")
                
            # Log final integration status
            active_features = []
            if hasattr(self.bot, 'context_switch_detector') and self.bot.context_switch_detector:
                active_features.append("Context Switch Detection")
            if hasattr(self.bot, 'engagement_engine') and self.bot.engagement_engine:
                active_features.append("Proactive Engagement")
            # Memory-Triggered Moments removed (phantom feature)
            # Advanced Thread Manager removed (phantom feature)
                
            if active_features:
                self.logger.info(f"🎉 Advanced Conversation Features ACTIVE: {', '.join(active_features)}")
            else:
                self.logger.warning("⚠️ No advanced conversation features available - using basic conversation mode")
                
        except Exception as e:
            self.logger.error(f"Failed to integrate advanced components: {e}")
            self.logger.warning("Bot will continue with basic conversation features only")

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
        # Vector-native personality analysis replaces legacy components
        self.logger.info("📊 Using vector-native personality analysis (CDL + embedding intelligence)")

        # Initialize Dynamic Personality Profiler
        self.logger.info("🎭 Initializing Dynamic Personality Profiler...")
        try:
            # Dynamic personality profiling - always enabled in development!
            from src.intelligence.dynamic_personality_profiler import (
                PersistentDynamicPersonalityProfiler,
            )

            self.dynamic_personality_profiler = PersistentDynamicPersonalityProfiler()
            self.logger.info("✅ Dynamic personality profiler initialized (always active)")

        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic personality profiler: {e}")
            self.logger.warning("⚠️ Continuing without dynamic personality profiling features")
            self.dynamic_personality_profiler = None

        # Initialize Predictive Emotional Intelligence
        self.logger.info("🎯 Initializing Predictive Emotional Intelligence...")
        try:
            # Use simplified emotion integration - vector-native architecture
            from src.intelligence.simplified_emotion_manager import create_simplified_emotion_manager

            self.logger.info("🧠 Emotional Intelligence Mode: Simplified Vector-Native System")

            # Create simplified emotion manager with vector memory integration
            vector_memory_manager = getattr(self, "vector_memory_manager", None)
            
            self.simplified_emotion_manager = create_simplified_emotion_manager(vector_memory_manager)
            self.logger.info("✅ Simplified Emotion Manager initialized with Enhanced Vector system")

            # For backward compatibility, also set as phase2_integration
            # This allows existing code to work during transition
            self.phase2_integration = self.simplified_emotion_manager

            # Memory manager emotion integration (if available)
            if (
                hasattr(self, "memory_manager")
                and self.memory_manager
                and hasattr(self.memory_manager, "emotion_manager")
                and self.memory_manager.emotion_manager
            ):
                self.memory_manager.emotion_manager.simplified_emotion_manager = self.simplified_emotion_manager
                self.logger.info("✅ Updated memory manager's emotion manager with Simplified system")

        except Exception as e:
            self.logger.error("Failed to initialize simplified emotional intelligence: %s", e)
            self.logger.warning("⚠️ Continuing without emotional intelligence features")
            # Set fallback
            self.simplified_emotion_manager = None
            self.phase2_integration = None

        # Vector-native memory networks replace Phase 3 memory networks
        self.logger.info("🕸️ Memory Networks: Using Vector-Native Qdrant Intelligence")

        # Initialize Phase 3 Advanced Intelligence Components
        self.logger.info("🧠 Initializing Phase 3: Advanced Intelligence Components...")
        try:
            from src.intelligence.context_switch_detector import ContextSwitchDetector
            from src.intelligence.empathy_calibrator import EmpathyCalibrator

            # Initialize ContextSwitchDetector
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.context_switch_detector = ContextSwitchDetector(vector_memory_store=self.memory_manager)
                self.logger.info("✅ Phase 3: ContextSwitchDetector initialized with memory manager")
                
                # Log thresholds and configuration for debugging
                topic_threshold = self.context_switch_detector.topic_shift_threshold
                emotional_threshold = self.context_switch_detector.emotional_shift_threshold
                mode_threshold = self.context_switch_detector.conversation_mode_threshold
                urgency_threshold = self.context_switch_detector.urgency_change_threshold
                
                self.logger.info("✅ Phase 3: ContextSwitchDetector thresholds: topic=%s, emotional=%s, mode=%s, urgency=%s",
                                topic_threshold, emotional_threshold, mode_threshold, urgency_threshold)
                
                # Make sure it's properly attached to bot instance for handlers
                if hasattr(self, 'bot') and self.bot:
                    self.bot.context_switch_detector = self.context_switch_detector
                    self.logger.info("✅ Phase 3: ContextSwitchDetector attached to bot instance")
            else:
                self.context_switch_detector = None
                self.logger.warning("⚠️ Cannot initialize ContextSwitchDetector - missing memory manager")

            # Initialize EmpathyCalibrator
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.empathy_calibrator = EmpathyCalibrator(vector_memory_store=self.memory_manager)
                self.logger.info("✅ Phase 3: EmpathyCalibrator initialized")
            else:
                self.empathy_calibrator = None
                self.logger.warning("⚠️ Cannot initialize EmpathyCalibrator - missing memory manager")

        except Exception as e:
            self.logger.error(f"Failed to initialize Phase 3 advanced intelligence components: {e}")
            self.logger.warning("⚠️ Continuing without Phase 3 advanced intelligence features")
            self.context_switch_detector = None
            self.empathy_calibrator = None

        # Initialize Phase 4.1: Memory-Triggered Personality Moments - REMOVED (phantom feature)
        self.logger.info("💭 Phase 4.1: Memory-Triggered Personality Moments removed (phantom feature)")
        self.memory_moments = None
        self.logger.debug("🧠 Memory-triggered personality moments removed - vector memory provides this functionality")

        # Initialize Phase 4.2: Advanced Thread Manager
        # Phase 4.2: Advanced Thread Manager removed as phantom feature
        self.logger.info("🧵 Phase 4.2: Advanced Thread Manager removed (phantom feature)")
        self._thread_manager_task = None
        self.thread_manager = None
        self.logger.info("✅ Phase 4.2: Advanced Thread Manager removed")

        # Initialize Phase 4.3: Proactive Engagement Engine
        self.logger.info("⚡ Initializing Phase 4.3: Proactive Engagement Engine...")
        try:
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
        """Initialize vector-native conversation context (Redis removed for simplification)."""
        self.logger.info("Using vector-native conversation context (Redis disabled)")

        # Vector memory system provides superior semantic context vs Redis chronological cache
        self.logger.info("✅ Vector-native conversation context enabled (Redis cache disabled)")

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
                conversation_cache=None,  # Removed phantom feature - using vector memory
                emotion_manager=emotion_mgr,
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
        """Initialize voice functionality using the factory pattern."""
        voice_service_type = os.getenv("VOICE_SERVICE_TYPE", "discord_elevenlabs")
        
        # Voice support always enabled in development!
        voice_support_enabled = True
        
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
        """Initialize the production optimization system."""
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

    async def initialize_postgres_pool(self):
        """
        Initialize PostgreSQL connection pool using centralized pool manager.
        
        This runs asynchronously and is required for the knowledge_router.
        """
        try:
            self.logger.info("🐘 Initializing PostgreSQL connection pool via centralized manager...")
            
            # Use centralized pool manager instead of creating our own pool
            from src.database.postgres_pool_manager import get_postgres_pool
            
            self.postgres_pool = await get_postgres_pool()
            
            if self.postgres_pool:
                # Store configuration for reference
                self.postgres_config = {
                    "host": os.getenv("POSTGRES_HOST", "whisperengine-multi-postgres"),
                    "port": int(os.getenv("POSTGRES_PORT", "5432")),
                    "database": os.getenv("POSTGRES_DB", "whisperengine"),
                    "user": os.getenv("POSTGRES_USER", "whisperengine")
                }
                
                self.logger.info("✅ PostgreSQL pool initialized via centralized manager: %s:%s/%s",
                               self.postgres_config["host"], self.postgres_config["port"], self.postgres_config["database"])
                return True
            else:
                self.logger.error("❌ Failed to get PostgreSQL pool from centralized manager")
                return False
            
        except Exception as e:
            self.logger.error("❌ Failed to initialize PostgreSQL pool: %s", str(e))
            self.logger.warning("⚠️ Bot will continue without semantic knowledge graph features")
            self.postgres_pool = None
            self.postgres_config = None
            return False


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

    async def initialize_conversation_manager(self):
        """Initialize conversation processing - using simple, reliable AsyncIO patterns."""
        # Simple async processing - no complex concurrent manager needed
        self.conversation_manager = None
        self.logger.info("✅ Using simple AsyncIO gather for reliable parallel processing")

    def initialize_all(self):
        """Initialize all bot components in the correct order."""
        self.logger.info("Starting bot core initialization...")

        # Core components
        self.initialize_bot()
        self.initialize_llm_client()
        self.initialize_memory_system()
        self.initialize_character_system()
        self.initialize_hybrid_emotion_analyzer()
        
        # LLM Tool Integration removed - memory system simplified

        # Schedule async initialization of PostgreSQL pool (required for knowledge router)
        asyncio.create_task(self.initialize_postgres_pool())
        
        # Schedule async initialization of enhanced CDL manager (requires postgres pool)
        # Adds rich character data (relationships, behavioral triggers, speech patterns)
        asyncio.create_task(self.initialize_enhanced_cdl_manager())
        
        # Schedule async initialization of Phase 4 components
        asyncio.create_task(self.initialize_conversation_intelligence())
        
        # Schedule async initialization of knowledge router (requires postgres pool)
        # Note: This will wait for postgres_pool to be available
        asyncio.create_task(self.initialize_knowledge_router())
        
        # Schedule async initialization of transaction manager (requires postgres pool)
        # Used for roleplay bots with stateful interactions (bartenders, shops, quests)
        asyncio.create_task(self.initialize_transaction_manager())
        
        # Schedule async initialization of workflow manager (requires transaction_manager + llm_client)
        # Loads YAML workflow files for declarative transaction patterns
        asyncio.create_task(self.initialize_workflow_manager())

        # Supporting systems
        self.initialize_conversation_cache()
        self.initialize_health_monitor()
        self.initialize_image_processor()
        self.initialize_supporting_systems()

        # Optional enhancements
        self.initialize_ai_enhancements()
        self.initialize_voice_system()
        self.initialize_production_optimization()
        # PostgreSQL initialization removed - using vector-native storage only

        # Schedule async initialization of concurrent conversation manager
        asyncio.create_task(self.initialize_conversation_manager())

        # 🚀 CRITICAL FIX: Attach advanced conversation components to Discord bot instance
        # This enables the sophisticated conversation features in event handlers
        asyncio.create_task(self._integrate_advanced_components())

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

        # Use the standard memory manager (vector-native architecture)
        return {
            "bot": self.bot,
            "llm_client": self.llm_client,
            "memory_manager": self.memory_manager,
            "llm_tool_manager": None,  # LLM tool manager removed in memory system simplification
            "image_processor": self.image_processor,
            "health_monitor": self.health_monitor,
            "voice_manager": self.voice_manager,
            "shutdown_manager": self.shutdown_manager,
            "heartbeat_monitor": self.heartbeat_monitor,
            "conversation_history": self.conversation_history,
            "postgres_config": self.postgres_config,
            "dynamic_personality_profiler": getattr(self, "dynamic_personality_profiler", None),
            "phase2_integration": self.phase2_integration,
            "context_switch_detector": getattr(self, "context_switch_detector", None),
            "empathy_calibrator": getattr(self, "empathy_calibrator", None),
            "memory_moments": getattr(self, "memory_moments", None),
            "production_adapter": self.production_adapter,
            "conversation_manager": self.conversation_manager,
        }
