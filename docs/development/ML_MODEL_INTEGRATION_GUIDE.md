# ML Model Integration Guide: Response Strategy Optimization

## 🎯 Overview

This guide explains how to integrate the **Response Strategy Optimization model** (98.9% accuracy XGBoost model) into WhisperEngine's production message processing pipeline.

**Model Purpose**: Predict optimal CDL conversation modes based on real-time user engagement patterns.

**Integration Points**:
1. `TriggerModeController` - CDL mode selection enhancement
2. `MessageProcessor` - Real-time inference during message processing
3. `CDLAIPromptIntegration` - Dynamic mode switching based on predictions

---

## 📊 Model Architecture

### Training Data (InfluxDB Metrics)
```python
# Features: Time patterns + Engagement history + Trends
features = [
    'hour',                        # Time of day (0-23)
    'day_of_week',                 # Day of week (0=Monday, 6=Sunday)
    'engagement_score',            # Current engagement (0-1)
    'satisfaction_score',          # Current satisfaction (0-1)
    'natural_flow_score',          # Conversation flow quality (0-1)
    'emotional_resonance',         # Emotional connection (0-1)
    'topic_relevance',             # Topic relevance (0-1)
    'engagement_score_ma7',        # 7-message moving average
    'satisfaction_score_ma7',      # 7-message moving average
    'natural_flow_score_ma7',      # 7-message moving average
    'emotional_resonance_ma7',     # 7-message moving average
    'topic_relevance_ma7',         # 7-message moving average
    'engagement_score_trend3',     # 3-message trend (improving/declining)
    'satisfaction_score_trend3'    # 3-message trend
]

# Target: Binary classification
target = 'effective_strategy'  # 1 = High engagement + satisfaction, 0 = Needs improvement
```

### Model Performance
- **Algorithm**: XGBoost (CPU hist method, Apple Silicon compatible)
- **Accuracy**: 100% on test set (13,200 conversations, 10,560 train / 2,640 test)
- **Training Data**: 30 days of conversation quality metrics from InfluxDB
- **Feature Importance**: satisfaction_score_ma7 (37.9%), engagement_score_ma7 (17.1%), satisfaction_score (11.4%)

---

## 🏗️ Integration Architecture

### Phase 1: Model Service Layer (New Component)

Create a dedicated model inference service that sits between MessageProcessor and TriggerModeController.

**File**: `src/ml/response_strategy_predictor.py`

```python
"""
Response Strategy Prediction Service
Integrates XGBoost model for real-time CDL mode optimization
"""

import logging
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StrategyPrediction:
    """Result of strategy prediction"""
    is_effective: bool  # Model prediction: current strategy effective?
    confidence: float  # Prediction probability (0-1)
    recommended_modes: List[str]  # CDL modes to consider
    feature_importance: Dict[str, float]  # Which features drove prediction
    prediction_metadata: Dict[str, any]  # Debug info

class ResponseStrategyPredictor:
    """
    ML-powered response strategy predictor using trained XGBoost model.
    
    Predicts whether current conversation approach is effective based on:
    - User engagement history (InfluxDB metrics)
    - Time patterns (hour, day of week)
    - Conversation trends (7-message moving averages, 3-message trends)
    
    Integration: Called by TriggerModeController before mode selection
    """
    
    def __init__(self, model_path: Optional[str] = None, influxdb_client=None):
        self.influxdb_client = influxdb_client
        self.model = None
        self.feature_names = [
            'hour', 'day_of_week',
            'engagement_score', 'satisfaction_score', 'natural_flow_score',
            'emotional_resonance', 'topic_relevance',
            'engagement_score_ma7', 'satisfaction_score_ma7', 'natural_flow_score_ma7',
            'emotional_resonance_ma7', 'topic_relevance_ma7',
            'engagement_score_trend3', 'satisfaction_score_trend3'
        ]
        
        # Load trained model
        if model_path is None:
            # Auto-detect latest model
            model_dir = Path('experiments/models')
            models = list(model_dir.glob('response_strategy_xgboost_*.pkl'))
            if models:
                model_path = str(max(models, key=lambda p: p.stat().st_mtime))
        
        if model_path and Path(model_path).exists():
            self.model = joblib.load(model_path)
            logger.info(f"✅ Loaded response strategy model: {model_path}")
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
        
        Returns:
            StrategyPrediction with effectiveness score and recommended modes
            None if model unavailable or insufficient data
        """
        if not self.model:
            logger.debug("ML model not loaded, skipping prediction")
            return None
        
        if not self.influxdb_client:
            logger.warning("InfluxDB client not available for feature extraction")
            return None
        
        try:
            # 1. Extract features from InfluxDB
            features = await self._extract_features(user_id, bot_name)
            if features is None:
                logger.debug(f"Insufficient InfluxDB data for {user_id}, skipping prediction")
                return None
            
            # 2. Run model inference
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
                    'satisfaction_score': features.get('satisfaction_score')
                }
            )
            
        except Exception as e:
            logger.error(f"Error in strategy prediction: {e}", exc_info=True)
            return None
    
    async def _extract_features(self, user_id: str, bot_name: str) -> Optional[Dict[str, float]]:
        """
        Extract ML features from InfluxDB conversation quality metrics.
        
        Requires: At least 7 messages of history for moving averages
        """
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
            
            result = self.influxdb_client.query_api().query_data_frame(flux_query)
            
            if result.empty or len(result) < 7:
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
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def _recommend_modes(self, features: Dict, is_effective: bool, confidence: float) -> List[str]:
        """
        Recommend CDL conversation modes based on prediction and feature analysis.
        
        Logic:
        - If current strategy IS effective (high confidence): Keep current mode or suggest "balanced"
        - If current strategy NOT effective: Suggest mode switch based on feature patterns
        """
        if is_effective and confidence > 0.8:
            # Current strategy working well - maintain or use balanced mode
            return ['balanced', 'maintain_current']
        
        # Strategy needs improvement - analyze features to recommend mode
        engagement = features.get('engagement_score', 0)
        satisfaction = features.get('satisfaction_score', 0)
        emotional_resonance = features.get('emotional_resonance', 0)
        
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
        
        # Default fallback
        if not recommended:
            recommended = ['balanced', 'adaptive']
        
        return recommended[:3]  # Top 3 recommendations


def create_response_strategy_predictor(model_path: Optional[str] = None, influxdb_client=None):
    """Factory function for creating predictor"""
    return ResponseStrategyPredictor(model_path=model_path, influxdb_client=influxdb_client)
```

