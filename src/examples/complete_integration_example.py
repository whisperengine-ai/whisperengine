"""
Complete Graph Database Integration Example with LLM Support

This example demonstrates the full integrated system with:
- Proper environment loading via env_manager
- LLM client initialization for emotion analysis
- Local embeddings (single unified model)
- Qdrant vector database integration
- Memory system integration
"""

import asyncio
import logging
import os
import sys

# Add project root to path and load environment (like main.py does)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Load environment configuration using your env_manager
from env_manager import load_environment

if not load_environment():
    sys.exit(1)

# Import the integrated components
from src.llm.concurrent_llm_manager import ConcurrentLLMManager
from src.llm.llm_client import LLMClient
from src.memory.memory_manager import UserMemoryManager
from src.utils.graph_integrated_emotion_manager import GraphIntegratedEmotionManager

logger = logging.getLogger(__name__)


class CompleteIntegratedBot:
    """Complete example bot with full LLM and graph integration"""

    def __init__(self):
        """Initialize bot with full system integration"""

        # Initialize LLM client (like main.py does)
        base_llm_client = LLMClient()
        safe_llm_client = ConcurrentLLMManager(base_llm_client)
        # Test connection (network/IO issues simply result in disabled LLM mode)
        self.llm_client = safe_llm_client if base_llm_client.check_connection() else None

        # Initialize memory manager (embeddings are always local now)
        self.memory_manager = UserMemoryManager(
            enable_auto_facts=True, enable_global_facts=False, llm_client=self.llm_client
        )

        # Initialize graph-integrated emotion manager
        self.emotion_manager = GraphIntegratedEmotionManager(
            llm_client=self.llm_client, memory_manager=self.memory_manager
        )

    async def process_message(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> dict:
        """Process a message through the complete integrated system"""

        try:
            # Process through enhanced emotion system
            profile, emotion_profile = self.emotion_manager.process_interaction_enhanced(
                user_id, message, display_name
            )

            # Store in memory system
            memory_id = self.memory_manager.store_conversation(user_id, message, "")

            # Get comprehensive context
            context = await self._build_comprehensive_context(user_id, message)

            # Generate contextual response
            response = await self._generate_contextual_response(message, context)

            return {
                "response": response,
                "memory_id": memory_id,
                "user_profile": {
                    "relationship_level": profile.relationship_level.value,
                    "current_emotion": profile.current_emotion.value,
                    "interaction_count": profile.interaction_count,
                    "escalation_count": profile.escalation_count,
                    "trust_indicators": len(profile.trust_indicators or []),
                    "name": profile.name,
                },
                "emotion_analysis": {
                    "detected_emotion": emotion_profile.detected_emotion.value,
                    "confidence": emotion_profile.confidence,
                    "intensity": emotion_profile.intensity,
                    "triggers": emotion_profile.triggers,
                },
                "context_sources": context.get("active_systems", []),
                "context_quality": context.get("quality_score", 0.0),
            }

        except Exception as e:  # Broad catch to return safe error response
            logger.error("Error processing message: %s", e)
            return {
                "response": "I apologize, but I encountered an error processing your message.",
                "error": str(e),
            }

    async def _build_comprehensive_context(self, user_id: str, message: str) -> dict:
        """Build comprehensive context from all available systems"""

        context = {"active_systems": [], "quality_score": 0.0, "sections": {}}

        # Get emotion context (enhanced with graph data if available)
        try:
            emotion_context = await self.emotion_manager.get_enhanced_emotion_context(
                user_id, message
            )
            if emotion_context:
                context["sections"]["emotion"] = emotion_context
                context["active_systems"].append("emotion_system")
                context["quality_score"] += 0.3
        except Exception as e:  # Non-critical
            logger.warning("Failed to get emotion context: %s", e)

        # Get memory context
        try:
            relevant_memories = self.memory_manager.retrieve_relevant_memories(
                user_id, message, limit=5
            )
            if relevant_memories:
                memory_text = "\n".join([f"• {mem['content']}" for mem in relevant_memories])
                context["sections"]["memories"] = f"Relevant memories:\n{memory_text}"
                context["active_systems"].append("memory_system")
                context["quality_score"] += 0.2
        except Exception as e:  # Non-critical
            logger.warning("Failed to get memory context: %s", e)

        # Get graph-based contextual insights
        try:
            if self.emotion_manager.enable_graph_sync:
                graph_insights = await self.emotion_manager.get_contextual_memories_for_prompt(
                    user_id, message, limit=3
                )
                if graph_insights:
                    context["sections"]["graph_insights"] = graph_insights
                    context["active_systems"].append("graph_database")
                    context["quality_score"] += 0.4
        except Exception as e:  # Non-critical
            logger.warning("Failed to get graph insights: %s", e)

        # Get user facts if available
        try:
            potential = getattr(self.memory_manager, "get_user_facts", None)
            if callable(potential):
                user_facts_raw = potential(user_id, limit=3)
                user_facts_list = []
                if isinstance(user_facts_raw, dict):
                    user_facts_list = [user_facts_raw]
                elif isinstance(user_facts_raw, (list, tuple, set)):
                    user_facts_list = list(user_facts_raw)
                # else: unsupported type or None -> skip
                if user_facts_list:
                    facts_text_parts = []
                    for fact in user_facts_list:
                        if isinstance(fact, dict):
                            content = fact.get("content") or fact.get("text") or str(fact)
                            facts_text_parts.append(f"• {content}")
                        else:
                            facts_text_parts.append(f"• {str(fact)}")
                    if facts_text_parts:
                        facts_text = "\n".join(facts_text_parts)
                        context["sections"]["facts"] = f"Known facts about user:\n{facts_text}"
                        context["active_systems"].append("fact_system")
                        context["quality_score"] += 0.1
        except Exception as e:  # Non-critical
            logger.warning("Failed to get user facts: %s", e)

        return context

    async def _generate_contextual_response(self, message: str, context: dict) -> str:
        """Generate response using LLM with full context"""

        if not self.llm_client:
            return self._generate_fallback_response(message, context)

        try:
            # Build comprehensive prompt
            system_prompt = self._build_system_prompt(context)

            # Create conversation context for LLM
            conversation_context = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]

            # Get LLM response
            response = await asyncio.to_thread(
                self.llm_client.get_chat_response, conversation_context
            )

            return response

        except Exception as e:
            logger.error("LLM response generation failed: %s", e)
            return self._generate_fallback_response(message, context)

    def _build_system_prompt(self, context: dict) -> str:
        """Build system prompt with context"""

        prompt_parts = [
            "You are a helpful, empathetic AI assistant that remembers and learns from conversations.",
            "Respond naturally and personally based on the context provided.",
        ]

        # Add context sections
        for section_name, section_content in context.get("sections", {}).items():
            prompt_parts.append(f"\n=== {section_name.upper()} ===")
            prompt_parts.append(section_content)

        # Add quality indicator
        quality = context.get("quality_score", 0.0)
        if quality > 0.7:
            prompt_parts.append("\n=== INSTRUCTION ===")
            prompt_parts.append(
                "You have rich context about this user. Use it to provide a personalized, emotionally aware response."
            )
        elif quality > 0.3:
            prompt_parts.append("\n=== INSTRUCTION ===")
            prompt_parts.append(
                "You have some context about this user. Use it to provide a more personalized response."
            )

        return "\n".join(prompt_parts)

    def _generate_fallback_response(self, message: str, context: dict) -> str:
        """Generate fallback response without LLM"""

        # Use context to determine response tone
        active_systems = context.get("active_systems", [])
        quality = context.get("quality_score", 0.0)

        if quality > 0.5:
            tone = "contextual and personalized"
        elif "emotion_system" in active_systems:
            tone = "emotionally aware"
        else:
            tone = "helpful and friendly"

        return f'[tone: {tone}] I understand your message: "{message[:100]}..."'

    async def get_system_status(self) -> dict:
        """Get comprehensive system status"""

        status = {
            "timestamp": asyncio.get_event_loop().time(),
            "overall_health": "healthy",
            "components": {},
        }

        # Check LLM client
        if self.llm_client:
            try:
                # Test connection
                connected = await asyncio.to_thread(self.llm_client.check_connection)
                status["components"]["llm_client"] = {
                    "status": "connected" if connected else "disconnected",
                    "endpoint": os.getenv("LLM_CHAT_API_URL", "unknown"),
                }
            except Exception as e:
                status["components"]["llm_client"] = {"status": "error", "error": str(e)}
        else:
            status["components"]["llm_client"] = {"status": "not_initialized"}

        # Check memory manager
        try:
            # Test memory system
            self.memory_manager.retrieve_relevant_memories("test_user", "test", limit=1)
            status["components"]["memory_manager"] = {
                "status": "healthy",
                "embedding_model": os.getenv("EMBEDDING_MODEL", "snowflake/snowflake-arctic-embed-xs"),
            }
        except Exception as e:
            status["components"]["memory_manager"] = {"status": "error", "error": str(e)}

        # Check emotion manager
        try:
            health = await self.emotion_manager.health_check()
            status["components"]["emotion_manager"] = health
        except Exception as e:
            status["components"]["emotion_manager"] = {"status": "error", "error": str(e)}

        # Overall health assessment
        component_statuses = [
            comp.get("status", "unknown") for comp in status["components"].values()
        ]
        if "error" in component_statuses:
            status["overall_health"] = "degraded"
        elif "disconnected" in component_statuses:
            status["overall_health"] = "limited"

        return status


