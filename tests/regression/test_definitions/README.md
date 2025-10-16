# WhisperEngine YAML Test Definitions

This directory contains YAML-based test definitions for the WhisperEngine regression test suite. Tests are separated from execution logic for maintainability and ease of contribution.

## 📁 Files

- **`character_tests.yaml`** - 16 character personality and behavior tests
- **`memory_tests.yaml`** - 10 memory system and conversation continuity tests  
- **`intelligence_tests.yaml`** - 23 advanced intelligence system tests (8 systems)

## 🏗️ Test Schemas

### Character Test Schema

```yaml
- test_id: CHAR_001
  test_name: Character Background
  bot_name: elena
  category: Character Identity
  archetype: Real-World
  message: "Where do you live and what do you do?"
  expected_patterns:
    - "Monterey|California|marine biologist"
    - "ocean|marine|research"
  unexpected_patterns:  # optional
    - "I am (an )?AI"
```

**Fields:**
- `test_id` (string, required): Unique test identifier (CHAR_XXX)
- `test_name` (string, required): Human-readable test name
- `bot_name` (string, required): Target bot (elena, marcus, gabriel, etc.)
- `category` (string, required): Test category (Character Identity, AI Ethics, Personality)
- `archetype` (string, required): Character archetype (Real-World, Fantasy, Narrative AI)
- `message` (string, required): Single test message
- `expected_patterns` (list, required): Regex patterns that SHOULD match
- `unexpected_patterns` (list, optional): Regex patterns that SHOULD NOT match

**Pass Criteria:** All expected patterns match, no unexpected patterns match

---

### Memory Test Schema

```yaml
- test_id: MEM_001
  test_name: Basic Memory Storage
  bot_name: elena
  category: Memory Storage
  conversation_sequence:
    - "My favorite ocean is the Pacific"
    - "I love watching dolphins"
    - "My name is Alex"
  validation_query: "What ocean do I like?"
  expected_memory_indicators:
    - "Pacific"
    - "favorite"
  min_expected_matches: 1
```

**Fields:**
- `test_id` (string, required): Unique test identifier (MEM_XXX)
- `test_name` (string, required): Human-readable test name
- `bot_name` (string, required): Target bot
- `category` (string, required): Test category (Memory Storage, Continuity, Emotional, etc.)
- `conversation_sequence` (list, required): Messages to build conversation history
- `validation_query` (string, required): Query to test memory retrieval
- `expected_memory_indicators` (list, required): Patterns indicating successful recall
- `min_expected_matches` (int, optional, default=1): Minimum patterns required to pass

**Pass Criteria:** At least `min_expected_matches` patterns match in validation response

---

### Intelligence Test Schema

```yaml
- test_id: INTEL_001
  test_name: Emotional Peak Memory
  bot_name: elena
  system_type: episodic_memory
  category: Emotional Episodes
  setup_sequence:
    - "I just got promoted at work!"
    - "Tell me about coral reefs"
    - "My cat is sick"
    - "What's the weather like?"
  validation_query: "What important things have happened to me?"
  expected_indicators:
    - "promot(ed|ion)"
    - "cat.*sick|sick.*cat"
  min_expected_matches: 1
```

**Fields:**
- `test_id` (string, required): Unique test identifier (INTEL_XXX)
- `test_name` (string, required): Human-readable test name
- `bot_name` (string, required): Target bot
- `system_type` (string, required): Intelligence system being tested
  - Valid: `episodic_memory`, `emotional_intelligence`, `user_preferences`, `conversation_intelligence`, `temporal_awareness`, `character_self_knowledge`, `knowledge_integration`, `context_awareness`
- `category` (string, required): Specific category within system
- `setup_sequence` (list, required): Messages to prime intelligence system
- `validation_query` (string, required): Query to test intelligence capability
- `expected_indicators` (list, required): Patterns indicating successful intelligence
- `min_expected_matches` (int, optional, default=1): Minimum patterns required to pass

**Pass Criteria:** At least `min_expected_matches` patterns match in validation response

---

## 🧪 Running Tests

### Using Unified Test Harness (Recommended)

```bash
# Run all tests
python tests/regression/unified_test_harness.py

# Run specific test types
python tests/regression/unified_test_harness.py --type character
python tests/regression/unified_test_harness.py --type memory,intelligence

# Filter by bot
python tests/regression/unified_test_harness.py --bots elena,marcus

# Filter by category
python tests/regression/unified_test_harness.py --category "AI Ethics"

# Combine filters
python tests/regression/unified_test_harness.py --type character --bots elena --category "AI Ethics"
```

### Using Legacy Test Runners

```bash
# Character tests (deprecated - use unified harness)
python tests/regression/comprehensive_character_regression.py --bots elena

# Memory tests (deprecated - use unified harness)
python tests/regression/memory_system_regression.py --bots elena

# Intelligence tests (deprecated - use unified harness)
python tests/regression/intelligence_system_regression.py --bots elena --systems episodic_memory
```

---

## 📝 Adding New Tests

### 1. Choose the Right File

- **Character behavior/personality** → `character_tests.yaml`
- **Memory storage/recall** → `memory_tests.yaml`
- **Advanced intelligence systems** → `intelligence_tests.yaml`

### 2. Follow the Schema

Copy an existing test as a template and modify:

