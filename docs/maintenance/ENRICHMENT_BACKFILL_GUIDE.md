# Enrichment Worker Fact Timestamp Backfill Guide

## Problem Description

**Symptom**: Enrichment worker continuously re-processes old conversations, making hundreds of Qdrant scroll requests every cycle (11 minutes), extracting the same facts repeatedly.

**Root Cause**: Facts created before October 20, 2025 are missing the `latest_message_timestamp` field in their `context_metadata`. The worker falls back to using `fact.created_at` as the "last processed" marker, which is incorrect because fact creation time doesn't indicate "all messages up to this point were processed."

**Impact**:
- Wasteful API calls (hundreds of unnecessary Qdrant scroll requests)
- Worker constantly busy instead of idle when no new messages
- Same facts re-extracted every cycle (ON CONFLICT prevents duplicates, but wastes resources)
- ~90% reduction in efficiency

## Solution: Timestamp Backfill Script

The `scripts/backfill_fact_message_timestamps.py` script fixes this by:

1. Finding all facts missing `latest_message_timestamp`
2. Querying Qdrant to find the **actual** latest message timestamp at the time each fact was created
3. Updating `context_metadata` with the correct timestamp
4. Adding `backfilled_at` metadata to track which facts were backfilled

## Prerequisites

- Python 3.11+ with virtual environment activated
- PostgreSQL database running and accessible
- Qdrant database running and accessible
- Environment variables configured (see `.env` file)

## Usage

### Step 1: Dry-Run (Recommended First)

Test the script to see what would change without making modifications:

```bash
source .venv/bin/activate
python scripts/backfill_fact_message_timestamps.py --dry-run
```

**Expected Output**:
```
=== WhisperEngine Fact Timestamp Backfill ===
Mode: DRY RUN (no changes will be made)

Database: localhost:5433/whisperengine
Qdrant: localhost:6334

🔍 Step 1: Finding facts missing latest_message_timestamp...
Found 1,654 facts missing timestamps across 10 bots

📊 Breakdown by bot:
  elena: 361 facts (14 with no messages found)
  marcus: 58 facts
  jake: 93 facts (2 with no messages found)
  ...

DRY RUN COMPLETE - No changes made
Would update 1,654 facts
Would skip 52 facts (no messages found)
```

### Step 2: Execute Backfill

Once you've reviewed the dry-run output and confirmed it looks correct:

```bash
source .venv/bin/activate
python scripts/backfill_fact_message_timestamps.py
```

**Expected Output**:
```
=== WhisperEngine Fact Timestamp Backfill ===
Mode: LIVE (will update database)

Database: localhost:5433/whisperengine
Qdrant: localhost:6334

🔍 Step 1: Finding facts missing latest_message_timestamp...
Found 1,654 facts missing timestamps across 10 bots

✅ Step 2: Backfilling timestamps...
Processing elena (361 facts)...
  ✓ Updated user_123 facts (latest: 2025-10-18T23:23:30.655569)
  ...

📊 Backfill Summary:
Successfully updated: 1,654 facts
Failed: 0 facts
Skipped (no messages): 52 facts

✅ BACKFILL COMPLETE
```

### Step 3: Restart Enrichment Worker

Restart the enrichment worker to pick up the new timestamps:

```bash
# Docker Compose multi-bot setup
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker

# OR using multi-bot.sh script
./multi-bot.sh restart

# OR direct Docker restart
docker restart enrichment-worker
```

### Step 4: Verify Fix

Monitor enrichment worker logs to confirm it's no longer re-processing old conversations:

```bash
# Check logs for users without new messages
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker

# You should see messages like:
# ✅ No new messages for fact extraction (for users with no activity)
# 🔍 Extracting facts from X new messages (only for users with actual new messages)
```

**Before Fix**:
- Hundreds of scroll requests per cycle
- "Extracting facts from 26 new messages" for users with no recent activity
- Worker constantly busy

**After Fix**:
- Minimal scroll requests (only for active users)
- "No new messages" for inactive users
- Worker mostly idle when no new activity
- ~90% reduction in unnecessary processing

