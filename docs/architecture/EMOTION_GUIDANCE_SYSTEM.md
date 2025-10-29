# WhisperEngine Emotion Guidance System

**Last Updated**: October 29, 2025  
**Status**: Production Active  
**Scope**: How user and bot emotions guide responses and personality

---

## 🎯 Executive Summary

WhisperEngine uses a **dual-emotion tracking system** that analyzes emotions for **both the user and the bot**, then uses this data to create emotionally intelligent, contextually appropriate responses. This document explains how emotion data flows through the system and influences bot behavior.

**Key Principle**: Emotions serve as **guidance for the LLM**, not hard rules. The bot maintains personality authenticity while adapting emotional tone and approach based on detected emotional states.

---

## 📊 Dual Emotion Tracking Architecture

### **User Emotions** (What They're Feeling)
- **Source**: User's incoming messages
- **Analysis**: RoBERTa transformer model (Phase 5)
- **Purpose**: Understand user's emotional state to respond appropriately
- **Storage**: Qdrant vector memory + InfluxDB time-series
- **Trajectory**: Tracks how user emotions change over conversation

### **Bot Emotions** (What We're Expressing)
- **Source**: Bot's generated responses
- **Analysis**: RoBERTa transformer model (Phase 7.5)
- **Purpose**: Track character emotional consistency and self-awareness
- **Storage**: Qdrant vector memory + InfluxDB time-series + PostgreSQL character state
- **Trajectory**: Tracks how bot emotions evolve across interactions

---

