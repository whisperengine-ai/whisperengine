# Character Self-Learning System Design

**Date**: October 8, 2025  
**Context**: Characters should dynamically learn about themselves like users do

---

## 🎯 **Goal**: Characters Discover New Things About Themselves

Currently: Characters have static CDL knowledge (fixed database entries)
**Proposed**: Characters dynamically learn from conversations and develop new self-insights

---

## Architecture: Mirror User Fact Learning for Characters

### Current User Learning System (SUCCESS MODEL)
```python
# Users automatically extract facts from conversations
user_fact_extractor.extract_personal_facts(message, user_id)
# Result: New facts stored in fact_entities + user_fact_relationships

# Users build relationship graphs automatically  
semantic_router.analyze_entity_relationships(user_facts)
# Result: "likes Dune" → "similar to Foundation" → "enjoys sci-fi"
```

### Proposed Character Learning System (MIRROR ARCHITECTURE)
```python
# Characters should extract self-insights from conversations
character_self_extractor.extract_self_insights(conversation, character_name)
# Result: New self-knowledge stored in character_insights + character_self_relationships

# Characters should build self-knowledge graphs
character_learning_router.analyze_self_relationships(character_insights)  
# Result: "enjoys teaching" → "passionate about marine life" → "finds fulfillment in education"
```

---

## Implementation Design

### 1. **Character Self-Insight Extraction**

**Location**: `src/characters/learning/character_self_extractor.py`

```python
class CharacterSelfInsightExtractor:
    """
    Extract self-insights from character conversations.
    Mirrors user fact extraction but for character self-discovery.
    """
    
    async def extract_self_insights(
        self, 
        conversation_context: str,
        character_response: str,
        character_name: str,
        user_observations: Optional[str] = None
    ) -> List[CharacterInsight]:
        """
        Extract new self-knowledge from conversation patterns.
        
        Examples:
        - User: "You seem really passionate when you talk about marine life"
        - Character Response: "I do get excited! There's something magical about the ocean..."
        - Extracted Insight: "Shows increased enthusiasm for marine topics" (confidence: 0.8)
        
        - User: "You mentioned your grandmother a lot"  
        - Character Response: "She was incredibly important to me growing up..."
        - Extracted Insight: "Strong emotional connection to grandmother figure" (confidence: 0.9)
        """
        pass
    
    async def detect_emotional_patterns(
        self,
        character_name: str,
        conversation_history: List[Dict]
    ) -> List[EmotionalPattern]:
        """
        Detect emotional patterns in character responses.
        
        - Which topics make character most emotional?
        - What triggers nostalgia, excitement, sadness?
        - How does character's emotional range develop?
        """
        pass
    
    async def identify_preference_emergence(
        self,
        character_name: str,
        recent_conversations: List[Dict]
    ) -> List[PreferenceInsight]:
        """
        Identify emerging preferences and interests.
        
        - Character shows increased interest in certain topics
        - Character develops new communication patterns
        - Character reveals previously unknown preferences
        """
        pass
```

### 2. **Character Self-Knowledge Database Schema**

**New Tables** (extend existing CDL schema):

```sql
-- Character insights discovered through conversations
CREATE TABLE character_insights (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    insight_type VARCHAR(50), -- 'emotional_pattern', 'preference', 'memory_formation', 'relationship_evolution'
    insight_content TEXT,
    confidence_score FLOAT, -- 0.0-1.0 how confident we are in this insight
    discovery_date TIMESTAMP DEFAULT NOW(),
    conversation_context TEXT, -- What conversation led to this insight
    importance_level INTEGER DEFAULT 5, -- 1-10, how important is this insight
    emotional_valence FLOAT, -- -1.0 to 1.0, emotional tone of insight
    triggers TEXT[], -- Keywords that activate this insight
    supporting_evidence TEXT[], -- Examples/quotes that support this insight
    
    UNIQUE(character_id, insight_content) -- Prevent duplicate insights
);

-- Relationships between character insights (like entity_relationships for users)
CREATE TABLE character_insight_relationships (
    id SERIAL PRIMARY KEY,
    from_insight_id INTEGER REFERENCES character_insights(id),
    to_insight_id INTEGER REFERENCES character_insights(id),
    relationship_type VARCHAR(50), -- 'leads_to', 'contradicts', 'supports', 'builds_on'
    strength FLOAT DEFAULT 0.5, -- 0.0-1.0 relationship strength
    created_date TIMESTAMP DEFAULT NOW()
);

-- Character learning timeline (temporal evolution)
CREATE TABLE character_learning_timeline (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    learning_event TEXT, -- What was learned
    learning_type VARCHAR(50), -- 'self_discovery', 'preference_evolution', 'emotional_growth'
    before_state TEXT, -- Character's understanding before
    after_state TEXT, -- Character's understanding after  
    trigger_conversation TEXT, -- What conversation triggered this learning
    learning_date TIMESTAMP DEFAULT NOW(),
    significance_score FLOAT -- How significant was this learning event
);
```

