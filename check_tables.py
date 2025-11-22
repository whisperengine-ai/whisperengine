import asyncio
import os
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://whisper:password@localhost:5432/whisperengine_v2")
    tables = ["v2_goals", "v2_user_goal_progress", "v2_user_relationships"]
    for t in tables:
        exists = await conn.fetchval(f"SELECT to_regclass('{t}')")
        print(f"{t}: {'✅ Exists' if exists else '❌ Missing'}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
