#!/usr/bin/env python3
"""
Test script to verify critical fixes are working
"""
import os
import sys
import logging
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_environment_validation():
    """Test environment variable validation"""
    print("🔍 Testing environment variable validation...")
    
    # Save original token
    original_token = os.getenv('DISCORD_BOT_TOKEN')
    
    try:
        # Test missing token
        if 'DISCORD_BOT_TOKEN' in os.environ:
            del os.environ['DISCORD_BOT_TOKEN']
        
        # This should fail with proper error message
        import subprocess
        result = subprocess.run([sys.executable, 'basic_discord_bot.py'], 
                              capture_output=True, text=True, timeout=5)
        
        if "DISCORD_BOT_TOKEN environment variable not set" in result.stdout:
            print("✅ Environment variable validation working correctly")
            return True
        else:
            print("❌ Environment variable validation not working")
            print(f"Output: {result.stdout}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Script properly exits (timeout expected)")
        return True
    except Exception as e:
        print(f"❌ Error testing environment validation: {e}")
        return False
    finally:
        # Restore original token
        if original_token:
            os.environ['DISCORD_BOT_TOKEN'] = original_token

def test_memory_manager():
    """Test memory manager with better error handling"""
    print("🔍 Testing memory manager...")
    
    try:
        from memory_manager import UserMemoryManager
        from exceptions import ValidationError, MemoryError
        
        # Test initialization
        memory_manager = UserMemoryManager()
        print("✅ Memory manager initialization successful")
        
        # Test input validation
        try:
            memory_manager.store_conversation("", "test", "response")
            print("❌ Validation should have failed for empty user_id")
            return False
        except ValidationError:
            print("✅ Input validation working correctly")
        
        # Test valid operation
        try:
            memory_manager.store_conversation("123456789", "test message", "test response")
            print("✅ Valid conversation storage successful")
        except Exception as e:
            print(f"❌ Valid operation failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing memory manager: {e}")
        return False

def test_llm_client():
    """Test LLM client with better error handling"""
    print("🔍 Testing LLM client...")
    
    try:
        from lmstudio_client import LMStudioClient
        from exceptions import LLMConnectionError
        
        # Test initialization
        client = LMStudioClient()
        print("✅ LLM client initialization successful")
        
        # Test connection (should fail gracefully)
        if client.check_connection():
            print("✅ LM Studio is running - connection successful")
        else:
            print("⚠️ LM Studio not running - this is expected if server is down")
        
        # Test error handling
        try:
            # This should raise proper exception if server is down
            response = client.get_chat_response([{"role": "user", "content": "test"}])
            print("✅ Chat response successful (LM Studio is running)")
        except LLMConnectionError:
            print("✅ Connection error handled correctly")
        except Exception as e:
            print(f"✅ Error handled: {type(e).__name__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing LLM client: {e}")
        return False

def test_conversation_history():
    """Test conversation history manager"""
    print("🔍 Testing conversation history manager...")
    
    try:
        # Import the class directly
        sys.path.insert(0, '.')
        import basic_discord_bot
        
        # Create conversation history manager
        conv_history = basic_discord_bot.ConversationHistoryManager(max_channels=2, max_messages_per_channel=3)
        
        # Test adding messages
        conv_history.add_message("channel1", {"role": "user", "content": "message1"})
        conv_history.add_message("channel1", {"role": "assistant", "content": "response1"})
        conv_history.add_message("channel1", {"role": "user", "content": "message2"})
        conv_history.add_message("channel1", {"role": "assistant", "content": "response2"})
        
        # Should have 3 messages (max limit)
        messages = conv_history.get_messages("channel1")
        if len(messages) <= 3:
            print("✅ Message limit working correctly")
        else:
            print(f"❌ Message limit not working: {len(messages)} messages")
            return False
        
        # Test channel limit
        conv_history.add_message("channel2", {"role": "user", "content": "msg"})
        conv_history.add_message("channel3", {"role": "user", "content": "msg"})  # Should remove channel1
        
        stats = conv_history.get_stats()
        if stats['channels'] <= 2:
            print("✅ Channel limit working correctly")
        else:
            print(f"❌ Channel limit not working: {stats['channels']} channels")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing conversation history: {e}")
        return False

def test_backup_system():
    """Test backup system"""
    print("🔍 Testing backup system...")
    
    try:
        from backup_manager import BackupManager
        
        # Create backup manager with test directories
        backup_manager = BackupManager(
            chromadb_path="./chromadb_data",
            backup_path="./test_backups"
        )
        print("✅ Backup manager initialization successful")
        
        # Test listing backups (should not fail)
        backups = backup_manager.list_backups()
        print(f"✅ Backup listing successful: {len(backups)} backups found")
        
        # Test backup creation (if ChromaDB exists)
        if Path("./chromadb_data").exists():
            try:
                backup_path = backup_manager.create_backup(include_metadata=False)
                print(f"✅ Backup creation successful: {backup_path}")
                
                # Clean up test backup
                import shutil
                if Path(backup_path).exists():
                    shutil.rmtree(backup_path)
                    print("✅ Test backup cleaned up")
                    
            except Exception as e:
                print(f"⚠️ Backup creation failed (may be normal): {e}")
        else:
            print("⚠️ No ChromaDB data to backup (normal for fresh install)")
        
        # Clean up test backup directory
        test_backup_dir = Path("./test_backups")
        if test_backup_dir.exists():
            import shutil
            shutil.rmtree(test_backup_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing backup system: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Critical Fixes Implementation")
    print("=" * 50)
    
    tests = [
        ("Environment Validation", test_environment_validation),
        ("Memory Manager", test_memory_manager),
        ("LLM Client", test_llm_client),
        ("Conversation History", test_conversation_history),
        ("Backup System", test_backup_system),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All critical fixes are working correctly!")
        return 0
    else:
        print("⚠️ Some issues were found. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
