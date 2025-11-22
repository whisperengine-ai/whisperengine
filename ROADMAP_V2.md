# WhisperEngine 2.0 Implementation Roadmap

This document tracks the progress of the "Back to Basics" rewrite.

## ✅ Phase 1: Core Foundation (Completed)
- [x] **Project Scaffolding**: Directory structure, `pyproject.toml`, `requirements-v2.txt`.
- [x] **Infrastructure**: Docker Compose with Postgres, Qdrant, Neo4j, Redis (pinned versions).
- [x] **Configuration**: Pydantic settings with `.env` support and character-specific config (`.env.elena`).
- [x] **Database Management**: Async connection pooling and Alembic migrations (`migrations_v2`).
- [x] **Discord Bot**: Basic event loop, message handling, and character loading.
- [x] **LLM Integration**: LangChain factory supporting OpenAI, OpenRouter, Ollama.
- [x] **Short-Term Memory**: Chat history persistence in PostgreSQL (`v2_chat_history`).

---

## ✅ Phase 2: Long-Term Memory (Vector RAG) (Completed)
**Goal**: Give the bot "episodic memory" so it remembers details from past conversations.

- [x] **Embedding Service**: 
    - Implement `src_v2/memory/embeddings.py`.
    - Use `fastembed` to generate 384-dimension vectors locally (matching WE1).
    - **Async Support**: Implemented `embed_query_async` for non-blocking generation.
- [x] **Vector Storage**: 
    - Update `MemoryManager.add_message` to upsert vectors into Qdrant.
    - Store metadata: `user_id`, `role`, `content`, `timestamp`.
    - **Named Vectors**: Implemented `content`, `emotion`, `semantic` vectors.
- [x] **Semantic Retrieval**: 
    - Implement `MemoryManager.search_memories(query, user_id)`.
    - Filter by `user_id` to ensure privacy.
- [x] **Context Injection**: 
    - Update `src_v2/discord/bot.py` to fetch relevant memories.
    - Inject them into the `{recent_memories}` placeholder in the character prompt.

---

## ✅ Phase 3: Knowledge & Reasoning (Neo4j) (Completed)
**Goal**: Allow the bot to remember structured facts (e.g., "User owns a cat named Luna").

- [x] **Graph Connection**: Verified `AsyncGraphDatabase` driver usage.
- [x] **Fact Extraction**: 
    - Created `src_v2/knowledge/extractor.py` with `FactExtractor` chain.
    - Extracts entities: `(User)-[PREDICATE]->(Object)`.
- [x] **Graph Storage**: 
    - Created `src_v2/knowledge/manager.py`.
    - Implemented Cypher queries to merge nodes/relationships.
- [x] **Context Injection**: 
    - Updated `src_v2/discord/bot.py` to inject facts into `{knowledge_context}`.

---

## 🗣️ Phase 4: Multimodal Capabilities
**Goal**: Voice interaction and image understanding.

- [ ] **Voice Support**: 
    - Integrate ElevenLabs API (using keys from `.env`).
    - Implement Discord Voice Client to join channels and speak.
- [ ] **Vision Support**: 
    - Detect image attachments in Discord messages.
    - Pass image URLs to multimodal LLMs (GPT-4o/Vision).

---

## 🗣️ Phase 4: Multimodal Capabilities (Completed)
**Goal**: Voice interaction and image understanding.

- [x] **Voice Support**: 
    - Integrate ElevenLabs API (using keys from `.env`).
    - Implement Discord Voice Client to join channels and speak.
- [x] **Vision Support**: 
    - Detect image attachments in Discord messages.
    - Pass image URLs to multimodal LLMs (GPT-4o/Vision).

---

## 🛠️ Phase 5: Polish & Production
- [x] **Tooling**: Add "slash commands" for debugging (e.g., `/memory wipe`, `/debug`).
- [x] **Error Handling**: Graceful fallbacks if LLM or DB is unreachable.
- [x] **Testing**: Add unit tests for `MemoryManager` and `AgentEngine`.
