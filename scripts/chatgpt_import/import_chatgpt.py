#!/usr/bin/env python3
"""
ChatGPT Conversation Import Script for WhisperEngine

Usage:
    python scripts/chatgpt_import/import_chatgpt.py --file conversations.json --user-id 123456789
    
Requirements:
    - WhisperEngine environment set up
    - Valid .env file with database credentials
    - conversations.json from ChatGPT export
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.chatgpt_import.importer import ChatGPTImporter
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import ChatGPT conversations to WhisperEngine')
    parser.add_argument('--file', '-f', required=True, help='Path to conversations.json file')
    parser.add_argument('--user-id', '-u', type=int, required=True, help='Discord user ID')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Parse and validate without storing (dry run)')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate file exists
    if not Path(args.file).exists():
        print(f"Error: File {args.file} not found")
        return 1
        
    # Run import
    try:
        importer = ChatGPTImporter(args.user_id, dry_run=args.dry_run, verbose=args.verbose)
        
        if args.dry_run:
            print("🧪 DRY RUN MODE - No data will be stored")
        
        await importer.initialize()
        
        result = await importer.import_conversations(args.file)
        
        if args.dry_run:
            print("✅ Dry run completed successfully!")
            print("📋 Parsing Results:")
        else:
            print("✅ Import completed successfully!")
        
        print(f"📊 Conversations processed: {result['conversations_imported']}")
        print(f"💬 Messages processed: {result['messages_processed']}")
        print(f"👤 User ID: {result['user_id']}")
        
        if args.dry_run:
            print("\n🔄 To perform actual import, run without --dry-run flag")
        
        return 0
        
    except Exception as e:
        print(f"❌ {'Dry run' if args.dry_run else 'Import'} failed: {e}")
        logger.error("Operation failed with error: %s", e, exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))