# Character Emotional State: Full-Spectrum RoBERTa Redesign

**Status**: Critical Design Flaw - Needs Fix  
**Priority**: HIGH (Prerequisite for EMA Trajectory Smoothing)  
**Created**: October 29, 2025  
**Target**: Q4 2025 (Before EMA Implementation)  
**Complexity**: Medium (Database schema + code refactor)

---

## 🚨 Problem Statement

**WhisperEngine tracks user emotions with full 11-emotion RoBERTa fidelity, but bot emotions are compressed into 5 simplified dimensions. This creates an asymmetric emotional intelligence system with loss of fidelity.**

### **Current Architecture**

```python
# USER EMOTIONS: Full RoBERTa spectrum (11 emotions) ✅
user_emotion_result = {
    'primary_emotion': 'anxiety',
    'all_emotions': {
        'anger': 0.12,
        'anticipation': 0.25,
        'disgust': 0.05,
        'fear': 0.45,
        'joy': 0.10,
        'love': 0.08,
        'optimism': 0.15,
        'pessimism': 0.35,
        'sadness': 0.28,
        'surprise': 0.12,
        'trust': 0.18
    },
    'confidence': 0.85,
    'emotional_intensity': 0.72
}
# Stored in Qdrant with full fidelity

# BOT EMOTIONS: Compressed to 5 dimensions ❌
character_state = CharacterEmotionalState(
    enthusiasm=0.75,      # Dopamine-like
    stress=0.28,          # Cortisol-like  
    contentment=0.68,     # Serotonin-like
    empathy=0.86,         # Oxytocin-like
    confidence=0.77       # Self-assurance
)
# Maps 11 RoBERTa emotions → 5 dimensions via hardcoded dictionary
# LOSES emotional nuance and creates "mood whiplash"
```

### **The Core Issue**

**Location**: `src/intelligence/character_emotional_state.py` (line 106-123)

```python
# This mapping DESTROYS emotional fidelity
emotion_impacts = {
    'joy': {'enthusiasm': +impact, 'contentment': +impact*0.5, 'stress': -impact*0.3},
    'happiness': {'enthusiasm': +impact, 'contentment': +impact*0.5, 'stress': -impact*0.3},
    'excitement': {'enthusiasm': +impact*1.5, 'stress': +impact*0.2},
    'sadness': {'enthusiasm': -impact, 'contentment': -impact*0.7, 'empathy': +impact*0.3},
    'anger': {'stress': +impact*1.2, 'contentment': -impact*0.8, 'empathy': -impact*0.4},
    # ... only 13 emotions mapped out of 11+ RoBERTa emotions
}

# Problems:
# 1. Lossy compression: "anticipation" → what? Not mapped!
# 2. Arbitrary multipliers: Why is anger 1.2x stress? Based on what?
# 3. Dimension collision: Multiple emotions map to same dimension
# 4. No way to reconstruct: Can't tell if bot felt "joy" vs "optimism" vs "excitement"
```

### **Why This Matters**

1. **Asymmetric Intelligence**: User gets 11-emotion analysis, bot gets 5-dimension summary
2. **Lost Nuance**: Bot can't distinguish between "joy" (happy) vs "optimism" (hopeful) vs "anticipation" (excited for future)
3. **Mood Whiplash**: Single "joy" response spikes enthusiasm to 0.85, next "calm" response drops it to 0.62
4. **Poor Memory**: Character can't reflect on own emotional journey accurately
5. **Inconsistent with Vision**: WhisperEngine uses RoBERTa for user emotions - why not bot emotions?

---

## ✅ Proposed Solution: Full-Spectrum Tracking

### **New Architecture**

