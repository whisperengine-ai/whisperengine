# 🚀 Quick Regression Testing Guide

## Run Complete Regression Tests

```bash
cd /Users/markcastillo/git/whisperengine

# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run comprehensive character tests (RECOMMENDED)
python tests/regression/comprehensive_character_regression.py \
  --output validation_reports/character_regression_$(date +%Y%m%d_%H%M%S).json

# 3. Run infrastructure health checks
python tests/regression/automated_manual_test_regression.py
```

## Test Results Location

- **Latest Summary**: `validation_reports/LATEST_REGRESSION_SUMMARY.md`
- **Detailed JSON**: `validation_reports/character_regression_*.json`
- **Test Scripts**: `tests/regression/`

## Current Status (October 15, 2025)

### Overall: 62.5% Pass Rate ⚠️
- **10/16 tests passed**
- **1 test failed** (Gabriel background)
- **5 warnings** (AI disclosure timing, boundary language)

### Bot Status Summary
- ✅ **Aethys**: 100% (2/2) - Perfect
- ⚠️ **Elena**: 40% (2/5) - AI timing issues
- ❌ **Gabriel**: 75% (3/4) - Missing identity traits
- ⚠️ **Marcus**: 67% (2/3) - Minor advice wording
- ⚠️ **Jake**: 50% (1/2) - Not disclosing AI nature

## Critical Issues to Fix

1. **Gabriel**: Missing "devoted companion" core identity
2. **Jake**: Not acknowledging AI nature when asked directly
3. **Elena**: Mentioning AI unprompted in background questions

## Quick Test Commands

```bash
# Test specific bot only
python tests/regression/comprehensive_character_regression.py --bots elena

# Test multiple bots
python tests/regression/comprehensive_character_regression.py --bots elena gabriel marcus

# Increase timeout for slow responses
python tests/regression/comprehensive_character_regression.py --timeout 120

# Health check only (faster)
python tests/regression/automated_manual_test_regression.py
```

## What Gets Tested

### ✅ Character Regression Tests (HTTP Chat API)
- Character personality and voice
- AI ethics and honesty
- Roleplay interaction handling
- Relationship boundaries
- Professional advice guidance
- Pattern matching validation

### ✅ Health Regression Tests (Health API)
- Bot health endpoints
- CDL character data loading
- Infrastructure availability

## View Detailed Results

```bash
# View latest summary
cat validation_reports/LATEST_REGRESSION_SUMMARY.md

# View JSON report (requires jq)
jq '.' validation_reports/character_regression_*.json | less

# List all test reports
ls -lht validation_reports/
```

## Before Deployment Checklist

- [ ] Run comprehensive character regression tests
- [ ] Review `LATEST_REGRESSION_SUMMARY.md`
- [ ] Verify pass rate ≥90%
- [ ] Check no FAILED tests
- [ ] Verify no ERRORS
- [ ] Test critical bots (Elena, Gabriel, Marcus)
- [ ] Update documentation if needed

## Manual Discord Testing (Optional)

For full validation including memory/emotion systems, see:
- `docs/manual_tests/CHARACTER_TESTING_MANUAL.md`
- `docs/manual_tests/DISCORD_REGRESSION_CHECKLIST.md`

---

**Last Updated**: October 15, 2025  
**Next Test**: After fixing critical issues