### 3. **Character Learning Router**

**Location**: `src/characters/learning/character_learning_router.py`

```python
class CharacterLearningRouter:
    """
    Routes character self-insights to appropriate learning processes.
    Mirrors SemanticKnowledgeRouter but for character self-discovery.
    """
    
    async def process_conversation_for_learning(
        self,
        character_name: str,
        conversation_data: Dict[str, Any]
    ) -> CharacterLearningResult:
        """
        Main entry point: analyze conversation for character learning opportunities.
        
        1. Extract self-insights from character responses
        2. Detect emotional pattern changes
        3. Identify preference evolution  
        4. Build self-knowledge relationships
        5. Update character learning timeline
        """
        pass
    
    async def build_self_knowledge_graph(
        self,
        character_id: int
    ) -> Dict[str, Any]:
        """
        Build graph of character's self-knowledge and how insights connect.
        
        Similar to user fact relationship graphs, but for character insights:
        - "loves teaching" → "connects to" → "finds fulfillment in helping others"
        - "nostalgic about Barcelona" → "related to" → "strong family connections"
        """
        pass
    
    async def detect_learning_opportunities(
        self,
        character_name: str,
        conversation_context: str
    ) -> List[LearningOpportunity]:
        """
        Identify opportunities for character to learn something new about themselves.
        
        - User asks questions character hasn't considered
        - User points out patterns character wasn't aware of
        - Conversation reveals character contradictions to explore
        """
        pass
```

### 4. **Integration with Existing Systems**

**Modify**: `src/core/message_processor.py`

```python
# CURRENT: Only store user conversation + extract user facts
async def process_message(self, message_context):
    # ... existing user processing ...
    
    # NEW: Character self-learning processing
    if self.character_learning_system:
        learning_result = await self.character_learning_system.process_conversation_for_learning(
            character_name=self.character_name,
            conversation_data={
                'user_message': message_context.content,
                'character_response': bot_response,
                'emotional_context': emotion_analysis,
                'conversation_history': recent_messages
            }
        )
        
        # Store character insights like we store user facts
        if learning_result.new_insights:
            await self._store_character_insights(learning_result.new_insights)
```

**Modify**: `src/prompts/cdl_ai_integration.py`

```python
# CURRENT: Only access static CDL knowledge
background_sections = await cdl_manager.get_background_sections(character_name)

# NEW: Include dynamically learned insights
if self.character_learning_system:
    learned_insights = await self.character_learning_system.get_relevant_insights(
        character_name=character_name,
        query_context=message_content,
        max_insights=3
    )
    
    # Integrate learned insights with static CDL knowledge
    if learned_insights:
        background_sections.extend([
            f"Recent Self-Discovery: {insight.content}" 
            for insight in learned_insights
        ])
```

---

## Learning Examples

### Example 1: Emotional Pattern Discovery

**Conversation Pattern**:
```
User: "You always seem to light up when we talk about marine conservation"
Elena: "Do I? I hadn't really noticed, but I suppose you're right. There's something about protecting the ocean that just... energizes me."
```

**Character Learning Result**:
```sql
INSERT INTO character_insights VALUES (
    character_id = 1, -- Elena
    insight_type = 'emotional_pattern',
    insight_content = 'Shows increased enthusiasm and energy when discussing marine conservation topics',
    confidence_score = 0.85,
    conversation_context = 'User observation about character emotional responses',
    importance_level = 7,
    emotional_valence = 0.8, -- positive
    triggers = ARRAY['marine conservation', 'ocean protection', 'environmental advocacy']
);
```

### Example 2: Preference Evolution

