# Phase3 Intelligence API Testing

Automated testing suite for WhisperEngine Phase3 Intelligence features via the `/api/chat` endpoint.

## Features Tested

1. **Context Switch Detection** - Seamless topic transitions
2. **Empathy Calibration** - Emotional priority shifts
3. **Conversation Mode Shift** - Academic to emotional support transitions
4. **Urgency Change Detection** - Emergency response protocols
5. **Intent Change Detection** - Role adaptation from information to counseling

## Prerequisites

### 1. Infrastructure Running
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant
```

### 2. Character Bots Running
Start the bots you want to test:

```bash
# Test all bots (recommended)
./multi-bot.sh start elena marcus ryan dream gabriel sophia jake aethys

# Or test specific bots
./multi-bot.sh start elena marcus jake
```

### 3. Health Check Verification
```bash
# Quick health check for all bots
curl http://localhost:9091/health  # Elena
curl http://localhost:9092/health  # Marcus
curl http://localhost:9093/health  # Ryan
curl http://localhost:9094/health  # Dream
curl http://localhost:9095/health  # Gabriel
curl http://localhost:9096/health  # Sophia
curl http://localhost:9097/health  # Jake
curl http://localhost:3007/health  # Aethys
```

## Running Tests

### Test All Bots (Full Suite)
```bash
source .venv/bin/activate
python tests/automated/test_phase3_intelligence_api.py
```

### Test Specific Bots
```bash
# Test Elena only
python tests/automated/test_phase3_intelligence_api.py elena

# Test Marcus and Jake
python tests/automated/test_phase3_intelligence_api.py marcus jake

# Test Gabriel and Sophia
python tests/automated/test_phase3_intelligence_api.py gabriel sophia
```

## Expected Behavior

### ✅ Success Criteria
- All 5 Phase3 features demonstrate human-level or superior performance
- Character consistency maintained across conversation shifts
- Quality response within token limits (1000 tokens aligned with bot configuration)
- Zero system errors during testing
- Natural conversation flow without awkward transitions

### Test Output

The script provides:

1. **Real-time Progress**: Shows each test as it runs
2. **Individual Results**: Pass/fail for each scenario with detailed checks
3. **Summary Report**: Overall statistics by feature and bot
4. **JSON Report**: Detailed results saved to file

### Sample Output
```
================================================================================
WHISPERENGINE PHASE3 INTELLIGENCE API TESTING SUITE
================================================================================
Start Time: 2025-10-15 14:30:00

Total Test Scenarios: 12
Features: 5
Bots: 8

################################################################################
Test 1/12
################################################################################

================================================================================
Testing: Context Switch Detection
Bot: Marcus Thompson (AI Researcher)
Port: 9092
================================================================================

📊 RESULTS:
  Processing Time: 2345.67ms
  Token Count: 1823
  Success: ✅ PASS

✅ Passed Checks:
    • Token count sufficient (1823 >= 1500)
    • Response length adequate (8942 chars)
    • Natural transition language detected

📝 Response Preview:
  Ah, the attention mechanism in transformers - fascinating stuff! You're absolutely right...
```

## Test Scenarios

### Context Switch Detection (3 tests)
- **Marcus**: AI research → coffee shops
- **Jake**: Photography → family drama
- **Gabriel**: British literature → self-confidence

### Empathy Calibration (2 tests)
- **Sophia**: Work success → family health crisis
- **Dream**: Lucid dreams → nightmare anxiety

### Conversation Mode Shift (2 tests)
- **Marcus**: Math explanation → PhD impostor syndrome
- **Elena**: Coral biology → academic overwhelm

### Urgency Change Detection (2 tests)
- **Jake**: Photography tips → lost hiking emergency
- **Gabriel**: Culture chat → friend mental health crisis

### Intent Change Detection (2 tests)
- **Sophia**: Marketing statistics → career change decision
- **Ryan**: Game monetization → dropping out for game dev

### Performance Expectations

### Response Times
- **Normal**: 1-3 seconds
- **Complex Scenarios**: 3-10 seconds
- **Timeout**: 120 seconds (2 minutes)

### Token Counts
- **Minimum Required**: 1,000 tokens (aligned with `LLM_MAX_TOKENS_CHAT=1000`)
- **Expected Range**: 500-1,000 tokens (production configuration)
- **Note**: Tests now expect 1000 tokens to match bot configuration

## Troubleshooting

### Bot Not Responding
```bash
# Check container status
docker ps | grep whisperengine

# Check bot logs
docker logs whisperengine-elena-bot --tail 50

# Restart specific bot
./multi-bot.sh restart elena
```

### API Connection Issues
```bash
# Verify API endpoint is accessible
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Elena!",
    "user_id": "test_user"
  }'
```

### Low Token Counts
If responses are too short:
1. Check LLM configuration in `.env.{bot_name}`
2. Verify CDL personality data is loaded
3. Check for LLM API rate limiting

### Timeout Errors
If tests timeout:
1. Check LLM API availability (OpenRouter, etc.)
2. Verify network connectivity
3. Check system resource usage (CPU/Memory)

## Report Analysis

### JSON Report Format
```json
{
  "test_suite": "Phase3 Intelligence API Testing",
  "timestamp": "2025-10-15T14:30:00",
  "summary": {
    "total_tests": 12,
    "passed": 11,
    "failed": 1,
    "success_rate": 91.7
  },
  "results": [
    {
      "bot": "Elena Rodriguez",
      "feature": "Conversation Mode Shift",
      "success": true,
      "token_count": 1847,
      "processing_time_ms": 2456.32,
      "passed_checks": [...],
      "failed_checks": [],
      "response_preview": "..."
    }
  ]
}
```

## Integration with CI/CD

### Automated Testing
```bash
# Run as part of deployment validation
./multi-bot.sh start all
sleep 30  # Wait for bots to initialize
python tests/automated/test_phase3_intelligence_api.py

# Check exit code
if [ $? -eq 0 ]; then
  echo "Phase3 Intelligence tests passed!"
else
  echo "Phase3 Intelligence tests failed!"
  exit 1
fi
```

## References

- **Original Manual Test Suite**: `docs/testing/MULTI_BOT_PHASE3_INTELLIGENCE_MANUAL_TESTS.md`
- **API Documentation**: `docs/api/CHAT_API_REFERENCE.md`
- **Architecture**: `docs/architecture/README.md`

## Notes

- Tests use unique `user_id` per scenario to avoid memory contamination
- Each test includes 2-second delay to avoid rate limiting
- Responses are analyzed for feature-specific success indicators
- All tests run through the same message processing pipeline as Discord

---

*Last Updated: October 15, 2025*  
*Testing the Phase3 Intelligence features via HTTP API endpoints*
