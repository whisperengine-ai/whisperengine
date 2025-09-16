#!/usr/bin/env python3
"""
Database query tool for user_profiles.db
Provides easy ways to view and query user profile data
"""

import json
import sqlite3
import sys


class UserProfileQuery:
    """Query tool for user profiles database"""

    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path

    def get_all_users(self) -> list[dict]:
        """Get all users with basic info"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT user_id, name, relationship_level, current_emotion,
                       interaction_count, escalation_count,
                       first_interaction, last_interaction
                FROM users
                ORDER BY last_interaction DESC
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_user_details(self, user_id: str) -> dict | None:
        """Get detailed info for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get user info
            cursor = conn.execute(
                """
                SELECT * FROM users WHERE user_id = ?
            """,
                (user_id,),
            )
            user = cursor.fetchone()

            if not user:
                return None

            # Get emotion history
            cursor = conn.execute(
                """
                SELECT detected_emotion, confidence, triggers, intensity, timestamp
                FROM emotion_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """,
                (user_id,),
            )

            emotions = []
            for row in cursor.fetchall():
                emotions.append(
                    {
                        "detected_emotion": row["detected_emotion"],
                        "confidence": row["confidence"],
                        "triggers": json.loads(row["triggers"]),
                        "intensity": row["intensity"],
                        "timestamp": row["timestamp"],
                    }
                )

            result = dict(user)
            result["recent_emotions"] = emotions
            result["trust_indicators"] = (
                json.loads(user["trust_indicators"]) if user["trust_indicators"] else []
            )

            return result

    def get_emotion_stats(self) -> dict:
        """Get emotion statistics across all users"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT detected_emotion, COUNT(*) as count,
                       AVG(confidence) as avg_confidence,
                       AVG(intensity) as avg_intensity
                FROM emotion_history
                GROUP BY detected_emotion
                ORDER BY count DESC
            """
            )

            emotions = []
            for row in cursor.fetchall():
                emotions.append(
                    {
                        "emotion": row[0],
                        "count": row[1],
                        "avg_confidence": round(row[2], 3),
                        "avg_intensity": round(row[3], 3),
                    }
                )

            return {"emotion_breakdown": emotions}

    def get_active_users(self, days: int = 7) -> list[dict]:
        """Get users active in the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"""
                SELECT user_id, name, interaction_count, last_interaction,
                       current_emotion, relationship_level
                FROM users
                WHERE last_interaction > date('now', '-{days} days')
                ORDER BY last_interaction DESC
            """
            )

            return [dict(row) for row in cursor.fetchall()]

    def search_users_by_emotion(self, emotion: str) -> list[dict]:
        """Find users who have experienced a specific emotion"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT DISTINCT u.user_id, u.name, u.current_emotion,
                       u.interaction_count, u.last_interaction,
                       COUNT(eh.id) as emotion_occurrences
                FROM users u
                JOIN emotion_history eh ON u.user_id = eh.user_id
                WHERE eh.detected_emotion = ?
                GROUP BY u.user_id
                ORDER BY emotion_occurrences DESC
            """,
                (emotion,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total users
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Total emotions
            cursor = conn.execute("SELECT COUNT(*) FROM emotion_history")
            total_emotions = cursor.fetchone()[0]

            # Most active user
            cursor = conn.execute(
                """
                SELECT user_id, interaction_count
                FROM users
                ORDER BY interaction_count DESC
                LIMIT 1
            """
            )
            most_active = cursor.fetchone()

            # Most recent interaction
            cursor = conn.execute(
                """
                SELECT user_id, last_interaction
                FROM users
                WHERE last_interaction IS NOT NULL
                ORDER BY last_interaction DESC
                LIMIT 1
            """
            )
            most_recent = cursor.fetchone()

            return {
                "total_users": total_users,
                "total_emotions": total_emotions,
                "most_active_user": {
                    "user_id": most_active[0] if most_active else None,
                    "interactions": most_active[1] if most_active else 0,
                },
                "most_recent_interaction": {
                    "user_id": most_recent[0] if most_recent else None,
                    "timestamp": most_recent[1] if most_recent else None,
                },
            }


def print_table(data: list[dict], title: str):
    """Print data in a nice table format"""
    if not data:
        return

    # Get all unique keys
    all_keys = set()
    for item in data:
        all_keys.update(item.keys())

    # Print each item
    for _i, item in enumerate(data, 1):
        for key, _value in item.items():
            if key == "user_id":
                pass
            elif key == "name":
                pass
            elif key == "current_emotion":
                pass
            elif key == "relationship_level":
                pass
            elif key == "interaction_count":
                pass
            elif key == "last_interaction":
                break


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()
    query = UserProfileQuery()

    try:
        if command == "list" or command == "all":
            users = query.get_all_users()
            print_table(users, "All Users")

        elif command == "user" and len(sys.argv) > 2:
            user_id = sys.argv[2]
            user = query.get_user_details(user_id)
            if user:
                for key, value in user.items():
                    if key == "recent_emotions":
                        for emotion in value[:5]:  # Show last 5
                            pass
                    elif key == "trust_indicators":
                        pass
                    else:
                        pass
            else:
                pass

        elif command == "stats":
            stats = query.get_database_stats()
            for key, value in stats.items():
                pass

            # Also show emotion stats
            emotion_stats = query.get_emotion_stats()
            for emotion in emotion_stats["emotion_breakdown"]:
                pass

        elif command == "active":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            users = query.get_active_users(days)
            print_table(users, f"Active Users (last {days} days)")

        elif command == "emotion" and len(sys.argv) > 2:
            emotion = sys.argv[2]
            users = query.search_users_by_emotion(emotion)
            print_table(users, f"Users who experienced '{emotion}'")

        elif command == "delete" and len(sys.argv) > 2:
            subcommand = sys.argv[2].lower()

            if subcommand == "user" and len(sys.argv) > 3:
                user_id = sys.argv[3]
                confirm = input(f"⚠️  Delete ALL data for user {user_id}? (type 'YES' to confirm): ")
                if confirm == "YES":
                    from user_profile_db import UserProfileDatabase

                    db = UserProfileDatabase()
                    db.delete_user_profile(user_id)
                else:
                    pass

            elif subcommand == "emotions" and len(sys.argv) > 3:
                user_id = sys.argv[3]
                days = int(sys.argv[4]) if len(sys.argv) > 4 else None

                from user_profile_db import UserProfileDatabase

                db = UserProfileDatabase()

                if days:
                    confirm = input(
                        f"⚠️  Delete emotions older than {days} days for user {user_id}? (y/n): "
                    )
                else:
                    confirm = input(f"⚠️  Delete ALL emotions for user {user_id}? (y/n): ")

                if confirm.lower() == "y":
                    db.delete_user_emotions(user_id, days)
                else:
                    pass

            elif subcommand == "old" and len(sys.argv) > 3:
                days = int(sys.argv[3])
                confirm = input(
                    f"⚠️  Delete ALL emotion records older than {days} days? (type 'YES' to confirm): "
                )
                if confirm == "YES":
                    from user_profile_db import UserProfileDatabase

                    db = UserProfileDatabase()
                    db.cleanup_old_emotions(days)
                else:
                    pass
            else:
                pass

        elif command == "reset" and len(sys.argv) > 2:
            user_id = sys.argv[2]
            keep_basic = len(sys.argv) <= 3 or sys.argv[3].lower() != "full"

            reset_type = "partial (keep basic info)" if keep_basic else "complete"
            confirm = input(f"⚠️  Reset user {user_id} ({reset_type})? (y/n): ")

            if confirm.lower() == "y":
                from user_profile_db import UserProfileDatabase

                db = UserProfileDatabase()
                db.reset_user_profile(user_id, keep_basic)
            else:
                pass

        elif command == "archive":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 90

            from user_profile_db import UserProfileDatabase

            db = UserProfileDatabase()

            # Show preview first
            archivable = db.get_archivable_users(days)
            if archivable:
                for user in archivable:
                    pass

                confirm = input(f"\n⚠️  Archive {len(archivable)} inactive users? (y/n): ")
                if confirm.lower() == "y":
                    db.archive_inactive_users(days)
                else:
                    pass
            else:
                pass

        elif command == "sql":
            # Interactive SQL mode
            with sqlite3.connect(query.db_path) as conn:
                conn.row_factory = sqlite3.Row
                while True:
                    try:
                        sql = input("SQL> ").strip()
                        if sql.lower() in ["quit", "exit"]:
                            break
                        if sql:
                            cursor = conn.execute(sql)
                            rows = cursor.fetchall()
                            if rows:
                                for _row in rows:
                                    pass
                            else:
                                pass
                    except Exception:
                        pass
        else:
            print_help()

    except Exception:
        pass


def print_help():
    pass


if __name__ == "__main__":
    main()