async def demonstrate_complete_integration():
    """Demonstrate the complete integrated system"""

    # Initialize complete bot
    bot = CompleteIntegratedBot()

    # System status check
    status = await bot.get_system_status()

    for _component, _details in status["components"].items():
        pass

    # Conversation demonstration

    user_id = "123456789012345678"  # Discord user ID format (18 digits)
    conversations = [
        ("Hi, I'm Alex and I'm really excited about AI!", "Enthusiastic introduction"),
        ("I've been learning about machine learning lately", "Interest sharing"),
        ("Sometimes I worry I'm not smart enough for this field", "Vulnerability/self-doubt"),
        ("Thanks for encouraging me, that really helps!", "Gratitude and relationship building"),
        ("What do you remember about my interests?", "Memory and context test"),
    ]

    for _i, (message, _description) in enumerate(conversations, 1):

        # Process through complete system
        result = await bot.process_message(user_id, message, "Alex")

        if "error" in result:
            pass
        else:
            if result["user_profile"]["trust_indicators"] > 0:
                pass
            if result["user_profile"]["escalation_count"] > 0:
                pass

    # Show final system capabilities

    capabilities = []
    if "llm_client" in [
        comp
        for comp, details in status["components"].items()
        if details.get("status") in ["healthy", "connected"]
    ]:
        capabilities.append("✅ Full LLM-powered responses")
    if "emotion_manager" in status["components"]:
        capabilities.append("✅ Enhanced emotion analysis")
    if "memory_manager" in status["components"]:
        capabilities.append("✅ Persistent memory with local embeddings")
    if os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true":
        capabilities.append("✅ Graph database relationship tracking")

    for _capability in capabilities:
        pass

    if not capabilities:
        pass


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    # Run the complete demonstration
    asyncio.run(demonstrate_complete_integration())
