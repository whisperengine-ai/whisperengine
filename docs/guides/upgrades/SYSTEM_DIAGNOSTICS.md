# 🔍 System Verification & Diagnostics

**Quick commands to verify your WhisperEngine installation is correct**

---

## 📋 Quick Health Check

Run these commands to verify everything is set up correctly:

### 1️⃣ Check Database Tables Exist

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
  'characters' as table_name,
  COUNT(*) as row_count
FROM characters
UNION ALL
SELECT 'character_personalities', COUNT(*) FROM character_personalities
UNION ALL
SELECT 'character_voices', COUNT(*) FROM character_voices
UNION ALL
SELECT 'character_modes', COUNT(*) FROM character_modes
UNION ALL
SELECT 'communication_styles', COUNT(*) FROM communication_styles
UNION ALL
SELECT 'user_facts', COUNT(*) FROM user_facts
ORDER BY table_name;
"
```

**Expected output:**
```
      table_name        | row_count 
------------------------+-----------
 characters             |         1
 character_modes        |         1   ← Should have 1+ rows
 character_personalities|         1   ← Should have 1+ rows
 character_voices       |         1   ← Should have 1+ rows
 communication_styles   |         1   ← Should have 1+ rows
 user_facts             |     0+    ← May be 0 for new installs
```

❌ **If character_personalities/voices/modes show 0:** You have the personality loss issue - follow restoration guide

---

### 2️⃣ Check Assistant Character Status

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
  c.name,
  c.normalized_name,
  c.occupation,
  CASE WHEN cp.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_personality,
  CASE WHEN cv.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_voice,
  CASE WHEN cm.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_mode,
  CASE WHEN cs.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_communication
FROM characters c
LEFT JOIN character_personalities cp ON c.id = cp.character_id
LEFT JOIN character_voices cv ON c.id = cv.character_id
LEFT JOIN character_modes cm ON c.id = cm.character_id AND cm.is_default = true
LEFT JOIN communication_styles cs ON c.id = cs.character_id
WHERE c.normalized_name = 'assistant';
"
```

**Expected output (HEALTHY):**
```
    name      | normalized_name | occupation   | has_personality | has_voice | has_mode | has_communication
--------------+-----------------+--------------+-----------------+-----------+----------+-------------------
 AI Assistant | assistant       | AI Assistant | ✅ YES          | ✅ YES    | ✅ YES   | ✅ YES
```

**If you see ❌ MISSING:** You need to restore personality data (use Web UI guide or SQL script)

---

### 3️⃣ Check Qdrant Collections

```bash
docker exec whisperengine-assistant curl -s http://qdrant:6333/collections | python3 -m json.tool
```

**Expected output:**
```json
{
  "result": {
    "collections": [
      {
        "name": "whisperengine_memory_assistant"
      }
    ]
  }
}
```

**Should see:** `whisperengine_memory_assistant` collection exists

---

### 4️⃣ Check Qdrant Collection Schema

```bash
docker exec whisperengine-assistant curl -s http://qdrant:6333/collections/whisperengine_memory_assistant | python3 -m json.tool | grep -A 20 "vectors"
```

**Expected output:**
```json
"vectors": {
  "content": {
    "size": 384,
    "distance": "Cosine"
  },
  "emotion": {
    "size": 384,
    "distance": "Cosine"
  },
  "semantic": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

**Should see:** All 3 vectors (content, emotion, semantic) with size 384

---

### 5️⃣ Check Alembic Migration Status

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT version_num, applied 
FROM alembic_version 
ORDER BY version_num DESC 
LIMIT 5;
"
```

**Expected output:**
```
           version_num            |   applied
----------------------------------+---------------------
 27e207ded5a0                     | 2025-10-19 23:11:30
 (shows most recent migration)
```

**Should see:** Recent timestamp showing migrations have run

---

### 6️⃣ List All Database Tables

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "\dt" | grep character
```

**Expected output (should include these):**
```
 character_attributes
 character_background_stories
 character_communication_patterns
 character_interests
 character_modes                    ← NEW in v1.0.7+
 character_personalities            ← NEW in v1.0.7+
 character_response_style_items
 character_speech_patterns
 character_voices                   ← NEW in v1.0.7+
 characters
 communication_styles
```

**If missing** `character_personalities`, `character_voices`, or `character_modes`: Migrations didn't run correctly

---

## 🔬 Deep Diagnostics

### Check Personality Data Details

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
  c.name,
  cp.openness,
  cp.conscientiousness,
  cp.extraversion,
  cp.agreeableness,
  cp.neuroticism
FROM characters c
LEFT JOIN character_personalities cp ON c.id = cp.character_id
WHERE c.normalized_name = 'assistant';
"
```

**Expected output (HEALTHY):**
```
    name      | openness | conscientiousness | extraversion | agreeableness | neuroticism
--------------+----------+-------------------+--------------+---------------+-------------
 AI Assistant |     0.80 |              0.90 |         0.70 |          0.90 |        0.20
```

**If all values are NULL:** Personality data missing - needs restoration

---

### Check User Facts Table

```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT COUNT(*) as total_facts, 
       COUNT(DISTINCT user_id) as unique_users 
FROM user_facts;
"
```

