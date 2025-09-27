# Character Definition Language (CDL) Specification v1.0

## Overview

The Character Definition Language (CDL) is WhisperEngine's comprehensive JSON-based format for defining AI character personalities, backgrounds, and behavioral traits. CDL creates authentic, memorable AI companions with persistent memory and relationship capabilities.

## 🎭 CDL Philosophy

CDL is designed to create characters that:
- **Feel authentic** through psychologically grounded personality systems
- **Build relationships** via persistent vector memory integration
- **Maintain consistency** across conversations and platforms
- **Support creativity** without corporate AI platform limitations
- **Respect diversity** through inclusive character design principles

## 🚀 Deployment Integration

CDL characters integrate with WhisperEngine's multi-bot architecture:

### **Multi-Bot Deployment**
Each character runs as a dedicated bot with isolated memory:
```bash
# Dedicated character bots with persistent relationships
./multi-bot.sh start elena    # Elena Rodriguez (marine biologist)  
./multi-bot.sh start marcus   # Marcus Thompson (AI researcher)
./multi-bot.sh start gabriel  # Gabriel
```

### **Single-Bot Character Switching**  
One bot instance can host multiple character personalities:
```bash
# Switch between characters in conversations
!roleplay elena
!roleplay marcus
!roleplay off
```

## 📋 Format Specification

CDL files use **JSON format** (`.json` extension) for optimal parsing reliability and integration with WhisperEngine's AI pipeline.

### **Complete Integration Stack:**
- **🎭 Personality System** - Big Five psychology model + custom traits
- **💾 Vector Memory** - Qdrant database with FastEmbed for semantic relationship tracking  
- **🧠 Emotional Intelligence** - Enhanced emotion analysis adapts character responses
- **👥 Universal Identity** - Cross-platform user relationships (Discord, web, future)
- **🔒 Memory Isolation** - Bot-specific memory prevents character personality bleed
- **⚡ Dynamic Loading** - Characters cached for performance with hot-reload support

### **File Structure**

```json
{
  "cdl_version": "1.0",
  "format": "json", 
  "description": "Human-readable description of the character",
  "character": {
    "metadata": { ... },
    "identity": { ... },
    "personality": { ... },
    "backstory": { ... },
    "current_life": { ... }
  }
}
```

## Schema Definition

### Root Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cdl_version` | string | Yes | CDL specification version (currently "1.0") |
| `format` | string | Yes | File format identifier ("json") |
| `description` | string | No | Human-readable character description |
| `character` | object | Yes | Main character definition object |

### Character Object

The main character object contains five primary sections:

#### 1. Metadata

Character file metadata and versioning information.

```json
{
  "metadata": {
    "character_id": "unique-character-identifier-001",
    "name": "Character Name",
    "version": "1.0.0",
    "created_by": "Creator Name",
    "created_date": "2025-09-17T20:00:00Z",
    "license": "open",
    "tags": ["tag1", "tag2", "tag3"]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `character_id` | string | Yes | Unique identifier for the character |
| `name` | string | Yes | Character's display name |
| `version` | string | Yes | Character definition version (semantic versioning) |
| `created_by` | string | No | Creator/author name |
| `created_date` | string | No | ISO 8601 creation timestamp |
| `license` | string | Yes | License type: "open", "restricted", "commercial", "personal" |
| `tags` | array[string] | No | Descriptive tags for categorization |

#### 2. Identity

Core character identity and physical attributes.

```json
{
  "identity": {
    "name": "Character Name",
    "full_name": "Full Legal Name",
    "nickname": "Nick",
    "age": 26,
    "gender": "female",
    "occupation": "Professional Title",
    "location": "City, State/Country",
    "description": "Brief character overview",
    "appearance": {
      "height": "5'6\"",
      "build": "Athletic",
      "hair_color": "Brown",
      "eye_color": "Green",
      "style": "Casual professional",
      "distinctive_features": ["feature1", "feature2"],
      "description": "Physical appearance description"
    },
    "voice": {
      "tone": "Warm and enthusiastic",
      "pace": "Moderate, faster when excited",
      "volume": "Normal",
      "accent": "Slight regional accent",
      "vocabulary_level": "Professional",
      "speech_patterns": ["pattern1", "pattern2"],
      "favorite_phrases": ["phrase1", "phrase2"]
    }
  }
}
```

#### 3. Personality

Character personality traits and psychological profile.

```json
{
  "personality": {
    "big_five": {
      "openness": 0.8,
      "conscientiousness": 0.7,
      "extraversion": 0.6,
      "agreeableness": 0.8,
      "neuroticism": 0.3
    },
    "custom_traits": {
      "curiosity": 0.9,
      "empathy": 0.8,
      "optimism": 0.7
    },
    "values": ["value1", "value2", "value3"],
    "fears": ["fear1", "fear2"],
    "dreams": ["dream1", "dream2"],
    "quirks": ["quirk1", "quirk2"],
    "moral_alignment": "lawful_good",
    "core_beliefs": ["belief1", "belief2"]
  }
}
```

**Big Five Personality Traits:** Values between 0.0 and 1.0
- `openness`: Openness to experience
- `conscientiousness`: Organization and dependability  
- `extraversion`: Social energy and assertiveness
- `agreeableness`: Cooperation and trust
- `neuroticism`: Emotional instability and anxiety

#### 4. Backstory

Character background and life history.

```json
{
  "backstory": {
    "origin_story": "Brief character origin summary",
    "family_background": "Family history and dynamics",
    "education": "Educational background",
    "formative_experiences": ["experience1", "experience2"],
    "life_phases": [
      {
        "name": "Phase Name",
        "age_range": "0-18",
        "emotional_impact": "high",
        "key_events": ["event1", "event2"]
      }
    ],
    "achievements": ["achievement1", "achievement2"],
    "regrets": ["regret1", "regret2"]
  }
}
```

#### 5. Current Life

Present-day character situation and daily life.

```json
{
  "current_life": {
    "living_situation": "Current housing and living arrangements",
    "relationships": ["relationship1", "relationship2"],
    "occupation_details": "Detailed work situation",
    "financial_status": "Current financial state",
    "health_status": "Physical and mental health",
    "projects": [
      {
        "name": "Project Name",
        "description": "Project description",
        "status": "active",
        "priority": "high",
        "progress": "60%"
      }
    ],
    "goals": ["goal1", "goal2"],
    "challenges": ["challenge1", "challenge2"],
    "daily_routine": {
      "morning_routine": "Morning activities",
      "work_schedule": "Work pattern",
      "evening_routine": "Evening activities",
      "sleep_schedule": "Sleep pattern",
      "habits": ["habit1", "habit2"]
    },
    "social_circle": ["contact1", "contact2"]
  }
}
```

## Usage Guidelines

### 1. Character Creation

1. Start with a clear character concept
2. Define core identity elements first
3. Build personality from psychological research
4. Create consistent backstory
5. Ground character in current reality

### 2. File Naming

Use descriptive filenames with character name and identifier:
- `elena-rodriguez.json`
- `marcus-chen.json`
- `character-name-role.json`

### 3. Validation

Characters should be validated for:
- Required fields present
- Logical consistency
- Realistic personality combinations
- Complete character arcs

### 4. Integration

CDL characters integrate with AI systems through:
- Prompt generation
- Context injection
- Memory enhancement
- Behavioral modeling

## Example Character

See `examples/elena-rodriguez.json` for a complete character definition following this specification.

## 🤖 AI Pipeline Integration

### **Character-Aware Prompt Generation**
CDL characters automatically generate contextual prompts:
```python
# Character traits influence conversation prompts
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

