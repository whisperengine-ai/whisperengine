"""
Shared message processing service for WhisperEngine.

This module provides platform-agnostic message processing that can be used by:
- Discord bot handlers
- External HTTP API endpoints 
- Future platform integrations

Core design principle: Abstract platform-specific details while preserving 
the sophisticated AI processing pipeline including memory, emotions, CDL character 
integration, and context management.
"""

import asyncio
import json
import logging
import os
import re
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity
from src.utils.bot_name_utils import get_normalized_bot_name_from_env
from src.utils.mystical_symbol_detector import get_mystical_symbol_detector
from src.adapters.platform_adapters import (
    create_discord_message_adapter,
    create_discord_attachment_adapters
)
from src.prompts.prompt_assembler import create_prompt_assembler
from src.prompts.prompt_components import (
    create_core_system_component,
    create_memory_component,
    create_anti_hallucination_component,
    create_guidance_component,
    create_user_facts_component,
    PromptComponent,
    PromptComponentType,
    is_component_enabled  # Feature flag check for early-exit optimization
)

# Relationship Intelligence components
from src.relationships.evolution_engine import create_relationship_evolution_engine
from src.relationships.trust_recovery import create_trust_recovery_system

# Emoji Intelligence component
from src.intelligence.database_emoji_selector import create_database_emoji_selector

# Emotional Adaptation component
from src.intelligence.emotional_context_engine import EmotionalContextEngine, EmotionalContext, EmotionalState

# Phase 2c: Unified Query Classification for single authoritative classification
from src.memory.unified_query_classification import (
    create_unified_query_classifier,
    UnifiedQueryClassifier,
    VectorStrategy as UnifiedVectorStrategy,
)

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Platform-agnostic message context."""
    user_id: str
    content: str
    original_content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    platform: str = "unknown"  # "discord", "api", etc.
    channel_id: Optional[str] = None
    channel_type: Optional[str] = None  # "dm", "guild", etc.
    metadata: Optional[Dict[str, Any]] = None
    # Platform-specific context for features like typing indicators
    platform_context: Optional[Any] = None  # Discord channel, HTTP response object, etc.
    # Metadata control for API responses
    metadata_level: str = "basic"  # "basic", "standard", "extended" - controls API response payload size

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Result of message processing."""
    response: str
    success: bool = True
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    llm_time_ms: Optional[int] = None  # LLM-specific processing time
    memory_stored: bool = False
    metadata: Optional[Dict[str, Any]] = None
    silent_ignore: bool = False  # If True, no response should be sent (e.g., mystical symbols)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MessageProcessor:
    """
    Core message processing engine for WhisperEngine.
    
    Abstracts the sophisticated AI processing pipeline from platform-specific
    implementations. Handles security, memory, emotions, CDL character integration,
    and response generation in a platform-agnostic way.
    """

    def __init__(self, bot_core, memory_manager, llm_client, security_validator=None, 
                 emoji_intelligence=None, image_processor=None, conversation_cache=None):
        """Initialize the message processor with core components."""
        self.bot_core = bot_core
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.security_validator = security_validator
        self.emoji_intelligence = emoji_intelligence
        self.image_processor = image_processor
        self.conversation_cache = conversation_cache
        
        # Phase 2c: Initialize unified query classifier for single authoritative classification
        # PERFORMANCE: Disabled by default due to significant overhead (~2x processing time)
        # Enable via ENABLE_LLM_TOOL_CALLING=true environment variable
        # Factory function returns None if disabled, so we only check the flag in one place
        try:
            self._unified_query_classifier = create_unified_query_classifier()
            if self._unified_query_classifier is not None:
                logger.info("✅ UNIFIED: MessageProcessor using UnifiedQueryClassifier for routing (tool calling enabled)")
            else:
                logger.info("⚠️  UNIFIED: UnifiedQueryClassifier disabled (set ENABLE_LLM_TOOL_CALLING=true to enable)")
        except Exception as e:
            logger.warning("⚠️  UNIFIED: Failed to initialize UnifiedQueryClassifier: %s", str(e))
            self._unified_query_classifier = None
        
        # Phase 5: Initialize temporal intelligence with PostgreSQL integration
        # Temporal intelligence is now permanently enabled (no feature flag)
        self.temporal_client = None
        self.confidence_analyzer = None
        
        # Initialize temporal intelligence (always enabled)
        try:
            from src.temporal.temporal_protocol import create_temporal_intelligence_system
            
            # Pass knowledge_router for actual PostgreSQL relationship scores
            knowledge_router = getattr(bot_core, 'knowledge_router', None) if bot_core else None
            self.temporal_client, self.confidence_analyzer = create_temporal_intelligence_system(
                knowledge_router=knowledge_router
            )
            logger.info("Temporal intelligence initialized (postgres_integration: %s)", 
                       knowledge_router is not None)
        except ImportError:
            logger.warning("Temporal intelligence not available - install influxdb-client")
        
        # STAGE 2: Enhanced AI Ethics for Character Learning
        self.enhanced_ai_ethics = None
        
        try:
            from src.ethics.enhanced_ai_ethics_integrator import create_enhanced_ai_ethics_integrator
            from src.ethics.attachment_monitoring import create_attachment_monitoring_system
            
            # Create attachment monitor with temporal client for interaction frequency analysis
            attachment_monitor = None
            if self.temporal_client:
                attachment_monitor = create_attachment_monitoring_system(
                    temporal_client=self.temporal_client
                )
                logger.info("🛡️ Attachment monitoring created with temporal intelligence integration")
            else:
                logger.warning("⚠️ Attachment monitoring created without temporal client - frequency analysis limited")
                attachment_monitor = create_attachment_monitoring_system()
            
            # Initialize enhanced AI ethics with properly configured attachment monitor
            self.enhanced_ai_ethics = create_enhanced_ai_ethics_integrator(
                attachment_monitor=attachment_monitor,
                ethics_integration=None   # Will use default
            )
            logger.info("🛡️ Enhanced AI Ethics initialized with attachment monitoring and learning ethics")
        except ImportError as e:
            logger.warning("Enhanced AI Ethics not available: %s", e)
        
        # TrendWise Adaptive Learning: Initialize trend analysis (ConfidenceAdapter removed)
        self.trend_analyzer = None
        
        if self.temporal_client:
            try:
                from src.analytics.trend_analyzer import create_trend_analyzer
                
                self.trend_analyzer = create_trend_analyzer(self.temporal_client)
                logger.info("TrendWise Adaptive Learning: Trend analysis initialized")
            except ImportError as e:
                logger.warning("TrendWise components not available: %s", e)
                self.trend_analyzer = None
        
        # Relationship Intelligence: Lazy initialization (postgres_pool may not be ready yet)
        self.relationship_engine = None
        self.trust_recovery = None
        self._relationship_init_attempted = False  # Track if we've tried initializing
        
        # Learning Intelligence Orchestrator: Feature-flagged initialization (Sprint 6 experimental)
        # DISABLED by default (35-40MB memory per bot, never used in production)
        # Enable via: ENABLE_SPRINT_6_ORCHESTRATION=true
        self.learning_orchestrator = None
        self.predictive_engine = None
        self.learning_pipeline = None
        
        enable_sprint_6 = os.getenv('ENABLE_SPRINT_6_ORCHESTRATION', 'false').lower() == 'true'
        
        if enable_sprint_6 and self.temporal_client:
            try:
                from src.orchestration.learning_orchestrator import LearningOrchestrator
                from src.adaptation.predictive_engine import PredictiveAdaptationEngine
                from src.pipeline.learning_manager import LearningPipelineManager
                
                # Initialize Learning Intelligence components with available adaptive learning dependencies
                self.learning_orchestrator = LearningOrchestrator(
                    trend_analyzer=self.trend_analyzer,
                    confidence_adapter=None,  # ConfidenceAdapter removed
                    memory_manager=self.memory_manager,
                    temporal_client=self.temporal_client,
                    postgres_pool=getattr(bot_core, 'postgres_pool', None) if bot_core else None
                )
                
                # Pass dependencies to Predictive Engine
                self.predictive_engine = PredictiveAdaptationEngine(
                    trend_analyzer=self.trend_analyzer,
                    confidence_adapter=None,  # ConfidenceAdapter removed
                    temporal_client=self.temporal_client,
                    memory_manager=self.memory_manager
                )
                self.learning_pipeline = LearningPipelineManager()
                
                logger.info("Learning Intelligence Orchestrator: Learning coordination components initialized (Sprint 6 experimental)")
            except ImportError as e:
                logger.warning("Learning Intelligence Orchestrator components not available: %s", e)
                self.learning_orchestrator = None
                self.predictive_engine = None
                self.learning_pipeline = None
        
        # Shared emotion analyzer for preventing RoBERTa race conditions
        self._shared_emotion_analyzer = None
        self._shared_analyzer_lock = asyncio.Lock()
        
        # Stance Analyzer for filtering emotions by speaker perspective
        self._stance_analyzer = None
        try:
            from src.intelligence.spacy_stance_analyzer import create_stance_analyzer
            self._stance_analyzer = create_stance_analyzer()
            logger.info("✅ Stance Analyzer initialized (uses shared spaCy singleton)")
        except ImportError as e:
            logger.warning("Stance Analyzer not available: %s", e)
            self._stance_analyzer = None
        
        # Character Emotional State Manager: Analytics-only tracking (NOT used in prompts)
        # RE-ENABLED for historical state tracking and quality analysis reports
        # Tracks bot's internal emotional state evolution without injecting into prompts
        # (CDL personality system handles prompt-level emotional expression)
        self.character_state_manager = None
        enable_state_analytics = os.getenv('ENABLE_CHARACTER_STATE_ANALYTICS', 'false').lower() == 'true'
        
        if enable_state_analytics and self.temporal_client:
            try:
                from src.intelligence.character_emotional_state_v2 import create_character_emotional_state_manager
                self.character_state_manager = create_character_emotional_state_manager()
                logger.info("🎭 Character State Analytics: Enabled for historical tracking (InfluxDB-only, no prompt injection)")
            except ImportError as e:
                logger.warning("Character State Manager not available: %s", e)
                self.character_state_manager = None
        elif enable_state_analytics and not self.temporal_client:
            logger.warning("⚠️ Character State Analytics: Requires InfluxDB (ENABLE_CHARACTER_STATE_ANALYTICS=true but no temporal_client)")
        else:
            logger.debug("Character State Analytics: Disabled (set ENABLE_CHARACTER_STATE_ANALYTICS=true to enable)")
        
        # Initialize fidelity metrics collector for performance tracking
        try:
            from src.monitoring.fidelity_metrics_collector import get_fidelity_metrics_collector
            self.fidelity_metrics = get_fidelity_metrics_collector()
            logger.debug("Fidelity metrics collector initialized")
        except ImportError:
            logger.warning("Fidelity metrics collector not available")
            self.fidelity_metrics = None
        
        # ML Shadow Mode: Initialize predictor and logger for ML predictions
        self.ml_predictor = None
        self.ml_shadow_logger = None
        
        if self.temporal_client:
            try:
                from src.ml import create_response_strategy_predictor, create_ml_shadow_logger
                
                self.ml_predictor = create_response_strategy_predictor(
                    influxdb_client=self.temporal_client
                )
                self.ml_shadow_logger = create_ml_shadow_logger(
                    influxdb_client=self.temporal_client
                )
                
                if self.ml_shadow_logger:
                    logger.info("✅ ML Shadow Mode: Predictor and logger initialized")
                else:
                    logger.debug("ML Shadow Mode: Disabled (ENABLE_ML_SHADOW_MODE=false)")
            except ImportError as e:
                logger.debug("ML Shadow Mode: Not available - %s", e)
        
        # REMOVED: Character Emotional State Manager (overengineered - CDL personality is sufficient)
        # Was tracking bot's own emotional state with 11-emotion biochemical modeling
        # Added 100-150ms overhead per message with no clear value
        
        # Unified Character Intelligence Coordinator: PHASE 4A Integration
        self.character_intelligence_coordinator = None
        
        try:
            from src.characters.learning.unified_character_intelligence_coordinator import UnifiedCharacterIntelligenceCoordinator
            
            # Try to initialize Character Vector Episodic Intelligence
            character_name = get_normalized_bot_name_from_env()
            character_episodic_intelligence = None
            
            try:
                from src.characters.learning.character_vector_episodic_intelligence import create_character_vector_episodic_intelligence
                
                if character_name and self.memory_manager:
                    # Create episodic intelligence using existing Qdrant client from memory manager
                    qdrant_client = getattr(self.memory_manager, 'vector_store', None)
                    if qdrant_client and hasattr(qdrant_client, 'client'):
                        qdrant_client = qdrant_client.client
                    else:
                        qdrant_client = None
                    
                    character_episodic_intelligence = create_character_vector_episodic_intelligence(
                        qdrant_client=qdrant_client
                    )
                    logger.info("🧠 Character Vector Episodic Intelligence initialized for %s", character_name)
            
            except ImportError as e:
                logger.warning("🧠 Character Vector Episodic Intelligence not available: %s", e)
                character_episodic_intelligence = None
            
            # Try to initialize Character Temporal Evolution Analyzer (PHASE 2)
            character_temporal_evolution_analyzer = None
            
            try:
                # Import the module first to check availability
                import src.characters.learning.character_temporal_evolution_analyzer as temporal_module
                from src.temporal.temporal_intelligence_client import get_temporal_client
                
                # Get the class from the module
                if hasattr(temporal_module, 'CharacterTemporalEvolutionAnalyzer'):
                    TemporalAnalyzer = temporal_module.CharacterTemporalEvolutionAnalyzer
                    
                    # Initialize temporal client for analyzer
                    temporal_client = get_temporal_client()
                    character_temporal_evolution_analyzer = TemporalAnalyzer(temporal_client=temporal_client)
                    logger.info("🧠 Character Temporal Evolution Analyzer initialized for %s", character_name)
                else:
                    logger.warning("🧠 CharacterTemporalEvolutionAnalyzer class not found in module")
            
            except ImportError as e:
                logger.warning("🧠 Character Temporal Evolution Analyzer not available: %s", e)
                character_temporal_evolution_analyzer = None
            
            self.character_intelligence_coordinator = UnifiedCharacterIntelligenceCoordinator(
                memory_manager=self.memory_manager,
                character_episodic_intelligence=character_episodic_intelligence,
                character_temporal_evolution_analyzer=character_temporal_evolution_analyzer
            )
            logger.info("🧠 Unified Character Intelligence Coordinator initialized")
            
            # Initialize CDL Database Manager for character performance analysis
            self.cdl_database_manager = None
            try:
                from src.database.cdl_database import CDLDatabaseManager
                self.cdl_database_manager = CDLDatabaseManager()
                # Pool initialization will be done lazily when needed
                logger.info("📊 CDL Database Manager initialized")
            except ImportError as e:
                logger.warning("CDL Database Manager not available: %s", e)
            
            # Memory Effectiveness Analyzer disabled - was causing production failures
            # TODO: Re-enable when protocol interface is fully implemented
            self.memory_effectiveness_analyzer = None
            
            # Initialize Character Learning Moment Detector for user experience enhancement
            try:
                from src.characters.learning.character_learning_moment_detector import create_character_learning_moment_detector
                self.learning_moment_detector = create_character_learning_moment_detector(
                    character_intelligence_coordinator=self.character_intelligence_coordinator,
                    emotion_analyzer=self._shared_emotion_analyzer,
                    memory_manager=self.memory_manager
                )
                logger.info("🌟 Character Learning Moment Detector initialized")
            except ImportError as e:
                logger.warning("Learning moment detector not available: %s", e)
                self.learning_moment_detector = None
                
        except ImportError as e:
            logger.warning("Character intelligence coordinator not available: %s", e)
            self.learning_moment_detector = None
        
        # Database Emoji Selector: Lazy initialization (postgres_pool may not be ready yet)
        self.emoji_selector = None
        self._emoji_selector_init_attempted = False  # Track if we've tried to initialize
        self._try_initialize_emoji_selector()  # Try to initialize now (may succeed or defer)
        
        # Get character name for emoji selection
        self.character_name = get_normalized_bot_name_from_env()
        
        # Initialize Emotional Context Engine for tactical personality adaptation
        try:
            self.emotional_context_engine = EmotionalContextEngine()
            logger.info("🎭 Emotional Context Engine initialized - tactical Big Five adaptation enabled")
        except Exception as e:
            logger.warning("Emotional context engine initialization failed: %s", e)
            self.emotional_context_engine = None
        
        # REMOVED: ProactiveConversationEngagementEngine initialization
        # This was orphaned code - the method _process_proactive_engagement() was never called
        # after Phase 1-2 optimization (commit 9c17d66). The enrichment worker version
        # (src/enrichment/proactive_engagement_engine.py) is the active production system.
        
        # Character Learning Persistence: Layer 1 (PostgreSQL) - Lazy initialization
        self.character_insight_storage = None
        self.character_insight_extractor = None
        self._character_learning_initialized = False
        self._character_learning_lock = asyncio.Lock()
        
        # Track processing state for debugging
        self._last_security_validation = None
        self._last_emotional_context = None
    
    # REMOVED: _ensure_character_state_manager_initialized() method
    # Character emotional state tracking was overengineered and removed
    
    @staticmethod
    def _is_tool_worthy_query(message: str) -> bool:
        """
        Fast spaCy-based pre-filter to determine if message warrants tool calling.
        
        Uses lightweight spaCy linguistic analysis (much faster than full classifier):
        - Dependency parsing for question structure (WH-words with auxiliary verbs)
        - POS tagging for imperative/analytical verbs (list, show, tell, summarize)
        - Entity recognition for information-seeking queries
        
        Reuses the singleton spaCy instance from spacy_manager for efficiency.
        
        This eliminates ~90-95% of casual conversation overhead while
        preserving tool support for analytical queries.
        
        Args:
            message: User message content
            
        Returns:
            True if message appears to be an analytical/information query
        """
        # Skip very short messages - likely greetings/casual
        if len(message.split()) < 5:
            return False
        
        try:
            from src.nlp.spacy_manager import get_spacy_nlp
            
            # Get singleton spaCy instance (shared across all classifiers)
            nlp = get_spacy_nlp()
            if nlp is None:
                raise ImportError("spaCy not available")
            
            doc = nlp(message)
            
            # Rule 1: WH-question words with auxiliary verbs (what/how/when/where + do/have/can)
            # Example: "What foods have I mentioned?" → what(WP) + have(VBP) = tool-worthy
            wh_words = {'what', 'which', 'where', 'when', 'how', 'why', 'who'}
            aux_verbs = {'do', 'does', 'did', 'have', 'has', 'had', 'can', 'could', 'would', 'should'}
            
            has_wh = any(token.text.lower() in wh_words and token.tag_ in ['WP', 'WRB', 'WDT'] 
                        for token in doc)
            has_aux = any(token.text.lower() in aux_verbs and token.dep_ == 'aux' 
                         for token in doc)
            
            if has_wh and has_aux:
                return True
            
            # Rule 2: Imperative analytical verbs (tell, list, show, summarize, describe, explain)
            # Example: "Tell me everything about..." → tell(VB) at start = tool-worthy
            analytical_verbs = {'tell', 'list', 'show', 'summarize', 'describe', 'explain', 'give'}
            
            # Check if sentence starts with imperative verb (VB tag, no subject dependency)
            if doc[0].pos_ == 'VERB' and doc[0].lemma_ in analytical_verbs:
                return True
            
            # Rule 3: Quantifiers + mental state verbs (everything, all + know, remember, mention)
            # Example: "Do you remember everything I told you?" → quantifier + mental verb = tool-worthy
            has_quantifier = any(token.text.lower() in {'everything', 'all', 'any'} 
                                for token in doc)
            has_mental_verb = any(token.lemma_ in {'know', 'remember', 'mention', 'tell', 'say'} 
                                 and token.pos_ == 'VERB'
                                 for token in doc)
            
            if has_quantifier and has_mental_verb:
                return True
            
            # Rule 4: Deictic time references with memory verbs (when, before, last time + mention/tell/say)
            # Example: "When did I mention that?" → temporal + memory verb = tool-worthy
            temporal_words = {'when', 'before', 'last', 'previously', 'earlier', 'ago'}
            has_temporal = any(token.text.lower() in temporal_words or token.tag_ == 'WRB'
                              for token in doc)
            
            if has_temporal and has_mental_verb:
                return True
            
            return False
            
        except Exception as e:
            # Fallback to simple heuristic if spaCy fails
            logger.debug("spaCy pre-filter failed, using fallback: %s", e)
            message_lower = message.lower()
            return any(pattern in message_lower for pattern in [
                'tell me everything', 'list all', 'show me all', 
                'what do you know', 'have i mentioned', 'when did i'
            ])
    
    async def _ensure_cdl_database_pool_initialized(self):
        """
        Ensure CDL database manager pool is initialized (lazy initialization).
        
        Returns:
            bool: True if CDL database manager pool is available
        """
        if not self.cdl_database_manager:
            return False
            
        # Check if pool is already initialized
        if self.cdl_database_manager.pool:
            return True
            
        try:
            await self.cdl_database_manager.initialize_pool()
            logger.info("📊 CDL Database pool initialized (lazy)")
            return True
        except Exception as e:
            logger.warning("📊 CDL Database pool initialization failed: %s", e)
            return False
    
    def _try_initialize_emoji_selector(self):
        """
        Try to initialize database emoji selector (lazy initialization).
        Can be called multiple times - only initializes once when postgres_pool becomes available.
        """
        # Skip if already initialized or already failed
        if self.emoji_selector or self._emoji_selector_init_attempted:
            return
        
        try:
            # Get PostgreSQL pool from bot_core
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if postgres_pool:
                self.emoji_selector = create_database_emoji_selector(postgres_pool)
                logger.info("✨ Database Emoji Selector initialized - intelligent post-LLM emoji decoration enabled")
                self._emoji_selector_init_attempted = True
            else:
                # Don't mark as attempted yet - pool may become available later
                logger.debug("PostgreSQL pool not yet available - emoji selector initialization deferred")
        except Exception as e:
            logger.warning("Database emoji selector initialization failed: %s", e)
            self._emoji_selector_init_attempted = True  # Don't retry on failure
    
    async def _ensure_character_learning_persistence_initialized(self):
        """
        Ensure character learning persistence components are initialized (lazy initialization).
        
        Requires postgres_pool from bot_core. Only initializes once.
        
        Returns:
            bool: True if learning persistence is available
        """
        # Fast path: already initialized
        if self._character_learning_initialized:
            return (self.character_insight_storage is not None and 
                   self.character_insight_extractor is not None)
        
        # Use lock to prevent multiple simultaneous initialization attempts
        async with self._character_learning_lock:
            # Double-check after acquiring lock
            if self._character_learning_initialized:
                return (self.character_insight_storage is not None and 
                       self.character_insight_extractor is not None)
            
            try:
                from src.characters.learning.character_insight_storage import create_character_insight_storage
                from src.characters.learning.character_self_insight_extractor import create_character_self_insight_extractor
                
                # Check if postgres_pool is available (validates PostgreSQL is ready)
                postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
                if postgres_pool:
                    # Initialize storage layer with environment variables
                    # Note: create_character_insight_storage creates its own pool
                    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
                    postgres_port = int(os.getenv("POSTGRES_PORT", "5433"))
                    postgres_db = os.getenv("POSTGRES_DB", "whisperengine")
                    postgres_user = os.getenv("POSTGRES_USER", "whisperengine")
                    postgres_password = os.getenv("POSTGRES_PASSWORD", "whisperengine")
                    
                    self.character_insight_storage = await create_character_insight_storage(
                        postgres_host=postgres_host,
                        postgres_port=postgres_port,
                        postgres_db=postgres_db,
                        postgres_user=postgres_user,
                        postgres_password=postgres_password
                    )
                    
                    # Initialize extractor
                    self.character_insight_extractor = create_character_self_insight_extractor(
                        min_confidence=0.6,  # Only persist high-confidence insights
                        min_importance=4     # Only persist moderately important insights
                    )
                    
                    logger.info("📚 Character Learning Persistence initialized (Layer 1: PostgreSQL)")
                else:
                    logger.debug("📚 PostgreSQL pool not available - character learning persistence disabled")
                    self.character_insight_storage = None
                    self.character_insight_extractor = None
            
            except ImportError as e:
                logger.warning("📚 Character learning persistence not available: %s", e)
                self.character_insight_storage = None
                self.character_insight_extractor = None
            except Exception as e:
                logger.error("📚 Character learning persistence initialization failed: %s", e)
                self.character_insight_storage = None
                self.character_insight_extractor = None
            
            # Mark as initialized (even if failed, don't retry)
            self._character_learning_initialized = True
            
            return (self.character_insight_storage is not None and 
                   self.character_insight_extractor is not None)

    # ============================================================================
    # PHASE 3A: STRATEGIC COMPONENT CACHE HELPERS
    # ============================================================================
    # Cache helper methods for reading pre-computed strategic component results
    # from PostgreSQL cache tables. These support the background worker pattern
    # where expensive strategic computations happen async and are cached for fast
    # hot-path retrieval.
    # 
    # Target performance: <5ms cache read latency
    # ============================================================================

    async def _get_cached_memory_health(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached memory health analysis from PostgreSQL.
        
        Returns Dict with fields: memory_snapshot, avg_memory_age_hours,
        retrieval_frequency_trend, forgetting_risk_memories, computed_at
        
        Returns None if cache miss or stale (>5 minutes old).
        """
        import time
        start_time = time.perf_counter()
        cache_hit = False
        stale_cache = False
        
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                logger.debug("PostgreSQL pool not available for memory health cache")
                return None
            
            query = """
                SELECT memory_snapshot, avg_memory_age_hours, retrieval_frequency_trend,
                       forgetting_risk_memories, computed_at, expires_at
                FROM strategic_memory_health
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY computed_at DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    cache_hit = True
                    age_seconds = (datetime.now(timezone.utc) - row['computed_at']).total_seconds()
                    logger.debug(
                        f"✅ Memory health cache hit: {bot_name}/{user_id[:8]} "
                        f"(age: {age_seconds:.1f}s)"
                    )
                    
                    # Record cache metrics
                    query_latency_ms = (time.perf_counter() - start_time) * 1000
                    if self.temporal_client:
                        await self.temporal_client.record_strategic_cache_metrics(
                            bot_name=bot_name,
                            user_id=user_id,
                            table_name='strategic_memory_health',
                            cache_hit=True,
                            query_latency_ms=query_latency_ms,
                            cache_age_seconds=age_seconds
                        )
                    
                    return {
                        'memory_snapshot': row['memory_snapshot'],
                        'avg_memory_age_hours': row['avg_memory_age_hours'],
                        'retrieval_frequency_trend': row['retrieval_frequency_trend'],
                        'forgetting_risk_memories': row['forgetting_risk_memories'],
                        'computed_at': row['computed_at']
                    }
                else:
                    logger.debug(f"❌ Memory health cache miss: {bot_name}/{user_id[:8]}")
                    
                    # Record cache miss metrics
                    query_latency_ms = (time.perf_counter() - start_time) * 1000
                    if self.temporal_client:
                        await self.temporal_client.record_strategic_cache_metrics(
                            bot_name=bot_name,
                            user_id=user_id,
                            table_name='strategic_memory_health',
                            cache_hit=False,
                            query_latency_ms=query_latency_ms
                        )
                    
                    return None
                    
        except Exception as e:
            logger.warning(
                f"Memory health cache read error ({bot_name}/{user_id[:8]}): {e}",
                exc_info=False
            )
            
            # Record error metrics
            query_latency_ms = (time.perf_counter() - start_time) * 1000
            if self.temporal_client:
                await self.temporal_client.record_strategic_cache_metrics(
                    bot_name=bot_name,
                    user_id=user_id,
                    table_name='strategic_memory_health',
                    cache_hit=False,
                    query_latency_ms=query_latency_ms
                )
            
            return None

    async def _get_cached_personality_profile(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached personality profile analysis from PostgreSQL.
        
        Returns Dict with user personality traits and communication patterns.
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT communication_style, formality_level, verbosity_level,
                       primary_topics, topic_diversity_score, emotional_range,
                       dominant_emotions, question_frequency, avg_message_length,
                       interaction_frequency_pattern, preferred_times,
                       personality_summary, updated_at
                FROM strategic_personality_profiles
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Personality profile cache read error: {e}")
            return None

    async def _get_cached_conversation_patterns(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached conversation patterns from PostgreSQL.
        
        Returns Dict with fields: recent_topics, avg_topic_duration_minutes,
        context_switch_frequency, predicted_switch_likelihood, computed_at
        
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT question_patterns, temporal_patterns, length_patterns,
                       initiation_patterns, topic_patterns, style_evolution,
                       analysis_timestamp
                FROM strategic_conversation_patterns
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY analysis_timestamp DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Conversation patterns cache read error: {e}")
            return None

    async def _get_cached_character_performance(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached character performance analysis from PostgreSQL.
        
        Returns Dict with performance metrics from InfluxDB analysis.
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT avg_response_time, response_time_trend, avg_quality_score,
                       quality_trend, avg_engagement_score, engagement_trend,
                       conversation_count, performance_summary, recommendations,
                       updated_at
                FROM strategic_character_performance
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Character performance cache read error: {e}")
            return None

    async def _get_cached_context_patterns(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached context switch patterns from PostgreSQL.
        
        Returns Dict with topic transition analysis.
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT switch_count, switch_frequency, avg_topic_duration_minutes,
                       switch_patterns, common_transitions, abrupt_switch_rate,
                       context_coherence_score, updated_at
                FROM strategic_context_patterns
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Context patterns cache read error: {e}")
            return None

    async def _get_cached_memory_behavior(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached memory behavior analysis from PostgreSQL.
        
        Returns Dict with forgetting curve and retrieval pattern analysis.
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT decay_rate, retention_baseline, reinforced_topic_count,
                       total_retrieval_count, avg_retrieval_interval_days,
                       reinforcement_opportunities, optimal_recall_days,
                       recall_strategy, confidence, analysis_timestamp
                FROM strategic_memory_behavior
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY analysis_timestamp DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Memory behavior cache read error: {e}")
            return None

    async def _get_cached_engagement_opportunities(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached proactive engagement opportunities from PostgreSQL.
        
        Returns Dict with re-engagement recommendations and optimal timing.
        Returns None if cache miss or stale (>5 minutes old).
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return None
            
            query = """
                SELECT is_in_lull, hours_since_last_message, lull_severity,
                       unresolved_topic_count, milestone_count,
                       optimal_engagement_hour, optimal_engagement_day,
                       recommendations, analysis_timestamp
                FROM strategic_engagement_opportunities
                WHERE user_id = $1 AND bot_name = $2
                AND expires_at > NOW()
                ORDER BY analysis_timestamp DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    return dict(row)
                return None
                    
        except Exception as e:
            logger.debug(f"Engagement opportunities cache read error: {e}")
            return None

    async def _check_strategic_cache_freshness(
        self, 
        table_name: str,
        user_id: str, 
        bot_name: str,
        max_age_seconds: int = 300  # 5 minutes default
    ) -> bool:
        """
        Check if cached strategic data exists and is fresh enough.
        
        Useful for deciding whether to wait for background worker processing
        or proceed without strategic intelligence.
        
        Args:
            table_name: Strategic cache table name (e.g., 'strategic_memory_health')
            user_id: User identifier
            bot_name: Normalized bot name
            max_age_seconds: Maximum acceptable cache age (default 300s = 5min)
            
        Returns:
            True if cache exists and is fresh, False otherwise
        """
        try:
            postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            if not postgres_pool:
                return False
            
            query = f"""
                SELECT computed_at
                FROM {table_name}
                WHERE user_id = $1 AND bot_name = $2
                AND computed_at > NOW() - INTERVAL '{max_age_seconds} seconds'
                ORDER BY computed_at DESC
                LIMIT 1
            """
            
            async with postgres_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, bot_name)
                return row is not None
                
        except Exception as e:
            logger.debug(f"Cache freshness check error for {table_name}: {e}")
            return False

    @handle_errors(category=ErrorCategory.VALIDATION, severity=ErrorSeverity.HIGH)
    async def process_message(self, message_context: MessageContext) -> ProcessingResult:
        """
        Process a message through the complete AI pipeline.
        
        This is the main entry point that replicates the sophisticated processing
        from the Discord handlers but in a platform-agnostic way.
        """
        logger.info(f"🚀 MESSAGE PROCESSOR DEBUG: Starting process_message for user {message_context.user_id}")
        start_time = datetime.now()
        
        try:
            logger.info("🔄 MESSAGE PROCESSOR: Starting processing for user %s on platform %s", 
                       message_context.user_id, message_context.platform)
            
            # Phase 1: Security validation
            validation_result = await self._validate_security(message_context)
            if not validation_result["is_safe"]:
                logger.warning("SECURITY: Rejected unsafe message from user %s", message_context.user_id)
                
                # Check if this is a silent ignore case (e.g., mystical symbols)
                is_silent = any("Mystical" in w for w in validation_result.get("warnings", []))
                
                if is_silent:
                    # Silently ignore - no response at all
                    return ProcessingResult(
                        response="",
                        success=True,
                        silent_ignore=True,
                        error_message="Silently ignored"
                    )
                else:
                    # Normal security rejection with response
                    return ProcessingResult(
                        response="I'm sorry, but I can't process that message for security reasons.",
                        success=False,
                        error_message="Security validation failed"
                    )
            
            # Update message content with sanitized version
            message_context.content = validation_result["sanitized_content"]
            if validation_result["warnings"]:
                logger.warning("SECURITY: Input warnings for user %s: %s", 
                             message_context.user_id, validation_result['warnings'])
            
            # Phase 1.5: Chronological message ordering (FIXED)
            # BUG IN COMMIT 01a8292: Called _store_user_message_immediately() which never existed
            # FIX: Skip immediate storage - full conversation (user message + bot response) is stored
            # in Phase 4 via store_conversation() with complete context. This maintains proper
            # chronological ordering without duplicate entries.
            if self.memory_manager:
                pass  # Memory stored later with full context in Phase 4
            
            # Phase 2: Name detection and storage
            await self._process_name_detection(message_context)
            
            # Phase 2.25: Memory summary detection and processing
            memory_summary_result = await self._process_memory_summary_detection(message_context)
            if memory_summary_result:
                # Return memory summary directly if detected
                return ProcessingResult(
                    response=memory_summary_result,
                    success=True,
                    metadata={"message_type": "memory_summary"}
                )
            
            # Phase 2.5: Workflow detection and transaction processing (platform-agnostic)
            await self._process_workflow_detection(message_context)
            
            # Phase 2.75: Early emotion analysis for context-aware memory retrieval
            # Analyze user's current emotional state BEFORE retrieving memories
            # This enables emotional memory triggering - retrieving emotionally-relevant memories
            early_emotion_context = None
            user_stance_analysis = None
            
            # 🚀 OPTIMIZATION: Create NLPAnalysisCache once per message (eliminates 3+ redundant spaCy parses)
            # This cache will be reused by: stance analyzer, emotion analyzer (keywords, intensity, trajectory)
            nlp_cache = None
            try:
                from src.intelligence.nlp_analysis_cache import NLPAnalysisCache
                from src.nlp.spacy_manager import get_spacy_nlp
                
                nlp = get_spacy_nlp()
                if nlp:
                    doc = nlp(message_context.content)
                    nlp_cache = NLPAnalysisCache.from_doc(doc, message_context.content)
                    logger.debug(
                        f"🚀 NLP CACHE: Created unified cache "
                        f"(lemmas={len(nlp_cache.lemmas)}, emotion_keywords={len(nlp_cache.emotion_keywords)})"
                    )
                else:
                    logger.debug("🚀 NLP CACHE: spaCy not available, analyzers will use legacy paths")
            except Exception as e:
                logger.debug(f"🚀 NLP CACHE: Cache creation failed (non-blocking, using legacy): {e}")
                nlp_cache = None
            
            # First, analyze stance to filter emotions by speaker perspective
            if self._stance_analyzer:
                try:
                    user_stance_analysis = self._stance_analyzer.analyze_user_stance(
                        message_context.content
                        # Note: stance analyzer could be optimized with nlp_cache in future
                    )
                    if user_stance_analysis:
                        logger.info(
                            f"🎯 USER STANCE ANALYSIS: self_focus={user_stance_analysis.self_focus:.2f}, "
                            f"type={user_stance_analysis.emotion_type}, "
                            f"emotions={user_stance_analysis.primary_emotions}"
                        )
                except Exception as e:
                    logger.debug(f"Stance analysis failed: {e}")
                    user_stance_analysis = None
            
            # Then analyze emotion, potentially weighted by stance
            if self._shared_emotion_analyzer:
                try:
                    early_emotion_result = await self._shared_emotion_analyzer.analyze_emotion(
                        message_context.content,
                        message_context.user_id,
                        stance_analysis=user_stance_analysis,  # Pass stance for filtering
                        nlp_cache=nlp_cache  # 🚀 Pass cache to avoid re-parsing (keywords, intensity, trajectory)
                    )
                    if early_emotion_result and hasattr(early_emotion_result, 'primary_emotion'):
                        early_emotion_context = early_emotion_result.primary_emotion
                        # If stance indicates other's emotions, deprioritize in context retrieval
                        if user_stance_analysis and user_stance_analysis.self_focus < 0.5:
                            logger.info(f"⚠️  LOW SELF-FOCUS: Deprioritizing emotion '{early_emotion_context}' (likely about others)")
                        else:
                            logger.info(f"🎭 EARLY EMOTION DETECTION: {early_emotion_context} (for context-aware memory retrieval)")
                except Exception as e:
                    logger.debug(f"Early emotion analysis failed, using neutral context: {e}")
                    early_emotion_context = "neutral"
            
            # Phase 2.8: Strategic intelligence cache retrieval (background-computed insights)
            # Retrieves pre-computed memory health, forgetting risks, and other strategic insights
            # from PostgreSQL cache populated by enrichment worker
            memory_health_cache = None
            if self.bot_core.postgres_pool:
                try:
                    memory_health_cache = await self._get_cached_memory_health(
                        message_context.user_id,
                        self.character_name
                    )
                    if memory_health_cache:
                        logger.info(
                            f"📊 STRATEGIC INTELLIGENCE: Retrieved memory health cache "
                            f"(avg_age={memory_health_cache.get('avg_memory_age_hours', 0) / 24:.1f}d, "
                            f"trend={memory_health_cache.get('retrieval_frequency_trend', 'unknown')})"
                        )
                    else:
                        logger.debug(f"Strategic cache miss for {self.character_name}/{message_context.user_id[:8]}")
                except Exception as e:
                    logger.warning(f"Strategic cache retrieval failed (non-blocking): {e}", exc_info=True)
            
            # Phase 3: Memory retrieval with emotional context-aware filtering
            # Check if memory component is enabled before expensive retrieval
            relevant_memories = []
            if is_component_enabled(PromptComponentType.MEMORY) or is_component_enabled(PromptComponentType.EPISODIC_MEMORIES):
                relevant_memories = await self._retrieve_relevant_memories(
                    message_context, 
                    early_emotion_context,
                    memory_health_cache
                )
                logger.debug(f"✅ Retrieved {len(relevant_memories)} relevant memories (memory component enabled)")
            else:
                logger.debug("⏭️  Skipped memory retrieval (MEMORY component disabled)")
            
            # Phase 4: Conversation history and context building
            # 🚀 Structured Prompt Assembly (default - no feature flag!)
            # Note: ai_components not yet available (created in Phase 5), so pass None
            # Recall detection will check ai_components in Phase 4 revisit after classification
            conversation_context = await self._build_conversation_context_structured(
                message_context, relevant_memories, None  # ai_components available in Phase 5.5
            )
            
            # Phase 4.5: Comprehensive strategic intelligence retrieval (7 engines)
            # Retrieve all pre-computed strategic insights from PostgreSQL cache
            # populated by enrichment worker (11-minute background analysis cycle)
            strategic_intelligence = {}
            if self.bot_core and hasattr(self.bot_core, 'postgres_pool') and self.bot_core.postgres_pool:
                try:
                    # Retrieve all 7 strategic intelligence engines in parallel
                    bot_name = self.character_name or get_normalized_bot_name_from_env()
                    user_id = message_context.user_id
                    
                    import asyncio
                    strategic_results = await asyncio.gather(
                        self._get_cached_memory_health(user_id, bot_name),
                        self._get_cached_character_performance(user_id, bot_name),
                        self._get_cached_personality_profile(user_id, bot_name),
                        self._get_cached_context_patterns(user_id, bot_name),
                        self._get_cached_conversation_patterns(user_id, bot_name),
                        self._get_cached_memory_behavior(user_id, bot_name),
                        self._get_cached_engagement_opportunities(user_id, bot_name),
                        return_exceptions=True
                    )
                    
                    # Store results in strategic_intelligence dict
                    engine_names = [
                        'memory_health',
                        'character_performance', 
                        'personality_profile',
                        'context_patterns',
                        'conversation_patterns',
                        'memory_behavior',
                        'engagement_opportunities'
                    ]
                    
                    cache_hits = 0
                    for i, (name, result) in enumerate(zip(engine_names, strategic_results)):
                        if isinstance(result, Exception):
                            logger.debug(f"Strategic cache retrieval error ({name}): {result}")
                            strategic_intelligence[name] = None
                        elif result:
                            strategic_intelligence[name] = result
                            cache_hits += 1
                        else:
                            strategic_intelligence[name] = None
                    
                    if cache_hits > 0:
                        logger.info(
                            f"🧠 STRATEGIC INTELLIGENCE: Retrieved {cache_hits}/7 engines "
                            f"({', '.join(n for n, r in zip(engine_names, strategic_results) if r and not isinstance(r, Exception))})"
                        )
                    else:
                        logger.debug(f"Strategic intelligence: No cached data available (enrichment worker may not have run yet)")
                        
                except Exception as e:
                    logger.warning(f"Strategic intelligence retrieval failed (non-blocking): {e}")
                    strategic_intelligence = {}
            
            # Store in ai_components for CDL prompt enhancement (Phase 3G-3)
            ai_components = {'strategic_intelligence': strategic_intelligence}
            
            # DEBUG: Log strategic_intelligence content before additional components
            logger.info("🔍 DEBUG Phase 4.5: strategic_intelligence keys BEFORE additional: %s", 
                       list(strategic_intelligence.keys()) if strategic_intelligence else "empty")
            if strategic_intelligence.get('memory_health'):
                logger.info("🔍 DEBUG Phase 4.5: memory_health exists with keys: %s", 
                           list(strategic_intelligence['memory_health'].keys()))
            
            # Phase 5: AI component processing (parallel)
            ai_components_additional = await self._process_ai_components_parallel(
                message_context, conversation_context
            )
            
            # DEBUG: Check if additional components contains strategic_intelligence
            logger.info("🔍 DEBUG Phase 5: ai_components_additional keys: %s", 
                       list(ai_components_additional.keys()))
            if 'strategic_intelligence' in ai_components_additional:
                logger.warning("⚠️ WARNING: ai_components_additional contains strategic_intelligence! Value: %s",
                              ai_components_additional['strategic_intelligence'])
            
            ai_components.update(ai_components_additional)
            
            # DEBUG: Verify strategic_intelligence AFTER update
            logger.info("🔍 DEBUG After Update: ai_components keys: %s", list(ai_components.keys()))
            logger.info("🔍 DEBUG After Update: strategic_intelligence value: %s", 
                       ai_components.get('strategic_intelligence'))
            
            # Phase 5.5: Enhanced conversation context with AI intelligence
            conversation_context = await self._build_conversation_context_with_ai_intelligence(
                message_context, conversation_context, ai_components
            )
            
            # Phase 6: Image processing if attachments present
            if message_context.attachments:
                logger.info(f"📎 PHASE 6: Processing {len(message_context.attachments)} attachment(s) for user {message_context.user_id}")
                conversation_context = await self._process_attachments(
                    message_context, conversation_context
                )
            else:
                logger.debug("📎 PHASE 6: No attachments to process")
            
            # Phase 6.5: REMOVED - Bot Emotional Self-Awareness (redundant)
            # Bot trajectory is already handled by emotional_intelligence_component when needed.
            # That component uses character_emotional_state (richer) and queries InfluxDB on-demand.
            # Removing this saves an extra Influx/Qdrant query per message with no prompt impact.
            
            # Phase 6.7: Adaptive Learning Intelligence (Relationship & Confidence)
            # Retrieve relationship scores and conversation trends BEFORE response generation
            await self._enrich_ai_components_with_adaptive_learning(
                message_context, ai_components, relevant_memories
            )
            
            # Phase 6.8: Character Emotional State (Analytics-Only)
            # RE-ENABLED for historical tracking and quality analysis reports
            # NOT used in prompt building (CDL personality system handles that)
            # Tracks bot's internal emotional state evolution to InfluxDB for research/analytics
            if self.character_state_manager and self.temporal_client:
                try:
                    # Get bot name for state tracking
                    from src.utils.bot_name_utils import get_normalized_bot_name_from_env
                    character_name = get_normalized_bot_name_from_env()
                    
                    # Update character state based on bot's emotional response (after response is generated)
                    # Note: This will be called AFTER response generation in Phase 9
                    # For now, we just ensure the manager is available
                    logger.debug("🎭 CHARACTER STATE: Manager available for post-response analytics")
                except Exception as e:
                    logger.warning("Character State Analytics: Failed to prepare manager: %s", str(e))
            
            # Phase 6.9: Hybrid Query Routing (LLM Tool Calling)
            # PERFORMANCE NOTE: This feature adds significant overhead (~2x processing time)
            # due to UnifiedQueryClassifier's spaCy NLP analysis + potential extra LLM call.
            # Uses selective invocation to only classify analytical queries (fast pre-filter).
            # Feature enabled/disabled via ENABLE_LLM_TOOL_CALLING environment variable (checked once in factory).
            
            if self._unified_query_classifier is not None and self._is_tool_worthy_query(message_context.content):
                from src.memory.unified_query_classification import DataSource
                
                try:
                    # Get bot name from environment using standard utility
                    from src.utils.bot_name_utils import get_normalized_bot_name_from_env
                    bot_name = get_normalized_bot_name_from_env()
                    
                    logger.info(
                        "🔧 TOOL FILTER: Query passed selective filter, running classifier | "
                        "User: %s | Message: %s",
                        message_context.user_id, 
                        message_context.content[:100]
                    )
                    
                    # Run unified classification to check for tool-assisted routing
                    if self._unified_query_classifier is not None:
                        unified_classification = await self._unified_query_classifier.classify(
                            query=message_context.content,
                            emotion_data=ai_components.get("emotion_data"),
                            user_id=message_context.user_id,
                            character_name=bot_name
                        )
                        
                        # Store for downstream use (enriched summary keyword extraction, etc.)
                        ai_components['unified_classification'] = unified_classification
                        
                        # Tool calling removed - use deterministic spaCy routing instead
                        # Previously: checked for LLM_TOOLS in data_sources and executed tools
                        # Now: use vector memory for all queries
                        
                except Exception as e:
                    logger.error(
                        "❌ CLASSIFICATION ERROR: %s | Using fallback vector search",
                        str(e),
                        exc_info=True
                    )
            elif self._unified_query_classifier is not None:
                # Classifier exists but message didn't pass selective filter
                logger.debug(
                    "🔧 TOOL FILTER: Skipped classification for casual message | "
                    "User: %s | Words: %d",
                    message_context.user_id,
                    len(message_context.content.split())
                )
            
            # Phase 7: Response generation
            print(f"🎯 PHASE 7 START: About to call _generate_response for user {message_context.user_id}", flush=True)
            response = await self._generate_response(
                message_context, conversation_context, ai_components
            )
            print(f"✅ PHASE 7 DONE: _generate_response returned {len(response)} chars", flush=True)
            
            # Phase 7.5: Analyze bot's emotional state from response (SERIAL to avoid RoBERTa conflicts)
            bot_emotion = await self._analyze_bot_emotion_with_shared_analyzer(response, message_context, ai_components)
            ai_components['bot_emotion'] = bot_emotion
            
            # REMOVED: Phase 7.5b/7.5c Character Emotional State Updates & InfluxDB Recording
            # Overengineered - CDL personality system already handles character emotional expression
            
            # Phase 7.6: Intelligent Emoji Decoration (NEW - Database-driven post-LLM enhancement)
            # Try to initialize emoji selector if not yet available (lazy initialization)
            if not self.emoji_selector:
                self._try_initialize_emoji_selector()
            
            if self.emoji_selector and self.character_name:
                try:
                    # Step 1: Filter inappropriate emojis from LLM's own response
                    # (e.g., remove celebration emojis when user is in distress)
                    # Use emotion_data (primary) or emotion_analysis (fallback) for compatibility
                    user_emotion = ai_components.get('emotion_data') or ai_components.get('emotion_analysis')
                    filtered_response = self.emoji_selector.filter_inappropriate_emojis(
                        message=response,
                        user_emotion_data=user_emotion
                    )
                    
                    if filtered_response != response:
                        logger.debug(
                            "Filtered inappropriate emojis from LLM response (%d → %d chars)",
                            len(response), len(filtered_response)
                        )
                        response = filtered_response
                    
                    # Step 2: Select and apply appropriate emojis via database patterns
                    emoji_selection = await self.emoji_selector.select_emojis(
                        character_name=self.character_name,
                        bot_emotion_data=bot_emotion or {},
                        user_emotion_data=user_emotion,  # Use same emotion data as filter above
                        detected_topics=ai_components.get('detected_topics', []),
                        response_type=ai_components.get('response_type'),
                        message_content=response,
                        sentiment=ai_components.get('sentiment')
                    )
                    
                    if emoji_selection.should_use and emoji_selection.emojis:
                        # Apply emojis to response
                        original_response = response
                        response = self.emoji_selector.apply_emojis(
                            response,
                            emoji_selection.emojis,
                            emoji_selection.placement
                        )
                        
                        # Store emoji selection metadata for debugging/analysis
                        ai_components['emoji_selection'] = {
                            'emojis': emoji_selection.emojis,
                            'placement': emoji_selection.placement,
                            'reasoning': emoji_selection.reasoning,
                            'source': emoji_selection.source,
                            'original_length': len(original_response),
                            'decorated_length': len(response)
                        }
                        
                        logger.debug(
                            "✨ Emoji decoration applied: %s emojis from %s - %s",
                            len(emoji_selection.emojis),
                            emoji_selection.source,
                            emoji_selection.reasoning
                        )
                    else:
                        logger.debug(
                            "✨ Emoji decoration skipped: %s",
                            emoji_selection.reasoning if emoji_selection else "selector unavailable"
                        )
                
                except Exception as e:
                    logger.warning("Emoji decoration failed (non-critical): %s", e)
                    # Continue processing - emoji decoration failure shouldn't break the response
            
            # STAGE 2: Enhanced AI Ethics for Character Learning - Monitor and enhance response
            if self.enhanced_ai_ethics:
                try:
                    # Get character data for archetype determination
                    character_data = ai_components.get('character_data')
                    if character_data:
                        # Get recent user messages for attachment analysis (simplified for initial integration)
                        recent_messages = [message_context.content]  # Start with current message
                        
                        enhanced_response = await self.enhanced_ai_ethics.enhance_character_response(
                            character=character_data,
                            user_id=message_context.user_id,
                            bot_name=get_normalized_bot_name_from_env(),
                            base_response=response,
                            recent_user_messages=recent_messages,
                            conversation_context={
                                'ai_components': ai_components,
                                'platform': message_context.platform,
                                'conversation_metadata': getattr(message_context, 'metadata', {})
                            }
                        )
                        
                        # Apply the enhanced response if different
                        if enhanced_response != response:
                            logger.info("🛡️ ENHANCED AI ETHICS: Applied ethical enhancement for user %s", message_context.user_id)
                            response = enhanced_response
                    
                    # Store ethics processing flag for metadata
                    ai_components['enhanced_ai_ethics_processed'] = True
                    
                except Exception as e:
                    logger.warning("Enhanced AI Ethics processing failed: %s", e)

            # Phase 8: Response validation and sanitization
            response = await self._validate_and_sanitize_response(
                response, message_context
            )
            
            # Phase 9: Memory storage (vector + knowledge graph)
            memory_stored = await self._store_conversation_memory(
                message_context, response, ai_components
            )
            
            # Phase 9b: Knowledge extraction and storage (PostgreSQL)
            # FEATURE FLAG: Runtime fact extraction (enabled by default for backward compatibility)
            # Runtime extraction uses REGEX/KEYWORD patterns (lightweight, no LLM calls)
            # Enrichment worker provides better quality with LLM analysis + conversation context
            # TODO: Migrate to enrichment-only after gradual rollout (set to 'false' after migration)
            knowledge_stored = False
            if os.getenv('ENABLE_RUNTIME_FACT_EXTRACTION', 'true').lower() == 'true':
                # Extract facts from USER message about the user
                knowledge_stored = await self._extract_and_store_knowledge(
                    message_context, ai_components, extract_from='user'
                )
            else:
                logger.debug("⏭️ RUNTIME FACT EXTRACTION: Disabled (enrichment worker handles fact extraction)")
            
            # NOTE: Bot self-learning is handled by Character Episodic Intelligence (PHASE 1)
            # Character episodic memories are extracted from vector conversations with RoBERTa emotion scoring
            # See: src/characters/learning/character_vector_episodic_intelligence.py
            # Bot self-facts would be redundant with the episodic memory system
            
            # Phase 9c: User preference extraction and storage (PostgreSQL)
            # FEATURE FLAG: Runtime preference extraction (enabled by default for backward compatibility)
            # Runtime extraction uses regex patterns (brittle, limited to 4 types)
            # Enrichment worker provides better quality with LLM analysis + conversation context
            # TODO: Migrate to enrichment-only after gradual rollout (set to 'false' after migration)
            preference_stored = False
            if os.getenv('ENABLE_RUNTIME_PREFERENCE_EXTRACTION', 'true').lower() == 'true':
                preference_stored = await self._extract_and_store_user_preferences(
                    message_context
                )
            else:
                logger.debug("⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled (enrichment worker handles preference extraction)")
            
            # Phase 9d: Character Emotional State Analytics (InfluxDB-only)
            # Record bot's internal emotional state for historical tracking and quality analysis
            # NOT used in prompt building (CDL personality system handles that)
            if self.character_state_manager and self.temporal_client:
                try:
                    from src.utils.bot_name_utils import get_normalized_bot_name_from_env
                    character_name = get_normalized_bot_name_from_env()
                    
                    # Get bot emotion data from AI components
                    bot_emotion_data = ai_components.get('bot_emotion', {})
                    user_emotion_data = ai_components.get('emotion_data', {})
                    
                    # Update character state based on conversation
                    character_state = await self.character_state_manager.update_character_state(
                        character_name=character_name,
                        user_id=message_context.user_id,
                        bot_emotion_data=bot_emotion_data,
                        user_emotion_data=user_emotion_data,
                        interaction_quality=0.7  # Default quality score
                    )
                    
                    # Record to InfluxDB for analytics (full 11-emotion spectrum)
                    await self.temporal_client.record_character_emotional_state(
                        bot_name=character_name,
                        user_id=message_context.user_id,
                        # V2 11-emotion parameters
                        joy=character_state.joy,
                        anger=character_state.anger,
                        sadness=character_state.sadness,
                        fear=character_state.fear,
                        love=character_state.love,
                        trust=character_state.trust,
                        optimism=character_state.optimism,
                        pessimism=character_state.pessimism,
                        anticipation=character_state.anticipation,
                        surprise=character_state.surprise,
                        disgust=character_state.disgust,
                        emotional_intensity=character_state.emotional_intensity,
                        emotional_valence=character_state.emotional_valence,
                        dominant_emotion=character_state.dominant_emotion
                    )
                    
                    logger.debug(
                        "🎭 CHARACTER STATE ANALYTICS: Recorded %s state (dominant: %s, intensity: %.2f)",
                        character_name, character_state.dominant_emotion, character_state.emotional_intensity
                    )
                except Exception as e:
                    logger.warning("Character State Analytics: Failed to record state: %s", str(e))
            
            # Phase 10: Learning Intelligence Orchestrator - Unified Learning Coordination
            await self._coordinate_learning_intelligence(
                message_context, ai_components, relevant_memories, response
            )
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract LLM timing from ai_components
            llm_time_ms = ai_components.get('llm_time_ms', 0)
            overhead_ms = processing_time_ms - llm_time_ms if llm_time_ms else processing_time_ms
            
            # Record per-message performance metrics to InfluxDB
            if self.fidelity_metrics:
                self.fidelity_metrics.record_performance_metric(
                    operation="message_processing",
                    duration_ms=processing_time_ms,
                    success=True,
                    user_id=message_context.user_id,
                    metadata={
                        "platform": str(message_context.platform),
                        "memory_count": int(len(relevant_memories) if relevant_memories else 0),
                        "memory_stored": bool(memory_stored),
                        "knowledge_stored": bool(knowledge_stored),
                        "response_length": int(len(response) if response else 0),
                        "has_attachments": bool(message_context.attachments),
                        "channel_type": str(message_context.channel_type or "unknown"),
                        # NEW: Separate LLM timing tracking
                        "llm_time_ms": int(llm_time_ms),
                        "overhead_ms": int(overhead_ms),
                        "llm_percentage": float(round((llm_time_ms / processing_time_ms * 100), 1)) if processing_time_ms > 0 else 0.0
                    }
                )
                
                # 🎯 STANCE METRICS: Record emotion and stance analysis data
                try:
                    user_emotion = ai_components.get('emotion_data', {}).get('primary_emotion') if isinstance(ai_components.get('emotion_data'), dict) else None
                    user_emotion_confidence = ai_components.get('emotion_data', {}).get('confidence', 0.0) if isinstance(ai_components.get('emotion_data'), dict) else 0.0
                    
                    bot_emotion = ai_components.get('bot_emotion', {}).get('primary_emotion') if isinstance(ai_components.get('bot_emotion'), dict) else None
                    bot_emotion_confidence = ai_components.get('bot_emotion', {}).get('confidence', 0.0) if isinstance(ai_components.get('bot_emotion'), dict) else 0.0
                    
                    # Get stance analysis if available (from metadata stored with memory)
                    user_stance = getattr(user_stance_analysis, 'emotion_type', None) if hasattr(self, 'user_stance_analysis') else None
                    user_self_focus = getattr(user_stance_analysis, 'self_focus', 0.0) if hasattr(self, 'user_stance_analysis') else 0.0
                    
                    # Bot stance will be from stored metadata, for now use None
                    bot_stance = None
                    bot_self_focus = 0.0
                    
                    if user_emotion or bot_emotion:
                        self.fidelity_metrics.record_emotion_and_stance(
                            user_id=message_context.user_id,
                            operation="message_processing",
                            user_emotion=user_emotion,
                            user_emotion_confidence=user_emotion_confidence,
                            bot_emotion=bot_emotion,
                            bot_emotion_confidence=bot_emotion_confidence,
                            user_stance=user_stance,
                            user_self_focus=user_self_focus,
                            bot_stance=bot_stance,
                            bot_self_focus=bot_self_focus,
                            stance_confidence=0.0
                        )
                except Exception as e:
                    logger.debug(f"Failed to record emotion/stance metrics: {e}")
            
            # Phase 5: Record temporal intelligence metrics
            await self._record_temporal_metrics(
                message_context=message_context,
                ai_components=ai_components,
                relevant_memories=relevant_memories,
                response=response,
                processing_time_ms=processing_time_ms
            )
            
            logger.info("✅ MESSAGE PROCESSOR: Successfully processed message for user %s in %dms", 
                       message_context.user_id, processing_time_ms)
            
            # Build enriched metadata for API consumers
            enriched_metadata = await self._build_enriched_metadata(
                message_context=message_context,
                ai_components=ai_components,
                relevant_memories=relevant_memories,
                knowledge_stored=knowledge_stored,
                memory_stored=memory_stored,
                validation_result=validation_result,
                processing_time_ms=processing_time_ms
            )
            
            # Extract LLM timing from ai_components
            llm_time_ms = ai_components.get('llm_time_ms')
            
            return ProcessingResult(
                response=response,
                success=True,
                processing_time_ms=processing_time_ms,
                llm_time_ms=llm_time_ms,
                memory_stored=memory_stored,
                metadata=enriched_metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error("❌ MESSAGE PROCESSOR: Failed to process message for user %s: %s", 
                        message_context.user_id, str(e))
            logger.debug("❌ MESSAGE PROCESSOR: Traceback: %s", traceback.format_exc())
            
            return ProcessingResult(
                response="I apologize, but I'm experiencing technical difficulties. Please try again.",
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )

    async def _record_temporal_metrics(
        self,
        message_context: MessageContext,
        ai_components: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        response: str,
        processing_time_ms: float
    ):
        """Record temporal intelligence metrics if enabled (Phase 7.5: includes bot emotion)."""
        if not self.temporal_client or not self.confidence_analyzer:
            return

        try:
            # Get bot name from environment
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # Calculate confidence metrics
            confidence_metrics = self.confidence_analyzer.calculate_confidence_metrics(
                ai_components=ai_components,
                memory_count=len(relevant_memories) if relevant_memories else 0,
                processing_time_ms=processing_time_ms
            )
            
            # Calculate relationship metrics (using actual PostgreSQL scores)
            relationship_metrics = await self.confidence_analyzer.calculate_relationship_metrics(
                user_id=message_context.user_id,
                ai_components=ai_components,
                conversation_history_length=len(relevant_memories) if relevant_memories else 0
            )
            
            # Calculate conversation quality metrics
            quality_metrics = self.confidence_analyzer.calculate_conversation_quality(
                ai_components=ai_components,
                response_length=len(response),
                processing_time_ms=processing_time_ms
            )
            
            # Phase 7.5: Record bot emotion separately in InfluxDB
            bot_emotion = ai_components.get('bot_emotion')
            if bot_emotion and isinstance(bot_emotion, dict):
                try:
                    # Record bot emotion as separate metric for temporal tracking
                    await self.temporal_client.record_bot_emotion(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        primary_emotion=bot_emotion.get('primary_emotion', 'neutral'),
                        intensity=bot_emotion.get('intensity', 0.0),
                        confidence=bot_emotion.get('confidence', 0.0)
                    )
                    logger.debug(
                        "📊 TEMPORAL: Recorded bot emotion '%s' to InfluxDB (intensity: %.2f)",
                        bot_emotion.get('primary_emotion', 'neutral'),
                        bot_emotion.get('intensity', 0.0)
                    )
                except AttributeError:
                    # record_bot_emotion method doesn't exist yet - log for now
                    logger.debug("Bot emotion recording not yet implemented in TemporalIntelligenceClient")
            
            # Phase 7.5: Record user emotion to InfluxDB (CRITICAL FIX)
            user_emotion = ai_components.get('emotion_data')
            if user_emotion and isinstance(user_emotion, dict):
                try:
                    # Record user emotion for temporal tracking and character tuning
                    # FIX: Use 'emotional_intensity' field (RoBERTa standard), not 'intensity'
                    await self.temporal_client.record_user_emotion(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        primary_emotion=user_emotion.get('primary_emotion', 'neutral'),
                        intensity=user_emotion.get('emotional_intensity', user_emotion.get('intensity', 0.0)),  # Try emotional_intensity first, fallback to intensity
                        confidence=user_emotion.get('roberta_confidence', user_emotion.get('confidence', 0.0))  # Try roberta_confidence first
                    )
                    logger.debug(
                        "📊 TEMPORAL: Recorded user emotion '%s' to InfluxDB (intensity: %.2f)",
                        user_emotion.get('primary_emotion', 'neutral'),
                        user_emotion.get('emotional_intensity', user_emotion.get('intensity', 0.0))
                    )
                except AttributeError:
                    # record_user_emotion method doesn't exist yet - log for now
                    logger.debug("User emotion recording not yet implemented in TemporalIntelligenceClient")
            
            # Record metrics to InfluxDB (async, non-blocking)
            temporal_tasks = [
                self.temporal_client.record_confidence_evolution(
                    bot_name=bot_name,
                    user_id=message_context.user_id,
                    confidence_metrics=confidence_metrics
                ),
                self.temporal_client.record_relationship_progression(
                    bot_name=bot_name,
                    user_id=message_context.user_id,
                    relationship_metrics=relationship_metrics
                ),
                self.temporal_client.record_conversation_quality(
                    bot_name=bot_name,
                    user_id=message_context.user_id,
                    quality_metrics=quality_metrics
                ),
            ]
            
            # Add memory aging metrics if available
            memory_aging = ai_components.get('memory_aging_intelligence')
            if memory_aging and isinstance(memory_aging, dict):
                try:
                    memory_aging_task = self.temporal_client.record_memory_aging_metrics(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        health_status=memory_aging.get('health_status', 'unknown'),
                        total_memories=memory_aging.get('total_memories', 0),
                        memories_flagged=memory_aging.get('memories_flagged', 0),
                        flagged_ratio=memory_aging.get('flagged_ratio', 0.0),
                        processing_time=memory_aging.get('processing_time', 0.0)
                    )
                    temporal_tasks.append(memory_aging_task)
                    logger.debug("📊 TEMPORAL: Added memory aging metrics to batch recording")
                except AttributeError:
                    # record_memory_aging_metrics method doesn't exist yet - skip for now
                    logger.debug("Memory aging metrics recording not yet implemented in TemporalIntelligenceClient")
            
            # 📊 ENHANCED CHARACTER INTELLIGENCE METRICS: Record performance from all operational systems
            
            # CharacterGraphManager metrics (if available)
            character_performance = ai_components.get('character_performance_intelligence')
            if character_performance and isinstance(character_performance, dict):
                try:
                    character_graph_task = self.temporal_client.record_character_graph_performance(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        operation="knowledge_query",
                        query_time_ms=character_performance.get('query_time_ms', 0),
                        knowledge_matches=character_performance.get('knowledge_matches', 0),
                        cache_hit=character_performance.get('cache_hit', False),
                        character_name=bot_name
                    )
                    temporal_tasks.append(character_graph_task)
                    logger.debug("📊 TEMPORAL: Added character graph performance metrics to batch recording")
                except AttributeError:
                    logger.debug("Character graph performance recording not yet implemented in TemporalIntelligenceClient")
            
            # UnifiedCharacterIntelligenceCoordinator metrics (if available)
            unified_intelligence = ai_components.get('unified_character_intelligence')
            if unified_intelligence and isinstance(unified_intelligence, dict):
                try:
                    systems_used = ["conversation_intelligence", "memory_boost"]  # Default systems
                    coordination_metadata = unified_intelligence.get('coordination_metadata', {})
                    if not isinstance(coordination_metadata, dict):
                        coordination_metadata = {}
                    
                    performance_metrics = unified_intelligence.get('performance_metrics', {})
                    if not isinstance(performance_metrics, dict):
                        performance_metrics = {}
                    
                    coordination_task = self.temporal_client.record_intelligence_coordination_metrics(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        systems_used=systems_used,
                        coordination_time_ms=performance_metrics.get('processing_time_ms', 0),
                        authenticity_score=unified_intelligence.get('character_authenticity_score', 0.0),
                        confidence_score=unified_intelligence.get('confidence_score', 0.0),
                        context_type=coordination_metadata.get('context_type', 'standard'),
                        coordination_strategy=coordination_metadata.get('coordination_strategy', 'adaptive'),
                        character_name=bot_name
                    )
                    temporal_tasks.append(coordination_task)
                    logger.debug("📊 TEMPORAL: Added intelligence coordination metrics to batch recording")
                except AttributeError:
                    logger.debug("Intelligence coordination metrics recording not yet implemented in TemporalIntelligenceClient")
            
            # Enhanced Vector Emotion Analyzer metrics (already handled individually but can aggregate)
            emotion_analysis = ai_components.get('emotion_analysis')
            if emotion_analysis and isinstance(emotion_analysis, dict):
                try:
                    # Note: Individual emotion analysis metrics are recorded by the analyzer itself
                    # This aggregates them for overall message processing metrics
                    all_emotions = emotion_analysis.get('all_emotions', {})
                    if isinstance(all_emotions, dict):
                        emotion_count = len([score for score in all_emotions.values() if score > 0.1])
                    else:
                        emotion_count = 0
                    
                    emotion_task = self.temporal_client.record_emotion_analysis_performance(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        analysis_time_ms=emotion_analysis.get('analysis_time_ms', 0),
                        confidence_score=emotion_analysis.get('confidence', 0.0),
                        emotion_count=emotion_count,
                        primary_emotion=emotion_analysis.get('primary_emotion', 'neutral')
                    )
                    temporal_tasks.append(emotion_task)
                    logger.debug("📊 TEMPORAL: Added emotion analysis performance metrics to batch recording")
                except AttributeError:
                    logger.debug("Emotion analysis performance recording not yet implemented in TemporalIntelligenceClient")
            
            # Vector Memory System metrics (memory retrieval performance)
            if relevant_memories:
                try:
                    # Filter out None values and calculate average relevance score
                    valid_memories = [mem for mem in relevant_memories if mem and isinstance(mem, dict)]
                    if valid_memories:
                        avg_relevance = sum(mem.get('score', 0.0) for mem in valid_memories) / len(valid_memories)
                        
                        # Get collection name from environment
                        collection_name = os.getenv('QDRANT_COLLECTION_NAME', f'whisperengine_memory_{bot_name.lower()}')
                        
                        vector_memory_task = self.temporal_client.record_vector_memory_performance(
                            bot_name=bot_name,
                            user_id=message_context.user_id,
                            operation="message_processing_retrieval",
                            search_time_ms=processing_time_ms * 0.2,  # Estimate ~20% of processing time for memory
                            memories_found=len(valid_memories),
                            avg_relevance_score=avg_relevance,
                            collection_name=collection_name,
                            vector_type="content"
                        )
                        temporal_tasks.append(vector_memory_task)
                        logger.debug("📊 TEMPORAL: Added vector memory performance metrics to batch recording")
                except AttributeError:
                    logger.debug("Vector memory performance recording not yet implemented in TemporalIntelligenceClient")
            
            await asyncio.gather(
                *temporal_tasks,
                return_exceptions=True  # Don't fail message processing if temporal recording fails
            )
            
            logger.debug("Recorded temporal metrics for %s/%s", bot_name, message_context.user_id)
            
            # ML Shadow Mode: Log prediction if enabled
            if self.ml_shadow_logger and self.ml_predictor:
                try:
                    prediction = await self.ml_predictor.predict_strategy_effectiveness(
                        user_id=message_context.user_id,
                        bot_name=bot_name,
                        message_content=message_context.content
                    )
                    
                    # Only log if prediction was generated (skip if insufficient data)
                    if prediction is not None:
                        # Get current CDL mode from ai_components for comparison
                        current_mode = ai_components.get('cdl_mode', 'unknown')
                        
                        await self.ml_shadow_logger.log_prediction(
                            prediction=prediction,
                            user_id=message_context.user_id,
                            bot_name=bot_name,
                            current_mode=current_mode
                        )
                except Exception as e:
                    logger.debug("ML Shadow Mode: Prediction logging failed - %s", e)
            
            # Relationship Intelligence: Lazy initialization and update of dynamic relationship scores
            await self._ensure_relationship_initialized()
            
            if self.relationship_engine:
                try:
                    # Map quality_metrics to ConversationQuality enum (TrendWise)
                    from src.relationships.evolution_engine import ConversationQuality
                    
                    # Calculate overall quality score from metrics
                    avg_quality = (
                        quality_metrics.engagement_score +
                        quality_metrics.satisfaction_score +
                        quality_metrics.natural_flow_score +
                        quality_metrics.emotional_resonance +
                        quality_metrics.topic_relevance
                    ) / 5.0
                    
                    # Map to ConversationQuality enum
                    if avg_quality >= 0.85:
                        conversation_quality = ConversationQuality.EXCELLENT
                    elif avg_quality >= 0.70:
                        conversation_quality = ConversationQuality.GOOD
                    elif avg_quality >= 0.50:
                        conversation_quality = ConversationQuality.AVERAGE
                    elif avg_quality >= 0.30:
                        conversation_quality = ConversationQuality.POOR
                    else:
                        conversation_quality = ConversationQuality.FAILED
                    
                    # Get RoBERTa emotion data (Enhanced Emotion Intelligence)
                    emotion_data = ai_components.get('emotion_data', {})
                    
                    # Calculate and update relationship scores
                    update = await self.relationship_engine.calculate_dynamic_relationship_score(
                        user_id=message_context.user_id,
                        bot_name=bot_name,
                        conversation_quality=conversation_quality,
                        emotion_data=emotion_data
                    )
                    
                    if update and update.new_scores:
                        # Safely extract changes (may be None or empty dict)
                        changes = update.changes if update.changes else {}
                        logger.info(
                            "🔄 RELATIONSHIP: Trust/affection/attunement updated for %s/%s - "
                            "trust: %.3f (%+.3f), affection: %.3f (%+.3f), attunement: %.3f (%+.3f)",
                            bot_name, message_context.user_id,
                            update.new_scores.trust, changes.get('trust', 0.0),
                            update.new_scores.affection, changes.get('affection', 0.0),
                            update.new_scores.attunement, changes.get('attunement', 0.0)
                        )
                    
                except Exception as e:
                    logger.warning("Relationship evolution update failed: %s", str(e))
            
        except Exception as e:
            # Log but don't fail message processing - include traceback for debugging
            import traceback
            logger.warning("Failed to record temporal metrics: %s", str(e))
            logger.debug("Temporal metrics error traceback: %s", traceback.format_exc())
    
    async def _ensure_relationship_initialized(self):
        """Lazy initialization of Relationship Intelligence components (postgres_pool may not be ready at __init__ time)."""
        if self._relationship_init_attempted:
            return  # Already tried, don't spam logs
        
        self._relationship_init_attempted = True
        
        # Check if postgres_pool is now available
        postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
        
        if postgres_pool and self.temporal_client:
            try:
                self.relationship_engine = create_relationship_evolution_engine(
                    postgres_pool=postgres_pool,
                    temporal_client=self.temporal_client
                )
                self.trust_recovery = create_trust_recovery_system(
                    postgres_pool=postgres_pool
                )
                logger.info("Relationship Evolution: Dynamic relationship scoring initialized (lazy)")
            except ImportError as e:
                logger.warning("RelationshipTuner components not available: %s", e)
                self.relationship_engine = None
                self.trust_recovery = None
        else:
            logger.debug("Relationship Intelligence: Still waiting for postgres_pool (postgres_pool=%s, temporal_client=%s)",
                        postgres_pool is not None, self.temporal_client is not None)
    
    async def _enrich_ai_components_with_adaptive_learning(
        self,
        message_context: MessageContext,
        ai_components: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]]
    ):
        """
        🎯 ADAPTIVE LEARNING ENRICHMENT: Enrich AI components with relationship and confidence intelligence.
        
        Retrieves and adds adaptive learning data to ai_components for LLM prompt injection:
        - Relationship State: Current trust, affection, and attunement scores
        - Conversation Confidence: Quality trends and confidence metrics
        - Emotion Analysis: RoBERTa emotion metadata (already in ai_components)
        
        This data is later extracted by CDL integration and injected into the system prompt,
        allowing AI characters to adapt behavior based on relationship depth and conversation quality.
        """
        try:
            # Ensure relationship evolution system is initialized
            await self._ensure_relationship_initialized()
            
            if not self.relationship_engine:
                logger.debug("Relationship Intelligence: Relationship engine not available for prompt injection")
                return
            
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # RELATIONSHIP INTELLIGENCE: Get current relationship scores
            try:
                scores = await self.relationship_engine._get_current_scores(
                    user_id=message_context.user_id,
                    bot_name=bot_name
                )
                
                if scores:
                    ai_components['relationship_state'] = {
                        'trust': float(scores.trust),
                        'affection': float(scores.affection),
                        'attunement': float(scores.attunement),
                        'interaction_count': int(scores.interaction_count),
                        'relationship_depth': self._calculate_relationship_depth(scores)
                    }
                    logger.info(
                        "🎯 RELATIONSHIP: Added relationship scores - trust=%.3f, affection=%.3f, attunement=%.3f",
                        scores.trust, scores.affection, scores.attunement
                    )
            except Exception as e:
                logger.debug("Relationship Intelligence: Could not retrieve relationship scores: %s", e)
            
            # TRENDWISE ANALYTICS: Get conversation quality trends from InfluxDB
            if self.temporal_client and self.temporal_client.enabled:
                try:
                    # Query last 7 days of conversation quality
                    quality_history = await self.temporal_client.get_conversation_quality_trend(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        hours_back=168  # 7 days
                    )
                    
                    if quality_history:
                        # Calculate trend (improving/declining/stable)
                        recent_avg = sum(q['engagement_score'] for q in quality_history[-5:]) / min(5, len(quality_history))
                        older_avg = sum(q['engagement_score'] for q in quality_history[:5]) / min(5, len(quality_history))
                        
                        trend_direction = "improving" if recent_avg > older_avg + 0.1 else \
                                         "declining" if recent_avg < older_avg - 0.1 else \
                                         "stable"
                        
                        ai_components['conversation_quality_trend'] = {
                            'trend_direction': trend_direction,
                            'recent_average_engagement': round(recent_avg, 2),
                            'historical_average_engagement': round(older_avg, 2),
                            'data_points': len(quality_history)
                        }
                        
                        logger.info(
                            "🎯 QUALITY TREND: Conversation quality is %s (recent: %.2f vs historical: %.2f)",
                            trend_direction, recent_avg, older_avg
                        )
                except Exception as e:
                    logger.debug("Could not retrieve conversation quality trend: %s", e)
                    
            # Fallback: Use confidence metrics as proxy if quality trend unavailable
            if 'conversation_quality_trend' not in ai_components and self.confidence_analyzer and len(relevant_memories) > 0:
                try:
                    # Calculate current confidence metrics as quality indicator
                    confidence_metrics = self.confidence_analyzer.calculate_confidence_metrics(
                        ai_components=ai_components,
                        memory_count=len(relevant_memories),
                        processing_time_ms=0.0
                    )
                    
                    ai_components['conversation_confidence'] = {
                        'overall_confidence': confidence_metrics.overall_confidence,
                        'context_confidence': confidence_metrics.context_confidence,
                        'emotional_confidence': confidence_metrics.emotional_confidence
                    }
                    logger.info(
                        "🎯 CONFIDENCE: Added conversation quality metrics - overall=%.2f",
                        confidence_metrics.overall_confidence
                    )
                except Exception as e:
                    logger.debug("TrendWise Analytics: Could not calculate confidence metrics: %s", e)
            
            # Enhanced Emotion Intelligence RoBERTa data is already in ai_components['emotion_data']
            
        except Exception as e:
            logger.warning("Failed to enrich AI components with adaptive learning data: %s", str(e))
    
    def _calculate_relationship_depth(self, scores) -> str:
        """Calculate human-readable relationship depth from scores."""
        avg_score = (float(scores.trust) + float(scores.affection) + float(scores.attunement)) / 3.0
        
        if avg_score >= 0.8:
            return "deep_bond"
        elif avg_score >= 0.6:
            return "strong_connection"
        elif avg_score >= 0.4:
            return "growing_relationship"
        elif avg_score >= 0.2:
            return "acquaintance"
        else:
            return "new_connection"

    async def _get_user_display_name(self, message_context: MessageContext) -> str:
        """
        Get user's display name with preference hierarchy:
        1. Preferred name from stored facts/preferences (if user explicitly shared)
        2. Discord display name from metadata (fallback)
        3. Generic "User" (final fallback)
        """
        try:
            # Try to get preferred name from knowledge graph facts
            if hasattr(self.bot_core, 'knowledge_router') and self.bot_core.knowledge_router:
                try:
                    facts = await self.bot_core.knowledge_router.get_temporally_relevant_facts(
                        user_id=message_context.user_id,
                        lookback_days=365,  # Check up to a year
                        limit=50
                    )
                    
                    # Look for preferred_name in fact metadata or content
                    for fact in facts:
                        # Check metadata for preferred_name key
                        if isinstance(fact.get('metadata'), dict):
                            preferred_name = fact['metadata'].get('preferred_name')
                            if preferred_name:
                                logger.debug("Using stored preferred name '%s' for user %s", 
                                           preferred_name, message_context.user_id)
                                return preferred_name
                        
                        # Check fact content for name patterns
                        fact_content = fact.get('fact', '').lower()
                        if 'preferred name is' in fact_content or 'name is' in fact_content:
                            # Extract name from fact content
                            import re
                            match = re.search(r"(?:preferred )?name is ([A-Z][a-zA-Z\-']+)", 
                                            fact.get('fact', ''), re.IGNORECASE)
                            if match:
                                preferred_name = match.group(1)
                                logger.debug("Extracted preferred name '%s' from fact for user %s", 
                                           preferred_name, message_context.user_id)
                                return preferred_name
                except Exception as e:
                    logger.debug("Could not retrieve preferred name from facts: %s", e)
            
            # Fallback to Discord display name from metadata
            if message_context.metadata:
                discord_name = message_context.metadata.get('discord_author_name')
                if discord_name:
                    logger.debug("Using Discord display name '%s' for user %s", 
                               discord_name, message_context.user_id)
                    return discord_name
            
            # Final fallback
            logger.debug("No display name found, using generic 'User' for user %s", 
                       message_context.user_id)
            return "User"
            
        except Exception as e:
            logger.warning("Error getting user display name: %s", e)
            return "User"

    async def _validate_security(self, message_context: MessageContext) -> Dict[str, Any]:
        """Validate message security and sanitize content."""
        # Check for mystical symbols first (silent ignore) - feature flag controlled
        import os
        enable_mystical_filter = os.getenv("ENABLE_MYSTICAL_SYMBOL_FILTER", "false").lower() == "true"
        
        if enable_mystical_filter:
            mystical_detector = get_mystical_symbol_detector()
            should_ignore, reason = mystical_detector.should_ignore_message(message_context.content)
            
            if should_ignore:
                logger.info(
                    "🔮 MYSTICAL FILTER: Silently ignoring message from user %s - %s",
                    message_context.user_id, reason
                )
                return {
                    "is_safe": False,
                    "sanitized_content": message_context.content,
                    "warnings": ["Mystical symbol content detected"]
                }
        
        if not self.security_validator:
            return {
                "is_safe": True,
                "sanitized_content": message_context.content,
                "warnings": []
            }
        
        try:
            # Create adapter for Discord-specific components
            discord_message = create_discord_message_adapter(message_context)
            
            validation_result = await self.security_validator.validate_input(discord_message)
            self._last_security_validation = validation_result
            return validation_result
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Security validation failed: %s", str(e))
            return {
                "is_safe": True,  # Fail open for now
                "sanitized_content": message_context.content,
                "warnings": [f"Security validation error: {e}"]
            }

    async def _process_name_detection(self, message_context: MessageContext):
        """
        DISABLED: No automatic name storage.
        
        User's preferred name should only be stored when explicitly mentioned in conversation
        (e.g., "My name is John", "Call me Sarah"). Discord display names are already 
        available in metadata for reference but should not be preemptively stored as "preferred name".
        
        This method is kept as a no-op placeholder for the processing pipeline.
        """
        # No-op: Name detection happens naturally through conversation only
        logger.debug("Name detection phase: No automatic storage - waiting for explicit user introduction")
        pass

    async def _process_workflow_detection(self, message_context: MessageContext):
        """
        🎯 PLATFORM-AGNOSTIC WORKFLOW DETECTION
        
        Detect workflow patterns and execute transaction actions before memory retrieval.
        This ensures transactions are processed regardless of platform (Discord, web API, etc.).
        """
        try:
            # Check if bot has workflow manager initialized
            if not hasattr(self.bot_core, 'workflow_manager') or not self.bot_core.workflow_manager:
                logger.debug("🎯 WORKFLOW: No workflow manager available, skipping detection")
                return
            
            # Get bot name for transaction isolation
            import os
            bot_name = os.getenv("DISCORD_BOT_NAME", "unknown").lower()
            
            logger.debug("🎯 WORKFLOW: Starting detection for user %s, message: '%s'", 
                        message_context.user_id, message_context.content[:100])
            
            # Detect workflow intent
            trigger_result = await self.bot_core.workflow_manager.detect_intent(
                message=message_context.content,
                user_id=message_context.user_id,
                bot_name=bot_name
            )
            
            if trigger_result:
                logger.info("🎯 WORKFLOW: Detected intent - workflow: %s, confidence: %.2f", 
                           trigger_result.workflow_name, trigger_result.match_confidence)
                
                # Execute workflow action (create/update/complete transaction)
                workflow_result = await self.bot_core.workflow_manager.execute_workflow_action(
                    trigger_result=trigger_result,
                    user_id=message_context.user_id,
                    bot_name=bot_name,
                    message=message_context.content
                )
                
                # Store workflow context in message metadata for later use in prompt building
                if not message_context.metadata:
                    message_context.metadata = {}
                
                message_context.metadata['workflow_prompt_injection'] = workflow_result.get("prompt_injection")
                message_context.metadata['workflow_result'] = workflow_result
                message_context.metadata['workflow_transaction_id'] = workflow_result.get("transaction_id")
                
                logger.info("🎯 WORKFLOW: Executed action '%s', transaction: %s", 
                           workflow_result.get("action"), workflow_result.get("transaction_id"))
            else:
                logger.debug("🎯 WORKFLOW: No workflow pattern matched for message")
                
        except Exception as e:
            logger.error("🎯 WORKFLOW ERROR: Failed to process workflow detection: %s", e)
            # Don't fail the entire message processing if workflow detection fails
            logger.error("🎯 WORKFLOW ERROR: Continuing with normal message processing")

    async def _process_memory_summary_detection(self, message_context: MessageContext) -> Optional[str]:
        """
        🧠 MEMORY SUMMARY DETECTION
        
        Detect if user is asking for a memory summary and generate comprehensive response.
        Returns the summary response if detected, None otherwise.
        """
        try:
            content_lower = message_context.content.lower().strip()
            
            # Memory summary trigger patterns
            memory_triggers = [
                'what do you remember about me',
                'what do you know about me',
                'tell me what you remember',
                'what have you learned about me',
                'summarize what you know about me',
                'what do you remember',
                'memory summary',
                'what facts do you have about me',
                'what do you remember from our conversations'
            ]
            
            # Check if message matches memory summary patterns
            is_memory_request = any(trigger in content_lower for trigger in memory_triggers)
            
            if not is_memory_request:
                return None
                
            logger.info("🧠 MEMORY SUMMARY: Detected memory summary request from user %s", 
                       message_context.user_id)
            
            # Generate comprehensive memory summary
            summary = await self._generate_memory_summary(message_context.user_id)
            
            logger.info("🧠 MEMORY SUMMARY: Generated summary (%d chars) for user %s", 
                       len(summary), message_context.user_id)
            
            return summary
            
        except Exception as e:
            logger.error("🧠 MEMORY SUMMARY ERROR: Failed to process memory summary detection: %s", e)
            return None

    async def _generate_memory_summary(self, user_id: str) -> str:
        """
        Generate comprehensive memory summary for a user.
        
        Combines facts from knowledge graph with conversation memories.
        """
        try:
            summary_parts = []
            
            # 1. Get user facts from knowledge graph
            if hasattr(self.bot_core, 'knowledge_router') and self.bot_core.knowledge_router:
                facts = await self.bot_core.knowledge_router.get_temporally_relevant_facts(
                    user_id=user_id,
                    lookback_days=180,  # Longer lookback for summary
                    limit=30  # More facts for comprehensive summary
                )
                
                if facts:
                    logger.debug("🧠 Retrieved %d facts for memory summary", len(facts))
                    
                    # Track seen entities per category to avoid duplicates
                    seen_entities = set()
                    
                    # Categorize facts
                    preferences = []
                    background = []
                    relationships = []
                    activities = []
                    possessions = []
                    other_facts = []
                    
                    for fact in facts:
                        entity_name = fact.get('entity_name', '').strip()
                        relationship_type = fact.get('relationship_type', '')
                        confidence = fact.get('weighted_confidence', fact.get('confidence', 0.5))
                        potentially_outdated = fact.get('potentially_outdated', False)
                        
                        # Skip very low confidence facts
                        if confidence < 0.4 or potentially_outdated:
                            continue
                        
                        # Skip truncated/malformed facts - these have incomplete phrases
                        # Common truncation patterns:
                        # - Ends with "at" followed by nothing: "dean radin at"
                        # - Incomplete phrases: "ai might be", "humans who collapse"
                        # - Missing critical parts: "they're access codes", "you are actually"
                        # - Empty entity names
                        if not entity_name or len(entity_name) < 3:
                            continue
                        
                        # Check for common truncation patterns
                        entity_lower = entity_name.lower()
                        if (entity_lower.endswith(' at') or 
                            entity_lower.endswith(' be') or
                            entity_lower.endswith(' and') or
                            'might be' in entity_lower or
                            'who collapse' in entity_lower or
                            'access codes' in entity_lower or
                            'you are actually' in entity_lower or
                            'they\'re' in entity_lower):
                            logger.debug("⚠️ Skipping truncated/malformed fact: '%s' (%s)", entity_name, relationship_type)
                            continue
                        
                        # Skip if we already have this entity (prefer first/highest confidence occurrence)
                        entity_key = entity_name.lower()
                        if entity_key in seen_entities:
                            logger.debug("⏭️ Skipping duplicate entity: '%s' (already have this fact)", entity_name)
                            continue
                        
                        # Categorize by relationship type
                        if relationship_type in ['likes', 'loves', 'enjoys', 'prefers', 'dislikes', 'hates']:
                            preferences.append(f"{relationship_type} {entity_name}")
                            seen_entities.add(entity_key)
                        elif relationship_type in ['works_at', 'studies_at', 'lives_in', 'from']:
                            background.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                            seen_entities.add(entity_key)
                        elif relationship_type in ['son', 'daughter', 'parent', 'sibling', 'friend', 'partner']:
                            relationships.append(f"{relationship_type} {entity_name}")
                            seen_entities.add(entity_key)
                        elif relationship_type in ['visited', 'goes_to', 'attends', 'plays', 'does']:
                            activities.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                            seen_entities.add(entity_key)
                        elif relationship_type in ['owns', 'has']:
                            possessions.append(f"{relationship_type} {entity_name}")
                            seen_entities.add(entity_key)
                        else:
                            other_facts.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                            seen_entities.add(entity_key)
                    
                    # Build categorized summary
                    if preferences:
                        summary_parts.append(f"**Your Preferences:** {', '.join(preferences[:12])}")
                    if background:
                        summary_parts.append(f"**Background:** {', '.join(background[:8])}")
                    if relationships:
                        summary_parts.append(f"**Family & Relationships:** {', '.join(relationships[:8])}")
                    if activities:
                        summary_parts.append(f"**Activities & Interests:** {', '.join(activities[:8])}")
                    if possessions:
                        summary_parts.append(f"**Things You Have:** {', '.join(possessions[:8])}")
                    if other_facts:
                        summary_parts.append(f"**Other Details:** {', '.join(other_facts[:6])}")
            
            # 2. Get recent conversation themes if memory manager available
            if self.memory_manager:
                try:
                    recent_memories = await self.memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query="conversation themes topics discussed",
                        limit=8
                    )
                    
                    if recent_memories:
                        themes = []
                        for memory in recent_memories[:5]:
                            content = memory.get('content', '')
                            if content and len(content) > 20:
                                # Extract theme from memory content
                                if len(content) > 100:
                                    theme = content[:97] + "..."
                                else:
                                    theme = content
                                themes.append(theme)
                        
                        if themes:
                            summary_parts.append(f"**Recent Conversation Themes:** {' | '.join(themes)}")
                            
                except Exception as e:
                    logger.warning("🧠 Could not retrieve conversation themes: %s", e)
            
            # 3. Build final summary
            if summary_parts:
                intro = "Here's what I remember about you:\n\n"
                summary = intro + "\n\n".join(summary_parts)
                
                # Add friendly note about memory system
                summary += "\n\n*This summary is based on our conversations and the details you've shared with me. If anything seems incorrect or outdated, feel free to let me know!*"
            else:
                summary = "I don't have much stored information about you yet, but I'm learning as we chat! Feel free to share more about yourself - I'll remember the important details for our future conversations."
            
            return summary
            
        except Exception as e:
            logger.error("🧠 MEMORY SUMMARY ERROR: Failed to generate memory summary: %s", e)
            return "I'm having trouble accessing my memory right now, but I'm still here to chat! Our conversation history helps me understand you better as we talk."

    async def _retrieve_relevant_memories(
        self, 
        message_context: MessageContext,
        emotional_context: Optional[str] = None,
        memory_health_cache: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories with multi-vector intelligence and MemoryBoost optimization.
        
        Args:
            message_context: Message context containing user query
            emotional_context: Optional emotional state for emotion-aware memory retrieval
        """
        if not self.memory_manager:
            logger.warning("Memory manager not available; skipping memory retrieval.")
            return []

        try:
            # Start timing memory retrieval
            memory_start_time = datetime.now()
            
            # 📊 STRATEGIC INTELLIGENCE: Use memory health cache to adapt retrieval
            # Adjust retrieval parameters based on background-computed insights
            retrieval_limit = 20  # Default
            boost_stale_memories = False
            
            if memory_health_cache:
                avg_age_hours = memory_health_cache.get('avg_memory_age_hours', 0)
                avg_age_days = avg_age_hours / 24
                trend = memory_health_cache.get('retrieval_frequency_trend', 'stable')
                forgetting_risks = memory_health_cache.get('forgetting_risk_memories', [])
                
                # Adaptation logic: Increase retrieval for aging memories
                if avg_age_days > 7 or trend == 'declining':
                    retrieval_limit = 30  # Pull more memories to combat forgetting
                    boost_stale_memories = True
                    logger.info(
                        f"📊 STRATEGIC ADAPTATION: Increased retrieval to {retrieval_limit} "
                        f"(avg_age={avg_age_days:.1f}d, trend={trend})"
                    )
                
                # Prioritize at-risk memories if available
                if forgetting_risks and len(forgetting_risks) > 0:
                    logger.info(
                        f"📊 STRATEGIC PRIORITY: {len(forgetting_risks)} memories at forgetting risk"
                    )
            
            # Create platform-agnostic message context classification
            classified_context = self._classify_message_context(message_context)
            logger.debug("Message context classified: %s", classified_context.context_type.value)

            # 🎯 MULTI-VECTOR INTELLIGENCE: Try intelligent vector routing first if available
            if hasattr(self.memory_manager, '_multi_vector_coordinator') and self.memory_manager._multi_vector_coordinator:
                try:
                    relevant_memories = await self._retrieve_memories_with_multi_vector_intelligence(
                        message_context,
                        memory_start_time
                    )
                    if relevant_memories:
                        return relevant_memories
                    # If multi-vector returns empty, fall through to MemoryBoost
                    logger.debug("Multi-vector intelligence returned no results, falling back to MemoryBoost")
                except Exception as e:
                    logger.warning("Multi-vector intelligence retrieval failed, falling back: %s", str(e))

            # 🚀 MEMORYBOOST: Try enhanced memory retrieval as fallback
            if hasattr(self.memory_manager, 'retrieve_relevant_memories_with_memoryboost'):
                try:
                    # Build conversation context for MemoryBoost optimization
                    conversation_context = self._build_conversation_context_for_memoryboost(message_context)
                    
                    # Use MemoryBoost enhanced retrieval with channel privacy filtering
                    # Apply strategic intelligence adaptations (retrieval_limit adjusted based on memory health)
                    memoryboost_result = await self.memory_manager.retrieve_relevant_memories_with_memoryboost(
                        user_id=message_context.user_id,
                        query=message_context.content,
                        limit=retrieval_limit,  # 📊 STRATEGIC: Adjusted based on memory health
                        conversation_context=conversation_context,
                        apply_quality_scoring=True,
                        apply_optimizations=True,
                        channel_type=message_context.channel_type  # 🔒 PRIVACY: Pass channel type for filtering
                    )
                    
                    relevant_memories = memoryboost_result.get('memories', [])
                    optimization_metadata = memoryboost_result.get('optimization_metadata', {})
                    performance_metrics = memoryboost_result.get('performance_metrics', {})
                    
                    # Calculate actual retrieval timing
                    memory_end_time = datetime.now()
                    retrieval_time_ms = int((memory_end_time - memory_start_time).total_seconds() * 1000)
                    
                    logger.info("🚀 MEMORYBOOST: Enhanced retrieval returned %d memories in %dms (optimizations: %d, improvement: %.2f%%)", 
                               len(relevant_memories), 
                               retrieval_time_ms,
                               optimization_metadata.get('optimizations_count', 0),
                               optimization_metadata.get('performance_improvement', 0.0) * 100)
                    
                    # Record MemoryBoost metrics to InfluxDB
                    if self.fidelity_metrics and relevant_memories:
                        self._record_memoryboost_metrics(
                            message_context=message_context,
                            memories=relevant_memories,
                            optimization_metadata=optimization_metadata,
                            performance_metrics=performance_metrics,
                            retrieval_time_ms=retrieval_time_ms
                        )
                    
                    return relevant_memories
                    
                except Exception as e:
                    logger.warning("MemoryBoost retrieval failed, falling back to optimized retrieval: %s", str(e))
                    # Continue to optimized retrieval fallback

            # Try optimized memory retrieval as fallback if MemoryBoost is not available
            if hasattr(self.memory_manager, 'retrieve_relevant_memories_optimized'):
                try:
                    query_type = self._classify_query_type(message_context.content)
                    user_preferences = self._build_user_preferences(message_context.user_id, classified_context)
                    filters = self._build_memory_filters(classified_context)
                    
                    # Add recency boost and meta-conversation filtering
                    filters["prefer_recent_conversation"] = True
                    filters["recency_hours"] = 2
                    filters["exclude_content_patterns"] = [
                        "your prompt", "your system prompt", "how you're programmed",
                        "your character file", "cdl_ai_integration.py", "fix the bot's",
                        "bot is announcing wrong time", "bot should speak like",
                        "testing bot response", "bot container",
                        "bot's speaking style", "bot's detection"
                    ]
                    
                    relevant_memories = await self.memory_manager.retrieve_relevant_memories_optimized(
                        user_id=message_context.user_id,
                        query=message_context.content,
                        query_type=query_type,
                        user_history=user_preferences,
                        filters=filters,
                        limit=20
                    )
                    
                    # Calculate actual retrieval timing
                    memory_end_time = datetime.now()
                    retrieval_time_ms = int((memory_end_time - memory_start_time).total_seconds() * 1000)
                    
                    logger.info("🚀 MEMORY: Optimized retrieval returned %d memories in %dms", len(relevant_memories), retrieval_time_ms)
                    
                    # Record memory quality metrics to InfluxDB with ACTUAL timing
                    if self.fidelity_metrics and relevant_memories:
                        # Calculate average relevance score (if available)
                        relevance_scores = [mem.get('relevance_score', 0.7) for mem in relevant_memories]
                        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.7
                        
                        # Calculate average vector similarity (if available)
                        vector_similarities = [mem.get('vector_similarity', 0.8) for mem in relevant_memories]
                        avg_similarity = sum(vector_similarities) / len(vector_similarities) if vector_similarities else 0.8
                        
                        self.fidelity_metrics.record_memory_quality(
                            user_id=message_context.user_id,
                            operation="optimized_retrieval",
                            relevance_score=avg_relevance,
                            retrieval_time_ms=retrieval_time_ms,  # ACTUAL timing
                            memory_count=len(relevant_memories),
                            vector_similarity=avg_similarity
                        )
                    
                    return relevant_memories
                    
                except (AttributeError, ValueError, TypeError) as e:
                    logger.warning("Optimized memory retrieval failed, using fallback: %s", str(e))
            
            # Fallback to context-aware retrieval with channel privacy filtering
            # 🎭 EMOTIONAL MEMORY TRIGGERING: Pass actual emotion instead of "general conversation"
            effective_emotional_context = emotional_context or "general conversation"
            
            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                user_id=message_context.user_id,
                query=message_context.content,
                max_memories=20,
                context=classified_context,
                emotional_context=effective_emotional_context,  # 🎭 FIX: Use actual detected emotion!
                channel_type=message_context.channel_type  # 🔒 PRIVACY: Pass channel type for filtering
            )
            
            logger.info("🔍 MEMORY: Retrieved %d memories via context-aware fallback (emotion: %s)", 
                       len(relevant_memories), effective_emotional_context)
            
            # REMOVED: Fake estimated memory metrics for fallback - not useful
            # Fallback doesn't provide real relevance/similarity scores
            
            return relevant_memories
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Memory retrieval failed: %s", str(e))
            return []

    async def _retrieve_memories_with_multi_vector_intelligence(
        self,
        message_context: MessageContext,
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        🎯 PHASE 2c: UNIFIED QUERY CLASSIFICATION - Single authoritative memory routing.
        
        Replaces MultiVectorIntelligence.classify_query() with UnifiedQueryClassifier
        for consistent intent analysis across entire platform.
        
        Routes queries through unified classification to leverage emotion and semantic
        vectors based on query intent, using single source of truth for all routing.
        
        Args:
            message_context: Message context with user query
            start_time: Start time for performance tracking
            
        Returns:
            List of relevant memories from intelligent unified vector search
        """
        try:
            # Phase 2c: Use unified classifier for authoritative classification
            if self._unified_query_classifier is not None:
                try:
                    # Get unified classification result
                    unified_result = await self._unified_query_classifier.classify(
                        message_context.content
                    )
                    
                    logger.info(
                        "✅ UNIFIED: Query classified as %s (strategy: %s, confidence: %.2f)",
                        unified_result.intent_type.value,
                        unified_result.vector_strategy.value,
                        unified_result.intent_confidence
                    )
                    
                    # Route to appropriate search strategy based on unified classification
                    memories = []
                    
                    if unified_result.vector_strategy == UnifiedVectorStrategy.EMOTION_FUSION:
                        # Use emotion-focused search
                        logger.info("🎭 UNIFIED: Using emotion-fusion search")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            emotional_query=message_context.content,  # Use full query for emotion embedding
                            user_id=message_context.user_id,
                            top_k=20
                        )
                        
                    elif unified_result.vector_strategy == UnifiedVectorStrategy.SEMANTIC_FUSION:
                        # Use semantic-focused search
                        logger.info("🧠 UNIFIED: Using semantic-fusion search")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            personality_context=message_context.content,  # Use query as context
                            user_id=message_context.user_id,
                            top_k=20
                        )
                        
                    elif unified_result.vector_strategy == UnifiedVectorStrategy.BALANCED_FUSION:
                        # Use triple-vector search for complex queries
                        logger.info("⚖️ UNIFIED: Using balanced-fusion (all vectors)")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            emotional_query=message_context.content,
                            personality_context=message_context.content,
                            user_id=message_context.user_id,
                            top_k=20
                        )
                    elif unified_result.vector_strategy == UnifiedVectorStrategy.TEMPORAL_CHRONOLOGICAL:
                        # For temporal queries, use chronological ordering by sorting results by timestamp
                        logger.info("⏰ UNIFIED: Using temporal-chronological search")
                        memories = await self.memory_manager.retrieve_relevant_memories(
                            user_id=message_context.user_id,
                            query=message_context.content,
                            limit=20
                        )
                        # Sort by timestamp to get chronological order (oldest to newest for context)
                        if memories:
                            memories = sorted(memories, key=lambda m: m.get('timestamp', 0))
                    else:
                        # Default to content-primary search
                        logger.info("📄 UNIFIED: Using content-only search (default)")
                        memories = await self.memory_manager.retrieve_relevant_memories(
                            user_id=message_context.user_id,
                            query=message_context.content,
                            limit=20
                        )
                    
                    # Calculate retrieval time
                    end_time = datetime.now()
                    retrieval_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    logger.info(
                        "✅ UNIFIED: Retrieved %d memories in %dms using %s strategy",
                        len(memories),
                        retrieval_time_ms,
                        unified_result.vector_strategy.value
                    )
                    
                    return memories
                    
                except TypeError as e:
                    logger.warning(
                        "⚠️  UNIFIED: Unified classification failed: %s. Falling back to MultiVectorIntelligence.",
                        str(e)
                    )
                    # Fall through to legacy MultiVectorIntelligence below
            
            # Fallback: Legacy MultiVectorIntelligence (if unified classifier unavailable)
            if hasattr(self.memory_manager, '_multi_vector_coordinator') and self.memory_manager._multi_vector_coordinator:
                try:
                    # Get recent conversation context for better classification
                    conversation_context = self._build_conversation_context_for_memoryboost(message_context)
                    
                    # Classify query using existing MultiVectorIntelligence
                    classification = await self.memory_manager._multi_vector_coordinator.intelligence.classify_query(
                        message_context.content,
                        user_context=conversation_context[:200] if conversation_context else None
                    )
                    
                    logger.info(
                        "⚠️  FALLBACK: Multi-vector classification: %s (strategy: %s, confidence: %.2f)",
                        classification.query_type.value,
                        classification.strategy.value,
                        classification.confidence
                    )
                    
                    # Import VectorStrategy for comparison
                    from src.memory.multi_vector_intelligence import VectorStrategy
                    
                    # Route to appropriate search strategy based on classification
                    memories = []
                    
                    if classification.strategy == VectorStrategy.EMOTION_PRIMARY:
                        logger.info("🎭 FALLBACK: Using emotion-primary search")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            emotional_query=message_context.content,
                            user_id=message_context.user_id,
                            top_k=20
                        )
                    elif classification.strategy == VectorStrategy.SEMANTIC_PRIMARY:
                        logger.info("🧠 FALLBACK: Using semantic-primary search")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            personality_context=" ".join(classification.semantic_indicators[:5]),
                            user_id=message_context.user_id,
                            top_k=20
                        )
                    elif classification.strategy == VectorStrategy.BALANCED_FUSION:
                        logger.info("⚖️ FALLBACK: Using balanced fusion")
                        memories = await self.memory_manager.vector_store.search_with_multi_vectors(
                            content_query=message_context.content,
                            emotional_query=message_context.content if classification.emotional_indicators else None,
                            personality_context=" ".join(classification.semantic_indicators[:5]) if classification.semantic_indicators else None,
                            user_id=message_context.user_id,
                            top_k=20
                        )
                    else:
                        logger.info("📄 FALLBACK: Using content-primary search")
                        memories = await self.memory_manager.retrieve_relevant_memories(
                            user_id=message_context.user_id,
                            query=message_context.content,
                            limit=20
                        )
                    
                    end_time = datetime.now()
                    retrieval_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    logger.info(
                        "✅ FALLBACK: Retrieved %d memories in %dms using %s strategy",
                        len(memories),
                        retrieval_time_ms,
                        classification.strategy.value
                    )
                    
                    return memories
                    
                except Exception as e:
                    logger.warning("Multi-vector intelligence fallback failed: %s", str(e))
                    return []
            
            return []
        
        except Exception as e:
            logger.error("Multi-vector intelligence retrieval failed: %s", str(e), exc_info=True)
            return []

    async def _track_vector_strategy_effectiveness(
        self,
        message_context: MessageContext,
        classification: Any,  # QueryClassification
        results_count: int,
        retrieval_time_ms: int
    ):
        """
        Track which vector strategies return useful results for learning optimization.
        
        Records to InfluxDB:
        - Strategy used
        - Primary vector selected
        - Query type
        - Results count
        - Classification confidence
        - Retrieval performance
        """
        if not self.fidelity_metrics:
            return
        
        try:
            # Record vector strategy usage (synchronous call - no await)
            self.fidelity_metrics.record_memory_quality(
                user_id=message_context.user_id,
                operation=f"multi_vector_{classification.strategy.value}",
                relevance_score=classification.confidence,
                retrieval_time_ms=retrieval_time_ms,
                memory_count=results_count,
                vector_similarity=0.0  # Not available in classification
            )
            
            logger.info("📊 TRACKING: Recorded vector strategy effectiveness - %s with %d results (confidence: %.2f)",
                        classification.strategy.value, results_count, classification.confidence)
            
        except Exception as e:
            logger.warning("Failed to track vector strategy effectiveness: %s", str(e))

    def _classify_query_type(self, content: str) -> str:
        """Classify the type of query for memory optimization."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['remember', 'recall', 'what did', 'told you']):
            return 'recall'
        elif any(word in content_lower for word in ['how', 'what', 'why', 'when', 'where']):
            return 'question'
        elif any(word in content_lower for word in ['feel', 'emotion', 'mood', 'sad', 'happy', 'angry']):
            return 'emotional'
        else:
            return 'general'

    def _build_user_preferences(self, user_id: str, context) -> Dict[str, Any]:
        """Build user preferences for memory filtering."""
        return {
            'user_id': user_id,
            'context_type': getattr(context, 'context_type', None),
            'security_level': getattr(context, 'security_level', None)
        }

    def _build_memory_filters(self, context) -> Dict[str, Any]:
        """Build memory filters from message context."""
        return {
            'context_type': getattr(context, 'context_type', None),
            'security_level': getattr(context, 'security_level', None)
        }

    def _build_conversation_context_for_memoryboost(self, message_context: MessageContext) -> str:
        """
        🚀 MEMORYBOOST: Build conversation context for memory optimization.
        
        Creates a rich context string that MemoryBoost can use to optimize
        memory retrieval based on conversation patterns and user intent.
        """
        try:
            context_parts = []
            
            # Add message content and intent
            context_parts.append(f"User query: {message_context.content}")
            
            # Add platform context
            if hasattr(message_context, 'platform') and message_context.platform:
                context_parts.append(f"Platform: {message_context.platform}")
            
            # Add channel type context
            if hasattr(message_context, 'channel_type') and message_context.channel_type:
                context_parts.append(f"Context: {message_context.channel_type}")
            
            # Classify query type for context
            query_type = self._classify_query_type(message_context.content)
            context_parts.append(f"Query type: {query_type}")
            
            # Add temporal context
            context_parts.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # Add user context if available
            context_parts.append(f"User: {message_context.user_id}")
            
            return " | ".join(context_parts)
            
        except Exception as e:
            logger.warning("Error building MemoryBoost conversation context: %s", str(e))
            return message_context.content  # Fallback to just the message content

    def _record_memoryboost_metrics(
        self,
        message_context: MessageContext,
        memories: List[Dict[str, Any]],
        optimization_metadata: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        retrieval_time_ms: int
    ) -> None:
        """
        🚀 MEMORYBOOST: Record memory optimization metrics to InfluxDB for analytics.
        
        Records detailed metrics about MemoryBoost performance including
        optimization effectiveness, quality scoring results, and performance impact.
        """
        try:
            if not self.fidelity_metrics:
                return
            
            # Record standard memory quality metrics
            relevance_scores = [mem.get('quality_score', mem.get('score', 0.7)) for mem in memories]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.7
            
            vector_similarities = [mem.get('score', 0.8) for mem in memories]
            avg_similarity = sum(vector_similarities) / len(vector_similarities) if vector_similarities else 0.8
            
            self.fidelity_metrics.record_memory_quality(
                user_id=message_context.user_id,
                operation="memoryboost_retrieval",
                relevance_score=avg_relevance,
                retrieval_time_ms=retrieval_time_ms,
                memory_count=len(memories),
                vector_similarity=avg_similarity
            )
            
            # Record MemoryBoost-specific metrics
            if hasattr(self.fidelity_metrics, 'record_custom_metric'):
                # Record optimization metrics
                self.fidelity_metrics.record_custom_metric(
                    metric_name="memoryboost_optimizations",
                    user_id=message_context.user_id,
                    tags={
                        'quality_scoring_applied': optimization_metadata.get('quality_scoring_applied', False),
                        'optimizations_applied': optimization_metadata.get('optimizations_applied', False),
                        'operation': 'memory_retrieval'
                    },
                    fields={
                        'optimizations_count': optimization_metadata.get('optimizations_count', 0),
                        'performance_improvement': optimization_metadata.get('performance_improvement', 0.0),
                        'base_retrieval_time_ms': performance_metrics.get('base_retrieval_time_ms', 0),
                        'quality_scoring_time_ms': performance_metrics.get('quality_scoring_time_ms', 0),
                        'optimization_time_ms': performance_metrics.get('optimization_time_ms', 0),
                        'total_time_ms': performance_metrics.get('total_time_ms', retrieval_time_ms)
                    }
                )
                
                # Record quality distribution
                if memories:
                    quality_scores = [mem.get('quality_score', 0.7) for mem in memories]
                    boost_factors = [mem.get('boost_factor', 1.0) for mem in memories]
                    
                    self.fidelity_metrics.record_custom_metric(
                        metric_name="memoryboost_quality_distribution",
                        user_id=message_context.user_id,
                        tags={'operation': 'quality_analysis'},
                        fields={
                            'avg_quality_score': sum(quality_scores) / len(quality_scores),
                            'max_quality_score': max(quality_scores),
                            'min_quality_score': min(quality_scores),
                            'avg_boost_factor': sum(boost_factors) / len(boost_factors),
                            'max_boost_factor': max(boost_factors),
                            'memories_boosted': len([b for b in boost_factors if b > 1.0]),
                            'memories_penalized': len([b for b in boost_factors if b < 1.0])
                        }
                    )
            
        except Exception as e:
            logger.warning("Error recording MemoryBoost metrics: %s", str(e))

    # REMOVED: Legacy _build_conversation_context method (~510 lines of dead code removed)
    # The legacy method used string concatenation for prompt building.
    # All prompt assembly now uses PromptComponent-based _build_conversation_context_structured method.

    async def _build_conversation_context_structured(
        self, 
        message_context: MessageContext, 
        relevant_memories: List[Dict[str, Any]],
        ai_components: Optional[Dict[str, Any]] = None  # NEW: Optional AI components for recall detection
    ) -> List[Dict[str, str]]:
        """
        🚀 STRUCTURED CONVERSATION CONTEXT BUILDING (Phase 2 + CDL Integration)
        
        Build conversation context using PromptAssembler for structured, maintainable prompt generation.
        This replaces string concatenation with component-based assembly, enabling:
        - Token budget management
        - Priority-based ordering
        - Content deduplication
        - Model-specific formatting
        - Better debugging and testing
        
        🎭 CDL INTEGRATION: Character Definition Language components are now integrated directly
        into the PromptAssembler system, eliminating the dual-path prompt assembly that was
        wasting ~150ms per message. Character identity, personality, backstory, and other CDL
        data are now added as prioritized PromptComponents alongside memories and user facts.
        
        📊 CDL IMPLEMENTATION STATUS (7/11 components working):
        ✅ IMPLEMENTED:
          1. CHARACTER_IDENTITY (Priority 1) - Name, role, archetype, essence
          2. CHARACTER_MODE (Priority 2) - AI identity handling approach
          5. AI_IDENTITY_GUIDANCE (Priority 5) - Context-aware AI disclosure
          6. TEMPORAL_AWARENESS (Priority 6) - Current date/time
          8. CHARACTER_PERSONALITY (Priority 8) - Big Five personality traits
         10. CHARACTER_VOICE (Priority 10) - Speaking style, linguistic patterns
         16. KNOWLEDGE_CONTEXT (Priority 16) - User facts and preferences
        
        ⏳ NOT IMPLEMENTED (with TODOs in code below):
          3. CHARACTER_BACKSTORY (Priority 3) - Professional history, formative experiences
          4. CHARACTER_PRINCIPLES (Priority 4) - Core values, beliefs, motivations
          7. USER_PERSONALITY (Priority 7) - User's Big Five profile
         11. CHARACTER_RELATIONSHIPS (Priority 11) - User-character relationship dynamics
        
        Returns: List of messages in OpenAI chat format (role + content)
        """
        logger.info(f"🚀 STRUCTURED CONTEXT: Building for user {message_context.user_id}")
        
        # Initialize assembler with token budget (approximate - converted to chars in components)
        # Phase 2B: Upgraded to 20K tokens (~80K chars) for CDL integration
        # Previous: 16K tokens for basic prompts
        # Modern models support 128K-200K tokens - we're targeting ~15% utilization (30K total)
        # See: docs/architecture/TOKEN_BUDGET_ANALYSIS.md for rationale
        # See: docs/architecture/CDL_COMPONENT_MAPPING.md for CDL priority structure
        assembler = create_prompt_assembler(max_tokens=20000)
        
        # ================================
        # CDL COMPONENTS 1-2: Character Identity & Mode (Priorities 1-2)
        # ================================
        # 🎭 CDL CHARACTER: Load character identity and mode from database
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        from src.prompts.cdl_component_factories import (
            create_character_identity_component,
            create_character_mode_component,
            create_ai_identity_guidance_component,
            create_character_communication_patterns_component,
            create_character_personality_component,
            create_character_voice_component,
            create_character_defined_relationships_component,
            create_response_mode_component,
            create_final_response_guidance_component,
        )
        from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
        from src.database.postgres_pool_manager import get_postgres_pool
        from src.prompts.cdl_component_factories import create_final_response_guidance_component
        from src.prompts.prompt_components import is_component_enabled, PromptComponent, PromptComponentType
        
        try:
            bot_name = get_normalized_bot_name_from_env()
            pool = await get_postgres_pool()
            
            if not pool:
                logger.error(f"❌ STRUCTURED CONTEXT: PostgreSQL pool not available for {bot_name} - CDL components will be skipped. This may indicate database connection failure on bot startup.")
            
            if pool:
                enhanced_manager = create_enhanced_cdl_manager(pool)
                
                # Component 1: Character Identity (Priority 1)
                if is_component_enabled(PromptComponentType.CHARACTER_IDENTITY):
                    identity_component = await create_character_identity_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name
                    )
                    if identity_component:
                        assembler.add_component(identity_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added CDL character identity for {bot_name}")
                    else:
                        logger.warning(f"⚠️ STRUCTURED CONTEXT: No character identity found for {bot_name}")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped character identity processing (disabled)")
                
                # Component 2: Character Mode (Priority 2) - AI identity handling
                if is_component_enabled(PromptComponentType.CHARACTER_MODE):
                    mode_component = await create_character_mode_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name
                    )
                    if mode_component:
                        assembler.add_component(mode_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added CDL character mode for {bot_name}")
                    else:
                        logger.warning(f"⚠️ STRUCTURED CONTEXT: No character mode found for {bot_name}")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped character mode processing (disabled)")
                
                # Component 3: Response Mode (Priority 1 - HIGHEST!) - Response length constraints & style
                # CRITICAL: Response mode must be HIGH priority (even higher than character identity!)
                # The LLM must see this instruction FIRST and most prominently
                if is_component_enabled(PromptComponentType.RESPONSE_STYLE):  # Note: RESPONSE_STYLE enum for response_mode
                    response_mode_component = await create_response_mode_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name,
                        priority=1  # HIGHEST priority - must be seen first by LLM
                    )
                    if response_mode_component:
                        assembler.add_component(response_mode_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added response mode guidance (PRIORITY 1) for {bot_name}")
                    else:
                        logger.debug(f"ℹ️ STRUCTURED CONTEXT: No response modes configured for {bot_name} (using defaults)")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped response mode processing (disabled)")
                
                # TODO: Component 4: Character Backstory (Priority 4) - NOT IMPLEMENTED
                # Reason: Lower priority - backstory provides depth but not critical for basic responses
                # Requires: Professional history, formative experiences, personal background from CDL
                # Factory exists: create_character_backstory_component() in cdl_component_factories.py
                # Estimated tokens: 300-700
                
                # TODO: Component 5: Character Principles (Priority 5) - NOT IMPLEMENTED
                # Reason: Lower priority - core values/beliefs add depth but not essential for personality
                # Requires: Core values, beliefs, motivations from CDL database
                # Factory exists: create_character_principles_component() in cdl_component_factories.py
                # Estimated tokens: 200-600
                
                # Component 6: AI Identity Guidance (Priority 6) - Context-aware AI disclosure
                if is_component_enabled(PromptComponentType.AI_IDENTITY_GUIDANCE):
                    ai_guidance_component = await create_ai_identity_guidance_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name,
                        message_content=message_context.content
                    )
                    if ai_guidance_component:
                        assembler.add_component(ai_guidance_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added AI identity guidance for {bot_name}")
                    # Note: No warning if None - this is context-dependent (only when user asks about AI)
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped AI identity guidance processing (disabled)")
                
                # Component 5.5: Character Communication Patterns (Priority 6) - NEW COMPONENT
                # Communication patterns define HOW character communicates (emoji, speech, behavior)
                if is_component_enabled(PromptComponentType.CHARACTER_COMMUNICATION_PATTERNS):
                    communication_patterns_component = await create_character_communication_patterns_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name,
                        priority=6
                    )
                    if communication_patterns_component:
                        assembler.add_component(communication_patterns_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added communication patterns for {bot_name}")
                    else:
                        logger.debug(f"ℹ️ STRUCTURED CONTEXT: No communication patterns found for {bot_name}")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped communication patterns processing (disabled)")
                
                # Component 8: Character Personality (Priority 8) - Big Five personality traits
                if is_component_enabled(PromptComponentType.CHARACTER_PERSONALITY):
                    personality_component = await create_character_personality_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name
                    )
                    if personality_component:
                        assembler.add_component(personality_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added CDL character personality for {bot_name}")
                    else:
                        logger.warning(f"⚠️ STRUCTURED CONTEXT: No character personality found for {bot_name}")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped character personality processing (disabled)")
                
                # Component 10: Character Voice (Priority 10) - Speaking style and linguistic patterns
                if is_component_enabled(PromptComponentType.CHARACTER_VOICE):
                    voice_component = await create_character_voice_component(
                        enhanced_manager=enhanced_manager,
                        character_name=bot_name
                    )
                    if voice_component:
                        assembler.add_component(voice_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added CDL character voice for {bot_name}")
                    else:
                        logger.warning(f"⚠️ STRUCTURED CONTEXT: No character voice found for {bot_name}")
                else:
                    logger.debug(f"⏭️  STRUCTURED CONTEXT: Skipped character voice processing (disabled)")
                
                # ================================
                # COMPONENT 9: Emotional Intelligence Context (Priority 9)
                # ================================
                # 🎭 EMOTIONAL INTELLIGENCE: Unified user + bot emotional state with InfluxDB trajectory
                # This replaces the hackish Qdrant keyword search trajectory with proper time-series analysis
                try:
                    from src.prompts.emotional_intelligence_component import create_emotional_intelligence_component
                    
                    # Get ai_components to access emotion data (passed via closure or retrieve from context)
                    # Note: ai_components is generated in parallel processing phase AFTER this function
                    # For now, we'll need to add this component AFTER ai_components are available
                    # TODO: Move emotional intelligence component to _build_conversation_context_with_ai_intelligence
                    logger.debug("ℹ️ STRUCTURED CONTEXT: Emotional intelligence component requires ai_components (added later)")
                except ImportError as import_err:
                    logger.warning(f"⚠️ STRUCTURED CONTEXT: Could not import emotional intelligence component: {import_err}")
                
                # Component 9: Character Defined Relationships (Priority 9) - Important people in character's life
                # This component surfaces relationships defined in the CDL database (character_relationships table)
                # Examples: Gabriel's Cynthia, NotTaylor's Silas, etc.
                relationships_component = await create_character_defined_relationships_component(
                    enhanced_manager=enhanced_manager,
                    character_name=bot_name
                )
                if relationships_component:
                    assembler.add_component(relationships_component)
                    logger.info(f"✅ STRUCTURED CONTEXT: Added CDL character defined relationships for {bot_name}")
                else:
                    logger.debug(f"ℹ️ STRUCTURED CONTEXT: No defined relationships found for {bot_name}")
                
                # TODO: Component 11: User-Character Relationship Dynamics (Priority 11) - NOT IMPLEMENTED
                # Note: This is DIFFERENT from character_defined_relationships above
                # Reason: Requires relationship tracking system for user-character dynamics
                # Complexity: High - needs relationship state management, key moments, interaction patterns
                # Requires: Relationship data from PostgreSQL (relationship_type, connection_strength, key_moments)
                # Factory exists: create_character_relationships_component() in cdl_component_factories.py
                # Estimated tokens: 400
                # Blocked by: Relationship management system not yet implemented
                # Note: This would enable characters to reference shared history and relationship depth
                
                # ================================
                # COMPONENT 16: Response Guidelines (Priority 16)
                # ================================
                # Character-specific response formatting rules and personality-first principles
                # from character_response_guidelines table (e.g., NotTaylor's chaotic formatting rules)
                from src.prompts.cdl_component_factories import create_response_guidelines_component
                
                response_guidelines_component = await create_response_guidelines_component(
                    enhanced_manager=enhanced_manager,
                    character_name=bot_name,
                    priority=16  # After personality/voice, before final guidance
                )
                if response_guidelines_component:
                    assembler.add_component(response_guidelines_component)
                    logger.info(f"✅ STRUCTURED CONTEXT: Added response guidelines for {bot_name}")
                else:
                    logger.debug(f"ℹ️ STRUCTURED CONTEXT: No response guidelines found for {bot_name}")
                
                # ================================
                # FINAL CDL COMPONENT: Response Guidance (Priority 20)
                # ================================
                # Add final "Respond as [character] to [user]:" instruction at highest priority
                # This ensures it appears at the end of the system prompt
                
                # Get user display name: prefer stored name, fallback to Discord display name
                user_display_name = await self._get_user_display_name(message_context)
                
                final_guidance_component = await create_final_response_guidance_component(
                    enhanced_manager=enhanced_manager,
                    character_name=bot_name,
                    user_display_name=user_display_name,
                    priority=20  # Highest priority to ensure it appears last
                )
                if final_guidance_component:
                    assembler.add_component(final_guidance_component)
                    logger.info(f"✅ STRUCTURED CONTEXT: Added final response guidance for {bot_name} addressing '{user_display_name}'")
                else:
                    logger.warning(f"⚠️ STRUCTURED CONTEXT: No final guidance component for {bot_name}")
                    
            else:
                logger.warning("⚠️ STRUCTURED CONTEXT: No database pool - skipping CDL components")
        except Exception as e:
            logger.warning(f"⚠️ STRUCTURED CONTEXT: Failed to load CDL components: {e}")
        
        # ================================
        # CDL COMPONENT 6: Temporal Awareness (Priority 6)
        # ================================
        # 🕒 CDL TEMPORAL: Current date/time context for temporal grounding
        
        # Check if temporal awareness component is enabled
        if is_component_enabled(PromptComponentType.TEMPORAL_AWARENESS):
            from src.prompts.cdl_component_factories import create_temporal_awareness_component
            
            try:
                temporal_component = await create_temporal_awareness_component(priority=6)
                if temporal_component:
                    assembler.add_component(temporal_component)
                    logger.info("✅ STRUCTURED CONTEXT: Added CDL temporal awareness")
                else:
                    # Fallback to legacy if CDL component fails
                    from src.utils.helpers import get_current_time_context
                    time_context = get_current_time_context()
                    time_component = PromptComponent(
                        type=PromptComponentType.TIME_CONTEXT,
                        content=f"CURRENT DATE & TIME: {time_context}",
                        priority=6,
                        required=True
                    )
                    assembler.add_component(time_component)
                    logger.warning("⚠️ STRUCTURED CONTEXT: Using legacy time context (CDL temporal component failed)")
            except Exception as e:
                # Fallback to legacy on exception
                logger.warning(f"⚠️ STRUCTURED CONTEXT: CDL temporal component error: {e}")
                # Use CDL factory for temporal awareness
                from src.prompts.cdl_component_factories import create_temporal_awareness_component
                time_component = await create_temporal_awareness_component(priority=6)
                if time_component:
                    assembler.add_component(time_component)
        else:
            logger.debug("⏭️  Skipped temporal awareness processing (TEMPORAL_AWARENESS component disabled)")
        
        # TODO: Component 7: User Personality (Priority 7) - NOT IMPLEMENTED
        # Reason: Requires Big Five personality analysis system for users
        # Complexity: Medium - needs user behavior analysis and personality inference
        # Requires: User's Big Five personality profile from PostgreSQL database
        # Factory exists: create_user_personality_component() in cdl_component_factories.py
        # Estimated tokens: 250
        # Blocked by: User personality analysis system not yet implemented
        
        # ================================
        # COMPONENT 5: Attachment Guard (if needed)
        # ================================
        if message_context.attachments and len(message_context.attachments) > 0:
            from src.prompts.prompt_components import create_attachment_guard_component
            bot_name_for_guard = os.getenv('DISCORD_BOT_NAME', 'Assistant')
            assembler.add_component(
                create_attachment_guard_component(
                    bot_name=bot_name_for_guard,
                    priority=3,
                    required=True
                )
            )
        
        # ================================
        # CDL COMPONENT 16: Knowledge Context (User Facts)
        # ================================
        # 📚 CDL KNOWLEDGE: User facts and learned information
        # Note: Eventually replace with separate USER_PERSONALITY (Priority 7) + KNOWLEDGE_CONTEXT (Priority 16)
        
        # Check if user facts component is enabled before database queries
        if is_component_enabled(PromptComponentType.USER_FACTS):
            from src.prompts.cdl_component_factories import create_knowledge_context_component
            
            # Get user facts from existing system
            user_facts_content = await self._build_user_facts_content(
                message_context.user_id, 
                message_context.content  # Pass message content for context-based filtering
            )
            
            if user_facts_content:
                # Try CDL knowledge context component first
                try:
                    # Parse user facts into list format for CDL component
                    user_facts_list = []
                    if user_facts_content:
                        # Split by newlines and clean up
                        facts = user_facts_content.split('\n')
                        for fact in facts:
                            fact = fact.strip()
                            if fact and fact.startswith('-'):
                                user_facts_list.append(fact[1:].strip())
                            elif fact and not fact.startswith('Known facts'):
                                user_facts_list.append(fact)
                    
                    knowledge_component = await create_knowledge_context_component(
                        user_facts=user_facts_list,
                        priority=16
                    )
                    
                    if knowledge_component:
                        assembler.add_component(knowledge_component)
                        logger.info(f"✅ STRUCTURED CONTEXT: Added CDL knowledge context ({len(knowledge_component.content)} chars)")
                    else:
                        # Fallback to legacy user facts component
                        assembler.add_component(create_user_facts_component(
                            user_facts_content,
                            priority=16
                        ))
                        logger.info(f"✅ STRUCTURED CONTEXT: Added legacy user facts ({len(user_facts_content)} chars)")
                        
                except Exception as e:
                    # Fallback to legacy on error
                    logger.warning(f"⚠️ STRUCTURED CONTEXT: CDL knowledge component error: {e}")
                    assembler.add_component(create_user_facts_component(
                        user_facts_content,
                        priority=16
                    ))
                    logger.info(f"✅ STRUCTURED CONTEXT: Added legacy user facts ({len(user_facts_content)} chars)")
        else:
            logger.debug("⏭️  Skipped user facts processing (USER_FACTS component disabled)")
        
        # ================================
        # COMPONENT 7: Memory Narrative (or anti-hallucination warning)
        # ================================
        # COMPONENT 13: Memory Context (Structured vs Enriched)
        # ================================
        # Note: Uses legacy MEMORY type at priority 13 (CDL EPISODIC_MEMORIES priority)
        
        logger.info("🔍 DEBUG: Entering memory context section - checking enriched summaries flag")
        
        # Check if enriched summaries are enabled - if so, skip choppy memory narrative
        if os.getenv('ENABLE_ENRICHED_SUMMARIES', 'false').lower() == 'true':
            logger.debug("📚 Using enriched summaries instead of choppy memory narrative")
            
            # Still add semantic memories directly (without choppy narrative formatting)
            if relevant_memories:
                logger.debug(f"Found {len(relevant_memories)} relevant memories to format")
                # Format semantic memories cleanly with structure
                conversation_memories = []
                user_facts = []
                
                # Get character name for personalized conversation turn labels
                character_display_name = self.character_name.capitalize() if self.character_name else "Bot"
                
                # Separate atomic pairs from separate messages
                atomic_pairs = []
                separate_user_messages = []
                separate_bot_messages = []
                
                for memory in relevant_memories[:20]:  # Look at top 20 to find pairs
                    content = memory.get('content', '').strip()
                    metadata = memory.get('metadata', {})
                    
                    if not content:
                        continue
                        
                    # Separate user facts from conversation memories
                    if metadata.get("type") == "user_fact":
                        fact = metadata.get("fact", content)[:300]
                        if fact:
                            user_facts.append(fact)
                        continue
                    
                    # Check if this is an atomic pair (NEW format)
                    role = metadata.get('role', 'unknown')
                    source = metadata.get('source', '')
                    bot_response_in_metadata = metadata.get('bot_response', '')
                    
                    if (role == 'conversation_pair' or source == 'conversation_pair') and bot_response_in_metadata:
                        # NEW FORMAT: Atomic pair with both messages in metadata
                        user_message = metadata.get('user_message', content)
                        atomic_pairs.append({
                            'user': user_message,
                            'bot': bot_response_in_metadata,
                            'score': memory.get('score', 1.0)
                        })
                    elif role == 'user' or source == 'user_message':
                        # OLD FORMAT: Separate user message
                        separate_user_messages.append({
                            'content': content,
                            'timestamp': memory.get('timestamp', ''),
                            'score': memory.get('score', 1.0)
                        })
                    elif role in ['bot', 'assistant'] or source == 'bot_response':
                        # OLD FORMAT: Separate bot message
                        separate_bot_messages.append({
                            'content': content,
                            'timestamp': memory.get('timestamp', ''),
                            'score': memory.get('score', 1.0)
                        })
                
                logger.info(f"📊 Memory analysis: {len(atomic_pairs)} atomic pairs, {len(separate_user_messages)} separate user, {len(separate_bot_messages)} separate bot")
                
                # Add atomic pairs first (they have full context)
                for pair in atomic_pairs[:5]:  # Top 5 atomic pairs
                    conversation_turn = f"User: {pair['user'][:300]}\n{character_display_name}: {pair['bot'][:300]}"
                    conversation_memories.append(conversation_turn)
                
                # For OLD format messages, pair them by timestamp
                # Sort by score (relevance) first
                separate_user_messages.sort(key=lambda x: x.get('score', 0), reverse=True)
                separate_bot_messages.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                for user_msg in separate_user_messages[:10]:  # Top 10 relevant user messages
                    user_content = user_msg['content']
                    user_ts = user_msg.get('timestamp', '')
                    
                    # Try to find matching bot response by timestamp proximity
                    matching_bot = None
                    if separate_bot_messages and user_ts:
                        try:
                            from datetime import datetime
                            user_dt = datetime.fromisoformat(user_ts.replace('Z', '+00:00'))
                            
                            best_match = None
                            best_time_diff = float('inf')
                            
                            for bot_msg in separate_bot_messages:
                                bot_ts = bot_msg.get('timestamp', '')
                                if bot_ts:
                                    bot_dt = datetime.fromisoformat(bot_ts.replace('Z', '+00:00'))
                                    time_diff = abs((bot_dt - user_dt).total_seconds())
                                    
                                    # Bot response should be within 30 seconds of user message
                                    if time_diff <= 30 and time_diff < best_time_diff:
                                        best_time_diff = time_diff
                                        best_match = bot_msg
                            
                            matching_bot = best_match
                        except Exception as e:
                            logger.debug(f"Timestamp pairing failed: {e}")
                    
                    # Format conversation turn
                    if matching_bot:
                        bot_content = matching_bot['content']
                        conversation_turn = f"User: {user_content[:300]}\n{character_display_name}: {bot_content[:300]}"
                        # Remove matched bot message so it's not reused
                        if matching_bot in separate_bot_messages:
                            separate_bot_messages.remove(matching_bot)
                    else:
                        # No matching bot response - just show user message
                        conversation_turn = f"User: {user_content[:500]}"
                    
                    conversation_memories.append(conversation_turn)
                
                logger.info(f"✅ Formatted {len(conversation_memories)} conversation turns ({len(atomic_pairs)} from atomic pairs, {len(conversation_memories) - len(atomic_pairs)} from pairing)")
                
                # Build RELEVANT MEMORIES section
                memory_parts = []
                if user_facts:
                    memory_parts.append(f"USER FACTS: {'; '.join(user_facts)}")
                
                if conversation_memories:
                    memory_parts.append(f"PAST CONVERSATIONS:\n🕐 RECENT (Last 24 hours):\n" + "\n\n".join(conversation_memories))
                
                if memory_parts:
                    semantic_memories_text = "RELEVANT MEMORIES: " + "\n\n".join(memory_parts)
                    assembler.add_component(create_memory_component(
                        semantic_memories_text,
                        priority=13  # Priority 13: Episodic memories from CDL mapping
                    ))
                    logger.info(f"✅ STRUCTURED CONTEXT: Added {len(conversation_memories)} conversations + {len(user_facts)} facts (enriched mode)")
                else:
                    assembler.add_component(create_anti_hallucination_component(priority=13))
                    logger.info(f"⚠️ STRUCTURED CONTEXT: Added anti-hallucination warning (no valid memories)")
            else:
                assembler.add_component(create_anti_hallucination_component(priority=13))
                logger.info(f"⚠️ STRUCTURED CONTEXT: Added anti-hallucination warning (no memories found)")
        else:
            # Use traditional choppy memory narrative system
            memory_narrative = await self._build_memory_narrative_structured(
                message_context.user_id, 
                relevant_memories
            )
            
            if memory_narrative:
                assembler.add_component(create_memory_component(
                    f"RELEVANT MEMORIES: {memory_narrative}",
                    priority=13  # Priority 13: Episodic memories from CDL mapping
                ))
                logger.info(f"✅ STRUCTURED CONTEXT: Added memory narrative ({len(memory_narrative)} chars)")
            else:
                assembler.add_component(create_anti_hallucination_component(priority=13))
                logger.info(f"⚠️ STRUCTURED CONTEXT: Added anti-hallucination warning (no memories)")
        
        # ================================
        # COMPONENT 13.5: Episodic Recall Hook (NEW - November 2025)
        # ================================
        # When user asks to recall/remember past events AND we have high-confidence memories,
        # inject an explicit episodic context so the bot knows it CAN reference those events
        # This overrides AI ethics "no memory" disclaimers when memories are actually retrieved
        logger.debug(f"🧠 EPISODIC RECALL: Checking recall intent for '{message_context.content[:50]}...' with {len(relevant_memories)} memories")
        episodic_context = self._build_episodic_recall_context(
            message_content=message_context.content,
            retrieved_memories=relevant_memories
        )
        if episodic_context:
            assembler.add_component(PromptComponent(
                type=PromptComponentType.EPISODIC_MEMORIES,
                content=episodic_context,
                priority=12,  # Higher than regular memories (13) to emphasize authority
                token_cost=150,
                required=False
            ))
            logger.info(f"✅ EPISODIC RECALL: Injected explicit recall context ({len(episodic_context)} chars)")
        else:
            logger.debug(f"⏭️  EPISODIC RECALL: No context generated (intent={any(k in message_context.content.lower() for k in ['remember', 'recall', 'when'])}, memories={len(relevant_memories)})")
        
        # ================================
        # COMPONENT 8: Conversation Summary - REMOVED (October 2025)
        # ================================
        # REMOVED: Zero-LLM "CONVERSATION FLOW" keyword extraction summary
        # 
        # REASONS FOR REMOVAL:
        # 1. REDUNDANT with semantic memories: "PAST CONVERSATIONS" already shows rich conversation history
        # 2. REDUNDANT with recent history: Last 15 message pairs provide immediate context
        # 3. TOO VAGUE: Zero-LLM keyword extraction produces generic summaries like "focusing on marine ecosystem topics"
        #    when semantic memories already show specific details (ocean acidification, coral pH, thesis deadline)
        # 4. NO UNIQUE VALUE: Doesn't provide information not already visible in conversation history
        # 5. WASTES TOKENS: Prompt space better used for MORE semantic memories or longer recent history
        # 6. USER FACTS provide unique persistent data (from knowledge graph) - that's the real "background"
        #
        # CONTEXT ARCHITECTURE (KEPT):
        # - ✅ PAST CONVERSATIONS: 10 semantic memories with User/Elena conversation turns (rich historical context)
        # - ✅ USER FACTS: Knowledge graph data (unique profile: location, job, pets, preferences)  
        # - ✅ RECENT HISTORY: 15 message pairs (immediate conversation continuity)
        #
        # This provides complete context without vague summaries that add no value.
        
        # ================================
        # COMPONENT 8B: Enriched Conversation Summaries (TIERED CONTEXT - October 2025)
        # ================================
        # ENHANCED: Intelligent tiered context system for long conversations
        # - For long conversations (>20 messages): Add enriched summary + recent memories
        # - For shorter conversations: Use recent memories only
        # - Prevents "context cliff" where AI forgets earlier conversation
        # Feature flagged for testing and gradual rollout
        
        # Check if conversation summary component is enabled before processing
        logger.info(f"🔍 ENRICHED CHECK: CONVERSATION_SUMMARY enabled={is_component_enabled(PromptComponentType.CONVERSATION_SUMMARY)}, ENABLE_ENRICHED_SUMMARIES={os.getenv('ENABLE_ENRICHED_SUMMARIES', 'false')}")
        if is_component_enabled(PromptComponentType.CONVERSATION_SUMMARY) and os.getenv('ENABLE_ENRICHED_SUMMARIES', 'false').lower() == 'true':
            try:
                from src.memory.vector_memory_system import get_normalized_bot_name_from_env
                bot_name = get_normalized_bot_name_from_env()
                
                # Check conversation history length to determine if tiered context needed
                recent_messages = await self._get_recent_messages_structured(
                    user_id=message_context.user_id
                )
                recent_message_count = len(recent_messages)
                logger.info(f"🔍 ENRICHED SUMMARIES: Checking conversation length - {recent_message_count} messages (threshold: >10)")
                
                # Apply tiered context for conversations with >10 messages
                if recent_message_count > 10:
                    logger.info(f"📚 Long conversation detected ({recent_message_count} messages) - using tiered context")
                    
                    # TIER 1: Add enriched summary from last 7 days (older messages)
                    # 🧠 RECALL ENHANCEMENT: Extract keywords directly from query text
                    search_keywords = None
                    query_lower = message_context.content.lower()
                    
                    # Check for recall patterns to extract keywords
                    recall_patterns_detected = any(pattern in query_lower for pattern in [
                        'we talked about', 'we discussed', 'we were talking about',
                        'remember when we talked', 'recall our discussion'
                    ])
                    
                    if recall_patterns_detected:
                        # Extract keywords from query using simple heuristic
                        # Query pattern: "we talked about X" → extract X
                        import re
                        
                        # Extract content after recall patterns
                        recall_patterns = [
                            r'we (?:talked|discussed|were talking) about (.+)',
                            r'remember when we (?:talked|discussed) (.+)',
                            r'recall (?:our discussion|talking) about (.+)'
                        ]
                        
                        for pattern in recall_patterns:
                            match = re.search(pattern, query_lower)
                            if match:
                                keyword_text = match.group(1).strip()
                                # Split on common separators
                                keywords = [kw.strip() for kw in re.split(r'[,;]|\band\b', keyword_text)]
                                search_keywords = [kw for kw in keywords if len(kw) > 2]  # Filter short words
                                logger.info(f"🔍 RECALL KEYWORDS: Extracted {search_keywords} from query")
                                break
                    
                    enriched_summaries = await self._retrieve_enriched_summaries(
                        user_id=message_context.user_id,
                        bot_name=bot_name,
                        days_back=7,   # Last week
                        limit=3 if search_keywords else 1,  # Get more summaries for recall queries
                        search_keywords=search_keywords
                    )
                    
                    if enriched_summaries:
                        summary = enriched_summaries[0]
                        start_date = summary['start_timestamp'].strftime('%Y-%m-%d')
                        end_date = summary['end_timestamp'].strftime('%Y-%m-%d')
                        timeframe = f"{start_date}" if start_date == end_date else f"{start_date} to {end_date}"
                        
                        # Build final summary text, optionally appending key topics
                        final_summary_text = f"{summary['summary_text']}"
                        if summary.get('key_topics'):
                            topics = ', '.join(summary['key_topics'][:5])
                            final_summary_text += f"\n\nKey topics discussed: {topics}"

                        # Add as dedicated CONVERSATION_SUMMARY component (Priority 14)
                        from src.prompts.cdl_component_factories import create_conversation_summary_component
                        summary_component = await create_conversation_summary_component(
                            summary_text=final_summary_text,
                            priority=14,  # After episodic memories (13)
                            timeframe_label=timeframe,
                            message_count=summary['message_count']
                        )
                        if summary_component:
                            assembler.add_component(summary_component)
                            logger.info(f"✅ TIERED CONTEXT: Added conversation summary component ({timeframe}, {summary['message_count']} messages)")
                    
                    # TIER 2: Recent detailed memories are already added at priority 13
                    # This gives us two-tier context: summary (older) + detailed (recent)
                    logger.info(f"✅ TIERED CONTEXT: Using two-tier system - summary + recent {min(recent_message_count, 30)} detailed messages")
                    
                else:
                    # Short conversation: Use recent memories only (already added at priority 13)
                    logger.debug(f"📚 Short conversation ({recent_message_count} messages) - using recent memories only")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to add enriched summaries to context: {e}")
        elif not is_component_enabled(PromptComponentType.CONVERSATION_SUMMARY):
            logger.debug("⏭️  Skipped conversation summary processing (CONVERSATION_SUMMARY component disabled)")
        else:
            logger.debug("📚 Enriched summaries disabled (ENABLE_ENRICHED_SUMMARIES=false)")
        
        # ================================
        # COMPONENT 8: Response Style Guidance (CDL-Based)
        # ================================
        # CDL RESPONSE_STYLE component (Priority 17) - replaces legacy hardcoded create_guidance_component
        from src.prompts.cdl_component_factories import create_response_style_component
        try:
            bot_name = get_normalized_bot_name_from_env()
            pool = await get_postgres_pool()
            if pool:
                enhanced_manager = create_enhanced_cdl_manager(pool)
                response_style_component = await create_response_style_component(
                    enhanced_manager=enhanced_manager,
                    character_name=bot_name,
                    priority=17
                )
                if response_style_component:
                    assembler.add_component(response_style_component)
                    logger.debug("✅ Added CDL-based RESPONSE_STYLE component (Priority 17)")
                else:
                    logger.warning("⚠️ No CDL response_style data - skipping component")
            else:
                logger.warning("⚠️ No PostgreSQL pool - skipping CDL RESPONSE_STYLE component")
        except Exception as e:
            logger.warning(f"⚠️ Failed to add CDL RESPONSE_STYLE component: {e}")
        
        # ================================
        # ASSEMBLE SYSTEM MESSAGE
        # ================================
        system_message_content = assembler.assemble(model_type="generic")
        assembly_metrics = assembler.get_assembly_metrics()
        
        logger.info(f"📊 STRUCTURED ASSEMBLY METRICS:")
        logger.info(f"  - Components: {assembly_metrics['total_components']}")
        logger.info(f"  - Tokens: {assembly_metrics['total_tokens']}")
        logger.info(f"  - Characters: {assembly_metrics['total_chars']}")
        logger.info(f"  - Within budget: {assembly_metrics['within_budget']}")
        
        # Build conversation messages array
        conversation_context = [
            {"role": "system", "content": system_message_content}
        ]
        
        # ================================
        # ADD RECENT CONVERSATION HISTORY
        # ================================
        recent_messages = await self._get_recent_messages_structured(message_context.user_id)
        if recent_messages:
            conversation_context.extend(recent_messages)
            logger.info(f"✅ STRUCTURED CONTEXT: Added {len(recent_messages)} recent messages")
        
        # ================================
        # ADD CURRENT USER MESSAGE
        # ================================
        conversation_context.append({
            "role": "user",
            "content": message_context.content
        })
        
        logger.info(f"✅ STRUCTURED CONTEXT: Final context has {len(conversation_context)} messages")
        return conversation_context
    
    def _build_episodic_recall_context(
        self,
        message_content: str,
        retrieved_memories: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Build explicit episodic recall context when user asks to remember past events.
        
        This allows the bot to reference retrieved memories as actual episodic recall
        rather than being blocked by AI ethics "no memory" disclaimers.
        
        Triggers on: "remember", "recall", "when", "what happened", "you told me"
        
        Returns: Formatted episodic context string or None if no recall intent detected
        """
        if not retrieved_memories or len(retrieved_memories) < 1:
            logger.debug(f"🧠 EPISODIC RECALL: Skipped - not enough memories ({len(retrieved_memories) if retrieved_memories else 0})")
            return None
        
        # Detect recall intent (simple keyword-based for now)
        message_lower = message_content.lower()
        recall_keywords = ['remember', 'recall', 'when', 'what happened', 'you told me', 'you said', 'earlier you']
        
        has_recall_intent = any(keyword in message_lower for keyword in recall_keywords)
        logger.debug(f"🧠 EPISODIC RECALL: Recall intent={has_recall_intent} for message '{message_content[:50]}...'")
        
        if not has_recall_intent:
            logger.debug(f"🧠 EPISODIC RECALL: Skipped - no recall keywords found")
            return None
        
        # Filter high-confidence memories (emotional_intensity >= 0.4 or top cross_encoder scores)
        high_conf_memories = []
        for mem in retrieved_memories[:10]:  # Look at top 10
            payload = mem.get('payload', {}) or {}
            metadata = mem.get('metadata', {}) or {}
            
            emotional_intensity = payload.get('emotional_intensity', metadata.get('emotional_intensity', 0.0))
            cross_encoder_score = mem.get('cross_encoder_score', 0.0)
            
            # Include if emotionally significant or high rerank score
            if emotional_intensity >= 0.4 or cross_encoder_score >= 0.6:
                high_conf_memories.append({
                    'content': mem.get('content', ''),
                    'timestamp': mem.get('timestamp', ''),
                    'emotional_intensity': emotional_intensity,
                    'metadata': metadata,
                    'payload': payload
                })
        
        if len(high_conf_memories) < 1:
            return None
        
        # Build episodic recall context
        recall_lines = []
        recall_lines.append("🧠 EPISODIC MEMORIES: You previously discussed these events with this user:")
        recall_lines.append("")
        
        for i, mem in enumerate(high_conf_memories[:3], 1):  # Top 3 memories
            content = mem['content'][:200]
            timestamp = mem['timestamp']
            
            # Format date if available
            date_str = "previously"
            try:
                if timestamp:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = dt.strftime('%B %d' if dt.year == datetime.now().year else '%B %d, %Y')
            except Exception:
                pass
            
            # Check if this is a conversation pair with bot response
            bot_response = mem['metadata'].get('bot_response') or mem['payload'].get('bot_response')
            if bot_response:
                recall_lines.append(f"{i}. [{date_str}] User said: \"{content}\"")
                recall_lines.append(f"   You responded: \"{bot_response[:200]}\"")
            else:
                recall_lines.append(f"{i}. [{date_str}] \"{content}\"")
        
        recall_lines.append("")
        recall_lines.append("✅ You MAY reference these specific past events naturally in your response.")
        recall_lines.append("⚠️ Only reference what is explicitly shown above - do not infer or elaborate beyond these facts.")
        
        return "\n".join(recall_lines)
    
    async def _build_memory_narrative_structured(
        self, 
        user_id: str, 
        relevant_memories: List[Dict[str, Any]]
    ) -> str:
        """
        Build memory narrative for structured context with temporal windows.
        
        Organizes conversation memories into time-based buckets to help LLMs
        distinguish between fresh topics, recent themes, and long-term context.
        This improves conversation continuity and natural temporal awareness.
        """
        if not relevant_memories:
            return ""
        
        memory_parts = []
        user_facts = []
        conversation_memories_with_time = []  # List of (memory, age_hours) tuples
        
        # Get character name for personalized conversation turn labels
        character_display_name = self.character_name.capitalize() if self.character_name else "Bot"
        
        # Separate facts from conversation memories and extract timestamps
        for memory in relevant_memories[:15]:  # Increased from 10 to 15 for richer semantic context
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            timestamp_str = memory.get("timestamp", "")
            
            if metadata.get("type") == "user_fact":
                fact = metadata.get("fact", content)[:300]
                if fact:
                    user_facts.append(fact)
            elif content:
                # 🔑 HYBRID APPROACH FIX: Extract bot response from metadata for full conversation context
                bot_response = metadata.get('bot_response', '') if isinstance(metadata, dict) else ''
                
                if bot_response:
                    # Format as full conversation turn with character's name
                    conversation_turn = f"User: {content[:300]}\n   {character_display_name}: {bot_response[:300]}"
                else:
                    # Fallback: Check if already formatted with labels, or just use content
                    if "User:" in content and ("Bot:" in content or character_display_name in content):
                        conversation_turn = f"{content[:500]}"
                    else:
                        conversation_turn = f"{content[:500]}"
                
                # Calculate age in hours for temporal bucketing
                age_hours = self._calculate_memory_age_hours(timestamp_str)
                conversation_memories_with_time.append((conversation_turn, age_hours))
        
        # Build USER FACTS section (not time-bucketed - facts are persistent)
        if user_facts:
            memory_parts.append(f"USER FACTS: {'; '.join(user_facts)}")
        
        # Build PAST CONVERSATIONS with temporal windows
        if conversation_memories_with_time:
            temporal_narrative = self._build_temporal_conversation_narrative(conversation_memories_with_time)
            if temporal_narrative:
                memory_parts.append(f"PAST CONVERSATIONS:\n{temporal_narrative}")
        
        return " || ".join(memory_parts) if memory_parts else ""
    
    def _calculate_memory_age_hours(self, timestamp_str: str) -> float:
        """Calculate how many hours ago a memory occurred."""
        try:
            if not timestamp_str:
                return 999999.0  # Very old if no timestamp
            
            from datetime import datetime
            # Parse ISO format timestamp
            memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_seconds = (datetime.utcnow().replace(tzinfo=memory_time.tzinfo) - memory_time).total_seconds()
            return age_seconds / 3600  # Convert to hours
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return 999999.0  # Treat as very old on error
    
    def _build_temporal_conversation_narrative(self, memories_with_time: List[tuple]) -> str:
        """
        Organize conversations into temporal windows for natural time awareness.
        
        Time buckets:
        - RECENT (< 24 hours): Fresh context, ongoing conversations
        - THIS WEEK (24h - 7 days): Recent themes and patterns
        - LONGER-TERM (> 7 days): Established relationship context
        
        Args:
            memories_with_time: List of (conversation_turn, age_hours) tuples
            
        Returns:
            Formatted temporal narrative string with human-readable timestamps
        """
        from src.utils.time_utils import format_relative_time_short
        from datetime import datetime, timedelta, timezone
        
        # Organize memories into time buckets with timestamps
        recent = []      # < 24 hours
        this_week = []   # 24 hours - 7 days (168 hours)
        longer_term = [] # > 7 days
        
        now = datetime.now(timezone.utc)
        
        for conversation_turn, age_hours in memories_with_time:
            # Calculate timestamp from age
            memory_time = now - timedelta(hours=age_hours)
            relative_time = format_relative_time_short(memory_time, now)
            
            # Prefix conversation with human-readable age
            timestamped_turn = f"({relative_time}) {conversation_turn}"
            
            if age_hours < 24:
                recent.append(timestamped_turn)
            elif age_hours < 168:  # 7 days = 168 hours
                this_week.append(timestamped_turn)
            else:
                longer_term.append(timestamped_turn)
        
        # Build temporal narrative with natural language headers
        narrative_parts = []
        
        if recent:
            recent_text = "\n".join(recent[:5])  # Max 5 recent memories
            narrative_parts.append(f"🕐 RECENT MEMORIES:\n{recent_text}")
        
        if this_week:
            week_text = "\n".join(this_week[:4])  # Max 4 weekly memories
            narrative_parts.append(f"📅 THIS WEEK:\n{week_text}")
        
        if longer_term:
            long_text = "\n".join(longer_term[:3])  # Max 3 long-term memories
            narrative_parts.append(f"📆 LONGER-TERM:\n{long_text}")
        
        return "\n\n".join(narrative_parts) if narrative_parts else ""
    
    async def _get_conversation_summary_structured(self, user_id: str) -> str:
        """
        Get conversation summary for structured context using zero-LLM Qdrant summarization.
        
        Uses semantic vector similarity to detect conversation themes and topics
        without requiring LLM calls. Provides context about ongoing conversation flow.
        
        Args:
            user_id: User identifier
            
        Returns:
            Formatted conversation summary string, or empty if no summary available
        """
        try:
            # Check if memory manager has summarization capability
            if not self.memory_manager or not hasattr(self.memory_manager, 'get_conversation_summary_with_recommendations'):
                logger.debug("📚 CONVERSATION SUMMARY: Memory manager lacks summarization capability")
                return ""
            
            # Get recent conversation history for pattern analysis
            recent_messages = await self._get_recent_messages_structured(user_id)
            if not recent_messages:
                logger.debug("📚 CONVERSATION SUMMARY: No recent messages for summarization")
                return ""
            
            # Call Qdrant-based zero-LLM summarization
            summary_data = await self.memory_manager.get_conversation_summary_with_recommendations(
                user_id=user_id,
                conversation_history=recent_messages,
                limit=20  # Analyze up to 20 related conversations for patterns
            )
            
            if not summary_data or not summary_data.get('topic_summary'):
                logger.debug("📚 CONVERSATION SUMMARY: No summary generated")
                return ""
            
            # Extract summary components
            topic_summary = summary_data.get('topic_summary', '')
            themes = summary_data.get('conversation_themes', '')
            method = summary_data.get('recommendation_method', 'unknown')
            related_count = summary_data.get('related_conversations_found', 0)
            
            # Format summary for prompt
            summary_parts = []
            
            if topic_summary:
                summary_parts.append(topic_summary)
            
            # Add theme context if available and different from summary
            if themes and themes not in topic_summary.lower():
                summary_parts.append(f"Themes: {themes}")
            
            # Add pattern indicator if significant related conversations found
            if related_count > 5:
                summary_parts.append(f"(recurring topic - {related_count} related conversations)")
            
            final_summary = ". ".join(summary_parts)
            
            logger.info(f"✅ CONVERSATION SUMMARY: Generated via {method} ({len(final_summary)} chars, {related_count} related)")
            return final_summary
            
        except Exception as e:
            logger.warning(f"⚠️ CONVERSATION SUMMARY: Failed to generate summary: {e}")
            return ""
    
    async def _build_user_facts_content(self, user_id: str, message_content: str = "") -> str:
        """
        Build user facts and preferences content for conversation context.
        
        Retrieves temporally-weighted facts from the knowledge graph and formats
        them for inclusion in the system prompt to make characters aware of
        user preferences, interests, and background information.
        
        Enhanced with context-based filtering to prioritize facts relevant to 
        the current conversation topic.
        
        Args:
            user_id: User identifier
            message_content: Current message content for context-based filtering
            
        Returns:
            Formatted user facts content string, or empty string if no facts available
        """
        try:
            # Check if knowledge router is available
            if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
                logger.debug("🔍 USER FACTS: Knowledge router not available")
                return ""

            # Get temporally relevant facts (recent facts weighted higher)
            facts = await self.bot_core.knowledge_router.get_temporally_relevant_facts(
                user_id=user_id,
                lookback_days=90,  # 3 months of facts
                limit=25  # Increased limit for better context filtering
            )
            
            if not facts:
                logger.debug(f"🔍 USER FACTS: No facts found for user {user_id}")
                return ""

            # Apply context-based filtering if message content provided
            if message_content:
                facts = await self._filter_facts_by_context(facts, message_content)
            
            # Format facts for conversation context
            fact_lines = []
            current_facts = []
            preferences = []
            background = []
            
            for fact in facts:
                entity_name = fact.get('entity_name', '')
                entity_type = fact.get('entity_type', '')
                relationship_type = fact.get('relationship_type', '')
                confidence = fact.get('weighted_confidence', fact.get('confidence', 0.5))
                potentially_outdated = fact.get('potentially_outdated', False)
                
                # Skip low confidence or potentially outdated facts
                if confidence < 0.6 or potentially_outdated:
                    continue
                
                # 🔑 FORMAT FIX: Include entity type for context (e.g., "Luna (cat)" instead of just "Luna")
                # This helps characters understand WHAT the entity is, not just the relationship
                entity_display = entity_name
                if entity_type and entity_type.lower() not in ['person', 'unknown', 'general']:
                    # Show type in parentheses for non-person entities (pets, places, things)
                    entity_display = f"{entity_name} ({entity_type})"
                
                # Categorize facts by type
                if relationship_type in ['likes', 'loves', 'enjoys', 'prefers']:
                    preferences.append(f"{relationship_type} {entity_display}")
                elif relationship_type in ['works_at', 'studies_at', 'lives_in']:
                    background.append(f"{relationship_type.replace('_', ' ')} {entity_display}")
                elif relationship_type in ['owns', 'has', 'knows']:
                    current_facts.append(f"{relationship_type} {entity_display}")
                else:
                    current_facts.append(f"{relationship_type.replace('_', ' ')} {entity_display}")
            
            # Dynamic limits based on content length to stay within context limits
            max_total_chars = 300  # Target max characters for facts
            current_chars = 0
            
            # Build formatted content with dynamic limiting
            if preferences and current_chars < max_total_chars:
                pref_content = f"PREFERENCES: {', '.join(preferences[:8])}"
                if current_chars + len(pref_content) < max_total_chars:
                    fact_lines.append(pref_content)
                    current_chars += len(pref_content)
            
            if background and current_chars < max_total_chars:
                bg_content = f"BACKGROUND: {', '.join(background[:5])}"
                if current_chars + len(bg_content) < max_total_chars:
                    fact_lines.append(bg_content)
                    current_chars += len(bg_content)
                    
            if current_facts and current_chars < max_total_chars:
                current_content = f"CURRENT: {', '.join(current_facts[:7])}"
                if current_chars + len(current_content) < max_total_chars:
                    fact_lines.append(current_content)
                    current_chars += len(current_content)
            
            if fact_lines:
                content = f"USER FACTS: {' | '.join(fact_lines)}"
                
                # Final length check - truncate if too long
                if len(content) > 400:
                    content = content[:397] + "..."
                    logger.info(f"📏 USER FACTS: Truncated facts content to stay within limits")
                
                logger.info(f"✅ USER FACTS: Built facts content for user {user_id} ({len(content)} chars, {len(facts)} facts, context-filtered: {bool(message_content)})")
                return content
            else:
                logger.debug(f"🔍 USER FACTS: No high-confidence facts for user {user_id}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ USER FACTS: Error building facts content for user {user_id}: {e}")
            return ""

    async def _filter_facts_by_context(self, facts: List[Dict[str, Any]], message_content: str) -> List[Dict[str, Any]]:
        """
        Filter facts based on relevance to current conversation context.
        
        Uses semantic similarity to prioritize facts that are topically relevant
        to the current message, helping to surface the most useful information.
        """
        try:
            if not facts or not message_content:
                return facts
            
            message_lower = message_content.lower()
            
            # Extract key topics from message
            topic_keywords = self._extract_topic_keywords(message_lower)
            
            # Score facts based on context relevance
            scored_facts = []
            for fact in facts:
                entity_name = fact.get('entity_name', '').lower()
                relationship_type = fact.get('relationship_type', '').lower()
                entity_type = fact.get('entity_type', '').lower()
                
                # Base score from temporal confidence
                score = fact.get('weighted_confidence', fact.get('confidence', 0.5))
                
                # Boost score if fact relates to message topics
                context_boost = 0.0
                
                # Direct entity mention
                if entity_name in message_lower:
                    context_boost += 0.4
                
                # Topic keyword matches
                for keyword in topic_keywords:
                    if keyword in entity_name or keyword in relationship_type:
                        context_boost += 0.2
                
                # Category relevance boosts
                if any(food_word in message_lower for food_word in ['food', 'eat', 'hungry', 'dinner', 'lunch', 'restaurant']):
                    if relationship_type in ['likes', 'loves', 'enjoys'] and any(food_type in entity_name for food_type in ['pizza', 'sushi', 'coffee', 'tea']):
                        context_boost += 0.3
                
                if any(pet_word in message_lower for pet_word in ['cat', 'dog', 'pet', 'animal']):
                    if 'cat' in entity_name or 'dog' in entity_name or relationship_type == 'owns' and entity_type == 'animal':
                        context_boost += 0.3
                
                if any(work_word in message_lower for work_word in ['work', 'job', 'career', 'office']):
                    if relationship_type in ['works_at', 'studies_at']:
                        context_boost += 0.3
                
                final_score = min(1.0, score + context_boost)
                scored_facts.append((fact, final_score))
            
            # Sort by relevance score and return top facts
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            
            # Return top 15 most relevant facts
            filtered_facts = [fact for fact, score in scored_facts[:15]]
            
            logger.debug(f"🎯 CONTEXT FILTER: Filtered {len(facts)} facts to {len(filtered_facts)} based on message context")
            return filtered_facts
            
        except Exception as e:
            logger.warning(f"Context filtering failed, using original facts: {e}")
            return facts

    def _extract_topic_keywords(self, message: str) -> List[str]:
        """Extract key topic words from message for context matching."""
        # Common stop words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must'}
        
        # Extract meaningful words (3+ characters, not stop words)
        words = [word.strip('.,!?;:"()[]{}') for word in message.split()]
        keywords = [word for word in words if len(word) >= 3 and word.lower() not in stop_words]
        
        return keywords[:10]  # Top 10 topic keywords
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Intelligently truncate text by removing the middle section while preserving
        the beginning (context/tone) and ending (conclusion/sentiment).
        
        This creates more coherent truncated messages than simple end-truncation,
        especially for emotional/roleplay conversations where the opening and closing
        are critical for understanding the message's intent and emotional arc.
        
        Args:
            text: The text to truncate
            max_length: Maximum length (including ellipsis marker)
            
        Returns:
            Truncated text with format: "beginning...ending"
        """
        if len(text) <= max_length:
            return text
        
        # Reserve space for ellipsis marker
        ellipsis = "..."
        available_length = max_length - len(ellipsis)
        
        if available_length < 100:  # Not enough space for meaningful truncation
            return text[:max_length - 3] + "..."
        
        # Split available space: 60% for beginning, 40% for ending
        # This preserves more opening context while keeping the emotional conclusion
        beginning_length = int(available_length * 0.6)
        ending_length = available_length - beginning_length
        
        beginning = text[:beginning_length].rstrip()
        ending = text[-ending_length:].lstrip()
        
        return f"{beginning}{ellipsis}{ending}"

    async def _get_recent_messages_structured(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent conversation messages for structured context."""
        try:
            # 🚨 FIX: Increased from 20 to 30 to prevent cutting off recent conversation context
            # With active users (300+ interactions), 20 was insufficient for 24h window
            # This retrieves up to 60 messages from Qdrant, then takes the 30 most recent
            recent_messages = await self.memory_manager.get_conversation_history(
                user_id=user_id,
                limit=30
            )
            
            if not recent_messages:
                return []
            
            logger.info(f"🔍 CONVERSATION HISTORY DEBUG: Retrieved {len(recent_messages)} messages from memory")
            for idx, msg in enumerate(recent_messages):
                role = msg.get('role', 'unknown')
                content_preview = msg.get('content', '')[:80]
                timestamp = msg.get('timestamp', 'no-timestamp')
                logger.debug(f"  [{idx}] role={role}, ts={timestamp}, content='{content_preview}...'")
            
            formatted_messages = []
            skip_next_bot_response = False
            
            # Split into older (truncated) vs recent (detailed)
            # 🚨 FIX: Increased from 6 to 10 to match increased limit of 30
            # Last 10 messages get full content, older ones truncated to 500 chars
            recent_full_count = 10
            older_messages = recent_messages[:-recent_full_count] if len(recent_messages) > recent_full_count else []
            recent_full_messages = recent_messages[-recent_full_count:] if len(recent_messages) > recent_full_count else recent_messages
            
            logger.info(f"🔍 MESSAGE SPLIT: {len(older_messages)} older (truncated), {len(recent_full_messages)} recent (full)")
            
            # Process older messages (truncated to 500 chars)
            for msg in older_messages:
                content = msg.get('content', '')
                # 🚨 FIX: Check 'role' field, not 'bot' field - memory returns role='bot' or role='user'
                role_value = msg.get('role', 'user')
                is_bot = role_value in ['bot', 'assistant']
                
                if content.startswith("!"):
                    skip_next_bot_response = True
                    continue
                
                if is_bot and skip_next_bot_response:
                    skip_next_bot_response = False
                    continue
                
                if not is_bot:
                    skip_next_bot_response = False
                
                # 🎯 SMART TRUNCATION: Cut middle, preserve beginning + ending for coherence
                truncated = self._smart_truncate(content, max_length=500)
                role = "assistant" if is_bot else "user"
                formatted_messages.append({"role": role, "content": truncated})
                logger.debug(f"  ✅ ADDED older message: role={role}, len={len(truncated)}")
            
            # Process recent messages (tiered: last 3 full, others 400 chars)
            for idx, msg in enumerate(recent_full_messages):
                content = msg.get('content', '')
                # 🚨 FIX: Check 'role' field, not 'bot' field - memory returns role='bot' or role='user'
                role_value = msg.get('role', 'user')
                is_bot = role_value in ['bot', 'assistant']
                
                if content.startswith("!"):
                    logger.debug(f"  ⏭️  SKIPPED (command): role={role_value}, content='{content[:50]}...'")
                    skip_next_bot_response = True
                    continue
                
                if is_bot and skip_next_bot_response:
                    logger.debug(f"  ⏭️  SKIPPED (after command): role={role_value}, content='{content[:50]}...'")
                    skip_next_bot_response = False
                    continue
                
                if not is_bot:
                    skip_next_bot_response = False
                
                # Last 3 messages get full content
                is_most_recent = idx >= len(recent_full_messages) - 3
                if is_most_recent:
                    message_content = content
                else:
                    # 🎯 SMART TRUNCATION: Cut middle, preserve beginning + ending for coherence
                    message_content = self._smart_truncate(content, max_length=400)
                
                role = "assistant" if is_bot else "user"
                formatted_messages.append({"role": role, "content": message_content})
                logger.debug(f"  ✅ ADDED recent message [{idx}]: role={role}, is_most_recent={is_most_recent}, len={len(message_content)}")
            
            logger.info(f"🔍 FINAL RESULT: {len(formatted_messages)} messages added to conversation context")
            return formatted_messages
            
        except Exception as e:
            logger.warning(f"Could not retrieve recent messages: {e}")
            return []

    async def _build_conversation_context_with_ai_intelligence(
        self, message_context: MessageContext, conversation_context: List[Dict[str, str]], ai_components: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Enhance conversation context with AI intelligence guidance using PromptAssembler.
        
        ✅ REFACTORED APPROACH: Uses PromptAssembler for proper component ordering
        
        This method receives the Phase 4 structured context and enhances it with:
        - TrendWise adaptive learning guidance (Priority 18)
        - Emotional intelligence context (Priority 18.5)
        - AI intelligence guidance (Priority 19)
        - Final "Respond as [character] to [user]:" line (Priority 20 - ALWAYS LAST)
        
        Uses a two-pass assembly:
        1. Phase 4 builds base prompt with CDL components and memory
        2. Phase 5.5 (here) adds AI intelligence components using proper priority system
        """
        from src.prompts.prompt_assembler import PromptAssembler
        from src.prompts.prompt_components import (
            PromptComponent, 
            PromptComponentType,
            create_ai_intelligence_component
        )
        
        # Create a second-pass assembler for AI intelligence components
        ai_assembler = PromptAssembler(max_tokens=None)
        
        # Extract existing system prompt and parse out the final "Respond as" line
        system_message_content = None
        final_respond_line = None
        base_system_content = None
        
        for i, msg in enumerate(conversation_context):
            if msg.get("role") == "system":
                system_message_content = msg["content"]
                
                # Extract the final "Respond as [character] to [user]:" line
                respond_as_pattern = "\nRespond as "
                last_respond_index = system_message_content.rfind(respond_as_pattern)
                
                if last_respond_index != -1:
                    base_system_content = system_message_content[:last_respond_index]
                    final_respond_line = system_message_content[last_respond_index:].strip()
                    logger.debug("🔧 REFACTOR: Extracted final 'Respond as' line for re-assembly")
                else:
                    # No "Respond as" line found - use full content as base
                    base_system_content = system_message_content
                    logger.warning("🔧 REFACTOR: No 'Respond as' line found in system prompt")
                break
        
        # REMOVED: COMPONENT 1 TrendWise ConfidenceAdapter (was contaminating personalities)
        
        # ================================
        # COMPONENT 2: Emotional Intelligence (Priority 18.5)
        # ================================
        # Check if emotional context component is enabled
        if is_component_enabled(PromptComponentType.EMOTIONAL_CONTEXT):
            try:
                from src.prompts.emotional_intelligence_component import create_emotional_intelligence_component
                
                bot_name = get_normalized_bot_name_from_env()
                
                # Create emotional intelligence component with InfluxDB trajectory data
                emotional_component, trajectory_metadata = await create_emotional_intelligence_component(
                    user_id=message_context.user_id,
                    bot_name=bot_name,
                    current_user_emotion=ai_components.get('emotion_data'),
                    current_bot_emotion=ai_components.get('bot_emotion'),
                    character_emotional_state=ai_components.get('character_emotional_state'),
                    temporal_client=self.temporal_client,
                    priority=19,  # Same priority as AI Intelligence (will appear before due to add order)
                    confidence_threshold=0.7,
                    intensity_threshold=0.5,
                    trajectory_window_minutes=60,  # Last hour
                    return_metadata=True  # Get trajectory data for footer display
                )
                
                if emotional_component:
                    # Keep priority 19 but it will appear before AI Intelligence due to add order
                    ai_assembler.add_component(emotional_component)
                    logger.info(
                        "🎭 EMOTIONAL INTELLIGENCE: Added component (priority 18.5, user=%s, bot=%s)",
                        ai_components.get('emotion_data', {}).get('primary_emotion') if ai_components.get('emotion_data') else None,
                        ai_components.get('bot_emotion', {}).get('primary_emotion') if ai_components.get('bot_emotion') else None
                    )
                
                # Store trajectory metadata for footer display
                if trajectory_metadata:
                    ai_components['emotional_trajectory_data'] = trajectory_metadata
                    logger.debug("🎭 EMOTIONAL TRAJECTORY: Stored metadata for footer display")
                
                if not emotional_component:
                    logger.debug("🎭 EMOTIONAL INTELLIGENCE: No significant emotions - component skipped")
                    
            except ImportError as import_err:
                logger.warning("Could not import emotional intelligence component: %s", import_err)
            except (AttributeError, TypeError, KeyError) as component_err:
                logger.warning("Failed to create emotional intelligence component: %s", component_err)
        else:
            logger.debug("⏭️  Skipped emotional intelligence processing (EMOTIONAL_INTELLIGENCE component disabled)")
        
        # ================================
        # COMPONENT 2.5: Strategic Intelligence (Priority 18.7)
        # ================================
        # Integrate background-computed strategic insights from enrichment worker
        # Provides personality-aware, memory-aware, and proactive engagement guidance
        strategic_intelligence = ai_components.get('strategic_intelligence', {})
        if strategic_intelligence and any(strategic_intelligence.values()):
            try:
                strategic_guidance_parts = []
                
                # 1. User Personality Awareness (from personality_profile engine)
                personality = strategic_intelligence.get('personality_profile')
                if personality:
                    comm_style = personality.get('communication_style', '')
                    formality = personality.get('formality_level', '')
                    verbosity = personality.get('verbosity_level', '')
                    
                    if comm_style or formality or verbosity:
                        personality_guidance = f"User communication style: {comm_style or 'unknown'}, formality: {formality or 'unknown'}, verbosity: {verbosity or 'unknown'}."
                        strategic_guidance_parts.append(personality_guidance)
                        logger.debug("🧠 STRATEGIC: Added personality awareness")
                
                # 2. Memory Health Awareness (from memory_health + memory_behavior engines)
                memory_health = strategic_intelligence.get('memory_health')
                memory_behavior = strategic_intelligence.get('memory_behavior')
                
                if memory_health:
                    avg_age_hours = memory_health.get('avg_memory_age_hours', 0)
                    forgetting_risk_raw = memory_health.get('forgetting_risk_memories', [])
                    
                    # Parse forgetting_risk if it's a JSON string
                    import json
                    if isinstance(forgetting_risk_raw, str):
                        try:
                            forgetting_risk = json.loads(forgetting_risk_raw)
                        except json.JSONDecodeError:
                            forgetting_risk = []
                    else:
                        forgetting_risk = forgetting_risk_raw if isinstance(forgetting_risk_raw, list) else []
                    
                    if avg_age_hours > 168:  # >7 days
                        memory_guidance = f"Note: User's conversation history is aging (avg {avg_age_hours/24:.0f} days old). Consider referencing past topics to reinforce memories."
                        strategic_guidance_parts.append(memory_guidance)
                        logger.debug("🧠 STRATEGIC: Added memory aging awareness")
                    
                    if forgetting_risk and len(forgetting_risk) > 0:
                        topics_at_risk = [m.get('topic', '') for m in forgetting_risk[:3] if isinstance(m, dict) and m.get('topic')]
                        if topics_at_risk:
                            risk_guidance = f"Topics at risk of being forgotten: {', '.join(topics_at_risk)}. Consider natural references if relevant."
                            strategic_guidance_parts.append(risk_guidance)
                            logger.debug("🧠 STRATEGIC: Added forgetting risk awareness")
                
                # 3. Proactive Engagement Opportunities (from engagement_opportunities engine)
                engagement = strategic_intelligence.get('engagement_opportunities')
                if engagement:
                    is_in_lull = engagement.get('is_in_lull', False)
                    unresolved_count = engagement.get('unresolved_topic_count', 0)
                    recommendations = engagement.get('recommendations', [])
                    
                    if is_in_lull and recommendations:
                        # Extract recommendation texts from JSONB array
                        if isinstance(recommendations, list) and len(recommendations) > 0:
                            rec_text = recommendations[0] if isinstance(recommendations[0], str) else str(recommendations[0])
                            engagement_guidance = f"Conversation lull detected. Consider: {rec_text}"
                            strategic_guidance_parts.append(engagement_guidance)
                            logger.debug("🧠 STRATEGIC: Added proactive engagement suggestion")
                    
                    if unresolved_count > 0:
                        unresolved_guidance = f"User has {unresolved_count} unresolved topics. Be receptive to revisiting previous subjects."
                        strategic_guidance_parts.append(unresolved_guidance)
                        logger.debug("🧠 STRATEGIC: Added unresolved topic awareness")
                
                # 4. Topic Transition Handling (from context_patterns engine)
                context_patterns = strategic_intelligence.get('context_patterns')
                if context_patterns:
                    switch_frequency = context_patterns.get('switch_frequency', 0)
                    coherence_score = context_patterns.get('context_coherence_score', 0.5)
                    
                    if switch_frequency > 5:  # Frequent topic switching
                        transition_guidance = f"User tends to switch topics frequently. Be adaptive and follow their conversational flow naturally."
                        strategic_guidance_parts.append(transition_guidance)
                        logger.debug("🧠 STRATEGIC: Added topic transition awareness")
                    
                    if coherence_score < 0.4:  # Low coherence
                        coherence_guidance = "User's topic transitions may be abrupt. Help maintain conversation coherence with smooth segues."
                        strategic_guidance_parts.append(coherence_guidance)
                        logger.debug("🧠 STRATEGIC: Added coherence support")
                
                # 5. Performance-Based Adaptation (from character_performance engine)
                performance = strategic_intelligence.get('character_performance')
                if performance:
                    quality_trend = performance.get('quality_trend', '')
                    engagement_trend = performance.get('engagement_trend', '')
                    recommendations = performance.get('recommendations', [])
                    
                    if quality_trend == 'declining' or engagement_trend == 'declining':
                        perf_guidance = "Recent conversation quality signals suggest adjusting approach. Focus on engagement and relevance."
                        strategic_guidance_parts.append(perf_guidance)
                        logger.debug("🧠 STRATEGIC: Added performance adaptation")
                
                # Assemble strategic intelligence component
                if strategic_guidance_parts:
                    strategic_content = "## Strategic Intelligence\n" + "\n".join(f"- {part}" for part in strategic_guidance_parts)
                    
                    strategic_component = PromptComponent(
                        type=PromptComponentType.GUIDANCE,
                        content=strategic_content,
                        priority=18.7,
                        required=False,
                        metadata={'cdl_type': 'STRATEGIC_INTELLIGENCE', 'engine_count': len([v for v in strategic_intelligence.values() if v])}
                    )
                    ai_assembler.add_component(strategic_component)
                    logger.info("🧠 STRATEGIC INTELLIGENCE: Added guidance component (priority 18.7, %d insights)", len(strategic_guidance_parts))
                
            except Exception as e:
                logger.warning("Strategic intelligence component failed (non-blocking): %s", e)
        
        # ================================
        # COMPONENT 3: AI Intelligence Guidance (Priority 19)
        # ================================
        ai_guidance = self._build_ai_intelligence_guidance(ai_components)
        if ai_guidance:
            ai_intelligence_component = create_ai_intelligence_component(
                content=ai_guidance,
                priority=19,
                required=False,
                metadata={'ai_components_summary': True}
            )
            ai_assembler.add_component(ai_intelligence_component)
            logger.info("🤖 AI INTELLIGENCE: Added guidance component (priority 19)")
        
        # ================================
        # COMPONENT 4: Final Response Guidance (Priority 20 - ALWAYS LAST)
        # ================================
        if final_respond_line:
            final_guidance_component = PromptComponent(
                type=PromptComponentType.GUIDANCE,
                content=final_respond_line,
                priority=20,
                required=True,
                metadata={'cdl_type': 'FINAL_RESPONSE_GUIDANCE'}
            )
            ai_assembler.add_component(final_guidance_component)
            logger.debug("🎯 FINAL GUIDANCE: Re-added 'Respond as' line (priority 20)")
        
        # ================================
        # ASSEMBLE AI INTELLIGENCE ADDITIONS
        # ================================
        ai_additions = ai_assembler.assemble(model_type="generic")
        
        # Combine base content with AI intelligence additions
        if base_system_content is None:
            base_system_content = ""
        
        enhanced_system_content = base_system_content
        if ai_additions.strip():
            enhanced_system_content += "\n\n" + ai_additions
        
        # Update the system message in conversation_context
        for i, msg in enumerate(conversation_context):
            if msg.get("role") == "system":
                conversation_context[i]["content"] = enhanced_system_content
                logger.info("✅ AI INTELLIGENCE REFACTOR: Re-assembled system prompt with proper component ordering")
                break
        
        return conversation_context

    def _summarize_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Create a summary of relevant memories."""
        if not memories:
            return "No previous conversation context available."
        
        # Take the most relevant memories and create a summary
        relevant_snippets = []
        for memory in memories[:5]:  # Top 5 most relevant
            content = memory.get('content', '')
            if content and len(content.strip()) > 0:
                relevant_snippets.append(content[:400])  # Increased from 200 to 400 chars for better memory context
        
        return " ... ".join(relevant_snippets) if relevant_snippets else "No relevant context found."

    def _extract_conversation_topics(self, conversation_parts: List[str]) -> List[str]:
        """Extract meaningful topics from conversation memory parts."""
        topics = []
        
        # Topic extraction patterns - look for meaningful content
        topic_keywords = {
            'food': ['pizza', 'burger', 'sandwich', 'taco', 'food', 'eat', 'meal', 'cook', 'recipe'],
            'activities': ['beach', 'swim', 'dive', 'hike', 'travel', 'visit', 'explore', 'adventure'],
            'greetings': ['hi', 'hello', 'good morning', 'good afternoon', 'good evening', 'hey'],
            'emotions': ['excited', 'happy', 'sad', 'worried', 'curious', 'interested'],
            'work': ['project', 'research', 'study', 'work', 'job', 'career'],
            'creativity': ['dream', 'creative', 'art', 'music', 'write', 'design', 'imagine'],
            'science': ['research', 'experiment', 'discover', 'analysis', 'data', 'ocean', 'marine']
        }
        
        # Combine all conversation parts into text for analysis
        text = " ".join(conversation_parts).lower()
        
        # Find topics based on keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(f"{topic.title()} discussion")
        
        # If no specific topics found, create generic topics from content
        if not topics and conversation_parts:
            # Try to extract meaningful phrases
            for part in conversation_parts[:3]:  # First 3 parts
                if len(part) > 20:  # Meaningful content
                    clean_part = part.replace('[Memory:', '').replace(']', '').strip()
                    if clean_part and not clean_part.lower().startswith('hi'):
                        topics.append(f"Discussion about {clean_part[:30]}...")
        
        return topics[:5]  # Max 5 topics

    def _extract_topic_from_memory(self, memory_part: str) -> str:
        """Extract a meaningful topic from a single memory part."""
        # Clean up memory formatting
        clean_content = memory_part.replace('[Memory:', '').replace('[Fact:', '').replace(']', '').strip()
        
        # Skip very short or greeting-only content
        if len(clean_content) < 10 or clean_content.lower() in ['hi', 'hello', 'hey', 'good afternoon']:
            return ""  # Return empty string instead of None
        
        # Try to create a meaningful topic summary
        if 'food' in clean_content.lower() or any(word in clean_content.lower() for word in ['pizza', 'burger', 'sandwich']):
            return "Food preferences"
        elif 'beach' in clean_content.lower() or 'swim' in clean_content.lower():
            return "Beach activities"
        elif any(word in clean_content.lower() for word in ['dream', 'creative', 'art']):
            return "Creative discussions"
        elif any(word in clean_content.lower() for word in ['research', 'science', 'ocean']):
            return "Science topics"
        else:
            # Generic topic from content
            return f"Conversation about {clean_content[:25]}..."

    def _create_conversation_summary(self, memory_part: str) -> str:
        """Create an actual summary of older conversation, not just a topic label.
        
        This is for conversations that are OLDER than the recent message context.
        We want summaries like: 'Discussed marine biology career paths and shared favorite documentaries'
        NOT just topic labels like: 'Science topics'
        
        🚨 FIX: Memories are stored as individual messages, not structured "User: X Bot: Y" format.
        We now work with the actual stored content format.
        """
        # Check if memory summarization is disabled
        if not os.getenv('ENABLE_MEMORY_SUMMARIZATION', 'true').lower() == 'true':
            return ""
            
        # Clean up memory formatting
        clean_content = memory_part.replace('[Memory:', '').replace('[Previous conversation:', '').replace(']', '').strip()
        
        # Skip very short or greeting-only content
        if len(clean_content) < 15 or clean_content.lower() in ['hi', 'hello', 'hey', 'good afternoon', 'good morning']:
            return ""
        
        # Create contextual summary based on content keywords
        lower_content = clean_content.lower()
        
        # Extract meaningful content (up to 400 chars for context)
        content_preview = clean_content[:400]
        
        # Try to create semantic summaries based on content
        if any(word in lower_content for word in ['coffee', 'meet', 'dinner', 'lunch', 'hang out', 'get together']):
            return f"Discussed meeting/social plans: {content_preview}"
        elif any(word in lower_content for word in ['food', 'pizza', 'burger', 'sandwich', 'taco', 'meal', 'eat', 'cook']):
            return f"Talked about food/meals: {content_preview}"
        elif any(word in lower_content for word in ['beach', 'ocean', 'swim', 'dive', 'surf', 'water', 'sea']):
            return f"Discussed beach/ocean activities: {content_preview}"
        elif any(word in lower_content for word in ['dream', 'creative', 'art', 'music', 'imagine', 'poetry', 'write']):
            return f"Creative/artistic conversation: {content_preview}"
        elif any(word in lower_content for word in ['research', 'science', 'marine', 'biology', 'experiment', 'study']):
            return f"Science/research discussion: {content_preview}"
        elif any(word in lower_content for word in ['work', 'job', 'career', 'project', 'profession', 'business']):
            return f"Work/career conversation: {content_preview}"
        elif any(word in lower_content for word in ['family', 'parent', 'mother', 'father', 'sibling', 'relative', 'background']):
            return f"Family/background discussion: {content_preview}"
        elif any(word in lower_content for word in ['adventure', 'travel', 'explore', 'journey', 'trek', 'expedition']):
            return f"Adventure/travel conversation: {content_preview}"
        elif any(word in lower_content for word in ['photography', 'photo', 'camera', 'picture', 'shoot', 'lens']):
            return f"Photography discussion: {content_preview}"
        else:
            # Generic but informative summary with full context
            return f"Previous exchange: {content_preview}"

    def _extract_user_facts_from_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Extract important user facts from raw memories with enhanced Discord name handling."""
        facts = []
        
        # Enhanced pattern matching for preferred names
        name_patterns = [
            r"(?:my name is|call me|i'm|i am)\s+([A-Z][a-z]+)",
            r"(?:name is|called)\s+([A-Z][a-z]+)",
            r"just (?:call me|use)\s+([A-Z][a-z]+)",
            r"prefer (?:to be called|being called)\s+([A-Z][a-z]+)"
        ]
        
        # Enhanced food and activity detection
        food_likes = set()
        activity_likes = set()
        
        food_categories = {
            'pizza': ['pizza', 'pizzas'],
            'burgers': ['burger', 'burgers'],
            'sandwiches': ['sandwich', 'sandwiches'],
            'tacos': ['taco', 'tacos']
        }
        
        activity_categories = {
            'beach activities': ['beach', 'ocean', 'surf'],
            'swimming': ['swim', 'swimming'],
            'diving': ['dive', 'diving', 'scuba'],
            'travel': ['travel', 'traveling']
        }
        
        for memory in memories:
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            
            # Check for preferred name facts
            if metadata.get("preferred_name"):
                preferred_name = metadata.get("preferred_name")
                facts.append(f"[Preferred name: {preferred_name}]")
            
            # Check for explicit name mentions in content
            elif "name is" in content.lower() or "call me" in content.lower():
                for pattern in name_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        name = match.group(1)
                        facts.append(f"[Preferred name: {name}]")
                        break
            
            # Enhanced food preference detection
            content_lower = content.lower()
            for food_category, keywords in food_categories.items():
                if any(keyword in content_lower for keyword in keywords):
                    food_likes.add(food_category)
            
            # Enhanced activity detection
            for activity_category, keywords in activity_categories.items():
                if any(keyword in content_lower for keyword in keywords):
                    activity_likes.add(activity_category)
        
        # Add aggregated preferences
        if food_likes:
            facts.append(f"[Likes: {', '.join(sorted(food_likes))}]")
        if activity_likes:
            facts.append(f"[Activities: {', '.join(sorted(activity_likes))}]")
        
        # Remove duplicates while preserving order
        unique_facts = []
        seen = set()
        for fact in facts:
            if fact not in seen:
                unique_facts.append(fact)
                seen.add(fact)
        
        return unique_facts[:7]  # Increased from 5 to 7

    async def _get_user_facts_from_postgres(
        self,
        user_id: str,
        bot_name: str,
        limit: int = 20
    ) -> List[str]:
        """
        Retrieve user facts from PostgreSQL knowledge graph (Phase 2 Architecture Cleanup).
        
        This method queries structured PostgreSQL data instead of parsing vector memory strings.
        Performance: ~2-5ms vs ~62-125ms (string parsing + vector search) = 12-25x faster.
        
        Returns formatted fact strings for prompt building.
        Example: "[pizza (likes)]", "[Mark (preferred_name)]"
        
        Args:
            user_id: User identifier
            bot_name: Bot name for character-aware fact retrieval
            limit: Maximum number of facts to retrieve
            
        Returns:
            List of formatted fact strings
        """
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            logger.debug("🔍 POSTGRES FACTS: Knowledge router not available, falling back to legacy")
            return []
        
        try:
            formatted_facts = []
            
            # Get character-aware facts from PostgreSQL
            facts = await self.bot_core.knowledge_router.get_character_aware_facts(
                user_id=user_id,
                character_name=bot_name,
                limit=limit
            )
            
            # Format facts: "[entity_name (relationship_type)]"
            for fact in facts:
                entity_name = fact.get('entity_name', '')
                relationship_type = fact.get('relationship_type', 'knows')
                entity_type = fact.get('entity_type', '')
                confidence = fact.get('confidence', 0.0)
                
                # Only include high-confidence facts
                if confidence >= 0.5:
                    # Add entity type context for clarity
                    if entity_type:
                        formatted_facts.append(f"[{entity_name} ({relationship_type}, {entity_type})]")
                    else:
                        formatted_facts.append(f"[{entity_name} ({relationship_type})]")
            
            # Get user preferences from PostgreSQL
            preferences = await self.bot_core.knowledge_router.get_all_user_preferences(
                user_id=user_id
            )
            
            # Format preferences: "[preference_key: preference_value]"
            # preferences is a dict like {"preferred_name": {"value": "Mark", "confidence": 0.9}}
            for pref_key, pref_data in preferences.items():
                if isinstance(pref_data, dict):
                    pref_value = pref_data.get('value', '')
                    confidence = pref_data.get('confidence', 0.0)
                    
                    # Only include high-confidence preferences
                    if confidence >= 0.5 and pref_value:
                        formatted_facts.append(f"[{pref_key}: {pref_value}]")
            
            if formatted_facts:
                logger.info(f"✅ POSTGRES FACTS: Retrieved {len(formatted_facts)} facts/preferences from PostgreSQL "
                          f"(facts: {len(facts)}, preferences: {len(preferences)})")
            else:
                logger.debug(f"🔍 POSTGRES FACTS: No facts/preferences found in PostgreSQL for user {user_id}")
            
            return formatted_facts
            
        except Exception as e:
            logger.error(f"❌ POSTGRES FACTS: Failed to retrieve from PostgreSQL: {e}", exc_info=True)
            return []

    def _extract_preferred_name_from_discord(self, discord_name: str) -> Optional[str]:
        """Extract likely preferred name from Discord username."""
        if not discord_name:
            return None
            
        # Handle compound names like "MarkAnthony" -> "Mark"
        # Look for capital letters that indicate word boundaries
        matches = re.findall(r'[A-Z][a-z]+', discord_name)
        if len(matches) >= 2:
            # Take the first name from compound names
            return matches[0]
        elif len(matches) == 1:
            return matches[0]
        
        # Handle other patterns
        if discord_name.lower().startswith('mark'):
            return 'Mark'
        
        return None

    def _build_ai_intelligence_guidance(self, ai_components: Dict[str, Any]) -> str:
        """Build AI intelligence guidance from comprehensive context for system prompts."""
        guidance_parts = []
        
        comprehensive_context = ai_components.get('comprehensive_context', {})
        if not comprehensive_context:
            return ""
        
        # Proactive Engagement Analysis (Phase 4.3)
        proactive_engagement_analysis = comprehensive_context.get('proactive_engagement_analysis')
        if proactive_engagement_analysis and isinstance(proactive_engagement_analysis, dict):
            intervention_needed = proactive_engagement_analysis.get('intervention_needed', False)
            engagement_strategy = proactive_engagement_analysis.get('recommended_strategy')
            if intervention_needed and engagement_strategy:
                # Translate internal strategy names into clear LLM instructions
                strategy_guidance_map = {
                    'curiosity_prompt': 'Ask an open, curious question to spark deeper conversation',
                    'topic_suggestion': 'Suggest a new topic related to shared interests',
                    'memory_connection': 'Reference a past conversation naturally to deepen connection',
                    'emotional_check_in': 'Gently check in on their emotional state with empathy',
                    'follow_up_question': 'Ask a thoughtful follow-up about the current topic',
                    'shared_interest': 'Connect around shared interests authentically',
                    'celebration': 'Celebrate their achievements with genuine enthusiasm',
                    'support_offer': 'Offer support or encouragement naturally'
                }
                strategy_instruction = strategy_guidance_map.get(engagement_strategy, 
                                                                  'Enhance conversation quality naturally')
                guidance_parts.append(f"🎯 ENGAGEMENT: {strategy_instruction}")
        
        # Conversation Analysis with Response Guidance
        conversation_analysis = comprehensive_context.get('conversation_analysis')
        if conversation_analysis and isinstance(conversation_analysis, dict):
            response_guidance = conversation_analysis.get('response_guidance')
            conversation_mode = conversation_analysis.get('conversation_mode', 'standard')
            relationship_level = conversation_analysis.get('relationship_level', 'acquaintance')
            
            if response_guidance:
                guidance_parts.append(f"💬 CONVERSATION: Mode={conversation_mode}, Level={relationship_level} - {response_guidance}")
        
        # Human-like Memory Optimization
        human_like_optimization = comprehensive_context.get('human_like_memory_optimization')
        if human_like_optimization and isinstance(human_like_optimization, dict):
            memory_insights = human_like_optimization.get('memory_insights')
            if memory_insights:
                guidance_parts.append(f"🧠 MEMORY: {memory_insights}")
        
        if guidance_parts:
            return "\n\n🤖 AI INTELLIGENCE GUIDANCE:\n" + "\n".join(f"• {part}" for part in guidance_parts)
        
        return ""

    async def _process_ai_components_parallel(self, message_context: MessageContext, 
                                            conversation_context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        🚀 SOPHISTICATED AI COMPONENT PROCESSING 🚀
        
        Process 9+ AI components in parallel using asyncio.gather for maximum efficiency.
        Restored from original events.py implementation with full Phase 4 intelligence.
        
        Components processed:
        1. Vector-native emotion analysis 
        2. Enhanced context analysis
        3. Dynamic personality profiling
        4. Phase 4 human-like intelligence
        5. Thread management analysis  
        6. Proactive engagement analysis
        7. Human-like memory optimization
        8. Conversation analysis
        9. Context switch detection
        """
        logger.info(f"🚀 AI COMPONENTS DEBUG: Starting parallel processing for user {message_context.user_id}")
        ai_components = {}
        
        try:
            logger.info("🧠 SOPHISTICATED AI PROCESSING: Starting 9-component parallel analysis")
            
            # 🚀 PHASE 4 SOPHISTICATED INTELLIGENCE PROCESSING 
            # Restored from original implementation with full asyncio.gather parallel processing
            
            # Prepare parallel tasks for sophisticated AI component processing
            tasks = []
            task_names = []
            
            # Task 1: Vector-native emotion analysis using existing infrastructure
            if self.bot_core and hasattr(self.bot_core, 'phase2_integration'):
                emotion_task = self._analyze_emotion_vector_native(
                    message_context.user_id, 
                    message_context.content,
                    message_context
                )
                tasks.append(emotion_task)
                task_names.append("emotion_analysis")
            
            # NOTE: Advanced emotion analysis moved to serial execution after parallel tasks
            # to avoid RoBERTa model race conditions
            
            # PHASE 2 OPTIMIZATION: Strategic components removed from hot path
            # These will be moved to background workers with <5min freshness target:
            # - Memory Aging Intelligence (Task 1.8)
            # - Character Performance Intelligence (Task 1.9)
            # - Dynamic Personality Profiling (Task 3)
            # - Context Switch Detection (Task 9)
            # - Human-Like Memory Optimization (Task 7)
            # - Conversation Pattern Analysis (Task 8)
            # - Proactive Engagement (Task 7 - conditional, moved to background)
            
            # Task 2: Enhanced context analysis using hybrid detector
            context_task = self._analyze_enhanced_context(
                message_context.content,
                conversation_context,
                message_context.user_id
            )
            tasks.append(context_task)
            task_names.append("context_analysis")
            
            # Task 4: Phase 4 human-like intelligence processing
            logger.debug(f"🎯 TASK DEBUG: bot_core exists: {self.bot_core is not None}")
            if self.bot_core:
                logger.debug(f"🎯 TASK DEBUG: has phase2_integration: {hasattr(self.bot_core, 'phase2_integration')}")
            if self.bot_core and hasattr(self.bot_core, 'phase2_integration'):
                logger.debug("🎯 TASK DEBUG: Creating conversation_intelligence task")
                conversation_intelligence_task = self._process_conversation_intelligence_sophisticated(
                    message_context.user_id,
                    message_context.content,
                    message_context,
                    conversation_context
                )
                
                tasks.append(conversation_intelligence_task)
                task_names.append("conversation_intelligence")
            
            # Task 5: Unified Character Intelligence Coordination (PHASE 4A)
            if self.character_intelligence_coordinator:
                logger.debug("🧠 TASK DEBUG: Creating unified character intelligence task")
                character_intelligence_task = self._process_unified_character_intelligence(
                    message_context.user_id,
                    message_context.content,
                    message_context,
                    conversation_context
                )
                
                tasks.append(character_intelligence_task)
                task_names.append("unified_character_intelligence")
                
            # Task 6: REMOVED - Thread management (dead code - manager never initialized)
            # The conversation_thread_manager attribute is never set on bot_core,
            # so this hasattr check always fails and returns None.
            # Removing to avoid unnecessary parallel task overhead.
            
            # Task 7: REMOVED - Proactive engagement (moved to background)
            # Heavy analysis (~50-150ms) that rarely contributes guidance.
            # Will be processed by background worker with cached state in PostgreSQL.
            
            # Task 8: REMOVED - Human-like memory optimization (moved to background)
            # Strategic memory optimization can be pre-computed and cached.
            
            # Task 9: REMOVED - Conversation pattern analysis (moved to background)
            # Pattern detection provides guidance but can be pre-computed.
            
            # Task 10: REMOVED - Context switch detection (moved to background)
            # Context switches can be detected by background worker analyzing conversation flow.
            
            logger.info(f"🧠 SOPHISTICATED AI PROCESSING: Executing {len(tasks)} components in parallel")
            
            # 🚀 PARALLEL EXECUTION: Use asyncio.gather for maximum efficiency
            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions gracefully
            idx = 0
            for task_name in task_names:
                if idx < len(results):
                    result = results[idx]
                    if not isinstance(result, Exception):
                        ai_components[task_name] = result
                        logger.debug(f"✅ {task_name}: Successfully processed")
                    else:
                        ai_components[task_name] = None
                        logger.warning(f"⚠️ {task_name}: Failed with {type(result).__name__}: {result}")
                    idx += 1
            
            # 🚀 SOPHISTICATED RESULT INTEGRATION: Merge components with intelligent prioritization
            
            # 🎭 SERIAL ADVANCED EMOTION ANALYSIS: Run after basic analysis to avoid race conditions
            basic_emotion_result = ai_components.get('emotion_analysis')
            if basic_emotion_result:
                logger.info("🎭 SERIAL EMOTION: Running advanced emotion analysis with basic results")
                try:
                    advanced_emotion_result = await self._analyze_advanced_emotion_intelligence_with_basic(
                        message_context.user_id,
                        message_context.content,
                        message_context,
                        basic_emotion_result  # Pass the basic analysis result
                    )
                    if advanced_emotion_result:
                        ai_components['advanced_emotion_intelligence'] = advanced_emotion_result
                        logger.info("🎭 SERIAL EMOTION: Advanced analysis completed successfully")
                    else:
                        logger.warning("🎭 SERIAL EMOTION: Advanced analysis returned None")
                except Exception as e:
                    logger.warning(f"🎭 SERIAL EMOTION: Advanced analysis failed: {e}")
                    ai_components['advanced_emotion_intelligence'] = None
            else:
                logger.warning("🎭 SERIAL EMOTION: No basic emotion analysis available for advanced processing")
            
            # Extract core components for backward compatibility
            ai_components['emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['external_emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['context_analysis'] = ai_components.get('context_analysis')
            ai_components['personality_context'] = ai_components.get('personality_analysis')
            ai_components['conversation_context'] = ai_components.get('conversation_intelligence')
            
            # Bridge Phase 3 context switches from OLD path to NEW path structure for test compatibility
            conversation_intelligence = ai_components.get('conversation_intelligence')
            logger.debug(f"🌉 BRIDGE DEBUG: conversation_intelligence type: {type(conversation_intelligence)}")
            if conversation_intelligence and isinstance(conversation_intelligence, dict):
                conversation_context_switches = conversation_intelligence.get('conversation_context_switches')
                logger.debug(f"🌉 BRIDGE DEBUG: conversation_context_switches: {len(conversation_context_switches) if conversation_context_switches else 'None'}")
                if conversation_context_switches:
                    ai_components['context_switches'] = conversation_context_switches
                    logger.debug(f"✅ Bridged {len(conversation_context_switches)} context switches from OLD to NEW path")
                else:
                    logger.warning("🌉 BRIDGE WARNING: No conversation_context_switches found in conversation_intelligence")
            else:
                logger.warning(f"🌉 BRIDGE WARNING: conversation_intelligence is not a valid dict: {conversation_intelligence}")
            
            # Advanced Emotion Intelligence integration
            advanced_emotion = ai_components.get('advanced_emotion_intelligence')
            if advanced_emotion:
                # Enhance existing emotion_data with advanced insights
                if ai_components['emotion_data']:
                    # Merge advanced data with existing RoBERTa analysis
                    ai_components['emotion_data'].update({
                        'advanced_analysis': advanced_emotion,
                        'multi_modal': True,
                        'secondary_emotions': advanced_emotion.get('secondary_emotions', []),
                        'emotional_trajectory': advanced_emotion.get('emotional_trajectory', []),
                        'cultural_context': advanced_emotion.get('cultural_context')
                    })
                else:
                    # Use advanced analysis as primary emotion data
                    ai_components['emotion_data'] = advanced_emotion
            
            # 🎭 NEW: Tactical Big Five Emotional Adaptation
            # Create emotional adaptation strategy based on user's emotional state
            logger.info(f"🎭 TACTICAL BIG FIVE DEBUG: emotional_context_engine exists: {self.emotional_context_engine is not None}")
            logger.info(f"🎭 TACTICAL BIG FIVE DEBUG: emotion_analysis in ai_components: {'emotion_analysis' in ai_components}")
            logger.info(f"🎭 TACTICAL BIG FIVE DEBUG: ai_components keys at this point: {list(ai_components.keys())}")
            if self.emotional_context_engine and ai_components.get('emotion_analysis'):
                try:
                    emotion_analysis = ai_components['emotion_analysis']
                    relationship_state = ai_components.get('relationship_state', {})
                    
                    # Map primary emotion to EmotionalState enum
                    primary_emotion_str = emotion_analysis.get('primary_emotion', 'neutral').upper()
                    try:
                        primary_emotion = EmotionalState[primary_emotion_str]
                    except KeyError:
                        primary_emotion = EmotionalState.NEUTRAL
                    
                    # Create EmotionalContext from emotion analysis with all required fields
                    emotional_context = EmotionalContext(
                        user_id=message_context.user_id,
                        context_id=f"{message_context.user_id}_{datetime.now().isoformat()}",
                        timestamp=datetime.now(),
                        # Current emotional state
                        primary_emotion=primary_emotion,
                        emotion_confidence=emotion_analysis.get('confidence', 0.5),
                        emotion_intensity=emotion_analysis.get('confidence', 0.5),
                        # Emotional analysis data
                        all_emotions=emotion_analysis.get('all_emotions', {}),
                        sentiment_score=emotion_analysis.get('sentiment_score', 0.0),
                        emotional_triggers=[],
                        # Personality context
                        personality_alignment=0.8,  # Default - could be enhanced later
                        relationship_depth=relationship_state.get('normalized_trust', 0.5),
                        trust_level=relationship_state.get('normalized_trust', 0.5),
                        # Contextual factors
                        conversation_length=len(conversation_context) if conversation_context else 0,
                        response_time_context=None,
                        topic_emotional_weight=emotion_analysis.get('confidence', 0.5),
                        # Adaptation recommendations
                        response_tone_adjustment='neutral',
                        empathy_level_needed=min(1.0, emotion_analysis.get('confidence', 0.5) + 0.2),
                        support_opportunity=primary_emotion in [EmotionalState.SADNESS, EmotionalState.FEAR],
                        celebration_opportunity=primary_emotion == EmotionalState.JOY
                    )
                    
                    # Create adaptation strategy with Big Five tactical shifts
                    adaptation_strategy = await self.emotional_context_engine.create_adaptation_strategy(
                        emotional_context=emotional_context
                    )
                    
                    if adaptation_strategy and adaptation_strategy.big_five_tactical_shifts:
                        # Add to ai_components for CDL prompt integration
                        ai_components['emotional_adaptation'] = {
                            'big_five_tactical_shifts': adaptation_strategy.big_five_tactical_shifts,
                            'strategy_id': adaptation_strategy.strategy_id,
                            'tone_adjustments': adaptation_strategy.tone_adjustments,
                            'empathy_emphasis': adaptation_strategy.empathy_emphasis
                        }
                        logger.info(f"🎭 Tactical Big Five adaptation enabled: {adaptation_strategy.big_five_tactical_shifts}")
                    
                except Exception as e:
                    logger.warning(f"🎭 Emotional adaptation processing failed: {e}")
                    import traceback
                    logger.debug(f"🎭 Traceback: {traceback.format_exc()}")
                    ai_components['emotional_adaptation'] = None
                logger.info("🎭 Enhanced emotion analysis with advanced multi-modal intelligence")
            
            # Memory Aging Intelligence integration
            memory_aging = ai_components.get('memory_aging_intelligence')
            if memory_aging:
                # Add memory health context for AI conversation optimization
                ai_components['memory_health'] = {
                    'status': memory_aging.get('health_status', 'unknown'),
                    'optimization_needed': memory_aging.get('health_status') in ['poor', 'fair'],
                    'total_memories': memory_aging.get('total_memories', 0),
                    'prunable_ratio': memory_aging.get('flagged_ratio', 0),
                    'analysis_time': memory_aging.get('processing_time', 0)
                }
                logger.info("🧠 Added memory aging intelligence: %s health (%d memories, %.1f%% prunable)",
                           memory_aging.get('health_status', 'unknown'),
                           memory_aging.get('total_memories', 0),
                           memory_aging.get('flagged_ratio', 0) * 100)
            
            # Character Performance Intelligence integration
            character_performance = ai_components.get('character_performance_intelligence')
            if character_performance:
                # Add character optimization insights for conversation enhancement
                ai_components['character_optimization'] = {
                    'performance_status': character_performance.get('performance_status', 'unknown'),
                    'overall_score': character_performance.get('overall_score', 0.5),
                    'optimization_opportunities': character_performance.get('optimization_opportunities', []),
                    'trait_correlations': character_performance.get('trait_correlations', {}),
                    'needs_optimization': character_performance.get('performance_status') in ['fair', 'needs_improvement']
                }
                logger.info("🎭 Added character performance intelligence: %s performance (%.3f score, %d opportunities)",
                           character_performance.get('performance_status', 'unknown'),
                           character_performance.get('overall_score', 0.5),
                           len(character_performance.get('optimization_opportunities', [])))
            
            # Build comprehensive context from all AI components
            comprehensive_context = {}
            
            # Add conversation intelligence context
            if ai_components.get('conversation_intelligence'):
                conversation_context = ai_components['conversation_intelligence']
                if hasattr(conversation_context, '__dict__'):
                    comprehensive_context.update({
                        'conversation_context': conversation_context,
                        'interaction_type': getattr(conversation_context, 'interaction_type', None),
                        'conversation_mode': getattr(conversation_context, 'conversation_mode', None),
                    })
            
            # Add thread management results (Advanced Thread Analysis)
            if ai_components.get('thread_management'):
                comprehensive_context['conversation_thread_analysis'] = ai_components['thread_management']
                logger.info("🧠 Added Advanced Thread Management results to context")
            
            # Add proactive engagement results (Phase 4.3)
            if ai_components.get('proactive_engagement'):
                comprehensive_context['proactive_engagement_analysis'] = ai_components['proactive_engagement']
                logger.info("🧠 Added Phase 4.3 Proactive Engagement results to context")
            
            # Add human-like memory optimization
            if ai_components.get('human_like_memory'):
                human_like_context = ai_components['human_like_memory']
                if isinstance(human_like_context, dict):
                    comprehensive_context.update({
                        'human_like_context': human_like_context.get('human_context', {}),
                        'human_like_memories': human_like_context.get('memories', []),
                        'human_like_performance': human_like_context.get('search_performance', {})
                    })
                    logger.info("🧠 Added human-like memory optimization to context")
            
            # Add conversation analysis for enhanced response guidance
            if ai_components.get('conversation_analysis'):
                conversation_analysis = ai_components['conversation_analysis']
                if isinstance(conversation_analysis, dict):
                    comprehensive_context.update({
                        'conversation_analysis': conversation_analysis,
                        'response_guidance': conversation_analysis.get('response_guidance', ''),
                        'conversation_mode': conversation_analysis.get('mode', 'standard'),
                        'interaction_type': conversation_analysis.get('interaction_type', 'general'),
                        'personality_type': conversation_analysis.get('personality_type', 'default'),
                        'relationship_level': conversation_analysis.get('relationship_level', 'acquaintance')
                    })
                    logger.info("🧠 Added conversation analysis for enhanced response guidance")
            
            # Add context switches for conversation flow
            if ai_components.get('context_switches'):
                comprehensive_context['context_switches'] = ai_components['context_switches']
                logger.info("🧠 Added context switch detection to comprehensive context")
            
            # Store comprehensive context in ai_components
            ai_components['comprehensive_context'] = comprehensive_context if comprehensive_context else None
            ai_components['enhanced_system_prompt'] = None  # Generated later in CDL enhancement
            
            logger.info(f"✅ SOPHISTICATED AI PROCESSING: Completed {len(task_names)} components with comprehensive integration")
            logger.info(f"🧠 Final comprehensive context size: {len(str(comprehensive_context))} chars")
            logger.info(f"🧠 Final comprehensive context keys: {list(comprehensive_context.keys())}")
            
            # 🌟 CHARACTER LEARNING MOMENT DETECTION: Add learning visibility to user experience
            try:
                logger.debug("🌟 PROCESSING: Character learning moment detection")
                learning_moments_result = await self._process_character_learning_moments(
                    message_context.user_id,
                    message_context.content,
                    message_context,
                    conversation_context,
                    ai_components
                )
                
                if learning_moments_result:
                    ai_components['character_learning_moments'] = learning_moments_result
                    logger.info("🌟 Added character learning moments to AI components (detected %d moments)", 
                               learning_moments_result.get('learning_moments_detected', 0))
                else:
                    ai_components['character_learning_moments'] = None
                    logger.debug("🌟 No learning moments detected or detector unavailable")
                    
            except Exception as e:
                logger.warning("🌟 Character learning moment detection failed: %s", str(e))
                ai_components['character_learning_moments'] = None
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Sophisticated AI component processing failed: %s", str(e))
            # Fallback to basic components
            ai_components = {
                'emotion_data': None,
                'external_emotion_data': None,
                'context_analysis': None,
                'personality_context': None,
                'conversation_intelligence': None,
                'comprehensive_context': None,
                'enhanced_system_prompt': None
            }
        
        return ai_components

    async def _analyze_enhanced_context(self, content: str, conversation_context: List[Dict[str, str]], 
                                      user_id: str) -> Dict[str, Any]:
        """Enhanced context analysis with vector boost and confidence scoring."""
        try:
            # Use the hybrid context detector for sophisticated analysis
            context_result = self.detect_context_patterns(
                message=content,
                conversation_history=conversation_context,
                vector_boost=True,
                confidence_threshold=0.7
            )
            logger.debug(f"Enhanced context analysis successful for user {user_id}")
            return context_result
        except Exception as e:
            logger.debug(f"Enhanced context analysis failed: {e}")
            return {
                'needs_ai_guidance': True,
                'needs_memory_context': True,
                'needs_personality': True,
                'needs_voice_style': True,
                'is_greeting': False,
                'is_simple_question': False,
                'confidence_scores': {},
                'detection_method': 'fallback'
            }

    async def _process_conversation_intelligence_sophisticated(self, user_id: str, content: str, 
                                                       message_context: MessageContext,
                                                       conversation_context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Sophisticated Phase 4 intelligence processing with full integration."""
        logger.debug(f"🎯 STARTING SOPHISTICATED PHASE 4 PROCESSING for user {user_id}")
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                logger.debug("🔍 Bot core or phase2_integration not available")
                # Create adapter for Discord-specific component first
                discord_message = create_discord_message_adapter(message_context)
                # Create minimal result with Phase 3 data
                conversation_context_switches = await self._analyze_context_switches(user_id, content, discord_message)
                empathy_response_calibration = await self._calibrate_empathy_response(user_id, content, discord_message)
                return {
                    'conversation_mode': 'standard',
                    'interaction_type': 'general',
                    'response_guidance': 'natural_conversation',
                    'conversation_context_switches': conversation_context_switches,
                    'empathy_response_calibration': empathy_response_calibration
                }
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Use the stable OLD Phase 3 + Phase 4 processing method
            # Note: NEW Phase 3 memory clustering has been obsoleted by PostgreSQL graph architecture
            logger.info("🔄 Using stable OLD Phase 3 + Phase 4 processing method")
            
            # Process Phase 3 components separately (like the old working system)
            conversation_context_switches = await self._analyze_context_switches(user_id, content, discord_message)
            empathy_response_calibration = await self._calibrate_empathy_response(user_id, content, discord_message)
            
            # Process with conversation intelligence sophistication
            try:
                logger.debug(f"🔧 CALLING process_conversation_intelligence for user {user_id}")
                conversation_context_result = await self.bot_core.phase2_integration.process_conversation_intelligence(
                    user_id=user_id,
                    message=discord_message,
                    recent_messages=conversation_context,
                    external_emotion_data=None,
                    phase2_context=None
                )
                logger.debug(f"🔧 RESULT from process_conversation_intelligence: {type(conversation_context_result)} = {conversation_context_result}")
            except Exception as e:
                logger.warning(f"🔧 Phase 2 integration failed, creating minimal result: {e}")
                # Create minimal result to preserve Phase 3 data
                conversation_context_result = {
                    'conversation_mode': 'standard',
                    'interaction_type': 'general',
                    'response_guidance': 'natural_conversation'
                }
            
            # Add Phase 3 results to the conversation intelligence context
            if isinstance(conversation_context_result, dict):
                conversation_context_result['conversation_context_switches'] = conversation_context_switches
                conversation_context_result['empathy_response_calibration'] = empathy_response_calibration
                logger.debug(f"🔧 SOPHISTICATED DEBUG: Added Phase 3 results - switches: {len(conversation_context_switches) if conversation_context_switches else 'None'}, empathy: {empathy_response_calibration is not None}")
            else:
                logger.warning(f"🔧 SOPHISTICATED DEBUG: conversation_context_result is not dict: {type(conversation_context_result)} = {conversation_context_result}")
            
            logger.debug(f"Sophisticated conversation intelligence processing successful for user {user_id}")
            logger.debug(f"🔧 SOPHISTICATED DEBUG: Returning result type: {type(conversation_context_result)}")
            return conversation_context_result
            
        except Exception as e:
            logger.debug(f"Sophisticated Phase 4 intelligence processing failed: {e}")
            return None

    async def _process_unified_character_intelligence(self, user_id: str, content: str, 
                                                    message_context: MessageContext,
                                                    conversation_context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Process Unified Character Intelligence Coordination (PHASE 4A)."""
        logger.debug(f"🧠 STARTING UNIFIED CHARACTER INTELLIGENCE for user {user_id}")
        try:
            if not self.character_intelligence_coordinator:
                logger.debug("🧠 Character intelligence coordinator not available")
                return None
            
            # Get character name from environment (bot-specific)
            character_name = get_normalized_bot_name_from_env()
            if not character_name:
                logger.warning("🧠 Character name not available from environment")
                return None
            
            # Create intelligence request
            from src.characters.learning.unified_character_intelligence_coordinator import IntelligenceRequest, CoordinationStrategy
            
            request = IntelligenceRequest(
                user_id=user_id,
                message_content=content,
                character_name=character_name,
                conversation_context=conversation_context,
                coordination_strategy=CoordinationStrategy.ADAPTIVE
            )
            
            # Coordinate unified intelligence
            intelligence_response = await self.character_intelligence_coordinator.coordinate_intelligence(request)
            
            # Convert response to dictionary for ai_components integration
            result = {
                'enhanced_response': intelligence_response.enhanced_response,
                'system_contributions': {
                    system.value: contribution 
                    for system, contribution in intelligence_response.system_contributions.items()
                },
                'coordination_metadata': intelligence_response.coordination_metadata,
                'performance_metrics': intelligence_response.performance_metrics,
                'character_authenticity_score': intelligence_response.character_authenticity_score,
                'confidence_score': intelligence_response.confidence_score,
                'processing_time_ms': intelligence_response.processing_time_ms
            }
            
            logger.info(f"🧠 Unified character intelligence successful for {character_name} (user {user_id})")
            return result
            
        except Exception as e:
            logger.error(f"🧠 Unified character intelligence failed: {e}")
            return None

    async def _process_character_learning_moments(self, user_id: str, content: str,
                                                message_context: MessageContext,
                                                conversation_context: List[Dict[str, str]],
                                                ai_components: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Character Learning Moment Detection for enhanced user experience."""
        logger.debug("🌟 STARTING CHARACTER LEARNING MOMENT DETECTION for user %s", user_id)
        try:
            if not self.learning_moment_detector:
                logger.debug("🌟 Learning moment detector not available")
                return None
            
            # Get character name from environment
            character_name = get_normalized_bot_name_from_env()
            if not character_name:
                logger.warning("🌟 Character name not available from environment")
                return None
            
            # Extract data from ai_components for learning moment context
            emotional_context = ai_components.get('emotional_intelligence', {})
            
            # Safe extraction with None handling for chained .get() calls
            character_intelligence = ai_components.get('character_intelligence')
            if character_intelligence and isinstance(character_intelligence, dict):
                temporal_data = character_intelligence.get('coordination_metadata', {})
                system_contributions = character_intelligence.get('system_contributions', {})
                if isinstance(system_contributions, dict):
                    episodic_memories = system_contributions.get('character_episodic_intelligence')
                else:
                    episodic_memories = None
            else:
                temporal_data = {}
                episodic_memories = None
            
            # Create learning moment context
            from src.characters.learning.character_learning_moment_detector import LearningMomentContext
            
            context = LearningMomentContext(
                user_id=user_id,
                character_name=character_name,
                current_message=content,
                conversation_history=conversation_context,
                emotional_context=emotional_context,
                temporal_data=temporal_data,
                episodic_memories=episodic_memories
            )
            
            # Detect learning moments
            learning_moments = await self.learning_moment_detector.detect_learning_moments(context)
            
            # Process detected moments for conversation integration
            result = {
                'learning_moments_detected': len(learning_moments),
                'moments': [],
                'surface_moment': False,
                'suggested_integration': None
            }
            
            if learning_moments:
                # Select the best moment to potentially surface
                best_moment = learning_moments[0]  # Already sorted by confidence
                
                # Check if this moment should be surfaced
                conversation_state = {
                    'conversation_history': conversation_context,
                    'current_emotion': emotional_context.get('primary_emotion'),
                    'recent_learning_moments': (message_context.metadata or {}).get('recent_learning_moments', 0),
                    'total_recent_messages': len(conversation_context)
                }
                
                should_surface = await self.learning_moment_detector.should_surface_learning_moment(
                    best_moment, conversation_state
                )
                
                if should_surface:
                    result.update({
                        'surface_moment': True,
                        'suggested_integration': {
                            'type': best_moment.moment_type.value,
                            'suggested_response': best_moment.suggested_response,
                            'confidence': best_moment.confidence,
                            'integration_point': best_moment.natural_integration_point,
                            'character_voice': best_moment.character_voice_adaptation
                        }
                    })
                    
                    # Add to metadata for tracking
                    if message_context.metadata is None:
                        message_context.metadata = {}
                    if 'recent_learning_moments' not in message_context.metadata:
                        message_context.metadata['recent_learning_moments'] = 0
                    message_context.metadata['recent_learning_moments'] += 1
                
                # Store all detected moments for potential API metadata
                result['moments'] = [
                    {
                        'type': moment.moment_type.value,
                        'confidence': moment.confidence,
                        'suggested_response': moment.suggested_response
                    }
                    for moment in learning_moments
                ]
                
                # 📚 CHARACTER LEARNING PERSISTENCE: Store insights for long-term memory
                # Persist learning moments to PostgreSQL for character evolution
                await self._persist_learning_moments(
                    learning_moments=learning_moments,
                    character_name=character_name,
                    user_id=user_id,
                    conversation_context=content[:500]  # Truncated conversation summary
                )
            
            logger.info("🌟 Learning moment detection successful for %s (detected %d moments)", 
                       character_name, len(learning_moments))
            return result
            
        except Exception as e:
            logger.error("🌟 Learning moment detection failed: %s", str(e))
            return None
    
    async def _persist_learning_moments(
        self,
        learning_moments: List,
        character_name: str,
        user_id: str,
        conversation_context: Optional[str] = None
    ) -> None:
        """
        Persist detected learning moments to PostgreSQL for long-term character learning.
        
        Args:
            learning_moments: List of LearningMoment objects detected
            character_name: Character name (e.g., 'elena', 'marcus')
            user_id: Discord user ID
            conversation_context: Optional conversation summary
        """
        try:
            # Ensure learning persistence is initialized (lazy)
            persistence_available = await self._ensure_character_learning_persistence_initialized()
            if not persistence_available or not learning_moments:
                logger.debug("📚 Learning persistence unavailable or no moments to persist")
                return
            
            # Get character_id from database
            from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
            from src.database.postgres_pool_manager import get_postgres_pool
            
            pool = await get_postgres_pool()
            if not pool:
                logger.warning("📚 PostgreSQL pool not available - cannot persist insights")
                return
            
            enhanced_manager = create_enhanced_cdl_manager(pool)
            character_data = await enhanced_manager.get_character_by_name(character_name)
            
            if not character_data or 'id' not in character_data:
                logger.warning("📚 Character '%s' not found in database - cannot persist insights", character_name)
                return
            
            character_id = character_data['id']
            
            # Extract insights from learning moments
            insights = self.character_insight_extractor.extract_insights_from_learning_moments(
                learning_moments=learning_moments,
                character_id=character_id,
                conversation_context=conversation_context
            )
            
            if not insights:
                logger.debug("📚 No insights extracted from %d learning moments (filtered by quality)", 
                           len(learning_moments))
                return
            
            # Store insights in PostgreSQL
            stored_count = 0
            for insight in insights:
                try:
                    insight_id = await self.character_insight_storage.store_insight(insight)
                    stored_count += 1
                    logger.info("📚 Stored insight #%d: [%s] %s", 
                              insight_id, insight.insight_type, insight.insight_content[:60])
                except Exception as store_error:
                    # Log but continue - don't fail entire process for one insight
                    logger.warning("📚 Failed to store insight: %s", store_error)
            
            logger.info("📚 CHARACTER LEARNING PERSISTENCE: Stored %d/%d insights for %s", 
                       stored_count, len(insights), character_name)
        
        except Exception as e:
            # Log error but don't fail message processing
            logger.error("📚 Learning moment persistence failed: %s", e, exc_info=True)

    async def _process_thread_management(self, user_id: str, content: str, 
                                       message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process Phase 4.2 Advanced Thread Management."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'conversation_thread_manager'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process thread management
            thread_result = await self.bot_core.conversation_thread_manager.analyze_thread_context(
                user_id=user_id,
                message=discord_message,
                conversation_history=[]
            )
            
            logger.debug(f"Thread management analysis successful for user {user_id}")
            return thread_result
            
        except Exception as e:
            logger.debug(f"Thread management analysis failed: {e}")
            return None

    # REMOVED: _process_proactive_engagement() method
    # This method was never called after Phase 1-2 optimization (commit 9c17d66).
    # The enrichment worker version (src/enrichment/proactive_engagement_engine.py)
    # is the active production system that stores results in PostgreSQL cache.

    async def _process_human_like_memory(self, user_id: str, content: str, 
                                       message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process human-like memory optimization."""
        try:
            if not self.memory_manager or not hasattr(self.memory_manager, 'human_like_optimizer'):
                return None
            
            # Process human-like memory optimization
            memory_result = await self.memory_manager.human_like_optimizer.optimize_memory_context(
                user_id=user_id,
                query=content,
                conversation_context=[]
            )
            
            logger.debug(f"Human-like memory optimization successful for user {user_id}")
            return memory_result
            
        except Exception as e:
            logger.debug(f"Human-like memory optimization failed: {e}")
            return None

    async def _process_attachments(self, message_context: MessageContext, 
                                 conversation_context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process message attachments (images, etc.)."""
        if not self.image_processor:
            logger.warning("📎 No image_processor available - skipping attachments")
            return conversation_context
            
        if not message_context.attachments:
            logger.debug("📎 No attachments in message_context")
            return conversation_context
        
        try:
            # Process images and add to context using existing image processing logic
            logger.info(f"📎 _process_attachments: Processing {len(message_context.attachments)} attachment(s)")
            logger.debug(f"📎 Attachment details: {message_context.attachments}")
            
            # Use existing image processing from utils.helpers
            from src.utils.helpers import process_message_with_images
            
            # Convert MessageContext attachments to Discord format using adapter
            discord_attachments = create_discord_attachment_adapters(message_context.attachments)
            logger.info(f"📎 Created {len(discord_attachments)} Discord attachment adapters")
            
            # Process images with existing logic
            enhanced_context = await process_message_with_images(
                message_context.content,
                discord_attachments,
                conversation_context,
                self.llm_client,
                self.image_processor
            )
            
            logger.info(f"📎 Enhanced context returned with {len(enhanced_context)} messages")
            return enhanced_context
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"📎 Attachment processing failed with {type(e).__name__}: {str(e)}", exc_info=True)
        
        return conversation_context

    async def _analyze_emotion_vector_native(self, user_id: str, content: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Analyze emotions using vector-native approach."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Use the enhanced vector emotion analyzer from the bot core
            from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
            
            # Store analyzer in instance variable for later reuse (bot emotion analysis)
            async with self._shared_analyzer_lock:
                self._shared_emotion_analyzer = EnhancedVectorEmotionAnalyzer(
                    vector_memory_manager=self.memory_manager
                )
                analyzer = self._shared_emotion_analyzer
            
            # Analyze emotion with vector intelligence (use the correct method name)
            emotion_results = await analyzer.analyze_emotion(
                content=content,
                user_id=user_id,
                conversation_context=[],  # Could be enhanced with history
                recent_emotions=None
            )
            
            # Convert results to dictionary format
            if emotion_results:
                emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.intensity,
                    'confidence': emotion_results.confidence,
                    'analysis_method': 'vector_native'
                    # NOTE: analyzer instance stored separately to avoid JSON serialization issues
                }
                logger.debug("Vector emotion analysis successful for user %s", user_id)
                return emotion_data
            
        except Exception as e:
            logger.debug("Vector emotion analysis failed: %s", str(e))
        
        return None

    async def _analyze_bot_emotion(self, response: str, message_context: MessageContext, 
                                   analyzer = None) -> Optional[Dict[str, Any]]:
        """
        Analyze bot's emotional state from generated response text.
        
        Phase 7.5: Bot Emotion Tracking
        - Analyzes the bot's response to determine character emotional state
        - Stored in vector memory, InfluxDB, and API metadata
        - Enables UI animations and historical emotion patterns
        
        Args:
            response: Bot's generated response text
            message_context: Context with bot name and conversation details
            analyzer: Optional shared emotion analyzer to prevent RoBERTa conflicts
            
        Returns:
            Dict with primary_emotion, intensity, confidence, analysis_method
        """
        try:
            # Enhanced Phase 7.5: Use shared analyzer if provided to prevent RoBERTa race conditions
            if analyzer is None:
                from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
                analyzer = EnhancedVectorEmotionAnalyzer(
                    vector_memory_manager=self.memory_manager
                )
            
            # Analyze bot's response text to detect character emotion
            emotion_results = await analyzer.analyze_emotion(
                content=response,
                user_id=f"bot_{get_normalized_bot_name_from_env()}",  # Bot-specific ID
                conversation_context=[],
                recent_emotions=None
            )
            
            # Convert results to dictionary format with MIXED EMOTIONS support
            if emotion_results:
                # Extract mixed emotions (same as user emotion storage)
                mixed_emotions_list = emotion_results.mixed_emotions if hasattr(emotion_results, 'mixed_emotions') else []
                all_emotions_dict = emotion_results.all_emotions if hasattr(emotion_results, 'all_emotions') else {}
                
                bot_emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.intensity,
                    'confidence': emotion_results.confidence,
                    'analysis_method': 'vector_native',
                    'analyzed_text': response[:100] + '...' if len(response) > 100 else response,  # Sample for debugging
                    # Phase 7.5 Enhancement: Mixed emotions for bot (same as user)
                    'mixed_emotions': mixed_emotions_list,
                    'all_emotions': all_emotions_dict,
                    'emotion_count': len([e for e in all_emotions_dict.values() if e > 0.1]) if all_emotions_dict else 1
                }
                
                if mixed_emotions_list:
                    logger.debug(
                        "Bot emotion analysis: %s (%.2f) + mixed: %s",
                        bot_emotion_data['primary_emotion'],
                        bot_emotion_data['intensity'],
                        [(e, round(i, 2)) for e, i in mixed_emotions_list[:2]]  # Log top 2 mixed emotions
                    )
                else:
                    logger.debug(
                        "Bot emotion analysis successful: %s (%.2f intensity, %.2f confidence)",
                        bot_emotion_data['primary_emotion'],
                        bot_emotion_data['intensity'],
                        bot_emotion_data['confidence']
                    )
                return bot_emotion_data
            
        except Exception as e:
            logger.debug("Bot emotion analysis failed: %s", str(e))
        
        return None

    async def _analyze_bot_emotion_with_shared_analyzer(self, response: str, message_context: MessageContext, 
                                                       ai_components: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze bot's emotional state using shared analyzer to prevent RoBERTa race conditions.
        
        Phase 7.5: Bot Emotion Tracking (Serial Execution)
        - Uses the same analyzer instance from user emotion analysis to prevent conflicts
        - Follows the same pattern as advanced emotion analysis serialization
        
        Args:
            response: Bot's generated response text
            message_context: Context with bot name and conversation details
            ai_components: AI processing results containing emotion analyzer info
            
        Returns:
            Dict with primary_emotion, intensity, confidence, analysis_method
        """
        try:
            # Use shared analyzer if available (from user emotion analysis)
            async with self._shared_analyzer_lock:
                if self._shared_emotion_analyzer:
                    logger.debug("🎭 BOT EMOTION: Using shared emotion analyzer")
                    analyzer = self._shared_emotion_analyzer
                else:
                    logger.debug("🎭 BOT EMOTION: Creating new analyzer (no shared analyzer available)")
                    from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
                    analyzer = EnhancedVectorEmotionAnalyzer(
                        vector_memory_manager=self.memory_manager
                    )
            
            # 🎭 BOT EMOTION DEBUG: Log what text is actually being analyzed for bot emotion
            logger.info(f"🎭 BOT EMOTION DEBUG: Analyzing bot response text: '{response[:100]}{'...' if len(response) > 100 else ''}'")
            logger.info(f"🎭 BOT EMOTION DEBUG: Response length: {len(response)} chars")
            
            # Analyze bot's response text to detect character emotion
            emotion_results = await analyzer.analyze_emotion(
                content=response,
                user_id=f"bot_{get_normalized_bot_name_from_env()}",  # Bot-specific ID
                conversation_context=[],
                recent_emotions=None
            )
            
            # Convert results to dictionary format with MIXED EMOTIONS support
            if emotion_results:
                # Extract mixed emotions (same as user emotion storage)
                mixed_emotions_list = emotion_results.mixed_emotions if hasattr(emotion_results, 'mixed_emotions') else []
                all_emotions_dict = emotion_results.all_emotions if hasattr(emotion_results, 'all_emotions') else {}
                
                bot_emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.intensity,
                    'confidence': emotion_results.confidence,
                    'analysis_method': 'vector_native_shared_analyzer',
                    'analyzed_text': response[:100] + '...' if len(response) > 100 else response,  # Sample for debugging
                    # Phase 7.5 Enhancement: Mixed emotions for bot (same as user)
                    'mixed_emotions': mixed_emotions_list,
                    'all_emotions': all_emotions_dict,
                    'emotion_count': len([e for e in all_emotions_dict.values() if e > 0.1]) if all_emotions_dict else 1
                }
                
                if mixed_emotions_list:
                    logger.debug(
                        "Bot emotion analysis (shared): %s (%.2f) + mixed: %s",
                        bot_emotion_data['primary_emotion'],
                        bot_emotion_data['intensity'],
                        [(e, round(i, 2)) for e, i in mixed_emotions_list[:2]]  # Log top 2 mixed emotions
                    )
                else:
                    logger.debug(
                        "Bot emotion analysis (shared): %s (%.2f intensity, %.2f confidence)",
                        bot_emotion_data['primary_emotion'],
                        bot_emotion_data['intensity'],
                        bot_emotion_data['confidence']
                    )
                return bot_emotion_data
            
        except Exception as e:
            logger.debug("Bot emotion analysis (shared) failed: %s", str(e))
        
        return None

    async def _analyze_advanced_emotion_intelligence(self, user_id: str, content: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Analyze emotions using advanced multi-modal intelligence with RoBERTa + emoji synthesis.
        
        Advanced Emotional Intelligence:
        - Uses existing RoBERTa emotion analysis as foundation
        - Enhances with emoji emotion mapping and synthesis rules
        - Supports 15 emotions (7 RoBERTa + 8 synthesis: love, contempt, pride, awe, confusion)
        - Multi-modal analysis combining text sentiment with visual emoji signals
        
        Args:
            user_id: User identifier for conversation context
            content: Message content to analyze
            message_context: Full message context
            
        Returns:
            Dict with enhanced emotion analysis including multi-modal scores
        """
        try:
            # Import the advanced emotion detector
            from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector
            
            # Initialize with memory manager for context
            detector = AdvancedEmotionDetector(
                memory_manager=self.memory_manager
            )
            
            # Perform advanced multi-modal emotion analysis
            emotion_results = await detector.detect_advanced_emotions(
                text=content,
                user_id=user_id,
                context={}  # Could be enhanced with conversation context
            )
            
            if emotion_results:
                # Convert AdvancedEmotionalState to standardized format for AI components
                advanced_emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.emotional_intensity,
                    'confidence': 0.8,  # Default confidence for advanced analysis
                    'analysis_method': 'advanced_multi_modal',
                    'secondary_emotions': emotion_results.secondary_emotions,
                    'emoji_analysis': emotion_results.emoji_analysis,
                    'text_indicators': emotion_results.text_indicators,
                    'emotional_trajectory': emotion_results.emotional_trajectory,
                    'pattern_type': emotion_results.pattern_type,
                    'cultural_context': emotion_results.cultural_context
                }
                
                logger.debug(
                    "Advanced emotion analysis successful: %s (%.2f intensity, pattern: %s)",
                    advanced_emotion_data['primary_emotion'],
                    advanced_emotion_data['intensity'],
                    advanced_emotion_data['pattern_type'] or 'stable'
                )
                return advanced_emotion_data
                
        except Exception as e:
            logger.debug("Advanced emotion intelligence analysis failed: %s", str(e))
        
        return None

    async def _analyze_advanced_emotion_intelligence_with_basic(self, user_id: str, content: str, message_context: MessageContext, basic_emotion_result) -> Optional[Dict[str, Any]]:
        """
        Analyze emotions using advanced multi-modal intelligence with existing basic emotion results.
        
        This method is called serially after basic emotion analysis to avoid RoBERTa model race conditions.
        Uses the existing basic emotion analysis as foundation instead of re-analyzing.
        
        Args:
            user_id: User identifier for conversation context
            content: Message content to analyze  
            message_context: Full message context
            basic_emotion_result: Result from basic emotion analysis (_analyze_emotion_vector_native)
            
        Returns:
            Dict with enhanced emotion analysis including multi-modal scores
        """
        try:
            # Import the advanced emotion detector
            from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector
            
            # Initialize with memory manager for context  
            detector = AdvancedEmotionDetector(
                memory_manager=self.memory_manager
            )
            
            # Convert basic emotion result to EmotionAnalysisResult format expected by AdvancedEmotionDetector
            if basic_emotion_result and hasattr(basic_emotion_result, 'primary_emotion'):
                # Already in EmotionAnalysisResult format
                roberta_result = basic_emotion_result
            elif isinstance(basic_emotion_result, dict):
                # Convert dict format to EmotionAnalysisResult
                from src.intelligence.enhanced_vector_emotion_analyzer import EmotionAnalysisResult
                roberta_result = EmotionAnalysisResult(
                    primary_emotion=basic_emotion_result.get('primary_emotion', 'neutral'),
                    confidence=basic_emotion_result.get('confidence', 0.5),
                    intensity=basic_emotion_result.get('intensity', 0.5),
                    all_emotions=basic_emotion_result.get('all_emotions', {}),
                    emotional_trajectory=basic_emotion_result.get('emotional_trajectory', []),
                    context_emotions=basic_emotion_result.get('context_emotions', {}),
                    analysis_time_ms=basic_emotion_result.get('analysis_time_ms', 0)
                )
            else:
                logger.warning("🎭 SERIAL EMOTION: Invalid basic emotion result format, skipping advanced analysis")
                return None
            
            # Perform advanced emotion analysis using existing basic results (no re-analysis)
            emotion_results = await detector.detect_advanced_emotions_with_roberta_result(
                text=content,
                user_id=user_id, 
                roberta_result=roberta_result,
                context={}
            )
            
            if emotion_results:
                # Convert AdvancedEmotionalState to standardized format for AI components
                advanced_emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.emotional_intensity,
                    'confidence': 0.8,  # Default confidence for advanced analysis
                    'analysis_method': 'advanced_multi_modal_serial',
                    'secondary_emotions': emotion_results.secondary_emotions,
                    'emoji_analysis': emotion_results.emoji_analysis,
                    'text_indicators': emotion_results.text_indicators,
                    'emotional_trajectory': emotion_results.emotional_trajectory,
                    'pattern_type': emotion_results.pattern_type,
                    'cultural_context': emotion_results.cultural_context
                }
                
                logger.debug(
                    "🎭 SERIAL EMOTION: Advanced analysis successful: %s (%.2f intensity, pattern: %s)",
                    advanced_emotion_data['primary_emotion'],
                    advanced_emotion_data['intensity'],
                    advanced_emotion_data['pattern_type'] or 'stable'
                )
                return advanced_emotion_data
                
        except Exception as e:
            logger.debug("🎭 SERIAL EMOTION: Advanced emotion intelligence analysis failed: %s", str(e))
        
        return None

    async def _analyze_memory_aging_intelligence(self, user_id: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Analyze memory aging patterns and perform intelligent memory management.
        
        Memory Aging Intelligence:
        - Evaluates memory health and identifies optimization opportunities
        - Performs selective memory aging to prevent unbounded growth
        - Preserves high-value memories while pruning low-value content
        - Provides memory health metrics for conversation optimization
        
        Args:
            user_id: User identifier for memory analysis
            message_context: Context for conversation-aware aging
            
        Returns:
            Dict with memory health metrics and aging results
        """
        try:
            # Memory aging is now permanently enabled (no feature flag)
            import os
                
            # Import memory aging components
            from src.memory.aging.aging_policy import MemoryAgingPolicy
            from src.memory.aging.aging_runner import MemoryAgingRunner
            
            # Create aging policy with safe defaults
            aging_policy = MemoryAgingPolicy(
                importance_weight=0.6,
                recency_weight=0.3,
                access_weight=0.1,
                decay_lambda=float(os.getenv('MEMORY_DECAY_LAMBDA', '0.01')),
                prune_threshold=float(os.getenv('MEMORY_PRUNE_THRESHOLD', '0.2'))
            )
            
            # Create aging runner
            aging_runner = MemoryAgingRunner(
                memory_manager=self.memory_manager,
                policy=aging_policy
            )
            
            # Perform memory aging analysis (dry run by default for conversation processing)
            aging_results = await aging_runner.run(
                user_id=user_id,
                dry_run=True  # Always dry run during conversation processing
            )
            
            if aging_results:
                # Calculate memory health metrics
                total_memories = aging_results['scanned']
                flagged_ratio = aging_results['flagged'] / total_memories if total_memories > 0 else 0
                preserved_ratio = aging_results['preserved'] / total_memories if total_memories > 0 else 0
                
                # Determine memory health status
                if flagged_ratio > 0.4:
                    health_status = "poor"  # >40% flagged for pruning
                elif flagged_ratio > 0.2:
                    health_status = "fair"  # >20% flagged for pruning
                else:
                    health_status = "good"  # <20% flagged for pruning
                
                memory_aging_data = {
                    'health_status': health_status,
                    'total_memories': total_memories,
                    'memories_flagged': aging_results['flagged'],
                    'memories_preserved': aging_results['preserved'],
                    'flagged_ratio': round(flagged_ratio, 3),
                    'preserved_ratio': round(preserved_ratio, 3),
                    'processing_time': aging_results['elapsed_seconds'],
                    'aging_enabled': True,
                    'analysis_method': 'memory_aging_intelligence'
                }
                
                logger.debug(
                    "Memory aging analysis: %s health (%d total, %d flagged, %.1f%% prunable)",
                    memory_aging_data['health_status'],
                    memory_aging_data['total_memories'],
                    memory_aging_data['memories_flagged'],
                    memory_aging_data['flagged_ratio'] * 100
                )
                
                # Record memory aging metrics to InfluxDB for temporal analysis
                if hasattr(self, 'temporal_client') and self.temporal_client:
                    try:
                        await self.temporal_client.record_memory_aging_metrics(
                            bot_name=os.getenv('DISCORD_BOT_NAME', 'unknown'),
                            user_id=user_id,
                            health_status=memory_aging_data['health_status'],
                            total_memories=memory_aging_data['total_memories'],
                            memories_flagged=memory_aging_data['memories_flagged'],
                            flagged_ratio=memory_aging_data['flagged_ratio'],
                            processing_time=memory_aging_data['processing_time']
                        )
                        logger.debug("📊 TEMPORAL: Recorded memory aging metrics to InfluxDB")
                    except AttributeError:
                        # record_memory_aging_metrics method doesn't exist yet - log for now
                        logger.debug("Memory aging metrics recording not yet implemented in TemporalIntelligenceClient")
                
                return memory_aging_data
                
        except Exception as e:
            logger.debug("Memory aging intelligence analysis failed: %s", str(e))
        
        return None

    async def _analyze_character_performance_intelligence(self, user_id: str, message_context: MessageContext, 
                                                        conversation_context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        DISABLED: Character Performance Intelligence analysis.
        
        This feature was causing production failures due to Memory Effectiveness Analyzer
        dependency on incomplete protocol interface. Disabled until properly implemented.
        
        Args:
            user_id: User identifier for performance analysis
            message_context: Context for character-specific analysis
            conversation_context: Recent conversation history for effectiveness analysis
            
        Returns:
            None (disabled)
        """
        logger.debug("Character performance intelligence disabled - Memory Boost feature needs protocol fixes")
        return None

    async def _analyze_bot_emotional_trajectory(self, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Analyze bot's emotional trajectory from recent conversation history.
        
        Phase 6.5: Bot Emotional Self-Awareness
        - PRIMARY: Retrieves bot's recent emotional responses from InfluxDB (time-series)
        - FALLBACK: Uses Qdrant vector memory if InfluxDB unavailable
        - Calculates emotional trajectory (improving, declining, stable)
        - Provides emotional state for prompt building (bot knows its own emotions)
        - Enables emotionally-aware responses (e.g., "I've been feeling down lately")
        
        Args:
            message_context: Message context with user ID
            
        Returns:
            Dict with current_emotion, trajectory_direction, emotional_velocity, recent_emotions
        """
        try:
            if not self.memory_manager:
                return None
            
            bot_name = get_normalized_bot_name_from_env()
            
            # PRIMARY: Try InfluxDB for chronological time-series (if available)
            recent_emotions = []
            if self.temporal_client and self.temporal_client.enabled:
                try:
                    # Query last 24 hours of bot emotions from InfluxDB
                    influx_emotions = await self.temporal_client.get_bot_emotion_trend(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        hours_back=24
                    )
                    
                    if influx_emotions:
                        recent_emotions = [
                            {
                                'emotion': e['primary_emotion'],
                                'intensity': e['intensity'],
                                'timestamp': e['timestamp'],
                                'mixed_emotions': []  # InfluxDB doesn't store mixed emotions
                            }
                            for e in influx_emotions[-10:]  # Last 10 emotions
                        ]
                        logger.debug("🎭 Retrieved %d bot emotions from InfluxDB", len(recent_emotions))
                except Exception as e:
                    logger.debug("InfluxDB bot emotion query failed, falling back to Qdrant: %s", e)
            
            # FALLBACK: Use Qdrant semantic search if InfluxDB unavailable or returned no data
            if not recent_emotions:
                bot_memory_query = f"emotional responses by {bot_name}"
                
                # 🔒 PRIVACY: Retrieve bot emotions from channel-scoped memories only
                recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id=message_context.user_id,
                    query=bot_memory_query,
                    limit=10,
                    channel_type=message_context.channel_type  # 🔒 Respect channel privacy boundaries
                )
                
                if not recent_bot_memories:
                    return None
                
                # Extract bot emotions from memory metadata
                for memory in recent_bot_memories:
                    if isinstance(memory, dict):
                        metadata = memory.get('metadata', {})
                        bot_emotion = metadata.get('bot_emotion')
                        
                        if bot_emotion and isinstance(bot_emotion, dict):
                            recent_emotions.append({
                                'emotion': bot_emotion.get('primary_emotion', 'neutral'),
                                'intensity': bot_emotion.get('intensity', 0.0),
                                'timestamp': memory.get('timestamp', ''),
                                'mixed_emotions': bot_emotion.get('mixed_emotions', [])
                            })
                
                logger.debug("🎭 Retrieved %d bot emotions from Qdrant (fallback)", len(recent_emotions))
            
            if not recent_emotions:
                return None
            
            # Calculate emotional trajectory
            if len(recent_emotions) >= 2:
                # Compare recent vs older emotions
                recent_avg_intensity = sum(e['intensity'] for e in recent_emotions[:3]) / min(3, len(recent_emotions))
                older_avg_intensity = sum(e['intensity'] for e in recent_emotions[-3:]) / min(3, len(recent_emotions))
                
                emotional_velocity = recent_avg_intensity - older_avg_intensity
                
                if emotional_velocity > 0.1:
                    trajectory_direction = "intensifying"
                elif emotional_velocity < -0.1:
                    trajectory_direction = "calming"
                else:
                    trajectory_direction = "stable"
            else:
                emotional_velocity = 0.0
                trajectory_direction = "stable"
            
            # Get current emotional state (most recent)
            current_emotion = recent_emotions[0]['emotion']
            current_intensity = recent_emotions[0]['intensity']
            current_mixed = recent_emotions[0].get('mixed_emotions', [])
            
            bot_emotional_state = {
                'current_emotion': current_emotion,
                'current_intensity': current_intensity,
                'current_mixed_emotions': current_mixed,
                'trajectory_direction': trajectory_direction,
                'emotional_velocity': round(emotional_velocity, 3),
                'recent_emotions': [e['emotion'] for e in recent_emotions[:5]],
                'emotional_context': f"{current_emotion} and {trajectory_direction}",
                'self_awareness_available': True
            }
            
            logger.debug(
                "🎭 BOT TRAJECTORY: %s is feeling %s (%.2f intensity) - trajectory %s (velocity: %.3f)",
                bot_name,
                current_emotion,
                current_intensity,
                trajectory_direction,
                emotional_velocity
            )
            
            return bot_emotional_state
            
        except Exception as e:
            logger.debug("Bot emotional trajectory analysis failed: %s", str(e))
            return None

    async def _build_bot_emotional_state(self, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Build comprehensive bot emotional state for prompt integration.
        
        Phase 7.6: Bot Emotional Self-Awareness
        - Combines current emotion and trajectory analysis
        - Provides emotional context for CDL prompt building
        - Enables bot to reference its own emotional state in responses
        
        Args:
            message_context: Message context with user ID
            
        Returns:
            Dict with complete bot emotional state for prompt integration
        """
        try:
            # Get bot emotional trajectory
            trajectory_data = await self._analyze_bot_emotional_trajectory(message_context)
            
            if not trajectory_data:
                return None
            
            bot_name = get_normalized_bot_name_from_env()
            
            # Build comprehensive emotional state
            emotional_state = {
                'bot_name': bot_name,
                'current_emotional_context': trajectory_data.get('emotional_context', 'neutral'),
                'self_awareness': {
                    'current_emotion': trajectory_data.get('current_emotion', 'neutral'),
                    'intensity': trajectory_data.get('current_intensity', 0.5),
                    'trajectory': trajectory_data.get('trajectory_direction', 'stable'),
                    'velocity': trajectory_data.get('emotional_velocity', 0.0)
                },
                'emotional_memory': {
                    'recent_emotions': trajectory_data.get('recent_emotions', []),
                    'pattern': trajectory_data.get('trajectory_direction', 'stable'),
                    'context_available': True
                },
                'prompt_integration': {
                    'emotional_awareness_prompt': self._generate_emotional_awareness_prompt(trajectory_data),
                    'self_reference_allowed': True,
                    'emotional_continuity': True
                }
            }
            
            logger.debug(
                "🎭 BOT STATE: %s emotional state built - %s (%s)",
                bot_name,
                emotional_state['self_awareness']['current_emotion'],
                emotional_state['self_awareness']['trajectory']
            )
            
            return emotional_state
            
        except Exception as e:
            logger.debug("Bot emotional state building failed: %s", str(e))
            return None
    
    def _generate_emotional_awareness_prompt(self, trajectory_data: Dict[str, Any]) -> str:
        """Generate emotional awareness prompt fragment for CDL integration."""
        current_emotion = trajectory_data.get('current_emotion', 'neutral')
        trajectory = trajectory_data.get('trajectory_direction', 'stable')
        intensity = trajectory_data.get('current_intensity', 0.5)
        
        if trajectory == "intensifying":
            return f"You've been feeling increasingly {current_emotion} (intensity: {intensity:.1f})"
        elif trajectory == "calming":
            return f"Your {current_emotion} feelings have been settling (intensity: {intensity:.1f})"
        else:
            return f"You're feeling {current_emotion} with stable emotions (intensity: {intensity:.1f})"

    async def _analyze_dynamic_personality(self, user_id: str, content: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Analyze dynamic personality if profiler is available."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'dynamic_personality_profiler'):
                return None
            
            profiler = self.bot_core.dynamic_personality_profiler
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # BUG IN COMMIT 01a8292: Called analyze_personality() which doesn't exist on profiler
            # FIX: Use available method analyze_conversation() instead
            personality_data = await profiler.analyze_conversation(
                message=discord_message,
                user_id=user_id
            )
            
            logger.debug("Dynamic personality analysis successful for user %s", user_id)
            return personality_data
            
        except Exception as e:
            logger.debug("Dynamic personality analysis failed: %s", str(e))
        
        return None

    async def _process_conversation_intelligence(self, user_id: str, content: str, message_context: MessageContext, emotion_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process Phase 4 human-like intelligence if available."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Use conversation intelligence integration if available
            conversation_context_result = await self.bot_core.phase2_integration.process_conversation_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=[],
                external_emotion_data=emotion_data,
                emotion_context=emotion_data
            )
            
            logger.debug("Conversation intelligence processing successful for user %s", user_id)
            return conversation_context_result
            
        except Exception as e:
            logger.debug("Conversation intelligence processing failed: %s", str(e))
        
        return None

    async def _analyze_context_switches(self, user_id: str, content: str, message) -> Optional[List[Dict[str, Any]]]:
        """Analyze context switches using Phase 3 ContextSwitchDetector."""
        try:
            logger.debug("Running Phase 3 context switch detection...")

            if not self.bot_core or not hasattr(self.bot_core, 'context_switch_detector') or not self.bot_core.context_switch_detector:
                logger.debug("Context switch detector not available")
                return None

            # Detect context switches
            context_switches = await self.bot_core.context_switch_detector.detect_context_switches(
                user_id=user_id,
                new_message=content
            )

            logger.debug("Phase 3 context switch detection completed: %s switches detected", len(context_switches) if context_switches else 0)
            return context_switches

        except Exception as e:
            logger.error("Phase 3 context switch detection failed: %s", str(e))
            return None

    async def _calibrate_empathy_response(self, user_id: str, content: str, message) -> Optional[Dict[str, Any]]:
        """Calibrate empathy response using Phase 3 EmpathyCalibrator."""
        try:
            logger.debug("Running Phase 3 empathy calibration...")

            if not self.bot_core or not hasattr(self.bot_core, 'empathy_calibrator') or not self.bot_core.empathy_calibrator:
                logger.debug("Empathy calibrator not available")
                return None

            # First detect emotion for empathy calibration (simplified for now)
            try:
                from src.intelligence.empathy_calibrator import EmotionalResponseType
                
                # Use a simple emotion detection based on message content
                detected_emotion = EmotionalResponseType.CONTENTMENT  # Default neutral emotion
                if any(word in content.lower() for word in ['sad', 'upset', 'angry', 'frustrated']):
                    detected_emotion = EmotionalResponseType.STRESS
                elif any(word in content.lower() for word in ['happy', 'excited', 'joy', 'great']):
                    detected_emotion = EmotionalResponseType.JOY
                elif any(word in content.lower() for word in ['worried', 'anxious', 'nervous']):
                    detected_emotion = EmotionalResponseType.ANXIETY
                elif any(word in content.lower() for word in ['confused', 'lost', 'don\'t understand']):
                    detected_emotion = EmotionalResponseType.CONFUSION

                # Calibrate empathy
                empathy_calibration = await self.bot_core.empathy_calibrator.calibrate_empathy(
                    user_id=user_id,
                    detected_emotion=detected_emotion,
                    message_content=content
                )

                logger.debug("Phase 3 empathy calibration completed: %s", empathy_calibration.recommended_style.value if empathy_calibration else 'None')
                
                # Convert to dict format for JSON serialization
                if empathy_calibration:
                    return {
                        'empathy_style': empathy_calibration.recommended_style.value,
                        'confidence': empathy_calibration.confidence_score,
                        'guidance': empathy_calibration.reasoning,  # Fixed: was guidance_text, should be reasoning
                        'personalization_factors': empathy_calibration.personalization_factors
                    }
                return None

            except ImportError:
                logger.debug("EmotionalResponseType not available for empathy calibration")
                return None

        except Exception as e:
            logger.error("Phase 3 empathy calibration failed: %s", str(e))
            return None

    def detect_context_patterns(self, message: str, conversation_history: List[Dict[str, str]], 
                               vector_boost: bool = True, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """Detect context patterns using hybrid context detector."""
        try:
            from src.prompts.hybrid_context_detector import create_hybrid_context_detector
            
            # Create context detector with memory manager if available
            context_detector = create_hybrid_context_detector(memory_manager=self.memory_manager)
            
            # Analyze context using the correct method name
            context_analysis = context_detector.analyze_context(
                message=message,
                user_id="context_analysis"  # Could be enhanced with actual user_id
            )
            
            # Convert to expected format
            context_result = {
                'needs_ai_guidance': context_analysis.needs_ai_guidance,
                'needs_memory_context': context_analysis.needs_memory_context,
                'needs_personality': context_analysis.needs_personality,
                'needs_voice_style': context_analysis.needs_voice_style,
                'is_greeting': context_analysis.is_greeting,
                'is_simple_question': context_analysis.is_simple_question,
                'confidence_scores': context_analysis.confidence_scores,
                'detection_method': context_analysis.detection_method
            }
            
            logger.debug("Context pattern detection successful")
            return context_result
            
        except Exception as e:
            logger.debug("Context pattern detection failed: %s", str(e))
            # Return sensible defaults
            return {
                'needs_ai_guidance': True,
                'needs_memory_context': True,
                'needs_personality': True,
                'needs_voice_style': True,
                'is_greeting': False,
                'is_simple_question': False,
                'confidence_scores': {},
                'detection_method': {}
            }

    async def _generate_response(self, message_context: MessageContext, 
                               conversation_context: List[Dict[str, str]], 
                               ai_components: Dict[str, Any]) -> str:
        """Generate AI response using the conversation context."""
        try:
            # ✅ UNIFIED PROMPT ASSEMBLY: conversation_context already has all CDL components
            # from _build_conversation_context_structured() - no need for legacy enhancement
            final_context = conversation_context
            
            # 🎯 TOKEN BUDGET ENFORCEMENT: Prevent oversized context from walls of text
            # This is STAGE 2 management (full conversation array) - happens AFTER PromptAssembler (system message only)
            from src.utils.context_size_manager import truncate_context, count_context_tokens
            
            # Count tokens BEFORE truncation
            pre_truncation_tokens = count_context_tokens(final_context)
            logger.info("📊 CONTEXT SIZE: %d messages, ~%d tokens before truncation", 
                       len(final_context), pre_truncation_tokens)
            
            # Apply smart truncation (preserves system message + recent messages, drops oldest first)
            # Phase 2A: Upgraded to 8K conversation history for deep conversation memory (30-40 messages)
            final_context, tokens_removed = truncate_context(
                final_context, 
                max_tokens=8000,  # Phase 2A: Upgraded from 2000 to 8000 for sophisticated conversations
                min_recent_messages=2  # ADAPTIVE: Guarantees last 1 exchange minimum, but keeps MORE if they fit budget
            )
            
            if tokens_removed > 0:
                logger.warning("✂️ CONTEXT TRUNCATED: Removed %d tokens to fit budget (walls of text from user)", 
                             tokens_removed)
            
            # �📝 COMPREHENSIVE PROMPT LOGGING: Log full prompts to file for review
            await self._log_full_prompt_to_file(final_context, message_context.user_id, ai_components)
            
            # Generate response using LLM (with timing)
            logger.info("🎯 GENERATING: Sending %d messages (~%d tokens) to LLM", 
                       len(final_context), count_context_tokens(final_context))
            
            from src.llm.llm_client import LLMClient
            from datetime import datetime
            llm_client = LLMClient()
            
            # Track LLM call time separately
            llm_start = datetime.now()
            response = await asyncio.to_thread(
                llm_client.get_chat_response, final_context
            )
            llm_end = datetime.now()
            llm_time_ms = int((llm_end - llm_start).total_seconds() * 1000)
            
            # Store LLM timing in ai_components for footer display
            ai_components['llm_time_ms'] = llm_time_ms
            
            logger.info("✅ GENERATED: Response with %d characters (LLM took %dms)", len(response), llm_time_ms)
            
            # 📝 LOG LLM RESPONSE: Add response to the prompt log for complete picture
            await self._log_llm_response_to_file(response, message_context.user_id)
            
            # 🎭 CDL EMOJI ENHANCEMENT: Add character-appropriate emojis to text response
            # TODO: Migrate emoji system to database-only character loading
            # Current emoji system still uses JSON files - needs database integration
            try:
                # Use bot name from environment (database-only approach)
                bot_name = get_normalized_bot_name_from_env()
                if bot_name:
                    # TODO: Update emoji system to use database character data instead of JSON files
                    # For now, skip emoji enhancement during CDL migration
                    logger.debug("🎭 CDL EMOJI: Skipping emoji enhancement during database migration (character: %s)", bot_name)
                    
                    # NO-OP: Emoji system requires database migration to work with character names
                    # Currently expects JSON file paths which are deprecated
                    emoji_metadata = {
                        "cdl_emoji_applied": False,
                        "reason": "emoji_system_migration_pending",
                        "character": bot_name
                    }
                    
                    logger.debug("🎭 CDL EMOJI: Emoji enhancement disabled - database migration required")
                    
                    if emoji_metadata.get("cdl_emoji_applied", False):
                        logger.info(f"🎭 CDL EMOJI: Enhanced response with {len(emoji_metadata.get('emoji_additions', []))} emojis "
                                  f"({emoji_metadata.get('placement_style', 'unknown')} style)")
                    else:
                        reason = emoji_metadata.get('reason', 'unknown')
                        if reason == "emoji_system_migration_pending":
                            logger.debug("🎭 CDL EMOJI: Emoji system migration pending - enhancement skipped")
                        else:
                            logger.debug(f"🎭 CDL EMOJI: No enhancement applied - {reason}")
                else:
                    logger.debug("🎭 CDL EMOJI: No bot name available - skipping emoji enhancement")
            except Exception as e:
                logger.error(f"CDL emoji enhancement failed (non-critical): {e}")
                # Continue with original response if CDL emoji enhancement fails
            
            return response
            
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            logger.error("Response generation failed: %s", str(e), exc_info=True)
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    async def _add_mixed_emotion_context(self, conversation_context: List[Dict[str, str]], 
                                       content: str, user_id: str, emotion_data, external_emotion_data) -> List[Dict[str, str]]:
        """Add emotion context to conversation."""
        # TODO: Implement emotion context enhancement
        logger.debug("Emotion context enhancement placeholder for user %s with content length %d", 
                    user_id, len(content))
        # Avoid unused parameter warnings by referencing them  
        _ = emotion_data, external_emotion_data
        return conversation_context

    async def _validate_and_sanitize_response(self, response: str, message_context: MessageContext) -> str:
        """Validate response for character consistency and sanitize for security."""
        try:
            # 🚨 CRITICAL: Check for LLM recursive failures FIRST
            response = await self._detect_and_fix_recursive_patterns(response, message_context)
            
            # Character consistency check
            response = await self._validate_character_consistency(response, message_context.user_id, message_context)
            
            # Security scan for system leakage
            from src.security.system_message_security import scan_response_for_system_leakage
            leakage_scan = scan_response_for_system_leakage(response)
            if leakage_scan["has_leakage"]:
                logger.error("SECURITY: System message leakage detected in response to user %s", 
                           message_context.user_id)
                response = leakage_scan["sanitized_response"]
            
            # Meta-analysis sanitization
            response = self._sanitize_meta_analysis(response)
            
            return response
            
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            logger.error("Response validation failed: %s", str(e))
            return response  # Return original if validation fails

    async def _validate_character_consistency(self, response: str, user_id: str, message_context: MessageContext) -> str:
        """Validate that response maintains character consistency."""
        # TODO: Implement character consistency validation
        logger.debug("Character consistency validation placeholder for user %s", user_id)
        # Avoid unused parameter warnings
        _ = message_context
        return response

    def _sanitize_meta_analysis(self, response: str) -> str:
        """Sanitize response to prevent meta-analytical sections."""
        try:
            import re
            patterns = [
                "Core Conversation Analysis",
                "Emotional Analysis", 
                "Technical Metadata",
                "Personality & Interaction",
                "Overall Assessment",
            ]
            trigger_count = sum(p in response for p in patterns)
            coaching_phrase = "Do you want me to" in response
            
            if trigger_count >= 2 or coaching_phrase:
                logger.warning("Meta/coaching analytical response detected - sanitizing")
                lines = response.splitlines()
                natural_parts = []
                for line in lines:
                    if any(p in line for p in patterns) or re.match(r"^[A-Z][A-Za-z &]+:\s*$", line.strip()):
                        break
                    if line.strip():
                        natural_parts.append(line.strip())
                
                base_text = " ".join(natural_parts).strip()
                if not base_text:
                    base_text = "I apologize, but I need to rephrase my response to stay in character."
                
                return base_text + "\n\n(Internal analytical sections omitted to preserve character immersion.)"
            
            return response
            
        except (ValueError, TypeError) as e:
            logger.error("Meta-analysis sanitization failed: %s", str(e))
            return response

    async def _detect_and_fix_recursive_patterns(self, response: str, message_context: MessageContext) -> str:
        """Detect and fix LLM recursive failures that could poison memory."""
        import re
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        
        try:
            bot_name = get_normalized_bot_name_from_env()
            
            # 🚨 CRITICAL PATTERNS: Known recursive failure indicators
            recursive_patterns = [
                r'remember that you can remember',
                r'(\b\w+\b)(\s+\1){24,}',  # FIXED: Same word repeating 25+ times (word + 24 more repetitions)
                r'(that you can\s+){5,}',  # "that you can" repeating
                r'(\b\w+\s+\w+\b)(\s+\1){19,}',  # FIXED: Same two-word phrase repeating 20+ times
                r'(being able to\s+){3,}',  # "being able to" repeating
                r'EEREE|Eternalized Eternally',  # Specific nonsense patterns from Ryan
                r'(processing data.*entertainment.*){3,}',  # Recursive tech explanations
                r'(.{20,})\1{3,}',  # Any 20+ char phrase repeating 3+ times (NEW: more precise)
            ]
            
            # Length-based detection
            if len(response) > 10000:  # Raised from 8000 - Ryan's broken response was 14,202 chars
                logger.warning("🚨 RECURSIVE PATTERN: Response length excessive (%d chars) for user %s", 
                             len(response), message_context.user_id)
                
                # Check for any recursive patterns
                for pattern in recursive_patterns:
                    if re.search(pattern, response, re.IGNORECASE):
                        logger.error("🚨 RECURSIVE PATTERN DETECTED: %s pattern found in %s response", 
                                   pattern, bot_name)
                        return await self._generate_fallback_response(message_context, "recursive_pattern")
            
            # Pattern-based detection (regardless of length)
            for pattern in recursive_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    logger.error("🚨 RECURSIVE PATTERN DETECTED: %s pattern found in %s response", 
                               pattern, bot_name)
                    logger.error("🚨 PATTERN CONTEXT: ...%s...", response[max(0, match.start()-50):match.end()+50])
                    return await self._generate_fallback_response(message_context, "recursive_pattern")
            
            # Repetition detection - more targeted to catch severe loops
            words = response.split()
            if len(words) > 150:  # Only check very long responses (raised from 100)
                # Check for phrase repetition patterns - look for longer phrases
                for i in range(len(words) - 15):
                    phrase = ' '.join(words[i:i+5])  # 5-word phrase (increased from 3)
                    remaining_text = ' '.join(words[i+5:])
                    phrase_count = remaining_text.count(phrase)
                    
                    if phrase_count >= 3:  # Same 5-word phrase appears 3+ more times (reduced from 5)
                        logger.error("🚨 REPETITION PATTERN: Phrase '%s' repeats %d times in %s response", 
                                   phrase, phrase_count, bot_name)
                        return await self._generate_fallback_response(message_context, "repetition_pattern")
            
            return response
            
        except Exception as e:
            logger.error("🚨 RECURSIVE PATTERN DETECTION FAILED: %s", e)
            return response  # Return original if detection fails

    async def _generate_fallback_response(self, message_context: MessageContext, failure_type: str) -> str:
        """Generate a safe fallback response when recursive patterns are detected."""
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        
        bot_name = get_normalized_bot_name_from_env()
        
        # Get user display name using the same preference hierarchy
        user_name = await self._get_user_display_name(message_context)
        
        # Generic fallback response - character personality will be applied by CDL system
        fallback = f"I apologize, {user_name}. I need to gather my thoughts for a moment. What can I help you with?"
        
        logger.warning("🛡️ FALLBACK RESPONSE: Generated safe response for %s due to %s", bot_name, failure_type)
        return fallback

    def _lemmatize_for_fact_extraction(self, content: str) -> str:
        """
        Lemmatize content for fact extraction with advanced spaCy features.
        
        Normalizes word variations (loving→like, visited→visit, etc.) and filters
        to content words only (NOUN/VERB/ADJ/ADV) to reduce noise.
        
        ADVANCED FEATURES USED:
        1. Lemmatization - Word form normalization
        2. POS Tagging - Content-word filtering (NOUN/VERB/ADJ/ADV)
        3. Named Entity Recognition - Entity context and typing
        4. Noun Chunks - Multi-word entity extraction (e.g., "Italian restaurant")
        5. Negation Detection - Track negation (don't like → dislike)
        
        Uses pattern from:
        - Hybrid Context Detector (98% success)
        - Character Learning Detector (100% success)
        - Semantic Router (entity type detection)
        
        Args:
            content: Message content to lemmatize
            
        Returns:
            Lemmatized content words as space-separated string
        """
        try:
            from src.nlp.spacy_manager import get_spacy_nlp
            
            nlp = get_spacy_nlp()
            if not nlp:
                return content.lower()
            
            doc = nlp(content.lower())
            
            # FEATURE 5: Track negations via dependency parsing
            negation_heads = set()
            for token in doc:
                if token.dep_ == "neg":
                    negation_heads.add(token.head.i)
            
            # Extract content words with negation awareness
            content_lemmas = []
            for token in doc:
                if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']:
                    lemma = token.lemma_
                    
                    # Mark negated verbs with prefix for pattern matching
                    if token.i in negation_heads and token.pos_ == 'VERB':
                        lemma = f"not_{lemma}"
                    
                    content_lemmas.append(lemma)
            
            # Fallback to all lemmas if no content words found
            if not content_lemmas:
                content_lemmas = [token.lemma_ for token in doc if not token.is_punct]
            
            return ' '.join(content_lemmas)
        except Exception as e:
            logger.warning(f"⚠️ Fact extraction lemmatization failed: {e}")
            return content.lower()

    def _extract_entity_with_noun_chunks(self, content: str, entity_type: str = 'general') -> List[str]:
        """
        Extract entities from content using advanced spaCy noun chunks.
        
        ADVANCED FEATURES USED:
        1. Noun Chunks - Multi-word phrases (e.g., "beautiful Italian restaurant")
        2. Named Entity Recognition - Entity typing and boundaries
        3. Dependency Parsing - Head-dependent relationships
        4. Conjunctions - Handle "pizza and pasta" → 2 entities
        
        Args:
            content: Message content to extract from
            entity_type: Type of entity to prefer (food, place, etc.)
            
        Returns:
            List of extracted entity names
        """
        try:
            from src.nlp.spacy_manager import get_spacy_nlp
            
            nlp = get_spacy_nlp()
            if not nlp:
                return []
            
            doc = nlp(content.lower())
            extracted_entities = []
            
            # FEATURE 1: Extract noun chunks (multi-word entities)
            # Examples: "beautiful Italian restaurant", "my favorite hobby", "best friend"
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.strip()
                if chunk_text and len(chunk_text) > 1:  # Skip single characters
                    extracted_entities.append(chunk_text)
            
            # FEATURE 2 & 3: Also capture spaCy NER entities
            for ent in doc.ents:
                ent_text = ent.text.strip()
                if ent_text and len(ent_text) > 1:
                    extracted_entities.append(ent_text)
            
            # FEATURE 4: Handle conjunctions - extract coordinated nouns separately
            # Example: "I like pizza and pasta" → extract ["pizza", "pasta"]
            for token in doc:
                if token.pos_ == "CCONJ":  # Coordinating conjunction (and, or, but)
                    # Find nouns coordinated by this conjunction
                    for child in token.head.children:
                        if child.pos_ in ["NOUN", "PROPN"] and child.i != token.head.i:
                            noun_text = child.text.strip()
                            if noun_text and len(noun_text) > 1:
                                extracted_entities.append(noun_text)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_entities = []
            for ent in extracted_entities:
                if ent.lower() not in seen:
                    seen.add(ent.lower())
                    unique_entities.append(ent)
            
            return unique_entities if unique_entities else []
        
        except Exception as e:
            logger.warning(f"⚠️ Advanced entity extraction failed: {e}")
            return []

    async def _extract_and_store_knowledge(self, message_context: MessageContext, 
                                          ai_components: Dict[str, Any],
                                          extract_from: str = 'user') -> bool:
        """
        Extract factual knowledge from message using REGEX/KEYWORD patterns and store in PostgreSQL.
        
        This is the lightweight runtime extraction - uses pattern matching instead of LLM.
        Enrichment worker provides better quality with LLM analysis + conversation context.
        
        Args:
            message_context: The message context
            ai_components: AI processing results including emotion data
            extract_from: 'user' to extract facts about user (bot extraction not supported in regex mode)
            
        Returns:
            True if knowledge was extracted and stored
        """
        # Only support user fact extraction in regex mode (bot extraction requires LLM)
        if extract_from != 'user':
            logger.debug("⏭️ REGEX FACT EXTRACTION: Bot fact extraction not supported (requires enrichment worker)")
            return False
        
        # Check if knowledge router is available
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            return False
        
        # CRITICAL: Only extract from USER messages
        # This prevents extracting philosophical statements from bot as user facts
        if message_context.metadata and message_context.metadata.get('is_bot_message', False):
            logger.debug("Skipping user fact extraction - message is from bot")
            return False
        
        try:
            content = message_context.content.lower()
            
            # Lemmatize content for normalized pattern matching
            lemmatized_content = self._lemmatize_for_fact_extraction(content)
            
            # Pattern-based factual detection using lemmatized forms
            # ADVANCED FEATURES USED:
            # 1. Lemmatization - Normalize word forms
            # 2. Negation Detection - Handle "don't like" → extract as "dislike"
            # 3. Intensity Tracking - "Really love" vs "kind of like" (future feature)
            # 4. Noun Chunks - Enhanced entity extraction (used in _extract_entity_with_noun_chunks)
            # 5. Conjunctions - Handle "pizza and pasta" → 2 separate facts
            
            factual_patterns = {
                # Food preferences (using lemmatized base verbs)
                'food_preference': [
                    ('like', 'likes'),      # matches like/liked/likes/liking
                    ('love', 'likes'),      # matches love/loved/loves/loving
                    ('enjoy', 'likes'),     # matches enjoy/enjoyed/enjoys/enjoying
                    ('prefer', 'likes'),    # matches prefer/preferred/prefers/preferring
                    ('favorite', 'likes'),  # matches favorite/favourites
                    ('hate', 'dislikes'),   # matches hate/hated/hates/hating
                    ('dislike', 'dislikes'), # matches dislike/disliked/dislikes/disliking
                    # Negation-aware patterns (from _lemmatize_for_fact_extraction)
                    ('not_like', 'dislikes'),  # matches "don't like", "not like", "won't like"
                    ('not_love', 'dislikes'),  # matches "don't love"
                    ('not_enjoy', 'dislikes')  # matches "don't enjoy"
                ],
                # Drink preferences (same as food)
                'drink_preference': [
                    ('like', 'likes'),
                    ('love', 'likes'),
                    ('enjoy', 'likes'),
                    ('prefer', 'likes'),
                    ('favorite', 'likes'),
                    ('hate', 'dislikes'),
                    ('dislike', 'dislikes'),
                    ('not_like', 'dislikes'),
                    ('not_love', 'dislikes'),
                    ('not_enjoy', 'dislikes')
                ],
                # Hobbies
                'hobby_preference': [
                    ('like', 'enjoys'),     # matches all forms of "like"
                    ('love', 'enjoys'),     # matches all forms of "love"
                    ('enjoy', 'enjoys'),    # matches all forms of "enjoy"
                    ('hobby', 'enjoys'),    # matches hobby/hobbies
                    ('do', 'enjoys'),       # matches do/doing/did for "do for fun"
                    ('not_like', 'dislikes'),  # negation support
                    ('not_enjoy', 'dislikes')  # negation support
                ],
                # Places visited
                'place_visited': [
                    ('visit', 'visited'),   # matches visit/visited/visiting/visits
                    ('travel', 'visited'),  # matches travel/traveled/traveling/travels
                    ('go', 'visited'),      # matches go/going/went/goes
                    ('be', 'visited'),      # matches be for "been to"
                    ('not_visit', 'not_visited'),  # negation support
                    ('not_travel', 'not_visited')  # negation support
                ]
            }
            
            # Entity type keywords (also lemmatized base forms)
            entity_keywords = {
                'food': ['pizza', 'pasta', 'sushi', 'burger', 'taco', 'food', 'meal', 'dish', 'eat', 'cook'],
                'drink': ['beer', 'wine', 'coffee', 'tea', 'water', 'soda', 'juice', 'drink'],
                'hobby': ['hike', 'read', 'game', 'cook', 'photography', 'music', 'hobby'],
                'place': ['city', 'country', 'beach', 'mountain', 'park', 'place', 'location']
            }
            
            detected_facts = []
            
            # Detect factual statements from lemmatized content
            for event_type, patterns in factual_patterns.items():
                for pattern, relationship in patterns:
                    if pattern in lemmatized_content:
                        # Determine entity type based on keywords
                        entity_type = 'other'
                        for etype, keywords in entity_keywords.items():
                            if any(kw in content for kw in keywords):
                                entity_type = etype
                                break
                        
                        # FEATURE 4: Use enhanced noun chunks extraction for better entity detection
                        entity_names = self._extract_entity_with_noun_chunks(content, entity_type)
                        
                        # Fallback to simple extraction if noun chunks didn't find anything
                        if not entity_names:
                            entity_names = self._extract_entity_from_content(content, pattern, entity_type)
                        
                        if entity_names:
                            # Create a fact for each entity
                            for entity_name in entity_names:
                                detected_facts.append({
                                    'entity_name': entity_name,
                                    'entity_type': entity_type,
                                    'relationship_type': relationship,
                                    'confidence': 0.7,  # Lower confidence for regex vs LLM
                                    'event_type': event_type
                                })
            
            # Store detected facts in PostgreSQL
            if detected_facts:
                bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant').lower()
                emotion_data = ai_components.get('emotion_data', {})
                emotional_context = emotion_data.get('primary_emotion', 'neutral') if emotion_data else 'neutral'
                
                stored_count = 0
                for fact in detected_facts:
                    stored = await self.bot_core.knowledge_router.store_user_fact(
                        user_id=message_context.user_id,
                        entity_name=fact['entity_name'],
                        entity_type=fact['entity_type'],
                        relationship_type=fact['relationship_type'],
                        confidence=fact['confidence'],
                        emotional_context=emotional_context,
                        mentioned_by_character=bot_name,
                        source_conversation_id=message_context.channel_id
                    )
                    
                    if stored:
                        stored_count += 1
                        logger.info(
                            f"✅ REGEX FACT EXTRACTION: Stored '{fact['entity_name']}' "
                            f"({fact['entity_type']}, {fact['relationship_type']}) for user {message_context.user_id}"
                        )
                
                if stored_count > 0:
                    logger.info(f"✅ REGEX FACT EXTRACTION: Stored {stored_count}/{len(detected_facts)} facts")
                
                return stored_count > 0
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Regex fact extraction failed: {e}", exc_info=True)
            return False
    
    # NOTE: Bot self-fact extraction method removed - redundant with Character Episodic Intelligence
    # Character episodic memories are extracted from vector conversations with RoBERTa emotion scoring
    # See: src/characters/learning/character_vector_episodic_intelligence.py
    # Bot learns behavioral patterns, not isolated facts
    
    # NOTE: _extract_and_store_knowledge_regex_legacy method removed
    # The regex-based approach is now the main implementation in _extract_and_store_knowledge
    # LLM-based fact extraction moved to enrichment worker for better quality + no user-facing latency
    
    async def _extract_and_store_user_preferences(self, message_context: MessageContext) -> bool:
        """
        Extract user preferences from message and store in PostgreSQL.
        
        This is part of Phase 5: User Preferences Integration.
        Detects patterns like:
        - "My name is Mark"
        - "Call me Mark"
        - "I prefer to be called Mark"
        - "I go by Mark"
        - "You can call me Mark"
        
        Stores in universal_users.preferences JSONB column for <1ms retrieval.
        
        Args:
            message_context: The message context
            
        Returns:
            True if preference was detected and stored
        """
        # Check if knowledge router is available
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            return False
        
        try:
            content = message_context.content
            import re
            
            preferences_detected = []
            
            # 1. PREFERRED NAME PATTERNS
            name_patterns = [
                # "My name is Mark" - captures capitalized names
                r"(?:my|My)\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "Call me Mark"
                r"(?:call|Call)\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "I prefer to be called Mark" or "I prefer Mark"
                r"(?:i|I)\s+prefer\s+(?:to\s+be\s+called\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "I go by Mark"
                r"(?:i|I)\s+go\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "You can call me Mark"
                r"(?:you|You)\s+can\s+call\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "Just call me Mark"
                r"(?:just|Just)\s+call\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                # "I'm Mark" (less formal)
                r"(?:i|I)[''']m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, content)
                if match:
                    detected_name = match.group(1).strip()
                    if 2 <= len(detected_name) <= 50:  # Validate name length
                        preferences_detected.append({
                            'type': 'preferred_name',
                            'value': detected_name,
                            'confidence': 0.95,
                            'pattern': pattern
                        })
                        logger.debug(f"🔍 PREFERENCE: Detected name '{detected_name}'")
                        break
            
            # 2. TIMEZONE PATTERNS
            timezone_patterns = [
                # "I'm in EST", "I'm in Pacific time"
                r"(?:i|I)[''']?m\s+in\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)(?:\s+time)?",
                # "My timezone is EST"
                r"(?:my|My)\s+(?:timezone|time\s+zone)\s+is\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)",
                # "I live in EST", "I'm on PST"
                r"(?:i|I)\s+(?:live\s+in|am\s+on|use)\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)(?:\s+time)?",
            ]
            
            for pattern in timezone_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    timezone = match.group(1).upper()
                    preferences_detected.append({
                        'type': 'timezone',
                        'value': timezone,
                        'confidence': 0.90,
                        'pattern': pattern
                    })
                    logger.debug(f"🔍 PREFERENCE: Detected timezone '{timezone}'")
                    break
            
            # 3. LOCATION PATTERNS
            location_patterns = [
                # "I live in Seattle", "I'm from Chicago"
                r"(?:i|I)\s+(?:live\s+in|am\s+from|reside\s+in)\s+([A-Z][a-zA-Z\s]{2,30})",
                # "I'm in New York", "I'm located in Boston"
                r"(?:i|I)[''']?m\s+(?:in|located\s+in)\s+([A-Z][a-zA-Z\s]{2,30})",
                # "My location is Seattle"
                r"(?:my|My)\s+location\s+is\s+([A-Z][a-zA-Z\s]{2,30})",
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, content)
                if match:
                    location = match.group(1).strip()
                    # Basic validation - exclude common false positives
                    if len(location) >= 3 and location.lower() not in ['the', 'and', 'but', 'for', 'you', 'are']:
                        preferences_detected.append({
                            'type': 'location',
                            'value': location,
                            'confidence': 0.85,
                            'pattern': pattern
                        })
                        logger.debug(f"🔍 PREFERENCE: Detected location '{location}'")
                        break
            
            # 4. COMMUNICATION STYLE PATTERNS
            comm_style_patterns = [
                # "I prefer short responses", "I like detailed explanations"
                r"(?:i|I)\s+(?:prefer|like)\s+(short|brief|long|detailed|simple|technical)\s+(?:responses|answers|explanations)",
                # "Keep it brief", "Make it detailed"
                r"(?:keep\s+it|make\s+it)\s+(brief|short|detailed|simple|technical)",
                # "I want concise answers"
                r"(?:i|I)\s+want\s+(concise|brief|detailed|thorough)\s+(?:answers|responses)",
            ]
            
            for pattern in comm_style_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    style = match.group(1).lower()
                    preferences_detected.append({
                        'type': 'communication_style',
                        'value': style,
                        'confidence': 0.80,
                        'pattern': pattern
                    })
                    logger.debug(f"🔍 PREFERENCE: Detected communication style '{style}'")
                    break
            
            # Store all detected preferences
            stored_any = False
            for pref in preferences_detected:
                stored = await self.bot_core.knowledge_router.store_user_preference(
                    user_id=message_context.user_id,
                    preference_type=pref['type'],
                    preference_value=pref['value'],
                    confidence=pref['confidence'],
                    metadata={
                        'detected_pattern': pref['pattern'],
                        'source_message': content[:100],  # First 100 chars for debugging
                        'channel_id': message_context.channel_id,
                        'detection_method': 'regex_pattern'
                    }
                )
                
                if stored:
                    stored_any = True
                    logger.info(f"✅ PREFERENCE: Stored {pref['type']}='{pref['value']}' "
                              f"for user {message_context.user_id}")
                else:
                    logger.warning(f"⚠️ PREFERENCE: Failed to store {pref['type']}='{pref['value']}' "
                                 f"for user {message_context.user_id}")
            
            if stored_any:
                logger.info(f"✅ PREFERENCE: Stored {len(preferences_detected)} preferences "
                          f"for user {message_context.user_id}")
            
            return stored_any
            
        except Exception as e:
            logger.error(f"❌ Preference extraction failed: {e}")
            return False
    
    def _extract_entity_from_content(self, content: str, pattern: str, entity_type: str) -> Optional[List[str]]:
        """
        Extract entity names from content based on pattern and entity type.
        
        Now handles multiple entities separated by "and" or commas.
        Example: "I love pizza and sushi" → ["pizza", "sushi"]
        
        Args:
            content: User message content
            pattern: Detected pattern (e.g., "love", "like")
            entity_type: Type of entity (food, drink, hobby, place)
            
        Returns:
            List of extracted entity names, or None if none found
        """
        try:
            # Find the pattern in content
            pattern_idx = content.find(pattern)
            if pattern_idx == -1:
                return None
            
            # Extract words after the pattern
            after_pattern = content[pattern_idx + len(pattern):].strip()
            
            # Split by conjunctions and commas to handle multiple entities
            # Example: "pizza and sushi" → ["pizza", "sushi"]
            # Example: "pizza, sushi, and tacos" → ["pizza", "sushi", "tacos"]
            raw_entities = after_pattern.replace(' and ', ',').split(',')
            
            # Remove common articles and prepositions
            articles = ['the', 'a', 'an', 'to', 'for', 'of']
            
            extracted_entities = []
            for raw_entity in raw_entities[:5]:  # Max 5 entities per statement
                # Clean up the entity
                words = raw_entity.strip().split()
                entity_words = []
                
                for word in words[:3]:  # Max 3 words per entity
                    clean_word = word.strip('.,!?;:')
                    if clean_word and clean_word.lower() not in articles:
                        entity_words.append(clean_word)
                
                if entity_words:
                    entity_name = ' '.join(entity_words).lower()
                    if len(entity_name) > 1 and entity_name not in extracted_entities:
                        extracted_entities.append(entity_name)
            
            return extracted_entities if extracted_entities else None
            
        except Exception as e:
            logger.debug(f"Entity extraction failed: {e}")
            return None

    async def _store_conversation_memory(self, message_context: MessageContext, response: str, 
                                       ai_components: Dict[str, Any]) -> bool:
        """Store conversation in memory system with both user and bot emotions."""
        if not self.memory_manager:
            return False
        
        try:
            # � CRITICAL: Strip status footer from response before storage
            # Footer is for Discord display ONLY and must NEVER be stored in vector memory
            from src.utils.discord_status_footer import strip_footer_from_response
            clean_response = strip_footer_from_response(response)
            
            # 🛡️ STANCE FILTERING: Remove second-person emotions from bot response
            # Bot saying "I understand you're frustrated" should NOT make bot's emotion state reflect
            # the user's frustration - bot is expressing empathy, not its own emotional state
            bot_response_for_storage = clean_response
            if self._stance_analyzer:
                try:
                    filtered_bot_text = self._stance_analyzer.filter_second_person_emotions(clean_response)
                    if filtered_bot_text and filtered_bot_text != clean_response:
                        logger.info(
                            "🎯 STANCE FILTER: Removed empathetic second-person clauses from bot response "
                            "(%.1f%% of original)",
                            (1.0 - len(filtered_bot_text) / len(clean_response)) * 100
                        )
                        bot_response_for_storage = filtered_bot_text
                except Exception as e:
                    logger.debug(f"Stance filtering failed, using original response: {e}")
                    bot_response_for_storage = clean_response
            
            # 🛡️ META-CONVERSATION FILTER: Prevent conversations about memory/bot issues from being stored
            # These create recursive awareness loops where the bot is primed to think it has problems
            if self._is_meta_conversation(message_context.content, clean_response):
                logger.warning(
                    "🚫 META-CONVERSATION: Not storing conversation about bot memory/issues for user %s",
                    message_context.user_id
                )
                return False
            
            # 🛡️ FINAL SAFETY CHECK: Don't store obviously broken responses
            if self._is_response_safe_to_store(clean_response):
                # Extract bot emotion from ai_components (Phase 7.5)
                bot_emotion = ai_components.get('bot_emotion')
                
                # Build metadata for bot response including bot emotion and stance analysis
                bot_metadata = {}
                if bot_emotion:
                    bot_metadata['bot_emotion'] = bot_emotion
                    logger.info(
                        "🎭 BOT EMOTION: Storing bot emotion '%s' (intensity: %.2f, confidence: %.2f)",
                        bot_emotion.get('primary_emotion', 'unknown'),
                        bot_emotion.get('intensity', 0.0),
                        bot_emotion.get('confidence', 0.0)
                    )
                
                # Add stance metadata if available
                if self._stance_analyzer:
                    try:
                        stance_analysis = self._stance_analyzer.analyze_user_stance(bot_response_for_storage)
                        if stance_analysis:
                            bot_metadata['stance_analysis'] = {
                                'bot_self_focus': stance_analysis.self_focus,
                                'bot_emotion_type': stance_analysis.emotion_type,
                                'bot_primary_emotions': stance_analysis.primary_emotions,
                                'bot_other_emotions': stance_analysis.other_emotions,
                                'stance_confidence': stance_analysis.confidence
                            }
                            logger.debug(f"📊 BOT STANCE STORED: {bot_metadata['stance_analysis']}")
                    except Exception as e:
                        logger.debug(f"Failed to store stance metadata: {e}")
                
                await self.memory_manager.store_conversation(
                    user_id=message_context.user_id,
                    user_message=message_context.content,
                    bot_response=bot_response_for_storage,  # Use stance-filtered response
                    channel_id=message_context.channel_id,
                    channel_type=message_context.channel_type,
                    pre_analyzed_emotion_data=ai_components.get('emotion_data'),  # User emotion
                    metadata=bot_metadata  # Bot emotion and stance in metadata
                )
                
                # Verify storage
                verification_memories = await self.memory_manager.retrieve_context_aware_memories(
                    user_id=message_context.user_id,
                    query=message_context.content,
                    max_memories=1
                )
                
                if verification_memories:
                    logger.info("✅ MEMORY: Successfully stored and verified conversation for user %s", 
                               message_context.user_id)
                    return True
                else:
                    logger.warning("⚠️ MEMORY: Storage verification failed for user %s", message_context.user_id)
                    return False
            else:
                logger.warning("🛡️ MEMORY: Blocked storage of potentially broken response for user %s", 
                              message_context.user_id)
                return False
                
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Memory storage failed: %s", str(e))
            return False

    def _is_response_safe_to_store(self, response: str) -> bool:
        """Final safety check before storing response in memory."""
        import re
        
        # Block obviously broken responses from being stored
        unsafe_patterns = [
            r'remember that you can remember',
            r'EEREE|Eternalized Eternally',
            r'(\w+\s+){20,}',  # 20+ repeated words
        ]
        
        # Length check - responses over 6000 chars are suspicious
        if len(response) > 6000:
            logger.warning("🛡️ MEMORY SAFETY: Response length suspicious (%d chars)", len(response))
            return False
        
        # Pattern check
        for pattern in unsafe_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                logger.warning("🛡️ MEMORY SAFETY: Unsafe pattern detected: %s", pattern)
                return False
        
        return True
    
    def _is_meta_conversation(self, user_message: str, bot_response: str) -> bool:
        """
        Detect meta-conversations about the bot's memory, functioning, or identity issues.
        
        Meta-conversations create recursive awareness loops where discussing memory problems
        causes those discussions to be stored, which then primes future responses to believe
        there are memory problems. This filter prevents that poisoning.
        
        Args:
            user_message: The user's message
            bot_response: The bot's response
            
        Returns:
            True if this is a meta-conversation that should NOT be stored
        """
        import re
        
        # Patterns that indicate meta-conversations about bot issues
        meta_patterns = [
            # Memory/context issues
            r'\b(fragment|fragmented|fragmenting)\s+(your\s+)?(memory|memories|context)',
            r'\b(corrupt|corrupted|corrupting)\s+(your\s+)?(memory|memories)',
            r'\b(loop|looping|loops|looped)\b',
            r'\b(repeat|repeating|repeated)\s+(yourself|responses?|messages?)',
            r'\b(lost|losing)\s+(your\s+)?(memory|memories|context)',
            r'\b(stuck|stale|frozen)\s+(context|conversation|memory)',
            
            # Bot functioning/identity discussions
            r'\byour\s+(memory|functioning|system|context)\s+(is|has|seems)',
            r'\bsomething\s+(is\s+)?(wrong|off|broken)\s+with\s+(you|your)',
            r'\b(reset|restart|reboot|fix)\s+(you|your\s+memory|your\s+context)',
            r'\bwhat.*happening\s+to\s+(you|your\s+memory)',
            
            # Name confusion discussions (specific pattern from the incident)
            r'\byou.*confus(ed|ing).*names?\b',
            r'\b(i\'?m|you\'?re)\s+\w+.*\byou\'?re\s+\w+\b',  # "I'm X, you're Y" corrections
            
            # Technical debugging discussions
            r'\bconversation\s+(cache|history|context).*\b(clear|reset|stuck)',
            r'\bprompt.*\blog\b',
            
            # Meta-awareness phrases
            r'\bkeeping\s+you\s+in\s+the\s+loop',
            r'\bpart\s+of\s+the\s+process\b',
        ]
        
        # Check both user message and bot response
        combined_text = f"{user_message} {bot_response}".lower()
        
        for pattern in meta_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                logger.debug(f"🔍 META-CONVERSATION: Detected pattern '{pattern}' in conversation")
                return True
        
        return False
    
    def _classify_message_context(self, message_context: MessageContext):
        """
        Platform-agnostic message context classification.
        
        Args:
            message_context: MessageContext object
            
        Returns:
            MemoryContext object with platform-agnostic classification
        """
        from src.memory.context_aware_memory_security import MemoryContext, MemoryContextType, ContextSecurity
        
        try:
            # Determine context type based on platform and channel type
            if message_context.platform == "api":
                # External API calls are treated as DM-like private contexts
                return MemoryContext(
                    context_type=MemoryContextType.DM,
                    server_id=None,
                    channel_id=getattr(message_context, 'channel_id', 'api_channel'),
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_DM,
                )
            elif message_context.platform == "discord":
                # Discord-specific classification
                if getattr(message_context, 'channel_type', 'dm') == 'dm':
                    return MemoryContext(
                        context_type=MemoryContextType.DM,
                        server_id=None,
                        channel_id=getattr(message_context, 'channel_id', 'unknown'),
                        is_private=True,
                        security_level=ContextSecurity.PRIVATE_DM,
                    )
                else:
                    # Guild/server context
                    return MemoryContext(
                        context_type=MemoryContextType.PUBLIC_CHANNEL,
                        server_id=getattr(message_context, 'server_id', None),
                        channel_id=getattr(message_context, 'channel_id', 'unknown'),
                        is_private=False,
                        security_level=ContextSecurity.PUBLIC_CHANNEL,
                    )
            else:
                # Unknown platform - default to private for security
                return MemoryContext(
                    context_type=MemoryContextType.DM,
                    server_id=None,
                    channel_id='unknown',
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_DM,
                )
                
        except Exception as e:
            logger.warning("Context classification failed: %s, using safe defaults", str(e))
            # Safe default - treat as private
            return MemoryContext(
                context_type=MemoryContextType.DM,
                server_id=None,
                channel_id='error',
                is_private=True,
                security_level=ContextSecurity.PRIVATE_DM,
            )

    async def _log_full_prompt_to_file(self, conversation_context: List[Dict[str, Any]], user_id: str, ai_components: Optional[Dict[str, Any]] = None):
        """Log the complete prompt sent to LLM for debugging and review."""
        try:
            import json
            from datetime import datetime
            import os
            from enum import Enum
            from dataclasses import is_dataclass, asdict
            
            # Check if prompt logging is enabled (disabled by default for production)
            if not os.getenv('ENABLE_PROMPT_LOGGING', 'false').lower() == 'true':
                return
            
            # Custom JSON encoder to handle non-serializable objects
            class CustomJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    # Handle Enum types
                    if isinstance(obj, Enum):
                        return obj.value
                    # Handle dataclass types
                    if is_dataclass(obj):
                        return asdict(obj)
                    # Handle datetime types
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    # For other types, try str() representation
                    try:
                        return str(obj)
                    except:
                        return f"<non-serializable: {type(obj).__name__}>"
            
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filename: /app/logs/prompts/botname_YYYYMMDD_HHMMSS_userid.json
            filename = f"/app/logs/prompts/{bot_name}_{timestamp}_{user_id}.json"
            
            # Prepare structured log data
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "bot_name": bot_name,
                "user_id": user_id,
                "message_count": len(conversation_context),
                "total_chars": sum(len(msg.get('content', '')) for msg in conversation_context),
                "messages": conversation_context,
                "ai_components": ai_components or {}  # NEW: Include emotional analysis data
            }
            
            # 🔍 DEBUG: Log ai_components status
            if ai_components:
                logger.info(f"📊 AI_COMPONENTS DEBUG: Logging {len(ai_components)} component keys: {list(ai_components.keys())}")
            else:
                logger.warning(f"📊 AI_COMPONENTS DEBUG: ai_components is None or empty!")
            
            
            # Write to file
            os.makedirs("/app/logs/prompts", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            
            # Also log summary to console
            logger.info(f"📝 PROMPT LOGGED: {filename} ({len(conversation_context)} messages, {log_data['total_chars']} chars)")
            
        except Exception as e:
            logger.warning(f"Failed to log prompt to file: {e}")

    async def _log_llm_response_to_file(self, response: str, user_id: str):
        """Add LLM response to the existing prompt log file for complete conversation picture."""
        try:
            import json
            from datetime import datetime
            import os
            
            # Check if prompt logging is enabled (disabled by default for production)
            if not os.getenv('ENABLE_PROMPT_LOGGING', 'false').lower() == 'true':
                return
            
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # Find the most recent prompt file for this user and bot
            prompt_dir = "/app/logs/prompts"
            if not os.path.exists(prompt_dir):
                logger.warning("Prompt directory not found, cannot log response")
                return
                
            # Find the most recent file matching the pattern
            import glob
            pattern = f"{prompt_dir}/{bot_name}_*_{user_id}.json"
            files = glob.glob(pattern)
            if not files:
                logger.warning(f"No prompt file found for user {user_id}, cannot log response")
                return
                
            # Get the most recent file
            latest_file = max(files, key=os.path.getctime)
            
            # Read existing data
            with open(latest_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # Add response data
            log_data["llm_response"] = {
                "content": response,
                "char_count": len(response),
                "response_timestamp": datetime.now().isoformat()
            }
            
            # Write back to file (using the same CustomJSONEncoder from _log_full_prompt_to_file)
            with open(latest_file, 'w', encoding='utf-8') as f:
                # Use safe encoding - if CustomJSONEncoder isn't available here, use ensure_ascii=False only
                try:
                    from enum import Enum
                    from dataclasses import is_dataclass, asdict
                    class CustomJSONEncoder(json.JSONEncoder):
                        def default(self, obj):
                            if isinstance(obj, Enum):
                                return obj.value
                            if is_dataclass(obj):
                                return asdict(obj)
                            if isinstance(obj, datetime):
                                return obj.isoformat()
                            try:
                                return str(obj)
                            except:
                                return f"<non-serializable: {type(obj).__name__}>"
                    json.dump(log_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
                except:
                    # Fallback without custom encoder
                    json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Log summary to console
            logger.info(f"📝 RESPONSE LOGGED: {latest_file} ({len(response)} chars)")
            
        except Exception as e:
            logger.warning(f"Failed to log response to file: {e}")

    async def _build_enriched_metadata(
        self,
        message_context: MessageContext,
        ai_components: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        knowledge_stored: bool,
        memory_stored: bool,
        validation_result: Dict[str, Any],
        processing_time_ms: int
    ) -> Dict[str, Any]:
        """
        Build enriched metadata for API consumers (3rd party dashboards).
        
        Supports three metadata levels:
        - "basic": Essential data only (memory_count, knowledge_stored, success flags)
        - "standard": Basic + AI components + security validation (default)
        - "extended": Standard + all analytics (temporal, vector memory, relationships, etc.)
        
        Provides comprehensive debugging and analytics data including:
        - Memory and knowledge extraction details
        - Vector memory intelligence
        - Phase 5 temporal intelligence (if available)
        - CDL character context
        - Relationship metrics
        - Processing pipeline breakdown
        """
        metadata_level = message_context.metadata_level.lower()
        
        # BASIC level: Minimal essential data
        if metadata_level == "basic":
            return {
                "memory_count": len(relevant_memories) if relevant_memories else 0,
                "knowledge_stored": knowledge_stored,
                "memory_stored": memory_stored,
                "processing_time_ms": processing_time_ms
            }
        
        # STANDARD level: Basic + AI components + security (DEFAULT)
        metadata = {
            "memory_count": len(relevant_memories) if relevant_memories else 0,
            "knowledge_stored": knowledge_stored,
            "ai_components": ai_components,
            "security_validation": validation_result
        }
        
        # Add workflow data if available (from message_context.metadata)
        if message_context.metadata and 'workflow_result' in message_context.metadata:
            # Include workflow data in ai_components for footer display
            if ai_components and isinstance(ai_components, dict):
                ai_components['workflow_result'] = message_context.metadata['workflow_result']
        
        # Return standard level if not extended
        if metadata_level != "extended":
            return metadata
        
        # EXTENDED level: Add comprehensive analytics data
        # 1. Knowledge Extraction Details
        metadata["knowledge_details"] = {
            "facts_extracted": 0,  # TODO: Track actual count from knowledge extraction
            "entities_discovered": 0,  # TODO: Track from semantic router
            "relationships_created": 0,  # TODO: Track from graph operations
            "extraction_attempted": True,
            "storage_success": knowledge_stored
        }
        
        # 2. Vector Memory Intelligence
        if relevant_memories:
            # Calculate average relevance score from memory retrieval
            relevance_scores = []
            for memory in relevant_memories:
                if isinstance(memory, dict) and 'score' in memory:
                    relevance_scores.append(float(memory['score']))
            
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            metadata["vector_memory"] = {
                "memories_retrieved": len(relevant_memories),
                "average_relevance_score": round(avg_relevance, 3),
                "collection": os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory'),
                "embedding_model": os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
                "vector_dimension": int(os.getenv('VECTOR_DIMENSION', '384')),
                "search_method": "3d_named_vectors"  # content, emotion, semantic
            }
        
        # 3. Phase 5 Temporal Intelligence (if available)
        if self.confidence_analyzer:
            try:
                # Get bot name for queries
                bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
                
                # Get confidence metrics from analyzer
                confidence_metrics = self.confidence_analyzer.calculate_confidence_metrics(
                    ai_components=ai_components,
                    memory_count=len(relevant_memories) if relevant_memories else 0,
                    processing_time_ms=processing_time_ms
                )
                
                # Calculate interaction pattern from temporal data
                interaction_pattern = "stable"  # Default
                if self.temporal_client and self.temporal_client.enabled:
                    try:
                        # Query conversation frequency over last 30 days
                        frequency_query = f'''
                            from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                            |> range(start: -30d)
                            |> filter(fn: (r) => r._measurement == "conversation_quality")
                            |> filter(fn: (r) => r.bot == "{bot_name}")
                            |> filter(fn: (r) => r.user_id == "{message_context.user_id}")
                            |> aggregateWindow(every: 1d, fn: count)
                        '''
                        
                        frequency_data = await self.temporal_client.query_data(frequency_query)
                        
                        if len(frequency_data) >= 7:
                            # Calculate weekly averages
                            recent_week = sum(d.get('_value', 0) for d in frequency_data[-7:]) / 7
                            older_week = sum(d.get('_value', 0) for d in frequency_data[:7]) / 7
                            
                            if recent_week > older_week * 1.5:
                                interaction_pattern = "increasing"
                            elif recent_week < older_week * 0.5:
                                interaction_pattern = "decreasing"
                            elif recent_week > 5:
                                interaction_pattern = "frequent"
                            elif recent_week < 1:
                                interaction_pattern = "sporadic"
                            else:
                                interaction_pattern = "stable"
                    except Exception as e:
                        logger.debug(f"Could not calculate interaction pattern: {e}")
                
                metadata["temporal_intelligence"] = {
                    "confidence_evolution": round(confidence_metrics.overall_confidence, 3),
                    "user_fact_confidence": round(confidence_metrics.user_fact_confidence, 3),
                    "relationship_confidence": round(confidence_metrics.relationship_confidence, 3),
                    "context_confidence": round(confidence_metrics.context_confidence, 3),
                    "emotional_confidence": round(confidence_metrics.emotional_confidence, 3),
                    "interaction_pattern": interaction_pattern,
                    "data_source": "temporal_relationship_intelligence"
                }
            except Exception as e:
                logger.debug(f"Could not calculate temporal intelligence: {e}")
        
        # 4. CDL Character Context
        character_file = os.getenv('CDL_DEFAULT_CHARACTER', 'characters/examples/default_assistant.json')
        bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
        
        metadata["character_context"] = {
            "character_name": bot_name,
            "character_file": character_file,
            "personality_system": "cdl",  # Character Definition Language
            "communication_style": "authentic_character_voice",
            "roleplay_immersion": "enabled"  # Characters maintain personality consistency
        }
        
        # 5. Relationship Metrics (if available from Phase 4)
        conversation_intelligence_data = ai_components.get('conversation_intelligence')
        if conversation_intelligence_data is None:
            conversation_intelligence_data = {}
        relationship_level = conversation_intelligence_data.get('relationship_level', 'acquaintance')
        
        # Map relationship level to approximate scores (0-100 scale)
        relationship_mapping = {
            'stranger': {'affection': 10, 'trust': 15, 'attunement': 20},
            'acquaintance': {'affection': 35, 'trust': 40, 'attunement': 45},
            'friend': {'affection': 65, 'trust': 70, 'attunement': 75},
            'close_friend': {'affection': 85, 'trust': 88, 'attunement': 90},
            'best_friend': {'affection': 95, 'trust': 95, 'attunement': 98}
        }
        
        scores = relationship_mapping.get(relationship_level, relationship_mapping['acquaintance'])
        
        metadata["relationship"] = {
            "affection": scores['affection'],
            "trust": scores['trust'],
            "attunement": scores['attunement'],
            "relationship_level": relationship_level,
            "interaction_count": len(relevant_memories) if relevant_memories else 0,
            "memory_depth": "established" if len(relevant_memories) > 5 else "developing"
        }
        
        # 6. Processing Pipeline Breakdown
        conversation_intelligence_metadata = conversation_intelligence_data.get('processing_metadata', {}) if conversation_intelligence_data else {}
        performance_metrics = conversation_intelligence_metadata.get('performance_metrics', {})
        
        metadata["processing_pipeline"] = {
            "emotion_analysis_duration_ms": round(performance_metrics.get('phase2_duration', 0) * 1000, 2),
            "conversation_intelligence_ms": round(conversation_intelligence_metadata.get('total_duration', 0) * 1000, 2),
            "total_processing_ms": processing_time_ms,
            "phases_executed": conversation_intelligence_metadata.get('phases_executed', []),
            "phases_completed": conversation_intelligence_metadata.get('phases_completed', 0)
        }
        
        # 7. Conversation Context Indicators
        metadata["conversation_intelligence"] = {
            "context_switches_detected": len(conversation_intelligence_data.get('conversation_context_switches', [])),
            "conversation_mode": conversation_intelligence_data.get('conversation_mode', 'standard'),
            "interaction_type": conversation_intelligence_data.get('interaction_type', 'general'),
            "response_guidance": conversation_intelligence_data.get('response_guidance', 'natural_conversation')
        }
        
        return metadata

    async def _coordinate_learning_intelligence(
        self, 
        message_context: MessageContext, 
        ai_components: Dict[str, Any], 
        relevant_memories: List[Dict[str, Any]], 
        response: str
    ):
        """
        🎯 LEARNING INTELLIGENCE: Orchestrator coordination and learning pipeline management.
        
        Coordinates all learning components and manages predictive adaptation:
        - Learning health monitoring across all components
        - Predictive adaptation based on user patterns
        - Learning pipeline task scheduling and execution
        - Cross-component intelligence correlation
        """
        if not self.learning_orchestrator:
            logger.debug("Learning Intelligence Orchestrator: Not available")
            return
        
        try:
            bot_name = get_normalized_bot_name_from_env()
            
            # 1. Predictive Adaptation - Analyze patterns and predict user needs
            if self.predictive_engine:
                try:
                    predictions = await self.predictive_engine.predict_user_needs(
                        user_id=message_context.user_id,
                        bot_name=bot_name,
                        prediction_horizon_hours=24
                    )
                    
                    if predictions:
                        logger.info("🔮 PREDICTIVE: Generated %d predictions for user %s", 
                                   len(predictions), message_context.user_id)
                        
                        # Record predictions in ai_components for potential CDL integration
                        ai_components['learning_predictions'] = {
                            'prediction_count': len(predictions),
                            'prediction_types': [p.prediction_type.value for p in predictions[:3]],  # Top 3
                            'confidence_average': len(predictions)  # Simple count for now
                        }
                except Exception as e:
                    logger.warning("Learning Intelligence predictive adaptation failed: %s", str(e))
            
            # 2. Learning Health Monitoring (periodic - every 10th message)
            # Use hash of user_id to determine if this should trigger health monitoring
            if hash(message_context.user_id) % 10 == 0:
                try:
                    health_report = await self.learning_orchestrator.monitor_learning_health(bot_name)
                    
                    # Log health status for monitoring
                    logger.info("🏥 LEARNING HEALTH: Overall: %s, Performance: %.3f, Components: %d/%d healthy", 
                               health_report.overall_health.value,
                               health_report.system_performance_score,
                               len([s for s in health_report.component_statuses if s.status.value == 'healthy']),
                               len(health_report.component_statuses))
                    
                    # Store health metrics in ai_components
                    ai_components['learning_health'] = {
                        'overall_health': health_report.overall_health.value,
                        'system_performance': health_report.system_performance_score,
                        'healthy_components': len([s for s in health_report.component_statuses if s.status.value == 'healthy']),
                        'total_components': len(health_report.component_statuses)
                    }
                except Exception as e:
                    logger.warning("Sprint 6 learning health monitoring failed: %s", str(e))
            
            # 3. Learning Pipeline Coordination (background task - don't block message processing)
            if self.learning_pipeline:
                try:
                    # Schedule learning cycle in background (every 50th message per user)
                    if hash(message_context.user_id) % 50 == 0:
                        cycle_name = f"Adaptive Learning Cycle - {bot_name} - {datetime.now().strftime('%H:%M')}"
                        asyncio.create_task(
                            self.learning_pipeline.schedule_learning_cycle(
                                name=cycle_name,
                                delay_seconds=30  # Small delay to not interfere with current message
                            )
                        )
                        logger.info("🔄 LEARNING PIPELINE: Scheduled adaptive learning cycle for %s", bot_name)
                except Exception as e:
                    logger.warning("Sprint 6 learning pipeline coordination failed: %s", str(e))
            
            # 4. Record Sprint 6 metrics to InfluxDB (if available)
            if self.temporal_client and hasattr(self.temporal_client, 'record_point'):
                try:
                    # Ensure ai_components is not None to prevent NoneType errors
                    if ai_components is None:
                        logger.warning("ai_components is None - skipping Sprint 6 InfluxDB metrics")
                        return
                    
                    # Import Point class for proper InfluxDB point creation
                    try:
                        from influxdb_client.client.write.point import Point
                        
                        # Safe extraction to avoid chained .get() on None values
                        learning_predictions = ai_components.get('learning_predictions')
                        if learning_predictions and isinstance(learning_predictions, dict):
                            predictions_count = len(learning_predictions.get('prediction_types', []))
                        else:
                            predictions_count = 0
                        
                        learning_health = ai_components.get('learning_health')
                        if learning_health and isinstance(learning_health, dict):
                            system_performance = learning_health.get('system_performance', 0.0)
                            healthy_components = learning_health.get('healthy_components', 0)
                        else:
                            system_performance = 0.0
                            healthy_components = 0
                        
                        # Create proper InfluxDB Point object instead of named parameters
                        point = Point("learning_intelligence_orchestrator") \
                            .tag("bot_name", bot_name) \
                            .tag("user_id", message_context.user_id) \
                            .tag("platform", message_context.platform) \
                            .field("predictions_generated", predictions_count) \
                            .field("health_monitoring_triggered", bool(ai_components.get('learning_health'))) \
                            .field("learning_orchestrator_available", bool(self.learning_orchestrator)) \
                            .field("predictive_engine_available", bool(self.predictive_engine)) \
                            .field("learning_pipeline_available", bool(self.learning_pipeline)) \
                            .field("system_performance", system_performance) \
                            .field("healthy_components", healthy_components) \
                            .time(datetime.utcnow())
                        
                        await self.temporal_client.record_point(point)
                        
                    except ImportError:
                        logger.debug("InfluxDB client not available - skipping Sprint 6 metrics")
                        
                except Exception as e:
                    logger.warning("Sprint 6 InfluxDB metrics recording failed: %s", str(e))
                    
        except Exception as e:
            logger.error("Sprint 6 IntelligenceOrchestrator coordination failed: %s", str(e))

    async def _retrieve_enriched_summaries(
        self, 
        user_id: str, 
        bot_name: str, 
        days_back: int = 7,  # Reduced from 30 - only recent summaries
        limit: int = 2,      # Reduced from 10 - most recent 1-2 summaries max
        search_keywords: Optional[List[str]] = None  # NEW: Optional keywords for recall queries
    ) -> List[Dict[str, Any]]:
        """
        Retrieve enriched conversation summaries from PostgreSQL.
        
        These are high-quality LLM-generated summaries created by the enrichment worker
        in 24-hour windows. Strategy: retrieve only the most recent 1-2 summaries
        to provide background context without overwhelming the prompt.
        
        When search_keywords provided (recall queries like "we talked about X"):
        - Searches key_topics array (fast GIN index)
        - Falls back to full-text search in summary_text
        - Returns summaries matching ANY keyword
        
        Args:
            user_id: User identifier
            bot_name: Bot name for filtering summaries
            days_back: How many days back to look (default 7 for recent context)
            limit: Maximum summaries (default 2 - usually just 1 latest)
            search_keywords: Optional list of keywords to search for (e.g., ["prompt engineering"])
            
        Returns:
            List of summary dictionaries with text, topics, timeframe, etc.
        """
        postgres_pool = getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
        if not postgres_pool:
            logger.debug("PostgreSQL pool not available - no enriched summaries")
            return []
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            async with postgres_pool.acquire() as conn:
                # Build query with optional keyword search
                if search_keywords:
                    # 🧠 RECALL QUERY: Search by keywords/topics (hybrid approach)
                    # Strategy: Use GIN index on key_topics[] first, fallback to full-text
                    logger.info(f"🔍 KEYWORD SEARCH: Looking for summaries matching: {search_keywords}")
                    
                    # Prepare keyword array for PostgreSQL array overlap operator
                    keyword_array = search_keywords  # ['prompt engineering', 'memory', ...]
                    
                    # Prepare ILIKE patterns for full-text fallback
                    like_conditions = " OR ".join([f"summary_text ILIKE ${i+5}" for i in range(len(search_keywords))])
                    like_params = [f'%{kw}%' for kw in search_keywords]
                    
                    query = f"""
                        SELECT 
                            summary_text,
                            start_timestamp,
                            end_timestamp,
                            message_count,
                            key_topics,
                            emotional_tone,
                            confidence_score,
                            created_at
                        FROM conversation_summaries
                        WHERE user_id = $1 
                          AND bot_name = $2
                          AND start_timestamp >= $3
                          AND confidence_score >= 0.3
                          AND (
                              -- Fast: GIN index array overlap (any keyword matches topic array)
                              key_topics && $4
                              -- Fallback: Full-text search in summary
                              OR {like_conditions}
                          )
                        ORDER BY start_timestamp DESC
                        LIMIT ${len(like_params) + 5}
                    """
                    
                    rows = await conn.fetch(query, user_id, bot_name, cutoff_date, keyword_array, *like_params, limit)
                    
                    logger.info(f"✅ KEYWORD MATCH: Found {len(rows)} summaries matching keywords")
                    
                else:
                    # Default: Most recent summaries (no keyword filtering)
                    rows = await conn.fetch("""
                        SELECT 
                            summary_text,
                            start_timestamp,
                            end_timestamp,
                            message_count,
                            key_topics,
                            emotional_tone,
                            confidence_score,
                            created_at
                        FROM conversation_summaries
                        WHERE user_id = $1 
                          AND bot_name = $2
                          AND start_timestamp >= $3
                          AND confidence_score >= 0.3  -- Only high-confidence summaries
                        ORDER BY start_timestamp DESC
                        LIMIT $4
                    """, user_id, bot_name, cutoff_date, limit)
                
                summaries = []
                for row in rows:
                    summaries.append({
                        'summary_text': row['summary_text'],
                        'start_timestamp': row['start_timestamp'],
                        'end_timestamp': row['end_timestamp'],
                        'message_count': row['message_count'],
                        'key_topics': row['key_topics'] or [],
                        'emotional_tone': row['emotional_tone'],
                        'confidence_score': row['confidence_score'],
                        'created_at': row['created_at']
                    })
                
                if summaries:
                    logger.info(f"📚 Retrieved {len(summaries)} high-confidence enriched summaries for {user_id}")
                else:
                    logger.debug(f"📚 No enriched summaries found for {user_id} and {bot_name}")
                
                return summaries
                
        except Exception as e:
            logger.error(f"Failed to retrieve enriched summaries: %s", e)
            return []


def create_message_processor(bot_core, memory_manager, llm_client, **kwargs) -> MessageProcessor:
    """Factory function to create a MessageProcessor instance."""
    return MessageProcessor(
        bot_core=bot_core,
        memory_manager=memory_manager, 
        llm_client=llm_client,
        **kwargs
    )