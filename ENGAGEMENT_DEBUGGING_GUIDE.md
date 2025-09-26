# Proactive Engagement Engine - Debugging Guide

## 🤖 Overview

The Proactive Engagement Engine now includes comprehensive debugging features that show exactly when different engagement strategies and features get triggered. This debugging system uses structured logging with clear emoji indicators to make it easy to track engagement system behavior.

## 🔍 Debug Logging Features

### Engagement Logger Configuration

The system creates a specialized logger called `engagement_logger` with these characteristics:

```python
engagement_logger = logging.getLogger("whisperengine.engagement")
engagement_logger.setLevel(logging.DEBUG)
```

- **Console output**: Real-time debugging to console
- **Structured format**: `🤖 [ENGAGEMENT] timestamp - level - message`
- **Emoji indicators**: Visual categorization of different features

## 📊 Debug Output Categories

### 🎯 Main Analysis Flow
**When triggered**: Every time `analyze_conversation_engagement()` is called
**What it shows**:
- User ID and message count being analyzed
- Flow state detection (FLOWING, STAGNATING, STAGNANT, etc.)
- Engagement scores and trends
- Whether intervention is needed
- Number of recommendations generated

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🎯 ENGAGEMENT: Starting conversation analysis for user user_123 with 4 recent messages
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🎯 ENGAGEMENT: Flow state: STAGNATING, engagement score: 0.42
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🎯 ENGAGEMENT: Stagnation risk: high
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🎯 ENGAGEMENT: Intervention needed: True
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🎯 ENGAGEMENT: Generated 3 proactive recommendations
```

### 📊 Conversation Flow Analysis
**When triggered**: During conversation flow state analysis
**What it shows**:
- Message timing analysis (quick, normal, slow responses)
- Engagement indicators detected
- Flow state calculations

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 📊 ENGAGEMENT: Analyzing conversation flow for user user_123
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 📊 ENGAGEMENT: Average message gap: 45.2 seconds
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 📊 ENGAGEMENT: Normal pace detected
```

### 🔍 Vector Coherence Analysis
**When triggered**: When analyzing topic coherence using vector embeddings
**What it shows**:
- Vector embedding generation process
- Semantic similarity calculations
- Final coherence scores

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔍 ENGAGEMENT: Starting vector-based topic coherence analysis
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔍 ENGAGEMENT: Generating embeddings for 3 messages
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔍 ENGAGEMENT: Average semantic similarity: 0.743
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🔍 ENGAGEMENT: VECTOR COHERENCE analysis complete - Score: 0.685 (similarity: 0.743)
```

### 🧠 Memory System Integration
**When triggered**: During memory-based engagement analysis
**What it shows**:
- Vector memory connection attempts
- Memory moments integration
- Number of memory connections found
- Connection types (similar_topic, emotional_echo, personal_growth)

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🧠 ENGAGEMENT: Using vector memory for connection analysis
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🧠 ENGAGEMENT: VECTOR MEMORY triggered - Found 2 memory connections
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🧠 ENGAGEMENT: Using memory moments for additional context
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 🧠 ENGAGEMENT: MEMORY MOMENTS triggered - Found 1 memory connections
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🧠 ENGAGEMENT: Memory connection type: emotional_echo
```

### 🔧 Recommendation Generation
**When triggered**: When generating proactive recommendations
**What it shows**:
- Personality profile integration
- Topic suggestion generation
- Conversation prompt creation
- Individual recommendation details

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔧 ENGAGEMENT: Generating proactive recommendations for user user_123
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔧 ENGAGEMENT: Fetching personality profile for personalization
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔧 ENGAGEMENT: Got personality context - depth: moderate, trust: high
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔧 ENGAGEMENT: Generated 2 topic suggestions
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - DEBUG - 🔧 ENGAGEMENT: Generated 1 conversation prompts
```

### 💡 Strategy Triggers
**When triggered**: When specific engagement strategies are activated
**What it shows**:
- Topic suggestion triggers with relevance levels
- Conversation prompt triggers with strategy types

**Example output**:
```
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 💡 ENGAGEMENT: TOPIC SUGGESTION triggered - Topic: 'Marine Conservation', Relevance: high
🤖 [ENGAGEMENT] 2025-09-26 15:30:45 - INFO - 💬 ENGAGEMENT: CONVERSATION PROMPT triggered - Strategy: MEMORY_CALLBACK
```

## 🛠️ How to Enable Debug Logging

### 1. Container-based Development (Recommended)

The engagement debugging is automatically enabled when the engagement engine is initialized. To see the debug output:

```bash
# Start your bot with full logging
./multi-bot.sh logs elena

