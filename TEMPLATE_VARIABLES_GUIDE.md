# WhisperEngine System Prompt Template Variables Guide

## 📋 Complete List of Template Variables

WhisperEngine uses a sophisticated template variable system that allows dynamic system prompt generation based on real-time AI analysis. Here are all available template variables:

### 🧠 **Core Intelligence Variables**

#### `{AI_SYSTEM_CONTEXT}`
**Purpose**: System capabilities and configuration  
**Data Source**: Always populated with current system status  
**Example Output**: `"System Mode: Full Capabilities, Resource Allocation: Optimized"`  
**Usage**: Shows the AI what capabilities are available

#### `{INTERACTION_CONTEXT}` 
**Purpose**: Phase 4 conversation mode and processing metadata  
**Data Source**: `phase4_context` parameter  
**Example Output**: `"Interaction Type: guidance, Phases Executed: phase2_emotion, phase3_memory, phase4_intelligence"`  
**Usage**: Tells AI what type of interaction this is and what analysis phases were run

---

### 🕸️ **Memory & Relationship Variables**

#### `{MEMORY_NETWORK_CONTEXT}`
**Purpose**: Memory insights, conversation history, and recognized patterns  
**Data Source**: `comprehensive_context['memory_insights']`  
**Example Output**: `"Memory Network Status: 15 conversations recorded, Key Topics: personal goals, career growth, relationships, Relationship Summary: Developing trust, Patterns Recognized: seeks guidance, values authenticity"`  
**Usage**: Provides conversation continuity and relationship context

#### `{RELATIONSHIP_DEPTH_CONTEXT}`
**Purpose**: Current relationship level and trust indicators  
**Data Source**: `comprehensive_context` relationship data  
**Example Output**: `"Relationship Depth: Developing, Trust Markers: shares personal details, asks for advice, Connection Status: Building deeper rapport"`  
**Usage**: Helps AI adapt interaction style to relationship depth

#### `{MEMORY_MOMENTS_CONTEXT}` *(Phase 4.1)*
**Purpose**: Memory-triggered personality moments and authentic callbacks  
**Data Source**: `memory_moments_context` parameter  
**Example Output**: `"Memory-Triggered Moment: Reflective moment activated (based on 3 memory connections), triggered by contemplative emotion. Guidance: This echoes our previous discussion about finding balance - consider how your perspective has evolved"`  
**Usage**: Enables authentic personality moments based on conversation patterns

#### `{RELATIONSHIP_CONTEXT}`
**Purpose**: Basic user interaction context  
**Data Source**: `user_id` parameter  
**Example Output**: `"User interaction context for user_12345"`  
**Usage**: Simple user identification for basic relationship tracking

---

### 🎭 **Emotional Intelligence Variables**

#### `{EMOTIONAL_STATE_CONTEXT}`
**Purpose**: Current mood and emotional state analysis  
**Data Source**: `emotional_intelligence_results['mood_assessment']`  
**Example Output**: `"Current Emotional State: contemplative, stress level: moderate, stability: balanced"`  
**Usage**: Helps AI respond appropriately to user's current emotional state

#### `{EXTERNAL_EMOTION_CONTEXT}`
**Purpose**: Advanced external emotion analysis with confidence metrics  
**Data Source**: `emotional_intelligence_results['external_emotion_analysis']`  
**Example Output**: `"External Emotion Analysis (Tier ADVANCED): thoughtful (confidence: 0.87, intensity: 0.65), recent trend: increasingly reflective, sentiment: positive"`  
**Usage**: Provides precise emotional intelligence for nuanced responses

#### `{EMOTIONAL_PREDICTION_CONTEXT}`
**Purpose**: Predicted emotional trajectory and patterns  
**Data Source**: `emotional_intelligence_results['emotion_prediction']`  
**Example Output**: `"Emotional Prediction: likely to experience growth-oriented emotional patterns"`  
**Usage**: Helps AI anticipate emotional needs and prepare supportive responses

#### `{PROACTIVE_SUPPORT_CONTEXT}`
**Purpose**: Specific emotional support guidance  
**Data Source**: `emotional_intelligence_results['proactive_support']`  
**Example Output**: `"Emotional Support Context: User showing signs of decision fatigue - offer structured thinking framework"`  
**Usage**: Provides specific guidance for emotional support strategies

#### `{EMOTIONAL_INTELLIGENCE_CONTEXT}`
**Purpose**: Combined emotional intelligence summary  
**Data Source**: Combination of emotional analysis results  
**Example Output**: `"Current Emotional State: contemplative, stress level: moderate; Emotional Prediction: likely to experience growth-oriented patterns; External Emotion Analysis: thoughtful (confidence: 0.87)"`  
**Usage**: Comprehensive emotional context for complex emotional situations

