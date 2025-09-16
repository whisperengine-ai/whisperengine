#!/usr/bin/env python3
"""
Safe deletion tool for user_profiles.db
Provides controlled ways to remove data with confirmations and backups
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime

from user_profile_db import UserProfileDatabase


class SafeUserDeletion:
    """Safe deletion operations with backups and confirmations"""

    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        self.db = UserProfileDatabase(db_path)

    def create_backup(self, suffix: str | None = None) -> str:
        """Create a backup before any deletion operation"""
        if suffix is None:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = f"user_profiles_backup_{suffix}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def preview_user_deletion(self, user_id: str) -> dict:
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

    def preview_cleanup(self, days: int) -> dict:
        """Preview what would be deleted in cleanup operation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"""
                SELECT COUNT(*) as count,
                       COUNT(DISTINCT user_id) as affected_users
                FROM emotion_history
                WHERE timestamp < date('now', '-{days} days')
            """
            )

            result = dict(cursor.fetchone())

            # Get sample of what would be deleted
            cursor = conn.execute(
                f"""
                SELECT user_id, detected_emotion, timestamp
                FROM emotion_history
                WHERE timestamp < date('now', '-{days} days')
                ORDER BY timestamp ASC
                LIMIT 10
            """
            )

            result["sample_records"] = [dict(row) for row in cursor.fetchall()]
            return result

    def safe_delete_user(self, user_id: str, auto_backup: bool = True) -> bool:
        """Safely delete a user with confirmation and backup"""
        # Preview deletion
        preview = self.preview_user_deletion(user_id)

        if not preview["exists"]:
            return False

        preview["user_data"]
        preview["emotion_count"]


        # Confirmation
        confirm = input(
            f"\n⚠️  Delete ALL data for user {user_id}? (type 'DELETE {user_id}' to confirm): "
        )
        if confirm != f"DELETE {user_id}":
            return False

        # Create backup
        if auto_backup:
            self.create_backup(f"before_delete_{user_id}")

        # Perform deletion
        try:
            self.db.delete_user_profile(user_id)

            if auto_backup:
                pass

            return True

        except Exception:
            return False

    def safe_cleanup_emotions(self, days: int, auto_backup: bool = True) -> bool:
        """Safely cleanup old emotion records with preview and backup"""
        # Preview cleanup
        preview = self.preview_cleanup(days)

        if preview["count"] == 0:
            return True


        if preview["sample_records"]:
            for _record in preview["sample_records"][:5]:
                pass

            if len(preview["sample_records"]) > 5:
                pass

        # Confirmation
        confirm = input(
            f"\n⚠️  Delete {preview['count']} emotion records older than {days} days? (type 'YES' to confirm): "
        )
        if confirm != "YES":
            return False

        # Create backup
        if auto_backup:
            self.create_backup(f"before_cleanup_{days}days")

        # Perform cleanup
        try:
            self.db.cleanup_old_emotions(days)

            if auto_backup:
                pass

            return True

        except Exception:
            return False

    def safe_reset_user(
        self, user_id: str, full_reset: bool = False, auto_backup: bool = True
    ) -> bool:
        """Safely reset a user profile with backup"""
        # Check if user exists
        preview = self.preview_user_deletion(user_id)

        if not preview["exists"]:
            return False

        preview["user_data"]
        preview["emotion_count"]

        reset_type = "complete" if full_reset else "partial (keep basic info)"


        if full_reset:
            pass
        else:
            pass

        # Confirmation
        confirm = input(f"\n⚠️  Reset user {user_id} ({reset_type})? (y/n): ")
        if confirm.lower() != "y":
            return False

        # Create backup
        if auto_backup:
            self.create_backup(f"before_reset_{user_id}")

        # Perform reset
        try:
            self.db.reset_user_profile(user_id, not full_reset)

            if full_reset:
                pass
            else:
                pass

            if auto_backup:
                pass

            return True

        except Exception:
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
            backups.sort(key=lambda x: x["modified"], reverse=True)
            for _backup in backups:
                pass
        else:
            pass


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
                    pass
                else:
                    pass

            elif subcommand == "cleanup":
                days = int(sys.argv[3])
                preview = deleter.preview_cleanup(days)

        elif command == "backups":
            deleter.list_backups()

        else:
            print_help()

    except Exception:
        pass


def print_help():
    pass


if __name__ == "__main__":
    main()
