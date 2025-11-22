# Roadmap V2 - Phase 6: Agentic Memory Architecture

This phase focuses on implementing an "Agentic" memory system where the bot actively decides which memory tools to use based on user intent.

## Goals
- [ ] **Tool Infrastructure**: Create LangChain tools for searching Summaries, Episodes, and Facts.
- [ ] **Cognitive Router**: Implement a "Thought" step to select tools before generating a response.
- [ ] **Background Summarization**: Maintain a compressed history of "Mid-Term" memory.

## Tasks

### 1. Database Schema Updates
- [x] Create `v2_conversation_sessions` table (start_time, end_time, summary_id).
- [x] Create `v2_summaries` table (content, embedding_id, time_range).
- [x] **Create V2 Baseline Migration** (Clean slate for V2 tables).

### 2. Background Summarization (`src_v2/memory/summarizer.py`)
- [x] Implement `SummaryManager` class.
- [x] Create LLM prompt for summarizing conversation chunks.
- [x] **Implement Meaningfulness Scoring** (LLM rates depth 1-5).
- [x] Implement trigger logic (Hook added to `bot.py`, logic pending).

### 3. Memory Tools (`src_v2/tools/memory_tools.py`)
- [x] `SearchSummariesTool`: Wraps Qdrant search on `summaries` collection.
- [x] `SearchEpisodesTool`: Wraps Qdrant search on `episodes` collection (Hybrid Search).
- [x] `LookupFactsTool`: Wraps Neo4j Cypher queries.
- [x] `CharacterEvolutionTool`: Retrieves relationship metrics, learned traits, and **Current Goals**.

### 4. Cognitive Router (`src_v2/engine/router.py`)
- [x] Create a lightweight LLM chain that takes `user_input` and outputs a list of tools to call.
- [x] Implement **Reasoning Transparency** (log the "Thought Trace").
- [x] Implement **Confusion Detection** (handle low-confidence tool results).
- [x] Example Output: `{"tool": "search_summaries", "query": "marine biology discussion", "reasoning": "User is asking about past topic"}`.

### 5. Engine Integration (`src_v2/agents/engine.py`)
- [x] Update `generate_response` to:
    1.  [x] Run `CognitiveRouter`.
    2.  [x] **Check Mode**: Fast vs. Reflective.
    3.  [x] Execute selected tools.
    4.  [x] Inject tool outputs into `context_variables`.
    5.  [x] **Inject Dynamic Persona** (Evolution State) into System Prompt.
    6.  [x] Generate final response.

### 6. Social Features (Added)
- [x] **Group Chat Support**: Added `channel_id` to memory.
- [x] **Reply Handling**: Injected reply context.
- [x] **Thread Support**: Injected thread location context.
- [x] **Reaction Logging**: Logged emoji feedback to InfluxDB.
- [x] **File Uploads**: Integrated LlamaIndex for document reading.

### 7. Testing
- [ ] Unit tests for `SummaryManager`.
- [ ] Unit tests for `CognitiveRouter` (mocking LLM).
- [ ] Integration test: Verify bot can "remember" something by calling a tool.
- [ ] Integration test: Verify character tone changes based on "Trust" score.
- [ ] Integration test: Verify "Reflective Mode" triggers for complex queries.
