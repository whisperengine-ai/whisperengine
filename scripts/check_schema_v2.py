import asyncio
from src_v2.core.database import db_manager

async def check_schema():
    await db_manager.connect_postgres()
    try:
        rows = await db_manager.postgres_pool.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'v2_user_relationships'
        """)
        for row in rows:
            print(f"{row['column_name']}: {row['data_type']}")
    finally:
        await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(check_schema())
