"""
Character Self-Memory System

This module implements the autonomous character's personal memory system,
separate from user conversation memories. Characters maintain their own
internal memories about their lives, experiences, and ongoing thoughts.
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of character personal memories"""
    CHILDHOOD = "childhood"
    EDUCATION = "education"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    ACHIEVEMENT = "achievement"
    TRAUMA = "trauma"
    LEARNING = "learning"
    GOAL = "goal"
    REFLECTION = "reflection"
    DAILY_EVENT = "daily_event"
    EMOTIONAL_MOMENT = "emotional_moment"


class EmotionalWeight(Enum):
    """Emotional significance levels for memories"""
    TRIVIAL = 0.1      # Minor daily events
    LOW = 0.3          # Somewhat significant
    MEDIUM = 0.5       # Important experiences
    HIGH = 0.7         # Life-changing events
    PROFOUND = 0.9     # Defining moments


@dataclass
class PersonalMemory:
    """A single character personal memory"""
    memory_id: str
    character_id: str
    content: str
    memory_type: MemoryType
    emotional_weight: float  # 0.0-1.0
    formative_impact: str   # "low", "medium", "high"
    themes: List[str]       # Related themes/topics
    created_date: datetime
    last_recalled: Optional[datetime] = None
    recall_count: int = 0
    age_when_formed: Optional[int] = None
    related_people: List[str] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.related_people is None:
            self.related_people = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MemoryCluster:
    """Group of related memories forming a larger narrative"""
    cluster_id: str
    character_id: str
    theme: str
    memories: List[str]  # Memory IDs
    summary: str
    emotional_significance: float
    time_period: str
    created_date: datetime


