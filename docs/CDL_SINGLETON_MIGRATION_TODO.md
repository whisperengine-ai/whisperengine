# CDL Singleton Migration TODO

## Overview

This document outlines the remaining work needed to fully migrate WhisperEngine from multiple CDL file reads to the new singleton CDL Manager pattern. The CDL Manager (`src/characters/cdl/manager.py`) has been implemented and is working, but several parts of the codebase still use the old file-reading approach.

## Current Status

### ✅ COMPLETED
- **CDL Manager Implementation** (`src/characters/cdl/manager.py`)
  - Thread-safe singleton pattern with lazy loading
  - Generic field access via dot notation
  - One-time file read from `CHARACTER_FILE` environment variable
  - In-memory caching with schema validation
  - Convenience methods for common fields

- **Conversation Flow Guidelines** (`src/prompts/cdl_ai_integration.py`)
  - `_extract_conversation_flow_guidelines()` method updated to use CDL manager
  - No more file re-reading for conversation flow data
  - Works with Elena's conversation flow guidelines

### 🚨 NEEDS MIGRATION

## Phase 1: Core Runtime Migration (HIGH PRIORITY)

### 1. CDL AI Integration (`src/prompts/cdl_ai_integration.py`)

**Current Issues:**
- Still takes `character_file` parameter in `create_unified_character_prompt()`
- Still calls `load_character(character_file)` for every message
- Uses Character object properties like `character.identity.name`, `character.personality.big_five`
- Has its own `load_character()` method that reads files directly

**Migration Tasks:**
```python
# BEFORE (current):
async def create_unified_character_prompt(self, character_file: str, user_id: str, ...):
    character = await self.load_character(character_file)
    prompt = f"You are {character.identity.name}, a {character.identity.occupation}."

# AFTER (target):
async def create_unified_character_prompt(self, user_id: str, ...):
    character_name = get_cdl_field("character.metadata.name")
    occupation = get_cdl_field("character.identity.occupation")
    prompt = f"You are {character_name}, a {occupation}."
```

**Specific Files to Update:**
- Line 33: Remove `character_file: str` parameter
- Line 52: Replace `await self.load_character(character_file)` with CDL manager calls
- Line 145: Replace `character.identity.name` with `get_cdl_field("character.metadata.name")`
- Line 145: Replace `character.identity.occupation` with `get_cdl_field("character.identity.occupation")`
- Line 148-149: Replace `character.identity.description` with `get_cdl_field("character.identity.description")`
- Line 152-153: Replace `character.personality.big_five` with `get_cdl_field("character.personality.big_five")`
- Lines 232, 248, 253, 262, 322: Replace all `character.identity.name` references
- Line 371: Replace `character.personal_background` access

**Benefits:**
- Eliminates file reading on every message (major performance improvement)
- Reduces memory usage (no Character object creation)
- Simplifies API (no file parameter needed)

### 2. Character Bridge Migration (`src/characters/bridge.py`)

**Current Issues:**
- Has its own `load_character(character_file_path: str)` method
- Used for dynamic character switching operations
- May conflict with CDL manager singleton approach

**Migration Considerations:**
- Character bridge handles multiple characters, CDL manager handles single character
- May need CDL manager enhancement to support character switching
- Or character bridge could coordinate multiple CDL manager instances

## Phase 2: Development Tools Migration (MEDIUM PRIORITY)

### 1. Validation Files

**Files to Update:**
- `src/validation/cdl_validator.py` (Line 189: `character = load_character(str(file_path))`)
- `src/validation/pattern_tester.py` (Line 245: `character = load_character(str(file_path))`)

**Migration Strategy:**
- These tools validate arbitrary CDL files, not just the current character
- May need CDL manager enhancement: `CDLManager.load_from_file(file_path)`
- Or keep using direct file loading since these are development tools

### 2. Bulk Loading Function

**File:** `src/prompts/cdl_ai_integration.py`
**Function:** `load_character_definitions()` (Line 512)

**Current Issue:**
- Loads multiple character files for discovery/comparison
- Uses `load_character(file_path)` for each file

**Migration Options:**
1. Keep as-is (development-only function)
2. Create CDL manager bulk loading capability
3. Remove if no longer needed

## Phase 3: API Cleanup (LOW PRIORITY)

### 1. Remove Unused Methods
- `CDLAIPromptIntegration.load_character()` method
- Cleanup imports of `load_character` from parser
- Remove `character_file` parameters from public APIs

