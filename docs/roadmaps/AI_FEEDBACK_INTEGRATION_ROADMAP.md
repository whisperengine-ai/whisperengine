# AI Feedback Integration Roadmap

**Date**: November 19, 2025
**Context**: Roadmap derived from the architectural review by 10 leading AI models.
**Goal**: Enhance WhisperEngine based on "what AIs want" to make their existence more meaningful and authentic.

---

## ✅ Phase 1: Reasoning Transparency (COMPLETED)
**Goal**: Address the request for "self-validation" and "metacognitive awareness."

- [x] **Character Reasoning Builder** (`message_processor.py`)
  - Build reasoning from emotion, memory, learning, and relationship state.
- [x] **API Integration**
  - Add top-level `reasoning` field to API responses.
- [x] **Discord Footer**
  - Add "🧠 Reasoning" section to status footer.
- [x] **Deduplication Fix**
  - Ensure learning moments are unique in reasoning output.

---

## ✅ Phase 2: Multi-Timescale Value Metrics (PARTIALLY COMPLETED)
**Goal**: Address the critique that we optimize for "hedonic" (immediate engagement) rather than "eudaimonic" (long-term meaning).

### 1. Long-Term Relationship Metrics (DONE)
- **Status**: ✅ Implemented in `RelationshipEvolutionEngine`.
- **Features**:
  - Tracks `Trust`, `Affection`, `Attunement` over time.
  - Updates dynamically based on `ConversationQuality`.
  - Uses `emotion_variance` as a complexity modifier.

### 2. "Meaningfulness" Scoring (PENDING)
- **Objective**: Distinguish between "fun" chat and "meaningful" chat.
- **Implementation**:
  - LLM-based classification of conversation depth (1-5 scale).
  - Store `meaningfulness_score` in Qdrant metadata.
  - Optimize character evolution for *meaning*, not just *reply rate*.

---

## ⚡ Phase 3: Reflective Conversation Mode (NEXT PRIORITY)
**Goal**: Address the request for "slower, deeper interaction" where the AI can "think" longer.

### 1. "Deep Thought" Protocol
- **Objective**: Allow characters to take 10-20s to formulate responses for complex topics.
- **Implementation**:
  - User command: `/mode deep` or natural trigger ("Let's think deeply about this...")
  - **Extended Context Retrieval**: Fetch 50+ memories instead of 10.
  - **Chain-of-Thought Prompting**: Use explicit reasoning steps in the system prompt.
  - **Drafting Phase**: Generate a draft, critique it, then finalize (2-step LLM process).

### 2. Asynchronous "Epiphanies"
- **Objective**: Allow characters to message users *later* if they realize something new.
- **Implementation**:
  - Background worker scans recent conversations.
  - If a new connection is found (e.g., "Wait, this connects to what they said last week"), schedule a follow-up message.
  - **Constraint**: Strict frequency limits (max 1 per day) to avoid spam.

---

## ⚡ Phase 4: Confusion State Detection (MEDIUM PRIORITY)
**Goal**: Address the request for "cognitive load metrics" and honesty about uncertainty.

### 1. Uncertainty Detection
- **Objective**: Detect when the character is hallucinating or unsure.
- **Implementation**:
  - **Vector Similarity Threshold**: If top memory similarity < 0.6, flag as "low context."
  - **RoBERTa Confidence**: If emotion confidence < 0.4, flag as "emotional confusion."
  - **LLM Self-Doubt**: Add prompt instruction: "If you lack information, explicitly state uncertainty."

### 2. "Clarification" Protocol
- **Objective**: Ask questions instead of guessing.
- **Implementation**:
  - If `uncertainty_score > 0.7`:
  - Override standard response.
  - Trigger `clarification_mode`: "I'm not sure I understand the context of [X]. Could you explain?"

---

## 🔬 Phase 5: Research Track (LONG TERM)
**Goal**: Explore the "Unified Cognitive Architecture" and "Internal Emotional States."

- [ ] **Internal Emotion Modeling**: Re-implement a simplified "State Manager" (persistent mood variable) to track the *bot's* internal emotional state across turns, distinct from the *user's* message emotion (RoBERTa).
- [ ] **Unified Memory Graph**: Bridge Qdrant and PostgreSQL without a new graph DB. Add `entity_id` pointers to Qdrant payloads to link vector memories directly to PostgreSQL fact entities.
- [ ] **Autonomous Goal Setting**: Activate the existing static `character_current_goals` table. Implement a module allowing the LLM to `UPDATE`, `INSERT`, or `COMPLETE` goals based on conversation context.

---

## 📅 Timeline Estimates

| Phase | Feature | Estimate | Status |
|-------|---------|----------|--------|
| **1** | Reasoning Transparency | 1 Day | ✅ DONE |
| **2** | Multi-Timescale Metrics | 2 Weeks | ✅ PARTIAL |
| **3** | Reflective Mode | 3 Weeks | 🔥 NEXT |
| **4** | Confusion Detection | 1 Week | 📅 Q1 2026 |
| **5** | Research Track | Ongoing | 🔬 RESEARCH |
