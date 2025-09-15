#!/usr/bin/env python3
"""
Simple log generation test for system logs viewer
"""
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_logs():
    """Generate various log levels"""
    logger = logging.getLogger("TestLogGenerator")
    
    logger.info("🎬 Starting log generation test...")
    time.sleep(0.1)
    
    logger.debug("This is a DEBUG message - shows detailed diagnostic information")
    time.sleep(0.1)
    
    logger.info("This is an INFO message - general application flow information")
    time.sleep(0.1)
    
    logger.warning("This is a WARNING message - something unexpected but not critical")
    time.sleep(0.1)
    
    logger.error("This is an ERROR message - something went wrong but app continues")
    time.sleep(0.1)
    
    logger.critical("This is a CRITICAL message - serious error occurred")
    time.sleep(0.1)
    
    # Test different logger names
    ui_logger = logging.getLogger("WhisperEngine.UI")
    ui_logger.info("UI component initialized successfully")
    
    ai_logger = logging.getLogger("WhisperEngine.AI")
    ai_logger.debug("Processing user message...")
    ai_logger.info("AI response generated")
    
    memory_logger = logging.getLogger("WhisperEngine.Memory")
    memory_logger.warning("Memory usage approaching threshold")
    
    logger.info("✅ Log generation test completed")
    print("📋 Check the 'System Logs' tab in WhisperEngine to see these messages!")
    print("🔍 Try filtering by different log levels")
    print("📋 Test the Copy All and Copy Selected buttons")

if __name__ == "__main__":
    generate_logs()