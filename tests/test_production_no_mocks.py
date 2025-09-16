#!/usr/bin/env python3
"""
Test production optimization system with real implementations
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_production_system():
    """Test production optimization system with real implementations"""
    try:
        # Import necessary components
        from env_manager import load_environment
        from src.core.bot import DiscordBotCore
        from src.integration.production_system_integration import WhisperEngineProductionAdapter
        
        logger.info("🔧 Loading environment configuration...")
        if not load_environment():
            logger.error("❌ Failed to load environment configuration")
            return False
        
        # Set production optimization flag
        os.environ['ENABLE_PRODUCTION_OPTIMIZATION'] = 'true'
        
        logger.info("🚀 Testing production optimization system...")
        
        # Initialize bot core
        logger.info("⚙️ Initializing Discord bot core...")
        bot_core = DiscordBotCore(debug_mode=True)
        
        # Initialize production adapter
        logger.info("🔧 Initializing production adapter...")
        production_adapter = WhisperEngineProductionAdapter(bot_core)
        
        # Test production system initialization
        logger.info("🏗️ Testing production system initialization...")
        await production_adapter.initialize_production_mode()
        
        # Check system status
        status = production_adapter.get_system_status()
        logger.info(f"✅ Production system status: {status}")
        
        # Test component functionality through adapter
        logger.info("🧪 Testing component functionality...")
        
        # Test message processing through production pipeline
        logger.info("💬 Testing message processing...")
        result = await production_adapter.process_user_message(
            user_id='test_user',
            message='How are you doing today?',
            context={'channel_id': 'test_channel', 'priority': 'normal'}
        )
        logger.info(f"✅ Message processing result: {result}")
        
        # Test production performance
        logger.info("⚡ Testing production performance...")
        performance_stats = production_adapter.get_system_status()
        logger.info(f"✅ Performance metrics: {performance_stats}")
        
        logger.info("🎉 Production optimization system test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Production system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting production optimization test...")
    
    success = await test_production_system()
    
    if success:
        logger.info("✅ All tests passed! Production system is working with real implementations.")
    else:
        logger.error("❌ Tests failed! Check logs for details.")
    
    return success

if __name__ == "__main__":
    import signal
    
    def signal_handler(sig, frame):
        logger.info("🛑 Test interrupted by user")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)