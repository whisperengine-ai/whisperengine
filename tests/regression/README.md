# WhisperEngine Regression Testing Suite

This directory contains automated regression testing scripts for validating WhisperEngine functionality.

## ⭐ NEW: Unified YAML-Driven Test Harness (Phase 3)

### `unified_test_harness.py` 🚀 **RECOMMENDED TEST RUNNER**
**YAML-based test runner with declarative test definitions**

**What it tests:**
- ✅ Character personality and AI ethics (16 tests)
- ✅ Memory storage and conversation continuity (10 tests)
- ✅ Advanced intelligence systems (23 tests, 8 systems)

**Key Features:**
- 📝 Declarative YAML test definitions (easy to read and maintain)
- 🎯 Flexible filtering by type/bot/category
- 📊 Beautiful reporting with archetype awareness
- 🔧 Non-programmers can contribute tests
- 🔄 Backward compatible with legacy test runners

**Quick Start:**
```bash
source .venv/bin/activate

# Run all tests (49 total)
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

**Documentation:**
- `test_definitions/README.md` - Complete YAML schema reference
- `MIGRATION_GUIDE.md` - Python to YAML conversion guide
- `PHASE3_COMPLETE.md` - Phase 3 summary and achievements

---

## 🧪 Legacy Test Scripts (Still Functional)

### `comprehensive_character_regression.py`
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