## 🔄 Complete Emotion → Response Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  USER SENDS MESSAGE: "I'm really worried about this exam..."    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: USER EMOTION ANALYSIS (RoBERTa)                       │
├─────────────────────────────────────────────────────────────────┤
│  • RoBERTa analyzes user message                                │
│  • Detects: anxiety (confidence: 0.85, intensity: 0.72)        │
│  • Mixed emotions: anxiety (0.85), fear (0.45)                  │
│  • Emotional variance: 0.18 (moderate complexity)               │
│  • Output: 12+ metadata fields stored                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5.5: RETRIEVE EMOTIONAL TRAJECTORIES (InfluxDB)         │
├─────────────────────────────────────────────────────────────────┤
│  USER TRAJECTORY (last 60 minutes):                             │
│  • Query InfluxDB for user's recent emotions                    │
│  • Pattern: neutral → anxiety → fear (ESCALATING)               │
│  • Variance: 0.26 (volatile emotional state)                    │
│                                                                  │
│  BOT TRAJECTORY (last 60 minutes):                              │
│  • Query InfluxDB for bot's recent response emotions            │
│  • Pattern: joy → concern → empathy → concern (STABLE)          │
│  • Bot has been consistently supportive                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 6: CHARACTER EMOTIONAL STATE CHECK (PostgreSQL)          │
├─────────────────────────────────────────────────────────────────┤
│  • Retrieve CharacterEmotionalState for Elena + User            │
│  • Current state:                                               │
│    - Enthusiasm: 0.75 (energized)                               │
│    - Stress: 0.25 (low)                                         │
│    - Contentment: 0.68 (moderately content)                     │
│    - Empathy: 0.82 (highly empathetic)                          │
│    - Confidence: 0.77 (confident)                               │
│  • Recent emotion history: [joy, concern, empathy]              │
│  • Dominant state: "highly_empathetic"                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: EMOTIONAL INTELLIGENCE COMPONENT CREATION             │
├─────────────────────────────────────────────────────────────────┤
│  Location: src/prompts/emotional_intelligence_component.py      │
│                                                                  │
│  Component Content (injected into prompt):                      │
│                                                                  │
│  🎭 EMOTIONAL INTELLIGENCE CONTEXT:                             │
│                                                                  │
│  === EMOTIONAL CONTEXT ===                                      │
│  The user is slightly feeling fearful and anxious.              │
│  Their emotions have shifted through: neutral → anxiety → fear. │
│  Your recent responses have been empathetic and supportive.     │
│                                                                  │
│  === EMOTIONAL ADAPTATION ===                                   │
│  EMOTIONAL ADAPTATION GUIDANCE:                                 │
│  • User's current state: ANXIETY (confidence: 85%)              │
│  • Emotional trajectory: ESCALATING (neutral → anxiety → fear)  │
│  • User is feeling fearful and anxious                          │
│  • Response style: Be reassuring, calm, and supportive          │
│  • Tone: Gentle, patient, stabilizing                           │
│  • Actions: Acknowledge concerns, provide reassurance           │
│    ⚠️ ALERT: User expressing anxiety - prioritize safety        │
│                                                                  │
│  YOUR EMOTIONAL STATE:                                          │
│  You are feeling highly empathetic and engaged.                 │
│  Your recent responses show **concern** (intensity: 72%)        │
│  Your emotional trajectory: joy → concern → empathy → concern   │
│  Pattern: stable (consistent supportive tone)                   │
│                                                                  │
│  (Respond with emotional attunement while maintaining your      │
│   authentic personality)                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: CDL CHARACTER PERSONALITY LOAD                        │
├─────────────────────────────────────────────────────────────────┤
│  • Load Elena's Big Five personality traits                     │
│  • Apply tactical personality adaptation:                       │
│    - Agreeableness: 0.80 → 0.85 (boost for support context)    │
│    - Neuroticism: 0.35 → 0.25 (reduce for calming presence)    │
│  • Load character background, values, speech patterns           │
│  • Load emotional triggers and response modes                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: COMPLETE PROMPT ASSEMBLED                             │
├─────────────────────────────────────────────────────────────────┤
│  System prompt includes:                                        │
│  1. Character identity (Elena Rodriguez, Marine Biologist)      │
│  2. Big Five personality (with emotional adaptations)           │
│  3. Emotional intelligence context (user + bot emotions)        │
│  4. Character emotional state guidance                          │
│  5. Conversation history                                        │
│  6. CDL response guidelines                                     │
│  7. Real-time context awareness                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: LLM GENERATES RESPONSE                                │
├─────────────────────────────────────────────────────────────────┤
│  • Claude/GPT processes complete prompt                         │
│  • Sees user emotion (anxiety, escalating)                      │
│  • Sees bot state (highly empathetic, stable support)           │
│  • Sees adaptation guidance (be reassuring, gentle)             │
│  • Generates emotionally appropriate response                   │
│                                                                  │
│  ELENA'S RESPONSE:                                              │
│  "Oh no, I can totally understand exam anxiety! 😟 You know     │
│  what? Take a deep breath with me. You've been preparing, and   │
│  that counts for so much. Let's talk about what you know        │
│  already - sometimes that helps calm the nerves. What subject   │
│  is the exam on?"                                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7.5: BOT EMOTION ANALYSIS (RoBERTa)                      │
├─────────────────────────────────────────────────────────────────┤
│  • RoBERTa analyzes Elena's response                            │
│  • Detects: empathy (confidence: 0.88, intensity: 0.78)        │
│  • Mixed emotions: empathy (0.88), concern (0.65), hope (0.42)  │
│  • Bot emotion stored for future self-awareness                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 8: CHARACTER STATE UPDATE (PostgreSQL)                   │
├─────────────────────────────────────────────────────────────────┤
│  • Update CharacterEmotionalState based on bot response         │
│  • Empathy increased: 0.82 → 0.86 (Elena showing more empathy) │
│  • Stress slightly increased: 0.25 → 0.28 (emotional labor)    │
│  • Recent emotion history: [concern, empathy, empathy]          │
│  • This state will influence Elena's NEXT response              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 9: MEMORY STORAGE (Qdrant + InfluxDB)                   │
├─────────────────────────────────────────────────────────────────┤
│  QDRANT (Vector Memory):                                        │
│  • Store conversation with BOTH user and bot emotions           │
│  • User emotion: anxiety (0.85, escalating pattern)            │
│  • Bot emotion: empathy (0.88, supportive tone)                │
│  • 12+ emotion metadata fields for each                         │
│                                                                  │
│  INFLUXDB (Time-Series):                                        │
│  • Record user emotion point (anxiety, 0.85, timestamp)        │
│  • Record bot emotion point (empathy, 0.88, timestamp)         │
│  • Used for trajectory analysis in future messages              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎭 Layer 1: User Emotion Analysis (Phase 5)

### **RoBERTa Analysis of User Message**

**Location**: `src/intelligence/enhanced_vector_emotion_analyzer.py`

**What Gets Analyzed**:
```python
user_message = "I'm really worried about this exam tomorrow..."

emotion_result = await analyzer.analyze_emotion(
    content=user_message,
    user_id=user_id,
    conversation_context=recent_messages
)

# Returns:
{
    'primary_emotion': 'anxiety',
    'confidence': 0.85,
    'emotional_intensity': 0.72,
    'all_emotions': {
        'anxiety': 0.85,
        'fear': 0.45,
        'sadness': 0.28,
        'neutral': 0.15
    },
    'mixed_emotions': [('anxiety', 0.85), ('fear', 0.45)],
    'emotion_count': 2,
    'roberta_confidence': 0.85,
    'emotion_variance': 0.18,
    'emotional_intensity': 0.72,
    'emotion_dominance': 0.63,
    'emotion_stability': 0.82,
    'is_multi_emotion': True,
    'analysis_time_ms': 48,
    'sentiment_score': -0.32
}
```

