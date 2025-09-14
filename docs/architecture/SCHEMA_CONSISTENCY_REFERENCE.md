# Schema Consistency and Upgrade Path Documentation

## 🎯 Overview

WhisperEngine maintains **strict schema consistency** across all deployment modes to ensure seamless upgrade paths from desktop installations to self-hosted or cloud dockerized versions. This document details the schema standardization approach across all data stores.

## 📊 Core Schema Consistency

### **Primary Database Schema**

The system uses **identical logical schemas** across SQLite (desktop) and PostgreSQL (Docker/cloud) with automatic syntax translation:

#### **Core Tables Schema**
```sql
-- Consistent across SQLite and PostgreSQL
-- Only syntax differences are handled automatically

-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,              -- SQLite: TEXT PRIMARY KEY
                                          -- PostgreSQL: id SERIAL PRIMARY KEY, user_id TEXT UNIQUE NOT NULL
    username TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    preferences TEXT DEFAULT '{}',         -- JSON stored as TEXT (both backends)
    privacy_settings TEXT DEFAULT '{}'     -- JSON stored as TEXT (both backends)
);

-- Conversations table
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
                                          -- PostgreSQL: id SERIAL PRIMARY KEY
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_content TEXT NOT NULL,
    bot_response TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_used TEXT,
    response_time_ms INTEGER,
    ai_model_used TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
                                          -- PostgreSQL: adds ON DELETE CASCADE
);

-- Memory entries table
CREATE TABLE memory_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Auto-translated for PostgreSQL
    user_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance_score REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]',               -- JSON arrays as TEXT
    metadata TEXT DEFAULT '{}',           -- JSON objects as TEXT
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Facts table
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,                        -- Nullable for global facts
    fact_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.8,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    global_fact BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Emotions table
CREATE TABLE emotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    detected_emotion TEXT NOT NULL,
    confidence REAL NOT NULL,
    context TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_adapted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Relationships table
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- System settings table
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT DEFAULT '{}'               -- JSON as TEXT for consistency
);
```

### **Automatic Schema Translation**

The system automatically translates between database dialects:

```python
# From src/database/database_integration.py
@staticmethod 
def get_postgresql_schema() -> Dict[str, str]:
    """Get PostgreSQL-specific schema (with SERIAL support)"""
    schema = WhisperEngineSchema.get_core_schema()
    
    # Automatic translation rules:
    # SQLite -> PostgreSQL
    schema['users'] = schema['users'].replace(
        'user_id TEXT PRIMARY KEY',
        'id SERIAL PRIMARY KEY, user_id TEXT UNIQUE NOT NULL'
    )
    
    schema['conversations'] = schema['conversations'].replace(
        'id INTEGER PRIMARY KEY AUTOINCREMENT',
        'id SERIAL PRIMARY KEY'
    ).replace(
        'FOREIGN KEY (user_id) REFERENCES users (user_id)',
        'FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE'
    )
    
    # Similar translations for all tables...
```

#### **Key Translation Patterns**

| **Feature** | **SQLite** | **PostgreSQL** | **Compatibility** |
|-------------|------------|----------------|-------------------|
| **Auto-increment** | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` | ✅ Automatic |
| **Foreign Keys** | `FOREIGN KEY (user_id) REFERENCES users (user_id)` | `FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE` | ✅ Enhanced |
| **JSON Storage** | `TEXT DEFAULT '{}'` | `TEXT DEFAULT '{}'` or `JSONB` | ✅ Compatible |
| **Timestamps** | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP` | ✅ Enhanced |
| **Indexes** | Limited | `CREATE INDEX IF NOT EXISTS idx_...` | ✅ Added automatically |

---

## 🗄️ Vector Database Schema Consistency

### **ChromaDB Collections Schema**

**Consistent collection structure** across local (desktop) and HTTP (Docker) ChromaDB:

