"""
Local Emotion Engine
Ultra-fast local emotion analysis using VADER and RoBERTa hybrid approach.
Optimized for WhisperEngine's real-time conversation analysis.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmotionResult:
    """Structured emotion analysis result"""

    primary_emotion: str
    confidence: float
    sentiment_score: float  # -1 to 1
    emotions: dict[str, float]
    analysis_time_ms: float
    method: str  # "vader", "roberta", "hybrid"


class LocalEmotionEngine:
    """
    High-performance local emotion analysis engine.
    Uses VADER for ultra-fast real-time analysis and RoBERTa for detailed analysis.
    """

    def __init__(self):
        """Initialize the local emotion engine"""

        # Model configuration
        self.use_vader = os.getenv("ENABLE_VADER_EMOTION", "true").lower() == "true"
        self.use_roberta = os.getenv("ENABLE_ROBERTA_EMOTION", "true").lower() == "true"
        self.roberta_model_name = os.getenv(
            "ROBERTA_EMOTION_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest"
        )

        # Performance settings
        self.cache_size = int(os.getenv("EMOTION_CACHE_SIZE", "500"))
        self.batch_size = int(os.getenv("EMOTION_BATCH_SIZE", "8"))

        # Model instances
        self._vader_analyzer = None
        self._roberta_pipeline = None
        self._is_initialized = False
        self._init_lock = asyncio.Lock()

        # Performance tracking
        self.total_analyses = 0
        self.total_time = 0.0
        self.cache_hits = 0

        # Emotion cache
        self._emotion_cache = {}

        logger.info("LocalEmotionEngine initialized")

    async def initialize(self):
        """Initialize emotion models"""
        if self._is_initialized:
            return

        async with self._init_lock:
            if self._is_initialized:
                return

            try:
                await self._load_models()
                self._is_initialized = True
                logger.info("✅ Local emotion models initialized")
            except Exception as e:
                logger.error("❌ Failed to initialize emotion models: %s", e)
                raise

    async def _load_models(self):
        """Load emotion analysis models"""
        loop = asyncio.get_event_loop()

        # Load VADER (ultra-fast)
        if self.use_vader:
            try:

                def load_vader():
                    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

                    return SentimentIntensityAnalyzer()

                self._vader_analyzer = await loop.run_in_executor(None, load_vader)
                logger.info("✅ VADER sentiment analyzer loaded")
            except ImportError:
                logger.warning("⚠️ VADER not available - install with: pip install vaderSentiment")
                self.use_vader = False
            except Exception as e:
                logger.error("❌ VADER loading failed: %s", e)
                self.use_vader = False

        # Load RoBERTa (high quality)
        if self.use_roberta:
            try:

                def load_roberta():
                    from transformers import pipeline

                    return pipeline(
                        "sentiment-analysis",
                        model=self.roberta_model_name,
                        return_all_scores=False,  # Only return top score
                        device=0 if os.getenv("USE_GPU", "false").lower() == "true" else -1,
                    )

                self._roberta_pipeline = await loop.run_in_executor(None, load_roberta)
                logger.info("✅ RoBERTa emotion model loaded: %s", self.roberta_model_name)
            except ImportError:
                logger.warning(
                    "⚠️ transformers not available - install with: pip install transformers"
                )
                self.use_roberta = False
            except Exception as e:
                logger.error("❌ RoBERTa loading failed: %s", e)
                self.use_roberta = False

        if not self.use_vader and not self.use_roberta:
            raise RuntimeError("No emotion analysis models available")

    @lru_cache(maxsize=500)
    def _get_cache_key(self, text: str, method: str) -> str:
        """Generate cache key for emotion analysis"""
        return f"emotion_{method}_{hash(text)}"

    async def _analyze_with_vader(self, text: str) -> EmotionResult:
        """Analyze emotion using VADER (ultra-fast)"""
        start_time = time.time()

        # VADER analysis (synchronous, very fast)
        scores = self._vader_analyzer.polarity_scores(text)

        # Convert VADER scores to standard emotion format
        sentiment_score = scores["compound"]

        # Determine primary emotion from VADER scores
        if sentiment_score >= 0.05:
            primary_emotion = "positive"
            confidence = min(sentiment_score, 1.0)
        elif sentiment_score <= -0.05:
            primary_emotion = "negative"
            confidence = min(abs(sentiment_score), 1.0)
        else:
            primary_emotion = "neutral"
            confidence = 1.0 - abs(sentiment_score)

        emotions = {"positive": scores["pos"], "negative": scores["neg"], "neutral": scores["neu"]}

        analysis_time = (time.time() - start_time) * 1000

        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            sentiment_score=sentiment_score,
            emotions=emotions,
            analysis_time_ms=analysis_time,
            method="vader",
        )

    async def _analyze_with_roberta(self, text: str) -> EmotionResult:
        """Analyze emotion using RoBERTa (high quality)"""
        start_time = time.time()

        # RoBERTa analysis (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: self._roberta_pipeline(text)[0])

        # Convert RoBERTa results to standard format
        primary_emotion = result["label"].lower()
        confidence = result["score"]

        # Map to sentiment score (-1 to 1)
        if primary_emotion == "positive":
            sentiment_score = confidence
        elif primary_emotion == "negative":
            sentiment_score = -confidence
        else:
            sentiment_score = 0.0

        emotions = {primary_emotion: confidence}

        analysis_time = (time.time() - start_time) * 1000

        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            sentiment_score=sentiment_score,
            emotions=emotions,
            analysis_time_ms=analysis_time,
            method="roberta",
        )

    async def analyze_emotion(
        self, text: str, method: str = "auto", use_cache: bool = True
    ) -> EmotionResult:
        """
        Analyze emotion in text using specified method

        Args:
            text: Text to analyze
            method: "vader", "roberta", "hybrid", or "auto"
            use_cache: Whether to use emotion cache

        Returns:
            EmotionResult with analysis
        """
        if not self._is_initialized:
            await self.initialize()

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text, method)
            if cache_key in self._emotion_cache:
                self.cache_hits += 1
                return self._emotion_cache[cache_key]

        # Determine analysis method
        if method == "auto":
            # Auto-select based on text length and available models
            if len(text) < 100 and self.use_vader:
                method = "vader"  # Fast for short texts
            elif self.use_roberta:
                method = "roberta"  # Quality for longer texts
            elif self.use_vader:
                method = "vader"  # Fallback to VADER
            else:
                raise RuntimeError("No emotion analysis models available")

        # Perform analysis
        if method == "vader" and self.use_vader:
            result = await self._analyze_with_vader(text)
        elif method == "roberta" and self.use_roberta:
            result = await self._analyze_with_roberta(text)
        elif method == "hybrid" and self.use_vader and self.use_roberta:
            # Hybrid: Use VADER for speed, RoBERTa for refinement
            vader_result = await self._analyze_with_vader(text)

            # Use RoBERTa only if VADER is uncertain
            if vader_result.confidence < 0.7:
                roberta_result = await self._analyze_with_roberta(text)

                # Combine results (weighted average)
                combined_sentiment = (
                    vader_result.sentiment_score * 0.3 + roberta_result.sentiment_score * 0.7
                )

                result = EmotionResult(
                    primary_emotion=roberta_result.primary_emotion,
                    confidence=max(vader_result.confidence, roberta_result.confidence),
                    sentiment_score=combined_sentiment,
                    emotions={**vader_result.emotions, **roberta_result.emotions},
                    analysis_time_ms=vader_result.analysis_time_ms
                    + roberta_result.analysis_time_ms,
                    method="hybrid",
                )
            else:
                result = vader_result
                result.method = "hybrid"
        else:
            raise ValueError(f"Method '{method}' not available or models not loaded")

        # Cache result
        if use_cache:
            cache_key = self._get_cache_key(text, method)

            # Manage cache size
            if len(self._emotion_cache) >= self.cache_size:
                # Remove oldest entries
                oldest_keys = list(self._emotion_cache.keys())[:100]
                for key in oldest_keys:
                    del self._emotion_cache[key]

            self._emotion_cache[cache_key] = result

        # Update performance tracking
        self.total_analyses += 1
        self.total_time += result.analysis_time_ms / 1000

        return result

    async def analyze_emotions_batch(
        self, texts: list[str], method: str = "auto"
    ) -> list[EmotionResult]:
        """Analyze emotions for multiple texts efficiently"""
        if not texts:
            return []

        # Process in parallel for better performance
        tasks = [self.analyze_emotion(text, method=method) for text in texts]

        return await asyncio.gather(*tasks)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics"""
        avg_time_per_analysis = self.total_time / max(self.total_analyses, 1) * 1000

        cache_hit_rate = self.cache_hits / max(self.total_analyses, 1)

        return {
            "total_analyses": self.total_analyses,
            "avg_time_per_analysis_ms": avg_time_per_analysis,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._emotion_cache),
            "vader_available": self.use_vader,
            "roberta_available": self.use_roberta,
            "is_initialized": self._is_initialized,
        }

    async def warmup(self):
        """Warm up the emotion models"""
        if not self._is_initialized:
            await self.initialize()

        sample_texts = [
            "I'm so excited about this!",
            "This is really frustrating.",
            "The weather is okay today.",
        ]

        logger.info("🔥 Warming up emotion models...")
        start_time = time.time()

        # Test all available methods
        methods = []
        if self.use_vader:
            methods.append("vader")
        if self.use_roberta:
            methods.append("roberta")
        if self.use_vader and self.use_roberta:
            methods.append("hybrid")

        for method in methods:
            for text in sample_texts:
                await self.analyze_emotion(text, method=method)

        warmup_time = time.time() - start_time
        logger.info("✅ Emotion model warmup completed in %.2fms", warmup_time * 1000)

    async def shutdown(self):
        """Clean shutdown"""
        self._emotion_cache.clear()
        self._vader_analyzer = None
        self._roberta_pipeline = None
        self._is_initialized = False
        logger.info("✅ LocalEmotionEngine shutdown complete")


