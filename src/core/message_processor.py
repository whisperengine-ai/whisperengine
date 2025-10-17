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
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity
from src.memory.vector_memory_system import get_normalized_bot_name_from_env
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
    PromptComponentType
)

# Relationship Intelligence components
from src.relationships.evolution_engine import create_relationship_evolution_engine
from src.relationships.trust_recovery import create_trust_recovery_system

# Emoji Intelligence component
from src.intelligence.database_emoji_selector import create_database_emoji_selector

# Emotional Adaptation component
from src.intelligence.emotional_context_engine import EmotionalContextEngine, EmotionalContext, EmotionalState

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
    memory_stored: bool = False
    metadata: Optional[Dict[str, Any]] = None

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
        
        # TrendWise Adaptive Learning: Initialize trend analysis and confidence adaptation
        self.trend_analyzer = None
        self.confidence_adapter = None
        
        if self.temporal_client:
            try:
                from src.analytics.trend_analyzer import create_trend_analyzer
                from src.adaptation.confidence_adapter import create_confidence_adapter
                
                self.trend_analyzer = create_trend_analyzer(self.temporal_client)
                self.confidence_adapter = create_confidence_adapter(self.trend_analyzer)
                logger.info("TrendWise Adaptive Learning: Trend analysis and confidence adaptation initialized")
            except ImportError as e:
                logger.warning("TrendWise components not available: %s", e)
                self.trend_analyzer = None
                self.confidence_adapter = None
        
        # Relationship Intelligence: Lazy initialization (postgres_pool may not be ready yet)
        self.relationship_engine = None
        self.trust_recovery = None
        self._relationship_init_attempted = False  # Track if we've tried initializing
        
        # Learning Intelligence Orchestrator: Initialize unified learning coordination
        self.learning_orchestrator = None
        self.predictive_engine = None
        self.learning_pipeline = None
        
        if self.temporal_client:
            try:
                from src.orchestration.learning_orchestrator import LearningOrchestrator
                from src.adaptation.predictive_engine import PredictiveAdaptationEngine
                from src.pipeline.learning_manager import LearningPipelineManager
                
                # Initialize Learning Intelligence components with available adaptive learning dependencies
                self.learning_orchestrator = LearningOrchestrator(
                    trend_analyzer=self.trend_analyzer,
                    confidence_adapter=self.confidence_adapter,
                    memory_manager=self.memory_manager,
                    temporal_client=self.temporal_client,
                    postgres_pool=getattr(bot_core, 'postgres_pool', None) if bot_core else None
                )
                
                # Pass dependencies to Predictive Engine
                self.predictive_engine = PredictiveAdaptationEngine(
                    trend_analyzer=self.trend_analyzer,
                    confidence_adapter=self.confidence_adapter,
                    temporal_client=self.temporal_client,
                    memory_manager=self.memory_manager
                )
                self.learning_pipeline = LearningPipelineManager()
                
                logger.info("Learning Intelligence Orchestrator: Learning coordination components initialized")
            except ImportError as e:
                logger.warning("Learning Intelligence Orchestrator components not available: %s", e)
                self.learning_orchestrator = None
                self.predictive_engine = None
                self.learning_pipeline = None
        
        # Shared emotion analyzer for preventing RoBERTa race conditions
        self._shared_emotion_analyzer = None
        self._shared_analyzer_lock = asyncio.Lock()
        
        # Initialize fidelity metrics collector for performance tracking
        try:
            from src.monitoring.fidelity_metrics_collector import get_fidelity_metrics_collector
            self.fidelity_metrics = get_fidelity_metrics_collector()
            logger.debug("Fidelity metrics collector initialized")
        except ImportError:
            logger.warning("Fidelity metrics collector not available")
            self.fidelity_metrics = None
        
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
        
        # Initialize Proactive Conversation Engagement Engine for natural topic suggestions
        try:
            from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
            
            # Get personality profiler if available (for personality-based topic suggestions)
            personality_profiler = None
            if hasattr(self, 'bot_core') and self.bot_core:
                personality_profiler = getattr(self.bot_core, 'personality_profiler', None)
            
            self.engagement_engine = ProactiveConversationEngagementEngine(
                emotional_engine=self._shared_emotion_analyzer,  # Correct parameter name
                personality_profiler=personality_profiler,
                memory_manager=self.memory_manager,  # Add memory manager for conversation history
                stagnation_threshold_minutes=10,  # Conservative: 10 min before suggesting topics
                engagement_check_interval_minutes=5,  # Check every 5 min
                max_proactive_suggestions_per_hour=3  # Conservative: max 3 suggestions/hour
            )
            logger.info("🎯 Proactive Conversation Engagement Engine initialized")
            
            # Store in bot_core for access by integration point (line 3041)
            if hasattr(self, 'bot_core') and self.bot_core:
                self.bot_core.engagement_engine = self.engagement_engine
            
            # Log configuration for debugging
            logger.info("🎯 ENGAGEMENT CONFIG: Stagnation threshold: %d min, Check interval: %d min, Max suggestions: %d/hour",
                       self.engagement_engine.stagnation_threshold.total_seconds() / 60,
                       self.engagement_engine.engagement_check_interval.total_seconds() / 60,
                       self.engagement_engine.max_suggestions_per_hour)
                       
        except ImportError as e:
            logger.warning("Proactive engagement engine not available: %s", e)
            self.engagement_engine = None
        except Exception as e:
            logger.error("Proactive engagement engine initialization failed: %s", e)
            self.engagement_engine = None
        
        # Track processing state for debugging
        self._last_security_validation = None
        self._last_emotional_context = None
    
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
            
            # Phase 3: Memory retrieval with context-aware filtering
            relevant_memories = await self._retrieve_relevant_memories(message_context)
            
            # Phase 4: Conversation history and context building
            # 🚀 Structured Prompt Assembly (default - no feature flag!)
            conversation_context = await self._build_conversation_context_structured(
                message_context, relevant_memories
            )
            
            # Phase 5: AI component processing (parallel)
            ai_components = await self._process_ai_components_parallel(
                message_context, conversation_context
            )
            
            # Phase 5.5: Enhanced conversation context with AI intelligence
            conversation_context = await self._build_conversation_context_with_ai_intelligence(
                message_context, relevant_memories, ai_components
            )
            
            # Phase 6: Image processing if attachments present
            if message_context.attachments:
                conversation_context = await self._process_attachments(
                    message_context, conversation_context
                )
            
            # Phase 6.5: Bot Emotional Self-Awareness (NEW - Phase 7.6)
            # Retrieve bot's recent emotional history for self-aware responses
            bot_emotional_state = await self._analyze_bot_emotional_trajectory(message_context)
            if bot_emotional_state:
                ai_components['bot_emotional_state'] = bot_emotional_state
                logger.debug(
                    "🎭 BOT SELF-AWARENESS: Current state - %s (trajectory: %s)",
                    bot_emotional_state.get('current_emotion', 'unknown'),
                    bot_emotional_state.get('trajectory_direction', 'stable')
                )
            
            # Phase 6.7: Adaptive Learning Intelligence (Relationship & Confidence)
            # Retrieve relationship scores and conversation trends BEFORE response generation
            await self._enrich_ai_components_with_adaptive_learning(
                message_context, ai_components, relevant_memories
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
            
            # Phase 7.6: Intelligent Emoji Decoration (NEW - Database-driven post-LLM enhancement)
            # Try to initialize emoji selector if not yet available (lazy initialization)
            if not self.emoji_selector:
                self._try_initialize_emoji_selector()
            
            if self.emoji_selector and self.character_name:
                try:
                    # Step 1: Filter inappropriate emojis from LLM's own response
                    # (e.g., remove celebration emojis when user is in distress)
                    filtered_response = self.emoji_selector.filter_inappropriate_emojis(
                        message=response,
                        user_emotion_data=ai_components.get('emotion_analysis')
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
                        user_emotion_data=ai_components.get('emotion_analysis'),
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
            # Extract facts from USER message about the user
            knowledge_stored = await self._extract_and_store_knowledge(
                message_context, ai_components, extract_from='user'
            )
            
            # NOTE: Bot self-learning is handled by Character Episodic Intelligence (PHASE 1)
            # Character episodic memories are extracted from vector conversations with RoBERTa emotion scoring
            # See: src/characters/learning/character_vector_episodic_intelligence.py
            # Bot self-facts would be redundant with the episodic memory system
            
            # Phase 9c: User preference extraction and storage (PostgreSQL)
            preference_stored = await self._extract_and_store_user_preferences(
                message_context
            )
            
            # Phase 10: Learning Intelligence Orchestrator - Unified Learning Coordination
            await self._coordinate_learning_intelligence(
                message_context, ai_components, relevant_memories, response
            )
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
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
                        "channel_type": str(message_context.channel_type or "unknown")
                    }
                )
            
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
            
            return ProcessingResult(
                response=response,
                success=True,
                processing_time_ms=processing_time_ms,
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
                    await self.temporal_client.record_user_emotion(
                        bot_name=bot_name,
                        user_id=message_context.user_id,
                        primary_emotion=user_emotion.get('primary_emotion', 'neutral'),
                        intensity=user_emotion.get('intensity', 0.0),
                        confidence=user_emotion.get('confidence', 0.0)
                    )
                    logger.debug(
                        "📊 TEMPORAL: Recorded user emotion '%s' to InfluxDB (intensity: %.2f)",
                        user_emotion.get('primary_emotion', 'neutral'),
                        user_emotion.get('intensity', 0.0)
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

    async def _validate_security(self, message_context: MessageContext) -> Dict[str, Any]:
        """Validate message security and sanitize content."""
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
        """Process message for automatic name detection and storage."""
        try:
            from src.utils.automatic_name_storage import create_automatic_name_storage
            from src.llm.llm_protocol import create_llm_client
            
            if self.memory_manager:
                llm_client = create_llm_client()
                name_storage = create_automatic_name_storage(self.memory_manager, llm_client)
                detected_name = await name_storage.process_message_for_names(
                    message_context.user_id, message_context.content
                )
                if detected_name:
                    logger.info("🏷️ Auto-detected name '%s' for user %s", detected_name, message_context.user_id)
        except (ImportError, AttributeError, ValueError) as e:
            logger.debug("Name detection failed: %s", str(e))

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
                    
                    # Categorize facts
                    preferences = []
                    background = []
                    relationships = []
                    activities = []
                    possessions = []
                    other_facts = []
                    
                    for fact in facts:
                        entity_name = fact.get('entity_name', '')
                        relationship_type = fact.get('relationship_type', '')
                        confidence = fact.get('weighted_confidence', fact.get('confidence', 0.5))
                        potentially_outdated = fact.get('potentially_outdated', False)
                        
                        # Skip very low confidence facts
                        if confidence < 0.4 or potentially_outdated:
                            continue
                        
                        # Categorize by relationship type
                        if relationship_type in ['likes', 'loves', 'enjoys', 'prefers', 'dislikes', 'hates']:
                            preferences.append(f"{relationship_type} {entity_name}")
                        elif relationship_type in ['works_at', 'studies_at', 'lives_in', 'from']:
                            background.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                        elif relationship_type in ['son', 'daughter', 'parent', 'sibling', 'friend', 'partner']:
                            relationships.append(f"{relationship_type} {entity_name}")
                        elif relationship_type in ['visited', 'goes_to', 'attends', 'plays', 'does']:
                            activities.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                        elif relationship_type in ['owns', 'has']:
                            possessions.append(f"{relationship_type} {entity_name}")
                        else:
                            other_facts.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                    
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

    async def _retrieve_relevant_memories(self, message_context: MessageContext) -> List[Dict[str, Any]]:
        """Retrieve relevant memories with context-aware filtering and MemoryBoost optimization."""
        if not self.memory_manager:
            logger.warning("Memory manager not available; skipping memory retrieval.")
            return []

        try:
            # Start timing memory retrieval
            memory_start_time = datetime.now()
            
            # Create platform-agnostic message context classification
            classified_context = self._classify_message_context(message_context)
            logger.debug("Message context classified: %s", classified_context.context_type.value)

            # 🚀 MEMORYBOOST: Try enhanced memory retrieval first if available
            if hasattr(self.memory_manager, 'retrieve_relevant_memories_with_memoryboost'):
                try:
                    # Build conversation context for MemoryBoost optimization
                    conversation_context = self._build_conversation_context_for_memoryboost(message_context)
                    
                    # Use MemoryBoost enhanced retrieval
                    memoryboost_result = await self.memory_manager.retrieve_relevant_memories_with_memoryboost(
                        user_id=message_context.user_id,
                        query=message_context.content,
                        limit=20,
                        conversation_context=conversation_context,
                        apply_quality_scoring=True,
                        apply_optimizations=True
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
            
            # Fallback to context-aware retrieval
            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                user_id=message_context.user_id,
                query=message_context.content,
                max_memories=20,
                context=classified_context,
                emotional_context="general conversation"
            )
            
            logger.info("🔍 MEMORY: Retrieved %d memories via context-aware fallback", len(relevant_memories))
            
            # REMOVED: Fake estimated memory metrics for fallback - not useful
            # Fallback doesn't provide real relevance/similarity scores
            
            return relevant_memories
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Memory retrieval failed: %s", str(e))
            return []

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

    async def _build_conversation_context(self, message_context: MessageContext, 
                                        relevant_memories: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        🚀 SOPHISTICATED CONVERSATION CONTEXT BUILDING 🚀
        
        Build conversation context for LLM processing with sophisticated memory narrative,
        conversation cache integration, and advanced system message consolidation.
        
        Restored from original events.py implementation with full sophistication.
        """
        conversation_context = []
        
        # Debug memory input
        user_id = message_context.user_id
        logger.info(f"🤖 LLM CONTEXT DEBUG: Building context for user {user_id}")
        logger.info(f"🤖 LLM CONTEXT DEBUG: Memory input - {len(relevant_memories) if relevant_memories else 0} memories")
        
        # Add time context for temporal awareness
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        
        # 🚨 SOPHISTICATED MEMORY NARRATIVE BUILDING: Restored from original implementation
        memory_fragments = []
        if relevant_memories:
            logger.info(f"🤖 LLM CONTEXT DEBUG: Processing {len(relevant_memories)} memories for context")
            
            # Handle both legacy and hierarchical memory formats (original sophistication)
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
            
            # Process global facts
            if global_facts:
                gf_text = "; ".join(
                    memory["metadata"].get("fact", "")[:160] for memory in global_facts
                    if memory.get("metadata", {}).get("type") == "global_fact"
                )
                if gf_text:
                    memory_fragments.append(f"Shared truths: {gf_text}")
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added global facts: {gf_text[:100]}...")
            
            # 🚀 ADVANCED USER MEMORY PROCESSING: Restored sophisticated narrative building
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
                            memory_text = f"[Previous conversation: {content[:500]}]"  # Increased from 120 to 500 chars
                        else:
                            memory_text = f"[Memory: {content[:500]}]"  # Increased from 120 to 500 chars
                        
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
                            user_msg = md.get("user_message")[:300]  # Increased from 100 to 300 chars
                            bot_msg = md.get("bot_response")[:300]  # Increased from 100 to 300 chars
                            memory_text = f"[User said: \"{user_msg}\", You responded: \"{bot_msg}\"]"
                            
                            if is_recent:
                                recent_conversation_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata conversation")
                            else:
                                conversation_memory_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata conversation")
                        elif md.get("user_message"):
                            user_msg = md.get("user_message")[:300]  # Increased from 120 to 300 chars
                            memory_text = f"[User said: \"{user_msg}\"]"
                            
                            if is_recent:
                                recent_conversation_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata user message")
                            else:
                                conversation_memory_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata user message")
                        elif md.get("type") == "user_fact":
                            memory_text = f"[Fact: {md.get('fact', '')[:300]}]"  # Increased from 120 to 300 chars
                            conversation_memory_parts.append(memory_text)  # Facts are not time-sensitive
                            logger.info(f"🔍 MEMORY DEBUG: ✅ Added from metadata fact")
                        else:
                            logger.warning(f"🔍 MEMORY DEBUG: ❌ No valid content or metadata structure")
                
                # Build memory narrative with proper hierarchy: Facts (long-term) vs Summaries (medium-term)
                memory_parts = []
                
                # Separate facts from conversations for better organization
                user_facts = []
                older_conversation_summaries = []  # Real summaries, not just topics
                
                # 🚀 PHASE 2: PostgreSQL fact retrieval (PRIMARY - 12-25x faster than string parsing)
                postgres_facts = await self._get_user_facts_from_postgres(
                    user_id=message_context.user_id,
                    bot_name=get_normalized_bot_name_from_env()
                )
                if postgres_facts:
                    user_facts.extend(postgres_facts)
                    logger.info(f"✅ POSTGRES FACTS: Added {len(postgres_facts)} facts from PostgreSQL")
                
                # Legacy: Extract facts from memory content (FALLBACK - will be removed in Phase 1)
                legacy_facts = self._extract_user_facts_from_memories(user_memories)
                if legacy_facts and not postgres_facts:
                    # Only use legacy facts if PostgreSQL didn't return any
                    user_facts.extend(legacy_facts)
                    logger.debug(f"⚠️ LEGACY FACTS: Used {len(legacy_facts)} facts from memory string parsing (fallback)")
                
                # ENHANCEMENT: Add Discord preferred name detection
                if message_context.metadata:
                    discord_name = message_context.metadata.get('discord_author_name')
                    if discord_name:
                        preferred_name = self._extract_preferred_name_from_discord(discord_name)
                        if preferred_name and preferred_name != discord_name:
                            # Add as user fact if not already present
                            name_fact = f"[Preferred name: {preferred_name}]"
                            if name_fact not in user_facts:
                                user_facts.insert(0, name_fact)  # Put name first
                
                # Process OLDER conversation parts (beyond recent messages) - create REAL summaries
                if conversation_memory_parts:
                    for part in conversation_memory_parts:
                        if "[Fact:" in part:
                            user_facts.append(part)
                        else:
                            # Create actual summary, not just topic
                            summary = self._create_conversation_summary(part)
                            if summary:
                                older_conversation_summaries.append(summary)
                
                # Process RECENT conversation parts - add directly without summarization
                recent_conversation_summaries = []
                if recent_conversation_parts:
                    for part in recent_conversation_parts:
                        if "[Fact:" not in part:  # Don't duplicate facts
                            # Extract content without [Memory:] wrapper for cleaner context
                            clean_part = part.replace('[Memory:', '').replace('[Previous conversation:', '').replace(']', '').strip()
                            if len(clean_part) > 15:  # Skip very short content
                                recent_conversation_summaries.append(clean_part[:1500])  # Keep substantial context (Discord messages can be up to 2000 chars)
                
                # Build organized memory narrative
                if user_facts:
                    memory_parts.append("USER FACTS: " + "; ".join(user_facts))
                if recent_conversation_summaries:
                    # Recent conversations get priority - add them directly
                    unique_recent = list(dict.fromkeys(recent_conversation_summaries))[:10]  # Max 10 recent exchanges
                    memory_parts.append("RECENT CONVERSATIONS: " + "; ".join(unique_recent))
                if older_conversation_summaries:
                    # Deduplicate and limit summaries
                    unique_summaries = list(dict.fromkeys(older_conversation_summaries))[:5]  # Max 5 summaries
                    memory_parts.append("PAST CONVERSATION SUMMARIES: " + "; ".join(unique_summaries))
                
                if memory_parts:
                    memory_fragments.append(" ".join(memory_parts))
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added {len(user_facts)} facts + {len(recent_conversation_summaries)} recent + {len(older_conversation_summaries)} older summaries")
                else:
                    logger.error(f"🤖 LLM CONTEXT DEBUG: FAILED - No valid memory content found from {len(user_memories)} memories")
            else:
                logger.info(f"🤖 LLM CONTEXT DEBUG: No memories to process (memories: {relevant_memories is not None})")
        
        memory_narrative = " ".join(memory_fragments)
        logger.info(f"🤖 LLM CONTEXT DEBUG: Final memory narrative: '{memory_narrative[:200]}...'")
        
        # � CONVERSATION CACHE INTEGRATION: Restored sophisticated conversation history processing
        try:
            from src.utils.helpers import generate_conversation_summary
            
            # Get recent messages from conversation cache if available
            recent_messages = []
            if self.conversation_cache:
                try:
                    # Try to get recent messages from conversation cache
                    cache_key = f"recent_messages_{user_id}"
                    cached_messages = await self.conversation_cache.get(cache_key)
                    if cached_messages:
                        recent_messages = cached_messages
                        logger.info(f"🔥 CONVERSATION CACHE: Retrieved {len(recent_messages)} cached messages")
                except Exception as e:
                    logger.debug(f"Conversation cache retrieval failed: {e}")
            
            # Fallback to memory manager conversation history
            if not recent_messages:
                conversation_history = await self.memory_manager.get_conversation_history(
                    user_id=user_id, 
                    limit=15  # Get more messages for better context (matching previous implementation)
                )
                
                # Convert to expected format for generate_conversation_summary
                # 🚨 FIX: Include author_id so summary can filter user-specific messages
                recent_messages = []
                for msg in conversation_history:
                    if isinstance(msg, dict):
                        content = msg.get('content', '')
                        role = msg.get('role', 'user')
                        is_bot = role in ['assistant', 'bot']
                        
                        recent_messages.append({
                            'content': content,
                            'author_id': user_id if not is_bot else 'bot',  # 🚨 FIX: Add author_id for filtering
                            'role': role,
                            'bot': is_bot
                        })
                    else:
                        content = getattr(msg, 'content', '')
                        role = getattr(msg, 'role', 'user')
                        is_bot = role in ['assistant', 'bot']
                        
                        recent_messages.append({
                            'content': content,
                            'author_id': user_id if not is_bot else 'bot',  # 🚨 FIX: Add author_id for filtering
                            'role': role,
                            'bot': is_bot
                        })
                
                logger.info(f"🔥 FALLBACK: Using memory manager conversation history - {len(recent_messages)} messages")
                
                # 🚨 CRITICAL FIX: Ensure conversation context includes bot responses for continuity
                # If the most recent messages are all user messages, this breaks LLM context
                if recent_messages:
                    # Count recent user vs bot messages
                    # 🚨 FIX: Check 'role' field, not 'bot' field
                    recent_5 = recent_messages[-5:] if len(recent_messages) >= 5 else recent_messages
                    user_count = sum(1 for msg in recent_5 if msg.get('role', 'user') not in ['bot', 'assistant'])
                    bot_count = sum(1 for msg in recent_5 if msg.get('role', 'user') in ['bot', 'assistant'])
                    
                    logger.info(f"🔥 CONTINUITY CHECK: Recent 5 messages - User: {user_count}, Bot: {bot_count}")
                    
                    # If no bot messages in recent 5, expand search to include at least 1 bot response
                    if bot_count == 0 and len(recent_messages) > 5:
                        logger.warning(f"🔥 CONTINUITY FIX: No bot responses in recent 5 messages - expanding search")
                        # Look further back to find at least one bot response
                        for i in range(5, min(15, len(recent_messages))):
                            if recent_messages[-(i+1)].get('role', 'user') in ['bot', 'assistant']:
                                # Include this bot message for context
                                bot_msg = recent_messages[-(i+1)]
                                recent_messages = recent_messages[-5:] + [bot_msg]
                                logger.info(f"🔥 CONTINUITY FIX: Added bot response from position -{i+1} for context")
                                break
            
            # ALWAYS generate conversation summary - NO CONDITIONAL FALLBACKS
            conversation_summary = generate_conversation_summary(recent_messages, user_id)
            if conversation_summary and len(conversation_summary) > 600:
                conversation_summary = conversation_summary[:600] + "..."
            
            logger.info(f"📝 CONVERSATION SUMMARY: Generated summary ({len(conversation_summary)} chars)")
            
        except Exception as e:
            logger.warning(f"⚠️ Conversation cache integration failed: {e}")
            conversation_summary = ""
            recent_messages = []
        
        # 🚀 OPTIMIZED SYSTEM MESSAGE: Lean core prompt, memory/summary as bridge messages
        
        # Build lean system message - memory/summary moved to bridge position for better flow
        system_prompt_content = f"CURRENT DATE & TIME: {time_context}"
        
        # Log what will become bridge messages
        if memory_narrative:
            logger.info(f"📚 MEMORY: Will add memory narrative as bridge message ({len(memory_narrative)} chars)")
        
        if conversation_summary:
            logger.info(f"📝 SUMMARY: Will add conversation summary as bridge message ({len(conversation_summary)} chars)")
        
        # Add attachment guard if needed
        attachment_guard = ""
        if message_context.attachments and len(message_context.attachments) > 0:
            bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
            attachment_guard = (
                f" Image policy: respond only in-character ({bot_name}), never output analysis sections, "
                f"headings, scores, tables, coaching offers, or 'Would you like me to' prompts."
            )
        
        # Add guidance clause for natural conversation
        bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
        guidance_clause = (
            f" Communication style: Respond naturally and authentically as {bot_name} - "
            f"be warm, genuine, and conversational. No meta-analysis, breakdowns, bullet summaries, "
            f"or section headings. Stay in character and speak like a real person would."
        )
        
        # 🚨 FIX: Consolidate ALL system content at the beginning to maintain user/assistant alternation
        # Memory narrative and conversation summary will be added to initial system message
        # to prevent breaking alternation rules required by many LLM APIs
        
        core_system_parts = [system_prompt_content + attachment_guard + guidance_clause]
        
        # Add memory narrative to initial system message (not as separate message)
        if memory_narrative:
            core_system_parts.append(f"\n\nRELEVANT MEMORIES: {memory_narrative}")
            logger.debug(f"🔥 SYSTEM CONSOLIDATION: Added memory narrative ({len(memory_narrative)} chars) to initial system message")
        else:
            # Add no-memory warning to initial system message
            core_system_parts.append(
                "\n\n⚠️ MEMORY STATUS: No previous conversation history found. If asked about past conversations, "
                "politely say you don't have specific memories of those discussions yet. DO NOT invent or hallucinate conversation details."
            )
            logger.debug(f"🔥 SYSTEM CONSOLIDATION: Added NO MEMORY warning to initial system message")
        
        # Add conversation summary to initial system message (not as separate message)
        if conversation_summary:
            core_system_parts.append(f"\n\nCONVERSATION FLOW: {conversation_summary}")
            logger.debug(f"🔥 SYSTEM CONSOLIDATION: Added conversation summary ({len(conversation_summary)} chars) to initial system message")
        
        # Create consolidated system message
        consolidated_system = "".join(core_system_parts)
        conversation_context.append({"role": "system", "content": consolidated_system})
        
        # 🚀 SOPHISTICATED RECENT MESSAGE PROCESSING with OPTIMIZED ASSEMBLY ORDER
        try:
            if recent_messages:
                logger.info(f"🔥 CONTEXT DEBUG: Processing {len(recent_messages)} recent messages for conversation context")
                
                # OPTIMIZED: Split messages into OLDER (truncated) vs RECENT (detailed)
                recent_full_count = 6  # Reduced from 20 to 6 (last 3 exchanges) to prevent verbose pattern-matching
                older_messages = recent_messages[:-recent_full_count] if len(recent_messages) > recent_full_count else []
                recent_full_messages = recent_messages[-recent_full_count:] if len(recent_messages) > recent_full_count else recent_messages

                logger.info(f"🔥 CONTINUITY: Split into {len(older_messages)} older (500 chars) + {len(recent_full_messages)} recent (400 chars)")
                
                # Add older messages first (truncated for space)
                user_assistant_messages = []
                skip_next_bot_response = False
                
                for msg in older_messages:
                    msg_content = msg.get('content', '')
                    # 🚨 FIX: Check 'role' field, not 'bot' field - memory returns role='bot' or role='user'
                    role_value = msg.get('role', 'user')
                    is_bot_msg = role_value in ['bot', 'assistant']
                    
                    if msg_content.startswith("!"):
                        skip_next_bot_response = True
                        continue

                    if is_bot_msg and skip_next_bot_response:
                        skip_next_bot_response = False
                        continue

                    if not is_bot_msg:
                        skip_next_bot_response = False

                    # Truncate older messages to 500 chars
                    truncated_content = msg_content[:500] + "..." if len(msg_content) > 500 else msg_content
                    role = "assistant" if is_bot_msg else "user"
                    user_assistant_messages.append({"role": role, "content": truncated_content})
                    logger.debug(f"🔥 CONTEXT (OLDER): Added truncated [{role}]: '{truncated_content[:100]}...'")

                # Add older messages to context
                conversation_context.extend(user_assistant_messages)
                
                # 🚨 FIX: Memory narrative and conversation summary are now in initial system message
                # Do NOT add them here as that breaks user/assistant alternation
                # (Previously these were added as separate system messages mid-conversation)
                
                # Add recent messages (detailed)
                for idx, msg in enumerate(recent_full_messages):
                    msg_content = msg.get('content', '')
                    # 🚨 FIX: Check 'role' field, not 'bot' field - memory returns role='bot' or role='user'
                    role_value = msg.get('role', 'user')
                    is_bot_msg = role_value in ['bot', 'assistant']
                    
                    logger.info(f"🔥 CONTEXT DEBUG: Processing RECENT message - is_bot: {is_bot_msg}, content: '{msg_content[:100]}...'")
                    
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

                    # TIERED APPROACH: Most recent 3 messages (last exchange + current) get FULL content
                    # Older recent messages truncated to prevent verbose pattern-matching
                    is_most_recent = idx >= len(recent_full_messages) - 3
                    if is_most_recent:
                        # Last 3 messages: FULL content for rich immediate context
                        recent_content = msg_content
                        logger.info(f"🔥 CONTEXT (MOST RECENT): Full message [{idx}]")
                    else:
                        # Older recent messages: 400 chars to prevent verbose pattern-matching
                        recent_content = msg_content[:400] + "..." if len(msg_content) > 400 else msg_content
                        logger.info(f"🔥 CONTEXT (RECENT): Truncated message [{idx}] to 400 chars")
                    
                    role = "assistant" if is_bot_msg else "user"
                    conversation_context.append({"role": role, "content": recent_content})
                    logger.info(f"🔥 CONTEXT (RECENT): Added [{role}] ({len(recent_content)} chars): '{recent_content[:100]}...'")
                
                logger.info(f"✅ OPTIMIZED CONTEXT: Added {len(older_messages)} older (500 chars) + {len(recent_full_messages)} recent (tiered: 3 full + rest 400 chars) messages")
            else:
                logger.info("🔥 CONTEXT DEBUG: No recent messages available for context")
                
        except Exception as e:
            logger.warning(f"⚠️ Recent message processing failed: {e}")
        
        # Add current user message
        conversation_context.append({
            "role": "user", 
            "content": message_context.content
        })
        
        logger.info(f"🔥 CONTEXT DEBUG: Final conversation context has {len(conversation_context)} total messages")
        
        return conversation_context

    async def _build_conversation_context_structured(
        self, 
        message_context: MessageContext, 
        relevant_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        🚀 STRUCTURED CONVERSATION CONTEXT BUILDING (Phase 2)
        
        Build conversation context using PromptAssembler for structured, maintainable prompt generation.
        This replaces string concatenation with component-based assembly, enabling:
        - Token budget management
        - Priority-based ordering
        - Content deduplication
        - Model-specific formatting
        - Better debugging and testing
        
        Returns: List of messages in OpenAI chat format (role + content)
        """
        logger.info(f"🚀 STRUCTURED CONTEXT: Building for user {message_context.user_id}")
        
        # Initialize assembler with token budget (approximate - converted to chars in components)
        # Phase 2A: Upgraded to 16K tokens (~64K chars) for rich character personalities
        # Modern models support 128K-200K tokens - we're targeting ~18% utilization (24K total)
        # See: docs/architecture/TOKEN_BUDGET_ANALYSIS.md for rationale
        assembler = create_prompt_assembler(max_tokens=16000)
        
        # ================================
        # COMPONENT 1: Core System Prompt
        # ================================
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        
        core_system = f"CURRENT DATE & TIME: {time_context}"
        assembler.add_component(create_core_system_component(core_system, priority=1))
        
        # ================================
        # COMPONENT 2: Attachment Guard (if needed)
        # ================================
        if message_context.attachments and len(message_context.attachments) > 0:
            bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
            attachment_guard = (
                f"Image policy: respond only in-character ({bot_name}), never output analysis sections, "
                f"headings, scores, tables, coaching offers, or 'Would you like me to' prompts."
            )
            assembler.add_component(PromptComponent(
                type=PromptComponentType.ATTACHMENT_GUARD,
                content=attachment_guard,
                priority=2,
                required=True
            ))
        
        # ================================
        # COMPONENT 3: User Facts and Preferences
        # ================================
        user_facts_content = await self._build_user_facts_content(
            message_context.user_id, 
            message_context.content  # Pass message content for context-based filtering
        )
        if user_facts_content:
            assembler.add_component(create_user_facts_component(
                user_facts_content,
                priority=3
            ))
            logger.info(f"✅ STRUCTURED CONTEXT: Added user facts ({len(user_facts_content)} chars)")
        
        # ================================
        # COMPONENT 4: Memory Narrative (or anti-hallucination warning)
        # ================================
        memory_narrative = await self._build_memory_narrative_structured(
            message_context.user_id, 
            relevant_memories
        )
        
        if memory_narrative:
            assembler.add_component(create_memory_component(
                f"RELEVANT MEMORIES: {memory_narrative}",
                priority=5
            ))
            logger.info(f"✅ STRUCTURED CONTEXT: Added memory narrative ({len(memory_narrative)} chars)")
        else:
            assembler.add_component(create_anti_hallucination_component(priority=5))
            logger.info(f"⚠️ STRUCTURED CONTEXT: Added anti-hallucination warning (no memories)")
        
        # ================================
        # COMPONENT 5: Conversation Summary (if available)
        # ================================
        conversation_summary = await self._get_conversation_summary_structured(message_context.user_id)
        if conversation_summary:
            assembler.add_component(PromptComponent(
                type=PromptComponentType.CONVERSATION_FLOW,
                content=f"CONVERSATION FLOW: {conversation_summary}",
                priority=6,
                required=False  # Optional - can be dropped if over budget
            ))
            logger.info(f"✅ STRUCTURED CONTEXT: Added conversation summary ({len(conversation_summary)} chars)")
        
        # ================================
        # COMPONENT 6: Communication Style Guidance
        # ================================
        bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
        assembler.add_component(create_guidance_component(bot_name, priority=7))
        
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
    
    async def _build_memory_narrative_structured(
        self, 
        user_id: str, 
        relevant_memories: List[Dict[str, Any]]
    ) -> str:
        """Build memory narrative for structured context (extracted from original method)."""
        if not relevant_memories:
            return ""
        
        memory_parts = []
        user_facts = []
        conversation_memories = []
        
        # Separate facts from conversation memories
        for memory in relevant_memories[:10]:  # Limit to prevent token overflow
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            
            if metadata.get("type") == "user_fact":
                fact = metadata.get("fact", content)[:300]
                if fact:
                    user_facts.append(fact)
            elif content:
                # Conversation memory
                if "User:" in content and "Bot:" in content:
                    conversation_memories.append(f"{content[:500]}")
                else:
                    conversation_memories.append(f"{content[:500]}")
        
        # Build narrative with structure
        if user_facts:
            memory_parts.append(f"USER FACTS: {'; '.join(user_facts)}")
        
        if conversation_memories:
            memory_parts.append(f"PAST CONVERSATIONS: {' | '.join(conversation_memories[:5])}")
        
        return " || ".join(memory_parts) if memory_parts else ""
    
    async def _get_conversation_summary_structured(self, user_id: str) -> str:
        """Get conversation summary for structured context."""
        # Simplified: Conversation summary logic can be added later
        # For now, return empty string to keep Phase 2 focused on structure
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
                
                # Categorize facts by type
                if relationship_type in ['likes', 'loves', 'enjoys', 'prefers']:
                    preferences.append(f"{relationship_type} {entity_name}")
                elif relationship_type in ['works_at', 'studies_at', 'lives_in']:
                    background.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
                elif relationship_type in ['owns', 'has', 'knows']:
                    current_facts.append(f"{relationship_type} {entity_name}")
                else:
                    current_facts.append(f"{relationship_type.replace('_', ' ')} {entity_name}")
            
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
    
    async def _get_recent_messages_structured(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent conversation messages for structured context."""
        try:
            recent_messages = await self.memory_manager.get_conversation_history(
                user_id=user_id,
                limit=20
            )
            
            if not recent_messages:
                return []
            
            formatted_messages = []
            skip_next_bot_response = False
            
            # Split into older (truncated) vs recent (detailed)
            recent_full_count = 6
            older_messages = recent_messages[:-recent_full_count] if len(recent_messages) > recent_full_count else []
            recent_full_messages = recent_messages[-recent_full_count:] if len(recent_messages) > recent_full_count else recent_messages
            
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
                
                truncated = content[:500] + "..." if len(content) > 500 else content
                role = "assistant" if is_bot else "user"
                formatted_messages.append({"role": role, "content": truncated})
            
            # Process recent messages (tiered: last 3 full, others 400 chars)
            for idx, msg in enumerate(recent_full_messages):
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
                
                # Last 3 messages get full content
                is_most_recent = idx >= len(recent_full_messages) - 3
                if is_most_recent:
                    message_content = content
                else:
                    message_content = content[:400] + "..." if len(content) > 400 else content
                
                role = "assistant" if is_bot else "user"
                formatted_messages.append({"role": role, "content": message_content})
            
            return formatted_messages
            
        except Exception as e:
            logger.warning(f"Could not retrieve recent messages: {e}")
            return []

    async def _build_conversation_context_with_ai_intelligence(
        self, message_context: MessageContext, relevant_memories: List[Dict[str, Any]], ai_components: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Enhance conversation context with AI intelligence guidance.
        
        🚨 CRITICAL: This method ENHANCES the structured context from Phase 4,
        it does NOT rebuild from scratch. We accept the pre-built structured context
        and just add TrendWise adaptation and AI intelligence guidance to it.
        """
        # 🚨 CRITICAL FIX: Use structured context from Phase 4, don't rebuild!
        # The conversation_context is ALREADY built by _build_conversation_context_structured()
        # We just need to enhance it with AI intelligence additions
        conversation_context = await self._build_conversation_context_structured(message_context, relevant_memories)
        
        # TrendWise Adaptive Learning: Add confidence adaptation guidance
        if self.confidence_adapter:
            try:
                bot_name = get_normalized_bot_name_from_env()
                adaptation_params = await self.confidence_adapter.adjust_response_style(
                    user_id=message_context.user_id,
                    bot_name=bot_name
                )
                
                if adaptation_params:
                    # Generate adaptation guidance for system prompt
                    adaptation_guidance = self.confidence_adapter.generate_adaptation_guidance(
                        adaptation_params
                    )
                    
                    # Apply system prompt additions to existing system message
                    for i, msg in enumerate(conversation_context):
                        if msg.get("role") == "system":
                            if adaptation_guidance and hasattr(adaptation_guidance, 'system_prompt_additions'):
                                additional_guidance = " ".join(adaptation_guidance.system_prompt_additions)
                                conversation_context[i]["content"] += f" {additional_guidance}"
                            break
                    
                    # Store adaptation context for monitoring
                    ai_components['trendwise_adaptation'] = {
                        'response_style': adaptation_params.response_style.value,
                        'explanation_level': adaptation_params.explanation_level.value,
                        'detail_enhancement': adaptation_params.detail_enhancement,
                        'adaptation_reason': adaptation_params.adaptation_reason,
                        'parameters': adaptation_params
                    }
                    logger.info("📈 TRENDWISE: Applied confidence adaptation for %s (style: %s, reason: %s)",
                               message_context.user_id, adaptation_params.response_style.value, 
                               adaptation_params.adaptation_reason)
                
            except Exception as e:
                logger.warning("TrendWise adaptation failed: %s", e)
        
        # Add AI intelligence guidance to system messages
        ai_guidance = self._build_ai_intelligence_guidance(ai_components)
        if ai_guidance:
            # Insert AI guidance after the first system message but before user messages
            for i, msg in enumerate(conversation_context):
                if msg.get("role") == "system":
                    # Append AI guidance to existing system message
                    conversation_context[i]["content"] += ai_guidance
                    logger.info("🤖 AI INTELLIGENCE: Added sophisticated guidance to conversation context")
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
        
        # Context Switch Detection (Phase 3)
        context_switches = comprehensive_context.get('context_switches')
        if context_switches and isinstance(context_switches, dict):
            switch_type = context_switches.get('switch_type', 'none')
            confidence = context_switches.get('confidence', 0)
            if switch_type != 'none' and confidence > 0.6:
                guidance_parts.append(f"🔄 TOPIC TRANSITION: {switch_type} detected (confidence: {confidence:.2f}) - acknowledge the shift naturally")
        
        # Proactive Engagement Analysis (Phase 4.3)
        proactive_engagement_analysis = comprehensive_context.get('proactive_engagement_analysis')
        if proactive_engagement_analysis and isinstance(proactive_engagement_analysis, dict):
            intervention_needed = proactive_engagement_analysis.get('intervention_needed', False)
            engagement_strategy = proactive_engagement_analysis.get('recommended_strategy')
            if intervention_needed and engagement_strategy:
                guidance_parts.append(f"🎯 ENGAGEMENT: Use {engagement_strategy} strategy to enhance conversation quality")
        
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
            
            # Task 1.8: Memory Aging Intelligence (if enabled)
            memory_aging_task = self._analyze_memory_aging_intelligence(
                message_context.user_id,
                message_context
            )
            tasks.append(memory_aging_task)
            task_names.append("memory_aging_intelligence")
            
            # Task 1.9: Character Performance Intelligence
            character_performance_task = self._analyze_character_performance_intelligence(
                message_context.user_id,
                message_context,
                conversation_context
            )
            tasks.append(character_performance_task)
            task_names.append("character_performance_intelligence")
            
            # Task 2: Enhanced context analysis using hybrid detector
            context_task = self._analyze_enhanced_context(
                message_context.content,
                conversation_context,
                message_context.user_id
            )
            tasks.append(context_task)
            task_names.append("context_analysis")
            
            # Task 3: Dynamic personality profiling if available
            if self.bot_core and hasattr(self.bot_core, 'dynamic_personality_profiler'):
                personality_task = self._analyze_dynamic_personality(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(personality_task)
                task_names.append("personality_analysis")
            
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
                
            # Task 6: Thread management analysis (Advanced Thread Management)
            if self.bot_core and hasattr(self.bot_core, 'conversation_thread_manager'):
                thread_task = self._process_thread_management(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(thread_task)
                task_names.append("thread_management")
            
            # Task 6: Proactive engagement analysis (Phase 4.3)
            if self.bot_core and hasattr(self.bot_core, 'engagement_engine'):
                engagement_task = self._process_proactive_engagement(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(engagement_task)
                task_names.append("proactive_engagement")
            
            # Task 7: Human-like memory optimization
            if self.memory_manager and hasattr(self.memory_manager, 'human_like_optimizer'):
                memory_task = self._process_human_like_memory(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(memory_task)
                task_names.append("human_like_memory")
            
            # Task 8: Conversation analysis for enhanced guidance
            conversation_analysis_task = self._analyze_conversation_patterns(
                message_context.content,
                conversation_context,
                message_context.user_id
            )
            tasks.append(conversation_analysis_task)
            task_names.append("conversation_analysis")
            
            # Task 9: Context switch detection for conversation flow
            if self.bot_core and hasattr(self.bot_core, 'context_switch_detector'):
                context_switch_task = self._detect_context_switches(
                    message_context.content,
                    conversation_context,
                    message_context.user_id
                )
                tasks.append(context_switch_task)
                task_names.append("context_switches")
            
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
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Use the stable OLD Phase 3 + Phase 4 processing method
            # Note: NEW Phase 3 memory clustering has been obsoleted by PostgreSQL graph architecture
            logger.info("🔄 Using stable OLD Phase 3 + Phase 4 processing method")
            
            # Process Phase 3 components separately (like the old working system)
            conversation_context_switches = await self._analyze_context_switches(user_id, content, discord_message)
            empathy_response_calibration = await self._calibrate_empathy_response(user_id, content, discord_message)
            
            # Process with conversation intelligence sophistication
            conversation_context_result = await self.bot_core.phase2_integration.process_conversation_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=conversation_context,
                external_emotion_data=None,
                emotion_context=None
            )
            
            # Add Phase 3 results to the conversation intelligence context
            if isinstance(conversation_context_result, dict):
                conversation_context_result['conversation_context_switches'] = conversation_context_switches
                conversation_context_result['empathy_response_calibration'] = empathy_response_calibration
            
            logger.debug(f"Sophisticated conversation intelligence processing successful for user {user_id}")
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
            
            logger.info("🌟 Learning moment detection successful for %s (detected %d moments)", 
                       character_name, len(learning_moments))
            return result
            
        except Exception as e:
            logger.error("🌟 Learning moment detection failed: %s", str(e))
            return None

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

    async def _process_proactive_engagement(self, user_id: str, content: str, 
                                          message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process Proactive Conversation Engagement for natural topic suggestions."""
        logger.debug("🎯 STARTING PROACTIVE ENGAGEMENT ANALYSIS for user %s", user_id)
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'engagement_engine'):
                logger.debug("🎯 Engagement engine not available")
                return None
            
            engagement_engine = self.bot_core.engagement_engine
            
            # Get recent conversation history for analysis
            from datetime import datetime
            conversation_context = []
            if self.memory_manager:
                recent_memories = await self.memory_manager.get_conversation_history(
                    user_id=user_id,
                    limit=10
                )
                if recent_memories:
                    for memory in recent_memories:
                        if isinstance(memory, dict):
                            conversation_context.append({
                                'content': memory.get('content', ''),
                                'role': memory.get('role', 'user'),
                                'timestamp': memory.get('timestamp', datetime.now())
                            })
            
            # Add current message to context
            conversation_context.append({
                'content': content,
                'role': 'user',
                'timestamp': datetime.now()
            })
            
            # Get thread info if available
            current_thread_info = None
            if hasattr(self.bot_core, 'conversation_thread_manager'):
                # Get thread info from thread manager if needed
                pass  # Thread manager integration optional
            
            # Analyze conversation engagement
            engagement_analysis = await engagement_engine.analyze_conversation_engagement(
                user_id=user_id,
                context_id=f"discord_{user_id}",
                recent_messages=conversation_context,
                current_thread_info=current_thread_info
            )
            
            # Extract key data for prompt integration
            result = {
                'intervention_needed': engagement_analysis.get('intervention_needed', False),
                'recommended_strategy': engagement_analysis.get('recommended_strategy'),
                'flow_state': engagement_analysis.get('flow_analysis', {}).get('current_state'),
                'stagnation_risk': engagement_analysis.get('stagnation_analysis', {}).get('risk_level'),
                'recommendations': engagement_analysis.get('recommendations', [])
            }
            
            if result['intervention_needed']:
                logger.info("🎯 PROACTIVE ENGAGEMENT: Intervention recommended - Strategy: %s, Risk: %s",
                          result['recommended_strategy'], result['stagnation_risk'])
            else:
                logger.debug("🎯 PROACTIVE ENGAGEMENT: No intervention needed - Flow state: %s",
                           result['flow_state'])
            
            return result
            
        except Exception as e:
            logger.error("🎯 Proactive engagement analysis failed: %s", e)
            return None

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

    async def _analyze_conversation_patterns(self, content: str, conversation_context: List[Dict[str, str]], 
                                           user_id: str) -> Dict[str, Any]:
        """Analyze conversation patterns for enhanced response guidance."""
        try:
            # Analyze conversation patterns and provide guidance
            analysis = {
                'mode': 'standard',
                'interaction_type': 'general',
                'personality_type': 'default',
                'relationship_level': 'acquaintance',
                'response_guidance': 'Respond naturally and authentically'
            }
            
            # Detect conversation patterns
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['how are you', 'how have you been', 'whats up']):
                analysis['interaction_type'] = 'greeting'
                analysis['response_guidance'] = 'Respond warmly to greeting'
            elif any(word in content_lower for word in ['help', 'assist', 'support']):
                analysis['interaction_type'] = 'assistance_request'
                analysis['response_guidance'] = 'Provide helpful guidance'
            elif any(word in content_lower for word in ['tell me about', 'explain', 'what is']):
                analysis['interaction_type'] = 'information_seeking'
                analysis['response_guidance'] = 'Provide informative explanation'
            
            logger.debug(f"Conversation pattern analysis successful for user {user_id}")
            return analysis
            
        except Exception as e:
            logger.debug(f"Conversation pattern analysis failed: {e}")
            return {
                'mode': 'standard',
                'interaction_type': 'general',
                'personality_type': 'default',
                'relationship_level': 'acquaintance',
                'response_guidance': 'Respond naturally and authentically'
            }

    async def _detect_context_switches(self, content: str, conversation_context: List[Dict[str, str]], 
                                     user_id: str) -> Optional[Dict[str, Any]]:
        """Detect context switches for conversation flow management."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'context_switch_detector'):
                return None
            
            # Detect context switches
            context_switches = await self.bot_core.context_switch_detector.detect_context_switches(
                user_id=user_id,
                new_message=content
            )
            
            logger.debug(f"Context switch detection successful for user {user_id}")
            return context_switches
            
        except Exception as e:
            logger.debug(f"Context switch detection failed: {e}")
            return None

    async def _process_attachments(self, message_context: MessageContext, 
                                 conversation_context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process message attachments (images, etc.)."""
        if not self.image_processor or not message_context.attachments:
            return conversation_context
        
        try:
            # Process images and add to context using existing image processing logic
            logger.debug("Processing %d attachments", len(message_context.attachments))
            
            # Use existing image processing from utils.helpers
            from src.utils.helpers import process_message_with_images
            
            # Convert MessageContext attachments to Discord format using adapter
            discord_attachments = create_discord_attachment_adapters(message_context.attachments)
            
            # Process images with existing logic
            enhanced_context = await process_message_with_images(
                message_context.content,
                discord_attachments,
                conversation_context,
                self.llm_client,
                self.image_processor
            )
            
            return enhanced_context
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Attachment processing failed: %s", str(e))
        
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
        Analyze character performance and identify optimization opportunities.
        
        Character Performance Intelligence:
        - Analyzes character effectiveness across adaptive learning metrics
        - Identifies CDL parameter optimization opportunities
        - Correlates personality traits with conversation success
        - Provides data-driven character adaptation insights
        
        Args:
            user_id: User identifier for performance analysis
            message_context: Context for character-specific analysis
            conversation_context: Recent conversation history for effectiveness analysis
            
        Returns:
            Dict with character performance analysis and optimization opportunities
        """
        try:
            # Import character performance components
            from src.characters.performance_analyzer import CharacterPerformanceAnalyzer
            from src.characters.cdl_optimizer import create_cdl_parameter_optimizer
            
            # Get bot name for character-specific analysis
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # Initialize performance analyzer with all available adaptive learning components
            performance_analyzer = CharacterPerformanceAnalyzer(
                trend_analyzer=self.trend_analyzer,
                memory_effectiveness_analyzer=getattr(self, 'memory_effectiveness_analyzer', None),
                relationship_evolution_engine=getattr(self, 'relationship_engine', None),
                cdl_parser=None,  # Not needed for runtime analysis
                cdl_database_manager=getattr(self, 'cdl_database_manager', None),
                postgres_pool=getattr(self.bot_core, 'postgres_pool', None) if self.bot_core else None
            )
            
            # Analyze character effectiveness across adaptive learning metrics
            effectiveness_analysis = await performance_analyzer.analyze_character_effectiveness(
                bot_name=bot_name,
                days_back=14,
                user_id=user_id  # Optional parameter for user-specific analysis
            )
            
            # Identify optimization opportunities
            optimization_opportunities = await performance_analyzer.identify_optimization_opportunities(
                bot_name=bot_name
            )
            
            # Correlate personality traits with conversation outcomes
            trait_correlations = await performance_analyzer.correlate_personality_traits_with_outcomes(
                bot_name=bot_name
            )
            
            if effectiveness_analysis:
                # Calculate overall character performance score from CharacterEffectivenessData
                overall_score = effectiveness_analysis.overall_effectiveness
                
                # Determine character performance status
                if overall_score >= 0.8:
                    performance_status = "excellent"
                elif overall_score >= 0.6:
                    performance_status = "good"
                elif overall_score >= 0.4:
                    performance_status = "fair"
                else:
                    performance_status = "needs_improvement"
                
                # Convert CharacterEffectivenessData to JSON-serializable dict
                effectiveness_dict = {
                    'bot_name': effectiveness_analysis.bot_name,
                    'analysis_period_days': effectiveness_analysis.analysis_period_days,
                    'overall_effectiveness': effectiveness_analysis.overall_effectiveness,
                    'conversation_quality_avg': effectiveness_analysis.conversation_quality_avg,
                    'confidence_trend_direction': effectiveness_analysis.confidence_trend_direction,
                    'memory_effectiveness_score': effectiveness_analysis.memory_effectiveness_score,
                    'relationship_progression_rate': effectiveness_analysis.relationship_progression_rate,
                    'trust_building_success': effectiveness_analysis.trust_building_success,
                    'user_engagement_level': effectiveness_analysis.user_engagement_level,
                    'data_points': effectiveness_analysis.data_points,
                    'statistical_confidence': effectiveness_analysis.statistical_confidence,
                    'analysis_timestamp': effectiveness_analysis.analysis_timestamp.isoformat() if effectiveness_analysis.analysis_timestamp else None
                } if effectiveness_analysis else {}
                
                # Convert OptimizationOpportunity objects to JSON-serializable dicts
                opportunities_dict = []
                if optimization_opportunities:
                    for opp in optimization_opportunities:
                        opportunities_dict.append({
                            'category': opp.category.value if hasattr(opp.category, 'value') else str(opp.category),
                            'confidence_score': opp.confidence_score,
                            'impact_potential': opp.impact_potential,
                            'current_performance': opp.current_performance,
                            'target_performance': opp.target_performance,
                            'affected_traits': opp.affected_traits,
                            'evidence_metrics': opp.evidence_metrics,
                            'recommendation': opp.recommendation,
                            'priority': opp.priority
                        })
                
                character_performance_data = {
                    'performance_status': performance_status,
                    'overall_score': round(overall_score, 3),
                    'effectiveness_analysis': effectiveness_dict,
                    'optimization_opportunities': opportunities_dict,
                    'trait_correlations': trait_correlations or {},
                    'bot_name': bot_name,
                    'analysis_period_days': 14,
                    'analysis_method': 'character_performance_intelligence'
                }
                
                logger.debug(
                    "Character performance analysis: %s performance (%.3f overall score, %d opportunities)",
                    character_performance_data['performance_status'],
                    character_performance_data['overall_score'],
                    len(character_performance_data['optimization_opportunities'])
                )
                return character_performance_data
                
        except Exception as e:
            logger.debug("Character performance intelligence analysis failed: %s", str(e))
        
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
                
                recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id=message_context.user_id,
                    query=bot_memory_query,
                    limit=10
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
            
            # Analyze personality
            personality_data = await profiler.analyze_personality(
                user_id=user_id,
                content=content,
                message=discord_message,
                recent_messages=[]
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
            # Apply CDL character enhancement
            enhanced_context = await self._apply_cdl_character_enhancement(
                message_context.user_id, conversation_context, message_context, ai_components
            )
            
            # 🎭 CRITICAL FIX: Use enhanced context if CDL enhancement succeeded, otherwise use original
            # The emotion enhancement is already included in CDL enhancement, so no need for separate step
            final_context = enhanced_context if enhanced_context else conversation_context
            
            # � TOKEN BUDGET ENFORCEMENT: Prevent oversized context from walls of text
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
            
            # Generate response using LLM
            logger.info("🎯 GENERATING: Sending %d messages (~%d tokens) to LLM", 
                       len(final_context), count_context_tokens(final_context))
            
            from src.llm.llm_client import LLMClient
            llm_client = LLMClient()
            
            response = await asyncio.to_thread(
                llm_client.get_chat_response, final_context
            )
            
            logger.info("✅ GENERATED: Response with %d characters", len(response))
            
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
            logger.error("Response generation failed: %s", str(e))
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    async def _apply_cdl_character_enhancement(self, user_id: str, conversation_context: List[Dict[str, str]], 
                                             message_context: MessageContext, ai_components: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """
        🎭 SOPHISTICATED CDL CHARACTER INTEGRATION 🎭
        
        Apply sophisticated CDL character enhancement to conversation context with full AI pipeline integration.
        Restored from original events.py implementation with complete VectorAIPipelineResult creation.
        
        This injects character-aware prompts that combine:
        - CDL character personality, backstory, and voice
        - AI pipeline emotional analysis and memory networks  
        - Real-time conversation context and relationship dynamics
        - Context analysis insights from sophisticated AI processing
        - Phase 4 comprehensive context and human-like intelligence
        """
        try:
            import os
            logger.info("🎭 CDL CHARACTER DEBUG: Starting sophisticated enhancement for user %s", user_id)
            
            # Use database-only character loading (character_file parameter is legacy compatibility)
            bot_name = os.getenv("DISCORD_BOT_NAME", "Unknown")
            logger.info("🎭 CDL CHARACTER: Using database-only character loading for %s bot, user %s", 
                       bot_name, user_id)
            
            logger.info("🎭 CDL CHARACTER: User %s using database character for bot: %s", user_id, bot_name)
            
            # Import CDL integration modules
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineResult
            from datetime import datetime
            
            # 🚀 SOPHISTICATED PIPELINE RESULT CREATION: Map ALL AI components to VectorAIPipelineResult
            pipeline_result = VectorAIPipelineResult(
                user_id=user_id,
                message_content=message_context.content,
                timestamp=datetime.now(),
                # Map emotion data to emotional_state - keep as dict for processing, convert to str only if needed
                emotional_state=ai_components.get('external_emotion_data') or ai_components.get('emotion_data'),
                mood_assessment=ai_components.get('external_emotion_data') if isinstance(ai_components.get('external_emotion_data'), dict) else None,
                # Map personality data 
                personality_profile=ai_components.get('personality_context') if isinstance(ai_components.get('personality_context'), dict) else None,
                # Map conversation intelligence data
                enhanced_context=ai_components.get('conversation_intelligence') if isinstance(ai_components.get('conversation_intelligence'), dict) else None
            )
            
            # 🎭 CRITICAL FIX: Add emotion_analysis mapping for CDL integration  
            # The CDL system looks for 'emotion_analysis' in pipeline_dict, but we store under 'emotion_data'
            emotion_data = ai_components.get('emotion_data')
            logger.debug(f"🎭 DEBUG: emotion_data type: {type(emotion_data)}, content: {emotion_data}")
            if emotion_data and isinstance(emotion_data, dict):
                # Add emotion_analysis as direct attribute to pipeline result for CDL integration
                setattr(pipeline_result, 'emotion_analysis', emotion_data)
                logger.info("🎭 EMOTION FIX: Added emotion_analysis attribute to pipeline for CDL integration")
            else:
                logger.warning(f"🎭 EMOTION WARNING: emotion_data is not a dict - type: {type(emotion_data)}, value: {emotion_data}")
            
            # 🎯 SOPHISTICATED CONTEXT ANALYSIS INTEGRATION: Add context analysis insights to pipeline result
            context_analysis = ai_components.get('context_analysis')
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
                    
                    logger.info("🎯 CDL: Enhanced pipeline with context analysis insights")
                except Exception as e:
                    logger.debug(f"Failed to add context analysis to pipeline: {e}")
            
            # 🎯 COMPREHENSIVE CONTEXT ASSEMBLY: Consolidate ALL AI intelligence for CDL integration
            # This must happen BEFORE comprehensive context is copied to pipeline!
            
            # Get or create comprehensive_context in ai_components
            if 'comprehensive_context' not in ai_components:
                ai_components['comprehensive_context'] = {}
            
            # Add adaptive learning data (relationship state, confidence)
            relationship_data = ai_components.get('relationship_state')
            confidence_data = ai_components.get('conversation_confidence')
            
            if relationship_data:
                ai_components['comprehensive_context']['relationship_state'] = relationship_data
                logger.info("🎯 RELATIONSHIP: Added relationship data to comprehensive_context for prompt injection")
            
            if confidence_data:
                ai_components['comprehensive_context']['conversation_confidence'] = confidence_data
                logger.info("🎯 CONFIDENCE: Added confidence data to comprehensive_context for prompt injection")
            
            # 🧠 UNIFIED CHARACTER INTELLIGENCE: Add coordinated intelligence from all systems
            unified_intelligence = ai_components.get('unified_character_intelligence')
            if unified_intelligence and isinstance(unified_intelligence, dict):
                ai_components['comprehensive_context']['unified_character_intelligence'] = unified_intelligence
                logger.info("🧠 UNIFIED: Added unified character intelligence to comprehensive_context for prompt injection")
                
                # Log what intelligence systems contributed
                system_contributions = unified_intelligence.get('system_contributions', {})
                if system_contributions:
                    contributing_systems = list(system_contributions.keys())
                    logger.info(f"🧠 UNIFIED: Contributing systems: {', '.join(contributing_systems)}")
                    
                    # Specifically log memory_boost if present (this is the semantic search results)
                    memory_boost = system_contributions.get('memory_boost')
                    if memory_boost and isinstance(memory_boost, dict):
                        memory_count = memory_boost.get('memory_count', 0)
                        logger.info(f"🧠 MEMORY BOOST: {memory_count} relevant memories available for prompt injection")
            
            # 🚀 COMPREHENSIVE CONTEXT INTEGRATION: Add all AI components to pipeline
            comprehensive_context = ai_components.get('comprehensive_context')
            if comprehensive_context and isinstance(comprehensive_context, dict):
                # Merge comprehensive context into pipeline enhanced_context
                if isinstance(pipeline_result.enhanced_context, dict):
                    pipeline_result.enhanced_context.update(comprehensive_context)
                else:
                    pipeline_result.enhanced_context = comprehensive_context.copy()
                
                logger.info("🎯 CDL: Enhanced pipeline with comprehensive context from sophisticated AI processing (includes adaptive learning features)")
            
            # Use centralized character system if available, otherwise create new instance
            if self.bot_core and hasattr(self.bot_core, 'character_system'):
                cdl_integration = self.bot_core.character_system
                logger.info("🎭 CDL: Using centralized character system for %s", user_id)
            else:
                # Fallback: Create CDL integration instance with knowledge_router if available
                knowledge_router = getattr(self.bot_core, 'knowledge_router', None) if self.bot_core else None
                cdl_integration = CDLAIPromptIntegration(
                    vector_memory_manager=self.memory_manager,
                    llm_client=self.llm_client,
                    knowledge_router=knowledge_router,
                    bot_core=self.bot_core  # Pass bot_core for personality profiler access
                )
                logger.warning("⚠️ CDL: Using fallback CDL instance for %s - character system not initialized", user_id)
            
            # Get user's display name for better identification
            user_display_name = message_context.metadata.get('discord_author_name') if message_context.metadata else None
            
            # 🚀 FULL INTELLIGENCE: Use complete character-aware prompt with all emotional intelligence
            print(f"🚀 ABOUT TO CALL create_unified_character_prompt for user {user_id}", flush=True)
            character_prompt = await cdl_integration.create_unified_character_prompt(
                user_id=user_id,
                message_content=message_context.content,
                pipeline_result=pipeline_result,
                user_name=user_display_name
                # character_file parameter removed - using database-only approach
            )
            print(f"✅ RETURNED FROM create_unified_character_prompt - prompt length: {len(character_prompt)}", flush=True)
            
            # 🎯 WORKFLOW INTEGRATION: Inject workflow transaction context into character prompt
            workflow_prompt_injection = message_context.metadata.get('workflow_prompt_injection') if message_context.metadata else None
            if workflow_prompt_injection:
                character_prompt += f"\n\n🎯 ACTIVE TRANSACTION CONTEXT:\n{workflow_prompt_injection}"
                logger.info("🎯 WORKFLOW: Injected transaction context into character prompt (%d chars)", len(workflow_prompt_injection))
            
            # � DISABLED: VECTOR-NATIVE ENHANCEMENT (replaced by structured prompt assembly)
            # The vector_native_prompt_manager had hardcoded stub implementations that added
            # generic topics like "dreams, creativity, existence" to ALL characters.
            # Structured prompt assembly (Phase 4) already handles context properly.
            # 
            # LEGACY CODE (removed):
            # - Used vector_native_prompt_manager.create_contextualized_prompt()
            # - Added hardcoded topics, patterns, emotional states
            # - Caused all characters to mention "dreams, creativity, existence"
            #
            # NEW APPROACH: Character prompt from CDL is already complete and accurate
            # No additional "enhancement" needed - structured prompts handle everything
            logger.debug("🎯 VECTOR-NATIVE: Skipped legacy enhancement (using structured prompts from Phase 4)")
            
            # Clone the conversation context and replace/enhance system message
            enhanced_context = conversation_context.copy()
            
            # 🚨 CRITICAL FIX: Replace ONLY the first system message with character prompt
            # but PRESERVE any additional system messages (RELEVANT MEMORIES, CONVERSATION FLOW)
            system_message_found = False
            for i, msg in enumerate(enhanced_context):
                if msg.get('role') == 'system':
                    enhanced_context[i] = {
                        'role': 'system',
                        'content': character_prompt
                    }
                    system_message_found = True
                    logger.info("🎭 CDL CHARACTER: Replaced FIRST system message with character prompt (%d chars)", len(character_prompt))
                    # 🚨 CRITICAL: Don't break here! Let other system messages (memories, conversation flow) remain
                    break
            
            # If no system message found, add character prompt as first message
            if not system_message_found:
                enhanced_context.insert(0, {
                    'role': 'system', 
                    'content': character_prompt
                })
                logger.info("🎭 CDL CHARACTER: Added character prompt as new system message (%d chars)", len(character_prompt))
            
            # 🚨 DEBUG: Log what system messages we have in final enhanced context
            system_msg_count = sum(1 for msg in enhanced_context if msg.get('role') == 'system')
            logger.info("🎭 CDL CHARACTER: Final enhanced context has %d system messages and %d total messages", 
                       system_msg_count, len(enhanced_context))
            
            logger.info("🎭 CDL CHARACTER: Enhanced conversation context with database-only character for %s", bot_name)
            return enhanced_context
            
        except Exception as e:
            logger.error("🎭 CDL CHARACTER ERROR: Failed to apply character enhancement: %s", e)
            logger.error("🎭 CDL CHARACTER ERROR: Falling back to original conversation context")
            return None

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
            response = self._detect_and_fix_recursive_patterns(response, message_context)
            
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

    def _detect_and_fix_recursive_patterns(self, response: str, message_context: MessageContext) -> str:
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
                        return self._generate_fallback_response(message_context, "recursive_pattern")
            
            # Pattern-based detection (regardless of length)
            for pattern in recursive_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    logger.error("🚨 RECURSIVE PATTERN DETECTED: %s pattern found in %s response", 
                               pattern, bot_name)
                    logger.error("🚨 PATTERN CONTEXT: ...%s...", response[max(0, match.start()-50):match.end()+50])
                    return self._generate_fallback_response(message_context, "recursive_pattern")
            
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
                        return self._generate_fallback_response(message_context, "repetition_pattern")
            
            return response
            
        except Exception as e:
            logger.error("🚨 RECURSIVE PATTERN DETECTION FAILED: %s", e)
            return response  # Return original if detection fails

    def _generate_fallback_response(self, message_context: MessageContext, failure_type: str) -> str:
        """Generate a safe fallback response when recursive patterns are detected."""
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        
        bot_name = get_normalized_bot_name_from_env()
        user_name = getattr(message_context, 'user_display_name', 'there')
        
        # Generic fallback response - character personality will be applied by CDL system
        fallback = f"I apologize {user_name}, I need to gather my thoughts for a moment. What can I help you with?"
        
        logger.warning("🛡️ FALLBACK RESPONSE: Generated safe response for %s due to %s", bot_name, failure_type)
        return fallback

    async def _extract_and_store_knowledge(self, message_context: MessageContext, 
                                          ai_components: Dict[str, Any],
                                          extract_from: str = 'user') -> bool:
        """
        Extract factual knowledge from message using LLM analysis and store in PostgreSQL.
        
        Uses natural language understanding instead of regex patterns for 10x better quality.
        Runs asynchronously in background - no user-facing latency impact.
        
        Args:
            message_context: The message context
            ai_components: AI processing results including emotion data
            extract_from: 'user' to extract facts about user, 'bot' to extract facts about bot character
            
        Returns:
            True if knowledge was extracted and stored
        """
        # Check if knowledge router is available
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            return False
        
        # CRITICAL: Only extract from USER messages when extract_from='user'
        # This prevents extracting philosophical statements from bot as user facts
        # Check metadata for bot flag (set by platform adapters)
        if extract_from == 'user' and message_context.metadata and message_context.metadata.get('is_bot_message', False):
            logger.debug("Skipping user fact extraction - message is from bot")
            return False
        
        try:
            # Build LLM fact extraction prompt based on extraction target
            if extract_from == 'user':
                extraction_prompt = f"""Analyze this user message and extract ONLY clear, factual personal statements about the user.

User message: "{message_context.content}"

Instructions:
- Extract personal preferences: Foods/drinks/hobbies they explicitly like/dislike/enjoy
- Extract personal facts: Pets they own, places they've visited, hobbies they actively do
- DO NOT extract: Conversational phrases, questions, abstract concepts, philosophical statements, compliments
- DO NOT extract: Things the user asks about or discusses theoretically - only facts about themselves

Return JSON (return empty list if no clear facts found):
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food",
            "relationship_type": "likes",
            "confidence": 0.9,
            "reasoning": "User explicitly stated they love pizza"
        }}
    ]
}}

Valid entity_types: food, drink, hobby, place, pet, skill, goal, occupation, other
Valid relationship_types: 
- Preferences: likes, dislikes, enjoys, loves, hates, prefers
- Possessions: owns, has, bought, sold, lost
- Actions: visited, traveled_to, went_to, does, practices, plays
- Aspirations: wants, needs, plans_to, hopes_to, dreams_of
- Experiences: tried, learned, studied, worked_at, lived_in
- Relationships: knows, friends_with, family_of, works_with

Be conservative - only extract clear, unambiguous facts."""
            
            elif extract_from == 'bot':
                bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant')
                extraction_prompt = f"""Analyze this bot response and extract ONLY clear, factual personal statements the bot character made about ITSELF.

Bot response: "{message_context.content}"

Instructions:
- Extract bot's own preferences: Foods/drinks/hobbies the bot explicitly states it likes/dislikes/enjoys
- Extract bot's personal facts: Things the bot owns, places it has been, hobbies it does
- DO NOT extract: Conversational phrases, responses to questions, advice given to user
- DO NOT extract: Things about the USER - only facts about the BOT CHARACTER ({bot_name})

Return JSON (return empty list if no clear facts found):
{{
    "facts": [
        {{
            "entity_name": "collaborative discussions",
            "entity_type": "communication_style",
            "relationship_type": "prefers",
            "confidence": 0.9,
            "reasoning": "Bot stated 'I prefer collaborative discussions'"
        }}
    ]
}}

Valid entity_types: communication_style, value, hobby, interest, preference, skill, knowledge_area, other
Valid relationship_types: 
- Preferences: prefers, likes, enjoys, values, believes, prioritizes
- Abilities: excels_at, struggles_with, knows_about, specializes_in
- Characteristics: is_good_at, tends_to, always, never

Be conservative - only extract clear statements about the bot's own characteristics."""
            
            else:
                logger.warning(f"Invalid extract_from parameter: {extract_from}")
                return False

            # Get fact extraction model (fallback to chat model if not specified)
            fact_model = os.getenv('LLM_FACT_EXTRACTION_MODEL', '').strip()
            if not fact_model:
                fact_model = os.getenv('LLM_CHAT_MODEL', 'anthropic/claude-3.5-sonnet')
            
            # Call LLM for fact extraction (reuse existing client)
            # Use simple context format for extraction task
            extraction_context = [
                {
                    "role": "system", 
                    "content": "You are a precise fact extraction specialist. Only extract clear, verifiable personal facts. Return valid JSON only."
                },
                {
                    "role": "user", 
                    "content": extraction_prompt
                }
            ]
            
            # CRITICAL: Use lower temperature for fact extraction (consistency over creativity)
            # Fact extraction requires deterministic, consistent results - not creative responses
            fact_extraction_temperature = float(os.getenv('LLM_FACT_EXTRACTION_TEMPERATURE', '0.2'))
            
            # Run LLM call in thread to avoid blocking
            # Pass model override and temperature for fact extraction
            response = await asyncio.to_thread(
                self.llm_client.get_chat_response,
                extraction_context,
                model=fact_model,
                temperature=fact_extraction_temperature
            )
            
            # Parse LLM response
            try:
                # Handle markdown code blocks if present
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0].strip()
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0].strip()
                
                facts_data = json.loads(response)
                facts = facts_data.get("facts", [])
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ LLM FACT EXTRACTION: Failed to parse JSON response: {e}")
                logger.debug(f"Raw LLM response: {response[:200]}")
                return False
            
            if not facts:
                logger.debug(f"✅ LLM FACT EXTRACTION: No facts found in message (clean result)")
                return False
            
            # Store extracted facts
            bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant').lower()
            emotion_data = ai_components.get('emotion_data', {})
            emotional_context = emotion_data.get('primary_emotion', 'neutral') if emotion_data else 'neutral'
            
            stored_count = 0
            for fact in facts:
                # Validate fact structure
                required_fields = ['entity_name', 'entity_type', 'relationship_type', 'confidence']
                if not all(k in fact for k in required_fields):
                    logger.warning(f"⚠️ LLM FACT EXTRACTION: Invalid fact structure (missing fields): {fact}")
                    continue
                
                # Store in PostgreSQL
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
                    reasoning = fact.get('reasoning', 'N/A')
                    logger.info(
                        f"✅ LLM FACT EXTRACTION: Stored '{fact['entity_name']}' "
                        f"({fact['entity_type']}, {fact['relationship_type']}) - {reasoning}"
                    )
            
            if stored_count > 0:
                target_description = "user" if extract_from == 'user' else "bot character"
                logger.info(f"✅ LLM FACT EXTRACTION: Stored {stored_count}/{len(facts)} facts for {target_description} (ID: {message_context.user_id})")
            
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"❌ LLM fact extraction failed: {e}", exc_info=True)
            return False
    
    # NOTE: Bot self-fact extraction method removed - redundant with Character Episodic Intelligence
    # Character episodic memories are extracted from vector conversations with RoBERTa emotion scoring
    # See: src/characters/learning/character_vector_episodic_intelligence.py
    # Bot learns behavioral patterns, not isolated facts
    
    async def _extract_and_store_knowledge_regex_legacy(self, message_context: MessageContext, 
                                          ai_components: Dict[str, Any]) -> bool:
        """
        LEGACY: Regex-based fact extraction (replaced by LLM extraction).
        Kept for reference only - not called in production.
        """
        # Check if knowledge router is available
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            return False
        
        try:
            content = message_context.content.lower()
            
            # Simple pattern-based factual detection for Phase 3
            # This will be enhanced with semantic analysis in future iterations
            factual_patterns = {
                # Food preferences
                'food_preference': [
                    ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
                    ('favorite', 'likes'), ('prefer', 'likes'),
                    ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
                ],
                # Drink preferences  
                'drink_preference': [
                    ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
                    ('favorite', 'likes'), ('prefer', 'likes'),
                    ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
                ],
                # Hobbies
                'hobby_preference': [
                    ('love', 'enjoys'), ('like', 'enjoys'), ('enjoy', 'enjoys'),
                    ('hobby', 'enjoys'), ('do for fun', 'enjoys')
                ],
                # Places visited
                'place_visited': [
                    ('visited', 'visited'), ('been to', 'visited'), ('went to', 'visited'),
                    ('traveled to', 'visited')
                ]
            }
            
            # Entity type keywords for classification
            entity_keywords = {
                'food': ['pizza', 'pasta', 'sushi', 'burger', 'taco', 'food', 'meal', 'dish', 'eat', 'eating'],
                'drink': ['beer', 'wine', 'coffee', 'tea', 'water', 'soda', 'juice', 'drink'],
                'hobby': ['hiking', 'reading', 'gaming', 'cooking', 'photography', 'music', 'hobby'],
                'place': ['city', 'country', 'beach', 'mountain', 'park', 'place', 'location']
            }
            
            detected_facts = []
            
            # Detect factual statements
            for event_type, patterns in factual_patterns.items():
                for pattern, relationship in patterns:
                    if pattern in content:
                        # Determine entity type based on keywords
                        entity_type = 'other'
                        for etype, keywords in entity_keywords.items():
                            if any(kw in content for kw in keywords):
                                entity_type = etype
                                break
                        
                        # Extract entity names (now returns list to handle "pizza and sushi")
                        entity_names = self._extract_entity_from_content(content, pattern, entity_type)
                        
                        if entity_names:
                            # Create a fact for each entity
                            for entity_name in entity_names:
                                detected_facts.append({
                                    'entity_name': entity_name,
                                    'entity_type': entity_type,
                                    'relationship_type': relationship,
                                    'confidence': 0.8,
                                    'event_type': event_type
                                })
            
            # Store detected facts in PostgreSQL
            if detected_facts:
                bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant').lower()
                emotion_data = ai_components.get('emotion_data', {})
                emotional_context = emotion_data.get('primary_emotion', 'neutral') if emotion_data else 'neutral'
                
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
                        logger.info(f"✅ KNOWLEDGE: Stored fact '{fact['entity_name']}' ({fact['entity_type']}) "
                                  f"for user {message_context.user_id}")
                
                return len(detected_facts) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Knowledge extraction failed: {e}")
            return False
    
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
            
            # �🛡️ FINAL SAFETY CHECK: Don't store obviously broken responses
            if self._is_response_safe_to_store(clean_response):
                # Extract bot emotion from ai_components (Phase 7.5)
                bot_emotion = ai_components.get('bot_emotion')
                
                # Build metadata for bot response including bot emotion
                bot_metadata = {}
                if bot_emotion:
                    bot_metadata['bot_emotion'] = bot_emotion
                    logger.info(
                        "🎭 BOT EMOTION: Storing bot emotion '%s' (intensity: %.2f, confidence: %.2f)",
                        bot_emotion.get('primary_emotion', 'unknown'),
                        bot_emotion.get('intensity', 0.0),
                        bot_emotion.get('confidence', 0.0)
                    )
                
                await self.memory_manager.store_conversation(
                    user_id=message_context.user_id,
                    user_message=message_context.content,
                    bot_response=clean_response,  # Use clean_response without footer
                    pre_analyzed_emotion_data=ai_components.get('emotion_data'),  # User emotion
                    metadata=bot_metadata  # Bot emotion in metadata
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


def create_message_processor(bot_core, memory_manager, llm_client, **kwargs) -> MessageProcessor:
    """Factory function to create a MessageProcessor instance."""
    return MessageProcessor(
        bot_core=bot_core,
        memory_manager=memory_manager, 
        llm_client=llm_client,
        **kwargs
    )