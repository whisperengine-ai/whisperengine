#!/usr/bin/env python3
"""
ChromaDB User Data Dump Script

This script dumps all ChromaDB data for a specific user, including:
- Conversations (user messages and bot responses)
- Auto-extracted facts
- Manual user facts
- All associated metadata and timestamps

Usage:
    python dump_user_data.py <user_id> [options]

Examples:
    python dump_user_data.py 123456789012345678
    python dump_user_data.py 123456789012345678 --format json --output user_data.json
    python dump_user_data.py 123456789012345678 --facts-only --format json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

import chromadb
from chromadb.config import Settings

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ChromaDBUserDumper:
    def __init__(self, host: str | None = None, port: int | None = None):
        """Initialize ChromaDB HTTP client"""
        try:
            # Use environment variables for connection details
            self.host = host or os.getenv("CHROMADB_HOST", "localhost")
            self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))

            # Configure ChromaDB settings
            telemetry_enabled = os.getenv("ANONYMIZED_TELEMETRY", "false").lower() == "true"
            settings = Settings(anonymized_telemetry=telemetry_enabled)

            # Use HTTP client for containerized ChromaDB service
            self.client = chromadb.HttpClient(host=self.host, port=self.port, settings=settings)
            logger.info(f"Using ChromaDB HTTP client: {self.host}:{self.port}")

            # Get collection names from environment
            collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "user_memories")

            # Get the user memories collection
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"Connected to {collection_name} collection")
            except Exception:
                logger.error(
                    f"{collection_name} collection not found. Make sure the bot has been used before."
                )
                sys.exit(1)

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            sys.exit(1)

    def get_user_data(self, user_id: str, facts_only: bool = False) -> dict:
        """Get all data for a specific user"""
        try:
            # Get all documents for the user
            results = self.collection.get(where={"user_id": user_id})

            if not results["ids"]:
                logger.warning(f"No data found for user {user_id}")
                return {
                    "user_id": user_id,
                    "total_entries": 0,
                    "conversations": [] if not facts_only else None,
                    "facts": [],
                    "dump_timestamp": datetime.now().isoformat(),
                }

            # Process the results
            conversations = []
            facts = []

            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                document = results["documents"][i]

                entry = {
                    "id": doc_id,
                    "document": document,
                    "metadata": metadata,
                    "timestamp": metadata.get("timestamp", "unknown"),
                }

                # Categorize by type
                entry_type = metadata.get("type", "conversation")
                if entry_type == "user_fact":
                    facts.append(entry)
                elif not facts_only:  # Only add conversations if not facts-only mode
                    conversations.append(entry)

            # Sort by timestamp
            if not facts_only:
                conversations.sort(key=lambda x: x["timestamp"])
            facts.sort(key=lambda x: x["timestamp"])

            result = {
                "user_id": user_id,
                "total_entries": len(results["ids"]),
                "facts": facts,
                "dump_timestamp": datetime.now().isoformat(),
            }

            # Only include conversations if not in facts-only mode
            if not facts_only:
                result["conversations"] = conversations

            return result

        except Exception as e:
            logger.error(f"Error retrieving user data: {e}")
            sys.exit(1)

    def dump_to_json(self, user_data: dict, output_file: str | None = None) -> str:
        """Dump user data to JSON format"""
        json_data = json.dumps(user_data, indent=2, ensure_ascii=False)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_data)
            logger.info(f"Data dumped to {output_file}")

        return json_data

    def dump_to_text(self, user_data: dict, output_file: str | None = None) -> str:
        """Dump user data to human-readable text format"""
        lines = []
        lines.append("ChromaDB User Data Dump")
        lines.append("=" * 50)
        lines.append(f"User ID: {user_data['user_id']}")
        lines.append(f"Total Entries: {user_data['total_entries']}")
        lines.append(f"Dump Timestamp: {user_data['dump_timestamp']}")
        lines.append("")

        # Conversations section (only if conversations are included)
        if "conversations" in user_data:
            lines.append(f"CONVERSATIONS ({len(user_data['conversations'])} entries)")
            lines.append("-" * 50)
            for i, conv in enumerate(user_data["conversations"], 1):
                metadata = conv["metadata"]
                lines.append(f"\n[{i}] Conversation ID: {conv['id']}")
                lines.append(f"    Timestamp: {conv['timestamp']}")
                lines.append(f"    Channel: {metadata.get('channel_id', 'DM')}")
                lines.append(f"    User Message: {metadata.get('user_message', 'N/A')}")
                lines.append(f"    Bot Response: {metadata.get('bot_response', 'N/A')}")

        # Facts section
        lines.append(f"\n\nFACTS ({len(user_data['facts'])} entries)")
        lines.append("-" * 50)
        for i, fact in enumerate(user_data["facts"], 1):
            metadata = fact["metadata"]
            lines.append(f"\n[{i}] Fact ID: {fact['id']}")
            lines.append(f"    Timestamp: {fact['timestamp']}")
            lines.append(f"    Fact: {metadata.get('fact', 'N/A')}")
            lines.append(f"    Category: {metadata.get('category', 'N/A')}")
            lines.append(f"    Confidence: {metadata.get('confidence', 'N/A')}")
            lines.append(f"    Source: {metadata.get('source', 'N/A')}")
            lines.append(f"    Method: {metadata.get('extraction_method', 'manual')}")
            context = metadata.get("context", "")
            if context:
                lines.append(f"    Context: {context}")

        text_output = "\n".join(lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text_output)
            logger.info(f"Data dumped to {output_file}")

        return text_output


def main():
    parser = argparse.ArgumentParser(
        description="Dump ChromaDB data for a specific user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 123456789012345678
  %(prog)s 123456789012345678 --format json --output user_data.json
  %(prog)s 123456789012345678 --format text --output user_data.txt
  %(prog)s 123456789012345678 --facts-only --format json
        """,
    )

    parser.add_argument("user_id", help="Discord user ID to dump data for")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format (default: text)"
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout for text/json)")
    parser.add_argument(
        "--chromadb-path",
        default="./chromadb_data",
        help="Path to ChromaDB data directory (default: ./chromadb_data)",
    )
    parser.add_argument(
        "--stats-only", action="store_true", help="Only show statistics, not full data"
    )
    parser.add_argument(
        "--facts-only", action="store_true", help="Only dump facts, exclude conversations"
    )

    args = parser.parse_args()

    # Initialize dumper
    dumper = ChromaDBUserDumper(args.chromadb_path)

    # Get user data
    logger.info(f"Retrieving data for user {args.user_id}")
    user_data = dumper.get_user_data(args.user_id, facts_only=args.facts_only)

    if args.stats_only:
        if "conversations" in user_data:
            pass
        return

    # Output in requested format
    if args.format == "json":
        dumper.dump_to_json(user_data, args.output)
        if not args.output:
            pass
    else:  # text format
        dumper.dump_to_text(user_data, args.output)
        if not args.output:
            pass


if __name__ == "__main__":
    main()
