"""
WhisperEngine Optimized Emotional Intelligence Engine
High-performance emotion processing using pandas vectorization and parallel sentiment analysis
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, AsyncIterator
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading

import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class EmotionVector:
    """Vectorized emotion representation for batch processing"""

    primary_emotion: str
    intensity: float
    confidence: float
    valence: float  # Positive/negative scale
    arousal: float  # Energy/activation level
    dominance: float  # Control/power feeling
    sentiment_compound: float
    triggers: List[str]
    metadata: Dict[str, Any]


@dataclass
class BatchEmotionResult:
    """Results from batch emotion processing"""

    emotions: List[EmotionVector]
    processing_time: float
    batch_size: int
    avg_confidence: float
    emotion_distribution: Dict[str, int]


class VectorizedEmotionProcessor:
    """High-performance emotion processing using pandas vectorization"""

    def __init__(self, max_workers: int = 4):
        """
        Initialize vectorized emotion processor

        Args:
            max_workers: Number of worker threads for parallel processing
        """
        self.max_workers = max_workers

        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Thread pools for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)

        # Emotion mapping dictionaries for vectorized operations
        self.emotion_keywords = self._load_emotion_keywords()
        self.emotion_intensifiers = self._load_emotion_intensifiers()

        # Performance tracking
        self.total_processed = 0
        self.processing_times = []
        self.batch_sizes = []

        # Thread safety
        self._lock = threading.RLock()

        logger.info(f"🧠 Initialized VectorizedEmotionProcessor with {max_workers} workers")

    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """Load emotion keyword mappings for vectorized detection"""
        return {
            "joy": [
                "happy",
                "excited",
                "thrilled",
                "delighted",
                "pleased",
                "cheerful",
                "elated",
                "euphoric",
            ],
            "sadness": [
                "sad",
                "depressed",
                "down",
                "melancholy",
                "sorrowful",
                "dejected",
                "despondent",
            ],
            "anger": [
                "angry",
                "furious",
                "mad",
                "irritated",
                "annoyed",
                "outraged",
                "livid",
                "irate",
            ],
            "fear": ["afraid", "scared", "terrified", "anxious", "worried", "nervous", "panicked"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "startled", "stunned"],
            "disgust": ["disgusted", "revolted", "repulsed", "sickened", "appalled"],
            "love": ["love", "adore", "cherish", "affection", "fondness", "devotion"],
            "gratitude": ["grateful", "thankful", "appreciative", "blessed", "indebted"],
            "pride": ["proud", "accomplished", "successful", "triumphant", "satisfied"],
            "shame": ["ashamed", "embarrassed", "humiliated", "mortified", "guilty"],
            "excitement": ["excited", "thrilled", "pumped", "enthusiastic", "eager"],
            "calm": ["calm", "peaceful", "serene", "tranquil", "relaxed", "composed"],
        }

    def _load_emotion_intensifiers(self) -> Dict[str, float]:
        """Load emotion intensifier mappings for confidence scoring"""
        return {
            "extremely": 1.5,
            "very": 1.3,
            "really": 1.2,
            "quite": 1.1,
            "somewhat": 0.9,
            "slightly": 0.8,
            "barely": 0.6,
            "incredibly": 1.6,
            "absolutely": 1.5,
            "totally": 1.4,
            "completely": 1.4,
            "utterly": 1.3,
            "super": 1.3,
            "tremendously": 1.4,
            "enormously": 1.3,
            "immensely": 1.3,
        }

    def process_batch(
        self,
        texts: List[str],
        user_ids: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> BatchEmotionResult:
        """
        Process multiple texts using vectorized operations for maximum performance

        Args:
            texts: List of text messages to analyze
            user_ids: Optional list of user IDs for personalization
            metadata_list: Optional list of metadata dicts for each text

        Returns:
            BatchEmotionResult with vectorized emotion analysis
        """
        start_time = time.time()

        if not texts:
            return BatchEmotionResult([], 0.0, 0, 0.0, {})

        # Create DataFrame for vectorized operations
        df = pd.DataFrame(
            {
                "text": texts,
                "user_id": user_ids or [None] * len(texts),
                "metadata": metadata_list or [{}] * len(texts),
            }
        )

        # Add text preprocessing columns
        df["text_lower"] = df["text"].str.lower()
        df["text_words"] = df["text_lower"].str.split()
        df["word_count"] = df["text_words"].str.len()

        # Vectorized sentiment analysis
        sentiment_scores = []
        for text in df["text"]:
            scores = self.sentiment_analyzer.polarity_scores(text)
            sentiment_scores.append(scores)

        sentiment_df = pd.DataFrame(sentiment_scores)
        df = pd.concat([df, sentiment_df], axis=1)

        # Vectorized emotion detection
        emotion_results = self._detect_emotions_vectorized(df)

        # Calculate emotion distribution
        emotion_distribution = emotion_results["primary_emotion"].value_counts().to_dict()

        # Create EmotionVector objects
        emotions = []
        for i in range(len(emotion_results)):
            row = emotion_results.iloc[i]
            original_metadata = df.iloc[i]["metadata"]

            emotion = EmotionVector(
                primary_emotion=row["primary_emotion"],
                intensity=row["intensity"],
                confidence=row["confidence"],
                valence=row["compound"],  # Using VADER compound as valence
                arousal=row["arousal"],
                dominance=row["dominance"],
                sentiment_compound=row["compound"],
                triggers=row["triggers"],
                metadata=original_metadata,
            )
            emotions.append(emotion)

        processing_time = time.time() - start_time

        # Update performance tracking
        with self._lock:
            self.total_processed += len(texts)
            self.processing_times.append(processing_time)
            self.batch_sizes.append(len(texts))

            # Keep last 1000 records
            if len(self.processing_times) > 1000:
                self.processing_times = self.processing_times[-1000:]
                self.batch_sizes = self.batch_sizes[-1000:]

        result = BatchEmotionResult(
            emotions=emotions,
            processing_time=processing_time,
            batch_size=len(texts),
            avg_confidence=emotion_results["confidence"].mean(),
            emotion_distribution=emotion_distribution,
        )

        logger.debug(f"🧠 Processed {len(texts)} emotions in {processing_time*1000:.1f}ms")

        return result

    def _detect_emotions_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized emotion detection using pandas operations"""

        # Initialize result columns
        df["primary_emotion"] = "neutral"
        df["intensity"] = 0.5
        df["confidence"] = 0.0
        df["arousal"] = 0.5
        df["dominance"] = 0.5
        df["triggers"] = [[] for _ in range(len(df))]

        # Vectorized keyword matching for each emotion
        for emotion, keywords in self.emotion_keywords.items():
            # Create regex pattern for all keywords
            pattern = "|".join([f"\\b{keyword}\\b" for keyword in keywords])

            # Vectorized pattern matching
            matches = df["text_lower"].str.contains(pattern, regex=True, na=False)

            if matches.any():
                # Calculate intensity based on keyword frequency
                keyword_counts = df.loc[matches, "text_lower"].str.count(pattern)

                # Update emotions where this pattern matches
                mask = matches & (keyword_counts > 0)
                if mask.any():
                    df.loc[mask, "primary_emotion"] = emotion
                    df.loc[mask, "intensity"] = np.minimum(0.3 + (keyword_counts[mask] * 0.2), 1.0)
                    df.loc[mask, "confidence"] = np.minimum(
                        0.4 + (keyword_counts[mask] * 0.15), 0.95
                    )

                    # Set arousal and dominance based on emotion type
                    arousal_map = {
                        "joy": 0.8,
                        "anger": 0.9,
                        "fear": 0.8,
                        "surprise": 0.9,
                        "excitement": 0.9,
                        "sadness": 0.3,
                        "calm": 0.2,
                    }
                    dominance_map = {
                        "anger": 0.8,
                        "pride": 0.8,
                        "joy": 0.7,
                        "excitement": 0.7,
                        "fear": 0.2,
                        "sadness": 0.3,
                        "shame": 0.2,
                    }

                    df.loc[mask, "arousal"] = arousal_map.get(emotion, 0.5)
                    df.loc[mask, "dominance"] = dominance_map.get(emotion, 0.5)

                    # Extract triggers (matched keywords)
                    for idx in df[mask].index:
                        text_value = str(df.loc[idx, "text_lower"])  # Ensure string type
                        found_keywords = [kw for kw in keywords if kw in text_value]
                        df.at[idx, "triggers"] = found_keywords

        # Apply intensifier adjustments vectorized
        for intensifier, multiplier in self.emotion_intensifiers.items():
            has_intensifier = df["text_lower"].str.contains(f"\\b{intensifier}\\b", regex=True)
            df.loc[has_intensifier, "intensity"] *= multiplier
            df.loc[has_intensifier, "confidence"] *= min(multiplier, 1.2)

        # Clamp values to valid ranges
        df["intensity"] = np.clip(df["intensity"], 0.0, 1.0)
        df["confidence"] = np.clip(df["confidence"], 0.0, 1.0)
        df["arousal"] = np.clip(df["arousal"], 0.0, 1.0)
        df["dominance"] = np.clip(df["dominance"], 0.0, 1.0)

        # Use VADER sentiment for neutral cases
        neutral_mask = df["primary_emotion"] == "neutral"
        if neutral_mask.any():
            # Map VADER compound to basic emotions
            compound_scores = df.loc[neutral_mask, "compound"]

            # Positive compound -> joy, negative -> sadness
            positive_mask = neutral_mask & (df["compound"] > 0.2)
            negative_mask = neutral_mask & (df["compound"] < -0.2)

            df.loc[positive_mask, "primary_emotion"] = "joy"
            df.loc[positive_mask, "intensity"] = np.abs(df.loc[positive_mask, "compound"])
            df.loc[positive_mask, "confidence"] = np.abs(df.loc[positive_mask, "compound"]) * 0.8

            df.loc[negative_mask, "primary_emotion"] = "sadness"
            df.loc[negative_mask, "intensity"] = np.abs(df.loc[negative_mask, "compound"])
            df.loc[negative_mask, "confidence"] = np.abs(df.loc[negative_mask, "compound"]) * 0.8

        return df

    async def process_batch_async(
        self,
        texts: List[str],
        user_ids: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> BatchEmotionResult:
        """Async wrapper for batch processing"""

        # Use thread pool for CPU-intensive emotion processing
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.thread_pool, self.process_batch, texts, user_ids, metadata_list
        )

        return result

    async def process_streaming(
        self, text_stream: asyncio.Queue, batch_size: int = 10, timeout: float = 1.0
    ) -> AsyncIterator[BatchEmotionResult]:
        """Process streaming text data in batches for real-time emotion analysis"""

        batch = []
        last_process_time = time.time()

        while True:
            try:
                # Collect batch items
                try:
                    text_data = await asyncio.wait_for(text_stream.get(), timeout=timeout)
                    batch.append(text_data)
                except asyncio.TimeoutError:
                    pass

                # Process batch when ready
                current_time = time.time()
                should_process = len(batch) >= batch_size or (
                    batch and current_time - last_process_time > timeout
                )

                if should_process and batch:
                    # Extract texts and metadata from batch
                    texts = [item.get("text", "") for item in batch]
                    user_ids = [item.get("user_id") for item in batch]
                    metadata_list = [item.get("metadata", {}) for item in batch]

                    # Process batch
                    result = await self.process_batch_async(texts, user_ids, metadata_list)

                    yield result

                    batch.clear()
                    last_process_time = current_time

            except Exception as e:
                logger.error(f"Streaming emotion processing error: {e}")
                await asyncio.sleep(0.1)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the emotion processor"""

        with self._lock:
            avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
            avg_batch_size = np.mean(self.batch_sizes) if self.batch_sizes else 0
            throughput = (
                self.total_processed / sum(self.processing_times) if self.processing_times else 0
            )

            return {
                "total_processed": self.total_processed,
                "avg_processing_time_ms": avg_processing_time * 1000,
                "avg_batch_size": avg_batch_size,
                "throughput_per_second": throughput,
                "max_workers": self.max_workers,
                "total_batches": len(self.processing_times),
            }

    def shutdown(self):
        """Graceful shutdown of thread pools"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("✅ VectorizedEmotionProcessor shutdown complete")


