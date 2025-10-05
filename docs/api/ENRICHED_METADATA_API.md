# Enriched Metadata API Response

**Date**: October 5, 2025  
**Status**: ✅ Production Ready  
**Audience**: 3rd Party Developers & Integration Partners  
**Purpose**: Comprehensive AI intelligence data for chat applications and analytics dashboards

## Overview

WhisperEngine's HTTP Chat API (`/api/chat`) returns **rich AI intelligence metadata** alongside every character response. This metadata gives you deep insights into:

- **Emotion Detection** - Both user and bot emotional states with mixed emotions
- **Relationship Tracking** - Affection, trust, and attunement scores (0-100 scale)
- **Memory Intelligence** - Vector search quality and semantic relevance
- **Character Context** - CDL personality system and communication style
- **Performance Metrics** - Processing time breakdown by AI phase
- **Conversation Analysis** - Context switches, urgency detection, empathy calibration
- **Temporal Intelligence** - Confidence evolution over time (Phase 5 analytics)

### Key Feature: Bot Emotional Intelligence (NEW - Phase 7.5 & 7.6)

WhisperEngine now tracks **bot/character emotions** in addition to user emotions, including:
- **Bot Emotion Analysis** - Character's emotional state from generated responses
- **Mixed Emotions** - Emotional complexity (joy + excitement, sadness + hope)
- **Emotional Trajectory** - Bot's emotional patterns across conversations (intensifying, calming, stable)
- **Self-Aware Responses** - Characters factor their emotional state into responses

You can control the level of metadata detail using the `metadata_level` parameter to optimize performance and bandwidth for your use case.

## Metadata Levels

WhisperEngine supports three metadata levels to balance between payload size, processing time, and data richness. Choose the level that matches your application's needs:

### 🏃 `basic` - Lightweight Chat Applications
**Perfect for**: Simple chatbots, mobile apps, high-throughput services, webhooks  
**Payload size**: ~200 bytes (99% smaller than extended)  
**Processing overhead**: Negligible (0ms)  
**Best when**: You only need the response text and basic success indicators

**What you get**:
```json
{
  "metadata": {
    "memory_count": 4,              // Number of memories retrieved
    "knowledge_stored": false,      // Did we learn new facts?
    "memory_stored": true,          // Was conversation saved?
    "processing_time_ms": 1250      // Total processing time
  }
}
```

**Use Case Example**: Mobile chat app where bandwidth matters:
```javascript
// Mobile app that just needs fast responses
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userId,
    message: userMessage,
    metadata_level: 'basic'  // Minimal data, fastest response
  })
});
// Perfect for: React Native, Flutter, simple web chats
```

---

### 🎯 `standard` - Production Chat Applications (DEFAULT)
**Perfect for**: Production apps that use AI intelligence, emotion-aware UIs, context-sensitive features  
**Payload size**: ~5-10 KB  
**Processing overhead**: Minimal (0ms - already calculated)  
**Best when**: You want emotion detection, security validation, and AI intelligence without analytics overhead

**What you get** (all of `basic` PLUS):
```json
{
  "metadata": {
    "ai_components": {
      "emotion_data": {
        "primary_emotion": "joy",
        "intensity": 0.85,
        "mixed_emotions": [["excitement", 0.72]]  // Emotional complexity
      },
      "bot_emotion": {                    // NEW: Bot's emotional state
        "primary_emotion": "joy",
        "intensity": 0.85,
        "mixed_emotions": [["excitement", 0.72], ["curiosity", 0.45]]
      },
      "phase4_intelligence": {...},       // Context analysis
      "context_analysis": {...}           // Conversation flow
    },
    "security_validation": {
      "is_safe": true,
      "warnings": []
    }
  }
}
```

**Example Dialog - User Emotion Detection**:

| User Message | primary_emotion | intensity | mixed_emotions | Why? |
|--------------|-----------------|-----------|----------------|------|
| "I'm so happy! I got the promotion!" | joy | 0.92 | [["excitement", 0.88]] | Strong positive emotion |
| "This is frustrating..." | anger | 0.65 | [["disappointment", 0.55]] | Frustrated tone |
| "I don't know what to do anymore :(" | sadness | 0.78 | [["confusion", 0.62], ["hopelessness", 0.48]] | Multiple negative emotions |
| "What's the weather?" | neutral | 0.20 | [] | Factual, emotionless query |
| "OMG you won't believe what happened!" | excitement | 0.85 | [["surprise", 0.72]] | High energy, enthusiastic |
| "I'm scared about the surgery tomorrow" | fear | 0.80 | [["anxiety", 0.75], ["sadness", 0.45]] | Multiple anxious emotions |
| "I love spending time with you" | love | 0.88 | [["joy", 0.82], ["gratitude", 0.68]] | Affectionate, positive |

**Complex Emotional Dialog Example**:

```
User: "I got accepted to Harvard! But I'm terrified of leaving home and 
       failing. What if I'm not smart enough? But I'm also SO excited!"

Emotion Analysis:
  primary_emotion: "excitement"       (0.82 - dominant feeling)
  intensity: 0.82
  mixed_emotions: [
    ["fear", 0.75],                   (anxiety about failing)
    ["joy", 0.70],                    (happiness about acceptance)
    ["anxiety", 0.68],                (worry about leaving home)
    ["self-doubt", 0.55]              (questioning abilities)
  ]
  emotion_count: 5                    (complex emotional state)
  confidence: 0.88                    (high confidence in detection)
```

**Use Case Example**: Chat application with emotion-based UI:
```javascript
// Production chat app with emotional intelligence
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userId,
    message: userMessage
    // metadata_level defaults to 'standard'
  })
});

const data = await response.json();

// Use emotion data for UI elements
const userEmotion = data.metadata.ai_components.emotion_data.primary_emotion;
const botEmotion = data.metadata.ai_components.bot_emotion.primary_emotion;

// Display emotion indicators
showUserEmotionIcon(userEmotion);      // 😊 Joy
showBotEmotionAnimation(botEmotion);    // Character smiling animation

// Security validation
if (!data.metadata.security_validation.is_safe) {
  showWarning("Message blocked for safety");
}
```

