# Elena Test Scripts Reference Guide

## 🧪 Overview

This document provides a complete reference for Elena's automated test suite. These scripts validate Elena's personality, emotional intelligence, and Discord-like conversation flow without requiring container deployments or Discord coordination.

**Key Benefits:**
- ⚡ **Fast Feedback**: Test personality changes in seconds, not minutes
- 🚫 **No Discord Required**: Script entire conversation flows locally
- ✅ **Automated Validation**: Automatic detection of Spanish phrases, emojis, marine terms
- 🎯 **Confidence**: Make changes knowing core personality works perfectly

---

## 📋 Test Scripts Overview

| Script | Purpose | Features Tested | Runtime |
|--------|---------|----------------|---------|
| `test_elena_infrastructure.py` | Infrastructure validation | PostgreSQL, Redis, Qdrant, character files | ~2s |
| `test_elena_simple.py` | Basic personality test | CDL system, LLM integration, character response | ~5s |
| `test_elena_emotional_cdl.py` | Emotional intelligence | Emotion detection + CDL integration pipeline | ~10s |
| `test_elena_personality_chat.py` | **Discord simulation** | **Complete conversation flow with all features** | **~15s** |

---

## 🏗️ Infrastructure Test

### `test_elena_infrastructure.py`

**Purpose**: Validate that all required services are accessible on localhost ports.

**What it tests:**
- ✅ PostgreSQL connection (localhost:5433)
- ✅ Redis connection (localhost:6380) 
- ✅ Qdrant connection (localhost:6334)
- ✅ Elena character file exists
- ✅ Elena .env file exists

**Usage:**
```bash
source .venv/bin/activate && python test_elena_infrastructure.py
```

**Sample Output:**
```
🏗️  Elena Infrastructure Test (Localhost)
==================================================
🔍 Testing PostgreSQL...
✅ PostgreSQL: Connected
🔍 Testing Redis...
✅ Redis: Connected
🔍 Testing Qdrant...
✅ Qdrant: Connected (1 collections)
🔍 Testing Character File...
✅ Elena character file: Found
🔍 Testing Environment File...
✅ Elena .env file: Found

📊 Infrastructure Test Results:
   Passed: 5/5
   Success Rate: 100.0%
🎉 All infrastructure ready for Elena testing!
```

**When to use:**
- Before running other tests
- After infrastructure changes
- Debugging connection issues

---

## 🎭 Simple Personality Test

### `test_elena_simple.py`

**Purpose**: Quick validation of core Elena personality systems.

**What it tests:**
- ✅ CDL Character System loading
- ✅ CDL AI Integration (character-aware prompts)
- ✅ LLM Client functionality
- ✅ Basic personality response (Spanish + marine biology)

**Usage:**
```bash
source .venv/bin/activate && python test_elena_simple.py
```

**Sample Output:**
```
🧪 Simple Elena Localhost Test
========================================
🔍 Testing CDL Character System...
   ✅ Elena character file found
   ✅ Character JSON loaded: Elena Rodriguez
🔍 Testing CDL AI Integration...
   ✅ CDL prompt generated with Elena personality
🔍 Testing LLM Client...
   ✅ LLM response: ¡Hola! ¿Cómo estás? Soy Elena, una bióloga marina...
🎉 All tests passed! Elena personality system works locally
```

**Key Validation:**
- **Spanish Response**: "¡Hola! ¿Cómo estás?"
- **Marine Identity**: "Soy Elena, una bióloga marina"
- **Ocean Reference**: "océano o la vida marina"

**When to use:**
- Quick personality validation after code changes
- Verifying CDL system integration
- Testing LLM connectivity

---

## 🧠 Emotional Intelligence Test

### `test_elena_emotional_cdl.py`

**Purpose**: Validate complete emotional intelligence + CDL integration pipeline.

**What it tests:**
- ✅ Emotion detection from user messages
- ✅ CDL integration with emotional context
- ✅ Emotional responsiveness in different scenarios
- ✅ Pipeline integration (emotion → CDL → response)

**Emotional Scenarios Tested:**
1. **Excited**: "I just saw the most amazing dolphins today!"
2. **Sad**: "I'm feeling down about coral bleaching..."
3. **Curious**: "I've been wondering about bioluminescence..."
4. **Grateful**: "Thank you for sharing your marine knowledge!"

**Usage:**
```bash
source .venv/bin/activate && python test_elena_emotional_cdl.py
```

