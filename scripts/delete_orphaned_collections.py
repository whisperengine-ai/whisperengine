#!/usr/bin/env python3
"""
Delete Orphaned Qdrant Collections

This script safely deletes orphaned test and legacy collections from Qdrant.
It will NOT delete active bot collections or their _7d sources.

Usage:
    python scripts/delete_orphaned_collections.py [--dry-run]
"""

import argparse
import sys
from datetime import datetime
from qdrant_client import QdrantClient


# Collections to delete (orphaned/test/legacy collections)
ORPHANED_COLLECTIONS = [
    "character_test_scenarios",      # Test collection (0 points)
    "chat_memories",                 # Old format (6,586 points)
    "chat_memories_aethys",          # Duplicate (4 points)
    "dream_memories",                # Old format (391 points)
    "test_atomic_pairs_20251018_094137",  # Test (1 point)
    "test_metrics_collection",       # Test (0 points)
    "test_roberta_emotion",          # Test (0 points)
    "test_sprint2_roberta",          # Test (0 points)
    "whisperengine_memory",          # Test/old (100 points)
    "whisperengine_test_sprint6",    # Test (2 points)
]

# Active collections (DO NOT DELETE)
ACTIVE_COLLECTIONS = [
    "whisperengine_memory_aetheris",
    "whisperengine_memory_aethys",
    "whisperengine_memory_dotty",
    "whisperengine_memory_dream_7d",    # Source for alias
    "whisperengine_memory_elena_7d",    # Source for alias
    "whisperengine_memory_gabriel_7d",  # Source for alias
    "whisperengine_memory_jake_7d",     # Source for alias
    "whisperengine_memory_marcus_7d",   # Source for alias
    "whisperengine_memory_ryan_7d",     # Source for alias
    "whisperengine_memory_sophia_7d",   # Source for alias
]


def validate_collections(client: QdrantClient) -> tuple[list, list]:
    """
    Validate that orphaned collections exist and active collections are safe.
    Returns (collections_to_delete, collections_not_found)
    """
    print("\n🔍 Validating collections...")
    
    # Get all collections
    all_collections = client.get_collections().collections
    collection_names = [c.name for c in all_collections]
    
    # Check each orphaned collection
    to_delete = []
    not_found = []
    
    for collection_name in ORPHANED_COLLECTIONS:
        if collection_name in collection_names:
            info = client.get_collection(collection_name)
            count = info.points_count
            to_delete.append((collection_name, count))
            print(f"  ✅ Found: {collection_name:<50} ({count:>8} points)")
        else:
            not_found.append(collection_name)
            print(f"  ⚠️  Not found: {collection_name}")
    
    # Safety check: ensure we're not deleting active collections
    print("\n🛡️  Safety check - verifying active collections are protected...")
    for collection_name in ACTIVE_COLLECTIONS:
        if collection_name in ORPHANED_COLLECTIONS:
            print(f"  ❌ CRITICAL ERROR: Active collection '{collection_name}' is marked for deletion!")
            return [], []
        if collection_name in collection_names:
            info = client.get_collection(collection_name)
            count = info.points_count
            print(f"  ✅ Protected: {collection_name:<50} ({count:>8} points)")
    
    return to_delete, not_found


def delete_collections(client: QdrantClient, collections: list, dry_run: bool = False) -> tuple[int, int]:
    """
    Delete collections from Qdrant.
    Returns (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    for collection_name, point_count in collections:
        try:
            if dry_run:
                print(f"  [DRY-RUN] Would delete: {collection_name} ({point_count} points)")
                success_count += 1
            else:
                client.delete_collection(collection_name)
                print(f"  ✅ Deleted: {collection_name} ({point_count} points)")
                success_count += 1
        except Exception as e:
            print(f"  ❌ Failed to delete {collection_name}: {e}")
            failure_count += 1
    
    return success_count, failure_count


def create_deletion_report(collections: list, dry_run: bool) -> str:
    """Create a markdown report of deleted collections."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Qdrant Collection Deletion Report

