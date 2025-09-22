#!/usr/bin/env python3
"""
WhisperEngine Memory Import Tool

Import memories from a text file into WhisperEngine's vector memory system.
Each line in the file should contain one memory/fact about the user.

Usage:
    python import_memories.py <user_id> <memory_file.txt> [options]

Examples:
    # Import for current bot:
    python import_memories.py 123456789 chatgpt_memories.txt --dry-run
    
    # Import for specific bot:
    python import_memories.py 123456789 user_facts.txt --bot-name Elena --confidence 0.9
    
    # Check available options:
    python import_memories.py --help
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from memory.memory_protocol import create_memory_manager
from memory.vector_memory_system import MemoryType, MemoryTier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryClassifier:
    """Classify memory types and extract relevant metadata"""
    
    def __init__(self):
        # Patterns to identify different types of memories
        self.fact_patterns = [
            (r"(i am|i'm|my name is|user is|user's name is)\s+(.+)", "personal_identity"),
            (r"(i live|i'm from|user lives|based in|located in)\s+(.+)", "location"),
            (r"(i work|i'm a|my job|profession|career|user works)\s+(.+)", "career"),
            (r"(i have|i own|user has|user owns)\s+(.+)", "possessions"),
            (r"(my age|i am \d+|user is \d+|age|born)\s*(.+)", "age_info"),
        ]
        
        self.preference_patterns = [
            (r"(i like|i love|i enjoy|i prefer|user likes|user loves|user enjoys|favorite)\s+(.+)", "likes"),
            (r"(i dislike|i hate|i don't like|user dislikes|user hates)\s+(.+)", "dislikes"),
            (r"(i usually|i typically|i often|user usually|user typically)\s+(.+)", "habits"),
        ]
        
        self.relationship_patterns = [
            (r"(my wife|my husband|my partner|my spouse|married to|user's wife|user's husband)\s+(.+)", "spouse"),
            (r"(my child|my son|my daughter|my kids|user's child|user's son|user's daughter)\s+(.+)", "children"),
            (r"(my parent|my mother|my father|my mom|my dad|user's parent)\s+(.+)", "parents"),
            (r"(my friend|my colleague|my coworker|user's friend)\s+(.+)", "friends"),
            (r"(my pet|my dog|my cat|user's pet|user's dog|user's cat)\s+(.+)", "pets"),
        ]
        
        self.context_patterns = [
            (r"(when|during|while|at the time|context|situation)\s+(.+)", "temporal_context"),
            (r"(because|since|due to|reason|explanation)\s+(.+)", "causal_context"),
        ]
    
    def classify_memory(self, memory_text: str) -> Tuple[MemoryType, str, Dict[str, Any]]:
        """
        Classify a memory and extract metadata
        
        Returns:
            Tuple[MemoryType, category, metadata]
        """
        memory_lower = memory_text.lower().strip()
        
        # Check for facts
        for pattern, category in self.fact_patterns:
            if re.search(pattern, memory_lower):
                return MemoryType.FACT, category, {
                    "fact_type": "personal_fact",
                    "category": category,
                    "original_text": memory_text
                }
        
        # Check for preferences
        for pattern, category in self.preference_patterns:
            if re.search(pattern, memory_lower):
                return MemoryType.PREFERENCE, category, {
                    "preference_type": category,
                    "original_text": memory_text
                }
        
        # Check for relationships
        for pattern, category in self.relationship_patterns:
            if re.search(pattern, memory_lower):
                return MemoryType.RELATIONSHIP, category, {
                    "relationship_type": category,
                    "original_text": memory_text
                }
        
        # Check for context
        for pattern, category in self.context_patterns:
            if re.search(pattern, memory_lower):
                return MemoryType.CONTEXT, category, {
                    "context_type": category,
                    "original_text": memory_text
                }
        
        # Default to fact if no specific pattern matches
        return MemoryType.FACT, "general_fact", {
            "fact_type": "general_fact",
            "original_text": memory_text
        }
    
    def determine_confidence(self, memory_text: str, memory_type: MemoryType) -> float:
        """Determine confidence level based on memory content and type"""
        
        # Higher confidence for specific, structured information
        high_confidence_indicators = [
            r"\d+",  # Contains numbers (dates, ages, etc.)
            r"(named|called|is)",  # Definitive statements
            r"(always|never|every)",  # Absolute statements
        ]
        
        # Lower confidence for vague or opinion-based statements
        low_confidence_indicators = [
            r"(maybe|possibly|might|perhaps|sometimes|occasionally)",
            r"(i think|i believe|probably|likely)",
        ]
        
        memory_lower = memory_text.lower()
        
        confidence = 0.8  # Base confidence
        
        # Adjust based on indicators
        for pattern in high_confidence_indicators:
            if re.search(pattern, memory_lower):
                confidence += 0.1
                
        for pattern in low_confidence_indicators:
            if re.search(pattern, memory_lower):
                confidence -= 0.2
        
        # Adjust based on memory type
        if memory_type == MemoryType.FACT:
            confidence += 0.05
        elif memory_type == MemoryType.PREFERENCE:
            confidence += 0.0  # Neutral
        elif memory_type == MemoryType.RELATIONSHIP:
            confidence += 0.1  # Usually high confidence
        
        # Ensure confidence is in valid range
        return max(0.1, min(1.0, confidence))


class MemoryImporter:
    """Import memories from file into WhisperEngine vector memory"""
    
    def __init__(self, user_id: str, bot_name: Optional[str] = None):
        self.user_id = user_id
        self.bot_name = bot_name or os.getenv("DISCORD_BOT_NAME", "unknown")
        self.classifier = MemoryClassifier()
        self.memory_manager = None
        # Set the bot name in environment for memory system
        os.environ["DISCORD_BOT_NAME"] = self.bot_name
        
    async def initialize(self):
        """Initialize the memory manager"""
        self.memory_manager = create_memory_manager(memory_type="vector")
        logger.info(f"Memory manager initialized for user {self.user_id} (bot: {self.bot_name})")
    
    def read_memory_file(self, file_path: str) -> List[str]:
        """Read memories from file, one per line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                memories = [line.strip() for line in f.readlines() if line.strip()]
            logger.info(f"Read {len(memories)} memories from {file_path}")
            return memories
        except Exception as e:
            logger.error(f"Failed to read memory file {file_path}: {e}")
            raise
    
    async def import_memory(
        self, 
        memory_text: str, 
        confidence_override: float = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Import a single memory with classification and analysis"""
        
        # Classify the memory
        memory_type, category, metadata = self.classifier.classify_memory(memory_text)
        
        # Determine confidence
        confidence = confidence_override or self.classifier.determine_confidence(memory_text, memory_type)
        
        # Prepare context for storage
        context = f"Imported from external source - {category}"
        
        # Add import metadata
        import_metadata = {
            **metadata,
            "import_source": "chatgpt_memories",
            "import_timestamp": datetime.utcnow().isoformat(),
            "memory_category": category,
            "auto_classified": True,
            "import_confidence": confidence
        }
        
        result = {
            "memory_text": memory_text,
            "memory_type": memory_type.value,
            "category": category,
            "confidence": confidence,
            "metadata": import_metadata,
            "success": False
        }
        
        if dry_run:
            result["action"] = "DRY RUN - would store"
            result["success"] = True
            return result
        
        try:
            # Store the memory based on type
            if memory_type in [MemoryType.FACT, MemoryType.PREFERENCE, MemoryType.RELATIONSHIP]:
                success = await self.memory_manager.store_fact(
                    user_id=self.user_id,
                    fact=memory_text,
                    context=context,
                    confidence=confidence,
                    metadata=import_metadata
                )
            else:
                # For other types, store as conversation context
                success = await self.memory_manager.store_conversation(
                    user_id=self.user_id,
                    user_message=f"Context: {memory_text}",
                    bot_response="Memory imported and catalogued.",
                    metadata=import_metadata
                )
            
            result["success"] = success
            result["action"] = "stored" if success else "failed to store"
            
        except Exception as e:
            logger.error(f"Failed to import memory '{memory_text[:50]}...': {e}")
            result["error"] = str(e)
            result["action"] = "error during storage"
        
        return result
    
    async def import_memories_from_file(
        self, 
        file_path: str, 
        confidence_override: float = None,
        dry_run: bool = False,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Import all memories from a file"""
        
        start_time = datetime.utcnow()
        
        # Read memories from file
        memories = self.read_memory_file(file_path)
        
        results = {
            "total_memories": len(memories),
            "successful_imports": 0,
            "failed_imports": 0,
            "memories_by_type": {},
            "memories_by_category": {},
            "import_details": [],
            "start_time": start_time.isoformat(),
            "dry_run": dry_run
        }
        
        logger.info(f"Starting import of {len(memories)} memories (dry_run={dry_run})")
        
        # Process memories in batches
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} memories)")
            
            for memory_text in batch:
                if not memory_text.strip():
                    continue
                    
                result = await self.import_memory(
                    memory_text=memory_text,
                    confidence_override=confidence_override,
                    dry_run=dry_run
                )
                
                results["import_details"].append(result)
                
                if result["success"]:
                    results["successful_imports"] += 1
                else:
                    results["failed_imports"] += 1
                
                # Track by type and category
                memory_type = result["memory_type"]
                category = result["category"]
                
                results["memories_by_type"][memory_type] = results["memories_by_type"].get(memory_type, 0) + 1
                results["memories_by_category"][category] = results["memories_by_category"].get(category, 0) + 1
                
                # Log progress
                if not dry_run and result["success"]:
                    logger.info(f"✅ Imported: {memory_text[:60]}... [{memory_type}:{category}]")
                elif not dry_run:
                    logger.warning(f"❌ Failed: {memory_text[:60]}... - {result.get('error', 'Unknown error')}")
                else:
                    logger.info(f"🔍 Would import: {memory_text[:60]}... [{memory_type}:{category}]")
        
        # Calculate final stats
        end_time = datetime.utcnow()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = (end_time - start_time).total_seconds()
        results["success_rate"] = results["successful_imports"] / results["total_memories"] if results["total_memories"] > 0 else 0
        
        return results


