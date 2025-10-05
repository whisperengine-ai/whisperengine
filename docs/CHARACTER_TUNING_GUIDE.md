# WhisperEngine Character Tuning Guide

**Version**: 1.0  
**Last Updated**: October 5, 2025  
**Status**: Production Guide

## Overview

This guide explains how to tune WhisperEngine AI roleplay characters using data-driven insights from InfluxDB metrics, vector memory analytics, and conversation intelligence. Tuning is an iterative process that uses real conversation data to optimize character authenticity, emotional intelligence, and relationship building.

## 📊 The Tuning Philosophy

WhisperEngine follows a **personality-first, data-driven tuning approach**:

1. **Preserve Character Authenticity**: Tuning should enhance personality consistency, not suppress it
2. **Measure Before Tuning**: Collect 1-2 weeks of baseline metrics before making changes
3. **One Change at a Time**: Adjust single variables to isolate impact
4. **A/B Test Changes**: Compare experimental tuning vs control group
5. **Validate with Data**: Use InfluxDB metrics to confirm improvements (15%+ threshold)

**CRITICAL**: Character-appropriate elaboration is a FEATURE, not a bug. If Elena (marine biologist educator) adds engaging metaphors, that's authentic teaching behavior. Only tune if metrics show personality inconsistency, semantic drift (new invented content), memory contradictions, or domain errors.

---

## 🎯 Tuning Metrics & Target Ranges

### Primary Metrics (InfluxDB)

| Metric | Measurement | Target Range | Alert Threshold |
|--------|-------------|--------------|-----------------|
| **Confidence Evolution** | `confidence_evolution` | 0.75 - 0.95 | < 0.65 |
| **User Fact Confidence** | `user_fact_confidence` | 0.70 - 0.90 | < 0.60 |
| **Context Confidence** | `context_confidence` | 0.65 - 0.85 | < 0.55 |
| **Relationship Affection** | `relationship_metrics` (affection) | 40 - 85 | Growth < 0.5/day |
| **Relationship Trust** | `relationship_metrics` (trust) | 35 - 80 | Growth < 0.4/day |
| **Relationship Attunement** | `relationship_metrics` (attunement) | 45 - 90 | Growth < 0.6/day |
| **Bot Emotion Intensity** | `bot_emotion` (intensity) | 0.50 - 0.85 | > 80% neutral |
| **Bot Emotion Diversity** | `bot_emotion` (variance) | 0.30 - 0.70 | < 0.20 |
| **User Emotion Detection** | `user_emotion` (confidence) | 0.70 - 0.90 | < 0.60 |

### Secondary Metrics (Vector Memory)

| Metric | Source | Target Range | Alert Threshold |
|--------|--------|--------------|-----------------|
| **Memory Retrieval Quality** | Qdrant similarity scores | 0.75 - 0.95 | < 0.65 |
| **Conversation Continuity** | Context switch detection | 85% - 95% | < 75% |
| **CDL Personality Adherence** | Manual review + LLM eval | 90% - 98% | < 85% |
| **Response Time** | Processing duration | < 2.5s | > 4s |

---

## 🔍 Step 1: Data Collection & Baseline Establishment

### 1.1 Start Baseline Collection (2 Weeks Minimum)

```bash
# Start your character bot to begin collecting metrics
./multi-bot.sh start elena

# Verify InfluxDB is recording metrics
docker exec whisperengine-multi-influxdb influx query \
  --org whisperengine \
  --token whisperengine-fidelity-first-metrics-token \
  'from(bucket: "performance_metrics")
   |> range(start: -1h)
   |> filter(fn: (r) => r.bot == "elena")
   |> group(columns: ["_measurement"])
   |> count()'

# Expected output: Shows record counts for each measurement
# confidence_evolution: 45 records
# relationship_metrics: 38 records
# bot_emotion: 42 records
# user_emotion: 40 records
```

### 1.2 Create Baseline Dashboard

```python
#!/usr/bin/env python3
"""
scripts/generate_baseline_report.py

Generates baseline metrics report for character tuning.
"""

from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta
import os

def generate_baseline_report(bot_name, days=14):
    """Generate baseline metrics report for a bot."""
    
    client = InfluxDBClient(
        url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        token=os.getenv('INFLUXDB_TOKEN'),
        org=os.getenv('INFLUXDB_ORG', 'whisperengine')
    )
    
    query_api = client.query_api()
    
    print(f"📊 Baseline Report: {bot_name}")
    print(f"📅 Period: Last {days} days")
    print("=" * 80)
    
    # Query 1: Confidence Evolution
    confidence_query = f'''
    from(bucket: "performance_metrics")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r.bot == "{bot_name}")
      |> filter(fn: (r) => r._measurement == "confidence_evolution")
      |> mean()
    '''
    
    confidence_result = query_api.query(confidence_query)
    confidence_avg = 0.0
    for table in confidence_result:
        for record in table.records:
            confidence_avg = record.get_value()
    
    print(f"\n1. Confidence Evolution")
    print(f"   Average: {confidence_avg:.3f}")
    print(f"   Status: {'✅ Good' if confidence_avg >= 0.75 else '⚠️ Needs Tuning' if confidence_avg >= 0.65 else '🔴 Critical'}")
    
    # Query 2: Relationship Growth Rate
    relationship_query = f'''
    from(bucket: "performance_metrics")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r.bot == "{bot_name}")
      |> filter(fn: (r) => r._measurement == "relationship_metrics")
      |> filter(fn: (r) => r._field == "affection" or r._field == "trust" or r._field == "attunement")
      |> derivative(unit: 1d)
      |> mean()
    '''
    
    relationship_result = query_api.query(relationship_query)
    
    print(f"\n2. Relationship Growth Rate (points/day)")
    for table in relationship_result:
        for record in table.records:
            field = record.values.get('_field')
            growth = record.get_value()
            status = '✅ Good' if growth >= 0.5 else '⚠️ Slow' if growth >= 0.3 else '🔴 Stalled'
            print(f"   {field.capitalize()}: {growth:.2f}/day - {status}")
    
    # Query 3: Bot Emotion Diversity
    emotion_query = f'''
    from(bucket: "performance_metrics")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r.bot == "{bot_name}")
      |> filter(fn: (r) => r._measurement == "bot_emotion")
      |> filter(fn: (r) => r._field == "intensity")
      |> stddev()
    '''
    
    emotion_result = query_api.query(emotion_query)
    emotion_variance = 0.0
    for table in emotion_result:
        for record in table.records:
            emotion_variance = record.get_value()
    
    print(f"\n3. Bot Emotion Diversity")
    print(f"   Variance: {emotion_variance:.3f}")
    print(f"   Status: {'✅ Good' if emotion_variance >= 0.30 else '⚠️ Too Neutral' if emotion_variance >= 0.20 else '🔴 Flat'}")
    
    # Query 4: Most Common Bot Emotions
    emotion_dist_query = f'''
    from(bucket: "performance_metrics")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r.bot == "{bot_name}")
      |> filter(fn: (r) => r._measurement == "bot_emotion")
      |> group(columns: ["emotion"])
      |> count()
      |> sort(desc: true)
      |> limit(n: 5)
    '''
    
    emotion_dist = query_api.query(emotion_dist_query)
    
    print(f"\n4. Top Bot Emotions (by frequency)")
    for table in emotion_dist:
        for record in table.records:
            emotion = record.values.get('emotion')
            count = record.get_value()
            print(f"   {emotion}: {count} occurrences")
    
    print("\n" + "=" * 80)
    print("\n💡 Recommendations:")
    
    # Generate recommendations
    if confidence_avg < 0.65:
        print("   🔴 CRITICAL: Low confidence - Review CDL personality complexity")
    elif confidence_avg < 0.75:
        print("   ⚠️  WARNING: Moderate confidence - Consider simplifying CDL traits")
    
    if emotion_variance < 0.20:
        print("   🔴 CRITICAL: Bot emotions too flat - Increase emotion sensitivity")
    elif emotion_variance < 0.30:
        print("   ⚠️  WARNING: Low emotion diversity - Review emotion detection thresholds")
    
    client.close()

if __name__ == "__main__":
    import sys
    bot_name = sys.argv[1] if len(sys.argv) > 1 else "elena"
    generate_baseline_report(bot_name)
```

