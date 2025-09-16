#!/usr/bin/env python3
"""
Simple SQLite browser for user_profiles.db
"""

import sqlite3


def connect_db(db_path: str = "user_profiles.db"):
    """Connect to the database and return connection"""
    return sqlite3.connect(db_path)


def show_schema():
    """Show database schema"""
    with connect_db() as conn:
        cursor = conn.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """
        )

        for (_sql,) in cursor.fetchall():
            pass


def show_tables():
    """Show all tables and their row counts"""
    with connect_db() as conn:
        cursor = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """
        )

        tables = cursor.fetchall()

        for (table_name,) in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            cursor.fetchone()[0]


def quick_queries():
    """Run some useful quick queries"""
    queries = {
        "Recent Users": """
            SELECT user_id, interaction_count, last_interaction
            FROM users
            ORDER BY last_interaction DESC
            LIMIT 5
        """,
        "Emotion Summary": """
            SELECT detected_emotion, COUNT(*) as count
            FROM emotion_history
            GROUP BY detected_emotion
            ORDER BY count DESC
        """,
        "Most Active Users": """
            SELECT user_id, interaction_count, relationship_level
            FROM users
            ORDER BY interaction_count DESC
            LIMIT 5
        """,
        "Users by Relationship": """
            SELECT relationship_level, COUNT(*) as count
            FROM users
            GROUP BY relationship_level
        """,
    }

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        for _title, query in queries.items():

            cursor = conn.execute(query)
            rows = cursor.fetchall()

            if rows:
                # Print column headers
                rows[0].keys()

                # Print data rows
                for row in rows:
                    values = []
                    for value in row:
                        if isinstance(value, str) and len(value) > 30:
                            values.append(value[:30] + "...")
                        else:
                            values.append(str(value))
            else:
                pass


if __name__ == "__main__":

    try:
        show_schema()
        show_tables()
        quick_queries()

    except FileNotFoundError:
        pass
    except Exception:
        pass
