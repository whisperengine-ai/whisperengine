#!/usr/bin/env python3
"""
Direct Qdrant Import for ChatGPT Conversations
==============================================

Bypasses WhisperEngine's emotion analysis pipeline to directly import
large ChatGPT conversations that exceed RoBERTa's 514 token limit.

Usage:
    python scripts/direct_qdrant_import.py conversations.json 1008886439108411472
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectQdrantImporter:
    def __init__(self, user_id: str, collection_name: str = "whisperengine_memory_aetheris"):
        self.user_id = user_id
        self.collection_name = collection_name
        
        # Connect to Qdrant
        self.client = QdrantClient(host="localhost", port=6334)
        
        # Initialize embedding model
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # Stats
        self.conversation_count = 0
        self.message_count = 0
        self.stored_count = 0
        
    def truncate_text(self, text: str, max_tokens: int = 400) -> str:
        """Truncate text to avoid RoBERTa token limits"""
        words = text.split()
        if len(words) > max_tokens:
            return " ".join(words[:max_tokens]) + "..."
        return text
        
    def extract_conversations(self, data: List[Dict]) -> List[Dict]:
        """Extract conversation messages from ChatGPT export format"""
        conversations = []
        
        for conv_data in data:
            try:
                title = conv_data.get("title", "Untitled")
                create_time = conv_data.get("create_time", 0)
                mapping = conv_data.get("mapping", {})
                
                # Extract messages in chronological order
                messages = []
                for node_id, node_data in mapping.items():
                    if not node_data.get("message"):
                        continue
                        
                    message = node_data["message"]
                    content = message.get("content", {})
                    
                    if content.get("content_type") == "text":
                        parts = content.get("parts", [])
                        if parts and parts[0]:  # Non-empty content
                            role = message.get("author", {}).get("role", "unknown")
                            text_content = parts[0]
                            
                            # Skip empty or system messages
                            if text_content.strip() and role in ["user", "assistant"]:
                                messages.append({
                                    "role": role,
                                    "content": text_content,
                                    "create_time": message.get("create_time") or create_time
                                })
                
                # Sort by create_time
                messages.sort(key=lambda x: x.get("create_time", 0))
                
                if messages:  # Only include conversations with actual messages
                    conversations.append({
                        "title": title,
                        "create_time": create_time,
                        "messages": messages
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to parse conversation: {e}")
                continue
                
        return conversations
        
    async def import_conversations(self, file_path: str):
        """Import conversations directly to Qdrant"""
        logger.info(f"🚀 Starting direct Qdrant import for user {self.user_id}")
        
        # Load conversations
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        conversations = self.extract_conversations(data)
        logger.info(f"📊 Found {len(conversations)} conversations to import")
        
        # Process each conversation
        for i, conversation in enumerate(conversations):
            try:
                await self.process_conversation(conversation, i)
                self.conversation_count += 1
                
                if i % 10 == 0:
                    logger.info(f"📈 Progress: {i}/{len(conversations)} conversations processed")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process conversation {i}: {e}")
                continue
                
        logger.info(f"✅ Import completed!")
        logger.info(f"📊 Stats: {self.conversation_count} conversations, {self.message_count} messages, {self.stored_count} stored")
        
    async def process_conversation(self, conversation: Dict, conv_index: int):
        """Process a single conversation"""
        title = conversation["title"]
        messages = conversation["messages"]
        create_time = conversation["create_time"]
        
        self.message_count += len(messages)
        
        # Create conversation pairs (user + assistant)
        pairs = []
        current_pair = {"user": None, "assistant": None}
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                # Start new pair
                if current_pair["user"] is not None:
                    # Store previous incomplete pair if exists
                    if current_pair["user"]:
                        pairs.append(current_pair)
                
                current_pair = {"user": content, "assistant": None, "timestamp": message.get("create_time", create_time)}
                
            elif role == "assistant" and current_pair["user"] is not None:
                current_pair["assistant"] = content
                pairs.append(current_pair)
                current_pair = {"user": None, "assistant": None}
                
        # Store remaining incomplete pair
        if current_pair["user"]:
            pairs.append(current_pair)
            
        # Store each pair in Qdrant
        for pair_index, pair in enumerate(pairs):
            await self.store_conversation_pair(pair, title, conv_index, pair_index)
            
    async def store_conversation_pair(self, pair: Dict, title: str, conv_index: int, pair_index: int):
        """Store a conversation pair in Qdrant"""
        try:
            user_msg = pair.get("user", "")
            assistant_msg = pair.get("assistant", "")
            timestamp = pair.get("timestamp", datetime.now().timestamp())
            
            # Create conversation content
            if assistant_msg:
                content = f"User: {user_msg}\nAI: {assistant_msg}"
            else:
                content = f"User: {user_msg}"
                
            # Truncate if too long
            content = self.truncate_text(content, max_tokens=400)
            
            # Generate embedding
            embeddings = list(self.embedding_model.embed([content]))
            if not embeddings:
                logger.warning("Failed to generate embedding")
                return
                
            embedding = embeddings[0].tolist()
            
            # Create point for Qdrant
            point_id = str(uuid.uuid4())
            
            # Create named vectors (3D system: content, emotion, semantic)
            vectors = {
                "content": embedding,
                "emotion": embedding,  # Use same embedding for emotion
                "semantic": embedding  # Use same embedding for semantic
            }
            
            # Create payload
            payload = {
                "user_id": self.user_id,
                "bot_name": "aetheris",
                "content": content,
                "user_message": user_msg,
                "bot_response": assistant_msg or "",
                "conversation_title": title,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "timestamp_unix": timestamp,
                "memory_type": "conversation",
                "importance": 0.5,
                "metadata": {
                    "conv_index": conv_index,
                    "pair_index": pair_index,
                    "import_source": "chatgpt_direct"
                }
            }
            
            point = PointStruct(
                id=point_id,
                vector=vectors,
                payload=payload
            )
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.stored_count += 1
            
        except Exception as e:
            logger.error(f"Failed to store conversation pair: {e}")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/direct_qdrant_import.py conversations.json user_id")
        sys.exit(1)
        
    file_path = sys.argv[1]
    user_id = sys.argv[2]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        sys.exit(1)
        
    importer = DirectQdrantImporter(user_id)
    await importer.import_conversations(file_path)

if __name__ == "__main__":
    asyncio.run(main())