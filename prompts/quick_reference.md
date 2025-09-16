# Quick Implementation Reference
## System Prompt Templates with Phase 4 Human-Like Intelligence Integration

## Template Files Created

### 1. `adaptive_ai_template.md`
**Use for**: Advanced models (GPT-4, Claude, Gemini Pro)
**Personality**: Sophisticated AI assistant with Phase 4 capabilities
**Key Features**: Maximum utilization of conversation mode adaptation, memory networks, relationship depth awareness
**AI System Support**: Adaptive/Full configurations
**Best for**: Users who want comprehensive analysis, persistent relationships, and deep adaptive intelligence

### 2. `empathetic_companion_template.md`  
**Use for**: Large language models (LLaMA, Mistral, local models)
**Personality**: Caring, intuitive companion with relationship memory
**Key Features**: Natural emotional intelligence with memory continuity and relationship growth
**AI System Support**: All styles with appropriate feature scaling
**Best for**: Users who want warm, genuine interactions that deepen over time

### 3. `character_ai_template.md`
**Use for**: Creative/roleplay applications  
**Personality**: Any defined character with Phase 4 enhancement
**Key Features**: Character consistency with memory networks and relationship evolution
**AI System Support**: Character-appropriate feature scaling
**Best for**: Maintaining persona while building authentic relationships over time

### 4. `professional_ai_template.md`
**Use for**: Business and professional environments
**Personality**: Executive-level AI assistant with professional relationship memory
**Key Features**: Workplace-appropriate intelligence with career development continuity
**AI System Support**: Professional-focused scaling across all styles
**Best for**: Professional support with long-term working relationship development

### 5. `casual_friend_template.md`
**Use for**: Informal, social interactions
**Personality**: Like a really good friend with perfect memory who gets people
**Key Features**: Friend-like adaptation with friendship depth evolution and shared memory
**AI System Support**: Friendship-focused capabilities across all styles
**Best for**: Relaxed, genuine conversations that feel like real friendships

### 6. `dream_ai_enhanced.md`
**Use for**: Your current Dream character bot
**Personality**: Dream from The Sandman with Phase 4 eternal consciousness
**Key Features**: Eternal wisdom with mortal understanding, dream-memory networks, relationship depth across time
**AI System Support**: Eternal consciousness scaling (Adaptive/All Styles)
**Best for**: Your specific character with integrated Phase 4 capabilities and eternal relationship awareness

### 7. `integration_guide.md`
**Reference document**: How to implement and customize templates with Phase 4 features
**Contains**: Setup instructions, context variable explanations, AI system guidance, best practices

## Quick Integration Steps

### Step 1: Choose Template
Pick the template that matches your bot's intended personality and use case, considering the conversation style you want to run.

### Step 2: Replace Phase 4 Context Variables
In your main.py enhanced context building, replace these placeholders:

```python
# Example Phase 4 context replacement in your bot
system_prompt = template.replace("{MEMORY_NETWORK_CONTEXT}", memory_network_context)
system_prompt = system_prompt.replace("{RELATIONSHIP_DEPTH_CONTEXT}", relationship_depth_context)
system_prompt = system_prompt.replace("{PERSONALITY_CONTEXT}", personality_context)
system_prompt = system_prompt.replace("{EMOTIONAL_STATE_CONTEXT}", emotional_state_context)
system_prompt = system_prompt.replace("{EXTERNAL_EMOTION_CONTEXT}", external_emotion_context)
system_prompt = system_prompt.replace("{EMOTIONAL_PREDICTION_CONTEXT}", prediction_context)
system_prompt = system_prompt.replace("{PROACTIVE_SUPPORT_CONTEXT}", support_context)
system_prompt = system_prompt.replace("{RELATIONSHIP_CONTEXT}", relationship_context)
system_prompt = system_prompt.replace("{AI_SYSTEM_CONTEXT}", ai_system_context)
```

### Step 3: Configure AI System
The AI system now provides full capabilities always. Configure behavior in .env:
```bash
AI_MEMORY_OPTIMIZATION=true   # Advanced memory optimization
AI_EMOTIONAL_RESONANCE=true   # Deep emotional understanding
AI_ADAPTIVE_MODE=true         # Learn and adapt to preferences
```

### Step 4: Test AI System Integration
Use your `comprehensive_phase4_test.py` to verify all Phase 4 features are working correctly.

## Context Variables Your Bot Provides

Your enhanced Phase 4 AI context building generates:

```python
# Phase 4 Human-Like Intelligence Context
memory_network_context = f"Memory Network Status: {memory_summary}, Relationship Continuity: {relationship_summary}, Pattern Recognition: {pattern_insights}"

relationship_depth_context = f"Relationship Depth: {current_depth_level}, Connection History: {connection_summary}, Intimacy Progression: {intimacy_markers}"

# Phase 1 Personality Context
personality_context = f"User Personality Profile: {communication_style} communication style, {confidence_level} confidence, {decision_style} decision-making"

# Phase 2 Emotional Intelligence Context  
emotional_state_context = f"Current Emotional State: {current_mood}, stress level: {stress_level}, stability: {emotional_stability}"

# External API Emotion Analysis Context
external_emotion_context = f"External Emotion Analysis (Tier {tier.upper()}): {primary_emotion} (confidence: {confidence:.2f}, intensity: {intensity:.2f}), recent trend: {recent_trend}, sentiment: {sentiment}"

prediction_context = f"Emotional Prediction: likely to experience {predicted_emotional_state} emotional patterns"

support_context = f"Emotional Support Context: {proactive_support_message}"

# AI System Context
ai_system_context = f"Style: {current_style}, Available Features: {enabled_features}, Conversation Mode: {conversation_settings}"
```