class ProductionEmotionEngine:
    """Production-ready emotion engine with caching and optimization"""

    def __init__(self, max_workers: int = 4, enable_caching: bool = True, cache_size: int = 1000):
        """
        Initialize production emotion engine

        Args:
            max_workers: Number of worker threads
            enable_caching: Enable emotion result caching
            cache_size: Maximum cache size
        """
        self.processor = VectorizedEmotionProcessor(max_workers)
        self.enable_caching = enable_caching
        self.cache_size = cache_size

        # LRU cache for frequent emotions
        self.emotion_cache = {}
        self.cache_access_times = {}

        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"🚀 Initialized ProductionEmotionEngine with caching={enable_caching}")

    async def analyze_emotion(
        self, text: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> EmotionVector:
        """Analyze single text with caching optimization"""

        # Check cache first
        cache_key = f"{hash(text)}_{user_id}" if self.enable_caching else None

        if cache_key and cache_key in self.emotion_cache:
            self.cache_hits += 1
            self.cache_access_times[cache_key] = time.time()
            return self.emotion_cache[cache_key]

        # Process emotion
        user_ids_list = [user_id] if user_id is not None else None
        result = await self.processor.process_batch_async([text], user_ids_list, [metadata or {}])

        if result.emotions:
            emotion = result.emotions[0]

            # Cache result
            if self.enable_caching and cache_key:
                self._cache_result(cache_key, emotion)

            self.cache_misses += 1
            return emotion

        # Return neutral emotion if processing failed
        return EmotionVector(
            primary_emotion="neutral",
            intensity=0.5,
            confidence=0.1,
            valence=0.0,
            arousal=0.5,
            dominance=0.5,
            sentiment_compound=0.0,
            triggers=[],
            metadata=metadata or {},
        )

    async def analyze_emotions_batch(
        self,
        texts: List[str],
        user_ids: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[EmotionVector]:
        """Analyze multiple texts with batch optimization"""

        if not texts:
            return []

        # Check cache for batch items
        cache_results = {}
        uncached_indices = []
        uncached_texts = []
        uncached_user_ids = []
        uncached_metadata = []

        if self.enable_caching:
            for i, text in enumerate(texts):
                user_id = user_ids[i] if user_ids else None
                cache_key = f"{hash(text)}_{user_id}"

                if cache_key in self.emotion_cache:
                    cache_results[i] = self.emotion_cache[cache_key]
                    self.cache_hits += 1
                    self.cache_access_times[cache_key] = time.time()
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
                    uncached_user_ids.append(user_id)
                    uncached_metadata.append(metadata_list[i] if metadata_list else {})
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts
            uncached_user_ids = user_ids or [None] * len(texts)
            uncached_metadata = metadata_list or [{}] * len(texts)

        # Process uncached items
        if uncached_texts:
            # Clean up user IDs - convert None values to string "None" or filter them out
            cleaned_user_ids = [
                uid if uid is not None else f"anonymous_{i}"
                for i, uid in enumerate(uncached_user_ids)
            ]

            batch_result = await self.processor.process_batch_async(
                uncached_texts, cleaned_user_ids, uncached_metadata
            )

            # Cache new results
            if self.enable_caching:
                for i, emotion in enumerate(batch_result.emotions):
                    original_index = uncached_indices[i]
                    user_id = uncached_user_ids[i]
                    cache_key = f"{hash(uncached_texts[i])}_{user_id}"
                    self._cache_result(cache_key, emotion)
                    cache_results[original_index] = emotion
            else:
                for i, emotion in enumerate(batch_result.emotions):
                    cache_results[uncached_indices[i]] = emotion

            self.cache_misses += len(uncached_texts)

        # Reconstruct results in original order
        results = []
        for i in range(len(texts)):
            if i in cache_results:
                results.append(cache_results[i])
            else:
                # Fallback neutral emotion
                results.append(
                    EmotionVector(
                        primary_emotion="neutral",
                        intensity=0.5,
                        confidence=0.1,
                        valence=0.0,
                        arousal=0.5,
                        dominance=0.5,
                        sentiment_compound=0.0,
                        triggers=[],
                        metadata=metadata_list[i] if metadata_list else {},
                    )
                )

        return results

    def _cache_result(self, cache_key: str, emotion: EmotionVector):
        """Cache emotion result with LRU eviction"""

        # Remove oldest entries if cache is full
        if len(self.emotion_cache) >= self.cache_size:
            # Find and remove oldest entries
            sorted_keys = sorted(
                self.cache_access_times.keys(), key=lambda k: self.cache_access_times[k]
            )

            keys_to_remove = sorted_keys[: self.cache_size // 4]  # Remove 25%
            for key in keys_to_remove:
                self.emotion_cache.pop(key, None)
                self.cache_access_times.pop(key, None)

        # Add new entry
        self.emotion_cache[cache_key] = emotion
        self.cache_access_times[cache_key] = time.time()

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""

        processor_stats = self.processor.get_performance_stats()

        cache_stats = {
            "cache_enabled": self.enable_caching,
            "cache_size": len(self.emotion_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
        }

        return {
            "processor": processor_stats,
            "cache": cache_stats,
            "total_requests": self.cache_hits + self.cache_misses,
        }

    async def shutdown(self):
        """Graceful shutdown"""
        self.processor.shutdown()
        logger.info("✅ ProductionEmotionEngine shutdown complete")


# ChromaDB/existing system adapter
class EmotionEngineAdapter:
    """Adapter to integrate optimized emotion engine with existing systems"""

    def __init__(self, max_workers: int = 4):
        self.engine = ProductionEmotionEngine(max_workers)

    async def process_interaction_enhanced(
        self, user_id: str, message: str, display_name: Optional[str] = None
    ) -> Tuple[Any, EmotionVector]:
        """Compatible with existing emotion manager interface"""

        metadata = {"display_name": display_name} if display_name else {}
        emotion = await self.engine.analyze_emotion(message, user_id, metadata)

        # Return tuple for compatibility (profile, emotion_profile)
        # Profile would be handled by existing user profile system
        return None, emotion

    async def get_enhanced_emotion_context(self, user_id: str, query: str) -> Dict[str, Any]:
        """Get emotion context for query"""

        emotion = await self.engine.analyze_emotion(query, user_id)

        return {
            "current_emotion": emotion.primary_emotion,
            "intensity": emotion.intensity,
            "confidence": emotion.confidence,
            "sentiment": emotion.sentiment_compound,
            "triggers": emotion.triggers,
        }