# Create default instance
_default_engine = None


async def get_default_emotion_engine() -> LocalEmotionEngine:
    """Get the default emotion engine instance"""
    global _default_engine
    if _default_engine is None:
        _default_engine = LocalEmotionEngine()
        await _default_engine.initialize()
    return _default_engine


async def analyze_emotion(text: str, method: str = "auto") -> EmotionResult:
    """Convenience function for emotion analysis"""
    engine = await get_default_emotion_engine()
    return await engine.analyze_emotion(text, method=method)


# Test function
async def test_local_emotion_engine():
    """Test the local emotion engine"""

    engine = LocalEmotionEngine()
    await engine.warmup()

    test_texts = [
        "I'm absolutely thrilled about this project!",
        "This is so frustrating and annoying.",
        "The weather is pretty normal today.",
        "I love spending time with my friends!",
    ]

    # Test different methods
    methods = ["vader", "roberta", "hybrid", "auto"]

    for method in methods:
        if (
            (method == "roberta" and not engine.use_roberta)
            or (method == "vader" and not engine.use_vader)
            or (method == "hybrid" and not (engine.use_vader and engine.use_roberta))
        ):
            continue


        start_time = time.time()
        results = await engine.analyze_emotions_batch(test_texts[:2], method=method)
        time.time() - start_time


        for _text, _result in zip(test_texts[:2], results, strict=False):
            pass

    # Show performance stats
    stats = engine.get_performance_stats()
    for _key, _value in stats.items():
        pass

    await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(test_local_emotion_engine())
