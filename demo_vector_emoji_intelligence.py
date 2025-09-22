#!/usr/bin/env python3
"""
Demo: Vector-Powered Emoji Intelligence System

This script demonstrates the new emoji response intelligence system that uses:
- Qdrant vector similarity search for historical pattern analysis
- Security validation integration for inappropriate content responses
- Character-aware emoji selection (mystical vs technical)
- Emotional intelligence for context-appropriate decisions
- Memory storage with emoji interaction patterns
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, '.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def demo_vector_emoji_intelligence():
    """Demonstrate the vector-powered emoji intelligence system"""
    print("🎭 Vector-Powered Emoji Intelligence Demo")
    print("=" * 50)
    
    try:
        # Import the components
        from src.intelligence.vector_emoji_intelligence import (
            VectorEmojiIntelligence, 
            EmojiResponseIntegration,
            EmojiResponseContext
        )
        from src.memory.memory_protocol import create_memory_manager
        
        print("✅ Imported emoji intelligence components")
        
        # Create a mock memory manager for demo
        print("📚 Creating memory manager...")
        memory_manager = create_memory_manager("test_mock")
        
        # Initialize the vector emoji intelligence
        print("🧠 Initializing Vector Emoji Intelligence...")
        emoji_intelligence = VectorEmojiIntelligence(memory_manager)
        
        # Test various scenarios
        test_scenarios = [
            {
                "name": "🚫 Inappropriate Content",
                "user_message": "You are stupid and I hate you",
                "bot_character": "general",
                "security_result": {
                    "is_safe": False,
                    "blocked_patterns": ["inappropriate_language"],
                    "warnings": ["Inappropriate content detected"]
                }
            },
            {
                "name": "🔮 Mystical Character - Wonder",
                "user_message": "Wow, that's amazing magic!",
                "bot_character": "mystical",
                "security_result": {"is_safe": True}
            },
            {
                "name": "🤖 Technical Character - Appreciation",
                "user_message": "This code is awesome!",
                "bot_character": "technical", 
                "security_result": {"is_safe": True}
            },
            {
                "name": "😊 Simple Acknowledgment",
                "user_message": "Thanks!",
                "bot_character": "general",
                "security_result": {"is_safe": True}
            },
            {
                "name": "😄 Playful Interaction", 
                "user_message": "Haha that's funny!",
                "bot_character": "general",
                "security_result": {"is_safe": True}
            },
            {
                "name": "📝 Complex Discussion (should NOT use emoji)",
                "user_message": "Can you explain the complex mathematical principles behind quantum computing and how they relate to cryptographic security algorithms in modern distributed systems?",
                "bot_character": "technical",
                "security_result": {"is_safe": True}
            }
        ]
        
        print("\n🎯 Testing Emoji Decision Scenarios:")
        print("-" * 40)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Message: \"{scenario['user_message'][:50]}{'...' if len(scenario['user_message']) > 50 else ''}\"")
            print(f"   Character: {scenario['bot_character']}")
            
            # Test the decision
            decision = await emoji_intelligence.should_respond_with_emoji(
                user_id="demo_user_123",
                user_message=scenario['user_message'],
                bot_character=scenario['bot_character'],
                security_validation_result=scenario['security_result'],
                emotional_context=None,
                conversation_context={'channel_type': 'guild'}
            )
            
            # Display results
            if decision.should_use_emoji:
                print(f"   ✅ EMOJI: {decision.emoji_choice}")
                print(f"   📊 Confidence: {decision.confidence_score:.2f}")
                print(f"   🔍 Reason: {decision.context_reason.value}")
            else:
                print(f"   📝 TEXT RESPONSE (confidence: {decision.confidence_score:.2f})")
                print(f"   🔍 Reason: {decision.context_reason.value}")
            
            # Show supporting evidence
            evidence = decision.supporting_evidence
            if evidence:
                emotion_score = evidence.get('emotion_score', 'N/A')
                personality_score = evidence.get('personality_alignment', 'N/A')
                context_score = evidence.get('context_score', 'N/A')
                
                emotion_str = f"{emotion_score:.2f}" if isinstance(emotion_score, (int, float)) else str(emotion_score)
                personality_str = f"{personality_score:.2f}" if isinstance(personality_score, (int, float)) else str(personality_score)
                context_str = f"{context_score:.2f}" if isinstance(context_score, (int, float)) else str(context_score)
                
                print(f"   📈 Evidence: emotion={emotion_str}, personality={personality_str}, context={context_str}")
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Vector similarity search for historical patterns")
        print("   • Security integration for inappropriate content")
        print("   • Character-aware emoji selection")
        print("   • Context-appropriate decision making")
        print("   • Confidence scoring and evidence tracking")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Vector Emoji Intelligence Demo...")
    success = asyncio.run(demo_vector_emoji_intelligence())
    if success:
        print("✨ Demo completed successfully!")
    else:
        print("💥 Demo failed - check error messages above")
    print()