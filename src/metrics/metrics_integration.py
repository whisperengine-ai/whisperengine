"""
Metrics Integration Module
=========================

Integrates the holistic AI metrics and A/B testing framework with the existing
WhisperEngine bot system for seamless performance measurement and optimization.
"""

import logging
import os
from typing import Any

from .ab_testing_framework import ABTestingFramework, TestType
from .holistic_ai_metrics import ConversationMetrics, HolisticAIMetrics

logger = logging.getLogger(__name__)


class MetricsIntegration:
    """
    Integration layer that connects metrics collection with the existing bot system
    """

    def __init__(self, bot_core, redis_client=None, database_manager=None):
        self.bot_core = bot_core
        self.redis_client = redis_client
        self.database_manager = database_manager

        # Initialize metrics systems
        self.metrics_collector = HolisticAIMetrics(redis_client, database_manager)
        self.ab_testing = ABTestingFramework(self.metrics_collector, redis_client, database_manager)

        # Integration settings
        self.metrics_enabled = os.getenv("ENABLE_METRICS_COLLECTION", "true").lower() == "true"
        self.ab_testing_enabled = os.getenv("ENABLE_AB_TESTING", "false").lower() == "true"

        logger.info(
            f"Metrics Integration initialized - Metrics: {self.metrics_enabled}, A/B Testing: {self.ab_testing_enabled}"
        )

    async def process_message_with_metrics(
        self, user_id: str, message: str, memory_manager, simplified_emotion_manager, phase4_integration
    ) -> dict[str, Any]:
        """
        Process a message with full metrics collection and A/B testing
        Uses SimplifiedEmotionManager instead of legacy emotional_intelligence
        """
        if not self.metrics_enabled:
            # Fallback to original processing without metrics
            return await self._process_message_original(
                user_id, message, memory_manager, simplified_emotion_manager, phase4_integration
            )

        # Start metrics collection
        interaction_id = await self.metrics_collector.start_conversation_timing(user_id, message)

        try:
            # Get A/B test configurations if enabled
            test_configs = {}
            if self.ab_testing_enabled:
                test_configs = await self._get_ab_test_configurations(user_id)

            # Process with timing and quality measurement
            result = await self._process_with_instrumentation(
                interaction_id,
                user_id,
                message,
                memory_manager,
                simplified_emotion_manager,
                phase4_integration,
                test_configs,
            )

            return result

        except Exception as e:
            logger.error(f"Error in metrics-enabled message processing: {e}")
            # Fallback to original processing
            return await self._process_message_original(
                user_id, message, memory_manager, simplified_emotion_manager, phase4_integration
            )

    async def _process_with_instrumentation(
        self,
        interaction_id: str,
        user_id: str,
        message: str,
        memory_manager,
        emotional_intelligence,
        phase4_integration,
        test_configs: dict,
    ) -> dict[str, Any]:
        """Process message with full instrumentation"""

        import time

        # 1. Memory Retrieval with Timing
        memory_start = time.time()
        memory_config = test_configs.get("memory", {})
        memory_results = await self._retrieve_memories_with_config(
            user_id, message, memory_manager, memory_config
        )
        memory_time = time.time() - memory_start
        await self.metrics_collector.record_phase_timing(interaction_id, "memory", memory_time)

        # 2. Emotional Intelligence with Timing
        emotion_start = time.time()
        emotion_config = test_configs.get("emotion", {})
        emotion_results = await self._analyze_emotion_with_config(
            user_id, message, emotional_intelligence, emotion_config
        )
        emotion_time = time.time() - emotion_start
        await self.metrics_collector.record_phase_timing(interaction_id, "emotion", emotion_time)

        # 3. Phase 4 Integration with Timing
        integration_start = time.time()
        personality_config = test_configs.get("personality", {})
        response_context = await self._generate_response_context(
            user_id,
            message,
            memory_results,
            emotion_results,
            phase4_integration,
            personality_config,
        )
        integration_time = time.time() - integration_start
        await self.metrics_collector.record_phase_timing(
            interaction_id, "integration", integration_time
        )

        # 4. Generate Final Response
        response = await self._generate_final_response(
            response_context, test_configs.get("response", {})
        )

        # 5. Calculate Quality Metrics
        await self._calculate_quality_metrics(
            interaction_id, user_id, message, response, memory_results, emotion_results
        )

        # 6. Finalize Metrics Collection
        conversation_metrics = await self.metrics_collector.finalize_conversation_metrics(
            interaction_id, response, memory_results, emotion_results
        )

        # 7. Record A/B Test Data
        if self.ab_testing_enabled and conversation_metrics:
            await self._record_ab_test_data(user_id, conversation_metrics, test_configs)

        # Return enhanced response context
        return {
            "response": response,
            "memory_results": memory_results,
            "emotion_results": emotion_results,
            "metrics": conversation_metrics,
            "test_configs": test_configs if self.ab_testing_enabled else None,
        }

    async def _get_ab_test_configurations(self, user_id: str) -> dict[str, dict]:
        """Get A/B test configurations for user"""
        configs = {}

        # Check for active tests and get user's variant
        for test_type in TestType:
            variant = await self.ab_testing.get_user_variant(user_id, test_type)
            if variant:
                configs[test_type.value.replace("_", "")] = variant.configuration

        return configs

    async def _retrieve_memories_with_config(
        self, user_id: str, message: str, memory_manager, config: dict
    ) -> list[dict]:
        """Retrieve memories with A/B test configuration"""
        # Apply test configuration to memory retrieval
        limit = config.get("memory_limit", 15)
        relevance_threshold = config.get("relevance_threshold", 0.5)

        try:
            memories = memory_manager.retrieve_relevant_memories(
                user_id=user_id, query=message, limit=limit
            )

            # Filter by relevance threshold if specified
            if relevance_threshold > 0:
                memories = [m for m in memories if m.get("score", 0) >= relevance_threshold]

            return memories

        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            return []

    async def _analyze_emotion_with_config(
        self, user_id: str, message: str, simplified_emotion_manager, config: dict
    ) -> dict:
        """Analyze emotion with configuration - updated for SimplifiedEmotionManager"""
        try:
            # Apply configuration settings
            intervention_threshold = config.get("intervention_threshold", 0.7)
            support_sensitivity = config.get("support_sensitivity", 0.5)

            # Check if emotion manager is available
            if not simplified_emotion_manager or not simplified_emotion_manager.is_available():
                return {"detected_emotion": "neutral", "intervention_needed": False, "error": "emotion_unavailable"}

            # Perform emotional analysis using simplified manager
            emotion_data = await simplified_emotion_manager.analyze_message_emotion(
                user_id=user_id, 
                message=message, 
                conversation_context={}
            )

            # Apply test configuration adjustments
            emotion_results = {
                "assessment": emotion_data,
                "detected_emotion": emotion_data.get("primary_emotion", "neutral"),
                "confidence": emotion_data.get("confidence", 0.5),
                "intervention_needed": emotion_data.get("support_needed", False) and 
                                     emotion_data.get("confidence", 0.0) > intervention_threshold,
                "support_level": min(
                    1.0, emotion_data.get("confidence", 0.0) / support_sensitivity
                ),
                "config_applied": config,
                "analysis_method": emotion_data.get("analysis_method", "simplified")
            }

            return emotion_results

        except Exception as e:
            logger.error("Emotion analysis error: %s", e)
            return {"detected_emotion": "neutral", "intervention_needed": False, "error": str(e)}

    async def _generate_response_context(
        self,
        user_id: str,
        message: str,
        memory_results: list[dict],
        emotion_results: dict,
        phase4_integration,
        config: dict,
    ) -> dict:
        """Generate response context with personality configuration"""
        try:
            # Apply personality test configuration
            formality_level = config.get("dream_formality", 0.7)
            archaic_language = config.get("archaic_language", 0.6)
            emotional_expression = config.get("emotional_expression", 0.6)

            # Create enhanced context
            context = {
                "user_id": user_id,
                "message": message,
                "memories": memory_results,
                "emotion": emotion_results,
                "personality_config": {
                    "formality": formality_level,
                    "archaic": archaic_language,
                    "emotional": emotional_expression,
                },
            }

            # Use Phase 4 integration if available
            if phase4_integration:
                phase4_context = await phase4_integration.get_comprehensive_context_for_response(
                    context
                )
                context.update(phase4_context)

            return context

        except Exception as e:
            logger.error(f"Context generation error: {e}")
            return {"user_id": user_id, "message": message}

    async def _generate_final_response(self, context: dict, config: dict) -> str:
        """Generate final response with configuration"""
        try:
            # Apply response timing configuration
            max_response_time = config.get("max_response_time", 2.0)

            # Use the bot's LLM client to generate response
            response = await self.bot_core.llm_client.generate_response(
                context=context, max_time=max_response_time
            )

            return response

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "I apologize, but I encountered an issue processing your message."

    async def _calculate_quality_metrics(
        self,
        interaction_id: str,
        user_id: str,
        message: str,
        response: str,
        memory_results: list[dict],
        emotion_results: dict,
    ):
        """Calculate quality metrics for the interaction"""

        # Calculate engagement score based on conversation characteristics
        engagement_score = self._calculate_engagement_score(message, response)
        await self.metrics_collector.record_quality_score(
            interaction_id, "engagement", engagement_score
        )

        # Calculate response appropriateness
        appropriateness = self._calculate_response_appropriateness(emotion_results, response)
        await self.metrics_collector.record_quality_score(
            interaction_id, "appropriateness", appropriateness
        )

        # Calculate memory utilization effectiveness
        memory_effectiveness = self._calculate_memory_effectiveness(memory_results, response)
        await self.metrics_collector.record_quality_score(
            interaction_id, "memory_effectiveness", memory_effectiveness
        )

    def _calculate_engagement_score(self, message: str, response: str) -> float:
        """Calculate user engagement score"""
        # Simplified engagement calculation
        factors = [
            len(message.split()) > 3,  # User provided substantial input
            len(response.split()) > 5,  # Bot provided substantial response
            "?" in message,  # User asked questions
            any(
                word in response.lower() for word in ["what", "how", "why", "tell me"]
            ),  # Bot encouraged conversation
        ]
        return sum(factors) / len(factors)

    def _calculate_response_appropriateness(self, emotion_results: dict, response: str) -> float:
        """Calculate emotional appropriateness of response"""
        detected_emotion = emotion_results.get("detected_emotion", "neutral")

        # Simple sentiment analysis of response
        positive_words = ["good", "great", "wonderful", "excellent", "happy", "joy"]
        negative_words = ["sorry", "sad", "difficult", "concern", "worry", "trouble"]

        response_lower = response.lower()
        positive_score = sum(1 for word in positive_words if word in response_lower)
        negative_score = sum(1 for word in negative_words if word in response_lower)

        # Match response sentiment to detected emotion
        if detected_emotion in ["positive", "very_positive"] and positive_score > negative_score:
            return 0.9
        elif detected_emotion in ["negative", "very_negative"] and negative_score >= positive_score:
            return 0.8
        elif detected_emotion == "neutral":
            return 0.7
        else:
            return 0.5

    def _calculate_memory_effectiveness(self, memory_results: list[dict], response: str) -> float:
        """Calculate how effectively memories were used in response"""
        if not memory_results:
            return 0.5  # Neutral score if no memories

        # Check if response references memory content
        memory_words = set()
        for memory in memory_results:
            content = memory.get("content", "")
            memory_words.update(content.lower().split())

        response_words = set(response.lower().split())
        overlap = len(memory_words.intersection(response_words))

        if len(memory_words) > 0:
            return min(1.0, overlap / min(len(memory_words), 10))  # Normalize
        return 0.5

    async def _record_ab_test_data(
        self, user_id: str, metrics: ConversationMetrics, test_configs: dict
    ):
        """Record data for A/B testing analysis"""
        for test_type_str, _config in test_configs.items():
            try:
                test_type = TestType(test_type_str.replace("config", ""))
                await self.ab_testing.record_test_interaction(user_id, test_type, metrics)
            except ValueError:
                continue  # Skip invalid test types

    async def _process_message_original(
        self, user_id: str, message: str, memory_manager, emotional_intelligence, phase4_integration
    ) -> dict[str, Any]:
        """Fallback to original message processing without metrics"""
        try:
            # Original processing logic (simplified)
            memories = memory_manager.retrieve_relevant_memories(user_id, message, limit=15)
            emotion_assessment = await emotional_intelligence.comprehensive_emotional_assessment(
                user_id, message, {}
            )

            context = {
                "user_id": user_id,
                "message": message,
                "memories": memories,
                "emotion": emotion_assessment,
            }

            response = await self.bot_core.llm_client.generate_response(context=context)

            return {
                "response": response,
                "memory_results": memories,
                "emotion_results": emotion_assessment,
            }

        except Exception as e:
            logger.error(f"Original processing error: {e}")
            return {
                "response": "I apologize, but I encountered an issue processing your message.",
                "memory_results": [],
                "emotion_results": {},
            }

    # Management methods
    async def start_ab_test(self, test_category: str, test_name: str) -> str:
        """Start a new A/B test"""
        if not self.ab_testing_enabled:
            raise ValueError("A/B testing is not enabled")

        test_id = await self.ab_testing.create_predefined_test(test_category, test_name)
        await self.ab_testing.start_test(test_id)
        return test_id

    async def get_metrics_summary(self, time_period: str = "daily") -> dict[str, Any]:
        """Get metrics summary"""
        if not self.metrics_enabled:
            return {"error": "Metrics collection is not enabled"}

        system_metrics = await self.metrics_collector.generate_system_metrics(time_period)
        return system_metrics.__dict__ if system_metrics else {}

    async def get_ab_test_results(self, test_id: str) -> dict[str, Any]:
        """Get A/B test results"""
        if not self.ab_testing_enabled:
            return {"error": "A/B testing is not enabled"}

        results = await self.ab_testing.analyze_test_results(test_id)
        recommendations = await self.ab_testing.get_test_recommendations(test_id)

        return {"results": results, "recommendations": recommendations}
