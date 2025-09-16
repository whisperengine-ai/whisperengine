"""
Fixed Example: How to Use the Integrated Graph-Enhanced Emotion System

This example shows how to use the new integrated system with your existing
ChromaDB setup to avoid embedding function conflicts.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

# Add project root to path and load environment (like main.py does)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Load environment configuration using your env_manager
from env_manager import load_environment

if not load_environment():
    print("❌ Failed to load environment configuration")
    print("💡 Run: python setup_env.py --template minimal")
    sys.exit(1)

# Import the integrated components
from src.utils.graph_integrated_emotion_manager import GraphIntegratedEmotionManager

logger = logging.getLogger(__name__)


class EnhancedBotFixed:
    """Example bot using integrated emotion and graph systems - Fixed for existing ChromaDB"""

    def __init__(self, llm_client=None):
        """Initialize bot with integrated systems - avoiding ChromaDB conflicts"""

        # Initialize graph-integrated emotion manager (this doesn't use ChromaDB directly)
        self.emotion_manager = GraphIntegratedEmotionManager(
            llm_client=llm_client,
            memory_manager=None,  # We'll avoid the memory manager for now to prevent conflicts
        )

        logger.info("Enhanced bot initialized with integrated emotion system (ChromaDB-safe)")

    async def process_message(
        self, user_id: str, message: str, display_name: Optional[str] = None
    ) -> dict:
        """Process a message using the enhanced emotion system only"""

        try:
            # 1. Process through emotion manager (gets emotion + relationship context)
            #    This also syncs to graph database if enabled
            profile, emotion_profile = self.emotion_manager.process_interaction_enhanced(
                user_id, message, display_name
            )

            # 2. Get comprehensive context for response generation
            context = await self._get_emotion_context(user_id, message)

            # 3. Generate response using context (replace with your actual LLM call)
            response = await self._generate_response(message, context)

            return {
                "response": response,
                "user_profile": {
                    "relationship_level": profile.relationship_level.value,
                    "current_emotion": profile.current_emotion.value,
                    "interaction_count": profile.interaction_count,
                    "escalation_count": profile.escalation_count,
                    "trust_indicators": len(profile.trust_indicators or []),
                },
                "emotion_analysis": {
                    "detected_emotion": emotion_profile.detected_emotion.value,
                    "confidence": emotion_profile.confidence,
                    "intensity": emotion_profile.intensity,
                    "triggers": emotion_profile.triggers,
                },
                "context_sources": context.get("systems_active", []),
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your message.",
                "error": str(e),
            }

    async def _get_emotion_context(self, user_id: str, message: str) -> dict:
        """Get context from emotion and graph systems"""

        context = {"systems_active": [], "emotion_context": "", "graph_insights": ""}

        try:
            # Get emotion context (enhanced with graph data if available)
            emotion_context = await self.emotion_manager.get_enhanced_emotion_context(
                user_id, message
            )
            context["emotion_context"] = emotion_context
            context["systems_active"].append("emotion_manager")

            if self.emotion_manager.enable_graph_sync:
                context["systems_active"].append("graph_database")

        except Exception as e:
            logger.warning(f"Failed to get emotion context: {e}")
            context["emotion_context"] = "Emotion system unavailable"

        try:
            # Get graph-based contextual memories if available
            if self.emotion_manager.enable_graph_sync:
                graph_memories = await self.emotion_manager.get_contextual_memories_for_prompt(
                    user_id, message, limit=3
                )
                if graph_memories:
                    context["graph_insights"] = graph_memories

        except Exception as e:
            logger.warning(f"Failed to get graph insights: {e}")

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

        # Add graph insights
        if context.get("graph_insights"):
            system_prompt_parts.append("\n=== CONTEXTUAL INSIGHTS ===")
            system_prompt_parts.append(context["graph_insights"])

        system_prompt = "\n".join(system_prompt_parts)

        # This is where you'd call your actual LLM
        # For demo purposes, return a context-aware response
        emotion_context = context.get("emotion_context", "")

        if "close" in emotion_context.lower() or "friend" in emotion_context.lower():
            tone = "warm and personal"
        elif "acquaintance" in emotion_context.lower():
            tone = "friendly"
        else:
            tone = "helpful and professional"

        return f"[{tone} response] I understand your message about: {message[:100]}..."

    async def get_user_summary(self, user_id: str) -> dict:
        """Get comprehensive user summary from emotion and graph systems"""

        summary = {"user_id": user_id, "timestamp": asyncio.get_event_loop().time()}

        try:
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

        except Exception as e:
            logger.warning(f"Failed to get emotion profile: {e}")

        try:
            # Get graph insights if available
            if self.emotion_manager.enable_graph_sync:
                graph_connector = await self.emotion_manager._get_graph_connector()
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

        except Exception as e:
            logger.warning(f"Failed to get graph analysis: {e}")

        return summary

    async def health_check(self) -> dict:
        """Check health of integrated systems"""

        health = {
            "timestamp": asyncio.get_event_loop().time(),
            "overall_status": "healthy",
            "components": {},
        }

        # Check emotion manager
        try:
            emotion_health = await self.emotion_manager.health_check()
            health["components"]["emotion_manager"] = emotion_health
        except Exception as e:
            health["components"]["emotion_manager"] = {"status": "error", "error": str(e)}

        # Overall status
        statuses = [comp.get("status", "unknown") for comp in health["components"].values()]
        if "error" in statuses:
            health["overall_status"] = "degraded"

        return health


# Example usage - ChromaDB safe
async def example_conversation_fixed():
    """Example of using the enhanced bot without ChromaDB conflicts"""

    print("🤖 Enhanced Bot with Graph-Emotion System (ChromaDB-Safe)")
    print("=" * 60)

    # Initialize bot (avoids ChromaDB memory manager)
    bot = EnhancedBotFixed()

    # Health check
    health = await bot.health_check()
    print(f"System Health: {health['overall_status']}")
    for component, status in health["components"].items():
        print(f"  {component}: {status.get('status', 'unknown')}")

    # Example conversation flow
    user_id = "example_user_fixed_789"

    conversations = [
        ("Hi, I'm Sarah and I'm new here", "Introduction"),
        ("I'm having a really stressful day at work", "Emotional sharing"),
        ("My boss is being unreasonable about deadlines", "Work stress - specific"),
        ("Thanks for listening, you're really helpful", "Gratitude - relationship building"),
        ("How do you remember my emotional patterns?", "Meta question about memory"),
    ]

    print(f"\n💬 Example Conversation with User: {user_id}")
    print("-" * 60)

    for i, (message, description) in enumerate(conversations, 1):
        print(f"\n[{i}] {description}")
        print(f"User: {message}")

        # Process message through integrated system
        result = await bot.process_message(user_id, message, "Sarah")

        print(f"Bot: {result['response']}")
        print(
            f"Relationship: {result['user_profile']['relationship_level']} "
            f"({result['user_profile']['interaction_count']} interactions)"
        )
        print(
            f"Emotion: {result['emotion_analysis']['detected_emotion']} "
            f"(confidence: {result['emotion_analysis']['confidence']:.2f}, "
            f"intensity: {result['emotion_analysis']['intensity']:.2f})"
        )
        print(f"Systems: {', '.join(result['context_sources'])}")

        # Show escalation tracking
        if result["user_profile"]["escalation_count"] > 0:
            print(f"⚠️  Escalation count: {result['user_profile']['escalation_count']}")

        # Show trust indicators
        trust_count = result["user_profile"]["trust_indicators"]
        if trust_count > 0:
            print(f"🤝 Trust indicators: {trust_count}")

    # Final summary
    print(f"\n📊 Final User Summary")
    print("-" * 60)
    final_summary = await bot.get_user_summary(user_id)
    for key, value in final_summary.items():
        if key not in ["user_id", "timestamp"]:
            print(f"{key}: {value}")

    # Show what would be different with graph database enabled
    print(f"\n🕸️ Graph Database Status")
    print("-" * 60)
    graph_enabled = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"
    print(f"Graph database enabled: {graph_enabled}")

    if graph_enabled:
        print("✅ Enhanced features active:")
        print("  • Relationship progression tracking in Neo4j")
        print("  • Emotional pattern analysis across conversations")
        print("  • Topic-emotion association mapping")
        print("  • Contextual memory linking")
    else:
        print("ℹ️  To enable graph features:")
        print("  1. Set ENABLE_GRAPH_DATABASE=true in .env")
        print("  2. Start Neo4j: docker-compose up -d neo4j")
        print("  3. Run setup: ./scripts/setup_neo4j.sh")


async def demonstrate_emotion_system_only():
    """Demonstrate just the enhanced emotion system without ChromaDB conflicts"""

    print("\n🧠 Emotion System Enhancement Demo")
    print("=" * 60)

    # Initialize just the emotion manager
    emotion_manager = GraphIntegratedEmotionManager()

    user_id = "demo_user_emotion"
    messages = [
        "Hello, I'm John",
        "I'm excited about my new job!",
        "Actually, I'm a bit nervous about starting",
        "Thanks for being so understanding",
        "You really help me feel better",
    ]

    print("Tracking relationship and emotion progression:")
    print("-" * 40)

    for i, message in enumerate(messages, 1):
        print(f"\n{i}. User: {message}")

        # Process through emotion system
        profile, emotion_profile = emotion_manager.process_interaction_enhanced(
            user_id, message, "John"
        )

        print(f"   Relationship: {profile.relationship_level.value}")
        print(
            f"   Emotion: {emotion_profile.detected_emotion.value} "
            f"(confidence: {emotion_profile.confidence:.2f})"
        )
        print(
            f"   Triggers: {', '.join(emotion_profile.triggers) if emotion_profile.triggers else 'none'}"
        )
        print(f"   Interactions: {profile.interaction_count}")

        if profile.trust_indicators:
            print(f"   Trust indicators: {len(profile.trust_indicators)}")

    print(f"\n📈 Relationship Evolution Summary:")
    print("-" * 40)
    print(f"Final relationship level: {profile.relationship_level.value}")
    print(f"Total interactions: {profile.interaction_count}")
    print(f"Current emotion: {profile.current_emotion.value}")
    print(f"Escalation count: {profile.escalation_count}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    print("🔧 Graph Database Integration Test (ChromaDB-Safe)")
    print("=" * 70)

    # Run the fixed examples
    asyncio.run(example_conversation_fixed())
    asyncio.run(demonstrate_emotion_system_only())