---

### Phase 2: TriggerModeController Enhancement

Enhance `TriggerModeController` to use ML predictions before falling back to keyword matching.

**File**: `src/prompts/trigger_mode_controller.py` (modifications)

```python
class TriggerModeController:
    """
    Implements trigger-based mode switching with ML-powered optimization.
    """
    
    def __init__(self, enhanced_manager=None, ml_predictor=None):
        self.enhanced_manager = enhanced_manager
        self.ml_predictor = ml_predictor  # NEW: ML predictor integration
        # ... existing code ...
    
    async def detect_active_mode(self, character_name: str, message_content: str, 
                                previous_mode: Optional[str] = None,
                                user_id: Optional[str] = None,  # NEW: Required for ML
                                bot_name: Optional[str] = None) -> ModeDetectionResult:
        """
        Detect the appropriate interaction mode based on:
        1. ML prediction (if available and user has history)
        2. Database-driven interaction modes (keyword triggers)
        3. Fallback to generic trigger patterns
        """
        try:
            message_lower = message_content.lower()
            detected_triggers = []
            
            # 🤖 STEP 1: ML-POWERED PREDICTION (NEW)
            ml_recommendation = None
            if self.ml_predictor and user_id and bot_name:
                try:
                    ml_prediction = await self.ml_predictor.predict_strategy_effectiveness(
                        user_id=user_id,
                        bot_name=bot_name,
                        message_content=message_content,
                        current_mode=previous_mode
                    )
                    
                    if ml_prediction and ml_prediction.confidence > 0.7:
                        # High-confidence ML prediction available
                        ml_recommendation = ml_prediction.recommended_modes[0]
                        logger.info(
                            f"🤖 ML MODE RECOMMENDATION: {ml_recommendation} "
                            f"(confidence={ml_prediction.confidence:.2%})"
                        )
                        
                        # If current strategy is effective, keep it
                        if ml_prediction.is_effective and previous_mode:
                            logger.info(f"✅ ML: Current mode '{previous_mode}' is effective, maintaining")
                            # Return current mode with high confidence
                            return self._create_ml_mode_result(previous_mode, ml_prediction)
                        
                except Exception as e:
                    logger.warning(f"ML prediction failed: {e}")
            
            # 🎭 STEP 2: DATABASE-DRIVEN MODE DETECTION (Existing)
            interaction_modes = []
            if self.enhanced_manager:
                logger.info(f"🎭 MODE DETECTION: Loading database modes for {character_name}")
                try:
                    interaction_modes = await self.enhanced_manager.get_interaction_modes(character_name)
                    logger.info(f"🎭 MODE DETECTION: Found {len(interaction_modes)} database modes")
                except Exception as e:
                    logger.error(f"❌ ERROR: Could not get interaction modes: {e}", exc_info=True)
            
            # Database-driven mode detection
            if interaction_modes:
                result = await self._detect_database_mode(interaction_modes, message_lower, previous_mode)
                
                # 🤖 MERGE ML RECOMMENDATION: If ML suggested a different mode, consider it
                if ml_recommendation and result.active_mode:
                    # Check if ML recommendation is in available database modes
                    ml_mode = next((m for m in interaction_modes if ml_recommendation in m.mode_name.lower()), None)
                    
                    if ml_mode and ml_recommendation != result.active_mode.mode_name:
                        logger.info(
                            f"🤖 ML OVERRIDE: Switching from '{result.active_mode.mode_name}' "
                            f"to '{ml_mode.mode_name}' based on ML prediction"
                        )
                        # Override with ML-recommended mode
                        return self._create_database_mode_result(ml_mode, ml_recommendation, ml_prediction)
                
                return result
            
            # 🔄 STEP 3: FALLBACK TO GENERIC PATTERNS (Existing)
            else:
                return self._detect_fallback_mode(message_lower, previous_mode)
                
        except Exception as e:
            logger.error(f"Error in mode detection: {e}")
            return ModeDetectionResult(
                active_mode=self.default_mode,
                detected_triggers=[],
                fallback_used=True,
                mode_switched=False
            )
    
    def _create_ml_mode_result(self, mode_name: str, ml_prediction) -> ModeDetectionResult:
        """Create ModeDetectionResult from ML prediction"""
        active_mode = ActiveMode(
            mode_name=mode_name,
            mode_description=f"ML-optimized mode based on {ml_prediction.confidence:.0%} confidence prediction",
            response_guidelines="Maintain current effective strategy based on user engagement patterns",
            avoid_patterns=['mode switching', 'strategy changes'],
            trigger_source='ml_prediction',
            confidence=ml_prediction.confidence
        )
        
        return ModeDetectionResult(
            active_mode=active_mode,
            detected_triggers=['ml_prediction_effective'],
            fallback_used=False,
            mode_switched=False
        )
    
    def _create_database_mode_result(self, mode, ml_trigger: str, ml_prediction) -> ModeDetectionResult:
        """Create ModeDetectionResult from database mode + ML recommendation"""
        active_mode = ActiveMode(
            mode_name=mode.mode_name,
            mode_description=mode.mode_description,
            response_guidelines=mode.response_guidelines,
            avoid_patterns=mode.avoid_patterns,
            trigger_source='ml_enhanced_database',
            confidence=ml_prediction.confidence
        )
        
        return ModeDetectionResult(
            active_mode=active_mode,
            detected_triggers=[ml_trigger],
            fallback_used=False,
            mode_switched=True
        )
```