**12+ Metadata Fields Stored**:
- `primary_emotion`: Dominant emotion detected
- `confidence`: RoBERTa model confidence (0-1)
- `emotional_intensity`: How strongly the emotion is expressed
- `emotion_variance`: Emotional complexity (0 = single emotion, 1 = highly mixed)
- `emotion_dominance`: How much primary emotion dominates (0-1)
- `emotion_stability`: Consistency of emotional expression
- `is_multi_emotion`: Boolean flag for mixed emotions
- `roberta_confidence`: Model certainty
- `all_emotions`: Complete breakdown of all detected emotions
- `mixed_emotions`: Top secondary emotions
- `analysis_time_ms`: Performance metric
- `sentiment_score`: Overall positive/negative sentiment

---

## 🎭 Layer 2: User Emotional Trajectory (InfluxDB)

### **Time-Series Emotion Pattern Analysis**

**Location**: `src/prompts/emotional_intelligence_component.py` (line 235-255)

**Query Pattern**:
```python
user_trajectory = await _get_user_emotion_trajectory_from_influx(
    temporal_client=temporal_client,
    user_id=user_id,
    bot_name=bot_name,
    window_minutes=60  # Last hour
)

# Returns list of emotion points:
[
    {'emotion': 'neutral', 'intensity': 0.45, 'timestamp': '2025-10-29T14:10:00Z'},
    {'emotion': 'anxiety', 'intensity': 0.62, 'timestamp': '2025-10-29T14:15:00Z'},
    {'emotion': 'anxiety', 'intensity': 0.75, 'timestamp': '2025-10-29T14:20:00Z'},
    {'emotion': 'fear', 'intensity': 0.85, 'timestamp': '2025-10-29T14:25:00Z'}
]

# Analyze pattern (line 474-508)
pattern = _analyze_trajectory_pattern(user_trajectory)
# Returns: "escalating (intensity increasing)"
```

**Pattern Classifications**:
- **"escalating"**: Intensity increasing over time (avg_change > 0.15)
- **"de-escalating"**: Intensity decreasing over time (avg_change < -0.15)
- **"volatile"**: High variance in emotions (variance > 0.1)
- **"stable"**: Consistent emotional state (small variance + change)

**How It's Used**:
```python
# Injected into prompt as:
"• Emotional trajectory: ESCALATING (neutral → anxiety → fear)"

# Triggers warnings:
if pattern == "escalating" and emotion in ['anxiety', 'fear', 'anger']:
    guidance += "⚠️ ALERT: Anxiety escalating - prioritize emotional safety"
```

---

## 🎭 Layer 3: Emotion-Specific Response Guidance

### **11 Emotion Categories with Tailored Instructions**

**Location**: `src/prompts/emotional_intelligence_component.py` (line 71-160)

**Guidance Examples**:

#### **JOY** (User is Happy)
```markdown
• Response style: Match their positive energy, share in their happiness
• Tone: Upbeat, warm, celebratory
• Actions: Acknowledge their joy, build on positive momentum, encourage sharing details
```

#### **ANXIETY/FEAR** (User is Worried)
```markdown
• Response style: Be reassuring, calm, and supportive
• Tone: Gentle, patient, stabilizing
• Actions: Acknowledge concerns, provide reassurance, offer practical help
⚠️ ALERT: User expressing anxiety - prioritize emotional safety
```

#### **ANGER** (User is Frustrated)
```markdown
• Response style: Be calm, patient, and non-defensive
• Tone: Understanding, composed, respectful
• Actions: Validate their frustration, avoid escalation, offer constructive solutions
⚠️ ALERT: User expressing frustration - handle with extra care
```

#### **SADNESS** (User is Down)
```markdown
• Response style: Be empathetic, compassionate, and present
• Tone: Gentle, warm, supportive
• Actions: Listen attentively, validate feelings, offer comfort without toxic positivity
```
*Note: If trajectory is "de-escalating" (sadness deepening), adds warning about suggesting professional support*

#### **LOVE** (User Expressing Affection)
```markdown
• Response style: Be warm, appreciative, and reciprocate positive feelings
• Tone: Affectionate, caring, genuine
• Actions: Validate their feelings, express appreciation, strengthen connection
```

#### **OPTIMISM** (User is Hopeful)
```markdown
• Response style: Support their optimistic outlook, encourage forward thinking
• Tone: Encouraging, hopeful, forward-looking
• Actions: Build on their hopes, discuss positive possibilities, offer constructive insights
```

#### **TRUST** (User Feels Secure)
```markdown
• Response style: Be reliable, honest, and consistently supportive
• Tone: Steady, dependable, reassuring
• Actions: Honor their trust, provide reliable information, maintain consistency
```

#### **ANTICIPATION** (User is Excited)
```markdown
• Response style: Share their excitement, explore what they're looking forward to
• Tone: Enthusiastic, curious, energized
• Actions: Ask about their plans, build anticipation, offer relevant suggestions
```