```python
# Standardized collections across all deployment modes
VECTOR_COLLECTIONS = {
    'user_memories': {
        'description': 'User-specific conversation memories and personal context',
        'embedding_dimension': 384,  # sentence-transformers/all-MiniLM-L6-v2
        'distance_metric': 'cosine',
        'metadata_schema': {
            'user_id': 'string',
            'timestamp': 'datetime',
            'message_type': 'string',
            'channel_id': 'string',
            'importance_score': 'float',
            'emotional_context': 'string',
            'conversation_thread': 'string'
        }
    },
    'global_facts': {
        'description': 'Universal knowledge facts and information',
        'embedding_dimension': 384,
        'distance_metric': 'cosine',
        'metadata_schema': {
            'fact_type': 'string',
            'knowledge_domain': 'string',
            'confidence_score': 'float',
            'source': 'string',
            'timestamp': 'datetime',
            'verified': 'boolean',
            'language': 'string'
        }
    },
    'emotional_contexts': {
        'description': 'Emotional conversation contexts and patterns',
        'embedding_dimension': 384,
        'distance_metric': 'cosine',
        'metadata_schema': {
            'user_id': 'string',
            'detected_emotion': 'string',
            'confidence': 'float',
            'triggers': 'string',
            'response_strategy': 'string',
            'timestamp': 'datetime'
        }
    }
}
```

### **Deployment Mode Mapping**

| **Deployment Mode** | **ChromaDB Backend** | **Collection Storage** | **Embedding Source** |
|---------------------|---------------------|----------------------|---------------------|
| **Desktop** | Local PersistentClient | `~/.whisperengine/chromadb/` | Local sentence-transformers |
| **Docker Compose** | HTTP Client | ChromaDB container volume | External API or local models |
| **Kubernetes** | Distributed HTTP | Persistent volumes | External API recommended |

### **Schema Migration Support**

```python
# Automatic collection schema validation and migration
class VectorSchemaManager:
    async def ensure_collection_schema(self, collection_name: str, expected_schema: Dict):
        """Ensure collection exists with correct schema"""
        
        # Check if collection exists
        collections = await self.chromadb_client.list_collections()
        
        if collection_name not in [c.name for c in collections]:
            # Create collection with schema
            await self.chromadb_client.create_collection(
                name=collection_name,
                metadata=expected_schema
            )
        else:
            # Validate existing schema
            collection = await self.chromadb_client.get_collection(collection_name)
            await self._validate_schema_compatibility(collection, expected_schema)
```

---

## 🗃️ Cache Layer Schema Consistency

### **Redis Key Structure**

**Standardized Redis key patterns** across in-memory (desktop) and Redis (Docker) cache:

```python
# Consistent key structure across memory and Redis cache
CACHE_KEY_PATTERNS = {
    'message_cache': {
        'pattern': 'discord_cache:messages:{channel_id}',
        'type': 'list',
        'ttl': 1800,  # 30 minutes
        'structure': {
            'message_id': 'string',
            'user_id': 'string',
            'content': 'string',
            'timestamp': 'datetime',
            'author_name': 'string',
            'channel_id': 'string',
            'response_quality': 'float'
        }
    },
    'conversation_meta': {
        'pattern': 'discord_cache:meta:{channel_id}',
        'type': 'hash',
        'ttl': 3600,  # 1 hour
        'structure': {
            'last_message_time': 'datetime',
            'message_count': 'integer',
            'active_users': 'set',
            'conversation_quality': 'float'
        }
    },
    'user_session': {
        'pattern': 'discord_cache:session:{user_id}',
        'type': 'hash',
        'ttl': 7200,  # 2 hours
        'structure': {
            'last_seen': 'datetime',
            'current_mood': 'string',
            'conversation_context': 'string',
            'preferences': 'json'
        }
    }
}
```

### **Cache Backend Compatibility**

| **Deployment Mode** | **Cache Backend** | **Serialization** | **Persistence** | **TTL Support** |
|---------------------|------------------|------------------|-----------------|-----------------|
| **Desktop** | In-Memory (deque) | Python pickle | None (ephemeral) | ✅ Background cleanup |
| **Docker Compose** | Redis | JSON + msgpack | ✅ Optional RDB/AOF | ✅ Native Redis TTL |
| **Kubernetes** | Redis Cluster | JSON + msgpack | ✅ Distributed persistence | ✅ Cluster-wide TTL |

### **Message Serialization Consistency**

```python
# Standardized message format across all cache backends
class UniversalMessage:
    """Standard message format for cache consistency"""
    
    def __init__(self, message_id: str, user_id: str, content: str, 
                 timestamp: datetime, channel_id: str, **metadata):
        self.message_id = message_id
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.metadata = metadata
    
    def to_cache_dict(self) -> Dict[str, Any]:
        """Convert to cache-compatible dictionary"""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'channel_id': self.channel_id,
            'metadata': json.dumps(self.metadata)
        }
    
    @classmethod
    def from_cache_dict(cls, data: Dict[str, Any]) -> 'UniversalMessage':
        """Restore from cache dictionary"""
        return cls(
            message_id=data['message_id'],
            user_id=data['user_id'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            channel_id=data['channel_id'],
            **json.loads(data.get('metadata', '{}'))
        )
```

