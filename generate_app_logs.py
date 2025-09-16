#!/usr/bin/env python3
"""
Simple test to interact with WhisperEngine app and generate logs
"""

import logging
import time


def generate_app_logs():
    """Generate application-like log messages"""
    # Get loggers for various components
    loggers = {
        "main": logging.getLogger("__main__"),
        "ai_service": logging.getLogger("src.core.native_ai_service"),
        "settings": logging.getLogger("src.ui.native_settings_manager"),
        "platform": logging.getLogger("src.platforms.platform_adapter"),
        "memory": logging.getLogger("src.memory.context_aware"),
        "ui": logging.getLogger("src.ui.system_logs_widget"),
    }

    # Simulate application activity
    loggers["main"].info("Starting WhisperEngine session simulation")

    time.sleep(0.1)
    loggers["settings"].info("Loading user preferences...")
    loggers["settings"].debug("Theme: dark, font_size: 12, opacity: 0.95")

    time.sleep(0.1)
    loggers["ai_service"].info("Initializing AI service connection")
    loggers["ai_service"].debug("LLM endpoint: http://localhost:1234/v1")
    loggers["ai_service"].warning("LLM server not detected, using mock responses")

    time.sleep(0.1)
    loggers["platform"].info("Platform adapter configured for macOS")
    loggers["platform"].debug("Window decorations: native, tray icon: enabled")

    time.sleep(0.1)
    loggers["memory"].info("Context-aware memory system initialized")
    loggers["memory"].debug("Vector store: ChromaDB, cache: Redis (disabled)")

    time.sleep(0.1)
    loggers["ui"].info("System logs widget initialized and capturing logs")
    loggers["ui"].debug("Max entries: 1000, auto-scroll: enabled")

    time.sleep(0.1)
    loggers["main"].info("User message received: 'Hello, how are you today?'")
    loggers["ai_service"].debug("Processing user input, length: 25 characters")
    loggers["ai_service"].info("Generating AI response...")

    time.sleep(0.2)
    loggers["ai_service"].info("AI response generated successfully")
    loggers["memory"].debug("Storing conversation in memory context")

    time.sleep(0.1)
    loggers["main"].info("Response displayed to user")

    # Simulate some warnings and errors
    time.sleep(0.1)
    loggers["memory"].warning("Memory usage at 85% capacity")
    loggers["ai_service"].error("Temporary connection timeout, retrying...")
    loggers["ai_service"].info("Connection restored successfully")

    time.sleep(0.1)
    loggers["main"].info("WhisperEngine session simulation completed")



if __name__ == "__main__":
    generate_app_logs()