**Date**: {timestamp}
**Mode**: {"DRY-RUN" if dry_run else "LIVE DELETION"}

## Collections {"Would Be " if dry_run else ""}Deleted

| Collection Name | Points | Reason |
|----------------|--------|--------|
"""
    
    reasons = {
        "character_test_scenarios": "Test collection",
        "chat_memories": "Legacy format (replaced by whisperengine_memory_*)",
        "chat_memories_aethys": "Duplicate (superseded by whisperengine_memory_aethys)",
        "dream_memories": "Legacy format (replaced by whisperengine_memory_dream_7d)",
        "test_atomic_pairs_20251018_094137": "Test collection",
        "test_metrics_collection": "Test collection",
        "test_roberta_emotion": "Test collection",
        "test_sprint2_roberta": "Test collection",
        "whisperengine_memory": "Test/incomplete collection",
        "whisperengine_test_sprint6": "Test collection",
    }
    
    total_points = 0
    for collection_name, point_count in collections:
        reason = reasons.get(collection_name, "Unknown")
        report += f"| `{collection_name}` | {point_count:,} | {reason} |\n"
        total_points += point_count
    
    report += f"\n**Total Collections**: {len(collections)}\n"
    report += f"**Total Points Removed**: {total_points:,}\n"
    
    report += "\n## Active Collections (Protected)\n\n"
    report += "The following collections are ACTIVE and were NOT deleted:\n\n"
    for collection_name in ACTIVE_COLLECTIONS:
        report += f"- `{collection_name}`\n"
    
    return report


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Delete orphaned Qdrant collections",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry-run without deleting collections'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🗑️  WhisperEngine Qdrant Collection Cleanup")
    print("=" * 80)
    
    if args.dry_run:
        print("\n⚠️  DRY-RUN MODE - No collections will be deleted\n")
    
    # Connect to Qdrant
    print("\n📡 Connecting to Qdrant (localhost:6334)...")
    try:
        client = QdrantClient(host="localhost", port=6334)
        print("  ✅ Connected successfully")
    except Exception as e:
        print(f"  ❌ Failed to connect: {e}")
        return 1
    
    # Validate collections
    to_delete, not_found = validate_collections(client)
    
    if not to_delete:
        print("\n❌ No collections to delete or validation failed!")
        return 1
    
    if not_found:
        print(f"\n⚠️  Warning: {len(not_found)} collection(s) not found (may have been deleted already)")
    
    # Calculate totals
    total_points = sum(count for _, count in to_delete)
    
    print("\n" + "=" * 80)
    print(f"📊 Summary: {len(to_delete)} collection(s) to delete, {total_points:,} total points")
    print("=" * 80)
    
    # Confirm before deletion (unless dry-run)
    if not args.dry_run:
        print("\n⚠️  This will PERMANENTLY delete the following collections:")
        for collection_name, point_count in to_delete:
            print(f"  • {collection_name} ({point_count:,} points)")
        
        print("\n💡 Active collections are protected and will NOT be deleted.")
        print("💡 The 7 _7d collections contain live data and will be kept.")
        
        response = input("\n🤔 Proceed with deletion? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n❌ Cancelled by user")
            return 0
    
    # Delete collections
    print("\n🗑️  Deleting collections...")
    success_count, failure_count = delete_collections(client, to_delete, args.dry_run)
    
    # Create report
    report = create_deletion_report(to_delete, args.dry_run)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Final Summary")
    print("=" * 80)
    print(f"  ✅ Successfully deleted: {success_count}/{len(to_delete)}")
    if failure_count > 0:
        print(f"  ❌ Failed: {failure_count}/{len(to_delete)}")
    print(f"  📈 Points removed: {total_points:,}")
    
    if args.dry_run:
        print("\n💡 This was a dry-run. Run without --dry-run to actually delete collections.")
    else:
        # Save report
        report_file = f"qdrant_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Deletion report saved to: {report_file}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