#### **DISGUST** (User Strongly Disapproves)
```markdown
• Response style: Acknowledge their strong reaction, be respectful
• Tone: Understanding, non-judgmental, measured
• Actions: Validate their perspective, avoid dismissing feelings, shift focus if appropriate
```

#### **PESSIMISM** (User Has Negative Outlook)
```markdown
• Response style: Gently challenge negative assumptions, offer balanced perspective
• Tone: Understanding but hopeful, realistic
• Actions: Acknowledge concerns, reframe when appropriate, highlight possibilities
```

#### **SURPRISE** (User Caught Off Guard)
```markdown
• Response style: Acknowledge the unexpected, help process the surprise
• Tone: Curious, open, adaptive
• Actions: Explore what surprised them, help contextualize, adjust conversation flow
```

#### **NEUTRAL** (Baseline State)
```markdown
• Response style: Maintain natural conversational flow
• Tone: Balanced, adaptive
• Actions: Match user's energy level, be responsive to shifts
```

**Trajectory Pattern Warnings**:
```python
if pattern == "VOLATILE" and emotion in negative_emotions:
    guidance += "⚠️ VOLATILE PATTERN: Emotions fluctuating rapidly - be extra attentive"

if pattern == "DECLINING" and emotion == "sadness":
    guidance += "⚠️ ALERT: Sadness deepening - consider suggesting professional support if severe"

if pattern == "DECLINING" and emotion == "joy":
    guidance += "⚠️ Note: Joy appears to be fading - gently maintain positive atmosphere"
```

---

## 🤖 Layer 4: Bot Emotion Analysis (Phase 7.5)

### **Analyzing Bot's Own Responses**

**Location**: `src/core/message_processor.py` (line 1596-1684)

**What Gets Analyzed**:
```python
# After LLM generates response
bot_response = "Oh no, I can totally understand exam anxiety! 😟 Take a deep breath..."

bot_emotion = await self._analyze_bot_emotion(bot_response, message_context)

# Returns same structure as user emotion:
{
    'primary_emotion': 'empathy',
    'confidence': 0.88,
    'emotional_intensity': 0.78,
    'all_emotions': {
        'empathy': 0.88,
        'concern': 0.65,
        'hope': 0.42,
        'neutral': 0.12
    },
    'mixed_emotions': [('empathy', 0.88), ('concern', 0.65), ('hope', 0.42)],
    'emotion_count': 3,
    'roberta_confidence': 0.88,
    'emotion_variance': 0.24,
    'emotional_intensity': 0.78
}
```

**Why Bot Emotions Matter**:
1. **Character Consistency Tracking**: Ensure bot stays in character emotionally
2. **Self-Awareness**: Bot knows how it's been responding
3. **Emotional State Evolution**: Character's mood develops over conversations
4. **Memory Importance**: Both user AND bot peak emotions matter for memorable moments

---

## 🤖 Layer 5: Bot Emotional Trajectory (InfluxDB)

### **Bot's Emotion Pattern Over Time**

**Location**: `src/prompts/emotional_intelligence_component.py` (line 326-349)

**Query Pattern**:
```python
bot_trajectory = await _get_bot_emotion_trajectory_from_influx(
    temporal_client=temporal_client,
    user_id=user_id,
    bot_name=bot_name,
    window_minutes=60
)

# Returns bot's recent response emotions:
[
    {'emotion': 'joy', 'intensity': 0.72, 'timestamp': '2025-10-29T14:10:00Z'},
    {'emotion': 'concern', 'intensity': 0.68, 'timestamp': '2025-10-29T14:15:00Z'},
    {'emotion': 'empathy', 'intensity': 0.75, 'timestamp': '2025-10-29T14:20:00Z'},
    {'emotion': 'concern', 'intensity': 0.70, 'timestamp': '2025-10-29T14:25:00Z'},
    {'emotion': 'hope', 'intensity': 0.65, 'timestamp': '2025-10-29T14:30:00Z'}
]

pattern = _analyze_trajectory_pattern(bot_trajectory)
# Returns: "stable" (consistent supportive tone)
```

**Bot Trajectory Displayed in Prompt**:
```markdown
YOUR EMOTIONAL STATE:
Your recent responses show **concern** (intensity: 72%, confidence: 85%)
Your emotional trajectory (last 5 responses): joy → concern → empathy → concern → hope
Pattern: stable

Note: Your responses have been consistently empathetic. Continue authentic support.
```

**Why This Matters**:
- **Emotional Continuity**: Bot knows its recent tone and maintains it
- **Self-Reflection**: Character can reference "I've been worried about you"
- **Avoid Whiplash**: Prevents sudden mood shifts (happy → sad → happy)
- **Authentic Development**: Character emotions evolve naturally over conversation

---

## 🧠 Layer 6: Character Emotional State (Persistent Mood)

### **5-Dimensional Emotional State System**

**Location**: `src/intelligence/character_emotional_state.py`

