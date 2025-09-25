#!/usr/bin/env python3
"""
Debug Sophia's Memory Amnesia Issue

This script investigates why Sophia "forgets" emotional states and previous conversations.
Checks for memory storage, retrieval, and bot name consistency issues.
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Set environment for localhost testing
os.environ.update({
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_PORT': '5433',
    'REDIS_HOST': 'localhost', 
    'REDIS_PORT': '6380',
    'QDRANT_HOST': 'localhost',
    'QDRANT_PORT': '6334',
    'DISCORD_BOT_NAME': 'Sophia Blake',  # Critical: ensure correct bot name
    'CDL_DEFAULT_CHARACTER': 'characters/examples/sophia-blake.json'
})

from src.memory.vector_memory_system import VectorMemorySystem
from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SophiaMemoryDiagnosticTool:
    """Diagnose Sophia's memory amnesia issues"""
    
    def __init__(self):
        self.test_user_id = "markanthony_test_user"  # Based on your Discord screenshots
        self.bot_name = "Sophia Blake"
        self.memory_manager = None
        
    async def initialize(self):
        """Initialize memory system"""
        try:
            self.memory_manager = create_memory_manager(memory_type="vector")
            logger.info("✅ Memory manager initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Memory initialization failed: {e}")
            return False
    
    async def analyze_memory_storage_issues(self):
        """Check for memory storage consistency issues"""
        print("\n🔍 ANALYZING MEMORY STORAGE ISSUES")
        print("=" * 60)
        
        # Check 1: Bot name consistency
        await self._check_bot_name_consistency()
        
        # Check 2: Recent memory storage
        await self._check_recent_memories()
        
        # Check 3: Emotional context storage
        await self._check_emotional_memory_storage()
        
        # Check 4: Memory retrieval patterns
        await self._check_memory_retrieval_patterns()
        
    async def _check_bot_name_consistency(self):
        """Check if bot name is consistent in memory storage"""
        print("\n📛 Bot Name Consistency Check:")
        
        current_bot_name = os.getenv('DISCORD_BOT_NAME', 'Unknown')
        print(f"Current DISCORD_BOT_NAME: '{current_bot_name}'")
        
        # Query memories and check bot names in metadata
        try:
            conversation_results = await self.memory_manager.search_memories(
                user_id=self.test_user_id,
                query="marketing harassment conversation",
                memory_types=["conversation"],
                limit=10
            )
            
            bot_names_found = set()
            for result in conversation_results.get("documents", []):
                metadata = result.get("metadata", {})
                bot_name = metadata.get("bot_name", "MISSING")
                bot_names_found.add(bot_name)
            
            print(f"Bot names found in memories: {list(bot_names_found)}")
            
            if len(bot_names_found) > 1:
                print(f"⚠️  INCONSISTENT BOT NAMES DETECTED: {bot_names_found}")
                print("This could cause memory retrieval failures!")
            elif current_bot_name not in bot_names_found:
                print(f"⚠️  CURRENT BOT NAME MISMATCH:")
                print(f"   Expected: '{current_bot_name}'")
                print(f"   Found in memories: {bot_names_found}")
            else:
                print("✅ Bot name consistency looks good")
                
        except Exception as e:
            print(f"❌ Error checking bot names: {e}")
    
    async def _check_recent_memories(self):
        """Check recent memories around the harassment conversation"""
        print("\n💭 Recent Memory Analysis:")
        
        try:
            # Search for harassment-related memories
            harassment_memories = await self.memory_manager.search_memories_with_qdrant_intelligence(
                user_id=self.test_user_id,
                query="harassment stop messaging me angry boundaries",
                memory_types=["conversation"],
                limit=20
            )
            
            print(f"Found {len(harassment_memories.get('documents', []))} harassment-related memories")
            
            # Search for post-amnesia memories  
            recent_memories = await self.memory_manager.search_memories_with_qdrant_intelligence(
                user_id=self.test_user_id,
                query="what do you remember about us",
                memory_types=["conversation"],
                limit=10
            )
            
            print(f"Found {len(recent_memories.get('documents', []))} recent 'remember us' memories")
            
            # Analyze timestamps if available
            all_memories = harassment_memories.get("documents", []) + recent_memories.get("documents", [])
            
            timestamps = []
            for memory in all_memories:
                metadata = memory.get("metadata", {})
                timestamp = metadata.get("timestamp")
                if timestamp:
                    timestamps.append(timestamp)
            
            if timestamps:
                timestamps.sort()
                print(f"Memory timestamps range: {timestamps[0]} to {timestamps[-1]}")
                
                # Check for gaps in memory
                timestamp_objects = []
                for ts in timestamps:
                    try:
                        if isinstance(ts, str):
                            # Handle different timestamp formats
                            if 'T' in ts:
                                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            else:
                                dt = datetime.fromisoformat(ts)
                            timestamp_objects.append(dt)
                    except Exception as e:
                        continue
                
                if len(timestamp_objects) > 1:
                    gaps = []
                    for i in range(1, len(timestamp_objects)):
                        gap = timestamp_objects[i] - timestamp_objects[i-1]
                        if gap > timedelta(hours=1):  # Significant gap
                            gaps.append(gap)
                    
                    if gaps:
                        print(f"⚠️  Found {len(gaps)} significant time gaps in memories")
                        print(f"   Largest gap: {max(gaps)}")
                    else:
                        print("✅ No significant memory gaps detected")
            
        except Exception as e:
            print(f"❌ Error analyzing recent memories: {e}")
    
    async def _check_emotional_memory_storage(self):
        """Check how emotional states are stored and retrieved"""
        print("\n😤 Emotional Memory Storage Analysis:")
        
        try:
            # Search for emotional context in memories
            emotional_memories = await self.memory_manager.search_memories_with_qdrant_intelligence(
                user_id=self.test_user_id,
                query="mad angry upset boundaries harassment",
                memory_types=["conversation", "emotional_state"],
                limit=15
            )
            
            emotional_metadata = []
            for memory in emotional_memories.get("documents", []):
                metadata = memory.get("metadata", {})
                
                # Extract emotional indicators
                emotional_fields = {k: v for k, v in metadata.items() if 'emotion' in k.lower()}
                if emotional_fields:
                    emotional_metadata.append(emotional_fields)
            
            print(f"Found {len(emotional_metadata)} memories with emotional metadata")
            
            if emotional_metadata:
                print("Sample emotional metadata:")
                for i, emotion_data in enumerate(emotional_metadata[:3]):
                    print(f"  Memory {i+1}: {emotion_data}")
            
            # Check if emotional states persist across conversations
            recent_emotional_query = await self.memory_manager.search_memories_with_qdrant_intelligence(
                user_id=self.test_user_id,
                query="feeling much better unwind office",
                memory_types=["conversation"],
                limit=5
            )
            
            print(f"Found {len(recent_emotional_query.get('documents', []))} recent 'feeling better' memories")
            
            # This suggests emotional state reset
            if len(emotional_memories.get("documents", [])) > 0 and len(recent_emotional_query.get("documents", [])) > 0:
                print("⚠️  EMOTIONAL STATE INCONSISTENCY DETECTED:")
                print("   Found both angry memories AND 'feeling better' memories")
                print("   This suggests emotional state isn't persisting properly")
            
        except Exception as e:
            print(f"❌ Error analyzing emotional memories: {e}")
    
    async def _check_memory_retrieval_patterns(self):
        """Check how memories are retrieved during conversations"""
        print("\n🔄 Memory Retrieval Pattern Analysis:")
        
        try:
            # Simulate what happens when Sophia responds to "still mad?"
            query = "still mad"
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.test_user_id,
                query=query,
                limit=10
            )
            
            print(f"Query: '{query}'")
            print(f"Retrieved {len(relevant_memories)} relevant memories")
            
            if relevant_memories:
                print("Top 3 retrieved memories:")
                for i, memory in enumerate(relevant_memories[:3]):
                    content = memory.get("content", "")[:100]
                    print(f"  {i+1}. {content}...")
                    
                # Check if angry memories are being retrieved
                angry_content = []
                for memory in relevant_memories:
                    content = memory.get("content", "").lower()
                    if any(word in content for word in ["angry", "mad", "upset", "harassment", "stop", "boundaries"]):
                        angry_content.append(content[:100])
                
                if angry_content:
                    print(f"✅ Found {len(angry_content)} angry memories in retrieval")
                else:
                    print("⚠️  NO ANGRY MEMORIES RETRIEVED for 'still mad' query")
                    print("   This could explain the amnesia!")
            
            # Test conversation history retrieval
            conversation_history = await self.memory_manager.get_conversation_history(
                user_id=self.test_user_id,
                limit=20
            )
            
            print(f"Conversation history: {len(conversation_history)} messages")
            
            if conversation_history:
                # Check for emotional continuity in recent conversations
                recent_topics = []
                for conv in conversation_history[-10:]:
                    content = conv.get("user_message", "") + " " + conv.get("bot_response", "")
                    recent_topics.append(content[:50])
                
                print("Recent conversation topics:")
                for i, topic in enumerate(recent_topics[-5:]):
                    print(f"  {i+1}. {topic}...")
            
        except Exception as e:
            print(f"❌ Error analyzing memory retrieval: {e}")
    
    async def simulate_memory_fix_test(self):
        """Test potential fixes for the amnesia issue"""
        print("\n🔧 TESTING POTENTIAL FIXES")
        print("=" * 60)
        
        # Test 1: Force store emotional context
        print("\n1. Testing explicit emotional context storage...")
        
        try:
            # Simulate storing an angry emotional state
            angry_context = {
                "emotional_state": "angry",
                "emotional_intensity": 0.9,
                "anger_reason": "harassment_boundaries",
                "anger_duration": "persistent",
                "emotional_memory_priority": "high"
            }
            
            test_storage = await self.memory_manager.store_conversation(
                user_id=self.test_user_id,
                user_message="Test: I'm still upset about the harassment",
                bot_response="Test: I understand you're still upset about being harassed",
                pre_analyzed_emotion_data=angry_context,
                channel_id="test_channel"
            )
            
            print(f"Emotional context storage test: {'✅ SUCCESS' if test_storage else '❌ FAILED'}")
            
        except Exception as e:
            print(f"❌ Emotional storage test failed: {e}")
        
        # Test 2: Retrieve with emotional query
        print("\n2. Testing emotional query retrieval...")
        
        try:
            emotional_query_results = await self.memory_manager.search_memories_with_qdrant_intelligence(
                user_id=self.test_user_id,
                query="angry upset harassment emotional state persistent",
                memory_types=["conversation"],
                limit=5
            )
            
            print(f"Emotional query retrieved: {len(emotional_query_results.get('documents', []))} memories")
            
        except Exception as e:
            print(f"❌ Emotional query test failed: {e}")
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        print("\n💡 RECOMMENDATIONS TO FIX SOPHIA'S AMNESIA")
        print("=" * 60)
        
        recommendations = [
            "1. BOT NAME CONSISTENCY: Ensure DISCORD_BOT_NAME is consistent in all memory operations",
            "2. EMOTIONAL STATE PERSISTENCE: Implement persistent emotional state tracking",
            "3. CONTEXT WINDOW: Increase conversation history context window beyond 5 messages", 
            "4. EMOTIONAL METADATA: Store emotional intensity and duration in memory metadata",
            "5. CHARACTER SWITCHING: Add safeguards to prevent memory clearing during character switches",
            "6. MEMORY RETRIEVAL: Improve semantic search to include emotional context words",
            "7. CONVERSATION THREADING: Implement conversation thread tracking to maintain context",
            "8. EMOTIONAL DECAY: Implement gradual emotional state decay rather than sudden resets"
        ]
        
        for rec in recommendations:
            print(f"  • {rec}")
        
        print("\n🔬 SUGGESTED NEXT STEPS:")
        print("  1. Run this diagnostic during/after emotional conversations")
        print("  2. Check memory storage immediately after 'angry' interactions")
        print("  3. Implement emotional state persistence system")
        print("  4. Test memory retrieval with emotional context queries")

