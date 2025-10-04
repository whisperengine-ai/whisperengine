#!/usr/bin/env python3
"""
Live Conversation Test Script
Tests real conversation flow with pauses to validate context preservation.

This script sends actual Discord messages to bots and validates that:
1. Context is maintained across multiple messages
2. Pauses between messages don't break conversation flow
3. Bot remembers previous messages in the conversation
4. Session timeout logic works correctly

Usage:
    python scripts/test_live_conversation.py --bot jake --user <discord_user_id>
    python scripts/test_live_conversation.py --bot elena --user <discord_user_id> --pause 30
"""

import asyncio
import os
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: This script requires Discord.py to send actual messages
# For now, we'll create a test plan that can be executed manually


class LiveConversationTester:
    """Tests conversation context with real Discord messages."""
    
    def __init__(self, bot_name: str, user_id: str = None, pause_seconds: int = 15):
        self.bot_name = bot_name.lower()
        self.user_id = user_id
        self.pause_seconds = pause_seconds
        self.test_results = []
        
    def generate_test_conversation(self) -> List[Dict[str, str]]:
        """Generate a test conversation that validates context preservation."""
        
        conversations = {
            "jake": [
                {
                    "message": "Hey Jake! I'm planning a trip to Iceland. Have you been there?",
                    "expected_context": ["iceland", "travel", "photography"],
                    "validates": "Initial context establishment"
                },
                {
                    "message": "What camera gear would you recommend for the Northern Lights?",
                    "expected_context": ["iceland", "northern lights", "camera", "photography"],
                    "validates": "Topic continuity (Iceland trip)"
                },
                {
                    "message": "How long should my exposure be?",
                    "expected_context": ["northern lights", "exposure", "photography", "iceland"],
                    "validates": "Conversation thread maintenance (Northern Lights photography)"
                },
                {
                    "message": "Thanks! By the way, what's your favorite location you've ever shot?",
                    "expected_context": ["photography", "location", "travel"],
                    "validates": "Topic shift while maintaining conversation context"
                },
                {
                    "message": "Did you use similar camera settings there as you mentioned for Iceland?",
                    "expected_context": ["iceland", "camera settings", "photography", "exposure"],
                    "validates": "Long-term context recall (referencing earlier Iceland discussion)"
                }
            ],
            "elena": [
                {
                    "message": "Elena, I saw a whale breaching today! It was incredible!",
                    "expected_context": ["whale", "ocean", "marine life"],
                    "validates": "Initial context establishment"
                },
                {
                    "message": "What species do you think it was? It had a tall dorsal fin.",
                    "expected_context": ["whale", "species", "dorsal fin", "identification"],
                    "validates": "Topic continuity (whale identification)"
                },
                {
                    "message": "How deep do they usually dive?",
                    "expected_context": ["whale", "diving", "depth", "behavior"],
                    "validates": "Conversation thread maintenance"
                },
                {
                    "message": "That's amazing! Do you ever worry about ocean pollution affecting them?",
                    "expected_context": ["whale", "ocean", "pollution", "conservation"],
                    "validates": "Topic expansion within same context"
                },
                {
                    "message": "What can I do to help protect the species we were talking about?",
                    "expected_context": ["whale", "conservation", "protection", "species"],
                    "validates": "Long-term context recall (referencing earlier whale discussion)"
                }
            ],
            "marcus": [
                {
                    "message": "Marcus, what do you think about GPT-4's architecture?",
                    "expected_context": ["gpt-4", "ai", "architecture", "llm"],
                    "validates": "Initial context establishment"
                },
                {
                    "message": "How does the attention mechanism actually work?",
                    "expected_context": ["attention", "mechanism", "gpt-4", "architecture"],
                    "validates": "Topic continuity (GPT-4 architecture)"
                },
                {
                    "message": "So is that similar to how transformers process tokens?",
                    "expected_context": ["transformers", "tokens", "attention", "gpt-4"],
                    "validates": "Conversation thread maintenance"
                },
                {
                    "message": "This is fascinating! How do you think AGI development is progressing?",
                    "expected_context": ["agi", "ai development", "progress"],
                    "validates": "Topic shift while maintaining technical context"
                },
                {
                    "message": "Would AGI use similar transformer architectures to what we discussed?",
                    "expected_context": ["agi", "transformers", "architecture", "gpt-4"],
                    "validates": "Long-term context recall (referencing earlier architecture discussion)"
                }
            ],
            "default": [
                {
                    "message": f"Hi {self.bot_name.title()}! How are you today?",
                    "expected_context": ["greeting", "conversation start"],
                    "validates": "Initial context establishment"
                },
                {
                    "message": "I wanted to ask about your interests.",
                    "expected_context": ["interests", "personal", "conversation"],
                    "validates": "Topic continuity"
                },
                {
                    "message": "That's interesting! Tell me more about that.",
                    "expected_context": ["interests", "elaboration", "conversation"],
                    "validates": "Conversation thread maintenance"
                },
                {
                    "message": "By the way, what do you usually do on weekends?",
                    "expected_context": ["weekends", "activities", "personal"],
                    "validates": "Topic shift within conversation"
                },
                {
                    "message": "Does that relate to what you mentioned earlier about your interests?",
                    "expected_context": ["interests", "activities", "connection"],
                    "validates": "Long-term context recall"
                }
            ]
        }
        
        return conversations.get(self.bot_name, conversations["default"])
    
    def print_test_plan(self):
        """Print a manual test plan for Discord testing."""
        
        conversation = self.generate_test_conversation()
        
        print("\n" + "="*70)
        print(f"LIVE CONVERSATION TEST PLAN: {self.bot_name.upper()}")
        print("="*70)
        print(f"\n📋 Test Configuration:")
        print(f"   Bot: {self.bot_name}")
        print(f"   Pause between messages: {self.pause_seconds} seconds")
        print(f"   Total messages: {len(conversation)}")
        print(f"   Expected duration: ~{len(conversation) * self.pause_seconds / 60:.1f} minutes")
        
        print(f"\n🎯 Test Objectives:")
        print("   1. Validate conversation context preservation")
        print("   2. Ensure pauses don't break conversation flow")
        print("   3. Verify long-term context recall")
        print("   4. Test session timeout handling (15min keepalive)")
        
        print(f"\n📝 Manual Test Instructions:")
        print("   1. Open Discord and navigate to bot's channel")
        print("   2. Send each message below with the specified pause")
        print("   3. Verify bot response includes expected context")
        print("   4. Document any context loss or unexpected behavior")
        
        print(f"\n💬 Test Conversation:")
        print("-"*70)
        
        for i, turn in enumerate(conversation, 1):
            print(f"\n[Message {i}] (Wait {self.pause_seconds}s after previous)")
            print(f"📤 Send: \"{turn['message']}\"")
            print(f"\n   ✅ Expected Context: {', '.join(turn['expected_context'])}")
            print(f"   🎯 Validates: {turn['validates']}")
            
            if i < len(conversation):
                print(f"\n   ⏰ PAUSE {self.pause_seconds} seconds before next message...")
            
            print("-"*70)
        
        print(f"\n🔍 Validation Checklist:")
        print("   □ Bot referenced Iceland/whale/GPT-4 context in later messages")
        print("   □ Bot maintained conversation thread throughout")
        print("   □ No 'reset' behavior or loss of context")
        print("   □ Bot responded appropriately to topic shifts")
        print("   □ Bot recalled earlier conversation details when asked")
        print("   □ Session stayed alive during pauses (15min keepalive)")
        
        print(f"\n⚠️  Failure Indicators:")
        print("   ✗ Bot asks 'What are you referring to?'")
        print("   ✗ Bot forgets earlier topics (e.g., Iceland, whale species)")
        print("   ✗ Bot treats each message as fresh conversation")
        print("   ✗ Bot doesn't connect current message to previous context")
        
        print(f"\n📊 After Test:")
        print("   1. Check vector memory for conversation history")
        print("   2. Verify all 5 messages stored with correct roles")
        print("   3. Run: python scripts/validate_conversation_context.py --bot {self.bot_name}")
        
        print("\n" + "="*70)
        print(f"🚀 Ready to test? Send messages in Discord with {self.pause_seconds}s pauses!")
        print("="*70 + "\n")
    
    def generate_validation_commands(self):
        """Generate commands to validate conversation after test."""
        
        print(f"\n📋 Post-Test Validation Commands:")
        print("-"*70)
        print(f"\n# 1. Validate conversation context system")
        print(f"python scripts/validate_conversation_context.py --bot {self.bot_name} --verbose")
        
        print(f"\n# 2. Check recent conversation memories in Qdrant")
        print(f"# (Run this in Python shell)")
        print(f"""
from qdrant_client import QdrantClient
from datetime import datetime, timedelta

client = QdrantClient(host='localhost', port=6334)
collection = 'whisperengine_memory_{self.bot_name}_7d'

# Get last 10 conversation memories
result = client.scroll(
    collection_name=collection,
    scroll_filter={{
        "must": [
            {{"key": "memory_type", "match": {{"value": "conversation"}}}},
            {{"key": "bot_name", "match": {{"value": "{self.bot_name}"}}}}
        ]
    }},
    limit=10,
    with_payload=True
)

for point in result[0]:
    print(f"Role: {{point.payload['role']}} | Content: {{point.payload['content'][:80]}}...")
""")
        
        print(f"\n# 3. Check bot logs for context processing")
        print(f"docker logs whisperengine-{self.bot_name}-bot --tail 50 | grep -i 'context\\|memory\\|conversation'")
        
        print("\n" + "-"*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate live conversation test plan for WhisperEngine bots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_live_conversation.py --bot jake
  python scripts/test_live_conversation.py --bot elena --pause 30
  python scripts/test_live_conversation.py --bot marcus --pause 60
  
This script generates a test plan for manual Discord testing.
Send each message with the specified pause to validate context preservation.
        """
    )
    
    parser.add_argument(
        '--bot',
        type=str,
        required=True,
        help='Bot name to test (e.g., jake, elena, marcus)'
    )
    
    parser.add_argument(
        '--user',
        type=str,
        help='Discord user ID (optional, for documentation)'
    )
    
    parser.add_argument(
        '--pause',
        type=int,
        default=15,
        help='Seconds to pause between messages (default: 15, tests keepalive)'
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = LiveConversationTester(
        bot_name=args.bot,
        user_id=args.user,
        pause_seconds=args.pause
    )
    
    # Print test plan
    tester.print_test_plan()
    
    # Print validation commands
    tester.generate_validation_commands()


if __name__ == "__main__":
    main()
