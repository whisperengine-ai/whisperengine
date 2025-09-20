#!/usr/bin/env python3
"""
ChatGPT History Import Script - Updated for Hierarchical Memory System

This script imports ChatGPT conversation history from JSON export files into the new
hierarchical memory system (HierarchicalMemoryManager) for a specific user.

Compatibility: Updated for the hierarchical memory architecture implemented this morning.

Usage:
    python import_chatgpt_history_hierarchical.py <user_id> <json_file> [options]

Examples:
    python import_chatgpt_history_hierarchical.py 123456789012345678 conversations.json
    python import_chatgpt_history_hierarchical.py 123456789012345678 export.json --dry-run
    python import_chatgpt_history_hierarchical.py 123456789012345678 export.json --channel-id 987654321
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the src directory to Python path for imports first
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import centralized environment manager
from env_manager import load_environment

# Load environment variables using centralized manager
load_environment()

# Import the new hierarchical memory system
from src.memory.core.storage_abstraction import HierarchicalMemoryManager
from src.memory.hierarchical_memory_adapter import HierarchicalMemoryAdapter
from src.llm.llm_client import LLMClient
from src.utils.exceptions import MemoryError, ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HierarchicalChatGPTImporter:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_llm_features: bool = True,
    ):
        """Initialize the ChatGPT importer with hierarchical memory manager"""
        try:
            # Use default config if none provided
            if config is None:
                config = self._get_default_config()
            
            # Initialize LLM client if requested
            llm_client = None
            if enable_llm_features:
                try:
                    llm_client = LLMClient()
                    if not llm_client.check_connection():
                        logger.warning("LLM server not available - some features will be disabled")
                        llm_client = None
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM client: {e}")
                    llm_client = None

            # Initialize hierarchical memory manager
            self.memory_manager = HierarchicalMemoryManager(config)
            
            # Wrap with adapter for easier interface
            self.memory_adapter = HierarchicalMemoryAdapter(self.memory_manager)
            
            logger.info("Hierarchical ChatGPT importer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hierarchical ChatGPT importer: {e}")
            raise MemoryError(f"Failed to initialize importer: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for hierarchical memory using proper environment variables"""
        import os
        
        # Build database URLs from environment variables
        redis_host = os.getenv('HIERARCHICAL_REDIS_HOST', 'redis')
        redis_port = os.getenv('HIERARCHICAL_REDIS_PORT', '6379')
        redis_url = f"redis://{redis_host}:{redis_port}"
        
        pg_host = os.getenv('HIERARCHICAL_POSTGRESQL_HOST', 'postgres')
        pg_port = os.getenv('HIERARCHICAL_POSTGRESQL_PORT', '5432')
        pg_user = os.getenv('HIERARCHICAL_POSTGRESQL_USERNAME', 'bot_user')
        pg_password = os.getenv('HIERARCHICAL_POSTGRESQL_PASSWORD', 'securepassword123')
        pg_database = os.getenv('HIERARCHICAL_POSTGRESQL_DATABASE', 'whisper_engine')
        postgresql_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        
        return {
            # Redis configuration (Tier 1: Cache)
            'redis': {
                'url': redis_url,
                'ttl': int(os.getenv('HIERARCHICAL_REDIS_TTL', '1800')),
            },
            # PostgreSQL configuration (Tier 2: Archive)
            'postgresql': {
                'url': postgresql_url,
            },
            # ChromaDB configuration (Tier 3: Semantic)
            'chromadb': {
                'host': os.getenv('HIERARCHICAL_CHROMADB_HOST', 'chromadb'),
                'port': int(os.getenv('HIERARCHICAL_CHROMADB_PORT', '8000')),
                'collection_name': 'hierarchical_conversations',
            },
            # Neo4j configuration (Tier 4: Graph)
            'neo4j': {
                'uri': f"bolt://{os.getenv('HIERARCHICAL_NEO4J_HOST', 'neo4j')}:{os.getenv('HIERARCHICAL_NEO4J_PORT', '7687')}",
                'user': os.getenv('HIERARCHICAL_NEO4J_USERNAME', 'neo4j'),
                'password': os.getenv('HIERARCHICAL_NEO4J_PASSWORD', 'neo4j_password_change_me'),
            },
            # Feature flags
            'redis_enabled': os.getenv('HIERARCHICAL_REDIS_ENABLED', 'true').lower() == 'true',
            'postgresql_enabled': os.getenv('HIERARCHICAL_POSTGRESQL_ENABLED', 'true').lower() == 'true',
            'chromadb_enabled': os.getenv('HIERARCHICAL_CHROMADB_ENABLED', 'true').lower() == 'true',
            'neo4j_enabled': os.getenv('HIERARCHICAL_NEO4J_ENABLED', 'true').lower() == 'true',
        }

    async def initialize_memory_system(self):
        """Initialize the hierarchical memory system"""
        try:
            await self.memory_manager.initialize()
            logger.info("✅ Hierarchical memory system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hierarchical memory system: {e}")
            raise

    def load_chatgpt_export(self, json_file_path: str) -> dict:
        """Load and parse ChatGPT export JSON file"""
        try:
            file_path = Path(json_file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {json_file_path}")

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Loaded ChatGPT export from {json_file_path}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON format in {json_file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise

    def _extract_conversations(self, data: dict) -> List[dict]:
        """Extract conversations from ChatGPT export data"""
        conversations = []
        
        if isinstance(data, list):
            # Handle direct list of conversations
            conversations = data
        elif isinstance(data, dict):
            # Handle various export formats
            if "conversations" in data:
                conversations = data["conversations"]
            elif "data" in data:
                conversations = data["data"]
            else:
                # Assume the dict itself contains conversation data
                conversations = [data]
        
        logger.info(f"Extracted {len(conversations)} conversations")
        return conversations

    def _extract_messages_from_conversation(self, conversation: dict) -> List[dict]:
        """Extract messages from a conversation using improved ChatGPT parsing"""
        messages = []
        
        # Handle different conversation formats
        if "mapping" in conversation:
            # ChatGPT export format with mapping - flatten tree structure
            messages = self._flatten_message_tree(conversation["mapping"])
        elif "messages" in conversation:
            # Direct messages array
            messages = conversation["messages"]
        elif "conversation" in conversation:
            # Nested conversation format
            messages = conversation["conversation"].get("messages", [])
        
        # Sort by create_time if available
        if messages:
            try:
                messages.sort(key=lambda x: x.get("create_time", 0))
            except (KeyError, TypeError):
                # Fallback to original order if sorting fails
                pass
        
        return messages

    def _flatten_message_tree(self, mapping: dict) -> List[dict]:
        """Convert ChatGPT's tree structure to linear message list"""
        messages = []
        processed_nodes = set()
        
        def extract_message_from_node(node_data):
            message = node_data.get('message')
            if not message:
                return None
            
            # Skip system messages and empty messages
            author = message.get('author', {})
            role = author.get('role') if isinstance(author, dict) else None
            
            if role == 'system':
                return None
                
            # Check if message has actual content
            content = message.get('content', {})
            parts = content.get('parts', [])
            
            # Skip messages with empty or missing content
            if not parts or (len(parts) == 1 and parts[0] and isinstance(parts[0], str) and not parts[0].strip()):
                return None
                
            return message
            
        def traverse(node_id):
            if node_id in processed_nodes or node_id not in mapping:
                return
                
            processed_nodes.add(node_id)
            node_data = mapping[node_id]
            
            # Extract message from current node
            message = extract_message_from_node(node_data)
            if message:
                messages.append(message)
            
            # Traverse children
            children = node_data.get('children', [])
            for child_id in children:
                traverse(child_id)
        
        # Find root nodes (nodes that aren't children of other nodes)
        all_children = set()
        for node_data in mapping.values():
            all_children.update(node_data.get('children', []))
        
        root_nodes = [node_id for node_id in mapping.keys() if node_id not in all_children]
        
        # Traverse from root nodes
        for root_id in root_nodes:
            traverse(root_id)
        
        return messages

    def _is_system_message(self, content: str) -> bool:
        """Check if a message is a system message that should be skipped"""
        if not content or not isinstance(content, str):
            return True
        
        content_lower = content.lower().strip()
        
        # Skip empty or very short messages
        if len(content_lower) < 3:
            return True
        
        # Skip common system messages
        system_indicators = [
            "this content may violate",
            "i'm sorry, but i can't",
            "i cannot provide",
            "as an ai language model",
            "i don't have access",
            "[system message]",
            "[error]",
            "unable to process",
        ]
        
        return any(indicator in content_lower for indicator in system_indicators)

    async def import_conversations(
        self,
        user_id: str,
        conversations: List[dict],
        channel_id: Optional[str] = None,
        dry_run: bool = False,
        batch_size: int = 10,
    ) -> dict:
        """Import conversations using hierarchical memory system with batching"""
        stats = {
            "total_conversations": len(conversations),
            "imported_conversations": 0,
            "imported_turns": 0,
            "skipped_conversations": 0,
            "skipped_turns": 0,
            "errors": 0,
        }

        logger.info(f"Starting import of {len(conversations)} conversations for user {user_id}")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No data will be stored")

        # Process in batches for better performance
        for batch_start in range(0, len(conversations), batch_size):
            batch_end = min(batch_start + batch_size, len(conversations))
            batch = conversations[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}/{(len(conversations) + batch_size - 1)//batch_size}")
            
            for conversation in batch:
                try:
                    await self._import_single_conversation(
                        user_id=user_id,
                        conversation=conversation,
                        channel_id=channel_id,
                        dry_run=dry_run,
                        stats=stats,
                    )
                except Exception as e:
                    logger.error(f"Error importing conversation {conversation.get('id', 'unknown')}: {e}")
                    stats["errors"] += 1
                    continue
            
            # Small delay between batches to prevent overwhelming the system
            if not dry_run and batch_end < len(conversations):
                await asyncio.sleep(0.1)

        return stats

    async def _import_single_conversation(
        self,
        user_id: str,
        conversation: dict,
        channel_id: Optional[str],
        dry_run: bool,
        stats: dict,
    ):
        """Import a single conversation"""
        messages = self._extract_messages_from_conversation(conversation)
        
        if not messages:
            stats["skipped_conversations"] += 1
            return

        # Process message pairs (user -> assistant)
        conversation_imported = False
        
        for i in range(len(messages) - 1):
            current_msg = messages[i]
            next_msg = messages[i + 1]
            
            # Extract roles from ChatGPT format
            current_role = self._get_message_role(current_msg)
            next_role = self._get_message_role(next_msg)
            
            # Look for user -> assistant pairs
            if (current_role == "user" and next_role == "assistant"):
                
                user_content = self._extract_message_content(current_msg)
                assistant_content = self._extract_message_content(next_msg)
                
                if not user_content or not assistant_content:
                    stats["skipped_turns"] += 1
                    continue
                
                # Skip system messages
                if self._is_system_message(user_content) or self._is_system_message(assistant_content):
                    stats["skipped_turns"] += 1
                    continue

                if not dry_run:
                    # Prepare metadata for hierarchical storage
                    metadata = {
                        'source': 'chatgpt_import',
                        'conversation_id': conversation.get('id', 'unknown'),
                        'import_timestamp': datetime.now().isoformat(),
                    }
                    
                    if channel_id:
                        metadata['channel_id'] = channel_id
                    
                    # Add conversation metadata if available
                    if 'create_time' in conversation:
                        metadata['original_timestamp'] = conversation['create_time']
                    if 'title' in conversation:
                        metadata['conversation_title'] = conversation['title']

                    # Store using hierarchical memory adapter
                    success = await self.memory_adapter.store_conversation_safe(
                        user_id=user_id,
                        user_message=user_content,
                        bot_response=assistant_content,
                        metadata=metadata
                    )
                    
                    if not success:
                        logger.warning(f"Failed to store conversation turn for user {user_id}")
                        stats["errors"] += 1
                        continue

                stats["imported_turns"] += 1
                conversation_imported = True
                
                logger.debug(f"Imported turn from conversation {conversation.get('id', 'unknown')}")

        if conversation_imported:
            stats["imported_conversations"] += 1
        else:
            stats["skipped_conversations"] += 1

    def _get_message_role(self, message: dict) -> str:
        """Extract role from ChatGPT message format"""
        if not message:
            return ""
        
        # Try author.role first (ChatGPT format)
        author = message.get("author", {})
        if isinstance(author, dict) and "role" in author:
            return author["role"]
        
        # Fallback to direct role field
        return message.get("role", "")

    def _extract_message_content(self, message: dict) -> str:
        """Extract text content from a ChatGPT message"""
        if not message:
            return ""
        
        # Get the role first to determine if this is a valid message
        author = message.get("author", {})
        role = author.get("role") if isinstance(author, dict) else message.get("role")
        
        if not role or role == "system":
            return ""
        
        content = message.get("content")
        
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, dict):
            # Handle ChatGPT structured content with parts
            if "parts" in content and isinstance(content["parts"], list):
                # Extract text from parts
                text_parts = []
                for part in content["parts"]:
                    if isinstance(part, str) and part.strip():
                        text_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        text_content = str(part["text"]).strip()
                        if text_content:
                            text_parts.append(text_content)
                return "\n".join(text_parts).strip()
            elif "text" in content:
                return str(content["text"]).strip()
        elif isinstance(content, list):
            # Handle content as list
            valid_parts = []
            for item in content:
                if item and str(item).strip():
                    valid_parts.append(str(item))
            return "\n".join(valid_parts).strip()
        
        return ""

    def print_import_summary(self, stats: dict, dry_run: bool = False):
        """Print a summary of the import process"""
        mode = "DRY RUN" if dry_run else "IMPORT"
        
        print(f"\n📊 {mode} SUMMARY")
        print("=" * 50)
        print(f"Total conversations processed: {stats['total_conversations']}")
        print(f"Conversations imported: {stats['imported_conversations']}")
        print(f"Conversation turns imported: {stats['imported_turns']}")
        print(f"Conversations skipped: {stats['skipped_conversations']}")
        print(f"Turns skipped: {stats['skipped_turns']}")
        print(f"Errors encountered: {stats['errors']}")
        
        if stats['total_conversations'] > 0:
            success_rate = (stats['imported_conversations'] / stats['total_conversations']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        if not dry_run and stats['imported_turns'] > 0:
            print(f"\n✅ Successfully imported {stats['imported_turns']} conversation turns")
            print("🔗 Data is now available in the hierarchical memory system!")


async def main():
    """Main function to run the ChatGPT import"""
    parser = argparse.ArgumentParser(
        description="Import ChatGPT conversation history into hierarchical memory system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python import_chatgpt_history_hierarchical.py 123456789012345678 conversations.json
  python import_chatgpt_history_hierarchical.py 123456789012345678 export.json --dry-run
  python import_chatgpt_history_hierarchical.py 123456789012345678 export.json --channel-id 987654321 --batch-size 20
        """,
    )

    parser.add_argument("user_id", help="Discord user ID to associate conversations with")
    parser.add_argument("json_file", help="Path to ChatGPT export JSON file")
    parser.add_argument(
        "--channel-id",
        help="Optional Discord channel ID to associate conversations with",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview import without storing data",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of conversations to process in each batch (default: 10)",
    )
    parser.add_argument(
        "--disable-llm",
        action="store_true",
        help="Disable LLM features for faster import",
    )

    args = parser.parse_args()

    try:
        # Initialize importer
        importer = HierarchicalChatGPTImporter(
            enable_llm_features=not args.disable_llm
        )
        
        # Initialize memory system
        await importer.initialize_memory_system()

        # Load ChatGPT export data
        logger.info(f"Loading ChatGPT export from {args.json_file}")
        data = importer.load_chatgpt_export(args.json_file)

        # Extract conversations
        conversations = importer._extract_conversations(data)

        if not conversations:
            logger.error("No conversations found in export file")
            return 1

        # Import conversations
        stats = await importer.import_conversations(
            user_id=args.user_id,
            conversations=conversations,
            channel_id=args.channel_id,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        )

        # Print summary
        importer.print_import_summary(stats, dry_run=args.dry_run)

        return 0

    except Exception as e:
        logger.error(f"Import failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))