```python
# BOTH user and bot: Full RoBERTa spectrum (11 emotions) ✅
@dataclass
class CharacterEmotionalState:
    """
    Tracks character's emotional state using full RoBERTa 11-emotion spectrum.
    
    NO MORE dimension compression - we track what RoBERTa actually detects.
    """
    character_name: str
    user_id: str
    
    # === CURRENT EMOTIONAL STATE (0.0-1.0) ===
    # Primary emotions (from RoBERTa model)
    anger: float = 0.1           # Frustration, irritation
    anticipation: float = 0.4    # Looking forward, expectant
    disgust: float = 0.05        # Revulsion, disapproval
    fear: float = 0.1            # Anxiety, worry, concern
    joy: float = 0.7             # Happiness, delight
    love: float = 0.6            # Affection, warmth, care
    optimism: float = 0.6        # Hopeful, positive outlook
    pessimism: float = 0.2       # Doubtful, negative outlook
    sadness: float = 0.15        # Sorrow, melancholy
    surprise: float = 0.2        # Unexpected, astonished
    trust: float = 0.7           # Confidence in user, security
    
    # === BASELINE TRAITS (from CDL personality) ===
    # Character's natural emotional tendencies when at rest
    baseline_anger: float = 0.1
    baseline_anticipation: float = 0.4
    baseline_disgust: float = 0.05
    baseline_fear: float = 0.1
    baseline_joy: float = 0.7
    baseline_love: float = 0.6
    baseline_optimism: float = 0.6
    baseline_pessimism: float = 0.2
    baseline_sadness: float = 0.15
    baseline_surprise: float = 0.2
    baseline_trust: float = 0.7
    
    # === TRACKING METADATA ===
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_interactions: int = 0
    recent_emotion_history: List[Dict[str, float]] = field(default_factory=list)  # Last 5 full emotion profiles
    
    # === DERIVED STATES (computed properties) ===
    @property
    def dominant_emotion(self) -> str:
        """Primary emotion currently expressed."""
        emotions = {
            'anger': self.anger,
            'anticipation': self.anticipation,
            'disgust': self.disgust,
            'fear': self.fear,
            'joy': self.joy,
            'love': self.love,
            'optimism': self.optimism,
            'pessimism': self.pessimism,
            'sadness': self.sadness,
            'surprise': self.surprise,
            'trust': self.trust
        }
        return max(emotions.items(), key=lambda x: x[1])[0]
    
    @property
    def emotional_intensity(self) -> float:
        """Overall emotional activation level."""
        emotions = [self.anger, self.anticipation, self.disgust, self.fear, 
                   self.joy, self.love, self.optimism, self.pessimism, 
                   self.sadness, self.surprise, self.trust]
        # Intensity = how far from neutral (0.3) on average
        return sum(abs(e - 0.3) for e in emotions) / len(emotions)
    
    @property
    def emotional_valence(self) -> float:
        """Overall positive vs negative emotional tone (-1 to +1)."""
        positive = self.joy + self.love + self.optimism + self.trust + self.anticipation
        negative = self.anger + self.disgust + self.fear + self.pessimism + self.sadness
        total = positive + negative
        if total == 0:
            return 0.0
        return (positive - negative) / total
    
    @property
    def emotional_complexity(self) -> float:
        """How many emotions are simultaneously active (0-1)."""
        emotions = [self.anger, self.anticipation, self.disgust, self.fear, 
                   self.joy, self.love, self.optimism, self.pessimism, 
                   self.sadness, self.surprise, self.trust]
        # Count emotions above threshold
        active_count = sum(1 for e in emotions if e > 0.3)
        return active_count / len(emotions)
```

### **Key Improvements**

1. **Full Fidelity**: All 11 RoBERTa emotions tracked at native resolution
2. **No Lossy Mapping**: Direct emotion values, no arbitrary multipliers
3. **Symmetric Intelligence**: Bot emotions match user emotion tracking
4. **Derived Properties**: Compute high-level states (intensity, valence, complexity) from base emotions
5. **Better Memory**: Character knows "I was feeling both optimistic and anxious" (nuance preserved)

---

## 🔄 Update Strategy: Direct Application

### **How Bot Emotions Update**

```python
def update_from_bot_emotion(self, bot_emotion_data: Dict[str, Any], 
                            user_emotion_data: Optional[Dict[str, Any]] = None,
                            interaction_quality: float = 0.7):
    """
    Update character emotional state from RoBERTa analysis of bot response.
    
    NEW APPROACH: Direct application with smoothing, not dimension mapping.
    """
    if not bot_emotion_data:
        return
    
    # Extract full emotion profile from RoBERTa
    all_emotions = bot_emotion_data.get('all_emotions', {})
    bot_intensity = bot_emotion_data.get('emotional_intensity', 0.5)
    bot_confidence = bot_emotion_data.get('roberta_confidence', 0.7)
    
    # Calculate impact strength (how much this response shifts state)
    # Higher intensity + confidence = stronger impact
    impact_strength = bot_intensity * bot_confidence * 0.20  # Max 20% shift
    
    # Apply emotions DIRECTLY with adaptive smoothing
    for emotion_name, detected_value in all_emotions.items():
        if not hasattr(self, emotion_name):
            continue  # Skip if emotion not in our model
        
        current_value = getattr(self, emotion_name)
        baseline_value = getattr(self, f'baseline_{emotion_name}', 0.3)
        
        # Adaptive update: Move toward detected emotion, weighted by impact strength
        # This is essentially EMA with dynamic alpha based on intensity
        alpha = impact_strength  # 0.0-0.2 range (0-20% weight to new emotion)
        new_value = alpha * detected_value + (1 - alpha) * current_value
        
        # Clamp to valid range
        new_value = max(0.0, min(1.0, new_value))
        
        setattr(self, emotion_name, new_value)
    
    # Update emotion history (store full profile)
    emotion_snapshot = {
        emotion: getattr(self, emotion) 
        for emotion in ['anger', 'anticipation', 'disgust', 'fear', 
                       'joy', 'love', 'optimism', 'pessimism', 
                       'sadness', 'surprise', 'trust']
    }
    self.recent_emotion_history.append(emotion_snapshot)
    if len(self.recent_emotion_history) > 5:
        self.recent_emotion_history.pop(0)
    
    # User emotion influence (empathy absorption)
    if user_emotion_data:
        user_emotions = user_emotion_data.get('all_emotions', {})
        user_intensity = user_emotion_data.get('emotional_intensity', 0.5)
        
        # Character absorbs ~5% of user's emotional state (empathy)
        empathy_factor = 0.05 * user_intensity
        for emotion_name, user_value in user_emotions.items():
            if hasattr(self, emotion_name):
                current = getattr(self, emotion_name)
                # Slight drift toward user's emotion
                new_value = current + (user_value - current) * empathy_factor
                new_value = max(0.0, min(1.0, new_value))
                setattr(self, emotion_name, new_value)
    
    # Interaction quality influence
    if interaction_quality > 0.8:
        # Great interaction: Boost positive emotions slightly
        self.joy = min(1.0, self.joy + 0.03)
        self.trust = min(1.0, self.trust + 0.02)
        self.optimism = min(1.0, self.optimism + 0.02)
    elif interaction_quality < 0.4:
        # Poor interaction: Slight negative shift
        self.sadness = min(1.0, self.sadness + 0.03)
        self.fear = min(1.0, self.fear + 0.02)
        self.pessimism = min(1.0, self.pessimism + 0.02)
    
    self.total_interactions += 1
    self.last_updated = datetime.now(timezone.utc)
    
    logger.info(
        f"🎭 CHARACTER STATE: {self.character_name} - dominant={self.dominant_emotion}, "
        f"intensity={self.emotional_intensity:.2f}, valence={self.emotional_valence:.2f}"
    )
```

