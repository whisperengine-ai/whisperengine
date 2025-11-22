# WhisperEngine 2.0 Source Code

This directory contains the source code for WhisperEngine 2.0, a simplified and robust version of the WhisperEngine platform.

## Structure

*   **`agents/`**: LangChain agents and logic for character behavior.
*   **`api/`**: FastAPI endpoints for the HTTP interface.
*   **`config/`**: Configuration management using `pydantic-settings`.
*   **`core/`**: Core application logic, logging, and database connections.
*   **`discord/`**: Discord bot implementation using `discord.py`.
*   **`memory/`**: Interfaces for Postgres, Qdrant, Neo4j, and Redis.
*   **`tools/`**: LLM tools for function calling (e.g., `save_memory`, `generate_image`).
*   **`utils/`**: Helper functions and utilities.

## Getting Started

Refer to the main `README.md` or `docs/architecture/WHISPERENGINE_2_DESIGN.md` for architectural details.
