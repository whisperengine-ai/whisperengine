# Discord Bot - Universal Dockerfile
FROM python:3.13-slim

# Image metadata labels
LABEL org.opencontainers.image.title="WhisperEngine Discord Bot" \
      org.opencontainers.image.description="Privacy-first Discord bot with AI memory and emotional intelligence" \
      org.opencontainers.image.vendor="WhisperEngine AI" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.source="https://github.com/whisperengine-ai/whisperengine" \
      org.opencontainers.image.documentation="https://github.com/whisperengine-ai/whisperengine/wiki"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    gcc g++ git curl ffmpeg wget netcat-traditional procps \
    libopus-dev libffi-dev libnacl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies using new multi-tier structure
COPY requirements-core.txt requirements-platform.txt requirements-discord.txt requirements-vector-memory.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements-core.txt && \
    pip install --no-cache-dir -r requirements-platform.txt && \
    pip install --no-cache-dir -r requirements-discord.txt && \
    pip install --no-cache-dir -r requirements-vector-memory.txt

# Copy application code (will be overridden by volume mounts in development)
COPY src/ ./src/
COPY pyproject.toml validate_config.py env_manager.py run.py ./
COPY characters/ ./characters/
COPY config/ ./config/

# No .env files copied - configuration injected at runtime via Docker Compose

# Create directories and non-root user in one layer
RUN mkdir -p backups privacy_data temp_images logs data \
    && mkdir -p logs/elena logs/marcus logs/gabriel logs/dream logs/marcus-chen \
    && useradd --create-home --shell /bin/bash --uid 1001 appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

USER appuser

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9090/health || exit 1

# Use exec form for proper signal handling, but keep validation
CMD ["sh", "-c", "python validate_config.py && exec python run.py"]
