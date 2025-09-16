#!/usr/bin/env python3
"""
Simple test to debug production optimization initialization
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_production_init():
    """Test production optimization initialization"""
    
    print("🔍 Testing Production Optimization Initialization...")
    
    # Import and create bot core
    from src.core.bot import DiscordBotCore
    
    print("Creating DiscordBotCore...")
    bot_core = DiscordBotCore(debug_mode=True)
    
    print(f"Before initialize_all: production_adapter = {bot_core.production_adapter}")
    
    # This should trigger initialize_production_optimization
    print("Calling initialize_all()...")
    try:
        bot_core.initialize_all()
        print("✅ initialize_all() completed")
    except Exception as e:
        print(f"❌ initialize_all() failed: {e}")
        return
    
    print(f"After initialize_all: production_adapter = {bot_core.production_adapter}")
    
    if bot_core.production_adapter:
        print("✅ Production adapter successfully initialized!")
        print(f"Type: {type(bot_core.production_adapter)}")
    else:
        print("❌ Production adapter is still None")

if __name__ == "__main__":
    test_production_init()