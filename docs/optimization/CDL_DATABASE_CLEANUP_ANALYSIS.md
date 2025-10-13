# CDL Database Cleanup - Root Cause Analysis

**Date**: October 13, 2025  
**Issue**: Bloated character prompts from redundant/empty CDL data

## 🎯 Root Cause: CDL Database Contains Bloat

Looking at Elena's actual prompt, the problem is **NOT the prompt builder** - it's the **CDL DATABASE DATA** itself:

### **Example: Empty Background Data** (from Elena's prompt)
```
📋 Education:
  • {'period': None, 'title': 'Education', 'description': '', 'date_range': None, 'importance_level': 8}
  • {'period': None, 'title': 'Education', 'description': '', 'date_range': None, 'importance_level': 8}
  • {'period': None, 'title': 'Education', 'description': '', 'date_range': None, 'importance_level': 8}

📋 Career:
  • {'period': None, 'title': 'Career History', 'description': '', 'date_range': None, 'importance_level': 7}
  • {'period': None, 'title': 'Career History', 'description': '', 'date_range': None, 'importance_level': 7}
  • {'period': None, 'title': 'Career History', 'description': '', 'date_range': None, 'importance_level': 7}
```

**Problem**: 3 duplicate empty entries for Education, 3 for Career, 3 for Personal = **~800 chars of useless data**

### **Example: Verbose Conversation Flow** (from Elena's prompt)
```
📋 Conversation Flow Guidance:
  • Marine Education: {'energy': 'Enthusiastic and educational', 'approach': 'Use oceanic metaphors...', 
     'avoid': ['Overly technical jargon...', 'Dismissing non-scientific...', 'Being dry or academic...', 
                'Forgetting to connect to personal experience'],
     'encourage': ['Oceanic metaphors and marine analogies', 'Scientific accuracy with accessible explanations', 
                    'Environmental consciousness and conservation', 'Personal stories from research experiences'],
     'examples': ['Think of it like ocean currents...', "In my research, I've observed...", 'The ocean teaches us that...']}
  • Passionate Discussion: {...}
  • General: {...}
  • Response Style: {huge dict with core_principles, formatting_rules, character_specific_adaptations...}
```

**Problem**: Showing ALL modes when only ONE is active = **~2,000 chars when only ~300 needed**

## ✅ What We Fixed in Code

**Priority 1 Optimizations** (already implemented):
1. ✅ Trigger-aware conversation flow - only show ACTIVE mode
2. ✅ Deduplicate response guidelines - remove early duplicate

**Savings**: ~2,700 chars (13% reduction)

## 🎯 What SHOULD Be Fixed: Clean the CDL Database

### **Immediate Database Cleanup Tasks**:

#### 1. Remove Empty Background Entries
**Query**:
```sql
-- Find empty background entries
SELECT character_id, COUNT(*) 
FROM character_background 
WHERE description IS NULL OR description = '' OR TRIM(description) = ''
GROUP BY character_id;

-- DELETE empty entries
DELETE FROM character_background 
WHERE description IS NULL OR description = '' OR TRIM(description) = '';
```

**Impact**: ~800 chars saved per character

#### 2. Deduplicate Background Entries
**Query**:
```sql
-- Find duplicates
SELECT character_id, title, COUNT(*) 
FROM character_background 
GROUP BY character_id, title 
HAVING COUNT(*) > 1;

-- DELETE duplicates (keep one)
WITH ranked AS (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY character_id, title ORDER BY id) as rn
  FROM character_background
)
DELETE FROM character_background 
WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
```

**Impact**: Removes duplicate "Education", "Career", "Personal" entries

#### 3. Streamline Conversation Flow Guidance
**Instead of storing massive nested dicts**, store:
- Active mode guidance only when needed
- Remove verbose arrays (limit to 2-3 items max)
- Remove redundant "examples" arrays
- Keep only essential fields (energy, approach, top 2 encourage/avoid)

**Tables to review**:
- `character_conversation_flows`
- `character_conversation_modes`
- `character_mode_guidance`
- `character_response_style`
- `character_response_style_items`

#### 4. Remove Redundant AI Identity Scenarios
**Current**: Stores 5-6 different physical interaction scenarios with full response patterns
**Better**: Store ONE general physical interaction guidance + tier structure

**Table**: `character_ai_scenarios`, `character_roleplay_scenarios_v2`

### **Long-Term CDL Schema Optimization**:

1. **Normalize nested dicts** - Don't store massive JSON blobs
2. **Active-only mode storage** - Store modes separately, load only active
3. **Deduplicate common patterns** - Use templates + overrides
4. **Remove empty/null entries** - Database constraint to prevent empty strings
5. **Consolidate response guidance** - Single source of truth, not duplicated across tables

## 📊 Expected Impact from Database Cleanup

| Cleanup | Current Size | After Cleanup | Savings |
|---------|-------------|---------------|---------|
| Remove empty background | ~800 chars | 0 | ~800 chars |
| Dedupe background entries | ~600 chars | ~200 chars | ~400 chars |
| Streamline conv flow | ~2000 chars | ~400 chars | ~1600 chars |
| Simplify AI scenarios | ~600 chars | ~200 chars | ~400 chars |
| **TOTAL** | **~4,000 chars** | **~800 chars** | **~3,200 chars** |

**Combined with code optimizations**:
- Code: ~2,700 chars saved
- Data: ~3,200 chars saved
- **Total**: ~5,900 chars saved (29% reduction)

**Projected prompt size**:
- Current: 20,358 chars ≈ 6,000 tokens
- After code fixes: ~17,658 chars ≈ 5,200 tokens
- After data cleanup: ~14,458 chars ≈ 4,300 tokens
- **Result**: Under 2,500 token target? Still need more cleanup, but huge progress!

## 🎯 Recommended Approach

**Option A: Quick Wins** (Do this first)
1. ✅ Code optimizations (already done) - ~2,700 chars
2. 🔧 Database cleanup script - ~3,200 chars
3. 📊 Test with Elena, validate prompt size
4. 🚀 Apply to all characters

**Option B: Comprehensive Redesign** (Future)
1. Redesign CDL schema for efficiency
2. Migrate all characters to new schema
3. Update prompt builder for new schema
4. Much bigger project, but cleaner long-term

## 🚀 Next Steps

1. **Create database cleanup script** (`scripts/cleanup_cdl_bloat.py`):
   - Remove empty background entries
   - Deduplicate background entries
   - Streamline conversation flow data
   - Simplify AI scenario data

2. **Test on Elena first**:
   - Run cleanup script
   - Restart bot
   - Check prompt log
   - Validate prompt size reduction

3. **Apply to all characters if successful**

4. **Document actual results**

---

**Status**: 🎯 Analysis Complete - Database cleanup is the real fix  
**Recommendation**: Focus on cleaning CDL data, not patching prompt builder  
**Expected Total Impact**: 29% prompt reduction (~5,900 chars)