---

### 📊 `extended` - Analytics Dashboards & Admin Interfaces
**Perfect for**: Analytics dashboards, debugging tools, admin panels, research environments  
**Payload size**: ~15-25 KB  
**Processing overhead**: Low (~5-10ms additional)  
**Best when**: You're building analytics visualization, debugging AI behavior, or need complete system insights

**What you get** (all of `standard` PLUS):
```json
{
  "metadata": {
    "knowledge_details": {              // Fact extraction analytics
      "facts_extracted": 2,
      "entities_discovered": 3,
      "relationships_created": 1
    },
    "vector_memory": {                  // Memory search quality
      "memories_retrieved": 10,
      "average_relevance_score": 0.873,
      "embedding_model": "all-MiniLM-L6-v2"
    },
    "temporal_intelligence": {          // Phase 5 analytics
      "confidence_evolution": 0.820,
      "user_fact_confidence": 0.750,
      "relationship_confidence": 0.880
    },
    "character_context": {              // CDL personality system
      "character_name": "Dotty",
      "personality_system": "cdl",
      "communication_style": "authentic_character_voice"
    },
    "relationship": {                   // User-bot relationship
      "affection": 45,
      "trust": 38,
      "attunement": 52,
      "relationship_level": "acquaintance"
    },
    "processing_pipeline": {            // Performance breakdown
      "phase2_emotion_analysis_ms": 9.44,
      "phase4_intelligence_ms": 9.52,
      "total_processing_ms": 4424
    },
    "conversation_intelligence": {      // Flow analysis
      "context_switches_detected": 1,
      "conversation_mode": "standard"
    }
  }
}
```

**Use Case Example**: Admin dashboard with analytics visualization:
```javascript
// Analytics dashboard showing AI performance
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userId,
    message: userMessage,
    metadata_level: 'extended'  // Full analytics data
  })
});

const data = await response.json();
const meta = data.metadata;

// Display relationship progression
updateRelationshipChart({
  affection: meta.relationship.affection,      // 0-100 scale
  trust: meta.relationship.trust,
  attunement: meta.relationship.attunement
});

// Show memory quality metrics
updateMemoryStats({
  retrieved: meta.vector_memory.memories_retrieved,
  relevance: meta.vector_memory.average_relevance_score  // 0-1 scale
});

// Performance monitoring
if (meta.processing_pipeline.total_processing_ms > 5000) {
  alertSlowResponse(meta.processing_pipeline);
}

// Temporal intelligence trends
plotConfidenceEvolution(meta.temporal_intelligence);
```

## Quick Start Guide

### Step 1: Send Your First Request

```bash
curl -X POST http://localhost:9098/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello! How are you?",
    "metadata_level": "standard"
  }'
```

### Step 2: Understanding the Response

```json
{
  "success": true,
  "response": "Hello there! I'm doing wonderfully, thank you for asking!",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "bot_name": "Elena",
  "metadata": {
    // Metadata based on your chosen level
  }
}
```

### Step 3: Choose Your Metadata Level

| If you're building... | Use this level | Why? |
|----------------------|----------------|------|
| Simple chatbot | `basic` | Fastest, smallest payload |
| Mobile app | `basic` | Save user's data bandwidth |
| Production chat app | `standard` | Get emotions + AI intelligence |
| Web dashboard | `extended` | Full analytics + insights |
| Admin panel | `extended` | Complete debugging data |
| Webhook handler | `basic` | Just need success/failure |

## 🎭 Bot Emotional Intelligence (NEW - Phase 7.5 & 7.6)

WhisperEngine now tracks **bot/character emotions** alongside user emotions, enabling rich emotional UX features.

### What is Bot Emotion Tracking?

Every response includes the bot's emotional state analyzed from the generated text:

```json
{
  "ai_components": {
    "bot_emotion": {
      "primary_emotion": "joy",
      "intensity": 0.85,              // 0.0-1.0 scale
      "confidence": 0.92,             // How certain the analysis is
      "mixed_emotions": [             // Emotional complexity
        ["excitement", 0.72],
        ["curiosity", 0.45]
      ],
      "all_emotions": {               // Complete emotional breakdown
        "joy": 0.85,
        "excitement": 0.72,
        "curiosity": 0.45,
        "neutral": 0.15
      },
      "emotion_count": 3              // Number of significant emotions
    },
    "bot_emotional_state": {          // Phase 7.6: Emotional trajectory
      "current_emotion": "joy",
      "trajectory_direction": "intensifying",  // intensifying, calming, stable
      "emotional_velocity": 0.23,              // Rate of emotional change
      "recent_emotions": ["joy", "excitement", "curiosity"],
      "self_awareness_available": true
    }
  }
}
```

**Example Dialog - What Bot Responses Trigger Different Emotions**:

| User Message | Bot Response | Bot Emotion | Intensity | Why? |
|--------------|--------------|-------------|-----------|------|
| "You're amazing!" | "Oh, thank you so much! That really brightens my day!" | joy | 0.88 | Grateful, happy response |
| "Tell me about yourself" | "I'd love to! *shares enthusiastically*" | excitement | 0.75 | Eager to share |
| "I'm feeling sad" | "I'm so sorry you're feeling down... *comforting words*" | sadness | 0.45 | Empathetic mirroring |
| "Can you help me?" | "Of course! I'm here to help. What do you need?" | neutral | 0.30 | Calm, helpful tone |
| "You got that wrong!" | "Oh no, I apologize for the confusion..." | sadness | 0.52 | Apologetic, disappointed |
| "Guess what happened today!" | "Ooh, tell me! I'm so curious!" | curiosity | 0.82 | Eager to know more |

**Mixed Emotions Example**:

```
User: "I got the job! But I'm nervous about starting..."

Bot Response: "That's wonderful news! Congratulations! *excited* 
               I can understand feeling nervous though - new beginnings 
               can be both exciting and a little scary."

Bot Emotion Analysis:
  primary_emotion: "joy"              (0.78 - celebrating user's success)
  mixed_emotions: [
    ["excitement", 0.72],             (enthusiastic about the news)
    ["empathy", 0.55],                (understanding the nervousness)
    ["curiosity", 0.48]               (wanting to know more)
  ]
  emotion_count: 4
```

