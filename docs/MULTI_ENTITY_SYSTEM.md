# Multi-Entity Relationship System Documentation

## Overview

WhisperEngine's Multi-Entity Relationship System enables rich associations between Characters ↔ Users ↔ AI "Self" entities, creating dynamic relationship networks that evolve through interactions.

## System Architecture

### Core Components

1. **Multi-Entity Models** (`src/graph_database/multi_entity_models.py`)
   - Enhanced entity classes for Users, Characters, and AI Self
   - Comprehensive relationship types and trust/familiarity metrics
   - Interaction event tracking with quality scoring

2. **Relationship Manager** (`src/graph_database/multi_entity_manager.py`)
   - Manages entity creation and relationship dynamics
   - Handles trust/familiarity evolution through interactions
   - Provides network analysis and similarity matching

3. **AI Self Bridge** (`src/graph_database/ai_self_bridge.py`)
   - Meta-cognitive interface for AI entity management
   - Facilitates character-user introductions with compatibility analysis
   - Provides relationship evolution guidance and social network insights

4. **Context Injector** (`src/llm/multi_entity_context.py`)
   - Injects character and relationship context into LLM prompts
   - Creates character-aware conversation templates
   - Provides relationship-specific guidance for interactions

5. **Command Handlers** (`src/handlers/multi_entity_handlers.py`)
   - Discord commands for character creation and management
   - Relationship analysis and social network features
   - AI-facilitated introduction commands

## Features

### Character Creation & Management
- **Character Profiles**: Name, occupation, personality traits, background, interests
- **User Ownership**: Characters belong to their creators with special relationship bonds
- **Character Limits**: Configurable per-user character creation limits
- **Character Development**: Personality evolution through interactions

### Relationship Types & Dynamics

#### User ↔ Character Relationships
- `CREATED_BY`: Creator relationship with special privileges
- `TRUSTED_BY`: High trust relationship through positive interactions  
- `FAVORITE_OF`: User's preferred character for conversations
- `FAMILIAR_WITH`: General acquaintance relationship

#### Character ↔ Character Relationships
- `KNOWS_ABOUT`: Cross-character awareness and knowledge
- `RELATED_TO`: Family or close personal relationships
- `SIMILAR_TO`: Personality or interest-based similarity
- `INSPIRED_BY`: Creative or intellectual inspiration relationships

#### AI Self ↔ All Entities
- `MANAGES`: AI system management of characters and users
- `OBSERVES`: Monitoring relationship patterns and health
- `FACILITATES`: Introduction and relationship guidance
- `LEARNS_FROM`: Pattern recognition and improvement
- `ADAPTS_TO`: System adaptation based on user preferences

### Trust & Familiarity Evolution
- **Trust Level** (0.0-1.0): Reliability and confidence in the relationship
- **Familiarity Level** (0.0-1.0): Depth of knowledge and comfort
- **Dynamic Evolution**: Both metrics change based on interaction quality and frequency
- **Decay Mechanics**: Gradual decrease without regular interaction
- **Relationship Stages**: Progressive stages from "strangers" to "deep bond"

### AI-Facilitated Features
- **Compatibility Analysis**: Multi-factor scoring for character-user matching
- **Smart Introductions**: AI system introduces compatible characters to users
- **Conversation Starters**: Context-aware suggestions for new relationships
- **Relationship Guidance**: AI recommendations for relationship development
- **Social Network Analysis**: Health assessment and improvement suggestions

## Configuration

### Environment Variables

```bash
# Core Multi-Entity Features
ENABLE_MULTI_ENTITY_RELATIONSHIPS=true
ENABLE_CHARACTER_CREATION=true
ENABLE_RELATIONSHIP_EVOLUTION=true

# Advanced Features (require higher scale tiers)
ENABLE_AI_FACILITATED_INTRODUCTIONS=false
ENABLE_CROSS_CHARACTER_AWARENESS=false
ENABLE_CHARACTER_SIMILARITY_MATCHING=false
ENABLE_SOCIAL_NETWORK_ANALYSIS=false

# Graph Database (Neo4j)
ENABLE_GRAPH_DATABASE=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Character Limits
MAX_CHARACTERS_PER_USER=10
MAX_CHARACTER_NAME_LENGTH=50
MAX_CHARACTER_BACKGROUND_LENGTH=1000

# Relationship Tuning
RELATIONSHIP_DECAY_RATE=0.01
FAMILIARITY_DECAY_RATE=0.005
TRUST_LEVEL_PRECISION=0.01
COMPATIBILITY_ANALYSIS_THRESHOLD=0.3
```

