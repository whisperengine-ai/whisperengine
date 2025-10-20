#!/usr/bin/env python3
"""
Setup Qdrant Collection Aliases for WhisperEngine

This script creates collection aliases to provide clean names for collections
with the _7d suffix. This is INSTANT (no copying) and allows bots to use
clean collection names while keeping existing data.

Usage:
    python scripts/setup_collection_aliases.py [--dry-run]

Collections to alias:
- whisperengine_memory_jake_7d → whisperengine_memory_jake
- whisperengine_memory_elena_7d → whisperengine_memory_elena
- whisperengine_memory_marcus_7d → whisperengine_memory_marcus
- whisperengine_memory_dream_7d → whisperengine_memory_dream
- whisperengine_memory_gabriel_7d → whisperengine_memory_gabriel
- whisperengine_memory_sophia_7d → whisperengine_memory_sophia
- whisperengine_memory_ryan_7d → whisperengine_memory_ryan
"""

import argparse
import sys
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models


# Collections that need aliases (source → alias)
COLLECTIONS_TO_ALIAS = [
    ("whisperengine_memory_jake_7d", "whisperengine_memory_jake"),
    ("whisperengine_memory_elena_7d", "whisperengine_memory_elena"),
    ("whisperengine_memory_marcus_7d", "whisperengine_memory_marcus"),
    ("whisperengine_memory_dream_7d", "whisperengine_memory_dream"),
    ("whisperengine_memory_gabriel_7d", "whisperengine_memory_gabriel"),
    ("whisperengine_memory_sophia_7d", "whisperengine_memory_sophia"),
    ("whisperengine_memory_ryan_7d", "whisperengine_memory_ryan"),
]


def check_collection_exists(client: QdrantClient, collection_name: str) -> bool:
    """Check if a collection exists."""
    try:
        client.get_collection(collection_name)
        return True
    except Exception:
        return False


def check_alias_exists(client: QdrantClient, alias_name: str) -> bool:
    """Check if an alias already exists."""
    try:
        aliases = client.get_aliases()
        for alias in aliases.aliases:
            if alias.alias_name == alias_name:
                return True
        return False
    except Exception:
        return False


def get_alias_target(client: QdrantClient, alias_name: str) -> str | None:
    """Get the collection name that an alias points to."""
    try:
        aliases = client.get_aliases()
        for alias in aliases.aliases:
            if alias.alias_name == alias_name:
                return alias.collection_name
        return None
    except Exception:
        return None


def create_alias(
    client: QdrantClient, 
    collection_name: str, 
    alias_name: str,
    dry_run: bool = False
) -> bool:
    """Create a collection alias."""
    try:
        if dry_run:
            print(f"  [DRY-RUN] Would create alias: {alias_name} → {collection_name}")
            return True
        
        client.update_collection_aliases(
            change_aliases_operations=[
                models.CreateAliasOperation(
                    create_alias=models.CreateAlias(
                        collection_name=collection_name,
                        alias_name=alias_name
                    )
                )
            ]
        )
        print(f"  ✅ Created alias: {alias_name} → {collection_name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create alias: {e}")
        return False


def validate_setup(client: QdrantClient, collections_to_alias: List[Tuple[str, str]]) -> Tuple[bool, List[str]]:
    """
    Validate that we can proceed with alias creation.
    Returns (is_valid, list_of_collections_to_delete)
    """
    print("\n🔍 Validating setup...")
    all_valid = True
    collections_to_delete = []
    
    for source_collection, alias_name in collections_to_alias:
        print(f"\n  Checking: {source_collection} → {alias_name}")
        
        # Check source exists
        if not check_collection_exists(client, source_collection):
            print(f"    ❌ Source collection '{source_collection}' does not exist!")
            all_valid = False
            continue
        else:
            print(f"    ✅ Source collection exists")
        
        # Check if alias already exists
        if check_alias_exists(client, alias_name):
            existing_target = get_alias_target(client, alias_name)
            if existing_target == source_collection:
                print(f"    ⚠️  Alias already exists and points to correct collection")
            else:
                print(f"    ❌ Alias already exists but points to: {existing_target}")
                all_valid = False
        else:
            print(f"    ✅ Alias name available")
        
        # Check if clean name exists as a real collection (will need deletion)
        if check_collection_exists(client, alias_name):
            print(f"    ⚠️  Collection '{alias_name}' exists - will be deleted before creating alias")
            collections_to_delete.append(alias_name)
    
    return all_valid, collections_to_delete


