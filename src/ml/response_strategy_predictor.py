"""
Response Strategy Prediction Service
Integrates Random Forest model for real-time CDL mode optimization

This module provides ML-powered response strategy prediction using trained Random Forest models
to optimize CDL conversation mode selection based on user engagement patterns.
CPU-optimized for production Docker containers.
"""

import logging
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class StrategyPrediction:
    """Result of strategy prediction"""
    is_effective: bool  # Model prediction: current strategy effective?
    confidence: float  # Prediction probability (0-1)
    recommended_modes: List[str]  # CDL modes to consider
    feature_importance: Dict[str, float]  # Which features drove prediction
    prediction_metadata: Dict[str, Any] = field(default_factory=dict)  # Debug info

class ResponseStrategyPredictor:
    """
    ML-powered response strategy predictor using trained Random Forest model.
    
    Predicts whether current conversation approach is effective based on:
    - User engagement history (InfluxDB metrics)
    - Time patterns (hour, day of week)
    - Conversation trends (7-message moving averages, 3-message trends)
    
    Integration: Called by TriggerModeController before mode selection
    
    Example Usage:
        predictor = ResponseStrategyPredictor(influxdb_client=influxdb_client)
        prediction = await predictor.predict_strategy_effectiveness(
            user_id="user123",
            bot_name="elena",
            message_content="Can you explain ocean currents?"
        )
        
        if prediction and prediction.is_effective:
            # Keep current CDL mode
            logger.info(f"Current strategy effective: {prediction.confidence:.2%}")
        else:
            # Consider mode switch: prediction.recommended_modes
            logger.info(f"Recommend switching to: {prediction.recommended_modes[0]}")
    """
    
    def __init__(self, model_path: Optional[str] = None, influxdb_client=None):
        """
        Initialize predictor with trained model and InfluxDB client.
        
        Args:
            model_path: Path to trained Random Forest model (.pkl file). If None, auto-detects latest.
            influxdb_client: InfluxDB client for feature extraction from conversation metrics
                            Can be either a raw InfluxDBClient or TemporalIntelligenceClient
        """
        # Handle both TemporalIntelligenceClient wrapper and raw InfluxDBClient
        if influxdb_client and hasattr(influxdb_client, 'client'):
            # It's a TemporalIntelligenceClient, extract the raw client
            self.influxdb_client = influxdb_client.client
        else:
            # It's a raw InfluxDBClient or None
            self.influxdb_client = influxdb_client
        
        self.model = None
        self.feature_names = None  # Will be loaded from model
        
        # Load trained model
        if model_path is None:
            # Auto-detect latest model (prefer Random Forest for CPU-only containers)
            model_dir = Path('experiments/models')
            if model_dir.exists():
                models = list(model_dir.glob('response_strategy_rf_*.pkl'))
                if models:
                    model_path = str(max(models, key=lambda p: p.stat().st_mtime))
        
        if model_path and Path(model_path).exists():
            try:
                self.model = joblib.load(model_path)
                
                # Try to load feature names from companion file
                features_path = str(Path(model_path).with_name(Path(model_path).stem.replace('rf', 'features') + '.pkl'))
                if Path(features_path).exists():
                    self.feature_names = joblib.load(features_path)
                    logger.info(f"✅ Loaded {len(self.feature_names)} feature names from {features_path}")
                else:
                    # Use model's feature names if available
                    if hasattr(self.model, 'feature_names_in_'):
                        self.feature_names = list(self.model.feature_names_in_)
                    elif hasattr(self.model, 'get_booster'):
                        self.feature_names = self.model.get_booster().feature_names
                    else:
                        # Fallback to basic feature names
                        self.feature_names = [
                            'hour', 'day_of_week',
                            'engagement_score', 'satisfaction_score', 'natural_flow_score',
                            'emotional_resonance', 'topic_relevance',
                            'engagement_score_ma7', 'satisfaction_score_ma7', 'natural_flow_score_ma7',
                            'emotional_resonance_ma7', 'topic_relevance_ma7',
                            'engagement_score_trend3', 'satisfaction_score_trend3'
                        ]
                        logger.warning("Using fallback feature names (model features not detected)")
                
                logger.info(f"✅ Loaded response strategy model: {model_path}")
                logger.debug(f"Model expects {len(self.feature_names)} features")
            except Exception as e:
                logger.error(f"Failed to load model from {model_path}: {e}")
        else:
            logger.warning(f"⚠️  No model found at {model_path}, predictions disabled")
    
    async def predict_strategy_effectiveness(
        self, 
        user_id: str, 
        bot_name: str,
        message_content: str,
        current_mode: Optional[str] = None
    ) -> Optional[StrategyPrediction]:
        """
        Predict if current conversation strategy is effective.
        
        Args:
            user_id: Discord user ID or API user identifier
            bot_name: Character bot name (elena, marcus, etc.)
            message_content: User's message content (for context)
            current_mode: Currently active CDL conversation mode
        
        Returns:
            StrategyPrediction with effectiveness score and recommended modes
            None if model unavailable or insufficient data
        """
        if not self.model:
            logger.debug("ML model not loaded, skipping prediction")
            return None
        
        if not self.influxdb_client:
            logger.debug("InfluxDB client not available for feature extraction")
            return None
        
        try:
            # 1. Extract features from InfluxDB
            features = await self._extract_features(user_id, bot_name)
            if features is None:
                logger.debug(f"Insufficient InfluxDB data for {user_id}, skipping prediction")
                return None
            
            # 2. Run model inference
            # Ensure features match model's expected feature names
            if self.feature_names:
                # Reorder/filter features to match model expectations
                X_dict = {}
                for feat_name in self.feature_names:
                    X_dict[feat_name] = features.get(feat_name, 0.0)
                X = pd.DataFrame([X_dict])
            else:
                X = pd.DataFrame([features])
            
            prediction_proba = self.model.predict_proba(X)[0]  # [prob_class_0, prob_class_1]
            is_effective = prediction_proba[1] > 0.5  # Class 1 = effective strategy
            confidence = float(prediction_proba[1])
            
            # 3. Get feature importance for this prediction
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # 4. Recommend CDL modes based on prediction
            recommended_modes = self._recommend_modes(features, is_effective, confidence)
            
            logger.info(
                f"🤖 ML PREDICTION: user={user_id}, effective={is_effective}, "
                f"confidence={confidence:.2%}, modes={recommended_modes}"
            )
            
            return StrategyPrediction(
                is_effective=is_effective,
                confidence=confidence,
                recommended_modes=recommended_modes,
                feature_importance=top_features,
                prediction_metadata={
                    'current_mode': current_mode,
                    'engagement_score': features.get('engagement_score'),
                    'satisfaction_score': features.get('satisfaction_score'),
                    'message_preview': message_content[:50] + '...' if len(message_content) > 50 else message_content
                }
            )
            
        except Exception as e:
            logger.error(f"Error in strategy prediction: {e}", exc_info=True)
            return None
    
    async def _extract_features(self, user_id: str, bot_name: str) -> Optional[Dict[str, float]]:
        """
        Extract 14 features from InfluxDB for model inference.
        
        Features extracted:
        - Time: hour, day_of_week
        - Current scores: engagement_score, satisfaction_score, natural_flow_score, emotional_resonance, topic_relevance
        - 7-msg moving averages: {above}_ma7
        - 3-msg trends: engagement_score_trend3, satisfaction_score_trend3
        
        Returns:
            Dictionary of 14 features matching model training data
            None if insufficient data (< 7 messages)
        """
        if not self.influxdb_client:
            logger.debug("InfluxDB client not available - cannot extract features")
            return None
            
        try:
            # Query last 7 messages for moving average calculation
            flux_query = f'''
            from(bucket: "performance_metrics")
              |> range(start: -7d)
              |> filter(fn: (r) => r._measurement == "conversation_quality")
              |> filter(fn: (r) => r.user_id == "{user_id}")
              |> filter(fn: (r) => r.bot == "{bot_name}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> sort(columns: ["_time"], desc: false)
              |> tail(n: 7)
            '''
            
            # Call query_api() method to get QueryApi object, then call query_data_frame
            result = self.influxdb_client.query_api().query_data_frame(flux_query)
            
            if result.empty or len(result) < 7:
                logger.debug(f"Insufficient data: {len(result) if not result.empty else 0} messages (need 7)")
                return None  # Need at least 7 messages for moving averages
            
            # Current values (most recent message)
            latest = result.iloc[-1]
            
            # Time-based features
            now = datetime.now()
            features = {
                'hour': now.hour,
                'day_of_week': now.weekday()
            }
            
            # Current scores
            for col in ['engagement_score', 'satisfaction_score', 'natural_flow_score', 
                       'emotional_resonance', 'topic_relevance']:
                features[col] = float(latest.get(col, 0))
            
            # 7-message moving averages
            for col in ['engagement_score', 'satisfaction_score', 'natural_flow_score',
                       'emotional_resonance', 'topic_relevance']:
                if col in result.columns:
                    features[f'{col}_ma7'] = float(result[col].tail(7).mean())
                else:
                    features[f'{col}_ma7'] = 0.0
            
            # 3-message trends (difference between recent and older messages)
            for col in ['engagement_score', 'satisfaction_score']:
                if col in result.columns and len(result) >= 3:
                    recent_avg = result[col].tail(3).mean()
                    older_avg = result[col].iloc[-6:-3].mean() if len(result) >= 6 else result[col].head(3).mean()
                    features[f'{col}_trend3'] = float(recent_avg - older_avg)
                else:
                    features[f'{col}_trend3'] = 0.0
            
            logger.debug(f"Extracted {len(features)} features for {user_id}: "
                        f"engagement={features['engagement_score']:.2f}, "
                        f"satisfaction={features['satisfaction_score']:.2f}")
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True)
            return None
    
    def _recommend_modes(self, features: Dict, is_effective: bool, confidence: float) -> List[str]:
        """
        Recommend CDL conversation modes based on prediction and feature analysis.
        
        Logic:
        - If current strategy IS effective (high confidence): Keep current mode or suggest "balanced"
        - If current strategy NOT effective: Suggest mode switch based on feature patterns
        
        Args:
            features: Extracted feature dictionary from InfluxDB
            is_effective: Model prediction (True = effective, False = needs improvement)
            confidence: Prediction confidence (0-1)
        
        Returns:
            List of recommended CDL mode names (up to 3)
        """
        if is_effective and confidence > 0.8:
            # Current strategy working well - maintain or use balanced mode
            return ['balanced', 'maintain_current']
        
        # Strategy needs improvement - analyze features to recommend mode
        engagement = features.get('engagement_score', 0)
        satisfaction = features.get('satisfaction_score', 0)
        emotional_resonance = features.get('emotional_resonance', 0)
        natural_flow = features.get('natural_flow_score', 0)
        
        recommended = []
        
        # Low engagement → Try more interactive/educational mode
        if engagement < 0.5:
            recommended.extend(['educational', 'creative', 'casual'])
        
        # Low satisfaction → Try more empathetic/supportive mode
        if satisfaction < 0.5:
            recommended.extend(['supportive', 'empathetic'])
        
        # Low emotional resonance → Try warmer communication
        if emotional_resonance < 0.5:
            recommended.extend(['warm', 'personal'])
        
        # Low natural flow → Simplify or change conversation style
        if natural_flow < 0.5:
            recommended.extend(['simplified', 'direct'])
        
        # Default fallback
        if not recommended:
            recommended = ['balanced', 'adaptive']
        
        # Return top 3 unique recommendations
        return list(dict.fromkeys(recommended))[:3]


def create_response_strategy_predictor(model_path: Optional[str] = None, influxdb_client=None):
    """
    Factory function for creating ResponseStrategyPredictor.
    
    Args:
        model_path: Path to trained Random Forest model. If None, auto-detects latest.
        influxdb_client: InfluxDB client for feature extraction
    
    Returns:
        Initialized ResponseStrategyPredictor instance
    
    Example:
        predictor = create_response_strategy_predictor(influxdb_client=my_client)
    """
    return ResponseStrategyPredictor(model_path=model_path, influxdb_client=influxdb_client)
