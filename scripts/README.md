# WhisperEngine Testing Scripts

This directory contains testing scripts for WhisperEngine bot APIs and functionality.

## Bot API Testing Scripts

### Python Script (Recommended)
**File**: `test_bot_apis.py`

Comprehensive async Python script for testing all bot API endpoints with parallel execution.

**Features**:
- ✅ **Parallel Testing**: Test all 8 bots simultaneously (completes in ~6 seconds)
- ✅ **Individual Bot Testing**: Test specific bots with verbose output
- ✅ **Comprehensive Validation**: Health, info, and chat endpoint testing
- ✅ **Load Testing**: Performance testing with randomized messages
- ✅ **Concurrent Load Testing**: Multiple parallel requests per bot
- ✅ **Detailed Statistics**: Response time percentiles (P50, P95, P99), RPS metrics
- ✅ **JSON Reports**: Detailed results saved to `/logs/` directory
- ✅ **Error Handling**: Proper timeout and error management
- ✅ **Clean Output**: Summary reports with emoji indicators

**Usage**:
```bash
# Normal Testing
python scripts/test_bot_apis.py                    # Test all bots in parallel (fast!)
python scripts/test_bot_apis.py elena              # Test specific bot with verbose output
python scripts/test_bot_apis.py sophia             # Test Sophia with detailed output

# Load Testing
python scripts/test_bot_apis.py load               # Load test all bots (10 requests each)
python scripts/test_bot_apis.py load --requests 50 # 50 requests per bot
python scripts/test_bot_apis.py load --concurrent 5 # 5 concurrent requests per bot
python scripts/test_bot_apis.py load --bot elena --requests 100 --concurrent 10  # Specific bot

# Show help
python scripts/test_bot_apis.py --help
```

**Example Output**:
```
🤖 WhisperEngine Bot API Test Suite
==================================================
Testing 8 bots in parallel...
⏳ Running parallel tests...

✅ Parallel testing completed! Results:
----------------------------------------
🌊 Elena Rodriguez: ✅ ALL PASS
🤖 Dr. Marcus Thompson: ✅ ALL PASS
🎮 Ryan Chen: ✅ ALL PASS
...

⚡ Parallel testing completed in 5.75 seconds
```

## Load Testing Features

The Python script includes comprehensive load testing capabilities for performance analysis:

### Load Test Parameters

- **`--requests N`**: Number of requests per bot (default: 10)
- **`--concurrent N`**: Number of concurrent requests per bot (default: 1)
- **`--bot NAME`**: Test specific bot only

### Load Test Examples

```bash
# Light load test - 10 requests per bot, sequential
python scripts/test_bot_apis.py load

# Medium load test - 50 requests per bot, 5 concurrent
python scripts/test_bot_apis.py load --requests 50 --concurrent 5

# Heavy load test on Elena - 100 requests, 10 concurrent
python scripts/test_bot_apis.py load --bot elena --requests 100 --concurrent 10

# Stress test all bots - 200 requests each, 20 concurrent
python scripts/test_bot_apis.py load --requests 200 --concurrent 20
```

### Load Test Metrics

The load testing provides detailed performance statistics:

- **Success Rate**: Percentage of successful requests vs total
- **Requests Per Second (RPS)**: Throughput measurement
- **Response Time Statistics**:
  - Average, minimum, maximum response times
  - P50 (median), P95, P99 percentiles for performance distribution
- **Response Length**: Average character count of responses
- **Error Analysis**: Detailed error information for failed requests

### Sample Load Test Output

```
📊 Load Test Results for 🌊 Elena Rodriguez
============================================================
Total Requests: 50
Success Rate: 100.0% (50/50)
Total Time: 45.23s
Requests/sec: 1.11
Response Times (seconds):
  Average: 0.892
  Min: 0.654
  Max: 1.234
  P50: 0.876
  P95: 1.145
  P99: 1.201
Response Length: 285 chars average
```

### Bash Script (Quick Testing)
**File**: `quick_bot_test.sh`

Simple curl-based script for quick manual testing and endpoint discovery.

**Features**:
- ✅ **Fast Setup**: Simple bash script, no dependencies
- ✅ **Individual Testing**: Test specific bots quickly
- ✅ **Endpoint Discovery**: List all available API endpoints
- ✅ **Response Snippets**: Shows sample bot responses

**Usage**:
```bash
# Test all bots (sequential)
./scripts/quick_bot_test.sh test

# Test specific bot
./scripts/quick_bot_test.sh test elena

# Show all available endpoints
./scripts/quick_bot_test.sh endpoints

# Show help
./scripts/quick_bot_test.sh help
```

## Available Bot Endpoints

All bots expose the same API structure:

| Bot | Port | Profession | Emoji |
|-----|------|------------|-------|
| Elena | 9091 | Marine Biologist | 🌊 |
| Marcus | 9092 | AI Researcher | 🤖 |
| Ryan | 9093 | Indie Game Developer | 🎮 |
| Dream | 9094 | Mythological Entity | 🌙 |
| Gabriel | 9095 | Archangel | 👼 |
| Sophia | 9096 | Marketing Executive | 💼 |
| Jake | 9097 | Adventure Photographer | 📸 |
| Aethys | 3007 | Omnipotent Entity | ✨ |

### API Endpoints

Each bot provides these endpoints:

1. **Health Check**: `GET /health`
   ```bash
   curl http://localhost:9091/health
   ```

2. **Bot Information**: `GET /api/bot-info`
   ```bash
   curl http://localhost:9091/api/bot-info
   ```

3. **Chat API**: `POST /api/chat`
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "Hello!", "user_id": "your_user_id"}' \
     http://localhost:9091/api/chat
   ```

### Response Format

**Chat API Response**:
```json
{
  "response": "¡Hola! How can I help you today? 🌊",
  "timestamp": "2025-09-29T05:02:16.906209",
  "message_id": "web_1759122135.930857",
  "bot_name": "Elena Rodriguez [AI DEMO]",
  "success": true
}
```

## Prerequisites

### For Python Script:
- Python 3.8+ with asyncio support
- aiohttp library (`pip install aiohttp`)
- WhisperEngine virtual environment activated

### For Bash Script:
- bash shell
- curl command
- jq command (for JSON parsing)

## Integration with Development Workflow

These scripts are designed to work with the WhisperEngine multi-bot system:

1. **Start Infrastructure**: `./multi-bot.sh start all`
2. **Run Tests**: `python scripts/test_bot_apis.py`
3. **Check Results**: Review logs and endpoint functionality

## Troubleshooting

**Common Issues**:

- **Connection Refused**: Ensure bots are running (`./multi-bot.sh status`)
- **Timeout Errors**: Check bot health and container status
- **Permission Errors**: Ensure scripts are executable (`chmod +x`)
- **Import Errors**: Activate virtual environment (`source .venv/bin/activate`)

**Debug Commands**:
```bash
# Check bot container status
./multi-bot.sh status

# Check individual bot logs
./multi-bot.sh logs elena

# Test single endpoint manually
curl http://localhost:9091/health
```

## Report Output

Test results are automatically saved to:
- **JSON Reports**: `/logs/bot_api_test_results_YYYYMMDD_HHMMSS.json`
- **Console Output**: Real-time status and summary tables
- **Error Logs**: Detailed error information for debugging

---

*Last Updated: September 28, 2025*  
*WhisperEngine Version: Multi-Bot + Individual APIs*