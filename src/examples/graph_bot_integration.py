"""Example integration of graph-enhanced memory manager with the main bot."""

import asyncio
import logging
from typing import Optional, Dict, Any, List

from src.memory.graph_enhanced_memory_manager import GraphEnhancedMemoryManager
from src.graph_database.neo4j_connector import get_neo4j_connector

logger = logging.getLogger(__name__)


class GraphEnhancedBot:
    """Example bot integration with graph database enhancement."""
    
    def __init__(self, llm_client=None):
        self.memory_manager = GraphEnhancedMemoryManager(llm_client=llm_client)
        self._system_prompt_base = self._load_base_system_prompt()
        
    def _load_base_system_prompt(self) -> str:
        """Load the base system prompt from file."""
        try:
            with open("prompts/default.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "You are a helpful AI assistant."
    
    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process a user message with graph-enhanced context."""
        
        try:
            # Get personalized context from graph database
            context = await self.memory_manager.get_personalized_context(
                user_id, message, limit=10
            )
            
            # Generate personalized system prompt
            personalized_prompt = await self.memory_manager.generate_personalized_system_prompt(
                user_id, message
            )
            
            # Combine base prompt with personalized elements
            full_system_prompt = self._build_system_prompt(
                base_prompt=self._system_prompt_base,
                personalized_prompt=personalized_prompt,
                context=context
            )
            
            # Simulate LLM response (replace with actual LLM call)
            response = await self._generate_response(message, full_system_prompt, context)
            
            # Store conversation with graph enhancement
            memory_id = await self.memory_manager.store_conversation_enhanced(
                user_id=user_id,
                message=message,
                response=response,
                emotion_data=self._detect_emotion(message),
                topics=await self._extract_topics(message)
            )
            
            return {
                "response": response,
                "memory_id": memory_id,
                "context_used": {
                    "chromadb_memories": len(context.get("chromadb_memories", [])),
                    "graph_memories": len(context.get("graph_context", {}).get("graph_memories", [])),
                    "relationship_intimacy": context.get("graph_context", {}).get("relationship_context", {}).get("intimacy_level", 0.3),
                    "personalized_prompt": bool(personalized_prompt)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message for {user_id}: {e}")
            # Fallback to basic response
            return {
                "response": "I'm sorry, I encountered an error processing your message.",
                "memory_id": None,
                "context_used": {},
                "error": str(e)
            }
    
    def _build_system_prompt(self, base_prompt: str, personalized_prompt: str, 
                           context: Dict[str, Any]) -> str:
        """Build complete system prompt with context."""
        
        prompt_parts = [base_prompt]
        
        # Add personalized relationship context
        if personalized_prompt:
            prompt_parts.append("\n=== RELATIONSHIP CONTEXT ===")
            prompt_parts.append(personalized_prompt)
        
        # Add recent relevant memories
        if context.get("graph_context", {}).get("graph_memories"):
            prompt_parts.append("\n=== RELEVANT MEMORIES ===")
            for memory in context["graph_context"]["graph_memories"][:5]:
                prompt_parts.append(f"- {memory.get('summary', '')}")
        
        # Add emotional context
        emotional_patterns = context.get("graph_context", {}).get("emotional_patterns", {})
        if emotional_patterns.get("triggers"):
            prompt_parts.append("\n=== EMOTIONAL CONTEXT ===")
            for trigger in emotional_patterns["triggers"][:3]:
                prompt_parts.append(
                    f"- Topic '{trigger['topic']}' often evokes {trigger['emotion']} "
                    f"(intensity: {trigger.get('avg_intensity', 0):.1f})"
                )
        
        return "\n".join(prompt_parts)
    
    async def _generate_response(self, message: str, system_prompt: str, 
                               context: Dict[str, Any]) -> str:
        """Generate response using LLM (replace with actual implementation)."""
        
        # This is a placeholder - replace with your actual LLM call
        relationship_level = context.get("graph_context", {}).get("relationship_context", {}).get("intimacy_level", 0.3)
        
        if relationship_level >= 0.8:
            tone = "warm and personal"
        elif relationship_level >= 0.5:
            tone = "friendly and familiar"
        else:
            tone = "helpful and professional"
        
        return f"[{tone} response] I understand your message about: {message[:50]}..."
    
    def _detect_emotion(self, message: str) -> Optional[Dict[str, Any]]:
        """Simple emotion detection (replace with actual emotion manager)."""
        
        message_lower = message.lower()
        
        # Simple keyword-based emotion detection
        if any(word in message_lower for word in ["happy", "great", "awesome", "love"]):
            return {"emotion": "happy", "intensity": 0.7, "context": "positive_keywords"}
        elif any(word in message_lower for word in ["sad", "upset", "angry", "frustrated"]):
            return {"emotion": "negative", "intensity": 0.6, "context": "negative_keywords"}
        elif any(word in message_lower for word in ["help", "confused", "don't understand"]):
            return {"emotion": "confused", "intensity": 0.5, "context": "help_seeking"}
        
        return {"emotion": "neutral", "intensity": 0.3, "context": "default"}
    
    async def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message."""
        # Reuse the topic extraction from the memory manager
        return await self.memory_manager._extract_topics_from_message(message)
    
    async def get_user_relationship_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a comprehensive relationship summary for a user."""
        
        try:
            graph_connector = await get_neo4j_connector()
            if not graph_connector:
                return {"status": "graph_unavailable"}
            
            # Get relationship context
            relationship_context = await graph_connector.get_user_relationship_context(user_id)
            emotional_patterns = await graph_connector.get_emotional_patterns(user_id)
            
            # Get recent conversations
            recent_memories = await graph_connector.get_contextual_memories(
                user_id, "general", limit=20
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "relationship_context": relationship_context,
                "emotional_patterns": emotional_patterns,
                "recent_memory_count": len(recent_memories),
                "summary": self._generate_relationship_summary(relationship_context, emotional_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting relationship summary for {user_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_relationship_summary(self, relationship_context: Dict, 
                                     emotional_patterns: Dict) -> str:
        """Generate human-readable relationship summary."""
        
        intimacy = relationship_context.get("intimacy_level", 0.3)
        memory_count = relationship_context.get("memory_count", 0)
        
        if intimacy >= 0.8:
            level = "very close"
        elif intimacy >= 0.6:
            level = "close"
        elif intimacy >= 0.4:
            level = "developing"
        else:
            level = "new"
        
        summary = f"This is a {level} relationship with {memory_count} shared conversations."
        
        # Add emotional context
        triggers = emotional_patterns.get("triggers", [])
        if triggers:
            common_emotions = [t["emotion"] for t in triggers[:3]]
            summary += f" Common emotional themes: {', '.join(common_emotions)}."
        
        return summary
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        
        health_status = {
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }
        
        # Check ChromaDB (through memory manager)
        try:
            # Test ChromaDB connection
            test_memories = await asyncio.get_event_loop().run_in_executor(
                None, self.memory_manager.retrieve_relevant_memories, 
                "test_user", "test message", 1
            )
            health_status["components"]["chromadb"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["chromadb"] = {"status": "error", "error": str(e)}
        
        # Check Neo4j
        graph_health = await self.memory_manager.get_graph_health_status()
        health_status["components"]["neo4j"] = graph_health
        
        # Overall status
        all_healthy = all(
            comp.get("status") in ["healthy", "disabled"] 
            for comp in health_status["components"].values()
        )
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_status


# Example usage function
async def example_usage():
    """Example of how to use the graph-enhanced bot."""
    
    print("🤖 Graph-Enhanced Bot Example")
    print("=" * 40)
    
    # Initialize bot
    bot = GraphEnhancedBot()
    
    # Health check
    health = await bot.health_check()
    print(f"Health Status: {health['overall_status']}")
    for component, status in health["components"].items():
        print(f"  {component}: {status['status']}")
    
    # Example conversation
    user_id = "example_user_123"
    
    messages = [
        "Hi, I'm John and I work as a software developer",
        "I'm feeling a bit stressed about my work project",
        "Do you remember what I do for work?",
        "I love programming in Python, it's my favorite language",
        "Can you help me with some coding advice?"
    ]
    
    print(f"\n💬 Example Conversation with User: {user_id}")
    print("-" * 40)
    
    for i, message in enumerate(messages, 1):
        print(f"\nMessage {i}: {message}")
        
        result = await bot.process_message(user_id, message)
        
        print(f"Response: {result['response']}")
        print(f"Context: {result['context_used']}")
        
        # Show relationship development
        if i % 2 == 0:  # Every other message
            summary = await bot.get_user_relationship_summary(user_id)
            if summary.get("status") == "success":
                print(f"Relationship: {summary['summary']}")
    
    print(f"\n📊 Final Relationship Summary")
    print("-" * 40)
    final_summary = await bot.get_user_relationship_summary(user_id)
    if final_summary.get("status") == "success":
        ctx = final_summary["relationship_context"]
        print(f"Intimacy Level: {ctx.get('intimacy_level', 0):.2f}")
        print(f"Total Memories: {ctx.get('memory_count', 0)}")
        print(f"Topics Discussed: {len(ctx.get('topics', []))}")
        print(f"Summary: {final_summary['summary']}")


if __name__ == "__main__":
    # To run this example:
    # 1. Start Docker containers: docker-compose up -d
    # 2. Run setup script: ./scripts/setup_neo4j.sh
    # 3. Run this example: python -m src.examples.graph_bot_integration
    
    asyncio.run(example_usage())
