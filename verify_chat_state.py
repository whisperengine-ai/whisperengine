import asyncio
import os
import sys
from loguru import logger

# Ensure the current directory is in the python path
sys.path.append(os.getcwd())

from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.memory.manager import memory_manager
from src_v2.knowledge.manager import knowledge_manager

async def verify_state():
    # Set bot name to match the one used in the chat
    settings.DISCORD_BOT_NAME = "elena"
    
    logger.info("Connecting to databases...")
    await db_manager.connect_all()
    
    # 1. Verify Qdrant (Vector Memory)
    logger.info("\n--- Verifying Qdrant (Vector Memory) ---")
    if db_manager.qdrant_client:
        collection_name = f"whisperengine_memory_{settings.DISCORD_BOT_NAME}"
        try:
            # Get collection info
            info = await db_manager.qdrant_client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' exists. Points count: {info.points_count}")
            
            # Scroll through recent points
            points, _ = await db_manager.qdrant_client.scroll(
                collection_name=collection_name,
                limit=10,
                with_payload=True,
                with_vectors=False
            )
            
            if points:
                logger.info(f"Found {len(points)} recent memory points:")
                for p in points:
                    payload = p.payload or {}
                    role = payload.get('role', 'unknown')
                    content = payload.get('content', 'no content')
                    logger.info(f"[{role.upper()}] {content[:100]}...")
            else:
                logger.warning("No points found in Qdrant collection.")
                
        except Exception as e:
            logger.error(f"Qdrant verification failed: {e}")
    else:
        logger.error("Qdrant client not connected.")

    # 2. Verify Neo4j (Knowledge Graph)
    logger.info("\n--- Verifying Neo4j (Knowledge Graph) ---")
    if db_manager.neo4j_driver:
        try:
            # We don't know the exact user ID from the chat log provided (it's just "MarkAnthony"),
            # but we can query ALL nodes to see what's there.
            query = """
            MATCH (u:User)-[r:FACT]->(o:Entity)
            RETURN u.id, r.predicate, o.name
            LIMIT 20
            """
            async with db_manager.neo4j_driver.session() as session:
                result = await session.run(query)
                records = await result.data()
                
                if records:
                    logger.info(f"Found {len(records)} knowledge facts:")
                    for r in records:
                        logger.info(f"User({r['u.id']}) -[{r['r.predicate']}]-> Entity({r['o.name']})")
                else:
                    logger.warning("No knowledge facts found in Neo4j.")
                    
        except Exception as e:
            logger.error(f"Neo4j verification failed: {e}")
    else:
        logger.error("Neo4j driver not connected.")

    # 3. Verify Postgres (Chat History)
    logger.info("\n--- Verifying Postgres (Chat History) ---")
    if db_manager.postgres_pool:
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_id, role, content, timestamp 
                    FROM v2_chat_history 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                
                if rows:
                    logger.info(f"Found {len(rows)} recent chat history entries:")
                    for row in rows:
                        logger.info(f"[{row['timestamp']}] {row['user_id']} ({row['role']}): {row['content'][:50]}...")
                else:
                    logger.warning("No chat history found in Postgres.")
        except Exception as e:
            logger.error(f"Postgres verification failed: {e}")
    else:
        logger.error("Postgres pool not connected.")

    await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(verify_state())
