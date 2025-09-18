"""
Enhanced logging configuration with rotation, structured logging, and environment-specific settings.
DevOps best practices implementation for the Discord bot.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for better parsing in log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "guild_id"):
            log_entry["guild_id"] = record.guild_id
        if hasattr(record, "channel_id"):
            log_entry["channel_id"] = record.channel_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        return json.dumps(log_entry, ensure_ascii=False)


class DiscordConnectionFilter(logging.Filter):
    """
    Filter to downgrade harmless Discord connection errors that look scary but are normal.
    """

    HARMLESS_CONNECTION_ERRORS = [
        "Cannot write to closing transport",
        "ClientConnectionResetError",
        "Connection reset by peer",
        "Attempting a reconnect",
        "WebSocket connection is closing",
        "Transport endpoint is not connected",
    ]

    def filter(self, record):
        """
        Downgrade scary but harmless connection errors to DEBUG level.
        Returns True to keep the record, False to drop it.
        """
        if record.levelno >= logging.ERROR:
            message = str(record.getMessage())

            # Check if this is a harmless connection error
            for harmless_error in self.HARMLESS_CONNECTION_ERRORS:
                if harmless_error in message:
                    # Downgrade to DEBUG level and make message less scary
                    record.levelno = logging.DEBUG
                    record.levelname = "DEBUG"
                    if (
                        "ClientConnectionResetError" in message
                        or "Cannot write to closing transport" in message
                    ):
                        record.msg = f"🔄 Discord connection hiccup (auto-recovering): {record.msg}"
                    elif "Attempting a reconnect" in message:
                        record.msg = f"🔄 Discord auto-reconnecting: {record.msg}"
                    break

        return True  # Always keep the record, just potentially modified


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development environments.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    debug: bool = False,
    environment: str = "development",
    log_dir: str = "logs",
    app_name: str = "discord_bot",
) -> dict[str, Any]:
    """
    Configure comprehensive logging with rotation, structured output, and environment-specific settings.

    Args:
        debug: Enable debug logging
        environment: Environment (development, production)
        log_dir: Directory for log files
        app_name: Application name for log files

    Returns:
        Dict with logging configuration details
    """

    # Determine file log level from environment variable or parameters
    log_level_str = os.getenv("LOG_LEVEL", "").upper()
    if log_level_str and hasattr(logging, log_level_str):
        file_level = getattr(logging, log_level_str)
    elif debug:
        file_level = logging.DEBUG
    elif environment == "production":
        file_level = logging.INFO
    else:
        file_level = logging.DEBUG if environment == "development" else logging.INFO

    # Determine console log level (can be different from file level)
    console_log_level_str = os.getenv("CONSOLE_LOG_LEVEL", "").upper()
    if console_log_level_str and hasattr(logging, console_log_level_str):
        console_level = getattr(logging, console_log_level_str)
    else:
        # Default to same as file level if CONSOLE_LOG_LEVEL not set
        console_level = file_level

    # Root logger level should be the most permissive (lowest) of the two
    root_level = min(file_level, console_level)

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Clear existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(root_level)

    handlers = []

    # Console Handler - Always enabled
    console_handler = logging.StreamHandler(sys.stdout)
    if environment == "development":
        # Use colored formatter for development
        console_formatter = ColoredConsoleFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        # Use structured JSON for production console output (for container logs)
        console_formatter = StructuredFormatter()

    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level)
    handlers.append(console_handler)

    # File Handlers with Rotation
    if environment == "development":
        # Development: Simple rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / f"{app_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(file_level)
        handlers.append(file_handler)

    else:
        # Production: Structured JSON logs with time-based rotation
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_path / f"{app_name}.jsonl",
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding="utf-8",
        )
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(file_level)
        handlers.append(file_handler)

        # Error-only file for critical issues
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_path / f"{app_name}_errors.jsonl",
            when="midnight",
            interval=1,
            backupCount=90,  # Keep errors longer
            encoding="utf-8",
        )
        error_handler.setFormatter(StructuredFormatter())
        error_handler.setLevel(logging.ERROR)
        handlers.append(error_handler)

    # Add all handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)

    # Configure third-party loggers to reduce noise
    third_party_loggers = {
        "discord": logging.WARNING if not debug else logging.INFO,
        "urllib3.connectionpool": logging.WARNING,
        "httpx": logging.WARNING,
        "chromadb": logging.WARNING,
        "sentence_transformers": logging.WARNING,
        "transformers": logging.WARNING,
        "asyncio": logging.WARNING if not debug else logging.INFO,
    }

    for logger_name, log_level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        # Add connection filter specifically to Discord client logger
        if logger_name == "discord.client":
            connection_filter = DiscordConnectionFilter()
            logger.addFilter(connection_filter)

    # Also add the filter to the main discord.client logger that generates the errors
    discord_client_logger = logging.getLogger("discord.client")
    discord_client_logger.addFilter(DiscordConnectionFilter())

    # Log the logging configuration
    config_info = {
        "file_level": logging.getLevelName(file_level),
        "console_level": logging.getLevelName(console_level),
        "root_level": logging.getLevelName(root_level),
        "environment": environment,
        "log_directory": str(log_path.absolute()),
        "handlers": [handler.__class__.__name__ for handler in handlers],
        "debug_enabled": debug,
    }

    logging.info("Logging configuration initialized", extra={"config": config_info})

    return config_info


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with optional context.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    user_id: int | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    request_id: str | None = None,
    **kwargs,
):
    """
    Log with additional context for better traceability.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        user_id: Discord user ID
        guild_id: Discord guild ID
        channel_id: Discord channel ID
        request_id: Request/operation ID for tracing
        **kwargs: Additional context
    """
    extra = {}
    if user_id:
        extra["user_id"] = user_id
    if guild_id:
        extra["guild_id"] = guild_id
    if channel_id:
        extra["channel_id"] = channel_id
    if request_id:
        extra["request_id"] = request_id
    extra.update(kwargs)

    logger.log(level, message, extra=extra)


# Convenience functions
def log_user_action(
    message: str, user_id: int, guild_id: int | None = None, channel_id: int | None = None
):
    """Log user actions with context."""
    logger = get_logger("discord_bot.user_actions")
    log_with_context(
        logger, logging.INFO, message, user_id=user_id, guild_id=guild_id, channel_id=channel_id
    )


def log_bot_response(
    message: str,
    user_id: int,
    response_time: float | None = None,
    guild_id: int | None = None,
):
    """Log bot responses with performance metrics."""
    logger = get_logger("discord_bot.responses")
    {"response_time_ms": response_time * 1000 if response_time else None}
    log_with_context(logger, logging.INFO, message, user_id=user_id, guild_id=guild_id)


def log_error_with_context(error: Exception, context: str, **kwargs):
    """Log errors with full context and stack trace."""
    logger = get_logger("discord_bot.errors")
    log_with_context(logger, logging.ERROR, f"{context}: {str(error)}", **kwargs)
    logger.exception("Full stack trace:", exc_info=error)