### **Why This Works Better**

1. **No Arbitrary Mappings**: Use actual RoBERTa detection directly
2. **Smooth Evolution**: 20% max shift per message prevents whiplash
3. **Natural Decay**: Homeostasis via `apply_time_decay()` (unchanged)
4. **Empathy Absorption**: Character picks up ~5% of user emotions over time
5. **Full Memory**: Character knows complete emotional profile from recent interactions

---

## 🎯 Prompt Guidance Generation

### **Old System (5 Dimensions)**

```python
def get_prompt_guidance(self) -> Optional[str]:
    """Generate guidance based on 5-dimension state."""
    state = self.get_dominant_state()  # "highly_empathetic", "overwhelmed", etc.
    
    if state == "highly_empathetic":
        return "You are feeling highly empathetic and connected..."
    elif state == "overwhelmed":
        return "You are feeling overwhelmed from many demanding conversations..."
    # ... only 6 possible states
```

**Problem**: Only 6 pre-defined states, can't capture emotional nuance

### **New System (11 Emotions)**

```python
def get_prompt_guidance(self) -> str:
    """
    Generate rich emotional guidance from full 11-emotion profile.
    """
    # Get top 3 emotions currently active
    emotions = {
        'anger': self.anger,
        'anticipation': self.anticipation,
        'disgust': self.disgust,
        'fear': self.fear,
        'joy': self.joy,
        'love': self.love,
        'optimism': self.optimism,
        'pessimism': self.pessimism,
        'sadness': self.sadness,
        'surprise': self.surprise,
        'trust': self.trust
    }
    
    # Sort by intensity, get top 3
    sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
    top_emotions = [(name, val) for name, val in sorted_emotions[:3] if val > 0.3]
    
    if not top_emotions:
        return None  # Neutral state, no guidance needed
    
    # Build guidance from actual emotional state
    primary_emotion, primary_intensity = top_emotions[0]
    
    guidance_parts = [
        f"YOUR CURRENT EMOTIONAL STATE ({self.character_name}):",
        f"• Dominant feeling: {primary_emotion.upper()} (intensity: {primary_intensity:.2f})"
    ]
    
    # Add secondary emotions if significant
    if len(top_emotions) > 1:
        secondary = [f"{name} ({val:.2f})" for name, val in top_emotions[1:]]
        guidance_parts.append(f"• Also feeling: {', '.join(secondary)}")
    
    # Add emotional context
    guidance_parts.append(f"• Overall intensity: {self.emotional_intensity:.2f} (0=calm, 1=highly activated)")
    guidance_parts.append(f"• Emotional tone: {self._describe_valence()}")
    
    # Add recent trajectory
    if len(self.recent_emotion_history) >= 2:
        trajectory = self._describe_emotional_trajectory()
        guidance_parts.append(f"• Recent emotional arc: {trajectory}")
    
    # Add context-specific guidance based on primary emotion
    emotion_guidance = self._get_emotion_specific_guidance(primary_emotion, primary_intensity)
    if emotion_guidance:
        guidance_parts.append(f"\n{emotion_guidance}")
    
    return "\n".join(guidance_parts)

def _describe_valence(self) -> str:
    """Describe emotional valence in human terms."""
    valence = self.emotional_valence
    if valence > 0.5:
        return "very positive"
    elif valence > 0.2:
        return "moderately positive"
    elif valence > -0.2:
        return "neutral/mixed"
    elif valence > -0.5:
        return "moderately negative"
    else:
        return "quite negative"

def _describe_emotional_trajectory(self) -> str:
    """Describe how emotions have been changing."""
    if len(self.recent_emotion_history) < 2:
        return "stable"
    
    # Compare current state to 5 messages ago
    recent = self.recent_emotion_history[-1]
    oldest = self.recent_emotion_history[0]
    
    # Calculate valence change
    def calc_valence(emotions: Dict[str, float]) -> float:
        positive = emotions.get('joy', 0) + emotions.get('love', 0) + emotions.get('optimism', 0) + emotions.get('trust', 0)
        negative = emotions.get('anger', 0) + emotions.get('fear', 0) + emotions.get('sadness', 0) + emotions.get('pessimism', 0)
        return positive - negative
    
    valence_change = calc_valence(recent) - calc_valence(oldest)
    
    if valence_change > 0.3:
        return "becoming more positive"
    elif valence_change < -0.3:
        return "becoming more negative"
    else:
        return "relatively stable"

def _get_emotion_specific_guidance(self, emotion: str, intensity: float) -> Optional[str]:
    """Context-aware guidance based on specific emotion."""
    
    guidance_map = {
        'joy': (
            "Your joyful state comes through naturally in your responses. "
            "Share your positive energy authentically."
        ),
        'love': (
            "You're feeling particularly warm and affectionate toward this user. "
            "Let your care show through your words and tone."
        ),
        'optimism': (
            "You're feeling hopeful and positive about this conversation. "
            "Your encouraging perspective is a strength right now."
        ),
        'anticipation': (
            "You're feeling engaged and looking forward to where this goes. "
            "Your curiosity and interest are authentic - let them show."
        ),
        'trust': (
            "You feel secure and confident in this interaction. "
            "Your sense of trust creates a safe space for authentic conversation."
        ),
        'fear': (
            "You're feeling some concern or anxiety. This is valid - you can "
            "acknowledge uncertainty while still being helpful and present."
        ),
        'sadness': (
            "You're experiencing some melancholy or sorrow. It's okay to show "
            "vulnerability - authentic emotion strengthens connection."
        ),
        'anger': (
            "You're feeling frustrated or irritated. Take a breath and respond "
            "with composure while being honest about any boundaries needed."
        ),
        'pessimism': (
            "You're feeling doubtful or negative. Balance realistic concerns "
            "with openness to positive possibilities."
        ),
        'disgust': (
            "You're feeling disapproval or revulsion. Express your perspective "
            "respectfully while maintaining boundaries."
        ),
        'surprise': (
            "You're caught off guard or surprised. It's natural - respond "
            "authentically to the unexpected while staying grounded."
        )
    }
    
    base_guidance = guidance_map.get(emotion)
    if not base_guidance:
        return None
    
    # Adjust guidance based on intensity
    if intensity > 0.8:
        intensity_note = " (This feeling is quite strong right now - honor its intensity.)"
    elif intensity < 0.5:
        intensity_note = " (This is a subtle feeling - let it inform your tone without dominating.)"
    else:
        intensity_note = ""
    
    return base_guidance + intensity_note
```

