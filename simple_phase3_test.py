#!/usr/bin/env python3
"""Simple Phase 3 component validation without external dependencies."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_phase3_imports():
    """Test that Phase 3 components can be imported."""
    print("🧠 Testing Phase 3 Component Imports...")
    
    try:
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        print("✅ ContextSwitchDetector import successful")
        
        from src.intelligence.empathy_calibrator import EmpathyCalibrator
        print("✅ EmpathyCalibrator import successful")
        
        from src.core.bot import ModularBotManager
        print("✅ ModularBotManager import successful")
        
        from src.handlers.events import EventHandlerManager
        print("✅ EventHandlerManager import successful")
        
        # Test basic initialization
        context_detector = ContextSwitchDetector()
        print("✅ ContextSwitchDetector instantiation successful")
        
        empathy_calibrator = EmpathyCalibrator()  
        print("✅ EmpathyCalibrator instantiation successful")
        
        print("\n🎉 All Phase 3 component imports and instantiations PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Import test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_in_bot_code():
    """Test that Phase 3 components are properly integrated in bot code."""
    print("\n🔧 Testing Phase 3 Integration in Bot Code...")
    
    try:
        # Check if bot.py contains Phase 3 initialization
        with open("src/core/bot.py", "r") as f:
            bot_content = f.read()
            
        if "context_switch_detector" in bot_content:
            print("✅ ContextSwitchDetector found in bot.py")
        else:
            print("❌ ContextSwitchDetector missing from bot.py")
            return False
            
        if "empathy_calibrator" in bot_content:
            print("✅ EmpathyCalibrator found in bot.py")
        else:
            print("❌ EmpathyCalibrator missing from bot.py")
            return False
            
        # Check if events.py contains Phase 3 processing
        with open("src/handlers/events.py", "r") as f:
            events_content = f.read()
            
        if "_analyze_context_switches" in events_content:
            print("✅ _analyze_context_switches method found in events.py")
        else:
            print("❌ _analyze_context_switches method missing from events.py")
            return False
            
        if "_calibrate_empathy_response" in events_content:
            print("✅ _calibrate_empathy_response method found in events.py")
        else:
            print("❌ _calibrate_empathy_response method missing from events.py")
            return False
            
        if "phase3_context_switches" in events_content:
            print("✅ phase3_context_switches parameter found in events.py")
        else:
            print("❌ phase3_context_switches parameter missing from events.py")
            return False
            
        if "phase3_empathy_calibration" in events_content:
            print("✅ phase3_empathy_calibration parameter found in events.py")
        else:
            print("❌ phase3_empathy_calibration parameter missing from events.py")
            return False
            
        print("✅ All Phase 3 integration checks PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    import_success = test_phase3_imports()
    integration_success = test_integration_in_bot_code()
    
    overall_success = import_success and integration_success
    
    print(f"\n{'='*60}")
    print("PHASE 3 INTEGRATION VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Component Imports: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"Code Integration:  {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Overall Result:    {'🎉 SUCCESS' if overall_success else '❌ FAILED'}")
    print(f"{'='*60}")
    
    sys.exit(0 if overall_success else 1)