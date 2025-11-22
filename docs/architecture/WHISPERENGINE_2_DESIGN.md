# WhisperEngine 2.0: "Back to Basics" Design Document

## 1. Vision & Philosophy
**"Complexity is the enemy of execution."**

WhisperEngine 1.0 proved that high-fidelity, memory-persistent AI roleplay is possible. However, it grew into a massive "Platform" with 50+ database tables, 12+ concurrent Docker containers, and a distributed service mesh (Postgres, Qdrant, InfluxDB).

**WhisperEngine 2.0** aims to deliver the same high-quality user experience (rich personality, long-term memory) with **simplified code logic** while leveraging **robust, specialized infrastructure**.

### Core Mission: Uncompromised Authenticity
The primary goal remains unchanged: **create AI characters that feel alive**.
*   **Personality First**: WE2 must support deep personality persistence where characters maintain their unique voice, quirks, and history.
*   **Continuous Learning**: The system must allow characters to learn about the user (preferences, facts) and themselves (evolving lore, relationships) over time, just as in WE1.
*   **Seamless Persistence**: Every interaction contributes to the character's long-term memory store (Vector + Graph + SQL), ensuring a continuous, evolving experience.

## 2. Core Architectural Simplifications

### A. Retain Container Isolation (Simplified Internals)
*   **Decision**: Keep the **One Container Per Character** model.
    *   *Reasoning*: Provides perfect process isolation, independent scaling, and crash resilience (if one bot crashes, others stay up).
    *   *Simplification*: While we keep the containers, we simplify the *internals* of each container by removing complex custom memory pipelines in favor of standard libraries (LangChain/LlamaIndex).

### B. Best-in-Class Infrastructure (Right Tool for the Job)
*   **Philosophy**: Use specialized tools where they excel, rather than forcing everything into Postgres.
*   **Vector Store**: **Qdrant** (Retained).
    *   *Reason*: Superior performance, filtering, and management compared to raw `pgvector`.
*   **Metrics**: **InfluxDB** (Retained).
    *   *Reason*: Purpose-built for high-volume time-series data (analytics, health checks).
*   **Caching**: **Redis** (Retained).
    *   *Reason*: Low-latency state management and pub/sub for multi-bot coordination.
*   **Knowledge Graph**: **Neo4j** (New).
    *   *Reason*: Model complex character relationships, lore connections, and "knowledge" as a graph, enabling multi-hop reasoning that vector search misses.

### C. Text-Based Character Definition (CDL as Code)
*   **Current (WE1)**: CDL (Character Definition Language) stored in 50+ normalized database tables.
*   **New (WE2)**: **Pure Text Files**.
    *   *Solution*: The "Database" for character personality is now just a folder of text files.
    *   *Format*: Use Markdown (`.md`) for system prompts and character definitions.
    *   *Templating*: **LangChain Dynamic Variables**.
        *   *Mechanism*: Files can contain placeholders like `{user_name}`, `{time_of_day}`, `{recent_memories}` which are injected at runtime via LangChain's `PromptTemplate`.
    *   *Benefit*: Zero database management for character traits. Users edit a file, restart the bot (or hot-reload), and the personality changes.
    *   *Structure*: `characters/{name}/character.md` (The core CDL), `characters/{name}/knowledge/`.

## 3. Codebase Refactoring

### A. Pipeline Simplification
Remove the complex "Protocol/Factory" patterns unless strictly necessary.
*   **Old Flow**: `MessageProcessor` -> `MemoryFactory` -> `VectorMemoryAdapter` -> `QdrantClient`.
*   **New Flow**: `Engine` -> `Agent` -> `MemoryStore` (Direct Postgres Calls).

### B. LangChain & LlamaIndex Integration
*   **LangChain**: Use for **Dynamic Prompt Management**.
    *   Replace custom Jinja2/String formatting with LangChain's `PromptTemplate`.
    *   Standardize chat history management.
*   **LlamaIndex**: Use for **RAG (Retrieval-Augmented Generation)**.
    *   *New Feature*: Support **File Uploads**. Users can upload PDFs/Docs, and LlamaIndex will ingest them into the character's knowledge base.
    *   Replace custom Qdrant adapter with LlamaIndex's `VectorStoreIndex` (backed by Postgres/pgvector).

### C. LLM-Native Intelligence (No More spaCy)
*   **Current (WE1)**: Heavy NLP pipeline using `spaCy`, `RoBERTa` models, and custom regex for intent detection and entity extraction.
*   **New (WE2)**: **LLM Tool Use / Function Calling**.
    *   *Solution*: Use the LLM (via LangChain Tools) to decide what to do.
    *   *Mechanism*: Define tools like `update_user_preference`, `search_memory`, `get_current_time`, `save_fact`.
    *   *Benefit*: Removes heavy ML dependencies, improves accuracy on complex queries, and allows natural handling of edge cases.
    *   *Flow*: User Message -> LLM -> [Decides to Call Tool] -> Tool Execution -> LLM Final Response.

