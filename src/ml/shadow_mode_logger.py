"""
ML Shadow Mode Logger - InfluxDB Integration

Logs ML model predictions to InfluxDB for analysis without affecting bot behavior.
Feature-flagged (ENABLE_ML_SHADOW_MODE=false by default) to avoid loading ML
dependencies for end users who aren't training models.

Shadow Mode Purpose:
- Compare ML predictions vs actual outcomes
- Track prediction confidence distribution
- Analyze when ML recommendations differ from keyword-based mode selection
- Build confidence before deploying hybrid/ML-first modes
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Feature flag: Default to FALSE for end users
ENABLE_ML_SHADOW_MODE = os.getenv("ENABLE_ML_SHADOW_MODE", "false").lower() == "true"

# Only import ML dependencies if shadow mode is enabled
if ENABLE_ML_SHADOW_MODE:
    try:
        from influxdb_client import Point
        INFLUXDB_AVAILABLE = True
    except ImportError:
        INFLUXDB_AVAILABLE = False
        Point = None
        logger.warning(
            "ML Shadow Mode enabled but InfluxDB client not available. "
            "Install with: pip install influxdb-client"
        )
else:
    INFLUXDB_AVAILABLE = False
    Point = None


@dataclass
class MLPredictionLog:
    """Single ML prediction log entry"""
    user_id: str
    bot_name: str
    predicted_effective: bool
    confidence: float
    recommended_modes: List[str]
    current_mode: Optional[str] = None
    engagement_score: Optional[float] = None
    satisfaction_score: Optional[float] = None
    message_count: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class MLShadowModeLogger:
    """
    Logs ML model predictions to InfluxDB for shadow mode analysis.
    
    Shadow mode means:
    - ML predictions are logged but NOT used to change bot behavior
    - Allows comparison of ML recommendations vs actual mode selection
    - Builds confidence in ML system before production deployment
    
    Usage:
        if ENABLE_ML_SHADOW_MODE:
            logger = MLShadowModeLogger(influxdb_client)
            await logger.log_prediction(prediction, user_id, bot_name, current_mode)
    """
    
    def __init__(self, influxdb_client=None):
        """
        Initialize shadow mode logger.
        
        Args:
            influxdb_client: InfluxDB client for writing predictions (optional)
                           Can be either a raw InfluxDBClient or TemporalIntelligenceClient
        """
        # Handle both TemporalIntelligenceClient wrapper and raw InfluxDBClient
        if influxdb_client and hasattr(influxdb_client, 'client'):
            # It's a TemporalIntelligenceClient, extract the raw client
            self.influxdb_client = influxdb_client.client
        else:
            # It's a raw InfluxDBClient or None
            self.influxdb_client = influxdb_client
        
        self.enabled = ENABLE_ML_SHADOW_MODE and INFLUXDB_AVAILABLE and self.influxdb_client is not None
        
        if ENABLE_ML_SHADOW_MODE and not self.enabled:
            if not INFLUXDB_AVAILABLE:
                logger.warning("ML Shadow Mode: InfluxDB client not available")
            elif influxdb_client is None:
                logger.warning("ML Shadow Mode: No InfluxDB client provided")
        
        if self.enabled:
            logger.info("✅ ML Shadow Mode ENABLED - Predictions will be logged to InfluxDB")
        else:
            logger.debug("ML Shadow Mode DISABLED (ENABLE_ML_SHADOW_MODE=false)")
    
    async def log_prediction(
        self,
        prediction,  # StrategyPrediction from response_strategy_predictor
        user_id: str,
        bot_name: str,
        current_mode: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log ML prediction to InfluxDB.
        
        Args:
            prediction: StrategyPrediction object from predictor
            user_id: Discord user ID
            bot_name: Character bot name
            current_mode: Current CDL mode being used (for comparison)
            additional_context: Optional extra fields to log
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Create InfluxDB point
            point = Point("ml_predictions") \
                .tag("user_id", user_id) \
                .tag("bot", bot_name) \
                .tag("predicted_effective", str(prediction.is_effective).lower()) \
                .tag("current_mode", current_mode or "unknown") \
                .field("confidence", float(prediction.confidence)) \
                .field("recommended_modes", ",".join(prediction.recommended_modes))
            
            # Add prediction metadata if available
            if prediction.prediction_metadata:
                if "engagement_score" in prediction.prediction_metadata:
                    point = point.field("engagement_score", float(prediction.prediction_metadata["engagement_score"]))
                if "satisfaction_score" in prediction.prediction_metadata:
                    point = point.field("satisfaction_score", float(prediction.prediction_metadata["satisfaction_score"]))
                if "current_mode" in prediction.prediction_metadata:
                    point = point.field("actual_mode", str(prediction.prediction_metadata["current_mode"]))
                if "message_count" in prediction.prediction_metadata:
                    point = point.field("message_count", int(prediction.prediction_metadata["message_count"]))
            
            # Add feature importances (top 5)
            if prediction.feature_importance:
                top_features = sorted(
                    prediction.feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                for idx, (feature, importance) in enumerate(top_features, 1):
                    point = point.field(f"top_feature_{idx}_name", feature)
                    point = point.field(f"top_feature_{idx}_importance", float(importance))
            
            # Add any additional context
            if additional_context:
                for key, value in additional_context.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)
                    elif isinstance(value, str):
                        point = point.field(key, value)
            
            # Write to InfluxDB (SYNCHRONOUS mode to prevent Rx thread spam)
            from influxdb_client.client.write_api import SYNCHRONOUS
            write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
            write_api.write(
                bucket=os.getenv("INFLUXDB_BUCKET", "whisperengine"),
                record=point
            )
            
            logger.debug(
                f"📊 ML Shadow Mode: Logged prediction for {user_id}@{bot_name} "
                f"(effective={prediction.is_effective}, confidence={prediction.confidence:.2%})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ML Shadow Mode: Failed to log prediction: {e}")
            return False
    
    async def log_batch_predictions(
        self,
        predictions: List[tuple],  # List of (prediction, user_id, bot_name, current_mode)
        additional_context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log multiple predictions in batch.
        
        Args:
            predictions: List of tuples (prediction, user_id, bot_name, current_mode)
            additional_context: Optional extra fields to log for all predictions
            
        Returns:
            int: Number of predictions successfully logged
        """
        if not self.enabled:
            return 0
        
        logged_count = 0
        for prediction, user_id, bot_name, current_mode in predictions:
            success = await self.log_prediction(
                prediction, user_id, bot_name, current_mode, additional_context
            )
            if success:
                logged_count += 1
        
        if logged_count > 0:
            logger.info(f"📊 ML Shadow Mode: Logged {logged_count}/{len(predictions)} predictions")
        
        return logged_count
    
    async def get_prediction_statistics(
        self,
        bot_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Query InfluxDB for shadow mode prediction statistics.
        
        Args:
            bot_name: Filter by bot (None = all bots)
            hours: Time window in hours
            
        Returns:
            dict: Statistics about logged predictions
        """
        if not self.enabled:
            return {"error": "ML Shadow Mode not enabled"}
        
        if not self.influxdb_client:
            return {"error": "InfluxDB client not available"}
        
        try:
            query_api = self.influxdb_client.query_api()
            
            # Build Flux query
            bot_filter = f'|> filter(fn: (r) => r["bot"] == "{bot_name}")' if bot_name else ""
            
            flux_query = f'''
                from(bucket: "{os.getenv("INFLUXDB_BUCKET", "whisperengine")}")
                    |> range(start: -{hours}h)
                    |> filter(fn: (r) => r["_measurement"] == "ml_predictions")
                    {bot_filter}
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = query_api.query_data_frame(flux_query)
            
            if result.empty:
                return {
                    "total_predictions": 0,
                    "time_window_hours": hours,
                    "bot": bot_name or "all"
                }
            
            stats = {
                "total_predictions": len(result),
                "effective_count": int(result[result["predicted_effective"] == "true"].shape[0]),
                "ineffective_count": int(result[result["predicted_effective"] == "false"].shape[0]),
                "avg_confidence": float(result["confidence"].mean()),
                "min_confidence": float(result["confidence"].min()),
                "max_confidence": float(result["confidence"].max()),
                "time_window_hours": hours,
                "bot": bot_name or "all"
            }
            
            # Top recommended modes
            if "recommended_modes" in result.columns:
                mode_counts = result["recommended_modes"].value_counts().head(5).to_dict()
                stats["top_recommended_modes"] = mode_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ ML Shadow Mode: Failed to get statistics: {e}")
            return {"error": str(e)}


def create_ml_shadow_logger(influxdb_client=None) -> Optional[MLShadowModeLogger]:
    """
    Factory function to create ML shadow mode logger.
    
    Returns None if shadow mode is disabled (default for end users).
    
    Args:
        influxdb_client: InfluxDB client instance
        
    Returns:
        MLShadowModeLogger if enabled, None otherwise
        
    Example:
        shadow_logger = create_ml_shadow_logger(influxdb_client)
        if shadow_logger:
            await shadow_logger.log_prediction(prediction, user_id, bot_name)
    """
    if not ENABLE_ML_SHADOW_MODE:
        return None
    
    return MLShadowModeLogger(influxdb_client=influxdb_client)