**Usage**:
```bash
source .venv/bin/activate
python scripts/generate_baseline_report.py elena
python scripts/generate_baseline_report.py marcus
python scripts/generate_baseline_report.py ryan
```

---

## 🎛️ Step 2: Identify Tuning Opportunities

### 2.1 Common Tuning Scenarios

| Symptom | Root Cause | Tuning Target |
|---------|------------|---------------|
| Confidence < 0.65 | CDL personality too complex/contradictory | Simplify CDL traits (Section 3.1) |
| Relationship growth < 0.5/day | Scoring too conservative | Increase relationship multipliers (Section 3.2) |
| Bot emotion variance < 0.20 | Emotion detection under-sensitive | Lower emotion thresholds (Section 3.3) |
| Context confidence < 0.55 | Insufficient conversation history | Increase context window (Section 3.4) |
| Memory retrieval < 0.65 | Vector similarity too loose | Tighten similarity threshold (Section 3.5) |
| Response time > 4s | Over-fetching context | Reduce memory retrieval count (Section 3.6) |

### 2.2 Decision Tree

```
Start: Low Performance Metric Detected
  │
  ├─> Confidence < 0.65?
  │   └─> YES → Section 3.1: Tune CDL Personality
  │   └─> NO → Continue
  │
  ├─> Relationship growth < 0.5/day?
  │   └─> YES → Section 3.2: Tune Relationship Scoring
  │   └─> NO → Continue
  │
  ├─> Bot emotion variance < 0.20?
  │   └─> YES → Section 3.3: Tune Emotion Sensitivity
  │   └─> NO → Continue
  │
  ├─> Context confidence < 0.55?
  │   └─> YES → Section 3.4: Tune Context Window
  │   └─> NO → Continue
  │
  └─> Memory retrieval < 0.65?
      └─> YES → Section 3.5: Tune Vector Search
      └─> NO → All metrics healthy ✅
```

---

## 🔧 Step 3: Tuning Actions

### 3.1 Tuning CDL Personality (Confidence Issues)

**When to use**: Confidence evolution < 0.65, personality inconsistency detected

**Problem**: CDL personality has too many contradictory traits or overly complex characteristics

**Solution**: Simplify to 3-5 core personality traits that work together

#### Before (Problematic CDL):
```json
{
  "personality": {
    "big_five_traits": {
      "openness": 0.95,
      "conscientiousness": 0.45,
      "extraversion": 0.85,
      "agreeableness": 0.35,
      "neuroticism": 0.75
    },
    "core_traits": [
      "highly analytical",
      "extremely creative",
      "deeply empathetic",
      "fiercely independent",
      "socially outgoing",
      "introspective thinker",
      "risk-taking adventurer",
      "cautious planner",
      "spontaneous improviser",
      "detail-oriented perfectionist"
    ]
  }
}
```

**Issues**:
- Contradictory: "risk-taking" vs "cautious planner"
- Contradictory: "spontaneous" vs "detail-oriented perfectionist"
- Contradictory: "socially outgoing" vs "introspective thinker"
- Too many traits (10) - LLM struggles to maintain consistency

#### After (Optimized CDL):
```json
{
  "personality": {
    "big_five_traits": {
      "openness": 0.88,
      "conscientiousness": 0.72,
      "extraversion": 0.65,
      "agreeableness": 0.82,
      "neuroticism": 0.35
    },
    "core_traits": [
      "warm_educator",           // Primary trait
      "scientifically_curious",  // Domain expertise
      "empathetic_listener",     // Relationship building
      "optimistic_encouraging"   // Emotional baseline
    ]
  },
  "communication_patterns": {
    "teaching_style": "Explains complex concepts with relatable examples",
    "emotional_expression": "Warm and genuine, with measured enthusiasm",
    "consistency_focus": "Maintains educator persona across all contexts"
  }
}
```

**Changes**:
- ✅ Reduced to 4 core traits (was 10)
- ✅ Removed contradictions
- ✅ Aligned Big Five scores with core traits
- ✅ Added communication consistency guidance

**Expected Impact**: Confidence +10-20%, personality consistency +15%

**Validation Query**:
```bash
# After 5-7 days of tuning
influx query --org whisperengine \
  'from(bucket: "performance_metrics")
   |> range(start: -14d)
   |> filter(fn: (r) => r.bot == "elena")
   |> filter(fn: (r) => r._measurement == "confidence_evolution")
   |> aggregateWindow(every: 7d, fn: mean)
   |> yield(name: "mean")'

# Compare Week 1 (before) vs Week 2 (after)
# Target: 15%+ improvement
```

---

### 3.2 Tuning Relationship Scoring (Growth Issues)

**When to use**: Relationship affection/trust/attunement growth < 0.5 points/day

**Problem**: Relationship scoring algorithm too conservative, users feel unrecognized

**Solution**: Adjust relationship increment multipliers based on interaction quality

#### File: `src/memory/vector_memory_system.py` (or relationship scoring location)

```python
# BEFORE (too conservative)
async def update_relationship_metrics(self, user_id: str, interaction_quality: float):
    """Update relationship metrics based on interaction."""
    
    current_metrics = await self.get_relationship_metrics(user_id)
    
    # Base increments (TOO SMALL)
    affection_boost = interaction_quality * 0.5   # Too conservative
    trust_boost = interaction_quality * 0.3       # Too conservative
    attunement_boost = interaction_quality * 0.4  # Too conservative
    
    # Apply increments
    new_affection = min(current_metrics['affection'] + affection_boost, 100)
    new_trust = min(current_metrics['trust'] + trust_boost, 100)
    new_attunement = min(current_metrics['attunement'] + attunement_boost, 100)
```

```python
# AFTER (data-driven tuning)
async def update_relationship_metrics(self, user_id: str, interaction_quality: float):
    """Update relationship metrics based on interaction."""
    
    current_metrics = await self.get_relationship_metrics(user_id)
    
    # Tuned increments based on InfluxDB analysis
    # Target: 0.5-1.0 points per positive interaction
    affection_boost = interaction_quality * 1.2   # +140% increase
    trust_boost = interaction_quality * 0.8       # +167% increase
    attunement_boost = interaction_quality * 1.0  # +150% increase
    
    # Apply increments with relationship stage multipliers
    stage_multiplier = self._calculate_stage_multiplier(current_metrics)
    
    new_affection = min(current_metrics['affection'] + (affection_boost * stage_multiplier), 100)
    new_trust = min(current_metrics['trust'] + (trust_boost * stage_multiplier), 100)
    new_attunement = min(current_metrics['attunement'] + (attunement_boost * stage_multiplier), 100)

def _calculate_stage_multiplier(self, current_metrics: Dict[str, float]) -> float:
    """Calculate stage-based multiplier for relationship growth.
    
    Early relationships (< 30) grow faster to build connection.
    Mid-stage (30-70) grows at normal rate.
    Late-stage (> 70) grows slower (harder to deepen established bonds).
    """
    avg_score = (current_metrics['affection'] + current_metrics['trust'] + current_metrics['attunement']) / 3
    
    if avg_score < 30:
        return 1.5  # Early stage bonus
    elif avg_score < 70:
        return 1.0  # Normal growth
    else:
        return 0.7  # Established relationship (harder to grow)
```