def print_import_summary(results: Dict[str, Any]):
    """Print a comprehensive summary of the import operation"""
    
    print("\n" + "="*80)
    print(f"📊 MEMORY IMPORT SUMMARY {'(DRY RUN)' if results['dry_run'] else ''}")
    print("="*80)
    
    print(f"📁 Total memories processed: {results['total_memories']}")
    print(f"✅ Successful imports: {results['successful_imports']}")
    print(f"❌ Failed imports: {results['failed_imports']}")
    print(f"📈 Success rate: {results['success_rate']:.1%}")
    print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
    
    print(f"\n📋 Memories by Type:")
    for mem_type, count in results['memories_by_type'].items():
        print(f"  • {mem_type}: {count}")
    
    print(f"\n🏷️  Memories by Category:")
    for category, count in sorted(results['memories_by_category'].items()):
        print(f"  • {category}: {count}")
    
    if results['failed_imports'] > 0:
        print(f"\n❌ Failed Imports:")
        for detail in results['import_details']:
            if not detail['success']:
                print(f"  • {detail['memory_text'][:60]}... - {detail.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)


async def main():
    parser = argparse.ArgumentParser(
        description="Import memories from a text file into WhisperEngine vector memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be imported
  python import_memories.py 123456789 memories.txt --dry-run
  
  # Import with custom confidence level
  python import_memories.py 123456789 memories.txt --confidence 0.9
  
  # Import with smaller batch size for large files
  python import_memories.py 123456789 memories.txt --batch-size 5
        """
    )
    
    parser.add_argument("user_id", help="Discord user ID to import memories for")
    parser.add_argument("memory_file", help="Path to text file containing memories (one per line)")
    parser.add_argument("--bot-name", help="Target bot name for memory segmentation (default: current DISCORD_BOT_NAME)")
    parser.add_argument("--confidence", type=float, help="Override confidence level (0.0-1.0)")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be imported without actually storing")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of memories to process in each batch")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not os.path.exists(args.memory_file):
        print(f"❌ Error: Memory file '{args.memory_file}' does not exist")
        sys.exit(1)
    
    if args.confidence and (args.confidence < 0.0 or args.confidence > 1.0):
        print(f"❌ Error: Confidence must be between 0.0 and 1.0")
        sys.exit(1)
    
    try:
        # Initialize importer
        importer = MemoryImporter(args.user_id, args.bot_name)
        await importer.initialize()
        
        print(f"🚀 Starting memory import for user {args.user_id}")
        print(f"📁 Source file: {args.memory_file}")
        print(f"🎯 Target bot: {importer.bot_name}")
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No memories will actually be stored")
        
        # Run the import
        results = await importer.import_memories_from_file(
            file_path=args.memory_file,
            confidence_override=args.confidence,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        # Print summary
        print_import_summary(results)
        
        if args.dry_run:
            print("\n💡 To actually import these memories, run the same command without --dry-run")
        else:
            print(f"\n✅ Memory import completed! {results['successful_imports']} memories imported successfully.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())