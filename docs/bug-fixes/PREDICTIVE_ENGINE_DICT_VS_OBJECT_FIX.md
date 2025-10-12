# Predictive Engine Dict vs Object Access Fix

**Date**: October 11, 2025  
**Issue**: `'RelationshipTrend' object has no attribute 'get'`  
**Root Cause**: Dictionary access methods (`.get()`) used on dataclass objects  
**Files Modified**: `src/adaptation/predictive_engine.py`

---

## Executive Summary

Fixed critical type mismatch errors in the Predictive Adaptation Engine where the code was treating dataclass objects (`ConfidenceTrend`, `RelationshipTrend`, `QualityTrend`) as dictionaries and attempting to use `.get()` method which doesn't exist on dataclass objects.

**Error Message**: 
```
2025-10-11 18:56:28,049 - src.adaptation.predictive_engine - ERROR - Failed to predict user needs for 1008886439108411472: 'RelationshipTrend' object has no attribute 'get'
```

---

## Problem Analysis

### Dataclass Structures (from `src/analytics/trend_analyzer.py`)

**TrendAnalysis** (base trend data):
```python
@dataclass
class TrendAnalysis:
    direction: TrendDirection
    slope: float              # Rate of change (NOT severity!)
    confidence: float         # Confidence in trend detection (0-1)
    current_value: float
    average_value: float
    volatility: float         # Standard deviation
    data_points: int
    time_span_days: int
```

**ConfidenceTrend**:
```python
@dataclass
class ConfidenceTrend:
    user_id: str
    bot_name: str
    trend_analysis: TrendAnalysis  # Contains direction, slope, etc.
    recent_confidence: float
    historical_average: float
    critical_threshold: float = 0.6
    needs_adaptation: bool = False
```

**RelationshipTrend**:
```python
@dataclass
class RelationshipTrend:
    user_id: str
    bot_name: str
    trust_trend: TrendAnalysis      # NOT a float!
    affection_trend: TrendAnalysis  # NOT a float!
    attunement_trend: TrendAnalysis
    overall_direction: TrendDirection
    needs_attention: bool = False
```

**QualityTrend**:
```python
@dataclass
class QualityTrend:
    bot_name: str
    satisfaction_trend: TrendAnalysis       # NOT a float!
    flow_trend: TrendAnalysis              # NOT a float!
    emotional_resonance_trend: TrendAnalysis
    overall_score: float
    needs_optimization: bool = False
```

### The Core Problem

The `_get_trend_analysis()` method returns:
```python
{
    'confidence_trend': ConfidenceTrend object,    # NOT a dict!
    'relationship_trend': RelationshipTrend object, # NOT a dict!
    'quality_trend': QualityTrend object,          # NOT a dict!
    'analysis_timestamp': datetime
}
```

But the prediction methods were treating these objects as dictionaries:
```python
# ❌ WRONG - trying to use .get() on dataclass object
trust_score = relationship_trend.get('trust', 0.5)
affection_score = relationship_trend.get('affection', 0.5)
```

---

## Fixes Applied

### Fix 1: `_predict_relationship_issues` (Lines 353-398)

**BEFORE** (broken):
```python
relationship_trend = trend_data.get('relationship_trend', {})
if not relationship_trend:
    return predictions

# Pattern: Trust or affection declining
trust_score = relationship_trend.get('trust', 0.5)           # ❌ .get() on object
affection_score = relationship_trend.get('affection', 0.5)   # ❌ .get() on object

if trust_score < 0.4 or affection_score < 0.4:
```

**AFTER** (fixed):
```python
relationship_trend = trend_data.get('relationship_trend')
if not relationship_trend:
    return predictions

# RelationshipTrend is a dataclass with trust_trend, affection_trend attributes (TrendAnalysis objects)
# Access the current_value from the TrendAnalysis objects
trust_score = relationship_trend.trust_trend.current_value if hasattr(relationship_trend, 'trust_trend') else 0.5
affection_score = relationship_trend.affection_trend.current_value if hasattr(relationship_trend, 'affection_trend') else 0.5

# Check if trust or affection are declining with low values
trust_declining = (hasattr(relationship_trend, 'trust_trend') and 
                  relationship_trend.trust_trend.direction == TrendDirection.DECLINING)
affection_declining = (hasattr(relationship_trend, 'affection_trend') and 
                      relationship_trend.affection_trend.direction == TrendDirection.DECLINING)

if (trust_score < 0.4 or affection_score < 0.4) or (trust_declining and affection_declining):
```

**Key Changes**:
- Access `trust_trend.current_value` instead of dict key `'trust'`
- Access `affection_trend.current_value` instead of dict key `'affection'`
- Check `trust_trend.direction` for trend analysis
- Added enhanced indicators showing both scores and trend directions

---

### Fix 2: `_predict_quality_issues` (Lines 318-370)

