# WhisperEngine 2.0 - Back to Basics

This is a simplified, robust implementation of WhisperEngine, focusing on code clarity and stability.

## Architecture

- **Language**: Python 3.13
- **Framework**: Discord.py + LangChain
- **Database**: PostgreSQL (Chat History), Qdrant (Semantic Memory - Coming Soon)
- **Configuration**: `.env` file (Pydantic Settings)

## Setup

1.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in the details.
    ```bash
    cp .env.example .env
    ```
    Ensure you set `DISCORD_TOKEN` and your LLM provider details.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements-v2.txt
    ```

3.  **Run Infrastructure**:
    ```bash
    docker compose -f docker-compose.v2.yml up -d
    ```

4.  **Run the Bot**:
    You must specify which character to run using `DISCORD_BOT_NAME`.
    ```bash
    export DISCORD_BOT_NAME=elena
    python -m src_v2.main
    ```

## Features

- **Text-Based Character Definitions**: Characters are defined in `characters/{name}/character.md`.
- **Multi-Character Support**: Run specific characters by setting `DISCORD_BOT_NAME`.
    - Example: `export DISCORD_BOT_NAME=elena` will load `.env.elena` and the character `elena`.
    - **Note**: `DISCORD_BOT_NAME` is required.
- **Local LLM Support**: Easily switch between OpenAI, OpenRouter, Ollama, and LM Studio via `.env`.
- **Persistent Memory**: Chat history is stored in PostgreSQL.

## Directory Structure

- `src_v2/`
    - `agents/`: LLM and Agent logic.
    - `config/`: Configuration settings.
    - `core/`: Core utilities (Database, Character loading).
    - `discord/`: Discord bot implementation.
    - `memory/`: Memory management.
    - `main.py`: Entry point.
