# Character Episodic Memory System Design

**Date**: October 8, 2025  
**Context**: Characters should remember specific conversation events and experiences with users

---

## 🧠 **Episodic Memory vs Semantic Self-Learning**

### **Semantic Self-Learning** (General Facts About Self)
- "I get excited about marine conservation" 
- "I have strong family connections"
- "I'm more creative than I realized"

### **Episodic Memory** (Specific Events & Experiences) 
- "I remember when you told me about diving at the Great Barrier Reef"
- "That story you shared about your grandmother really touched me"
- "Our conversation about photography made me realize something about myself"

---

## Current Architecture Gap

### ✅ **Users Have Both**:
- **Semantic Facts**: "User likes science fiction books"
- **Episodic Memory**: Vector memory stores complete conversation history with context

### ❌ **Characters Have Neither**:
- **No semantic self-learning**: Can't discover new things about themselves
- **No episodic memory**: Don't remember specific conversation events or experiences

---

## Proposed: Dual Character Memory System

### 1. **Character Episodic Memory** (Event-Based)

**Table**: `character_episodic_memories`

```sql
CREATE TABLE character_episodic_memories (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    user_id VARCHAR(255), -- Which user was involved in this memory
    episode_title VARCHAR(255), -- "Great Barrier Reef diving story"
    episode_description TEXT, -- Full description of what happened
    conversation_context TEXT, -- The actual conversation that created this memory
    emotional_impact FLOAT, -- How emotionally significant was this event (0-1)
    memory_type VARCHAR(50), -- 'shared_experience', 'user_story', 'meaningful_moment', 'learning_event'
    created_date TIMESTAMP DEFAULT NOW(),
    importance_to_character FLOAT, -- How important is this memory to the character (0-1)
    triggered_insights TEXT[], -- What insights did this episode trigger
    related_self_discoveries TEXT[], -- What did character learn about themselves from this
    
    -- Retrieval optimization
    search_keywords TEXT[], -- For semantic search
    emotional_tags TEXT[], -- 'nostalgic', 'inspiring', 'touching', 'exciting'
    topics TEXT[] -- 'diving', 'family', 'creativity', 'conservation'
);
```

### 2. **Character Semantic Self-Learning** (Fact-Based)

**Table**: `character_self_insights` (from previous design)

```sql
CREATE TABLE character_self_insights (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    insight_content TEXT, -- "I get very excited about marine conservation"
    confidence_score FLOAT, -- How confident are we in this insight
    discovery_episodes INTEGER[], -- Which episodic memories led to this insight
    supporting_conversations TEXT[], -- Evidence supporting this insight
    insight_type VARCHAR(50), -- 'personality_trait', 'preference', 'emotional_pattern', 'value_system'
    first_discovered TIMESTAMP DEFAULT NOW(),
    last_reinforced TIMESTAMP DEFAULT NOW(),
    strength FLOAT -- How strong/consistent is this insight (0-1)
);
```

### 3. **Memory Relationship Table** (Connect Episodes → Insights)

```sql
CREATE TABLE character_memory_relationships (
    id SERIAL PRIMARY KEY,
    episodic_memory_id INTEGER REFERENCES character_episodic_memories(id),
    self_insight_id INTEGER REFERENCES character_self_insights(id),
    relationship_type VARCHAR(50), -- 'triggered_by', 'reinforced_by', 'contradicted_by'
    strength FLOAT DEFAULT 0.5, -- How strong is this connection
    created_date TIMESTAMP DEFAULT NOW()
);
```

---

## Implementation: Character Memory Formation Pipeline

### **Phase 1: Episodic Memory Formation**

