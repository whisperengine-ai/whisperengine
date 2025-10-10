# WhisperEngine Production Dockerfile
# Multi-stage build for optimized production container with pre-downloaded models

FROM python:3.13-slim AS base

# Model Download Stage
FROM base AS model-downloader

# Set environment variables for model downloading
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/root/.cache/huggingface \
    TRANSFORMERS_CACHE=/root/.cache/huggingface \
    FASTEMBED_CACHE_PATH=/root/.cache/fastembed

WORKDIR /app

# Install build dependencies and model download requirements
RUN apt-get update && apt-get install -y \
    gcc g++ git curl \
    libopus-dev libffi-dev libnacl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install model download dependencies (lighter than full requirements)
RUN pip install --no-cache-dir \
    fastembed>=0.7.0 \
    numpy>=1.24.0 \
    transformers>=4.56.0 \
    torch>=2.0.0

# Create model directories and cache directories
RUN mkdir -p /app/models /root/.cache/huggingface /root/.cache/fastembed

# Copy model download script
COPY scripts/download_models.py ./

# Download all models during build (FastEmbed + RoBERTa)
# This includes:
# - sentence-transformers/all-MiniLM-L6-v2 (384D embeddings)
# - cardiffnlp/twitter-roberta-base-emotion-multilabel-latest (emotion analysis)
RUN python download_models.py

# Verify models were downloaded and show sizes
RUN echo "📊 Model Download Summary:" && \
    du -sh /app/models/* 2>/dev/null || echo "No model files in /app/models" && \
    echo "📁 FastEmbed cache:" && \
    du -sh /root/.cache/fastembed/* 2>/dev/null || echo "FastEmbed cache empty" && \
    echo "📁 HuggingFace cache:" && \
    du -sh /root/.cache/huggingface/* 2>/dev/null || echo "HuggingFace cache empty"

# Build stage
FROM base AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ git curl \
    libopus-dev libffi-dev libnacl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements files
COPY requirements-core.txt requirements-platform.txt requirements-discord.txt requirements-vector-memory.txt ./

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements-core.txt && \
    pip install --no-cache-dir -r requirements-platform.txt && \
    pip install --no-cache-dir -r requirements-discord.txt && \
    pip install --no-cache-dir -r requirements-vector-memory.txt

# Production stage
FROM base AS production

# Image metadata
LABEL org.opencontainers.image.title="WhisperEngine Assistant" \
      org.opencontainers.image.description="AI Character Platform with Persistent Memory" \
      org.opencontainers.image.vendor="WhisperEngine AI" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/whisperengine-ai/whisperengine" \
      org.opencontainers.image.documentation="https://github.com/whisperengine-ai/whisperengine/docs"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false \
    FASTEMBED_CACHE_PATH=/app/cache/fastembed \
    HF_HOME=/app/cache/huggingface \
    TRANSFORMERS_CACHE=/app/cache/huggingface \
    MODEL_CACHE_DIR=/app/models

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl ffmpeg wget netcat-traditional procps \
    libopus-dev libffi-dev libnacl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy pre-downloaded models from model-downloader stage
COPY --from=model-downloader /app/models /app/models
COPY --from=model-downloader /root/.cache/huggingface /app/cache/huggingface
COPY --from=model-downloader /root/.cache/fastembed /app/cache/fastembed

# Copy application code
COPY src/ ./src/
COPY pyproject.toml validate_config.py env_manager.py run.py ./
COPY characters/ ./characters/
COPY config/ ./config/
COPY sql/ ./sql/

# Create necessary directories
RUN mkdir -p \
    backups \
    privacy_data \
    temp_images \
    logs \
    data \
    cache/fastembed \
    cache/huggingface \
    logs/assistant \
    && mkdir -p logs/elena logs/marcus logs/gabriel logs/dream logs/ryan logs/sophia logs/jake logs/aethys logs/aetheris

# Verify pre-downloaded models are accessible
RUN echo "🔍 Verifying pre-downloaded models..." && \
    python -c "\
import os; \
import json; \
config_path = '/app/models/model_config.json'; \
config = json.load(open(config_path)) if os.path.exists(config_path) else {}; \
print('✅ Model configuration loaded' if config else '❌ Model configuration missing'); \
print(f'📊 Embedding model: {config.get(\"embedding_models\", {}).get(\"primary\", \"Unknown\")}' if config else ''); \
print(f'🎭 Emotion model: {config.get(\"emotion_models\", {}).get(\"primary\", \"Unknown\")}' if config else ''); \
exit(0 if config else 1) \
" && \
    echo "✅ FastEmbed cache ready:" && \
    ls -la /app/cache/fastembed/ 2>/dev/null || echo "FastEmbed cache empty" && \
    echo "✅ HuggingFace cache ready:" && \
    ls -la /app/cache/huggingface/ 2>/dev/null || echo "HuggingFace cache empty" && \
    echo "📁 Total model cache size:" && \
    du -sh /app/cache/* /app/models/* 2>/dev/null || echo "No cached models found"

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1001 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${HEALTH_CHECK_PORT:-9090}/health || exit 1

# Expose default port (can be overridden)
EXPOSE 9090

# Run the application
CMD ["python", "run.py"]