#!/usr/bin/env python3
"""
Tool to update user names in the profile database
This helps fix missing names from existing user profiles
"""

import sys
import logging
from user_profile_db import UserProfileDatabase
from query_profiles import UserProfileQuery

logger = logging.getLogger(__name__)

class UserNameUpdater:
    """Tool to update user names in profiles"""
    
    def __init__(self, db_path: str = "user_profiles.db"):
        self.db = UserProfileDatabase(db_path)
        self.query = UserProfileQuery(db_path)
    
    def update_user_name(self, user_id: str, name: str) -> bool:
        """Update name for a specific user"""
        success = self.db.update_user_name(user_id, name)
        if success:
            print(f"✅ Updated name for {user_id}: '{name}'")
        else:
            print(f"ℹ️  No update needed for {user_id}")
        return success
    
    def list_users_without_names(self):
        """List users that don't have names set"""
        users = self.query.get_all_users()
        unnamed_users = [user for user in users if not user.get('name')]
        
        if unnamed_users:
            print(f"\n👤 Users without names ({len(unnamed_users)}):")
            for user in unnamed_users:
                print(f"   • {user['user_id']} - {user['interaction_count']} interactions")
        else:
            print("\n✅ All users have names set!")
        
        return unnamed_users
    
    def update_names_from_discord_facts(self):
        """Try to extract names from Discord facts stored in ChromaDB"""
        try:
            import sqlite3
            
            # Query ChromaDB for user identification facts
            chromadb_path = "chromadb_data/chroma.sqlite3"
            
            with sqlite3.connect(chromadb_path) as conn:
                cursor = conn.execute("""
                    SELECT document, metadata 
                    FROM embeddings 
                    WHERE document LIKE '%Discord user%' 
                    OR document LIKE '%display name%'
                    OR metadata LIKE '%user_id%'
                """)
                
                updates = 0
                for document, metadata in cursor.fetchall():
                    print(f"Found: {document}")
                    # TODO: Parse and extract user ID and name mappings
                    # This would require more complex parsing
                
                print(f"Found {updates} potential name updates from ChromaDB")
                
        except Exception as e:
            print(f"❌ Could not access ChromaDB: {e}")
            return False
    
    def interactive_name_update(self):
        """Interactive mode to manually update user names"""
        unnamed_users = self.list_users_without_names()
        
        if not unnamed_users:
            return
        
        print(f"\n🔧 Interactive Name Update Mode")
        print("Enter names for users (press Enter to skip):")
        
        for user in unnamed_users:
            user_id = user['user_id']
            interactions = user['interaction_count']
            
            # Show some context about the user
            user_details = self.query.get_user_details(user_id) 
            if user_details and user_details.get('recent_emotions'):
                recent_emotion = user_details['recent_emotions'][0]['detected_emotion']
                print(f"\n👤 User: {user_id}")
                print(f"   Interactions: {interactions}")
                print(f"   Recent emotion: {recent_emotion}")
                print(f"   Last seen: {user.get('last_interaction', 'Unknown')}")
            else:
                print(f"\n👤 User: {user_id} ({interactions} interactions)")
            
            name = input(f"   Enter name (or press Enter to skip): ").strip()
            
            if name:
                self.update_user_name(user_id, name)
            else:
                print(f"   ⏭️  Skipped {user_id}")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    updater = UserNameUpdater()
    
    try:
        if command == "list":
            updater.list_users_without_names()
            
        elif command == "update" and len(sys.argv) > 3:
            user_id = sys.argv[2]
            name = sys.argv[3]
            updater.update_user_name(user_id, name)
            
        elif command == "interactive":
            updater.interactive_name_update()
            
        elif command == "auto":
            updater.update_names_from_discord_facts()
            
        else:
            print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")

def print_help():
    print("""
👤 User Name Updater Tool

Usage:
  python update_names.py <command> [args]

Commands:
  list                           - List users without names
  update <user_id> <name>        - Set name for specific user
  interactive                    - Interactive mode to set names
  auto                           - Try to extract names from Discord facts

Examples:
  python update_names.py list
  python update_names.py update 672814231002939413 "MarkAnthony"
  python update_names.py interactive
  python update_names.py auto
    """)

if __name__ == "__main__":
    main()