### 2. Update Call Sites
**Files that call CDL AI Integration:**
- Find all calls to `create_unified_character_prompt(character_file, ...)`
- Update to `create_unified_character_prompt(...)` (remove file parameter)
- Ensure `CHARACTER_FILE` environment variable is set before calls

### 3. Documentation Updates
- Update API documentation to reflect CDL manager usage
- Update examples and demos
- Update architecture documentation

## Implementation Guidelines

### CDL Manager Field Access Patterns

```python
# Basic field access
name = get_cdl_field("character.metadata.name", "Unknown")
occupation = get_cdl_field("character.identity.occupation", "")

# Nested object access
big_five = get_cdl_field("character.personality.big_five", {})
openness = big_five.get("openness", 0.5) if big_five else 0.5

# Complex field access with fallbacks
description = get_cdl_field("character.identity.description")
if not description:
    description = get_cdl_field("character.metadata.description", "")

# Check field existence before access
if has_cdl_field("character.personality.big_five"):
    personality = get_cdl_field("character.personality.big_five")
    # Process personality data
```

### Error Handling Patterns

```python
# Graceful fallback if CDL data unavailable
try:
    character_name = get_cdl_field("character.metadata.name")
    if not character_name:
        character_name = "AI Assistant"  # Fallback
except Exception:
    character_name = "AI Assistant"  # Ultimate fallback
```

### Character Switching Considerations

```python
# Current: Single character per bot instance via CHARACTER_FILE
# Future: May need CDL manager enhancement for character switching

# Option 1: Reset and reload
cdl_manager = get_cdl_manager()
cdl_manager.reset_instance()  # Clear current character
os.environ['CHARACTER_FILE'] = new_character_file
new_name = get_character_name()  # Loads new character

# Option 2: Multiple managers (if needed)
elena_manager = CDLManager.for_character("elena.json")
marcus_manager = CDLManager.for_character("marcus.json")
```

## Testing Strategy

### 1. Backward Compatibility Testing
- Ensure existing functionality works during migration
- Test with all current character files (Elena, Marcus, Jake, etc.)
- Verify conversation flow guidelines still work

### 2. Performance Testing
- Measure file read reduction (should be 1 read per bot startup vs N reads per conversation)
- Memory usage comparison (CDL manager vs Character objects)
- Response time improvements

### 3. Migration Testing
- Test each phase incrementally
- Rollback plan if issues found
- Validate CDL manager with different character file structures

## Success Criteria

### Phase 1 Complete When:
- ✅ No file reading in `create_unified_character_prompt()`
- ✅ Character object references replaced with CDL manager calls
- ✅ Elena bot works with updated CDL integration
- ✅ Performance improvement measurable

### Phase 2 Complete When:
- ✅ Validation tools work with CDL manager or explicit file loading
- ✅ Character bridge integration resolved
- ✅ All development tools functional

### Phase 3 Complete When:
- ✅ No unused `load_character()` methods
- ✅ Clean API without `character_file` parameters
- ✅ Updated documentation and examples
- ✅ All call sites updated

## Risk Mitigation

### 1. Character File Structure Changes
- **Risk:** Different characters have different JSON structures
- **Mitigation:** CDL manager handles field path variations
- **Example:** Elena's `character.communication.conversation_flow_guidelines` vs others

### 2. Performance Regression
- **Risk:** CDL manager overhead could be worse than file reading
- **Mitigation:** Benchmark before/after, optimize if needed
- **Fallback:** Keep file reading option available

### 3. Multi-Character Support
- **Risk:** CDL manager singleton may not support character switching
- **Mitigation:** Design character switching enhancement or multiple managers
- **Test:** Character bridge compatibility

## Future Enhancements

### 1. Schema Validation Enhancement
- Runtime schema validation for CDL fields
- Type checking for field access
- Automatic migration warnings for deprecated fields

### 2. Hot Reloading
- Watch CHARACTER_FILE for changes
- Reload CDL data without bot restart
- Development-friendly character editing

### 3. Multi-Character Support
- Support multiple characters in single bot instance
- Character switching via CDL manager API
- Memory isolation per character

---

## Quick Start for Contributors

To continue the CDL singleton migration:

1. **Start with Phase 1** - Update `src/prompts/cdl_ai_integration.py`
2. **Test with Elena** - She has the most complex CDL structure
3. **Use the patterns** - Follow the field access patterns above
4. **Check performance** - Measure file read reduction
5. **Document changes** - Update this TODO as you go

The CDL manager is ready and working - it just needs integration with the existing codebase!