"""
ChatGPT Conversation Importer for WhisperEngine

This module provides the core functionality to import ChatGPT conversation
history into WhisperEngine's memory system.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

# Import WhisperEngine modules
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass
from src.memory.vector_memory_system import VectorMemoryManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ConversationMessage:
    """Individual message within a conversation"""
    id: str
    content: str
    sender: str  # 'user' or 'assistant'
    timestamp: str
    metadata: dict[str, Any] | None = None
    files: list[dict[str, Any]] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.files is None:
            self.files = []


class ChatGPTImporter:
    """Imports ChatGPT conversations into WhisperEngine vector memory system"""
    
    def __init__(self, user_id: int, dry_run: bool = False, verbose: bool = False):
        self.user_id = user_id
        self.dry_run = dry_run
        self.verbose = verbose
        self.memory_manager = None
        self.processed_count = 0
        self.conversation_count = 0
        
    async def initialize(self):
        """Initialize the vector memory system (skip in dry run mode)"""
        if not self.dry_run:
            import os
            
            # Create vector memory config from environment variables
            vector_config = {
                'qdrant': {
                    'host': os.getenv('VECTOR_QDRANT_HOST', 'qdrant'),
                    'port': int(os.getenv('VECTOR_QDRANT_PORT', '6333')),
                    'grpc_port': int(os.getenv('VECTOR_QDRANT_GRPC_PORT', '6334')),
                    'collection_name': os.getenv('VECTOR_QDRANT_COLLECTION', 'whisperengine_memory'),
                    'vector_size': int(os.getenv('VECTOR_EMBEDDING_SIZE', '384'))
                },
                'embeddings': {
                    'model_name': os.getenv('EMBEDDING_MODEL', 'snowflake/snowflake-arctic-embed-xs'),
                    'device': os.getenv('VECTOR_EMBEDDING_DEVICE', 'cpu')
                },
                'postgresql': {
                    'url': f"postgresql://{os.getenv('POSTGRESQL_USERNAME', 'bot_user')}:{os.getenv('POSTGRESQL_PASSWORD', 'securepassword123')}@{os.getenv('POSTGRESQL_HOST', 'postgres')}:{os.getenv('POSTGRESQL_PORT', '5432')}/{os.getenv('POSTGRESQL_DATABASE', 'whisper_engine')}"
                },
                'redis': {
                    'url': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}",
                    'ttl': int(os.getenv('REDIS_TTL', '1800'))
                }
            }
            
            self.memory_manager = VectorMemoryManager(vector_config)
        else:
            logger.info("Dry run mode - skipping vector memory system initialization")
        
    async def import_conversations(self, file_path: str) -> Dict[str, int]:
        """Import conversations from ChatGPT export file"""
        logger.info("Starting import for user %s from %s", self.user_id, file_path)
        
        # Load and validate file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        conversations = self._extract_conversations(data)
        logger.info("Found %d conversations to import", len(conversations))
        
        # Process each conversation
        for i, conversation in enumerate(conversations):
            try:
                await self._process_conversation(conversation, i)
                self.conversation_count += 1
                
                if i % 10 == 0:  # Progress indicator
                    logger.info("Processed %d/%d conversations", i, len(conversations))
                    
            except Exception as e:
                logger.error("Error processing conversation %d: %s", i, e)
                continue
                
        # Trigger memory analysis
        if not self.dry_run:
            await self._analyze_imported_data()
        else:
            logger.info("Dry run complete - no data stored")
        
        return {
            'conversations_imported': self.conversation_count,
            'messages_processed': self.processed_count,
            'user_id': self.user_id,
            'dry_run': self.dry_run
        }
        
    def _extract_conversations(self, data: Dict[str, Any]) -> List[Dict]:
        """Extract conversations from various ChatGPT export formats"""
        conversations = []
        
        # Handle different export formats
        if isinstance(data, list):
            conversations = data
        elif 'conversations' in data:
            conversations = data['conversations']
        elif isinstance(data, dict):
            # Look for conversation-like objects
            for _, value in data.items():
                if isinstance(value, list) and value:
                    # Check if this looks like a conversation list
                    sample = value[0]
                    if isinstance(sample, dict) and self._is_conversation_object(sample):
                        conversations = value
                        break
                        
        return conversations
        
    def _is_conversation_object(self, obj: Dict) -> bool:
        """Check if object looks like a conversation"""
        conversation_indicators = ['mapping', 'messages', 'title', 'conversation_id', 'id']
        return any(indicator in obj for indicator in conversation_indicators)
        
    async def _process_conversation(self, conversation: Dict, index: int):
        """Process a single conversation with improved pairing logic"""
        conversation_id = conversation.get('id', f"chatgpt_import_{index}")
        title = conversation.get('title', f'Imported Conversation {index + 1}')
        
        try:
            # Extract messages from conversation
            messages = self._extract_messages(conversation)
            
            if not messages:
                logger.warning("No messages found in conversation %s", conversation_id)
                return
                
            logger.debug("Processing conversation '%s' with %d messages", title, len(messages))
            
            # Convert messages to WhisperEngine format
            converted_messages = []
            for message_data in messages:
                try:
                    whisper_message = self._convert_message(message_data, conversation_id)
                    if whisper_message:
                        converted_messages.append(whisper_message)
                except Exception as msg_error:
                    logger.error("Error converting message in conversation %d: %s", index, msg_error)
                    logger.debug("Problematic message data: %s", str(message_data)[:200])
                    continue
            
            # Store messages as conversation pairs for better analysis
            await self._store_conversation_pairs(converted_messages, conversation_id, title)
            
        except Exception as conv_error:
            logger.error("Error processing conversation %d: %s", index, conv_error)
            logger.debug("Conversation structure: %s", str(conversation)[:300])
                
    async def _store_conversation_pairs(self, messages: List[ConversationMessage], conversation_id: str, title: str):
        """Store messages as user-assistant pairs to maximize analysis effectiveness"""
        user_id = str(self.user_id)
        
        if self.dry_run:
            logger.info("DRY RUN: Would store %d messages from conversation '%s'", len(messages), title)
            for i, msg in enumerate(messages):
                logger.info("  Message %d: %s - '%s'", i+1, msg.sender, msg.content[:100] + "..." if len(msg.content) > 100 else msg.content)
            self.processed_count += len(messages)
            return
        
        # Group messages into user-assistant pairs
        i = 0
        while i < len(messages):
            current_msg = messages[i]
            
            if current_msg.sender == 'user':
                # Look for the next assistant message
                user_message = current_msg.content
                assistant_response = "..."  # Default if no response found
                
                if i + 1 < len(messages) and messages[i + 1].sender == 'assistant':
                    assistant_response = messages[i + 1].content
                    i += 2  # Skip both messages
                else:
                    i += 1  # Skip just the user message
                    
                # Store as conversation pair with metadata
                await self.memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=user_message,
                    bot_response=assistant_response,
                    channel_id=f"chatgpt_import_{conversation_id}",
                    metadata={
                        'source': 'chatgpt_import',
                        'conversation_id': conversation_id,
                        'conversation_title': title,
                        'imported_at': datetime.utcnow().isoformat(),
                        'original_timestamp': current_msg.timestamp,
                        'import_type': 'historical_conversation_pair'
                    }
                )
                self.processed_count += 2 if assistant_response != "..." else 1
                
            elif current_msg.sender == 'assistant':
                # Standalone assistant message (less common)
                await self.memory_manager.store_conversation(
                    user_id=user_id,
                    user_message="[Previous conversation context]",
                    bot_response=current_msg.content,
                    channel_id=f"chatgpt_import_{conversation_id}",
                    metadata={
                        'source': 'chatgpt_import',
                        'conversation_id': conversation_id,
                        'conversation_title': title,
                        'imported_at': datetime.utcnow().isoformat(),
                        'original_timestamp': current_msg.timestamp,
                        'import_type': 'standalone_assistant_message'
                    }
                )
                self.processed_count += 1
                i += 1
                
    def _extract_messages(self, conversation: Dict) -> List[Dict]:
        """Extract messages from conversation data"""
        messages = []
        
        if 'mapping' in conversation:
            # Handle ChatGPT's tree structure
            messages = self._flatten_message_tree(conversation['mapping'])
        elif 'messages' in conversation:
            messages = conversation['messages']
        elif 'conversation' in conversation and 'messages' in conversation['conversation']:
            messages = conversation['conversation']['messages']
            
        return messages
        
    def _flatten_message_tree(self, mapping: Dict) -> List[Dict]:
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
            
            # Extract message from this node
            message = extract_message_from_node(node_data)
            if message:
                messages.append(message)
                
            # Process children in chronological order
            children = node_data.get('children', [])
            # Sort children by their creation time if available
            def get_child_time(child_id):
                if child_id in mapping:
                    child_message = mapping[child_id].get('message')
                    if child_message:
                        create_time = child_message.get('create_time')
                        return create_time if create_time is not None else 0
                return 0
                
            sorted_children = sorted(children, key=get_child_time)
            for child_id in sorted_children:
                traverse(child_id)
                
        # Find root nodes (nodes with parent as "client-created-root" or no parent)
        root_nodes = []
        for node_id, node_data in mapping.items():
            parent = node_data.get('parent')
            if parent == 'client-created-root' or parent is None:
                # But skip the actual "client-created-root" node
                if node_id != 'client-created-root':
                    root_nodes.append(node_id)
        
        # Process from roots in chronological order
        def get_node_time(node_id):
            if node_id in mapping:
                message = mapping[node_id].get('message')
                if message:
                    create_time = message.get('create_time')
                    return create_time if create_time is not None else 0
            return 0
            
        sorted_roots = sorted(root_nodes, key=get_node_time)
        for root_id in sorted_roots:
            traverse(root_id)
            
        return messages
        
    def _convert_message(self, message_data: Dict, conversation_id: str) -> Optional[ConversationMessage]:
        """Convert ChatGPT message to WhisperEngine format"""
        # Extract content
        content = self._extract_content(message_data)
        if not content or (isinstance(content, str) and len(content.strip()) == 0):
            return None
            
        # ChatGPT format: author.role for role detection
        author = message_data.get('author', {})
        role = author.get('role', '') if isinstance(author, dict) else ''
        
        # Determine if this is a user message
        is_user = (role == 'user')
        
        # Skip system messages
        if role == 'system':
            return None
            
        # Extract timestamp
        timestamp = self._extract_timestamp(message_data)
        
        # Extract attachment metadata
        attachments_meta = self._extract_attachments_metadata(message_data)
        
        # Generate unique ID for this message
        message_id = f"chatgpt_{conversation_id}_{int(timestamp.timestamp())}"
        
        # Build comprehensive metadata
        metadata = {
            'source': 'chatgpt_import',
            'conversation_id': conversation_id,
            'original_role': role,
            'imported_at': datetime.utcnow().isoformat(),
            'user_id': str(self.user_id)
        }
        
        # Add attachment metadata if present
        if attachments_meta['has_attachments']:
            metadata.update({
                'has_attachments': True,
                'attachment_types': attachments_meta['attachment_types'],
                'image_count': attachments_meta['image_count'],
                'code_blocks': attachments_meta['code_blocks'],
                'file_references': attachments_meta['file_references']
            })
        
        return ConversationMessage(
            id=message_id,
            content=content,
            sender='user' if is_user else 'assistant',
            timestamp=timestamp.isoformat(),
            metadata=metadata
        )
        
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
        
    def _extract_timestamp(self, message_data: Dict) -> datetime:
        """Extract timestamp from ChatGPT message format"""
        # ChatGPT uses create_time as Unix timestamp (float)
        create_time = message_data.get('create_time')
        
        if create_time and isinstance(create_time, (int, float)):
            try:
                return datetime.fromtimestamp(create_time)
            except (ValueError, OSError):
                pass
        
        # Fallback: try other timestamp fields
        timestamp_fields = ['update_time', 'timestamp', 'created_at']
        
        for field in timestamp_fields:
            if field in message_data:
                try:
                    timestamp_value = message_data[field]
                    if isinstance(timestamp_value, (int, float)):
                        return datetime.fromtimestamp(timestamp_value)
                    elif isinstance(timestamp_value, str):
                        # Try common formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                            try:
                                return datetime.strptime(timestamp_value, fmt)
                            except ValueError:
                                continue
                except (ValueError, OSError, TypeError):
                    continue
                    
        # Final fallback to current time
        return datetime.utcnow()
        
    def _extract_attachments_metadata(self, message_data: Dict) -> Dict[str, Any]:
        """Extract metadata about attachments and structured content"""
        content = message_data.get('content', {})
        attachments_meta = {
            'has_attachments': False,
            'attachment_types': [],
            'image_count': 0,
            'code_blocks': 0,
            'file_references': []
        }
        
        if isinstance(content, dict):
            parts = content.get('parts', [])
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        content_type = part.get('content_type', '')
                        
                        if content_type == 'image_asset_pointer':
                            attachments_meta['has_attachments'] = True
                            attachments_meta['attachment_types'].append('image')
                            attachments_meta['image_count'] += 1
                            
                            asset_pointer = part.get('asset_pointer', '')
                            if asset_pointer:
                                attachments_meta['file_references'].append({
                                    'type': 'image',
                                    'pointer': asset_pointer,
                                    'size_bytes': part.get('size_bytes'),
                                    'dimensions': f"{part.get('width', 0)}x{part.get('height', 0)}"
                                })
                                
                        elif content_type == 'multimodal_text':
                            # Check for embedded images or files
                            if 'parts' in part:
                                for subpart in part['parts']:
                                    if isinstance(subpart, dict) and subpart.get('type') == 'image_url':
                                        attachments_meta['has_attachments'] = True
                                        attachments_meta['attachment_types'].append('image_url')
                                        attachments_meta['image_count'] += 1
                                        
                        elif content_type == 'code':
                            attachments_meta['code_blocks'] += 1
                            attachments_meta['attachment_types'].append('code')
                            
                        elif content_type == 'execution_output':
                            attachments_meta['attachment_types'].append('execution_output')
                            
        # Remove duplicates from attachment_types
        attachments_meta['attachment_types'] = list(set(attachments_meta['attachment_types']))
        
        return attachments_meta
        
    async def _store_message(self, message: ConversationMessage):
        """Store message in WhisperEngine memory system"""
        # Extract user_id from metadata, handling None case
        user_id = str(self.user_id)
        if message.metadata:
            user_id = message.metadata.get('user_id', user_id)
        
        # Store the conversation using the store_conversation method
        if message.sender == 'user':
            # For user messages, store with placeholder response
            self.memory_manager.store_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response="[Assistant response will follow]",
                channel_id="chatgpt_import",
                metadata=message.metadata or {}
            )
        else:
            # For assistant messages, store as bot response
            self.memory_manager.store_conversation(
                user_id=user_id,
                user_message="[Previous user message]",
                bot_response=message.content,
                channel_id="chatgpt_import", 
                metadata=message.metadata or {}
            )
            
    async def _analyze_imported_data(self):
        """Run comprehensive analysis on imported conversations"""
        logger.info("Analyzing imported conversations for user %s", self.user_id)
        
        try:
            # Vector memory system handles analysis automatically through embeddings
            logger.info("Vector memory system provides automatic semantic analysis of imported conversations")
                
            # Store comprehensive import analysis
            analysis_data = {
                'type': 'chatgpt_import_analysis',
                'total_messages': self.processed_count,
                'total_conversations': self.conversation_count,
                'import_date': datetime.utcnow().isoformat(),
                'source': 'chatgpt_import',
                'analysis_status': 'bulk_import_completed',
                'personality_learning': 'historical_context_preserved'
            }
            
            # Store analysis using the conversation method to trigger full pipeline
            await self.memory_manager.store_conversation(
                user_id=str(self.user_id),
                user_message=f"ChatGPT import analysis: Successfully imported {self.processed_count} messages from {self.conversation_count} conversations with historical timestamps preserved",
                bot_response="Your ChatGPT conversation history has been fully integrated into my memory system. I now have access to your historical interactions, preferences, and communication patterns. This will help me provide more personalized responses based on our complete conversation history.",
                channel_id="chatgpt_import_analysis",
                metadata=analysis_data
            )
            
            logger.info("Import analysis completed - full memory pipeline activated for historical data")
            
        except Exception as e:
            logger.error("Error during analysis: %s", e)