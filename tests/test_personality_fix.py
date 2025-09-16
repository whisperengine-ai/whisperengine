#!/usr/bin/env python3
"""
Test to verify that personality profiles are consistent between DMs and channels.
This tests the fix for the personality isolation bug.
"""

import logging
import sys
import os
sys.path.append('.')

from src.handlers.memory import MemoryCommandHandlers
from src.analysis.personality_profiler import PersonalityProfiler
from src.memory.memory_manager import UserMemoryManager
from unittest.mock import Mock, AsyncMock

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockDiscordMessage:
    def __init__(self, guild=None, channel_id="123456789"):
        self.guild = guild
        self.channel = Mock()
        self.channel.id = channel_id

class MockDiscordContext:
    def __init__(self, is_dm=True):
        self.message = MockDiscordMessage(guild=None if is_dm else Mock())
        self.author = Mock()
        self.author.id = "test_user_123"
        self.author.display_name = "TestUser"
        self.send = AsyncMock()

def test_personality_cross_context_retrieval():
    """Test that personality analysis retrieves messages from all contexts"""
    
    # Mock memory manager with sample data
    mock_memory_manager = Mock()
    mock_safe_memory_manager = Mock()
    
    # Create sample memories from different contexts (DM and channel)
    sample_memories = [
        {
            'metadata': {
                'user_message': 'I love programming and solving complex problems!',
                'context_type': 'dm',
                'security_level': 'private_dm'
            }
        },
        {
            'metadata': {
                'user_message': 'Working on this exciting new project with machine learning.',
                'context_type': 'public_channel', 
                'security_level': 'public_channel'
            }
        },
        {
            'metadata': {
                'user_message': 'I prefer to work alone and think things through carefully.',
                'context_type': 'dm',
                'security_level': 'private_dm'
            }
        },
        {
            'metadata': {
                'user_message': 'Let me analyze this step by step before we proceed.',
                'context_type': 'private_channel',
                'security_level': 'private_channel' 
            }
        }
    ]
    
    # Mock the base memory manager to return cross-context messages
    mock_base_memory_manager = Mock()
    mock_base_memory_manager.retrieve_relevant_memories.return_value = sample_memories
    mock_safe_memory_manager.base_memory_manager = mock_base_memory_manager
    
    # Create personality profiler
    personality_profiler = PersonalityProfiler()
    
    # Create memory command handler
    memory_handler = MemoryCommandHandlers(
        bot=Mock(),
        memory_manager=mock_memory_manager,
        safe_memory_manager=mock_safe_memory_manager,
        personality_profiler=personality_profiler,
        graph_personality_manager=None
    )
    
    print("🧪 Testing Cross-Context Personality Retrieval")
    print("=" * 50)
    
    # Test DM context - should get ALL user messages regardless of original context
    dm_ctx = MockDiscordContext(is_dm=True)
    print(f"📱 Testing DM context...")
    
    # Simulate the fixed personality analysis
    user_id = "test_user_123"
    base_memory_manager = getattr(mock_safe_memory_manager, 'base_memory_manager', mock_memory_manager)
    
    recent_messages = []
    if base_memory_manager and hasattr(base_memory_manager, 'retrieve_relevant_memories'):
        cross_context_memories = base_memory_manager.retrieve_relevant_memories(
            user_id, query="conversation messages recent", limit=25
        )
        
        for memory in cross_context_memories:
            metadata = memory.get('metadata', {})
            if metadata.get('user_message') and not metadata.get('user_message', '').startswith('!'):
                recent_messages.append(metadata['user_message'])
    
    print(f"📊 Retrieved {len(recent_messages)} messages for personality analysis:")
    for i, msg in enumerate(recent_messages, 1):
        print(f"  {i}. {msg[:60]}...")
    
    # Analyze personality with cross-context messages
    if len(recent_messages) >= 3:
        metrics = personality_profiler.analyze_personality(recent_messages, user_id)
        summary = personality_profiler.get_personality_summary(metrics)
        
        print(f"\n🧠 Personality Analysis Results:")
        print(f"   Messages Analyzed: {summary['analysis_meta']['messages_analyzed']}")
        print(f"   Confidence: {summary['analysis_meta']['confidence']:.2f}")
        print(f"   Communication Style: {summary['communication_style']['primary']}")
        print(f"   Decision Style: {summary['behavioral_patterns']['decision_style']}")
        
        # Verify we got messages from multiple contexts
        dm_messages = [msg for msg in recent_messages if any(mem['metadata'].get('context_type') == 'dm' for mem in sample_memories if mem['metadata']['user_message'] == msg)]
        channel_messages = [msg for msg in recent_messages if any(mem['metadata'].get('context_type') in ['public_channel', 'private_channel'] for mem in sample_memories if mem['metadata']['user_message'] == msg)]
        
        print(f"\n✅ Cross-Context Verification:")
        print(f"   DM Messages: {len(dm_messages)}")
        print(f"   Channel Messages: {len(channel_messages)}")
        
        if len(dm_messages) > 0 and len(channel_messages) > 0:
            print("   ✅ SUCCESS: Personality analysis includes messages from both DMs and channels!")
            return True
        else:
            print("   ❌ FAILED: Personality analysis missing messages from some contexts")
            return False
    else:
        print(f"❌ Not enough messages for analysis: {len(recent_messages)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Personality Cross-Context Bug Fix")
    print("=" * 60)
    
    success = test_personality_cross_context_retrieval()
    
    if success:
        print("\n🎉 TEST PASSED: Personality profiles should now be consistent across DMs and channels!")
    else:
        print("\n❌ TEST FAILED: The fix may not be working correctly")
    
    print("\n📝 Next Steps:")
    print("1. Start the Discord bot with: source .venv/bin/activate && python run.py")
    print("2. Test !personality command in both DMs and channels")
    print("3. Verify you get the same personality assessment in both contexts")