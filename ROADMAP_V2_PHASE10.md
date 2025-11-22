# Roadmap V2 - Phase 10: Advanced Knowledge Graph Integration

This phase focuses on turning the "Knowledge Graph" from a simple fact store into a dynamic, queryable brain. We want the bot to be able to answer complex questions about the user by querying the graph.

## Goals
- [x] **Smart Extraction**: Improve `FactExtractor` to handle conflicts and updates.
- [x] **Semantic Retrieval**: Instead of just dumping "all facts", retrieve facts relevant to the *current* user message.
- [x] **Graph QA**: Allow the bot to ask the graph questions (e.g., "Does the user have any pets?").
- [ ] **Visualization**: (Optional) Add a way to visualize the user's graph (maybe a command `!graph`).

## Tasks

### 1. Enhanced Extraction (`src_v2/knowledge/extractor.py`)
- [x] Update `FactExtractor` to identify if a fact is an *update* to an existing one (e.g., moved cities).
    - *Implemented `SINGLE_VALUE_PREDICATES` logic in `KnowledgeManager`.*
- [ ] Add `temporal` aspect (when was this fact true?). *Deferred.*

### 2. Smart Retrieval (`src_v2/knowledge/manager.py`)
- [x] Implement `query_graph(user_id, query)`:
    -   Use LLM to generate a Cypher query based on the user's natural language question.
    -   Execute Cypher and return results.
- [x] Update `get_user_knowledge` to use this smart retrieval if a specific question is asked.
    - *Implemented via `LookupFactsTool`.*

### 3. Integration (`src_v2/discord/bot.py`)
- [x] Update `bot.py` to use `query_graph` when the Cognitive Router detects a "Knowledge Query".
    - *Handled via `CognitiveRouter` and `LookupFactsTool`.*
- [ ] Add `!graph` command to generate a link or image of the user's graph (using a library like `pyvis` or just a text representation). *Deferred.*

### 4. Conflict Resolution
- [x] Handle contradictory facts (e.g., "I hate pizza" vs "I like pizza").
    - *Implemented `ANTONYM_PAIRS` logic in `KnowledgeManager`.*
- [x] Store `confidence` and `source_message_id`.
    - *Confidence is stored. Source ID is part of the metadata flow.*

## Database Schema (Neo4j)
- Nodes: `User`, `Entity`
- Relationships: `FACT` (properties: `predicate`, `confidence`, `timestamp`)