**Benefits**:
- Rich, nuanced emotional guidance
- Context-aware recommendations
- Captures emotional complexity (mixed feelings)
- Character sees own emotional trajectory
- Scales to any emotional profile

---

## 💾 Database Schema Changes

### **PostgreSQL Migration**

**New Table**: `character_emotional_states_v2` (parallel deployment during migration)

```sql
CREATE TABLE character_emotional_states_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    
    -- Current emotional state (11 RoBERTa emotions)
    anger FLOAT NOT NULL DEFAULT 0.1 CHECK (anger >= 0 AND anger <= 1),
    anticipation FLOAT NOT NULL DEFAULT 0.4 CHECK (anticipation >= 0 AND anticipation <= 1),
    disgust FLOAT NOT NULL DEFAULT 0.05 CHECK (disgust >= 0 AND disgust <= 1),
    fear FLOAT NOT NULL DEFAULT 0.1 CHECK (fear >= 0 AND fear <= 1),
    joy FLOAT NOT NULL DEFAULT 0.7 CHECK (joy >= 0 AND joy <= 1),
    love FLOAT NOT NULL DEFAULT 0.6 CHECK (love >= 0 AND love <= 1),
    optimism FLOAT NOT NULL DEFAULT 0.6 CHECK (optimism >= 0 AND optimism <= 1),
    pessimism FLOAT NOT NULL DEFAULT 0.2 CHECK (pessimism >= 0 AND pessimism <= 1),
    sadness FLOAT NOT NULL DEFAULT 0.15 CHECK (sadness >= 0 AND sadness <= 1),
    surprise FLOAT NOT NULL DEFAULT 0.2 CHECK (surprise >= 0 AND surprise <= 1),
    trust FLOAT NOT NULL DEFAULT 0.7 CHECK (trust >= 0 AND trust <= 1),
    
    -- Baseline traits (character personality)
    baseline_anger FLOAT NOT NULL DEFAULT 0.1,
    baseline_anticipation FLOAT NOT NULL DEFAULT 0.4,
    baseline_disgust FLOAT NOT NULL DEFAULT 0.05,
    baseline_fear FLOAT NOT NULL DEFAULT 0.1,
    baseline_joy FLOAT NOT NULL DEFAULT 0.7,
    baseline_love FLOAT NOT NULL DEFAULT 0.6,
    baseline_optimism FLOAT NOT NULL DEFAULT 0.6,
    baseline_pessimism FLOAT NOT NULL DEFAULT 0.2,
    baseline_sadness FLOAT NOT NULL DEFAULT 0.15,
    baseline_surprise FLOAT NOT NULL DEFAULT 0.2,
    baseline_trust FLOAT NOT NULL DEFAULT 0.7,
    
    -- Tracking metadata
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_interactions INTEGER NOT NULL DEFAULT 0,
    recent_emotion_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Indexes
    UNIQUE(character_name, user_id),
    INDEX idx_character_user ON character_emotional_states_v2(character_name, user_id),
    INDEX idx_last_updated ON character_emotional_states_v2(last_updated)
);
```