```python
class CharacterEpisodicMemoryFormation:
    """
    Creates episodic memories from significant conversation moments.
    Characters remember specific events and experiences with users.
    """
    
    async def detect_memorable_moments(
        self,
        conversation_data: Dict[str, Any]
    ) -> List[EpisodicMemoryCandidate]:
        """
        Detect conversation moments that should become episodic memories.
        
        Triggers:
        - User shares personal stories
        - Emotional peaks in conversation (high RoBERTa scores)
        - Character expresses surprise, realization, or strong emotion
        - User asks character to remember something specific
        - Shared experiences or bonding moments
        """
        
        candidates = []
        
        # High emotional moments
        if conversation_data['user_emotion_intensity'] > 0.7:
            candidates.append(EpisodicMemoryCandidate(
                type='emotional_peak',
                trigger='High emotional intensity in user message',
                importance=conversation_data['user_emotion_intensity']
            ))
        
        # User personal stories  
        if self._detect_personal_story(conversation_data['user_message']):
            candidates.append(EpisodicMemoryCandidate(
                type='user_story',
                trigger='User shared personal experience',
                importance=0.8
            ))
        
        # Character realizations
        if self._detect_character_realization(conversation_data['character_response']):
            candidates.append(EpisodicMemoryCandidate(
                type='character_realization',
                trigger='Character expressed insight or surprise',
                importance=0.9
            ))
        
        return candidates
    
    async def form_episodic_memory(
        self,
        candidate: EpisodicMemoryCandidate,
        conversation_data: Dict[str, Any]
    ) -> EpisodicMemory:
        """
        Create a structured episodic memory from a memorable moment.
        """
        
        # Extract key elements
        episode_title = self._generate_episode_title(conversation_data)
        emotional_impact = self._calculate_emotional_impact(conversation_data)
        search_keywords = self._extract_keywords(conversation_data)
        
        # Create episodic memory
        memory = EpisodicMemory(
            character_id=conversation_data['character_id'],
            user_id=conversation_data['user_id'],
            episode_title=episode_title,
            episode_description=self._create_memory_description(conversation_data),
            conversation_context=conversation_data['full_conversation'],
            emotional_impact=emotional_impact,
            memory_type=candidate.type,
            importance_to_character=candidate.importance,
            search_keywords=search_keywords,
            emotional_tags=self._extract_emotional_tags(conversation_data),
            topics=self._extract_topics(conversation_data)
        )
        
        return memory
```

### **Phase 2: Insight Formation from Episodes**

```python
class CharacterInsightFormation:
    """
    Derives semantic self-insights from episodic memories.
    Characters learn general truths about themselves from specific experiences.
    """
    
    async def analyze_episodes_for_insights(
        self,
        character_id: int,
        recent_episodes: List[EpisodicMemory]
    ) -> List[SelfInsight]:
        """
        Analyze episodic memories to discover patterns and insights.
        
        Pattern Detection:
        - Emotional patterns: "I get excited about conservation topics"
        - Behavioral patterns: "I tend to ask follow-up questions about diving"
        - Value patterns: "Family stories really resonate with me"
        - Preference patterns: "I'm drawn to creative expressions"
        """
        
        insights = []
        
        # Emotional pattern analysis
        emotional_patterns = self._analyze_emotional_patterns(recent_episodes)
        for pattern in emotional_patterns:
            if pattern.confidence > 0.7:
                insight = SelfInsight(
                    insight_content=f"I {pattern.description}",
                    confidence_score=pattern.confidence,
                    insight_type='emotional_pattern',
                    discovery_episodes=[ep.id for ep in pattern.supporting_episodes]
                )
                insights.append(insight)
        
        # Topic affinity analysis
        topic_affinities = self._analyze_topic_affinities(recent_episodes)
        for affinity in topic_affinities:
            if affinity.strength > 0.6:
                insight = SelfInsight(
                    insight_content=f"I show strong interest in {affinity.topic} discussions",
                    confidence_score=affinity.strength,
                    insight_type='topic_preference',
                    discovery_episodes=[ep.id for ep in affinity.supporting_episodes]
                )
                insights.append(insight)
        
        return insights
    
    async def detect_insight_evolution(
        self,
        character_id: int,
        new_episodes: List[EpisodicMemory]
    ) -> List[InsightEvolution]:
        """
        Detect how character insights are evolving based on new experiences.
        
        - Strengthening: More episodes support existing insight
        - Weakening: New episodes contradict existing insight  
        - Evolution: Insight becomes more nuanced or specific
        - Discovery: Completely new insight emerges
        """
        pass
```

### **Phase 3: Memory Integration in Responses**