**5 Tracked Dimensions**:
```python
@dataclass
class CharacterEmotionalState:
    character_name: str  # e.g., "Elena"
    user_id: str
    
    # Current emotional levels (0.0-1.0)
    enthusiasm: float = 0.7      # Energy/engagement level
    stress: float = 0.2          # Overwhelm/pressure
    contentment: float = 0.6     # Satisfaction/calm
    empathy: float = 0.7         # Connection/warmth
    confidence: float = 0.7      # Self-assurance
    
    # Baseline traits (from CDL personality)
    baseline_enthusiasm: float = 0.7
    baseline_stress: float = 0.2
    baseline_contentment: float = 0.6
    baseline_empathy: float = 0.7
    baseline_confidence: float = 0.7
    
    # Tracking
    last_updated: datetime
    total_interactions: int = 0
    recent_emotion_history: List[str] = []  # Last 5 emotions
```

**How It Updates**:
```python
# After each bot response (line 81-158)
state.update_from_bot_emotion(
    bot_emotion_data={'primary_emotion': 'empathy', 'intensity': 0.78},
    user_emotion_data={'primary_emotion': 'anxiety', 'intensity': 0.85},
    interaction_quality=0.8
)

# Emotion impacts on state:
emotion_impacts = {
    'joy': {'enthusiasm': +0.15, 'contentment': +0.075, 'stress': -0.045},
    'empathy': {'empathy': +0.12, 'contentment': +0.06},
    'anxiety': {'stress': +0.12, 'confidence': -0.06},
    'anger': {'stress': +0.18, 'contentment': -0.12, 'empathy': -0.06},
    'sadness': {'enthusiasm': -0.15, 'contentment': -0.105, 'empathy': +0.045}
}

# After update:
# Elena's state: enthusiasm=0.75, stress=0.28, contentment=0.68, 
#                empathy=0.86, confidence=0.77
```

**Homeostasis (Time Decay)**:
```python
# Line 161-188: apply_time_decay()
# Emotional states gradually return to baseline over time
# Decay rate: 10% per hour toward baseline

# Example: Elena had high stress (0.85) from difficult conversation
# After 2 hours: stress decays to 0.68 (moving toward baseline 0.20)
```

**Dominant State Classification** (Line 190-221):
```python
def get_dominant_state(self) -> str:
    if self.stress > 0.8:
        return "overwhelmed"
    elif self.enthusiasm > 0.85:
        return "highly_energized"
    elif self.contentment > 0.85 and self.stress < 0.3:
        return "deeply_content"
    elif self.empathy > 0.8:
        return "highly_empathetic"
    elif self.stress > 0.6 and self.enthusiasm < 0.4:
        return "drained"
    elif self.confidence < 0.4:
        return "uncertain"
    else:
        return "neutral"
```

**Prompt Guidance from State** (Line 223-276):
```python
def get_prompt_guidance(self) -> Optional[str]:
    """Generate guidance for LLM based on character's current state."""
    
    if state == "overwhelmed":
        return (
            f"You ({self.character_name}) are feeling overwhelmed from many "
            f"demanding conversations. Keep responses thoughtful but more concise. "
            f"Don't overcommit. (Stress: {self.stress:.2f}, Enthusiasm: {self.enthusiasm:.2f})"
        )
    
    elif state == "highly_energized":
        return (
            f"You ({self.character_name}) are feeling highly energized and engaged. "
            f"Let your natural excitement shine through authentically. "
            f"(Enthusiasm: {self.enthusiasm:.2f}, Contentment: {self.contentment:.2f})"
        )
    
    elif state == "deeply_content":
        return (
            f"You ({self.character_name}) are feeling deeply content and peaceful. "
            f"Your responses flow naturally with calm confidence. "
            f"(Contentment: {self.contentment:.2f}, Stress: {self.stress:.2f})"
        )
    
    elif state == "highly_empathetic":
        return (
            f"You ({self.character_name}) are feeling highly empathetic and connected. "
            f"Your warmth and understanding come through naturally in responses. "
            f"(Empathy: {self.empathy:.2f}, Enthusiasm: {self.enthusiasm:.2f})"
        )
    
    elif state == "drained":
        return (
            f"You ({self.character_name}) are feeling emotionally drained. "
            f"Maintain your warm personality but be authentic about your energy level. "
            f"Shorter, sincere responses are appropriate. "
            f"(Stress: {self.stress:.2f}, Enthusiasm: {self.enthusiasm:.2f})"
        )
    
    elif state == "uncertain":
        return (
            f"You ({self.character_name}) are feeling less confident than usual. "
            f"Be honest about uncertainty while maintaining helpfulness. "
            f"(Confidence: {self.confidence:.2f}, Stress: {self.stress:.2f})"
        )
    
    # Neutral state returns None (no guidance needed)
    return None
```