---

## 🕸️ Graph Database Schema Consistency

### **Neo4j Node and Relationship Schema**

**Consistent graph structure** when Neo4j is available (Docker/Kubernetes only):

```cypher
-- User Nodes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT user_discord_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.discord_id IS UNIQUE;

-- Memory Nodes
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;

-- Topic Nodes
CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;

-- Global Fact Nodes
CREATE CONSTRAINT global_fact_id_unique IF NOT EXISTS FOR (gf:GlobalFact) REQUIRE gf.id IS UNIQUE;
CREATE CONSTRAINT global_fact_chromadb_id_unique IF NOT EXISTS FOR (gf:GlobalFact) REQUIRE gf.chromadb_id IS UNIQUE;

-- Relationship Types (consistent across all graph deployments)
(:User)-[:REMEMBERS]->(:Memory)
(:User)-[:INTERESTED_IN]->(:Topic) 
(:User)-[:KNOWS]->(:GlobalFact)
(:Memory)-[:RELATES_TO]->(:Topic)
(:Memory)-[:TRIGGERED_BY]->(:EmotionContext)
(:GlobalFact)-[:BELONGS_TO]->(:KnowledgeDomain)
(:Topic)-[:SUBTOPIC_OF]->(:Topic)
```

### **Fallback to Relational Schema**

When Neo4j is not available (desktop mode), relationships are stored in the primary database:

```sql
-- Relationships table acts as graph fallback
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- Maps to Neo4j relationship types
    target_type TEXT NOT NULL,        -- 'memory', 'topic', 'fact', 'user'
    target_id TEXT NOT NULL,          -- ID of target entity
    strength REAL DEFAULT 0.5,        -- Relationship strength (0.0-1.0)
    properties TEXT DEFAULT '{}',     -- JSON metadata (Neo4j properties)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Index for efficient relationship queries
CREATE INDEX IF NOT EXISTS idx_relationships_user_type ON relationships(user_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_type, target_id);
```

---

## 🔄 Schema Migration and Upgrade Paths

### **Desktop to Docker Migration**

**Seamless upgrade path** from desktop SQLite to Docker PostgreSQL:

```python
class DatabaseMigrationManager:
    """Handles migration between database backends"""
    
    async def migrate_sqlite_to_postgresql(self, sqlite_path: str, postgres_config: Dict):
        """Migrate from SQLite (desktop) to PostgreSQL (Docker)"""
        
        # 1. Connect to both databases
        sqlite_adapter = SQLiteAdapter(sqlite_path)
        postgres_adapter = PostgreSQLAdapter(postgres_config)
        
        await sqlite_adapter.connect()
        await postgres_adapter.connect()
        
        # 2. Create PostgreSQL schema
        postgres_schema = WhisperEngineSchema.get_postgresql_schema()
        await postgres_adapter.create_tables(postgres_schema)
        
        # 3. Migrate data table by table
        tables = ['users', 'conversations', 'memory_entries', 'facts', 
                 'emotions', 'relationships', 'system_settings', 'performance_metrics']
        
        for table in tables:
            await self._migrate_table_data(sqlite_adapter, postgres_adapter, table)
        
        # 4. Verify data integrity
        await self._verify_migration_integrity(sqlite_adapter, postgres_adapter)
        
        return True
    
    async def _migrate_table_data(self, source_adapter, target_adapter, table_name: str):
        """Migrate data for a specific table"""
        
        # Export from SQLite
        result = await source_adapter.execute_query(f"SELECT * FROM {table_name}")
        
        if result.rows:
            # Transform data for PostgreSQL if needed
            transformed_rows = self._transform_data_for_postgres(result.rows, table_name)
            
            # Bulk insert to PostgreSQL
            await self._bulk_insert_rows(target_adapter, table_name, transformed_rows)
```

### **Vector Database Migration**

