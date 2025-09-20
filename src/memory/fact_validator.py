"""
Fact Validation and Conflict Resolution Engine

This module handles:
- Fact extraction from user messages 
- Conflict detection between old and new information
- Confidence scoring for facts
- Temporal prioritization (newer facts override older ones)
- Cross-tier memory consistency validation
"""

import re
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FactType(Enum):
    """Types of facts that can be extracted"""
    PET_NAME = "pet_name"
    PERSONAL_INFO = "personal_info"
    PREFERENCE = "preference"
    RELATIONSHIP = "relationship"
    POSSESSION = "possession"
    LOCATION = "location"
    UNKNOWN = "unknown"


@dataclass
class ExtractedFact:
    """Represents a fact extracted from user input"""
    fact_type: FactType
    subject: str  # What the fact is about (e.g., "goldfish", "dog", "favorite color")
    predicate: str  # The relationship (e.g., "named", "is", "likes")
    object: str  # The value (e.g., "Bubbles", "red", "pizza")
    confidence: float  # 0.0 to 1.0
    source_message: str
    timestamp: datetime
    user_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'fact_type': self.fact_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedFact':
        """Create from dictionary"""
        return cls(
            fact_type=FactType(data['fact_type']),
            subject=data['subject'],
            predicate=data['predicate'],
            object=data['object'],
            confidence=data['confidence'],
            source_message=data['source_message'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            user_id=data['user_id']
        )


@dataclass
class FactConflict:
    """Represents a conflict between facts"""
    old_fact: ExtractedFact
    new_fact: ExtractedFact
    conflict_type: str  # "contradiction", "update", "clarification"
    resolution: str  # "prefer_new", "prefer_old", "merge", "uncertain"
    confidence: float


class FactExtractor:
    """Extracts structured facts from natural language"""
    
    def __init__(self):
        # Pattern-based fact extraction rules
        self.patterns = [
            # Pet names: "My [pet] is named [name]" or "[pet] named [name]"
            {
                'regex': r'(?:my\s+)?(\w+)\s+(?:is\s+)?named\s+(\w+)',
                'fact_type': FactType.PET_NAME,
                'subject_group': 1,
                'predicate': 'named',
                'object_group': 2,
                'confidence': 0.9
            },
            # Possessions: "I have a [thing]"
            {
                'regex': r'i\s+have\s+an?\s+(\w+)',
                'fact_type': FactType.POSSESSION,
                'subject_group': 1,
                'predicate': 'have',
                'object_group': 1,
                'confidence': 0.8
            },
            # Preferences: "I like [thing]" or "My favorite [category] is [thing]"
            {
                'regex': r'(?:i\s+like|my\s+favorite\s+\w+\s+is)\s+(\w+)',
                'fact_type': FactType.PREFERENCE,
                'subject_group': 1,
                'predicate': 'likes',
                'object_group': 1,
                'confidence': 0.7
            }
        ]
    
    def extract_facts(self, message: str, user_id: str) -> List[ExtractedFact]:
        """Extract facts from a message"""
        facts = []
        message_lower = message.lower().strip()
        timestamp = datetime.now(timezone.utc)
        
        for pattern in self.patterns:
            matches = re.finditer(pattern['regex'], message_lower, re.IGNORECASE)
            
            for match in matches:
                try:
                    subject = match.group(pattern['subject_group']).strip()
                    object_val = match.group(pattern['object_group']).strip()
                    
                    fact = ExtractedFact(
                        fact_type=pattern['fact_type'],
                        subject=subject,
                        predicate=pattern['predicate'],
                        object=object_val,
                        confidence=pattern['confidence'],
                        source_message=message,
                        timestamp=timestamp,
                        user_id=user_id
                    )
                    facts.append(fact)
                    logger.info(f"Extracted fact: {subject} {pattern['predicate']} {object_val}")
                    
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Pattern match failed: {e}")
        
        return facts


class FactValidator:
    """Validates facts and resolves conflicts"""
    
    def __init__(self, storage_db=None):
        """Initialize fact validator with PostgreSQL database"""
        self.storage_db = storage_db  # PostgreSQLUserDB instance
        self.extractor = FactExtractor()
    
    async def process_message(self, message: str, user_id: str) -> Tuple[List[ExtractedFact], List[FactConflict]]:
        """Process a message for facts and conflicts"""
        # Extract new facts
        new_facts = self.extractor.extract_facts(message, user_id)
        
        if not new_facts:
            return [], []
        
        # Get existing facts for this user
        existing_facts = await self._get_existing_facts(user_id)
        
        # Detect conflicts
        conflicts = []
        for new_fact in new_facts:
            conflict = self._detect_conflict(new_fact, existing_facts)
            if conflict:
                conflicts.append(conflict)
        
        # Store new facts
        for fact in new_facts:
            await self._store_fact(fact)
        
        logger.info(f"Processed {len(new_facts)} facts, found {len(conflicts)} conflicts for user {user_id}")
        return new_facts, conflicts
    
    def _detect_conflict(self, new_fact: ExtractedFact, existing_facts: List[ExtractedFact]) -> Optional[FactConflict]:
        """Detect if a new fact conflicts with existing facts"""
        for existing_fact in existing_facts:
            # Same subject and predicate but different object = conflict
            if (existing_fact.subject.lower() == new_fact.subject.lower() and 
                existing_fact.predicate.lower() == new_fact.predicate.lower() and
                existing_fact.object.lower() != new_fact.object.lower()):
                
                # Determine conflict type and resolution
                conflict_type = "contradiction"
                resolution = "prefer_new"  # Default: newer facts override older ones
                confidence = min(new_fact.confidence, existing_fact.confidence)
                
                return FactConflict(
                    old_fact=existing_fact,
                    new_fact=new_fact,
                    conflict_type=conflict_type,
                    resolution=resolution,
                    confidence=confidence
                )
        
        return None
    
    async def _get_existing_facts(self, user_id: str) -> List[ExtractedFact]:
        """Get existing facts for a user from storage"""
        if not self.storage_db:
            return []
        
        try:
            # Query PostgreSQL for stored facts
            query = """
                SELECT fact_data FROM user_facts 
                WHERE user_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            results = await self.storage_db.execute_query(query, (user_id,))
            
            facts = []
            for row in results:
                fact_data = json.loads(row['fact_data'])
                fact = ExtractedFact.from_dict(fact_data)
                facts.append(fact)
            
            return facts
            
        except Exception as e:
            logger.warning(f"Failed to get existing facts for user {user_id}: {e}")
            return []
    
    async def _store_fact(self, fact: ExtractedFact):
        """Store a fact in the database"""
        if not self.storage_db:
            return
        
        try:
            query = """
                INSERT INTO user_facts (user_id, fact_type, subject, predicate, object, 
                                      confidence, source_message, timestamp, fact_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (user_id, subject, predicate) 
                DO UPDATE SET 
                    object = EXCLUDED.object,
                    confidence = EXCLUDED.confidence,
                    source_message = EXCLUDED.source_message,
                    timestamp = EXCLUDED.timestamp,
                    fact_data = EXCLUDED.fact_data
            """
            
            await self.storage_db.execute_command(query, (
                fact.user_id,
                fact.fact_type.value,
                fact.subject,
                fact.predicate,
                fact.object,
                fact.confidence,
                fact.source_message,
                fact.timestamp,
                json.dumps(fact.to_dict())
            ))
            
            logger.info(f"Stored fact: {fact.subject} {fact.predicate} {fact.object}")
            
        except Exception as e:
            logger.error(f"Failed to store fact: {e}")
    
    async def get_validated_facts(self, user_id: str, subject: Optional[str] = None) -> List[ExtractedFact]:
        """Get validated facts for a user, optionally filtered by subject"""
        existing_facts = await self._get_existing_facts(user_id)
        
        if subject:
            existing_facts = [f for f in existing_facts if f.subject.lower() == subject.lower()]
        
        # Return most recent facts (conflict resolution already applied in storage)
        return existing_facts
    
    async def resolve_goldfish_conflict(self, user_id: str, correct_name: str):
        """Special method to resolve the goldfish naming conflict"""
        logger.info(f"Resolving goldfish conflict for user {user_id}: correct name is {correct_name}")
        
        # Create a high-confidence fact for the correct goldfish name
        correction_fact = ExtractedFact(
            fact_type=FactType.PET_NAME,
            subject="goldfish",
            predicate="named",
            object=correct_name,
            confidence=1.0,  # Maximum confidence for manual correction
            source_message=f"MANUAL_CORRECTION: goldfish named {correct_name}",
            timestamp=datetime.now(timezone.utc),
            user_id=user_id
        )
        
        await self._store_fact(correction_fact)
        
        # Clear conflicting conversation history from PostgreSQL
        if self.storage_db:
            try:
                query = """
                    DELETE FROM conversations 
                    WHERE user_id = $1 
                    AND (user_message ILIKE $2 OR bot_response ILIKE $3 OR 
                         user_message ILIKE $4 OR bot_response ILIKE $5 OR
                         bot_response ILIKE $6)
                """
                await self.storage_db.execute_command(query, (
                    user_id, '%orion%', '%orion%', '%aiofe%', '%aiofe%', '%goldfish%'
                ))
                logger.info(f"Cleared conflicting goldfish conversations for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to clear conflicting conversations: {e}")


async def initialize_fact_validation_tables(storage_db):
    """Initialize database tables for fact validation"""
    try:
        # Create user_facts table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS user_facts (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                fact_type VARCHAR(100) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                predicate VARCHAR(255) NOT NULL,
                object VARCHAR(255) NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 0.8,
                source_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fact_data JSONB,
                UNIQUE(user_id, subject, predicate)
            );
        """
        
        await storage_db.execute_command(create_table_query)
        logger.info("Fact validation tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize fact validation tables: {e}")
        raise