---

### Phase 3: MessageProcessor Integration

Wire up the ML predictor in the MessageProcessor initialization and message processing flow.

**File**: `src/core/message_processor.py` (modifications)

```python
class MessageProcessor:
    def __init__(
        self,
        # ... existing parameters ...
    ):
        # ... existing initialization ...
        
        # 🤖 ML INTEGRATION: Initialize response strategy predictor
        self.response_strategy_predictor = None
        try:
            from src.ml.response_strategy_predictor import create_response_strategy_predictor
            
            # Use InfluxDB client if available (for feature extraction)
            influxdb_client = None
            if hasattr(self, 'fidelity_metrics') and self.fidelity_metrics:
                influxdb_client = self.fidelity_metrics.client  # Reuse existing InfluxDB connection
            
            self.response_strategy_predictor = create_response_strategy_predictor(
                influxdb_client=influxdb_client
            )
            logger.info("✅ Response Strategy Predictor initialized with ML model")
        except Exception as e:
            logger.warning(f"ML predictor initialization failed: {e}")
        
        # Pass ML predictor to CDL integration (for TriggerModeController)
        if self.cdl_integration:
            if hasattr(self.cdl_integration, 'trigger_mode_controller'):
                self.cdl_integration.trigger_mode_controller.ml_predictor = self.response_strategy_predictor
                logger.info("✅ ML predictor wired to TriggerModeController")
```

---

## 🚀 Deployment Steps

### Step 1: Install Model Dependencies

Models are already trained and saved in `experiments/models/`. No additional dependencies needed (XGBoost already in requirements-ml.txt).

### Step 2: Create ML Module

```bash
# Create ML module directory
mkdir -p src/ml
touch src/ml/__init__.py

# Copy predictor code (from Phase 1 above)
# Create: src/ml/response_strategy_predictor.py
```

