# ML Shadow Mode Quick Start

## 🎯 What is Shadow Mode?

**Shadow Mode** means ML predictions are logged to InfluxDB **without affecting bot behavior**. This allows you to:
- Validate ML predictions against actual outcomes
- Build confidence in the model before production deployment
- Compare ML recommendations vs keyword-based mode selection
- Analyze prediction confidence distribution over time

## 🚨 Feature Flag: DISABLED by Default

```bash
# Default state (end users, production)
ENABLE_ML_SHADOW_MODE=false  # or not set

# Enable for ML development/testing
ENABLE_ML_SHADOW_MODE=true
```

**Why disabled by default?**
- End users don't need ML dependencies (XGBoost, sklearn)
- Avoids loading 300+ MB of ML models on every bot restart
- No overhead for users who aren't training/testing models

## 📊 What Gets Logged

**InfluxDB Measurement**: `ml_predictions`

**Tags** (indexed):
- `user_id` - Discord user ID
- `bot` - Character bot name
- `predicted_effective` - true/false
- `current_mode` - CDL mode being used

**Fields**:
- `confidence` - Model confidence (0.0-1.0)
- `recommended_modes` - Comma-separated mode list
- `engagement_score` - Current engagement metric
- `satisfaction_score` - Current satisfaction metric
- `message_count` - Messages in conversation history
- `top_feature_1_name` - Most important feature
- `top_feature_1_importance` - Importance score
- ... (top 5 features logged)

## 🚀 Usage

### 1. Enable Shadow Mode (Optional)

```bash
# Add to .env file
ENABLE_ML_SHADOW_MODE=true
```

### 2. Initialize Logger in Bot

```python
from src.ml import create_ml_shadow_logger

# In bot initialization (src/core/bot.py or message_processor.py)
shadow_logger = create_ml_shadow_logger(influxdb_client)

if shadow_logger:
    logger.info("✅ ML Shadow Mode ENABLED")
else:
    logger.debug("ML Shadow Mode disabled (default)")
```

### 3. Log Predictions During Message Processing

```python
from src.ml import create_response_strategy_predictor

# Get ML prediction
predictor = create_response_strategy_predictor(influxdb_client=influxdb_client)
prediction = await predictor.predict_strategy_effectiveness(
    user_id=user_id,
    bot_name=bot_name,
    message_content=message
)

# Log prediction (shadow mode - doesn't affect behavior)
if shadow_logger:
    await shadow_logger.log_prediction(
        prediction=prediction,
        user_id=user_id,
        bot_name=bot_name,
        current_mode=current_cdl_mode,
        additional_context={"channel_id": channel_id}
    )

# Continue with normal keyword-based mode selection
# (prediction is logged but NOT used yet)
```

## 📈 Analyzing Shadow Mode Data

### Query Predictions (Last 24 Hours)

```python
# Get statistics
stats = await shadow_logger.get_prediction_statistics(
    bot_name="elena",
    hours=24
)

print(f"Total predictions: {stats['total_predictions']}")
print(f"Effective: {stats['effective_count']}")
print(f"Avg confidence: {stats['avg_confidence']:.2%}")
```

### Flux Query (InfluxDB UI)

```flux
from(bucket: "whisperengine")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "ml_predictions")
  |> filter(fn: (r) => r["bot"] == "elena")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

### Compare ML vs Actual Outcomes

```flux
// Join ML predictions with actual conversation quality
predictions = from(bucket: "whisperengine")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "ml_predictions")

actual = from(bucket: "whisperengine")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "temporal_intelligence_v2")

// Join on user_id + bot + timestamp (within 5 minute window)
join(
  left: predictions,
  right: actual,
  on: (l, r) => l.user_id == r.user_id and l.bot == r.bot
)
```

## 🎯 Success Metrics

After 1 week of shadow mode, analyze:

1. **Prediction Accuracy**
   - Do high-confidence predictions correlate with better outcomes?
   - What percentage of conversations are "effective" vs "ineffective"?

2. **Mode Recommendations**
   - How often does ML recommend different modes than keyword system?
   - Which modes does ML favor for which users?

3. **Confidence Distribution**
   - What's the typical confidence range?
   - Are low-confidence predictions less accurate?

4. **Feature Importance Trends**
   - Which features consistently rank highest?
   - Do feature importances vary by bot/user?

## 🔧 Testing

```bash
# Test with feature disabled (default)
python tests/automated/test_ml_shadow_logger.py

# Test with feature enabled
export ENABLE_ML_SHADOW_MODE=true
python tests/automated/test_ml_shadow_logger.py
```

## 🚦 Rollout Strategy

1. **Phase 1: Shadow Mode (Current)** ✅
   - Feature flag: `ENABLE_ML_SHADOW_MODE=true`
   - Log predictions without using them
   - Duration: 1 week
   - Goal: Validate prediction quality

2. **Phase 2: Hybrid Mode** (Next)
   - Feature flag: `ENABLE_ML_HYBRID_MODE=true`
   - Use ML predictions to supplement keyword detection
   - Duration: 2 weeks
   - Goal: A/B test ML vs keywords

3. **Phase 3: ML-First Mode** (Future)
   - Feature flag: `ENABLE_ML_FIRST_MODE=true`
   - ML predictions override keyword detection
   - Keyword system as fallback only
   - Goal: Full ML deployment

## 🛑 Disabling Shadow Mode

```bash
# Remove from .env or set to false
ENABLE_ML_SHADOW_MODE=false

# Restart bot
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena
```

Logger will return `None` and no predictions will be logged.

## 📝 Notes

- **Zero Performance Impact**: Logging is async, doesn't block message processing
- **Safe Rollback**: Just disable feature flag, no code changes needed
- **Data Privacy**: Same InfluxDB instance as existing metrics (already configured)
- **No Model Loading**: If feature disabled, ML models never load (saves memory)

---

**Status**: Shadow mode infrastructure ready. Enable `ENABLE_ML_SHADOW_MODE=true` to start logging predictions.
