import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import json
import logging
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Environment variables are loaded by main.py using env_manager
from src.utils.exceptions import MemoryError, MemoryStorageError, MemoryRetrievalError, ValidationError
from src.utils.fact_extractor import FactExtractor, GlobalFactExtractor
from src.memory.chromadb_manager_simple import ChromaDBManagerSimple as ChromaDBManager
from src.utils.emotion_manager import EmotionManager, UserProfile, EmotionProfile
from src.utils.embedding_manager import ExternalEmbeddingManager

# Import graph memory manager for hybrid storage
try:
    from src.memory.graph_memory_manager import get_graph_memory_manager
    GRAPH_MEMORY_AVAILABLE = True
except ImportError:
    GRAPH_MEMORY_AVAILABLE = False
    logger.warning("Graph memory manager not available - Neo4j features disabled")

logger = logging.getLogger(__name__)

class UserMemoryManager:
    def __init__(self, persist_directory: str = None, enable_auto_facts: bool = None, enable_global_facts: bool = None, enable_emotions: bool = None, llm_client=None):
        """Initialize ChromaDB client and create collections for user memories and global facts"""
        # Load configuration from environment variables with reasonable defaults
        if persist_directory is None:
            persist_directory = os.getenv("CHROMADB_PATH", "./chromadb_data")
        if enable_auto_facts is None:
            enable_auto_facts = True  # Always enabled in unified AI system
        if enable_global_facts is None:
            enable_global_facts = True  # Always enabled for better memory
        if enable_emotions is None:
            enable_emotions = True  # Always enabled for emotional intelligence
        
        try:
            # Use environment variable for telemetry setting
            telemetry_enabled = os.getenv("ANONYMIZED_TELEMETRY", "false").lower() == "true"
            settings = Settings(anonymized_telemetry=telemetry_enabled)
            
            # Check if we should use HTTP client or local file persistence
            use_chromadb_http = os.getenv("USE_CHROMADB_HTTP", "true").lower() == "true"
            
            if use_chromadb_http:
                # Use HTTP client for containerized ChromaDB service
                chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
                chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
                try:
                    self.client = chromadb.HttpClient(
                        host=chromadb_host,
                        port=chromadb_port,
                        settings=settings
                    )
                    logger.info(f"Using ChromaDB HTTP client: {chromadb_host}:{chromadb_port}")
                except Exception as e:
                    # Clean error message for ChromaDB connection failures
                    if "Could not connect to a Chroma server" in str(e) or "nodename nor servname provided" in str(e):
                        error_msg = f"ChromaDB server is not available at {chromadb_host}:{chromadb_port}"
                        logger.error(error_msg)
                        logger.info("To fix: Start ChromaDB server or set USE_CHROMADB_HTTP=false for local storage")
                        raise MemoryError(error_msg)
                    else:
                        logger.error(f"ChromaDB HTTP client initialization failed: {e}")
                        raise MemoryError(f"Failed to initialize ChromaDB HTTP client: {e}")
            else:
                # Use local file persistence for desktop mode
                chromadb_path = os.path.expanduser(os.getenv("CHROMADB_PATH", persist_directory))
                try:
                    self.client = chromadb.PersistentClient(
                        path=chromadb_path,
                        settings=settings
                    )
                    logger.info(f"Using ChromaDB local file persistence: {chromadb_path}")
                except Exception as e:
                    error_msg = f"Failed to initialize local ChromaDB storage at {chromadb_path}"
                    logger.error(f"{error_msg}: {e}")
                    raise MemoryError(error_msg)
            
            # Store the LLM client for emotion analysis
            self.llm_client = llm_client
            
            # Initialize external embedding manager for consistent embeddings
            self.external_embedding_manager = ExternalEmbeddingManager()
            
            # Configure embedding function based on external embedding setting
            # Check for both new LLM_EMBEDDING_* pattern and legacy variables for backward compatibility
            self.use_external_embeddings = (
                os.getenv("LLM_EMBEDDING_API_URL") is not None or
                os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true"
            )
            
            if self.use_external_embeddings:
                # Use None for embedding function - we'll handle embeddings manually
                self.embedding_function = None
                # Import external embedding manager
                try:
                    from src.memory.chromadb_external_embeddings import (
                        add_documents_with_embeddings, 
                        query_with_embeddings
                    )
                    self.add_documents_with_embeddings = add_documents_with_embeddings
                    self.query_with_embeddings = query_with_embeddings
                    logger.info("External embeddings configured")
                except ImportError:
                    logger.warning("External embeddings module not available")
            else:
                # Use local embedding model (check for bundled models first)
                use_local_models = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
                local_models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
                embedding_model = os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-Mpnet-BASE-v2")
                
                if use_local_models and os.path.exists(os.path.join(local_models_dir, embedding_model)):
                    # Use bundled local model
                    model_path = os.path.join(local_models_dir, embedding_model)
                    logger.info(f"Using bundled local embedding model: {model_path}")
                    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=model_path
                    )
                else:
                    # Use online model (will download if not cached)
                    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=embedding_model
                    )
                    logger.info(f"Local embedding model: {embedding_model}")
                
                self.add_documents_with_embeddings = None
                self.query_with_embeddings = None
            
            # Create or get collection with appropriate embedding function
            collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "user_memories")
            if self.use_external_embeddings:
                # Create collection with 768-dimensional metadata for external embeddings
                embedding_model = os.getenv("LLM_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")
                if "nomic" in embedding_model.lower() or "768" in embedding_model:
                    embedding_dim = 768
                else:
                    embedding_dim = 384  # Default fallback
                
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"embedding_dimension": embedding_dim}
                )
            else:
                # Create collection with local embedding function
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function  # type: ignore
                )
            
            # Create or get collection for global facts
            global_collection_name = os.getenv("CHROMADB_GLOBAL_COLLECTION_NAME", "global_facts")
            if self.use_external_embeddings:
                # Create collection with 768-dimensional metadata for external embeddings
                self.global_collection = self.client.get_or_create_collection(
                    name=global_collection_name,
                    metadata={"embedding_dimension": embedding_dim}
                )
            else:
                # Create collection with local embedding function
                self.global_collection = self.client.get_or_create_collection(
                    name=global_collection_name,
                    embedding_function=self.embedding_function  # type: ignore
                )
            
            # Initialize fact extractors if enabled
            self.enable_auto_facts = enable_auto_facts
            self.enable_global_facts = enable_global_facts
            if enable_auto_facts:
                self.fact_extractor = FactExtractor(llm_client=self.llm_client)
                logger.info("Automatic user fact extraction enabled with LLM support")
            else:
                self.fact_extractor = None
                logger.info("Automatic user fact extraction disabled")
            
            if enable_global_facts:
                self.global_fact_extractor = GlobalFactExtractor(llm_client=self.llm_client)
                logger.info("Automatic global fact extraction enabled with LLM support")
            else:
                self.global_fact_extractor = None
                logger.info("Automatic global fact extraction disabled")
            
            # Initialize emotion manager if enabled
            self.enable_emotions = enable_emotions
            if enable_emotions:
                self.emotion_manager = EmotionManager(llm_client=self.llm_client, memory_manager=self)
                logger.info("Emotion and relationship management enabled with LLM-based sentiment analysis")
            else:
                self.emotion_manager = None
                logger.info("Emotion and relationship management disabled")
            
            # Initialize graph memory manager for hybrid storage if available
            self.graph_memory_manager = None
            if GRAPH_MEMORY_AVAILABLE and enable_global_facts:
                try:
                    # Will be initialized lazily when first used
                    self._graph_memory_manager_initialized = False
                    logger.info("Graph memory manager support enabled")
                except Exception as e:
                    logger.warning(f"Failed to initialize graph memory manager: {e}")
            else:
                logger.info("Graph memory manager disabled (Neo4j not available or global facts disabled)")
            
            # Test connection
            try:
                self.client.heartbeat()
                logger.info("UserMemoryManager initialized with ChromaDB (user and global collections)")
            except Exception as e:
                # Clean error message for heartbeat failures
                if "Could not connect to a Chroma server" in str(e) or "nodename nor servname provided" in str(e):
                    error_msg = "ChromaDB server connection test failed"
                    logger.error(error_msg)
                    logger.info("ChromaDB server appears to be unavailable")
                    raise MemoryError(error_msg)
                else:
                    logger.error(f"ChromaDB heartbeat failed: {e}")
                    raise MemoryError(f"ChromaDB connection test failed: {e}")
            
        except MemoryError:
            # Re-raise MemoryError as-is (already properly formatted)
            raise
        except Exception as e:
            # Handle any other unexpected errors
            logger.error(f"Unexpected error during memory system initialization: {e}")
            raise MemoryError(f"Memory system initialization failed: {e}")

    def _validate_input(self, text: str, max_length: int = 10000) -> str:
        """Validate and sanitize input text"""
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty")
        
        text = text.strip()
        if len(text) > max_length:
            logger.warning(f"Text truncated from {len(text)} to {max_length} chars")
            text = text[:max_length]
        
        return text

    def _validate_user_id(self, user_id: str) -> str:
        """Validate user ID format"""
        if not user_id or not user_id.strip():
            raise ValidationError("User ID cannot be empty")
        
        user_id = user_id.strip()
        
        # Allow test user IDs (for testing), Discord user IDs (numeric), UUIDs, or desktop user
        if (user_id.startswith("test_") or 
            user_id.isdigit() or 
            user_id == "desktop_admin" or
            self._is_valid_uuid(user_id)):
            return user_id
        else:
            raise ValidationError(f"Invalid user ID format: {user_id}")

    def _is_valid_uuid(self, user_id: str) -> bool:
        """Check if user_id is a valid UUID format"""
        import re
        # UUID pattern: 8-4-4-4-12 hexadecimal digits
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, user_id.lower()))

    def _is_synthetic_message(self, message: str) -> bool:
        """Detect if a message is synthetic/system-generated"""
        # Check for synthetic patterns to avoid storing system-generated content
        synthetic_patterns = [
            "[Context from previous conversations]",
            "Previous relevant context:",
            "[Image:",
            "[Images:",
            "[User attached an image:",
            "[User attached a file:",
            "[User attached"
        ]
        
        # Check if message starts with any synthetic pattern
        synthetic_match = any(message.startswith(pattern) for pattern in synthetic_patterns)
        
        if synthetic_match:
            logger.debug(f"Message detected as synthetic: {message[:100]}...")
        
        return synthetic_match

    def store_conversation(self, user_id: str, user_message: str, bot_response: str, channel_id: str = None, pre_analyzed_emotion_data: dict = None, metadata: dict = None):
        """Store a conversation turn in the vector database and extract facts if enabled"""
        try:
            # Validate inputs
            user_id = self._validate_user_id(user_id)
            user_message = self._validate_input(user_message)
            bot_response = self._validate_input(bot_response)
            
            # Safety check: Don't store synthetic context messages
            if self._is_synthetic_message(user_message):
                logger.warning("Attempted to store synthetic message - skipping storage")
                return
            
            # Create a unique document ID
            timestamp = datetime.now().isoformat()
            doc_id = f"{user_id}_{timestamp}_{hash(user_message) % 10000}"
            
            # Create the document content
            conversation_text = f"User: {user_message}\nAssistant: {bot_response}"
            
            # Create metadata
            base_metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "channel_id": channel_id or "dm",
                "user_message": user_message,
                "bot_response": bot_response
            }
            
            # Merge with any additional metadata passed in
            if metadata:
                base_metadata.update(metadata)
            metadata = base_metadata
            
            # Filter out None values from metadata to prevent ChromaDB errors
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            # Process emotions and relationships if enabled
            emotion_data = None
            if self.enable_emotions and self.emotion_manager:
                try:
                    # Use pre-analyzed emotion data if provided, otherwise analyze now
                    if pre_analyzed_emotion_data:
                        emotion_data = pre_analyzed_emotion_data
                        logger.debug(f"Using pre-analyzed emotion data for user {user_id}")
                    else:
                        user_profile, emotion_profile = self.emotion_manager.process_interaction(user_id, user_message)
                        emotion_data = {
                            "detected_emotion": emotion_profile.detected_emotion.value,
                            "confidence": emotion_profile.confidence,
                            "intensity": emotion_profile.intensity,
                            "relationship_level": user_profile.relationship_level.value,
                            "interaction_count": user_profile.interaction_count
                        }
                        logger.debug(f"Analyzed emotion during storage for user {user_id}: {emotion_profile.detected_emotion.value}")
                    
                    # Add emotion data to metadata (filter out None values)
                    emotion_data_filtered = {k: v for k, v in emotion_data.items() if v is not None}
                    metadata.update(emotion_data_filtered)
                    
                    # Log emotion processing (works for both pre-analyzed and fresh analysis)
                    if emotion_data:
                        logger.debug(f"Emotion processed for user {user_id}: {emotion_data.get('detected_emotion', 'unknown')} "
                                   f"(confidence: {emotion_data.get('confidence', 0):.2f})")
                except Exception as e:
                    logger.warning(f"Error processing emotions for user {user_id}: {e}")
            
            # Store in ChromaDB using appropriate method
            if self.use_external_embeddings and self.add_documents_with_embeddings:
                # Use external embeddings
                import asyncio
                from src.memory.chromadb_external_embeddings import run_async_method
                success = run_async_method(
                    self.add_documents_with_embeddings,
                    self.collection,
                    [conversation_text],
                    [metadata],
                    [doc_id]
                )
                if not success:
                    raise MemoryStorageError("Failed to store conversation with external embeddings")
            else:
                # Use ChromaDB's built-in embeddings
                self.collection.add(
                    documents=[conversation_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
            logger.debug(f"Successfully stored conversation for user {user_id}: {user_message[:50]}...")
            logger.debug(f"Conversation storage - User message length: {len(user_message)}, Response length: {len(bot_response)}")
            
            # Automatic fact extraction if enabled
            if self.enable_auto_facts and self.fact_extractor:
                self._extract_and_store_facts(user_id, user_message, bot_response, timestamp)
            
            # Automatic global fact extraction if enabled
            if self.enable_global_facts and self.global_fact_extractor:
                self._extract_and_store_global_facts(user_message, bot_response, timestamp)
            
            # Return success indicator
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            raise MemoryStorageError(f"Failed to store conversation: {e}")

    def _extract_and_store_facts(self, user_id: str, user_message: str, bot_response: str, timestamp: str):
        """Extract and store facts from user message"""
        try:
            # Extract potential facts
            extracted_facts = self.fact_extractor.extract_facts_from_message(user_message, bot_response)
            
            facts_stored = 0
            for fact_data in extracted_facts:
                # Check if we already have a similar fact
                if not self._fact_already_exists(user_id, fact_data["fact"]):
                    # Store the extracted fact
                    self._store_extracted_fact(
                        user_id=user_id,
                        fact=fact_data["fact"],
                        category=fact_data["category"],
                        confidence=fact_data["confidence"],
                        source=fact_data["source"],
                        original_message=fact_data["original_message"],
                        timestamp=timestamp
                    )
                    facts_stored += 1
                    logger.info(f"Auto-extracted fact for user {user_id}: {fact_data['fact']}")
            
            if facts_stored > 0:
                logger.debug(f"Automatically stored {facts_stored} facts for user {user_id}")
                
        except Exception as e:
            # Don't fail the conversation storage if fact extraction fails
            logger.warning(f"Error during automatic fact extraction: {e}")

    def _fact_already_exists(self, user_id: str, new_fact: str) -> bool:
        """Check if a similar fact already exists for the user"""
        try:
            # Get existing facts for the user
            results = self.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": "user_fact"}]},
                limit=100
            )
            
            if not results['documents']:
                return False
            
            # Simple similarity check
            new_fact_words = set(new_fact.lower().split())
            
            for doc, metadata in zip(results['documents'], results['metadatas']):
                existing_fact = metadata.get('fact', doc)
                existing_words = set(existing_fact.lower().split())
                
                # Calculate overlap
                if len(new_fact_words) > 0 and len(existing_words) > 0:
                    overlap = len(new_fact_words.intersection(existing_words))
                    similarity = overlap / max(len(new_fact_words), len(existing_words))
                    
                    if similarity > 0.7:  # 70% similarity threshold
                        logger.debug(f"Similar fact already exists: '{existing_fact}' vs '{new_fact}'")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for existing facts: {e}")
            return False  # Assume no duplicates if check fails

    def _store_extracted_fact(self, user_id: str, fact: str, category: str, confidence: float, 
                             source: str, original_message: str, timestamp: str):
        """Store an automatically extracted fact"""
        try:
            doc_id = f"{user_id}_auto_fact_{timestamp}_{hash(fact) % 10000}"
            
            # Create document content
            fact_text = f"Auto-extracted fact: {fact}"
            
            metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "user_fact",
                "fact": fact,
                "category": category,
                "confidence": confidence,
                "source": source,
                "extraction_method": "automatic",
                "context": f"Extracted from: {original_message}"
            }
            
            # Store using appropriate method
            if self.use_external_embeddings and self.add_documents_with_embeddings:
                # Use external embeddings
                from src.memory.chromadb_external_embeddings import run_async_method
                success = run_async_method(
                    self.add_documents_with_embeddings,
                    self.collection,
                    [fact_text],
                    [metadata],
                    [doc_id]
                )
                if not success:
                    raise MemoryStorageError("Failed to store extracted fact with external embeddings")
            else:
                # Use ChromaDB's built-in embeddings
                self.collection.add(
                    documents=[fact_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
        except Exception as e:
            logger.error(f"Error storing extracted fact: {e}")
            raise MemoryStorageError(f"Failed to store extracted fact: {e}")

    def _extract_and_store_global_facts(self, user_message: str, bot_response: str, timestamp: str):
        """Extract and store global facts from conversation"""
        try:
            # Extract potential global facts
            extracted_facts = self.global_fact_extractor.extract_global_facts_from_message(user_message, bot_response)
            
            facts_stored = 0
            for fact_data in extracted_facts:
                # Check if we already have a similar global fact
                if not self._global_fact_already_exists(fact_data["fact"]):
                    # Store the extracted global fact
                    self._store_extracted_global_fact(
                        fact=fact_data["fact"],
                        category=fact_data["category"],
                        confidence=fact_data["confidence"],
                        source=fact_data["source"],
                        original_message=fact_data["original_message"],
                        timestamp=timestamp
                    )
                    facts_stored += 1
                    logger.info(f"Auto-extracted global fact: {fact_data['fact']}")
            
            if facts_stored > 0:
                logger.debug(f"Automatically stored {facts_stored} global facts")
                
        except Exception as e:
            # Don't fail the conversation storage if global fact extraction fails
            logger.warning(f"Error during automatic global fact extraction: {e}")

    def _global_fact_already_exists(self, new_fact: str) -> bool:
        """Check if a similar global fact already exists"""
        try:
            # Get existing global facts
            results = self.global_collection.get(
                where={"type": "global_fact"},
                limit=100
            )
            
            if not results['documents']:
                return False
            
            # Simple similarity check
            new_fact_words = set(new_fact.lower().split())
            
            for doc, metadata in zip(results['documents'], results['metadatas']):
                existing_fact = metadata.get('fact', doc)
                existing_words = set(existing_fact.lower().split())
                
                # Calculate overlap
                if len(new_fact_words) > 0 and len(existing_words) > 0:
                    overlap = len(new_fact_words.intersection(existing_words))
                    similarity = overlap / max(len(new_fact_words), len(existing_words))
                    
                    if similarity > 0.75:  # 75% similarity threshold for global facts
                        logger.debug(f"Similar global fact already exists: '{existing_fact}' vs '{new_fact}'")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for existing global facts: {e}")
            return False  # Assume no duplicates if check fails

    def _store_extracted_global_fact(self, fact: str, category: str, confidence: float, 
                                   source: str, original_message: str, timestamp: str):
        """Store an automatically extracted global fact"""
        try:
            doc_id = f"global_auto_fact_{timestamp}_{hash(fact) % 10000}"
            
            # Create document content
            fact_text = f"Global fact: {fact}"
            
            metadata = {
                "timestamp": timestamp,
                "type": "global_fact",
                "fact": fact,
                "category": category,
                "confidence": confidence,
                "source": source,
                "extraction_method": "automatic",
                "context": f"Extracted from: {original_message}"
            }
            
            # Store using appropriate method
            if self.use_external_embeddings and self.add_documents_with_embeddings:
                # Use external embeddings
                from src.memory.chromadb_external_embeddings import run_async_method
                success = run_async_method(
                    self.add_documents_with_embeddings,
                    self.global_collection,
                    [fact_text],
                    [metadata],
                    [doc_id]
                )
                if not success:
                    raise MemoryStorageError("Failed to store extracted global fact with external embeddings")
            else:
                # Use ChromaDB's built-in embeddings
                self.global_collection.add(
                    documents=[fact_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
        except Exception as e:
            logger.error(f"Error storing extracted global fact: {e}")
            raise MemoryStorageError(f"Failed to store extracted global fact: {e}")

    def store_global_fact(self, fact: str, context: str = "", added_by: str = "admin"):
        """Store a global fact manually (admin only) with hybrid ChromaDB + Neo4j storage"""
        try:
            # Validate inputs
            fact = self._validate_input(fact)
            if context:
                context = self._validate_input(context)
            
            # Check if we already have a similar global fact to avoid duplicates
            if self._global_fact_already_exists(fact):
                logger.debug(f"Similar global fact already exists, skipping: {fact[:50]}...")
                return
            
            timestamp = datetime.now().isoformat()
            doc_id = f"global_fact_{timestamp}_{hash(fact) % 10000}"
            
            # Create document content
            fact_text = f"Global fact: {fact}"
            if context:
                fact_text += f"\nContext: {context}"
            
            metadata = {
                "timestamp": timestamp,
                "type": "global_fact",
                "fact": fact,
                "context": context,
                "added_by": added_by,
                "extraction_method": "manual"
            }
            
            # Store in ChromaDB first
            if self.use_external_embeddings and self.add_documents_with_embeddings:
                # Use external embeddings for storage
                import asyncio
                from src.memory.chromadb_external_embeddings import run_async_method
                success = run_async_method(
                    self.add_documents_with_embeddings,
                    self.global_collection,
                    [fact_text],
                    [metadata],
                    [doc_id]
                )
                if not success:
                    raise MemoryStorageError("Failed to store global fact with external embeddings")
            else:
                # Use ChromaDB's built-in embeddings
                self.global_collection.add(
                    documents=[fact_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
            # Store in Neo4j graph database if available
            if GRAPH_MEMORY_AVAILABLE and self.enable_global_facts:
                try:
                    # Ensure graph memory manager is initialized
                    if not getattr(self, '_graph_memory_manager_initialized', False):
                        # Use asyncio to run the async function properly
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # We're in an async context, schedule the coroutine
                            task = asyncio.create_task(get_graph_memory_manager())
                            self.graph_memory_manager = None  # Will be set later
                            logger.warning("Graph memory manager initialization deferred - async context detected")
                            self._graph_memory_manager_initialized = False
                        else:
                            self.graph_memory_manager = asyncio.run(get_graph_memory_manager())
                            self._graph_memory_manager_initialized = True
                    
                    # Determine knowledge domain from context or content
                    knowledge_domain = self._determine_knowledge_domain(fact, context)
                    
                    # Store in graph database
                    if self.graph_memory_manager and self._graph_memory_manager_initialized:
                        # Similar handling for the hybrid storage
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            logger.warning("Skipping Neo4j storage - async context detected, use async wrapper instead")
                        else:
                            fact_id = asyncio.run(self.graph_memory_manager.store_global_fact_hybrid(
                                chromadb_id=doc_id,
                                fact_content=fact,
                                knowledge_domain=knowledge_domain,
                                confidence_score=0.8,  # Manual facts have high confidence
                                source="admin",
                                fact_type="declarative",
                                tags=self._extract_tags_from_fact(fact)
                            ))
                            logger.debug(f"Stored global fact in both ChromaDB and Neo4j: {fact_id}")
                    else:
                        logger.warning("Graph memory manager not available for global fact storage")
                except Exception as e:
                    logger.warning(f"Failed to store global fact in Neo4j, continuing with ChromaDB only: {e}")
            
            logger.debug(f"Stored global fact: {fact[:50]}...")
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error storing global fact: {e}")
            raise MemoryStorageError(f"Failed to store global fact: {e}")
    
    def _determine_knowledge_domain(self, fact: str, context: str = "") -> str:
        """Determine the knowledge domain for a fact based on content analysis"""
        fact_lower = fact.lower()
        context_lower = context.lower()
        combined_text = f"{fact_lower} {context_lower}"
        
        # Simple keyword-based classification
        domain_keywords = {
            "science": ["physics", "chemistry", "biology", "research", "experiment", "theory", "hypothesis"],
            "technology": ["computer", "software", "programming", "ai", "artificial intelligence", "machine learning", "algorithm"],
            "history": ["war", "battle", "ancient", "century", "historical", "empire", "revolution", "civilization"],
            "mathematics": ["equation", "formula", "theorem", "proof", "calculate", "mathematical", "geometry", "algebra"],
            "psychology": ["behavior", "mind", "cognitive", "emotion", "psychological", "mental", "brain"],
            "philosophy": ["ethics", "morality", "existence", "consciousness", "philosophical", "logic", "reasoning"],
            "arts": ["painting", "music", "literature", "artist", "creative", "aesthetic", "cultural"],
            "geography": ["country", "continent", "ocean", "mountain", "climate", "geographic", "location"],
            "economics": ["money", "economy", "finance", "market", "trade", "economic", "business"],
            "politics": ["government", "political", "democracy", "election", "policy", "law", "legal"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return domain
        
        return "general"  # Default domain
    
    def _extract_tags_from_fact(self, fact: str) -> list:
        """Extract simple tags from a fact for categorization"""
        # Simple tag extraction based on keywords
        fact_lower = fact.lower()
        tags = []
        
        tag_patterns = {
            "definition": ["is", "are", "defined as", "means", "refers to"],
            "historical": ["in", "during", "year", "century", "bc", "ad"],
            "scientific": ["discovered", "invented", "theory", "law", "principle"],
            "numerical": ["number", "amount", "quantity", "percent", "ratio"],
            "geographical": ["located", "situated", "found in", "capital", "country"]
        }
        
        for tag, patterns in tag_patterns.items():
            if any(pattern in fact_lower for pattern in patterns):
                tags.append(tag)
        
        return tags if tags else ["general"]
    
    def get_related_global_facts(self, query: str, limit: int = 5, include_graph_relationships: bool = True) -> List[Dict]:
        """Retrieve related global facts using both semantic search and graph relationships"""
        try:
            # First get semantically similar facts from ChromaDB
            semantic_facts = self.retrieve_relevant_global_facts(query, limit)
            
            # If graph memory manager is available, also get graph-related facts
            if (GRAPH_MEMORY_AVAILABLE and include_graph_relationships and 
                getattr(self, '_graph_memory_manager_initialized', False) and 
                self.graph_memory_manager):
                
                try:
                    # For each semantic fact, get graph relationships
                    enhanced_facts = []
                    for fact in semantic_facts:
                        fact_dict = dict(fact)
                        
                        # Try to get the ChromaDB ID from the fact
                        if 'id' in fact_dict:
                            chromadb_id = fact_dict['id']
                            
                            # Get related facts through graph relationships
                            related_facts = asyncio.run(
                                self.graph_memory_manager.get_related_facts(
                                    chromadb_id=chromadb_id,
                                    max_depth=2
                                )
                            )
                            
                            if related_facts:
                                fact_dict['graph_relationships'] = related_facts
                                fact_dict['has_relationships'] = True
                            else:
                                fact_dict['has_relationships'] = False
                        
                        enhanced_facts.append(fact_dict)
                    
                    return enhanced_facts
                    
                except Exception as e:
                    logger.warning(f"Failed to enhance facts with graph relationships: {e}")
                    # Return semantic facts only
                    return semantic_facts
            
            return semantic_facts
            
        except Exception as e:
            logger.error(f"Error retrieving related global facts: {e}")
            return []
    
    def create_fact_relationship(self, fact_1_query: str, fact_2_query: str, 
                               relationship_type: str = "RELATES_TO", 
                               strength: float = 1.0) -> bool:
        """Create a relationship between two global facts identified by their content"""
        if not (GRAPH_MEMORY_AVAILABLE and getattr(self, '_graph_memory_manager_initialized', False)):
            logger.warning("Graph memory manager not available for relationship creation")
            return False
        
        try:
            # Find the facts by their content
            fact_1_results = self.retrieve_relevant_global_facts(fact_1_query, limit=1)
            fact_2_results = self.retrieve_relevant_global_facts(fact_2_query, limit=1)
            
            if not fact_1_results or not fact_2_results:
                logger.warning("Could not find one or both facts for relationship creation")
                return False
            
            fact_1_id = fact_1_results[0].get('id')
            fact_2_id = fact_2_results[0].get('id')
            
            if not fact_1_id or not fact_2_id:
                logger.warning("Could not get IDs for facts")
                return False
            
            # Create the relationship in the graph
            success = asyncio.run(
                self.graph_memory_manager.create_fact_relationship(
                    fact_id_1=fact_1_id,
                    fact_id_2=fact_2_id,
                    relationship_type=relationship_type,
                    strength=strength
                )
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating fact relationship: {e}")
            return False
    
    def get_knowledge_domain_facts(self, domain: str, limit: int = 20) -> List[Dict]:
        """Get all facts from a specific knowledge domain"""
        if not (GRAPH_MEMORY_AVAILABLE and getattr(self, '_graph_memory_manager_initialized', False)):
            logger.warning("Graph memory manager not available for domain queries")
            return []
        
        try:
            graph_facts = asyncio.run(
                self.graph_memory_manager.search_facts_by_domain(
                    knowledge_domain=domain,
                    include_subdomain=True,
                    limit=limit
                )
            )
            
            # Convert graph facts to the expected format
            domain_facts = []
            for graph_fact in graph_facts:
                fact_dict = {
                    'fact': graph_fact.get('fact_content', ''),
                    'domain': graph_fact.get('knowledge_domain', domain),
                    'confidence': graph_fact.get('confidence_score', 0.0),
                    'source': graph_fact.get('source', 'unknown'),
                    'type': graph_fact.get('fact_type', 'declarative'),
                    'verification_status': graph_fact.get('verification_status', 'unverified'),
                    'chromadb_id': graph_fact.get('chromadb_id', ''),
                    'graph_id': graph_fact.get('id', '')
                }
                domain_facts.append(fact_dict)
            
            return domain_facts
            
        except Exception as e:
            logger.error(f"Error retrieving domain facts: {e}")
            return []

    def retrieve_relevant_global_facts(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant global facts based on the current query"""
        try:
            # Validate inputs
            query = self._validate_input(query, max_length=1000)
            
            if limit <= 0 or limit > 20:  # Reasonable limits for global facts
                limit = 5
            
            # Query the global collection for relevant facts using external embeddings
            if self.external_embedding_manager.use_external:
                # Generate embeddings using external API
                try:
                    # Use sync wrapper to get embeddings
                    embeddings = self.external_embedding_manager.get_embeddings_sync([query])
                    
                    if embeddings:
                        results = self.global_collection.query(
                            query_embeddings=[embeddings[0]],
                            where={"type": "global_fact"},
                            n_results=limit
                        )
                    else:
                        # Fallback to query_texts if embeddings fail
                        results = self.global_collection.query(
                            query_texts=[query],
                            where={"type": "global_fact"},
                            n_results=limit
                        )
                except Exception as e:
                    logger.error(f"Failed to use external embeddings for global facts: {e}")
                    # Fallback to query_texts
                    results = self.global_collection.query(
                        query_texts=[query],
                        where={"type": "global_fact"},
                        n_results=limit
                    )
            else:
                # Use ChromaDB's internal embeddings
                results = self.global_collection.query(
                    query_texts=[query],
                    where={"type": "global_fact"},
                    n_results=limit
                )
            
            global_facts = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    fact_id = results['ids'][0][i] if results['ids'] else None
                    distance = results['distances'][0][i] if results['distances'] else None
                    
                    global_facts.append({
                        "id": fact_id,
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance if distance else 1.0
                    })
            
            logger.debug(f"Retrieved {len(global_facts)} relevant global facts")
            return global_facts
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving global facts: {e}")
            raise MemoryRetrievalError(f"Failed to retrieve global facts: {e}")

    def get_all_global_facts(self, limit: int = 50) -> List[Dict]:
        """Get all global facts for admin management"""
        try:
            results = self.global_collection.get(
                where={"type": "global_fact"},
                limit=limit
            )
            
            if not results['documents']:
                return []
            
            # Sort by timestamp (most recent first)
            facts = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                fact_id = results['ids'][i] if results['ids'] else None
                facts.append({
                    "id": fact_id,
                    "content": doc,
                    "metadata": metadata
                })
            
            facts.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
            return facts
            
        except Exception as e:
            logger.error(f"Error retrieving all global facts: {e}")
            return []

    def delete_global_fact(self, fact_id: str) -> bool:
        """Delete a specific global fact by its ID (admin only)"""
        try:
            self.global_collection.delete(ids=[fact_id])
            logger.info(f"Deleted global fact with ID: {fact_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting global fact {fact_id}: {e}")
            return False

    def store_user_fact(self, user_id: str, fact: str, context: str = ""):
        """Store a specific fact about the user"""
        try:
            # Validate inputs
            user_id = self._validate_user_id(user_id)
            fact = self._validate_input(fact)
            if context:
                context = self._validate_input(context)
            
            timestamp = datetime.now().isoformat()
            doc_id = f"{user_id}_fact_{timestamp}_{hash(fact) % 10000}"
            
            # Create document content
            fact_text = f"User fact: {fact}"
            if context:
                fact_text += f"\nContext: {context}"
            
            metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "user_fact",
                "fact": fact,
                "context": context
            }
            
            # Store in ChromaDB using appropriate method
            if self.use_external_embeddings and self.add_documents_with_embeddings:
                # Use external embeddings
                import asyncio
                from src.memory.chromadb_external_embeddings import run_async_method
                success = run_async_method(
                    self.add_documents_with_embeddings,
                    self.collection,
                    [fact_text],
                    [metadata],
                    [doc_id]
                )
                if not success:
                    raise MemoryStorageError("Failed to store user fact with external embeddings")
            else:
                # Use ChromaDB's built-in embeddings
                self.collection.add(
                    documents=[fact_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
            logger.debug(f"Stored user fact for {user_id}: {fact[:50]}...")
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error storing user fact: {e}")
            raise MemoryStorageError(f"Failed to store user fact: {e}")

    async def get_memories_by_user(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Retrieve all memories for a specific user"""
        try:
            # Validate inputs
            user_id = self._validate_user_id(user_id)
            
            if limit <= 0 or limit > 1000:  # Reasonable limits
                limit = 100
            
            # Get all memories for this user
            results = self.collection.get(
                where={"user_id": user_id},
                limit=limit
            )
            
            memories = []
            if results and 'ids' in results and results['ids']:
                for i in range(len(results['ids'])):
                    memory_id = results['ids'][i]
                    document = results['documents'][i] if 'documents' in results else ""
                    metadata = results['metadatas'][i] if 'metadatas' in results else {}
                    
                    memory = {
                        'id': memory_id,
                        'memory_id': memory_id,  # Alias for compatibility
                        'content': document,
                        'text': document,  # Alias for compatibility
                        'metadata': metadata,
                        'user_id': metadata.get('user_id', user_id),
                        'timestamp': metadata.get('timestamp', ''),
                        'channel_id': metadata.get('channel_id', ''),
                        'user_message': metadata.get('user_message', ''),
                        'bot_response': metadata.get('bot_response', ''),
                        'type': metadata.get('type', 'conversation')
                    }
                    memories.append(memory)
            
            logger.debug(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            raise MemoryRetrievalError(f"Failed to retrieve memories for user {user_id}: {e}")

    def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories for a user based on the current query, including global facts with priority"""
        try:
            # Validate inputs
            user_id = self._validate_user_id(user_id)
            query = self._validate_input(query, max_length=1000)  # Shorter limit for queries
            
            if limit <= 0 or limit > 50:  # Reasonable limits
                limit = 5
            
            # First, get relevant global facts (they take precedence)
            global_facts = self.retrieve_relevant_global_facts(query, limit=min(limit // 2, 5))
            
            # Then get user-specific memories, reducing limit by number of global facts found
            remaining_limit = max(1, limit - len(global_facts))
            
            # Query the user collection for relevant memories using external embeddings
            if self.external_embedding_manager.use_external:
                # Generate embeddings using external API
                try:
                    # Use sync wrapper to get embeddings
                    embeddings = self.external_embedding_manager.get_embeddings_sync([query])
                    
                    if embeddings:
                        results = self.collection.query(
                            query_embeddings=[embeddings[0]],
                            where={"user_id": user_id},
                            n_results=remaining_limit
                        )
                    else:
                        # Fallback to query_texts if embeddings fail
                        results = self.collection.query(
                            query_texts=[query],
                            where={"user_id": user_id},
                            n_results=remaining_limit
                        )
                except Exception as e:
                    logger.error(f"Failed to use external embeddings: {e}")
                    # Fallback to query_texts
                    results = self.collection.query(
                        query_texts=[query],
                        where={"user_id": user_id},
                        n_results=remaining_limit
                    )
            else:
                # Use ChromaDB's internal embeddings
                results = self.collection.query(
                    query_texts=[query],
                    where={"user_id": user_id},
                    n_results=remaining_limit
                )
            
            memories = []
            
            # Add global facts first (higher priority)
            for global_fact in global_facts:
                memories.append({
                    "id": global_fact["id"],
                    "content": global_fact["content"],
                    "metadata": {**global_fact["metadata"], "is_global": True},
                    "relevance_score": global_fact["relevance_score"] + 0.1  # Boost global fact scores
                })
            
            # Add user-specific memories
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    memory_id = results['ids'][0][i] if results['ids'] else None
                    distance = results['distances'][0][i] if results['distances'] else None
                    
                    memories.append({
                        "id": memory_id,
                        "content": doc,
                        "metadata": {**metadata, "is_global": False},
                        "relevance_score": 1 - distance if distance else 1.0
                    })
            
            # Sort by relevance score (highest first) to maintain global fact priority
            memories.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            logger.debug(f"Retrieved {len(memories)} relevant memories for user {user_id} (including {len(global_facts)} global facts)")
            return memories
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            raise MemoryRetrievalError(f"Failed to retrieve memories: {e}")

    def get_user_summary(self, user_id: str, limit: int = 20) -> str:
        """Get a summary of what we know about the user"""
        try:
            # Get recent facts and conversations
            results = self.collection.get(
                where={"user_id": user_id},
                limit=limit
            )
            
            if not results['documents']:
                return "No previous interactions found."
            
            # Sort by timestamp (most recent first)
            memories = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                memories.append((metadata.get('timestamp', ''), doc, metadata))
            
            memories.sort(key=lambda x: x[0], reverse=True)
            
            # Create summary
            summary_parts = []
            for _, doc, metadata in memories[:10]:  # Last 10 interactions
                if metadata.get('type') == 'user_fact':
                    summary_parts.append(f"• {metadata.get('fact', doc)}")
                else:
                    # Extract key info from conversations
                    if 'user_message' in metadata:
                        summary_parts.append(f"• Recently discussed: {metadata['user_message'][:100]}...")
            
            return "\n".join(summary_parts) if summary_parts else "No significant information stored."
            
        except Exception as e:
            logger.error(f"Error generating user summary: {e}")
            return "Error retrieving user information."

    def delete_specific_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by its ID"""
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"Deleted memory with ID: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting specific memory {memory_id}: {e}")
            return False

    def delete_user_memories(self, user_id: str):
        """Delete all memories for a specific user"""
        try:
            # Get all documents for the user
            results = self.collection.get(where={"user_id": user_id})
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} memories for user {user_id}")
                return len(results['ids'])
            
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting user memories: {e}")
            return 0

    def get_emotion_context(self, user_id: str) -> str:
        """Get emotion and relationship context for the user"""
        if not self.enable_emotions or not self.emotion_manager:
            return ""
        
        try:
            return self.emotion_manager.get_emotion_context(user_id)
        except Exception as e:
            logger.error(f"Error getting emotion context for user {user_id}: {e}")
            return ""

    def get_user_emotion_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get the complete emotion profile for a user"""
        if not self.enable_emotions or not self.emotion_manager:
            return None
        
        try:
            return self.emotion_manager.get_or_create_profile(user_id)
        except Exception as e:
            logger.error(f"Error getting user emotion profile for {user_id}: {e}")
            return None

    def cleanup_emotion_data(self, days_to_keep: int = 30):
        """Clean up old emotion data"""
        if not self.enable_emotions or not self.emotion_manager:
            return
        
        try:
            self.emotion_manager.cleanup_old_data(days_to_keep)
        except Exception as e:
            logger.error(f"Error cleaning up emotion data: {e}")

    def save_emotion_profiles(self):
        """Manually save emotion profiles"""
        if not self.enable_emotions or not self.emotion_manager:
            return
        
        try:
            self.emotion_manager.save_profiles()
        except Exception as e:
            logger.error(f"Error saving emotion profiles: {e}")

    def get_emotion_aware_context(self, user_id: str, query: str, limit: int = 5) -> str:
        """Get context that's aware of the user's emotional state and relationship level"""
        try:
            # Get regular memories
            memories = self.retrieve_relevant_memories(user_id, query, limit)
            
            # Convert memories to context string
            context_parts = []
            
            if memories:
                for memory in memories:
                    metadata = memory.get('metadata', {})
                    if metadata.get('type') == 'user_fact':
                        context_parts.append(f"• {metadata.get('fact', 'Unknown fact')}")
                    elif 'user_message' in metadata:
                        context_parts.append(f"• Previously discussed: {metadata['user_message'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else "No previous context found."
            
            # Add emotion context if available
            if self.enable_emotions and self.emotion_manager:
                emotion_context = self.get_emotion_context(user_id)
                if emotion_context:
                    context = f"[Emotional Context: {emotion_context}]\n\n{context}"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting emotion-aware context: {e}")
            # Fallback to regular memory retrieval
            try:
                memories = self.retrieve_relevant_memories(user_id, query, limit)
                return f"Retrieved {len(memories)} memories (no emotion context due to error)"
            except:
                return "Error retrieving context"

    def get_collection_stats(self) -> Dict:
        """Get statistics about the memory collections"""
        try:
            user_count = self.collection.count()
            global_count = self.global_collection.count()
            
            stats = {
                "total_memories": user_count,
                "total_global_facts": global_count,
                "user_collection_name": self.collection.name,
                "global_collection_name": self.global_collection.name
            }
            
            # Add emotion stats if enabled
            if self.enable_emotions and self.emotion_manager:
                emotion_stats = {
                    "emotion_profiles_count": len(self.emotion_manager.user_profiles),
                    "emotion_system_enabled": True
                }
                stats.update(emotion_stats)
            else:
                stats["emotion_system_enabled"] = False
            
            return stats
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
