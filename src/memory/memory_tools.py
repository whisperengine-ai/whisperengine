"""
Memory Management Tools for LLM Tool Calling

Provides structured tools for LLMs to manage memory based on user requests.
Handles corrections, deletions, and updates with proper validation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .fact_validator import FactValidator, ExtractedFact, FactType

logger = logging.getLogger(__name__)


@dataclass
class MemoryTool:
    """Base class for memory management tools"""
    name: str
    description: str
    parameters: Dict[str, Any]


class MemoryToolManager:
    """Manages memory-related tools for LLM tool calling"""
    
    def __init__(self, fact_validator: FactValidator, storage_db):
        self.fact_validator = fact_validator
        self.storage_db = storage_db
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize available memory tools for LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "update_memory_fact",
                    "description": "Update or correct a specific fact in memory (e.g., pet name, preferences, personal details)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "What the fact is about (e.g., 'pet', 'goldfish', 'preference')"
                            },
                            "predicate": {
                                "type": "string", 
                                "description": "The relationship or attribute (e.g., 'is_named', 'likes', 'owns')"
                            },
                            "old_value": {
                                "type": "string",
                                "description": "The incorrect value to be replaced"
                            },
                            "new_value": {
                                "type": "string",
                                "description": "The correct value to store"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why this correction is being made"
                            }
                        },
                        "required": ["subject", "predicate", "new_value", "reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "delete_memory_fact",
                    "description": "Delete incorrect or outdated information from memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "What the fact is about"
                            },
                            "predicate": {
                                "type": "string",
                                "description": "The relationship or attribute to delete"
                            },
                            "value": {
                                "type": "string", 
                                "description": "The specific value to delete (optional for broader deletion)"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why this information should be deleted"
                            }
                        },
                        "required": ["subject", "reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory_facts",
                    "description": "Search for specific facts in memory to verify or review",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "What to search for (e.g., 'pet', 'goldfish')"
                            },
                            "predicate": {
                                "type": "string",
                                "description": "Specific relationship to search for (optional)"
                            }
                        },
                        "required": ["subject"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute a memory tool based on LLM tool call"""
        try:
            if tool_name == "update_memory_fact":
                return await self._update_memory_fact(parameters, user_id)
            elif tool_name == "delete_memory_fact":
                return await self._delete_memory_fact(parameters, user_id)
            elif tool_name == "search_memory_facts":
                return await self._search_memory_facts(parameters, user_id)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error executing memory tool {tool_name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def _update_memory_fact(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update a specific fact in memory"""
        subject = params["subject"]
        predicate = params["predicate"]
        new_value = params["new_value"]
        old_value = params.get("old_value")
        reason = params["reason"]
        
        # Create new fact with high confidence (user explicitly corrected it)
        new_fact = ExtractedFact(
            fact_type=FactType.PERSONAL_INFO,
            subject=subject,
            predicate=predicate,
            object=new_value,
            confidence=0.95,  # High confidence for user corrections
            source_message=f"User correction: {reason}",
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # Store the corrected fact
        await self.fact_validator._store_fact(new_fact)
        
        # If old value specified, delete conflicting facts
        if old_value:
            await self._delete_specific_fact(user_id, subject, predicate, old_value)
        
        logger.info(f"Updated memory fact for user {user_id}: {subject} {predicate} {new_value}")
        
        return {
            "success": True,
            "message": f"Updated {subject} {predicate} to '{new_value}'",
            "fact": new_fact.to_dict()
        }
    
    async def _delete_memory_fact(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Delete a fact from memory"""
        subject = params["subject"]
        predicate = params.get("predicate")
        value = params.get("value")
        reason = params["reason"]
        
        deleted_count = 0
        
        if value and predicate:
            # Delete specific fact
            deleted_count = await self._delete_specific_fact(user_id, subject, predicate, value)
        elif predicate:
            # Delete all facts with this subject and predicate
            deleted_count = await self._delete_facts_by_predicate(user_id, subject, predicate)
        else:
            # Delete all facts about this subject
            deleted_count = await self._delete_facts_by_subject(user_id, subject)
        
        logger.info(f"Deleted {deleted_count} memory facts for user {user_id}: {subject} (reason: {reason})")
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} facts about {subject}",
            "deleted_count": deleted_count,
            "reason": reason
        }
    
    async def _search_memory_facts(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Search for facts in memory"""
        subject = params["subject"]
        predicate = params.get("predicate")
        
        facts = await self.fact_validator.get_validated_facts(user_id, subject=subject)
        
        # Filter by predicate if specified
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        
        return {
            "success": True,
            "facts": [f.to_dict() for f in facts],
            "count": len(facts)
        }
    
    async def _delete_specific_fact(self, user_id: str, subject: str, predicate: str, value: str) -> int:
        """Delete a specific fact"""
        if not self.storage_db:
            return 0
        
        query = """
            DELETE FROM user_facts 
            WHERE user_id = $1 AND subject = $2 AND predicate = $3 AND object = $4
        """
        
        result = await self.storage_db.execute_command(query, (user_id, subject, predicate, value))
        return int(result.split()[-1]) if result else 0
    
    async def _delete_facts_by_predicate(self, user_id: str, subject: str, predicate: str) -> int:
        """Delete all facts with specific subject and predicate"""
        if not self.storage_db:
            return 0
        
        query = """
            DELETE FROM user_facts 
            WHERE user_id = $1 AND subject = $2 AND predicate = $3
        """
        
        result = await self.storage_db.execute_command(query, (user_id, subject, predicate))
        return int(result.split()[-1]) if result else 0
    
    async def _delete_facts_by_subject(self, user_id: str, subject: str) -> int:
        """Delete all facts about a subject"""
        if not self.storage_db:
            return 0
        
        query = """
            DELETE FROM user_facts 
            WHERE user_id = $1 AND subject = $2
        """
        
        result = await self.storage_db.execute_command(query, (user_id, subject))
        return int(result.split()[-1]) if result else 0


def detect_memory_correction_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    Detect if user is requesting a memory correction/update
    Returns intent parameters if detected, None otherwise
    """
    correction_patterns = [
        # Direct corrections
        "actually", "i meant", "i said", "correction", "that's wrong",
        "not", "never said", "didn't say", "mistake", "error",
        
        # Forget requests  
        "forget", "delete", "remove", "erase", "don't remember",
        
        # Update requests
        "update", "change", "correct", "fix", "it's actually",
        "the real", "the correct", "should be"
    ]
    
    message_lower = message.lower()
    
    # Check for correction patterns
    for pattern in correction_patterns:
        if pattern in message_lower:
            return {
                "intent": "memory_correction",
                "pattern": pattern,
                "confidence": 0.8,
                "message": message
            }
    
    return None