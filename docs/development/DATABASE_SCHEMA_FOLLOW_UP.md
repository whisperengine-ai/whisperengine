# Database Schema Requirements for Follow-up Feature

## 📊 **New Tables Required**

### 1. **Job Scheduler Tables** (Auto-created by `JobScheduler.initialize()`)

#### `scheduled_jobs` - Core job scheduling
```sql
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_time_status 
ON scheduled_jobs(scheduled_time, status);

CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_type 
ON scheduled_jobs(job_type);
```

#### `job_execution_history` - Analytics and monitoring
```sql
CREATE TABLE IF NOT EXISTS job_execution_history (
    execution_id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    execution_time TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_history_time 
ON job_execution_history(execution_time);
```

### 2. **Follow-up Tracking Table** (Auto-created by `initialize_follow_up_schema()`)

#### `follow_up_history` - Track sent follow-ups
```sql
CREATE TABLE IF NOT EXISTS follow_up_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message_sent TEXT NOT NULL,
    context_data JSONB,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_received BOOLEAN DEFAULT FALSE,
    response_time TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_follow_up_user_time 
ON follow_up_history(user_id, sent_at);
```

## 🔄 **Table Modifications Required**

### 3. **User Profiles Extensions** (Auto-updated by `initialize_follow_up_schema()`)

#### Add follow-up columns to existing `user_profiles` table:
```sql
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS follow_ups_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS last_follow_up_sent TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS follow_up_frequency_hours INTEGER DEFAULT 48;
```

## 🚀 **Auto-Initialization**

### ✅ **All schemas are automatically created!**

The bot handles all database setup automatically when it starts:

1. **Job Scheduler Tables**: Created when `JobScheduler.initialize()` runs
2. **Follow-up Tables**: Created when `initialize_follow_up_schema()` runs  
3. **User Profile Extensions**: Added via `ALTER TABLE IF NOT EXISTS`

### 📍 **Initialization Flow** (in `main.py`):
```python
# Initialize schema
asyncio.create_task(initialize_follow_up_schema(postgres_pool))
asyncio.create_task(job_scheduler.initialize())
```

## 📋 **Manual Setup (if needed)**

If you want to manually verify or set up the schema, you can run these commands directly in PostgreSQL:

```sql
-- Check if tables exist
\dt scheduled_jobs
\dt job_execution_history  
\dt follow_up_history

-- Check if user_profiles has new columns
\d user_profiles

-- View current schema
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
AND column_name LIKE '%follow%';
```

## 🎯 **Key Features**

### ✅ **Safe Migrations**
- All `CREATE TABLE IF NOT EXISTS` - won't break existing data
- All `ADD COLUMN IF NOT EXISTS` - safe for existing user_profiles
- Proper indexes for performance

### ✅ **Opt-in Default** 
- `follow_ups_enabled BOOLEAN DEFAULT FALSE` - users must opt-in
- No existing users affected - they keep NULL/FALSE (disabled)

### ✅ **Analytics Ready**
- Job execution history for monitoring
- Follow-up tracking for effectiveness analysis
- User interaction patterns

## 🚦 **Status: READY**

✅ **No manual database setup required!**
✅ **All schemas auto-create on bot startup**
✅ **Safe for existing installations**
✅ **Backwards compatible**

The database layer is fully ready for the follow-up feature!
