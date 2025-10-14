# WhisperEngine Smoke Test Suite

A comprehensive testing framework for validating all WhisperEngine bot functionality through API endpoints, with parallel execution support and detailed log analysis.

## Features

- **Parallel Testing**: Test all bots simultaneously for faster execution
- **Individual Bot Testing**: Target specific bots for focused testing  
- **Comprehensive Test Coverage**: Tests health, API, conversation, memory, personality, emotional intelligence, and performance
- **Log Analysis**: Analyzes Docker container logs for errors and warnings during test execution
- **Detailed Reporting**: Generates JSON reports for each bot plus a comprehensive final report
- **Smart Error Detection**: Filters out configuration warnings to focus on real issues

## Quick Start

```bash
# Test all bots in parallel (recommended)
./scripts/quick_smoke_test.sh

# Test specific bot
./scripts/quick_smoke_test.sh --bot elena

# Test with verbose output
./scripts/quick_smoke_test.sh --bot elena --verbose

# Test all bots sequentially (slower but easier to follow)
./scripts/quick_smoke_test.sh --sequential
```

## Direct Python Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Test all bots in parallel
python scripts/smoke_test.py

# Test specific bot
python scripts/smoke_test.py --bot elena --verbose

# Force sequential execution
python scripts/smoke_test.py --sequential
```

## Available Bots

- `elena` - Elena Rodriguez (Marine Biologist) - Port 9091
- `marcus` - Marcus Thompson (AI Researcher) - Port 9092  
- `ryan` - Ryan Chen (Indie Game Developer) - Port 9093
- `dream` - Dream of the Endless (Mythological Entity) - Port 9094
- `gabriel` - Gabriel (British Gentleman) - Port 9095
- `sophia` - Sophia Blake (Marketing Executive) - Port 9096
- `jake` - Jake Sterling (Adventure Photographer) - Port 9097
- `aethys` - Aethys (Omnipotent Entity) - Port 3007

## Test Categories

### 1. Health Check
- Validates `/health` endpoint returns `{"status": "healthy"}`
- Confirms bot container is responsive

### 2. Bot Info Validation
- Tests `/api/bot-info` endpoint
- Validates required fields: `bot_name`, `status`, `platform`, `capabilities`
- Confirms expected capabilities are present

### 3. Basic Conversation
- Tests `/api/chat` endpoint with simple message
- Validates response structure and content quality
- Ensures minimum response length and success flag

### 4. Personality Traits
- Tests character-specific conversations
- Validates personality-appropriate responses using keyword detection
- Each bot has customized test messages relevant to their character

### 5. Memory Storage & Recall
- Stores personal information in one conversation
- Tests recall in subsequent conversation
- Validates vector memory system is working correctly

### 6. Conversation Context
- Tests multi-turn conversation capabilities
- Validates follow-up questions work correctly
- Ensures context is maintained between messages

### 7. Emotional Intelligence
- Tests bot response to emotional user messages
- Validates supportive and empathetic language detection
- Confirms appropriate emotional awareness

### 8. Performance Testing
- Measures API response times
- Flags responses slower than 15 seconds
- Tracks overall execution duration

### 9. Log Analysis (NEW)
- Analyzes Docker container logs during test period
- Detects critical issues vs configuration warnings
- Categorizes error types for better troubleshooting

## Output and Reporting

### Console Output
The smoke test provides real-time colored console output showing:
- ✅ Successful tests
- ❌ Failed tests
- ⚠️ Warnings and issues
- ℹ️ Informational messages
- 🧪 Test progress indicators

### Report Files
Reports are generated in the `smoke_test_reports/` directory:

**Individual Bot Reports**: `{bot_name}_smoke_test_report.json`
```json
{
  "bot_name": "elena",
  "character": "Marine Biologist", 
  "test_results": {...},
  "log_analysis": {
    "warnings": 0,
    "errors": 2,
    "critical_issues": []
  },
  "summary": {
    "success_rate": 100.0
  }
}
```

**Final Report**: `final_smoke_test_report_{test_id}.json`
```json
{
  "test_suite": "WhisperEngine Smoke Test",
  "parallel_mode": true,
  "overall_summary": {
    "total_bots_tested": 8,
    "bots_fully_passed": 7,
    "overall_success_rate": 95.8
  },
  "recommendations": [...]
}
```

## Log Analysis Features

The smoke test analyzes Docker container logs to detect:

### Critical Issues (Causes Test Failure)
- Database connection failures
- Vector storage system failures  
- Discord API authentication failures
- Bot initialization failures

### Filtered Warnings (Non-Critical)
- Configuration warnings ("Facts API endpoint not configured")
- Missing optional config files
- Non-fatal deprecation warnings

### Smart Error Detection
- Distinguishes between real errors and configuration noise
- Provides adjusted error counts after filtering known non-critical issues
- Tracks both raw and filtered error counts for transparency

## Parallel vs Sequential Mode

### Parallel Mode (Default)
- **Pros**: Much faster (tests all bots simultaneously)
- **Cons**: Mixed output from multiple bots
- **Best for**: CI/CD, quick validation, production monitoring

### Sequential Mode  
- **Pros**: Cleaner output, easier to follow individual bot progress
- **Cons**: Takes much longer (tests bots one by one)
- **Best for**: Debugging, detailed analysis, troubleshooting

## Prerequisites

1. **Running Infrastructure**: All bots must be running
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d
   ```

2. **Virtual Environment**: Python virtual environment must be activated
   ```bash
   source .venv/bin/activate
   ```

3. **Docker Access**: Must have access to `docker logs` command for log analysis

## Exit Codes

- `0`: All tests passed, no critical log issues
- `1`: Some tests failed or critical issues detected

## Troubleshooting

### Common Issues

**"Connection refused" errors**: 
- Ensure all bots are running: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps`
- Restart if needed: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart`

**"Read timed out" errors**:
- Some bots may be slow to respond under load
- Try running individual bot tests: `--bot elena`
- Consider sequential mode: `--sequential`

**High error counts in logs**:
- Check if errors are actually configuration warnings
- Review the `critical_issues` field in reports for real problems
- Use `docker logs whisperengine-{bot}-bot` for detailed investigation

### Performance Optimization

For faster execution:
- Use parallel mode (default)
- Test individual bots when debugging
- Consider excluding slower bots during development

For more reliable results:
- Use sequential mode for stability
- Add delays between tests if needed
- Monitor system resources during parallel execution

## Integration with CI/CD

The smoke test suite is designed for automated testing:

```bash
#!/bin/bash
# CI/CD Pipeline Example

# Start all services
./multi-bot.sh start all

# Wait for services to be ready
sleep 30

# Run smoke tests
source .venv/bin/activate
python scripts/smoke_test.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All smoke tests passed"
else
    echo "❌ Smoke tests failed"
    exit 1
fi
```

## Future Enhancements

Potential improvements for the smoke test suite:
- WebSocket testing for real-time features
- Load testing with multiple concurrent users
- Database consistency validation
- Cross-bot memory isolation verification
- Performance benchmarking and regression detection