import asyncio
from typing import Optional
from redis.asyncio import Redis
from qdrant_client import AsyncQdrantClient
from neo4j import AsyncGraphDatabase, AsyncDriver
import asyncpg
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import WriteOptions
from loguru import logger

from src_v2.config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.qdrant_client: Optional[AsyncQdrantClient] = None
        self.neo4j_driver: Optional[AsyncDriver] = None
        self.redis_client: Optional[Redis] = None
        self.influxdb_client: Optional[InfluxDBClient] = None
        self.influxdb_write_api = None

    async def connect_postgres(self):
        try:
            logger.info(f"Connecting to PostgreSQL at {settings.POSTGRES_URL}...")
            self.postgres_pool = await asyncpg.create_pool(settings.POSTGRES_URL)
            logger.info("Connected to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def connect_qdrant(self):
        try:
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
            # Use AsyncQdrantClient for non-blocking operations
            self.qdrant_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
            )
            # Verify connection
            await self.qdrant_client.get_collections()
            logger.info("Connected to Qdrant.")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def connect_neo4j(self):
        try:
            logger.info(f"Connecting to Neo4j at {settings.NEO4J_URL}...")
            auth = (settings.NEO4J_USER, settings.NEO4J_PASSWORD.get_secret_value())
            self.neo4j_driver = AsyncGraphDatabase.driver(settings.NEO4J_URL, auth=auth)
            # Verify connection
            await self.neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4j.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def connect_redis(self):
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_URL}...")
            self.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def connect_influxdb(self):
        try:
            logger.info(f"Connecting to InfluxDB at {settings.INFLUXDB_URL}...")
            self.influxdb_client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN.get_secret_value() if settings.INFLUXDB_TOKEN else None,
                org=settings.INFLUXDB_ORG
            )
            # Create write API (synchronous but fast enough for batching, or we can use async client if needed)
            # For now, using synchronous write_api with batching
            self.influxdb_write_api = self.influxdb_client.write_api(write_options=WriteOptions(batch_size=1))
            
            # Verify connection
            self.influxdb_client.ping()
            logger.info("Connected to InfluxDB.")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            # We don't raise here because InfluxDB is optional for core functionality
            # raise

    async def connect_all(self):
        await asyncio.gather(
            self.connect_postgres(),
            self.connect_qdrant(),
            self.connect_neo4j(),
            self.connect_redis(),
            self.connect_influxdb()
        )

    async def disconnect_all(self):
        logger.info("Disconnecting from databases...")
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.aclose()
        if self.qdrant_client:
            await self.qdrant_client.close()
        if self.influxdb_client:
            self.influxdb_client.close()
        logger.info("Disconnected from databases.")

# Global database manager instance
db_manager = DatabaseManager()
