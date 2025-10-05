# PostgreSQL Fact Retrieval Testing Guide
**Date**: October 5, 2025  
**Branch**: `feature/postgres-fact-storage-cleanup`  
**Bots Running**: Elena, Dotty

---

## ✅ Bot Status

Both bots are running with the new PostgreSQL fact retrieval code:
- **Elena**: `whisperengine-elena-bot` (port 9091)
- **Dotty**: `whisperengine-dotty-bot` (port 3007)

Both bots have:
- ✅ PostgreSQL pool initialized
- ✅ Semantic Knowledge Router initialized
- ✅ New `_get_user_facts_from_postgres()` method available

---

## 🧪 Test Scenarios

### **Test 1: Store Facts via Discord Message**

**Send to Elena or Dotty:**
```
I love pizza and sushi. I also enjoy hiking and photography.
```

**Expected Behavior:**
1. Facts stored in PostgreSQL via `_extract_and_store_knowledge()`
2. Entities: pizza (food), sushi (food), hiking (hobby), photography (hobby)
3. Check logs for: `"✅ KNOWLEDGE: Stored fact 'pizza' (food)"`

**Validation:**
```bash
# Check PostgreSQL storage
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT fe.entity_name, fe.entity_type, ufr.relationship_type, ufr.confidence
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
ORDER BY ufr.updated_at DESC
LIMIT 10;
"
```

---

### **Test 2: Store Preference via Discord Message**

**Send to Elena or Dotty:**
```
My name is Mark, you can call me Mark
```

**Expected Behavior:**
1. Preference stored in PostgreSQL via `_extract_and_store_user_preferences()`
2. Preference: preferred_name = "Mark"
3. Check logs for: `"✅ PREFERENCE: Stored preferred name 'Mark'"`

**Validation:**
```bash
# Check PostgreSQL preferences
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT universal_id, preferences
FROM universal_users
WHERE preferences IS NOT NULL
ORDER BY last_active DESC
LIMIT 5;
"
```

---

### **Test 3: Retrieve Facts in Next Conversation**

**Send follow-up message:**
```
What do you remember about me?
```

**Expected Behavior:**
1. Bot queries PostgreSQL via `_get_user_facts_from_postgres()`
2. Logs show: `"✅ POSTGRES FACTS: Retrieved X facts/preferences from PostgreSQL"`
3. Bot response includes your facts: "You love pizza and sushi, enjoy hiking..."

**Validation Logs:**
```bash
# Elena logs
docker logs whisperengine-elena-bot 2>&1 | grep "POSTGRES FACTS"

# Dotty logs  
docker logs whisperengine-dotty-bot 2>&1 | grep "POSTGRES FACTS"

# Expected:
# "✅ POSTGRES FACTS: Retrieved 5 facts/preferences from PostgreSQL (facts: 4, preferences: 1)"
```

---

### **Test 4: Fallback to Legacy (if PostgreSQL fails)**

**Scenario**: If PostgreSQL query fails or returns no data, system falls back to legacy string parsing.

**Validation Logs:**
```bash
# Check for fallback usage
docker logs whisperengine-elena-bot 2>&1 | grep "LEGACY FACTS"

# If you see this, it means PostgreSQL didn't return data:
# "⚠️ LEGACY FACTS: Used X facts from memory string parsing (fallback)"
```

---

## 📊 Performance Monitoring

### **Query Timing (should be 2-5ms)**

Watch logs during conversation for timing:
```bash
# Follow logs in real-time
docker logs whisperengine-elena-bot -f

# Send message and watch for:
# "✅ POSTGRES FACTS: Retrieved 5 facts/preferences from PostgreSQL"
# (query should be nearly instant)
```

### **Memory Usage**

```bash
# Check bot memory
docker stats whisperengine-elena-bot --no-stream

# Should be similar to before (no major memory increase)
```

---

## 🔍 Detailed Validation Queries

### **Check Fact Storage**
```bash
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
    fe.entity_name,
    fe.entity_type,
    fe.category,
    ufr.relationship_type,
    ufr.confidence,
    ufr.mentioned_by_character,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
ORDER BY ufr.updated_at DESC
LIMIT 20;
"
```

### **Check Preference Storage**
```bash
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
    universal_id,
    primary_username,
    preferences,
    last_active
FROM universal_users
WHERE preferences IS NOT NULL
ORDER BY last_active DESC;
"
```

