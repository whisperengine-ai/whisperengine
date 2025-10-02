#!/usr/bin/env python3
"""
Bot Name Normalization Audit Script

Scans all Qdrant collections and reports unnormalized bot_name values.
Use this BEFORE merging feature branch to identify migration needs.

Usage:
    python scripts/audit_bot_names.py
"""

import asyncio
import os
from qdrant_client import QdrantClient
from typing import Set, Dict, List

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6334"))


def normalize_bot_name(bot_name: str) -> str:
    """Apply same normalization as vector_memory_system.py"""
    if not bot_name or not isinstance(bot_name, str):
        return "unknown"
    
    # Trim and lowercase
    normalized = bot_name.strip().lower()
    
    # Replace spaces with underscores
    import re
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Remove special characters except underscore/hyphen/alphanumeric
    normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
    
    return normalized


async def audit_bot_names():
    """Scan all collections and report unnormalized bot_name values"""
    
    print("=" * 80)
    print("🔍 BOT NAME NORMALIZATION AUDIT")
    print("=" * 80)
    print()
    
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        # Get all collections
        collections = client.get_collections().collections
        print(f"Found {len(collections)} collections\n")
        
        issues_found = False
        summary: Dict[str, List[str]] = {}
        
        for collection in collections:
            collection_name = collection.name
            print(f"📦 Collection: {collection_name}")
            print("-" * 80)
            
            # Scroll through first 1000 memories (sufficient for audit)
            try:
                result = client.scroll(
                    collection_name=collection_name,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False
                )
                
                points = result[0]
                
                if not points:
                    print("  ⚠️  Empty collection")
                    print()
                    continue
                
                # Collect unique bot_name values
                bot_names: Set[str] = set()
                missing_count = 0
                
                for point in points:
                    payload = getattr(point, 'payload', {}) or {}
                    bot_name = payload.get('bot_name', None)
                    
                    if bot_name is None:
                        missing_count += 1
                    else:
                        bot_names.add(bot_name)
                
                print(f"  Total memories scanned: {len(points)}")
                print(f"  Unique bot_name values: {len(bot_names)}")
                
                if missing_count > 0:
                    print(f"  ⚠️  Missing bot_name field: {missing_count} memories")
                    issues_found = True
                
                # Check for unnormalized values
                unnormalized = []
                for name in bot_names:
                    expected = normalize_bot_name(name)
                    if name != expected:
                        unnormalized.append((name, expected))
                        issues_found = True
                
                if unnormalized:
                    print(f"  ❌ UNNORMALIZED VALUES FOUND:")
                    for original, normalized in unnormalized:
                        print(f"     '{original}' → should be '{normalized}'")
                    summary[collection_name] = [f"{orig} → {norm}" for orig, norm in unnormalized]
                else:
                    print(f"  ✅ All bot_name values properly normalized")
                    if bot_names:
                        print(f"     Values: {', '.join(sorted(bot_names))}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Error scanning collection: {e}")
                print()
                continue
        
        # Print summary
        print("=" * 80)
        print("📊 AUDIT SUMMARY")
        print("=" * 80)
        print()
        
        if not issues_found:
            print("✅ NO ISSUES FOUND - All bot_name values are properly normalized!")
            print()
            print("Safe to merge feature branch without bot_name migration.")
            return
        
        print("⚠️  ISSUES FOUND - Migration required before merging feature branch")
        print()
        
        if summary:
            print("Collections requiring normalization:")
            for collection, issues in summary.items():
                print(f"  • {collection}:")
                for issue in issues:
                    print(f"      {issue}")
            print()
        
        print("RECOMMENDED ACTION:")
        print("  1. Run scripts/normalize_bot_names.py to fix unnormalized values")
        print("  2. Re-run this audit to verify")
        print("  3. Test bots with normalized values")
        print("  4. Then safe to merge feature branch")
        print()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    print()
    asyncio.run(audit_bot_names())
