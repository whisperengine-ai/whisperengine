# WhisperEngine Ban System Usage Guide

## Overview

WhisperEngine includes a ban system to protect AI roleplay characters from abusive users. The ban system prevents specific Discord users from interacting with any WhisperEngine bots across all servers.

## Ban System Components

### 1. Database Table: `banned_users`

The ban system uses a PostgreSQL table with the following structure:
- `discord_user_id` - The Discord user ID to ban (string)
- `banned_by` - Admin/moderator who issued the ban
- `ban_reason` - Reason for the ban
- `banned_at` - Timestamp when ban was issued
- `is_active` - Whether the ban is currently active (TRUE/FALSE)
- `notes` - Additional notes about the ban

### 2. Discord Commands (In-Bot)

When a bot is running, administrators can use Discord commands:

```
!ban <user_id> <reason>       # Ban a user
!unban <user_id> <reason>     # Unban a user
!banlist [limit]              # List banned users (default: 10)
!bancheck <user_id>           # Check if a user is banned
```

**Requirements**: These commands require admin permissions as configured in the bot.

### 3. Manual Ban Script: `add_ban.py`

For direct database access without running a bot, use the `add_ban.py` script.

## Using `add_ban.py`

### Prerequisites

1. **PostgreSQL must be running**:
   ```bash
   docker ps --filter "name=postgres"
   ```
   You should see `whisperengine-multi-postgres` container running.

2. **Python virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Environment variables** (loaded from `.env`):
   - `POSTGRES_DB` (default: whisperengine)
   - `POSTGRES_USER` (default: whisperengine)
   - `POSTGRES_PASSWORD` (default: whisperengine_password)

### Quick Usage

The script is pre-configured with the Discord ID to ban. Simply edit the values in the script and run:

```bash
source .venv/bin/activate
python add_ban.py
```

### Customizing the Ban

Edit these variables in `add_ban.py`:

```python
# Discord ID to ban
discord_id = "141345023796"  # Change this to target user ID
banned_by = "admin_manual"           # Your admin identifier
reason = "Manual ban via script"     # Reason for the ban
```

### Example Output

**Successful ban**:
```
✅ Connected to PostgreSQL database at localhost:5433
✅ Successfully banned Discord user: 141345023796
   Banned by: admin_manual
   Reason: Manual ban via script

✅ Verification: Ban record created successfully
   Active: True
   Banned at: 2025-10-09 06:33:44.819939

✅ Database connection closed
```

**Already banned**:
```
✅ Connected to PostgreSQL database at localhost:5433
⚠️  User 14134502379634 is already banned!
   Reason: Harassment and abusive behavior
```

### How to Find a Discord User ID

1. **Enable Developer Mode** in Discord:
   - User Settings → Advanced → Developer Mode (toggle on)

2. **Right-click the user** in Discord and select "Copy User ID"

3. **Paste the ID** into the `discord_id` variable in `add_ban.py`

## Verifying Bans

### Check if a user is banned (SQL query):

```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c \
  "SELECT discord_user_id, banned_by, ban_reason, banned_at, is_active 
   FROM banned_users 
   WHERE discord_user_id = '141345023796340';"
```

### List all active bans:

```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c \
  "SELECT discord_user_id, banned_by, ban_reason, banned_at 
   FROM banned_users 
   WHERE is_active = TRUE 
   ORDER BY banned_at DESC;"
```

### Count total bans:

```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c \
  "SELECT COUNT(*) as total_active_bans 
   FROM banned_users 
   WHERE is_active = TRUE;"
```

## Unbanning Users

### Method 1: Via Discord Command (when bot is running)

```
!unban <user_id> <reason>
```

Example:
```
!unban 14134502379634 Ban appeal approved
```

### Method 2: Direct SQL Update

```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c \
  "UPDATE banned_users 
   SET is_active = FALSE, 
       unbanned_at = CURRENT_TIMESTAMP, 
       unbanned_by = 'admin_manual', 
       unban_reason = 'Ban appeal approved' 
   WHERE discord_user_id = '141345023796340';"
```

### Method 3: Create `remove_ban.py` script

You can create a companion script for unbanning:

```python
#!/usr/bin/env python3
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def remove_ban():
    discord_id = "141345023796340"  # User to unban
    unbanned_by = "admin_manual"
    reason = "Ban appeal approved"
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        database=os.getenv('POSTGRES_DB', 'whisperengine'),
        user=os.getenv('POSTGRES_USER', 'whisperengine'),
        password=os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    )
    
    await conn.execute(
        """
        UPDATE banned_users 
        SET is_active = FALSE, 
            unbanned_at = CURRENT_TIMESTAMP,
            unbanned_by = $1,
            unban_reason = $2
        WHERE discord_user_id = $3
        """,
        unbanned_by, reason, discord_id
    )
    
    print(f"✅ Unbanned user: {discord_id}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(remove_ban())
```

## How the Ban System Works

1. **Message Processing**: When a user sends a message to any WhisperEngine bot, the system checks their Discord ID against the `banned_users` table.

2. **Ban Check**: The `BanCommandHandlers` class in `src/handlers/ban_commands.py` performs the check:
   - Query: `SELECT * FROM banned_users WHERE discord_user_id = ? AND is_active = TRUE`
   - Uses caching (5-minute TTL) for performance

3. **Message Blocking**: If user is banned:
   - Message is silently dropped (no response sent)
   - Logged for monitoring: `"Blocked message from banned user {user_id}"`

4. **Multi-Bot Protection**: Bans are system-wide:
   - Elena, Marcus, Jake, Ryan, Gabriel, Sophia, Aethys, Aetheris, Dream, Dotty
   - All bots share the same `banned_users` table
   - One ban blocks interaction with ALL characters

## Troubleshooting

### Error: "table banned_users does not exist"

The database table needs to be created. Run database migrations:

```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c \
  "CREATE TABLE IF NOT EXISTS banned_users (
    id SERIAL PRIMARY KEY,
    discord_user_id VARCHAR(255) NOT NULL,
    banned_by VARCHAR(255) NOT NULL,
    ban_reason TEXT,
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    unbanned_at TIMESTAMP,
    unbanned_by VARCHAR(255),
    unban_reason TEXT,
    UNIQUE(discord_user_id)
  );"
```

### Error: "nodename nor servname provided"

The script can't connect to PostgreSQL. Check:

1. **PostgreSQL is running**:
   ```bash
   docker ps --filter "name=postgres"
   ```

2. **Correct port mapping** (should be `5433->5432`):
   ```bash
   docker port whisperengine-multi-postgres
   ```

3. **Connection settings in script** (should be `localhost:5433` for local execution)

### Error: "password authentication failed"

Check your `.env` file credentials match the database:

```bash
grep POSTGRES .env
```

## Best Practices

1. **Document ban reasons clearly** - Include specific behavior that led to the ban
2. **Use meaningful `banned_by` identifiers** - Track who issued the ban
3. **Review bans periodically** - Some situations may improve over time
4. **Keep ban list reasonable** - Don't ban for minor infractions
5. **Test ban enforcement** - Verify banned users actually can't interact
6. **Backup ban database** - Include `banned_users` table in database backups

## Security Considerations

- **Admin permissions**: Only trusted administrators should have ban/unban access
- **Audit trail**: All bans/unbans are logged in the database with timestamps
- **Privacy**: Discord user IDs are the only user information stored
- **No IP bans**: System only bans Discord accounts, not IP addresses
- **Reversible**: All bans can be undone if needed

## Integration with Bot Systems

The ban system is automatically integrated into all WhisperEngine bots:

- **Location**: `src/handlers/ban_commands.py`
- **Initialization**: In `src/main.py` → `ModularBotManager`
- **Message filtering**: In `src/handlers/events.py` → `on_message` handler
- **Caching**: 5-minute cache TTL for performance
- **Multi-bot shared state**: All bots query the same `banned_users` table

## Related Files

- `src/handlers/ban_commands.py` - Main ban system implementation
- `add_ban.py` - Manual ban script (this guide)
- `test_ban_system.py` - Ban system test suite
- `.github/copilot-instructions.md` - Development guidelines for ban system

## Support

For issues with the ban system:

1. Check logs: `docker logs whisperengine-<bot>-bot | grep -i ban`
2. Verify database connectivity: `docker exec -it whisperengine-multi-postgres psql -U whisperengine`
3. Test with `test_ban_system.py`: `python test_ban_system.py`
4. Review Discord command permissions in bot configuration

---

**Last Updated**: October 8, 2025  
**WhisperEngine Version**: Multi-Bot Architecture  
**Database**: PostgreSQL 16.4