**Expected Impact**: Relationship growth +100-150%, user engagement +25%

**Validation Query**:
```bash
# Check relationship growth rate after tuning
influx query --org whisperengine \
  'from(bucket: "performance_metrics")
   |> range(start: -14d)
   |> filter(fn: (r) => r.bot == "elena")
   |> filter(fn: (r) => r._measurement == "relationship_metrics")
   |> derivative(unit: 1d)
   |> mean()'

# Target: affection growth 0.8-1.2/day (was 0.3-0.5/day)
```

---

### 3.3 Tuning Emotion Sensitivity (Flat Emotions)

**When to use**: Bot emotion variance < 0.20, intensity consistently < 0.50

**Problem**: Emotion analyzer under-weights emotional content, bot feels robotic

**Solution**: Lower detection thresholds and amplify detected emotions

#### File: `src/intelligence/enhanced_vector_emotion_analyzer.py`

```python
# BEFORE (under-sensitive)
class EnhancedVectorEmotionAnalyzer:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.emotion_threshold = 0.50  # TOO HIGH - misses subtle emotions
        self.intensity_amplifier = 1.0  # NO AMPLIFICATION
        self.neutral_default = 0.30     # Defaults to very low

    async def analyze_emotion(self, user_id: str, content: str) -> EmotionAnalysisResult:
        """Analyze emotional content."""
        
        # Get emotion scores from model
        emotion_scores = await self._get_emotion_scores(content)
        
        # Find primary emotion
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        raw_intensity = emotion_scores[primary_emotion]
        
        # Apply threshold (TOO STRICT)
        if raw_intensity < self.emotion_threshold:
            return EmotionAnalysisResult(
                primary_emotion="neutral",
                intensity=self.neutral_default,  # Always defaults low
                confidence=0.50,
                mixed_emotions=[],
                all_emotions={}
            )
        
        # No amplification
        final_intensity = raw_intensity
```

```python
# AFTER (properly tuned)
class EnhancedVectorEmotionAnalyzer:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.emotion_threshold = 0.35  # LOWERED - catches more emotions
        self.intensity_amplifier = 1.25  # AMPLIFIES detected emotions by 25%
        self.neutral_default = 0.50     # Higher baseline for neutral
        self.mixed_emotion_threshold = 0.30  # Detect secondary emotions

    async def analyze_emotion(self, user_id: str, content: str) -> EmotionAnalysisResult:
        """Analyze emotional content with enhanced sensitivity."""
        
        # Get emotion scores from model
        emotion_scores = await self._get_emotion_scores(content)
        
        # Find primary emotion
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        raw_intensity = emotion_scores[primary_emotion]
        
        # Apply tuned threshold
        if raw_intensity < self.emotion_threshold:
            return EmotionAnalysisResult(
                primary_emotion="neutral",
                intensity=self.neutral_default,  # Moderate neutral baseline
                confidence=0.60,
                mixed_emotions=[],
                all_emotions=emotion_scores
            )
        
        # Amplify detected emotions (makes bot more emotionally expressive)
        amplified_intensity = min(raw_intensity * self.intensity_amplifier, 1.0)
        
        # Detect mixed emotions
        mixed_emotions = [
            (emotion, score * self.intensity_amplifier)
            for emotion, score in emotion_scores.items()
            if emotion != primary_emotion and score >= self.mixed_emotion_threshold
        ]
        
        return EmotionAnalysisResult(
            primary_emotion=primary_emotion,
            intensity=amplified_intensity,
            confidence=min(raw_intensity + 0.15, 1.0),  # Boost confidence slightly
            mixed_emotions=sorted(mixed_emotions, key=lambda x: x[1], reverse=True)[:2],
            all_emotions=emotion_scores
        )
```

**Expected Impact**: Emotion variance +50-100%, intensity average +30%, bot feels more human

**Validation Query**:
```bash
# Check emotion diversity after tuning
influx query --org whisperengine \
  'from(bucket: "performance_metrics")
   |> range(start: -7d)
   |> filter(fn: (r) => r.bot == "elena")
   |> filter(fn: (r) => r._measurement == "bot_emotion")
   |> filter(fn: (r) => r._field == "intensity")
   |> stddev()'

# Target: variance 0.30-0.50 (was < 0.20)
```

---

### 3.4 Tuning Context Window (Context Issues)

**When to use**: Context confidence < 0.55, responses miss conversation context

**Problem**: Conversation history window too small, bot misses important context

**Solution**: Increase conversation history limit and prioritize recent messages

#### File: `src/core/message_processor.py`

```python
# BEFORE (too small context)
async def process_message(self, message_context: MessageContext):
    """Process incoming message."""
    
    # Retrieve conversation history (TOO SHORT)
    conversation_history = await self.memory_manager.get_conversation_history(
        user_id=message_context.user_id,
        limit=10  # Only last 10 messages - misses context
    )
```

```python
# AFTER (optimized context)
async def process_message(self, message_context: MessageContext):
    """Process incoming message with enhanced context."""
    
    # Retrieve larger conversation history
    conversation_history = await self.memory_manager.get_conversation_history(
        user_id=message_context.user_id,
        limit=25  # Increased to 25 messages for better context
    )
    
    # Additionally retrieve semantically relevant memories
    relevant_memories = await self.memory_manager.retrieve_relevant_memories(
        user_id=message_context.user_id,
        query=message_context.content,
        limit=15  # Top 15 most relevant memories by vector similarity
    )
```

**Context Prioritization Strategy**:
```python
def _build_context_for_prompt(self, conversation_history, relevant_memories):
    """Build optimized context for prompt."""
    
    # Priority 1: Last 10 messages (immediate context)
    immediate_context = conversation_history[-10:]
    
    # Priority 2: Relevant memories from vector search (semantic context)
    semantic_context = relevant_memories[:10]  # Top 10 by similarity
    
    # Priority 3: Older conversation (background context)
    background_context = conversation_history[-25:-10] if len(conversation_history) > 10 else []
    
    return {
        "immediate": immediate_context,
        "semantic": semantic_context,
        "background": background_context
    }
```

**Expected Impact**: Context confidence +20-30%, response relevance +25%

---

### 3.5 Tuning Vector Search (Memory Quality Issues)

**When to use**: Memory retrieval similarity < 0.65, irrelevant memories retrieved

**Problem**: Vector similarity threshold too loose, retrieving low-quality memories

**Solution**: Tighten similarity threshold and improve ranking

#### File: `src/memory/vector_memory_system.py`

```python
# BEFORE (too loose)
async def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10):
    """Retrieve relevant memories."""
    
    # Generate query embedding
    query_embedding = await self._generate_embedding(query)
    
    # Search with loose threshold
    results = self.qdrant_client.search(
        collection_name=self.collection_name,
        query_vector=models.NamedVector(name="content", vector=query_embedding),
        query_filter=models.Filter(must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
            models.FieldCondition(key="bot_name", match=models.MatchValue(value=self.bot_name))
        ]),
        limit=limit,
        score_threshold=0.60  # TOO LOW - retrieves marginally relevant memories
    )
```