## Script Features

### Safety Features
- **Dry-run mode**: Test before executing
- **Idempotent**: Can be run multiple times safely
- **No fact deletion**: Only adds/updates timestamps, never removes data
- **Rollback safe**: Backfilled facts have `backfilled_at` metadata for tracking
- **Error handling**: Continues processing even if individual facts fail

### Performance
- **Batch processing**: Processes facts in batches per bot
- **Connection pooling**: Reuses database connections
- **Progress reporting**: Real-time progress updates
- **Per-bot breakdown**: Shows exactly which bots/users affected

### Metadata Added
Each backfilled fact gets:
- `latest_message_timestamp`: Correct timestamp from Qdrant
- `backfilled_at`: ISO timestamp of when backfill occurred
- Original `created_at` preserved for audit trail

## Troubleshooting

### "Facts with no messages found"

Some facts may show "no messages found" during backfill. This is **normal** for:
- Test data that was manually inserted
- Facts from deleted/cleaned conversations
- Very old data from before current Qdrant collections

These facts are **skipped** (not updated) and will be handled by the enrichment worker's existing fallback logic.

### Connection Errors

If you see connection errors:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check Qdrant is running
docker ps | grep qdrant

# Verify environment variables
cat .env | grep -E "(POSTGRES_|QDRANT_)"
```

### Script Crashes Mid-Run

The script is **idempotent** - you can safely re-run it. Facts that were already backfilled will be skipped (they now have `latest_message_timestamp` populated).

## When to Run This Script

### Required
- **Upgrading from pre-October 20, 2025 versions**: Run once during upgrade
- **Excessive enrichment worker activity**: If logs show constant re-processing

### NOT Required
- **Fresh installations**: New deployments after October 20, 2025 don't need this
- **Already backfilled**: Running multiple times is safe but unnecessary

## Database Schema Changes

The script **does not modify schema**, only data:
- Updates existing `context_metadata` jsonb field in `user_fact_relationships` table
- No new tables, columns, or constraints
- Backward compatible with all versions

## Production Deployment Checklist

- [ ] Review dry-run output
- [ ] Confirm expected number of facts to update
- [ ] Schedule during low-traffic window (optional - no downtime required)
- [ ] Run backfill script
- [ ] Verify 0 failures in output
- [ ] Restart enrichment worker
- [ ] Monitor logs for 15+ minutes to confirm fix
- [ ] Document backfill completion date

## Support

For issues or questions:
- Check logs: `docker compose logs enrichment-worker`
- Review script source: `scripts/backfill_fact_message_timestamps.py`
- GitHub Issues: https://github.com/whisperengine-ai/whisperengine/issues

## Technical Details

### Why This Problem Occurred

The enrichment worker's incremental processing logic works like this:

1. Load user's existing facts from database
2. Get `latest_message_timestamp` from fact's `context_metadata`
3. Query Qdrant for messages **after** that timestamp
4. Extract facts from new messages only

**Before October 20, 2025**: The worker code correctly **stored** `latest_message_timestamp` when creating new facts, but facts created during initial development/testing didn't have this field.

**The Bug**: When `latest_message_timestamp` is missing, the worker falls back to using `fact.created_at`. But fact creation time doesn't mean "all messages up to this point were processed" - it just means "this fact was first discovered at this time."

**Example**:
- User has 26 messages from Oct 18, 23:20:00 to 23:23:30
- Fact created at 23:23:04 (during message processing)
- Worker queries for messages > 23:23:04
- Finds 11 messages (23:23:05 to 23:23:30)
- Re-extracts same facts every 11 minutes forever

**The Fix**: Backfill queries Qdrant to find the **actual** latest message timestamp that existed when the fact was created, then stores that in `context_metadata`. Now the worker correctly knows "all messages up to this timestamp were already processed."

---

**Last Updated**: October 20, 2025  
**Script Version**: 1.0.0  
**WhisperEngine Version**: Compatible with all versions after enrichment worker implementation