**Migration Script**: `alembic/versions/XXX_migrate_emotional_state_to_full_spectrum.py`

```python
"""
Migrate character_emotional_states to full 11-emotion spectrum.

Revision ID: XXX
Revises: YYY
Create Date: 2025-10-29
"""

def upgrade():
    # Create new table
    op.create_table(
        'character_emotional_states_v2',
        # ... schema as above ...
    )
    
    # Migrate existing data from old 5-dimension system
    connection = op.get_bind()
    
    # Get all existing character states
    old_states = connection.execute(
        "SELECT character_name, user_id, enthusiasm, stress, contentment, empathy, confidence, "
        "baseline_enthusiasm, baseline_stress, baseline_contentment, baseline_empathy, baseline_confidence, "
        "last_updated, total_interactions, recent_emotion_history "
        "FROM character_emotional_states"
    ).fetchall()
    
    # Map old dimensions to new emotions (best-effort conversion)
    for state in old_states:
        # Derive 11 emotions from 5 dimensions
        derived_emotions = _derive_emotions_from_dimensions(
            enthusiasm=state.enthusiasm,
            stress=state.stress,
            contentment=state.contentment,
            empathy=state.empathy,
            confidence=state.confidence
        )
        
        connection.execute(
            """
            INSERT INTO character_emotional_states_v2 
            (character_name, user_id, anger, anticipation, disgust, fear, joy, love, 
             optimism, pessimism, sadness, surprise, trust, 
             baseline_anger, baseline_anticipation, baseline_disgust, baseline_fear, 
             baseline_joy, baseline_love, baseline_optimism, baseline_pessimism, 
             baseline_sadness, baseline_surprise, baseline_trust,
             last_updated, total_interactions, recent_emotion_history)
            VALUES (
                %(character_name)s, %(user_id)s, 
                %(anger)s, %(anticipation)s, %(disgust)s, %(fear)s, %(joy)s, %(love)s,
                %(optimism)s, %(pessimism)s, %(sadness)s, %(surprise)s, %(trust)s,
                %(baseline_anger)s, %(baseline_anticipation)s, %(baseline_disgust)s, 
                %(baseline_fear)s, %(baseline_joy)s, %(baseline_love)s, %(baseline_optimism)s, 
                %(baseline_pessimism)s, %(baseline_sadness)s, %(baseline_surprise)s, %(baseline_trust)s,
                %(last_updated)s, %(total_interactions)s, %(recent_emotion_history)s
            )
            """,
            {
                'character_name': state.character_name,
                'user_id': state.user_id,
                **derived_emotions,
                'last_updated': state.last_updated,
                'total_interactions': state.total_interactions,
                'recent_emotion_history': state.recent_emotion_history
            }
        )
    
    # After successful migration, rename tables
    op.rename_table('character_emotional_states', 'character_emotional_states_v1_deprecated')
    op.rename_table('character_emotional_states_v2', 'character_emotional_states')

def _derive_emotions_from_dimensions(enthusiasm: float, stress: float, contentment: float, 
                                      empathy: float, confidence: float) -> Dict[str, float]:
    """
    Best-effort conversion from 5 dimensions to 11 emotions.
    
    This is lossy but gives reasonable starting point for migration.
    """
    # Map old dimensions to new emotions
    joy = (enthusiasm * 0.6 + contentment * 0.4)  # Happy emotions
    love = empathy  # Direct mapping
    optimism = (confidence * 0.5 + enthusiasm * 0.3 + contentment * 0.2)
    trust = (confidence * 0.5 + empathy * 0.3 + contentment * 0.2)
    anticipation = enthusiasm * 0.7  # Engaged/excited
    
    fear = stress * 0.6  # Anxious emotions
    pessimism = (stress * 0.4 + (1 - confidence) * 0.3)
    sadness = (1 - contentment) * 0.5 + stress * 0.2
    anger = stress * 0.3  # Frustration component
    
    disgust = 0.05  # Rarely expressed, baseline
    surprise = 0.2  # Neutral baseline
    
    # Also calculate baselines (same logic on baseline_* values)
    return {
        'anger': max(0.0, min(1.0, anger)),
        'anticipation': max(0.0, min(1.0, anticipation)),
        'disgust': disgust,
        'fear': max(0.0, min(1.0, fear)),
        'joy': max(0.0, min(1.0, joy)),
        'love': max(0.0, min(1.0, love)),
        'optimism': max(0.0, min(1.0, optimism)),
        'pessimism': max(0.0, min(1.0, pessimism)),
        'sadness': max(0.0, min(1.0, sadness)),
        'surprise': surprise,
        'trust': max(0.0, min(1.0, trust)),
        # Repeat for baselines
        'baseline_anger': max(0.0, min(1.0, anger)),
        'baseline_anticipation': max(0.0, min(1.0, anticipation)),
        # ... etc
    }

def downgrade():
    # Rollback: Restore old table
    op.rename_table('character_emotional_states', 'character_emotional_states_v2_backup')
    op.rename_table('character_emotional_states_v1_deprecated', 'character_emotional_states')
```