**Shows:** How many user facts are stored (can be 0 for new installs)

---

### Check Qdrant Memory Count

```bash
docker exec whisperengine-assistant curl -s http://qdrant:6333/collections/whisperengine_memory_assistant | python3 -m json.tool | grep "points_count"
```

**Shows:** Total memory points stored in Qdrant (can be 0 for new users)

---

## 📊 Understanding Your Logs

### ✅ What the Logs Show is WORKING:

From your provided logs, these are **correct and healthy**:

1. **Migrations Ran Successfully:**
   ```
   db-migrate | ✅ Alembic migrations completed successfully!
   db-migrate | 🎉 All migrations complete!
   ```
   ✅ Database schema is up-to-date

2. **Qdrant Collection Exists:**
   ```
   qdrant | Loading collection: whisperengine_memory_assistant
   qdrant | Recovered collection whisperengine_memory_assistant: 1/1 (100%)
   ```
   ✅ Qdrant memory system working

3. **Correct Vector Schema:**
   ```
   whisperengine-assistant | ✅ Collection has correct 3-vector schema: {'semantic', 'emotion', 'content'}
   ```
   ✅ Multi-vector memory system configured correctly

4. **PostgreSQL Connection:**
   ```
   whisperengine-assistant | ✅ PostgreSQL is ready
   ```
   ✅ Database connection working

5. **Character System Loaded:**
   ```
   whisperengine-assistant | ✅ Character system initialized with database-only CDL for bot: assistant
   ```
   ✅ CDL system operational

### ⚠️ What the Logs Show is MISSING:

**The warnings indicate missing CHARACTER DATA (not missing tables):**

```
whisperengine-assistant | ⚠️ STRUCTURED CONTEXT: No character mode found for assistant
whisperengine-assistant | ⚠️ STRUCTURED CONTEXT: No character personality found for assistant
whisperengine-assistant | ⚠️ STRUCTURED CONTEXT: No character voice found for assistant
```

❌ **Problem:** Tables exist but are EMPTY for the assistant character

**What this means:**
- ✅ Database migrations ran correctly
- ✅ All tables were created
- ❌ Seed data didn't populate personality/voice/mode data
- ❌ User upgraded from v1.0.6 which had incomplete seed data

---

## 🎯 Quick Diagnosis Summary

### If you see these in check #2:

| Output | Diagnosis | Solution |
|--------|-----------|----------|
| All ✅ YES | Everything is working! | No action needed |
| Some ❌ MISSING | Personality data missing | Follow Web UI or SQL restoration guide |
| Table doesn't exist error | Migrations didn't run | Run migrations: `docker restart whisperengine-db-migrate` |

---

## 🔧 Common Issues

### Issue: "Table doesn't exist" errors

**Means:** Migrations haven't run

**Fix:**
```bash
# Restart migration container
docker restart whisperengine-db-migrate

# Wait 30 seconds, then check logs
docker logs whisperengine-db-migrate --tail 50
```

**Should see:** `✅ Alembic migrations completed successfully!`

---

### Issue: All checks pass but bot still generic

**Means:** Bot hasn't reloaded new data

**Fix:**
```bash
# Restart the bot
docker restart whisperengine-assistant

# Wait 60 seconds for full reload
sleep 60

# Test again
```

---

### Issue: Qdrant collection doesn't exist

**Means:** Bot hasn't created collection yet

**Fix:** Bot creates collection on first run. Just send it a message.

---

## 📝 Save Your Diagnostics

**Create a diagnostic report:**

```bash
echo "=== WhisperEngine Health Check ===" > health_check.txt
echo "" >> health_check.txt

echo "1. Database Tables:" >> health_check.txt
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "\dt" | grep character >> health_check.txt
echo "" >> health_check.txt

echo "2. Assistant Character Status:" >> health_check.txt
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
SELECT c.name, 
       CASE WHEN cp.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_personality,
       CASE WHEN cv.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_voice
FROM characters c
LEFT JOIN character_personalities cp ON c.id = cp.character_id
LEFT JOIN character_voices cv ON c.id = cv.character_id
WHERE c.normalized_name = 'assistant';
" >> health_check.txt
echo "" >> health_check.txt

echo "3. Qdrant Collections:" >> health_check.txt
docker exec whisperengine-assistant curl -s http://qdrant:6333/collections >> health_check.txt
echo "" >> health_check.txt

echo "=== Report Complete ===" >> health_check.txt
cat health_check.txt
```

**Share `health_check.txt` with support if you need help**

---

## 🆘 When to Use Each Guide

| Your Situation | Use This Guide |
|----------------|----------------|
| Check #2 shows ❌ MISSING | [Web UI Restoration Guide](./RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md) OR [SQL Script](../../sql/migrations/fix_assistant_personality_v106_to_v124.sql) |
| All checks pass but bot generic | Restart bot and wait 60 seconds |
| "Table doesn't exist" errors | Restart migrations, then check again |
| Qdrant issues | Check Qdrant logs: `docker logs qdrant --tail 100` |

---

**Run check #2 first - it tells you exactly what's wrong in 5 seconds!** ⚡
