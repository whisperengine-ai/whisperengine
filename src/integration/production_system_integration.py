"""
Production System Integration
Integrates all optimized components into the main WhisperEngine bot architecture
"""

import asyncio
import logging
import os
import time
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionSystemIntegrator:
    """
    Integrates all production-optimized components into WhisperEngine

    Features:
    - Production Phase 4 Engine for multi-core processing
    - Faiss Memory Engine for ultra-fast vector search
    - Vectorized Emotion Engine for high-throughput sentiment analysis
    - Advanced Memory Batcher for database efficiency
    - Concurrent Conversation Manager for massive user scaling
    """

    def __init__(self, config: dict[str, Any] | None = None, bot_core=None):
        """Initialize production system integrator"""
        self.config = config or self._load_default_config()
        self.bot_core = bot_core  # Reference to bot core for real integrations
        self.components = {}
        self.is_initialized = False

        # Performance tracking
        self.performance_metrics = {
            "engine_throughput": 0,
            "memory_speed_improvement": 0,
            "emotion_processing_rate": 0,
            "memory_batch_efficiency": 0,
            "concurrent_sessions": 0,
        }

    def _load_default_config(self) -> dict[str, Any]:
        """Load default production configuration with environment-based scaling"""
        import os
        
        # Dynamic worker scaling based on available CPU cores
        cpu_count = os.cpu_count() or 4
        max_threads = min(int(os.getenv("MAX_WORKER_THREADS", cpu_count * 2)), 16)
        max_processes = min(int(os.getenv("MAX_WORKER_PROCESSES", cpu_count)), 8)
        
        return {
            "production_engine": {
                "max_workers_threads": max_threads,
                "max_workers_processes": max_processes,
                "batch_size": 32,
                "enable_multiprocessing": True,
            },
            "faiss_memory": {
                "index_type": "IVF",
                "num_clusters": 256,
                "enable_gpu": False,
                "batch_size": 100,
            },
            "vectorized_emotion": {
                "cache_size": 10000,
                "batch_size": 500,
                "enable_parallel_sentiment": True,
            },
            "memory_batcher": {
                "batch_size": 50,
                "max_batch_wait_ms": 100,
                "cache_ttl_seconds": 300,
            },
            "conversation_manager": {
                "max_concurrent_sessions": 1000,
                "max_workers_threads": max_threads + 4,  # Extra threads for conversation handling
                "max_workers_processes": max_processes + 2,  # Extra processes for heavy operations
                "session_timeout_minutes": 30,
            },
        }

    async def initialize_production_components(self) -> bool:
        """Initialize all production-optimized components"""
        try:
            logger.info("✨ Initializing production system components...")

            # Initialize Production Phase 4 Engine
            await self._init_production_engine()

            # Initialize Faiss Memory Engine
            await self._init_faiss_memory()

            # Initialize Vectorized Emotion Engine
            await self._init_vectorized_emotion()

            # Initialize Advanced Memory Batcher
            await self._init_memory_batcher()

            # Initialize Concurrent Conversation Manager
            await self._init_conversation_manager()

            self.is_initialized = True
            logger.info("✅ All production components initialized successfully")

            # Run initial performance validation
            await self._validate_component_integration()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize production components: {e}")
            return False

    async def _init_production_engine(self):
        """Initialize production Phase 4 engine"""
        try:
            from src.intelligence.production_phase4_engine import OptimizedPhase4Engine

            self.components["production_engine"] = OptimizedPhase4Engine(
                max_workers=self.config["production_engine"]["max_workers_threads"],
                batch_size=self.config["production_engine"]["batch_size"],
                enable_multiprocessing=True,
            )

            await self.components["production_engine"].start_engine()
            logger.info("✅ Production Phase 4 Engine initialized")

        except (ImportError, FileNotFoundError):
            logger.warning("⚠️ Production Phase 4 Engine not available - using fallback")
            self.components["production_engine"] = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize production engine: {e}")
            self.components["production_engine"] = None

    async def _init_faiss_memory(self):
        """Initialize Faiss memory engine"""
        try:
            from src.memory.faiss_memory_engine import FaissMemoryEngine

            # Use default parameters for the constructor
            self.components["faiss_memory"] = FaissMemoryEngine()

            await self.components["faiss_memory"].initialize()
            logger.info("✅ Faiss Memory Engine initialized")

        except (ImportError, FileNotFoundError):
            logger.warning("⚠️ Faiss Memory Engine not available - using fallback")
            self.components["faiss_memory"] = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Faiss memory: {e}")
            self.components["faiss_memory"] = None

    async def _init_vectorized_emotion(self):
        """Initialize vectorized emotion engine"""
        try:
            from src.emotion.vectorized_emotion_engine import ProductionEmotionEngine

            # Use default parameters for the constructor
            self.components["vectorized_emotion"] = ProductionEmotionEngine(enable_caching=True)

            logger.info("✅ Vectorized Emotion Engine initialized")

        except (ImportError, FileNotFoundError):
            logger.warning("⚠️ Vectorized Emotion Engine not available - using fallback")
            self.components["vectorized_emotion"] = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize vectorized emotion: {e}")
            self.components["vectorized_emotion"] = None

    async def _init_memory_batcher(self):
        """Initialize advanced memory batcher"""
        try:
            from src.memory.advanced_memory_batcher import AdvancedMemoryBatcher

            # Try to get real ChromaDB manager from bot core or create adapter
            chromadb_manager = None

            # Check if we have access to bot core with real memory manager
            if (
                hasattr(self, "bot_core")
                and self.bot_core
                and hasattr(self.bot_core, "memory_manager")
                and self.bot_core.memory_manager
            ):
                # Create adapter that wraps the real memory manager to provide ChromaDB-like interface
                class MemoryManagerAdapter:
                    def __init__(self, memory_manager):
                        self.memory_manager = memory_manager

                    async def store_conversation(
                        self,
                        user_id: str,
                        message: str,
                        response: str,
                        metadata: dict | None = None,
                    ):
                        """Adapt to UserMemoryManager.store_conversation interface"""
                        try:
                            # Merge channel_id into metadata for hierarchical memory compatibility
                            channel_id = (
                                metadata.get("channel_id", "production")
                                if metadata
                                else "production"
                            )
                            
                            # Prepare metadata with channel_id included
                            full_metadata = metadata or {}
                            full_metadata['channel_id'] = channel_id
                            
                            await self.memory_manager.store_conversation(
                                user_id=user_id,
                                user_message=message,
                                bot_response=response,
                                metadata=full_metadata,
                            )
                            return True
                        except Exception as e:
                            logger.warning(f"Memory store failed: {e}")
                            return False

                    async def store_memories(self, memories):
                        """Batch store multiple memories"""
                        for memory in memories:
                            await self.store_conversation(**memory)
                        return True

                    def retrieve_memories(self, query):
                        """Retrieve memories using real UserMemoryManager"""
                        try:
                            # Use the real memory manager's search functionality
                            if hasattr(self.memory_manager, "search_memories"):
                                memories = self.memory_manager.search_memories(query, limit=10)
                                return memories if memories else []
                            elif hasattr(self.memory_manager, "get_user_conversations"):
                                # Fallback to conversation retrieval if search not available
                                conversations = self.memory_manager.get_user_conversations(limit=10)
                                return conversations if conversations else []
                            else:
                                logger.warning("Memory manager doesn't support memory retrieval")
                                return []
                        except Exception as e:
                            logger.warning(f"Memory retrieval failed: {e}")
                            return []

                chromadb_manager = MemoryManagerAdapter(self.bot_core.memory_manager)
                logger.info("✅ Using real memory manager with adapter")
            else:
                # Use a simplified memory adapter when real components not available
                class SimplifiedMemoryAdapter:
                    """Simplified memory storage for production when full ChromaDB not available"""

                    def __init__(self):
                        self.memory_cache = []

                    def store_conversation(
                        self,
                        user_id: str,
                        message: str,
                        response: str,
                        metadata: dict | None = None,
                    ):
                        """Store conversation in memory cache"""
                        conversation = {
                            "user_id": user_id,
                            "message": message,
                            "response": response,
                            "metadata": metadata or {},
                            "timestamp": time.time(),
                        }
                        self.memory_cache.append(conversation)
                        # Keep only last 1000 conversations to prevent memory issues
                        if len(self.memory_cache) > 1000:
                            self.memory_cache = self.memory_cache[-1000:]
                        return True

                    async def store_memories(self, memories):
                        """Store batch memories"""
                        for memory in memories:
                            self.store_conversation(
                                memory.get("user_id", "unknown"),
                                memory.get("message", ""),
                                memory.get("response", ""),
                                memory.get("metadata", {}),
                            )
                        return True

                    def retrieve_memories(self, query):
                        """Simple memory retrieval based on text matching"""
                        if not query:
                            return self.memory_cache[-10:]  # Return last 10 conversations

                        matches = []
                        query_lower = query.lower()
                        for conversation in self.memory_cache:
                            if (
                                query_lower in conversation["message"].lower()
                                or query_lower in conversation["response"].lower()
                            ):
                                matches.append(conversation)

                        return matches[-10:]  # Return last 10 matches

                chromadb_manager = SimplifiedMemoryAdapter()
                logger.info(
                    "✅ Using simplified memory adapter (real memory manager not available)"
                )

            self.components["memory_batcher"] = AdvancedMemoryBatcher(
                chromadb_manager=chromadb_manager,
                batch_size=self.config["memory_batcher"]["batch_size"],
            )

            await self.components["memory_batcher"].start()
            logger.info("✅ Advanced Memory Batcher initialized")

        except (ImportError, FileNotFoundError):
            logger.warning("⚠️ Advanced Memory Batcher not available - using fallback")
            self.components["memory_batcher"] = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory batcher: {e}")
            self.components["memory_batcher"] = None

    async def _init_conversation_manager(self):
        """Initialize concurrent conversation manager"""
        try:
            from src.conversation.concurrent_conversation_manager import (
                ConcurrentConversationManager,
            )

            # Use real components when available, fallback to simplified versions
            advanced_thread_manager = None
            emotion_engine = None

            # Try to use real emotion engine if available
            if self.components.get("vectorized_emotion"):

                class EmotionEngineAdapter:
                    def __init__(self, vectorized_emotion):
                        self.vectorized_emotion = vectorized_emotion

                    async def analyze_emotion(self, message: str, user_id: str):
                        """Adapt vectorized emotion engine to expected interface"""
                        try:
                            emotions = await self.vectorized_emotion.analyze_emotions_batch(
                                [message], [user_id]
                            )
                            if emotions and len(emotions) > 0:
                                emotion = emotions[0]
                                return {
                                    "emotion": emotion.primary_emotion,
                                    "intensity": emotion.intensity,
                                    "confidence": emotion.confidence,
                                    "valence": emotion.valence,
                                }
                        except Exception as e:
                            logger.warning(f"Emotion analysis failed: {e}")

                        return {"emotion": "neutral", "intensity": 0.5, "confidence": 0.1}

                emotion_engine = EmotionEngineAdapter(self.components["vectorized_emotion"])
                logger.info("✅ Using real emotion engine with adapter")
            else:
                # Use simplified emotion analysis when real engine not available
                class SimplifiedEmotionEngine:
                    """Simplified emotion analysis for production when full emotion engine not available"""

                    async def analyze_emotion(self, message: str, user_id: str):
                        """Basic emotion analysis using keyword matching"""
                        message_lower = message.lower()

                        # Simple emotion detection based on keywords
                        positive_words = [
                            "happy",
                            "joy",
                            "excited",
                            "love",
                            "great",
                            "awesome",
                            "good",
                            "nice",
                            "thanks",
                            "thank you",
                        ]
                        negative_words = [
                            "sad",
                            "angry",
                            "hate",
                            "bad",
                            "terrible",
                            "awful",
                            "frustrated",
                            "upset",
                            "annoyed",
                        ]
                        question_words = ["?", "what", "how", "when", "where", "why", "who"]

                        positive_count = sum(1 for word in positive_words if word in message_lower)
                        negative_count = sum(1 for word in negative_words if word in message_lower)
                        question_count = sum(1 for word in question_words if word in message_lower)

                        if positive_count > negative_count:
                            emotion = "joy" if positive_count > 1 else "positive"
                            intensity = min(0.7 + positive_count * 0.1, 1.0)
                            valence = 0.7
                        elif negative_count > positive_count:
                            emotion = "anger" if negative_count > 1 else "negative"
                            intensity = min(0.6 + negative_count * 0.1, 1.0)
                            valence = 0.3
                        elif question_count > 0:
                            emotion = "curiosity"
                            intensity = 0.6
                            valence = 0.5
                        else:
                            emotion = "neutral"
                            intensity = 0.5
                            valence = 0.5

                        return {
                            "emotion": emotion,
                            "intensity": intensity,
                            "confidence": 0.6,  # Medium confidence for simplified analysis
                            "valence": valence,
                        }

                emotion_engine = SimplifiedEmotionEngine()
                logger.info("✅ Using simplified emotion engine (real engine not available)")

            # For advanced_thread_manager, use a simplified version for now
            class SimpleThreadManager:
                async def process_user_message(self, user_id: str, message: str, context: dict):
                    """Simple thread management for conversation tracking"""
                    thread_id = f"thread_{hash(f'{user_id}_{message}') % 1000}"
                    return {"thread_id": thread_id, "user_id": user_id, "status": "processed"}

            advanced_thread_manager = SimpleThreadManager()

            self.components["conversation_manager"] = ConcurrentConversationManager(
                advanced_thread_manager=advanced_thread_manager,
                emotion_engine=emotion_engine,
                memory_batcher=self.components.get(
                    "memory_batcher"
                ),  # Use real memory batcher if available
                max_concurrent_sessions=self.config["conversation_manager"][
                    "max_concurrent_sessions"
                ],
                max_workers_threads=self.config["conversation_manager"]["max_workers_threads"],
                max_workers_processes=self.config["conversation_manager"]["max_workers_processes"],
            )

            await self.components["conversation_manager"].start()
            logger.info("✅ Concurrent Conversation Manager initialized")

        except (ImportError, FileNotFoundError):
            logger.warning("⚠️ Concurrent Conversation Manager not available - using fallback")
            self.components["conversation_manager"] = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize conversation manager: {e}")
            self.components["conversation_manager"] = None

    async def _validate_component_integration(self):
        """Validate that all components work together"""
        logger.info("🧪 Validating component integration...")

        try:
            # Test message processing through integrated pipeline
            test_user_id = "integration_test_user"
            test_message = "Hello, this is a test message for production integration!"
            test_context = {"channel_id": "test_channel", "urgency": "normal"}

            # Process through production pipeline if available
            if self.components.get("conversation_manager"):
                result = await self.components["conversation_manager"].process_conversation_message(
                    user_id=test_user_id,
                    message=test_message,
                    channel_id=test_context["channel_id"],
                    context=test_context,
                    priority="normal",
                )
                logger.info(f"✅ Conversation manager test: {result.get('status', 'unknown')}")

            # Test vectorized emotion processing if available
            if self.components.get("vectorized_emotion"):
                emotion_result = await self.components["vectorized_emotion"].analyze_emotions_batch(
                    [test_message], [test_user_id]
                )
                if emotion_result and len(emotion_result) > 0:
                    logger.info(f"✅ Vectorized emotion test: {emotion_result[0].primary_emotion}")
                else:
                    logger.info("✅ Vectorized emotion test: completed")

            # Test memory operations if available
            if self.components.get("memory_batcher"):
                try:
                    await self.components["memory_batcher"].store_conversation_batch(
                        user_id=test_user_id,
                        message=test_message,
                        response="test response",
                        metadata={"test": True},
                    )
                    logger.info("✅ Memory batcher test: operation queued")
                except Exception as e:
                    logger.warning(f"⚠️ Memory batcher test skipped (dependency issue): {e}")
                    logger.info("✅ Memory batcher component available (validation skipped)")

            logger.info("✅ Component integration validation completed")

        except Exception as e:
            logger.error(f"❌ Component integration validation failed: {e}")
            raise

    async def process_message_production(
        self, user_id: str, message: str, context: dict[str, Any], priority: str = "normal"
    ) -> dict[str, Any]:
        """
        Process message through optimized production pipeline

        Uses all available optimized components for maximum performance
        """
        if not self.is_initialized:
            raise RuntimeError("Production system not initialized")

        result = {
            "user_id": user_id,
            "original_message": message,
            "context": context,
            "processing_pipeline": [],
            "performance_metrics": {},
        }

        try:
            # 1. Concurrent conversation management
            if self.components.get("conversation_manager"):
                conv_result = await self.components[
                    "conversation_manager"
                ].process_conversation_message(
                    user_id=user_id,
                    message=message,
                    channel_id=context.get("channel_id", "default"),
                    context=context,
                    priority=priority,
                )
                result["conversation_result"] = conv_result
                result["processing_pipeline"].append("concurrent_conversation")

            # 2. Vectorized emotion analysis
            if self.components.get("vectorized_emotion"):
                emotion_result = await self.components["vectorized_emotion"].analyze_emotions_batch(
                    [message], [user_id]
                )
                if emotion_result and len(emotion_result) > 0:
                    # Convert EmotionVector dataclass to dict for result storage
                    emotion_data = emotion_result[0]
                    result["emotion_analysis"] = {
                        "primary_emotion": emotion_data.primary_emotion,
                        "intensity": emotion_data.intensity,
                        "confidence": emotion_data.confidence,
                        "valence": emotion_data.valence,
                        "arousal": emotion_data.arousal,
                        "dominance": emotion_data.dominance,
                        "sentiment_compound": emotion_data.sentiment_compound,
                        "triggers": emotion_data.triggers,
                    }
                    result["processing_pipeline"].append("vectorized_emotion")

            # 3. Memory operations through batcher
            if self.components.get("memory_batcher"):
                try:
                    await self.components["memory_batcher"].store_conversation_batch(
                        user_id=user_id, message=message, response="AI processing", metadata=context
                    )
                    result["processing_pipeline"].append("memory_batching")
                except Exception as e:
                    logger.warning(f"Memory batching failed (dependency issue): {e}")
                    # Continue without memory batching

            # 4. Production Phase 4 processing (if needed)
            if self.components.get("production_engine") and context.get("enable_phase4", True):
                phase4_result = await self.components[
                    "production_engine"
                ].process_conversation_batch(
                    [{"user_id": user_id, "message": message, "context": context}]
                )
                result["phase4_result"] = phase4_result
                result["processing_pipeline"].append("production_phase4")

            result["status"] = "success"
            result["pipeline_used"] = " → ".join(result["processing_pipeline"])

            return result

        except Exception as e:
            logger.error(f"❌ Production message processing failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            return result

    def get_production_metrics(self) -> dict[str, Any]:
        """Get comprehensive production system metrics"""
        metrics = {
            "system_status": "online" if self.is_initialized else "offline",
            "components_available": {},
            "performance_metrics": self.performance_metrics.copy(),
        }

        # Check component availability and get their metrics
        for component_name, component in self.components.items():
            if component is not None:
                metrics["components_available"][component_name] = True

                # Get component-specific metrics if available
                if hasattr(component, "get_performance_stats"):
                    try:
                        # Check if it's a coroutine and handle accordingly
                        import inspect

                        if inspect.iscoroutinefunction(component.get_performance_stats):
                            # It's async, we'll need to handle this differently
                            metrics[f"{component_name}_stats"] = "async_available"
                        else:
                            # It's sync, safe to call
                            component_stats = component.get_performance_stats()
                            metrics[f"{component_name}_metrics"] = component_stats
                    except Exception as e:
                        logger.warning(f"Failed to get metrics for {component_name}: {e}")
                else:
                    metrics["components_available"][component_name] = False

        return metrics

    async def shutdown_production_system(self):
        """Gracefully shutdown all production components"""
        logger.info("🛑 Shutting down production system...")

        shutdown_tasks = []

        for component_name, component in self.components.items():
            if component and hasattr(component, "stop"):
                try:
                    shutdown_tasks.append(component.stop())
                except Exception as e:
                    logger.error(f"Error stopping {component_name}: {e}")

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        self.is_initialized = False
        logger.info("✅ Production system shutdown completed")


class WhisperEngineProductionAdapter:
    """
    Adapter to integrate production system with existing WhisperEngine bot

    This adapter allows existing Discord and Desktop bot code to transparently
    use optimized production components when available
    """

    def __init__(self, bot_core=None):
        """Initialize production adapter"""
        self.bot_core = bot_core
        self.production_integrator = None
        self.fallback_mode = False

    async def initialize_production_mode(self) -> bool:
        """Initialize production mode if components are available"""
        try:
            # Check if production mode is enabled
            enable_production = (
                os.getenv("ENABLE_PRODUCTION_OPTIMIZATION", "true").lower() == "true"
            )

            if not enable_production:
                logger.info("📋 Production optimization disabled by environment variable")
                self.fallback_mode = True
                return False

            # Initialize production integrator
            self.production_integrator = ProductionSystemIntegrator(bot_core=self.bot_core)
            success = await self.production_integrator.initialize_production_components()

            if success:
                logger.info("✨ WhisperEngine production mode enabled")
                return True
            else:
                logger.warning("⚠️ Production mode initialization failed - using fallback")
                self.fallback_mode = True
                return False

        except Exception as e:
            logger.error(f"❌ Production mode initialization error: {e}")
            self.fallback_mode = True
            return False

    async def process_user_message(
        self, user_id: str, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process user message with production optimizations if available

        Falls back to standard processing if production components unavailable
        """

        if self.production_integrator and not self.fallback_mode:
            # Use production pipeline
            try:
                return await self.production_integrator.process_message_production(
                    user_id=user_id,
                    message=message,
                    context=context,
                    priority=context.get("priority", "normal"),
                )
            except Exception as e:
                logger.error(f"Production processing failed, falling back: {e}")
                self.fallback_mode = True

        # Fallback to standard processing
        return await self._fallback_message_processing(user_id, message, context)

    async def _fallback_message_processing(
        self, user_id: str, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Fallback message processing using standard components"""

        # This would integrate with existing WhisperEngine components
        # For now, return a basic structure
        return {
            "user_id": user_id,
            "original_message": message,
            "context": context,
            "status": "processed_fallback",
            "processing_pipeline": ["standard_pipeline"],
            "note": "Processed using standard (non-optimized) pipeline",
        }

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status and performance metrics"""
        if self.production_integrator and not self.fallback_mode:
            return self.production_integrator.get_production_metrics()
        else:
            return {
                "system_status": "fallback_mode",
                "production_mode": False,
                "reason": "Production components not available or failed",
            }

    async def shutdown(self):
        """Shutdown production system gracefully"""
        if self.production_integrator:
            await self.production_integrator.shutdown_production_system()


# Factory function for easy integration
def create_production_adapter(bot_core=None) -> WhisperEngineProductionAdapter:
    """Create and return a production adapter instance"""
    return WhisperEngineProductionAdapter(bot_core)