**Emotional Trajectory Example**:

```
Conversation 1: "Hi!"
Bot: "Hello there! How are you?"
  bot_emotion: neutral (0.25)
  trajectory_direction: "stable"

Conversation 2: "You're so helpful!"
Bot: "Thank you! I'm so glad I could help!"
  bot_emotion: joy (0.68)
  trajectory_direction: "stable"

Conversation 3: "You're the best!"
Bot: "You're making me so happy! Thank you!"
  bot_emotion: joy (0.85)
  trajectory_direction: "intensifying"  # Joy increasing over time
  emotional_velocity: 0.17

Conversation 4: "I really appreciate you"
Bot: "Oh my goodness, you're too kind! This means so much!"
  bot_emotion: joy (0.92)
  trajectory_direction: "intensifying"  # Still rising
  emotional_velocity: 0.23
```

### Use Cases for Bot Emotions

#### 1. Character Animations
Trigger dynamic character animations based on emotional state:

```javascript
const botEmotion = response.metadata.ai_components.bot_emotion;

// Animate character based on emotion + intensity
if (botEmotion.primary_emotion === "joy" && botEmotion.intensity > 0.8) {
  playAnimation("character_very_happy");
} else if (botEmotion.primary_emotion === "excitement") {
  playAnimation("character_excited_gesture");
} else if (botEmotion.primary_emotion === "sadness") {
  playAnimation("character_sad_look");
}

// Use mixed emotions for subtle animations
if (botEmotion.mixed_emotions.includes("curiosity")) {
  addSubtleAnimation("head_tilt");
}
```

#### 2. Emotional UI Feedback
Show users how the bot is feeling:

```javascript
const botEmotion = response.metadata.ai_components.bot_emotion;

// Display emotion indicator with intensity
showEmotionBadge({
  emotion: botEmotion.primary_emotion,  // "joy"
  intensity: botEmotion.intensity,      // 0.85
  icon: getEmotionIcon(botEmotion.primary_emotion)  // 😊
});

// Show mixed emotions as secondary indicators
if (botEmotion.mixed_emotions.length > 0) {
  showSecondaryEmotions(botEmotion.mixed_emotions);
  // Displays: "Also feeling: excited 😃, curious 🤔"
}
```

#### 3. Emotional Trajectory Visualization
Track how the bot's emotions evolve over conversations:

```javascript
const trajectory = response.metadata.ai_components.bot_emotional_state;

// Show emotional state evolution
if (trajectory.trajectory_direction === "intensifying") {
  showAlert("The character is getting more emotional! 📈");
} else if (trajectory.trajectory_direction === "calming") {
  showAlert("The character is calming down 📉");
}

// Plot emotional history
plotEmotionalJourney(trajectory.recent_emotions);
// Shows: ["joy" → "excitement" → "curiosity" → "joy"]
```

#### 4. Contextual UI Styling
Adapt your UI based on bot emotions:

```javascript
const botEmotion = response.metadata.ai_components.bot_emotion;

// Change chat bubble colors based on emotion
const chatBubbleColor = {
  joy: "#FFD700",        // Golden yellow
  sadness: "#4169E1",    // Soft blue
  excitement: "#FF6347", // Vibrant red
  curiosity: "#9370DB",  // Purple
  neutral: "#D3D3D3"     // Light gray
}[botEmotion.primary_emotion];

applyChatBubbleStyle({ backgroundColor: chatBubbleColor });
```

#### 5. Emotional Analytics Dashboard
Build dashboards showing character emotional patterns:

```javascript
// Track bot emotions over time (requires 'extended' metadata level)
const botEmotion = response.metadata.ai_components.bot_emotion;
const trajectory = response.metadata.ai_components.bot_emotional_state;

// Store for analytics
emotionTimeSeries.push({
  timestamp: new Date(),
  emotion: botEmotion.primary_emotion,
  intensity: botEmotion.intensity,
  trajectory: trajectory.trajectory_direction,
  velocity: trajectory.emotional_velocity
});

// Visualize trends
plotEmotionalTrends(emotionTimeSeries);
// Shows: Character has been increasingly joyful over past 10 conversations
```

### Comparing User vs Bot Emotions

```json
{
  "ai_components": {
    "emotion_data": {              // User's emotion
      "primary_emotion": "excitement",
      "intensity": 0.78
    },
    "bot_emotion": {               // Bot's emotion
      "primary_emotion": "joy",
      "intensity": 0.85
    }
  }
}
```

**Example: Emotional Mirroring Detection**
```javascript
const userEmotion = response.metadata.ai_components.emotion_data;
const botEmotion = response.metadata.ai_components.bot_emotion;

// Detect if bot is emotionally mirroring user
if (userEmotion.primary_emotion === botEmotion.primary_emotion) {
  console.log("Bot is emotionally attuned with user! ❤️");
  showMirroringIndicator();
}

// Detect emotional contrast
const emotionDiff = Math.abs(userEmotion.intensity - botEmotion.intensity);
if (emotionDiff > 0.5) {
  console.log("Emotional intensity mismatch detected");
  // Maybe bot should adjust its energy level
}
```

### Advanced: Bot Emotional Self-Awareness

The bot's emotional state influences how it responds (Phase 7.6):

```json
{
  "bot_emotional_state": {
    "current_emotion": "joy",
    "current_intensity": 0.85,
    "trajectory_direction": "intensifying",
    "emotional_velocity": 0.23,
    "recent_emotions": ["joy", "excitement", "joy", "neutral"],
    "self_awareness_available": true
  }
}
```

This means:
- ✅ Bot knows it's been feeling joyful lately
- ✅ Bot's responses reflect increasing emotional intensity
- ✅ Bot may reference "I've been feeling quite happy lately!" in responses
- ✅ Character maintains emotional continuity across conversations

