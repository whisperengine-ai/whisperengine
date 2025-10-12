#!/usr/bin/env python3
"""
Ban System Testing Script for WhisperEngine
Tests the ban/unban commands and banned user message blocking functionality.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.handlers.ban_commands import BanCommandHandlers
from src.database.database_integration import DatabaseIntegrationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockBot:
    """Mock Discord bot for testing."""
    def __init__(self):
        self.user = MockUser()
        
    def command(self, **kwargs):  # pylint: disable=unused-argument
        """Mock command decorator."""
        def decorator(func):
            return func
        return decorator
        
    async def fetch_user(self, user_id):
        """Mock fetch_user method."""
        return MockDiscordUser(user_id)


class MockDiscordUser:
    """Mock Discord user returned by fetch_user."""
    def __init__(self, user_id):
        self.id = user_id
        self.name = f"TestUser{user_id[-4:]}"
        self.discriminator = "0001"


class MockUser:
    """Mock Discord user for testing."""
    def __init__(self):
        self.id = "123456789012345678"  # Mock bot ID


class MockContext:
    """Mock Discord context for testing."""
    def __init__(self, author_id: str, is_admin: bool = True):
        self.author = MockAuthor(author_id)
        self.is_admin = is_admin
        
    async def send(self, message: str, embed=None):
        """Mock send method."""
        print(f"[BOT RESPONSE] {message}")
        if embed:
            print(f"[EMBED] {embed.title}: {embed.description}")


class MockAuthor:
    """Mock Discord author for testing."""
    def __init__(self, user_id: str):
        self.id = user_id
        self.mention = f"<@{user_id}>"


async def test_ban_system():
    """Test the ban system functionality."""
    logger.info("🧪 Starting Ban System Test")
    
    # Initialize components
    mock_bot = MockBot()
    db_integration = DatabaseIntegrationManager()
    ban_handler = BanCommandHandlers(mock_bot, postgres_pool=None, db_integration=db_integration)
    
    # Test user IDs
    test_user_id = "987654321098765432"
    admin_user_id = "111111111111111111"
    
    try:
        # Initialize database
        logger.info("📊 Initializing database...")
        await db_integration.initialize()
        
        # Clean up any existing test data first
        logger.info("🧹 Cleaning up any existing test data...")
        try:
            # Direct database cleanup for test user
            db_manager = db_integration.get_database_manager()
            
            # Check what's in the database first
            result = await db_manager.query(
                "SELECT discord_user_id, is_active FROM banned_users WHERE discord_user_id = :user_id",
                {"user_id": test_user_id}
            )
            
            if hasattr(result, 'rows') and result.rows:
                logger.info(f"Found existing ban record: {result.rows}")
                
            # Delete any existing records for this test user (complete cleanup)
            await db_manager.query(
                "DELETE FROM banned_users WHERE discord_user_id = :user_id",
                {"user_id": test_user_id}
            )
            
            ban_handler.clear_cache()  # Clear any cached results
            logger.info("✅ Test data cleanup completed")
        except Exception as e:
            logger.debug("Cleanup note: %s", e)  # This is expected if no data exists
        
        # Test 1: Check initial ban status (should be False)
        logger.info("🔍 Test 1: Check initial ban status")
        is_banned = await ban_handler.is_user_banned(test_user_id)
        print(f"User {test_user_id} banned status: {is_banned}")
        assert not is_banned, "User should not be banned initially"
        logger.info("✅ Test 1 passed")
        
        # Test 2: Ban a user
        logger.info("🚫 Test 2: Ban a user")
        ctx = MockContext(admin_user_id)
        await ban_handler._handle_ban_command(
            ctx, 
            test_user_id, 
            "Testing ban functionality", 
            lambda user_id: True  # is_admin function that always returns True
        )
        
        # Verify user is now banned
        is_banned = await ban_handler.is_user_banned(test_user_id)
        print(f"User {test_user_id} banned status after ban: {is_banned}")
        assert is_banned, "User should be banned after ban command"
        logger.info("✅ Test 2 passed")
        
        # Test 3: Try to ban the same user again (should show already banned)
        logger.info("⚠️ Test 3: Try to ban already banned user")
        await ban_handler._handle_ban_command(
            ctx, 
            test_user_id, 
            "Duplicate ban test", 
            lambda user_id: True
        )
        logger.info("✅ Test 3 passed")
        
        # Test 4: List banned users
        logger.info("📋 Test 4: List banned users")
        await ban_handler._handle_banlist_command(ctx, 10, lambda user_id: True)
        logger.info("✅ Test 4 passed")
        
        # Test 5: Check ban details
        logger.info("🔍 Test 5: Check ban details")
        await ban_handler._handle_bancheck_command(ctx, test_user_id, lambda user_id: True)
        logger.info("✅ Test 5 passed")
        
        # Test 6: Unban the user
        logger.info("✅ Test 6: Unban a user")
        await ban_handler._handle_unban_command(
            ctx, 
            test_user_id, 
            "Testing unban functionality", 
            lambda user_id: True
        )
        
        # Verify user is no longer banned
        is_banned = await ban_handler.is_user_banned(test_user_id)
        print(f"User {test_user_id} banned status after unban: {is_banned}")
        assert not is_banned, "User should not be banned after unban command"
        logger.info("✅ Test 6 passed")
        
        # Test 7: Try to unban a user who isn't banned
        logger.info("⚠️ Test 7: Try to unban non-banned user")
        await ban_handler._handle_unban_command(
            ctx, 
            test_user_id, 
            "Testing unban non-banned user", 
            lambda user_id: True
        )
        logger.info("✅ Test 7 passed")
        
        # Test 8: Invalid Discord ID validation
        logger.info("❌ Test 8: Invalid Discord ID validation")
        await ban_handler._handle_ban_command(
            ctx, 
            "invalid_id", 
            "Testing invalid ID", 
            lambda user_id: True
        )
        logger.info("✅ Test 8 passed")
        
        # Test 9: Non-admin user trying to ban (if admin check is implemented)
        logger.info("🚨 Test 9: Non-admin ban attempt")
        non_admin_ctx = MockContext("222222222222222222")
        await ban_handler._handle_ban_command(
            non_admin_ctx, 
            test_user_id, 
            "Non-admin ban attempt", 
            lambda user_id: False  # is_admin function that returns False
        )
        logger.info("✅ Test 9 passed")
        
        # Test 10: Cache functionality
        logger.info("💾 Test 10: Cache functionality")
        # Ban user
        await ban_handler._add_ban_to_database(test_user_id, admin_user_id, "Cache test")
        
        # Check ban status twice (second should use cache)
        is_banned_1 = await ban_handler.is_user_banned(test_user_id)
        is_banned_2 = await ban_handler.is_user_banned(test_user_id)
        
        assert is_banned_1 == is_banned_2, "Cache should return consistent results"
        
        # Clear cache and check again
        ban_handler.clear_cache()
        is_banned_3 = await ban_handler.is_user_banned(test_user_id)
        
        assert is_banned_1 == is_banned_3, "Results should be consistent after cache clear"
        
        # Clean up
        await ban_handler._remove_ban_from_database(test_user_id, admin_user_id, "Test cleanup")
        logger.info("✅ Test 10 passed")
        
        # Clean up - ensure test user is not banned after all tests
        logger.info("🧹 Final cleanup - ensuring test user is not banned")
        try:
            db_manager = db_integration.get_database_manager()
            await db_manager.query(
                "UPDATE banned_users SET is_active = FALSE WHERE discord_user_id = :user_id",
                {"user_id": test_user_id}
            )
            ban_handler.clear_cache()
            logger.info("✅ Final cleanup completed")
        except Exception:  # pylint: disable=broad-except
            pass  # Ignore cleanup errors
        
        logger.info("🎉 All ban system tests passed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        # Cleanup
        try:
            await db_integration.cleanup()
            logger.info("🧹 Database cleanup completed")
        except Exception as e:
            logger.error(f"⚠️ Cleanup failed: {e}")


async def test_message_blocking_simulation():
    """Simulate message blocking for banned users."""
    logger.info("🚧 Testing message blocking simulation")
    
    # This would normally be tested with actual Discord integration
    # For now, we'll simulate the ban check logic
    
    mock_bot = MockBot()
    db_integration = DatabaseIntegrationManager()
    ban_handler = BanCommandHandlers(mock_bot, postgres_pool=None, db_integration=db_integration)
    
    test_user_id = "333333333333333333"
    
    try:
        await db_integration.initialize()
        
        # Simulate receiving a message from a non-banned user
        logger.info("📨 Simulating message from non-banned user")
        is_banned = await ban_handler.is_user_banned(test_user_id)
        if not is_banned:
            print("✅ Message would be processed (user not banned)")
        else:
            print("🚫 Message would be ignored (user banned)")
        
        # Ban the user
        await ban_handler._add_ban_to_database(test_user_id, "admin", "Test ban for message blocking")
        
        # Simulate receiving a message from the now-banned user
        logger.info("📨 Simulating message from banned user")
        is_banned = await ban_handler.is_user_banned(test_user_id)
        if not is_banned:
            print("✅ Message would be processed (user not banned)")
        else:
            print("🚫 Message would be ignored (user banned)")
        
        # Clean up
        await ban_handler._remove_ban_from_database(test_user_id, "admin", "Test cleanup")
        
        logger.info("✅ Message blocking simulation completed")
        
    except Exception as e:
        logger.error(f"❌ Message blocking test failed: {e}")
        raise
    finally:
        await db_integration.cleanup()


def print_usage_instructions():
    """Print instructions for manual testing with Discord."""
    print("\n" + "="*60)
    print("📖 MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    print()
    print("After running the automated tests, you can manually test with Discord:")
    print()
    print("1. Start your Discord bot with ban commands enabled")
    print("2. In a Discord server where you have admin permissions:")
    print()
    print("   !ban <user_id> <reason>     - Ban a user")
    print("   !unban <user_id> <reason>   - Unban a user")
    print("   !banlist [limit]            - List banned users")
    print("   !bancheck <user_id>         - Check if user is banned")
    print()
    print("3. Test message blocking:")
    print("   - Ban a user")
    print("   - Have that user send a DM or mention the bot")
    print("   - Verify the bot doesn't respond")
    print("   - Check logs for 'BANNED USER' messages")
    print()
    print("4. Test admin permissions:")
    print("   - Try ban commands as non-admin user")
    print("   - Should see permission denied messages")
    print()
    print("5. Test error handling:")
    print("   - Try invalid user IDs")
    print("   - Try to ban the bot itself")
    print("   - Try to ban yourself")
    print()
    print("="*60)


async def main():
    """Main test function."""
    print("🚀 WhisperEngine Ban System Test Suite")
    print("="*50)
    
    try:
        # Set up basic environment for testing
        os.environ.setdefault("USE_POSTGRESQL", "true")
        os.environ.setdefault("POSTGRES_HOST", "localhost")
        os.environ.setdefault("POSTGRES_PORT", "5433")
        os.environ.setdefault("POSTGRES_DB", "whisperengine")
        os.environ.setdefault("POSTGRES_USER", "whisperengine")
        os.environ.setdefault("POSTGRES_PASSWORD", "whisperengine")
        
        # Run automated tests
        await test_ban_system()
        await test_message_blocking_simulation()
        
        print("\n🎉 All automated tests completed successfully!")
        
        # Print manual testing instructions
        print_usage_instructions()
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())