# Assistant Personality Restoration Guide

## Problem
After upgrading from **WhisperEngine v1.0.6 to v1.0.24**, your assistant character lost its personality and is responding like a generic AI assistant instead of maintaining character consistency.

## Root Cause
Between v1.0.6 and v1.0.24, new database tables were added for character personalities, voices, and conversation modes. The seed data wasn't updated, leaving existing "assistant" characters with basic info but no personality traits.

## Solution
Run the personality restoration SQL script to populate the missing data.

---

## Quick Fix (Choose One Method)

### Method 1: Direct psql (if you have psql installed)
```bash
cd /path/to/whisperengine
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/migrations/fix_assistant_personality_v106_to_v124.sql
```

### Method 2: Via Docker (if running containerized)
```bash
cd /path/to/whisperengine
docker exec -i whisperengine-postgres psql -U whisperengine -d whisperengine \
     < sql/migrations/fix_assistant_personality_v106_to_v124.sql
```

### Method 3: Copy/Paste SQL (via database client)
1. Open your database client (pgAdmin, DBeaver, etc.)
2. Connect to your WhisperEngine database
3. Open and run the file: `sql/migrations/fix_assistant_personality_v106_to_v124.sql`

---

## After Running the Script

### 1. Verify Success
The script will output a verification table showing:
```
Character Name | Has Personality | Has Voice | Has Mode | Has Communication Style
AI Assistant   | ✅ YES         | ✅ YES    | ✅ YES   | ✅ YES
```

All should show "✅ YES". If any show "❌ MISSING", the script encountered an error.

### 2. Restart Your Bot
```bash
# If using Docker
docker restart whisperengine-assistant

# Or if using systemd
sudo systemctl restart whisperengine
```

### 3. Test Conversation
Send a message to your bot. It should now respond with its personality restored, not as a generic AI assistant.

### 4. Check Logs (Optional)
Look for these confirmations in startup logs:
```
✅ Character system initialized with database-only CDL for bot: assistant
✅ Structured Context: Added CDL character identity for assistant
```

Should **NOT** see warnings like:
```
⚠️ No character personality found for assistant
⚠️ No character voice found for assistant
⚠️ No character mode found for assistant
```

---

## Troubleshooting

### Still seeing personality issues?

**Check environment variable:**
```bash
echo $DISCORD_BOT_NAME
# Should output: assistant
```

If empty or different, set it:
```bash
export DISCORD_BOT_NAME=assistant
# Then restart bot
```

**Verify database connection:**
```bash
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "\dt"
# Should show list of tables including character_personalities, character_voices, etc.
```

**Check for migration errors:**
Look at bot startup logs for database connection errors or CDL loading failures.

---

## What This Script Does

Populates four critical CDL tables for the assistant character:

1. **character_personalities** - Big Five personality traits
   - Openness: 0.80 (curious, open to ideas)
   - Conscientiousness: 0.90 (organized, reliable)
   - Extraversion: 0.70 (balanced social engagement)
   - Agreeableness: 0.90 (cooperative, helpful)
   - Neuroticism: 0.20 (emotionally stable)

2. **character_voices** - Speaking style
   - Tone: Warm and professional
   - Pace: Moderate
   - Vocabulary: Accessible
   - Formality: Professional

3. **character_modes** - Conversation style
   - Mode: Helpful assistant
   - Description: Balanced, supportive assistance

4. **communication_styles** - Response preferences
   - Length: Medium
   - Emoji usage: Moderate
   - Style: Structured

---

## Need Help?

- **GitHub Issues**: https://github.com/whisperengine-ai/whisperengine/issues
- **Discord Community**: [Your Discord invite]
- **Documentation**: Check `docs/` directory for more guides

---

## For Future Installations

This issue is now fixed in the seed data (`sql/01_seed_data.sql`). Fresh installations of v1.0.24+ will have complete personality data from the start.
