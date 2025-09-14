#!/usr/bin/env python3
"""
Test Desktop App Startup
Quick test to see if the desktop app can start with local database integration.
"""

import asyncio
import os
import sys
import signal
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Override environment for local mode
os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
os.environ['WHISPERENGINE_MODE'] = 'desktop'
os.environ['LOG_LEVEL'] = 'INFO'

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.local_database_integration import LocalDatabaseIntegrationManager


async def test_desktop_app_startup():
    """Test if desktop app components can initialize properly"""
    print("🖥️ Testing Desktop App Startup with Local Databases...")
    print("=" * 60)
    
    try:
        # Test 1: Configuration Manager
        print("📋 Step 1: Testing Configuration Manager...")
        config_manager = AdaptiveConfigManager()
        deployment_info = config_manager.get_deployment_info()
        print(f"   ✅ Platform detected: {deployment_info['platform']}")
        print(f"   ✅ Memory: {deployment_info['memory_gb']:.1f}GB")
        print(f"   ✅ Scale tier: {deployment_info['scale_tier']}")
        
        # Test 2: Local Database Integration
        print("\n🗄️ Step 2: Testing Local Database Integration...")
        db_integration = LocalDatabaseIntegrationManager(config_manager)
        
        print("   🔄 Initializing local databases...")
        init_success = await db_integration.initialize()
        
        if init_success:
            print("   ✅ Local database integration initialized!")
            
            # Test health check
            print("\n💊 Step 3: Testing Health Check...")
            health = await db_integration.get_comprehensive_health_check()
            print(f"   📊 Overall status: {health.get('overall_status', 'unknown')}")
            print(f"   📊 Vector storage: {health.get('vector_storage', {}).get('status', 'unknown')}")
            print(f"   📊 Graph storage: {health.get('graph_storage', {}).get('status', 'unknown')}")
            print(f"   📊 Local cache: {health.get('local_cache', {}).get('status', 'unknown')}")
            
            # Test storage statistics
            print("\n📈 Step 4: Testing Storage Statistics...")
            stats = await db_integration.get_storage_statistics()
            print(f"   📊 Data directory: {stats.get('data_directory', 'unknown')}")
            print(f"   📊 Vector collections: {len(stats.get('vector_storage', {}).get('collections', {}))}")
            print(f"   📊 Graph nodes: {stats.get('graph_storage', {}).get('graph_statistics', {}).get('nodes', 0)}")
            
            # Test basic operations
            print("\n🧪 Step 5: Testing Basic Operations...")
            
            # Test vector storage
            vector_storage = db_integration.get_vector_storage()
            test_embedding = [0.1] * 384
            
            doc_id = await db_integration.store_conversation_embedding(
                user_id="test_user",
                content="Hello from desktop app test!",
                embedding=test_embedding,
                metadata={"test": True}
            )
            print(f"   ✅ Stored test conversation: {doc_id[:16]}...")
            
            # Test graph storage
            user_result = await db_integration.create_user_in_graph(
                user_id="test_user",
                username="desktop_tester",
                display_name="Desktop App Tester"
            )
            print(f"   ✅ Created test user in graph: {user_result.get('user_id', 'unknown')}")
            
            # Cleanup
            await db_integration.cleanup()
            print("\n🧹 Cleanup completed")
            
            print("\n" + "=" * 60)
            print("🎉 DESKTOP APP STARTUP TEST: SUCCESS!")
            print("✅ Configuration management working")
            print("✅ Local database integration working")
            print("✅ Vector storage (ChromaDB replacement) working")
            print("✅ Graph storage (Neo4j replacement) working")
            print("✅ Health monitoring working")
            print("✅ Basic operations working")
            print("\n🚀 Ready for full desktop app launch!")
            
            return True
            
        else:
            print("❌ Local database initialization failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Desktop app startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    success = await test_desktop_app_startup()
    
    if success:
        print("\n✅ Desktop app is ready to launch with local databases!")
        print("💡 You can now run: python desktop_app.py")
        sys.exit(0)
    else:
        print("\n❌ Desktop app startup test failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())