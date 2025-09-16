#!/usr/bin/env python3
"""
Test system logs functionality
Generates various log levels to test the logs viewer
"""

import logging


def test_logging():
    """Generate test log messages"""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger("TestLogger")

    # Generate various log levels
    logger.debug("This is a DEBUG message - used for detailed diagnostic info")
    logger.info("This is an INFO message - general application flow")
    logger.warning("This is a WARNING message - something unexpected happened")
    logger.error("This is an ERROR message - an error occurred but app continues")
    logger.critical("This is a CRITICAL message - serious error occurred")

    # Test different loggers
    ai_logger = logging.getLogger("src.core.native_ai_service")
    ai_logger.info("AI service initialized successfully")
    ai_logger.debug("Processing user message: 'Hello, how are you?'")

    ui_logger = logging.getLogger("src.ui.system_logs_widget")
    ui_logger.info("System logs widget created")
    ui_logger.debug("Applying log filter: INFO")

    memory_logger = logging.getLogger("src.memory.context_aware")
    memory_logger.info("Memory system initialized")
    memory_logger.warning("Memory cache approaching capacity limit")

    # Test threading info
    import threading

    thread_logger = logging.getLogger("ThreadTest")
    thread_logger.info(f"Running on thread: {threading.current_thread().name}")


if __name__ == "__main__":
    test_logging()
