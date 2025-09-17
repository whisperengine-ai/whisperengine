#!/usr/bin/env python3
"""
Quick test to verify WhisperEngine startup works
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test all critical imports"""
    try:
        print("🔧 Testing imports...")
        
        # Test environment loading
        from env_manager import load_environment
        print("✅ env_manager import OK")
        
        # Test logging
        from src.utils.logging_config import setup_logging
        print("✅ logging_config import OK")
        
        # Test onboarding
        from src.utils.onboarding_manager import ensure_onboarding_complete
        print("✅ onboarding_manager import OK")
        
        # Test main
        from src.main import sync_main
        print("✅ main import OK")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_environment():
    """Test environment loading"""
    try:
        print("🔧 Testing environment loading...")
        from env_manager import load_environment
        
        result = load_environment()
        if result:
            print("✅ Environment loaded successfully")
            
            # Check key environment variables
            discord_token = os.getenv('DISCORD_BOT_TOKEN', 'Not set')
            llm_url = os.getenv('LLM_CHAT_API_URL', 'Not set')
            
            print(f"📝 Discord token: {'Set' if discord_token != 'Not set' else 'Not set'}")
            print(f"📝 LLM URL: {llm_url}")
            
            return True
        else:
            print("❌ Environment loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_onboarding():
    """Test onboarding detection"""
    try:
        print("🔧 Testing onboarding detection...")
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector()
        is_first_run = detector.is_first_run()
        
        print(f"📝 Is first run: {is_first_run}")
        print(f"📝 Project root: {detector.project_root}")
        print(f"📝 Setup marker: {detector.setup_markers_file}")
        print(f"📝 Setup marker exists: {detector.setup_markers_file.exists()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Onboarding test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WhisperEngine Startup Test")
    print("=" * 40)
    
    all_good = True
    
    # Run tests
    all_good &= test_imports()
    print()
    all_good &= test_environment()
    print()
    all_good &= test_onboarding()
    print()
    
    if all_good:
        print("✅ All tests passed! Your WhisperEngine should start properly.")
        print("💡 Try running: python run.py")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("=" * 40)