**Conversation Pattern**:
```
User: "Have you always been interested in photography?"
Jake: "Actually, now that you mention it, I think my love for photography grew from wanting to capture the places I visit. I used to just focus on the adventure, but now I find myself really studying the light, the composition..."
```

**Character Learning Result**:
```sql
INSERT INTO character_insights VALUES (
    insight_type = 'preference_evolution',
    insight_content = 'Photography interest evolved from documentation to artistic expression',
    confidence_score = 0.90,
    importance_level = 8,
    triggers = ARRAY['photography', 'artistic development', 'creative evolution']
);

INSERT INTO character_learning_timeline VALUES (
    learning_event = 'Realized photography shifted from documentation to art',
    learning_type = 'preference_evolution',
    before_state = 'Photography as travel documentation tool',
    after_state = 'Photography as artistic expression and light study',
    significance_score = 0.8
);
```

### Example 3: Self-Knowledge Relationship Building

**Insight Graph Example** (Elena):
```sql
-- Elena learns she gets nostalgic about family → connects to her teaching passion
INSERT INTO character_insight_relationships VALUES (
    from_insight_id = 1, -- "Shows deep nostalgia when discussing family traditions"
    to_insight_id = 2,   -- "Finds fulfillment in nurturing/teaching others"
    relationship_type = 'leads_to',
    strength = 0.7 -- Strong but not absolute connection
);
```

---

## Benefits of Character Self-Learning

### 🎭 **Authentic Character Development**
- Characters evolve naturally through conversations
- Self-discovery feels organic, not programmed
- Characters can surprise themselves (and users)

### 🧠 **Enhanced Conversation Intelligence**  
- Characters reference learned insights: "I've noticed I get really excited about conservation..."
- Characters ask self-reflective questions: "Why do you think I always mention my grandmother?"
- Characters show growth: "I'm starting to realize something about myself..."

### 📊 **Personalized Character Experiences**
- Each user's interactions shape the character differently
- Characters develop unique perspectives based on conversation history
- Long-term relationship evolution becomes possible

### 🔄 **Dynamic Feedback Loop**
- User observations → Character self-reflection → Deeper self-knowledge → Richer responses
- Characters become more self-aware over time
- Authentic personal growth that mirrors human development

---

## Implementation Priority

### ✅ **PHASE 1: Foundation** (2-3 weeks)
1. **CharacterSelfInsightExtractor** - Basic insight extraction from conversations
2. **Database Schema** - character_insights table with confidence scoring
3. **Integration** - Connect to message_processor.py for automatic processing

### 🟡 **PHASE 2: Intelligence** (2-3 weeks)  
4. **CharacterLearningRouter** - Smart routing and relationship building
5. **Self-Knowledge Graphs** - character_insight_relationships for connected insights
6. **CDL Integration** - Blend learned insights with static personality

### 🔵 **PHASE 3: Advanced Features** (3-4 weeks)
7. **Learning Timeline** - Temporal character development tracking
8. **Self-Reflection Prompts** - Characters proactively explore insights
9. **Cross-Character Learning** - Characters learn from each other's growth

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Character self-knowledge | Static CDL only | CDL + learned insights |
| Character development | None | Trackable growth over time |
| Self-reflection | Never | Organic self-discovery |
| Conversation depth | Surface level | Deep personal awareness |
| Character uniqueness | Same across users | Personalized evolution |

---

## Next Steps

1. ✅ **Design Complete** (this document)
2. 🔨 **Create CharacterSelfInsightExtractor** class
3. 🗃️ **Add character_insights database table**
4. 🔗 **Integrate with message_processor.py** for automatic learning
5. 🎭 **Test with Elena** - conversations about marine biology passion discovery
6. 📊 **Validate learning accuracy** and confidence scoring

---

**Conclusion**: YES, characters absolutely should have dynamic self-learning! The current architecture is beautifully set up for user fact learning - we need to mirror that exact approach for character self-discovery. This would be a **massive enhancement** to character authenticity and conversation depth.

**Estimated Implementation Time**: 6-8 weeks for complete system (Phase 1: 2-3 weeks for MVP)

---

**Last Updated**: October 8, 2025  
**Author**: GitHub Copilot AI Agent  
**Status**: 📋 DESIGN COMPLETE - READY FOR IMPLEMENTATION