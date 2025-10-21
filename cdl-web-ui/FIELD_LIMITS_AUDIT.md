# CDL Web UI Field Limits Audit
**Date**: October 21, 2025

## Current UI Field Limits vs Database Schema

### 1. Basic Tab (characters table)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| name | 100 | 500 | ⚠️ TOO RESTRICTIVE | Should be 500 |
| occupation | 150 | 500 | ⚠️ TOO RESTRICTIVE | Should be 500 |
| description | 1000 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| location | 100 | TEXT (unlimited) | ✅ OK | Stored in character_identity_details |
| archetype | N/A | 100 | ✅ OK | Dropdown field |

### 2. Background Tab (character_background table)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| title | 200 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| description | 2000 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| period | 100 | 100 | ✅ MATCH | Perfect |
| category | N/A | 50 | ⚠️ NEEDS CHECK | Dropdown - need to verify options |

### 3. Interests Tab (character_interests table)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| interest_text | 1500 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| category | N/A | 200 | ⚠️ NEEDS CHECK | Dropdown - need to verify options |
| importance | N/A | 100 | ✅ OK | Dropdown field |

### 4. Communication Patterns Tab (character_communication_patterns table)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| pattern_value | 1500 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| pattern_name | N/A | 100 | ⚠️ NEEDS CHECK | Need to verify input type |
| pattern_type | N/A | 50 | ⚠️ NEEDS CHECK | Dropdown - need to verify options |
| context | N/A | 100 | ⚠️ NEEDS CHECK | Need to verify input type |
| frequency | N/A | 20 | ⚠️ NEEDS CHECK | Dropdown - need to verify options |

### 5. Speech Patterns Tab (character_speech_patterns table)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| pattern_value | 800 | TEXT (unlimited) | ✅ OK | Reasonable user limit |
| pattern_type | N/A | 100 | ⚠️ NEEDS CHECK | Need to verify input type |
| context | N/A | 100 | ⚠️ NEEDS CHECK | Need to verify input type |
| usage_frequency | N/A | 50 | ⚠️ NEEDS CHECK | Dropdown - need to verify options |

### 6. Response Style Tab (character_response_guidelines/modes tables)
| Field | UI Limit | DB Limit | Status | Notes |
|-------|----------|----------|--------|-------|
| item_text | 2000 | N/A | ❌ SCHEMA MISMATCH | API expects guidelines/modes, not items |

## Critical Issues Found

### Issue #1: Response Style API Mismatch ❌ CRITICAL
**Problem**: 
- Form sends: `{ items: [...] }` with `item_type`, `item_text`, `sort_order`
- API expects: `{ guidelines: [...], modes: [...] }` with different field structures
- This causes response style data to NOT SAVE!

**Fix Required**: Update response-style API to handle legacy `items` format OR update form to send correct format

### Issue #2: Field Limits Too Restrictive ⚠️
**Problem**:
- UI limits `name` to 100 chars but DB allows 500
- UI limits `occupation` to 150 chars but DB allows 500

**Fix Required**: Update FIELD_LIMITS constant to match DB constraints

### Issue #3: Missing Field Validations ⚠️
**Problem**: Several fields have DB constraints but no UI validation:
- pattern_name (100 char limit)
- pattern_type (50-100 char limit)
- context (100 char limit)
- frequency (20-50 char limit)

**Fix Required**: Add UI field limits for these fields

## API Endpoints Status

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/characters/[id]` | PUT | ✅ FIXED | Now handles archetype & allow_full_roleplay |
| `/api/characters/[id]/background` | PUT | ✅ OK | Correctly saves to character_background |
| `/api/characters/[id]/interests` | PUT | ✅ OK | Correctly saves to character_interests |
| `/api/characters/[id]/communication-patterns` | PUT | ✅ OK | Correctly saves to character_communication_patterns |
| `/api/characters/[id]/speech-patterns` | PUT | ✅ OK | Correctly saves to character_speech_patterns |
| `/api/characters/[id]/response-style` | PUT | ❌ BROKEN | Expects guidelines/modes but receives items |

## Recommended Actions

1. **URGENT**: Fix response-style API mismatch (prevents saving)
2. **HIGH**: Update field limits for name and occupation
3. **MEDIUM**: Add field limits for pattern_name, pattern_type, context, frequency
4. **LOW**: Add helpful tooltips showing field limits to users
