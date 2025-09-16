#!/usr/bin/env python3
"""
Simple test to debug production optimization initialization
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_production_init():
    """Test production optimization initialization"""

    # Import and create bot core
    from src.core.bot import DiscordBotCore

    bot_core = DiscordBotCore(debug_mode=True)

    # This should trigger initialize_production_optimization
    try:
        bot_core.initialize_all()
    except Exception:
        return

    if bot_core.production_adapter:
        pass
    else:
        pass


if __name__ == "__main__":
    test_production_init()
