# Migration Guide: Enrichment Worker Timestamp Fix

## Overview

**Issue**: Enrichment worker continuously re-processes old conversations  
**Affected Versions**: All deployments before October 20, 2025  
**Fix Version**: October 20, 2025+  
**Migration Required**: One-time database backfill

## Quick Migration (5 minutes)

```bash
# 1. Test the backfill (see what would change)
source .venv/bin/activate
python scripts/backfill_fact_message_timestamps.py --dry-run

# 2. Execute the backfill
python scripts/backfill_fact_message_timestamps.py

# 3. Restart enrichment worker
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker

# 4. Verify fix (watch logs for 15+ minutes)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker
```

## Should I Run This Migration?

### ✅ **YES - Run the migration if:**
- Your enrichment worker logs show hundreds of Qdrant scroll requests every ~11 minutes
- You see "Extracting facts from X new messages" for users with no recent activity
- Worker is constantly busy even when there's no new user activity
- You have facts created before October 20, 2025

### ❌ **NO - Skip the migration if:**
- Fresh installation (deployed after October 20, 2025)
- No enrichment worker deployed
- Already ran this migration successfully

## What This Migration Does

### Problem
Old facts are missing the `latest_message_timestamp` field, causing the enrichment worker to:
1. Fall back to using `created_at` as the "last processed" marker
2. Query for messages after `created_at` (incorrect - fact creation ≠ messages processed)
3. Re-process the same conversations every cycle
4. Waste ~90% of processing on already-extracted facts

### Solution
The backfill script:
1. Finds all facts missing `latest_message_timestamp` (typically 1,000-2,000 facts)
2. Queries Qdrant to find the **actual** latest message at time of fact creation
3. Updates `context_metadata` with correct timestamp
4. Adds `backfilled_at` metadata for audit trail

### Result
- ~90% reduction in unnecessary processing
- Worker correctly skips already-processed conversations
- Only processes truly new messages
- Dramatic reduction in Qdrant API calls

## Expected Results

### Before Migration
```
# Enrichment worker logs (every 11 minutes)
🔍 Extracting facts from 26 new messages (user test_user_phase3)
🔍 Extracting facts from 31 new messages (user another_old_user)
... (hundreds of scroll requests)
```

### After Migration
```
# Enrichment worker logs (every 11 minutes)
✅ No new messages for fact extraction (user test_user_phase3)
✅ No new messages for fact extraction (user another_old_user)
🔍 Extracting facts from 213 new messages (user active_user_123)  # Only actual new activity
```

## Rollback (if needed)

The migration is **safe and reversible**:

```sql
-- To remove backfilled timestamps (restore to pre-migration state)
UPDATE user_fact_relationships
SET context_metadata = context_metadata - 'latest_message_timestamp' - 'backfilled_at'
WHERE context_metadata->>'backfilled_at' IS NOT NULL;
```

However, rolling back is **not recommended** as it will restore the inefficient behavior.

## Zero Downtime

This migration requires **no downtime**:
- Enrichment worker can continue running during backfill
- Bots/Discord services unaffected
- Database updates are atomic and non-blocking
- Only restart required is enrichment worker (takes <1 second)

## Monitoring After Migration

Check enrichment worker health after migration:

```bash
# Monitor for one full cycle (11 minutes)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker | grep -E "(Extracting facts|No new messages)"

# Count scroll requests (should be dramatically lower)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep "scroll" | wc -l
```

**Success indicators**:
- Majority of users show "No new messages" (if they have no recent activity)
- Only users with actual new messages show "Extracting facts from X new messages"
- Scroll request count reduced by ~90%
- Worker mostly idle between active user processing

## Troubleshooting

### "Facts with no messages found"
**Status**: Normal, expected for test data or old cleaned conversations  
**Action**: None required - these facts are safely skipped

### "Failed to store relationship" errors in worker logs
**Status**: Pre-existing database constraint issue (unrelated to migration)  
**Action**: Safe to ignore - ON CONFLICT prevents duplicates

### Migration script crashes
**Status**: Script is idempotent - safe to re-run  
**Action**: Re-run the script, already-processed facts will be skipped

### Still seeing re-processing after migration
**Action**:
1. Verify backfill completed successfully (check script output for "✅ BACKFILL COMPLETE")
2. Confirm enrichment worker was restarted after backfill
3. Check database: `SELECT COUNT(*) FROM user_fact_relationships WHERE context_metadata->>'backfilled_at' IS NOT NULL;`

## Full Documentation

See [ENRICHMENT_BACKFILL_GUIDE.md](./ENRICHMENT_BACKFILL_GUIDE.md) for:
- Detailed problem explanation
- Technical implementation details
- Advanced troubleshooting
- Database schema information

## Support

Questions or issues?
- Check enrichment worker logs
- Review backfill script output
- GitHub Issues: https://github.com/whisperengine-ai/whisperengine/issues

---

**Migration Status**: Required for pre-Oct 20, 2025 deployments  
**Estimated Time**: 5 minutes  
**Downtime Required**: None (only enrichment worker restart)  
**Risk Level**: Low (idempotent, no data deletion, easily reversible)
