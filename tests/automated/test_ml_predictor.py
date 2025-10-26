#!/usr/bin/env python3
"""
Test ML Response Strategy Predictor (Standalone)

Tests the predictor in isolation without modifying any production code.
Verifies:
1. Model loads successfully
2. InfluxDB connection works
3. Feature extraction works for users with 7+ messages
4. Predictions are generated with reasonable confidence
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup environment
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('INFLUXDB_HOST', 'localhost')
os.environ.setdefault('INFLUXDB_PORT', '8087')

from influxdb_client import InfluxDBClient
from src.ml import create_response_strategy_predictor


async def test_model_loading():
    """Test 1: Verify model loads successfully"""
    print("\n" + "="*70)
    print("TEST 1: Model Loading")
    print("="*70)
    
    try:
        predictor = create_response_strategy_predictor()
        
        if predictor.model is None:
            print("❌ FAIL: Model not loaded")
            print("\n💡 Troubleshooting:")
            print("   1. Train model first: cd experiments/notebooks && jupyter nbconvert --execute 01_response_strategy_optimization.ipynb")
            print("   2. Or run: python experiments/notebooks/01_response_strategy_optimization.py")
            return False
        
        print(f"✅ PASS: Model loaded successfully")
        print(f"   Model type: {type(predictor.model).__name__}")
        print(f"   Features: {len(predictor.feature_names)}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error loading model: {e}")
        return False


async def test_influxdb_connection():
    """Test 2: Verify InfluxDB connection"""
    print("\n" + "="*70)
    print("TEST 2: InfluxDB Connection")
    print("="*70)
    
    try:
        influxdb_host = os.getenv("INFLUXDB_HOST", "localhost")
        influxdb_port = os.getenv("INFLUXDB_PORT", "8087")
        
        client = InfluxDBClient(
            url=f"http://{influxdb_host}:{influxdb_port}",
            token="whisperengine-fidelity-first-metrics-token",
            org="whisperengine"
        )
        
        # Test query
        query_api = client.query_api()
        test_query = '''
        from(bucket: "performance_metrics")
          |> range(start: -1d)
          |> filter(fn: (r) => r._measurement == "conversation_quality")
          |> limit(n: 1)
        '''
        
        result = query_api.query(test_query)
        
        print(f"✅ PASS: Connected to InfluxDB at {influxdb_host}:{influxdb_port}")
        return True, client
        
    except Exception as e:
        print(f"❌ FAIL: InfluxDB connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Start infrastructure: ./multi-bot.sh infra")
        print("   2. Check InfluxDB is running: docker ps | grep influxdb")
        return False, None


async def test_user_data_availability(client):
    """Test 3: Find users with sufficient data for predictions"""
    print("\n" + "="*70)
    print("TEST 3: User Data Availability")
    print("="*70)
    
    try:
        query_api = client.query_api()
        
        # Find users with 7+ messages
        query = '''
        from(bucket: "performance_metrics")
          |> range(start: -7d)
          |> filter(fn: (r) => r._measurement == "conversation_quality")
          |> group(columns: ["user_id", "bot"])
          |> count()
        '''
        
        result = query_api.query(query)
        
        eligible_users = []
        for table in result:
            for record in table.records:
                count = record.get_value()
                if count >= 7:
                    user_id = record.values.get('user_id')
                    bot = record.values.get('bot')
                    eligible_users.append((user_id, bot, count))
        
        if eligible_users:
            print(f"✅ PASS: Found {len(eligible_users)} user-bot pairs with 7+ messages")
            print("\n📊 Top 5 users with most messages:")
            for user_id, bot, count in sorted(eligible_users, key=lambda x: x[2], reverse=True)[:5]:
                print(f"   - {user_id[:20]:20s} @ {bot:10s} ({count:3d} messages)")
            return True, eligible_users
        else:
            print("⚠️  WARNING: No users with 7+ messages found")
            print("\n💡 Generate test data:")
            print("   1. Use HTTP chat API to create test conversations")
            print("   2. Or run synthetic data generator (if available)")
            return False, []
        
    except Exception as e:
        print(f"❌ FAIL: Error querying user data: {e}")
        return False, []


async def test_prediction(client, eligible_users):
    """Test 4: Run actual prediction on real user"""
    print("\n" + "="*70)
    print("TEST 4: ML Prediction")
    print("="*70)
    
    if not eligible_users:
        print("⏭️  SKIP: No eligible users (need users with 7+ messages)")
        return False
    
    try:
        # Create predictor with InfluxDB client
        predictor = create_response_strategy_predictor(influxdb_client=client)
        
        # Test on user with most messages
        user_id, bot_name, message_count = eligible_users[0]
        
        print(f"\n🧪 Testing prediction for:")
        print(f"   User: {user_id}")
        print(f"   Bot: {bot_name}")
        print(f"   Message history: {message_count} messages")
        
        # Run prediction
        prediction = await predictor.predict_strategy_effectiveness(
            user_id=user_id,
            bot_name=bot_name,
            message_content="Test message for ML prediction",
            current_mode="testing"
        )
        
        if prediction is None:
            print("❌ FAIL: Prediction returned None")
            return False
        
        print(f"\n✅ PASS: Prediction generated successfully")
        print(f"\n📊 Prediction Results:")
        print(f"   Is Effective: {prediction.is_effective}")
        print(f"   Confidence: {prediction.confidence:.2%}")
        print(f"   Recommended Modes: {', '.join(prediction.recommended_modes)}")
        print(f"\n🔍 Top Features (importance):")
        for feature, importance in list(prediction.feature_importance.items())[:5]:
            print(f"   {feature:30s} {importance:.4f}")
        print(f"\n📝 Metadata:")
        print(f"   Current Mode: {prediction.prediction_metadata.get('current_mode')}")
        print(f"   Engagement: {prediction.prediction_metadata.get('engagement_score'):.2f}")
        print(f"   Satisfaction: {prediction.prediction_metadata.get('satisfaction_score'):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_predictions(client, eligible_users):
    """Test 5: Run predictions on multiple users (shadow mode simulation)"""
    print("\n" + "="*70)
    print("TEST 5: Multiple Predictions (Shadow Mode Simulation)")
    print("="*70)
    
    if not eligible_users:
        print("⏭️  SKIP: No eligible users")
        return False
    
    try:
        predictor = create_response_strategy_predictor(influxdb_client=client)
        
        # Test on up to 5 users
        test_users = eligible_users[:5]
        results = []
        
        print(f"\n🧪 Running predictions on {len(test_users)} users...")
        
        for user_id, bot_name, _ in test_users:
            prediction = await predictor.predict_strategy_effectiveness(
                user_id=user_id,
                bot_name=bot_name,
                message_content="Shadow mode test",
                current_mode="unknown"
            )
            
            if prediction:
                results.append({
                    'user_id': user_id[:20],
                    'bot': bot_name,
                    'effective': prediction.is_effective,
                    'confidence': prediction.confidence,
                    'modes': prediction.recommended_modes[0]
                })
        
        if results:
            print(f"\n✅ PASS: Generated {len(results)} predictions")
            print(f"\n📊 Summary:")
            print(f"{'User':<20} {'Bot':<10} {'Effective':<10} {'Confidence':<12} {'Mode':<15}")
            print("-" * 70)
            for r in results:
                print(f"{r['user_id']:<20} {r['bot']:<10} {str(r['effective']):<10} "
                      f"{r['confidence']:.2%} {r['modes']:<15}")
            
            effective_count = sum(1 for r in results if r['effective'])
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            
            print(f"\n📈 Statistics:")
            print(f"   Effective conversations: {effective_count}/{len(results)} ({effective_count/len(results):.1%})")
            print(f"   Average confidence: {avg_confidence:.2%}")
            
            return True
        else:
            print("❌ FAIL: No predictions generated")
            return False
        
    except Exception as e:
        print(f"❌ FAIL: Multiple prediction error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ML RESPONSE STRATEGY PREDICTOR - STANDALONE TEST")
    print("Phase 1: Shadow Mode Validation")
    print("="*70)
    
    results = []
    
    # Test 1: Model loading
    results.append(("Model Loading", await test_model_loading()))
    
    # Test 2: InfluxDB connection
    influxdb_ok, client = await test_influxdb_connection()
    results.append(("InfluxDB Connection", influxdb_ok))
    
    if not influxdb_ok:
        print("\n⚠️  Cannot continue without InfluxDB connection")
        print_summary(results)
        return
    
    # Test 3: User data availability
    data_ok, eligible_users = await test_user_data_availability(client)
    results.append(("User Data Availability", data_ok))
    
    if not data_ok:
        print("\n⚠️  No users with sufficient data for testing")
        print_summary(results)
        return
    
    # Test 4: Single prediction
    results.append(("Single Prediction", await test_prediction(client, eligible_users)))
    
    # Test 5: Multiple predictions (shadow mode)
    results.append(("Shadow Mode Simulation", await test_multiple_predictions(client, eligible_users)))
    
    # Summary
    print_summary(results)
    
    # Cleanup
    client.close()


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10s} {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n📊 Results: {passed_count}/{total_count} tests passed ({passed_count/total_count:.1%})")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Ready for Phase 2 integration.")
    else:
        print("\n⚠️  Some tests failed. Fix issues before proceeding.")


if __name__ == "__main__":
    asyncio.run(main())