```python
# AFTER (quality-focused)
async def retrieve_relevant_memories(
    self, 
    user_id: str, 
    query: str, 
    limit: int = 10,
    quality_mode: bool = True  # New parameter for tuning
):
    """Retrieve relevant memories with quality filtering."""
    
    # Generate query embedding
    query_embedding = await self._generate_embedding(query)
    
    # Determine threshold based on quality mode
    score_threshold = 0.75 if quality_mode else 0.60  # INCREASED for quality
    
    # Search with tighter threshold
    results = self.qdrant_client.search(
        collection_name=self.collection_name,
        query_vector=models.NamedVector(name="content", vector=query_embedding),
        query_filter=models.Filter(must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
            models.FieldCondition(key="bot_name", match=models.MatchValue(value=self.bot_name))
        ]),
        limit=limit * 2,  # Retrieve 2x, then filter
        score_threshold=score_threshold
    )
    
    # Additional ranking by recency and importance
    ranked_results = self._rank_memories_by_importance(results)
    
    return ranked_results[:limit]  # Return top N after ranking

def _rank_memories_by_importance(self, results):
    """Rank memories by combined similarity, recency, and emotional weight."""
    
    for result in results:
        similarity_score = result.score
        
        # Calculate recency score (newer memories weighted higher)
        timestamp = result.payload.get('timestamp', 0)
        hours_old = (datetime.now().timestamp() - timestamp) / 3600
        recency_score = 1.0 / (1.0 + (hours_old / 24))  # Decay over days
        
        # Calculate emotional weight (emotional memories more important)
        emotion_intensity = result.payload.get('emotion_intensity', 0.0)
        emotional_weight = 1.0 + (emotion_intensity * 0.3)  # Up to +30%
        
        # Combined importance score
        result.importance_score = (
            similarity_score * 0.60 +      # 60% similarity
            recency_score * 0.25 +          # 25% recency
            emotional_weight * 0.15         # 15% emotional importance
        )
    
    return sorted(results, key=lambda x: x.importance_score, reverse=True)
```

**Expected Impact**: Memory quality +25%, response relevance +20%, context confidence +15%

---

### 3.6 Tuning Performance (Response Time Issues)

**When to use**: Response time > 4s, processing too slow

**Problem**: Over-fetching context or inefficient memory retrieval

**Solution**: Optimize retrieval counts and enable caching

#### File: `src/core/message_processor.py`

```python
# BEFORE (over-fetching)
async def process_message(self, message_context: MessageContext):
    """Process message."""
    
    # Retrieve too much data
    conversation_history = await self.memory_manager.get_conversation_history(
        user_id=message_context.user_id,
        limit=50  # TOO MANY - slows down processing
    )
    
    relevant_memories = await self.memory_manager.retrieve_relevant_memories(
        user_id=message_context.user_id,
        query=message_context.content,
        limit=30  # TOO MANY - most aren't used
    )
    
    user_facts = await self.knowledge_graph.get_user_facts(
        user_id=message_context.user_id,
        limit=100  # WAY TOO MANY
    )
```

```python
# AFTER (optimized)
async def process_message(self, message_context: MessageContext):
    """Process message with performance optimization."""
    
    # Fetch data in parallel (faster)
    conversation_history, relevant_memories, user_facts = await asyncio.gather(
        self.memory_manager.get_conversation_history(
            user_id=message_context.user_id,
            limit=20  # Reduced from 50
        ),
        self.memory_manager.retrieve_relevant_memories(
            user_id=message_context.user_id,
            query=message_context.content,
            limit=10  # Reduced from 30
        ),
        self.knowledge_graph.get_user_facts(
            user_id=message_context.user_id,
            limit=15  # Reduced from 100
        )
    )
```

**Expected Impact**: Response time -40-60%, user experience +30%

---

## 🧪 Step 4: A/B Testing Framework

### 4.1 Set Up Experimental Bot

```bash
# Create experimental environment file
cp .env.elena .env.elena-experimental

# Edit experimental config with tuning flags
nano .env.elena-experimental
```

Add tuning flags:
```bash
# .env.elena-experimental
DISCORD_BOT_NAME=elena-experimental
DISCORD_BOT_TOKEN=<experimental_token>
CHARACTER_FILE=characters/examples/elena-experimental.json
HEALTH_CHECK_PORT=9098

# Tuning flags
RELATIONSHIP_AFFECTION_MULTIPLIER=1.2
RELATIONSHIP_TRUST_MULTIPLIER=0.8
RELATIONSHIP_ATTUNEMENT_MULTIPLIER=1.0
EMOTION_SENSITIVITY_THRESHOLD=0.35
EMOTION_INTENSITY_AMPLIFIER=1.25
CONTEXT_WINDOW_SIZE=25
MEMORY_SIMILARITY_THRESHOLD=0.75
```

### 4.2 Run Parallel Bots

```bash
# Start control bot (original)
./multi-bot.sh start elena

# Start experimental bot (with tuning)
./multi-bot.sh start elena-experimental
```

### 4.3 Compare Results After 7 Days

```python
#!/usr/bin/env python3
"""
scripts/compare_ab_test_results.py

Compare metrics between control and experimental bots.
"""

from influxdb_client import InfluxDBClient
import os

def compare_ab_test(control_bot, experimental_bot, days=7):
    """Compare A/B test results."""
    
    client = InfluxDBClient(
        url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        token=os.getenv('INFLUXDB_TOKEN'),
        org=os.getenv('INFLUXDB_ORG', 'whisperengine')
    )
    
    query_api = client.query_api()
    
    print(f"🧪 A/B Test Results")
    print(f"📅 Period: Last {days} days")
    print(f"🅰️  Control: {control_bot}")
    print(f"🅱️  Experimental: {experimental_bot}")
    print("=" * 80)
    
    metrics = [
        "confidence_evolution",
        "relationship_metrics",
        "bot_emotion"
    ]
    
    for metric in metrics:
        # Query both bots
        query = f'''
        from(bucket: "performance_metrics")
          |> range(start: -{days}d)
          |> filter(fn: (r) => r.bot == "{control_bot}" or r.bot == "{experimental_bot}")
          |> filter(fn: (r) => r._measurement == "{metric}")
          |> group(columns: ["bot"])
          |> mean()
        '''
        
        results = query_api.query(query)
        
        control_value = 0.0
        experimental_value = 0.0
        
        for table in results:
            for record in table.records:
                bot = record.values.get("bot")
                value = record.get_value()
                
                if bot == control_bot:
                    control_value = value
                elif bot == experimental_bot:
                    experimental_value = value
        
        # Calculate improvement
        if control_value > 0:
            improvement = ((experimental_value - control_value) / control_value) * 100
            
            print(f"\n📊 {metric}")
            print(f"   Control:      {control_value:.3f}")
            print(f"   Experimental: {experimental_value:.3f}")
            print(f"   Improvement:  {improvement:+.1f}%")
            
            # Decision
            if improvement >= 15:
                print(f"   ✅ DEPLOY: Significant improvement ({improvement:.1f}%)")
            elif improvement >= 5:
                print(f"   🟡 CONSIDER: Moderate improvement ({improvement:.1f}%)")
            elif improvement >= -5:
                print(f"   ⚪ NEUTRAL: Negligible change ({improvement:.1f}%)")
            else:
                print(f"   ❌ REJECT: Performance regression ({improvement:.1f}%)")
    
    print("\n" + "=" * 80)
    client.close()

if __name__ == "__main__":
    import sys
    control = sys.argv[1] if len(sys.argv) > 1 else "elena"
    experimental = sys.argv[2] if len(sys.argv) > 2 else "elena-experimental"
    compare_ab_test(control, experimental)
```