**Sample Output:**
```
🧠 Elena Emotional Intelligence + CDL Integration Test
============================================================

🔍 Test 1: Excited Emotion Integration
   Message: I just saw the most amazing dolphins today! They w...
     🧠 Testing emotional analysis...
     🎭 Testing CDL integration with emotional context...
     🗣️  Testing full response generation...
     🔍 Validating personality integration...
   ✅ Excited: Emotional CDL integration working!
   📊 Emotion detected: surprise
   🎯 CDL elements found: 8
   🧠 Elena personality markers: 1

📊 Emotional Intelligence + CDL Integration Results:
   Passed: 4/4
   Success Rate: 100.0%
🎉 Perfect! Elena's emotional intelligence fully integrates with CDL personality!
```

**Key Validations:**
- **Emotion Detection**: Accurate emotion classification
- **CDL Integration**: Character elements in prompts
- **Personality Markers**: Spanish, marine terms, emojis in responses

**When to use:**
- Testing emotional intelligence changes
- Validating CDL prompt integration
- Ensuring emotion → personality flow works

---

## 🎭 Discord Personality Chat Simulation

### `test_elena_personality_chat.py` ⭐ **MAIN TEST**

**Purpose**: Complete Discord send/receive flow simulation with full personality validation.

**What it tests:**
- ✅ **Complete conversation flow**: Message → Emotion → CDL → Response
- ✅ **Spanish phrases**: "¡Hola", "¡Increíble", "de nada", etc.
- ✅ **Ocean emojis**: 🌊, 💙, 🐠, 🐬, etc.
- ✅ **Marine biology terms**: coral, diving, ecosystem, etc.
- ✅ **Enthusiasm markers**: amazing, incredible, fascinating, etc.
- ✅ **Emotional responsiveness**: Joy, sadness, excitement, etc.
- ✅ **Character consistency**: Maintains Elena's personality across conversation

**Conversation Scenarios:**
1. **Spanish Greeting**: "¡Hola Elena! How are you today?"
2. **Excited Ocean Discovery**: "I just saw the most amazing dolphins jumping!"
3. **Sad Environmental Concern**: "I'm worried about coral bleaching..."
4. **Scientific Curiosity**: "Tell me about bioluminescence in deep sea creatures"
5. **Personal Connection**: "What's your favorite thing about being a marine biologist?"
6. **Grateful Appreciation**: "Thank you for sharing your passion for the ocean!"

**Usage:**
```bash
source .venv/bin/activate && python test_elena_personality_chat.py
```

**Sample Output:**
```
🎭 Elena Discord Personality Simulator
======================================================================
Testing Elena's personality in Discord-like conversations
======================================================================
🤖 Initializing Elena Personality Systems...
✅ Elena personality systems ready!

🎬 Chat 1/6
========================================

💬 YOU: ¡Hola Elena! How are you today?
------------------------------------------------------------
🧠 Analyzing emotion...
   Emotion: joy (0.97)
🎭 Creating character-aware prompt...
   CDL elements: 6
🗣️  Generating Elena's response...
🎯 Spanish phrases: ['¡Hola', 'gracias', '¡']
🌊 Ocean emojis: []
🐠 Marine terms: ['ocean', 'sea']
✨ Enthusiasm: ['fascinating', 'beautiful']

🤖 ELENA: ¡Hola, User! Estoy fantástica, gracias. I've been busy with some fascinating research on our beautiful ocean friends. How about you?
⏱️  Processing: 2763.7ms

======================================================================
📊 ELENA PERSONALITY ANALYSIS
======================================================================
✅ Successful conversations: 6/6
🇪🇸 Spanish phrases detected: 11
🌊 Ocean emojis used: 4
🐠 Marine biology terms: 12
✨ Enthusiasm markers: 11
⏱️  Average response time: 2057.2ms

🎭 Elena Personality Score: 4/4
🎉 Perfect! Elena's personality is fully working in Discord simulation!
📋 Report saved: elena_personality_chat_report_20250924_215342.json
```

**Personality Validation:**
- **Spanish Integration**: Counts "¡Hola", "¡Increíble", "de nada", etc.
- **Ocean Emojis**: Detects 🌊, 💙, 🐠, 🐬, 🦑, 🌺, etc.
- **Marine Terms**: Finds "ocean", "coral", "diving", "underwater", etc.
- **Enthusiasm**: Identifies "amazing", "incredible", "fascinating", etc.

**Success Criteria:**
- All 6 conversations successful
- Spanish phrases used across conversations
- Ocean emojis appear in relevant contexts
- Marine biology terms demonstrate expertise
- Enthusiasm markers show personality

