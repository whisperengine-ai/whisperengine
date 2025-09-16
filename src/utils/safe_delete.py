#!/usr/bin/env python3
"""
Safe deletion tool for user_profiles.db
Provides controlled ways to remove data with confirmations and backups
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from user_profile_db import UserProfileDatabase


class SafeUserDeletion:
    """Safe deletion operations with backups and confirmations"""

    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        self.db = UserProfileDatabase(db_path)

    def create_backup(self, suffix: Optional[str] = None) -> str:
        """Create a backup before any deletion operation"""
        if suffix is None:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = f"user_profiles_backup_{suffix}.db"
        shutil.copy2(self.db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path

    def preview_user_deletion(self, user_id: str) -> Dict:
        """Preview what would be deleted for a user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get user info
            user_cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = user_cursor.fetchone()

            if not user:
                return {"exists": False}

            # Get emotion count
            emotion_cursor = conn.execute(
                "SELECT COUNT(*) FROM emotion_history WHERE user_id = ?", (user_id,)
            )
            emotion_count = emotion_cursor.fetchone()[0]

            return {"exists": True, "user_data": dict(user), "emotion_count": emotion_count}

    def preview_cleanup(self, days: int) -> Dict:
        """Preview what would be deleted in cleanup operation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count, 
                       COUNT(DISTINCT user_id) as affected_users
                FROM emotion_history 
                WHERE timestamp < date('now', '-{} days')
            """.format(
                    days
                )
            )

            result = dict(cursor.fetchone())

            # Get sample of what would be deleted
            cursor = conn.execute(
                """
                SELECT user_id, detected_emotion, timestamp
                FROM emotion_history 
                WHERE timestamp < date('now', '-{} days')
                ORDER BY timestamp ASC
                LIMIT 10
            """.format(
                    days
                )
            )

            result["sample_records"] = [dict(row) for row in cursor.fetchall()]
            return result

    def safe_delete_user(self, user_id: str, auto_backup: bool = True) -> bool:
        """Safely delete a user with confirmation and backup"""
        # Preview deletion
        preview = self.preview_user_deletion(user_id)

        if not preview["exists"]:
            print(f"❌ User {user_id} does not exist")
            return False

        user_data = preview["user_data"]
        emotion_count = preview["emotion_count"]

        print(f"\n🔍 User Deletion Preview:")
        print(f"   User ID: {user_id}")
        print(f"   Name: {user_data.get('name', 'No name')}")
        print(f"   Relationship: {user_data.get('relationship_level', 'Unknown')}")
        print(f"   Interactions: {user_data.get('interaction_count', 0)}")
        print(f"   Emotion records: {emotion_count}")
        print(f"   First seen: {user_data.get('first_interaction', 'Unknown')}")
        print(f"   Last seen: {user_data.get('last_interaction', 'Unknown')}")

        # Confirmation
        confirm = input(
            f"\n⚠️  Delete ALL data for user {user_id}? (type 'DELETE {user_id}' to confirm): "
        )
        if confirm != f"DELETE {user_id}":
            print("❌ Deletion cancelled")
            return False

        # Create backup
        if auto_backup:
            backup_path = self.create_backup(f"before_delete_{user_id}")

        # Perform deletion
        try:
            self.db.delete_user_profile(user_id)
            print(f"✅ Successfully deleted user {user_id}")
            print(f"   - Deleted 1 user record")
            print(f"   - Deleted {emotion_count} emotion records")

            if auto_backup:
                print(f"   - Backup saved: {os.path.basename(backup_path)}")

            return True

        except Exception as e:
            print(f"❌ Error during deletion: {e}")
            return False

    def safe_cleanup_emotions(self, days: int, auto_backup: bool = True) -> bool:
        """Safely cleanup old emotion records with preview and backup"""
        # Preview cleanup
        preview = self.preview_cleanup(days)

        if preview["count"] == 0:
            print(f"ℹ️  No emotion records older than {days} days found")
            return True

        print(f"\n🔍 Cleanup Preview:")
        print(f"   Records to delete: {preview['count']}")
        print(f"   Users affected: {preview['affected_users']}")
        print(f"   Age threshold: {days} days")

        if preview["sample_records"]:
            print(f"\n📋 Sample records to be deleted:")
            for record in preview["sample_records"][:5]:
                print(
                    f"   • {record['user_id']}: {record['detected_emotion']} at {record['timestamp']}"
                )

            if len(preview["sample_records"]) > 5:
                print(f"   ... and {len(preview['sample_records']) - 5} more")

        # Confirmation
        confirm = input(
            f"\n⚠️  Delete {preview['count']} emotion records older than {days} days? (type 'YES' to confirm): "
        )
        if confirm != "YES":
            print("❌ Cleanup cancelled")
            return False

        # Create backup
        if auto_backup:
            backup_path = self.create_backup(f"before_cleanup_{days}days")

        # Perform cleanup
        try:
            deleted = self.db.cleanup_old_emotions(days)
            print(f"✅ Successfully cleaned up {deleted} emotion records")

            if auto_backup:
                print(f"   - Backup saved: {os.path.basename(backup_path)}")

            return True

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False

    def safe_reset_user(
        self, user_id: str, full_reset: bool = False, auto_backup: bool = True
    ) -> bool:
        """Safely reset a user profile with backup"""
        # Check if user exists
        preview = self.preview_user_deletion(user_id)

        if not preview["exists"]:
            print(f"❌ User {user_id} does not exist")
            return False

        user_data = preview["user_data"]
        emotion_count = preview["emotion_count"]

        reset_type = "complete" if full_reset else "partial (keep basic info)"

        print(f"\n🔍 User Reset Preview ({reset_type}):")
        print(f"   User ID: {user_id}")
        print(f"   Current interactions: {user_data.get('interaction_count', 0)}")
        print(f"   Current emotion: {user_data.get('current_emotion', 'unknown')}")
        print(f"   Emotion records to delete: {emotion_count}")

        if full_reset:
            print(f"   ⚠️  FULL RESET: All user data will be deleted")
        else:
            print(f"   ℹ️  PARTIAL RESET: Will keep user_id, name, first_interaction")

        # Confirmation
        confirm = input(f"\n⚠️  Reset user {user_id} ({reset_type})? (y/n): ")
        if confirm.lower() != "y":
            print("❌ Reset cancelled")
            return False

        # Create backup
        if auto_backup:
            backup_path = self.create_backup(f"before_reset_{user_id}")

        # Perform reset
        try:
            deleted = self.db.reset_user_profile(user_id, not full_reset)
            print(f"✅ Successfully reset user {user_id}")
            print(f"   - Deleted {deleted} emotion records")

            if full_reset:
                print(f"   - Deleted user record")
            else:
                print(f"   - Reset interaction/escalation counters")
                print(f"   - Reset current emotion to neutral")
                print(f"   - Cleared trust indicators")

            if auto_backup:
                print(f"   - Backup saved: {os.path.basename(backup_path)}")

            return True

        except Exception as e:
            print(f"❌ Error during reset: {e}")
            return False

    def list_backups(self):
        """List available backup files"""
        backups = []
        for file in os.listdir("."):
            if file.startswith("user_profiles_backup_") and file.endswith(".db"):
                stat = os.stat(file)
                backups.append(
                    {
                        "filename": file,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                    }
                )

        if backups:
            print("\n📁 Available Backups:")
            backups.sort(key=lambda x: x["modified"], reverse=True)
            for backup in backups:
                print(f"   • {backup['filename']} ({backup['size']:,} bytes, {backup['modified']})")
        else:
            print("📁 No backup files found")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()
    deleter = SafeUserDeletion()

    try:
        if command == "delete" and len(sys.argv) > 2:
            user_id = sys.argv[2]
            deleter.safe_delete_user(user_id)

        elif command == "cleanup" and len(sys.argv) > 2:
            days = int(sys.argv[2])
            deleter.safe_cleanup_emotions(days)

        elif command == "reset" and len(sys.argv) > 2:
            user_id = sys.argv[2]
            full_reset = len(sys.argv) > 3 and sys.argv[3].lower() == "full"
            deleter.safe_reset_user(user_id, full_reset)

        elif command == "preview" and len(sys.argv) > 3:
            subcommand = sys.argv[2].lower()

            if subcommand == "user":
                user_id = sys.argv[3]
                preview = deleter.preview_user_deletion(user_id)
                if preview["exists"]:
                    print(f"User {user_id} exists with {preview['emotion_count']} emotion records")
                else:
                    print(f"User {user_id} does not exist")

            elif subcommand == "cleanup":
                days = int(sys.argv[3])
                preview = deleter.preview_cleanup(days)
                print(
                    f"Would delete {preview['count']} records affecting {preview['affected_users']} users"
                )

        elif command == "backups":
            deleter.list_backups()

        else:
            print_help()

    except Exception as e:
        print(f"❌ Error: {e}")


def print_help():
    print(
        """
🗑️  Safe User Profile Deletion Tool

Usage:
  python safe_delete.py <command> [args]

Commands:
  delete <user_id>           - Safely delete all data for a user
  cleanup <days>             - Delete emotion records older than N days
  reset <user_id> [full]     - Reset user profile (partial or full)
  preview user <user_id>     - Preview what would be deleted for user
  preview cleanup <days>     - Preview what would be cleaned up
  backups                    - List available backup files

Features:
  ✅ Automatic backups before any deletion
  ✅ Preview operations before execution
  ✅ Confirmation prompts for safety
  ✅ Detailed logging of what was deleted

Examples:
  python safe_delete.py delete 123456789
  python safe_delete.py cleanup 60
  python safe_delete.py reset 672814231002939413
  python safe_delete.py reset 672814231002939413 full
  python safe_delete.py preview user 123456789
  python safe_delete.py preview cleanup 30
  python safe_delete.py backups
    """
    )


if __name__ == "__main__":
    main()