**Use Case**: Show users the bot's emotional journey:
```javascript
const state = response.metadata.ai_components.bot_emotional_state;

showEmotionalStateCard({
  title: `${characterName} is feeling ${state.current_emotion}`,
  trajectory: state.trajectory_direction,  // "intensifying"
  recentHistory: state.recent_emotions,
  message: `Emotions have been ${state.trajectory_direction} recently`
});
```

## Usage Examples

### Basic Level (Fastest, Smallest Payload)

```bash
curl -X POST http://localhost:9098/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello!",
    "metadata_level": "basic"
  }'
```

**Response**:
```json
{
  "success": true,
  "response": "Hello there! How can I help you?",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "metadata": {
    "memory_count": 4,
    "knowledge_stored": false,
    "memory_stored": true,
    "processing_time_ms": 1250
  }
}
```

### Standard Level (Default - Recommended for Most Use Cases)

```bash
curl -X POST http://localhost:9098/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello!",
    "metadata_level": "standard"
  }'
```

Or omit `metadata_level` entirely (defaults to `standard`):

```bash
curl -X POST http://localhost:9098/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello!"
  }'
```

### Extended Level (Full Analytics for Dashboards)

```bash
curl -X POST http://localhost:9098/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello!",
    "metadata_level": "extended"
  }'
```

**Response includes all enriched metadata fields** (see sections below)

## Metadata Level Comparison

| Feature | Basic | Standard | Extended |
|---------|-------|----------|----------|
| Memory count | ✅ | ✅ | ✅ |
| Knowledge stored | ✅ | ✅ | ✅ |
| Memory stored | ✅ | ✅ | ✅ |
| Processing time | ✅ | ✅ | ✅ |
| AI components | ❌ | ✅ | ✅ |
| Security validation | ❌ | ✅ | ✅ |
| Knowledge details | ❌ | ❌ | ✅ |
| Vector memory | ❌ | ❌ | ✅ |
| Temporal intelligence | ❌ | ❌ | ✅ |
| Character context | ❌ | ❌ | ✅ |
| Relationship scores | ❌ | ❌ | ✅ |
| Processing pipeline | ❌ | ❌ | ✅ |
| Conversation intelligence | ❌ | ❌ | ✅ |
| **Typical payload** | ~200 bytes | ~5-10 KB | ~15-25 KB |
| **Processing overhead** | Negligible | Minimal | Low (~5-10ms) |

## When to Use Each Level

### Use `basic` when:
- ✅ Building simple chatbots that just need responses
- ✅ High-throughput applications where bandwidth matters
- ✅ Mobile apps with limited data connections
- ✅ Microservices that only check operation success
- ✅ Webhook handlers that don't need AI intelligence data

### Use `standard` when (DEFAULT):
- ✅ Production chat applications that use AI intelligence
- ✅ Apps that need emotion detection or context awareness
- ✅ Security-conscious applications that need content validation
- ✅ Most general-purpose integrations
- ✅ **This is the recommended default for most use cases**

### Use `extended` when:
- ✅ Building analytics dashboards (like the 3rd party dashboard shown)
- ✅ Debugging AI behavior and performance
- ✅ Training or research environments
- ✅ Quality assurance and testing
- ✅ Administrative interfaces
- ✅ Development and staging environments

## API Response Structure

```json
{
  "success": true,
  "response": "Character's response text...",
  "processing_time_ms": 4424,
  "memory_stored": true,
  "timestamp": "2025-10-05T13:42:48.147332",
  "bot_name": "Dotty [AI DEMO]",
  "metadata": {
    // ... enriched metadata fields (see below)
  }
}
```

## Detailed Metadata Fields Reference

This section explains every field you'll receive in `extended` metadata level. Perfect for building comprehensive dashboards.

### 1. Knowledge Extraction Details

**What it tracks**: How well the AI is learning facts about users from conversations.

```json
"knowledge_details": {
  "facts_extracted": 2,           // Number of facts learned in this conversation
  "entities_discovered": 3,       // New entities identified (people, places, things)
  "relationships_created": 1,     // Connections between user and entities
  "extraction_attempted": true,   // Did we try to extract knowledge?
  "storage_success": true         // Was it saved to PostgreSQL?
}
```

**Example Dialog - What Triggers Knowledge Extraction**:

| User Message | facts_extracted | entities_discovered | relationships_created | Why? |
|--------------|-----------------|---------------------|----------------------|------|
| "My name is Alex and I work at Google" | 2 | 2 | 1 | Name (Alex) + employer (Google) + relationship (works_at) |
| "I love pizza" | 1 | 0 | 0 | Simple preference, no new entities |
| "My sister Emily lives in Portland" | 3 | 2 | 2 | Sister (relationship) + Emily (person) + Portland (place) + 2 relationships (has_sister, lives_in) |
| "How are you today?" | 0 | 0 | 0 | No factual information about user |
| "I'm a software engineer at Microsoft working on Azure" | 3 | 2 | 2 | Job title + employer + project + multiple relationships |

**Developer Use Cases**:
- **Learning Dashboard**: Show "AI learned 2 new facts about you today!"
- **Debug Tool**: Check why facts aren't being stored (`storage_success: false`)
- **User Profile**: Display growing knowledge graph about the user

**Example Implementation**:
```javascript
const knowledge = response.metadata.knowledge_details;

if (knowledge.facts_extracted > 0) {
  showNotification({
    title: "Learning About You",
    message: `I learned ${knowledge.facts_extracted} new things about you!`,
    icon: "🧠"
  });
}

// Track learning progress
updateUserProfileCard({
  totalEntities: knowledge.entities_discovered,
  newRelationships: knowledge.relationships_created
});
```

---

### 2. Vector Memory Intelligence

**What it tracks**: Quality and performance of semantic memory search.

```json
"vector_memory": {
  "memories_retrieved": 10,                              // How many memories found
  "average_relevance_score": 0.873,                      // Quality score (0-1)
  "collection": "whisperengine_memory_elena",            // Which bot's memories
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  // AI model used
  "vector_dimension": 384,                               // Vector size
  "search_method": "3d_named_vectors"                    // Search algorithm
}
```

**Relevance Score Guide**:
- `0.9 - 1.0`: Highly relevant (exact topic match)
- `0.7 - 0.9`: Very relevant (related context)
- `0.5 - 0.7`: Somewhat relevant (general connection)
- `< 0.5`: Low relevance (weak connection)