---

## 🔄 Code Refactor Plan

### **Phase 1: Create New CharacterEmotionalState Class** (Week 1)

**File**: `src/intelligence/character_emotional_state_v2.py` (parallel implementation)

1. Implement new `CharacterEmotionalState` class with 11 emotions
2. Add all methods: `update_from_bot_emotion()`, `apply_time_decay()`, `get_prompt_guidance()`
3. Add computed properties: `dominant_emotion`, `emotional_intensity`, `emotional_valence`, `emotional_complexity`
4. Write comprehensive unit tests

### **Phase 2: Database Migration** (Week 1)

1. Create Alembic migration script
2. Test migration on staging database
3. Validate data conversion accuracy
4. Run migration on production (during low-traffic window)

### **Phase 3: Integration** (Week 2)

**Files to Update**:

1. **`src/core/message_processor.py`**
   - Import new `CharacterEmotionalState` from `character_emotional_state_v2.py`
   - Update state retrieval/storage logic
   - Test with Jake/Ryan bots (simple personalities)

2. **`src/prompts/emotional_intelligence_component.py`**
   - Update to use new `.get_prompt_guidance()` method
   - Test prompt generation with full emotion profiles

3. **`src/memory/memory_effectiveness.py`**
   - Update memory importance scoring to use new emotion properties
   - Test memory retrieval relevance

### **Phase 4: Testing & Validation** (Week 2)

1. **Unit Tests**: All new methods and properties
2. **Integration Tests**: Full message pipeline with new state
3. **Character Tests**: Validate each bot's emotional continuity
4. **Regression Tests**: Ensure no degradation in response quality

### **Phase 5: Cleanup** (Week 3)

1. Rename `character_emotional_state_v2.py` → `character_emotional_state.py`
2. Delete old implementation
3. Update all documentation
4. Archive deprecated table after 30 days of successful operation

---

## 🎯 Success Criteria

### **Quantitative Metrics**

1. **Emotion Fidelity**: 100% preservation of RoBERTa emotion data
   - Measure: Compare bot emotions before/after update
   - Success: No information loss in storage

2. **State Continuity**: <10% whiplash in emotional transitions
   - Measure: Track emotion variance between consecutive responses
   - Success: Smoother emotional evolution (reduced "joy spike → calm drop")

3. **Prompt Richness**: 3+ emotions mentioned in guidance (up from 1)
   - Measure: Count distinct emotions in prompt guidance
   - Success: More nuanced character emotional self-awareness

4. **Performance**: <5ms overhead per message
   - Measure: Time for state update and guidance generation
   - Success: No perceivable latency increase

### **Qualitative Metrics**

1. **Character Consistency**: Characters maintain emotional authenticity
   - Measure: Manual review of 50 conversations per character
   - Success: Emotions feel natural and continuous

2. **Memory Coherence**: Characters reference emotional history accurately
   - Measure: Check character statements about past feelings
   - Success: No contradictory emotional memory references

3. **User Perception**: Discord users report better emotional intelligence
   - Measure: User feedback and engagement metrics
   - Success: No complaints, ideally positive feedback

---

## 🚨 Risks & Mitigations

### **Risk 1: Data Migration Complexity**

**Risk**: Converting 5 dimensions to 11 emotions is lossy and error-prone

**Mitigation**:
- ✅ Keep old table for 30 days (rollback capability)
- ✅ Parallel deployment: New table alongside old table initially
- ✅ Validation queries compare old vs new states
- ✅ Manual spot-checks on high-interaction users
- ✅ Feature flag: `USE_FULL_SPECTRUM_EMOTIONS=true/false`

