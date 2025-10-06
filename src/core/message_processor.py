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

# Sprint 3: RelationshipTuner components
from src.relationships.evolution_engine import create_relationship_evolution_engine
from src.relationships.trust_recovery import create_trust_recovery_system

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
        self.temporal_intelligence_enabled = os.getenv('ENABLE_TEMPORAL_INTELLIGENCE', 'true').lower() == 'true'
        self.temporal_client = None
        self.confidence_analyzer = None
        
        if self.temporal_intelligence_enabled:
            try:
                from src.temporal.temporal_protocol import create_temporal_intelligence_system
                
                # Pass knowledge_router for actual PostgreSQL relationship scores
                knowledge_router = getattr(bot_core, 'knowledge_router', None) if bot_core else None
                self.temporal_client, self.confidence_analyzer = create_temporal_intelligence_system(
                    knowledge_router=knowledge_router
                )
                logger.info("Temporal intelligence initialized (enabled: %s, postgres_integration: %s)", 
                           self.temporal_client.enabled, knowledge_router is not None)
            except ImportError:
                logger.warning("Temporal intelligence not available - install influxdb-client")
                self.temporal_intelligence_enabled = False
        
        # Sprint 1 TrendWise: Initialize trend analysis and confidence adaptation
        self.trend_analyzer = None
        self.confidence_adapter = None
        
        if self.temporal_intelligence_enabled and self.temporal_client:
            try:
                from src.analytics.trend_analyzer import create_trend_analyzer
                from src.adaptation.confidence_adapter import create_confidence_adapter
                
                self.trend_analyzer = create_trend_analyzer(self.temporal_client)
                self.confidence_adapter = create_confidence_adapter(self.trend_analyzer)
                logger.info("Sprint 1 TrendWise: Trend analysis and confidence adaptation initialized")
            except ImportError as e:
                logger.warning("TrendWise components not available: %s", e)
                self.trend_analyzer = None
                self.confidence_adapter = None
        
        # Sprint 3 RelationshipTuner: Lazy initialization (postgres_pool may not be ready yet)
        self.relationship_engine = None
        self.trust_recovery = None
        self._sprint3_init_attempted = False  # Track if we've tried initializing
        
        # Initialize fidelity metrics collector for performance tracking
        try:
            from src.monitoring.fidelity_metrics_collector import get_fidelity_metrics_collector
            self.fidelity_metrics = get_fidelity_metrics_collector()
            logger.debug("Fidelity metrics collector initialized")
        except ImportError:
            logger.warning("Fidelity metrics collector not available")
            self.fidelity_metrics = None
        
        # Track processing state for debugging
        self._last_security_validation = None
        self._last_emotional_context = None

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
            
            # Phase 2.5: Workflow detection and transaction processing (platform-agnostic)
            await self._process_workflow_detection(message_context)
            
            # Phase 3: Memory retrieval with context-aware filtering
            relevant_memories = await self._retrieve_relevant_memories(message_context)
            
            # Phase 4: Conversation history and context building
            conversation_context = await self._build_conversation_context(
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
            response = await self._generate_response(
                message_context, conversation_context, ai_components
            )
            
            # Phase 7.5: Analyze bot's emotional state from response
            bot_emotion = await self._analyze_bot_emotion(response, message_context)
            ai_components['bot_emotion'] = bot_emotion
            
            # Phase 8: Response validation and sanitization
            response = await self._validate_and_sanitize_response(
                response, message_context
            )
            
            # Phase 9: Memory storage (vector + knowledge graph)
            memory_stored = await self._store_conversation_memory(
                message_context, response, ai_components
            )
            
            # Phase 9b: Knowledge extraction and storage (PostgreSQL)
            knowledge_stored = await self._extract_and_store_knowledge(
                message_context, ai_components
            )
            
            # Phase 9c: User preference extraction and storage (PostgreSQL)
            preference_stored = await self._extract_and_store_user_preferences(
                message_context
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
        if not self.temporal_intelligence_enabled or not self.temporal_client or not self.confidence_analyzer:
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
            if bot_emotion:
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
            if user_emotion:
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
            await asyncio.gather(
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
                return_exceptions=True  # Don't fail message processing if temporal recording fails
            )
            
            logger.debug("Recorded temporal metrics for %s/%s", bot_name, message_context.user_id)
            
            # Sprint 3: Lazy initialization and update of dynamic relationship scores
            await self._ensure_sprint3_initialized()
            
            if self.relationship_engine:
                try:
                    # Map quality_metrics to ConversationQuality enum (Sprint 1)
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
                    
                    # Get RoBERTa emotion data (Sprint 2)
                    emotion_data = ai_components.get('emotion_data', {})
                    
                    # Calculate and update relationship scores
                    update = await self.relationship_engine.calculate_dynamic_relationship_score(
                        user_id=message_context.user_id,
                        bot_name=bot_name,
                        conversation_quality=conversation_quality,
                        emotion_data=emotion_data
                    )
                    
                    if update:
                        logger.info(
                            "🔄 RELATIONSHIP: Trust/affection/attunement updated for %s/%s - "
                            "trust: %.3f (%+.3f), affection: %.3f (%+.3f), attunement: %.3f (%+.3f)",
                            bot_name, message_context.user_id,
                            update.new_scores.trust, update.changes.get('trust', 0.0),
                            update.new_scores.affection, update.changes.get('affection', 0.0),
                            update.new_scores.attunement, update.changes.get('attunement', 0.0)
                        )
                    
                except Exception as e:
                    logger.warning("Relationship evolution update failed: %s", str(e))
            
        except Exception as e:
            # Log but don't fail message processing
            logger.warning("Failed to record temporal metrics: %s", str(e))
    
    async def _ensure_sprint3_initialized(self):
        """Lazy initialization of Sprint 3 components (postgres_pool may not be ready at __init__ time)."""
        if self._sprint3_init_attempted:
            return  # Already tried, don't spam logs
        
        self._sprint3_init_attempted = True
        
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
            logger.debug("Sprint 3 RelationshipTuner: Still waiting for postgres_pool (postgres_pool=%s, temporal_client=%s)",
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
            await self._ensure_sprint3_initialized()
            
            if not self.relationship_engine:
                logger.debug("Sprint 1-3: Relationship engine not available for prompt injection")
                return
            
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            # SPRINT 3: Get current relationship scores
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
                logger.debug("Sprint 3: Could not retrieve relationship scores: %s", e)
            
            # SPRINT 1: Get conversation quality trends (if trend_analyzer available)
            # TODO: Implement temporal trend retrieval for prompt injection
            # For now, use confidence metrics as a proxy for conversation quality
            if self.confidence_analyzer and len(relevant_memories) > 0:
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
                    logger.debug("Sprint 1: Could not calculate confidence metrics: %s", e)
            
            # Sprint 2 RoBERTa data is already in ai_components['emotion_data']
            
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

            # 🚀 SPRINT 2: Try MemoryBoost enhanced retrieval first if available
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
        🚀 SPRINT 2: Build conversation context for MemoryBoost optimization.
        
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
        🚀 SPRINT 2: Record MemoryBoost metrics to InfluxDB for analytics.
        
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
                
                # Build memory narrative with proper topic summarization and fact separation
                memory_parts = []
                
                # Separate facts from conversations for better organization
                user_facts = []
                conversation_topics = []
                
                # Process recent conversation parts for topic extraction
                if recent_conversation_parts:
                    topics = self._extract_conversation_topics(recent_conversation_parts)
                    conversation_topics.extend(topics)
                
                # Process older conversation parts, separating facts from topics  
                if conversation_memory_parts:
                    for part in conversation_memory_parts:
                        if "[Fact:" in part:
                            user_facts.append(part)
                        else:
                            # Extract topic from conversation memory
                            topic = self._extract_topic_from_memory(part)
                            if topic:  # Only add non-empty topics
                                conversation_topics.append(topic)
                
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
                
                # Build organized memory narrative
                if user_facts:
                    memory_parts.append("USER FACTS: " + "; ".join(user_facts))
                if conversation_topics:
                    # Deduplicate and limit topics
                    unique_topics = list(dict.fromkeys(conversation_topics))[:7]  # Max 7 topics
                    memory_parts.append("CONVERSATION TOPICS: " + "; ".join(unique_topics))
                
                if memory_parts:
                    memory_fragments.append(" ".join(memory_parts))
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added {len(user_facts)} facts + {len(conversation_topics)} topics")
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
                    recent_5 = recent_messages[-5:] if len(recent_messages) >= 5 else recent_messages
                    user_count = sum(1 for msg in recent_5 if not msg.get('bot', False))
                    bot_count = sum(1 for msg in recent_5 if msg.get('bot', False))
                    
                    logger.info(f"🔥 CONTINUITY CHECK: Recent 5 messages - User: {user_count}, Bot: {bot_count}")
                    
                    # If no bot messages in recent 5, expand search to include at least 1 bot response
                    if bot_count == 0 and len(recent_messages) > 5:
                        logger.warning(f"🔥 CONTINUITY FIX: No bot responses in recent 5 messages - expanding search")
                        # Look further back to find at least one bot response
                        for i in range(5, min(15, len(recent_messages))):
                            if recent_messages[-(i+1)].get('bot', False):
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
        
        # Consolidate core system context (lean)
        core_system = system_prompt_content + attachment_guard + guidance_clause
        
        conversation_context.append({"role": "system", "content": core_system})
        
        # 🚀 SOPHISTICATED RECENT MESSAGE PROCESSING with OPTIMIZED ASSEMBLY ORDER
        try:
            if recent_messages:
                logger.info(f"🔥 CONTEXT DEBUG: Processing {len(recent_messages)} recent messages for conversation context")
                
                # OPTIMIZED: Split messages into OLDER (truncated) vs RECENT (detailed)
                recent_full_count = 20  # Last 10 exchanges (20 messages)
                older_messages = recent_messages[:-recent_full_count] if len(recent_messages) > recent_full_count else []
                recent_full_messages = recent_messages[-recent_full_count:] if len(recent_messages) > recent_full_count else recent_messages

                logger.info(f"🔥 CONTINUITY: Split into {len(older_messages)} older (500 chars) + {len(recent_full_messages)} recent (2000 chars)")
                
                # Add older messages first (truncated for space)
                user_assistant_messages = []
                skip_next_bot_response = False
                
                for msg in older_messages:
                    msg_content = msg.get('content', '')
                    is_bot_msg = msg.get('bot', False)
                    
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
                
                # OPTIMIZED: Add memory narrative as context bridge
                if memory_narrative:
                    conversation_context.append({
                        "role": "system", 
                        "content": f"RELEVANT MEMORIES: {memory_narrative}"
                    })
                    logger.debug(f"🔥 CONTEXT BRIDGE: Added memory narrative ({len(memory_narrative)} chars)")

                # OPTIMIZED: Add conversation summary as "where we left off" bridge
                if conversation_summary:
                    conversation_context.append({
                        "role": "system",
                        "content": f"CONVERSATION FLOW: {conversation_summary}"
                    })
                    logger.debug(f"🔥 CONTEXT BRIDGE: Added conversation summary ({len(conversation_summary)} chars)")
                
                # Add recent messages (detailed)
                for msg in recent_full_messages:
                    msg_content = msg.get('content', '')
                    is_bot_msg = msg.get('bot', False)
                    
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

                    # Recent messages: EXPANDED LIMIT - 2000 chars for conversation continuity
                    recent_content = msg_content[:2000] + "..." if len(msg_content) > 2000 else msg_content
                    role = "assistant" if is_bot_msg else "user"
                    conversation_context.append({"role": role, "content": recent_content})
                    logger.info(f"🔥 CONTEXT (RECENT): Added [{role}] ({len(recent_content)} chars): '{recent_content[:100]}...'")
                
                logger.info(f"✅ OPTIMIZED CONTEXT: Added {len(older_messages)} older (500 chars) + {len(recent_full_messages)} recent (2000 chars) messages")
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

    async def _build_conversation_context_with_ai_intelligence(
        self, message_context: MessageContext, relevant_memories: List[Dict[str, Any]], ai_components: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Build conversation context with AI intelligence guidance integrated."""
        # Start with basic conversation context
        conversation_context = await self._build_conversation_context(message_context, relevant_memories)
        
        # Sprint 1 TrendWise: Add confidence adaptation guidance
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
                relevant_snippets.append(content[:200])  # Truncate to 200 chars
        
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
        phase4_3_engagement = comprehensive_context.get('phase4_3_engagement_analysis')
        if phase4_3_engagement and isinstance(phase4_3_engagement, dict):
            intervention_needed = phase4_3_engagement.get('intervention_needed', False)
            engagement_strategy = phase4_3_engagement.get('recommended_strategy')
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
                logger.debug("🎯 TASK DEBUG: Creating phase4_intelligence task")
                phase4_task = self._process_phase4_intelligence_sophisticated(
                    message_context.user_id,
                    message_context.content,
                    message_context,
                    conversation_context
                )
                tasks.append(phase4_task)
                task_names.append("phase4_intelligence")
            
            # Task 5: Thread management analysis (Phase 4.2)
            if self.bot_core and hasattr(self.bot_core, 'phase4_thread_manager'):
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
            
            # Extract core components for backward compatibility
            ai_components['emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['external_emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['context_analysis'] = ai_components.get('context_analysis')
            ai_components['personality_context'] = ai_components.get('personality_analysis')
            ai_components['phase4_context'] = ai_components.get('phase4_intelligence')
            
            # Build comprehensive context from all AI components
            comprehensive_context = {}
            
            # Add Phase 4 intelligence context
            if ai_components.get('phase4_intelligence'):
                phase4_context = ai_components['phase4_intelligence']
                if hasattr(phase4_context, '__dict__'):
                    comprehensive_context.update({
                        'phase4_context': phase4_context,
                        'interaction_type': getattr(phase4_context, 'interaction_type', None),
                        'conversation_mode': getattr(phase4_context, 'conversation_mode', None),
                    })
            
            # Add thread management results (Phase 4.2)
            if ai_components.get('thread_management'):
                comprehensive_context['phase4_2_thread_analysis'] = ai_components['thread_management']
                logger.info("🧠 Added Phase 4.2 Advanced Thread Management results to context")
            
            # Add proactive engagement results (Phase 4.3)
            if ai_components.get('proactive_engagement'):
                comprehensive_context['phase4_3_engagement_analysis'] = ai_components['proactive_engagement']
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
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Sophisticated AI component processing failed: %s", str(e))
            # Fallback to basic components
            ai_components = {
                'emotion_data': None,
                'external_emotion_data': None,
                'context_analysis': None,
                'personality_context': None,
                'phase4_context': None,
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

    async def _process_phase4_intelligence_sophisticated(self, user_id: str, content: str, 
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
            phase3_context_switches = await self._analyze_context_switches(user_id, content, discord_message)
            phase3_empathy_calibration = await self._calibrate_empathy_response(user_id, content, discord_message)
            
            # Process with old Phase 4 sophistication
            phase4_context = await self.bot_core.phase2_integration.process_phase4_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=conversation_context,
                external_emotion_data=None,
                phase2_context=None
            )
            
            # Add Phase 3 results to the Phase 4 context
            if isinstance(phase4_context, dict):
                phase4_context['phase3_context_switches'] = phase3_context_switches
                phase4_context['phase3_empathy_calibration'] = phase3_empathy_calibration
            
            logger.debug(f"Sophisticated Phase 4 intelligence processing successful for user {user_id}")
            return phase4_context
            
        except Exception as e:
            logger.debug(f"Sophisticated Phase 4 intelligence processing failed: {e}")
            return None

    async def _process_thread_management(self, user_id: str, content: str, 
                                       message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process Phase 4.2 Advanced Thread Management."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase4_thread_manager'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process thread management
            thread_result = await self.bot_core.phase4_thread_manager.analyze_thread_context(
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
        """Process Phase 4.3 Proactive Engagement Analysis."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'engagement_engine'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process proactive engagement
            engagement_result = await self.bot_core.engagement_engine.analyze_engagement_potential(
                user_id=user_id,
                message=discord_message,
                conversation_history=[]
            )
            
            logger.debug(f"Proactive engagement analysis successful for user {user_id}")
            return engagement_result
            
        except Exception as e:
            logger.debug(f"Proactive engagement analysis failed: {e}")
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
            
            analyzer = EnhancedVectorEmotionAnalyzer(
                vector_memory_manager=self.memory_manager
            )
            
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
                }
                logger.debug("Vector emotion analysis successful for user %s", user_id)
                return emotion_data
            
        except Exception as e:
            logger.debug("Vector emotion analysis failed: %s", str(e))
        
        return None

    async def _analyze_bot_emotion(self, response: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Analyze bot's emotional state from generated response text.
        
        Phase 7.5: Bot Emotion Tracking
        - Analyzes the bot's response to determine character emotional state
        - Stored in vector memory, InfluxDB, and API metadata
        - Enables UI animations and historical emotion patterns
        
        Args:
            response: Bot's generated response text
            message_context: Context with bot name and conversation details
            
        Returns:
            Dict with primary_emotion, intensity, confidence, analysis_method
        """
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Use the enhanced vector emotion analyzer
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

    async def _analyze_bot_emotional_trajectory(self, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """
        Analyze bot's emotional trajectory from recent conversation history.
        
        Phase 7.6: Bot Emotional Self-Awareness
        - Retrieves bot's recent emotional responses from vector memory
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
            
            # Get bot name for querying bot-specific memories
            bot_name = get_normalized_bot_name_from_env()
            
            # Retrieve bot's recent responses from vector memory
            # Query for bot responses (role=bot) in recent conversations
            bot_memory_query = f"emotional responses by {bot_name}"
            
            recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=message_context.user_id,
                query=bot_memory_query,
                limit=10  # Last 10 bot responses
            )
            
            if not recent_bot_memories:
                return None
            
            # Extract bot emotions from memory metadata
            recent_emotions = []
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

    async def _process_phase4_intelligence(self, user_id: str, content: str, message_context: MessageContext, emotion_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process Phase 4 human-like intelligence if available."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Use Phase 4 integration if available
            phase4_context = await self.bot_core.phase2_integration.process_phase4_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=[],
                external_emotion_data=emotion_data,
                phase2_context=emotion_data
            )
            
            logger.debug("Phase 4 intelligence processing successful for user %s", user_id)
            return phase4_context
            
        except Exception as e:
            logger.debug("Phase 4 intelligence processing failed: %s", str(e))
        
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
                        'guidance': empathy_calibration.guidance_text,
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
            
            # Apply emotion enhancement
            emotion_enhanced_context = await self._add_mixed_emotion_context(
                enhanced_context if enhanced_context else conversation_context,
                message_context.content,
                message_context.user_id,
                ai_components.get('emotion_data'),
                ai_components.get('external_emotion_data')
            )
            
            # Choose final context
            final_context = emotion_enhanced_context if emotion_enhanced_context else conversation_context
            
            # 📝 COMPREHENSIVE PROMPT LOGGING: Log full prompts to file for review
            await self._log_full_prompt_to_file(final_context, message_context.user_id)
            
            # Generate response using LLM
            logger.info("🎯 GENERATING: Sending %d messages to LLM", len(final_context))
            
            from src.llm.llm_client import LLMClient
            llm_client = LLMClient()
            
            response = await asyncio.to_thread(
                llm_client.get_chat_response, final_context
            )
            
            logger.info("✅ GENERATED: Response with %d characters", len(response))
            
            # 📝 LOG LLM RESPONSE: Add response to the prompt log for complete picture
            await self._log_llm_response_to_file(response, message_context.user_id)
            
            # 🎭 CDL EMOJI ENHANCEMENT: Add character-appropriate emojis to text response
            try:
                character_file = os.getenv("CDL_DEFAULT_CHARACTER")
                if character_file:
                    from src.intelligence.cdl_emoji_integration import create_cdl_emoji_integration
                    
                    cdl_emoji_integration = create_cdl_emoji_integration()
                    
                    # Extract just the filename if full path is provided
                    if "/" in character_file:
                        character_file = character_file.split("/")[-1]
                    
                    # Enhance response with CDL-appropriate emojis (ADDS to text, doesn't replace)
                    enhanced_response, emoji_metadata = cdl_emoji_integration.enhance_bot_response(
                        character_file=character_file,
                        user_id=message_context.user_id,
                        user_message=message_context.content,
                        bot_response=response,
                        context={
                            'emotional_context': ai_components.get('emotion_data'),
                            'conversation_history': conversation_context[:3] if conversation_context else []
                        }
                    )
                    
                    if emoji_metadata.get("cdl_emoji_applied", False):
                        response = enhanced_response
                        logger.info(f"🎭 CDL EMOJI: Enhanced response with {len(emoji_metadata.get('emoji_additions', []))} emojis "
                                  f"({emoji_metadata.get('placement_style', 'unknown')} style)")
                    else:
                        logger.debug(f"🎭 CDL EMOJI: No enhancement applied - {emoji_metadata.get('reason', 'unknown')}")
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
            
            # Use CDL_DEFAULT_CHARACTER directly from environment - no dependency on CDL handler
            character_file = os.getenv("CDL_DEFAULT_CHARACTER")
            
            if not character_file:
                logger.info("🎭 CDL CHARACTER DEBUG: No CDL_DEFAULT_CHARACTER environment variable set")
                return None
            
            bot_name = os.getenv("DISCORD_BOT_NAME", "Unknown")
            logger.info("🎭 CDL CHARACTER: Using %s bot default character (%s) for user %s", 
                       bot_name, character_file, user_id)
            
            logger.info("🎭 CDL CHARACTER: User %s has active character: %s", user_id, character_file)
            
            # Import CDL integration modules
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineResult
            from datetime import datetime
            
            # 🚀 SOPHISTICATED PIPELINE RESULT CREATION: Map ALL AI components to VectorAIPipelineResult
            pipeline_result = VectorAIPipelineResult(
                user_id=user_id,
                message_content=message_context.content,
                timestamp=datetime.now(),
                # Map emotion data to emotional_state
                emotional_state=str(ai_components.get('external_emotion_data')) if ai_components.get('external_emotion_data') else str(ai_components.get('emotion_data')) if ai_components.get('emotion_data') else None,
                mood_assessment=ai_components.get('external_emotion_data') if isinstance(ai_components.get('external_emotion_data'), dict) else None,
                # Map personality data 
                personality_profile=ai_components.get('personality_context') if isinstance(ai_components.get('personality_context'), dict) else None,
                # Map phase4 data
                enhanced_context=ai_components.get('phase4_context') if isinstance(ai_components.get('phase4_context'), dict) else None
            )
            
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
            
            # 🎯 ADAPTIVE LEARNING INTEGRATION: Add relationship and confidence data to COMPREHENSIVE CONTEXT
            # This must happen BEFORE comprehensive context is copied to pipeline!
            relationship_data = ai_components.get('relationship_state')
            confidence_data = ai_components.get('conversation_confidence')
            
            if relationship_data or confidence_data:
                # Get or create comprehensive_context in ai_components
                if 'comprehensive_context' not in ai_components:
                    ai_components['comprehensive_context'] = {}
                
                # Add adaptive learning data INSIDE comprehensive_context (CDL integration reads from here)
                if relationship_data:
                    ai_components['comprehensive_context']['relationship_state'] = relationship_data
                    logger.info("🎯 RELATIONSHIP: Added relationship data to comprehensive_context for prompt injection")
                
                if confidence_data:
                    ai_components['comprehensive_context']['conversation_confidence'] = confidence_data
                    logger.info("🎯 CONFIDENCE: Added confidence data to comprehensive_context for prompt injection")
            
            # 🚀 COMPREHENSIVE CONTEXT INTEGRATION: Add all AI components to pipeline
            comprehensive_context = ai_components.get('comprehensive_context')
            if comprehensive_context and isinstance(comprehensive_context, dict):
                # Merge comprehensive context into pipeline enhanced_context
                if isinstance(pipeline_result.enhanced_context, dict):
                    pipeline_result.enhanced_context.update(comprehensive_context)
                else:
                    pipeline_result.enhanced_context = comprehensive_context.copy()
                
                logger.info("🎯 CDL: Enhanced pipeline with comprehensive context from sophisticated AI processing (includes Sprint 1-3)")
            
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
                    knowledge_router=knowledge_router
                )
                logger.warning("⚠️ CDL: Using fallback CDL instance for %s - character system not initialized", user_id)
            
            # Get user's display name for better identification
            user_display_name = message_context.metadata.get('discord_author_name') if message_context.metadata else None
            
            # 🚀 FULL INTELLIGENCE: Use complete character-aware prompt with all emotional intelligence
            character_prompt = await cdl_integration.create_unified_character_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=message_context.content,
                pipeline_result=pipeline_result,
                user_name=user_display_name
            )
            
            # 🎯 WORKFLOW INTEGRATION: Inject workflow transaction context into character prompt
            workflow_prompt_injection = message_context.metadata.get('workflow_prompt_injection') if message_context.metadata else None
            if workflow_prompt_injection:
                character_prompt += f"\n\n🎯 ACTIVE TRANSACTION CONTEXT:\n{workflow_prompt_injection}"
                logger.info("🎯 WORKFLOW: Injected transaction context into character prompt (%d chars)", len(workflow_prompt_injection))
            
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
                    current_message=message_context.content,
                    emotional_context=emotional_context
                )
                
                logger.info("🎯 VECTOR-NATIVE: Enhanced character prompt with dynamic context (%d chars)", len(vector_enhanced_prompt))
                character_prompt = vector_enhanced_prompt
                
            except ImportError as e:
                logger.debug("Vector-native prompt enhancement unavailable, using CDL-only: %s", e)
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
                    logger.info("🎭 CDL CHARACTER: Replaced system message with character prompt (%d chars)", len(character_prompt))
                    break
            
            # If no system message found, add character prompt as first message
            if not system_message_found:
                enhanced_context.insert(0, {
                    'role': 'system', 
                    'content': character_prompt
                })
                logger.info("🎭 CDL CHARACTER: Added character prompt as new system message (%d chars)", len(character_prompt))
            
            logger.info("🎭 CDL CHARACTER: Enhanced conversation context with %s personality", character_file)
            return enhanced_context
            
        except Exception as e:
            logger.error("🎭 CDL CHARACTER ERROR: Failed to apply character enhancement: %s", e)
            logger.error("🎭 CDL CHARACTER ERROR: Falling back to original conversation context")
            return None
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
                    current_message=message_context.content,
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
            return conversation_context

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
                r'(\w+\s+){25,}',  # Same words repeating 25+ times (raised from 10)
                r'(that you can\s+){5,}',  # "that you can" repeating
                r'(\w+\s+\w+\s+){20,}',  # Any two-word pattern repeating 20+ times (raised from 15)
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
                                          ai_components: Dict[str, Any]) -> bool:
        """
        Extract factual knowledge from message and store in PostgreSQL knowledge graph.
        
        This is Phase 3 of the Semantic Knowledge Graph implementation:
        - Detects factual statements (preferences, facts about user)
        - Extracts entity information
        - Stores in PostgreSQL with automatic relationship discovery
        
        Args:
            message_context: The message context
            ai_components: AI processing results including emotion data
            
        Returns:
            True if knowledge was extracted and stored
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
            
            # Preferred name patterns with regex (case-insensitive for keywords, preserves name capitalization)
            import re
            
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
            
            detected_name = None
            matched_pattern = None
            
            for pattern in name_patterns:
                match = re.search(pattern, content)  # Search in original content to preserve capitalization
                if match:
                    detected_name = match.group(1).strip()
                    matched_pattern = pattern
                    logger.debug(f"🔍 PREFERENCE: Detected name '{detected_name}' with pattern: {pattern}")
                    break
            
            if detected_name:
                # Validate name (basic sanity checks)
                if len(detected_name) < 2 or len(detected_name) > 50:
                    logger.debug(f"⚠️ PREFERENCE: Rejected name '{detected_name}' (invalid length)")
                    return False
                
                # Store in PostgreSQL with high confidence (explicit user statement)
                stored = await self.bot_core.knowledge_router.store_user_preference(
                    user_id=message_context.user_id,
                    preference_type='preferred_name',
                    preference_value=detected_name,
                    confidence=0.95,  # High confidence for explicit statements
                    metadata={
                        'detected_pattern': matched_pattern,
                        'source_message': content[:100],  # First 100 chars for debugging
                        'channel_id': message_context.channel_id
                    }
                )
                
                if stored:
                    logger.info(f"✅ PREFERENCE: Stored preferred name '{detected_name}' "
                              f"for user {message_context.user_id}")
                    return True
                else:
                    logger.warning(f"⚠️ PREFERENCE: Failed to store name '{detected_name}' "
                                 f"for user {message_context.user_id}")
            
            return False
            
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
            # 🛡️ FINAL SAFETY CHECK: Don't store obviously broken responses
            if self._is_response_safe_to_store(response):
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
                    bot_response=response,
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

    async def _log_full_prompt_to_file(self, conversation_context: List[Dict[str, Any]], user_id: str):
        """Log the complete prompt sent to LLM for debugging and review."""
        try:
            import json
            from datetime import datetime
            import os
            
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
                "messages": conversation_context
            }
            
            # Write to file
            os.makedirs("/app/logs/prompts", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
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
            
            # Write back to file
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
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
        if self.temporal_intelligence_enabled and self.confidence_analyzer:
            try:
                # Get confidence metrics from analyzer
                confidence_metrics = self.confidence_analyzer.calculate_confidence_metrics(
                    ai_components=ai_components,
                    memory_count=len(relevant_memories) if relevant_memories else 0,
                    processing_time_ms=processing_time_ms
                )
                
                metadata["temporal_intelligence"] = {
                    "confidence_evolution": round(confidence_metrics.overall_confidence, 3),
                    "user_fact_confidence": round(confidence_metrics.user_fact_confidence, 3),
                    "relationship_confidence": round(confidence_metrics.relationship_confidence, 3),
                    "context_confidence": round(confidence_metrics.context_confidence, 3),
                    "emotional_confidence": round(confidence_metrics.emotional_confidence, 3),
                    "interaction_pattern": "stable",  # TODO: Calculate from temporal data
                    "data_source": "phase5_temporal_intelligence"
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
        phase4_data = ai_components.get('phase4_intelligence', {})
        relationship_level = phase4_data.get('relationship_level', 'acquaintance')
        
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
        phase4_metadata = phase4_data.get('processing_metadata', {})
        performance_metrics = phase4_metadata.get('performance_metrics', {})
        
        metadata["processing_pipeline"] = {
            "phase2_emotion_analysis_ms": round(performance_metrics.get('phase2_duration', 0) * 1000, 2),
            "phase4_intelligence_ms": round(phase4_metadata.get('total_duration', 0) * 1000, 2),
            "total_processing_ms": processing_time_ms,
            "phases_executed": phase4_metadata.get('phases_executed', []),
            "phases_completed": phase4_metadata.get('phases_completed', 0)
        }
        
        # 7. Conversation Context Indicators
        metadata["conversation_intelligence"] = {
            "context_switches_detected": len(phase4_data.get('phase3_context_switches', [])),
            "conversation_mode": phase4_data.get('conversation_mode', 'standard'),
            "interaction_type": phase4_data.get('interaction_type', 'general'),
            "response_guidance": phase4_data.get('response_guidance', 'natural_conversation')
        }
        
        return metadata


def create_message_processor(bot_core, memory_manager, llm_client, **kwargs) -> MessageProcessor:
    """Factory function to create a MessageProcessor instance."""
    return MessageProcessor(
        bot_core=bot_core,
        memory_manager=memory_manager, 
        llm_client=llm_client,
        **kwargs
    )