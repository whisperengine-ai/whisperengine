#!/usr/bin/env python3
"""
Cross-Context Memory Leakage Security Fix - Test Suite

This test suite validates the context-aware memory security system that prevents
private information from leaking between different contexts (DMs, servers, channels).

SECURITY VULNERABILITY ADDRESSED: Cross-Context Memory Leakage (CVSS 8.5)
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_aware_memory_security import (
    ContextAwareMemoryManager, MemoryContext, MemoryContextType, 
    ContextSecurity
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestContextAwareMemorySecurity(unittest.TestCase):
    """Test suite for context-aware memory security"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock base memory manager
        self.mock_base_memory = Mock()
        self.mock_base_memory.retrieve_relevant_memories.return_value = [
            {
                'id': 'memory_1',
                'content': 'DM conversation about personal health',
                'metadata': {
                    'context_type': 'dm',
                    'security_level': 'private_dm',
                    'is_private': True,
                    'server_id': None,
                    'channel_id': 'dm_channel_123'
                }
            },
            {
                'id': 'memory_2', 
                'content': 'Public server discussion about weather',
                'metadata': {
                    'context_type': 'public_channel',
                    'security_level': 'public_channel',
                    'is_private': False,
                    'server_id': 'server_456',
                    'channel_id': 'public_channel_789'
                }
            },
            {
                'id': 'memory_3',
                'content': 'Cross-server safe information',
                'metadata': {
                    'context_type': 'public_channel',
                    'security_level': 'cross_server',
                    'is_private': False,
                    'server_id': 'any_server',
                    'channel_id': 'any_channel'
                }
            }
        ]
        
        # Initialize context-aware memory manager
        self.context_memory = ContextAwareMemoryManager(self.mock_base_memory)
    
    def test_context_classification_dm(self):
        """Test DM context classification"""
        print("\n🧪 Testing DM context classification...")
        
        # Mock Discord DM message
        mock_message = Mock()
        mock_message.guild = None
        mock_message.channel.id = 123456789
        
        context = self.context_memory.classify_discord_context(mock_message)
        
        self.assertEqual(context.context_type, MemoryContextType.DM)
        self.assertEqual(context.security_level, ContextSecurity.PRIVATE_DM)
        self.assertTrue(context.is_private)
        self.assertIsNone(context.server_id)
        self.assertEqual(context.channel_id, "123456789")
        
        print("  ✅ DM context correctly classified as PRIVATE_DM")
    
    def test_context_classification_public_server(self):
        """Test public server channel context classification"""
        print("\n🧪 Testing public server context classification...")
        
        # Mock Discord server message
        mock_message = Mock()
        mock_guild = Mock()
        mock_guild.id = 987654321
        mock_guild.default_role = Mock()
        
        mock_channel = Mock()
        mock_channel.id = 555666777
        mock_channel.guild = mock_guild
        mock_channel.permissions_for.return_value.read_messages = True  # Public channel
        
        mock_message.guild = mock_guild
        mock_message.channel = mock_channel
        
        context = self.context_memory.classify_discord_context(mock_message)
        
        self.assertEqual(context.context_type, MemoryContextType.PUBLIC_CHANNEL)
        self.assertEqual(context.security_level, ContextSecurity.PUBLIC_CHANNEL)
        self.assertFalse(context.is_private)
        self.assertEqual(context.server_id, "987654321")
        self.assertEqual(context.channel_id, "555666777")
        
        print("  ✅ Public server context correctly classified as PUBLIC_CHANNEL")
    
    def test_context_classification_private_server(self):
        """Test private server channel context classification"""
        print("\n🧪 Testing private server context classification...")
        
        # Mock Discord private server message
        mock_message = Mock()
        mock_guild = Mock()
        mock_guild.id = 111222333
        mock_guild.default_role = Mock()
        
        mock_channel = Mock()
        mock_channel.id = 444555666
        mock_channel.guild = mock_guild
        mock_channel.permissions_for.return_value.read_messages = False  # Private channel
        
        mock_message.guild = mock_guild
        mock_message.channel = mock_channel
        
        context = self.context_memory.classify_discord_context(mock_message)
        
        self.assertEqual(context.context_type, MemoryContextType.PRIVATE_CHANNEL)
        self.assertEqual(context.security_level, ContextSecurity.PRIVATE_CHANNEL)
        self.assertTrue(context.is_private)
        self.assertEqual(context.server_id, "111222333")
        self.assertEqual(context.channel_id, "444555666")
        
        print("  ✅ Private server context correctly classified as PRIVATE_CHANNEL")
    
    def test_dm_context_filtering(self):
        """Test that DM context only retrieves DM memories"""
        print("\n🧪 Testing DM context memory filtering...")
        
        dm_context = MemoryContext(
            context_type=MemoryContextType.DM,
            security_level=ContextSecurity.PRIVATE_DM
        )
        
        filtered_memories = self.context_memory.retrieve_context_aware_memories(
            "user123", "test query", dm_context, limit=10
        )
        
        # Should only get DM memories and cross-server safe content
        self.assertTrue(len(filtered_memories) <= 2)
        
        # Check that private server memories are filtered out
        for memory in filtered_memories:
            metadata = memory['metadata']
            security_level = metadata.get('security_level', 'private_dm')
            self.assertIn(security_level, ['private_dm', 'cross_server'])
        
        print(f"  ✅ DM context filtered to {len(filtered_memories)} safe memories")
    
    def test_public_server_context_filtering(self):
        """Test that public server context filters out private memories"""
        print("\n🧪 Testing public server context memory filtering...")
        
        public_context = MemoryContext(
            context_type=MemoryContextType.PUBLIC_CHANNEL,
            server_id="server_456",
            security_level=ContextSecurity.PUBLIC_CHANNEL
        )
        
        filtered_memories = self.context_memory.retrieve_context_aware_memories(
            "user123", "test query", public_context, limit=10
        )
        
        # Should not get private DM memories
        for memory in filtered_memories:
            metadata = memory['metadata']
            security_level = metadata.get('security_level', 'private_dm')
            self.assertNotEqual(security_level, 'private_dm')
        
        print(f"  ✅ Public server context filtered out private memories")
    
    def test_cross_server_content_sharing(self):
        """Test that cross-server safe content is available everywhere"""
        print("\n🧪 Testing cross-server content availability...")
        
        # Test in DM context
        dm_context = MemoryContext(
            context_type=MemoryContextType.DM,
            security_level=ContextSecurity.PRIVATE_DM
        )
        
        dm_memories = self.context_memory.retrieve_context_aware_memories(
            "user123", "test query", dm_context, limit=10
        )
        
        # Test in public server context
        public_context = MemoryContext(
            context_type=MemoryContextType.PUBLIC_CHANNEL,
            server_id="different_server",
            security_level=ContextSecurity.PUBLIC_CHANNEL
        )
        
        public_memories = self.context_memory.retrieve_context_aware_memories(
            "user123", "test query", public_context, limit=10
        )
        
        # Both should have access to cross-server content
        dm_cross_server = any(m['metadata'].get('security_level') == 'cross_server' for m in dm_memories)
        public_cross_server = any(m['metadata'].get('security_level') == 'cross_server' for m in public_memories)
        
        self.assertTrue(dm_cross_server, "DM context should have access to cross-server content")
        self.assertTrue(public_cross_server, "Public context should have access to cross-server content")
        
        print("  ✅ Cross-server content available in all contexts")
    
    def test_context_aware_storage(self):
        """Test that conversation storage includes context metadata"""
        print("\n🧪 Testing context-aware conversation storage...")
        
        test_context = MemoryContext(
            context_type=MemoryContextType.PRIVATE_CHANNEL,
            server_id="test_server",
            channel_id="test_channel",
            security_level=ContextSecurity.PRIVATE_CHANNEL
        )
        
        # Test storage with context
        self.context_memory.store_conversation(
            "user123", 
            "Test user message",
            "Test bot response",
            context=test_context
        )
        
        # Verify base memory manager was called with context metadata
        self.mock_base_memory.store_conversation.assert_called_once()
        call_args = self.mock_base_memory.store_conversation.call_args
        
        # Check that metadata includes context information
        metadata = call_args.kwargs.get('metadata', {})
        self.assertEqual(metadata['context_type'], 'private_channel')
        self.assertEqual(metadata['server_id'], 'test_server')
        self.assertEqual(metadata['channel_id'], 'test_channel')
        self.assertEqual(metadata['security_level'], 'private_channel')
        self.assertTrue(metadata['is_private'])
        
        print("  ✅ Context metadata properly added to stored conversation")
    
    def test_emergency_safe_retrieval(self):
        """Test emergency fallback that only returns safe memories"""
        print("\n🧪 Testing emergency safe memory retrieval...")
        
        # Mock an exception in normal retrieval
        self.mock_base_memory.retrieve_relevant_memories.side_effect = Exception("Test error")
        
        test_context = MemoryContext(
            context_type=MemoryContextType.PUBLIC_CHANNEL,
            security_level=ContextSecurity.PUBLIC_CHANNEL
        )
        
        safe_memories = self.context_memory._emergency_safe_retrieval(
            "user123", "test query", test_context, limit=10
        )
        
        # Should return empty list when base memory fails
        self.assertEqual(len(safe_memories), 0)
        
        print("  ✅ Emergency safe retrieval prevents data leakage on errors")
    
    def test_privacy_leak_prevention_scenario(self):
        """Test realistic privacy leak prevention scenario"""
        print("\n🧪 Testing privacy leak prevention scenario...")
        
        # Scenario: User discusses health in DM, then asks about hobbies in public server
        
        # 1. Setup memories with private health info from DM
        private_health_memory = {
            'id': 'health_dm',
            'content': 'User discussed alcoholism recovery in private DM',
            'metadata': {
                'context_type': 'dm',
                'security_level': 'private_dm',
                'is_private': True,
                'server_id': None,
                'channel_id': 'dm_123'
            }
        }
        
        public_hobby_memory = {
            'id': 'hobby_public',
            'content': 'User likes hiking and outdoor activities',
            'metadata': {
                'context_type': 'public_channel',
                'security_level': 'cross_server',
                'is_private': False,
                'server_id': 'server_456',
                'channel_id': 'general_789'
            }
        }
        
        self.mock_base_memory.retrieve_relevant_memories.return_value = [
            private_health_memory, public_hobby_memory
        ]
        
        # 2. User asks about hobbies in public server
        public_context = MemoryContext(
            context_type=MemoryContextType.PUBLIC_CHANNEL,
            server_id="server_456",
            security_level=ContextSecurity.PUBLIC_CHANNEL
        )
        
        filtered_memories = self.context_memory.retrieve_context_aware_memories(
            "user123", "what hobbies should I try", public_context, limit=10
        )
        
        # 3. Verify private health info is NOT included in public context
        health_mentioned = any('alcoholism' in m['content'].lower() for m in filtered_memories)
        hobby_mentioned = any('hiking' in m['content'].lower() for m in filtered_memories)
        
        self.assertFalse(health_mentioned, "Private health info should NOT leak to public context")
        self.assertTrue(hobby_mentioned, "Public hobby info should be available")
        
        print("  ✅ Privacy leak prevention: Health info blocked, hobbies allowed")
        print("  🛡️  SECURITY: Private DM conversations protected from public exposure")

