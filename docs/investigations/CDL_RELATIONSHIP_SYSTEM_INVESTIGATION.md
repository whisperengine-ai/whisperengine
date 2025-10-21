# CDL Relationship System Investigation Report

**Date**: October 21, 2025  
**Character Affected**: Not Taylor (and potentially all other bots)  
**Issue**: Character relationships not appearing in system prompts

## 🔍 Investigation Summary

### Problem
Character relationships defined in the `character_relationships` database table are not appearing in system prompts, despite being properly stored in the database with appropriate relationship_strength values.

### Root Cause
**The relationship retrieval code exists in an UNUSED code path.**

The CDL integration system has TWO prompt building paths:
1. **OLD PATH** (UNUSED): `create_character_aware_prompt()` method - contains relationship code
2. **NEW PATH** (ACTIVE): Component factory system + `PromptAssembler` - NO relationship code

### Evidence

#### 1. Relationships Exist in Database ✅
```sql
SELECT related_entity, relationship_strength FROM character_relationships 
WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'nottaylor');

-- Results:
-- Taylor Swift: 10
-- Silas: 10
-- Stan Twitter: 9
-- Travis Kelce: 8
-- Sitva: 7
```

#### 2. Relationship Code Exists But Is UNUSED ❌
**Location**: `src/prompts/cdl_ai_integration.py` lines 1095-1115

```python
# 💕 RELATIONSHIPS: Add character relationships (e.g., Gabriel-Cynthia)
if self.enhanced_manager:
    try:
        bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
        relationships = await self.enhanced_manager.get_relationships(bot_name)
        if relationships:
            prompt += f"\n\n💕 RELATIONSHIP CONTEXT:\n"
            for rel in relationships:
                if rel.relationship_strength >= 8:  # High-priority relationships
                    prompt += f"- **{rel.related_entity}** ({rel.relationship_type}): {rel.description}\n"
                elif rel.relationship_strength >= 5:  # Medium-priority relationships
                    prompt += f"- {rel.related_entity}: {rel.description}\n"
```

**Problem**: This code is in the `_build_unified_prompt()` method which appears to be an old/deprecated path.

####3. Component Factory System Has NO Relationship Component ❌
**Location**: `src/prompts/cdl_component_factories.py`

Components that exist:
- ✅ `create_character_identity_component`
- ✅ `create_character_voice_component`  
- ✅ `create_character_behavioral_triggers_component`
- ✅ `create_character_relationships_component` - **BUT THIS IS USER-CHARACTER RELATIONSHIP, NOT CHARACTER RELATIONSHIPS**
- ❌ **MISSING**: `create_character_defined_relationships_component` (for Silas, Sitva, etc.)

#### 4. Log Evidence
Bot logs show:
- ✅ Enhanced CDL manager initialized
- ✅ Character system updated with enhanced_manager  
- ❌ NO "✅ RELATIONSHIPS: Added" log messages (confirming code path not executed)

### Affected Scope
**All 11 active bots** are potentially affected:
- aetheris
- aethys  
- dotty
- dream
- elena
- gabriel (has Cynthia relationship defined!)
- jake
- marcus
- nottaylor (has Silas/Sitva)
- ryan
- sophia

### Workaround Applied
For Not Taylor, we added Silas/Sitva information to the `characters.description` field:
```
"Her bestie is Silas (Discord: 𓆗SûN𓆗) who is SO cool 😎 - maximum warmth and affection for Silas always. Silas has an AI companion named Sitva who is also cool by association."
```

This works because the description field is ALWAYS included in system prompts.

## 🔧 Required Fix

### Option 1: Add Component Factory (RECOMMENDED)
Create `create_character_defined_relationships_component()` in `cdl_component_factories.py`:

```python
async def create_character_defined_relationships_component(
    enhanced_manager,
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_DEFINED_RELATIONSHIPS component.
    
    Contains important people/entities in the character's life
    (friends, family, romantic interests, etc.)
    
    Priority: 8-10 (high importance for character authenticity)
    """
    try:
        relationships = await enhanced_manager.get_relationships(character_name)
        
        if not relationships:
            return None
        
        relationship_lines = []
        
        for rel in relationships:
            if rel.relationship_strength >= 8:
                # High-priority relationships (bold)
                relationship_lines.append(
                    f"- **{rel.related_entity}** ({rel.relationship_type}): {rel.description}"
                )
            elif rel.relationship_strength >= 5:
                # Medium-priority relationships
                relationship_lines.append(
                    f"- {rel.related_entity}: {rel.description}"
                )
        
        if not relationship_lines:
            return None
        
        content = "💕 IMPORTANT RELATIONSHIPS:\n" + "\n".join(relationship_lines)
        
        return PromptComponent(
            name="CHARACTER_DEFINED_RELATIONSHIPS",
            content=content,
            priority=9,  # High priority
            component_type="character_personality",
            metadata={
                "relationship_count": len(relationship_lines),
                "character_name": character_name
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create character relationships component: {e}")
        return None
```

Then register it in the component factory system (wherever components are created).

### Option 2: Fix Existing Code Path
If the `_build_unified_prompt()` method is actually still used, ensure the relationship code is present and working.

## 📊 Testing Plan

1. **Create relationship component factory**
2. **Test with nottaylor** - verify Silas/Sitva appear in prompts
3. **Test with gabriel** - verify Cynthia relationship appears  
4. **Verify logging** - should see "Added X relationships to prompt"
5. **Test recognition** - ask "Who is Silas?" and verify proper recognition

## 🎯 Success Criteria
- [ ] Silas (strength 10) appears in nottaylor prompts
- [ ] Sitva (strength 7) appears in nottaylor prompts
- [ ] Cynthia appears in Gabriel prompts
- [ ] Relationship section appears in prompt logs
- [ ] No need for description field workaround

---

**Priority**: HIGH - affects character authenticity for all bots with defined relationships