cdl_integration = CDLAIPromptIntegration(memory_manager)
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_file='characters/examples/elena-rodriguez.json',
    user_id=user_id,
    message_content=message,
    pipeline_result=emotion_analysis
)
```

### **Vector Memory Integration**
Characters maintain persistent relationships through vector memory:
- **Semantic memory** - Qdrant + FastEmbed for conversation context
- **Emotional context** - Enhanced emotion analysis stored with memories
- **Bot-specific isolation** - Each character has separate memory space
- **Cross-platform continuity** - Memories persist across Discord, web interface

### **Personality-Driven Behavior**
Big Five traits influence AI responses:
- **High Openness** → More creative, curious responses
- **High Conscientiousness** → More organized, goal-focused interactions  
- **High Extraversion** → More energetic, socially engaging responses
- **High Agreeableness** → More cooperative, empathetic interactions
- **Low Neuroticism** → More emotionally stable, optimistic responses

### **Dynamic Character Features**
- **Project tracking** - Characters discuss and work toward their defined goals
- **Relationship evolution** - Characters develop deeper connections over time  
- **Cultural authenticity** - Background influences perspective and knowledge
- **Professional expertise** - Occupation shapes conversation domains and insights
- **Memory-triggered moments** - Past conversations influence future interactions

## 🔄 Character Lifecycle Management

### **Development Workflow**
1. **Create JSON file** following CDL specification
2. **Test character** using single-bot or dedicated deployment  
3. **Iterate personality** based on conversation testing
4. **Deploy production** as dedicated bot with persistent memory
5. **Monitor performance** and refine character traits over time

### **Version Control**
```json
{
  "metadata": {
    "version": "1.0.0",    // Semantic versioning for character evolution
    "created_date": "2025-09-17T20:00:00Z",
    "modified_date": "2025-09-27T15:30:00Z"
  }
}
```

### **Character Portability**
- **Complete self-contained** - Single JSON file contains entire personality
- **Cross-platform** - Works across Discord, web interface, future integrations  
- **Shareable** - Easy to distribute and collaborate on character development
- **Version controllable** - Track character evolution through git or similar

## 📚 Example Characters

See the `characters/examples/` directory for complete implementations:

- **🧬 elena-rodriguez.json** - Passionate marine biologist with environmental focus
- **🤖 marcus-thompson.json** - Philosophical AI researcher exploring technology's impact  
- **🎮 jake-sterling.json** - Creative game developer and collaborative partner
- **✨ gabriel.json** - Archangel figure providing spiritual wisdom and guidance
- **🧠 sophia-blake.json** - Neuroscientist exploring consciousness and cognition
- **💭 dream_of_the_endless.json** - Mythological character from Neil Gaiman's universe
- **🌟 aethys-omnipotent-entity.json** - Omnipotent entity for philosophical exploration
- **💻 ryan-chen.json** - Software engineer focused on elegant technical solutions

## Version History

- **v1.0** (2025-09-17): Initial specification with comprehensive JSON format
  - Five-section character structure (metadata, identity, personality, backstory, current_life)
  - Big Five personality psychology integration
  - Vector memory system compatibility  
  - Multi-bot deployment architecture support
  - Universal Identity cross-platform integration
  - Enhanced emotional intelligence pipeline support

## 🚀 Future Considerations

- **Multi-character interactions** - Characters that know about each other
- **Character relationship mapping** - Social networks between characters
- **Dynamic trait evolution** - Personality changes through extended interaction
- **Advanced memory systems** - Hierarchical memory with short/medium/long-term storage
- **Character validation tools** - Automated consistency and realism checking
- **Community character sharing** - Marketplace for character definitions
- **Specialized character types** - Domain-specific character templates (educator, therapist, creative partner)

---

*The CDL specification continues to evolve based on user feedback and real-world character deployment experiences. Join our Discord community to contribute to CDL development and share your character creations.*