**When to use:**
- **Primary testing script** for Elena personality
- Before deploying personality changes
- Validating complete Discord-like experience
- Testing conversation flow and continuity

---

## 🚀 Setup & Prerequisites

### Environment Setup

**1. Infrastructure Services:**
```bash
# Start required services (PostgreSQL, Redis, Qdrant)
./multi-bot.sh start all
# Note: Elena bot container should be STOPPED for localhost testing
```

**2. Environment Configuration:**
```bash
# Copy Elena's configuration
cp .env.elena .env
```

**3. Python Virtual Environment:**
```bash
# ALWAYS use virtual environment (promised! 😄)
source .venv/bin/activate
```

### Required Services & Ports

| Service | Localhost Port | Container Port | Required For |
|---------|---------------|----------------|--------------|
| PostgreSQL | 5433 | 5432 | All tests |
| Redis | 6380 | 6379 | All tests |
| Qdrant | 6334 | 6333 | Memory tests |

### File Dependencies

- `characters/examples/elena-rodriguez.json` - Elena's CDL character definition
- `.env.elena` - Elena's environment configuration
- Virtual environment with all dependencies installed

---

## 🎯 Testing Strategy

### Development Workflow

**1. Quick Validation:**
```bash
source .venv/bin/activate && python test_elena_simple.py
```

**2. Full Personality Testing:**
```bash
source .venv/bin/activate && python test_elena_personality_chat.py
```

**3. Emotional Intelligence Deep Dive:**
```bash
source .venv/bin/activate && python test_elena_emotional_cdl.py
```

### Before Making Changes

1. **Baseline Test**: Run `test_elena_personality_chat.py` to establish current performance
2. **Make Changes**: Modify personality code, CDL files, or emotional intelligence
3. **Validate**: Re-run tests to ensure personality remains intact
4. **Deploy**: Once tests pass, deploy to container with confidence

### Debugging Failed Tests

**If infrastructure test fails:**
- Check if containers are running: `docker ps`
- Verify ports: `./multi-bot.sh status`
- Check container logs: `./multi-bot.sh logs elena`

**If personality test fails:**
- Check OpenRouter API key in `.env`
- Verify character file exists: `ls -la characters/examples/elena-rodriguez.json`
- Test LLM connectivity separately

**If emotional intelligence test fails:**
- Check emotion analyzer initialization
- Verify CDL integration pipeline
- Test individual components separately

---

## 📊 Interpreting Results

### Success Indicators

**Infrastructure Test:**
- All 5/5 checks pass
- No connection errors
- Services accessible on correct ports

**Simple Personality Test:**
- CDL character system loads
- Spanish phrases in response ("¡Hola", "Soy Elena")
- Marine biology context ("bióloga marina", "océano")

**Emotional Intelligence Test:**
- 4/4 emotional scenarios pass
- Emotion detection working (joy, sadness, surprise, etc.)
- CDL elements integrated (6+ elements per prompt)
- Personality markers in responses

**Discord Chat Simulation:**
- 6/6 conversations successful
- Personality Score: 4/4
- Spanish phrases: 10+ across conversations
- Ocean emojis: 3+ in appropriate contexts
- Marine terms: 10+ demonstrating expertise
- Enthusiasm markers: 10+ showing personality

### Warning Signs

**Personality Degradation:**
- Spanish phrases dropping below 5 total
- No ocean emojis in relevant conversations
- Generic responses without marine context
- Low enthusiasm markers

**System Issues:**
- Connection timeouts or errors
- CDL elements below 5 per prompt
- Emotion detection failures
- LLM client errors

---

## 🔧 Customization

### Adding New Test Scenarios

**In `test_elena_personality_chat.py`:**

```python
chat_scenarios = [
    "¡Hola Elena! How are you today?",
    "I just saw the most amazing dolphins jumping!",
    # Add your new scenario here:
    "Tell me about your latest research project",
    "What conservation efforts are you most excited about?"
]
```

### Modifying Personality Validation

**Custom Spanish Phrases:**
```python
def find_spanish_phrases(self, text: str) -> list:
    spanish_indicators = [
        "¡Hola", "¡Ay", "¡Increíble", "¡Qué", "Sí", 
        # Add new phrases:
        "¡Perfecto", "marinera", "bueno"
    ]
```

**Custom Ocean Emojis:**
```python
def find_ocean_emojis(self, text: str) -> list:
    ocean_emojis = [
        "🌊", "💙", "🐠", "🐬", "🦑", "🌺", 
        # Add new emojis:
        "🦈", "🐙", "⭐"
    ]
```

### Creating Bot-Specific Tests

