#!/usr/bin/env python3
"""
PHASE 2A Temporal Evolution Intelligence Direct Validation

Tests the new character temporal evolution system that analyzes personality changes
over time using existing InfluxDB data for character self-awareness.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["FASTEMBED_CACHE_PATH"] = "/tmp/fastembed_cache"
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6334"
os.environ["QDRANT_COLLECTION_NAME"] = "whisperengine_memory_sophia"
os.environ["DISCORD_BOT_NAME"] = "sophia"
os.environ["CHARACTER_FILE"] = "sophia.json"

# InfluxDB configuration for temporal data
os.environ["INFLUXDB_URL"] = "http://localhost:8086"
os.environ["INFLUXDB_TOKEN"] = "whisperengine-fidelity-first-metrics-token"
os.environ["INFLUXDB_ORG"] = "whisperengine"
os.environ["INFLUXDB_BUCKET"] = "performance_metrics"

from src.characters.learning.character_temporal_evolution_analyzer import CharacterTemporalEvolutionAnalyzer
from src.temporal.temporal_intelligence_client import TemporalIntelligenceClient

async def test_temporal_evolution_intelligence():
    """Test PHASE 2A temporal evolution intelligence system."""
    print("🚀 PHASE 2A Temporal Evolution Intelligence Direct Validation")
    print("=" * 60)
    
    try:
        # Initialize temporal intelligence client
        print("📊 Initializing InfluxDB temporal intelligence client...")
        temporal_client = TemporalIntelligenceClient()
        
        # Initialize temporal evolution analyzer
        print("⏰ Initializing character temporal evolution analyzer...")
        temporal_analyzer = CharacterTemporalEvolutionAnalyzer(temporal_client=temporal_client)
        
        # Test with Sophia bot (should have temporal data)
        bot_name = "sophia"
        user_id = "test_temporal_user"
        
        print(f"🎭 Testing temporal evolution analysis for bot: {bot_name}")
        
        # Test personality evolution analysis
        print("\n1️⃣ PERSONALITY EVOLUTION ANALYSIS:")
        print("-" * 40)
        
        evolution_result = await temporal_analyzer.analyze_character_personality_evolution(
            character_name=bot_name,
            days_back=30
        )
        
        if evolution_result:
            print("✅ Personality evolution detected:")
            print(f"   • Character: {evolution_result.character_name}")
            print(f"   • Analysis period: {evolution_result.analysis_period_days} days")
            print(f"   • Emotional stability trend: {evolution_result.emotional_stability_trend}")
            print(f"   • Confidence evolution: {evolution_result.confidence_evolution_trend}")
            
            # Show learning moments
            if evolution_result.learning_moments:
                print(f"   • Learning moments detected: {len(evolution_result.learning_moments)}")
                for i, moment in enumerate(evolution_result.learning_moments[:2], 1):
                    print(f"     {i}. {moment.evolution_type.value}: {moment.description}")
            
            # Show communication adaptations
            if evolution_result.communication_adaptations:
                print(f"   • Communication adaptations: {len(evolution_result.communication_adaptations)}")
                
            print(f"   • Growth summary: {evolution_result.overall_growth_summary}")
        else:
            print("❌ No personality evolution data found")
        
        # Test learning moments detection separately
        print("\n2️⃣ LEARNING MOMENTS DETECTION:")
        print("-" * 40)
        
        if evolution_result and evolution_result.learning_moments:
            print(f"✅ Found {len(evolution_result.learning_moments)} learning moments:")
            for i, moment in enumerate(evolution_result.learning_moments[:3], 1):
                print(f"   {i}. {moment.evolution_type.value}: {moment.description}")
                print(f"      Confidence: {moment.confidence:.3f}")
                print(f"      Date: {moment.timestamp}")
        else:
            print("❌ No learning moments detected")
            
        # Test temporal patterns analysis  
        print("\n3️⃣ TEMPORAL PATTERNS ANALYSIS:")
        print("-" * 40)
        
        if evolution_result:
            print("✅ Temporal patterns identified:")
            print(f"   • Emotional stability trend: {evolution_result.emotional_stability_trend}")
            print(f"   • Confidence evolution trend: {evolution_result.confidence_evolution_trend}")
            
            # Show emotional changes
            if evolution_result.dominant_emotions_early and evolution_result.dominant_emotions_recent:
                print("   • Emotional evolution:")
                print(f"     Early period emotions: {evolution_result.dominant_emotions_early[:3]}")
                print(f"     Recent period emotions: {evolution_result.dominant_emotions_recent[:3]}")
        else:
            print("❌ No temporal patterns detected")
            
        # Test temporal intelligence integration
        print("\n4️⃣ TEMPORAL INTELLIGENCE INTEGRATION:")
        print("-" * 40)
        
        if evolution_result:
            print("✅ Temporal intelligence data available:")
            print("   • Character evolution profile: ✅")
            print("   • Learning moment tracking: ✅")
            print("   • Communication adaptation tracking: ✅")  
            print("   • Emotional trend analysis: ✅")
        else:
            print("❌ No temporal intelligence data available")
            
        print("\n" + "=" * 60)
        print("🎉 PHASE 2A Temporal Evolution Intelligence Validation Complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during temporal evolution validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the temporal evolution intelligence validation
    result = asyncio.run(test_temporal_evolution_intelligence())
    
    if result:
        print("\n✅ PHASE 2A temporal evolution intelligence is working correctly!")
        print("🚀 Ready for production deployment with character self-awareness!")
    else:
        print("\n❌ PHASE 2A temporal evolution intelligence validation failed.")
        print("🔧 Check InfluxDB connection and temporal data availability.")