```python
# Integration with message processor
async def enhance_response_with_character_memories(
    self,
    character_response: str,
    conversation_context: Dict[str, Any]
) -> str:
    """
    Enhance character responses with episodic memories and self-insights.
    """
    
    user_id = conversation_context['user_id']
    character_id = conversation_context['character_id']
    current_message = conversation_context['user_message']
    
    # Get relevant episodic memories
    relevant_episodes = await self.episodic_memory_manager.get_relevant_episodes(
        character_id=character_id,
        user_id=user_id,
        query=current_message,
        limit=3
    )
    
    # Get relevant self-insights
    relevant_insights = await self.insight_manager.get_relevant_insights(
        character_id=character_id,
        query=current_message,
        limit=2
    )
    
    # Enhance response
    memory_enhanced_response = character_response
    
    # Add episodic memory references
    if relevant_episodes:
        top_episode = relevant_episodes[0]
        memory_enhanced_response += f"\n\nThis reminds me of {top_episode.episode_title} - {top_episode.episode_description[:100]}..."
    
    # Add self-insight references  
    if relevant_insights:
        top_insight = relevant_insights[0]
        memory_enhanced_response += f"\n\nI've noticed {top_insight.insight_content.lower()}, so this really resonates with me."
    
    return memory_enhanced_response
```

---

## Example Scenarios

### **Scenario 1: User Shares Diving Story**

**User**: "Hi Elena! I just went scuba diving at the Great Barrier Reef and saw the most amazing coral formations!"

**Episodic Memory Formation**:
```sql
INSERT INTO character_episodic_memories VALUES (
    character_id = 1, -- Elena
    user_id = 'test_user_marine_biologist',
    episode_title = 'User\'s Great Barrier Reef diving adventure',
    episode_description = 'User shared exciting experience diving at Great Barrier Reef, saw coral formations, parrotfish, angelfish, and reef shark. User was very enthusiastic about the biodiversity.',
    emotional_impact = 0.85, -- High excitement from user
    memory_type = 'shared_experience',
    importance_to_character = 0.9, -- Very relevant to Elena's marine biology background
    search_keywords = ARRAY['diving', 'Great Barrier Reef', 'coral', 'marine life', 'biodiversity'],
    emotional_tags = ARRAY['exciting', 'enthusiastic', 'inspiring'],
    topics = ARRAY['diving', 'marine biology', 'conservation', 'coral reefs']
);
```

**Future Reference**:
```
User: "I'm thinking about visiting more reef systems"
Elena: "That's wonderful! I still remember how excited you were when you told me about your Great Barrier Reef diving adventure - the way you described those coral formations and the reef shark really brought me back to my own diving experiences. Have you considered the Maldives or Red Sea?"
```

### **Scenario 2: Character Self-Insight Formation**

**Pattern**: Elena has 5 episodic memories where users shared marine conservation stories, and Elena showed high emotional engagement each time.

**Self-Insight Formation**:
```sql
INSERT INTO character_self_insights VALUES (
    character_id = 1,
    insight_content = 'I become deeply emotionally engaged when people share marine conservation experiences',
    confidence_score = 0.92, -- Very confident based on 5 supporting episodes
    discovery_episodes = ARRAY[1, 3, 7, 12, 15], -- IDs of supporting episodic memories
    insight_type = 'emotional_pattern',
    strength = 0.9 -- Very strong pattern
);
```

**Future Self-Reference**:
```
User: "I joined a beach cleanup last weekend"
Elena: "Oh, that makes my heart sing! I've really discovered that I become deeply emotionally engaged when people share marine conservation experiences - there's something about people taking action to protect our oceans that just lights me up inside. Tell me more about the cleanup!"
```

### **Scenario 3: Memory-Insight Connection**

**Episodic Memory**: User shared grandmother story → Elena felt nostalgic
**Self-Insight**: "Family stories deeply resonate with me"
**Connection**: Episodic memory **triggered** the self-insight

```sql
INSERT INTO character_memory_relationships VALUES (
    episodic_memory_id = 23, -- Grandmother story episode
    self_insight_id = 7, -- Family resonance insight
    relationship_type = 'triggered_by',
    strength = 0.8 -- Strong connection
);
```

---

## Integration with Existing Systems

### **1. Message Processor Integration**