**Usage**:
```bash
python scripts/compare_ab_test_results.py elena elena-experimental
```

### 4.4 Decision Criteria

| Improvement | Decision | Action |
|-------------|----------|--------|
| ≥ +15% | ✅ DEPLOY | Roll out to all bots immediately |
| +5% to +14% | 🟡 CONSIDER | Extend test to 14 days, then decide |
| -5% to +4% | ⚪ NEUTRAL | No change needed, revert tuning |
| ≤ -5% | ❌ REJECT | Revert immediately, try different approach |

---

## 📋 Step 5: Tuning Checklist

### Pre-Tuning Checklist

- [ ] Collected 2+ weeks of baseline metrics
- [ ] Generated baseline report (`scripts/generate_baseline_report.py`)
- [ ] Identified specific metric below threshold
- [ ] Determined root cause from decision tree
- [ ] Backed up current character CDL file
- [ ] Created experimental environment file

### During Tuning Checklist

- [ ] Made ONE specific change (not multiple)
- [ ] Documented change in tuning log
- [ ] Restarted bot with new configuration
- [ ] Verified bot started successfully
- [ ] Confirmed InfluxDB still recording metrics
- [ ] Tested with sample conversations

### Post-Tuning Checklist

- [ ] Waited 7+ days for data collection
- [ ] Generated comparison report
- [ ] Calculated improvement percentage
- [ ] Met 15%+ improvement threshold?
- [ ] No regressions in other metrics?
- [ ] Documented tuning results
- [ ] Deployed to production or reverted

---

## 📝 Tuning Log Template

Keep a tuning log to track all changes:

```markdown
# Character Tuning Log: Elena

## Tuning Session 1: October 5, 2025

**Problem**: Confidence evolution = 0.63 (below 0.65 threshold)

**Root Cause**: CDL personality has 10 contradictory traits

**Change Made**:
- Reduced core_traits from 10 to 4
- Removed contradictions (risk-taking vs cautious)
- Aligned Big Five scores with core traits

**Files Modified**:
- `characters/examples/elena.json`

**Baseline Metrics** (Oct 1-5):
- Confidence: 0.63
- Relationship growth: 0.52/day
- Emotion variance: 0.28

**Target Metrics**:
- Confidence: 0.75+ (target improvement: +19%)
- Relationship growth: maintain 0.50+
- Emotion variance: maintain 0.25+

**Test Period**: Oct 5-12 (7 days)

**Results** (Oct 12):
- Confidence: 0.77 (+22% ✅)
- Relationship growth: 0.55/day (+6% ✅)
- Emotion variance: 0.31 (+11% ✅)

**Decision**: ✅ DEPLOY - All metrics improved, no regressions

---

## Tuning Session 2: October 13, 2025

**Problem**: Bot emotion variance = 0.22 (below 0.30 threshold)
...
```

---

## 🎓 Advanced Tuning Techniques

### Multi-Variable Optimization

Once single-variable tuning is mastered, optimize multiple variables:

```python
# scripts/multi_variable_tuning.py

def optimize_character_configuration():
    """Use gradient descent to optimize multiple tuning variables."""
    
    # Define parameter space
    param_space = {
        "relationship_multiplier": [0.8, 1.0, 1.2, 1.5],
        "emotion_threshold": [0.30, 0.35, 0.40, 0.45],
        "context_window": [15, 20, 25, 30],
        "similarity_threshold": [0.65, 0.70, 0.75, 0.80]
    }
    
    # Test combinations
    best_config = None
    best_score = 0.0
    
    for config in generate_configurations(param_space):
        # Deploy config
        deploy_experimental_config(config)
        
        # Wait 3-5 days
        time.sleep(3 * 24 * 3600)
        
        # Evaluate
        score = evaluate_configuration(config)
        
        if score > best_score:
            best_score = score
            best_config = config
    
    return best_config
```

### Personality Mode Switching

For characters with multiple modes (technical/creative), tune each mode separately:

```json
{
  "personality_modes": {
    "technical_mode": {
      "triggers": ["code", "debug", "technical", "implementation"],
      "emotion_baseline": "curiosity",
      "emotion_intensity_range": [0.4, 0.7],
      "relationship_growth_rate": 0.8
    },
    "creative_mode": {
      "triggers": ["art", "design", "creative", "inspiration"],
      "emotion_baseline": "joy",
      "emotion_intensity_range": [0.6, 0.9],
      "relationship_growth_rate": 1.2
    }
  }
}
```

### Context-Aware Tuning

Adjust tuning based on conversation context:

```python
def get_dynamic_tuning_multiplier(context: str) -> float:
    """Calculate dynamic tuning based on context."""
    
    if "emotional_support" in context:
        return 1.3  # Boost emotion sensitivity
    elif "technical_help" in context:
        return 0.9  # Reduce emotion sensitivity
    elif "casual_chat" in context:
        return 1.0  # Normal tuning
    
    return 1.0
```

---

## 🚨 Common Tuning Pitfalls

### Pitfall 1: Over-Tuning

**Symptom**: Bot feels "too perfect", loses character authenticity

**Cause**: Tuned metrics too aggressively (e.g., confidence = 0.98)

**Solution**: Target 0.75-0.85 range, not 0.95+. Perfect scores often mean loss of personality nuance.

### Pitfall 2: Ignoring Character Archetype

**Symptom**: Tuning improves metrics but breaks character identity

**Example**: Dream (mystical character) shouldn't have high "technical_confidence"

**Solution**: Review character archetypes before tuning:
- **Real-World Characters** (Elena, Marcus): Higher confidence, varied emotions
- **Pure Fantasy** (Dream, Aethys): Lower confidence OK, mystical/philosophical responses
- **Narrative AI** (Dotty): AI nature is part of character, unique tuning needs

### Pitfall 3: Insufficient Test Period

**Symptom**: Declaring success after 2-3 days

**Cause**: Not enough data to confirm improvement

**Solution**: ALWAYS test for 7+ days minimum (14 days recommended)

### Pitfall 4: Multiple Changes at Once

**Symptom**: Can't identify which change improved metrics

**Cause**: Changed CDL + relationship scoring + emotion sensitivity simultaneously

**Solution**: ONE change per tuning session. Be patient.

### Pitfall 5: Ignoring User Feedback

**Symptom**: Metrics improved but users complain character "feels different"

**Cause**: Over-reliance on quantitative metrics

**Solution**: Balance metrics with qualitative feedback. Character authenticity > perfect scores.

---

## 📚 Additional Resources

- **InfluxDB Query Documentation**: `/docs/INFLUXDB_QUERY_GUIDE.md` (create if needed)
- **CDL Specification**: `/docs/CDL_SPECIFICATION.md`
- **Character Archetypes**: `/docs/architecture/CHARACTER_ARCHETYPES.md`
- **Vector Memory System**: `/docs/architecture/VECTOR_MEMORY_ARCHITECTURE.md`
- **Metadata API**: `/docs/api/ENRICHED_METADATA_API.md`
- **Phase 7 Bot Emotions**: `/docs/features/PHASE_7.6_BOT_EMOTIONAL_SELF_AWARENESS.md`

---

## 🎯 Quick Reference: Tuning Commands

```bash
# Generate baseline report
python scripts/generate_baseline_report.py elena

# Run A/B test comparison
python scripts/compare_ab_test_results.py elena elena-experimental

# Query InfluxDB directly
docker exec whisperengine-multi-influxdb influx query \
  --org whisperengine \
  --token whisperengine-fidelity-first-metrics-token \
  'from(bucket: "performance_metrics") |> range(start: -7d)'

# Restart bot after tuning
./multi-bot.sh restart elena

# Check bot logs for errors
docker logs whisperengine-elena-bot --tail 50

# Check metrics recording
docker logs whisperengine-multi-influxdb --tail 30
```