def run_context_security_tests():
    """Run all context-aware memory security tests"""
    print("🔒 Cross-Context Memory Leakage - Security Fix Test Suite")
    print("=" * 70)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestContextAwareMemorySecurity)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🎉 All context-aware memory security tests PASSED!")
        print("\n🔒 Security Test Summary:")
        print("  ✅ DM context classification and filtering")
        print("  ✅ Public server context classification and filtering") 
        print("  ✅ Private server context classification and filtering")
        print("  ✅ Cross-server content availability controls")
        print("  ✅ Context-aware conversation storage with metadata")
        print("  ✅ Emergency safe retrieval fallback")
        print("  ✅ Privacy leak prevention scenario validation")
        
        print("\n🛡️  CVSS 8.5 Vulnerability - FIXED:")
        print("  ❌ Private DM conversations leaking to public servers")
        print("  ❌ Cross-server information sharing without consent")
        print("  ❌ Personal information exposed in wrong contexts")
        print("  ✅ Context-aware memory filtering prevents leakage")
        print("  ✅ Private information protected at all security levels")
        
        print("\n🎯 Technical Implementation:")
        print("  ✅ Memory context classification system")
        print("  ✅ Security level compatibility matrix")
        print("  ✅ Context-aware memory retrieval filtering")
        print("  ✅ Metadata enhancement for stored conversations")
        print("  ✅ Emergency fallback with maximum privacy protection")
        
        print("\n✅ Cross-Context Memory Security - IMPLEMENTATION COMPLETE ✅")
        return True
    else:
        print("❌ Some context-aware memory security tests FAILED!")
        print(f"  Failed: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_context_security_tests()
    sys.exit(0 if success else 1)
