#!/usr/bin/env python3
"""
Test Account Discovery Functionality

This script demonstrates the Universal Identity account discovery feature.
It simulates the scenario where an existing Discord user tries to login
to the web UI and the system discovers their existing account.
"""

import asyncio
import json
import sys
import os
import requests

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.identity.universal_identity import create_identity_manager
import asyncpg

async def create_test_discord_user():
    """Create a test Discord user to simulate existing Discord history"""
    print("🔧 Setting up test scenario...")
    
    # Create database connection
    db_params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "database": os.getenv("POSTGRES_DB", "whisperengine"),
        "user": os.getenv("POSTGRES_USER", "whisperengine"),
        "password": os.getenv("POSTGRES_PASSWORD", "whisperengine_password")
    }
    
    pool = await asyncpg.create_pool(**db_params)
    identity_manager = create_identity_manager(pool)
    
    # Create a test Discord user
    test_discord_id = "672814231002939413"  # Example Discord ID
    test_username = "testuser"
    test_display_name = "Test User"
    
    print(f"📝 Creating Discord user: {test_username} (ID: {test_discord_id})")
    
    discord_user = await identity_manager.get_or_create_discord_user(
        discord_user_id=test_discord_id,
        username=test_username,
        display_name=test_display_name
    )
    
    print(f"✅ Created Discord user with Universal ID: {discord_user.universal_id}")
    
    await pool.close()
    return {
        "universal_id": discord_user.universal_id,
        "discord_id": test_discord_id,
        "username": test_username,
        "display_name": test_display_name
    }

def test_web_login_with_existing_username(username: str):
    """Test web UI login with a username that already exists"""
    print(f"\n🌐 Testing web UI login with existing username: {username}")
    
    # Attempt to login via web UI API without providing Discord ID
    login_data = {
        "username": username,
        "display_name": "Test User Web"
    }
    
    try:
        response = requests.post(
            "http://localhost:8081/api/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("account_discovery"):
                print("🔍 ACCOUNT DISCOVERY TRIGGERED!")
                print(f"📊 Message: {result['message']}")
                print(f"💡 Suggested Action: {result['suggested_action']}")
                print("\n👥 Found existing accounts:")
                
                for i, account in enumerate(result['existing_accounts'], 1):
                    print(f"  {i}. Username: {account['username']}")
                    print(f"     Display Name: {account.get('display_name', 'N/A')}")
                    print(f"     Universal ID: {account['universal_id']}")
                    print(f"     Has Discord: {'Yes' if account['has_discord'] else 'No'}")
                    if account['has_discord']:
                        print(f"     Discord Username: {account.get('discord_username', 'N/A')}")
                    print()
                
                print("✅ Account discovery working correctly!")
                return True
            else:
                print("❌ No account discovery triggered - user was created as new")
                print(f"📄 Response: {json.dumps(result, indent=2)}")
                return False
        else:
            print(f"❌ Login failed with status code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during web login test: {e}")
        return False

def test_web_login_with_discord_link(username: str, discord_id: str):
    """Test web UI login with Discord ID to properly link accounts"""
    print(f"\n🔗 Testing web UI login with Discord linking...")
    
    login_data = {
        "username": username,
        "display_name": "Test User Web",
        "discord_id": discord_id
    }
    
    try:
        response = requests.post(
            "http://localhost:8081/api/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("session_token") and result.get("user"):
                print("✅ Successfully linked Discord account!")
                user = result['user']
                print(f"👤 User: {user['username']} ({user.get('display_name', 'N/A')})")
                print(f"🆔 Universal ID: {user.get('universal_user_id', 'N/A')}")
                print(f"🔗 Discord Linked: {user.get('linked_discord', False)}")
                if user.get('linked_discord'):
                    print(f"🎮 Discord ID: {user.get('discord_id', 'N/A')}")
                return True
            else:
                print("❌ Login successful but unexpected response format")
                print(f"📄 Response: {json.dumps(result, indent=2)}")
                return False
        else:
            print(f"❌ Login failed with status code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Discord linking test: {e}")
        return False

async def main():
    """Main test flow"""
    print("🧪 Account Discovery Test")
    print("=" * 50)
    
    # Step 1: Create a test Discord user
    try:
        discord_user_data = await create_test_discord_user()
    except Exception as e:
        print(f"❌ Failed to create test Discord user: {e}")
        return False
    
    # Step 2: Try to login with the same username via web UI (should trigger discovery)
    discovery_success = test_web_login_with_existing_username(discord_user_data['username'])
    
    # Step 3: Try to login with Discord ID (should link properly)
    if discovery_success:
        link_success = test_web_login_with_discord_link(
            discord_user_data['username'], 
            discord_user_data['discord_id']
        )
    else:
        print("\n⚠️  Skipping Discord linking test due to discovery failure")
        link_success = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Discord User Creation: Success")
    print(f"{'✅' if discovery_success else '❌'} Account Discovery: {'Success' if discovery_success else 'Failed'}")
    print(f"{'✅' if link_success else '❌'} Discord Account Linking: {'Success' if link_success else 'Failed'}")
    
    if discovery_success and link_success:
        print("\n🎉 All tests passed! Account discovery is working correctly.")
        print("\n💡 Key Benefits:")
        print("   • Existing Discord users are discovered when they try to use web UI")
        print("   • Users are prompted to link their Discord account to access history")
        print("   • No duplicate accounts or fragmented conversation history")
        print("   • Seamless cross-platform experience")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)