**BEFORE** (broken):
```python
quality_trend = trend_data.get('quality_trend', {})
if not quality_trend:
    return predictions

# Pattern: Quality degradation with conversation frequency increase
if (quality_trend.get('direction') == 'declining' and      # ❌ .get() on object
    trend_data.get('frequency_trend', {}).get('direction') == 'increasing'):
```

**AFTER** (fixed):
```python
quality_trend = trend_data.get('quality_trend')
if not quality_trend:
    return predictions

# QualityTrend is a dataclass with satisfaction_trend, flow_trend, emotional_resonance_trend (TrendAnalysis objects)
# Check if any major quality metric is declining
satisfaction_declining = (hasattr(quality_trend, 'satisfaction_trend') and 
                         quality_trend.satisfaction_trend.direction == TrendDirection.DECLINING)
flow_declining = (hasattr(quality_trend, 'flow_trend') and 
                 quality_trend.flow_trend.direction == TrendDirection.DECLINING)
emotional_resonance_declining = (hasattr(quality_trend, 'emotional_resonance_trend') and 
                                quality_trend.emotional_resonance_trend.direction == TrendDirection.DECLINING)

# Check overall quality score
overall_score = quality_trend.overall_score if hasattr(quality_trend, 'overall_score') else 0.7

# Predict quality drop if multiple metrics declining or overall score is low
if ((satisfaction_declining and flow_declining) or 
    overall_score < 0.5 or 
    (emotional_resonance_declining and overall_score < 0.6)):
```

**Key Changes**:
- Check individual trend directions from `TrendAnalysis` objects
- Use `overall_score` attribute instead of dict access
- Enhanced prediction logic considering multiple quality dimensions
- Added detailed indicators for all quality trend components

---

### Fix 3: `_predict_confidence_issues` (Lines 273-314)

**BEFORE** (broken):
```python
severity = confidence_trend.trend_analysis.severity  # ❌ No 'severity' attribute!
current_confidence = confidence_trend.recent_confidence

if current_confidence > 0.6 and severity > 0.3:
```

**AFTER** (fixed):
```python
# Use absolute slope as severity indicator (how fast it's declining)
severity = abs(confidence_trend.trend_analysis.slope) if hasattr(confidence_trend.trend_analysis, 'slope') else 0.0
current_confidence = confidence_trend.recent_confidence

# Predict confidence will drop below threshold
if current_confidence > 0.6 and severity > 0.01:  # slope > 0.01 indicates meaningful decline
    prediction = PredictedNeed(
        ...
        confidence=self._calculate_prediction_confidence(severity * 10, confidence_trend),  # Scale slope to 0-1 range
        ...
        indicators=[
            f"Current confidence: {current_confidence:.2f}",
            f"Decline rate (slope): {severity:.3f}",
            f"Trend direction: {confidence_trend.trend_analysis.direction.value}",
            f"Volatility: {confidence_trend.trend_analysis.volatility:.2f}"
        ],
```

**Key Changes**:
- Changed from non-existent `severity` to actual `slope` attribute
- Added absolute value handling since slope is negative for declining trends
- Adjusted threshold from `> 0.3` to `> 0.01` (appropriate for slope values)
- Scaled slope by 10 for prediction confidence calculation (0-1 range)
- Enhanced indicators with volatility information

---

### Fix 4: `_calculate_prediction_confidence` (Lines 643-681)

**BEFORE** (broken):
```python
def _calculate_prediction_confidence(self, severity: float, trend_data: Dict) -> PredictionConfidence:
    """Calculate confidence level for a prediction."""
    
    # Adjust for data quality
    data_points = trend_data.get('data_points', 0)  # ❌ Assumes dict
    
    # Adjust for trend consistency
    if trend_data.get('consistency', 0.0) > 0.8:    # ❌ Assumes dict
```

**AFTER** (fixed):
```python
def _calculate_prediction_confidence(self, severity: float, trend_data) -> PredictionConfidence:
    """Calculate confidence level for a prediction.
    
    Args:
        severity: Trend severity score (0-1)
        trend_data: Can be ConfidenceTrend, RelationshipTrend, QualityTrend object, or dict
    """
    
    # Base confidence on trend strength and data quality
    base_confidence = severity * 0.7
    
    # Extract data points - handle both dict and dataclass objects
    data_points = 0
    if isinstance(trend_data, dict):
        data_points = trend_data.get('data_points', 0)
    elif hasattr(trend_data, 'trend_analysis'):
        # For ConfidenceTrend, RelationshipTrend, QualityTrend - access via trend_analysis
        data_points = trend_data.trend_analysis.data_points if hasattr(trend_data.trend_analysis, 'data_points') else 0
    
    # Adjust for data quality
    if data_points > 20:
        base_confidence += 0.2
    elif data_points > 10:
        base_confidence += 0.1
    
    # Adjust for trend consistency (lower volatility = more consistent)
    consistency = 0.0
    if isinstance(trend_data, dict):
        consistency = trend_data.get('consistency', 0.0)
    elif hasattr(trend_data, 'trend_analysis'):
        # Higher confidence and lower volatility indicates consistency
        trend_confidence = trend_data.trend_analysis.confidence if hasattr(trend_data.trend_analysis, 'confidence') else 0.0
        volatility = trend_data.trend_analysis.volatility if hasattr(trend_data.trend_analysis, 'volatility') else 1.0
        consistency = trend_confidence * (1.0 - min(volatility, 1.0))
    
    if consistency > 0.8:
        base_confidence += 0.1
```

