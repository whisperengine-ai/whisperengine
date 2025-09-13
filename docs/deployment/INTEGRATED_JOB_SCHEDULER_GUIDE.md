# Generic Job Scheduler Integration Guide

## 🎯 **Overview**
The bot now includes a **generic job scheduler** that runs within the main bot process, eliminating the need for a separate Docker container while providing flexible background task capabilities.

## ✅ **Benefits of Integrated Approach**

### **1. Simpler Architecture**
- **No separate containers** - Everything runs in the main bot process
- **Shared database connections** - Uses existing PostgreSQL pool
- **Unified logging** - All logs in one place
- **Single deployment** - One Docker container to manage

### **2. Generic Job System**
Instead of just follow-up messages, the system can handle:
- **Follow-up messages** - Re-engage inactive users
- **Data cleanup** - Remove old conversations, temp files
- **Health checks** - Monitor system components
- **Analytics** - Generate usage reports
- **Backups** - Scheduled data backups
- **Custom jobs** - Easy to add new job types

### **3. Better Resource Sharing**
- **Shared memory manager** - Access to user profiles and conversation history
- **Shared LLM client** - Use same AI service for follow-up generation
- **Shared Discord bot** - Direct access to send messages
- **Shared Redis** - Use existing cache for job queuing (if needed)

## 🚀 **Features**

### **Automatic Follow-up Scheduling**
- **Smart detection** - Automatically schedules follow-ups when users become inactive
- **User preferences** - Respects opt-out settings
- **Natural messages** - AI-generated personalized follow-ups
- **Spam prevention** - Cooldowns and interaction checks

### **Administrative Controls**
```bash
# Schedule manual follow-up
!schedule_followup @username 24

# Check job status
!job_status
!job_status job-id-here

# View/manage follow-up preferences  
!followup_settings status
!followup_settings off
!followup_settings on
```

### **Automatic Background Tasks**
- **Daily cleanup** - Removes old data automatically
- **Health monitoring** - Checks system status
- **Retry logic** - Failed jobs are automatically retried
- **Logging** - Full audit trail of all job executions

## 📊 **Database Schema**

### **Job Tables**
```sql
-- Main job queue
CREATE TABLE scheduled_jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Execution history for analytics
CREATE TABLE job_execution_history (
    execution_id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    execution_time TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER,
    status VARCHAR(50) NOT NULL
);

-- Follow-up tracking
CREATE TABLE follow_up_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message_sent TEXT NOT NULL,
    context_data JSONB,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_received BOOLEAN DEFAULT FALSE
);
```

### **Enhanced User Profiles**
```sql
-- Add follow-up preferences to existing user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN follow_ups_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN last_follow_up_sent TIMESTAMPTZ,
ADD COLUMN follow_up_frequency_hours INTEGER DEFAULT 48;
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Enable/disable job scheduler
JOB_SCHEDULER_ENABLED=true

# Follow-up message settings
FOLLOW_UP_DEFAULT_DELAY_HOURS=48
FOLLOW_UP_MAX_PER_USER_PER_WEEK=2
FOLLOW_UP_ENABLED=true
```

### **Job Types**
- `FOLLOW_UP_MESSAGE` - Send re-engagement messages
- `DATA_CLEANUP` - Clean old conversations, temp files
- `HEALTH_CHECK` - Monitor system health
- `ANALYTICS` - Generate usage statistics
- `BACKUP` - Create data backups
- `CUSTOM` - User-defined job types

## 📈 **Usage Examples**

### **Schedule Follow-up Messages**
```python
# Automatic scheduling when user becomes inactive
await job_scheduler.schedule_follow_up_message(
    user_id="123456789",
    delay_hours=48,
    message_context={"last_topic": "Python programming"}
)

# Manual scheduling via command
!schedule_followup @username 24
```

### **Schedule Cleanup Jobs**
```python
# Daily cleanup
await job_scheduler.schedule_job(
    JobType.DATA_CLEANUP,
    scheduled_time=tomorrow,
    payload={"type": "old_conversations", "days_to_keep": 30}
)
```

### **Custom Job Types**
```python
# Register custom handler
class CustomHandler:
    async def execute(self, payload):
        # Your custom logic here
        pass

job_scheduler.register_handler(JobType.CUSTOM, CustomHandler())
```

## 🛠 **How It Works**

### **1. Job Scheduling**
```python
# Jobs are stored in PostgreSQL
job_id = await job_scheduler.schedule_job(
    job_type=JobType.FOLLOW_UP_MESSAGE,
    scheduled_time=future_time,
    payload={"user_id": "123", "context": {...}}
)
```

### **2. Background Processing**
```python
# Scheduler runs every 30 seconds
async def _scheduler_loop(self):
    while self.running:
        await self._process_due_jobs()
        await asyncio.sleep(30)
```

### **3. Job Execution**
```python
# Each job type has a handler
handler = self.job_handlers[job.job_type]
await handler.execute(job.payload)
```

### **4. Follow-up Logic**
```python
# Smart follow-up decisions
if await self._user_interacted_recently(user_id, hours=48):
    return  # Skip if user was active

if await self._user_opted_out_of_followups(user_id):
    return  # Respect user preferences

# Generate personalized message
message = await self._generate_follow_up_message(user_id, context)
await self._send_follow_up_message(user_id, message)
```

## 🔍 **Monitoring & Analytics**

### **Job Status Monitoring**
```bash
# Overall scheduler status
!job_status

# Specific job status
!job_status abc-123-def
```

### **Performance Metrics**
- Job execution times
- Success/failure rates
- Queue lengths
- User engagement rates from follow-ups

### **Logs**
All job execution is logged with:
- Execution time
- Success/failure status
- Error messages
- Performance metrics

## 🚦 **Comparison: Standalone vs Integrated**

| Feature | Standalone Container | Integrated Approach |
|---------|---------------------|---------------------|
| **Complexity** | Higher - separate container | Lower - single process |
| **Resource Usage** | More - duplicate connections | Less - shared resources |
| **Data Access** | API calls to bot | Direct database access |
| **Deployment** | Multiple containers | Single container |
| **Monitoring** | Separate logs/metrics | Unified monitoring |
| **Flexibility** | Follow-up only | Generic job system |
| **Maintenance** | Multiple codebases | Single codebase |

## ✅ **Why This Approach is Better**

1. **Simpler deployment** - One container instead of two
2. **Better performance** - Direct database access, shared connections
3. **More flexible** - Generic job system for many task types
4. **Easier maintenance** - Single codebase to maintain
5. **Better integration** - Access to all bot components
6. **Resource efficient** - Shared memory, connections, caches
7. **Unified monitoring** - All logs and metrics in one place

The integrated approach provides all the follow-up functionality you wanted while being much more maintainable and flexible for future enhancements!