# Or start and follow logs
./multi-bot.sh start elena
./multi-bot.sh logs elena -f
```

### 2. Testing with Debug Script

Use the provided test script to trigger engagement features:

```bash
# Run the debugging test script
python test_engagement_debugging.py
```

This script will:
- Create test conversation scenarios
- Trigger various engagement strategies
- Display all debug logging output
- Show final analysis results

### 3. Integration into Bot Handlers

To integrate proactive engagement with debugging into your bot handlers:

```python
# In your message handler
from src.conversation.engagement_protocol import create_engagement_engine
from src.memory.memory_protocol import create_memory_manager

async def handle_message(user_id, message_content):
    # Create memory manager
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Create engagement engine with debugging
    engagement_engine = await create_engagement_engine(
        engagement_engine_type="full",
        memory_manager=memory_manager
    )
    
    # Prepare recent messages
    recent_messages = [
        {
            "content": message_content,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        # Add more messages from conversation history
    ]
    
    # Run engagement analysis (with debugging output)
    result = await engagement_engine.analyze_conversation_engagement(
        user_id=user_id,
        context_id=f"conversation_{user_id}",
        recent_messages=recent_messages,
        current_thread_info=None
    )
    
    # Use recommendations for proactive engagement
    if result.get('recommendations'):
        for rec in result['recommendations']:
            if rec['type'] == 'topic_suggestion':
                # Send topic suggestion to user
                await send_proactive_message(user_id, rec['content'])
            elif rec['type'] == 'conversation_prompt':
                # Send conversation prompt
                await send_proactive_message(user_id, rec['content'])
```

## 🔧 Debugging Configuration

### Environment Variables

Optional tuning parameters (already in `.env.template`):

```env
# Proactive Engagement Tuning (Phase 4.3)
PHASE4_ENGAGEMENT_STAGNATION_THRESHOLD_MINUTES=5  # When conversation is stagnant
PHASE4_ENGAGEMENT_CHECK_INTERVAL_MINUTES=3        # How often to check
PHASE4_ENGAGEMENT_MAX_SUGGESTIONS_PER_HOUR=8      # Rate limiting
```

### Log Level Control

To adjust debug verbosity:

```python
# For more verbose debugging
engagement_logger.setLevel(logging.DEBUG)

# For only key events
engagement_logger.setLevel(logging.INFO)

# To reduce noise
engagement_logger.setLevel(logging.WARNING)
```

## 📈 Interpreting Debug Output

### Engagement Flow States
- **FLOWING**: Conversation is healthy and engaging
- **STAGNATING**: Conversation showing signs of decline  
- **STAGNANT**: Conversation has stopped or become minimal

### Vector Coherence Scores
- **0.7-1.0**: High coherence (similar topics, good flow)
- **0.4-0.7**: Moderate coherence (some topic drift)
- **0.0-0.4**: Low coherence (topic jumping, confusion)

### Intervention Triggers
- **Time-based**: Long gaps between messages
- **Content-based**: Short responses, repetitive patterns
- **Engagement-based**: Low engagement scores, declining trends

## 🎯 Common Debugging Scenarios

### Scenario 1: No Engagement Triggers
**Symptoms**: No proactive recommendations generated
**Debug to check**:
- Flow state analysis - is conversation actually stagnant?
- Stagnation threshold - are thresholds too high?
- Memory connections - is vector store accessible?

### Scenario 2: Too Many Triggers
**Symptoms**: Excessive proactive interventions
**Debug to check**:
- Engagement thresholds - may be too sensitive
- Rate limiting - check max suggestions per hour
- Flow analysis - may be over-detecting stagnation

### Scenario 3: Vector Analysis Failing
**Symptoms**: Coherence analysis defaulting to 0.5
**Debug to check**:
- Vector store connectivity
- Embedding generation failures
- Memory manager initialization

## ✅ Best Practices

### 1. Monitor Debug Logs Regularly
Watch for patterns in engagement triggers and user responses

### 2. Adjust Thresholds Based on Usage
Fine-tune stagnation and engagement thresholds for your user base

### 3. Test Different Conversation Scenarios  
Use the test script with various message patterns to validate behavior

### 4. Integrate with Bot Analytics
Combine engagement debugging with overall bot performance metrics

## 🚀 Production Deployment

When deploying to production:

1. **Keep INFO level logging** for key engagement events
2. **Reduce DEBUG level** to avoid log spam
3. **Monitor engagement success rates** through the debug output
4. **Use rate limiting** to prevent overwhelming users
5. **Collect metrics** on engagement strategy effectiveness

The debugging system provides comprehensive visibility into when and why proactive engagement features trigger, making it easy to optimize conversation intelligence for your users.