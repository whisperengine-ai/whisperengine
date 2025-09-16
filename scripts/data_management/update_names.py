#!/usr/bin/env python3
"""
Tool to update user names in the profile database
This helps fix missing names from existing user profiles
"""

import logging
import sys

from query_profiles import UserProfileQuery
from user_profile_db import UserProfileDatabase

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
            pass
        else:
            pass
        return success

    def list_users_without_names(self):
        """List users that don't have names set"""
        users = self.query.get_all_users()
        unnamed_users = [user for user in users if not user.get("name")]

        if unnamed_users:
            for _user in unnamed_users:
                pass
        else:
            pass

        return unnamed_users

    def update_names_from_discord_facts(self):
        """Try to extract names from Discord facts stored in ChromaDB"""
        try:
            import sqlite3

            # Query ChromaDB for user identification facts
            chromadb_path = "chromadb_data/chroma.sqlite3"

            with sqlite3.connect(chromadb_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT document, metadata
                    FROM embeddings
                    WHERE document LIKE '%Discord user%'
                    OR document LIKE '%display name%'
                    OR metadata LIKE '%user_id%'
                """
                )

                for _document, _metadata in cursor.fetchall():
                    pass
                    # TODO: Parse and extract user ID and name mappings
                    # This would require more complex parsing


        except Exception:
            return False

    def interactive_name_update(self):
        """Interactive mode to manually update user names"""
        unnamed_users = self.list_users_without_names()

        if not unnamed_users:
            return


        for user in unnamed_users:
            user_id = user["user_id"]
            user["interaction_count"]

            # Show some context about the user
            user_details = self.query.get_user_details(user_id)
            if user_details and user_details.get("recent_emotions"):
                user_details["recent_emotions"][0]["detected_emotion"]
            else:
                pass

            name = input("   Enter name (or press Enter to skip): ").strip()

            if name:
                self.update_user_name(user_id, name)
            else:
                pass


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

    except Exception:
        pass


def print_help():
    pass


if __name__ == "__main__":
    main()
