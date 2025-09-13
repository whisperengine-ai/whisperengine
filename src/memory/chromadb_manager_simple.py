#!/usr/bin/env python3
"""
ChromaDB Manager - Working Version

Simple, reliable command line utilities to manage ChromaDB datastore.
Handles type safety and provides essential operations for querying and managing data.

Usage:
    # Query operations
    python chromadb_manager_simple.py query conversations --user-id 123456789012345678
    python chromadb_manager_simple.py query user-facts --user-id 123456789012345678
    python chromadb_manager_simple.py query global-facts --limit 10
    python chromadb_manager_simple.py query search --text "tower"
    
    # Info operations
    python chromadb_manager_simple.py info users
    python chromadb_manager_simple.py info stats
    
    # Export operations
    python chromadb_manager_simple.py export user --user-id 123456789012345678
    python chromadb_manager_simple.py export global-facts
    
    # Delete operations (with confirmation and automatic backup)
    python chromadb_manager_simple.py delete user --user-id 123456789012345678 --confirm
    python chromadb_manager_simple.py delete user-facts --user-id 123456789012345678 --confirm
    python chromadb_manager_simple.py delete conversation --doc-id <doc_id> --confirm
    python chromadb_manager_simple.py delete global-fact --fact-id <fact_id> --confirm
    
    # Preview operations (safe, no changes)
    python chromadb_manager_simple.py preview user --user-id 123456789012345678
    python chromadb_manager_simple.py preview conversation --doc-id <doc_id>
    python chromadb_manager_simple.py preview global-fact --fact-id <fact_id>
"""

