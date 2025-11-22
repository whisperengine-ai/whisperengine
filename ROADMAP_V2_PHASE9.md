# Roadmap V2 - Phase 9: Dynamic Memory Consolidation & Reflection

This phase focuses on "Memory Consolidation" - the process of turning raw conversation logs into high-level summaries and insights. This allows the bot to remember "what we talked about" over long periods without needing to retrieve every single message.

## Goals
- [ ] **Session Management**: Logic to detect when a conversation starts and ends.
- [ ] **Auto-Summarization**: Generate summaries of completed sessions.
- [ ] **Reflection**: Extract high-level insights (e.g., "User seems stressed about work") from sessions.
- [ ] **Consolidation**: Store summaries in Qdrant for semantic retrieval.

## Tasks

### 1. Session Logic (`src_v2/memory/session.py`)
- [x] Implement `SessionManager`.
- [x] `get_active_session(user_id)`: Find open session or create new one.
- [x] `close_session(session_id)`: Mark session as inactive (e.g., after 30m timeout).
- [x] **Middleware**: Update `bot.py` to track session IDs for every message.

### 2. Summarization Engine (`src_v2/memory/summarizer.py`)
- [x] Implement `SummaryManager`.
- [x] `summarize_session(session_id)`:
    - Fetch all messages for the session.
    - Use LLM to generate a concise summary.
    - Extract "Key Takeaways" and "Mood".
- [x] **Trigger**: Run summarization when a session closes (background task).

### 3. Reflection & Insight (`src_v2/intelligence/reflection.py`)
- [x] Create `ReflectionEngine`.
- [x] Analyze summaries to find patterns over time.
- [x] Update `v2_user_relationships` with new insights.

### 4. Storage & Retrieval
- [x] Store summaries in `v2_summaries` (PostgreSQL).
- [x] Embed summaries and store in Qdrant (Collection: `whisperengine_summaries`).
- [x] Update `MemoryManager` to retrieve **Summaries** alongside **Raw Messages**.

### 5. Integration
- [x] Inject **Relevant Past Summaries** into the system prompt.
    ```
    [PAST CONVERSATIONS]
    - Last week, you discussed the user's project deadline.
    - You previously talked about ocean conservation.
    ```

## Database Schema (Already Created in Phase 8 Fix)
- `v2_conversation_sessions` (id, user_id, start_time, end_time, is_active)
- `v2_summaries` (id, session_id, content, embedding_id)