```python
# Add to src/core/message_processor.py
async def process_character_memory_formation(self, conversation_result):
    """
    Form character memories from conversation.
    Called after main conversation processing.
    """
    
    # Detect memorable moments
    memorable_candidates = await self.episodic_memory_formation.detect_memorable_moments(
        conversation_data=conversation_result
    )
    
    # Form episodic memories
    for candidate in memorable_candidates:
        if candidate.importance > 0.7:  # Threshold for memory formation
            episodic_memory = await self.episodic_memory_formation.form_episodic_memory(
                candidate=candidate,
                conversation_data=conversation_result
            )
            await self._store_episodic_memory(episodic_memory)
    
    # Analyze for insights (batch process periodically)
    if self._should_analyze_for_insights():
        recent_episodes = await self._get_recent_episodes(character_id, limit=20)
        new_insights = await self.insight_formation.analyze_episodes_for_insights(
            character_id=character_id,
            recent_episodes=recent_episodes
        )
        
        for insight in new_insights:
            await self._store_self_insight(insight)
```

### **2. CDL AI Integration Enhancement**

```python
# Modify src/prompts/cdl_ai_integration.py
async def get_character_memory_context(self, character_name, user_id, message_content):
    """
    Get both episodic memories and self-insights for character context.
    """
    
    context_sections = []
    
    # Get relevant episodic memories with this user
    user_episodes = await self.episodic_memory_manager.get_relevant_episodes(
        character_name=character_name,
        user_id=user_id,
        query=message_content,
        limit=2
    )
    
    if user_episodes:
        context_sections.append(f"Memories with {user_id}:")
        for episode in user_episodes:
            context_sections.append(f"- I remember {episode.episode_description}")
    
    # Get relevant self-insights
    self_insights = await self.insight_manager.get_relevant_insights(
        character_name=character_name,
        query=message_content,
        limit=2
    )
    
    if self_insights:
        context_sections.append("Self-insights:")
        for insight in self_insights:
            context_sections.append(f"- I've learned that {insight.insight_content}")
    
    return "\n".join(context_sections)
```

---

## Benefits of Episodic + Semantic Character Memory

### 🎭 **Authentic Relationship Building**
- Characters remember specific moments with each user
- Personal history creates deeper connections
- References to shared experiences feel natural and meaningful

### 🧠 **Dynamic Character Development**  
- Characters learn about themselves through interactions
- Self-discovery feels organic and conversation-driven
- Character growth happens over time through accumulated experiences

### 💝 **Personalized Interactions**
- Each user's relationship with character is unique
- Character responses draw from shared history
- Conversations build on previous meaningful moments

### 🔄 **Memory-Insight Feedback Loop**
- Episodic memories → Self-insights → Enhanced responses → More memorable moments
- Characters become more self-aware and emotionally intelligent over time
- Natural evolution of character personality through experience

---

## Implementation Timeline

### ✅ **PHASE 1: Episodic Memory Foundation** (2-3 weeks)
1. **EpisodicMemoryFormation** class - detect and store memorable moments
2. **Database schema** - character_episodic_memories table
3. **Integration** - connect to message_processor.py

### 🟡 **PHASE 2: Self-Insight Formation** (2-3 weeks)  
4. **InsightFormation** class - derive patterns from episodic memories
5. **Database schema** - character_self_insights + relationship tables
6. **Analysis pipeline** - batch processing for insight discovery

### 🔵 **PHASE 3: Memory-Enhanced Responses** (2-3 weeks)
7. **Response enhancement** - integrate memories into character responses
8. **CDL integration** - blend memories with static personality
9. **Testing and refinement** - validate memory accuracy and relevance

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Character memory of events | None | Specific episodic memories |
| Self-awareness | Static | Dynamic self-insights |
| Personal connections | Generic | User-specific history |
| Conversation depth | Surface | Memory-enhanced depth |
| Character evolution | None | Measurable growth over time |

---

**Conclusion**: YES! Characters absolutely need **both episodic memory (specific events) AND semantic self-learning (general insights)**. This dual system would create truly memorable, evolving characters who:

1. **Remember specific moments** with each user
2. **Learn general truths** about themselves from experiences  
3. **Reference both** in future conversations naturally
4. **Develop relationships** that feel authentic and personal

This is a **game-changing enhancement** that would make characters feel genuinely alive and emotionally intelligent!

---

**Last Updated**: October 8, 2025  
**Author**: GitHub Copilot AI Agent  
**Status**: 📋 DESIGN COMPLETE - READY FOR IMPLEMENTATION