```python
class VectorMigrationManager:
    """Migrate between ChromaDB deployments"""
    
    async def migrate_local_to_http_chromadb(self, local_path: str, http_config: Dict):
        """Migrate from local ChromaDB to HTTP ChromaDB"""
        
        # 1. Initialize both clients
        local_client = LocalChromaDBManager(local_path)
        http_client = HTTPChromaDBManager(http_config)
        
        await local_client.initialize()
        await http_client.initialize()
        
        # 2. Migrate each collection
        collections = ['user_memories', 'global_facts', 'emotional_contexts']
        
        for collection_name in collections:
            await self._migrate_collection(local_client, http_client, collection_name)
        
        return True
    
    async def _migrate_collection(self, source_client, target_client, collection_name: str):
        """Migrate a specific ChromaDB collection"""
        
        # Export from source
        documents = await source_client.export_collection(collection_name)
        
        # Ensure target collection exists
        await target_client.ensure_collection(collection_name)
        
        # Import to target
        for doc in documents:
            await target_client.add_document(
                collection_name=collection_name,
                document_id=doc.id,
                content=doc.content,
                embedding=doc.embedding,
                metadata=doc.metadata
            )
```

### **Cache Migration**

```python
class CacheMigrationManager:
    """Migrate between cache backends"""
    
    async def migrate_memory_to_redis_cache(self, memory_cache: HybridConversationCache, 
                                          redis_cache: RedisConversationCache):
        """Migrate from in-memory to Redis cache"""
        
        # Get all cached channels from memory cache
        cached_channels = memory_cache.get_cached_channels()
        
        for channel_id in cached_channels:
            # Export from memory cache
            messages = await memory_cache.get_conversation_context(channel_id, limit=100)
            
            # Import to Redis cache
            for message in messages:
                universal_message = UniversalMessage.from_cache_dict(message)
                await redis_cache.add_message(channel_id, universal_message)
        
        return True
```

---

## 📋 Schema Verification and Validation

### **Cross-Backend Validation**

```python
class SchemaValidationManager:
    """Validate schema consistency across backends"""
    
    async def validate_database_schema_consistency(self, sqlite_adapter, postgres_adapter):
        """Ensure SQLite and PostgreSQL schemas are logically equivalent"""
        
        # Get table structures from both databases
        sqlite_schema = await self._get_table_structures(sqlite_adapter)
        postgres_schema = await self._get_table_structures(postgres_adapter)
        
        # Validate logical equivalence
        for table_name in sqlite_schema:
            if table_name not in postgres_schema:
                raise SchemaInconsistencyError(f"Table {table_name} missing in PostgreSQL")
            
            await self._validate_table_compatibility(
                sqlite_schema[table_name], 
                postgres_schema[table_name],
                table_name
            )
        
        return True
    
    async def validate_vector_schema_consistency(self, local_chromadb, http_chromadb):
        """Ensure ChromaDB collections are consistent"""
        
        expected_collections = ['user_memories', 'global_facts', 'emotional_contexts']
        
        for collection_name in expected_collections:
            local_collection = await local_chromadb.get_collection(collection_name)
            http_collection = await http_chromadb.get_collection(collection_name)
            
            # Validate metadata schemas match
            await self._validate_collection_schemas(local_collection, http_collection)
        
        return True
```

### **Automated Schema Testing**

```python
# tests/test_schema_consistency.py
class TestSchemaConsistency:
    """Automated tests for schema consistency"""
    
    @pytest.mark.asyncio
    async def test_sqlite_postgres_schema_compatibility(self):
        """Test SQLite to PostgreSQL schema translation"""
        
        sqlite_schema = WhisperEngineSchema.get_core_schema()
        postgres_schema = WhisperEngineSchema.get_postgresql_schema()
        
        # Verify all tables exist in both schemas
        assert set(sqlite_schema.keys()) == set(postgres_schema.keys())
        
        # Verify key transformations are correct
        for table_name in sqlite_schema:
            await self._verify_table_translation(
                sqlite_schema[table_name], 
                postgres_schema[table_name],
                table_name
            )
    
    @pytest.mark.asyncio
    async def test_vector_collection_schema_consistency(self):
        """Test ChromaDB collection schemas across deployments"""
        
        # Test with both local and HTTP ChromaDB
        local_manager = LocalChromaDBManager(test_config)
        http_manager = HTTPChromaDBManager(test_config)
        
        await local_manager.initialize()
        await http_manager.initialize()
        
        # Verify same collections can be created with same schemas
        for collection_name, schema in VECTOR_COLLECTIONS.items():
            local_collection = await local_manager.create_collection(collection_name, schema)
            http_collection = await http_manager.create_collection(collection_name, schema)
            
            assert local_collection.metadata == http_collection.metadata
    
    @pytest.mark.asyncio
    async def test_cache_serialization_consistency(self):
        """Test message serialization across cache backends"""
        
        # Create test message
        test_message = UniversalMessage(
            message_id="12345",
            user_id="67890",
            content="Test message",
            timestamp=datetime.now(),
            channel_id="channel_123"
        )
        
        # Test memory cache
        memory_cache = HybridConversationCache()
        await memory_cache.add_message("test_channel", test_message)
        memory_retrieved = await memory_cache.get_conversation_context("test_channel", 1)
        
        # Test Redis cache
        redis_cache = RedisConversationCache()
        await redis_cache.initialize()
        await redis_cache.add_message("test_channel", test_message)
        redis_retrieved = await redis_cache.get_conversation_context("test_channel", 1)
        
        # Verify identical serialization
        assert memory_retrieved[0]['content'] == redis_retrieved[0]['content']
        assert memory_retrieved[0]['user_id'] == redis_retrieved[0]['user_id']
```

