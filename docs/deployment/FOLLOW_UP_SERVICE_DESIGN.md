# Follow-Up Message System - Design Document

## 🎯 System Overview

An integrated background job system that proactively engages users who haven't messaged in a while, running within the main Discord bot process and using the existing PostgreSQL database infrastructure.

## 🏗️ Architecture Design

### Integrated Components

1. **Generic Job Scheduler** (Integrated in Main Bot Process)
   - Handles multiple job types including follow-up messages
   - Uses existing PostgreSQL connection pool
   - Runs background tasks within bot process
   - Supports retry logic and error handling

2. **Follow-Up Job Handler** (Part of Job Scheduler)
   - Monitors user activity from PostgreSQL
   - Generates personalized follow-up messages using existing LLM
   - Integrates with existing emotion/relationship systems
   - Respects user preferences and privacy settings

3. **Message Queue** (Optional Redis - Already Available)
   - Can queue messages if Redis is available
   - Handles rate limiting and cooldowns
   - Falls back to direct PostgreSQL storage

4. **Discord Integration** (Existing Bot)
   - Sends follow-up messages via existing bot instance
   - Maintains conversation continuity
   - Uses existing personality/memory systems
   - Direct access to Discord API without webhooks

## 📊 Database Schema Extensions

### Job Scheduler Tables (Automatically Created)

```sql
-- Generic job scheduling system
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

-- Job execution history for analytics
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
```

### Follow-Up Specific Tables

```sql
-- Follow-up message tracking and history
CREATE TABLE IF NOT EXISTS follow_up_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message_sent TEXT NOT NULL,
    context_data JSONB,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_received BOOLEAN DEFAULT FALSE,
    response_time TIMESTAMPTZ
);

-- Enhanced user profiles with follow-up preferences
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS follow_ups_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS last_follow_up_sent TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS follow_up_frequency_hours INTEGER DEFAULT 48;
```

### Performance Indexes
```sql
-- Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_time_status 
ON scheduled_jobs(scheduled_time, status);

CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_type 
ON scheduled_jobs(job_type);

CREATE INDEX IF NOT EXISTS idx_follow_up_user_time 
ON follow_up_history(user_id, sent_at);

CREATE INDEX IF NOT EXISTS idx_job_history_time 
ON job_execution_history(execution_time);
```

## 🔧 System Implementation

### Integrated Structure
```
src/
├── utils/
│   └── job_scheduler.py       # Generic job scheduling system
├── jobs/
│   ├── follow_up_handler.py   # Follow-up message logic
│   └── cleanup_handler.py     # Data cleanup jobs
└── run.py                     # Bot with integrated scheduler
```

### Key Features

#### 1. **Automatic Integration**
```python
# Job scheduler starts with bot
@bot.event
async def on_ready():
    if job_scheduler:
        await job_scheduler.start()
        
        # Set bot instance for handlers
        for handler in job_scheduler.job_handlers.values():
            if hasattr(handler, 'set_bot'):
                handler.set_bot(bot)
```

#### 2. **Smart Follow-up Scheduling**
```python
# Automatically schedule when users become inactive
async def schedule_follow_up_message(user_id: str, delay_hours: int = 48):
    """Schedule personalized follow-up based on user context"""
    # Uses existing conversation history and emotional context
    # Respects user preferences and cooldown periods
    # Generates natural, personalized messages
```

#### 3. **Intelligent Messaging**
```python
# Generate personalized follow-up messages
async def _generate_follow_up_message(user_id: str, context: Dict) -> str:
    """Uses existing user context for personalization"""
    # Access to:
    # - User's conversation history (PostgreSQL)
    # - Emotional profile and relationship level
    # - Recent topics and interests
    # - Previous interaction patterns
```

## 🔄 Integration Benefits

### Shared Resources
- **Database Connections**: Uses existing PostgreSQL pool
- **Memory Systems**: Direct access to conversation history and user profiles
- **LLM Client**: Uses same AI service for personalized message generation
- **Discord Bot**: Direct API access without webhooks
- **Emotion System**: Leverages existing emotional intelligence
- **Privacy Manager**: Respects existing privacy controls

### Simplified Architecture
```
User Activity → Job Scheduler → Follow-Up Handler → Discord Bot → User
                      ↓
              PostgreSQL Tracking
```

## 🎛️ Configuration

### Environment Variables
```env
# Job scheduler configuration
JOB_SCHEDULER_ENABLED=true

# Follow-up specific settings
FOLLOW_UP_DEFAULT_DELAY_HOURS=48
FOLLOW_UP_MAX_PER_USER_PER_WEEK=2
FOLLOW_UP_ENABLED=true
```

### No Additional Containers
The system runs entirely within the existing bot container:
- **No new Docker services needed**
- **No additional deployment complexity**
- **Shared monitoring and logging**
- **Single point of configuration**

## 🎮 User Commands & Controls

### User Commands
```bash
# Check/modify follow-up preferences
!followup_settings status    # View current settings
!followup_settings on        # Enable follow-ups
!followup_settings off       # Disable follow-ups
```

### Admin Commands
```bash
# Manual follow-up scheduling
!schedule_followup @user 24  # Schedule follow-up in 24 hours

# Monitor job system
!job_status                  # Overall scheduler status
!job_status <job-id>         # Check specific job

# System management
!debug on                    # Enable debug logging
!bot_status                  # Check bot health
```

## 🤖 Message Types & Examples

### 1. **Relationship-Based Follow-ups**

**Acquaintance Level**:
- "Hey [name]! Just wanted to check in and see how things are going. 😊"
- "Hi there! Hope you're having a good week. Anything interesting happening lately?"

