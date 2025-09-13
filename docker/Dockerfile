# Discord Bot - Universal Dockerfile
FROM python:3.13-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false \
    BOT_SYSTEM_PROMPT_FILE=/app/system_prompt.md

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    gcc g++ git curl ffmpeg wget netcat-traditional procps \
    libopus-dev libffi-dev libnacl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add spaCy model download
RUN python -m spacy download en_core_web_sm

# Copy application code (will be overridden by volume mounts in development)
COPY src/ ./src/
COPY pyproject.toml validate_config.py env_manager.py run.py ./
# Copy environment files for configuration
COPY .env* ./

# Copy system prompt (default, can be overridden by volume mount)
COPY system_prompt.md ./system_prompt.md

# Create directories and non-root user in one layer
RUN mkdir -p backups privacy_data temp_images logs \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Start bot with validation
CMD ["sh", "-c", "python validate_config.py && python run.py"]
