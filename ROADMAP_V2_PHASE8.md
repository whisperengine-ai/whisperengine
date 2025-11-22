# Roadmap V2 - Phase 8: Goal-Driven Behavior

This phase introduces a "Goal System" that gives characters long-term objectives. Instead of just reacting to the user, the character will proactively steer conversations towards specific outcomes (e.g., "Learn about the user's hobbies", "Teach a specific concept", "Solve a mystery together").

## Goals
- [x] **Goal Definition**: Define structured goals for characters.
- [x] **Progress Tracking**: Track completion status of goals per user.
- [x] **Proactivity**: Inject goal-oriented instructions into the prompt.
- [x] **Goal Completion**: Trigger events when goals are achieved.

## Tasks

### 1. Database Schema (`alembic/versions/`)
- [x] Create `v2_goals` table (id, character_name, description, success_criteria, priority).
- [x] Create `v2_user_goal_progress` table (user_id, goal_id, status, progress_score, last_updated).

### 2. Goal Manager (`src_v2/evolution/goals.py`)
- [x] Implement `GoalManager` class.
- [x] `load_goals(character_name)`: Load goals from character definition.
- [x] `get_active_goals(user_id, character_name)`: Get incomplete, high-priority goals.
- [x] `update_progress(user_id, goal_id, progress)`: Update DB.

### 3. Goal Analysis (LLM)
- [x] Create `GoalAnalyzer` (or add to `CognitiveRouter`).
- [x] Analyze user messages to see if they contribute to a goal.
- [x] Analyze bot responses to see if they advanced a goal.

### 4. Engine Integration (`src_v2/agents/engine.py`)
- [x] Inject **Current Goals** into System Prompt.
    ```
    [CURRENT GOAL: Learn User's Name]
    (Try to naturally ask for the user's name in this conversation.)
    ```
- [x] **Goal Completion Check**: After response, check if goal was met.

### 5. Testing
- [x] Unit Test: Goal loading and progress tracking.
- [x] Integration Test: Verify bot asks relevant questions to advance goal.