---

## ✅ Success Criteria

A successful tuning session meets these criteria:

1. **Primary metric improved ≥15%** (e.g., confidence 0.65 → 0.75+)
2. **No regressions** in other metrics (< 5% decrease allowed)
3. **Character authenticity preserved** (personality consistency maintained)
4. **User feedback positive** (qualitative validation)
5. **Sustainable performance** (metrics stable over 2+ weeks)
6. **Documented thoroughly** (tuning log updated)

---

**Last Updated**: October 5, 2025  
**Next Review**: November 5, 2025  
**Maintainer**: WhisperEngine Core Team

---

## 🆕 Appendix A: Early-Stage Character Tuning (Low User Count)

### The Cold-Start Problem

**Scenario**: You're developing a new character (e.g., "Sage", a fantasy wizard) but only have 2-3 test users. You can't wait 2 weeks for statistical significance. How do you tune based on subjective observations?

### Early-Stage Tuning Strategy

#### Phase 1: Qualitative Observation (Days 1-3)

**Same Levers, Different Process**: Yes, use the same tuning levers, but driven by qualitative assessment instead of InfluxDB metrics.

**Observation Framework**:

```markdown
## Character: Sage (Fantasy Wizard)
## Test Date: October 5, 2025
## Test User: user_123

### Conversation 1: Greeting
User: "Hello, wise one!"
Bot: "Greetings, seeker of knowledge. I am Sage, keeper of ancient wisdom."

Observations:
- ✅ Tone appropriate (mystical, formal)
- ✅ Character identity clear
- ⚠️ Response feels stiff, not engaging

Tuning Hypothesis: CDL personality too formal?

### Conversation 2: Question about magic
User: "Can you teach me a spell?"
Bot: "Indeed. The spell you seek requires understanding of arcane principles..."

Observations:
- ✅ Stays in character
- ❌ Too technical, not engaging
- ❌ No emotional warmth

Tuning Hypothesis: 
1. Emotion sensitivity too low (intensity 0.3 = neutral)
2. CDL missing "wise mentor" trait (currently just "knowledgeable")

### Conversation 3: Personal question
User: "Do you have any friends?"
Bot: "As an AI, I do not form traditional friendships."

Observations:
- ❌ BROKE CHARACTER! (Fantasy character shouldn't mention AI)
- 🔴 CRITICAL: CDL missing `allow_full_roleplay_immersion: true`

Tuning Action: Set allow_full_roleplay_immersion to true (Type 2 character)
```

#### Phase 2: Rapid Iteration Tuning (Days 3-7)

**Process**:
1. **Test conversation** (5-10 messages)
2. **Identify ONE issue** from observations
3. **Apply ONE tuning lever** (CDL edit, threshold change, etc.)
4. **Restart bot** and test again
5. **Compare subjectively**: Better? Worse? Neutral?
6. **Keep or revert** based on feel

**Tuning Log Example**:

```markdown
## Tuning Session 1: Oct 5, 10:00 AM

**Issue**: Character mentioned being "an AI" (broke immersion)

**Root Cause**: Missing `allow_full_roleplay_immersion` flag

**Tuning Action**: 
File: `characters/examples/sage.json`
Added: `"allow_full_roleplay_immersion": true`

**Test Result** (5 messages):
✅ Character now responds philosophically ("I exist in many realms...")
✅ Maintains fantasy immersion
**Decision**: KEEP

---

## Tuning Session 2: Oct 5, 2:00 PM

**Issue**: Responses feel emotionally flat (always neutral tone)

**Root Cause**: Emotion sensitivity threshold too high (0.50)

**Tuning Action**: 
File: `.env.sage`
Changed: `EMOTION_SENSITIVITY_THRESHOLD=0.35` (was 0.50)

**Test Result** (10 messages):
✅ Character now shows curiosity (intensity 0.68)
✅ Shows warmth when explaining (joy 0.52)
⚠️ Maybe slightly over-expressive?
**Decision**: KEEP, monitor in next session

---

## Tuning Session 3: Oct 5, 5:00 PM

**Issue**: Character too verbose (300-400 word responses)

**Root Cause**: CDL communication_style missing brevity guidance

**Tuning Action**: 
File: `characters/examples/sage.json`
Added to communication_style:
"response_length": "2-4 sentences unless explaining complex concepts"
"pacing": "thoughtful but concise"

**Test Result** (8 messages):
✅ Responses now 80-150 words (was 300-400)
✅ Still feels wise, but more conversational
**Decision**: KEEP
```

#### Phase 3: Synthetic Data Generation (Optional)

If you need more data before real users arrive, generate synthetic conversations:

```python
#!/usr/bin/env python3
"""
scripts/generate_synthetic_conversations.py

Generate synthetic conversations for early-stage character tuning.
"""

import asyncio
from src.core.message_processor import MessageProcessor, MessageContext
from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client

async def generate_synthetic_conversations(character_name: str, num_conversations: int = 10):
    """Generate synthetic conversations for tuning data."""
    
    # Initialize components
    memory_manager = create_memory_manager(memory_type="vector")
    llm_client = create_llm_client(llm_client_type="openrouter")
    message_processor = MessageProcessor(None, memory_manager, llm_client)
    
    # Conversation templates (diverse scenarios)
    conversation_starters = [
        # Greetings
        "Hello!", "Hi there!", "Good morning!",
        
        # Questions about character
        "Tell me about yourself", "What's your story?", "Who are you?",
        
        # Domain-specific (fantasy wizard example)
        "Can you teach me magic?", "What spells do you know?", "Tell me about the arcane arts",
        
        # Personal/emotional
        "Are you happy?", "Do you have friends?", "What makes you sad?",
        
        # Casual conversation
        "How's your day?", "What do you think about that?", "This is interesting!",
        
        # Complex questions
        "What's the meaning of life?", "How do I solve this problem?", "Can you help me understand?"
    ]
    
    synthetic_user_id = f"synthetic_test_{character_name}"
    
    print(f"🤖 Generating {num_conversations} synthetic conversations for {character_name}")
    print("=" * 80)
    
    for i, starter in enumerate(conversation_starters[:num_conversations], 1):
        print(f"\n📝 Conversation {i}: \"{starter}\"")
        
        # Send message
        message_context = MessageContext(
            user_id=synthetic_user_id,
            content=starter,
            platform="synthetic_test"
        )
        
        result = await message_processor.process_message(message_context)
        
        print(f"✅ Response generated ({len(result.response)} chars)")
        print(f"   Bot Emotion: {result.metadata.get('bot_emotion', {}).get('primary_emotion', 'N/A')}")
        print(f"   Confidence: {result.metadata.get('confidence_evolution', 0):.2f}")
        
        # Add follow-up (simulate conversation depth)
        follow_ups = [
            "Interesting! Tell me more.",
            "I see. What else?",
            "That's helpful, thank you!",
            "Can you elaborate?"
        ]
        
        follow_up = follow_ups[i % len(follow_ups)]
        
        follow_up_context = MessageContext(
            user_id=synthetic_user_id,
            content=follow_up,
            platform="synthetic_test"
        )
        
        await message_processor.process_message(follow_up_context)
        
        print(f"   Follow-up processed")
    
    print("\n" + "=" * 80)
    print(f"✅ Generated {num_conversations} synthetic conversations")
    print(f"💡 Now you can query InfluxDB for metrics even with low user count!")

if __name__ == "__main__":
    import sys
    character = sys.argv[1] if len(sys.argv) > 1 else "sage"
    asyncio.run(generate_synthetic_conversations(character, num_conversations=20))
```