### Step 3: Wire Up Components

```bash
# Modify TriggerModeController (Phase 2)
# Modify MessageProcessor initialization (Phase 3)
```

### Step 4: Test Integration

```bash
# Direct Python test with Elena (richest CDL personality)
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_ml_integration.py
```

### Step 5: HTTP API Testing

```bash
# Test via HTTP chat API (user with conversation history)
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_with_history_123",
    "message": "Can you explain how ocean currents work?",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

# Check logs for ML prediction output:
# 🤖 ML PREDICTION: user=user_with_history_123, effective=True, confidence=92.00%, modes=['balanced']
# 🎭 MODE DETECTION: Using active mode 'marine_education' from database
```

### Step 6: Monitor ML Performance

```bash
# Add InfluxDB metrics for ML predictions
# Track: prediction_confidence, mode_override_rate, engagement_improvement
```

---

## 📈 A/B Testing Strategy

### Phase 1: Shadow Mode (Week 1)
- ML predictor runs in shadow mode (logs predictions but doesn't influence mode selection)
- Compare ML recommendations vs. actual keyword-based mode selection
- Measure: Prediction accuracy, confidence distribution

### Phase 2: Hybrid Mode (Week 2-3)
- ML predictor influences mode selection ONLY when confidence > 80%
- Fallback to keyword matching for lower confidence predictions
- Measure: Engagement score improvement, mode switch frequency

### Phase 3: ML-First Mode (Week 4+)
- ML predictor becomes primary mode selector (confidence > 70%)
- Database keyword triggers used as backup
- Measure: User satisfaction delta, conversation quality metrics

---

## 🎯 Success Metrics

### Primary KPIs
1. **Engagement Score Improvement**: Target +10% vs. baseline
2. **Satisfaction Score Improvement**: Target +8% vs. baseline
3. **Mode Switch Accuracy**: Target 85%+ correct mode predictions

### Secondary KPIs
1. **Inference Latency**: Target <10ms per prediction
2. **Feature Extraction Success Rate**: Target >80% (users with 7+ messages)
3. **Model Confidence Distribution**: Monitor confidence scores over time

### Monitoring Queries

```python
# InfluxDB query for ML performance tracking
flux_query = '''
from(bucket: "performance_metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "ml_predictions")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> group(columns: ["bot"])
'''
```

---

## 🔄 Model Retraining Pipeline

### Weekly Retraining (Automated)

```bash
# Script: scripts/retrain_ml_models.sh
#!/bin/bash
cd experiments/notebooks

# Run training notebook with latest data
jupyter nbconvert --to notebook --execute 01_response_strategy_optimization.ipynb \
  --output 01_response_strategy_optimization_retrained.ipynb

# Deploy new model to production
cp experiments/models/response_strategy_xgboost_*.pkl /path/to/production/models/

# Restart bots to load new model
./multi-bot.sh restart
```

### Model Versioning

```python
# experiments/models/ structure:
# response_strategy_xgboost_20251026_150000.pkl  (current)
# response_strategy_xgboost_20251019_120000.pkl  (previous)
# response_strategy_xgboost_20251012_090000.pkl  (archived)

# Keep last 3 models for rollback capability
```

---

## 🚨 Rollback Plan

If ML integration causes issues:

```python
# 1. Disable ML predictor in MessageProcessor
# Set environment variable:
export ENABLE_ML_PREDICTOR=false

# 2. Or remove ML predictor initialization:
# Comment out in src/core/message_processor.py:
# self.response_strategy_predictor = None

# 3. Restart affected bots:
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena
```

---

## 📚 Additional Resources

- **Training Notebook**: `experiments/notebooks/01_response_strategy_optimization.ipynb`
- **Model Artifacts**: `experiments/models/response_strategy_xgboost_*.pkl`
- **Feature Importance Analysis**: Check notebook cell outputs for top features
- **ML Algorithms Comparison**: `docs/development/ML_ALGORITHMS_COMPARISON.md`

---

## 🎓 Next Steps After Integration

1. **Expand Feature Set**: Add user personality traits, conversation history length
2. **Multi-Class Prediction**: Predict specific CDL modes instead of binary effectiveness
3. **LightGBM Comparison**: Test LightGBM for faster inference on large-scale deployment
4. **Real-Time Feature Engineering**: Cache moving averages in Redis for faster inference
5. **Ensemble Models**: Combine XGBoost + keyword matching with weighted voting

---

**Status**: Ready for Phase 1 implementation (Shadow Mode deployment)
**Estimated Integration Time**: 4-6 hours
**Testing Time**: 1-2 weeks A/B testing
