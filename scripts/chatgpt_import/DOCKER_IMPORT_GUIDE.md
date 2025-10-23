# ChatGPT Memories Import - Docker Commands

Simple Docker commands to import ChatGPT memories without needing Python installed locally.

## Quick Start (3 Steps)

### 1. Prepare Your Memories File

Create a text file `memories.txt` with your ChatGPT memories (one per line):

```
User likes Italian food
User has a cat named Luna
User prefers brief, technical responses
User is a software engineer
User wants to learn machine learning
```

### 2. Copy File Into Container

```bash
# Copy your memories file into the bot container
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    cp memories.txt assistant-bot:/tmp/memories.txt
```

Replace `assistant-bot` with your bot name if using a character bot:
- `elena-bot`, `marcus-bot`, `jake-bot`, `ryan-bot`
- `gabriel-bot`, `sophia-bot`, `dream-bot`, `dotty-bot`
- `aetheris-bot`, `aethys-bot`

### 3. Run Import Script

```bash
# Run the import script inside the container
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id YOUR_DISCORD_USER_ID \
        --bot-name assistant \
        --bot-port 9090 \
        --verbose
```

**Note**: Use port `9090` (internal container port), not `8090` (external port).

**That's it!** The bot will process the memories and extract facts/preferences automatically.

---

## Complete Examples

### Import to Assistant Bot (Port 9090)

```bash
# 1. Copy file
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    cp memories.txt assistant-bot:/tmp/memories.txt

# 2. Import
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id 123456789012345678 \
        --bot-name assistant \
        --bot-port 9090 \
        --verbose
```

### Import to Elena (Port 9091)

```bash
# 1. Copy file
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    cp memories.txt elena-bot:/tmp/memories.txt

# 2. Import
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec elena-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id 123456789012345678 \
        --bot-name elena \
        --bot-port 9091 \
        --verbose
```

### Import to Marcus (Port 9092)

```bash
# 1. Copy file
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    cp memories.txt marcus-bot:/tmp/memories.txt

# 2. Import
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec marcus-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id 123456789012345678 \
        --bot-name marcus \
        --bot-port 9092 \
        --verbose
```

### Dry Run (Preview Without Sending)

```bash
# Copy file
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    cp memories.txt assistant-bot:/tmp/memories.txt

# Dry run with --dry-run flag
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id 123456789012345678 \
        --bot-name assistant \
        --bot-port 9090 \
        --dry-run \
        --verbose
```

---

## Bot Names and Ports Reference

**Use internal container ports (not external mapped ports)**

| Bot Name  | Container Name | Internal Port |
|-----------|----------------|---------------|
| assistant | assistant-bot  | 9090          |
| elena     | elena-bot      | 9091          |
| marcus    | marcus-bot     | 9092          |
| jake      | jake-bot       | 9097          |
| ryan      | ryan-bot       | 9093          |
| gabriel   | gabriel-bot    | 9095          |
| sophia    | sophia-bot     | 9096          |
| dream     | dream-bot      | 9094          |
| dotty     | dotty-bot      | 9098          |
| aetheris  | aetheris-bot   | 9099          |
| aethys    | aethys-bot     | 3007          |

---

## Finding Your Discord User ID

1. Enable Developer Mode in Discord:
   - Settings → Advanced → Developer Mode (toggle ON)

2. Get Your User ID:
   - Right-click your username anywhere
   - Select "Copy User ID"
   - You'll get a number like: `123456789012345678`

---

## How It Works

1. **Conversion**: Memories are converted from ChatGPT format to natural statements
   - "User likes pizza" → "I like pizza"
   - "User has a cat" → "I have a cat"

2. **Processing**: Sent through bot's HTTP chat API (as if you typed it)

3. **Extraction**: Enrichment worker extracts facts and preferences in background
   - Facts → `user_fact_relationships` table
   - Preferences → `universal_users.preferences` JSONB

4. **No restart needed**: Changes take effect immediately!

---

## Verifying Import

### Check that memories were sent:
```bash
# View bot logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    logs assistant-bot | tail -50
```

### Monitor enrichment worker processing:
```bash
# Watch enrichment worker (this processes the memories)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    logs -f enrichment-worker
```

Wait a few minutes for background processing. You should see:
```
✅ Stored X facts for user 123456789...
```

### Test with your bot:
Send a message: **"What do you know about me?"**

The bot should recall facts/preferences you imported!

---

## Troubleshooting

### Container not found

**Error**: `Error: No such service: assistant-bot`

**Solution**: Check your bot is running:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps
```

Start the bot:
```bash
./multi-bot.sh bot assistant
```

### Permission denied

**Error**: `permission denied while trying to connect`

**Solution**: Run Docker commands with appropriate permissions (may need `sudo` on Linux).

### Import succeeds but bot doesn't remember

**Cause**: Enrichment worker hasn't processed yet (runs every few minutes)

**Solution**: Wait 2-5 minutes and check enrichment worker logs:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    logs enrichment-worker | grep "Stored.*facts"
```

### Memory format issues

**Problem**: Some memories not converting properly

**Solution**: Format memories clearly:
- ✅ Good: `User likes Italian food`
- ✅ Good: `User has a cat named Luna`
- ✅ Good: `User prefers brief responses`
- ❌ Bad: `likes food` (missing subject)
- ❌ Bad: Too complex paragraphs (split into separate lines)

---

## Advanced Options

### Custom delay between messages

Default is 2 seconds. To change:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py \
        --file /tmp/memories.txt \
        --user-id 123456789012345678 \
        --bot-name assistant \
        --bot-port 9090 \
        --delay 1.0
```

### Clean up temp file after import

```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec assistant-bot rm /tmp/memories.txt
```

---

## Windows-Specific Notes

### PowerShell

Use backticks for line continuation:
```powershell
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml `
    cp memories.txt assistant-bot:/tmp/memories.txt

docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml `
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py `
        --file /tmp/memories.txt `
        --user-id 123456789012345678 `
        --bot-name assistant `
        --bot-port 9090 `
        --verbose
```

### Command Prompt

Use caret (^) for line continuation:
```cmd
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ^
    cp memories.txt assistant-bot:/tmp/memories.txt

docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ^
    exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py ^
        --file /tmp/memories.txt ^
        --user-id 123456789012345678 ^
        --bot-name assistant ^
        --bot-port 9090 ^
        --verbose
```

Or use single line (remove backslashes):
```cmd
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec assistant-bot python scripts/chatgpt_import/import_via_bot_api.py --file /tmp/memories.txt --user-id 123456789012345678 --bot-name assistant --bot-port 9090 --verbose
```

---

## Privacy & Data

- ✅ **Local processing**: Everything runs in your local Docker containers
- ✅ **Your data**: Memories stored in your local PostgreSQL database
- ✅ **No external calls**: Import doesn't send data anywhere
- ✅ **Full control**: Delete imported data anytime

To remove imported data:
```bash
# Connect to database
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
    exec postgres psql -U whisperengine

# Remove facts for specific user
DELETE FROM user_fact_relationships WHERE user_id = 'YOUR_USER_ID';

# Remove preferences for specific user
UPDATE universal_users SET preferences = '{}' WHERE universal_id = 'YOUR_USER_ID';
```