**Usage**:
```bash
# Generate 20 synthetic conversations for new character
source .venv/bin/activate
python scripts/generate_synthetic_conversations.py sage

# Now you have enough data to run baseline report
python scripts/generate_baseline_report.py sage
```

---

## 🗂️ Appendix B: Tuning Lever Locations (Complete Reference)

### Overview: Where Do Tuning Levers Live?

**SHORT ANSWER**: Most levers are in **CDL JSON files**. Some are in **environment variables** (`.env.*` files). A few require **Python code changes**.

### Lever Location Matrix

| Tuning Lever | Location | File Type | Requires Restart? |
|--------------|----------|-----------|-------------------|
| **Personality Traits** | CDL JSON | `characters/examples/*.json` | Yes |
| **Communication Style** | CDL JSON | `characters/examples/*.json` | Yes |
| **Emotional Baseline** | CDL JSON | `characters/examples/*.json` | Yes |
| **Response Length Guidance** | CDL JSON | `characters/examples/*.json` | Yes |
| **Roleplay Immersion Flag** | CDL JSON | `characters/examples/*.json` | Yes |
| **Big Five Personality** | CDL JSON | `characters/examples/*.json` | Yes |
| **Character Modes** | CDL JSON | `characters/examples/*.json` | Yes |
| **Bot Name** | `.env.*` | `.env.sage` | Yes (full stop/start) |
| **LLM Model** | `.env.*` | `.env.sage` | Yes (full stop/start) |
| **Character File Path** | `.env.*` | `.env.sage` | Yes (full stop/start) |
| **Health Check Port** | `.env.*` | `.env.sage` | Yes (full stop/start) |
| **Emotion Sensitivity** ⚠️ | Python Code | `src/intelligence/enhanced_vector_emotion_analyzer.py` | Yes |
| **Relationship Multipliers** ⚠️ | Python Code | `src/memory/vector_memory_system.py` | Yes |
| **Context Window Size** ⚠️ | Python Code | `src/core/message_processor.py` | Yes |
| **Vector Similarity Threshold** ⚠️ | Python Code | `src/memory/vector_memory_system.py` | Yes |

⚠️ = Currently requires code changes (see future work section)

---

### Category 1: CDL JSON Configuration (Most Common)

**Location**: `characters/examples/your_character.json`

**What You Can Tune**:

```json
{
  "identity": {
    "name": "Sage",
    "occupation": "Ancient Wizard",
    "age": "Unknown (appears 300+)",
    "description": "A mystical wizard keeper of ancient wisdom"
  },
  
  "personality": {
    "core_traits": [
      "wise_mentor",           // TUNABLE: Change personality traits
      "mysteriously_cryptic",
      "warmly_patient",
      "intellectually_curious"
    ],
    "big_five_traits": {
      "openness": 0.95,        // TUNABLE: Adjust personality dimensions
      "conscientiousness": 0.80,
      "extraversion": 0.45,
      "agreeableness": 0.88,
      "neuroticism": 0.15
    },
    "emotional_baseline": "calm_wisdom",  // TUNABLE: Default emotion
    "emotional_range": {
      "min_intensity": 0.30,   // TUNABLE: Emotion intensity range
      "max_intensity": 0.85
    }
  },
  
  "communication_patterns": {
    "tone": "mystical, wise, patient",     // TUNABLE: Communication style
    "pacing": "thoughtful and measured",
    "vocabulary": "archaic with modern clarity",
    "response_length": "2-4 sentences unless explaining complex concepts",  // TUNABLE
    "teaching_style": "Socratic questioning with storytelling"
  },
  
  "behavioral_guidelines": {
    "allow_full_roleplay_immersion": true,  // TUNABLE: Type 2 character (pure fantasy)
    "maintains_character_consistently": true,
    "adapts_communication_to_user_level": true
  },
  
  "personality_modes": {
    "teaching_mode": {
      "triggers": ["teach", "explain", "how does", "show me"],
      "characteristics": "Patient, detailed, uses metaphors"
    },
    "mystical_mode": {
      "triggers": ["prophecy", "vision", "destiny", "fate"],
      "characteristics": "Cryptic, poetic, philosophical"
    }
  },
  
  "knowledge_domains": [
    {
      "domain": "arcane_magic",
      "expertise_level": "master",
      "teaching_approach": "theoretical foundations first, practical applications second"
    },
    {
      "domain": "ancient_history",
      "expertise_level": "expert",
      "teaching_approach": "storytelling with moral lessons"
    }
  ]
}
```

**Tuning Process for CDL**:
```bash
# 1. Edit CDL file
nano characters/examples/sage.json

# 2. Restart bot (full stop/start for CDL changes)
./multi-bot.sh stop sage && ./multi-bot.sh start sage

# 3. Test with conversation
# 4. Observe results
# 5. Iterate
```

---

### Category 2: Environment Variables (`.env.*` files)

**Location**: `.env.sage` (bot-specific)

**What You Can Tune**:

```bash
# === CORE IDENTITY ===
DISCORD_BOT_NAME=sage                                    # Bot name (display)
CHARACTER_FILE=characters/examples/sage.json             # Which CDL file to use

# === LLM CONFIGURATION ===
LLM_CHAT_MODEL=mistral/mistral-medium                   # TUNABLE: Model selection
# Options: anthropic/claude-3.7-sonnet, mistral/mistral-large, etc.
# TIP: Mistral better for strict CDL compliance, Claude better for creativity

# === INFRASTRUCTURE ===
HEALTH_CHECK_PORT=9099                                   # Unique port per bot
QDRANT_COLLECTION_NAME=whisperengine_memory_sage        # Unique collection
DISCORD_BOT_TOKEN=your_discord_token_here               # Discord auth

# === FUTURE TUNING FLAGS (Not Yet Implemented) ===
# EMOTION_SENSITIVITY_THRESHOLD=0.35                    # TODO: Move from Python
# RELATIONSHIP_AFFECTION_MULTIPLIER=1.2                 # TODO: Move from Python
# RELATIONSHIP_TRUST_MULTIPLIER=0.8                     # TODO: Move from Python
# CONTEXT_WINDOW_SIZE=25                                # TODO: Move from Python
# MEMORY_SIMILARITY_THRESHOLD=0.75                      # TODO: Move from Python
```

**Tuning Process for Environment**:
```bash
# 1. Edit environment file
nano .env.sage

# 2. CRITICAL: Full stop/start required (not just restart)
./multi-bot.sh stop sage
./multi-bot.sh start sage

# 3. Test
# 4. Iterate
```

---

### Category 3: Python Code (Advanced Tuning)

**Current Limitation**: Some tuning levers require Python code changes because they haven't been moved to config yet.

#### 3.1 Emotion Sensitivity

**File**: `src/intelligence/enhanced_vector_emotion_analyzer.py`

```python
class EnhancedVectorEmotionAnalyzer:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        
        # TUNABLE (currently hardcoded)
        self.emotion_threshold = float(os.getenv('EMOTION_SENSITIVITY_THRESHOLD', '0.35'))
        self.intensity_amplifier = float(os.getenv('EMOTION_INTENSITY_AMPLIFIER', '1.25'))
        self.neutral_default = float(os.getenv('EMOTION_NEUTRAL_BASELINE', '0.50'))
```

