#!/usr/bin/env python3
"""
Quick Elena Test Runner
Simple script to test Elena's personality and emotional intelligence
"""

import asyncio
import os
import sys
from pathlib import Path

# Set up localhost environment BEFORE any imports
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'  # Multi-bot port
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'     # Multi-bot port
os.environ['REDIS_PASSWORD'] = ''

os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'    # Multi-bot port

# Override any container hostnames that might be in .env.elena
os.environ['MEMORY_QDRANT_HOST'] = 'localhost'
os.environ['MEMORY_QDRANT_PORT'] = '6334'
os.environ['MEMORY_POSTGRESQL_HOST'] = 'localhost'
os.environ['MEMORY_POSTGRESQL_PORT'] = '5433'
os.environ['MEMORY_REDIS_HOST'] = 'localhost'
os.environ['MEMORY_REDIS_PORT'] = '6380'

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from elena_personality_test import ElenaPersonalityTester

async def run_quick_test():
    """Run a quick personality test"""
    print("🧪 Elena Personality Quick Test")
    print("="*50)
    
    tester = ElenaPersonalityTester()
    
    try:
        # Run just the key personality tests
        results = {}
        
        # Test 1: CDL Character System
        print("🔍 Testing CDL Character System...")
        success, details = await tester.test_cdl_character_system()
        results["cdl_system"] = success
        print(f"   {'✅' if success else '❌'} CDL Character System")
        
        # Test 2: Spanish Integration
        print("🔍 Testing Spanish Integration...")
        success, details = await tester.test_spanish_integration()
        results["spanish"] = success
        print(f"   {'✅' if success else '❌'} Spanish Integration")
        
        # Test 3: Ocean Emojis
        print("🔍 Testing Ocean Emojis...")
        success, details = await tester.test_ocean_emoji_usage()
        results["emojis"] = success
        print(f"   {'✅' if success else '❌'} Ocean Emojis")
        
        # Test 4: Marine Biology Personality
        print("🔍 Testing Marine Biology Personality...")
        success, details = await tester.test_marine_biology_personality()
        results["marine_bio"] = success
        print(f"   {'✅' if success else '❌'} Marine Biology Personality")
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        print("\n📊 Quick Test Results:")
        print(f"   Passed: {passed}/{total}")
        print(f"   Success Rate: {passed/total:.1%}")
        
        if passed == total:
            print("🎉 All core personality features working!")
        else:
            print("⚠️  Some personality features need attention")
            for test, success in results.items():
                if not success:
                    print(f"   ❌ {test}")
        
        return passed == total
        
    except Exception as e:
        print(f"💥 Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_quick_test())
    exit(0 if success else 1)