class CharacterSelfMemoryManager:
    """Manages a character's personal memory system"""
    
    def __init__(self, character_id: str, db_path: Optional[str] = None):
        self.character_id = character_id
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        self.db_path = db_path or f"data/character_memories_{character_id}.db"
        self.init_database()
        
        # Memory configuration
        self.max_daily_memories = 10
        self.memory_retention_days = 365 * 10  # 10 years
        self.recall_boost_factor = 0.1  # Boost importance when recalled
        
    def init_database(self):
        """Initialize SQLite database for character memories"""
        try:
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS personal_memories (
                        memory_id TEXT PRIMARY KEY,
                        character_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        emotional_weight REAL NOT NULL,
                        formative_impact TEXT NOT NULL,
                        themes TEXT NOT NULL,  -- JSON array
                        created_date TEXT NOT NULL,
                        last_recalled TEXT,
                        recall_count INTEGER DEFAULT 0,
                        age_when_formed INTEGER,
                        related_people TEXT,  -- JSON array
                        location TEXT,
                        metadata TEXT  -- JSON object
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_clusters (
                        cluster_id TEXT PRIMARY KEY,
                        character_id TEXT NOT NULL,
                        theme TEXT NOT NULL,
                        memories TEXT NOT NULL,  -- JSON array of memory IDs
                        summary TEXT NOT NULL,
                        emotional_significance REAL NOT NULL,
                        time_period TEXT NOT NULL,
                        created_date TEXT NOT NULL
                    )
                """)
                
                # Indexes for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_character_memories 
                    ON personal_memories(character_id)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memory_type 
                    ON personal_memories(character_id, memory_type)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_emotional_weight 
                    ON personal_memories(character_id, emotional_weight DESC)
                """)
                
                conn.commit()
                
            self.logger.info("Initialized character memory database: %s", self.db_path)
            
        except (sqlite3.Error, OSError) as e:
            self.logger.error("Failed to initialize character memory database: %s", e)
            raise
    
    def store_memory(self, memory: PersonalMemory) -> bool:
        """Store a personal memory in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO personal_memories (
                        memory_id, character_id, content, memory_type, emotional_weight,
                        formative_impact, themes, created_date, last_recalled, recall_count,
                        age_when_formed, related_people, location, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.memory_id,
                    memory.character_id,
                    memory.content,
                    memory.memory_type.value,
                    memory.emotional_weight,
                    memory.formative_impact,
                    json.dumps(memory.themes),
                    memory.created_date.isoformat(),
                    memory.last_recalled.isoformat() if memory.last_recalled else None,
                    memory.recall_count,
                    memory.age_when_formed,
                    json.dumps(memory.related_people),
                    memory.location,
                    json.dumps(memory.metadata)
                ))
                conn.commit()
                
            self.logger.debug("Stored memory: %s for character %s", memory.memory_id, self.character_id)
            return True
            
        except (sqlite3.Error, ValueError, TypeError) as e:
            self.logger.error("Failed to store memory %s: %s", memory.memory_id, e)
            return False
    
    def recall_memories(
        self,
        themes: Optional[List[str]] = None,
        memory_types: Optional[List[MemoryType]] = None,
        min_emotional_weight: float = 0.0,
        limit: int = 10,
        boost_recall: bool = True
    ) -> List[PersonalMemory]:
        """Recall memories based on themes and criteria"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM personal_memories 
                    WHERE character_id = ? AND emotional_weight >= ?
                """
                params = [self.character_id, min_emotional_weight]
                
                # Add theme filtering
                if themes:
                    theme_conditions = []
                    for theme in themes:
                        theme_conditions.append("themes LIKE ?")
                        params.append(f"%{theme}%")
                    query += f" AND ({' OR '.join(theme_conditions)})"
                
                # Add memory type filtering
                if memory_types:
                    type_conditions = []
                    for mem_type in memory_types:
                        type_conditions.append("memory_type = ?")
                        params.append(mem_type.value)
                    query += f" AND ({' OR '.join(type_conditions)})"
                
                # Order by emotional weight and recency
                query += """
                    ORDER BY emotional_weight DESC, created_date DESC
                    LIMIT ?
                """
                params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                memories = []
                for row in rows:
                    memory = self._row_to_memory(row)
                    memories.append(memory)
                    
                    # Boost recall count and update last_recalled
                    if boost_recall:
                        self._update_recall_stats(memory.memory_id)
                
                self.logger.debug(
                    "Recalled %d memories for character %s", len(memories), self.character_id
                )
                return memories
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to recall memories: %s", e)
            return []
    
    def get_formative_memories(self, limit: int = 5) -> List[PersonalMemory]:
        """Get the most formative/important memories"""
        return self.recall_memories(
            min_emotional_weight=0.7,
            limit=limit,
            boost_recall=False
        )
    
    def get_recent_memories(self, days: int = 7, limit: int = 10) -> List[PersonalMemory]:
        """Get recent memories within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM personal_memories 
                    WHERE character_id = ? AND created_date >= ?
                    ORDER BY created_date DESC
                    LIMIT ?
                """, (self.character_id, cutoff_date.isoformat(), limit))
                
                rows = cursor.fetchall()
                return [self._row_to_memory(row) for row in rows]
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to get recent memories: %s", e)
            return []
    
    def get_memories_by_type(self, memory_type: MemoryType, limit: int = 10) -> List[PersonalMemory]:
        """Get memories of a specific type"""
        return self.recall_memories(
            memory_types=[memory_type],
            limit=limit,
            boost_recall=False
        )
    
    def add_daily_reflection(self, reflection_content: str, themes: List[str]) -> PersonalMemory:
        """Add a daily reflection memory"""
        memory = PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=self.character_id,
            content=reflection_content,
            memory_type=MemoryType.REFLECTION,
            emotional_weight=EmotionalWeight.LOW.value,
            formative_impact="low",
            themes=themes,
            created_date=datetime.now()
        )
        
        if self.store_memory(memory):
            return memory
        else:
            raise ValueError("Failed to store daily reflection")
    
    def create_memory_cluster(
        self,
        theme: str,
        memory_ids: List[str],
        summary: str,
        time_period: str
    ) -> MemoryCluster:
        """Create a cluster of related memories"""
        # Calculate average emotional significance
        memories = []
        for mem_id in memory_ids:
            memory = self.get_memory_by_id(mem_id)
            if memory:
                memories.append(memory)
        
        avg_significance = sum(m.emotional_weight for m in memories) / len(memories) if memories else 0.0
        
        cluster = MemoryCluster(
            cluster_id=str(uuid.uuid4()),
            character_id=self.character_id,
            theme=theme,
            memories=memory_ids,
            summary=summary,
            emotional_significance=avg_significance,
            time_period=time_period,
            created_date=datetime.now()
        )
        
        # Store cluster
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO memory_clusters (
                        cluster_id, character_id, theme, memories, summary,
                        emotional_significance, time_period, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cluster.cluster_id,
                    cluster.character_id,
                    cluster.theme,
                    json.dumps(cluster.memories),
                    cluster.summary,
                    cluster.emotional_significance,
                    cluster.time_period,
                    cluster.created_date.isoformat()
                ))
                conn.commit()
                
            self.logger.info("Created memory cluster: %s", cluster.theme)
            return cluster
            
        except (sqlite3.Error, ValueError, TypeError) as e:
            self.logger.error("Failed to create memory cluster: %s", e)
            raise
    
    def get_memory_by_id(self, memory_id: str) -> Optional[PersonalMemory]:
        """Get a specific memory by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM personal_memories WHERE memory_id = ?
                """, (memory_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_memory(row)
                return None
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to get memory %s: %s", memory_id, e)
            return None
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about character's memory system"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total memories
                total_cursor = conn.execute("""
                    SELECT COUNT(*) FROM personal_memories WHERE character_id = ?
                """, (self.character_id,))
                total_memories = total_cursor.fetchone()[0]
                
                # Memories by type
                type_cursor = conn.execute("""
                    SELECT memory_type, COUNT(*) FROM personal_memories 
                    WHERE character_id = ? GROUP BY memory_type
                """, (self.character_id,))
                memories_by_type = dict(type_cursor.fetchall())
                
                # Average emotional weight
                weight_cursor = conn.execute("""
                    SELECT AVG(emotional_weight) FROM personal_memories 
                    WHERE character_id = ?
                """, (self.character_id,))
                avg_emotional_weight = weight_cursor.fetchone()[0] or 0.0
                
                # Most recalled memory
                recall_cursor = conn.execute("""
                    SELECT content, recall_count FROM personal_memories 
                    WHERE character_id = ? ORDER BY recall_count DESC LIMIT 1
                """, (self.character_id,))
                most_recalled = recall_cursor.fetchone()
                
                return {
                    "total_memories": total_memories,
                    "memories_by_type": memories_by_type,
                    "average_emotional_weight": round(avg_emotional_weight, 2),
                    "most_recalled_memory": {
                        "content": most_recalled[0][:100] + "..." if most_recalled and len(most_recalled[0]) > 100 else most_recalled[0] if most_recalled else None,
                        "recall_count": most_recalled[1] if most_recalled else 0
                    }
                }
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to get memory statistics: %s", e)
            return {}
    
    def _row_to_memory(self, row) -> PersonalMemory:
        """Convert database row to PersonalMemory object"""
        return PersonalMemory(
            memory_id=row[0],
            character_id=row[1],
            content=row[2],
            memory_type=MemoryType(row[3]),
            emotional_weight=row[4],
            formative_impact=row[5],
            themes=json.loads(row[6]),
            created_date=datetime.fromisoformat(row[7]),
            last_recalled=datetime.fromisoformat(row[8]) if row[8] else None,
            recall_count=row[9],
            age_when_formed=row[10],
            related_people=json.loads(row[11]) if row[11] else [],
            location=row[12],
            metadata=json.loads(row[13]) if row[13] else {}
        )
    
    def _update_recall_stats(self, memory_id: str):
        """Update recall statistics for a memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE personal_memories 
                    SET recall_count = recall_count + 1, last_recalled = ?
                    WHERE memory_id = ?
                """, (datetime.now().isoformat(), memory_id))
                conn.commit()
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to update recall stats for %s: %s", memory_id, e)
    
    def cleanup_old_memories(self):
        """Remove very old, low-importance memories to prevent database bloat"""
        cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Only delete low-importance, old memories
                cursor = conn.execute("""
                    DELETE FROM personal_memories 
                    WHERE character_id = ? 
                    AND created_date < ? 
                    AND emotional_weight < 0.3
                    AND recall_count < 2
                """, (self.character_id, cutoff_date.isoformat()))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info("Cleaned up %d old memories for character %s", deleted_count, self.character_id)
                
        except (sqlite3.Error, ValueError) as e:
            self.logger.error("Failed to cleanup old memories: %s", e)