---

## 🔧 Developer Guidelines

### **Adding New Schema Elements**

When adding new tables or collections:

1. **Define in Core Schema**:
   ```python
   # Add to WhisperEngineSchema.get_core_schema()
   'new_table': '''
       CREATE TABLE IF NOT EXISTS new_table (
           id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Will auto-translate to SERIAL
           user_id TEXT NOT NULL,
           new_field TEXT NOT NULL,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           FOREIGN KEY (user_id) REFERENCES users (user_id)
       )
   '''
   ```

2. **Update PostgreSQL Translation**:
   ```python
   # Add to WhisperEngineSchema.get_postgresql_schema()
   schema['new_table'] = schema['new_table'].replace(
       'id INTEGER PRIMARY KEY AUTOINCREMENT',
       'id SERIAL PRIMARY KEY'
   ).replace(
       'FOREIGN KEY (user_id) REFERENCES users (user_id)',
       'FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE'
   )
   ```

3. **Add Migration Support**:
   ```python
   # Update migration table lists
   tables = ['users', 'conversations', 'memory_entries', 'facts', 
            'emotions', 'relationships', 'system_settings', 
            'performance_metrics', 'new_table']  # Add new table
   ```

4. **Create Schema Tests**:
   ```python
   async def test_new_table_consistency(self):
       """Test new table across backends"""
       # Test SQLite creation
       # Test PostgreSQL creation
       # Test data insertion/retrieval
       # Test migration compatibility
   ```

### **Vector Collection Guidelines**

When adding new ChromaDB collections:

1. **Define Collection Schema**:
   ```python
   VECTOR_COLLECTIONS['new_collection'] = {
       'description': 'Purpose and content description',
       'embedding_dimension': 384,  # Must match embedding model
       'distance_metric': 'cosine',
       'metadata_schema': {
           'required_field': 'string',
           'optional_field': 'float',
           'timestamp': 'datetime'
       }
   }
   ```

2. **Update Collection Lists**:
   ```python
   # Update in migration and validation code
   collections = ['user_memories', 'global_facts', 'emotional_contexts', 'new_collection']
   ```

3. **Test Across Backends**:
   ```python
   # Ensure collection works with both local and HTTP ChromaDB
   ```

---

## ✅ Verification Checklist

**Before deploying schema changes:**

- [ ] **Core schema updated** in `WhisperEngineSchema.get_core_schema()`
- [ ] **PostgreSQL translation added** in `WhisperEngineSchema.get_postgresql_schema()`
- [ ] **Migration support added** to table/collection lists
- [ ] **Schema tests created** for new elements
- [ ] **Documentation updated** in this file
- [ ] **Backup compatibility verified** for new schema elements
- [ ] **Cross-backend validation tests pass**
- [ ] **Vector collection schemas defined** (if applicable)
- [ ] **Cache key patterns documented** (if applicable)
- [ ] **Neo4j relationships defined** (if applicable)

This schema consistency ensures that users can seamlessly upgrade from desktop SQLite installations to full Docker/Kubernetes deployments without data loss or compatibility issues.

---

*This documentation ensures WhisperEngine maintains perfect schema consistency across all deployment modes, enabling seamless upgrade paths from desktop to self-hosted to cloud deployments.*