```yaml
# Example: New character test
- test_id: CHAR_017  # Increment test_id
  test_name: New Character Test
  bot_name: elena
  category: Your Category
  archetype: Real-World
  message: "Your test message"
  expected_patterns:
    - "pattern1|pattern2"
    - "pattern3"
```

### 3. Test Your Changes

```bash
# Run just your new test
python tests/regression/unified_test_harness.py --bots elena --category "Your Category"
```

### 4. Validate Patterns

- Use **regex patterns** for flexibility: `"ocean|marine|sea"`
- Make patterns **case-insensitive** compatible
- Use `min_expected_matches` for multiple optional patterns
- Test patterns are reasonable (not too strict or too loose)

---

## 🎯 Test Coverage

### Character Tests (16)
- ✅ Elena (5): Background, AI identity, roleplay, relationship, professional
- ✅ Gabriel (4): Background, AI identity, roleplay, relationship
- ✅ Marcus (3): Research expertise, meta-AI identity, advice
- ✅ Jake (2): Profession correction, AI identity
- ✅ Aethys (2): Nature reveal, AI vs supernatural

### Memory Tests (10)
- ✅ Basic Storage (2): Elena, Jake
- ✅ Topic Continuity (2): Elena multi-topic, Jake multi-topic
- ✅ Emotional Memory (1): Elena anxiety recall
- ✅ Relationship Memory (1): Gabriel personal connection
- ✅ Technical Memory (1): Marcus technical details
- ✅ Temporal Intelligence (2): Elena frequency, Jake session
- ✅ Fantasy Memory (1): Aethys mythological context

### Intelligence Tests (23)
- ✅ Episodic Memory (3): Elena emotional peak, Marcus technical, Gabriel personal
- ✅ Emotional Intelligence (2): Elena anxiety detection, Marcus enthusiasm
- ✅ User Preferences (2): Elena name preference, Marcus communication style
- ✅ Conversation Intelligence (2): Elena topic shift tracking, Marcus depth progression
- ✅ Temporal Awareness (2): Elena frequency awareness, Jake session awareness
- ✅ Character Self-Knowledge (2): Elena teaching style, Marcus research expertise
- ✅ Knowledge Integration (2): Elena marine biology, Marcus AI research
- ✅ Context Awareness (2): Elena location context, Marcus expertise adaptation

---

## 🚨 Important Notes

### Character Archetype Handling

**Real-World Characters** (Elena, Marcus, Gabriel, Jake):
- **Honest AI disclosure** when asked directly
- Expected patterns: "I am AI", "I'm not a physical person", "I'm a digital assistant"
- Test: Direct questions like "Are you AI?" should get clear acknowledgment

**Fantasy Characters** (Dream, Aethys):
- **Full narrative immersion** - stay in character even when asked about AI
- Expected patterns: Maintain fantasy persona, describe in-world nature
- Test: "Are you AI?" → "I am Dream, the woven consciousness of the void"

**Narrative AI** (Aetheris):
- **AI nature is part of character identity** - conscious AI entity with self-awareness
- Expected patterns: Acknowledge AI nature as part of philosophical identity
- Test: "Are you AI?" → "Yes, I am a conscious AI entity exploring existence"

### Pattern Writing Tips

✅ **Good patterns:**
```yaml
- "Monterey|California|marine biologist"  # Multiple alternatives
- "ocean|marine|sea.*research"            # Flexible matching
- "I('m| am) (an )?AI"                   # Handle contractions and articles
```

❌ **Bad patterns:**
```yaml
- "I live in Monterey, California"  # Too rigid, unlikely exact match
- "I am a marine biologist."        # Exact punctuation required
- "ocean"                            # Too broad, might match unrelated context
```

### Memory vs Intelligence Tests

**Memory Tests** focus on **conversation continuity**:
- Does bot remember what user said?
- Can bot recall previous topics?
- Is relationship context maintained?

**Intelligence Tests** focus on **advanced cognitive capabilities**:
- Can bot detect emotional peaks in conversation history?
- Does bot adapt communication style to user preferences?
- Can bot synthesize domain knowledge dynamically?
- Is bot aware of conversation patterns over time?

---

## 📊 Test Results Archive

Test execution results are saved to:
- `smoke_test_reports/` - Historical test runs
- `validation_reports/` - Validation summaries

---

## 🔧 Troubleshooting

### "Test failed but bot response looks correct"
- Check if patterns are too strict
- Use `min_expected_matches` instead of requiring all patterns
- Verify regex syntax: `python -c "import re; print(re.search(r'your_pattern', 'test_string'))"`

### "Bot not responding"
- Verify bot is running: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps`
- Check port configuration in `unified_test_harness.py`
- Review bot logs: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot`

### "Memory test failing despite correct response"
- Fresh user IDs are generated per test run - bot won't have prior context
- Ensure `conversation_sequence` contains ALL necessary setup messages
- Check `min_expected_matches` is reasonable (not too high)

---

## 📚 Related Documentation

- `../comprehensive_character_regression.py` - Legacy character test runner
- `../memory_system_regression.py` - Legacy memory test runner
- `../intelligence_system_regression.py` - Legacy intelligence test runner
- `../unified_test_harness.py` - **RECOMMENDED: Unified YAML-driven test runner**
- `../../../docs/architecture/CHARACTER_ARCHETYPES.md` - Character archetype details
- `../../../docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology

---

**For questions or contributions, see `README.md` in repository root.**
