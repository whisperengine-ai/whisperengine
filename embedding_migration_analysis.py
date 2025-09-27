#!/usr/bin/env python3
"""
WhisperEngine Embedding Migration Analysis
Analyze the current vector store for mixed embedding models and plan migration
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from fastembed import TextEmbedding

async def analyze_vector_store():
    """Analyze the current vector store to understand the embedding model situation"""
    
    print("🔍 WhisperEngine Embedding Migration Analysis")
    print("=" * 60)
    
    try:
        # Connect to Qdrant
        client = QdrantClient(host="localhost", port=6334)
        collection_name = "whisperengine_memory"
        
        # Get collection info
        info = client.get_collection(collection_name)
        total_vectors = info.points_count
        print(f"📊 Total vectors in collection: {total_vectors}")
        
        # Sample data to analyze timeline and content
        sample_size = min(100, total_vectors or 0)
        points_result = client.scroll(collection_name, limit=sample_size, with_payload=True, with_vectors=["content", "emotion", "semantic"])  # ✅ FIXED: Specify named vectors
        points = points_result[0] if points_result[0] else []
        
        print(f"📝 Analyzing {len(points)} sample points...")
        
        # Analyze data patterns
        bot_stats = defaultdict(int)
        timestamp_analysis = []
        content_samples = []
        
        for point in points:
            if point.payload:
                # Bot distribution
                bot_name = point.payload.get('bot_name', 'unknown')
                bot_stats[bot_name] += 1
                
                # Timeline analysis
                if 'timestamp' in point.payload:
                    timestamp_analysis.append(point.payload['timestamp'])
                
                # Content sampling for re-embedding
                if 'content' in point.payload:
                    content_samples.append({
                        'id': point.id,
                        'content': point.payload['content'],
                        'bot_name': bot_name,
                        'timestamp': point.payload.get('timestamp', ''),
                        'vector_dim': len(point.vector) if point.vector else 0
                    })
        
        # Print analysis
        print(f"\n🤖 Bot Distribution:")
        for bot, count in sorted(bot_stats.items()):
            percentage = (count / len(points)) * 100
            print(f"  {bot}: {count} vectors ({percentage:.1f}%)")
        
        # Vector dimension analysis
        vector_dims = [len(point.vector) if point.vector else 0 for point in points]
        unique_dims = set(vector_dims)
        print(f"\n📏 Vector Dimensions Found: {sorted(unique_dims)}")
        
        if len(unique_dims) > 1:
            print("⚠️  WARNING: Multiple vector dimensions detected!")
            for dim in sorted(unique_dims):
                count = vector_dims.count(dim)
                print(f"  {dim}D vectors: {count} ({(count/len(points)*100):.1f}%)")
        
        # Timeline analysis
        if timestamp_analysis:
            # Convert string timestamps to datetime for analysis
            dates = []
            for ts in timestamp_analysis:
                try:
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        dates.append(dt)
                except:
                    pass
            
            if dates:
                dates.sort()
                print(f"\n📅 Timeline Analysis:")
                print(f"  Earliest: {dates[0].strftime('%Y-%m-%d %H:%M')}")
                print(f"  Latest: {dates[-1].strftime('%Y-%m-%d %H:%M')}")
                print(f"  Span: {(dates[-1] - dates[0]).days} days")
        
        # Test current embedding model
        print(f"\n🧪 Current Embedding Model Test:")
        current_embedder = TextEmbedding()  # Use default from env
        print(f"  Model: {current_embedder.model_name}")
        
        test_embedding = list(current_embedder.embed(["test"]))[0]
        current_dim = len(test_embedding)
        print(f"  Dimension: {current_dim}")
        
        # Check if we need migration
        stored_dims = [d for d in unique_dims if d > 0]
        if stored_dims and current_dim not in stored_dims:
            print(f"\n⚠️  MIGRATION NEEDED:")
            print(f"  Stored vectors: {stored_dims} dimensions")
            print(f"  Current model: {current_dim} dimensions")
            print(f"  This mismatch will cause search quality issues!")
        elif len(stored_dims) > 1:
            print(f"\n⚠️  MIXED DIMENSIONS DETECTED:")
            print(f"  Multiple embedding models were used: {stored_dims}")
            print(f"  Recommend full re-embedding for consistency")
        else:
            print(f"\n✅ Dimension consistency check passed")
        
        return {
            'total_vectors': total_vectors,
            'bot_stats': dict(bot_stats),
            'vector_dimensions': sorted(unique_dims),
            'current_model_dim': current_dim,
            'needs_migration': current_dim not in stored_dims or len(stored_dims) > 1,
            'content_samples': content_samples[:10]  # First 10 for testing
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_migration_plan(analysis_result):
    """Create a migration plan based on analysis"""
    
    if not analysis_result:
        return
    
    print(f"\n🚀 MIGRATION PLAN")
    print("=" * 40)
    
    if analysis_result['needs_migration']:
        print("📋 Recommended Actions:")
        print("1. ✅ Backup current vector collection")
        print("2. 🔄 Re-embed ALL vectors with consistent model")
        print("3. ✅ Validate search quality post-migration")
        print("4. 🧹 Clean up old inconsistent vectors")
        
        print(f"\n⚡ Migration Scope:")
        print(f"  Total vectors to re-embed: {analysis_result['total_vectors']:,}")
        
        est_time = analysis_result['total_vectors'] * 0.002  # ~2ms per embedding
        print(f"  Estimated time: {est_time/60:.1f} minutes")
        
        print(f"\n🎯 Target Configuration:")
        print(f"  Model: BAAI/bge-small-en-v1.5 (current default)")
        print(f"  Dimensions: {analysis_result['current_model_dim']}")
        print(f"  Bots affected: {list(analysis_result['bot_stats'].keys())}")
    else:
        print("✅ No migration needed - vectors are consistent")

if __name__ == "__main__":
    # Run analysis
    result = asyncio.run(analyze_vector_store())
    
    # Create migration plan
    create_migration_plan(result)
    
    print(f"\n📝 Next Steps:")
    print("1. Review analysis results above")
    print("2. If migration needed, run: python embedding_migration_script.py")
    print("3. Monitor bot performance post-migration")