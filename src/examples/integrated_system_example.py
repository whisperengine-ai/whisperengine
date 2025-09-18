"""
Example: How to Use the Integrated Graph-Enhanced Emotion System

This example shows how to use the new integrated system that combines:
- Enhanced emotion detection and relationship tracking
- Graph database storage for persistent context
- Memory system integration
- Contextual response generation

The system gracefully falls back to existing functionality if components are unavailable.
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

from src.memory.memory_manager import UserMemoryManager
from src.utils.graph_integrated_emotion_manager import GraphIntegratedEmotionManager

# Import the integrated components

logger = logging.getLogger(__name__)


class EnhancedBot:
    """Example bot using integrated emotion and graph systems"""

    def __init__(self, llm_client=None):
        """Initialize bot with integrated systems"""
        # Initialize memory manager (always uses unified local embedding model)
        self.memory_manager = UserMemoryManager(llm_client=llm_client)

        # Initialize graph-integrated emotion manager (shares same memory manager)
        self.emotion_manager = GraphIntegratedEmotionManager(
            llm_client=llm_client, memory_manager=self.memory_manager
        )

        logger.info("Enhanced bot initialized with integrated systems (local embeddings)")

    async def process_message(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> dict:
        """Process a message using all integrated systems"""

        try:  # Broad catch acceptable here to return safe structured error (mixed sources)
            # 1. Process interaction (emotion + relationship + optional graph sync)
            profile, emotion_profile = self.emotion_manager.process_interaction_enhanced(
                user_id, message, display_name
            )
        except Exception as e:  # noqa: BLE001 - multiple underlying libs may raise arbitrary errors
            logger.error("Emotion processing failed: %s", e)
            return {"response": "Temporary processing issue.", "error": str(e)}

        # 2. Store conversation stub (actual response inserted later if you extend logic)
        memory_id = None
        try:  # Conversation storage failures shouldn't abort entire flow
            memory_id = self.memory_manager.store_conversation(
                user_id, message, "(pending response)"
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to store conversation: %s", e)

        # 3. Build context
        context = await self._get_comprehensive_context(user_id, message)

        # 4. Generate response (replace with actual LLM usage if desired)
        response = await self._generate_response(message, context)

        # 5. (Optional) Update stored conversation with real response here

        return {
            "response": response,
            "user_profile": {
                "relationship_level": profile.relationship_level.value,
                "current_emotion": profile.current_emotion.value,
                "interaction_count": profile.interaction_count,
            },
            "emotion_analysis": {
                "detected_emotion": emotion_profile.detected_emotion.value,
                "confidence": emotion_profile.confidence,
                "intensity": emotion_profile.intensity,
            },
            "context_sources": context.get("systems_active", []),
            "memory_id": memory_id,
        }

    async def _get_comprehensive_context(self, user_id: str, message: str) -> dict:
        """Get context from all available systems"""

        context = {
            "systems_active": [],
            "emotion_context": "",
            "memory_context": [],
            "graph_insights": "",
        }

        try:  # Context enrichment is best-effort
            # Get emotion context (enhanced with graph data if available)
            emotion_context = await self.emotion_manager.get_enhanced_emotion_context(
                user_id, message
            )
            context["emotion_context"] = emotion_context
            context["systems_active"].append("emotion_manager")

            if self.emotion_manager.enable_graph_sync:
                context["systems_active"].append("graph_database")

        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get emotion context: %s", e)

        try:  # Memory retrieval is optional for response quality
            # Get relevant memories
            memories = self.memory_manager.retrieve_relevant_memories(user_id, message, limit=5)
            context["memory_context"] = [m.get("content", "")[:100] for m in memories]
            context["systems_active"].append("chromadb")
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get memory context: %s", e)

        try:  # Graph insights are optional
            # Get graph-based contextual memories if available
            if self.emotion_manager.enable_graph_sync:
                graph_memories = await self.emotion_manager.get_contextual_memories_for_prompt(
                    user_id, message, limit=3
                )
                if graph_memories:
                    context["graph_insights"] = graph_memories
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get graph insights: %s", e)

        return context

    async def _generate_response(self, message: str, context: dict) -> str:
        """Generate response using context (replace with your actual LLM call)"""

        # Build system prompt with context
        system_prompt_parts = []

        # Add base personality
        system_prompt_parts.append("You are a helpful AI assistant.")

        # Add emotion context
        if context.get("emotion_context"):
            system_prompt_parts.append("\n=== USER CONTEXT ===")
            system_prompt_parts.append(context["emotion_context"])

        # Add memory context
        if context.get("memory_context"):
            system_prompt_parts.append("\n=== RELEVANT MEMORIES ===")
            for i, memory in enumerate(context["memory_context"][:3], 1):
                system_prompt_parts.append(f"{i}. {memory}")

        # Add graph insights
        if context.get("graph_insights"):
            system_prompt_parts.append("\n=== CONTEXTUAL INSIGHTS ===")
            system_prompt_parts.append(context["graph_insights"])

        "\n".join(system_prompt_parts)

        # This is where you'd call your actual LLM
        # For demo purposes, return a context-aware response
        emotion_context = context.get("emotion_context", "")

        if "close" in emotion_context.lower() or "friend" in emotion_context.lower():
            tone = "warm and personal"
        elif "acquaintance" in emotion_context.lower():
            tone = "friendly"
        else:
            tone = "helpful and professional"

        return f"[{tone} response based on context] I understand your message: {message[:50]}..."

    async def get_user_summary(self, user_id: str) -> dict:
        """Get comprehensive user summary from all systems"""

        summary = {"user_id": user_id, "timestamp": asyncio.get_event_loop().time()}

        try:  # Profile retrieval may fail if emotion subsystem degraded
            # Get emotion manager profile
            profile = self.emotion_manager.get_or_create_profile(user_id)
            summary.update(
                {
                    "relationship_level": profile.relationship_level.value,
                    "interaction_count": profile.interaction_count,
                    "current_emotion": profile.current_emotion.value,
                    "name": profile.name,
                    "escalation_count": profile.escalation_count,
                    "trust_indicators": len(profile.trust_indicators or []),
                }
            )

        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get emotion profile: %s", e)

        try:  # Memory stats are optional
            # Get memory statistics
            memories = self.memory_manager.retrieve_relevant_memories(
                user_id, "all conversations", limit=100
            )
            summary["total_memories"] = len(memories)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get memory statistics: %s", e)

        try:  # Graph analysis optional
            if self.emotion_manager.enable_graph_sync:
                connector_getter = getattr(self.emotion_manager, "_get_graph_connector", None)
                if callable(connector_getter):  # Private access guarded intentionally
                    graph_connector = await connector_getter()  # noqa: SLF001
                    if graph_connector:
                        relationship_context = await graph_connector.get_user_relationship_context(
                            user_id
                        )
                        summary["graph_analysis"] = {
                            "intimacy_level": relationship_context.get("intimacy_level", 0),
                            "topics_discussed": len(relationship_context.get("topics", [])),
                            "emotional_patterns": len(
                                relationship_context.get("experienced_emotions", [])
                            ),
                        }
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to get graph analysis: %s", e)

        return summary

    async def health_check(self) -> dict:
        """Check health of all integrated systems"""

        health = {
            "timestamp": asyncio.get_event_loop().time(),
            "overall_status": "healthy",
            "components": {},
        }

        # Check emotion manager
        try:  # Emotion manager health
            emotion_health = await self.emotion_manager.health_check()
            health["components"]["emotion_manager"] = emotion_health
        except Exception as e:  # noqa: BLE001
            health["components"]["emotion_manager"] = {"status": "error", "error": str(e)}

        # Check memory manager
        try:  # Memory subsystem health
            self.memory_manager.retrieve_relevant_memories("health_check", "test", limit=1)
            health["components"]["memory_manager"] = {"status": "healthy"}
        except Exception as e:  # noqa: BLE001
            health["components"]["memory_manager"] = {"status": "error", "error": str(e)}

        # Overall status
        statuses = [comp.get("status", "unknown") for comp in health["components"].values()]
        if "error" in statuses:
            health["overall_status"] = "degraded"

        return health


# Example usage
async def example_conversation():
    """Example of using the enhanced bot"""

    # Initialize bot
    bot = EnhancedBot()

    # Health check
    health = await bot.health_check()
    for _component, _status in health["components"].items():
        pass

    # Example conversation flow
    user_id = "example_user_456"

    conversations = [
        ("Hi, I'm Sarah and I'm new here", "Introduction"),
        ("I'm having a really stressful day at work", "Emotional sharing"),
        ("My boss is being unreasonable about deadlines", "Work stress - specific"),
        ("Thanks for listening, you're really helpful", "Gratitude - relationship building"),
        ("How do you remember all this stuff about me?", "Meta question about memory"),
    ]

    for i, (message, _description) in enumerate(conversations, 1):

        # Process message through integrated system
        await bot.process_message(user_id, message, "Sarah")

        # Show relationship progression
        if i % 2 == 0:  # Every other message
            await bot.get_user_summary(user_id)

    # Final summary
    final_summary = await bot.get_user_summary(user_id)
    for key, _value in final_summary.items():
        if key != "user_id":
            pass


# Integration with existing Discord bot
class DiscordBotIntegration:
    """Example of integrating with existing Discord bot code"""

    def __init__(self, discord_client, llm_client):
        self.discord_client = discord_client
        self.enhanced_bot = EnhancedBot(llm_client)

    async def on_message(self, message):
        """Enhanced message handler for Discord bot"""

        if message.author.bot:
            return

        user_id = str(message.author.id)
        display_name = message.author.display_name
        content = message.content

        try:  # Discord message processing should never raise uncaught errors
            # Process through enhanced system
            result = await self.enhanced_bot.process_message(user_id, content, display_name)

            # Send response
            await message.channel.send(result["response"])

            # Log interaction details
            logger.info(
                "Processed message from %s: emotion=%s, relationship=%s",
                display_name,
                result['emotion_analysis']['detected_emotion'],
                result['user_profile']['relationship_level'],
            )

        except Exception as e:  # noqa: BLE001
            logger.error("Error processing Discord message: %s", e)
            await message.channel.send("I'm sorry, I encountered an error processing your message.")


if __name__ == "__main__":
    # To run this example:
    # 1. Ensure Neo4j container is running: docker-compose up -d neo4j
    # 2. Set ENABLE_GRAPH_DATABASE=true in your .env
    # 3. Run: python -m src.examples.integrated_system_example

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run example
    asyncio.run(example_conversation())
