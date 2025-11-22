# Roadmap V2 - Phase 7: Character Evolution & Feedback Loops

This phase focuses on making the character "alive" by allowing it to learn from interactions, adapt its personality, and build long-term relationships.

## Goals
- [ ] **Feedback Loop**: Use emoji reactions (👍/👎) to tune memory and personality.
- [ ] **Trust System**: Track relationship depth and unlock new behaviors.
- [ ] **Evolution**: Allow characters to change over time (e.g., become friendlier, more sarcastic).
- [ ] **Analytics**: Use InfluxDB data to drive insights.

## Tasks

### 1. Feedback Analysis System (`src_v2/evolution/feedback.py`)
- [x] Create `FeedbackAnalyzer` class.
- [x] Implement `get_feedback_score(message_id)`: Queries InfluxDB for reactions.
- [x] Implement `adjust_memory_score(memory_id, score)`: Updates Qdrant payload `importance` score.
- [x] **Auto-Tuning**:
    - If user consistently reacts 👎 to long messages -> Reduce `verbosity` setting.
    - If user reacts ❤️ to "empathetic" responses -> Increase `empathy` trait.

### 2. Trust & Relationship Manager (`src_v2/evolution/trust.py`)
- [x] Create `v2_user_relationships` table (user_id, bot_name, trust_score, level).
- [x] Implement `TrustManager`:
    - `update_trust(user_id, delta)`: Increases/decreases trust based on interactions.
    - `get_relationship_level(user_id)`: Returns "Stranger", "Acquaintance", "Friend", "Close Friend", "Partner".
- [x] **Milestone System**:
    - Define milestones in `character.yaml` (e.g., `trust_threshold: 50 -> unlock_trait: "vulnerable"`).
    - Trigger "Level Up" events (e.g., Bot sends a special message: "I feel like I can really trust you...").

### 3. Dynamic Personality Injection
- [x] Update `AgentEngine` to fetch `relationship_level` and `active_traits`.
- [x] Inject into System Prompt:
    ```
    [RELATIONSHIP STATUS: Close Friend]
    [ACTIVE TRAITS: Sarcastic, Vulnerable]
    ```
- [x] Verify bot behavior changes based on these injections.

### 4. Long-Term Goal System (`src_v2/evolution/goals.py`)
- [ ] Define `goals` in `character.yaml` (e.g., "Publish Research Paper").
- [ ] Implement `GoalTracker`:
    - Analyze conversation for "Goal Progress" (e.g., User gives advice on research).
    - Update `goal_progress` in DB.
- [ ] **Goal-Driven Proactivity**:
    - If goal progress is high, bot initiates conversation about the goal.

### 5. Analytics Dashboard (Grafana)
- [ ] Create "Character Evolution" dashboard.
- [ ] Visualize:
    - Trust Score over time.
    - Reaction Sentiment (Positive vs Negative).
    - Session Duration trends.

## Testing
- [ ] Unit tests for `FeedbackAnalyzer`.
- [ ] Integration test: React to a message and verify memory score updates.
- [ ] Integration test: Manually set Trust Score and verify prompt injection.
