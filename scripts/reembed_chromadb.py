#!/usr/bin/env python3
"""
Re-embed existing ChromaDB collections with the new 384-dim embedding model (all-MiniLM-L6-v2).

Use when migrating from a 768-dim embedding model (e.g., all-mpnet-base-v2) to 384-dim.

Process Overview:
1. Connect to ChromaDB (HTTP or local depending on env vars)
2. Detect existing collection(s) and stored embedding dimension
3. Export all documents + metadata (ignoring previous embeddings)
4. Delete and recreate target collection with new metadata indicating 384-dim
5. Re-embed content in batches and insert
6. Provide progress reporting and safety confirmations

Safe by default:
- Won't run unless user confirms (or passes --yes)
- Creates timestamped JSON export backup before modifying

Usage:
    source .venv/bin/activate && python scripts/reembed_chromadb.py \
        --collection user_memories --batch-size 64

Options:
    --collection <name>        Specific collection (default: user_memories)
    --global-collection <name> Re-embed global collection as well
    --all                      Re-embed all collections (overrides specific choices)
    --host <host>              Chroma host (override env)
    --port <port>              Chroma port (override env)
    --persist-path <path>      Local Chroma path override
    --batch-size <n>           Embedding batch size (default 64)
    --yes                      Skip confirmation prompt
    --dry-run                  Show plan only, no changes

Environment variables respected:
    USE_CHROMADB_HTTP, CHROMADB_HOST, CHROMADB_PORT, CHROMADB_PATH

Backup export file naming:
    chroma_export_<collection>_<timestamp>.json

Exit codes:
    0 success
    1 failure
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception as e:  # pragma: no cover - import errors surfaced immediately
    print(f"❌ Failed to import chromadb: {e}")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"❌ Failed to import sentence-transformers: {e}")
    sys.exit(1)

MODEL_NAME = "all-MiniLM-L6-v2"
TARGET_DIM = 384


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Re-embed ChromaDB collections with new 384-dim model")
    p.add_argument("--collection", default=os.getenv("CHROMADB_COLLECTION_NAME", "user_memories"))
    p.add_argument("--global-collection", default=os.getenv("CHROMADB_GLOBAL_COLLECTION_NAME", "global_facts"))
    p.add_argument("--all", action="store_true", help="Re-embed all collections")
    p.add_argument("--host", help="Override Chroma host")
    p.add_argument("--port", type=int, help="Override Chroma port")
    p.add_argument("--persist-path", help="Override local Chroma path")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--dry-run", action="store_true", help="Show actions without modifying")
    return p.parse_args()


def connect_client(args: argparse.Namespace):
    use_http = os.getenv("USE_CHROMADB_HTTP", "false").lower() == "true"
    host = args.host or os.getenv("CHROMADB_HOST", "localhost")
    port = args.port or int(os.getenv("CHROMADB_PORT", "8000"))
    persist_path = args.persist_path or os.getenv("CHROMADB_PATH", "./chromadb_data")

    if use_http:
        print(f"🌐 Connecting to ChromaDB HTTP at {host}:{port}")
        return chromadb.HttpClient(host=host, port=port)
    else:
        print(f"📁 Connecting to local ChromaDB at {persist_path}")
        return chromadb.Client(Settings(is_persistent=True, persist_directory=persist_path))


def list_collections(client) -> List[str]:
    cols = client.list_collections()
    return [c.name for c in cols]


def export_collection(col) -> Dict[str, Any]:
    """Export all documents + metadata (ignoring embeddings)."""
    data = col.get()
    return {
        "ids": data.get("ids", []),
        "documents": data.get("documents", []),
        "metadatas": data.get("metadatas", []),
    }


def backup_export(collection_name: str, payload: Dict[str, Any]) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(f"chroma_export_{collection_name}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def chunked(seq: List[Any], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def reembed_collection(client, name: str, model: SentenceTransformer, batch_size: int, dry_run: bool = False):
    print(f"\n=== Re-embedding collection: {name} ===")
    try:
        col = client.get_collection(name)
    except Exception:
        print(f"⚠️  Collection '{name}' not found, skipping")
        return

    export_payload = export_collection(col)
    count = len(export_payload["ids"])
    if count == 0:
        print("(empty collection) - skipping")
        return

    print(f"Found {count} items. Backing up...")
    backup_path = backup_export(name, export_payload)
    print(f"🗄️  Backup written to {backup_path}")

    if dry_run:
        print("--dry-run enabled: not modifying collection")
        return

    # Delete and recreate collection
    client.delete_collection(name)
    col = client.create_collection(name)
    print("Deleted and recreated collection with fresh schema (384-dim assumed).")

    ids = export_payload["ids"]
    docs = export_payload["documents"]
    metas = export_payload["metadatas"] or [{} for _ in ids]

    start_time = time.time()
    added = 0
    for batch_ids, batch_docs, batch_metas in zip(
        chunked(ids, batch_size), chunked(docs, batch_size), chunked(metas, batch_size)
    ):
        embeddings = model.encode(list(batch_docs), batch_size=len(batch_docs), show_progress_bar=False)
        col.add(ids=list(batch_ids), documents=list(batch_docs), metadatas=list(batch_metas), embeddings=embeddings)
        added += len(list(batch_ids))
        pct = (added / count) * 100
        print(f"Progress: {added}/{count} ({pct:.1f}%)")

    dur = time.time() - start_time
    print(f"✅ Re-embedded {count} items in {dur:.1f}s ({count / dur:.1f} items/sec)")


def main():
    args = parse_args()

    if args.batch_size <= 0:
        print("Batch size must be > 0")
        return 1

    client = connect_client(args)
    available = list_collections(client)
    print(f"📚 Collections detected: {available}")

    target_collections: List[str]
    if args.all:
        target_collections = available
    else:
        target_collections = []
        if args.collection in available:
            target_collections.append(args.collection)
        if args.global_collection and args.global_collection in available:
            target_collections.append(args.global_collection)

    if not target_collections:
        print("No matching collections to re-embed. Exiting.")
        return 0

    print("\nPlanned collections to re-embed:")
    for c in target_collections:
        print(f"  - {c}")

    if not args.yes and not args.dry_run:
        confirm = input("\nType 'REEMBED' to proceed (backup will be created first): ")
        if confirm.strip().upper() != "REEMBED":
            print("Aborted by user.")
            return 1

    print(f"\nLoading embedding model: {MODEL_NAME} (target dim {TARGET_DIM}) ...")
    model = SentenceTransformer(MODEL_NAME)
    test_vec = model.encode(["test"], show_progress_bar=False)[0]
    if len(test_vec) != TARGET_DIM:
        print(f"❌ Dimension mismatch: expected {TARGET_DIM}, got {len(test_vec)}")
        return 1
    print("Model loaded and dimension verified.")

    for name in target_collections:
        reembed_collection(client, name, model, args.batch_size, dry_run=args.dry_run)

    print("\n🎉 Re-embedding process complete.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
