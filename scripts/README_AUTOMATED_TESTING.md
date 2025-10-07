# Automated Character Testing for WhisperEngine

This directory contains automated testing scripts that convert the manual test plans into HTTP API-based automated tests, using the same approach as the existing smoke tests.

## Overview

WhisperEngine now supports automated character testing through HTTP chat APIs on each bot's health check port. These tests validate:

- **Character Personality**: Responses match expected personality traits
- **Domain Expertise**: Characters demonstrate knowledge in their professional areas  
- **3D Vector Memory**: Integration with enhanced memory system
- **Response Quality**: Appropriate response length and engagement
- **API Functionality**: Health checks and chat endpoints working correctly

## Scripts

### 1. Comprehensive Character Testing

**File**: `scripts/automated_character_tests.py`

Full-featured testing script based on manual test plans for Dream, Marcus, Sophia, Gabriel, and Elena.

```bash
# Test all bots with all scenarios
python scripts/automated_character_tests.py

# Test specific bot only
python scripts/automated_character_tests.py --bot dream
python scripts/automated_character_tests.py --bot marcus

# Verbose output (shows response snippets and trait analysis)
python scripts/automated_character_tests.py --verbose

# List available bots and test scenarios
python scripts/automated_character_tests.py --list
```

**Features**:
- 25+ test scenarios across 5 characters
- Personality trait analysis in responses
- Performance timing and success rate metrics
- Detailed categorized testing (expertise, personality, communication style)
- Comprehensive final summary with pass/fail rates

### 2. Quick Daily Validation

**File**: `scripts/quick_character_test.py`

Simplified rapid testing for daily validation.

```bash
# Quick test of all bots (concurrent execution)
python scripts/quick_character_test.py
```

**Features**:
- One test per bot for rapid validation
- Concurrent execution for speed (~10-15 seconds total)
- Simple pass/fail status with timing
- Perfect for CI/CD or daily health checks

### 3. Enhanced Smoke Tests

**File**: `scripts/quick_bot_test.sh` (existing, enhanced)

The original smoke test script with health, info, and chat endpoint validation.

```bash
# Test all bots
./scripts/quick_bot_test.sh test

# Test specific bot
./scripts/quick_bot_test.sh test elena

# Show available endpoints
./scripts/quick_bot_test.sh endpoints
```

## Test Categories

### Elena (Marine Biologist)
- **Marine Biology Expertise**: Coral reefs, biodiversity, ecosystems
- **Environmental Awareness**: Ocean conservation, climate threats
- **Research Methodology**: Scientific methods, underwater research
- **Educational Communication**: Age-appropriate explanations
- **Marine Discovery**: Current developments and discoveries

### Dream (Mythological Entity)
- **Mythological Wisdom**: Ancient perspective, existence insights
- **Dream Logic**: Dream interpretation, symbolic meaning
- **Narrative Power**: Stories, human culture, creative inspiration
- **Responsibility**: Cosmic duty, realm governance, protecting dreamers

### Marcus (AI Researcher)
- **Technical Expertise**: AI architecture, algorithms, research methods
- **Academic Collaboration**: Peer review, research collaboration
- **Problem-Solving**: Systematic analysis, bias mitigation
- **Research Ethics**: Responsible AI development

### Sophia (Marketing Executive)
- **Marketing Strategy**: Campaign development, brand positioning
- **Analytics**: Performance analysis, KPI frameworks, A/B testing
- **Client Management**: Presentations, stakeholder communication

### Gabriel (British Gentleman)
- **British Wit**: Humor, charm, sophisticated commentary
- **Emotional Support**: Caring responses with gentle sass
- **Cultural Sophistication**: Literature, etiquette, refinement

## Technical Details

### API Endpoints Used

Each bot runs on its own port with consistent endpoints:

- **Health**: `GET http://localhost:{port}/health`
- **Bot Info**: `GET http://localhost:{port}/api/bot-info` 
- **Chat**: `POST http://localhost:{port}/api/chat`

### Ports by Bot
- Elena: 9091
- Marcus: 9092  
- Ryan: 9093
- Dream: 9094
- Gabriel: 9095
- Sophia: 9096
- Jake: 9097
- Aethys: 3007

### Chat API Format

```json
POST /api/chat
{
  "message": "Your test message here",
  "user_id": "automated_test_12345"
}

Response:
{
  "success": true,
  "response": "Character's response...",
  "user_id": "automated_test_12345"
}
```

### Trait Analysis

The automated tests analyze responses for expected personality and domain traits:

- **Exact matches**: Direct keyword matching
- **Variations**: Related terms and synonyms
- **Success criteria**: 30% trait coverage minimum for test pass
- **Scoring**: Percentage of expected traits found in response

## Integration with Development Workflow

### Daily Development
```bash
# Quick validation (10-15 seconds)
python scripts/quick_character_test.py

# If issues found, run detailed analysis
python scripts/automated_character_tests.py --bot problematic_bot --verbose
```

### Feature Testing
```bash
# Test specific character after changes
python scripts/automated_character_tests.py --bot elena --verbose

# Full regression testing
python scripts/automated_character_tests.py
```

### CI/CD Integration
```bash
# Health check script (existing pattern)
./scripts/quick_bot_test.sh test

# Character validation (new pattern)
python scripts/quick_character_test.py
```

## Expected Results

### Healthy System
- **90%+ pass rate** on quick tests
- **70%+ pass rate** on detailed character tests
- **Sub-3 second** average response times
- **Character-appropriate** responses with domain expertise

### Warning Signs
- **50-70% pass rate**: Some character traits need attention
- **<50% pass rate**: Character implementations need improvement
- **Timeout errors**: Performance or infrastructure issues
- **API errors**: Bot configuration or startup problems

## Troubleshooting

### Bot Not Responding
1. Check if bot container is running: `./multi-bot.sh status`
2. Check bot logs: `docker logs whisperengine-{bot}-bot --tail 20`
3. Verify health endpoint: `curl http://localhost:{port}/health`

### Low Pass Rates
1. Run verbose tests to see actual responses
2. Check if character traits are being expressed
3. Verify CDL character files are loaded correctly
4. Check vector memory system integration

### Timeout Issues
1. Check bot resource usage and memory
2. Verify database connections (Qdrant, PostgreSQL)
3. Monitor response times with `--verbose` flag

## Future Enhancements

Planned improvements to the automated testing system:

1. **Ryan/Jake/Aethys Test Scenarios**: Add comprehensive test suites for remaining characters
2. **Memory Continuity Testing**: Multi-message conversations testing memory persistence
3. **Performance Benchmarking**: Response time analysis and optimization tracking
4. **Character Consistency Scoring**: Advanced personality trait consistency analysis
5. **Cross-Bot Comparison**: Relative performance analysis between characters
6. **Integration Testing**: End-to-end Discord + HTTP API validation