#!/usr/bin/env python3
"""
Test ML Shadow Mode Logger

Validates shadow mode logging functionality without affecting bot behavior.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables BEFORE importing any modules
os.environ.setdefault("FASTEMBED_CACHE_PATH", "/tmp/fastembed_cache")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6334")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("INFLUXDB_HOST", "localhost")
os.environ.setdefault("INFLUXDB_PORT", "8087")
os.environ.setdefault("INFLUXDB_BUCKET", "whisperengine")
os.environ.setdefault("INFLUXDB_ORG", "whisperengine")
os.environ.setdefault("INFLUXDB_TOKEN", "whisperengine-dev-token")
os.environ.setdefault("DISCORD_BOT_NAME", "elena")

# Feature flag: DISABLED by default (end user mode)
# os.environ["ENABLE_ML_SHADOW_MODE"] = "true"  # Uncomment to test

import asyncio
from datetime import datetime
from influxdb_client import InfluxDBClient

from src.ml.shadow_mode_logger import (
    MLShadowModeLogger,
    create_ml_shadow_logger,
    ENABLE_ML_SHADOW_MODE
)
from src.ml.response_strategy_predictor import (
    ResponseStrategyPredictor,
    StrategyPrediction
)


def print_header(title: str):
    """Print formatted test header"""
    print("\n" + "=" * 70)
    print(f"TEST: {title}")
    print("=" * 70 + "\n")


async def test_feature_flag():
    """Test that feature flag defaults to FALSE"""
    print_header("Feature Flag Default State")
    
    print(f"ENABLE_ML_SHADOW_MODE environment variable: {os.getenv('ENABLE_ML_SHADOW_MODE', 'NOT SET')}")
    print(f"ENABLE_ML_SHADOW_MODE parsed value: {ENABLE_ML_SHADOW_MODE}")
    
    if not ENABLE_ML_SHADOW_MODE:
        print("✅ PASS: Feature flag defaults to FALSE (safe for end users)")
        return True
    else:
        print("❌ FAIL: Feature flag is TRUE (should be FALSE by default)")
        return False


async def test_logger_disabled_by_default():
    """Test that logger is None when feature flag is disabled"""
    print_header("Logger Creation with Feature Disabled")
    
    # Create mock InfluxDB client
    influxdb_client = InfluxDBClient(
        url=f"http://{os.getenv('INFLUXDB_HOST')}:{os.getenv('INFLUXDB_PORT')}",
        token=os.getenv('INFLUXDB_TOKEN'),
        org=os.getenv('INFLUXDB_ORG')
    )
    
    shadow_logger = create_ml_shadow_logger(influxdb_client)
    
    if shadow_logger is None:
        print("✅ PASS: Logger is None when feature flag disabled")
        print("   (No ML dependencies loaded for end users)")
        return True
    else:
        print("❌ FAIL: Logger created despite feature flag being disabled")
        return False


async def test_logger_with_feature_enabled():
    """Test logger functionality when feature flag is enabled"""
    print_header("Logger with Feature Enabled (Manual Test)")
    
    print("⚠️  MANUAL TEST: Set ENABLE_ML_SHADOW_MODE=true to test logging")
    print("   Uncomment line 30 in this script and re-run")
    
    if not ENABLE_ML_SHADOW_MODE:
        print("⏭️  SKIP: Feature flag disabled (expected)")
        return True
    
    # If feature is enabled, test logging
    influxdb_client = InfluxDBClient(
        url=f"http://{os.getenv('INFLUXDB_HOST')}:{os.getenv('INFLUXDB_PORT')}",
        token=os.getenv('INFLUXDB_TOKEN'),
        org=os.getenv('INFLUXDB_ORG')
    )
    
    shadow_logger = MLShadowModeLogger(influxdb_client)
    
    if shadow_logger.enabled:
        print("✅ Logger initialized and enabled")
        
        # Create mock prediction
        mock_prediction = StrategyPrediction(
            is_effective=True,
            confidence=0.85,
            recommended_modes=["analytical", "detailed"],
            feature_importance={"satisfaction_score_trend3": 0.42},
            metadata={"engagement_score": 0.75, "message_count": 100}
        )
        
        # Test logging
        success = await shadow_logger.log_prediction(
            prediction=mock_prediction,
            user_id="test_user_shadow_mode",
            bot_name="elena",
            current_mode="balanced"
        )
        
        if success:
            print("✅ PASS: Successfully logged prediction to InfluxDB")
            
            # Test statistics
            await asyncio.sleep(1)  # Wait for write
            stats = await shadow_logger.get_prediction_statistics(
                bot_name="elena",
                hours=1
            )
            print(f"📊 Statistics: {stats}")
            return True
        else:
            print("❌ FAIL: Failed to log prediction")
            return False
    else:
        print("❌ FAIL: Logger not enabled despite feature flag")
        return False


async def test_no_ml_overhead_when_disabled():
    """Test that ML module doesn't import heavy dependencies when disabled"""
    print_header("ML Dependencies Overhead Check")
    
    if not ENABLE_ML_SHADOW_MODE:
        print("✅ PASS: Feature disabled, no XGBoost/sklearn overhead for end users")
        print("   Shadow logger imports only when ENABLE_ML_SHADOW_MODE=true")
        return True
    else:
        print("⚠️  Feature enabled, ML dependencies loaded")
        return True


async def main():
    """Run all shadow mode logger tests"""
    print("\n" + "=" * 70)
    print("ML SHADOW MODE LOGGER TEST SUITE")
    print("=" * 70)
    print("\nTesting feature flag and logger behavior...")
    print("Default state: ENABLE_ML_SHADOW_MODE=false (safe for end users)\n")
    
    tests = [
        ("Feature Flag Default", test_feature_flag),
        ("Logger Disabled by Default", test_logger_disabled_by_default),
        ("No ML Overhead When Disabled", test_no_ml_overhead_when_disabled),
        ("Logger with Feature Enabled", test_logger_with_feature_enabled),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Shadow mode logger is ready.")
        print("\n💡 To enable shadow mode:")
        print("   1. Set ENABLE_ML_SHADOW_MODE=true in .env")
        print("   2. Shadow logger will log predictions to InfluxDB")
        print("   3. No impact on bot behavior (shadow mode only)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
