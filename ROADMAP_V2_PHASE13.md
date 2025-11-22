# Roadmap V2 - Phase 13: Proactive Engagement

This phase transforms the bot from a reactive responder into a proactive companion. It will analyze user activity patterns and initiate conversations at appropriate times.

## Goals
- [ ] **Activity Modeling**: Analyze session history to determine "active hours" for each user.
- [ ] **Proactive Scheduler**: Implement a background task to check for engagement opportunities.
- [ ] **Engagement Triggers**: Define rules for *when* and *why* to message first (e.g., "Haven't spoken in 24h", "User usually active now").
- [ ] **Topic Selection**: Use the Knowledge Graph to pick a relevant topic for the opening message.

## Tasks

### 1. Activity Analysis (`src_v2/intelligence/activity.py`)
- [x] Create `ActivityModeler` class.
- [x] Implement `get_user_activity_heatmap(user_id)`:
    - Queries `v2_conversation_sessions`.
    - Returns a 24x7 grid of activity probabilities.
- [x] Implement `is_good_time_to_message(user_id)`:
    - Checks current time against the heatmap.
    - Returns boolean + confidence score.

### 2. Proactive Scheduler (`src_v2/discord/scheduler.py`)
- [x] Create `ProactiveScheduler` class.
- [x] Implement `start_loop()`:
    - Runs every 15-60 minutes.
    - Iterates through active users.
- [x] Implement `check_user(user_id)`:
    - Checks `last_message_time`.
    - Checks `is_good_time_to_message`.
    - Checks `trust_score` (only message trusted users).

### 3. Message Generation (`src_v2/agents/proactive.py`)
- [x] Create `ProactiveAgent` class.
- [x] Implement `generate_opener(user_id)`:
    - Fetches recent memories and knowledge graph facts.
    - Generates a context-aware opening message (e.g., "How did that meeting go?").

### 4. Integration
- [x] Initialize `ProactiveScheduler` in `WhisperBot.setup_hook`.
- [x] Add configuration to enable/disable proactivity per character.

## Success Criteria
- [x] Bot sends a message to the user after 24h of silence, during their active hours.
- [x] The message references a previous topic or fact ("How is Luna doing?").
- [x] User responds positively (tracked via feedback).
