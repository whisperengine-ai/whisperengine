# 🚀 Automatic Fix for Assistant Personality Issue

## Problem
After upgrading from v1.0.6 to v1.0.24, your assistant bot lost its personality and behaves like a generic AI.

## ✨ Automatic Solution (Recommended)

**Good news!** This issue now fixes itself automatically through database migrations. You don't need to manually edit anything in the Web UI.

### Steps:

1. **Pull the latest code:**
   ```bash
   cd /path/to/whisperengine
   git pull origin main
   ```

2. **Rebuild and restart your containers:**
   ```bash
   # If using docker-compose directly:
   docker compose down
   docker compose up -d --build
   
   # OR if using the startup script:
   ./start.sh
   ```

3. **Wait for migrations to complete:**
   - Watch the logs: `docker compose logs -f postgres`
   - Look for: `✅ Alembic migrations completed successfully!`
   - Takes ~10-30 seconds

4. **Verify the fix worked:**
   ```bash
   docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "
   SELECT 
     c.name,
     CASE WHEN cp.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_personality,
     CASE WHEN cv.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_voice,
     CASE WHEN cm.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END as has_mode
   FROM characters c
   LEFT JOIN character_personalities cp ON c.id = cp.character_id
   LEFT JOIN character_voices cv ON c.id = cv.character_id
   LEFT JOIN character_modes cm ON c.id = cm.character_id AND cm.is_default = true
   WHERE c.normalized_name = 'assistant';
   "
   ```
   
   **You should see all "✅ YES"!**

5. **Test your bot:**
   - Send a message to your assistant
   - It should now respond with its proper personality restored

---

## ℹ️ What Happened?

- A new database migration was added: `20251019_2308_c64001afbd46_backfill_assistant_personality_data.py`
- When you restart, Alembic automatically runs this migration
- The migration populates the missing personality/voice/mode data
- Safe to run multiple times (won't duplicate data)

---

## 🛟 Troubleshooting

### "Migrations didn't run"
Check the postgres container logs:
```bash
docker compose logs postgres | grep -i migration
```

### "Still shows ❌ MISSING"
The assistant character might not exist. Run:
```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "SELECT * FROM characters WHERE normalized_name = 'assistant';"
```

If no results, you need to run the seed data first:
```bash
docker exec -i whisperengine-postgres psql -U whisperengine -d whisperengine < sql/01_seed_data.sql
```

### "Manual fix preferred"
If you prefer the Web UI method, see: [RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md](./RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md)

---

## 📝 Technical Details

The migration adds:
- **Personality traits**: Big Five model (openness, conscientiousness, etc.)
- **Voice characteristics**: Tone, pace, formality, vocabulary level
- **Default mode**: `helpful_assistant` operational mode
- **Communication styles**: Informative, empathetic, problem-solving

All using `INSERT...ON CONFLICT` for safety - won't break existing installations.

---

**Need help?** Check the [main upgrade documentation](./README_PERSONALITY_RESTORATION.md) or open a GitHub issue.
