import asyncio
from src_v2.core.database import db_manager

async def check_version():
    await db_manager.connect_postgres()
    try:
        rows = await db_manager.postgres_pool.fetch("SELECT * FROM alembic_version")
        for row in rows:
            print(f"Current Revision: {row['version_num']}")
    finally:
        await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(check_version())
