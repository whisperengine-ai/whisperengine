# WhisperEngine Bot Name Migration Guide

This guide explains the migration from bot_name filtering to pure collection-based isolation in WhisperEngine.

## Background

Previously, WhisperEngine used a bot_name field in each memory vector payload to isolate memories between bots, even when they were stored in the same collection. This approach has been deprecated in favor of complete collection isolation, where each bot has its own dedicated Qdrant collection.

## Migration Process

The migration script `scripts/migrate_vector_storage_remove_bot_name.py` performs the following:

1. Identifies active collections from `.env.*` files
2. Removes the bot_name field from each record in active collections
3. Optionally identifies and deletes obsolete collections
4. Generates a comprehensive migration report

## Running the Migration

### Step 1: Review Active Collections

First, run the script to see which collections are active:

```bash
source .venv/bin/activate
python scripts/migrate_vector_storage_remove_bot_name.py
```

This will show you all the collections that would be migrated based on your `.env.*` files.

### Step 2: Run the Migration

To run the migration with auto-confirmation:

```bash
source .venv/bin/activate
AUTO_CONFIRM_MIGRATION=true python scripts/migrate_vector_storage_remove_bot_name.py
```

### Step 3: Clean Up Obsolete Collections

To identify and optionally delete obsolete collections:

```bash
source .venv/bin/activate
CLEANUP_OBSOLETE_COLLECTIONS=true AUTO_CONFIRM_MIGRATION=true python scripts/migrate_vector_storage_remove_bot_name.py
```

### Step 4: Validate Migration

After migration, validate that bot_name fields were successfully removed:

```bash
source .venv/bin/activate
python scripts/validate_bot_name_removal.py
```

## Environment Variables

The script supports the following environment variables:

- `AUTO_CONFIRM_MIGRATION=true`: Skip confirmation prompts
- `CLEANUP_OBSOLETE_COLLECTIONS=true`: Identify and optionally delete obsolete collections

## Migration Report

The script generates a comprehensive migration report showing:
- Collections migrated
- Total points processed and updated
- Bot names removed
- Success rate
- Detailed breakdown by collection

## Rollback

If needed, you can restore from a Qdrant snapshot. However, this migration is non-destructive and only removes a redundant field, so rollback should not be necessary.