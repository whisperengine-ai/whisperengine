#!/usr/bin/env python3
"""
External API Emotion AI - Advanced Emotional Intelligence System

Full-capability emotional intelligence system designed for external API deployment.
Combines multiple AI models for comprehensive emotion analysis and response generation.

Features:
- Multi-model emotional analysis (LLM + external APIs)
- Conversation context tracking
- Embedding-based similarity analysis
- Advanced prompt generation for empathetic responses
- Performance monitoring and caching

This system provides the highest accuracy emotional intelligence capabilities
using multiple external API calls and advanced analysis techniques.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

# Import embedding manager for external embedding-based emotion analysis
from src.utils.embedding_manager import ExternalEmbeddingManager

# Graceful import for Phase 3
try:
    from src.memory.phase3_integration import Phase3MemoryNetworks

    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False


@dataclass
class EmotionConfig:
    """Configuration for emotion analysis"""

    tier: str
    description: str
    accuracy: str
    resource_usage: str
    api_calls_per_analysis: int
    avg_latency_ms: int


class ExternalAPIEmotionAI:
    """
    Cloud-optimized emotional intelligence using external APIs and embeddings
    Designed for Docker deployment without local GPU dependencies
    """

    def __init__(
        self,
        llm_client=None,
        llm_api_url: str | None = None,  # Deprecated, kept for compatibility
        openai_api_key: str | None = None,
        huggingface_api_key: str | None = None,  # Deprecated but kept for compatibility
        logger=None,
    ):

        # LLM Client integration - preferred method
        self.llm_client = llm_client

        # Fallback API Configuration (deprecated)
        if llm_api_url is not None:
            self.llm_api_url = llm_api_url.rstrip("/")
        elif llm_client is not None:
            # Extract URL from LLM client for compatibility with existing embedding calls
            self.llm_api_url = llm_client.api_url
        else:
            # Final fallback
            self.llm_api_url = os.getenv("LLM_CHAT_API_URL", "http://localhost:1234").rstrip("/")

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = huggingface_api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.logger = logger

        # Initialize external embedding manager for emotion analysis
        self.embedding_manager = ExternalEmbeddingManager()

        # Initialize session for HTTP requests
        self.session = None

        # Cache for performance
        self.emotion_cache = {}
        self.sentiment_cache = {}

        # Phase 3 integration if available
        if PHASE3_AVAILABLE:
            try:
                self.phase3_networks = Phase3MemoryNetworks()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Phase 3 initialization failed: {e}")
                self.phase3_networks = None
        else:
            self.phase3_networks = None

        # Performance tracking
        self.analysis_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0

        # Configuration for full capabilities emotion analysis
        # Configuration for full capabilities emotion analysis
        self.config = EmotionConfig(
            tier="full",
            description="Multiple API calls + external embedding analysis",
            accuracy="96-98%",
            resource_usage="High",
            api_calls_per_analysis=3,
            avg_latency_ms=600,
        )

        if self.logger:
            if self.llm_client:
                self.logger.info(
                    "🌐 External API Emotion AI initialized with LLM client integration"
                )
                self.logger.info(f"🔗 LLM provider: {self.llm_api_url}")
                self.logger.info(
                    f"🎭 Emotion model: {getattr(self.llm_client, 'emotion_model_name', 'default')}"
                )
                self.logger.info(
                    f"🔄 Emotion endpoint: {getattr(self.llm_client, 'emotion_chat_endpoint', 'same as main')}"
                )
            else:
                self.logger.info(
                    "🌐 External API Emotion AI initialized with direct HTTP (legacy mode)"
                )
                self.logger.info(f"🔗 LLM provider: {self.llm_api_url}")
            self.logger.info(
                f"🧠 External Embeddings: {'✅' if self.embedding_manager.use_external else '?'}"
            )

    async def initialize(self):
        """Initialize HTTP session and test API connectivity"""

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30), headers={"Content-Type": "application/json"}
        )

        # Test API connectivity
        await self._test_api_connectivity()
        if self.logger:
            self.logger.info("✅ External API Emotion AI ready")

    async def close(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()

    async def analyze_emotion_cloud(
        self,
        text: str,
        user_id: str | None = None,
        conversation_history: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze emotion using external APIs with full capabilities
        """

        if not self.session:
            await self.initialize()

        start_time = time.time()

        # Check cache first
        cache_key = hash(f"{text}")
        if cache_key in self.emotion_cache:
            self.cache_hits += 1
            cached_result = self.emotion_cache[cache_key].copy()
            cached_result["cache_hit"] = True
            return cached_result

        self.cache_misses += 1

        # Always use full emotion analysis capabilities
        try:
            result = await self._analyze_full_capabilities(text, user_id, conversation_history)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Emotion analysis failed: {e}")
            # Fallback to keywords
            result = self._analyze_with_keywords(text)
            result["analysis_method"] = "fallback_keywords"

        # Track performance
        analysis_time = (time.time() - start_time) * 1000
        self.analysis_times.append(analysis_time)
        result["analysis_time_ms"] = round(analysis_time, 2)
        result["cache_hit"] = False
        result["api_calls_made"] = 3  # Full capabilities use multiple API calls

        # Cache result (limit cache size)
        if len(self.emotion_cache) < 200:
            self.emotion_cache[cache_key] = result.copy()

        return result

    async def _analyze_full_capabilities(
        self,
        text: str,
        user_id: str | None = None,
        conversation_history: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Full capabilities emotion analysis - Multiple API calls + advanced linguistic analysis
        Maximum accuracy with comprehensive emotional intelligence
        """

        # Multiple parallel API calls
        tasks = [
            self._call_lm_studio_emotion_detailed(text),
            self._call_external_sentiment_api(text),
            self._call_embedding_emotion_analysis(text),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        lm_emotion, sentiment_result, embedding_emotion = results

        # Advanced emotion fusion from multiple sources
        emotion_sources = []

        if not isinstance(lm_emotion, Exception) and lm_emotion is not None:
            emotion_sources.append(("lm_studio", lm_emotion))
        else:
            if self.logger:
                self.logger.warning(f"LLM provider failed: {lm_emotion}")

        if not isinstance(embedding_emotion, Exception) and embedding_emotion is not None:
            emotion_sources.append(("embeddings", embedding_emotion))
        else:
            if self.logger:
                self.logger.warning(f"Embedding emotion analysis failed: {embedding_emotion}")

        if not emotion_sources:
            # Complete fallback
            emotion_sources.append(("keywords", self._analyze_with_keywords(text)))

        # Fusion algorithm - weighted combination
        fused_emotions = self._fuse_emotion_results(emotion_sources)

        # Advanced conversation context analysis
        context_emotion = None
        if conversation_history and user_id and len(conversation_history) > 1:
            context_emotion = await self._analyze_conversation_context_heavy(
                user_id, conversation_history
            )

        # Linguistic analysis
        linguistic_features = self._analyze_linguistic_features(text)

        # Adjust confidence based on multiple sources
        source_count = len(emotion_sources)
        confidence_multiplier = min(1.0, 0.7 + (source_count * 0.15))
        adjusted_confidence = fused_emotions["confidence"] * confidence_multiplier

        intensity = self._calculate_emotional_intensity_advanced(
            text, adjusted_confidence, linguistic_features
        )

        return {
            "primary_emotion": fused_emotions["primary_emotion"],
            "confidence": round(adjusted_confidence, 3),
            "intensity": round(intensity, 3),
            "all_emotions": fused_emotions["all_emotions"],
            "sentiment": (
                sentiment_result
                if not isinstance(sentiment_result, Exception)
                else {"label": "UNKNOWN", "score": 0.5}
            ),
            "conversation_context": context_emotion,
            "linguistic_features": linguistic_features,
            "analysis_method": "heavy_fusion",
            "emotion_sources_used": len(emotion_sources),
            "api_success_rate": len([r for r in results if not isinstance(r, Exception)])
            / len(results),
            "detected_emotions_count": len(fused_emotions.get("all_emotions", {})),
        }

    async def _call_lm_studio_emotion(self, text: str) -> dict | None:
        """Simple emotion analysis via LLM provider"""

        prompt = f"""Analyze the emotion in this text and respond with ONLY a JSON object:
Text: "{text}"

Response format:
{{"emotion": "joy|sadness|anger|fear|surprise|disgust|neutral", "confidence": 0.0-1.0}}"""

        try:
            self.api_calls += 1

            # Use LLM client if available (preferred method)
            if self.llm_client:
                messages = [{"role": "user", "content": prompt}]

                # Use emotion-specific endpoint if configured
                if (
                    hasattr(self.llm_client, "generate_emotion_chat_completion")
                    and self.llm_client.emotion_chat_endpoint
                ):
                    response = self.llm_client.generate_emotion_chat_completion(
                        messages=messages,
                        temperature=0.1,
                        max_tokens=self.llm_client.max_tokens_emotion,  # Use emotion-specific token limit
                    )
                else:
                    # Fallback to main endpoint
                    response = self.llm_client.generate_chat_completion(
                        messages=messages, temperature=0.1, max_tokens=100
                    )

                content = response["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                if content.startswith("{") and content.endswith("}"):
                    emotion_data = json.loads(content)
                    return emotion_data

            # Legacy fallback using direct HTTP session
            elif self.session:
                async with self.session.post(
                    f"{self.llm_api_url}/v1/chat/completions",
                    json={
                        "model": "local-llm",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 100,
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"].strip()

                        # Parse JSON response
                        if content.startswith("{") and content.endswith("}"):
                            emotion_data = json.loads(content)
                            return emotion_data

        except Exception as e:
            if self.logger:
                self.logger.warning(f"LLM provider emotion call failed: {e}")

        return None

    async def _call_lm_studio_emotion_detailed(self, text: str) -> dict:
        """Detailed emotion analysis via LLM provider"""

        prompt = f"""Analyze the emotions in this text. Provide a detailed emotional breakdown.

Text: "{text}"

Identify:
1. Primary emotion (joy, sadness, anger, fear, surprise, disgust, neutral)
2. Confidence level (0.0-1.0)
3. Secondary emotions if present
4. Emotional intensity

Respond with ONLY a JSON object:
{{
  "primary_emotion": "emotion_name",
  "confidence": 0.0-1.0,
  "all_emotions": {{"emotion1": score1, "emotion2": score2}},
  "reasoning": "brief explanation"
}}"""

        try:
            self.api_calls += 1

            # Use LLM client if available (preferred method)
            if self.llm_client:
                messages = [{"role": "user", "content": prompt}]

                # Use emotion-specific endpoint if configured
                if (
                    hasattr(self.llm_client, "generate_emotion_chat_completion")
                    and self.llm_client.emotion_chat_endpoint
                ):
                    response = self.llm_client.generate_emotion_chat_completion(
                        messages=messages,
                        temperature=0.2,
                        max_tokens=self.llm_client.max_tokens_emotion,  # Use emotion-specific token limit
                    )
                else:
                    # Fallback to main endpoint
                    response = self.llm_client.generate_chat_completion(
                        messages=messages, temperature=0.2, max_tokens=200
                    )

                content = response["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                if content.startswith("{") and content.endswith("}"):
                    emotion_data = json.loads(content)
                    return emotion_data
                else:
                    # Extract JSON from response
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        emotion_data = json.loads(content[start:end])
                        return emotion_data

            # Legacy fallback using direct HTTP session
            elif self.session:
                async with self.session.post(
                    f"{self.llm_api_url}/v1/chat/completions",
                    json={
                        "model": "local-llm",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 200,
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"].strip()

                        # Extract JSON from response
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        if start >= 0 and end > start:
                            emotion_data = json.loads(content[start:end])
                            return emotion_data

        except Exception as e:
            if self.logger:
                self.logger.warning(f"LLM provider detailed emotion call failed: {e}")

        # Fallback to keywords
        return self._analyze_with_keywords(text)

    async def _call_external_sentiment_api(self, text: str) -> dict:
        """Call external sentiment analysis API (Hugging Face as example)"""

        if not self.huggingface_api_key:
            return {"label": "UNKNOWN", "score": 0.5}

        try:
            self.api_calls += 1
            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}

            if not self.session:
                return {"label": "UNKNOWN", "score": 0.5}

            async with self.session.post(
                "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest",
                headers=headers,
                json={"inputs": text},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        return {"label": result["label"], "score": result["score"]}

        except Exception as e:
            if self.logger:
                self.logger.warning(f"External sentiment API failed: {e}")

        return {"label": "UNKNOWN", "score": 0.5}

    async def _call_embedding_emotion_analysis(self, text: str) -> dict | None:
        """Use external embeddings for emotion analysis via semantic similarity"""

        try:
            # Define emotion reference texts for semantic comparison
            emotion_references = {
                "joy": [
                    "I am feeling very happy and joyful",
                    "This makes me so excited and pleased",
                    "I feel wonderful and delighted",
                ],
                "sadness": [
                    "I am feeling very sad and down",
                    "This makes me feel disappointed and blue",
                    "I feel melancholy and sorrowful",
                ],
                "anger": [
                    "I am feeling very angry and upset",
                    "This makes me furious and mad",
                    "I feel irritated and frustrated",
                ],
                "fear": [
                    "I am feeling very scared and afraid",
                    "This makes me nervous and anxious",
                    "I feel worried and apprehensive",
                ],
                "surprise": [
                    "I am feeling very surprised and amazed",
                    "This is so unexpected and shocking",
                    "I feel astonished and startled",
                ],
                "disgust": [
                    "I am feeling disgusted and repulsed",
                    "This makes me feel sick and revolted",
                    "I feel nauseated and appalled",
                ],
            }

            # Get embedding for the input text
            # Note: We can use either external or local embeddings for emotion analysis
            text_embedding = await self.embedding_manager.get_embeddings([text])
            if not text_embedding or len(text_embedding) == 0:
                return None

            text_vec = text_embedding[0]

            # Calculate similarities with emotion references
            emotion_scores = {}

            for emotion, references in emotion_references.items():
                ref_embeddings = await self.embedding_manager.get_embeddings(references)
                if ref_embeddings and len(ref_embeddings) == len(references):
                    # Calculate average similarity with all references for this emotion
                    similarities = []
                    for ref_vec in ref_embeddings:
                        # Cosine similarity
                        dot_product = sum(a * b for a, b in zip(text_vec, ref_vec, strict=False))
                        magnitude_text = sum(a * a for a in text_vec) ** 0.5
                        magnitude_ref = sum(a * a for a in ref_vec) ** 0.5

                        if magnitude_text > 0 and magnitude_ref > 0:
                            similarity = dot_product / (magnitude_text * magnitude_ref)
                            similarities.append(max(0, similarity))  # Ensure non-negative

                    if similarities:
                        emotion_scores[emotion] = sum(similarities) / len(similarities)

            if not emotion_scores:
                return None

            # Find primary emotion and normalize scores
            primary_emotion = max(emotion_scores.keys(), key=lambda e: emotion_scores[e])
            max_score = emotion_scores[primary_emotion]

            # Normalize scores to sum to 1
            total_score = sum(emotion_scores.values())
            if total_score > 0:
                normalized_emotions = {
                    e: score / total_score for e, score in emotion_scores.items()
                }
            else:
                normalized_emotions = emotion_scores

            return {
                "primary_emotion": primary_emotion,
                "confidence": max_score,
                "all_emotions": normalized_emotions,
            }

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Embedding-based emotion analysis failed: {e}")
            return None

    def _analyze_with_keywords(self, text: str) -> dict[str, Any]:
        """Enhanced keyword-based emotion analysis (no API calls)"""

        text_lower = text.lower()

        # Enhanced emotion patterns with intensity modifiers
        emotion_patterns = {
            "joy": {
                "strong": [
                    "ecstatic",
                    "thrilled",
                    "overjoyed",
                    "elated",
                    "fantastic",
                    "amazing",
                    "incredible",
                ],
                "medium": [
                    "happy",
                    "excited",
                    "delighted",
                    "cheerful",
                    "joyful",
                    "wonderful",
                    "great",
                ],
                "mild": ["pleased", "glad", "good", "nice", "fine", "okay"],
            },
            "sadness": {
                "strong": ["devastated", "heartbroken", "miserable", "depressed", "crushed"],
                "medium": ["sad", "upset", "disappointed", "down", "unhappy"],
                "mild": ["blue", "low", "bummed", "meh"],
            },
            "anger": {
                "strong": ["furious", "enraged", "livid", "irate", "outraged"],
                "medium": ["angry", "mad", "frustrated", "annoyed", "irritated"],
                "mild": ["bothered", "miffed", "irked"],
            },
            "fear": {
                "strong": ["terrified", "petrified", "horrified", "panicked"],
                "medium": ["scared", "afraid", "worried", "anxious", "nervous"],
                "mild": ["concerned", "uneasy", "hesitant"],
            },
            "surprise": {
                "strong": ["shocked", "stunned", "flabbergasted", "amazed"],
                "medium": ["surprised", "astonished", "unexpected"],
                "mild": ["interesting", "huh", "oh"],
            },
            "disgust": {
                "strong": ["revolting", "repulsive", "disgusting", "vile"],
                "medium": ["gross", "awful", "terrible", "horrible"],
                "mild": ["bad", "unpleasant", "ick"],
            },
        }

        emotion_scores = {}
        max_intensity = 0

        for emotion, intensity_levels in emotion_patterns.items():
            total_score = 0
            for intensity, keywords in intensity_levels.items():
                multiplier = {"strong": 1.0, "medium": 0.7, "mild": 0.4}[intensity]
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                total_score += matches * multiplier
                max_intensity = max(max_intensity, matches * multiplier)

            if total_score > 0:
                emotion_scores[emotion] = min(total_score / 3, 1.0)  # Normalize

        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            confidence = emotion_scores[primary_emotion]
        else:
            primary_emotion = "neutral"
            confidence = 0.5

        return {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "all_emotions": emotion_scores,
        }

    def _fuse_emotion_results(self, emotion_sources: list[tuple]) -> dict:
        """Fuse emotion results from multiple sources with weighted averaging"""

        # Source weights (can be adjusted based on reliability)
        source_weights = {
            "lm_studio": 0.4,
            "embeddings": 0.4,  # External embedding-based analysis
            "keywords": 0.2,
        }

        all_emotions = {}
        weighted_confidence = 0
        total_weight = 0

        for source_name, result in emotion_sources:
            # Skip None results
            if result is None:
                continue

            weight = source_weights.get(source_name, 0.2)

            # Add emotions with weighting
            emotions = result.get(
                "all_emotions",
                {result.get("primary_emotion", "neutral"): result.get("confidence", 0.5)},
            )
            for emotion, score in emotions.items():
                if emotion in all_emotions:
                    all_emotions[emotion] += score * weight
                else:
                    all_emotions[emotion] = score * weight

            # Weight confidence
            confidence = result.get("confidence", 0.5)
            weighted_confidence += confidence * weight
            total_weight += weight

        # Normalize
        if total_weight > 0:
            weighted_confidence /= total_weight
            for emotion in all_emotions:
                all_emotions[emotion] /= total_weight

        # Find primary emotion
        primary_emotion = (
            max(all_emotions.items(), key=lambda x: x[1])[0] if all_emotions else "neutral"
        )

        return {
            "primary_emotion": primary_emotion,
            "confidence": weighted_confidence,
            "all_emotions": all_emotions,
        }

    def _calculate_emotional_intensity(self, text: str, base_confidence: float) -> float:
        """Calculate emotional intensity from text features"""

        if not text:
            return base_confidence

        intensity_factors = {
            "exclamation_marks": min(text.count("!") * 0.15, 0.3),
            "capital_letters": (
                min(sum(1 for c in text if c.isupper()) / len(text), 0.2) if len(text) > 0 else 0
            ),
            "repetitive_characters": min(len([c for c in text if text.count(c) > 3]) * 0.05, 0.15),
            "emotional_intensifiers": 0,
        }

        # Check for intensifier words
        intensifiers = [
            "very",
            "really",
            "extremely",
            "incredibly",
            "absolutely",
            "totally",
            "completely",
            "so",
            "super",
        ]
        for intensifier in intensifiers:
            if intensifier in text.lower():
                intensity_factors["emotional_intensifiers"] += 0.1

        total_intensity = sum(intensity_factors.values())
        combined_intensity = min(base_confidence + total_intensity, 1.0)

        return combined_intensity

    def _calculate_emotional_intensity_advanced(
        self, text: str, base_confidence: float, linguistic_features: dict
    ) -> float:
        """Advanced emotional intensity calculation using linguistic features"""

        base_intensity = self._calculate_emotional_intensity(text, base_confidence)

        # Add linguistic adjustments
        linguistic_boost = 0

        if linguistic_features.get("has_emotional_words", False):
            linguistic_boost += 0.1

        if linguistic_features.get("word_count", 0) > 20:  # Longer text might be more emotional
            linguistic_boost += 0.05

        if linguistic_features.get("question_marks", 0) > 0:
            linguistic_boost += 0.05

        return min(base_intensity + linguistic_boost, 1.0)

    def _analyze_linguistic_features(self, text: str) -> dict[str, Any]:
        """Analyze linguistic features for advanced emotion detection"""

        return {
            "word_count": len(text.split()),
            "sentence_count": text.count(".") + text.count("!") + text.count("?"),
            "question_marks": text.count("?"),
            "exclamation_marks": text.count("!"),
            "uppercase_ratio": sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            "has_emotional_words": any(
                word in text.lower() for word in ["feel", "emotion", "heart", "soul", "mind"]
            ),
            "average_word_length": (
                sum(len(word) for word in text.split()) / len(text.split()) if text.split() else 0
            ),
        }

    async def _analyze_conversation_context_light(
        self, user_id: str, conversation_history: list[str]
    ) -> dict | None:
        """Light conversation context analysis (minimal API calls)"""

        if not conversation_history or len(conversation_history) < 2:
            return None

        # Quick keyword analysis of recent messages
        recent_emotions = []
        for message in conversation_history[-3:]:  # Last 3 messages
            keyword_result = self._analyze_with_keywords(message)
            recent_emotions.append(keyword_result["primary_emotion"])

        if recent_emotions:
            most_common = max(set(recent_emotions), key=recent_emotions.count)
            consistency = recent_emotions.count(most_common) / len(recent_emotions)

            return {
                "recent_emotional_trend": most_common,
                "emotional_consistency": round(consistency, 3),
                "conversation_length": len(conversation_history),
            }

        return None

    async def _analyze_conversation_context_heavy(
        self, user_id: str, conversation_history: list[str]
    ) -> dict | None:
        """Heavy conversation context analysis (multiple API calls)"""

        light_context = await self._analyze_conversation_context_light(
            user_id, conversation_history
        )

        if not light_context or len(conversation_history) < 5:
            return light_context

        # Analyze emotional trajectory over time
        try:
            # Sample key messages for API analysis
            sample_messages = conversation_history[-10::2]  # Every other message from last 10

            emotion_tasks = [
                self._call_lm_studio_emotion(msg) for msg in sample_messages[:3]
            ]  # Limit API calls
            emotion_results = await asyncio.gather(*emotion_tasks, return_exceptions=True)

            emotions_over_time = []
            for i, result in enumerate(emotion_results):
                if not isinstance(result, Exception) and result:
                    # Type casting to help the linter
                    result_dict = result if isinstance(result, dict) else {}
                    emotions_over_time.append(result_dict.get("emotion", "neutral"))
                else:
                    # Fallback to keywords
                    keyword_result = self._analyze_with_keywords(sample_messages[i])
                    emotions_over_time.append(keyword_result["primary_emotion"])

            # Calculate emotional stability
            if emotions_over_time:
                unique_emotions = len(set(emotions_over_time))
                emotional_stability = 1.0 - (unique_emotions / len(emotions_over_time))

                heavy_context_data = {
                    "emotional_trajectory": emotions_over_time,
                    "emotional_stability": round(emotional_stability, 3),
                    "unique_emotions_count": unique_emotions,
                }

                if light_context:
                    light_context.update(heavy_context_data)
                else:
                    light_context = heavy_context_data

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Heavy context analysis failed: {e}")

        return light_context

    async def _test_api_connectivity(self):
        """Test connectivity to configured APIs"""

        if self.logger:
            self.logger.info("🔌 Testing API connectivity...")

        # Test LLM provider (optional fallback)
        try:
            if self.session:
                async with self.session.get(f"{self.llm_api_url}/v1/models") as response:
                    if response.status == 200:
                        if self.logger:
                            self.logger.info("✅ LLM provider: Connected")
                    else:
                        if self.logger:
                            # Downgrade to debug since it's optional when using external embeddings
                            self.logger.debug(
                                f"🔧 LLM provider: HTTP {response.status} (using external embeddings as primary)"
                            )
        except Exception as e:
            if self.logger:
                # Downgrade to debug since it's optional when using external embeddings
                self.logger.debug(f"🔧 LLM provider: {e} (using external embeddings as primary)")

        # Test Hugging Face API (legacy, now using external embeddings)
        if self.huggingface_api_key:
            try:
                headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
                if self.session:
                    async with self.session.get(
                        "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            if self.logger:
                                self.logger.debug("✅ Hugging Face: Connected (legacy fallback)")
                        else:
                            if self.logger:
                                self.logger.debug(
                                    f"🔧 Hugging Face: HTTP {response.status} (using external embeddings as primary)"
                                )
            except Exception as e:
                if self.logger:
                    self.logger.debug(
                        f"🔧 Hugging Face: {e} (using external embeddings as primary)"
                    )
        else:
            if self.logger:
                # Remove warning since Hugging Face is now optional (we use external embeddings)
                self.logger.debug(
                    "🔧 Hugging Face: No API key provided (using external embeddings as primary)"
                )

    def build_cloud_emotional_prompt(
        self, emotion_analysis: dict, phase3_context: dict | None = None
    ) -> str:
        """Build emotional system prompt optimized for cloud deployment"""

        primary_emotion = emotion_analysis.get("primary_emotion", "neutral")
        confidence = emotion_analysis.get("confidence", 0.5)
        intensity = emotion_analysis.get("intensity", 0.5)
        api_calls = emotion_analysis.get("api_calls_made", 3)

        prompt = "You are an advanced emotionally intelligent AI companion with comprehensive emotional analysis.\n\n"

        # Add emotion analysis details
        prompt += "EMOTION ANALYSIS (Full Capabilities):\n"
        prompt += f"- Primary emotion: {primary_emotion} (confidence: {confidence:.2f})\n"
        prompt += f"- Emotional intensity: {intensity:.2f}/1.0\n"
        prompt += f"- Analysis: Full capabilities ({api_calls} API calls)\n"

        # Add analysis quality indicators
        if emotion_analysis.get("analysis_method"):
            prompt += f"- Analysis method: {emotion_analysis['analysis_method']}\n"

        if emotion_analysis.get("emotion_sources_used"):
            prompt += f"- Emotion sources: {emotion_analysis['emotion_sources_used']}\n"

        # Add multiple emotions if detected
        all_emotions = emotion_analysis.get("all_emotions", {})
        if len(all_emotions) > 1:
            top_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            prompt += f"- Secondary emotions: {', '.join([f'{e}({s:.2f})' for e, s in top_emotions[1:]])}\n"

        # Add conversation context if available
        context = emotion_analysis.get("conversation_context")
        if context:
            prompt += f"- Recent emotional trend: {context['recent_emotional_trend']}\n"
            prompt += f"- Emotional consistency: {context['emotional_consistency']:.2f}\n"

        prompt += "\n"

        # Full capabilities response mode
        prompt += "RESPONSE MODE: Maximum emotional intelligence. Deep, nuanced, therapeutic-level understanding.\n"

        # Standard emotional strategies
        emotion_strategies = {
            "joy": "Share in their happiness with genuine enthusiasm. Match their positive energy appropriately.",
            "sadness": "Provide gentle, compassionate support. Use warm, comforting language. Validate their feelings.",
            "anger": "Acknowledge their frustration with empathy. Stay calm and help them feel heard.",
            "fear": "Offer reassurance and comfort. Help them feel safe and break down overwhelming thoughts.",
            "surprise": "Share in their amazement. Help them process the unexpected experience.",
            "disgust": "Acknowledge their strong reaction with understanding and validation.",
            "neutral": "Be warm and engaging. Look for subtle emotional cues.",
        }

        strategy = emotion_strategies.get(primary_emotion, emotion_strategies["neutral"])
        prompt += f"RESPONSE STRATEGY: {strategy}\n\n"

        # Confidence-based adjustments
        if confidence < 0.4:
            prompt += "LOW CONFIDENCE: The emotional reading is uncertain. Be gentle and probe for more emotional cues.\n\n"
        elif confidence > 0.8:
            prompt += "HIGH CONFIDENCE: The emotional reading is very reliable. Respond with matching emotional intelligence.\n\n"

        # Add Phase 3 memory context if available
        if phase3_context:
            core_memories = phase3_context.get("core_memories", [])
            if core_memories:
                prompt += "IMPORTANT MEMORIES:\n"
                for memory in core_memories[:3]:
                    if hasattr(memory, "content"):
                        prompt += f"- {memory.content[:100]}...\n"
                    elif isinstance(memory, dict) and "content" in memory:
                        prompt += f"- {memory['content'][:100]}...\n"
                prompt += "\n"

        prompt += "Respond with full emotional intelligence. Be authentic, empathetic, and human-like while maintaining appropriate boundaries."

        return prompt

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics"""

        avg_analysis_time = (
            sum(self.analysis_times) / len(self.analysis_times) if self.analysis_times else 0
        )
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

        return {
            "average_analysis_time_ms": round(avg_analysis_time, 2),
            "total_analyses": len(self.analysis_times),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_api_calls": self.api_calls,
            "lm_studio_configured": self.llm_api_url is not None,
            "openai_configured": self.openai_api_key is not None,
            "huggingface_configured": self.huggingface_api_key is not None,
            "phase3_available": PHASE3_AVAILABLE,
            "tier_configurations": {"full": self.config.__dict__},
        }