### **Check Entity Relationships (Similarity Graph)**
```bash
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
    e1.entity_name as entity_1,
    e2.entity_name as entity_2,
    er.relationship_type,
    er.similarity_score
FROM entity_relationships er
JOIN fact_entities e1 ON er.entity_id_1 = e1.id
JOIN fact_entities e2 ON er.entity_id_2 = e2.id
ORDER BY er.similarity_score DESC
LIMIT 10;
"
```

---

## 🎯 Success Criteria

### **Phase 2 Working Correctly If:**
- ✅ Facts stored in PostgreSQL (query returns data)
- ✅ Preferences stored in PostgreSQL (query returns data)
- ✅ Logs show "POSTGRES FACTS: Retrieved X facts"
- ✅ Bot mentions your facts in conversation
- ✅ No errors about missing methods or PostgreSQL connection
- ✅ Query timing is fast (<10ms, ideally 2-5ms)

### **Potential Issues to Watch For:**
- ⚠️ If logs show "LEGACY FACTS" instead of "POSTGRES FACTS" → PostgreSQL query failing
- ⚠️ If no facts stored → Check `knowledge_router` initialization
- ⚠️ If bot doesn't mention facts → Check conversation context building
- ⚠️ If errors about missing attributes → Check imports/initialization

---

## 🐛 Debugging Commands

### **Check Knowledge Router Initialization**
```bash
docker logs whisperengine-elena-bot 2>&1 | grep "Knowledge Router"
# Expected: "✅ Semantic Knowledge Router initialized with multi-modal intelligence"
```

### **Check PostgreSQL Connection**
```bash
docker logs whisperengine-elena-bot 2>&1 | grep "PostgreSQL pool"
# Expected: "✅ PostgreSQL pool initialized: postgres:5432/whisperengine"
```

### **Full Message Processing Flow**
```bash
# Watch full processing pipeline
docker logs whisperengine-elena-bot -f | grep -E "POSTGRES|KNOWLEDGE|PREFERENCE|LEGACY"
```

### **Check for Errors**
```bash
docker logs whisperengine-elena-bot 2>&1 | grep -i "error\|failed\|exception"
```

---

## 📝 Test Results Template

After testing, document results:

```markdown
### Test Results - PostgreSQL Fact Retrieval

**Date**: October 5, 2025
**Bots Tested**: Elena, Dotty

#### Test 1: Fact Storage
- [ ] Pizza stored: Yes/No
- [ ] Sushi stored: Yes/No
- [ ] Hiking stored: Yes/No
- [ ] Photography stored: Yes/No
- PostgreSQL Query Results: [paste output]

#### Test 2: Preference Storage
- [ ] Preferred name stored: Yes/No
- PostgreSQL Query Results: [paste output]

#### Test 3: Fact Retrieval
- [ ] PostgreSQL facts retrieved: Yes/No
- [ ] Bot mentioned facts in response: Yes/No
- Logs: [paste "POSTGRES FACTS" log line]

#### Test 4: Performance
- [ ] Query time <10ms: Yes/No
- [ ] No memory increase: Yes/No

#### Issues Found:
[List any issues or unexpected behavior]

#### Overall Assessment:
- [ ] Phase 2 working correctly
- [ ] Ready for Phase 1 migration
```

---

## 🚀 Next Steps After Testing

### **If Tests Pass:**
1. ✅ Phase 2 validated
2. Run migration dry-run: `python scripts/migrate_vector_facts_to_postgres.py --dry-run`
3. Plan Phase 1 execution
4. Consider merging to main

### **If Tests Fail:**
1. Check error logs
2. Validate PostgreSQL connection
3. Check knowledge_router initialization
4. Review code changes
5. Fix issues and retest

---

## 🔗 Related Documentation

- **Implementation Guide**: `docs/architecture/POSTGRES_FACT_STORAGE_CLEANUP_IMPLEMENTATION.md`
- **Architecture Audit**: `docs/architecture/POSTGRES_VECTOR_ARCHITECTURE_AUDIT.md`
- **Session Summary**: `docs/SESSION_SUMMARY_POSTGRES_FACT_CLEANUP.md`

---

**Ready to Test!** 🎯

Send Discord messages to Elena or Dotty and observe the logs for PostgreSQL fact retrieval.
