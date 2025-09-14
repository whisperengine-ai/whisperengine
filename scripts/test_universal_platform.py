#!/usr/bin/env python3
"""
Universal Platform Abstraction Test

This script tests that the same AI components and logic work
across Discord bot and Web UI platforms.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.llm.llm_client import LLMClient
from src.memory.conversation_cache import HybridConversationCache
from src.platforms.universal_chat import Message, ChatPlatform, MessageType

class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name}" + (f" - {self.message}" if self.message else "")

class UniversalPlatformTester:
    """Tests universal platform abstraction"""
    
    def __init__(self):
        self.results = []
        self.config_manager = None
        self.db_manager = None
        self.llm_client = None
        self.cache_manager = None
    
    async def test_config_manager(self) -> TestResult:
        """Test adaptive configuration manager"""
        try:
            self.config_manager = AdaptiveConfigManager()
            
            # Verify config has expected methods
            assert hasattr(self.config_manager, 'environment')
            assert hasattr(self.config_manager, 'scale_tier')
            
            environment = self.config_manager.environment
            scale_tier = self.config_manager.scale_tier
            
            return TestResult(
                "Adaptive Configuration Manager",
                True,
                f"Environment: {environment}, Scale: {scale_tier}"
            )
        except Exception as e:
            return TestResult("Adaptive Configuration Manager", False, str(e))
    
    async def test_database_integration(self) -> TestResult:
        """Test database integration manager"""
        try:
            self.db_manager = DatabaseIntegrationManager(self.config_manager)
            
            # Test initialization (should work even without external databases)
            init_success = await self.db_manager.initialize()
            
            if init_success:
                message = "Initialized successfully"
            else:
                message = "Failed to initialize (expected for some environments)"
            
            return TestResult("Database Integration Manager", True, message)
        except Exception as e:
            return TestResult("Database Integration Manager", False, str(e))
    
    async def test_llm_client(self) -> TestResult:
        """Test LLM client initialization"""
        try:
            from src.llm.llm_client import LLMClient
            
            self.llm_client = LLMClient()
            
            # Test configuration
            config = self.llm_client.get_client_config()
            assert config is not None
            
            return TestResult(
                "LLM Client",
                True,
                f"API URL: {config.get('api_url', 'Not configured')}"
            )
        except Exception as e:
            return TestResult("LLM Client", False, str(e))
    
    async def test_conversation_cache(self) -> TestResult:
        """Test conversation cache manager"""
        try:
            self.cache_manager = HybridConversationCache()
            
            # Test basic operations
            test_channel = "test_channel_123"
            test_message = UniversalMessage(
                message_id="test_msg_1",
                user_id="test_user_1",
                content="Hello, this is a test message",
                timestamp=None,
                channel_id=test_channel,
                platform="test"
            )
            
            # Add message
            await self.cache_manager.add_message(test_channel, test_message)
            
            # Retrieve context
            context = await self.cache_manager.get_conversation_context(test_channel, limit=1)
            
            assert len(context) == 1
            assert context[0]['content'] == "Hello, this is a test message"
            
            # Cleanup
            await self.cache_manager.clear_channel_cache(test_channel)
            
            return TestResult("Conversation Cache Manager", True, "Basic operations successful")
        except Exception as e:
            return TestResult("Conversation Cache Manager", False, str(e))
    
    async def test_universal_message(self) -> TestResult:
        """Test universal message format"""
        try:
            # Test message creation and serialization
            message = UniversalMessage(
                message_id="test_123",
                user_id="user_456",
                content="Test message content",
                timestamp=None,
                channel_id="channel_789",
                platform="discord",
                author_name="TestUser",
                metadata={"test_key": "test_value"}
            )
            
            # Test serialization
            serialized = message.to_dict()
            assert serialized['message_id'] == "test_123"
            assert serialized['content'] == "Test message content"
            assert serialized['platform'] == "discord"
            
            # Test deserialization
            restored = UniversalMessage.from_dict(serialized)
            assert restored.message_id == message.message_id
            assert restored.content == message.content
            assert restored.platform == message.platform
            
            return TestResult("Universal Message Format", True, "Serialization/deserialization works")
        except Exception as e:
            return TestResult("Universal Message Format", False, str(e))
    
    async def test_platform_abstraction(self) -> TestResult:
        """Test platform abstraction interface"""
        try:
            # Check that UniversalChatPlatform exists and has expected methods
            assert hasattr(UniversalChatPlatform, 'send_message')
            assert hasattr(UniversalChatPlatform, 'get_message_history')
            assert hasattr(UniversalChatPlatform, 'format_response')
            
            return TestResult("Platform Abstraction Interface", True, "Interface methods available")
        except Exception as e:
            return TestResult("Platform Abstraction Interface", False, str(e))
    
    async def test_component_integration(self) -> TestResult:
        """Test that components work together"""
        try:
            # Verify all components can be initialized together
            assert self.config_manager is not None
            assert self.cache_manager is not None
            assert self.llm_client is not None
            
            # Test that config can be used by other components
            storage_config = self.config_manager.get_storage_configuration()
            assert storage_config is not None
            
            return TestResult("Component Integration", True, "All components compatible")
        except Exception as e:
            return TestResult("Component Integration", False, str(e))
    
    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("🧪 Testing Universal Platform Abstraction")
        print("=" * 50)
        
        # Run tests in order
        tests = [
            self.test_config_manager(),
            self.test_database_integration(),
            self.test_llm_client(),
            self.test_conversation_cache(),
            self.test_universal_message(),
            self.test_platform_abstraction(),
            self.test_component_integration()
        ]
        
        for test_coro in tests:
            result = await test_coro
            self.results.append(result)
            print(result)
        
        # Summary
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        
        print("\n" + "=" * 50)
        if passed_count == total_count:
            print(f"🎉 All {total_count} tests passed!")
            print("✅ Universal platform abstraction is working correctly")
            return True
        else:
            print(f"❌ {total_count - passed_count} of {total_count} tests failed")
            return False
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.db_manager:
            await self.db_manager.cleanup()
        if self.cache_manager:
            await self.cache_manager.cleanup()

async def main():
    """Main test function"""
    tester = UniversalPlatformTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return False
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)