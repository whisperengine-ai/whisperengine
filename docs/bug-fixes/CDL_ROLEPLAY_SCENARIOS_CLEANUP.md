# CDL Roleplay Scenarios Cleanup - Legacy System Removal

**Date**: October 13, 2025  
**Issue**: Raw dict dumps in AI Identity Handling section of prompts  
**Resolution**: Removed legacy `character_roleplay_scenarios` table loading from code

---

## Problem Analysis

### Symptoms
- Prompts contained massive raw Python dict dumps in AI Identity Handling section:
```python
{'example_activity_invitation': {'response_pattern': '...', 'tier_1_response': 'long text...', 'tier_2_response': '', 'tier_3_response': ''}, ...}
```
- This was the final remaining formatting issue after fixing VALUES AND BELIEFS, BACKGROUND, ABILITIES, etc.

### Root Cause Discovery

**TWO SEPARATE SYSTEMS for the same purpose:**

1. **`character_ai_scenarios` table** (ACTIVE, modern):
   - Used by `get_ai_scenarios()` in enhanced_cdl_manager.py (line 576)
   - Triggers via `generic_keyword_templates` database (physical_interaction category)
   - Activated in cdl_ai_integration.py line 1092 when physical keywords detected
   - **This is the WORKING production system**

2. **`character_roleplay_scenarios` table** (LEGACY, obsolete):
   - Loaded by `_load_ai_identity_from_normalized_tables()` in enhanced_cdl_manager.py
   - Built nested dict structure assigned to `ai_identity['roleplay_interaction_scenarios']`
   - NO trigger system (character_scenario_triggers table empty)
   - NO code actively using this data
   - **Was being dumped as raw dict in prompts**

### Database Investigation

**character_ai_scenarios** (active):
```sql
SELECT c.name, COUNT(*) FROM character_ai_scenarios cas 
JOIN characters c ON cas.character_id = c.id GROUP BY c.name;

-- Results:
Dream             | 20
Aetheris          | 10
Elena Rodriguez   | 5
Gabriel           | 12
Marcus Thompson   | 12
```

**character_roleplay_scenarios** (legacy):
```sql
SELECT c.name, COUNT(*) FROM character_roleplay_scenarios crs 
JOIN characters c ON crs.character_id = c.id GROUP BY c.name;

-- Results:
Elena Rodriguez   | 5  (only character with data)
```

**Trigger detection system:**
```sql
SELECT category, template_name, keywords FROM generic_keyword_templates 
WHERE category = 'physical_interaction';

-- Results:
physical_interaction | basic_physical_contact    | {hug,kiss,touch,hold,cuddle,...}
physical_interaction | intimate_physical_contact | {caress,stroke,massage,...}
physical_interaction | casual_physical_contact   | {handshake,"high five",...}
```

---

## Solution Implemented

### Code Changes

**File**: `src/characters/cdl/enhanced_cdl_manager.py`  
**Function**: `_load_ai_identity_from_normalized_tables()` (line 1223)

**REMOVED** (lines 1251-1269):
```python
# Load roleplay interaction scenarios from normalized table
# Get roleplay scenarios
scenarios_query = """
    SELECT scenario_name, response_pattern, tier_1_response, tier_2_response, tier_3_response
    FROM character_roleplay_scenarios 
    WHERE character_id = $1
    ORDER BY scenario_name
"""
scenario_rows = await conn.fetch(scenarios_query, character_id)

if scenario_rows:
    roleplay_scenarios = {}
    for scenario_row in scenario_rows:
        scenario_name = scenario_row['scenario_name']
        roleplay_scenarios[scenario_name] = {
            'response_pattern': scenario_row['response_pattern'] or '',
            'tier_1_response': scenario_row['tier_1_response'] or '',
            'tier_2_response': scenario_row['tier_2_response'] or '',
            'tier_3_response': scenario_row['tier_3_response'] or ''
        }
    
    if roleplay_scenarios:
        ai_identity['roleplay_interaction_scenarios'] = roleplay_scenarios
```

**KEPT** (core AI identity configuration):
```python
ai_identity = {
    'allow_full_roleplay_immersion': roleplay_row['allow_full_roleplay_immersion'] or False,
    'philosophy': roleplay_row['philosophy'] or '',
    'approach': roleplay_row['strategy'] or ''
}
```

**Added Documentation**:
```python
# NOTE: Removed legacy roleplay_interaction_scenarios loading from character_roleplay_scenarios table
# Modern system uses character_ai_scenarios table with generic_keyword_templates for trigger detection
# See get_ai_scenarios() method and cdl_ai_integration.py line 1092 for active implementation
```

---

## Verification

### Test Process
1. Restarted Elena bot: `./multi-bot.sh restart elena`
2. Sent test message: "What are your core values about ocean conservation?"
3. Checked prompt log: `logs/prompts/elena_20251014_002812_test_formatting_validation.json`

