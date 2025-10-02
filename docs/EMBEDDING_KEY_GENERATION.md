# WhisperEngine 6-Dimensional Embedding Key Generation

## 🔤 How Embedding Tags/Keys Are Determined

### 1. **CONTENT Dimension**
- **Tag**: `{raw_content}` (no prefix)
- **Logic**: Direct embedding of the original message content
- **Example**: `"I love hiking in the mountains"`

### 2. **EMOTION Dimension** 
- **Tag**: `"emotion {emotion_context}: {content}"`
- **Logic**: Uses **RoBERTa → VADER → Keyword Analysis** cascade
- **Sources**:
  - **RoBERTa**: `j-hartmann/emotion-english-distilroberta-base` model results
  - **VADER**: Sentiment analysis mapped to emotions
  - **Keywords**: Pattern matching with emotion dictionaries
- **Examples**: 
  - `"emotion joy: I got promoted today!"`
  - `"emotion sadness: I feel disappointed about the cancellation"`

### 3. **SEMANTIC Dimension**
- **Tag**: `"concept {semantic_key}: {content}"`
- **Logic**: Uses `_get_semantic_key()` for concept clustering
- **Key Generation**:
  - Pet names: `pet_name`
  - Color preferences: `favorite_color` 
  - User identity: `user_name`, `user_location`
  - Generic: First 3 words joined with underscores
- **Examples**:
  - `"concept pet_name: My cat's name is Whiskers"`
  - `"concept favorite_color: I really like blue"`

### 4. **RELATIONSHIP Dimension**
- **Tag**: `"relationship {relationship_context}: {content}"`
- **Logic**: Uses `_extract_relationship_context()` for intimacy + trust levels
- **Key Generation**: `"intimacy_{level}_trust_{level}"`
- **Intimacy Levels**: casual, personal, deep, intimate
- **Trust Levels**: skeptical, neutral, trusting, confidential
- **Examples**:
  - `"relationship intimacy_personal_trust_trusting: I had a great time with my friend"`
  - `"relationship intimacy_deep_trust_confidential: This is private between us"`

### 5. **CONTEXT Dimension**
- **Tag**: `"context {context_situation}: {content}"`
- **Logic**: Uses `_extract_context_situation()` for situational awareness
- **Key Generation**: `"mode_{conversation_mode}_time_{time_context}"`
- **Conversation Modes**: crisis_support, educational, emotional_support, playful, serious, casual_chat
- **Time Contexts**: morning, evening, weekend, holiday, general
- **Examples**:
  - `"context mode_educational_time_general: Can you explain how this works?"`
  - `"context mode_emotional_support_time_evening: I'm feeling anxious about tomorrow"`

### 6. **PERSONALITY Dimension**
- **Tag**: `"personality {personality_prominence}: {content}"`
- **Logic**: Uses `_extract_personality_prominence()` for character trait analysis
- **Key Generation**: `"traits_{trait1}_{trait2}"` (top 2 traits)
- **Trait Detection**: empathy, analytical, creative, adventurous, scientific, philosophical, humorous, protective, curious
- **Examples**:
  - `"personality traits_scientific_curious: I want to research marine ecosystems"`
  - `"personality traits_empathy_protective: I care about your wellbeing"`

## 🎯 Tag Generation Summary

| Dimension | Tag Format | Data Source | Example Key |
|-----------|------------|-------------|-------------|
| content | `{content}` | Raw message | Direct content |
| emotion | `emotion {context}:` | RoBERTa/VADER/Keywords | `joy`, `sadness`, `anger` |
| semantic | `concept {key}:` | Pattern matching | `pet_name`, `favorite_color` |
| relationship | `relationship {context}:` | Intimacy + Trust analysis | `intimacy_deep_trust_confidential` |
| context | `context {situation}:` | Mode + Time analysis | `mode_educational_time_general` |
| personality | `personality {traits}:` | Character trait detection | `traits_scientific_curious` |

## 🧠 Intelligence Behind Each Dimension

- **Emotion**: Sophisticated ML analysis (RoBERTa) with graceful fallbacks
- **Semantic**: Concept clustering for contradiction detection
- **Relationship**: Bond development and intimacy tracking
- **Context**: Situational and environmental awareness
- **Personality**: Character trait prominence for authenticity
- **Content**: Pure semantic similarity baseline

This multi-dimensional approach enables WhisperEngine to understand conversations from 6 different perspectives simultaneously! 🚀