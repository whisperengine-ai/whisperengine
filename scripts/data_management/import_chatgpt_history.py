#!/usr/bin/env python3
"""
ChatGPT History Import Script

This script imports ChatGPT conversation history from JSON export files into ChromaDB
for a specific user. It processes the conversation history and integrates it with the
existing bot's memory system.

ChatGPT Export Format:
The script expects the standard ChatGPT export format where each conversation is
structured with messages containing 'role' (user/assistant) and 'content' fields.

Usage:
    python import_chatgpt_history.py <user_id> <json_file> [options]

Examples:
    python import_chatgpt_history.py 123456789012345678 conversations.json
    python import_chatgpt_history.py 123456789012345678 export.json --dry-run
    python import_chatgpt_history.py 123456789012345678 export.json --channel-id 987654321
"""

import argparse
import json
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
# Add the src directory to Python path for imports first
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import centralized environment manager
from env_manager import load_environment

# Load environment variables using centralized manager
load_environment()

# Import our existing memory system
from src.memory.memory_manager import UserMemoryManager
from src.llm.llm_client import LLMClient
from src.utils.exceptions import MemoryError, ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatGPTImporter:
    def __init__(self, chromadb_path: str = "./chromadb_data", enable_auto_facts: bool = True, enable_global_facts: bool = False, llm_client=None):
        """Initialize the ChatGPT importer with memory manager"""
        try:
            # Initialize LLM client if not provided
            if llm_client is None:
                try:
                    llm_client = LLMClient()
                    # Test connection to make sure LLM is available
                    if not llm_client.check_connection():
                        logger.warning("LLM Studio server not available - fact extraction and emotion analysis will be disabled")
                        llm_client = None
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM client: {e} - fact extraction and emotion analysis will be disabled")
                    llm_client = None
            
            self.memory_manager = UserMemoryManager(
                persist_directory=chromadb_path,
                enable_auto_facts=enable_auto_facts,
                enable_global_facts=enable_global_facts,
                llm_client=llm_client
            )
            logger.info("ChatGPT importer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatGPT importer: {e}")
            raise MemoryError(f"Failed to initialize importer: {e}")

    def load_chatgpt_export(self, json_file_path: str) -> Dict:
        """Load and parse ChatGPT export JSON file"""
        try:
            file_path = Path(json_file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {json_file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded ChatGPT export from {json_file_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON format in {json_file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise

    def parse_conversations(self, export_data: Dict) -> List[Dict]:
        """Parse conversations from ChatGPT export data"""
        conversations = []
        
        # Handle different possible export formats
        if isinstance(export_data, list):
            # Direct list of conversations
            raw_conversations = export_data
            logger.info(f"Found direct list format with {len(raw_conversations)} conversations")
        elif 'conversations' in export_data:
            # Nested under 'conversations' key
            raw_conversations = export_data['conversations']
            logger.info(f"Found nested conversations format with {len(raw_conversations)} conversations")
        elif 'data' in export_data:
            # Nested under 'data' key
            raw_conversations = export_data['data']
            logger.info(f"Found data format with {len(raw_conversations)} conversations")
        else:
            # Try to find conversations in the root
            raw_conversations = [export_data] if 'mapping' in export_data else []
            logger.info(f"Single conversation format, found {len(raw_conversations)} conversations")
        
        logger.info(f"Processing {len(raw_conversations)} raw conversations...")
        
        for i, conv_data in enumerate(raw_conversations):
            try:
                parsed_conv = self._parse_single_conversation(conv_data)
                if parsed_conv:
                    conversations.append(parsed_conv)
            except Exception as e:
                logger.warning(f"Error parsing conversation: {e}")
                continue
        
        logger.info(f"Parsed {len(conversations)} conversations from export")
        return conversations

    def _parse_single_conversation(self, conv_data: Dict) -> Optional[Dict]:
        """Parse a single conversation from ChatGPT export"""
        try:
            # Extract conversation metadata
            conv_id = conv_data.get('id', 'unknown')
            title = conv_data.get('title', 'Untitled Conversation')
            create_time = conv_data.get('create_time', conv_data.get('created_at'))
            update_time = conv_data.get('update_time', conv_data.get('updated_at'))
            
            # Parse messages from mapping structure (common in ChatGPT exports)
            messages = []
            if 'mapping' in conv_data:
                messages = self._extract_messages_from_mapping(conv_data['mapping'])
            elif 'messages' in conv_data:
                messages = conv_data['messages']
            else:
                logger.warning(f"No messages found in conversation {conv_id}")
                return None
            
            if not messages:
                return None
            
            # Convert to our format
            conversation_turns = self._convert_to_conversation_turns(messages)
            
            return {
                'id': conv_id,
                'title': title,
                'create_time': create_time,
                'update_time': update_time,
                'turns': conversation_turns
            }
            
        except Exception as e:
            logger.warning(f"Error parsing conversation: {e}")
            return None

    def _extract_messages_from_mapping(self, mapping: Dict) -> List[Dict]:
        """Extract messages from ChatGPT's mapping structure"""
        messages = []
        
        for node_id, node in mapping.items():
            if 'message' in node and node['message']:
                message_data = node['message']
                if message_data.get('content') and message_data.get('author'):
                    author = message_data['author']
                    role = author.get('role', '').lower()
                    
                    # Skip system messages and non-conversational roles
                    if role in ['system', 'tool']:
                        continue
                        
                    content = message_data.get('content', {})
                    
                    # Handle different content formats
                    if isinstance(content, dict):
                        # Standard format with parts
                        if 'parts' in content and content['parts']:
                            part_content = content['parts'][0]
                            text_content = str(part_content) if part_content is not None else ""
                        # Text content format
                        elif 'text' in content:
                            text_content = str(content['text']) if content['text'] is not None else ""
                        # Direct content
                        elif isinstance(content.get('content_type'), str) and content.get('content_type') == 'text':
                            parts = content.get('parts', [''])
                            part_content = parts[0] if parts else ""
                            text_content = str(part_content) if part_content is not None else ""
                        else:
                            text_content = str(content) if content else ""
                    elif isinstance(content, str):
                        text_content = content
                    else:
                        text_content = str(content) if content else ""
                    
                    # Ensure text_content is always a string before calling strip()
                    if not isinstance(text_content, str):
                        text_content = str(text_content) if text_content is not None else ""
                    
                    # Skip empty content
                    if not text_content or not text_content.strip():
                        continue
                        
                    messages.append({
                        'role': role,
                        'content': text_content.strip(),
                        'create_time': message_data.get('create_time'),
                        'id': message_data.get('id', node_id)
                    })
        
        # Sort by creation time if available, handling None values properly
        messages.sort(key=lambda x: x.get('create_time') or 0)
        logger.debug(f"Extracted {len(messages)} messages from mapping")
        return messages

    def _convert_to_conversation_turns(self, messages: List[Dict]) -> List[Tuple[str, str]]:
        """Convert messages to user-assistant conversation turns"""
        turns = []
        current_user_msg = ""
        current_assistant_msg = ""
        
        for message in messages:
            role = message.get('role', '').lower()
            content = message.get('content', '')
            
            # Ensure content is a string before calling strip()
            if not isinstance(content, str):
                content = str(content) if content is not None else ""
            
            content = content.strip()
            
            if not content:
                continue
                
            if role == 'user':
                # If we have a complete previous turn, save it
                if current_user_msg and current_assistant_msg:
                    turns.append((current_user_msg, current_assistant_msg))
                    current_user_msg = ""
                    current_assistant_msg = ""
                
                # Start new user message or append to existing
                if current_user_msg:
                    current_user_msg += f"\n{content}"
                else:
                    current_user_msg = content
                    
            elif role == 'assistant':
                # Append to assistant message
                if current_assistant_msg:
                    current_assistant_msg += f"\n{content}"
                else:
                    current_assistant_msg = content
        
        # Don't forget the last turn
        if current_user_msg and current_assistant_msg:
            turns.append((current_user_msg, current_assistant_msg))
        
        return turns

    def import_conversations(self, user_id: str, conversations: List[Dict], 
                           channel_id: Optional[str] = None, dry_run: bool = False) -> Dict:
        """Import conversations into ChromaDB"""
        stats = {
            'total_conversations': len(conversations),
            'total_turns': 0,
            'imported_turns': 0,
            'skipped_turns': 0,
            'errors': 0
        }
        
        if dry_run:
            logger.info("DRY RUN MODE - No data will be stored")
        
        for i, conversation in enumerate(conversations, 1):
            logger.info(f"Processing conversation {i}/{len(conversations)}: {conversation.get('title', 'Untitled')}")
            
            turns = conversation.get('turns', [])
            stats['total_turns'] += len(turns)
            
            for turn_idx, (user_msg, assistant_msg) in enumerate(turns):
                try:
                    # Ensure messages are strings
                    if not isinstance(user_msg, str):
                        user_msg = str(user_msg) if user_msg is not None else ""
                    if not isinstance(assistant_msg, str):
                        assistant_msg = str(assistant_msg) if assistant_msg is not None else ""
                    
                    # Skip very short or empty messages
                    if len(user_msg.strip()) < 3 or len(assistant_msg.strip()) < 3:
                        stats['skipped_turns'] += 1
                        logger.debug(f"Skipped short turn in conversation {conversation['id']}")
                        continue
                    
                    # Skip if this looks like a system message or error
                    if self._is_system_message(user_msg) or self._is_system_message(assistant_msg):
                        stats['skipped_turns'] += 1
                        logger.debug(f"Skipped system message in conversation {conversation['id']}")
                        continue
                    
                    if not dry_run:
                        # Store the conversation turn
                        self.memory_manager.store_conversation(
                            user_id=user_id,
                            user_message=user_msg,
                            bot_response=assistant_msg,
                            channel_id=channel_id or f"chatgpt_import_{conversation['id']}"
                        )
                    
                    stats['imported_turns'] += 1
                    logger.debug(f"Imported turn {turn_idx + 1} from conversation {conversation['id']}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.warning(f"Error importing turn from conversation {conversation['id']}: {e}")
                    continue
        
        return stats

    def _is_system_message(self, message: str) -> bool:
        """Check if a message appears to be a system message"""
        system_indicators = [
            "I'm an AI assistant",
            "I'm ChatGPT",
            "I'm an AI language model",
            "I don't have the ability to",
            "I can't access",
            "I don't have access to",
            "I cannot",
            "As an AI",
            "I'm sorry, but I",
            "I apologize, but I"
        ]
        
        message_lower = message.lower()
        return any(indicator.lower() in message_lower for indicator in system_indicators)

    def validate_user_id(self, user_id: str) -> str:
        """Validate Discord user ID format"""
        if not isinstance(user_id, str):
            user_id = str(user_id)
        user_id = user_id.strip()
        if not user_id.isdigit():
            raise ValidationError(f"Invalid user ID format: {user_id}")
        return user_id

def main():
    parser = argparse.ArgumentParser(
        description="Import ChatGPT conversation history into ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 123456789012345678 conversations.json
  %(prog)s 123456789012345678 export.json --dry-run
  %(prog)s 123456789012345678 export.json --channel-id 987654321 --no-auto-facts
  %(prog)s 123456789012345678 export.json --enable-global-facts
        """
    )
    
    parser.add_argument('user_id', help='Discord user ID to import conversations for')
    parser.add_argument('json_file', help='Path to ChatGPT export JSON file')
    parser.add_argument('--channel-id', help='Channel ID to associate with imported conversations')
    parser.add_argument('--chromadb-path', default='./chromadb_data',
                       help='Path to ChromaDB data directory (default: ./chromadb_data)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview import without actually storing data')
    parser.add_argument('--no-auto-facts', action='store_true',
                       help='Disable automatic user fact extraction during import')
    parser.add_argument('--enable-global-facts', action='store_true',
                       help='Enable automatic global fact extraction during import (disabled by default)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize importer
        importer = ChatGPTImporter(
            chromadb_path=args.chromadb_path,
            enable_auto_facts=not args.no_auto_facts,
            enable_global_facts=args.enable_global_facts,
        )
        
        # Validate user ID
        user_id = importer.validate_user_id(args.user_id)
        
        # Load and parse ChatGPT export
        logger.info(f"Loading ChatGPT export from {args.json_file}")
        export_data = importer.load_chatgpt_export(args.json_file)
        
        # Parse conversations
        conversations = importer.parse_conversations(export_data)
        
        if not conversations:
            logger.error("No valid conversations found in export file")
            sys.exit(1)
        
        # Import conversations
        logger.info(f"Starting import for user {user_id}")
        stats = importer.import_conversations(
            user_id=user_id,
            conversations=conversations,
            channel_id=args.channel_id,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\n" + "="*50)
        print("IMPORT SUMMARY")
        print("="*50)
        print(f"Total conversations: {stats['total_conversations']}")
        print(f"Total turns: {stats['total_turns']}")
        print(f"Imported turns: {stats['imported_turns']}")
        print(f"Skipped turns: {stats['skipped_turns']}")
        print(f"Errors: {stats['errors']}")
        
        if args.dry_run:
            print("\nDRY RUN COMPLETED - No data was actually stored")
        else:
            print(f"\nSUCCESS - Imported {stats['imported_turns']} conversation turns for user {user_id}")
            
        if stats['errors'] > 0:
            print(f"\nWARNING - {stats['errors']} errors occurred during import")
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
