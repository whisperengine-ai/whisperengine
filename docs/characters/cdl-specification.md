# Character Definition Language (CDL) Specification v1.0

## Overview

The Character Definition Language (CDL) is a structured format for defining AI character personalities, backgrounds, and behavioral traits. CDL uses JSON format for reliability and ease of parsing.

## Format

CDL files use **JSON format** (`.json` extension) for optimal parsing reliability and developer experience.

### File Structure

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

## Version History

- **v1.0** (2025-09-17): Initial specification with JSON format
  - Core schema definition
  - Five-section character structure
  - Big Five personality integration
  - Project and goal tracking

## Future Considerations

- Extended personality models
- Relationship mapping
- Character evolution tracking
- Multi-character interactions
- Validation schema