#!/usr/bin/env python3
"""
Vector Format Validation Script

Checks if Qdrant collections use named vectors (compatible) or single vectors (incompatible).
Use this BEFORE merging feature branch to identify migration needs.

Usage:
    python scripts/validate_vector_format.py
"""

import os
from qdrant_client import QdrantClient
from typing import Dict, List, Any


# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6334"))


def validate_vector_format():
    """Check vector format in all collections"""
    
    print("=" * 80)
    print("🔍 VECTOR FORMAT VALIDATION")
    print("=" * 80)
    print()
    
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        # Get all collections
        collections = client.get_collections().collections
        print(f"Found {len(collections)} collections\n")
        
        compatible = []
        incompatible = []
        empty = []
        unknown = []
        
        for collection in collections:
            collection_name = collection.name
            print(f"📦 Collection: {collection_name}")
            print("-" * 80)
            
            try:
                # Get first point with vectors to check format
                result = client.scroll(
                    collection_name=collection_name,
                    limit=1,
                    with_payload=False,
                    with_vectors=True  # Need vectors to check format
                )
                
                points = result[0]
                
                if not points:
                    print("  ⚠️  Empty collection (no data to validate)")
                    print()
                    empty.append(collection_name)
                    continue
                
                point = points[0]
                vector = point.vector
                
                if isinstance(vector, dict):
                    # Named vectors (compatible with feature branch)
                    print("  ✅ NAMED VECTORS (compatible)")
                    vector_names = list(vector.keys())
                    print(f"     Vector names: {', '.join(vector_names)}")
                    
                    # Check if all expected vectors present
                    expected_vectors = {'content', 'emotion', 'semantic'}
                    optional_vectors = {'relationship', 'personality', 'interaction', 'temporal'}
                    
                    missing = expected_vectors - set(vector_names)
                    if missing:
                        print(f"     ⚠️  Missing expected vectors: {', '.join(missing)}")
                    
                    has_enhanced = bool(set(vector_names) & optional_vectors)
                    if has_enhanced:
                        present_enhanced = set(vector_names) & optional_vectors
                        print(f"     🎯 Enhanced vectors present: {', '.join(present_enhanced)}")
                    
                    compatible.append(collection_name)
                    
                elif isinstance(vector, list):
                    # Single vector (incompatible with feature branch)
                    print("  ❌ SINGLE VECTOR (INCOMPATIBLE)")
                    print(f"     Vector dimension: {len(vector)}")
                    print("     ⚠️  Migration required before using feature branch")
                    incompatible.append(collection_name)
                    
                else:
                    # Unknown format
                    print(f"  ⚠️  UNKNOWN FORMAT: {type(vector)}")
                    unknown.append(collection_name)
                
                print()
                
            except Exception as e:
                print(f"  ❌ Error checking collection: {e}")
                print()
                unknown.append(collection_name)
                continue
        
        # Print summary
        print("=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        print()
        
        total = len(collections)
        print(f"Total collections: {total}")
        print(f"  ✅ Compatible (named vectors): {len(compatible)}")
        print(f"  ❌ Incompatible (single vectors): {len(incompatible)}")
        print(f"  ⚠️  Empty collections: {len(empty)}")
        print(f"  ❓ Unknown format: {len(unknown)}")
        print()
        
        if incompatible:
            print("⚠️  INCOMPATIBLE COLLECTIONS FOUND")
            print()
            print("Collections with single vector format:")
            for name in incompatible:
                print(f"  • {name}")
            print()
            print("MIGRATION REQUIRED:")
            print("  Option 1: Create new collections with named vectors (data loss)")
            print("  Option 2: Migrate data to named vector format (complex)")
            print("  Option 3: Update .env files to use different collections")
            print()
            print("⚠️  DO NOT MERGE feature branch until migration complete")
            print()
            return False
        
        if unknown:
            print("⚠️  UNKNOWN FORMATS FOUND")
            print()
            print("Collections with unknown format:")
            for name in unknown:
                print(f"  • {name}")
            print()
            print("Investigate these collections manually before merging.")
            print()
        
        if compatible and not incompatible:
            print("✅ ALL COLLECTIONS COMPATIBLE")
            print()
            print("Safe to merge feature branch (vector format compatible).")
            print()
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = validate_vector_format()
    exit(0 if success else 1)