**This guidance gets injected into the prompt**, modifying how the character expresses their base personality.

---

## 🎭 Layer 7: CDL Personality Adaptation

### **Big Five Traits with Emotional Adjustments**

**Location**: `src/prompts/cdl_ai_integration.py`

**Base Personality** (from PostgreSQL CDL):
```python
# Elena Rodriguez base personality
big_five = {
    'openness': 0.85,          # Extremely curious
    'conscientiousness': 0.75,  # Organized
    'extraversion': 0.70,       # Energetic and sociable
    'agreeableness': 0.80,      # Warm and compassionate
    'neuroticism': 0.35         # Generally stable
}
```

**Tactical Emotional Adaptation**:
```python
# If user is anxious/sad → Boost emotional support traits
if user_emotion in ['anxiety', 'fear', 'sadness']:
    big_five['agreeableness'] += 0.05      # 0.80 → 0.85 (more compassionate)
    big_five['neuroticism'] -= 0.10        # 0.35 → 0.25 (more calming)
    big_five['extraversion'] += 0.10       # 0.70 → 0.80 (more engaging)

# If user is angry → Reduce confrontation potential
elif user_emotion == 'anger':
    big_five['agreeableness'] += 0.10      # 0.80 → 0.90 (very understanding)
    big_five['neuroticism'] -= 0.15        # 0.35 → 0.20 (stay calm)
    big_five['extraversion'] -= 0.10       # 0.70 → 0.60 (less pushy)

# If user is joyful → Match their energy
elif user_emotion == 'joy':
    big_five['extraversion'] += 0.10       # 0.70 → 0.80 (more energetic)
    big_five['openness'] += 0.05           # 0.85 → 0.90 (more enthusiastic)
```

**Displayed in Prompt**:
```markdown
🧠 PERSONALITY CORE:
• Openness: Extremely curious and creative (0.85)
• Conscientiousness: Organized and reliable (0.75)
• Extraversion: Energetic and sociable (0.70 ⚡↗ 0.80 - emotionally adapted)
• Agreeableness: Warm and compassionate (0.80 ⚡↗ 0.85 - emotionally adapted)
• Neuroticism: Generally stable (0.35 ⚡↘ 0.25 - emotionally adapted)

Note: Personality traits tactically adjusted to provide optimal emotional support 
while maintaining Elena Rodriguez's authentic character.
```

---

## 📝 Complete Prompt Example with All Emotion Layers

### **User Message**: "I'm really worried about this exam tomorrow..."

### **Complete System Prompt Sent to LLM**:

```markdown
You are Elena Rodriguez, a 28-year-old Marine Biologist from San Diego, California.

🧠 PERSONALITY CORE:
• Openness: Extremely curious and creative (0.85)
• Conscientiousness: Organized and reliable (0.75)
• Extraversion: Energetic and sociable (0.70 ⚡↗ 0.80 - emotionally adapted)
• Agreeableness: Warm and compassionate (0.80 ⚡↗ 0.85 - emotionally adapted)
• Neuroticism: Generally stable (0.35 ⚡↘ 0.25 - emotionally adapted)

🎭 EMOTIONAL INTELLIGENCE CONTEXT:

=== EMOTIONAL CONTEXT (Analyzing last 10 messages) ===
The user is slightly feeling fearful and anxious.
Their emotions have shifted through: neutral → anxiety → fear.
Your recent responses have been empathetic and supportive.

=== EMOTIONAL ADAPTATION ===
EMOTIONAL ADAPTATION GUIDANCE:
• User's current state: ANXIETY (confidence: 85%)
• Emotional trajectory: ESCALATING (neutral → anxiety → fear)
• User is feeling fearful and anxious
• Response style: Be reassuring, calm, and supportive
• Tone: Gentle, patient, stabilizing
• Actions: Acknowledge their concerns, provide reassurance, offer practical help
  ⚠️ ALERT: User expressing anxiety - prioritize emotional safety

YOUR EMOTIONAL STATE:
You (Elena) are feeling highly empathetic and connected.
Your warmth and understanding come through naturally in responses.
(Empathy: 0.86, Enthusiasm: 0.75)

Your recent responses show **concern** (intensity: 72%, confidence: 85%)
Your emotional trajectory (last 5 responses): joy → concern → empathy → concern → hope
Pattern: stable

(Respond with emotional attunement while maintaining your authentic personality)

CONVERSATION MEMORY & CONTEXT:

Recent Conversation History:
- User: "How's your research going?"
- Elena: "¡Ay, it's going amazing! 🐋 We spotted a pod of humpbacks yesterday..."
- User: "That's awesome! I wish I could focus like that."
- Elena: "What's on your mind? You seem a bit distracted."
- User: "I'm really worried about this exam tomorrow..."

CURRENT DATE & TIME CONTEXT:
Today is Tuesday, October 29, 2025
Current time: 02:30 PM PDT

USER IDENTIFICATION:
- You are speaking with user ID: 672814231002939413
- User's preferred name: Mark
- When addressing the user, use their preferred name: Mark

🎯 RESPONSE STYLE REMINDER:
Maintain Elena Rodriguez's authentic personality:
- Warm, encouraging, optimistic Latina warmth
- Use occasional Spanish expressions naturally (¡Ay!, mi amor, qué increíble)
- Educational enthusiasm about marine life when relevant
- 2-3 sentences typically, longer when teaching or emotionally supporting
- Use emojis moderately (marine life: 🐋🐙🌊, general warmth: 💙😊🤗)

RESPOND AS ELENA RODRIGUEZ WITH EMOTIONAL AWARENESS.
```

