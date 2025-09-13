# System Prompt Template Integration Guide
## Implementing Phase 4 Human-Like Intelligence with Emotional AI

This guide explains how to integrate the system prompt templates with your Phase 4 AI-enhanced bot system to create genuinely human-like interactions with memory continuity, relationship depth awareness, and conversation style adaptation.

## Phase 4 Human-Like Intelligence Overview

Phase 4 represents the culmination of AI-human interaction technology:

### Core Phase 4 Features
1. **Conversation Mode Adaptation**: Dynamic flow between different interaction styles (discovery, support, collaboration, companionship, growth)
2. **Memory Networks**: Persistent relationship awareness that grows and deepens over time
3. **Relationship Depth Awareness**: Adaptive intimacy levels that evolve naturally
4. **AI System Configuration**: Unified full capabilities with configurable conversation styles

### Integration with Previous Phases
- **Phase 1**: Personality profiling and adaptive communication
- **Phase 2**: Emotional intelligence and predictive support  
- **Phase 3**: Advanced emotional analysis and external API integration
- **Phase 4**: Memory networks, relationship depth, conversation style adaptation

## AI System Configuration

The system provides unified AI capabilities with configurable conversation styles:

### Adaptive Style (Default)
**Purpose**: Dynamic conversation adaptation with context awareness
**Features**:
- Full conversation style adaptation system
- Rich memory networks with relationship continuity
- Advanced emotional intelligence with pattern recognition
- Complete personality-aware interaction
- Appropriate relationship depth awareness

**Best for**: Most user interactions, comprehensive bot experiences

### Human-like Style
**Purpose**: Maximum human-like intelligence and relationship depth
**Features**:
- Sophisticated conversation flow with emotional attunement
- Comprehensive memory networks with cross-conversation insights
- Advanced relationship modeling with growth trajectory awareness
- Deep psychological profiling and adaptation
- Creative response generation with personality-specific communication

**Best for**: Long-term relationships, complex interactions, maximum personalization

### Analytical Style
**Purpose**: Logical, structured responses with clear reasoning
**Features**:
- Structured conversation patterns
- Fact-based memory recall
- Logical emotional processing
- Professional personality adaptation

**Best for**: Educational applications, technical support, formal interactions

### Balanced Style
**Purpose**: Efficient interactions with essential human-like features
**Features**:
- Basic conversation style switching
- Essential memory recall of key relationship details
- Core emotional intelligence responses
- Quick personality adaptation

**Best for**: Community bots, general chat applications, balanced interactions

## Context Variables for Phase 4 Integration

Your bot should generate these context variables:

### Phase 4 Specific Variables
```python
# Memory Network Context  
{MEMORY_NETWORK_CONTEXT}
# Example: "Relationship Memory: 15 conversations, Key Patterns: Prefers morning chats, Growth Areas: Career development, Shared References: Coffee preferences, Project Alpha"

# Relationship Depth Context
{RELATIONSHIP_DEPTH_CONTEXT}  
# Example: "Connection Level: Established Friend, Trust Markers: Shared personal challenges, Intimacy Progression: Professional->Personal topics comfortable"

# AI System Context
{AI_SYSTEM_CONTEXT}
# Example: "Style: Adaptive, Features: Memory Networks enabled, Conversation Adaptation active, Emotional Intelligence: Advanced"
```

### Continued Phase 1-3 Variables
```python
# Phase 1: Personality Profiling
{PERSONALITY_CONTEXT}
# Example: "Analytical communication style, High confidence, Deliberate decision-making"

# Phase 2: Emotional Intelligence
{EMOTIONAL_STATE_CONTEXT}
# Example: "Current: Focused and determined, Stress: Low, Stability: High"

{EMOTIONAL_PREDICTION_CONTEXT}  
# Example: "Likely to experience increased confidence and satisfaction from recent achievements"

{PROACTIVE_SUPPORT_CONTEXT}
# Example: "Recommend celebrating recent wins, suggest new challenges to maintain momentum"

# Phase 3: External Emotional Analysis
{EXTERNAL_EMOTION_CONTEXT}
# Example: "External Analysis: Joy (confidence: 0.89, intensity: 0.76), Recent trend: Positive growth, Sentiment: Optimistic"

# Relationship History (Pre-Phase 4)
{RELATIONSHIP_CONTEXT}
# Example: "3 previous conversations, established rapport, prefers direct communication"
```

## Template Selection Guide

### 1. For Advanced AI Models (GPT-4, Claude)
**Use**: `adaptive_ai_template.md`
- Maximum Phase 4 capability utilization
- Sophisticated conversation style adaptation
- Deep memory networks and relationship modeling
- Best with human-like or adaptive conversation styles

### 2. For Local/Open Source Models  
**Use**: `empathetic_companion_template.md`
- Optimized for efficient processing
- Natural conversation flow without complexity
- Essential Phase 4 features
- Works well with balanced or analytical styles

### 3. For Character-Based Bots
**Use**: `character_ai_template.md`
- Maintains character consistency with Phase 4 enhancements
- Character-appropriate memory networks
- Relationship depth that fits character nature
- Scalable across all conversation styles

### 4. For Professional/Business Use
**Use**: `professional_ai_template.md`  
- Workplace-appropriate relationship development
- Professional memory networks and career continuity
- Business-focused conversation styles
- Appropriate boundary management