**How to Tune**:
```bash
# Option 1: Add to .env.sage (if __init__ supports it)
echo "EMOTION_SENSITIVITY_THRESHOLD=0.40" >> .env.sage
./multi-bot.sh stop sage && ./multi-bot.sh start sage

# Option 2: Edit Python code directly (not recommended)
nano src/intelligence/enhanced_vector_emotion_analyzer.py
# Change: self.emotion_threshold = 0.40
./multi-bot.sh restart sage  # Code change = restart OK
```

#### 3.2 Relationship Scoring

**File**: `src/memory/vector_memory_system.py` (or wherever relationship logic lives)

```python
async def update_relationship_metrics(self, user_id: str, interaction_quality: float):
    """Update relationship metrics."""
    
    # TUNABLE (currently hardcoded)
    affection_multiplier = float(os.getenv('RELATIONSHIP_AFFECTION_MULTIPLIER', '1.2'))
    trust_multiplier = float(os.getenv('RELATIONSHIP_TRUST_MULTIPLIER', '0.8'))
    attunement_multiplier = float(os.getenv('RELATIONSHIP_ATTUNEMENT_MULTIPLIER', '1.0'))
    
    affection_boost = interaction_quality * affection_multiplier
    trust_boost = interaction_quality * trust_multiplier
    attunement_boost = interaction_quality * attunement_multiplier
```

#### 3.3 Context Window

**File**: `src/core/message_processor.py`

```python
async def process_message(self, message_context: MessageContext):
    """Process message."""
    
    # TUNABLE (currently hardcoded)
    context_window_size = int(os.getenv('CONTEXT_WINDOW_SIZE', '20'))
    
    conversation_history = await self.memory_manager.get_conversation_history(
        user_id=message_context.user_id,
        limit=context_window_size
    )
```

---

### Tuning Lever Priority for Early-Stage Characters

**Start with CDL (Highest Impact, Easiest)**:
1. ✅ Core personality traits (3-5 traits)
2. ✅ Communication style (tone, pacing, length)
3. ✅ Emotional baseline
4. ✅ `allow_full_roleplay_immersion` flag (Type 2 characters)
5. ✅ Knowledge domains and expertise levels

**Then Environment Variables**:
6. ✅ LLM model selection (Mistral vs Claude)

**Finally Python Code (If Needed)**:
7. ⚠️ Emotion sensitivity thresholds
8. ⚠️ Relationship multipliers
9. ⚠️ Context window size
10. ⚠️ Vector similarity thresholds

---

### Early-Stage Tuning Example: "Sage" Character (Days 1-7)

#### Day 1: Initial CDL Creation
```json
{
  "identity": {"name": "Sage", "occupation": "Wizard"},
  "personality": {
    "core_traits": ["wise", "mystical", "helpful"]
  }
}
```

**Test**: 3 conversations  
**Observation**: Too generic, no personality depth  
**Action**: Expand core traits to 5, add communication patterns

---

#### Day 2: CDL Enhancement
```json
{
  "personality": {
    "core_traits": [
      "wise_mentor",
      "mysteriously_cryptic", 
      "warmly_patient",
      "intellectually_curious",
      "storyteller"
    ],
    "emotional_baseline": "calm_wisdom"
  },
  "communication_patterns": {
    "tone": "mystical yet approachable",
    "response_length": "2-4 sentences"
  }
}
```

**Test**: 5 conversations  
**Observation**: Better! But broke character (mentioned "AI")  
**Action**: Add `allow_full_roleplay_immersion: true`

---

#### Day 3: Immersion Fix
```json
{
  "behavioral_guidelines": {
    "allow_full_roleplay_immersion": true
  }
}
```

**Test**: 5 conversations  
**Observation**: ✅ Character maintained! But too verbose (300+ words)  
**Action**: Tighten response length guidance

---

#### Day 4: Response Length Tuning
```json
{
  "communication_patterns": {
    "response_length": "2-3 sentences for simple questions, 4-6 for complex teaching",
    "pacing": "thoughtful but concise"
  }
}
```

**Test**: 8 conversations  
**Observation**: ✅ Much better! Responses now 100-150 words  
**Observation**: Emotions feel flat (always neutral 0.35)  
**Action**: Consider emotion sensitivity (Python code change)

---

#### Day 5-7: Monitoring Period

**Action**: No changes, just collect more conversations  
**Generate synthetic data**: 20 conversations  
**Check InfluxDB**: Now have enough data for baseline report  

```bash
python scripts/generate_baseline_report.py sage

# Results:
# Confidence: 0.72 ✅
# Emotion variance: 0.23 ⚠️ (target 0.30+)
# Relationship growth: 0.58/day ✅
```

**Decision**: Emotion variance slightly low, but acceptable for fantasy character. Monitor for another week before tuning emotion sensitivity.

---

## 🎯 Quick Decision Tree: Early-Stage Tuning

```
New Character Issue Detected
  │
  ├─> Personality inconsistent or generic?
  │   └─> YES → Edit CDL core_traits (3-5 focused traits)
  │   
  ├─> Character mentions being "AI"?
  │   └─> YES → Set allow_full_roleplay_immersion: true
  │   
  ├─> Responses too long/short?
  │   └─> YES → Edit CDL communication_patterns.response_length
  │   
  ├─> Tone wrong (too formal/casual)?
  │   └─> YES → Edit CDL communication_patterns.tone
  │   
  ├─> Emotions too flat?
  │   └─> YES → Check CDL emotional_baseline first
  │   └─> Still flat? → Edit Python emotion_threshold (advanced)
  │   
  ├─> Responses too fast/slow?
  │   └─> YES → Change LLM_CHAT_MODEL in .env (Mistral faster than Claude)
  │   
  └─> Relationship not growing?
      └─> YES → Edit Python relationship_multipliers (advanced)
```

---

## 🚀 Future Work: Moving Levers to Config

**Goal**: Move all Python tuning levers to environment variables or CDL JSON for easier tuning without code changes.

**Planned Migrations**:

```json
// Future CDL section: "tuning_parameters"
{
  "tuning_parameters": {
    "emotion_detection": {
      "sensitivity_threshold": 0.35,
      "intensity_amplifier": 1.25,
      "neutral_baseline": 0.50,
      "mixed_emotion_threshold": 0.30
    },
    "relationship_scoring": {
      "affection_multiplier": 1.2,
      "trust_multiplier": 0.8,
      "attunement_multiplier": 1.0,
      "early_stage_bonus": 1.5
    },
    "context_management": {
      "conversation_history_limit": 20,
      "relevant_memories_limit": 10,
      "similarity_threshold": 0.75
    },
    "performance": {
      "max_response_time_ms": 2500,
      "enable_caching": true
    }
  }
}
```

**Until Then**: Use combination of CDL + `.env.*` + Python code changes for advanced tuning.

---

## 💡 Key Takeaways for Early-Stage Tuning

1. **Start with CDL**: 90% of tuning can be done in JSON (personality, communication, immersion)
2. **Use Subjective Observations**: Don't wait for metrics - tune based on feel
3. **Iterate Rapidly**: Test → Observe → Tune → Repeat (daily cycles)
4. **Generate Synthetic Data**: Use scripts to create baseline metrics even with 2-3 users
5. **One Change at a Time**: Even without metrics, isolate changes
6. **Document Everything**: Keep tuning log with observations and decisions
7. **Most Levers in CDL/Env**: Personality, communication, model selection all in config
8. **Some Levers in Code**: Emotion sensitivity, relationship scoring (future work to migrate)
9. **Restart Required**: All config changes need full stop/start (not just restart)
10. **Trust Your Gut**: Early-stage = qualitative. If character "feels right", it probably is.

---

