# WhisperEngine Regression Testing Suite

This directory contains automated regression testing scripts for validating WhisperEngine functionality.

## 🧪 Test Scripts

### `comprehensive_character_regression.py` ⭐ **PRIMARY TEST SUITE**
**Comprehensive character personality and AI ethics testing via HTTP Chat API**

**What it tests:**
- ✅ Character personality responses (actual conversations!)
- ✅ AI ethics handling (transparency, boundaries, disclaimers)
- ✅ Roleplay interactions
- ✅ Relationship boundaries
- ✅ Professional advice handling
- ✅ Character voice consistency
- ✅ Pattern matching validation

**Bots tested:**
- Elena Rodriguez (Marine Biologist) - 5 tests
- Gabriel (British Gentleman) - 4 tests
- Marcus Thompson (AI Researcher) - 3 tests
- Jake Sterling (Adventure Photographer) - 2 tests
- Aethys (Omnipotent Entity) - 2 tests

**Usage:**
```bash
# Test all characters (default: elena, gabriel, marcus, jake, aethys)
source .venv/bin/activate
python tests/regression/comprehensive_character_regression.py

# Test specific bots
python tests/regression/comprehensive_character_regression.py --bots elena marcus

# Generate JSON report
python tests/regression/comprehensive_character_regression.py \
  --output validation_reports/character_regression_$(date +%Y%m%d_%H%M%S).json

# Custom timeout (default 60s)
python tests/regression/comprehensive_character_regression.py --timeout 90
```

**Example Output:**
```
🎭 WhisperEngine Character Regression Testing
Total Tests:    16
✅ Passed:      10
❌ Failed:      1
⚠️  Warnings:    5
Success Rate:   62.5%
```

---

### `automated_manual_test_regression.py`
Automated health and status checks for all bots based on manual testing procedures.

**What it tests:**
- ✅ Bot health endpoints (all bots)
- ✅ CDL character system integration
- ✅ Infrastructure availability

**Usage:**
```bash
# Test all bots
python tests/regression/automated_manual_test_regression.py

# Test specific bots
python tests/regression/automated_manual_test_regression.py --bots elena marcus gabriel

# Generate JSON report
python tests/regression/automated_manual_test_regression.py \
  --output reports/health_regression_$(date +%Y%m%d_%H%M%S).json
```

## 🎭 Manual Testing Required

For comprehensive character and conversation testing, refer to:
- `docs/manual_tests/CHARACTER_TESTING_MANUAL.md` - Character personality validation
- `docs/manual_tests/MANUAL_TEST_PLAN_VECTOR_INTELLIGENCE.md` - Memory system testing
- `docs/manual_tests/COMPREHENSIVE_TESTING_RESULTS.md` - Expected test results

**Why Discord is Required:**
- WhisperEngine is a **Discord-only platform** for conversations
- Character responses require full event pipeline (message processing, CDL integration, memory)
- Vector intelligence features are triggered by actual Discord messages
- Health APIs only provide infrastructure status, not character behavior

## 📊 Test Reports

Test reports are saved in JSON format with the following structure:
```json
{
  "test_run": {
    "timestamp": "2025-10-15T...",
    "total_tests": 30,
    "passed": 28,
    "failed": 0,
    "skipped": 2,
    "warnings": 0,
    "success_rate": 93.33
  },
  "summary": {
    "overall_status": "PASS",
    "critical_failures": [],
    "warnings": []
  },
  "results_by_category": {...},
  "results_by_bot": {...},
  "detailed_results": [...]
}
```

## 🚀 Quick Start

```bash
# Ensure all bots are running
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps

# Run regression tests
cd /Users/markcastillo/git/whisperengine
python tests/regression/automated_manual_test_regression.py

# For detailed output with report
python tests/regression/automated_manual_test_regression.py \
  --output validation_reports/regression_$(date +%Y%m%d_%H%M%S).json
```

## 🎯 Testing Strategy

1. **Automated Health Checks** (this script) - Infrastructure validation
2. **Manual Discord Testing** (manual guides) - Character behavior validation
3. **Direct Python Testing** (test scripts) - Component-level validation

Use all three approaches for comprehensive regression testing.