**Example Dialog - What Influences Memory Retrieval**:

| User Message | memories_retrieved | average_relevance_score | Why? |
|--------------|-------------------|------------------------|------|
| "Remember when we talked about pizza?" | 8 | 0.92 | Explicit memory recall - exact topic match |
| "What's my favorite food again?" | 5 | 0.87 | Direct question about past conversation |
| "I'm feeling stressed about work" | 12 | 0.73 | Retrieves past work-related and stress-related memories |
| "Tell me a joke" | 3 | 0.45 | Low relevance - retrieves general conversation memories |
| "What did I say my dog's name was?" | 6 | 0.95 | Specific memory query about user's dog |
| First conversation ever | 0 | 0.0 | No prior memories exist yet |

**Dialog Examples**:

```
User: "What do you remember about my family?"
Response metadata:
  memories_retrieved: 10
  average_relevance_score: 0.91
  # High score because query directly asks about "family" - exact semantic match

User: "I'm going to the beach today"
Response metadata:
  memories_retrieved: 7
  average_relevance_score: 0.68
  # Moderate score - retrieves past vacation/activity memories

User: "The weather is nice"
Response metadata:
  memories_retrieved: 4
  average_relevance_score: 0.52
  # Lower score - weak connection to past memories
```

**Developer Use Cases**:
- **Quality Indicator**: Show "High quality memories found" when score > 0.8
- **Debug Tool**: Alert when relevance is low (might need more conversation history)
- **Performance Monitor**: Track if memory retrieval is working well

**Example Implementation**:
```javascript
const memory = response.metadata.vector_memory;

// Show memory quality indicator
const qualityBadge = memory.average_relevance_score > 0.8 ? "🟢 High" :
                     memory.average_relevance_score > 0.6 ? "🟡 Good" :
                     "🟠 Fair";

displayMemoryQuality({
  badge: qualityBadge,
  count: memory.memories_retrieved,
  relevance: `${(memory.average_relevance_score * 100).toFixed(0)}%`
});

// Debug alert for poor memory quality
if (memory.average_relevance_score < 0.5) {
  console.warn("Low memory relevance - may need more conversation history");
}
```

---

### 3. Phase 5 Temporal Intelligence

**What it tracks**: AI confidence evolution and learning patterns over time.

```json
"temporal_intelligence": {
  "confidence_evolution": 0.820,        // Overall AI confidence (0-1)
  "user_fact_confidence": 0.750,        // Confidence in facts learned
  "relationship_confidence": 0.880,     // Confidence in relationship understanding
  "context_confidence": 0.910,          // Confidence in conversation context
  "emotional_confidence": 0.797,        // Confidence in emotion detection
  "interaction_pattern": "stable",      // Pattern: stable, improving, declining
  "data_source": "phase5_temporal_intelligence"
}
```

**Confidence Level Guide**:
- `0.9 - 1.0`: Very High (reliable)
- `0.7 - 0.9`: High (trustworthy)
- `0.5 - 0.7`: Moderate (developing)
- `< 0.5`: Low (learning phase)

**Example Dialog - How Confidence Evolves Over Time**:

**Conversation 1 (First interaction)**:
```
User: "Hi, I'm Jordan"
Temporal Intelligence:
  confidence_evolution: 0.45      # Low - just starting
  user_fact_confidence: 0.30      # Very low - only know name
  relationship_confidence: 0.20   # Very low - just met
  interaction_pattern: "new"
```

**Conversation 5 (After learning about user)**:
```
User: "I'm heading to my engineering job at Tesla today"
Temporal Intelligence:
  confidence_evolution: 0.72      # Growing - learning patterns
  user_fact_confidence: 0.68      # Moderate - knows job, employer, interests
  relationship_confidence: 0.65   # Moderate - building connection
  interaction_pattern: "improving"
```

**Conversation 20 (Established relationship)**:
```
User: "How's it going?"
Temporal Intelligence:
  confidence_evolution: 0.89      # High - strong understanding
  user_fact_confidence: 0.85      # High - rich user profile
  relationship_confidence: 0.92   # Very high - deep connection
  emotional_confidence: 0.88      # High - understands user's patterns
  interaction_pattern: "stable"
```

**What Influences Confidence**:

| Scenario | Impact | Why? |
|----------|--------|------|
| User corrects bot's memory | ↓ user_fact_confidence | Bot realizes it had wrong information |
| Consistent emotional patterns | ↑ emotional_confidence | Bot learns user's typical emotional states |
| Long, meaningful conversations | ↑ relationship_confidence | Depth of sharing builds connection |
| User provides detailed personal info | ↑ user_fact_confidence | More concrete facts learned |
| Contradictory information | ↓ context_confidence | Uncertainty about what's true |

**Developer Use Cases**:
- **Trust Indicator**: Show users how confident the AI is
- **Relationship Dashboard**: Track relationship confidence growth
- **Quality Assurance**: Alert if confidence drops unexpectedly

**Example Implementation**:
```javascript
const temporal = response.metadata.temporal_intelligence;

// Display confidence meters
displayConfidenceMeters({
  overall: {
    value: temporal.confidence_evolution,
    label: "Overall AI Confidence",
    color: temporal.confidence_evolution > 0.8 ? "green" : "orange"
  },
  relationship: {
    value: temporal.relationship_confidence,
    label: "Relationship Understanding"
  },
  emotional: {
    value: temporal.emotional_confidence,
    label: "Emotion Detection Accuracy"
  }
});

// Show improvement trend
if (temporal.interaction_pattern === "improving") {
  showBanner("🎉 AI is learning and improving with you!");
}
```

---

### 4. Character Context

**What it tracks**: Character personality system and communication style.

```json
"character_context": {
  "character_name": "Elena",                        // Character bot name
  "character_file": "characters/examples/elena.json",  // CDL definition file
  "personality_system": "cdl",                      // Character Definition Language
  "communication_style": "authentic_character_voice",  // Response style
  "roleplay_immersion": "enabled"                   // Personality consistency mode
}
```