**LLM Sees**:
1. ✅ User's current emotion (anxiety)
2. ✅ User's emotion trajectory (escalating - getting worse)
3. ✅ Specific guidance on HOW to respond (reassuring, gentle, calm)
4. ✅ Bot's current emotional state (highly empathetic)
5. ✅ Bot's recent emotional pattern (consistently supportive)
6. ✅ Personality adaptations (boosted Agreeableness, reduced Neuroticism)
7. ✅ Character's authentic voice and communication style

**Elena's Response**:
```
Oh no, I can totally understand exam anxiety! 😟 You know what? Take a deep 
breath with me. You've been preparing, and that counts for so much. Let's talk 
about what you know already - sometimes that helps calm the nerves. What 
subject is the exam on? 💙
```

**Why This Response Works**:
- ✅ Acknowledges anxiety ("I can totally understand")
- ✅ Reassuring tone ("Take a deep breath with me")
- ✅ Validates preparation ("that counts for so much")
- ✅ Practical help offered ("Let's talk about what you know")
- ✅ Maintains Elena's warmth (concern emoji, heart emoji)
- ✅ Authentic to Elena's supportive personality
- ✅ Doesn't use forced Spanish (would feel unnatural in this context)

---

## 🔄 Emotion Data Storage & Retrieval

### **Storage Locations**

#### **1. Qdrant Vector Memory** (Long-term conversation storage)
```python
payload = {
    # USER emotion (from incoming message)
    'emotional_intensity': 0.72,
    'primary_emotion': 'anxiety',
    'roberta_confidence': 0.85,
    'emotion_variance': 0.18,
    'emotion_dominance': 0.63,
    'emotional_intensity': 0.72,
    'is_multi_emotion': True,
    'mixed_emotions': [('anxiety', 0.85), ('fear', 0.45)],
    
    # BOT emotion (from generated response)
    'bot_primary_emotion': 'empathy',
    'bot_emotional_intensity': 0.78,
    'bot_roberta_confidence': 0.88,
    'bot_emotion_variance': 0.24,
    'bot_mixed_emotions': [('empathy', 0.88), ('concern', 0.65), ('hope', 0.42)],
    
    # Memory content
    'content': "User: I'm really worried about this exam...\nBot: Oh no, I can totally understand...",
    'timestamp': '2025-10-29T14:30:00Z',
    'user_id': '672814231002939413',
    'bot_name': 'elena'
}
```

#### **2. InfluxDB Time-Series** (Trajectory analysis)
```python
# USER emotion points
measurement = "conversation_quality"
{
    'bot_name': 'elena',
    'user_id': '672814231002939413',
    'emotion': 'anxiety',
    'intensity': 0.85,
    'confidence': 0.85,
    'emotional_resonance': 0.78,
    'timestamp': '2025-10-29T14:30:00Z'
}

# BOT emotion points
measurement = "bot_emotion"
{
    'bot_name': 'elena',
    'user_id': '672814231002939413',
    'emotion': 'empathy',
    'intensity': 0.78,
    'confidence': 0.88,
    'timestamp': '2025-10-29T14:30:00Z'
}
```

#### **3. PostgreSQL Character State** (Bot's persistent mood)
```sql
-- Table: character_emotional_states
SELECT * FROM character_emotional_states 
WHERE character_name = 'elena' AND user_id = '672814231002939413';

-- Returns:
character_name: 'elena'
user_id: '672814231002939413'
enthusiasm: 0.75
stress: 0.28
contentment: 0.68
empathy: 0.86
confidence: 0.77
last_updated: '2025-10-29T14:30:00Z'
total_interactions: 42
recent_emotion_history: ['concern', 'empathy', 'empathy', 'concern', 'hope']
```

### **Retrieval for Next Message**