---

### 👤 **Personality & Behavior Variables**

#### `{PERSONALITY_CONTEXT}`
**Purpose**: User personality profile and communication preferences  
**Data Source**: `personality_metadata` parameter  
**Example Output**: `"User Personality Profile: analytical communication style, high confidence, methodical decision-making"`  
**Usage**: Helps AI adapt communication style to user's personality

---

## 🔧 **How to Use Template Variables**

### **1. In System Prompt Templates**

Add variables to your system prompt template file:

```markdown
### Current Context Analysis
**Memory Networks**: {MEMORY_NETWORK_CONTEXT}
**Relationship Status**: {RELATIONSHIP_DEPTH_CONTEXT} 
**Emotional State**: {EMOTIONAL_STATE_CONTEXT}
**Personality**: {PERSONALITY_CONTEXT}
**Memory Moments**: {MEMORY_MOMENTS_CONTEXT}
**System Status**: {AI_SYSTEM_CONTEXT}
```

### **2. In Code - Calling the Function**

```python
from src.utils.helpers import get_contextualized_system_prompt

# Basic usage
contextualized_prompt = get_contextualized_system_prompt(
    personality_metadata={
        'communication_style': 'analytical', 
        'confidence_level': 'high',
        'decision_style': 'methodical'
    },
    emotional_intelligence_results={
        'mood_assessment': {
            'current_mood': 'contemplative',
            'stress_level': 'moderate',
            'emotional_stability': 'balanced'
        },
        'external_emotion_analysis': {
            'primary_emotion': 'thoughtful',
            'confidence': 0.87,
            'intensity': 0.65,
            'tier_used': 'advanced'
        }
    },
    user_id="user_12345",
    comprehensive_context={
        'memory_insights': {
            'conversation_count': 15,
            'key_topics': ['personal goals', 'career growth'],
            'relationship_summary': 'Developing trust',
            'patterns': ['seeks guidance', 'values authenticity']
        },
        'relationship_level': 'developing',
        'trust_indicators': ['shares personal details', 'asks for advice']
    },
    memory_moments_context={
        'moment': {
            'moment_type': 'reflective',
            'emotional_trigger': 'contemplative',
            'prompt_guidance': 'This echoes our previous discussion about finding balance'
        },
        'connections': 3
    }
)
```

### **3. Variable Processing Flow**

1. **Template Loading**: System loads the base template from `config/system_prompts/dream_ai_enhanced.md`
2. **Data Analysis**: AI systems analyze user input and generate context data
3. **Variable Replacement**: `get_contextualized_system_prompt()` replaces `{VARIABLE_NAME}` with actual data
4. **Cleanup**: Any unfilled variables are safely removed
5. **Final Prompt**: Contextualized prompt is sent to LLM

### **4. Security Features**

- **Safe Fallbacks**: Empty variables are replaced with empty strings, not error messages
- **Pattern Cleanup**: Multiple cleanup passes ensure no template artifacts remain
- **Input Validation**: Context data is validated before insertion

---

## 🎯 **Variable Usage Examples**

### **Emotional Response Adaptation**
```markdown
**Current Emotional Context**: {EMOTIONAL_STATE_CONTEXT}
**Enhanced Perception**: {EXTERNAL_EMOTION_CONTEXT}

*Respond with empathy matching their current emotional state, using insights from both internal assessment and external analysis.*
```

### **Memory-Driven Conversations**
```markdown
**Memory Networks**: {MEMORY_NETWORK_CONTEXT}
**Memory Moments**: {MEMORY_MOMENTS_CONTEXT}

*Reference past conversations naturally and trigger authentic personality moments when patterns emerge.*
```

### **Relationship-Aware Interaction**
```markdown
**Relationship Depth**: {RELATIONSHIP_DEPTH_CONTEXT}
**Personality Profile**: {PERSONALITY_CONTEXT}

*Adapt your communication style to their personality and the current depth of your relationship.*
```

---

## 🚀 **Advanced Usage Tips**

1. **Combine Variables**: Use multiple variables together for rich context
2. **Conditional Content**: Template sections can be conditionally included based on variable presence
3. **Fallback Handling**: Design templates that work even when variables are empty
4. **Performance**: Variables are processed efficiently - no need to limit usage
5. **Debugging**: Check the final contextualized prompt to see how variables were replaced

This template system enables WhisperEngine to provide highly contextual, personalized AI interactions that adapt to user personality, emotional state, relationship depth, and conversation history!