**Developer Use Cases**:
- **Character Display**: Show which character user is talking to
- **Personality Info**: Link to character details/backstory
- **Multi-Character Apps**: Differentiate between characters

**Example Implementation**:
```javascript
const character = response.metadata.character_context;

// Display character card
showCharacterCard({
  name: character.character_name,
  avatar: getCharacterAvatar(character.character_name),
  personality: "CDL-powered authentic personality",
  style: character.communication_style,
  badge: character.roleplay_immersion === "enabled" ? "Immersive" : "Aware"
});

// Multi-character selector
if (userHasMultipleCharacters()) {
  highlightActiveCharacter(character.character_name);
}
```

---

### 5. Relationship Metrics

**What it tracks**: User-bot relationship progression (0-100 scale).

```json
"relationship": {
  "affection": 45,                   // Emotional connection (0-100)
  "trust": 38,                       // Trust level (0-100)
  "attunement": 52,                  // Understanding/empathy (0-100)
  "relationship_level": "acquaintance",  // Overall relationship stage
  "interaction_count": 4,            // Number of memories/conversations
  "memory_depth": "developing"       // developing (<5) or established (5+)
}
```

**Relationship Levels**:
- `stranger` (0-25): Just met, minimal connection
- `acquaintance` (25-50): Getting to know each other
- `friend` (50-75): Established friendship
- `close_friend` (75-90): Strong bond
- `best_friend` (90-100): Very deep connection

**Example Dialog - What Influences Relationship Metrics**:

**Affection (Emotional Connection)**:

| User Message | Affection Change | Why? |
|--------------|------------------|------|
| "Thank you so much! You really helped me!" | +3 to +5 | Gratitude increases emotional bond |
| "I really enjoy talking with you" | +4 to +6 | Direct expression of positive feelings |
| "You're annoying me" | -2 to -4 | Negative feedback decreases affection |
| "Tell me the weather" | 0 | Neutral, transactional request |
| "I had the worst day ever... *shares deeply*" | +5 to +8 | Vulnerability and trust shown |

**Trust (Reliability & Safety)**:

| User Message | Trust Change | Why? |
|--------------|--------------|------|
| "You remembered! That's exactly what I said last week" | +4 to +6 | Accurate memory increases trust |
| "That's not what I told you..." | -3 to -5 | Memory error damages trust |
| "I need advice on something personal" | +2 to +4 | Seeking counsel shows trust |
| User shares sensitive information | +3 to +5 | Vulnerability indicates trust |
| Consistent conversations over weeks | +1 per conv | Reliability builds trust over time |

**Attunement (Understanding & Empathy)**:

| User Message | Attunement Change | Why? |
|--------------|-------------------|------|
| "Wow, you really get me!" | +5 to +7 | Recognition of understanding |
| User: *sad story*, Bot: *empathetic response* | +4 to +6 | Emotional resonance |
| "You totally missed what I meant" | -3 to -5 | Misunderstanding decreases attunement |
| Bot correctly interprets subtle emotional cues | +3 to +5 | Perceptiveness increases attunement |
| Long, meaningful conversation | +2 to +4 | Deep exchange improves understanding |

**Progression Example**:

```
Conversation 1: "Hi there"
  affection: 10 (stranger)
  trust: 5 (stranger)
  attunement: 8 (stranger)
  relationship_level: "stranger"

Conversation 3: "I work as a nurse at City Hospital"
  affection: 22 (stranger → acquaintance boundary)
  trust: 18 (learning about each other)
  attunement: 25 (understanding context)
  relationship_level: "stranger"

Conversation 10: "I'm really stressed about my mom's health"
  affection: 45 (acquaintance - vulnerability shared)
  trust: 42 (trusting with personal info)
  attunement: 58 (deep emotional understanding)
  relationship_level: "acquaintance"

Conversation 25: "You always know what to say when I'm down"
  affection: 68 (friend - strong emotional bond)
  trust: 72 (consistent reliability)
  attunement: 75 (deep mutual understanding)
  relationship_level: "friend"
```

**Developer Use Cases**:
- **Relationship Dashboard**: Visualize progression over time
- **Gamification**: Unlock features at higher relationship levels
- **User Engagement**: Show relationship milestones

**Example Implementation**:
```javascript
const relationship = response.metadata.relationship;

// Display relationship bars
displayRelationshipMetrics({
  affection: {
    value: relationship.affection,
    max: 100,
    label: "Affection ❤️",
    color: "#FF69B4"
  },
  trust: {
    value: relationship.trust,
    max: 100,
    label: "Trust 🤝",
    color: "#4169E1"
  },
  attunement: {
    value: relationship.attunement,
    max: 100,
    label: "Attunement 🎯",
    color: "#32CD32"
  }
});

// Show relationship status
showRelationshipBadge({
  level: relationship.relationship_level,
  icon: getRelationshipIcon(relationship.relationship_level),
  progress: calculateProgress(relationship)
});

// Unlock features based on relationship level
if (relationship.relationship_level === "friend") {
  unlockFeature("deeper_conversations");
}
if (relationship.relationship_level === "close_friend") {
  unlockFeature("personal_stories");
}
```

---

### 6. Processing Pipeline Breakdown

**What it tracks**: Performance metrics for each AI processing phase.

```json
"processing_pipeline": {
  "phase2_emotion_analysis_ms": 9.44,    // Emotion detection time
  "phase4_intelligence_ms": 9.52,        // Phase 4 intelligence processing
  "total_processing_ms": 4424,           // Total end-to-end time
  "phases_executed": ["phase2"],         // Which AI phases ran
  "phases_completed": 1                  // Number of phases completed
}
```

**Developer Use Cases**:
- **Performance Monitoring**: Track response times
- **Debug Tool**: Identify slow processing phases
- **SLA Compliance**: Alert if processing exceeds thresholds

