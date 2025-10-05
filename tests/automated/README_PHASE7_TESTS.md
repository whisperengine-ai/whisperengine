# Phase 7.5 & 7.6 Bot Emotional Intelligence - Test Suite

## Overview

This test suite validates all bot emotional intelligence features added on **October 5, 2025**:

- **Phase 7.5**: Bot emotion analysis and storage (track bot's emotional state)
- **Phase 7.6**: Bot emotional self-awareness and trajectory analysis (bot knows its emotional history)

## Test File

**File**: `test_phase7_bot_emotions_direct_validation.py`

This script uses **direct Python API testing** (preferred method) without HTTP layer for complete access to internal data structures and immediate debugging.

## Features Tested

### Phase 7.5 Features
1. ✅ Bot emotion analysis from response text
2. ✅ Mixed emotions detection for bot (multiple simultaneous emotions)
3. ✅ Bot emotion storage in vector memory
4. ✅ Bot emotion storage in InfluxDB (temporal tracking)

### Phase 7.6 Features
1. ✅ Bot emotional trajectory analysis (intensifying, calming, stable)
2. ✅ Bot emotional self-awareness in CDL prompts
3. ✅ Bot emotional state in API metadata responses
4. ✅ Integration with message processing pipeline

## Prerequisites

### Environment Setup

```bash
# Required environment variables
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
export QDRANT_HOST="localhost" 
export QDRANT_PORT="6334"

# Activate Python virtual environment
source .venv/bin/activate
```

### Running Services

Ensure Qdrant is running:

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker-compose up -d qdrant
```

## Running the Tests

### Method 1: Direct Python Execution

```bash
# From project root
cd /Users/markcastillo/git/whisperengine

# Set environment
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
source .venv/bin/activate

# Run tests
python tests/automated/test_phase7_bot_emotions_direct_validation.py
```

### Method 2: Make Executable and Run

```bash
# Make executable
chmod +x tests/automated/test_phase7_bot_emotions_direct_validation.py

# Run directly
./tests/automated/test_phase7_bot_emotions_direct_validation.py
```

## Test Suite Structure

### Test 1: Bot Emotion Analysis
**What it tests**: Emotion analysis from bot response text

**Test cases**:
- Joyful gratitude: "Oh, thank you so much!"
- Empathetic sadness: "I'm so sorry to hear that..."
- Curious excitement: "Ooh, tell me more!"
- Neutral factual: "The weather forecast shows rain tomorrow."

**Validates**:
- ✅ Primary emotion detection
- ✅ Emotion intensity (0-1 scale)
- ✅ Mixed emotions list structure
- ✅ All emotions dict structure

### Test 2: Mixed Emotions Storage
**What it tests**: Complex emotional states with multiple emotions

**Test case**:
```
Response: "That's wonderful news! Congratulations! I can understand 
           feeling nervous though - new beginnings can be both 
           exciting and a little scary."
```

**Validates**:
- ✅ Mixed emotions list populated
- ✅ All emotions dict populated
- ✅ Multiple emotions detected (≥1)
- ✅ Storage in vector memory

### Test 3: End-to-End Message Processing
**What it tests**: Full message processing pipeline with bot emotions

**Test flow**:
1. Create MessageContext with "You're wonderful!"
2. Process through MessageProcessor
3. Check metadata structure

**Validates**:
- ✅ Metadata structure (ai_components)
- ✅ Bot emotion field present
- ✅ Bot emotional state field present (Phase 7.6)
- ✅ Trajectory direction calculated
- ✅ Emotional velocity tracked
- ✅ Recent emotions history available

## Expected Output

### Successful Test Run

```
================================================================================
WhisperEngine Phase 7.5 & 7.6 Bot Emotional Intelligence
Direct Validation Test Suite
================================================================================
Date: 2025-10-05 14:32:15
Features: Bot emotion tracking, trajectory analysis, self-awareness
================================================================================

🔧 Initializing test components...
✅ Components initialized successfully

================================================================================
TEST 1: Bot Emotion Analysis from Response Text
================================================================================
✅ PASS: Test 1.1: Joyful gratitude response
   Response: 'Oh, thank you so much! That really brightens my...'
   Expected category: joy, Got: joy
   Intensity: 0.85 (threshold: 0.5)
   Mixed emotions: 2 detected
   All emotions dict: 4 emotions
   Description: Joyful gratitude response

✅ PASS: Test 1.2: Empathetic sad response
...

================================================================================
TEST SUMMARY - Phase 7.5 & 7.6 Bot Emotional Intelligence
================================================================================

Total Tests: 10
✅ Passed: 10
❌ Failed: 0
Success Rate: 100.0%

================================================================================
FEATURE VALIDATION STATUS
================================================================================
✅ Phase 7.5: Bot emotion analysis
✅ Phase 7.5: Mixed emotions for bot
✅ Phase 7.6: Emotional trajectory
✅ Phase 7.6: Prompt integration
✅ API metadata availability
```

### Failed Test Run

If tests fail, you'll see detailed error messages:

```
❌ FAIL: Test 1.1: Joyful gratitude response
   Exception: Connection to Qdrant failed - ensure Qdrant is running

Failed Tests:
  ❌ Test 1.1: Joyful gratitude response
```

## Troubleshooting

### Issue: "Connection to Qdrant failed"

**Solution**: Start Qdrant service

```bash
docker-compose up -d qdrant
# Wait 5 seconds
docker ps | grep qdrant
```

### Issue: "Module not found"

**Solution**: Ensure virtual environment is activated

```bash
source .venv/bin/activate
python --version  # Should show Python 3.11+
```

### Issue: "FASTEMBED_CACHE_PATH error"

**Solution**: Set environment variable

```bash
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
mkdir -p /tmp/fastembed_cache
```

### Issue: "No value for argument 'user_id'"

**Solution**: This is expected - the test script handles this correctly with dummy user_ids.

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Phase 7 Bot Emotion Tests
  run: |
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
    export QDRANT_HOST="localhost"
    export QDRANT_PORT="6334"
    source .venv/bin/activate
    python tests/automated/test_phase7_bot_emotions_direct_validation.py
```

### Docker Container Testing

```bash
# Run tests inside Docker container
docker exec whisperengine-elena-bot \
  python /app/tests/automated/test_phase7_bot_emotions_direct_validation.py
```

## Test Data Cleanup

Tests use isolated user IDs:
- `test_bot_emotion`
- `test_phase7_mixed_emotions_user`
- `test_phase7_e2e_user`

These are automatically isolated in Qdrant and don't interfere with production data.

## Related Documentation

- **Implementation Guide**: `docs/features/PHASE_7.6_BOT_EMOTIONAL_SELF_AWARENESS.md`
- **API Reference**: `docs/api/ENRICHED_METADATA_API.md`
- **Metadata Control**: `docs/features/METADATA_LEVEL_CONTROL.md`

## Test Maintenance

### Adding New Tests

1. Add test method to `Phase7BotEmotionValidator` class
2. Follow naming convention: `test_N_description`
3. Use `self.log_test()` for result logging
4. Add test call in `main()` function

### Updating Test Cases

Test cases are defined in dictionaries within each test method. To add new cases:

```python
test_cases = [
    {
        "response": "Your bot response here",
        "expected_emotion": "joy",
        "min_intensity": 0.5,
        "description": "Test case description"
    },
    # Add new case here
]
```

## Success Criteria

For Phase 7.5 & 7.6 to be considered validated:

- ✅ All 10+ tests pass
- ✅ Bot emotion detection works for 4+ emotion types
- ✅ Mixed emotions structure validated
- ✅ Emotional trajectory calculation functional
- ✅ API metadata includes bot emotional state
- ✅ No exceptions during normal operation

---

**Last Updated**: October 5, 2025  
**Test Suite Version**: 1.0  
**WhisperEngine Version**: Phase 7.6 (Bot Emotional Self-Awareness)