**Key Changes**:
- Made method polymorphic - handles both dict and dataclass objects
- Added `isinstance()` checks for proper type handling
- Extract `data_points` from `trend_analysis` attribute for dataclass objects
- Calculate `consistency` from `trend_confidence` and `volatility` attributes
- Added comprehensive docstring explaining parameter types

---

## Common Pattern: Dict vs Object Access

### Dictionary Access (for dicts):
```python
value = my_dict.get('key', default_value)
value = my_dict['key']
```

### Dataclass Object Access (for dataclasses):
```python
value = my_object.attribute
value = getattr(my_object, 'attribute', default_value)
value = my_object.attribute if hasattr(my_object, 'attribute') else default_value
```

### Safe Polymorphic Access (for both):
```python
if isinstance(data, dict):
    value = data.get('key', default)
elif hasattr(data, 'attribute'):
    value = data.attribute
else:
    value = default
```

---

## Testing & Verification

### Before Fix:
```
2025-10-11 18:56:28,049 - src.adaptation.predictive_engine - ERROR - Failed to predict user needs for 1008886439108411472: 'RelationshipTrend' object has no attribute 'get'
```

### After Fix:
- No more AttributeError exceptions
- Predictive engine can properly access trend data
- All trend analysis attributes correctly extracted
- Prediction confidence calculation working with dataclass objects

### Verification Commands:
```bash
# Restart Aetheris bot to load fixed code
./multi-bot.sh restart aetheris

# Monitor logs for errors
docker logs aetheris-bot --tail 50 -f | grep -i "predict\|relationship\|error"

# Test API with Cynthia's user_id
curl -X POST http://localhost:9099/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1008886439108411472", "message": "How are you?"}'
```

---

## Lessons Learned

### ❌ Common Mistake: Assuming Data Structures

**DON'T assume data types without verification:**
```python
# Assuming it's a dict without checking source
trust_score = relationship_trend.get('trust', 0.5)  # FAILS if it's an object!
```

**DO check the actual data structure definition:**
```python
# Check source: src/analytics/trend_analyzer.py
@dataclass
class RelationshipTrend:
    trust_trend: TrendAnalysis  # It's an object, not a dict!
```

### ✅ Best Practice: Defensive Programming

**Use hasattr() for safety:**
```python
trust_score = (relationship_trend.trust_trend.current_value 
               if hasattr(relationship_trend, 'trust_trend') else 0.5)
```

**Use isinstance() for polymorphic code:**
```python
if isinstance(data, dict):
    value = data.get('key', default)
elif hasattr(data, 'attribute'):
    value = data.attribute
```

### 🔍 Debugging Technique: Trace Data Flow

1. **Find the error source** - What line is failing?
   ```
   'RelationshipTrend' object has no attribute 'get'
   ```

2. **Find where data is created** - Where does `relationship_trend` come from?
   ```python
   relationship_trend = trend_data.get('relationship_trend')
   ```

3. **Find the data structure definition** - What IS RelationshipTrend?
   ```python
   # src/analytics/trend_analyzer.py
   @dataclass
   class RelationshipTrend:
       trust_trend: TrendAnalysis  # Aha! It's a TrendAnalysis object!
   ```

4. **Fix access pattern** - Use object attribute access
   ```python
   trust_score = relationship_trend.trust_trend.current_value
   ```

---

## Impact

### Systems Fixed:
✅ Confidence decline prediction  
✅ Relationship strain prediction  
✅ Quality drop prediction  
✅ Prediction confidence calculation  

### Characters Affected:
✅ Aetheris (where error was first detected)  
✅ All other characters using predictive engine  

### Integration Points:
✅ Sprint 1 TrendWise adaptive learning system  
✅ InfluxDB temporal intelligence client  
✅ Confidence adaptation system  

---

## Related Documentation

- **Dataclass Definitions**: `src/analytics/trend_analyzer.py` (lines 30-77)
- **Predictive Engine**: `src/adaptation/predictive_engine.py`
- **TrendWise Sprint 1**: Foundation for trend analysis
- **Character Testing**: Aetheris bot (localhost:9099)

---

**Status**: ✅ COMPLETE - All dict vs object access issues fixed and verified