**For Marcus (AI Researcher):**
```python
# Copy test_elena_personality_chat.py to test_marcus_personality_chat.py
# Modify character file and personality indicators:

character_file = "characters/examples/marcus-thompson.json"
tech_terms = ["AI", "machine learning", "neural networks", "algorithm"]
enthusiasm_markers = ["fascinating", "breakthrough", "innovation"]
```

---

## 📈 Performance Benchmarks

### Expected Response Times

- **Infrastructure Test**: ~2 seconds
- **Simple Personality**: ~5 seconds  
- **Emotional Intelligence**: ~10 seconds
- **Discord Chat Simulation**: ~15 seconds (6 conversations)

### Personality Score Targets

**Excellent Performance:**
- Spanish phrases: 10+ total
- Ocean emojis: 4+ total
- Marine terms: 12+ total
- Enthusiasm markers: 10+ total
- Success rate: 100%

**Good Performance:**
- Spanish phrases: 6+ total
- Ocean emojis: 2+ total  
- Marine terms: 8+ total
- Enthusiasm markers: 6+ total
- Success rate: 85%+

**Needs Attention:**
- Spanish phrases: <5 total
- Ocean emojis: 0-1 total
- Marine terms: <6 total
- Enthusiasm markers: <4 total
- Success rate: <80%

---

## 🎉 Benefits & Impact

### Development Speed
- **Before**: 5+ minutes to test personality change (container rebuild + Discord coordination)
- **After**: 15 seconds to test complete personality flow

### Confidence
- **Before**: "Hope the personality still works after this change"  
- **After**: "I know the personality works - tests prove it"

### Debugging
- **Before**: Manual Discord message testing, hard to reproduce issues
- **After**: Automated scenarios, consistent reproduction, detailed analysis

### Team Collaboration  
- **Before**: "Can you test Elena in Discord while I make this change?"
- **After**: "Run the test script - it covers everything automatically"

---

## 🚨 Troubleshooting

### Common Issues

**1. Connection Errors:**
```
[Errno 8] nodename nor servname provided, or not known
```
**Solution:** Infrastructure containers not running
```bash
./multi-bot.sh start all
./multi-bot.sh status  # Check all services are up
```

**2. No Spanish Phrases:**
```
Spanish phrases detected: 0
```
**Solution:** CDL integration issue or LLM problem
- Check character file exists
- Verify `.env` has correct OpenRouter key
- Test simple personality script first

**3. Memory/Import Errors:**
```
ModuleNotFoundError: No module named 'src.memory'
```
**Solution:** Virtual environment not activated
```bash
source .venv/bin/activate  # ALWAYS use venv!
```

**4. LLM Client Failures:**
```
'NoOpLLMClient' object has no attribute 'generate_chat_completion_safe'
```
**Solution:** LLM client type configuration
- Check `LLM_CLIENT_TYPE=openrouter` in `.env`
- Verify OpenRouter API key is valid

### Debug Mode

**Add debug logging to any test:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Run test script
```

**Check specific component:**
```bash
source .venv/bin/activate && python -c "
from src.llm.llm_protocol import create_llm_client
client = create_llm_client()
print('LLM Client:', type(client).__name__)
"
```

---

## 📝 Report Files

All tests generate JSON reports for detailed analysis:

- `elena_personality_chat_report_YYYYMMDD_HHMMSS.json` - Complete conversation analysis
- `elena_emotional_cdl_test_report_YYYYMMDD_HHMMSS.json` - Emotional intelligence results

**Report Structure:**
```json
{
  "simulation_time": "2025-09-24T21:53:42.123456",
  "results": [...],
  "summary": {
    "successful_chats": 6,
    "total_spanish": 11,
    "total_emojis": 4,
    "total_marine_terms": 12,
    "personality_score": 4
  }
}
```

---

## 🚀 Next Steps

### Expanding Test Coverage
1. **Memory Integration**: Add datastore validation (as requested)
2. **Multi-Turn Conversations**: Test conversation continuity
3. **Edge Cases**: Test with unusual inputs
4. **Performance**: Add response time benchmarks

### Other Bots
1. **Marcus Thompson**: AI researcher personality testing
2. **Marcus Chen**: Game developer personality testing  
3. **Cross-Bot**: Comparative personality analysis

### Integration
1. **CI/CD**: Run tests automatically on code changes
2. **Discord Bot**: Integration testing with real Discord flow
3. **Web UI**: Test personality in web chat interface

---

*Created: September 24, 2025*  
*Elena Test Scripts v1.0*  
*WhisperEngine AI - stable-pre-refactor branch*