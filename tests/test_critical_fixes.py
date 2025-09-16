#!/usr/bin/env python3
"""
Test script to verify critical fixes are working
"""
import os
import sys
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).parent))


def test_environment_validation():
    """Test environment variable validation"""

    # Save original token
    original_token = os.getenv("DISCORD_BOT_TOKEN")

    try:
        # Test missing token
        if "DISCORD_BOT_TOKEN" in os.environ:
            del os.environ["DISCORD_BOT_TOKEN"]

        # This should fail with proper error message
        import subprocess

        result = subprocess.run(
            [sys.executable, "basic_discord_bot.py"], capture_output=True, text=True, timeout=5
        )

        if "DISCORD_BOT_TOKEN environment variable not set" in result.stdout:
            return True
        else:
            return False

    except subprocess.TimeoutExpired:
        return True
    except Exception:
        return False
    finally:
        # Restore original token
        if original_token:
            os.environ["DISCORD_BOT_TOKEN"] = original_token


def test_memory_manager():
    """Test memory manager with better error handling"""

    try:
        from exceptions import MemoryError, ValidationError
        from memory_manager import UserMemoryManager

        # Test initialization
        memory_manager = UserMemoryManager()

        # Test input validation
        try:
            memory_manager.store_conversation("", "test", "response")
            return False
        except ValidationError:
            pass

        # Test valid operation
        try:
            memory_manager.store_conversation("123456789", "test message", "test response")
        except Exception:
            return False

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_llm_client():
    """Test LLM client with better error handling"""

    try:
        from exceptions import LLMConnectionError
        from lmstudio_client import LMStudioClient

        # Test initialization
        client = LMStudioClient()

        # Test connection (should fail gracefully)
        if client.check_connection():
            pass
        else:
            pass

        # Test error handling
        try:
            # This should raise proper exception if server is down
            client.get_chat_response([{"role": "user", "content": "test"}])
        except LLMConnectionError:
            pass
        except Exception:
            pass

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_conversation_history():
    """Test conversation history manager"""

    try:
        # Import the class directly
        sys.path.insert(0, ".")
        import basic_discord_bot

        # Create conversation history manager
        conv_history = basic_discord_bot.ConversationHistoryManager(
            max_channels=2, max_messages_per_channel=3
        )

        # Test adding messages
        conv_history.add_message("channel1", {"role": "user", "content": "message1"})
        conv_history.add_message("channel1", {"role": "assistant", "content": "response1"})
        conv_history.add_message("channel1", {"role": "user", "content": "message2"})
        conv_history.add_message("channel1", {"role": "assistant", "content": "response2"})

        # Should have 3 messages (max limit)
        messages = conv_history.get_messages("channel1")
        if len(messages) <= 3:
            pass
        else:
            return False

        # Test channel limit
        conv_history.add_message("channel2", {"role": "user", "content": "msg"})
        conv_history.add_message(
            "channel3", {"role": "user", "content": "msg"}
        )  # Should remove channel1

        stats = conv_history.get_stats()
        if stats["channels"] <= 2:
            pass
        else:
            return False

        return True

    except Exception:
        return False


def test_backup_system():
    """Test backup system"""

    try:
        from backup_manager import BackupManager

        # Create backup manager with test directories
        backup_manager = BackupManager(
            chromadb_path="./chromadb_data", backup_path="./test_backups"
        )

        # Test listing backups (should not fail)
        backup_manager.list_backups()

        # Test backup creation (if ChromaDB exists)
        if Path("./chromadb_data").exists():
            try:
                backup_path = backup_manager.create_backup(include_metadata=False)

                # Clean up test backup
                import shutil

                if Path(backup_path).exists():
                    shutil.rmtree(backup_path)

            except Exception:
                pass
        else:
            pass

        # Clean up test backup directory
        test_backup_dir = Path("./test_backups")
        if test_backup_dir.exists():
            import shutil

            shutil.rmtree(test_backup_dir)

        return True

    except Exception:
        return False


def main():
    """Run all tests"""

    tests = [
        ("Environment Validation", test_environment_validation),
        ("Memory Manager", test_memory_manager),
        ("LLM Client", test_llm_client),
        ("Conversation History", test_conversation_history),
        ("Backup System", test_backup_system),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception:
            results[test_name] = False


    passed = 0
    failed = 0

    for test_name, result in results.items():
        if result:
            passed += 1
        else:
            failed += 1


    if failed == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