async def main():
    """Run Sophia memory amnesia diagnostic"""
    
    print("🤖 SOPHIA MEMORY AMNESIA DIAGNOSTIC TOOL")
    print("=" * 60)
    print("Investigating why Sophia 'forgets' emotional states...")
    
    diagnostic = SophiaMemoryDiagnosticTool()
    
    # Initialize
    if not await diagnostic.initialize():
        print("❌ Failed to initialize - check if multi-bot infrastructure is running")
        return
    
    # Run diagnostics
    await diagnostic.analyze_memory_storage_issues()
    
    # Test fixes
    await diagnostic.simulate_memory_fix_test()
    
    # Generate recommendations
    diagnostic.generate_recommendations()
    
    print(f"\n🎯 SUMMARY:")
    print("Sophia's 'amnesia' is likely caused by:")
    print("  • Memory retrieval not including emotional context")
    print("  • Conversation history context window too small") 
    print("  • Emotional state not persisting between conversation sessions")
    print("  • Possible bot name inconsistencies in memory storage")
    
    print(f"\n📝 The fact that she was mad 'for more than a day' but then")
    print(f"   suddenly forgets suggests the memory system isn't retrieving")
    print(f"   emotional context properly when generating responses!")

if __name__ == "__main__":
    asyncio.run(main())