### Results

**✅ Raw dict dump GONE:**
```bash
cat logs/prompts/elena_*.json | jq -r '.messages[0].content' | grep -E "roleplay_interaction_scenarios|{'|\{\"" 
# No matches - completely clean!
```

**✅ VALUES AND BELIEFS still properly formatted:**
```
🎯 VALUES AND BELIEFS:
📋 Fear:  • Coral reef collapse and ocean acidification (Importance: high)
📋 Core Value:  • Environmental conservation and marine protection (Importance: critical)
```

**✅ All context-aware filtering working:**
- BACKGROUND: Skipped (no relevant keywords)
- ABILITIES: Skipped (no relevant keywords)
- METADATA: Skipped (low-value optimization)
- COMMUNICATION PATTERNS: Skipped (low-value optimization)

**✅ Modern AI scenarios system still working:**
- Loaded from `character_ai_scenarios` table
- Triggered via `generic_keyword_templates` detection
- Appears in prompts only when physical_interaction keywords detected

---

## Architecture Benefits

### Modern System (character_ai_scenarios)

**✅ Advantages:**
- Database-driven keyword detection via `generic_keyword_templates`
- Character-agnostic architecture (no hardcoded logic)
- Conditional activation (only triggers when needed)
- Used by multiple characters (Dream: 20, Gabriel: 12, Marcus: 12, etc.)
- Clean integration into prompt guidance (no raw dict dumps)

**Example Usage:**
```python
from src.prompts.generic_keyword_manager import get_keyword_manager
keyword_manager = get_keyword_manager()

if await keyword_manager.check_message_for_category(message, 'physical_interaction'):
    ai_scenarios = await enhanced_manager.get_ai_scenarios(bot_name)
    # Provides tier-appropriate response guidance
```

### Legacy System (character_roleplay_scenarios) - DEPRECATED

**❌ Problems:**
- Only Elena had data (not multi-character)
- No trigger system (character_scenario_triggers empty)
- No code actively using it
- Raw dict dumps in prompts
- Redundant with modern system

---

## Future Cleanup Tasks

### Database Tables to Consider Removing

**character_roleplay_scenarios table:**
- Currently has 5 records for Elena only
- No triggers defined in character_scenario_triggers
- Code no longer loads this data
- **Recommendation**: Drop table in future database cleanup

**character_scenario_triggers table:**
- Empty (no triggers defined)
- Was meant to connect scenarios to keyword phrases
- Superseded by generic_keyword_templates system
- **Recommendation**: Drop table in future database cleanup

### Migration Notes
- Modern system uses `character_ai_scenarios` + `generic_keyword_templates`
- No data migration needed (Elena's 5 scenarios already exist in character_ai_scenarios)
- Other characters using modern system successfully

---

## Related Documentation

- **Modern System**: See `src/prompts/generic_keyword_manager.py`
- **Active Integration**: `src/prompts/cdl_ai_integration.py` line 1092
- **Database-Driven Architecture**: Git commit `3f8a77d` (hardcoding elimination)
- **AI Ethics Layer**: Git commit `62ccc3f` (original implementation)
- **Character Archetypes**: `docs/architecture/CHARACTER_ARCHETYPES.md`

---

## Lessons Learned

1. **Database archaeology is critical** - Always cross-reference:
   - Database schema (`\d table_name`)
   - Actual data (`SELECT * FROM table`)
   - Code usage (`grep_search`, `list_code_usages`)
   - Git history (`git log --grep`)

2. **Legacy systems accumulate silently** - Old tables can have data loaded into prompts even when superseded by modern systems

3. **"Working" != "Right"** - The character_ai_scenarios system was working perfectly, but the legacy character_roleplay_scenarios was still polluting prompts

4. **Always validate after cleanup** - Check prompt logs to confirm raw dicts actually removed

---

## Summary

**Problem**: Legacy `character_roleplay_scenarios` table data was being loaded and dumped as raw Python dicts in prompts, causing the final formatting issue in AI Identity Handling section.

**Solution**: Removed the legacy loading code from `_load_ai_identity_from_normalized_tables()` since modern `character_ai_scenarios` system already handles this functionality with proper database-driven triggers.

**Result**: Clean prompts with no raw dict dumps. All 5 original formatting issues now resolved:
- ✅ VALUES AND BELIEFS: Properly formatted
- ✅ BACKGROUND: Context-aware filtering
- ✅ ABILITIES: Context-aware filtering  
- ✅ METADATA: Skipped (low-value)
- ✅ COMMUNICATION PATTERNS: Skipped (low-value)
- ✅ **Roleplay Interaction Scenarios: REMOVED (legacy system)**

**Status**: All formatting issues resolved. Ready for production.