**Friend Level**:
- "Hey [name]! I was thinking about our conversation regarding [last_topic]. How did that work out?"
- "Hope you're doing well! I remembered you were dealing with [emotional_context] - feeling any better?"

**Close Friend Level**:
- "Hey [name] ❤️ I miss our chats! How are you holding up with everything?"
- "Thinking of you! I know [time_period] ago you were [emotional_context]. Hope things are looking up!"

### 2. **Emotion-Driven Follow-ups**

**After Stress/Sadness**:
- "Hey [name], I wanted to check in on you. I remember you were going through a tough time. How are you feeling now?"

**After Happiness/Excitement**:
- "Hi [name]! I remember you were excited about [topic]. How did it go?"

### 3. **Interest-Based Follow-ups**

Based on previous conversation topics:
- "Hey [name]! I remember you mentioned [interest/hobby]. Have you been able to work on that lately?"

## 📈 Success Metrics & Analytics

### Built-in Tracking
The job scheduler automatically tracks:
- **Job Execution Times**: Performance monitoring
- **Success/Failure Rates**: System reliability
- **Response Rates**: User engagement effectiveness
- **Retry Patterns**: System optimization insights

### Follow-up Specific Metrics
```sql
-- Response rate tracking
SELECT 
    COUNT(*) as total_sent,
    COUNT(*) FILTER (WHERE response_received = true) as responses,
    (COUNT(*) FILTER (WHERE response_received = true)::float / COUNT(*)) * 100 as response_rate
FROM follow_up_history 
WHERE sent_at >= NOW() - INTERVAL '30 days';

-- Engagement by user
SELECT 
    user_id,
    COUNT(*) as follow_ups_sent,
    COUNT(*) FILTER (WHERE response_received = true) as responses,
    AVG(EXTRACT(EPOCH FROM response_time - sent_at) / 60) as avg_response_minutes
FROM follow_up_history 
GROUP BY user_id;
```

### Optimization Insights
- **Optimal Timing**: When users are most likely to respond
- **Message Effectiveness**: Which personalization works best
- **Frequency Analysis**: Ideal intervals between follow-ups
- **User Patterns**: Individual engagement preferences

## 🔒 Privacy & Safety

### Automatic Privacy Integration
- **Existing Privacy Controls**: Inherits all current privacy protections
- **User Consent**: Opt-in/opt-out via simple commands
- **Data Boundaries**: Uses same privacy manager for context boundaries
- **Audit Trail**: All follow-up activity logged and trackable

### Safety Measures
- **Rate Limiting**: Built into job scheduler (max retries, cooldowns)
- **User Interaction Checks**: Avoids messaging recently active users
- **Respect Preferences**: Honors user's follow-up settings
- **Emotional Sensitivity**: Integrates with existing emotion tracking
- **Admin Override**: Complete administrative control over all jobs

## 🚀 Implementation & Deployment

### Current Status: ✅ **IMPLEMENTED**
The integrated job scheduler system is already implemented and ready to use:

1. **Job Scheduler**: `src/utils/job_scheduler.py` - Generic job system
2. **Follow-up Handler**: `src/jobs/follow_up_handler.py` - Follow-up logic  
3. **Main Integration**: Job scheduler starts with bot in `src/main.py`
4. **Commands**: User and admin commands already available
5. **Database Schema**: Auto-created on first run

### Quick Start
```bash
# Enable job scheduler (if not already enabled)
export JOB_SCHEDULER_ENABLED=true

# Start the bot - job scheduler starts automatically
python main.py

# Test with admin commands
!job_status                    # Check scheduler status
!schedule_followup @user 1     # Test follow-up (1 hour)
!followup_settings status      # Check user preferences
```

### Deployment Benefits vs Original Design

| Feature | Original (Separate Container) | Current (Integrated) |
|---------|------------------------------|---------------------|
| **Deployment** | Multiple containers | Single container ✅ |
| **Database Access** | API/webhook calls | Direct access ✅ |
| **Performance** | Network overhead | In-memory sharing ✅ |
| **Maintenance** | Multiple codebases | Single codebase ✅ |
| **Resource Usage** | Higher (duplicate connections) | Lower (shared resources) ✅ |
| **Flexibility** | Follow-up only | Generic job system ✅ |
| **Monitoring** | Separate logs | Unified logging ✅ |

### Automatic Features
- **Schema Creation**: Database tables created automatically on startup
- **Job Registration**: Follow-up handler registered automatically  
- **Bot Integration**: Discord bot instance passed to handlers automatically
- **Cleanup Scheduling**: Default cleanup jobs scheduled automatically
- **Error Handling**: Built-in retry logic and error reporting

## 📋 Next Steps & Enhancements

### Immediate Use
1. **Enable the system**: Set `JOB_SCHEDULER_ENABLED=true`
2. **Test follow-ups**: Use `!schedule_followup @user 1` for quick testing
3. **Monitor activity**: Check `!job_status` for system health
4. **User education**: Inform users about `!followup_settings` command

### Future Enhancements
1. **Enhanced Personalization**
   - Machine learning for optimal timing
   - Advanced emotion-based message selection
   - User behavior pattern recognition

2. **Additional Job Types**
   - Birthday reminders
   - Goal check-ins  
   - Content recommendations
   - System maintenance tasks

3. **Advanced Analytics**
   - Response prediction models
   - A/B testing framework
   - User satisfaction tracking
   - ROI analysis for engagement

4. **Smart Features**
   - Timezone detection
   - Quiet hours respect
   - Context-aware follow-up delays
   - Multi-language support

The integrated approach provides a solid foundation that can be extended with these advanced features while maintaining the simplicity and efficiency of the current design.