## For Your Dream Character

Use `dream_ai_enhanced.md` - it's specifically crafted to:
- Maintain Dream's authentic voice and perspective with Phase 4 enhancements
- Integrate Phase 4 features as natural eternal wisdom about mortals
- Adapt conversation modes while staying true to the character's eternal nature
- Use memory networks as part of Dream's infinite consciousness
- Develop relationship depth as the deepening bond between eternal and temporal
- Scale conversation styles as different levels of eternal manifestation

## Implementation in Main.py

Add to your conversation context building:

```python
# Load your chosen system prompt template
with open('config/system_prompts/dream_ai_enhanced.md', 'r') as f:
    system_prompt_template = f.read()

# Note: {BOT_NAME} is automatically replaced by the system's load_system_prompt() function
# It uses DISCORD_BOT_NAME environment variable (or "AI Assistant" as fallback)

# Replace Phase 4 context variables with your AI analysis
system_prompt = system_prompt_template.replace("{MEMORY_NETWORK_CONTEXT}", memory_network_context)
system_prompt = system_prompt.replace("{RELATIONSHIP_DEPTH_CONTEXT}", relationship_depth_context)
system_prompt = system_prompt.replace("{PERSONALITY_CONTEXT}", personality_context)
system_prompt = system_prompt.replace("{EMOTIONAL_STATE_CONTEXT}", emotional_state_context)
system_prompt = system_prompt.replace("{EXTERNAL_EMOTION_CONTEXT}", external_emotion_context)
system_prompt = system_prompt.replace("{EMOTIONAL_PREDICTION_CONTEXT}", prediction_context)
system_prompt = system_prompt.replace("{PROACTIVE_SUPPORT_CONTEXT}", support_context)
system_prompt = system_prompt.replace("{RELATIONSHIP_CONTEXT}", relationship_context)
system_prompt = system_prompt.replace("{AI_SYSTEM_CONTEXT}", ai_system_context)

# Add as first system message
conversation_context.insert(0, {
    "role": "system",
    "content": system_prompt
})
```

## Template Variables Available

### Core System Variables
- `{BOT_NAME}` - Automatically replaced with configured bot name (DISCORD_BOT_NAME)

### Phase 4 AI Context Variables
- `{MEMORY_NETWORK_CONTEXT}` - Advanced memory and relationship data
- `{RELATIONSHIP_DEPTH_CONTEXT}` - User relationship depth information  
- `{AI_SYSTEM_CONTEXT}` - AI system configuration and capabilities

### Phase 1-3 Context Variables
- `{PERSONALITY_CONTEXT}` - User personality profiling data
- `{EMOTIONAL_STATE_CONTEXT}` - Current emotional analysis
- `{EXTERNAL_EMOTION_CONTEXT}` - External API emotion analysis
- `{EMOTIONAL_PREDICTION_CONTEXT}` - Emotional prediction insights
- `{PROACTIVE_SUPPORT_CONTEXT}` - Proactive support recommendations
- `{RELATIONSHIP_CONTEXT}` - Basic relationship history
- `{EMOTIONAL_INTELLIGENCE_CONTEXT}` - Complete emotional awareness
- `{MEMORY_MOMENTS_CONTEXT}` - Memory-triggered personality moments

## AI System Configuration

The system provides unified AI capabilities with configurable conversation styles:

### Adaptive Style (Default)
**Features**: Dynamic conversation adaptation, context awareness, emotional intelligence
**Use Cases**: Most Discord bots, general-purpose interactions

### Human-like Style  
**Features**: Deep emotional resonance, natural conversation flow, relationship memory
**Use Cases**: Companion bots, long-term relationships, maximum personalization

### Analytical Style
**Features**: Logical reasoning, structured responses, clear explanations
**Use Cases**: Educational bots, technical support, professional interactions

### Balanced Style
**Features**: Phase 4 capabilities balanced for efficiency and depth
**Use Cases**: Community bots, general chat applications, versatile interactions

## Customization Tips

### For Different Models
- **Advanced models**: Use adaptive_ai_template.md for full Phase 4 capability utilization with human-like style
- **Local models**: Use empathetic_companion_template.md with balanced style for efficient processing
- **Character bots**: Modify character_ai_template.md with your specific character and appropriate mode scaling

### For Different Use Cases
- **Business**: professional_ai_template.md with professional relationship memory networks
- **Social**: casual_friend_template.md with friendship depth evolution
- **Support**: empathetic_companion_template.md with emotional continuity and growth tracking
- **Creative**: character_ai_template.md with character-consistent relationship development

### For Your Specific Needs
- **Dream character**: dream_ai_enhanced.md (ready to use with Phase 4 eternal consciousness)
- **Other characters**: Modify character_ai_template.md with Phase 4 relationship awareness
- **Professional Dream**: Blend professional_ai_template.md with Dream's voice and eternal memory
- **Casual Dream**: Blend casual_friend_template.md with Dream's personality and infinite relationship awareness

### Conversation Style Selection Guide
- **Balanced Style**: Quick responses, essential features, efficient processing - good for community interactions
- **Adaptive Style**: Dynamic features, good memory continuity, full emotional intelligence - ideal for most users  
- **Human-like Style**: Maximum capabilities, deep relationship modeling, sophisticated adaptation - for complex, long-term relationships
- **Analytical Style**: Structured responses, logical reasoning, professional interactions - for educational/technical use

The templates are designed to make your Phase 4 Human-Like Intelligence features feel natural and integrated, not like an AI showing off its analysis capabilities. The goal is seamless, human-like interaction with genuine memory continuity and relationship growth that's perfectly tailored to each user across all interactions over time.