def setup_aliases(dry_run: bool = False) -> bool:
    """Main function to set up all collection aliases."""
    print("=" * 80)
    print("🏷️  WhisperEngine Qdrant Collection Alias Setup")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY-RUN MODE - No changes will be made\n")
    
    # Connect to Qdrant
    print("\n📡 Connecting to Qdrant (localhost:6334)...")
    try:
        client = QdrantClient(host="localhost", port=6334)
        print("  ✅ Connected successfully")
    except Exception as e:
        print(f"  ❌ Failed to connect: {e}")
        return False
    
    # Validate setup
    is_valid, collections_to_delete = validate_setup(client, COLLECTIONS_TO_ALIAS)
    if not is_valid:
        print("\n❌ Validation failed! Please fix the issues above before proceeding.")
        return False
    
    print("\n" + "=" * 80)
    print(f"✅ Validation complete - Ready to create {len(COLLECTIONS_TO_ALIAS)} aliases")
    if collections_to_delete:
        print(f"⚠️  Will delete {len(collections_to_delete)} conflicting collection(s) first")
    print("=" * 80)
    
    # Confirm before proceeding (unless dry-run)
    if not dry_run:
        print("\n⚠️  This will:")
        if collections_to_delete:
            print("\n  1. DELETE the following conflicting collections:")
            for col in collections_to_delete:
                print(f"     • {col}")
            print("\n  2. CREATE aliases for:")
        else:
            print("\n  CREATE aliases for:")
        for source, alias in COLLECTIONS_TO_ALIAS:
            print(f"     • {alias} → {source}")
        print("\n💡 Benefits:")
        print("  • Instant (no copying)")
        print("  • Bots can use clean names immediately")
        print("  • Original data in _7d collections remains untouched")
        print("  • Can migrate data later and switch aliases atomically")
        
        response = input("\n🤔 Proceed with deletion + alias creation? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n❌ Cancelled by user")
            return False
    
    # Delete conflicting collections first
    if collections_to_delete:
        print("\n🗑️  Deleting conflicting collections...")
        for collection_name in collections_to_delete:
            try:
                if dry_run:
                    print(f"  [DRY-RUN] Would delete collection: {collection_name}")
                else:
                    client.delete_collection(collection_name)
                    print(f"  ✅ Deleted collection: {collection_name}")
            except Exception as e:
                print(f"  ❌ Failed to delete {collection_name}: {e}")
                return False
    
    # Create aliases
    print("\n🚀 Creating aliases...")
    success_count = 0
    failed_count = 0
    
    for source_collection, alias_name in COLLECTIONS_TO_ALIAS:
        print(f"\n📌 Processing: {source_collection} → {alias_name}")
        
        # Skip if alias already exists and points to correct collection
        if check_alias_exists(client, alias_name):
            existing_target = get_alias_target(client, alias_name)
            if existing_target == source_collection:
                print(f"  ⏭️  Skipping - alias already exists and is correct")
                success_count += 1
                continue
        
        if create_alias(client, source_collection, alias_name, dry_run):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"  ✅ Successful: {success_count}/{len(COLLECTIONS_TO_ALIAS)}")
    if failed_count > 0:
        print(f"  ❌ Failed: {failed_count}/{len(COLLECTIONS_TO_ALIAS)}")
    
    if dry_run:
        print("\n💡 This was a dry-run. Run without --dry-run to create aliases.")
    else:
        if failed_count == 0:
            print("\n✅ All aliases created successfully!")
            print("\n📋 Next Steps:")
            print("  1. Update .env.{bot_name} files to use clean collection names")
            print("  2. Restart bots (they'll use aliases → existing data)")
            print("  3. Verify bots can retrieve memories correctly")
            print("  4. Remove BOT_COLLECTION_MAPPING from enrichment worker")
            print("  5. Later: migrate data to clean collections and switch aliases")
        else:
            print("\n⚠️  Some aliases failed to create. Please check the errors above.")
    
    return failed_count == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Qdrant collection aliases for WhisperEngine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry-run without making changes'
    )
    
    args = parser.parse_args()
    
    success = setup_aliases(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
