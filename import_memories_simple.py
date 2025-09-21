#!/usr/bin/env python3
"""
WhisperEngine Memory Import Tool (Container Version)

Import memories from a text file into WhisperEngine's vector memory system.
This version is designed to run inside the WhisperEngine Docker container.

Usage:
    docker exec -it whisperengine-bot python import_memories_simple.py <user_id> <memory_file.txt>

Example:
    # Copy your memory file to the container first:
    docker cp memories.txt whisperengine-bot:/app/memories.txt
    
    # Then run the import:
    docker exec -it whisperengine-bot python import_memories_simple.py 123456789 memories.txt
"""

import asyncio
import sys
import os
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Import WhisperEngine components
from src.memory.memory_protocol import create_memory_manager
from src.memory.vector_memory_system import MemoryType, MemoryTier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleMemoryImporter:
    """Simple memory importer for container use"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_manager = None
    
    async def initialize(self):
        """Initialize the memory manager"""
        try:
            self.memory_manager = create_memory_manager(memory_type="vector")
            logger.info(f"✅ Memory manager initialized for user {self.user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory manager: {e}")
            raise
    
    def classify_memory(self, memory_text: str) -> Tuple[str, float]:
        """
        Simple classification of memory type and confidence
        
        Returns:
            Tuple[context_type, confidence]
        """
        memory_lower = memory_text.lower().strip()
        
        # Fact indicators (higher confidence)
        if any(indicator in memory_lower for indicator in [
            "my name is", "i am", "i work", "i live", "my age", "my job",
            "i have", "i own", "born", "graduated", "married"
        ]):
            return "personal_facts", 0.9
        
        # Preference indicators
        elif any(indicator in memory_lower for indicator in [
            "i like", "i love", "i enjoy", "i prefer", "favorite", "i hate", "i dislike"
        ]):
            return "preferences", 0.8
        
        # Relationship indicators
        elif any(indicator in memory_lower for indicator in [
            "my wife", "my husband", "my child", "my friend", "my family", "my pet"
        ]):
            return "relationships", 0.85
        
        # Habit/behavior indicators
        elif any(indicator in memory_lower for indicator in [
            "i usually", "i often", "i always", "i never", "i typically"
        ]):
            return "habits_behaviors", 0.7
        
        # Default to general facts
        else:
            return "general_information", 0.6
    
    async def import_memory(self, memory_text: str) -> bool:
        """Import a single memory"""
        try:
            context_type, confidence = self.classify_memory(memory_text)
            
            # Store as a fact with appropriate context
            success = await self.memory_manager.store_fact(
                user_id=self.user_id,
                fact=memory_text,
                context=f"Imported memory - {context_type}",
                confidence=confidence,
                metadata={
                    "import_source": "external_file",
                    "import_timestamp": datetime.utcnow().isoformat(),
                    "memory_category": context_type,
                    "auto_imported": True
                }
            )
            
            if success:
                logger.info(f"✅ Imported: {memory_text[:60]}... [{context_type}, conf:{confidence:.2f}]")
            else:
                logger.warning(f"❌ Failed to import: {memory_text[:60]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error importing '{memory_text[:50]}...': {e}")
            return False
    
    async def import_from_file(self, file_path: str) -> Dict[str, Any]:
        """Import all memories from a file"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Memory file not found: {file_path}")
        
        # Read memories
        with open(file_path, 'r', encoding='utf-8') as f:
            memories = [line.strip() for line in f.readlines() if line.strip()]
        
        logger.info(f"📁 Found {len(memories)} memories in {file_path}")
        
        # Import memories
        results = {
            "total": len(memories),
            "successful": 0,
            "failed": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        for i, memory in enumerate(memories, 1):
            logger.info(f"🔄 Processing {i}/{len(memories)}: {memory[:50]}...")
            
            success = await self.import_memory(memory)
            
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results


async def main():
    if len(sys.argv) != 3:
        print("Usage: python import_memories_simple.py <user_id> <memory_file.txt>")
        print("\nExample:")
        print("  python import_memories_simple.py 123456789 memories.txt")
        sys.exit(1)
    
    user_id = sys.argv[1]
    memory_file = sys.argv[2]
    
    print("🤖 WhisperEngine Memory Import Tool")
    print("="*50)
    print(f"👤 User ID: {user_id}")
    print(f"📁 Memory file: {memory_file}")
    print("="*50)
    
    try:
        # Initialize importer
        importer = SimpleMemoryImporter(user_id)
        await importer.initialize()
        
        # Run import
        results = await importer.import_from_file(memory_file)
        
        # Print results
        print("\n📊 IMPORT RESULTS")
        print("="*30)
        print(f"📝 Total memories: {results['total']}")
        print(f"✅ Successfully imported: {results['successful']}")
        print(f"❌ Failed to import: {results['failed']}")
        print(f"📈 Success rate: {results['successful']/results['total']*100:.1f}%")
        
        if results['successful'] > 0:
            print(f"\n🎉 Successfully imported {results['successful']} memories!")
            print("💡 You can now use Discord commands like !my_memory to see what the bot remembers.")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} memories failed to import. Check the logs above for details.")
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())