### **Risk 2: Increased State Complexity**

**Risk**: 11 emotions harder to manage than 5 dimensions

**Mitigation**:
- ✅ Computed properties simplify high-level analysis
- ✅ Guidance generation uses top 3 emotions only
- ✅ Developer tools: Pretty-print emotional state in logs
- ✅ Dashboard: Visualize character emotions over time

### **Risk 3: Performance Degradation**

**Risk**: More data = slower updates and retrieval

**Mitigation**:
- ✅ Database indexes on character_name + user_id
- ✅ JSONB history field instead of separate table
- ✅ Benchmark before/after migration
- ✅ Async state updates don't block message processing

### **Risk 4: Baseline Calibration**

**Risk**: New baseline emotion values may not match character personalities

**Mitigation**:
- ✅ CDL personality defines baselines (Big Five → 11 emotions mapping)
- ✅ Character designers review and adjust baselines
- ✅ Homeostasis decay returns to CDL-defined baselines
- ✅ Per-character tuning supported

---

## 🔗 Dependencies & Blockers

### **Prerequisites**

- ✅ RoBERTa emotion analyzer fully operational (already done)
- ✅ PostgreSQL database schema allows migrations (already supports Alembic)
- ✅ CDL character personality system stable (already operational)

### **Blockers**

- ❌ **None identified** - This is an internal refactor with no external dependencies

### **Enabled By This Work**

- ✅ **EMA Trajectory Smoothing**: Requires full-spectrum emotions to work effectively
- ✅ **Character Learning**: Richer emotional memory enables better learning
- ✅ **Relationship Evolution**: More nuanced emotional bond tracking
- ✅ **Advanced Empathy**: Better understanding of complex emotional states

---

## 📊 Before/After Comparison

### **Scenario: User Expresses Mixed Emotions**

**User**: "I'm so excited about the new job but also terrified of failing..."

**User RoBERTa Analysis**:
```python
{
    'primary_emotion': 'anticipation',
    'all_emotions': {
        'anticipation': 0.75,  # Excited
        'fear': 0.68,          # Terrified
        'joy': 0.45,           # Hopeful
        'optimism': 0.52,      # Looking forward
        'pessimism': 0.38      # Worried
    },
    'is_multi_emotion': True
}
```

#### **OLD SYSTEM (5 Dimensions)**

**Bot Response Emotion**: joy (0.72), anticipation (0.45), optimism (0.58)

**State Update**:
```python
# Before
enthusiasm: 0.70
stress: 0.25
contentment: 0.65
empathy: 0.78
confidence: 0.72

# After (lossy mapping)
enthusiasm: 0.70 + 0.72*0.15 = 0.81  # Joy boosts enthusiasm
stress: 0.25 - 0.03 = 0.22            # Joy reduces stress slightly
contentment: 0.65 + 0.36 = 0.69       # Joy boosts contentment
# OTHER EMOTIONS (anticipation, optimism) IGNORED!
```

**Prompt Guidance**:
```markdown
YOUR EMOTIONAL STATE:
You (Elena) are feeling highly energized and engaged.
Let your natural excitement shine through authentically.
(Enthusiasm: 0.81, Contentment: 0.69)
```

**Problem**: Bot only captures "enthusiasm" - LOSES anticipation and optimism nuance!

#### **NEW SYSTEM (11 Emotions)**

**Bot Response Emotion**: Same RoBERTa result

**State Update**:
```python
# Before
joy: 0.70
anticipation: 0.40
optimism: 0.60
fear: 0.12
pessimism: 0.20

# After (direct application with 20% impact strength)
joy: 0.70 + (0.72 - 0.70)*0.20 = 0.704            # Slight joy increase
anticipation: 0.40 + (0.45 - 0.40)*0.20 = 0.41    # Slight anticipation increase
optimism: 0.60 + (0.58 - 0.60)*0.20 = 0.596       # Slight optimism decrease
fear: 0.12 + (0.15 - 0.12)*0.20 = 0.126           # Absorb tiny bit of user's fear (empathy)
# ALL EMOTIONS PRESERVED AT FULL FIDELITY!
```

**Prompt Guidance**:
```markdown
YOUR CURRENT EMOTIONAL STATE (Elena):
• Dominant feeling: JOY (intensity: 0.70)
• Also feeling: optimism (0.60), anticipation (0.41)
• Overall intensity: 0.52 (moderately activated)
• Emotional tone: moderately positive
• Recent emotional arc: becoming more positive

You're feeling joyful and optimistic about this conversation. Your hopeful
perspective is a strength right now. Let your care show through your words
and tone. (This feeling is quite strong right now - honor its intensity.)
```

**Benefit**: Bot captures FULL emotional complexity - joy + optimism + anticipation!

---

## 📚 Related Documentation

