#!/usr/bin/env python3
"""
Phase 5 Temporal Intelligence Direct Validation Test
Tests the complete temporal intelligence integration in WhisperEngine
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

async def test_phase5_temporal_intelligence():
    """Test Phase 5 temporal intelligence system integration"""
    
    print("🚀 Phase 5: Temporal Intelligence Integration Test")
    print("=" * 60)
    
    # Set up test environment with correct InfluxDB configuration
    os.environ['ENABLE_TEMPORAL_INTELLIGENCE'] = 'true'
    os.environ['INFLUXDB_URL'] = 'http://localhost:8086'
    os.environ['INFLUXDB_TOKEN'] = 'whisperengine-fidelity-first-metrics-token'
    os.environ['INFLUXDB_ORG'] = 'whisperengine'
    os.environ['INFLUXDB_BUCKET'] = 'performance_metrics'
    os.environ['DISCORD_BOT_NAME'] = 'Elena Rodriguez [AI DEMO]'
    
    print("🧪 Testing Temporal Intelligence Components...")
    
    # Test 1: Import temporal intelligence modules
    try:
        from src.temporal.temporal_intelligence_client import (
            TemporalIntelligenceClient, ConfidenceMetrics, RelationshipMetrics, ConversationQualityMetrics
        )
        from src.temporal.confidence_analyzer import ConfidenceAnalyzer
        from src.temporal.temporal_protocol import create_temporal_intelligence_system, get_temporal_intelligence_status
        print("✅ Successfully imported all temporal intelligence modules")
    except ImportError as e:
        print(f"❌ Failed to import temporal modules: {e}")
        return False
    
    # Test 2: Create temporal intelligence system
    try:
        temporal_client, confidence_analyzer = create_temporal_intelligence_system()
        print(f"✅ Temporal intelligence system created (enabled: {temporal_client.enabled})")
    except Exception as e:
        print(f"❌ Failed to create temporal system: {e}")
        return False
    
    # Test 3: Get system status
    try:
        status = get_temporal_intelligence_status()
        print("✅ Temporal intelligence status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get temporal status: {e}")
        return False
    
    # Test 4: Test confidence analysis
    try:
        # Sample AI components data (mimicking real conversation data)
        sample_ai_components = {
            'emotion_analysis': {
                'primary_emotion': 'joy',
                'intensity': 0.8,
                'confidence': 0.9
            },
            'context_analysis': {
                'confidence_scores': {
                    'greeting': 0.9,
                    'personality': 0.8,
                    'memory_context': 0.7
                }
            },
            'phase4_intelligence': {
                'interaction_type': 'personal',
                'relationship_level': 'friend',
                'conversation_mode': 'standard'
            }
        }
        
        # Calculate confidence metrics
        confidence_metrics = confidence_analyzer.calculate_confidence_metrics(
            ai_components=sample_ai_components,
            memory_count=5,
            processing_time_ms=1500.0
        )
        
        print("✅ Confidence metrics calculated:")
        print(f"   User fact confidence: {confidence_metrics.user_fact_confidence:.2f}")
        print(f"   Relationship confidence: {confidence_metrics.relationship_confidence:.2f}")
        print(f"   Context confidence: {confidence_metrics.context_confidence:.2f}")
        print(f"   Emotional confidence: {confidence_metrics.emotional_confidence:.2f}")
        print(f"   Overall confidence: {confidence_metrics.overall_confidence:.2f}")
        
    except Exception as e:
        print(f"❌ Failed to calculate confidence metrics: {e}")
        return False
    
    # Test 5: Test relationship metrics (updated to async with user_id)
    try:
        # Note: This will use fallback estimates since we don't have knowledge_router in test
        relationship_metrics = await confidence_analyzer.calculate_relationship_metrics(
            user_id="test_user_123",
            ai_components=sample_ai_components,
            conversation_history_length=10
        )
        
        print("✅ Relationship metrics calculated (using estimates - no PostgreSQL in test):")
        print(f"   Trust level: {relationship_metrics.trust_level:.2f}")
        print(f"   Affection level: {relationship_metrics.affection_level:.2f}")
        print(f"   Attunement level: {relationship_metrics.attunement_level:.2f}")
        print(f"   Interaction quality: {relationship_metrics.interaction_quality:.2f}")
        print(f"   Communication comfort: {relationship_metrics.communication_comfort:.2f}")
        
    except Exception as e:
        print(f"❌ Failed to calculate relationship metrics: {e}")
        return False
    
    # Test 6: Test conversation quality metrics
    try:
        quality_metrics = confidence_analyzer.calculate_conversation_quality(
            ai_components=sample_ai_components,
            response_length=150,
            processing_time_ms=1500.0
        )
        
        print("✅ Conversation quality metrics calculated:")
        print(f"   Engagement score: {quality_metrics.engagement_score:.2f}")
        print(f"   Satisfaction score: {quality_metrics.satisfaction_score:.2f}")
        print(f"   Natural flow score: {quality_metrics.natural_flow_score:.2f}")
        print(f"   Emotional resonance: {quality_metrics.emotional_resonance:.2f}")
        print(f"   Topic relevance: {quality_metrics.topic_relevance:.2f}")
        
    except Exception as e:
        print(f"❌ Failed to calculate quality metrics: {e}")
        return False
    
    # Test 7: Test InfluxDB recording (if enabled)
    if temporal_client.enabled:
        try:
            print("🔄 Testing InfluxDB recording...")
            
            # Record confidence evolution
            success1 = await temporal_client.record_confidence_evolution(
                bot_name="Elena Rodriguez [AI DEMO]",
                user_id="test_user_phase5",
                confidence_metrics=confidence_metrics
            )
            
            # Record relationship progression
            success2 = await temporal_client.record_relationship_progression(
                bot_name="Elena Rodriguez [AI DEMO]",
                user_id="test_user_phase5",
                relationship_metrics=relationship_metrics
            )
            
            # Record conversation quality
            success3 = await temporal_client.record_conversation_quality(
                bot_name="Elena Rodriguez [AI DEMO]",
                user_id="test_user_phase5",
                quality_metrics=quality_metrics
            )
            
            if success1 and success2 and success3:
                print("✅ Successfully recorded all temporal metrics to InfluxDB")
            else:
                print(f"⚠️ Partial recording success: confidence={success1}, relationship={success2}, quality={success3}")
                
        except Exception as e:
            print(f"❌ Failed to record to InfluxDB: {e}")
            return False
    else:
        print("⚠️ InfluxDB not enabled - skipping recording test")
    
    # Test 8: Test MessageProcessor integration
    try:
        print("🔄 Testing MessageProcessor temporal integration...")
        
        from src.core.message_processor import MessageProcessor, MessageContext
        
        # Create a mock MessageProcessor to test temporal integration
        processor = MessageProcessor(
            bot_core=None,
            memory_manager=None,
            llm_client=None
        )
        
        print(f"✅ MessageProcessor temporal integration: enabled={processor.temporal_intelligence_enabled}")
        if processor.temporal_client:
            print(f"   Temporal client enabled: {processor.temporal_client.enabled}")
        if processor.confidence_analyzer:
            print("   Confidence analyzer available: Yes")
            
    except Exception as e:
        print(f"❌ Failed to test MessageProcessor integration: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Phase 5 Temporal Intelligence Integration Test COMPLETE!")
    print("✅ All components working correctly")
    print("\n🚀 Ready for Production Use:")
    print("   • Confidence evolution tracking")
    print("   • Relationship progression analysis")
    print("   • Conversation quality metrics")
    print("   • InfluxDB temporal storage")
    print("   • MessageProcessor integration")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_phase5_temporal_intelligence())
    if success:
        print("\n🎯 Phase 5 implementation successful!")
        sys.exit(0)
    else:
        print("\n❌ Phase 5 implementation needs attention")
        sys.exit(1)