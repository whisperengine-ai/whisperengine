#!/usr/bin/env python3
"""
Clean ChatGPT Import Script - Disables emotion analysis to avoid warnings
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Import the memory manager
try:
    from src.memory.memory_manager import UserMemoryManager
except ImportError:
    try:
        from memory.memory_manager import UserMemoryManager
    except ImportError:
        UserMemoryManager = None

# Simple message structure
class ConversationMessage(NamedTuple):
    role: str
    content: str
    timestamp: datetime
    user_id: str
    metadata: dict

# Configure logging to suppress emotion analysis warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress emotion analysis warnings
logging.getLogger('src.memory.memory_manager').setLevel(logging.ERROR)
logging.getLogger('memory.memory_manager').setLevel(logging.ERROR)


class CleanChatGPTImporter:
    """Clean ChatGPT conversation importer without emotion analysis noise"""
    
    def __init__(self, user_id: int, dry_run: bool = False, verbose: bool = False):
        self.user_id = user_id
        self.dry_run = dry_run
        self.verbose = verbose
        self.memory_manager = None
        self.processed_count = 0
        self.conversation_count = 0
        
    def initialize(self):
        """Initialize the memory manager (skip in dry run mode)"""
        if not self.dry_run:
            if UserMemoryManager is None:
                raise ImportError("UserMemoryManager not available - check imports")
            # Initialize with emotion analysis disabled
            self.memory_manager = UserMemoryManager(
                enable_emotions=False  # Disable emotion analysis to avoid warnings
            )
            logger.info("Memory manager initialized (emotion analysis disabled)")
        else:
            logger.info("Dry run mode - skipping memory manager initialization")
            
    def import_conversations(self, file_path: str) -> Dict[str, int]:
        """Import conversations from ChatGPT export file"""
        logger.info(f"Starting clean import for user {self.user_id} from {file_path}")
        
        # Load and validate file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        conversations = self._extract_conversations(data)
        logger.info(f"Found {len(conversations)} conversations to import")
        
        # Process each conversation
        for i, conversation in enumerate(conversations):
            try:
                self._process_conversation(conversation, i)
                self.conversation_count += 1
                
                if i % 25 == 0:  # Progress indicator every 25 conversations
                    logger.info(f"Processed {i}/{len(conversations)} conversations")
                    
            except Exception as e:
                logger.error(f"Error processing conversation {i}: {e}")
                continue
                
        if not self.dry_run:
            logger.info("✅ Clean import complete!")
        else:
            logger.info("✅ Dry run complete - no data stored")
        
        return {
            'conversations_imported': self.conversation_count,
            'messages_processed': self.processed_count,
            'user_id': self.user_id,
            'dry_run': self.dry_run
        }
        
    def _extract_conversations(self, data: Dict) -> List[Dict]:
        """Extract conversations from ChatGPT export data"""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'conversations' in data:
            return data['conversations']
        else:
            raise ValueError("Unexpected data format - expected list or dict with 'conversations' key")
            
    def _process_conversation(self, conversation: Dict, index: int):
        """Process a single conversation"""
        try:
            conversation_id = conversation.get('id', f'imported_{index}')
            title = conversation.get('title', f'Imported Conversation {index + 1}')
            
            if self.verbose:
                logger.debug(f"Processing conversation {index}: {title}")
            
            # Extract and convert messages
            messages = self._flatten_message_tree(conversation)
            converted_messages = []
            
            for msg in messages:
                converted_msg = self._convert_message(msg)
                if converted_msg:
                    converted_messages.append(converted_msg)
                    self.processed_count += 1
                    
            if not converted_messages:
                if self.verbose:
                    logger.debug(f"No valid messages found in conversation {index}")
                return
                
            # Store conversation pairs
            if not self.dry_run:
                self._store_conversation_pairs(converted_messages, conversation_id, title)
                
        except Exception as conv_error:
            logger.error(f"Error processing conversation {index}: {conv_error}")
            
    def _flatten_message_tree(self, conversation: Dict) -> List[Dict]:
        """Flatten ChatGPT's tree structure into a linear message list"""
        mapping = conversation.get('mapping', {})
        if not mapping:
            return []
            
        # Find root message
        root_id = None
        for msg_id, msg_data in mapping.items():
            if msg_data.get('parent') is None:
                root_id = msg_id
                break
                
        if not root_id:
            return []
            
        # Traverse the tree depth-first
        messages = []
        
        def traverse(node_id):
            if node_id not in mapping:
                return
                
            node = mapping[node_id]
            message = node.get('message')
            
            if message and message.get('content'):
                messages.append(message)
                
            # Process children
            children = node.get('children', [])
            for child_id in children:
                traverse(child_id)
                
        traverse(root_id)
        return messages
        
    def _convert_message(self, message_data: Dict) -> Optional[ConversationMessage]:
        """Convert ChatGPT message to WhisperEngine format"""
        try:
            author = message_data.get('author', {})
            role = author.get('role', 'unknown')
            
            # Skip system messages
            if role == 'system':
                return None
                
            content = self._extract_content(message_data)
            if not content:
                return None
                
            # Create timestamp
            create_time = message_data.get('create_time')
            if create_time:
                timestamp = datetime.fromtimestamp(create_time)
            else:
                timestamp = datetime.now()
                
            return ConversationMessage(
                role=role,
                content=content,
                timestamp=timestamp,
                user_id=str(self.user_id),
                metadata={
                    'source': 'chatgpt_import',
                    'original_id': message_data.get('id', ''),
                    'author': author
                }
            )
            
        except Exception as e:
            if self.verbose:
                logger.debug(f"Error converting message: {e}")
            return None
            
    def _extract_content(self, message_data: Dict) -> Optional[str]:
        """Extract text content from ChatGPT message format using JSON-safe parsing"""
        
        def safe_string_extract(obj, default=""):
            """Safely extract string content from any object"""
            if obj is None:
                return default
            if isinstance(obj, str):
                return obj.strip()
            if isinstance(obj, (int, float, bool)):
                return str(obj)
            if isinstance(obj, dict):
                # Try common text fields
                for field in ['text', 'content', 'value', 'data']:
                    if field in obj and obj[field] is not None:
                        return safe_string_extract(obj[field])
                # Return JSON representation for complex objects
                try:
                    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
                except (TypeError, ValueError):
                    return str(obj)
            if isinstance(obj, list):
                # Extract text from all list elements
                texts = [safe_string_extract(item) for item in obj if item is not None]
                return ' '.join(filter(None, texts))
            return str(obj)

        def extract_from_parts(parts):
            """Extract content from ChatGPT parts array"""
            if not parts:
                return None
                
            text_parts = []
            attachments = []
            
            for part in parts:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    content_type = part.get('content_type', '')
                    
                    # Handle different content types
                    if content_type == 'image_asset_pointer':
                        asset_info = part.get('asset_pointer', 'image')
                        width = part.get('width', 0)
                        height = part.get('height', 0)
                        attachments.append(f"[Image: {asset_info} {width}x{height}]")
                    elif content_type == 'multimodal_text':
                        # Recursively extract from multimodal parts
                        sub_parts = part.get('parts', [])
                        sub_content = extract_from_parts(sub_parts)
                        if sub_content:
                            text_parts.append(sub_content)
                    elif content_type == 'execution_output':
                        output_text = safe_string_extract(part.get('text', ''))
                        if output_text:
                            text_parts.append(f"[Code Output: {output_text}]")
                    elif content_type == 'code':
                        language = part.get('language', 'text')
                        code_text = safe_string_extract(part.get('text', ''))
                        if code_text:
                            text_parts.append(f"```{language}\n{code_text}\n```")
                    else:
                        # Try to extract text from any text field
                        text_content = safe_string_extract(part)
                        if text_content and text_content != '{}':
                            text_parts.append(text_content)
                else:
                    # Convert non-dict, non-string to string
                    text_parts.append(safe_string_extract(part))
            
            # Combine all content
            all_content = []
            all_content.extend(filter(None, [safe_string_extract(p) for p in text_parts]))
            all_content.extend(attachments)
            
            return ' '.join(all_content) if all_content else None
        
        # Main extraction logic
        try:
            content = message_data.get('content', {})
            
            if isinstance(content, dict):
                # Standard ChatGPT format: content.parts[]
                parts = content.get('parts', [])
                if parts:
                    return extract_from_parts(parts)
                
                # Fallback: try direct text fields
                for field in ['text', 'content', 'message']:
                    if field in content:
                        text = safe_string_extract(content[field])
                        if text:
                            return text
            else:
                # Direct content (string or other)
                return safe_string_extract(content)
                
        except Exception as e:
            if self.verbose:
                print(f"Warning: Content extraction failed: {e}")
            return None
            
        return None
        
    def _store_conversation_pairs(self, messages: List[ConversationMessage], conversation_id: str, title: str):
        """Store conversation as user-assistant pairs"""
        user_id = str(self.user_id)
        
        # Group messages into user-assistant pairs
        pairs = []
        current_user_msg = None
        
        for msg in messages:
            if msg.role == 'user':
                current_user_msg = msg
            elif msg.role == 'assistant' and current_user_msg:
                pairs.append((current_user_msg, msg))
                current_user_msg = None
                
        # Store each pair
        for i, (user_msg, assistant_msg) in enumerate(pairs):
            try:
                # Check for synthetic/generated content
                if ('generated' in user_msg.content.lower() or 
                    'synthetic' in user_msg.content.lower()):
                    if self.verbose:
                        logger.debug("Skipping synthetic message pair")
                    continue
                    
                # Store the conversation pair with disabled emotion analysis
                self.memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=user_msg.content,
                    bot_response=assistant_msg.content,
                    channel_id=conversation_id,
                    pre_analyzed_emotion_data={'emotion': 'neutral', 'intensity': 0.5},  # Pre-supply emotion data
                    metadata={
                        'source': 'chatgpt_import',
                        'conversation_title': title,
                        'conversation_id': conversation_id,
                        'pair_index': i,
                        'original_timestamp': user_msg.timestamp.isoformat(),
                        'import_timestamp': datetime.now().isoformat()
                    }
                )
                
            except Exception as e:
                logger.error(f"Error storing message pair {i}: {e}")
                continue


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Clean ChatGPT import without emotion analysis warnings')
    parser.add_argument('--file', '-f', required=True, help='Path to conversations.json file')
    parser.add_argument('--user-id', '-u', type=int, required=True, help='Discord user ID')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Parse and validate without storing (dry run)')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate file exists
    if not Path(args.file).exists():
        print(f"Error: File {args.file} not found")
        return 1
        
    # Run import
    try:
        importer = CleanChatGPTImporter(args.user_id, dry_run=args.dry_run, verbose=args.verbose)
        
        if args.dry_run:
            print("🧪 DRY RUN MODE - No data will be stored")
        else:
            print(f"🚀 Starting clean import for user {args.user_id}")
        
        importer.initialize()
        
        result = importer.import_conversations(args.file)
        
        if args.dry_run:
            print("✅ Dry run completed successfully!")
            print("📋 Parsing Results:")
        else:
            print("✅ Clean import completed successfully!")
        
        print(f"📊 Conversations processed: {result['conversations_imported']}")
        print(f"💬 Messages processed: {result['messages_processed']}")
        print(f"👤 User ID: {result['user_id']}")
        
        if args.dry_run:
            print("\n🔄 To perform actual import, run without --dry-run flag")
            
        return 0
        
    except Exception as e:
        if args.dry_run:
            print(f"❌ Dry run failed: {e}")
        else:
            print(f"❌ Import failed: {e}")
        print(f"Operation failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())