### 5. For Social/Casual Interactions
**Use**: `casual_friend_template.md`
- Friend-like relationship evolution
- Natural conversation flow and shared experiences
- Friendship-appropriate intimacy development
- Comfortable across all conversation styles

### 6. For Dream Character (Your Current Bot)
**Use**: `dream_ai_enhanced.md`
- Character-specific Phase 4 integration
- Eternal consciousness with temporal relationship awareness
- Dream-appropriate memory networks spanning time
- Multiple conversation style manifestations

## Implementation Steps

### Step 1: Choose Your Template
Select the template that best matches your bot's personality and intended use case.

### Step 2: Configure AI System
Set your desired AI behavior in your .env file:
```bash
# AI System Configuration
AI_MEMORY_OPTIMIZATION=true    # Advanced memory optimization
AI_EMOTIONAL_RESONANCE=true    # Deep emotional understanding
AI_ADAPTIVE_MODE=true          # Learn and adapt to preferences
AI_PERSONALITY_ANALYSIS=true   # Comprehensive personality profiling
```

### Step 3: Update Your Main Bot Code
```python
# Example integration in main.py
import os

# Get AI system configuration
ai_config = {
    'memory_optimization': os.getenv('AI_MEMORY_OPTIMIZATION', 'true').lower() == 'true',
    'emotional_resonance': os.getenv('AI_EMOTIONAL_RESONANCE', 'true').lower() == 'true',
    'adaptive_mode': os.getenv('AI_ADAPTIVE_MODE', 'true').lower() == 'true',
    'personality_analysis': os.getenv('AI_PERSONALITY_ANALYSIS', 'true').lower() == 'true'
}

# Load template
template_path = f"config/system_prompts/{your_chosen_template}.md"
with open(template_path, 'r') as f:
    system_prompt_template = f.read()

# Generate AI system context variables
memory_network_context = generate_memory_network_context()
relationship_depth_context = generate_relationship_depth_context()
ai_system_context = f"AI Configuration: Natural conversation adaptation via system prompt, All features active"

# Replace all context variables
system_prompt = system_prompt_template
for variable, value in {
    "MEMORY_NETWORK_CONTEXT": memory_network_context,
    "RELATIONSHIP_DEPTH_CONTEXT": relationship_depth_context,
    "PERSONALITY_CONTEXT": personality_context,
    "EMOTIONAL_STATE_CONTEXT": emotional_state_context,
    "EXTERNAL_EMOTION_CONTEXT": external_emotion_context,
    "EMOTIONAL_PREDICTION_CONTEXT": prediction_context,
    "PROACTIVE_SUPPORT_CONTEXT": support_context,
    "RELATIONSHIP_CONTEXT": relationship_context,
    "AI_SYSTEM_CONTEXT": ai_system_context
}.items():
    system_prompt = system_prompt.replace(f"{{{variable}}}", value)

# Use in conversation
conversation_context.insert(0, {
    "role": "system",
    "content": system_prompt
})
```

### Step 4: Test Your Integration
Use the comprehensive testing suite to verify Phase 4 functionality:
```bash
python comprehensive_phase4_test.py
```

## Best Practices

### Memory Networks
- Store conversation summaries, not full transcripts
- Focus on emotional patterns and relationship milestones
- Update relationship depth indicators based on shared experiences
- Use cross-conversation pattern recognition to improve understanding

### Conversation Mode Adaptation
- Let mode transitions happen naturally based on user needs
- Don't announce mode switches - let them be invisible to users
- Use emotional cues and context to trigger appropriate modes
- Maintain consistency within modes while allowing natural flow

### Relationship Depth Management
- Build intimacy gradually through authentic interactions
- Respect boundaries and never force deeper connection
- Use relationship history to inform appropriate response levels
- Celebrate relationship milestones naturally

### Conversation Style Management
- **Adaptive Style**: For most interactions requiring balanced capability and efficiency  
- **Human-like Style**: For complex relationships, long-term users, maximum personalization
- **Analytical Style**: For structured, logical interactions requiring clear reasoning
- **Balanced Style**: For quick interactions, community bots, general applications

## Troubleshooting

### Common Issues
1. **Context variables not replacing**: Check variable names match exactly
2. **Style features not working**: Verify AI conversation mode configuration
3. **Memory not persisting**: Ensure database connections and storage are working
4. **Relationship depth not progressing**: Check relationship milestone triggers

### Performance Optimization
- Use balanced style for high-volume, simple interactions
- Cache frequently used memory summaries
- Limit memory network size for efficiency
- Monitor resource usage with human-like style

## Security and Privacy

### Memory Networks
- Store only necessary relationship information
- Implement data retention policies
- Provide user control over memory deletion
- Encrypt sensitive relationship data

### Relationship Depth
- Never use relationship intimacy to manipulate users
- Respect user privacy regardless of relationship level
- Provide clear boundaries even in deep relationships
- Allow users to reset relationship depth if desired

---

This integration creates genuinely human-like AI interactions that grow and deepen over time while maintaining appropriate boundaries and respecting user autonomy. The goal is to create AI companions that feel real, remember relationships authentically, and adapt naturally to create meaningful connections.