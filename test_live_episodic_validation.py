#!/usr/bin/env python3
"""
Live Episodic Intelligence Validation Script
Tests PHASE 1A Character Vector Episodic Intelligence in production environment
"""

import asyncio
import os
import sys

# Set environment for validation
os.environ['FASTEMBED_CACHE_PATH'] = "/tmp/fastembed_cache"
os.environ['QDRANT_HOST'] = "localhost"
os.environ['QDRANT_PORT'] = "6334"
os.environ['QDRANT_COLLECTION_NAME'] = "whisperengine_memory_sophia"  # Sophia's collection
os.environ['DISCORD_BOT_NAME'] = "sophia"

# WhisperEngine imports
sys.path.append('/Users/markcastillo/git/whisperengine')

async def test_live_episodic_intelligence():
    """Test episodic intelligence with actual production components"""
    
    print("🧠 Testing PHASE 1A Character Vector Episodic Intelligence...")
    
    try:
        # Import after environment setup
        from src.characters.learning.character_vector_episodic_intelligence import CharacterVectorEpisodicIntelligence
        from qdrant_client import QdrantClient
        
        # Initialize components
        client = QdrantClient(host="localhost", port=6334)
        episodic_intelligence = CharacterVectorEpisodicIntelligence(client)
        collection_name = "whisperengine_memory_sophia_7d"  # Correct Sophia collection
        
        print("✅ Episodic intelligence initialized successfully")
        
        # Test 1: Memorable moments detection
        print("\n🔍 Testing memorable moments detection...")
        memorable_moments = await episodic_intelligence.detect_memorable_moments_from_vector_patterns(
            collection_name=collection_name,
            user_id="episodic_test_user",
            limit=10
        )
        
        print(f"📊 Found {len(memorable_moments)} memorable moments:")
        for i, moment in enumerate(memorable_moments[:3], 1):
            print(f"  {i}. Score: {moment.memorable_score:.3f} - {moment.content[:100]}...")
        
        # Test 2: Response enhancement
        print("\n✨ Testing episodic response enhancement...")
        enhancement_data = await episodic_intelligence.get_episodic_memory_for_response_enhancement(
            collection_name=collection_name,
            current_message="I need help with my creative project",
            user_id="episodic_test_user",
            limit=5
        )
        
        print("📝 Response enhancement data:")
        print(f"  - Memorable moments: {len(enhancement_data.get('memories', []))}")
        print(f"  - Character insights: {len(enhancement_data.get('insights', []))}")
        
        if 'context_suggestions' in enhancement_data:
            print(f"  - Context suggestions: {len(enhancement_data['context_suggestions'])}")
            for suggestion in enhancement_data['context_suggestions'][:2]:
                print(f"    • {suggestion}")
        
        print("\n🎉 LIVE EPISODIC INTELLIGENCE VALIDATION COMPLETE!")
        print("✅ All components functioning correctly in production environment")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_live_episodic_intelligence())
    sys.exit(0 if success else 1)