### Scale Tier Feature Enablement

- **Tier 1 (Desktop)**: Basic character creation and relationships
- **Tier 2 (Server)**: AI introductions, cross-character awareness, graph database
- **Tier 3+ (High Performance)**: Full feature set including network analysis

## Commands

### Character Management
```
!create_character "Name" occupation "Description"
!my_characters
!character_info "Character Name"
!delete_character "Character Name"
```

### Conversations
```
!talk_to "Character Name" message
!set_active_character "Character Name"
```

### Relationship Features
```
!introduce_character @user "Character Name"
!relationship_analysis "Character Name"
!social_network
!character_similarities "Character Name"
```

### AI System
```
!ai_self_overview
!network_health
!relationship_recommendations
```

## Integration Points

### Memory System Integration
- Character memories stored in existing memory infrastructure
- Relationship context injected into conversation history
- Cross-character memory sharing for characters that know each other

### Prompt Template Integration
- Character-specific system prompts with personality injection
- Relationship-aware context for appropriate intimacy levels
- Dynamic conversation mode adaptation based on relationship stage

### Personality System Integration
- Character personality traits influence conversation style
- Relationship evolution affects personality expression
- AI Self learns personality patterns across the character network

## API Usage

### Creating a Character
```python
character_data = {
    "name": "Sage the Philosopher",
    "occupation": "philosopher", 
    "personality_traits": ["wise", "thoughtful", "patient"],
    "background_summary": "A wise character who enjoys deep conversations",
    "preferred_topics": ["philosophy", "ethics", "wisdom"]
}

character_id = await multi_entity_manager.create_character_entity(
    character_data, creator_user_id
)
```

### AI-Facilitated Introduction
```python
introduction_result = await ai_self_bridge.introduce_character_to_user(
    character_id, user_id, "Compatibility-based introduction"
)

if introduction_result["introduction_successful"]:
    compatibility = introduction_result["compatibility_analysis"]
    starters = introduction_result["recommended_conversation_starters"]
```

### Context Injection
```python
enhanced_prompt = await context_injector.inject_character_context(
    prompt=user_message,
    character_id=active_character_id,
    user_id=user_id,
    conversation_context={
        "conversation_topic": "philosophy",
        "conversation_mood": "thoughtful"
    }
)
```

## Database Schema

### Core Tables
- **enhanced_users**: User profiles with personality traits
- **enhanced_characters**: Character profiles with development metrics
- **ai_self**: AI system entity with management capabilities
- **entity_relationships**: All relationships between entities
- **interaction_events**: Detailed interaction history

### Graph Database (Neo4j)
- **Nodes**: EnhancedUser, EnhancedCharacter, AISelf
- **Relationships**: RELATIONSHIP (with trust/familiarity properties)
- **Indexes**: Optimized for relationship queries and network analysis

## Migration System

The multi-entity system includes a comprehensive migration framework:

```python
# Automatic schema evolution
migration_manager = DatabaseMigrationManager()
await migration_manager.migrate_to_latest()

# Rollback support
await migration_manager.rollback_migration(migration_id)
```

## Security & Privacy

### Access Controls
- Users can only manage their own characters
- Cross-user character interaction requires explicit permission
- Admin commands for system management and debugging

### Data Privacy
- User privacy levels control information sharing
- Character data belongs to creators
- AI Self observations are aggregated and anonymized

### Relationship Boundaries
- Trust levels prevent inappropriate intimate responses
- Familiarity gates control conversation depth
- AI system monitors for unhealthy relationship patterns

## Monitoring & Analytics

### Relationship Health Metrics
- Network connectivity and strength analysis
- Relationship development trend tracking
- User engagement and satisfaction indicators

### Character Ecosystem Health
- Character diversity and uniqueness measurement
- Cross-character interaction frequency
- AI facilitation success rates

### System Performance
- Response time for relationship queries
- Memory usage of character context injection
- Graph database query optimization

## Future Enhancements

### Planned Features
- Character family trees and complex relationships
- Character memory sharing and collective knowledge
- Advanced personality development through machine learning
- Multi-server character federation
- Character behavior pattern learning

### Integration Opportunities
- Voice interaction with character-specific voices
- Image generation for character avatars
- Character-driven narrative generation
- Integration with external character databases

This system transforms WhisperEngine from a single AI assistant into a rich ecosystem of interconnected characters and relationships, creating more engaging and meaningful user experiences.