import argparse
import json
import sys
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaDBManagerSimple:
    """Simple ChromaDB manager with robust error handling"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize ChromaDB client"""
        if persist_directory is None:
            persist_directory = os.getenv("CHROMADB_PATH", "./chromadb_data")
        
        self.persist_directory = persist_directory
            
        try:
            # Use environment variable for telemetry setting
            telemetry_enabled = os.getenv("ANONYMIZED_TELEMETRY", "false").lower() == "true"
            settings = Settings(anonymized_telemetry=telemetry_enabled)
            self.client = chromadb.PersistentClient(path=persist_directory, settings=settings)
            
            # Get collections
            self.user_collection = None
            self.global_collection = None
            
            try:
                collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "user_memories")
                self.user_collection = self.client.get_collection(name=collection_name)
                logger.info(f"Connected to user collection: {collection_name}")
            except Exception as e:
                logger.warning(f"User collection not found: {e}")
            
            try:
                global_collection_name = os.getenv("CHROMADB_GLOBAL_COLLECTION_NAME", "global_facts")
                self.global_collection = self.client.get_collection(name=global_collection_name)
                logger.info(f"Connected to global collection: {global_collection_name}")
            except Exception as e:
                logger.warning(f"Global collection not found: {e}")
            
            # Test connection
            self.client.heartbeat()
            logger.info("ChromaDB connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def safe_get_string(self, value, default: str = "") -> str:
        """Safely convert value to string"""
        if value is None:
            return default
        return str(value)
    
    def safe_truncate(self, text: str, length: int = 200) -> str:
        """Safely truncate text"""
        if not text:
            return ""
        if len(text) > length:
            return text[:length] + "..."
        return text
    
    def create_backup(self, suffix: Optional[str] = None) -> str:
        """Create a backup of the ChromaDB directory before operations"""
        if suffix is None:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = f"chromadb_backup_{suffix}"
        
        try:
            # Copy the entire ChromaDB directory
            shutil.copytree(self.persist_directory, backup_path)
            print(f"✅ Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            print(f"❌ Failed to create backup: {e}")
            raise
    
    def preview_user_deletion(self, user_id: str) -> Dict[str, Any]:
        """Preview what would be deleted for a user (safe, no changes)"""
        if not self.user_collection:
            return {"exists": False, "error": "User collection not found"}
        
        try:
            # Get all user data
            user_data = self.user_collection.get(
                where={"user_id": user_id},
                include=["documents", "metadatas"]
            )
            
            if not user_data or not user_data.get("ids"):
                return {"exists": False}
            
            # Count by type
            conversations = 0
            facts = 0
            channels = set()
            first_seen = None
            last_seen = None
            
            metadatas = user_data.get("metadatas")
            if metadatas:
                for metadata in metadatas:
                    if metadata and self.safe_get_string(metadata.get("type")) == "user_fact":
                        facts += 1
                    else:
                        conversations += 1
                    
                    # Track timestamps
                    timestamp = metadata.get("timestamp") if metadata else None
                    if timestamp:
                        if not first_seen or timestamp < first_seen:
                            first_seen = timestamp
                        if not last_seen or timestamp > last_seen:
                            last_seen = timestamp
                    
                    # Track channels
                    channel_id = metadata.get("channel_id") if metadata else None
                    if channel_id:
                        channels.add(channel_id)
            
            return {
                "exists": True,
                "user_id": user_id,
                "total_items": len(user_data["ids"]),
                "conversations": conversations,
                "facts": facts,
                "channels": list(channels),
                "first_seen": first_seen,
                "last_seen": last_seen
            }
            
        except Exception as e:
            logger.error(f"Error previewing user deletion: {e}")
            return {"exists": False, "error": str(e)}
    
    def preview_conversation_deletion(self, doc_id: str) -> Dict[str, Any]:
        """Preview what conversation would be deleted (safe, no changes)"""
        if not self.user_collection:
            return {"exists": False, "error": "User collection not found"}
        
        try:
            # Get the specific document
            doc_data = self.user_collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if not doc_data or not doc_data.get("ids"):
                return {"exists": False}
            
            metadata = doc_data["metadatas"][0] if doc_data.get("metadatas") and doc_data["metadatas"][0] else {}
            document = doc_data["documents"][0] if doc_data.get("documents") else ""
            
            return {
                "exists": True,
                "doc_id": doc_id,
                "user_id": self.safe_get_string(metadata.get("user_id", "unknown")),
                "timestamp": self.safe_get_string(metadata.get("timestamp", "unknown")),
                "channel_id": self.safe_get_string(metadata.get("channel_id", "dm")),
                "type": self.safe_get_string(metadata.get("type", "conversation")),
                "user_message": self.safe_truncate(self.safe_get_string(metadata.get("user_message", "")), 200),
                "bot_response": self.safe_truncate(self.safe_get_string(metadata.get("bot_response", "")), 200),
                "document_preview": self.safe_truncate(document, 200)
            }
            
        except Exception as e:
            logger.error(f"Error previewing conversation deletion: {e}")
            return {"exists": False, "error": str(e)}
    
    def preview_global_fact_deletion(self, fact_id: str) -> Dict[str, Any]:
        """Preview what global fact would be deleted (safe, no changes)"""
        if not self.global_collection:
            return {"exists": False, "error": "Global collection not found"}
        
        try:
            # Get the specific fact
            fact_data = self.global_collection.get(
                ids=[fact_id],
                include=["documents", "metadatas"]
            )
            
            if not fact_data or not fact_data.get("ids"):
                return {"exists": False}
            
            metadata = fact_data["metadatas"][0] if fact_data.get("metadatas") and fact_data["metadatas"][0] else {}
            document = fact_data["documents"][0] if fact_data.get("documents") else ""
            
            return {
                "exists": True,
                "fact_id": fact_id,
                "fact": self.safe_get_string(metadata.get("fact", document)),
                "category": self.safe_get_string(metadata.get("category", "unknown")),
                "added_by": self.safe_get_string(metadata.get("added_by", "unknown")),
                "extraction_method": self.safe_get_string(metadata.get("extraction_method", "unknown")),
                "timestamp": self.safe_get_string(metadata.get("timestamp", "unknown")),
                "context": self.safe_truncate(self.safe_get_string(metadata.get("context", "")), 200)
            }
            
        except Exception as e:
            logger.error(f"Error previewing global fact deletion: {e}")
            return {"exists": False, "error": str(e)}
    
    def query_conversations(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Query conversation history"""
        if not self.user_collection:
            print("❌ User collection not found")
            return []
        
        try:
            # Build where clause
            where_conditions = {}
            if user_id:
                where_conditions["user_id"] = user_id
            
            # Get documents
            results = self.user_collection.get(
                where=where_conditions if where_conditions else None,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            conversations = []
            
            # Safe access to results
            if results and results.get("documents") and results.get("metadatas") and results.get("ids"):
                documents = results["documents"]
                metadatas = results["metadatas"]
                ids = results["ids"]
                
                for i in range(min(len(documents), len(metadatas), len(ids))):
                    metadata = metadatas[i] if metadatas[i] else {}
                    
                    # Skip non-conversation entries (facts, etc.)
                    if metadata.get("type") not in [None, "conversation"]:
                        continue
                    
                    conversations.append({
                        "id": ids[i],
                        "document": documents[i],
                        "metadata": metadata,
                        "user_message": self.safe_get_string(metadata.get("user_message", "")),
                        "bot_response": self.safe_get_string(metadata.get("bot_response", "")),
                        "timestamp": self.safe_get_string(metadata.get("timestamp", "")),
                        "channel_id": self.safe_get_string(metadata.get("channel_id", "dm")),
                        "user_id": self.safe_get_string(metadata.get("user_id", "unknown"))
                    })
            
            return sorted(conversations, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error querying conversations: {e}")
            return []
    
    def query_user_facts(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Query user-specific facts"""
        if not self.user_collection:
            print("❌ User collection not found")
            return []
        
        try:
            results = self.user_collection.get(
                where={"$and": [{"user_id": user_id}, {"type": "user_fact"}]},
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            facts = []
            
            if results and results.get("documents") and results.get("metadatas") and results.get("ids"):
                documents = results["documents"]
                metadatas = results["metadatas"]
                ids = results["ids"]
                
                for i in range(min(len(documents), len(metadatas), len(ids))):
                    metadata = metadatas[i] if metadatas[i] else {}
                    
                    facts.append({
                        "id": ids[i],
                        "fact": self.safe_get_string(metadata.get("fact", documents[i])),
                        "category": self.safe_get_string(metadata.get("category", "unknown")),
                        "confidence": metadata.get("confidence", 0),
                        "source": self.safe_get_string(metadata.get("source", "unknown")),
                        "extraction_method": self.safe_get_string(metadata.get("extraction_method", "unknown")),
                        "timestamp": self.safe_get_string(metadata.get("timestamp", "")),
                        "context": self.safe_get_string(metadata.get("context", ""))
                    })
            
            return sorted(facts, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error querying user facts: {e}")
            return []
    
    def query_global_facts(self, limit: int = 100, search_text: Optional[str] = None) -> List[Dict]:
        """Query global facts with optional text search"""
        if not self.global_collection:
            print("❌ Global collection not found")
            return []
        
        try:
            facts = []
            
            if search_text:
                # Perform similarity search
                results = self.global_collection.query(
                    query_texts=[search_text],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                
                if (results and results.get("documents") and len(results["documents"]) > 0 and 
                    results.get("metadatas") and len(results["metadatas"]) > 0 and
                    results.get("ids") and len(results["ids"]) > 0):
                    
                    documents = results["documents"][0]
                    metadatas = results["metadatas"][0]
                    ids = results["ids"][0]
                    distances = results["distances"][0] if results.get("distances") and len(results["distances"]) > 0 else []
                    
                    for i in range(min(len(documents), len(metadatas), len(ids))):
                        metadata = metadatas[i] if metadatas[i] else {}
                        distance = distances[i] if i < len(distances) else 1.0
                        
                        facts.append({
                            "id": ids[i],
                            "fact": self.safe_get_string(metadata.get("fact", documents[i])),
                            "category": self.safe_get_string(metadata.get("category", "unknown")),
                            "confidence": metadata.get("confidence", 0),
                            "added_by": self.safe_get_string(metadata.get("added_by", "unknown")),
                            "extraction_method": self.safe_get_string(metadata.get("extraction_method", "unknown")),
                            "timestamp": self.safe_get_string(metadata.get("timestamp", "")),
                            "context": self.safe_get_string(metadata.get("context", "")),
                            "similarity_score": 1 - distance
                        })
            else:
                # Get all global facts
                results = self.global_collection.get(
                    limit=limit,
                    include=["documents", "metadatas"]
                )
                
                if results and results.get("documents") and results.get("metadatas") and results.get("ids"):
                    documents = results["documents"]
                    metadatas = results["metadatas"]
                    ids = results["ids"]
                    
                    for i in range(min(len(documents), len(metadatas), len(ids))):
                        metadata = metadatas[i] if metadatas[i] else {}
                        
                        facts.append({
                            "id": ids[i],
                            "fact": self.safe_get_string(metadata.get("fact", documents[i])),
                            "category": self.safe_get_string(metadata.get("category", "unknown")),
                            "confidence": metadata.get("confidence", 0),
                            "added_by": self.safe_get_string(metadata.get("added_by", "unknown")),
                            "extraction_method": self.safe_get_string(metadata.get("extraction_method", "unknown")),
                            "timestamp": self.safe_get_string(metadata.get("timestamp", "")),
                            "context": self.safe_get_string(metadata.get("context", ""))
                        })
            
            return sorted(facts, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error querying global facts: {e}")
            return []
    
    def search_all_data(self, search_text: str, limit: int = 20) -> Dict[str, List[Dict]]:
        """Search across all collections for text"""
        results = {
            "conversations": [],
            "user_facts": [],
            "global_facts": []
        }
        
        # Search conversations and user facts
        if self.user_collection:
            try:
                conv_results = self.user_collection.query(
                    query_texts=[search_text],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                
                if (conv_results and conv_results.get("documents") and len(conv_results["documents"]) > 0 and
                    conv_results.get("metadatas") and len(conv_results["metadatas"]) > 0 and
                    conv_results.get("ids") and len(conv_results["ids"]) > 0):
                    
                    documents = conv_results["documents"][0]
                    metadatas = conv_results["metadatas"][0]
                    ids = conv_results["ids"][0]
                    distances = conv_results["distances"][0] if conv_results.get("distances") and len(conv_results["distances"]) > 0 else []
                    
                    for i in range(min(len(documents), len(metadatas), len(ids))):
                        metadata = metadatas[i] if metadatas[i] else {}
                        distance = distances[i] if i < len(distances) else 1.0
                        result_type = self.safe_get_string(metadata.get("type", "conversation"))
                        
                        item = {
                            "id": ids[i],
                            "document": documents[i],
                            "metadata": metadata,
                            "similarity_score": 1 - distance,
                            "timestamp": self.safe_get_string(metadata.get("timestamp", ""))
                        }
                        
                        if result_type == "user_fact":
                            results["user_facts"].append(item)
                        else:
                            results["conversations"].append(item)
                            
            except Exception as e:
                logger.error(f"Error searching user collection: {e}")
        
        # Search global facts
        if self.global_collection:
            try:
                global_results = self.global_collection.query(
                    query_texts=[search_text],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                
                if (global_results and global_results.get("documents") and len(global_results["documents"]) > 0 and
                    global_results.get("metadatas") and len(global_results["metadatas"]) > 0 and
                    global_results.get("ids") and len(global_results["ids"]) > 0):
                    
                    documents = global_results["documents"][0]
                    metadatas = global_results["metadatas"][0]
                    ids = global_results["ids"][0]
                    distances = global_results["distances"][0] if global_results.get("distances") and len(global_results["distances"]) > 0 else []
                    
                    for i in range(min(len(documents), len(metadatas), len(ids))):
                        metadata = metadatas[i] if metadatas[i] else {}
                        distance = distances[i] if i < len(distances) else 1.0
                        
                        results["global_facts"].append({
                            "id": ids[i],
                            "document": documents[i],
                            "metadata": metadata,
                            "similarity_score": 1 - distance,
                            "timestamp": self.safe_get_string(metadata.get("timestamp", ""))
                        })
                        
            except Exception as e:
                logger.error(f"Error searching global collection: {e}")
        
        return results
    
    def get_users_list(self) -> List[Dict[str, Any]]:
        """Get list of all users with basic statistics"""
        if not self.user_collection:
            return []
        
        try:
            user_data = self.user_collection.get(include=["metadatas"])
            
            # Group by user ID
            users_info = {}
            
            if user_data and user_data.get("metadatas"):
                for metadata in user_data["metadatas"]:
                    if not metadata:
                        continue
                        
                    user_id = self.safe_get_string(metadata.get("user_id"))
                    if not user_id or user_id == "unknown":
                        continue
                    
                    if user_id not in users_info:
                        users_info[user_id] = {
                            "user_id": user_id,
                            "conversations": 0,
                            "facts": 0,
                            "first_seen": None,
                            "last_seen": None,
                            "channels": set()
                        }
                    
                    # Update counts
                    if self.safe_get_string(metadata.get("type")) == "user_fact":
                        users_info[user_id]["facts"] += 1
                    else:
                        users_info[user_id]["conversations"] += 1
                    
                    # Update timestamps
                    timestamp = self.safe_get_string(metadata.get("timestamp"))
                    if timestamp:
                        if not users_info[user_id]["first_seen"] or timestamp < users_info[user_id]["first_seen"]:
                            users_info[user_id]["first_seen"] = timestamp
                        if not users_info[user_id]["last_seen"] or timestamp > users_info[user_id]["last_seen"]:
                            users_info[user_id]["last_seen"] = timestamp
                    
                    # Track channels
                    channel_id = self.safe_get_string(metadata.get("channel_id"))
                    if channel_id and channel_id != "unknown":
                        users_info[user_id]["channels"].add(channel_id)
            
            # Convert sets to lists and sort by last seen
            for user_info in users_info.values():
                user_info["channels"] = list(user_info["channels"])
            
            return sorted(users_info.values(), 
                         key=lambda x: x["last_seen"] or "", reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {
            "collections": {},
            "user_data": {},
            "global_data": {}
        }
        
        # User collection stats
        if self.user_collection:
            try:
                user_data = self.user_collection.get(include=["metadatas"])
                
                if user_data and user_data.get("metadatas"):
                    # Count by type
                    conversations = 0
                    user_facts = 0
                    user_ids = set()
                    
                    for metadata in user_data["metadatas"]:
                        if not metadata:
                            continue
                            
                        if self.safe_get_string(metadata.get("type")) == "user_fact":
                            user_facts += 1
                        else:
                            conversations += 1
                        
                        user_id = self.safe_get_string(metadata.get("user_id"))
                        if user_id and user_id != "unknown":
                            user_ids.add(user_id)
                    
                    total_docs = len(user_data.get("ids", []))
                    
                    stats["collections"]["user_memories"] = {
                        "total_documents": total_docs,
                        "conversations": conversations,
                        "user_facts": user_facts,
                        "unique_users": len(user_ids)
                    }
                    
                    stats["user_data"] = {
                        "unique_users": len(user_ids),
                        "total_conversations": conversations,
                        "total_user_facts": user_facts
                    }
                
            except Exception as e:
                logger.error(f"Error getting user collection stats: {e}")
                stats["collections"]["user_memories"] = {"error": str(e)}
        
        # Global collection stats
        if self.global_collection:
            try:
                global_data = self.global_collection.get(include=["metadatas"])
                
                if global_data and global_data.get("metadatas"):
                    # Count by extraction method
                    auto_facts = 0
                    manual_facts = 0
                    
                    for metadata in global_data["metadatas"]:
                        if not metadata:
                            continue
                            
                        method = self.safe_get_string(metadata.get("extraction_method"))
                        if method == "automatic":
                            auto_facts += 1
                        elif method == "manual":
                            manual_facts += 1
                    
                    total_docs = len(global_data.get("ids", []))
                    
                    stats["collections"]["global_facts"] = {
                        "total_documents": total_docs,
                        "automatic_facts": auto_facts,
                        "manual_facts": manual_facts
                    }
                    
                    stats["global_data"] = {
                        "total_global_facts": total_docs,
                        "automatic_extractions": auto_facts,
                        "manual_entries": manual_facts
                    }
                
            except Exception as e:
                logger.error(f"Error getting global collection stats: {e}")
                stats["collections"]["global_facts"] = {"error": str(e)}
        
        return stats
    
    def export_user_data(self, user_id: str, output_file: Optional[str] = None, format_type: str = "json", 
                        facts_only: bool = False, stats_only: bool = False) -> Optional[str]:
        """Export all data for a specific user"""
        conversations = [] if facts_only else self.query_conversations(user_id=user_id, limit=10000)
        facts = self.query_user_facts(user_id=user_id, limit=10000)
        
        if not conversations and not facts:
            print(f"❌ No data found for user {user_id}")
            return None
        
        # Stats-only mode
        if stats_only:
            stats = {
                "user_id": user_id,
                "total_conversations": len(conversations),
                "total_facts": len(facts),
                "total_entries": len(conversations) + len(facts)
            }
            print(f"📊 User Statistics for {user_id}:")
            print(f"   Conversations: {stats['total_conversations']}")
            print(f"   Facts: {stats['total_facts']}")  
            print(f"   Total Entries: {stats['total_entries']}")
            return None
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_facts" if facts_only else ""
            extension = ".txt" if format_type == "text" else ".json"
            output_file = f"user_data_export_{user_id}{suffix}_{timestamp}{extension}"
        
        try:
            if format_type == "text":
                # Generate text format
                lines = []
                lines.append(f"ChromaDB User Data Export")
                lines.append(f"=" * 50)
                lines.append(f"User ID: {user_id}")
                lines.append(f"Export Date: {datetime.now().isoformat()}")
                lines.append(f"Total Conversations: {len(conversations)}")
                lines.append(f"Total Facts: {len(facts)}")
                lines.append("")
                
                if not facts_only and conversations:
                    lines.append(f"CONVERSATIONS ({len(conversations)} entries)")
                    lines.append("-" * 50)
                    for i, conv in enumerate(conversations, 1):
                        lines.append(f"\n[{i}] Conversation ID: {conv['id']}")
                        lines.append(f"    Timestamp: {conv['timestamp']}")
                        lines.append(f"    Channel: {conv.get('channel_id', 'dm')}")
                        lines.append(f"    User: {conv.get('user_message', 'N/A')}")
                        lines.append(f"    Bot: {conv.get('bot_response', 'N/A')}")
                
                if facts:
                    lines.append(f"\n\nFACTS ({len(facts)} entries)")
                    lines.append("-" * 50)
                    for i, fact in enumerate(facts, 1):
                        lines.append(f"\n[{i}] Fact ID: {fact['id']}")
                        lines.append(f"    Timestamp: {fact['timestamp']}")
                        lines.append(f"    Fact: {fact.get('fact', 'N/A')}")
                        lines.append(f"    Category: {fact.get('category', 'N/A')}")
                        lines.append(f"    Method: {fact.get('extraction_method', 'N/A')}")
                        if fact.get('context'):
                            lines.append(f"    Context: {fact['context']}")
                
                content = "\n".join(lines)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # Generate JSON format
                export_data = {
                    "export_type": "user_data",
                    "exported_at": datetime.now().isoformat(),
                    "user_id": user_id,
                    "conversations": {
                        "count": len(conversations),
                        "data": conversations
                    } if not facts_only else None,
                    "facts": {
                        "count": len(facts),
                        "data": facts
                    }
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            conv_msg = f"{len(conversations)} conversations and " if not facts_only else ""
            print(f"✅ Exported {conv_msg}{len(facts)} facts to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            print(f"❌ Error exporting user data: {e}")
            return None
    
    def export_global_facts(self, output_file: Optional[str] = None) -> Optional[str]:
        """Export global facts to JSON file"""
        facts = self.query_global_facts(limit=10000)
        
        if not facts:
            print("❌ No global facts found to export")
            return None
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"global_facts_export_{timestamp}.json"
        
        try:
            export_data = {
                "export_type": "global_facts",
                "exported_at": datetime.now().isoformat(),
                "total_facts": len(facts),
                "facts": facts
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(facts)} global facts to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting global facts: {e}")
            print(f"❌ Error exporting global facts: {e}")
            return None
    
    def delete_user_data(self, user_id: str, confirm: bool = False, create_backup: bool = True) -> bool:
        """Delete all data for a specific user"""
        if not confirm:
            print("❌ This operation requires --confirm flag")
            return False
        
        if not self.user_collection:
            print("❌ User collection not found")
            return False
        
        try:
            # Get all user data first to show what will be deleted
            user_data = self.user_collection.get(
                where={"user_id": user_id},
                include=["documents", "metadatas"]
            )
            
            if not user_data or not user_data.get("ids"):
                print(f"❌ No data found for user {user_id}")
                return False
            
            total_items = len(user_data["ids"])
            print(f"🔍 Found {total_items} items for user {user_id}")
            
            # Count by type
            conversations = 0
            facts = 0
            metadatas = user_data.get("metadatas")
            if metadatas:
                for metadata in metadatas:
                    if metadata and self.safe_get_string(metadata.get("type")) == "user_fact":
                        facts += 1
                    else:
                        conversations += 1
            
            print(f"   - {conversations} conversations")
            print(f"   - {facts} user facts")
            
            # Create backup if requested
            if create_backup:
                try:
                    self.create_backup(f"before_user_delete_{user_id}")
                except Exception as e:
                    print(f"❌ Failed to create backup: {e}")
                    return False
            
            # Delete all user data
            self.user_collection.delete(where={"user_id": user_id})
            print(f"✅ Successfully deleted all data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            print(f"❌ Error deleting user data: {e}")
            return False
    
    def delete_global_fact(self, fact_id: str, confirm: bool = False, create_backup: bool = True) -> bool:
        """Delete a specific global fact"""
        if not confirm:
            print("❌ This operation requires --confirm flag")
            return False
        
        if not self.global_collection:
            print("❌ Global collection not found")
            return False
        
        try:
            # Check if fact exists
            fact_data = self.global_collection.get(
                ids=[fact_id],
                include=["documents", "metadatas"]
            )
            
            if not fact_data or not fact_data.get("ids"):
                print(f"❌ Global fact {fact_id} not found")
                return False
            
            metadata = fact_data["metadatas"][0] if fact_data.get("metadatas") and fact_data["metadatas"] else {}
            document = fact_data["documents"][0] if fact_data.get("documents") and fact_data["documents"] else ""
            
            fact_text = self.safe_get_string(metadata.get("fact", document))
            print(f"🔍 Found global fact: {self.safe_truncate(fact_text, 100)}")
            print(f"   Added by: {self.safe_get_string(metadata.get('added_by', 'unknown'))}")
            print(f"   Timestamp: {self.safe_get_string(metadata.get('timestamp', 'unknown'))}")
            
            # Create backup if requested
            if create_backup:
                try:
                    self.create_backup(f"before_global_fact_delete_{fact_id[:8]}")
                except Exception as e:
                    print(f"❌ Failed to create backup: {e}")
                    return False
            
            # Delete the fact
            self.global_collection.delete(ids=[fact_id])
            print(f"✅ Successfully deleted global fact {fact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting global fact: {e}")
            print(f"❌ Error deleting global fact: {e}")
            return False
    
    def delete_user_facts(self, user_id: str, confirm: bool = False, create_backup: bool = True) -> bool:
        """Delete only facts for a specific user (keep conversations)"""
        if not confirm:
            print("❌ This operation requires --confirm flag")
            return False
        
        if not self.user_collection:
            print("❌ User collection not found")
            return False
        
        try:
            # Get user facts first
            user_facts = self.user_collection.get(
                where={"user_id": user_id, "type": "user_fact"},
                include=["documents", "metadatas"]
            )
            
            if not user_facts or not user_facts.get("ids"):
                print(f"❌ No facts found for user {user_id}")
                return False
            
            print(f"🔍 Will delete {len(user_facts['ids'])} facts for user {user_id}")
            
            # Create backup if requested
            if create_backup:
                try:
                    self.create_backup(f"before_user_facts_delete_{user_id}")
                except Exception as e:
                    print(f"❌ Failed to create backup: {e}")
                    return False
            
            # Delete all user facts
            self.user_collection.delete(where={"user_id": user_id, "type": "user_fact"})
            print(f"✅ Successfully deleted {len(user_facts['ids'])} facts for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user facts: {e}")
            print(f"❌ Error deleting user facts: {e}")
            return False
    
    def delete_conversation(self, doc_id: str, confirm: bool = False, create_backup: bool = True) -> bool:
        """Delete a specific conversation"""
        if not confirm:
            print("❌ This operation requires --confirm flag")
            return False
        
        if not self.user_collection:
            print("❌ User collection not found")
            return False
        
        # Preview what will be deleted
        preview = self.preview_conversation_deletion(doc_id)
        if not preview["exists"]:
            print(f"❌ Conversation {doc_id} not found")
            return False
        
        print(f"🔍 Will delete conversation:")
        print(f"   - ID: {doc_id}")
        print(f"   - User: {preview['user_id']}")
        print(f"   - Timestamp: {preview['timestamp']}")
        print(f"   - Channel: {preview['channel_id']}")
        print(f"   - Type: {preview['type']}")
        print(f"   - User message: {preview['user_message']}")
        
        # Create backup if requested
        if create_backup:
            try:
                self.create_backup(f"before_conversation_delete_{doc_id[:8]}")
            except Exception as e:
                print(f"❌ Failed to create backup: {e}")
                return False
        
        try:
            # Delete the conversation
            self.user_collection.delete(ids=[doc_id])
            print(f"✅ Successfully deleted conversation {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            print(f"❌ Error deleting conversation: {e}")
            return False
    
    def import_user_data(self, filename: str, user_id: Optional[str] = None, dry_run: bool = False) -> bool:
        """Import user data from JSON export file"""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return False
        
        if not self.user_collection:
            print("❌ User collection not found")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate JSON structure
            if not isinstance(data, dict) or 'conversations' not in data or 'facts' not in data:
                print("❌ Invalid export file format")
                return False
            
            # Get user ID from file or parameter
            import_user_id = user_id or data.get('user_id')
            if not import_user_id:
                print("❌ No user ID specified and none found in file")
                return False
            
            conversations = data.get('conversations', {}).get('data', [])
            facts = data.get('facts', {}).get('data', [])
            
            print(f"📁 Found {len(conversations)} conversations and {len(facts)} facts for user {import_user_id}")
            
            if dry_run:
                print("🔍 DRY RUN - No data will be imported")
                print(f"   Would import {len(conversations)} conversations")
                print(f"   Would import {len(facts)} facts")
                return True
            
            # Check if user already has data
            existing_data = self.user_collection.get(
                where={"user_id": import_user_id},
                limit=1
            )
            
            if existing_data and existing_data.get("ids"):
                response = input(f"⚠️  User {import_user_id} already has data. Overwrite? (y/N): ").strip().lower()
                if response != 'y':
                    print("❌ Import cancelled")
                    return False
                
                # Delete existing data
                print(f"🗑️  Deleting existing data for user {import_user_id}")
                self.user_collection.delete(where={"user_id": import_user_id})
            
            # Import conversations
            conversation_count = 0
            for conv in conversations:
                try:
                    # Reconstruct document format
                    user_msg = conv.get('user_message', '')
                    bot_msg = conv.get('bot_response', '')
                    document = f"User: {user_msg}\nAssistant: {bot_msg}"
                    
                    # Prepare metadata
                    metadata = {
                        "user_id": import_user_id,
                        "user_message": user_msg,
                        "bot_response": bot_msg,
                        "timestamp": conv.get('timestamp', ''),
                        "channel_id": conv.get('channel_id', 'dm')
                    }
                    
                    # Add any additional metadata from the conversation
                    if 'metadata' in conv and isinstance(conv['metadata'], dict):
                        for key, value in conv['metadata'].items():
                            if key not in metadata:  # Don't overwrite core fields
                                metadata[key] = value
                    
                    # Generate embeddings and add to collection
                    self.user_collection.add(
                        ids=[conv.get('id', f"{import_user_id}_imported_{conversation_count}")],
                        documents=[document],
                        metadatas=[metadata]
                    )
                    conversation_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import conversation {conv.get('id', 'unknown')}: {e}")
                    continue
            
            # Import facts
            fact_count = 0
            for fact in facts:
                try:
                    # Prepare metadata for facts
                    metadata = {
                        "user_id": import_user_id,
                        "type": "user_fact",
                        "fact": fact.get('fact', ''),
                        "category": fact.get('category', 'unknown'),
                        "confidence": fact.get('confidence', 0.95),
                        "extraction_method": fact.get('extraction_method', 'imported'),
                        "timestamp": fact.get('timestamp', ''),
                        "context": fact.get('context', '')
                    }
                    
                    # Use fact text as document
                    document = fact.get('fact', '')
                    
                    # Generate embeddings and add to collection
                    self.user_collection.add(
                        ids=[fact.get('id', f"{import_user_id}_fact_imported_{fact_count}")],
                        documents=[document],
                        metadatas=[metadata]
                    )
                    fact_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import fact {fact.get('id', 'unknown')}: {e}")
                    continue
            
            print(f"✅ Successfully imported {conversation_count} conversations and {fact_count} facts for user {import_user_id}")
            return True
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON file format")
            return False
        except Exception as e:
            logger.error(f"Error importing user data: {e}")
            print(f"❌ Error importing user data: {e}")
            return False
    
    def import_global_facts(self, filename: str, dry_run: bool = False) -> bool:
        """Import global facts from JSON export file"""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return False
        
        if not self.global_collection:
            print("❌ Global collection not found")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate JSON structure
            if not isinstance(data, dict) or 'facts' not in data:
                print("❌ Invalid global facts export file format")
                return False
            
            facts = data.get('facts', [])
            print(f"📁 Found {len(facts)} global facts to import")
            
            if dry_run:
                print("🔍 DRY RUN - No data will be imported")
                print(f"   Would import {len(facts)} global facts")
                return True
            
            # Import facts
            fact_count = 0
            for fact in facts:
                try:
                    # Prepare metadata
                    metadata = {
                        "fact": fact.get('fact', ''),
                        "category": fact.get('category', 'unknown'),
                        "added_by": fact.get('added_by', 'imported'),
                        "extraction_method": fact.get('extraction_method', 'imported'),
                        "timestamp": fact.get('timestamp', ''),
                        "context": fact.get('context', '')
                    }
                    
                    # Use fact text as document
                    document = fact.get('fact', '')
                    
                    # Generate embeddings and add to collection
                    self.global_collection.add(
                        ids=[fact.get('id', f"global_fact_imported_{fact_count}")],
                        documents=[document],
                        metadatas=[metadata]
                    )
                    fact_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import global fact {fact.get('id', 'unknown')}: {e}")
                    continue
            
            print(f"✅ Successfully imported {fact_count} global facts")
            return True
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON file format")
            return False
        except Exception as e:
            logger.error(f"Error importing global facts: {e}")
            print(f"❌ Error importing global facts: {e}")
            return False


def print_formatted_results(data: List[Dict], result_type: str, limit: Optional[int] = None):
    """Print query results in a formatted way"""
    if not data:
        print(f"❌ No {result_type} found")
        return
    
    # Apply limit if specified
    if limit and len(data) > limit:
        display_data = data[:limit]
        print(f"🔍 Showing first {limit} of {len(data)} {result_type}")
    else:
        display_data = data
        print(f"🔍 Found {len(data)} {result_type}")
    
    print("=" * 80)
    
    for i, item in enumerate(display_data, 1):
        if result_type == "conversations":
            print(f"\n[{i}] Conversation ID: {item['id']}")
            print(f"    User ID: {item.get('user_id', item['metadata'].get('user_id', 'unknown'))}")
            print(f"    Timestamp: {item['timestamp']}")
            print(f"    Channel: {item.get('channel_id', item['metadata'].get('channel_id', 'unknown'))}")
            
            # Handle different data structures
            if 'user_message' in item:
                user_msg = item['user_message'][:100] + "..." if len(item['user_message']) > 100 else item['user_message']
                bot_msg = item['bot_response'][:100] + "..." if len(item['bot_response']) > 100 else item['bot_response']
            else:
                # Search results format
                user_msg = item['metadata'].get('user_message', item.get('document', ''))[:100] + "..."
                bot_msg = item['metadata'].get('bot_response', '')[:100] + "..." if item['metadata'].get('bot_response') else 'N/A'
            
            print(f"    User: {user_msg}")
            print(f"    Bot: {bot_msg}")
            if item.get('similarity_score'):
                print(f"    Similarity: {item['similarity_score']:.3f}")
            
        elif result_type == "user_facts":
            print(f"\n[{i}] Fact ID: {item['id']}")
            
            # Handle different data structures
            if 'fact' in item:
                fact_text = item['fact']
            else:
                # Search results format
                fact_text = item['metadata'].get('fact', item.get('document', ''))
            
            print(f"    Fact: {fact_text}")
            print(f"    Category: {item.get('category', item['metadata'].get('category', 'unknown'))}")
            print(f"    Confidence: {item.get('confidence', item['metadata'].get('confidence', 'unknown'))}")
            print(f"    Method: {item.get('extraction_method', item['metadata'].get('extraction_method', 'unknown'))}")
            print(f"    Timestamp: {item['timestamp']}")
            
            context = item.get('context', item['metadata'].get('context', ''))
            if context:
                context_display = context[:100] + "..." if len(context) > 100 else context
                print(f"    Context: {context_display}")
            
            if item.get('similarity_score'):
                print(f"    Similarity: {item['similarity_score']:.3f}")
                
        elif result_type == "global_facts":
            print(f"\n[{i}] Fact ID: {item['id']}")
            
            # Handle different data structures
            if 'fact' in item:
                fact_text = item['fact']
            else:
                # Search results format
                fact_text = item['metadata'].get('fact', item.get('document', ''))
            
            print(f"    Fact: {fact_text}")
            print(f"    Category: {item.get('category', item['metadata'].get('category', 'unknown'))}")
            print(f"    Added by: {item.get('added_by', item['metadata'].get('added_by', 'unknown'))}")
            print(f"    Method: {item.get('extraction_method', item['metadata'].get('extraction_method', 'unknown'))}")
            print(f"    Timestamp: {item['timestamp']}")
            
            context = item.get('context', item['metadata'].get('context', ''))
            if context:
                context_display = context[:100] + "..." if len(context) > 100 else context
                print(f"    Context: {context_display}")
            
            if item.get('similarity_score'):
                print(f"    Similarity: {item['similarity_score']:.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="ChromaDB Manager - Simple Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Add chromadb path option
    parser.add_argument(
        '--chromadb-path', 
        default=None,
        help='Path to ChromaDB directory (default: ./chromadb_data)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Query commands
    query_parser = subparsers.add_parser('query', help='Query database')
    query_subparsers = query_parser.add_subparsers(dest='query_type', help='Query types')
    
    # Query conversations
    conv_parser = query_subparsers.add_parser('conversations', help='Query conversations')
    conv_parser.add_argument('--user-id', help='Filter by user ID')
    conv_parser.add_argument('--limit', type=int, default=50, help='Limit results')
    
    # Query user facts
    user_facts_parser = query_subparsers.add_parser('user-facts', help='Query user facts')
    user_facts_parser.add_argument('--user-id', required=True, help='User ID')
    user_facts_parser.add_argument('--limit', type=int, default=100, help='Limit results')
    
    # Query global facts
    global_facts_parser = query_subparsers.add_parser('global-facts', help='Query global facts')
    global_facts_parser.add_argument('--limit', type=int, default=100, help='Limit results')
    global_facts_parser.add_argument('--search', help='Search text in facts')
    
    # Search all data
    search_parser = query_subparsers.add_parser('search', help='Search all data')
    search_parser.add_argument('--text', required=True, help='Search text')
    search_parser.add_argument('--limit', type=int, default=20, help='Limit results per type')
    
    # Info commands
    info_parser = subparsers.add_parser('info', help='Get database information')
    info_subparsers = info_parser.add_subparsers(dest='info_type', help='Info types')
    
    info_subparsers.add_parser('users', help='List all users')
    info_subparsers.add_parser('stats', help='Database statistics')
    
    # Export commands
    export_parser = subparsers.add_parser('export', help='Export data')
    export_subparsers = export_parser.add_subparsers(dest='export_type', help='Export types')
    
    # Export user data
    export_user_parser = export_subparsers.add_parser('user', help='Export user data')
    export_user_parser.add_argument('--user-id', required=True, help='User ID')
    export_user_parser.add_argument('--output', help='Output filename')
    export_user_parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format (default: json)')
    export_user_parser.add_argument('--facts-only', action='store_true', help='Export only facts, exclude conversations')
    export_user_parser.add_argument('--stats-only', action='store_true', help='Show only statistics, not full data')
    
    # Export global facts
    export_global_parser = export_subparsers.add_parser('global-facts', help='Export global facts')
    export_global_parser.add_argument('--output', help='Output filename')
    
    # Delete commands
    delete_parser = subparsers.add_parser('delete', help='Delete data (requires --confirm)')
    delete_subparsers = delete_parser.add_subparsers(dest='delete_type', help='Delete types')
    
    # Delete user data
    user_delete_parser = delete_subparsers.add_parser('user', help='Delete all user data')
    user_delete_parser.add_argument('--user-id', required=True, help='User ID')
    user_delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    user_delete_parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    
    # Delete user facts only
    user_facts_delete_parser = delete_subparsers.add_parser('user-facts', help='Delete user facts only (keep conversations)')
    user_facts_delete_parser.add_argument('--user-id', required=True, help='User ID')
    user_facts_delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    user_facts_delete_parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    
    # Delete conversation
    conversation_delete_parser = delete_subparsers.add_parser('conversation', help='Delete specific conversation')
    conversation_delete_parser.add_argument('--doc-id', required=True, help='Document ID')
    conversation_delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    conversation_delete_parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    
    # Delete global fact
    global_delete_parser = delete_subparsers.add_parser('global-fact', help='Delete global fact')
    global_delete_parser.add_argument('--fact-id', required=True, help='Fact ID')
    global_delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    global_delete_parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    
    # Import commands
    import_parser = subparsers.add_parser('import', help='Import data from JSON files')
    import_subparsers = import_parser.add_subparsers(dest='import_type', help='Import types')
    
    # Import user data
    user_import_parser = import_subparsers.add_parser('user', help='Import user data from JSON export')
    user_import_parser.add_argument('filename', help='JSON export file to import')
    user_import_parser.add_argument('--user-id', help='Override user ID (uses file user ID if not specified)')
    user_import_parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without importing')
    
    # Import global facts
    global_import_parser = import_subparsers.add_parser('global-facts', help='Import global facts from JSON export')
    global_import_parser.add_argument('filename', help='JSON export file to import')
    global_import_parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without importing')
    
    # Preview commands (safe operations)
    preview_parser = subparsers.add_parser('preview', help='Preview deletion operations (safe, no changes)')
    preview_subparsers = preview_parser.add_subparsers(dest='preview_type', help='Preview types')
    
    # Preview user deletion
    preview_user_parser = preview_subparsers.add_parser('user', help='Preview user deletion (safe)')
    preview_user_parser.add_argument('--user-id', required=True, help='User ID')
    
    # Preview conversation deletion
    preview_conv_parser = preview_subparsers.add_parser('conversation', help='Preview conversation deletion (safe)')
    preview_conv_parser.add_argument('--doc-id', required=True, help='Document ID')
    
    # Preview global fact deletion
    preview_fact_parser = preview_subparsers.add_parser('global-fact', help='Preview global fact deletion (safe)')
    preview_fact_parser.add_argument('--fact-id', required=True, help='Fact ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize ChromaDB manager
        manager = ChromaDBManagerSimple(persist_directory=args.chromadb_path)
        
        # Handle query commands
        if args.command == 'query':
            if args.query_type == 'conversations':
                results = manager.query_conversations(user_id=args.user_id, limit=args.limit)
                print_formatted_results(results, "conversations")
                
            elif args.query_type == 'user-facts':
                results = manager.query_user_facts(args.user_id, args.limit)
                print_formatted_results(results, "user_facts")
                
            elif args.query_type == 'global-facts':
                results = manager.query_global_facts(args.limit, args.search)
                print_formatted_results(results, "global_facts")
                
            elif args.query_type == 'search':
                results = manager.search_all_data(args.text, args.limit)
                print(f"🔍 Search results for: '{args.text}'")
                print("=" * 80)
                
                if results['conversations']:
                    print(f"\n📄 CONVERSATIONS ({len(results['conversations'])})")
                    print_formatted_results(results['conversations'], "conversations", 10)
                
                if results['user_facts']:
                    print(f"\n👤 USER FACTS ({len(results['user_facts'])})")
                    print_formatted_results(results['user_facts'], "user_facts", 10)
                
                if results['global_facts']:
                    print(f"\n🌍 GLOBAL FACTS ({len(results['global_facts'])})")
                    print_formatted_results(results['global_facts'], "global_facts", 10)
        
        # Handle info commands
        elif args.command == 'info':
            if args.info_type == 'users':
                users = manager.get_users_list()
                print(f"👥 Found {len(users)} users")
                print("=" * 80)
                
                for user in users:
                    print(f"\nUser ID: {user['user_id']}")
                    print(f"  Conversations: {user['conversations']}")
                    print(f"  Facts: {user['facts']}")
                    print(f"  Channels: {', '.join(user['channels'])}")
                    print(f"  First seen: {user['first_seen'] or 'unknown'}")
                    print(f"  Last seen: {user['last_seen'] or 'unknown'}")
                
            elif args.info_type == 'stats':
                stats = manager.get_database_stats()
                print("📊 ChromaDB Statistics")
                print("=" * 50)
                print(json.dumps(stats, indent=2))
        
        # Handle export commands
        elif args.command == 'export':
            if args.export_type == 'user':
                manager.export_user_data(
                    args.user_id, 
                    args.output, 
                    format_type=args.format,
                    facts_only=args.facts_only,
                    stats_only=args.stats_only
                )
                
            elif args.export_type == 'global-facts':
                manager.export_global_facts(args.output)
        
        # Handle delete commands
        elif args.command == 'delete':
            create_backup = not getattr(args, 'no_backup', False)
            
            if args.delete_type == 'user':
                manager.delete_user_data(args.user_id, args.confirm, create_backup)
                
            elif args.delete_type == 'user-facts':
                manager.delete_user_facts(args.user_id, args.confirm, create_backup)
                
            elif args.delete_type == 'conversation':
                manager.delete_conversation(args.doc_id, args.confirm, create_backup)
                
            elif args.delete_type == 'global-fact':
                manager.delete_global_fact(args.fact_id, args.confirm, create_backup)
        
        # Handle import commands
        elif args.command == 'import':
            if args.import_type == 'user':
                manager.import_user_data(args.filename, args.user_id, args.dry_run)
                
            elif args.import_type == 'global-facts':
                manager.import_global_facts(args.filename, args.dry_run)
        
        # Handle preview commands (safe operations)
        elif args.command == 'preview':
            if args.preview_type == 'user':
                preview = manager.preview_user_deletion(args.user_id)
                if preview["exists"]:
                    print(f"👤 User {args.user_id} data preview:")
                    print(f"   - Total items: {preview['total_items']}")
                    print(f"   - Conversations: {preview['conversations']}")
                    print(f"   - Facts: {preview['facts']}")
                    print(f"   - Channels: {', '.join(preview['channels'])}")
                    print(f"   - First seen: {preview['first_seen']}")
                    print(f"   - Last seen: {preview['last_seen']}")
                    print(f"\nTo delete this data, run:")
                    print(f"python chromadb_manager_simple.py delete user --user-id {args.user_id} --confirm")
                else:
                    print(f"❌ User {args.user_id} not found or no data")
                    if "error" in preview:
                        print(f"Error: {preview['error']}")
            
            elif args.preview_type == 'conversation':
                preview = manager.preview_conversation_deletion(args.doc_id)
                if preview["exists"]:
                    print(f"💬 Conversation {args.doc_id} preview:")
                    print(f"   - User: {preview['user_id']}")
                    print(f"   - Timestamp: {preview['timestamp']}")
                    print(f"   - Channel: {preview['channel_id']}")
                    print(f"   - Type: {preview['type']}")
                    print(f"   - User message: {preview['user_message']}")
                    print(f"   - Bot response: {preview['bot_response']}")
                    print(f"\nTo delete this conversation, run:")
                    print(f"python chromadb_manager_simple.py delete conversation --doc-id {args.doc_id} --confirm")
                else:
                    print(f"❌ Conversation {args.doc_id} not found")
                    if "error" in preview:
                        print(f"Error: {preview['error']}")
            
            elif args.preview_type == 'global-fact':
                preview = manager.preview_global_fact_deletion(args.fact_id)
                if preview["exists"]:
                    print(f"🌍 Global fact {args.fact_id} preview:")
                    print(f"   - Fact: {preview['fact']}")
                    print(f"   - Category: {preview['category']}")
                    print(f"   - Added by: {preview['added_by']}")
                    print(f"   - Method: {preview['extraction_method']}")
                    print(f"   - Timestamp: {preview['timestamp']}")
                    if preview['context']:
                        print(f"   - Context: {preview['context']}")
                    print(f"\nTo delete this fact, run:")
                    print(f"python chromadb_manager_simple.py delete global-fact --fact-id {args.fact_id} --confirm")
                else:
                    print(f"❌ Global fact {args.fact_id} not found")
                    if "error" in preview:
                        print(f"Error: {preview['error']}")
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