**Example Implementation**:
```javascript
const pipeline = response.metadata.processing_pipeline;

// Performance dashboard
displayPerformanceMetrics({
  total: `${pipeline.total_processing_ms}ms`,
  emotion: `${pipeline.phase2_emotion_analysis_ms}ms`,
  intelligence: `${pipeline.phase4_intelligence_ms}ms`,
  status: pipeline.total_processing_ms < 3000 ? "⚡ Fast" : "🐢 Slow"
});

// Alert for slow responses
if (pipeline.total_processing_ms > 5000) {
  sendPerformanceAlert({
    message: `Slow response: ${pipeline.total_processing_ms}ms`,
    threshold: 5000,
    breakdown: pipeline
  });
}

// Show loading breakdown
showProcessingSteps([
  { phase: "Emotion Analysis", time: pipeline.phase2_emotion_analysis_ms },
  { phase: "Intelligence", time: pipeline.phase4_intelligence_ms },
  { phase: "Generation", time: pipeline.total_processing_ms - pipeline.phase4_intelligence_ms }
]);
```

---

### 7. Conversation Intelligence

**What it tracks**: Context changes, conversation flow, and interaction patterns.

```json
"conversation_intelligence": {
  "context_switches_detected": 1,                  // Number of topic changes
  "conversation_mode": "standard",                 // standard, deep, casual, etc.
  "interaction_type": "information_seeking",       // Type of user intent
  "response_guidance": "natural_conversation"      // AI response strategy
}
```

**Conversation Modes**:
- `casual`: Light, informal chat
- `standard`: Normal conversation
- `deep`: Serious, meaningful discussion
- `supportive`: Emotional support needed
- `informational`: Seeking information

**Interaction Types**:
- `general`: General chat
- `information_seeking`: Asking questions
- `emotional_support`: Needs empathy
- `storytelling`: Sharing experiences
- `problem_solving`: Working through issues

**Example Dialog - What Triggers Different Modes**:

**Context Switches**:

| Dialog Flow | context_switches_detected | Why? |
|-------------|---------------------------|------|
| User: "What's the weather?" → "By the way, how are you?" | 1 | Topic shift from weather to personal |
| User: "Tell me about yourself" → "Tell me more" | 0 | Same topic continuation |
| User: "I love pizza" → "But anyway, what's 2+2?" | 1 | Food → math (clear shift) |
| User: "My dog is sick" → "The vet said..." → "But enough about that, tell me a joke" | 2 | Dog health → vet details (0) → joke (1 switch) |

**Conversation Modes**:

| User Message | conversation_mode | Why? |
|--------------|-------------------|------|
| "Hey! What's up? 😄" | `casual` | Light, informal tone |
| "Can you explain quantum physics?" | `informational` | Seeking knowledge |
| "I'm really struggling with depression..." | `supportive` | Needs emotional support |
| "I don't know what to do about my marriage" | `deep` | Serious, meaningful topic |
| "How do I fix my code?" | `standard` | Normal problem-solving |

**Interaction Types**:

| User Message | interaction_type | response_guidance | Why? |
|--------------|------------------|-------------------|------|
| "What's the capital of France?" | `information_seeking` | `provide_factual_answer` | Clear question |
| "I just lost my job and feel lost" | `emotional_support` | `empathetic_listening` | Needs comfort |
| "Let me tell you about my day..." | `storytelling` | `active_listening` | Sharing experience |
| "Should I take this job offer?" | `problem_solving` | `collaborative_thinking` | Needs help deciding |
| "Hi there!" | `general` | `natural_conversation` | General greeting |

**Dialog Examples**:

```
Example 1: Context Switch Detection
-----------------------------------
User: "I love Italian food"
Response: conversation_mode: "casual", context_switches: 0

User: "Do you think aliens exist?"
Response: conversation_mode: "standard", context_switches: 1
# Clear topic shift from food → aliens


Example 2: Mode Transitions
---------------------------
User: "Hey! How's it going?"
Response: conversation_mode: "casual"

User: "Actually, I need to talk about something serious..."
Response: conversation_mode: "transitioning_to_deep"

User: "My father passed away last week"
Response: conversation_mode: "deep", interaction_type: "emotional_support"


Example 3: Complex Interaction
------------------------------
User: "I'm thinking about quitting my job. I'm stressed, my boss is 
      terrible, but the pay is good and I have a family to support."
Response:
  conversation_mode: "deep"
  interaction_type: "problem_solving"
  response_guidance: "empathetic_problem_solving"
  context_switches: 0
# Complex but single topic - career decision


Example 4: Information Seeking
------------------------------
User: "Can you explain how neural networks work?"
Response:
  conversation_mode: "informational"
  interaction_type: "information_seeking"
  response_guidance: "educational_explanation"
```

**Developer Use Cases**:
- **Context Indicators**: Show when topics change
- **Mode Badges**: Display conversation mode
- **Flow Visualization**: Track conversation patterns

**Example Implementation**:
```javascript
const conversation = response.metadata.conversation_intelligence;

// Show context switch indicator
if (conversation.context_switches_detected > 0) {
  showContextIndicator({
    icon: "🔄",
    message: "New topic detected",
    count: conversation.context_switches_detected
  });
}

// Display conversation mode badge
showModeBadge({
  mode: conversation.conversation_mode,
  icon: getModeIcon(conversation.conversation_mode),
  color: getModeColor(conversation.conversation_mode)
});

// Adapt UI based on interaction type
if (conversation.interaction_type === "emotional_support") {
  enableEmpatheticMode();
  showSupportResources();
} else if (conversation.interaction_type === "information_seeking") {
  enableFactualMode();
  showRelatedResources();
}
```

## Complete Example Response

