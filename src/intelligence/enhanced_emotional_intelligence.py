"""
Enhanced Emotional Intelligence Engine with Industry-Standard Libraries

This module enhances our emotional intelligence system using scikit-learn, SciPy,
and VADER for better performance, accuracy, and real-time processing.

Key Enhancements:
- VADER sentiment analysis for real-time emotional processing
- scikit-learn clustering for emotional pattern recognition
- SciPy statistical analysis for emotional trend detection
- pandas for efficient emotional data manipulation
- Optimized performance with vectorized operations

Integration with existing systems maintained for backward compatibility.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

# Enhanced libraries for better performance
try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - using basic emotional analysis")

try:
    from scipy import stats
    from scipy.signal import find_peaks
    from scipy.spatial.distance import cosine

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available - using basic statistical analysis")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("VADER sentiment analysis not available")

# Import existing systems for integration
try:
    from src.intelligence.emotional_context_engine import (
        EmotionalContext,
        EmotionalContextEngine,
        EmotionalPattern,
        EmotionalState,
        EmotionalTrigger,
    )

    EXISTING_EMOTIONAL_ENGINE_AVAILABLE = True
except ImportError:
    EXISTING_EMOTIONAL_ENGINE_AVAILABLE = False

try:
    from src.emotion.external_api_emotion_ai import ExternalAPIEmotionAI

    EXTERNAL_EMOTION_AI_AVAILABLE = True
except ImportError:
    EXTERNAL_EMOTION_AI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EnhancedEmotionalAnalysis:
    """Enhanced emotional analysis results with confidence metrics"""

    primary_emotion: str
    emotion_scores: dict[str, float]  # All emotion probabilities
    sentiment_scores: dict[str, float]  # VADER sentiment breakdown
    confidence: float  # Overall confidence in analysis
    emotional_intensity: float  # How intense the emotion is
    emotional_stability: float  # How stable emotions are over time
    processing_time_ms: float  # Performance metric


class EnhancedEmotionalIntelligence:
    """
    Enhanced emotional intelligence engine using industry-standard libraries
    for better performance, accuracy, and scalability.
    """

    def __init__(self, user_id: str, retention_days: int = 90):
        self.user_id = user_id
        self.retention_days = retention_days
        self.logger = logging.getLogger(f"{__name__}.{user_id}")

        # Initialize enhanced components
        self.vader_analyzer = None
        self.emotion_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.emotion_clusterer = None

        # Data storage using pandas for efficiency
        self.emotion_history = (
            pd.DataFrame(
                columns=[
                    "timestamp",
                    "message",
                    "primary_emotion",
                    "emotion_scores",
                    "sentiment_scores",
                    "confidence",
                    "intensity",
                    "context",
                ]
            )
            if pd
            else None
        )

        # Initialize components
        self._initialize_enhanced_components()

        # Backward compatibility with existing system
        self.existing_engine = None
        if EXISTING_EMOTIONAL_ENGINE_AVAILABLE:
            try:
                self.existing_engine = EmotionalContextEngine(user_id, retention_days)
                self.logger.info("✅ Integrated with existing emotional engine")
            except Exception as e:
                self.logger.warning(f"Could not initialize existing engine: {e}")

    def _initialize_enhanced_components(self):
        """Initialize enhanced AI/ML components"""
        try:
            # Initialize VADER for real-time sentiment analysis
            if VADER_AVAILABLE:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.logger.info("✅ VADER sentiment analyzer initialized")

            # Initialize clustering for pattern recognition
            if SKLEARN_AVAILABLE:
                self.emotion_clusterer = DBSCAN(eps=0.3, min_samples=2)
                self.logger.info("✅ Emotion clustering initialized")

            self.logger.info("🚀 Enhanced emotional intelligence components ready")

        except Exception as e:
            self.logger.error(f"❌ Enhanced component initialization failed: {e}")

    async def analyze_emotion_enhanced(
        self, message: str, context: dict[str, Any] | None = None
    ) -> EnhancedEmotionalAnalysis:
        """
        Perform enhanced emotional analysis using multiple AI libraries
        for improved accuracy and performance.
        """
        start_time = datetime.now()

        try:
            # Phase 1: Fast sentiment analysis with VADER
            sentiment_scores = {}
            if self.vader_analyzer:
                vader_scores = self.vader_analyzer.polarity_scores(message)
                sentiment_scores = {
                    "positive": vader_scores["pos"],
                    "negative": vader_scores["neg"],
                    "neutral": vader_scores["neu"],
                    "compound": vader_scores["compound"],
                }

            # Phase 2: Detailed emotion analysis (existing system or enhanced)
            emotion_scores = {}
            primary_emotion = "neutral"
            base_confidence = 0.5

            if self.existing_engine and EXISTING_EMOTIONAL_ENGINE_AVAILABLE:
                # Use existing system for detailed emotion analysis
                try:
                    existing_result = await self.existing_engine.analyze_emotional_context(
                        message, context or {}
                    )
                    primary_emotion = existing_result.primary_emotion.value
                    base_confidence = existing_result.confidence
                    # Convert to emotion scores format
                    emotion_scores = {primary_emotion: base_confidence}
                except Exception as e:
                    self.logger.warning(f"Existing engine analysis failed: {e}")

            # Phase 3: Enhanced analysis with ML libraries
            emotional_intensity = self._calculate_emotional_intensity(
                message, sentiment_scores, emotion_scores
            )

            emotional_stability = await self._calculate_emotional_stability()

            # Phase 4: Confidence calculation using multiple signals
            final_confidence = self._calculate_enhanced_confidence(
                sentiment_scores, emotion_scores, base_confidence
            )

            # Performance measurement
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create enhanced analysis result
            analysis = EnhancedEmotionalAnalysis(
                primary_emotion=primary_emotion,
                emotion_scores=emotion_scores,
                sentiment_scores=sentiment_scores,
                confidence=final_confidence,
                emotional_intensity=emotional_intensity,
                emotional_stability=emotional_stability,
                processing_time_ms=processing_time,
            )

            # Store in pandas DataFrame for efficient analysis
            await self._store_emotion_data(message, analysis, context)

            self.logger.info(
                f"🧠 Enhanced emotion analysis: {primary_emotion} "
                f"(confidence: {final_confidence:.2f}, "
                f"intensity: {emotional_intensity:.2f}, "
                f"time: {processing_time:.1f}ms)"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"❌ Enhanced emotion analysis failed: {e}")
            # Fallback to basic analysis
            return EnhancedEmotionalAnalysis(
                primary_emotion="neutral",
                emotion_scores={"neutral": 0.5},
                sentiment_scores={},
                confidence=0.3,
                emotional_intensity=0.5,
                emotional_stability=0.5,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    def _calculate_emotional_intensity(
        self, message: str, sentiment_scores: dict[str, float], emotion_scores: dict[str, float]
    ) -> float:
        """Calculate emotional intensity using multiple signals"""
        try:
            # Use VADER compound score as base intensity
            base_intensity = abs(sentiment_scores.get("compound", 0.0))

            # Enhance with message characteristics
            message_length = len(message)
            exclamation_count = message.count("!")
            caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)

            # Combine signals
            intensity_factors = [
                base_intensity,
                min(exclamation_count * 0.2, 0.4),  # Max 0.4 boost from exclamations
                min(caps_ratio * 0.3, 0.3),  # Max 0.3 boost from caps
                min(message_length / 1000, 0.2),  # Max 0.2 boost from length
            ]

            final_intensity = np.clip(np.mean(intensity_factors), 0.0, 1.0)
            return float(final_intensity)

        except Exception as e:
            self.logger.warning(f"Intensity calculation failed: {e}")
            return 0.5

    async def _calculate_emotional_stability(self) -> float:
        """Calculate emotional stability using SciPy statistical analysis"""
        try:
            if not SCIPY_AVAILABLE or self.emotion_history is None or len(self.emotion_history) < 3:
                return 0.5  # Default stability

            # Get recent emotion intensities
            recent_data = self.emotion_history.tail(10)
            if "intensity" not in recent_data.columns:
                return 0.5

            intensities = recent_data["intensity"].values

            # Calculate stability using coefficient of variation
            if len(intensities) > 1:
                stability = 1.0 - (np.std(intensities) / (np.mean(intensities) + 0.01))
                return float(np.clip(stability, 0.0, 1.0))

            return 0.5

        except Exception as e:
            self.logger.warning(f"Stability calculation failed: {e}")
            return 0.5

    def _calculate_enhanced_confidence(
        self,
        sentiment_scores: dict[str, float],
        emotion_scores: dict[str, float],
        base_confidence: float,
    ) -> float:
        """Calculate confidence using multiple signals"""
        try:
            confidence_factors = [base_confidence]

            # VADER confidence (higher absolute compound = higher confidence)
            if sentiment_scores.get("compound"):
                vader_confidence = abs(sentiment_scores["compound"])
                confidence_factors.append(vader_confidence)

            # Emotion score confidence (higher max score = higher confidence)
            if emotion_scores:
                max_emotion_score = max(emotion_scores.values())
                confidence_factors.append(max_emotion_score)

            # Average confidence from all sources
            final_confidence = np.mean(confidence_factors)
            return float(np.clip(final_confidence, 0.0, 1.0))

        except Exception as e:
            self.logger.warning(f"Confidence calculation failed: {e}")
            return base_confidence

    async def _store_emotion_data(
        self, message: str, analysis: EnhancedEmotionalAnalysis, context: dict[str, Any] | None
    ):
        """Store emotion data efficiently using pandas"""
        try:
            if self.emotion_history is None:
                return

            # Create new row
            new_row = pd.DataFrame(
                [
                    {
                        "timestamp": datetime.now(),
                        "message": message[:200],  # Truncate for storage efficiency
                        "primary_emotion": analysis.primary_emotion,
                        "emotion_scores": analysis.emotion_scores,
                        "sentiment_scores": analysis.sentiment_scores,
                        "confidence": analysis.confidence,
                        "intensity": analysis.emotional_intensity,
                        "context": str(context) if context else None,
                    }
                ]
            )

            # Append to history
            self.emotion_history = pd.concat([self.emotion_history, new_row], ignore_index=True)

            # Cleanup old data
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            self.emotion_history = self.emotion_history[
                self.emotion_history["timestamp"] > cutoff_date
            ]

        except Exception as e:
            self.logger.warning(f"Emotion data storage failed: {e}")

    async def get_emotional_patterns_enhanced(self) -> dict[str, Any]:
        """
        Analyze emotional patterns using advanced ML clustering
        and statistical analysis.
        """
        try:
            if self.emotion_history is None or len(self.emotion_history) < 5:
                return {"patterns": [], "insights": "Insufficient data for pattern analysis"}

            patterns = {}

            # Use scikit-learn clustering for pattern recognition
            if SKLEARN_AVAILABLE:
                patterns.update(await self._analyze_emotional_clusters())

            # Use SciPy for statistical trend analysis
            if SCIPY_AVAILABLE:
                patterns.update(await self._analyze_emotional_trends())

            # Use pandas for efficient data analysis
            if pd:
                patterns.update(await self._analyze_emotional_statistics())

            return patterns

        except Exception as e:
            self.logger.error(f"❌ Enhanced pattern analysis failed: {e}")
            return {"error": str(e)}

    async def _analyze_emotional_clusters(self) -> dict[str, Any]:
        """Use scikit-learn to identify emotional patterns"""
        try:
            # Prepare feature vectors for clustering
            features = []
            for _, row in self.emotion_history.iterrows():
                if row["sentiment_scores"]:
                    features.append(
                        [
                            row["sentiment_scores"].get("positive", 0),
                            row["sentiment_scores"].get("negative", 0),
                            row["sentiment_scores"].get("neutral", 0),
                            row["intensity"],
                        ]
                    )

            if len(features) < 3:
                return {"clusters": "Insufficient data for clustering"}

            # Standardize features
            features_scaled = self.emotion_scaler.fit_transform(features)

            # Perform clustering
            clusters = self.emotion_clusterer.fit_predict(features_scaled)

            # Analyze clusters
            unique_clusters = set(clusters)
            cluster_analysis = {}

            for cluster_id in unique_clusters:
                if cluster_id == -1:  # Noise points in DBSCAN
                    continue

                cluster_mask = clusters == cluster_id
                cluster_data = self.emotion_history[cluster_mask]

                cluster_analysis[f"cluster_{cluster_id}"] = {
                    "size": len(cluster_data),
                    "avg_intensity": cluster_data["intensity"].mean(),
                    "dominant_emotions": cluster_data["primary_emotion"]
                    .value_counts()
                    .head(3)
                    .to_dict(),
                    "time_pattern": self._analyze_temporal_pattern(cluster_data),
                }

            return {"emotional_clusters": cluster_analysis}

        except Exception as e:
            self.logger.warning(f"Clustering analysis failed: {e}")
            return {"clusters": "Clustering analysis unavailable"}

    async def _analyze_emotional_trends(self) -> dict[str, Any]:
        """Use SciPy for trend analysis"""
        try:
            # Analyze intensity trends over time
            intensities = self.emotion_history["intensity"].values
            pd.to_datetime(self.emotion_history["timestamp"]).values

            # Calculate trend using linear regression
            time_numeric = np.arange(len(intensities))
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                time_numeric, intensities
            )

            # Find peaks and valleys in emotional intensity
            peaks, _ = find_peaks(intensities, height=0.7)
            valleys, _ = find_peaks(-intensities, height=-0.3)

            return {
                "emotional_trends": {
                    "overall_trend": (
                        "increasing"
                        if slope > 0.01
                        else "decreasing" if slope < -0.01 else "stable"
                    ),
                    "trend_strength": abs(slope),
                    "correlation_coefficient": r_value,
                    "statistical_significance": p_value,
                    "emotional_peaks": len(peaks),
                    "emotional_valleys": len(valleys),
                    "volatility": np.std(intensities),
                }
            }

        except Exception as e:
            self.logger.warning(f"Trend analysis failed: {e}")
            return {"trends": "Trend analysis unavailable"}

    async def _analyze_emotional_statistics(self) -> dict[str, Any]:
        """Use pandas for efficient statistical analysis"""
        try:
            stats_analysis = {
                "basic_statistics": {
                    "total_interactions": len(self.emotion_history),
                    "avg_confidence": self.emotion_history["confidence"].mean(),
                    "avg_intensity": self.emotion_history["intensity"].mean(),
                    "most_common_emotion": (
                        self.emotion_history["primary_emotion"].mode().iloc[0]
                        if len(self.emotion_history) > 0
                        else "unknown"
                    ),
                },
                "temporal_patterns": {
                    "interactions_per_day": len(self.emotion_history) / max(self.retention_days, 1),
                    "recent_activity": len(
                        self.emotion_history[
                            self.emotion_history["timestamp"] > datetime.now() - timedelta(days=7)
                        ]
                    ),
                },
            }

            return {"emotional_statistics": stats_analysis}

        except Exception as e:
            self.logger.warning(f"Statistical analysis failed: {e}")
            return {"statistics": "Statistical analysis unavailable"}

    def _analyze_temporal_pattern(self, cluster_data: pd.DataFrame) -> str:
        """Analyze when certain emotional patterns occur"""
        try:
            if len(cluster_data) < 2:
                return "insufficient_data"

            # Analyze time distribution
            hours = pd.to_datetime(cluster_data["timestamp"]).dt.hour
            hour_distribution = hours.value_counts()

            # Find peak hour
            peak_hour = hour_distribution.idxmax()

            if 6 <= peak_hour <= 12:
                return "morning_pattern"
            elif 12 <= peak_hour <= 18:
                return "afternoon_pattern"
            elif 18 <= peak_hour <= 22:
                return "evening_pattern"
            else:
                return "night_pattern"

        except Exception:
            return "unknown_pattern"


# Factory function for easy initialization
def create_enhanced_emotional_intelligence(
    user_id: str, retention_days: int = 90
) -> EnhancedEmotionalIntelligence:
    """Create enhanced emotional intelligence engine with optimizations"""
    return EnhancedEmotionalIntelligence(user_id, retention_days)