### D. LLM-Based Sentiment & Emotion Analysis
*   **Current (WE1)**: Dedicated `RoBERTa` model running locally to score emotion/sentiment.
*   **New (WE2)**: **Prompt Engineering**.
    *   *Solution*: Ask the LLM to output its internal emotional state or sentiment as part of the structured response or chain-of-thought.
    *   *Benefit*: No extra model inference cost/latency, better alignment with the generated text (the LLM knows why it's angry better than an external classifier).

### E. Discord Capabilities
*   **Voice Chat (Retained)**:
    *   **Decision**: Keep the existing voice architecture (Discord voice client + STT/TTS pipelines).
    *   *Integration*: Ensure the voice input is transcribed and fed into the standard LangChain agent loop, and the text response is sent to TTS.
*   **Channel Context (New)**:
    *   *Current (WE1)*: Bots mostly responded to direct mentions or DMs, often ignoring surrounding context or other users' messages.
    *   *New (WE2)*: **Full Channel Awareness**.
    *   *Mechanism*: When triggered (or passively listening), the bot fetches the last $N$ messages from the channel history to construct the prompt context.
    *   *Benefit*: Enables natural multi-user roleplay, understanding of group dynamics, and "lurking" behavior (bot chiming in when relevant without being pinged).

### F. Continuous Learning & Evolution
*   **Goal**: Replicate and improve WE1's ability to learn about the user and itself.
*   **Mechanism**:
    *   **User Learning**: Extract facts/preferences from conversation and store in **Neo4j** (Graph) and **Postgres** (Structured).
    *   **Self-Evolution**: Allow the character to reflect on conversations and update its own "Self-Knowledge" nodes in the graph.
    *   **Implementation**: A background "Reflector" agent (or post-interaction step) that analyzes chat logs to update the Knowledge Graph and Vector Store without blocking the real-time response.

### G. Multimodal Capabilities
*   **Image Input (Vision)**:
    *   **Goal**: Allow characters to "see" images shared by users (retained from WE1).
    *   **Mechanism**: Pass Discord image attachments directly to multimodal LLMs (GPT-4o, Claude 3.5 Sonnet) via LangChain's multimodal message types.
    *   **Benefit**: Characters can react to memes, analyze photos, and understand visual context.
*   **Image Generation (Art)**:
    *   **Goal**: Allow characters to "draw" or share visual imagination.
    *   **Mechanism**:
        *   **Tool**: Expose a `generate_image` tool to the LLM.
        *   **Backend**: Connect to DALL-E 3, Midjourney (via proxy), or local Stable Diffusion.
    *   **Trigger**: The bot decides when to generate art based on the conversation (e.g., "Here's a sketch of what I mean...") or upon user request.
*   **Audio Input (Voice Messages)**:
    *   **Goal**: Process Discord voice messages and uploaded audio files.
    *   **Mechanism**: Transcribe audio attachments using the STT pipeline (Whisper) and process as text.
    *   **Benefit**: Seamless interaction for users who prefer voice notes over typing or live calls.
*   **Video Input (Clips)**:
    *   **Goal**: Understand context from shared video clips or GIFs.
    *   **Mechanism**: Extract keyframes from video attachments and pass to the multimodal LLM.
    *   **Benefit**: Characters can react to shared content (memes, gameplay clips) with visual understanding.

### H. Dual Interface (Discord + HTTP API)
*   **Primary**: **Discord Bot**.
    *   The core experience is designed for Discord (Events, Voice, Reactions, Threads).
*   **Secondary**: **HTTP Chat API** (Retained).
    *   *Goal*: Allow external integrations (Web UI, testing scripts, other platforms) to chat with the characters.
    *   *Mechanism*: Expose a FastAPI endpoint (e.g., `POST /chat`) that reuses the same `Agent` logic as the Discord bot.
    *   *Benefit*: Enables automated testing and future expansion to other platforms without rewriting the core logic.

## 4. Migration Strategy
1.  **Export**: Create a script to dump the current complex CDL tables into human-readable Markdown/Text files per character.
2.  **Vectors**: Migrate Qdrant vectors to `pgvector` (optional, or just start fresh with better embedding models).
3.  **Code**: Start a fresh `src_v2/` directory to avoid entanglement with legacy code during the transition.

## 5. Proposed Stack
*   **Language**: Python 3.13
*   **Frameworks**: **LangChain** (Orchestration), **LlamaIndex** (Data/RAG), **FastAPI** (HTTP API).
*   **Databases**:
    *   **PostgreSQL**: Relational data (Users, Chat Logs).
    *   **Qdrant**: Vector Memory.
    *   **Neo4j**: Knowledge Graph.
    *   **InfluxDB**: Metrics.
    *   **Redis**: Caching/PubSub.
*   **Discord Lib**: `discord.py`.
*   **Key Libraries**:
    *   **Configuration**: `pydantic-settings` (Type-safe config management).
    *   **Background Tasks**: `arq` (Async Redis Queue for the "Reflector" agent).
    *   **Migrations**: `alembic` (Database schema management).
    *   **Logging**: `loguru` (Structured, simplified logging).
    *   **HTTP Client**: `httpx` (Modern async HTTP client).
*   **Removed**: `spaCy`, `RoBERTa`, custom NLP pipelines (replaced by LLM Tool Calling & Prompt Engineering).
*   **Deployment**: `docker-compose.yml` with individual services per bot and shared infrastructure containers.