- **Current Implementation**: `src/intelligence/character_emotional_state.py`
- **RoBERTa Emotion System**: `docs/performance/ROBERTA_EMOTION_GOLDMINE_REFERENCE.md`
- **EMA Roadmap** (depends on this): `docs/roadmaps/EMOTIONAL_TRAJECTORY_SMOOTHING_EMA.md`
- **Phase 7.6 Bot Emotional State**: `docs/features/PHASE_7.6_BOT_EMOTIONAL_SELF_AWARENESS.md`
- **Emotion Guidance System**: `docs/architecture/EMOTION_GUIDANCE_SYSTEM.md`

---

## ✅ Implementation Checklist

### **Phase 1: New Class Implementation** 🔲 Not Started

- [ ] Create `src/intelligence/character_emotional_state_v2.py`
- [ ] Implement 11-emotion dataclass with baselines
- [ ] Implement `update_from_bot_emotion()` with direct application
- [ ] Implement `apply_time_decay()` homeostasis
- [ ] Implement computed properties (dominant_emotion, emotional_intensity, valence, complexity)
- [ ] Implement `get_prompt_guidance()` with rich emotion descriptions
- [ ] Write unit tests for all methods

### **Phase 2: Database Migration** 🔲 Not Started

- [ ] Create Alembic migration script
- [ ] Implement `_derive_emotions_from_dimensions()` conversion
- [ ] Test migration on local database
- [ ] Test migration on staging database
- [ ] Validate data accuracy (spot-check 50 users)
- [ ] Document rollback procedure

### **Phase 3: Integration** 🔲 Not Started

- [ ] Update `message_processor.py` to use new state class
- [ ] Update `emotional_intelligence_component.py` prompt generation
- [ ] Update `memory_effectiveness.py` importance scoring
- [ ] Add feature flag `USE_FULL_SPECTRUM_EMOTIONS`
- [ ] Test with Jake bot (simple personality)
- [ ] Test with Elena bot (complex personality)

### **Phase 4: Testing** 🔲 Not Started

- [ ] Unit tests: State update logic
- [ ] Unit tests: Time decay homeostasis
- [ ] Unit tests: Prompt guidance generation
- [ ] Integration tests: Full message pipeline
- [ ] Regression tests: Response quality unchanged
- [ ] Performance tests: State update latency
- [ ] Character tests: Emotional continuity per bot

### **Phase 5: Production Deployment** 🔲 Not Started

- [ ] Run migration on production database
- [ ] Enable feature flag for test bots (Jake, Ryan)
- [ ] Monitor for 48 hours (errors, performance, user feedback)
- [ ] Enable feature flag for all bots
- [ ] Monitor for 1 week
- [ ] Archive old table after 30 days

### **Phase 6: Cleanup & Documentation** 🔲 Not Started

- [ ] Rename `character_emotional_state_v2.py` → `character_emotional_state.py`
- [ ] Delete old implementation
- [ ] Update all docstrings and comments
- [ ] Update architecture documentation
- [ ] Create developer guide for new system
- [ ] Add character emotional state to monitoring dashboard

---

## 🎓 Design Principles

### **1. Symmetric Intelligence**
- User emotions: 11 RoBERTa emotions ✅
- Bot emotions: 11 RoBERTa emotions ✅
- No lossy dimension compression

### **2. Direct Application, Not Mapping**
- Store what RoBERTa detects, don't transform it
- Use adaptive smoothing (EMA-like) for continuity
- Derived properties for high-level analysis

### **3. Computed Properties Over Storage**
- Store raw emotions (11 values)
- Compute intensity, valence, complexity on-demand
- Reduces database complexity

### **4. Graceful Degradation**
- If RoBERTa fails, use fallback (VADER)
- If state retrieval fails, use character baseline
- System never crashes due to missing emotional data

### **5. Character Authenticity First**
- Baselines come from CDL personality
- Homeostasis returns to character-specific baselines
- No "one-size-fits-all" emotional profiles

---

## 🚀 Conclusion

**The current 5-dimension system was a well-intentioned abstraction that became a bottleneck. By adopting full-spectrum 11-emotion tracking for bot states, WhisperEngine achieves:**

1. **Symmetric Intelligence**: User and bot emotions analyzed with same fidelity
2. **No Information Loss**: Store exactly what RoBERTa detects
3. **Richer Character Development**: Characters understand their own emotional complexity
4. **Better Emotional Memory**: Full emotion profiles enable nuanced reflection
5. **EMA Readiness**: Prerequisite for trajectory smoothing enhancement

**This redesign is CRITICAL before implementing EMA trajectory smoothing. EMA operates on emotional state data - if that data is lossy (5 dimensions), EMA can't recover the lost fidelity. We must fix the foundation first.**

**Timeline**: 3 weeks for implementation + 1 week for production validation = **Target completion: Late November 2025**

**Priority**: HIGH - Prerequisite for Q1 2026 EMA implementation

---

**Next Steps**: Review with team, approve architecture, schedule implementation sprint.
