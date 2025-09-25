#!/usr/bin/env python3
"""
Test Elena Infrastructure (Localhost)
Verify localhost connections work for Elena testing
"""

import os
import sys

# Set up localhost environment
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['REDIS_HOST'] = 'localhost'  
os.environ['REDIS_PORT'] = '6380'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'

def test_postgres():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ['POSTGRES_HOST'],
            port=os.environ['POSTGRES_PORT'],
            database='whisperengine',
            user='whisperengine', 
            password='whisperengine123'
        )
        conn.close()
        print("✅ PostgreSQL: Connected")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    try:
        import redis
        r = redis.Redis(
            host=os.environ['REDIS_HOST'],
            port=int(os.environ['REDIS_PORT']),
            decode_responses=True
        )
        r.ping()
        print("✅ Redis: Connected")
        return True
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

def test_qdrant():
    """Test Qdrant connection"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            host=os.environ['QDRANT_HOST'],
            port=int(os.environ['QDRANT_PORT'])
        )
        collections = client.get_collections()
        print(f"✅ Qdrant: Connected ({len(collections.collections)} collections)")
        return True
    except Exception as e:
        print(f"❌ Qdrant: {e}")
        return False

def test_character_file():
    """Test Elena character file exists"""
    from pathlib import Path
    
    elena_file = Path("characters/examples/elena-rodriguez.json")
    if elena_file.exists():
        print("✅ Elena character file: Found")
        return True
    else:
        print("❌ Elena character file: Not found")
        return False

def test_env_file():
    """Test Elena .env file exists"""
    from pathlib import Path
    
    env_file = Path(".env.elena")
    if env_file.exists():
        print("✅ Elena .env file: Found")
        return True
    else:
        print("❌ Elena .env file: Not found")
        return False

def main():
    """Run infrastructure tests"""
    print("🏗️  Elena Infrastructure Test (Localhost)")
    print("="*50)
    
    tests = [
        ("PostgreSQL", test_postgres),
        ("Redis", test_redis), 
        ("Qdrant", test_qdrant),
        ("Character File", test_character_file),
        ("Environment File", test_env_file)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"🔍 Testing {name}...")
        success = test_func()
        results.append(success)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Infrastructure Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total:.1%}")
    
    if passed == total:
        print("🎉 All infrastructure ready for Elena testing!")
    else:
        print("⚠️  Infrastructure issues found")
        print("   💡 Make sure multi-bot containers are running:")
        print("   ./multi-bot.sh start all")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)