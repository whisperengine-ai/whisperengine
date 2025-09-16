#!/usr/bin/env python3
"""
Test the full production optimization system activation
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_full_production_activation():
    """Test the complete production optimization activation flow"""


    # Import and create bot core
    from src.core.bot import DiscordBotCore

    bot_core = DiscordBotCore(debug_mode=True)

    try:
        bot_core.initialize_all()
    except Exception:
        return False


    if bot_core.production_adapter:
        try:
            success = await bot_core.production_adapter.initialize_production_mode()

            if success:

                # Test a sample operation

                if (
                    hasattr(bot_core.production_adapter, "production_integrator")
                    and bot_core.production_adapter.production_integrator
                ):
                    try:
                        # Test a sample message processing
                        test_result = await bot_core.production_adapter.production_integrator.process_message_production(
                            user_id="test_user_123",
                            message="Hello, this is a test message!",
                            context={"test": True, "channel_id": "test_channel"},
                            priority="normal",
                        )

                        if test_result:
                            if "emotion_analysis" in test_result:
                                test_result["emotion_analysis"]
                        else:
                            pass

                    except Exception:
                        pass
                else:
                    pass

                return True

            else:
                return False

        except Exception:
            return False
    else:
        return False


if __name__ == "__main__":

    success = asyncio.run(test_full_production_activation())

    if success:
        pass
    else:
        pass