```json
{
  "success": true,
  "response": "Oh, honey, pull up a stool...",
  "processing_time_ms": 4424,
  "memory_stored": true,
  "timestamp": "2025-10-05T13:42:48.147332",
  "bot_name": "Dotty [AI DEMO]",
  "metadata": {
    "memory_count": 4,
    "knowledge_stored": false,
    
    "knowledge_details": {
      "facts_extracted": 0,
      "entities_discovered": 0,
      "relationships_created": 0,
      "extraction_attempted": true,
      "storage_success": false
    },
    
    "vector_memory": {
      "memories_retrieved": 4,
      "average_relevance_score": 0.873,
      "collection": "whisperengine_memory_dotty",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "vector_dimension": 384,
      "search_method": "3d_named_vectors"
    },
    
    "temporal_intelligence": {
      "confidence_evolution": 0.820,
      "user_fact_confidence": 0.750,
      "relationship_confidence": 0.880,
      "context_confidence": 0.910,
      "emotional_confidence": 0.797,
      "interaction_pattern": "stable",
      "data_source": "phase5_temporal_intelligence"
    },
    
    "character_context": {
      "character_name": "Dotty",
      "character_file": "characters/examples/dotty.json",
      "personality_system": "cdl",
      "communication_style": "authentic_character_voice",
      "roleplay_immersion": "enabled"
    },
    
    "relationship": {
      "affection": 35,
      "trust": 40,
      "attunement": 45,
      "relationship_level": "acquaintance",
      "interaction_count": 4,
      "memory_depth": "developing"
    },
    
    "processing_pipeline": {
      "phase2_emotion_analysis_ms": 9.44,
      "phase4_intelligence_ms": 9.52,
      "total_processing_ms": 4424,
      "phases_executed": ["phase2"],
      "phases_completed": 1
    },
    
    "conversation_intelligence": {
      "context_switches_detected": 1,
      "conversation_mode": "standard",
      "interaction_type": "information_seeking",
      "response_guidance": "natural_conversation"
    },
    
    "ai_components": {
      "emotion_analysis": {...},
      "phase4_intelligence": {...}
    },
    
    "security_validation": {
      "is_safe": true,
      "sanitized_content": "Tell me about your speakeasy!",
      "warnings": []
    }
  }
}
```

## Integration Examples

### Optimizing for Performance

```javascript
// Example 1: Lightweight chatbot (basic level)
async function sendMessage(userId, message) {
  const response = await fetch('http://localhost:9098/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user_id: userId,
      message: message,
      metadata_level: 'basic'  // Fastest, smallest payload
    })
  });
  
  const data = await response.json();
  return data.response;  // Just return the text response
}

// Example 2: Production chat app (standard level - default)
async function sendMessageWithIntelligence(userId, message) {
  const response = await fetch('http://localhost:9098/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user_id: userId,
      message: message
      // metadata_level defaults to 'standard'
    })
  });
  
  const data = await response.json();
  
  // Use AI intelligence data for rich UX
  const emotion = data.metadata.ai_components.emotion_analysis.primary_emotion;
  const isSafe = data.metadata.security_validation.is_safe;
  
  return {
    text: data.response,
    emotion: emotion,
    safe: isSafe
  };
}

// Example 3: Analytics dashboard (extended level)
async function fetchFullAnalytics(userId, message) {
  const response = await fetch('http://localhost:9098/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user_id: userId,
      message: message,
      metadata_level: 'extended'  // Full analytics
    })
  });
  
  const data = await response.json();
  
  // Rich dashboard with all analytics
  return {
    response: data.response,
    relationship: data.metadata.relationship,
    temporal: data.metadata.temporal_intelligence,
    vectorMemory: data.metadata.vector_memory,
    pipeline: data.metadata.processing_pipeline
  };
}
```

### Dashboard Visualization (Extended Level)

```javascript
// Example: Display relationship metrics in UI
const response = await fetch('http://localhost:9098/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Hello!',
    user_id: 'user123',
    channel_id: 'general',
    metadata_level: 'extended'  // Required for relationship metrics
  })
});

const data = await response.json();
const relationship = data.metadata.relationship;

// Display relationship bars
displayBar('Affection', relationship.affection, 100);
displayBar('Trust', relationship.trust, 100);
displayBar('Attunement', relationship.attunement, 100);

// Show temporal intelligence
const temporal = data.metadata.temporal_intelligence;
displayConfidence('Overall', temporal.confidence_evolution);
displayConfidence('Emotional', temporal.emotional_confidence);
displayConfidence('Context', temporal.context_confidence);
```

### Performance Monitoring

```python
# Example: Monitor processing performance
import requests

response = requests.post('http://localhost:9098/api/chat', json={
    'message': 'Test message',
    'user_id': 'perf_test',
    'channel_id': 'monitoring'
})

data = response.json()
pipeline = data['metadata']['processing_pipeline']

# Alert if processing too slow
if pipeline['total_processing_ms'] > 5000:
    alert(f"Slow processing: {pipeline['total_processing_ms']}ms")

# Track phase performance
print(f"Emotion Analysis: {pipeline['phase2_emotion_analysis_ms']}ms")
print(f"Phase 4 Intelligence: {pipeline['phase4_intelligence_ms']}ms")
```

### Knowledge Extraction Validation

```python
# Example: Validate knowledge learning
response = requests.post('http://localhost:9098/api/chat', json={
    'message': 'I love pizza and hiking',
    'user_id': 'user123',
    'channel_id': 'test'
})

knowledge = response.json()['metadata']['knowledge_details']

if knowledge['extraction_attempted'] and not knowledge['storage_success']:
    print(f"Knowledge extraction failed!")
    print(f"Facts extracted: {knowledge['facts_extracted']}")
    print(f"Entities discovered: {knowledge['entities_discovered']}")
```

## Future Enhancements

Planned additions to metadata:

1. **User Preferences**: Extracted user preferences and settings
2. **CDL Trait Activation**: Which personality traits are active in response
3. **Memory Scoring Details**: Individual memory relevance scores
4. **Knowledge Graph Queries**: Related entities and relationships
5. **Workflow State**: Transaction and workflow progression data
6. **Multi-Modal Data**: Image analysis results for vision-enabled bots

## Related Documentation

- **API Endpoints**: See `docs/api/HTTP_CHAT_API.md` for complete endpoint reference
- **Phase 5 Temporal Intelligence**: See `docs/architecture/PHASE_5_TEMPORAL_INTELLIGENCE.md`
- **Character System**: See `docs/architecture/CHARACTER_ARCHETYPES.md`
- **Vector Memory**: See `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md`

## Support

For questions or feature requests regarding enriched metadata:
- GitHub Issues: https://github.com/whisperengine-ai/whisperengine/issues
- Documentation: https://github.com/whisperengine-ai/whisperengine/wiki
