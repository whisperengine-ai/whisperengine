"""
ChatGPT Memories Import via Bot API

This is the PREFERRED way to import ChatGPT memories. Instead of manually 
parsing and routing to fact/preference storage, we format memories as natural
user messages and send them through the bot's HTTP chat API.

This approach:
- Uses existing fact/preference extraction pipeline
- Consistent with how real conversations are processed
- Automatically benefits from any extraction improvements
- Natural language processing instead of regex parsing
- Facts and preferences stored via same enrichment worker logic

Usage:
    python scripts/chatgpt_import/import_via_bot_api.py \
        --file memories.txt \
        --user-id YOUR_DISCORD_ID \
        --bot-name elena \
        --bot-port 9091
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List
import httpx
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ChatGPTMemoriesAPIImporter:
    """Import ChatGPT memories by sending them as natural messages through bot API"""
    
    def __init__(
        self,
        user_id: str,
        bot_name: str,
        bot_port: int,
        dry_run: bool = False,
        verbose: bool = False,
        delay_seconds: float = 2.0
    ):
        """
        Initialize API-based importer
        
        Args:
            user_id: Discord user ID or universal user ID
            bot_name: Name of bot character (elena, marcus, etc.)
            bot_port: HTTP port for bot (elena=9091, marcus=9092, etc.)
            dry_run: If True, only print what would be sent
            verbose: Verbose logging
            delay_seconds: Delay between messages to avoid overwhelming bot
        """
        self.user_id = user_id
        self.bot_name = bot_name
        self.bot_port = bot_port
        # Use localhost - works both inside and outside containers
        # Inside container: localhost connects to the same container's API
        # Outside container: localhost connects to exposed port
        self.bot_url = f"http://localhost:{bot_port}/api/chat"
        self.dry_run = dry_run
        self.verbose = verbose
        self.delay_seconds = delay_seconds
        
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def convert_memory_to_natural_statement(self, memory_text: str) -> str:
        """
        Convert ChatGPT memory format to natural user statement.
        
        ChatGPT memories often start with "User" which feels unnatural.
        Convert to first-person statements that sound like real user messages.
        
        Examples:
            "User likes pizza" → "I like pizza"
            "User has a cat named Luna" → "I have a cat named Luna"
            "User prefers dark mode" → "I prefer dark mode"
            "User is a software engineer" → "I'm a software engineer"
        """
        memory_lower = memory_text.lower().strip()
        
        # Remove "User" prefix and convert to first person
        replacements = [
            ("user likes ", "I like "),
            ("user dislikes ", "I dislike "),
            ("user enjoys ", "I enjoy "),
            ("user prefers ", "I prefer "),
            ("user loves ", "I love "),
            ("user hates ", "I hate "),
            ("user has ", "I have "),
            ("user owns ", "I own "),
            ("user is ", "I'm "),
            ("user works on ", "I work on "),
            ("user wants to ", "I want to "),
            ("user's ", "My "),
        ]
        
        result = memory_text
        for pattern, replacement in replacements:
            if memory_lower.startswith(pattern):
                # Preserve original capitalization for the rest
                result = replacement + memory_text[len(pattern):]
                break
        
        return result.strip()
    
    async def send_message_to_bot(self, message: str) -> bool:
        """
        Send a message to bot via HTTP chat API
        
        Args:
            message: The message text to send
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "user_id": self.user_id,
            "message": message,
            "metadata": {
                "platform": "chatgpt_import",
                "channel_type": "dm",
                "import_timestamp": datetime.now().isoformat()
            }
        }
        
        if self.dry_run:
            logger.info("🔍 [DRY RUN] Would send to %s: %s", self.bot_url, message)
            return True
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.bot_url, json=payload)
                
                if response.status_code == 200:
                    if self.verbose:
                        logger.info("✅ Sent: %s", message[:100])
                    return True
                else:
                    logger.error("❌ Failed to send message (status %d): %s", 
                               response.status_code, response.text[:200])
                    return False
                    
        except Exception as e:
            logger.error("❌ Error sending message: %s", e)
            return False
    
    async def import_memories_file(self, file_path: str) -> dict:
        """
        Import memories from text file by sending through bot API
        
        Args:
            file_path: Path to memories file (one memory per line or blocks)
            
        Returns:
            Dictionary with import statistics
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Memories file not found: {file_path}")
            
            logger.info("📁 Importing memories from: %s", file_path)
            logger.info("🤖 Bot: %s (port %d)", self.bot_name, self.bot_port)
            logger.info("👤 User ID: %s", self.user_id)
            
            # Read memories (split by blank lines to handle multi-line blocks)
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            memory_blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
            total_blocks = len(memory_blocks)
            
            logger.info("📋 Found %d memory blocks to import", total_blocks)
            
            if self.dry_run:
                logger.info("🔍 DRY RUN MODE - No messages will be sent")
            
            # Process each memory block
            for block_num, memory_block in enumerate(memory_blocks, 1):
                # Skip comments
                if memory_block.startswith('#'):
                    self.skipped_count += 1
                    continue
                
                # Convert to natural statement
                natural_message = self.convert_memory_to_natural_statement(memory_block)
                
                # Send to bot
                success = await self.send_message_to_bot(natural_message)
                
                if success:
                    self.processed_count += 1
                else:
                    self.error_count += 1
                
                # Progress logging
                if block_num % 5 == 0 or block_num == total_blocks:
                    logger.info("🔄 Progress: %d/%d memories processed", block_num, total_blocks)
                
                # Delay between messages to avoid overwhelming bot
                if not self.dry_run and block_num < total_blocks:
                    await asyncio.sleep(self.delay_seconds)
            
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


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Import ChatGPT memories by sending through bot HTTP API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import to Elena bot
  python scripts/chatgpt_import/import_via_bot_api.py \\
      --file memories.txt --user-id 123456789 --bot-name elena --bot-port 9091
  
  # Dry run to see what would be sent
  python scripts/chatgpt_import/import_via_bot_api.py \\
      --file memories.txt --user-id 123456789 --bot-name marcus --bot-port 9092 --dry-run
  
  # Custom delay between messages
  python scripts/chatgpt_import/import_via_bot_api.py \\
      --file memories.txt --user-id 123456789 --bot-name elena --bot-port 9091 --delay 1.0

Bot Ports:
  elena: 9091, marcus: 9092, jake: 9097, ryan: 9093
  gabriel: 9095, sophia: 9096, dream: 9094, dotty: 9098
  aetheris: 9099, aethys: 3007
        """
    )
    
    parser.add_argument("--file", required=True, help="Path to memories file")
    parser.add_argument("--user-id", required=True, help="Discord user ID")
    parser.add_argument("--bot-name", required=True, help="Bot character name")
    parser.add_argument("--bot-port", type=int, required=True, help="Bot HTTP port")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--delay", type=float, default=2.0, 
                       help="Delay between messages in seconds (default: 2.0)")
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = ChatGPTMemoriesAPIImporter(
        user_id=args.user_id,
        bot_name=args.bot_name,
        bot_port=args.bot_port,
        dry_run=args.dry_run,
        verbose=args.verbose,
        delay_seconds=args.delay
    )
    
    # Run import
    stats = await importer.import_memories_file(args.file)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Import Summary")
    print("=" * 60)
    print(f"Total memories: {stats['total_blocks']}")
    print(f"Processed: {stats['processed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No messages were actually sent")
        print("Remove --dry-run flag to perform actual import")
    else:
        print("\n✅ Memories sent to bot successfully!")
        print(f"💡 The enrichment worker will process these messages and extract")
        print(f"   facts/preferences in the background (may take a few minutes)")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
