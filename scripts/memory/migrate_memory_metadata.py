"""Backfill missing metadata fields for all memories in the store."""

import asyncio
import time
from src.memory.integrated_memory_manager import IntegratedMemoryManager

REQUIRED_FIELDS = [
    ("created_at", lambda: time.time()),
    ("last_accessed", lambda: time.time()),
    ("access_count", lambda: 0),
    ("importance_score", lambda: 0.5),
    ("decay_score", lambda: 0.0),
    ("category", lambda: "general"),
    ("emotional_intensity", lambda: 0.0),
]

async def migrate_all_users():
    mm = IntegratedMemoryManager()
    users = await mm.get_all_user_ids()
    for user_id in users:
        memories = await mm.get_memories_by_user(user_id)
        for mem in memories:
            updated = False
            for field, default_fn in REQUIRED_FIELDS:
                if field not in mem:
                    mem[field] = default_fn()
                    updated = True
            if updated:
                await mm.update_memory_metadata(mem["id"], mem)
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_all_users())
