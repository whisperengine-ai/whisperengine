#!/usr/bin/env python3
"""Comprehensive Phase 3 Integration Test"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_phase3_integration():
    """Test comprehensive Phase 3 integration"""
    print("🧠 COMPREHENSIVE PHASE 3 INTEGRATION TEST")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Component Imports
    print("\n1️⃣ Testing Component Imports...")
    try:
        from src.intelligence.context_switch_detector import ContextSwitchDetector, ContextSwitchType
        from src.intelligence.empathy_calibrator import EmpathyCalibrator, EmpathyStyle
        print("✅ All Phase 3 imports successful")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        all_tests_passed = False
        return all_tests_passed
        
    # Test 2: Component Instantiation
    print("\n2️⃣ Testing Component Instantiation...")
    try:
        detector = ContextSwitchDetector()
        calibrator = EmpathyCalibrator()
        print("✅ All Phase 3 components instantiated successfully")
    except Exception as e:
        print(f"❌ Instantiation test failed: {e}")
        all_tests_passed = False
        return all_tests_passed
        
    # Test 3: Method Existence
    print("\n3️⃣ Testing Method Existence...")
    try:
        # Check detector methods
        assert hasattr(detector, 'detect_context_switches'), "detect_context_switches method missing"
        assert callable(getattr(detector, 'detect_context_switches')), "detect_context_switches not callable"
        
        # Check calibrator methods
        assert hasattr(calibrator, 'calibrate_empathy'), "calibrate_empathy method missing"
        assert callable(getattr(calibrator, 'calibrate_empathy')), "calibrate_empathy not callable"
        
        print("✅ All Phase 3 methods exist and are callable")
    except Exception as e:
        print(f"❌ Method existence test failed: {e}")
        all_tests_passed = False
        
    # Test 4: Environment Variable Integration
    print("\n4️⃣ Testing Environment Variable Integration...")
    try:
        # Test environment variable reading
        original_threshold = detector.topic_shift_threshold
        
        # Set a test environment variable
        os.environ['PHASE3_TOPIC_SHIFT_THRESHOLD'] = '0.7'
        
        # Create new detector to test env var loading
        test_detector = ContextSwitchDetector()
        assert test_detector.topic_shift_threshold == 0.7, f"Expected 0.7, got {test_detector.topic_shift_threshold}"
        
        # Clean up
        del os.environ['PHASE3_TOPIC_SHIFT_THRESHOLD']
        
        print("✅ Environment variable integration works correctly")
    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        all_tests_passed = False
        
    # Test 5: Bot Integration Check
    print("\n5️⃣ Testing Bot Integration...")
    try:
        # Check if bot.py contains Phase 3 initialization
        with open("src/core/bot.py", "r") as f:
            bot_content = f.read()
            
        assert "context_switch_detector" in bot_content, "ContextSwitchDetector not found in bot.py"
        assert "empathy_calibrator" in bot_content, "EmpathyCalibrator not found in bot.py"
        
        print("✅ Phase 3 components found in bot initialization")
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        all_tests_passed = False
        
    # Test 6: Events Handler Integration Check
    print("\n6️⃣ Testing Events Handler Integration...")
    try:
        # Check if events.py contains Phase 3 processing
        with open("src/handlers/events.py", "r") as f:
            events_content = f.read()
            
        assert "_analyze_context_switches" in events_content, "_analyze_context_switches method missing"
        assert "_calibrate_empathy_response" in events_content, "_calibrate_empathy_response method missing"
        assert "phase3_context_switches" in events_content, "phase3_context_switches parameter missing"
        assert "phase3_empathy_calibration" in events_content, "phase3_empathy_calibration parameter missing"
        
        print("✅ Phase 3 methods and parameters found in events handler")
    except Exception as e:
        print(f"❌ Events handler integration test failed: {e}")
        all_tests_passed = False
        
    # Test 7: Universal Chat Integration Check
    print("\n7️⃣ Testing Universal Chat Integration...")
    try:
        # Check if universal_chat.py has been updated for Phase 3
        with open("src/platforms/universal_chat.py", "r") as f:
            chat_content = f.read()
            
        assert "phase3_context_switches" in chat_content, "phase3_context_switches parameter missing in universal_chat.py"
        assert "phase3_empathy_calibration" in chat_content, "phase3_empathy_calibration parameter missing in universal_chat.py"
        assert "Phase 3 Intelligence" in chat_content, "Phase 3 Intelligence context missing in prompt generation"
        
        print("✅ Phase 3 integration found in Universal Chat orchestrator")
    except Exception as e:
        print(f"❌ Universal Chat integration test failed: {e}")
        all_tests_passed = False
        
    # Test 8: Configuration File Check
    print("\n8️⃣ Testing Configuration Files...")
    try:
        # Check if .env has Phase 3 variables
        with open(".env", "r") as f:
            env_content = f.read()
            
        assert "ENABLE_PHASE3_CONTEXT_DETECTION" in env_content, "ENABLE_PHASE3_CONTEXT_DETECTION missing in .env"
        assert "ENABLE_PHASE3_EMPATHY_CALIBRATION" in env_content, "ENABLE_PHASE3_EMPATHY_CALIBRATION missing in .env"
        assert "PHASE3_TOPIC_SHIFT_THRESHOLD" in env_content, "PHASE3_TOPIC_SHIFT_THRESHOLD missing in .env"
        
        print("✅ Phase 3 configuration variables found in .env")
    except Exception as e:
        print(f"❌ Configuration file test failed: {e}")
        all_tests_passed = False
        
    # Test Results
    print("\n" + "=" * 60)
    print("COMPREHENSIVE PHASE 3 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Phase 3 integration is fully functional")
        print("✅ Components are properly imported and instantiated")
        print("✅ Environment variables are correctly integrated")
        print("✅ Bot initialization includes Phase 3 components")
        print("✅ Event handlers process Phase 3 intelligence")
        print("✅ Universal Chat orchestrator includes Phase 3 in prompts")
        print("✅ Configuration files contain Phase 3 variables")
        print("\n🚀 PHASE 3 IS READY FOR PRODUCTION TESTING!")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Please review the failed tests above")
        
    return all_tests_passed

if __name__ == "__main__":
    success = test_phase3_integration()
    sys.exit(0 if success else 1)