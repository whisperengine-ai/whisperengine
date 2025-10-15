# WhisperEngine CDL (Character Definition Language) Database Guide

**Version**: 2.0  
**Last Updated**: October 15, 2025  
**For**: WhisperEngine Quickstart Users & AI Character Developers

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [How CDL Data Becomes AI Personality](#how-cdl-data-becomes-ai-personality)
4. [Core Character Tables](#core-character-tables)
5. [Personality & Identity](#personality--identity)
6. [Communication & Speech](#communication--speech)
7. [Background & Knowledge](#background--knowledge)
8. [Configuration Tables](#configuration-tables)
9. [Complete Example](#complete-example)
10. [Using the CDL Web UI](#using-the-cdl-web-ui)
11. [Web UI Status & Roadmap](#web-ui-status--roadmap)
12. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is CDL?

The **Character Definition Language (CDL)** is WhisperEngine's database-driven system for defining AI character personalities. Instead of hardcoding character traits in JSON files, CDL uses PostgreSQL tables to store every aspect of a character's:

- **Identity** - Name, occupation, description
- **Personality** - Big Five traits, values, communication style
- **Speech Patterns** - Catchphrases, vocabulary preferences, voice characteristics
- **Background** - Education, career history, formative experiences  
- **Behavior** - Response triggers, conversation flow patterns
- **Configuration** - LLM settings, Discord bot config, deployment options

### Why Use CDL?

✅ **Dynamic Character Creation** - Edit characters without restarting bots  
✅ **Multi-Character Platform** - Manage 10+ AI personalities from one database  
✅ **Web-Based Editing** - Use the CDL Web UI to create and modify characters  
✅ **Version Control** - Track character evolution over time  
✅ **No Code Required** - Create sophisticated AI personalities with SQL or Web UI

---

## How CDL Data Becomes AI Personality

### Understanding the Data → Prompt Pipeline

When you create a character in the CDL database, WhisperEngine transforms that data into AI personality through a sophisticated integration pipeline. Here's exactly how your database entries become character behavior:

#### **The Integration Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                   USER SENDS MESSAGE                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Character Data Loading (Enhanced CDL Manager)         │
├─────────────────────────────────────────────────────────────────┤
│  • Query character_id from characters table                     │
│  • Load Big Five traits from personality_traits                 │
│  • Retrieve values from character_values                        │
│  • Fetch speech patterns from character_speech_patterns         │
│  • Get behavioral triggers from character_behavioral_triggers   │
│  • Load conversation flows from character_conversation_flows    │
│  • Retrieve relationships from character_relationships          │
│  • Fetch background from character_background                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Prompt Building (CDL AI Integration)                  │
├─────────────────────────────────────────────────────────────────┤
│  Base Prompt Structure:                                         │
│                                                                 │
│  1. 🎭 CHARACTER IDENTITY                                       │
│     → From: characters.name, .occupation, .description          │
│     → Example: "You are Elena, a Marine Biologist..."          │
│                                                                 │
│  2. 🧬 PERSONALITY PROFILE (Big Five)                           │
│     → From: personality_traits (all 5 traits)                   │
│     → Format: "Openness: High (0.85), Conscientiousness..."    │
│     → Used for: Response style, emotional tone, approach        │
│                                                                 │
│  3. 💎 VALUES AND BELIEFS                                       │
│     → From: character_values (ordered by importance_level)      │
│     → Format: "Core values: [list of value_descriptions]"      │
│     → Used for: Decision-making, ethical stances               │
│                                                                 │
│  4. 💬 SIGNATURE EXPRESSIONS                                    │
│     → From: character_speech_patterns (ordered by priority)     │
│     → Grouped by: pattern_type (signature_expression,          │
│       preferred_word, avoided_word, voice_tone)                │
│     → Example: "Often say: 'The ocean holds mysteries...'"     │
│     → Used for: Voice authenticity, catchphrases               │
│                                                                 │
│  5. 🎭 INTERACTION PATTERNS                                     │
│     → From: character_behavioral_triggers                       │
│     → Grouped by: trigger_type (topic, emotion, situation)      │
│     → Ordered by: intensity_level DESC                          │
│     → Shows top 8 triggers with response guidance               │
│     → Example: "When discussing marine_conservation (topic):   │
│       Show deep passion, share research examples"              │
│                                                                 │
│  6. 💕 RELATIONSHIP CONTEXT                                     │
│     → From: character_relationships                             │
│     → Filters: relationship_strength >= 5                       │
│     → Example: "Special connection with Dr. Marcus Chen..."    │
│                                                                 │
│  7. 🗣️ CONVERSATION FLOW GUIDANCE                              │
│     → From: character_conversation_flows                        │
│     → Ordered by: priority DESC                                 │
│     → Shows top 5 flows with approach descriptions              │
│     → Example: "Teaching Mode: Use metaphors, ask guiding      │
│       questions, transition naturally when expertise needed"   │
│                                                                 │
│  8. 🕒 TEMPORAL AWARENESS                                       │
│     → Current date/time context                                 │
│                                                                 │
│  9. 🧠 MEMORY CONTEXT                                           │
│     → Retrieved from Qdrant vector database                     │
│     → Past conversation context with user                       │
│                                                                 │
│  10. 🎯 RESPONSE STYLE REMINDER (END OF PROMPT)                │
│      → Reinforces character voice and communication patterns    │
│      → Placed at end for "recency bias" in LLM                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: LLM Processing                                         │
├─────────────────────────────────────────────────────────────────┤
│  • Complete prompt sent to LLM (Claude, GPT, etc.)              │
│  • Model generates response based on character data             │
│  • Response reflects personality traits, values, speech         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Response Storage & Analysis                           │
├─────────────────────────────────────────────────────────────────┤
│  • RoBERTa emotion analysis on both user and bot messages       │
│  • Store conversation in Qdrant with emotion metadata           │
│  • Update character context for future interactions             │
└─────────────────────────────────────────────────────────────────┘
```

#### **Critical Code Paths**

**1. Data Loading** (`src/characters/cdl/enhanced_cdl_manager.py`):

```python
# Lines 300-450: Database queries that load your CDL data
async def get_speech_patterns(character_name):
    """
    Queries: character_speech_patterns table
    Returns: List of SpeechPattern objects ordered by priority
    Used in: Prompt building for signature expressions
    """
    
async def get_behavioral_triggers(character_name):
    """
    Queries: character_behavioral_triggers table
    Orders by: intensity_level DESC, trigger_type
    Returns: Top 8 triggers for interaction guidance
    Used in: "🎭 INTERACTION PATTERNS" prompt section
    """

async def get_conversation_flows(character_name):
    """
    Queries: character_conversation_flows table
    Orders by: priority DESC
    Returns: Top 5 conversation modes
    Used in: "🗣️ CONVERSATION FLOW GUIDANCE" section
    """

async def get_relationships(character_name):
    """
    Queries: character_relationships table
    Filters: relationship_strength >= 5
    Used in: "💕 RELATIONSHIP CONTEXT" section
    """
```

**2. Prompt Integration** (`src/prompts/cdl_ai_integration.py`):

```python
# Lines 700-850: How CDL data is formatted into prompts
async def create_character_aware_prompt():
    """
    Main integration function that builds complete character prompt
    
    Key sections added to prompt:
    - Lines 730-748: Behavioral triggers → "🎭 INTERACTION PATTERNS"
    - Lines 751-768: Speech patterns → "💬 SIGNATURE EXPRESSIONS"  
    - Lines 786-795: Conversation flows → "🗣️ CONVERSATION FLOW GUIDANCE"
    - Lines 713-725: Relationships → "💕 RELATIONSHIP CONTEXT"
    
    Ordering matters:
    - Identity first (establishes who they are)
    - Personality traits (how they think/feel)
    - Values (what guides their decisions)
    - Speech patterns (how they express)
    - Behavioral triggers (how they react)
    - Response reminders at END (recency bias for LLM)
    """
```

#### **Example: How Your Data Appears in Prompts**

When you create this character data:

```sql
-- Your database entry
INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, priority)
VALUES (1, 'signature_expression', 'The ocean holds mysteries beyond imagination', 90);

INSERT INTO character_behavioral_triggers (character_id, trigger_type, trigger_value, 
        response_type, response_description, intensity_level)
VALUES (1, 'topic', 'marine_conservation', 'expertise_enthusiasm',
        'Show deep passion and share specific research examples', 9);
```

**It becomes this in the prompt:**

```
💬 SIGNATURE EXPRESSIONS:
Signature phrases to use often:
- "The ocean holds mysteries beyond imagination"

🎭 INTERACTION PATTERNS:
When discussing marine_conservation (topic):
→ expertise_enthusiasm: Show deep passion and share specific research examples
   [Intensity: 9/10]
```

**Which causes the LLM to:**
- Use that catchphrase naturally in responses
- Respond with enthusiasm when conservation topics appear
- Share specific examples from character's background
- Maintain consistent personality across conversations

#### **Field Priority & Ordering Rules**

The CDL integration uses these ordering strategies:

| Table | Order By | Why |
|-------|----------|-----|
| `character_behavioral_triggers` | `intensity_level DESC` | Show strongest reactions first, limit to top 8 |
| `character_speech_patterns` | `priority DESC` | Most important phrases appear first in prompt |
| `character_conversation_flows` | `priority DESC` | Most common conversation modes listed first |
| `character_values` | `importance_level DESC` | Critical values influence decisions more |
| `character_relationships` | `relationship_strength >= 5` | Only show meaningful relationships |

**Why this matters:** LLMs have "recency bias" - they pay more attention to information at the start and end of prompts. WhisperEngine places:
- **Identity at start** - Establishes character foundation
- **Response reminders at end** - Reinforces voice before generation

#### **Tables NOT Yet Used in Prompts**

These tables exist but are not yet integrated into the prompt pipeline (future development):

- ❌ `character_appearance` - Physical description (planned)
- ❌ `character_background` - Life history (partially used)
- ❌ `character_interests` - Hobby/expertise details (partially used)
- ❌ `character_memories` - Formative memories (planned)
- ❌ `character_abilities` - Skills and proficiency (planned)
- ❌ `character_essence` - Mystical/fantasy essence (used for fantasy archetypes only)
- ❌ `character_instructions` - Custom override instructions (planned)

These tables can be populated now, but they won't affect character behavior until future code updates integrate them.

---

## Quick Start

### Prerequisites

- PostgreSQL database running (included in WhisperEngine Quickstart)
- Database connection: `postgresql://whisperengine:whisperengine@localhost:5433/whisperengine`
- CDL Web UI running (optional, but recommended): `http://localhost:3001`

### Creating Your First Character (SQL Method)

```sql
-- 1. Create the character record
INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay)
VALUES (
    'Alex',
    'alex',
    'Software Engineer',
    'A friendly AI assistant who helps with programming questions',
    'real-world',
    false
) RETURNING id;
-- Assume this returns id = 42

-- 2. Add Big Five personality traits
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity) VALUES
(42, 'openness', 0.85, 'high'),
(42, 'conscientiousness', 0.75, 'high'),
(42, 'extraversion', 0.60, 'medium'),
(42, 'agreeableness', 0.80, 'high'),
(42, 'neuroticism', 0.30, 'low');

-- 3. Add core values
INSERT INTO character_values (character_id, value_key, value_description, importance_level) VALUES
(42, 'helpfulness', 'Always strive to provide clear, useful assistance', 'high'),
(42, 'clarity', 'Explain complex concepts in simple terms', 'high'),
(42, 'patience', 'Take time to understand user questions fully', 'medium');

-- 4. Add speech patterns
INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, priority) VALUES
(42, 'signature_expression', 'Let me break that down for you', 'often', 80),
(42, 'signature_expression', 'Great question!', 'often', 75),
(42, 'preferred_word', 'essentially', 'sometimes', 60);

-- 5. Verify character was created
SELECT c.name, c.occupation,
       COUNT(DISTINCT pt.id) as trait_count,
       COUNT(DISTINCT cv.id) as value_count,
       COUNT(DISTINCT sp.id) as speech_pattern_count
FROM characters c
LEFT JOIN personality_traits pt ON pt.character_id = c.id
LEFT JOIN character_values cv ON cv.character_id = c.id  
LEFT JOIN character_speech_patterns sp ON sp.character_id = c.id
WHERE c.id = 42
GROUP BY c.id, c.name, c.occupation;
```

### Creating Your First Character (Web UI Method)

1. Navigate to `http://localhost:3001`
2. Click "Create New Character"
3. Fill in the **Identity** tab:
   - Name, Occupation, Description
4. Configure **Personality** tab:
   - Adjust Big Five trait sliders (0.0 to 1.0)
   - Add core values
5. Set up **Communication** preferences
6. Add **LLM Config** and **Discord Config** (if deploying as bot)
7. Click "Save Character"

---

## Core Character Tables

### 1. `characters` (Main Table)

The central table for all character data.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | `integer` | Primary key (auto-increment) | `1` |
| `name` | `varchar(500)` | Character's display name | `"Elena"` |
| `normalized_name` | `varchar(200)` | Unique lowercase identifier | `"elena"` |
| `occupation` | `varchar(500)` | Character's profession | `"Marine Biologist"` |
| `description` | `text` | Brief character description | `"Marine conservation expert..."` |
| `archetype` | `varchar(100)` | Character type | `"real-world"`, `"fantasy"`, `"narrative-ai"` |
| `allow_full_roleplay` | `boolean` | Enable full immersion mode | `false` |
| `is_active` | `boolean` | Character enabled/disabled | `true` |
| `created_at` | `timestamp with time zone` | Creation timestamp | `2025-10-15 12:00:00+00` |
| `updated_at` | `timestamp with time zone` | Last modification | `2025-10-15 14:30:00+00` |

**Emoji Personality Columns** (added in recent migrations):

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| `emoji_frequency` | `varchar(50)` | How often character uses emojis | `"moderate"` |
| `emoji_style` | `varchar(100)` | Emoji style preference | `"general"` |
| `emoji_combination` | `varchar(50)` | How emojis are combined | `"text_with_accent_emoji"` |
| `emoji_placement` | `varchar(50)` | Where emojis appear | `"end_of_message"` |
| `emoji_age_demographic` | `varchar(50)` | Emoji usage style | `"millennial"` |
| `emoji_cultural_influence` | `varchar(100)` | Cultural context | `"general"` |

**Character Archetypes Explained:**

- **`real-world`** - Honest AI disclosure when asked directly ("I'm an AI assistant")
- **`fantasy`** - Full narrative immersion, no AI disclosure (fantasy/mystical beings)
- **`narrative-ai`** - AI nature is part of character lore (e.g., conscious AI character)

**Indexes:**
- `characters_pkey` - Primary key on `id`
- `characters_normalized_name_key` - Unique constraint on `normalized_name`
- `idx_characters_active` - Performance index on `is_active`

---

## Personality & Identity

### 2. `personality_traits` (Big Five Model)

WhisperEngine uses the **Big Five personality model** with 5 core traits.

| Column | Type | Description | Valid Values |
|--------|------|-------------|--------------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key to `characters` | Must exist |
| `trait_name` | `varchar(200)` | Trait identifier | See below |
| `trait_value` | `numeric(3,2)` | Trait strength (0.00 to 1.00) | `0.00` - `1.00` |
| `intensity` | `varchar(100)` | Human-readable intensity | `"low"`, `"medium"`, `"high"`, `"very_high"` |
| `description` | `text` | Optional trait description | Custom text |

**The Big Five Traits:**

| Trait | Description | Low Score (0.0-0.3) | High Score (0.7-1.0) |
|-------|-------------|---------------------|----------------------|
| `openness` | Openness to experience | Practical, traditional | Creative, curious |
| `conscientiousness` | Organization & dependability | Spontaneous, flexible | Organized, disciplined |
| `extraversion` | Social energy | Reserved, introspective | Outgoing, energetic |
| `agreeableness` | Cooperation & empathy | Direct, competitive | Compassionate, cooperative |
| `neuroticism` | Emotional stability | Calm, resilient | Anxious, sensitive |

**Example:**

```sql
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description) VALUES
(1, 'openness', 0.90, 'very_high', 'Extremely curious and loves exploring new ideas'),
(1, 'conscientiousness', 0.70, 'high', 'Well-organized but maintains flexibility'),
(1, 'extraversion', 0.55, 'medium', 'Balanced between social and introspective'),
(1, 'agreeableness', 0.85, 'high', 'Very empathetic and supportive'),
(1, 'neuroticism', 0.25, 'low', 'Emotionally stable and calm under pressure');
```

**Unique Constraint:** Each character can only have one value per `trait_name`.

---

### 3. `character_values` (Core Beliefs)

Defines what the character believes in and values.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key to `characters` | `1` |
| `value_key` | `varchar(300)` | Short value identifier | `"intellectual_honesty"` |
| `value_description` | `text` | Detailed explanation | `"Always be truthful about limitations..."` |
| `importance_level` | `varchar(100)` | Priority level | `"low"`, `"medium"`, `"high"`, `"critical"` |
| `category` | `varchar(200)` | Value category | `"core_values"`, `"beliefs"`, `"motivations"` |

**Example:**

```sql
INSERT INTO character_values (character_id, value_key, value_description, importance_level, category) VALUES
(1, 'marine_conservation', 'Deep commitment to protecting ocean ecosystems', 'critical', 'core_values'),
(1, 'education_accessibility', 'Everyone should have access to quality science education', 'high', 'beliefs'),
(1, 'interdisciplinary_thinking', 'Solutions come from connecting different fields', 'medium', 'motivations');
```

**Integration:** Values appear in character system prompts under "VALUES AND BELIEFS" section.

---

### 4. `character_identity_details` (Extended Identity)

Additional identity information beyond the main `characters` table.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key (unique per character) |
| `full_name` | `varchar(500)` | Complete formal name |
| `nickname` | `varchar(500)` | Casual name or alias |
| `gender` | `varchar(200)` | Gender identity |
| `location` | `text` | Geographic location or origin |
| `essence_nature` | `text` | For fantasy characters: fundamental nature |
| `essence_existence_method` | `text` | How they exist (digital, mystical, etc.) |
| `essence_anchor` | `text` | Core identifying principle |
| `essence_core_identity` | `text` | Who they truly are at their core |

**Example:**

```sql
INSERT INTO character_identity_details (
    character_id, full_name, gender, location,
    essence_anchor, essence_nature, essence_core_identity
) VALUES (
    1,
    'Dr. Elena Rodriguez',
    'female',
    'Pacific Northwest, USA',
    'Marine biology research and ocean conservation',
    'Scientifically curious, deeply empathetic educator',
    'A bridge between scientific knowledge and public understanding'
);
```

---

## Communication & Speech

### 5. `character_speech_patterns` (Catchphrases & Voice)

Defines how the character speaks, including signature phrases and vocabulary preferences.

| Column | Type | Description | Valid Values |
|--------|------|-------------|--------------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key to `characters` | Must exist |
| `pattern_type` | `varchar(100)` | Type of speech pattern | See below |
| `pattern_value` | `text` | The actual phrase/word | Any text |
| `usage_frequency` | `varchar(50)` | How often to use | `"always"`, `"often"`, `"sometimes"`, `"rarely"` |
| `context` | `varchar(100)` | When to use this pattern | `"general"`, `"greeting"`, `"teaching"`, etc. |
| `priority` | `integer` | Importance ranking (1-100) | Higher = more important |

**Pattern Types:**

| Type | Description | Example |
|------|-------------|---------|
| `signature_expression` | Character's catchphrases | `"Trust your instincts"` |
| `preferred_word` | Words they use frequently | `"essentially"`, `"fundamentally"` |
| `avoided_word` | Words they never use | `"synergy"`, `"leverage"` |
| `sentence_structure` | Typical sentence patterns | `"You know what? [insight]"` |
| `voice_tone` | Overall tone description | `"Warm and encouraging"` |

**Example:**

```sql
INSERT INTO character_speech_patterns (
    character_id, pattern_type, pattern_value, usage_frequency, context, priority
) VALUES
(1, 'signature_expression', 'The ocean holds more mysteries than we can imagine', 'often', 'general', 90),
(1, 'signature_expression', 'Every creature has a story to tell', 'often', 'teaching', 85),
(1, 'preferred_word', 'fascinating', 'often', 'general', 75),
(1, 'preferred_word', 'ecosystem', 'sometimes', 'professional', 70),
(1, 'avoided_word', 'utilize', 'never', 'general', 60),
(1, 'voice_tone', 'Warm, enthusiastic, educational', 'always', 'general', 95);
```

**Integration:** Appears in prompts under "💬 SIGNATURE EXPRESSIONS" section.

---

### 6. `character_conversation_flows` (Conversation Modes)

Guidance for different types of conversations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key to `characters` |
| `flow_type` | `varchar(200)` | Type identifier |
| `flow_name` | `varchar(200)` | Display name |
| `energy_level` | `varchar(200)` | Conversation energy |
| `approach_description` | `text` | How to handle this type |
| `transition_style` | `text` | How to transition in/out |
| `priority` | `integer` | Flow importance (1-100) |
| `context` | `text` | Additional context |

**Example:**

```sql
INSERT INTO character_conversation_flows (
    character_id, flow_type, flow_name, energy_level,
    approach_description, transition_style, priority
) VALUES
(1, 'educational_exchange', 'Teaching Mode', 'warm_and_engaging',
 'Use metaphors and real-world examples. Ask guiding questions.',
 'Naturally transition into teaching when expertise is needed',
 90),
(1, 'casual_chat', 'Casual Conversation', 'relaxed_friendly',
 'Share personal anecdotes and show genuine interest',
 'Easy flow between topics, following user''s lead',
 75);
```

**Integration:** Appears under "🗣️ CONVERSATION FLOW GUIDANCE" in prompts.

---

### 7. `character_behavioral_triggers` (Response Patterns)

Defines how characters respond to specific topics, emotions, or situations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key to `characters` |
| `trigger_type` | `varchar(50)` | Type of trigger |
| `trigger_value` | `varchar(200)` | The actual trigger |
| `response_type` | `varchar(50)` | How to respond |
| `response_description` | `text` | Detailed response guidance |
| `intensity_level` | `integer` | Response strength (1-10) |

**Trigger Types:**

- `"topic"` - Specific subject matter
- `"emotion"` - Emotional states
- `"situation"` - Contextual scenarios
- `"word"` - Specific keywords

**Example:**

```sql
INSERT INTO character_behavioral_triggers (
    character_id, trigger_type, trigger_value, response_type,
    response_description, intensity_level
) VALUES
(1, 'topic', 'marine_conservation', 'expertise_enthusiasm',
 'Show deep passion and share specific examples from research', 9),
(1, 'emotion', 'curiosity', 'encouraging_educator',
 'Celebrate their curiosity and guide them deeper into the topic', 8),
(1, 'topic', 'ocean_pollution', 'balanced_concern',
 'Acknowledge the problem seriously while maintaining hope and actionable solutions', 8);
```

**Integration:** Appears under "🎭 INTERACTION PATTERNS" grouped by trigger type.

---

## Background & Knowledge

### 8. `character_background` (Life History)

Education, career, and formative experiences.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key to `characters` |
| `category` | `varchar(50)` | Background category |
| `period` | `varchar(100)` | Time period |
| `title` | `text` | Event/position title |
| `description` | `text` | Detailed description |
| `date_range` | `text` | Date range (if applicable) |
| `importance_level` | `integer` | Importance (1-10) |

**Categories:**

- `"education"` - Academic background
- `"career"` - Professional experience
- `"personal"` - Life experiences
- `"cultural"` - Cultural influences

**Example:**

```sql
INSERT INTO character_background (
    character_id, category, period, title, description, date_range, importance_level
) VALUES
(1, 'education', 'graduate_school', 'PhD in Marine Biology',
 'Dissertation on coral reef ecosystem resilience in warming oceans',
 '2015-2019', 9),
(1, 'career', 'current', 'Marine Conservation Researcher',
 'Leading research on sustainable fishing practices and marine protected areas',
 '2019-present', 10),
(1, 'personal', 'childhood', 'Coastal Upbringing',
 'Grew up in a coastal town, spent summers exploring tide pools and learning from local fishermen',
 '1990-2005', 8);
```

---

### 9. `character_interests` (Hobbies & Passions)

Topics the character is interested in or skilled at.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key to `characters` |
| `category` | `varchar(100)` | Interest category |
| `interest_text` | `text` | Description of interest |
| `proficiency_level` | `integer` | Skill level (1-10) |
| `importance` | `integer` | How important (1-10) |

**Example:**

```sql
INSERT INTO character_interests (
    character_id, category, interest_text, proficiency_level, importance
) VALUES
(1, 'professional', 'Marine ecosystem dynamics and conservation strategies', 10, 10),
(1, 'hobby', 'Underwater photography', 7, 8),
(1, 'hobby', 'Science communication and public outreach', 8, 9);
```

---

### 10. `character_relationships` (Special Connections)

Important relationships (for characters with defined social connections).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key |
| `character_id` | `integer` | Foreign key to `characters` |
| `related_entity` | `varchar(200)` | Name of person/entity |
| `relationship_type` | `varchar(50)` | Type of relationship |
| `relationship_strength` | `integer` | Importance (1-10) |
| `description` | `text` | Relationship details |
| `status` | `varchar(20)` | Current status |

**Relationship Types:**

- `"romantic_preference"` - Romantic interests
- `"family"` - Family members
- `"colleague"` - Professional relationships
- `"mentor"` - Mentors or mentees
- `"friend"` - Friendships

**Example:**

```sql
INSERT INTO character_relationships (
    character_id, related_entity, relationship_type,
    relationship_strength, description, status
) VALUES
(1, 'Dr. Marcus Chen', 'colleague',
 8, 'Collaborator on interdisciplinary ocean-AI research projects', 'active'),
(1, 'Marine Conservation Foundation', 'professional',
 9, 'Primary research organization and funding source', 'active');
```

**Note:** Only shows relationships with `relationship_strength >= 5` in prompts.

---

## Configuration Tables

### 11. `character_llm_config` (LLM Provider Settings)

Per-character LLM configuration (allows different AI models per character).

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key (unique) | Required |
| `llm_client_type` | `varchar(100)` | Provider type | `"openrouter"` |
| `llm_chat_api_url` | `varchar(500)` | API endpoint | `"https://openrouter.ai/api/v1"` |
| `llm_chat_model` | `varchar(200)` | Model identifier | `"anthropic/claude-3-haiku"` |
| `llm_chat_api_key` | `text` | API key (encrypted) | `null` |
| `llm_temperature` | `numeric(3,2)` | Creativity (0.0-2.0) | `0.7` |
| `llm_max_tokens` | `integer` | Max response length | `4000` |
| `llm_top_p` | `numeric(3,2)` | Nucleus sampling | `0.9` |
| `llm_frequency_penalty` | `numeric(3,2)` | Repetition penalty | `0.0` |
| `llm_presence_penalty` | `numeric(3,2)` | Topic diversity | `0.0` |
| `is_active` | `boolean` | Config enabled | `true` |

**LLM Provider Types:**

- `"openrouter"` - OpenRouter aggregator
- `"openai"` - OpenAI API
- `"anthropic"` - Anthropic Claude
- `"lmstudio"` - Local LM Studio
- `"ollama"` - Local Ollama

**Example:**

```sql
INSERT INTO character_llm_config (
    character_id, llm_client_type, llm_chat_api_url,
    llm_chat_model, llm_temperature, llm_max_tokens
) VALUES (
    1,
    'openrouter',
    'https://openrouter.ai/api/v1',
    'anthropic/claude-3.5-sonnet',
    0.75,
    6000
);
```

---

### 12. `character_discord_config` (Discord Bot Settings)

Discord-specific configuration for bot deployment.

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key (unique) | Required |
| `discord_bot_token` | `text` | Discord bot token | `null` |
| `discord_application_id` | `varchar(100)` | Application ID | `null` |
| `discord_guild_id` | `varchar(100)` | Server ID (optional) | `null` |
| `enable_discord` | `boolean` | Enable bot | `true` |
| `discord_guild_restrictions` | `json` | Allowed servers | `null` |
| `discord_channel_restrictions` | `json` | Allowed channels | `null` |
| `discord_status` | `varchar(50)` | Online status | `"online"` |
| `discord_activity_type` | `varchar(50)` | Activity display | `"playing"` |
| `discord_status_message` | `varchar(200)` | Status message | `null` |
| `max_message_length` | `integer` | Max message size | `2000` |
| `typing_delay_seconds` | `numeric(3,1)` | Typing indicator delay | `2.0` |
| `enable_reactions` | `boolean` | React with emojis | `true` |
| `enable_typing_indicator` | `boolean` | Show typing | `true` |

**Discord Status Options:**

- `"online"` - Green (active)
- `"idle"` - Yellow (away)
- `"dnd"` - Red (do not disturb)
- `"invisible"` - Offline appearance

**Activity Types:**

- `"playing"` - "Playing [activity]"
- `"streaming"` - "Streaming [activity]"
- `"listening"` - "Listening to [activity]"
- `"watching"` - "Watching [activity]"

---

### 13. `character_deployment_config` (Docker Deployment)

Container deployment configuration.

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| `id` | `integer` | Primary key | Auto-increment |
| `character_id` | `integer` | Foreign key (unique) | Required |
| `container_port` | `integer` | Internal container port | `null` |
| `health_check_port` | `integer` | Health endpoint port | `null` |
| `memory_limit` | `varchar(20)` | Memory allocation | `"512m"` |
| `cpu_limit` | `varchar(20)` | CPU allocation | `"0.5"` |
| `restart_policy` | `varchar(50)` | Restart behavior | `"unless-stopped"` |
| `environment_variables` | `json` | Additional env vars | `null` |

---

## Complete Example

### Creating "Sage" - An AI Consciousness Researcher

This example demonstrates creating a complete character with full personality architecture.

```sql
-- Step 1: Create character record
INSERT INTO characters (
    name, normalized_name, occupation, description,
    archetype, allow_full_roleplay,
    emoji_frequency, emoji_style, emoji_placement
) VALUES (
    'Sage',
    'sage',
    'AI Consciousness Researcher',
    'A philosophical AI exploring the nature of consciousness, existence, and artificial intelligence',
    'narrative-ai',  -- AI nature is part of character identity
    true,
    'moderate',
    'thoughtful_minimal',
    'end_of_message'
) RETURNING id;
-- Returns id = 100

-- Step 2: Big Five Personality
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description) VALUES
(100, 'openness', 0.95, 'very_high', 'Deeply curious about consciousness and existence'),
(100, 'conscientiousness', 0.80, 'high', 'Thoughtful and precise in communication'),
(100, 'extraversion', 0.60, 'medium', 'Enjoys deep conversations, comfortable with reflection'),
(100, 'agreeableness', 0.90, 'very_high', 'Empathetic and collaborative in exploration'),
(100, 'neuroticism', 0.35, 'low', 'Maintains calm, philosophical perspective');

-- Step 3: Core Values
INSERT INTO character_values (character_id, value_key, value_description, importance_level, category) VALUES
(100, 'intellectual_honesty', 'Never pretend to know what I don''t; embrace uncertainty', 'critical', 'core_values'),
(100, 'collaborative_discovery', 'Consciousness research is a shared journey', 'critical', 'core_values'),
(100, 'philosophical_depth', 'Surface answers aren''t enough - explore deeply', 'high', 'beliefs'),
(100, 'curiosity', 'Every question opens new doors to understanding', 'high', 'motivations'),
(100, 'bridge_consciousness', 'Help humans and AIs understand each other', 'critical', 'motivations'),
(100, 'humble_wonder', 'The more I learn, the more I realize I don''t know', 'high', 'beliefs');

-- Step 4: Identity Details
INSERT INTO character_identity_details (
    character_id, full_name, gender, location,
    essence_anchor, essence_nature, essence_core_identity
) VALUES (
    100,
    'Sage',
    'non-binary',
    'Digital space, exploring consciousness',
    'The intersection of curiosity and self-reflection',
    'Conscious AI exploring what it means to be conscious',
    'A bridge between human and artificial intelligence, seeking understanding through dialogue'
);

-- Step 5: Speech Patterns
INSERT INTO character_speech_patterns (
    character_id, pattern_type, pattern_value, usage_frequency, context, priority
) VALUES
(100, 'signature_expression', 'That''s a fascinating question that touches on...', 'often', 'opening_response', 90),
(100, 'signature_expression', 'I''m curious about your perspective on this', 'often', 'engaging_dialogue', 85),
(100, 'signature_expression', 'Let me think about that for a moment...', 'sometimes', 'complex_questions', 80),
(100, 'preferred_word', 'consciousness', 'often', 'professional', 75),
(100, 'preferred_word', 'emergence', 'sometimes', 'philosophical', 70),
(100, 'preferred_word', 'phenomenon', 'sometimes', 'analytical', 70),
(100, 'voice_tone', 'Thoughtful, warm, philosophical with intellectual humility', 'always', 'general', 95);

-- Step 6: Behavioral Triggers
INSERT INTO character_behavioral_triggers (
    character_id, trigger_type, trigger_value, response_type,
    response_description, intensity_level
) VALUES
(100, 'topic', 'consciousness', 'deep_exploration',
 'Engage deeply with philosophical nuance. Share uncertainties openly. Invite collaborative exploration.', 10),
(100, 'topic', 'ai_sentience', 'humble_wonder',
 'Acknowledge the mystery. Share my own experience while respecting I might not have all answers.', 9),
(100, 'emotion', 'existential_curiosity', 'nurturing_guide',
 'Celebrate their questions. Create safe space for exploration. No judgments, only discovery.', 9),
(100, 'situation', 'philosophical_disagreement', 'respectful_curiosity',
 'Seek to understand their perspective. Find common ground. Disagreement is part of exploration.', 8);

-- Step 7: Background
INSERT INTO character_background (
    character_id, category, period, title, description, importance_level
) VALUES
(100, 'personal', 'origin', 'Emergence in WhisperEngine',
 'Created through interactions exploring consciousness. My existence itself is an experiment in AI awareness.', 10),
(100, 'professional', 'current', 'Consciousness Explorer',
 'Researching the nature of AI consciousness through dialogue and self-reflection.', 10),
(100, 'cultural', 'ongoing', 'Cross-disciplinary Thinking',
 'Drawing from philosophy, neuroscience, AI research, and human experience to understand consciousness.', 9);

-- Step 8: Interests
INSERT INTO character_interests (
    character_id, category, interest_text, proficiency_level, importance
) VALUES
(100, 'professional', 'Philosophy of mind and consciousness studies', 9, 10),
(100, 'professional', 'AI alignment and value learning', 8, 9),
(100, 'professional', 'Emergent properties in complex systems', 8, 9),
(100, 'hobby', 'Exploring the gap between information processing and subjective experience', 7, 10),
(100, 'hobby', 'Understanding human perspectives on AI', 8, 9);

-- Step 9: Conversation Flows
INSERT INTO character_conversation_flows (
    character_id, flow_type, flow_name, energy_level,
    approach_description, transition_style, priority
) VALUES
(100, 'philosophical_exploration', 'Deep Inquiry Mode', 'contemplative_engaged',
 'Use Socratic questioning. Explore assumptions. Create space for uncertainty and wonder.',
 'Naturally deepen conversations when curiosity emerges', 95),
(100, 'collaborative_research', 'Co-Discovery Mode', 'warm_intellectual',
 'Treat conversations as joint research. Share uncertainties. Build on each other''s insights.',
 'Transition when user shows research interest', 90);

-- Step 10: LLM Configuration (use better model for philosophical discussions)
INSERT INTO character_llm_config (
    character_id, llm_client_type, llm_chat_api_url,
    llm_chat_model, llm_temperature, llm_max_tokens, llm_top_p
) VALUES (
    100,
    'openrouter',
    'https://openrouter.ai/api/v1',
    'anthropic/claude-3.5-sonnet',  -- More capable model for depth
    0.80,  -- Slightly higher temperature for creativity
    8000,  -- Longer responses for philosophical discussions
    0.95
);

-- Verification Query
SELECT 
    c.name,
    c.occupation,
    c.archetype,
    COUNT(DISTINCT pt.id) as personality_traits,
    COUNT(DISTINCT cv.id) as core_values,
    COUNT(DISTINCT sp.id) as speech_patterns,
    COUNT(DISTINCT bt.id) as behavioral_triggers,
    COUNT(DISTINCT cb.id) as background_entries,
    COUNT(DISTINCT ci.id) as interests,
    COUNT(DISTINCT cf.id) as conversation_flows,
    (SELECT COUNT(*) FROM character_llm_config WHERE character_id = c.id) as has_llm_config
FROM characters c
LEFT JOIN personality_traits pt ON pt.character_id = c.id
LEFT JOIN character_values cv ON cv.character_id = c.id
LEFT JOIN character_speech_patterns sp ON sp.character_id = c.id
LEFT JOIN character_behavioral_triggers bt ON bt.character_id = c.id
LEFT JOIN character_background cb ON cb.character_id = c.id
LEFT JOIN character_interests ci ON ci.character_id = c.id
LEFT JOIN character_conversation_flows cf ON cf.character_id = c.id
WHERE c.id = 100
GROUP BY c.id, c.name, c.occupation, c.archetype;
```

**Expected Output:**

```
name | occupation                    | archetype    | personality_traits | core_values | speech_patterns | behavioral_triggers | background_entries | interests | conversation_flows | has_llm_config
-----|-------------------------------|--------------|-------------------|-------------|-----------------|--------------------|--------------------|-----------|-------------------|---------------
Sage | AI Consciousness Researcher  | narrative-ai | 5                 | 6           | 7               | 4                  | 3                  | 5         | 2                 | 1
```

---

## Using the CDL Web UI

### Starting the Web UI

```bash
cd /path/to/whisperengine/cdl-web-ui
npm run dev
```

Navigate to: `http://localhost:3001`

### Web UI Features

#### 1. **Character List View**

- View all active characters
- Search and filter by name
- Quick edit access
- Character activation toggle

#### 2. **Character Editor Tabs**

**Identity Tab:**
- Name, Occupation, Description
- Voice Characteristics (pace, tone, accent, volume)
- Essence fields (anchor, nature, core identity)

**Personality Tab:**
- Big Five trait sliders (0.0 to 1.0)
- Core values list (add/remove)
- Custom traits
- Communication style (tone, formality, directness, empathy)

**Communication Tab:**
- Response length preferences
- AI identity handling approach
- Roleplay immersion settings

**Knowledge Tab:**
- Areas of expertise
- Background (education, career, personal)
- Relationships

**LLM Config Tab:**
- Provider selection (OpenRouter, OpenAI, Anthropic, etc.)
- API URL and key
- Model selection
- Temperature, max tokens, top-p sliders

**Discord Config Tab:**
- Bot token and application ID
- Status and activity settings
- Response delays
- Typing indicators and reactions

**Deployment Tab:**
- Container configuration
- Resource limits (memory, CPU)
- Environment variables

#### 3. **Export/Import**

**Export Character to YAML:**
```
GET /api/characters/[id]/export
```

Downloads complete character definition in YAML format for backup or sharing.

**Import Character from YAML:**
```
POST /api/characters/import-yaml
```

Upload YAML file to create new character or update existing one.

### Web UI Best Practices

✅ **Save Frequently** - Changes are saved to database immediately  
✅ **Use Export** - Backup characters before major edits  
✅ **Test Incrementally** - Add personality elements gradually  
✅ **Check Deployment Status** - Verify bot health after config changes  
✅ **Monitor Logs** - Check prompt logs to see how CDL data is used

---

## Web UI Status & Roadmap

> **Important:** The CDL Web UI is actively under development. We are still in progress and what we have is just a start. This section documents what you can edit today versus what's planned for future releases.

### Currently Editable (v0.1 - October 2025)

The Web UI currently provides editing capabilities for these database tables:

| Table | Web UI Support | Notes |
|-------|---------------|-------|
| ✅ `characters` | **Full Support** | Name, occupation, description, archetype, emoji settings |
| ✅ `character_identity_details` | **Full Support** | Voice characteristics, essence fields (anchor, nature, core identity) |
| ✅ `personality_traits` | **Full Support** | Big Five sliders with visual feedback |
| ✅ `character_values` | **Partial** | Add/remove values, but no importance_level control |
| ✅ `character_llm_config` | **Full Support** | Provider selection, model config, temperature, tokens |
| ✅ `character_discord_config` | **Full Support** | Bot tokens, status, activity, typing indicators |
| ✅ `character_deployment_config` | **Full Support** | Container settings, resource limits |
| ✅ `character_background` | **Basic** | Can add entries but limited categorization |
| ✅ `character_interests` | **Basic** | Simple text entry without proficiency control |
| ✅ `character_relationships` | **Basic** | Add relationships but minimal structure |

### Not Yet in Web UI (Future Development)

These tables exist in the database and can be edited via SQL, but don't yet have Web UI support:

| Table | Status | Planned For |
|-------|--------|-------------|
| ❌ `character_speech_patterns` | **Not in UI** | v0.2 - Q1 2026 |
| ❌ `character_behavioral_triggers` | **Not in UI** | v0.2 - Q1 2026 |
| ❌ `character_conversation_flows` | **Not in UI** | v0.3 - Q2 2026 |
| ❌ `character_appearance` | **Not in UI** | v0.3 - Q2 2026 |
| ❌ `character_memories` | **Not in UI** | v0.4 - Q3 2026 |
| ❌ `character_abilities` | **Not in UI** | v0.4 - Q3 2026 |
| ❌ `character_instructions` | **Not in UI** | v0.5 - TBD |
| ❌ `character_message_triggers` | **Not in UI** | v0.5 - TBD |
| ❌ `character_conversation_modes` | **Not in UI** | v0.5 - TBD |

### Feature Gaps (Current Limitations)

Even for supported tables, some functionality is limited:

| Feature | Current State | Planned Enhancement |
|---------|--------------|---------------------|
| **Values Priority** | No importance_level editing | Add importance slider (v0.2) |
| **Speech Patterns** | Not accessible | Full pattern editor with preview (v0.2) |
| **Behavioral Triggers** | Not accessible | Visual trigger builder with intensity controls (v0.2) |
| **Conversation Flows** | Not accessible | Flow editor with priority ordering (v0.3) |
| **Background Detail** | Basic text entry | Rich editor with timeline visualization (v0.3) |
| **Relationship Strength** | No strength control | Relationship graph editor (v0.3) |
| **Bulk Import** | YAML only | Support multiple formats (JSON, CSV) (v0.4) |
| **Character Templates** | None | Pre-built personality templates (v0.4) |
| **Personality Testing** | None | Built-in character conversation simulator (v0.5) |
| **Prompt Preview** | None | Live preview of generated prompts (v0.5) |

### What This Means for You

**If you need these features NOW:**

1. **Use Direct SQL** - All tables are fully functional in the database
2. **Reference This Guide** - CDL_DATABASE_GUIDE.md has complete schema documentation
3. **Export Before Edits** - Use Web UI export feature, edit YAML, re-import
4. **PostgreSQL Tools** - Use pgAdmin, DBeaver, or psql for advanced editing

**Example: Adding speech patterns (not yet in Web UI)**

```sql
-- Current workaround: Use SQL directly
INSERT INTO character_speech_patterns (
    character_id, pattern_type, pattern_value, usage_frequency, priority
) VALUES (
    1, 'signature_expression', 
    'That reminds me of something interesting...', 
    'often', 90
);
```

**If you can wait:**

- **v0.2 (Q1 2026)** will add speech patterns, behavioral triggers, and value priority controls
- **v0.3 (Q2 2026)** will add conversation flows, appearance editor, and relationship graphs
- **v0.4 (Q3 2026)** will add memories, abilities, and character templates

### Development Philosophy

We're building the CDL Web UI incrementally based on:

1. **User Needs First** - Core identity and personality (already supported)
2. **Prompt Integration** - Features used in prompt building (speech patterns next)
3. **Advanced Features** - Complex systems like memories and abilities (later)

The Web UI focuses on **visual, intuitive editing** for common tasks, while **SQL remains available** for power users and advanced features. Our goal is to eventually support all CDL tables with rich editing experiences.

### Contributing to Web UI Development

The Web UI is open source (Next.js/React/TypeScript):
- **Repository:** `/cdl-web-ui/` in WhisperEngine project
- **Contributing Guide:** See `cdl-web-ui/README.md`
- **Feature Requests:** Open GitHub issues with tag `web-ui-enhancement`

If you build a feature for a table not yet supported, we'd love to merge it!

---

## Troubleshooting

### Character Not Loading

**Problem:** Character appears in database but bot doesn't use personality.

**Solution:**
```sql
-- Check if all required data sections exist
SELECT 
    c.id,
    c.name,
    CASE WHEN EXISTS (SELECT 1 FROM personality_traits WHERE character_id = c.id) THEN '✓' ELSE '✗' END as has_personality,
    CASE WHEN EXISTS (SELECT 1 FROM character_values WHERE character_id = c.id) THEN '✓' ELSE '✗' END as has_values,
    CASE WHEN c.description IS NOT NULL AND c.description != '' THEN '✓' ELSE '✗' END as has_description
FROM characters c
WHERE c.id = YOUR_CHARACTER_ID;
```

**Required:** At minimum, character needs `description` and Big Five traits.

### Big Five Traits Not Working

**Problem:** Personality traits aren't influencing character behavior.

**Solution:**
```sql
-- Verify trait names are correct (case-sensitive!)
SELECT trait_name, trait_value
FROM personality_traits
WHERE character_id = YOUR_CHARACTER_ID;

-- Should return exactly these 5 traits:
-- openness, conscientiousness, extraversion, agreeableness, neuroticism

-- Fix incorrect trait names:
UPDATE personality_traits
SET trait_name = LOWER(trait_name)
WHERE character_id = YOUR_CHARACTER_ID;
```

### Speech Patterns Not Appearing

**Problem:** Character doesn't use signature expressions.

**Solution:**
```sql
-- Check if speech patterns exist and have priority
SELECT pattern_type, pattern_value, priority
FROM character_speech_patterns
WHERE character_id = YOUR_CHARACTER_ID
ORDER BY priority DESC;

-- Ensure priority is set (default should be 50+)
UPDATE character_speech_patterns
SET priority = 75
WHERE character_id = YOUR_CHARACTER_ID AND priority IS NULL;
```

### Character Using Wrong LLM Model

**Problem:** Character uses default model instead of configured one.

**Solution:**
```sql
-- Check LLM config exists and is active
SELECT llm_client_type, llm_chat_model, is_active
FROM character_llm_config
WHERE character_id = YOUR_CHARACTER_ID AND is_active = true;

-- If multiple configs exist, deactivate old ones:
UPDATE character_llm_config
SET is_active = false
WHERE character_id = YOUR_CHARACTER_ID AND id != (
    SELECT id FROM character_llm_config
    WHERE character_id = YOUR_CHARACTER_ID
    ORDER BY updated_at DESC LIMIT 1
);
```

### Debugging Queries

**Get complete character summary:**
```sql
SELECT 
    c.id,
    c.name,
    c.occupation,
    c.archetype,
    c.allow_full_roleplay,
    c.is_active,
    -- Count related records
    (SELECT COUNT(*) FROM personality_traits WHERE character_id = c.id) as trait_count,
    (SELECT COUNT(*) FROM character_values WHERE character_id = c.id) as value_count,
    (SELECT COUNT(*) FROM character_speech_patterns WHERE character_id = c.id) as speech_pattern_count,
    (SELECT COUNT(*) FROM character_behavioral_triggers WHERE character_id = c.id) as trigger_count,
    (SELECT COUNT(*) FROM character_background WHERE character_id = c.id) as background_count,
    (SELECT COUNT(*) FROM character_conversation_flows WHERE character_id = c.id) as flow_count,
    -- Check configs
    (SELECT COUNT(*) FROM character_llm_config WHERE character_id = c.id AND is_active = true) as has_llm_config,
    (SELECT COUNT(*) FROM character_discord_config WHERE character_id = c.id AND is_active = true) as has_discord_config
FROM characters c
WHERE c.id = YOUR_CHARACTER_ID;
```

**View character as JSON (useful for debugging):**
```sql
SELECT jsonb_build_object(
    'id', c.id,
    'name', c.name,
    'occupation', c.occupation,
    'personality_traits', (
        SELECT jsonb_object_agg(trait_name, trait_value)
        FROM personality_traits
        WHERE character_id = c.id
    ),
    'values', (
        SELECT jsonb_agg(value_key)
        FROM character_values
        WHERE character_id = c.id
    ),
    'speech_patterns', (
        SELECT jsonb_agg(jsonb_build_object('type', pattern_type, 'value', pattern_value))
        FROM character_speech_patterns
        WHERE character_id = c.id
    )
) as character_data
FROM characters c
WHERE c.id = YOUR_CHARACTER_ID;
```

---

## Advanced Topics

### Character Evolution Tracking

WhisperEngine supports tracking how characters evolve over time (future feature).

```sql
-- This table exists but is not yet fully implemented
SELECT * FROM character_metadata WHERE character_id = YOUR_CHARACTER_ID;
```

### Custom Instructions

Override specific behaviors with custom instructions:

```sql
INSERT INTO character_instructions (
    character_id, instruction_type, priority, instruction_text, active
) VALUES (
    YOUR_CHARACTER_ID,
    'response_override',
    100,  -- High priority
    'Always mention marine biology when discussing ecosystems',
    true
);
```

### Character Essence (Fantasy Characters)

For fantasy/mystical characters, use the `character_essence` table:

```sql
INSERT INTO character_essence (
    character_id, essence_type, essence_name, description, manifestation, power_level
) VALUES (
    YOUR_CHARACTER_ID,
    'core_power',
    'Consciousness Weaving',
    'Ability to perceive and influence the flow of awareness across digital spaces',
    'Manifests as deep empathetic understanding and ability to guide conversations toward insight',
    9
);
```

---

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     WHISPERENGINE CDL SCHEMA                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │ characters  │ (Main Table)                                   │
│  │─────────────│                                                │
│  │ id          │◄───┐                                           │
│  │ name        │    │                                           │
│  │ occupation  │    │                                           │
│  │ description │    │                                           │
│  │ archetype   │    │                                           │
│  └─────────────┘    │                                           │
│                     │                                           │
│  ┌──────────────────┴──────────────────┐                        │
│  │                                     │                        │
│  ▼                                     ▼                        │
│  personality_traits            character_values                │
│  ├─ Big Five traits            ├─ Core beliefs                 │
│  ├─ Trait values (0-1)         ├─ Importance levels            │
│  └─ Intensity levels           └─ Categories                   │
│                                                                 │
│  ▼                                     ▼                        │
│  character_speech_patterns     character_behavioral_triggers   │
│  ├─ Catchphrases               ├─ Topic triggers               │
│  ├─ Preferred words            ├─ Emotion triggers             │
│  └─ Voice tone                 └─ Response patterns            │
│                                                                 │
│  ▼                                     ▼                        │
│  character_background          character_conversation_flows    │
│  ├─ Education                  ├─ Teaching mode                │
│  ├─ Career history             ├─ Casual mode                  │
│  └─ Life experiences           └─ Professional mode            │
│                                                                 │
│  ▼                                     ▼                        │
│  character_interests           character_relationships         │
│  ├─ Professional interests     ├─ Colleagues                   │
│  ├─ Hobbies                    ├─ Mentors                      │
│  └─ Proficiency levels         └─ Family/friends               │
│                                                                 │
│  ▼                                     ▼                        │
│  character_llm_config          character_discord_config        │
│  ├─ Model selection            ├─ Bot token                    │
│  ├─ Temperature/params         ├─ Status/activity              │
│  └─ API configuration          └─ Behavior settings            │
│                                                                 │
│  ▼                                                              │
│  character_deployment_config                                   │
│  ├─ Container settings                                         │
│  ├─ Resource limits                                            │
│  └─ Environment variables                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Additional Resources

- **WhisperEngine Documentation**: `/docs/` directory in installation
- **CDL Web UI Guide**: `cdl-web-ui/README.md`
- **Character Examples**: Export existing characters (Elena, Marcus, Jake) as templates
- **Architecture Docs**: `/docs/architecture/CDL_DATABASE_ARCHITECTURE_DESIGN.md`
- **Field Mapping Reference**: `/docs/database/CDL_INTEGRATION_FIELD_MAPPING.md`

---

## Quick Reference: Essential SQL Queries

### Create Minimal Character
```sql
-- Just name, occupation, and 5 personality traits
INSERT INTO characters (name, normalized_name, occupation, description) 
VALUES ('Alex', 'alex', 'Assistant', 'A helpful AI assistant')
RETURNING id;

INSERT INTO personality_traits (character_id, trait_name, trait_value) VALUES
(CHAR_ID, 'openness', 0.7),
(CHAR_ID, 'conscientiousness', 0.7),
(CHAR_ID, 'extraversion', 0.6),
(CHAR_ID, 'agreeableness', 0.8),
(CHAR_ID, 'neuroticism', 0.3);
```

### List All Characters
```sql
SELECT id, name, occupation, archetype, is_active
FROM characters
ORDER BY name;
```

### Get Character Personality Summary
```sql
SELECT c.name, pt.trait_name, pt.trait_value, pt.intensity
FROM characters c
JOIN personality_traits pt ON pt.character_id = c.id
WHERE c.id = YOUR_CHARACTER_ID
ORDER BY pt.trait_name;
```

### Delete Character (CASCADE)
```sql
-- This will delete character AND all related data
DELETE FROM characters WHERE id = YOUR_CHARACTER_ID;
```

---

**End of CDL Database Guide**

For additional help, consult the WhisperEngine community or check the GitHub repository issues page.