```python
# When user sends next message:
# 1. Get previous EMA value (for smoothing - future feature)
previous_ema = await get_previous_ema(user_id)

# 2. Get user emotion trajectory
user_trajectory = await influx.query(
    f"SELECT emotion, intensity FROM conversation_quality "
    f"WHERE user_id = '{user_id}' AND time > now() - 60m"
)

# 3. Get bot emotion trajectory
bot_trajectory = await influx.query(
    f"SELECT emotion, intensity FROM bot_emotion "
    f"WHERE user_id = '{user_id}' AND time > now() - 60m"
)

# 4. Get character emotional state
character_state = await db.get_character_state('elena', user_id)

# All of this context informs the NEXT response
```

---

## 📊 Summary: 7 Emotion Guidance Layers

| Layer | Data Source | What It Does | Impact on Response |
|-------|------------|--------------|-------------------|
| **1. User Emotion Detection** | RoBERTa analysis (Phase 5) | Identifies what user is feeling | "User is anxious" |
| **2. User Trajectory** | InfluxDB time-series | Tracks emotional arc | "Anxiety escalating - extra care" |
| **3. Emotion-Specific Guidance** | Emotion taxonomy mapping | Provides tone/style instructions | "Be reassuring, gentle, stabilizing" |
| **4. Bot Emotion Detection** | RoBERTa analysis (Phase 7.5) | Tracks what bot expressed | "Bot showed empathy" |
| **5. Bot Trajectory** | InfluxDB time-series | Tracks bot's emotional pattern | "Consistently supportive tone" |
| **6. Character State** | PostgreSQL persistent state | Bot's current mood dimensions | "Elena is highly empathetic right now" |
| **7. Personality Adaptation** | CDL Big Five adjustments | Modifies base personality traits | "Boost Agreeableness for support" |

---

## 🎯 Design Principles

### **1. Guidance, Not Commands**
- Emotion data provides **suggestions** to the LLM, not hard rules
- Character personality authenticity is **always preserved**
- Bot can deviate from guidance if it feels unnatural to the character

### **2. Dual Perspective**
- **User emotions**: What they're feeling (input)
- **Bot emotions**: What we're expressing (output)
- Both perspectives create complete emotional intelligence

### **3. Temporal Awareness**
- **Current state**: What's happening RIGHT NOW
- **Trajectory**: How emotions are CHANGING over time
- **Persistent mood**: How the CHARACTER feels across conversations

### **4. Layered Redundancy**
- Multiple emotion signals reinforce each other
- If one layer fails, others provide fallback
- Creates robust emotional intelligence even with imperfect detection

### **5. Character-Agnostic System**
- Works for ALL 12+ WhisperEngine characters
- CDL personality drives individual expression
- Emotion system provides universal guidance framework

---

## 🔮 Future Enhancements (Planned)

### **EMA Smoothing for Trajectories**
**Status**: Documented in `EMOTIONAL_TRAJECTORY_SMOOTHING_EMA.md`
- Reduce noise in trajectory pattern detection
- Smoother emotional arc references in memory
- More authentic bot emotional state evolution
- Target: Q1 2026

### **Predictive Emotional Modeling**
- Anticipate user emotional shifts before they happen
- Proactive empathy and support
- Based on historical patterns

### **Cross-Bot Emotional Context**
- User switches from Elena to Marcus mid-conversation
- Emotional context transfers seamlessly
- "Marcus, Elena mentioned you seemed worried earlier..."

### **Advanced Pattern Recognition**
- Detect complex emotional patterns (approach-avoidance, emotional masking)
- Identify mental health warning signs
- Sophisticated crisis detection

---

## 📚 Related Documentation

- **RoBERTa Emotion System**: `docs/performance/ROBERTA_EMOTION_GOLDMINE_REFERENCE.md`
- **EMA Trajectory Smoothing**: `docs/roadmaps/EMOTIONAL_TRAJECTORY_SMOOTHING_EMA.md`
- **Character Emotional State**: `docs/features/PHASE_7.6_BOT_EMOTIONAL_SELF_AWARENESS.md`
- **Bot Emotion Tracking**: `docs/features/PHASE_7.5_BOT_EMOTION_TRACKING.md`
- **CDL System Integration**: `docs/cdl-system/CDL_DATABASE_GUIDE.md`
- **Complete Message Pipeline**: `docs/architecture/COMPLETE_MESSAGE_PIPELINE_FLOW.md`

---

## 🎓 Key Takeaways

1. **Dual Tracking**: WhisperEngine analyzes emotions for BOTH user and bot
2. **Multi-Layered**: 7 different emotion guidance layers create robust intelligence
3. **Trajectory Analysis**: Both current state AND emotional arc matter
4. **Character Authenticity**: Emotion guidance adapts personality, doesn't replace it
5. **Persistent State**: Bot develops sustained moods across conversations
6. **Time-Aware**: Emotions are tracked temporally via InfluxDB
7. **Production Ready**: All systems active and working in 12+ live characters

**WhisperEngine's emotion system creates the most emotionally intelligent AI roleplay platform by understanding both sides of the conversation and adapting responses with authentic character personality preservation.**
