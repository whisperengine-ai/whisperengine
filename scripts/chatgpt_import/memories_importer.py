"""
ChatGPT Memories Importer for WhisperEngine

This module imports ChatGPT-style memories (one-line user facts) into 
WhisperEngine's PostgreSQL semantic knowledge graph system.

Unlike conversation history (which goes to Qdrant vector store), memories
are factual statements about the user that get stored in the structured
fact_entities and user_fact_relationships tables for efficient querying.
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.semantic_router import SemanticKnowledgeRouter
from src.utils.logging_config import get_logger
import asyncpg

logger = get_logger(__name__)

@dataclass
class UserMemory:
    """A single user memory/fact from ChatGPT"""
    raw_text: str
    entity_type: str
    entity_name: str
    relationship_type: str
    confidence: float
    category: Optional[str] = None
    subcategory: Optional[str] = None
    emotional_context: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

class ChatGPTMemoriesImporter:
    """Imports ChatGPT memories into WhisperEngine's PostgreSQL knowledge graph"""
    
    def __init__(self, user_id: str, character_name: str = "aetheris", dry_run: bool = False, verbose: bool = False):
        self.user_id = user_id
        self.character_name = character_name
        self.dry_run = dry_run
        self.verbose = verbose
        self.knowledge_router = None
        self.db_pool = None
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    async def initialize(self):
        """Initialize database connection and knowledge router"""
        try:
            # Initialize PostgreSQL connection
            self.db_pool = await asyncpg.create_pool(
                host="localhost",
                port=5433,
                database="whisperengine",
                user="whisperengine",
                password="development_password_change_in_production",
                min_size=1,
                max_size=5
            )
            
            # Initialize semantic knowledge router
            self.knowledge_router = SemanticKnowledgeRouter(self.db_pool)
            
            logger.info("✅ Initialized ChatGPT memories importer for user %s", self.user_id)
            
        except Exception as e:
            logger.error("❌ Failed to initialize importer: %s", e)
            raise
    
    async def close(self):
        """Clean up database connections"""
        if self.db_pool:
            await self.db_pool.close()
    
    def parse_memory_line(self, memory_text: str) -> Optional[UserMemory]:
        """
        Parse a memory block (potentially multi-line) from ChatGPT into structured data
        
        Examples of ChatGPT memory patterns:
        - "User likes Italian food"
        - "User has a cat named Whiskers"
        - Multi-line blocks like art book lists or structured formats
        """
        memory_text = memory_text.strip()
        if not memory_text or memory_text.startswith('#'):
            return None
        
        # For multi-line memories, use the first sentence/line to determine the type
        # but store the complete text as the entity_name
        first_line = memory_text.split('\n')[0].strip()
        
        # Enhanced pattern matching for various memory types
        patterns = [
            # Ownership/possession patterns
            (r"owns?\s+(?:the\s+)?following\s+(.+)", "possession", "owns", 0.8),
            (r"(?:has|owns?)\s+(?:a|an|the)?\s*(.+)", "possession", "owns", 0.7),
            
            # Background/experience patterns  
            (r"has\s+(?:a\s+)?background\s+in\s+(.+)", "background", "has_background", 0.8),
            (r"has\s+experience\s+(?:with|in)\s+(.+)", "experience", "experienced_in", 0.8),
            
            # Device/equipment patterns
            (r"uses?\s+(?:the\s+)?(.+)", "equipment", "uses", 0.7),
            (r"bought\s+(?:the\s+)?(.+)", "equipment", "owns", 0.8),
            
            # Learning/educational patterns
            (r"wants?\s+to\s+remember\s+(.+)", "learning", "wants_to_remember", 0.8),
            (r"wants?\s+(?:a\s+)?document\s+that\s+(.+)", "learning", "wants", 0.7),
            
            # Personal characteristics
            (r"is\s+(?:a\s+)?(.+)", "characteristic", "is", 0.7),
            (r"tends?\s+to\s+(.+)", "behavior", "tends_to", 0.7),
            (r"prefers?\s+(.+)", "preference", "prefers", 0.8),
            
            # Professional patterns
            (r"(?:was|is)\s+(?:an?\s+)?engineer\s+(.+)", "professional", "worked_as", 0.8),
            (r"(?:works?|working)\s+on\s+(.+)", "professional", "works_on", 0.8),
            (r"is\s+doing\s+(?:a\s+)?mentorship\s+(.+)", "professional", "mentorship", 0.8),
            
            # Goals and aspirations
            (r"goal\s+is\s+to\s+(.+)", "goal", "goal", 0.9),
            (r"is\s+focused\s+on\s+(.+)", "focus", "focused_on", 0.8),
            (r"is\s+not\s+aiming\s+to\s+(.+)", "goal", "not_aiming", 0.8),
            
            # Skills and abilities
            (r"strengths?\s+include\s+(.+)", "skill", "strengths", 0.8),
            (r"is\s+less\s+experienced\s+at\s+(.+)", "skill", "less_experienced", 0.7),
            
            # Technology and devices
            (r"is\s+(?:a\s+)?mac,?\s+(.+)", "technology", "uses", 0.8),
            
            # Mentorship and advice
            (r"mentor,?\s+(.+)", "mentorship", "mentor_advice", 0.8),
            
            # Likes/preferences (original patterns)
            (r"(?:user|they|he|she)\s+likes?\s+(.+)", "preference", "likes", 0.8),
            (r"(?:user|they|he|she)\s+loves?\s+(.+)", "preference", "loves", 0.9),
            (r"(?:user|they|he|she)\s+enjoys?\s+(.+)", "activity", "enjoys", 0.8),
            (r"(?:user|they|he|she)\s+dislikes?\s+(.+)", "preference", "dislikes", 0.8),
            
            # Generic fallback
            (r"(.+)", "general", "mentioned", 0.5),
        ]
        
        for pattern, entity_type, relationship, confidence in patterns:
            match = re.search(pattern, first_line.lower())
            if match:
                # For multi-line memories, use the full text as entity_name
                # For single-line memories, clean up the matched portion
                if '\n' in memory_text:
                    entity_name = memory_text  # Keep full multi-line content
                else:
                    entity_name = self._clean_entity_name(match.group(1))
                
                # Determine category and emotional context
                category, subcategory = self._categorize_entity(entity_type, entity_name)
                emotional_context = self._detect_emotional_context(relationship)
                
                # Create attributes dict with source information
                attributes = {
                    "source": "chatgpt_import",
                    "raw_text": memory_text,
                    "import_timestamp": datetime.now().isoformat(),
                    "parsed_pattern": pattern,
                    "is_multiline": '\n' in memory_text
                }
                
                return UserMemory(
                    raw_text=memory_text,
                    entity_type=entity_type,
                    entity_name=entity_name,
                    relationship_type=relationship,
                    confidence=confidence,
                    category=category,
                    subcategory=subcategory,
                    emotional_context=emotional_context,
                    attributes=attributes
                )
        
        return None
    
    def _clean_entity_name(self, entity_name: str) -> str:
        """Clean and normalize entity names"""
        # Remove articles and common words
        entity_name = re.sub(r'\b(the|a|an)\b\s*', '', entity_name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation
        entity_name = re.sub(r'[.!?;,]+$', '', entity_name)
        
        # Normalize whitespace
        entity_name = ' '.join(entity_name.split())
        
        return entity_name.strip()
    
    def _categorize_entity(self, entity_type: str, entity_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Determine category and subcategory for an entity"""
        categories = {
            "preference": {
                "food": ["pizza", "pasta", "sushi", "burger", "sandwich", "coffee", "tea", "wine", "beer"],
                "music": ["rock", "pop", "jazz", "classical", "hip hop", "country", "electronic"],
                "entertainment": ["movies", "tv shows", "books", "games", "youtube", "netflix"],
                "sport": ["football", "basketball", "soccer", "tennis", "swimming", "running", "gym"]
            },
            "activity": {
                "hobby": ["reading", "writing", "drawing", "painting", "photography", "cooking"],
                "sport": ["playing", "tennis", "basketball", "soccer", "swimming", "running"],
                "creative": ["music", "art", "writing", "design", "coding", "programming"],
                "outdoor": ["hiking", "camping", "fishing", "gardening", "walking"]
            },
            "possession": {
                "pet": ["cat", "dog", "bird", "fish", "hamster", "rabbit"],
                "vehicle": ["car", "bike", "motorcycle", "bicycle"],
                "device": ["phone", "computer", "laptop", "tablet", "watch"],
                "instrument": ["guitar", "piano", "drums", "violin", "bass"]
            },
            "location": {
                "city": ["san francisco", "new york", "los angeles", "chicago", "seattle", "boston"],
                "country": ["usa", "canada", "uk", "australia", "germany", "japan"],
                "venue": ["gym", "library", "coffee shop", "restaurant", "park"]
            }
        }
        
        entity_lower = entity_name.lower()
        
        if entity_type in categories:
            for category, keywords in categories[entity_type].items():
                for keyword in keywords:
                    if keyword in entity_lower:
                        return (category, None)
        
        return (entity_type, None)
    
    def _detect_emotional_context(self, relationship: str, entity_name: Optional[str] = None) -> Optional[str]:
        """Detect emotional context from relationship and entity"""
        # Remove unused parameter warning by actually using it if needed for future enhancement
        _ = entity_name  # Placeholder for future emotional analysis based on entity content
        
        positive_relationships = ["likes", "loves", "enjoys"]
        negative_relationships = ["dislikes", "hates"]
        
        if relationship in positive_relationships:
            return "positive"
        elif relationship in negative_relationships:
            return "negative"
        elif relationship in ["owns", "has"]:
            return "neutral"
        elif "goal" in relationship or "wants" in relationship:
            return "aspirational"
        
        return "neutral"
    
    async def import_memories_file(self, file_path: str) -> Dict[str, int]:
        """
        Import memories from a text file (memory blocks separated by blank lines)
        
        Args:
            file_path: Path to the memories file
            
        Returns:
            Dictionary with import statistics
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Memories file not found: {file_path}")
            
            logger.info("📁 Importing memories from: %s", file_path)
            
            # Read all content and split by blank lines to preserve multi-line memories
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by double newlines (blank lines) to get memory blocks
            memory_blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
            
            total_blocks = len(memory_blocks)
            logger.info("📋 Found %d memory blocks to process", total_blocks)
            
            # Process each memory block
            for block_num, memory_block in enumerate(memory_blocks, 1):
                await self._process_memory_block(memory_block, block_num, total_blocks)
            
            # Return statistics
            stats = {
                "total_blocks": total_blocks,
                "processed": self.processed_count,
                "skipped": self.skipped_count,
                "errors": self.error_count
            }
            
            logger.info("✅ Import complete: %s", stats)
            return stats
            
        except Exception as e:
            logger.error("❌ Failed to import memories: %s", e)
            raise
    
    async def _process_memory_block(self, memory_block: str, block_num: int, total_blocks: int):
        """Process a single memory block (which may be multi-line)"""
        try:
            # Parse the memory block
            memory = self.parse_memory_line(memory_block)
            if not memory:
                self.skipped_count += 1
                if self.verbose:
                    logger.info("⏭️  Skipped block %d: '%s'", block_num, memory_block[:100] + "..." if len(memory_block) > 100 else memory_block)
                return
            
            if self.verbose:
                logger.info("📝 [%d/%d] Parsed: %s (%s)", block_num, total_blocks, memory.entity_name[:50] + "..." if len(memory.entity_name) > 50 else memory.entity_name, memory.relationship_type)
            
            # Store in knowledge graph (if not dry run)
            if not self.dry_run:
                await self._store_memory(memory)
            
            self.processed_count += 1
            
            # Progress logging
            if block_num % 5 == 0 or block_num == total_blocks:
                logger.info("🔄 Progress: %d/%d blocks processed", block_num, total_blocks)
                
        except (ValueError, TypeError, KeyError) as e:
            self.error_count += 1
            logger.error("❌ Error processing block %d: %s", block_num, e)
            if self.verbose:
                logger.error("   Block content: '%s'", memory_block[:200] + "..." if len(memory_block) > 200 else memory_block)
    
    async def _store_memory(self, memory: UserMemory):
        """Store a memory in the PostgreSQL knowledge graph"""
        try:
            # Store using the semantic knowledge router
            await self.knowledge_router.store_user_fact(
                user_id=self.user_id,
                entity_type=memory.entity_type,
                entity_name=memory.entity_name,
                relationship_type=memory.relationship_type,
                confidence=memory.confidence,
                category=memory.category,
                emotional_context=memory.emotional_context,
                mentioned_by_character=self.character_name,
                source_conversation_id=None,
                attributes=memory.attributes
            )
            
            if self.verbose:
                logger.info("💾 Stored: %s -> %s", memory.entity_name, memory.relationship_type)
                
        except Exception as e:
            logger.error("❌ Failed to store memory '%s': %s", memory.raw_text, e)
            raise

# Example usage and CLI interface
async def main():
    """Main CLI interface for ChatGPT memories import"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import ChatGPT memories into WhisperEngine")
    parser.add_argument("file_path", help="Path to the memories file (one memory per line)")
    parser.add_argument("--user-id", required=True, help="User ID (Discord ID or universal user ID)")
    parser.add_argument("--character", default="aetheris", help="Character name (default: aetheris)")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, don't store in database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = ChatGPTMemoriesImporter(
        user_id=args.user_id,
        character_name=args.character,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    try:
        await importer.initialize()
        
        # Run import
        stats = await importer.import_memories_file(args.file_path)
        
        # Print summary
        print("\n📊 Import Summary:")
        print(f"   Memory blocks: {stats['total_blocks']}")
        print(f"   Processed: {stats['processed']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Errors: {stats['errors']}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN - No data was stored in database")
        else:
            print("\n✅ Memories imported successfully!")
            
    finally:
        await importer.close()

if __name__ == "__main__":
    asyncio.run(main())