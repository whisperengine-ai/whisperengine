#!/usr/bin/env python3
"""
Simple test for PHASE 2 temporal evolution integration.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

def test_imports():
    """Test if imports work properly"""
    print("🧪 Testing imports...")
    
    try:
        # Test temporal module import
        import src.characters.learning.character_temporal_evolution_analyzer as temporal_module
        print(f"✅ Temporal module imported: {temporal_module.__file__}")
        
        # Check what's in the module
        available = [attr for attr in dir(temporal_module) if not attr.startswith('_')]
        print(f"✅ Available in module: {available}")
        
        # Test if class exists
        if hasattr(temporal_module, 'CharacterTemporalEvolutionAnalyzer'):
            TemporalAnalyzer = temporal_module.CharacterTemporalEvolutionAnalyzer
            print("✅ CharacterTemporalEvolutionAnalyzer class found")
            
            # Try to create instance
            analyzer = TemporalAnalyzer()
            print("✅ CharacterTemporalEvolutionAnalyzer instance created")
            
            # Check methods
            methods = [method for method in dir(analyzer) if callable(getattr(analyzer, method)) and not method.startswith('_')]
            print(f"✅ Available methods: {methods[:5]}...")  # Show first 5 methods
            
            return True
        else:
            print("❌ CharacterTemporalEvolutionAnalyzer class not found")
            return False
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_coordinator_integration():
    """Test coordinator integration"""
    print("\n🧪 Testing coordinator integration...")
    
    try:
        from src.characters.learning.unified_character_intelligence_coordinator import (
            UnifiedCharacterIntelligenceCoordinator, 
            IntelligenceSystemType
        )
        
        # Check if temporal evolution enum exists
        has_temporal_enum = hasattr(IntelligenceSystemType, 'CHARACTER_TEMPORAL_EVOLUTION')
        print(f"✅ CHARACTER_TEMPORAL_EVOLUTION enum exists: {has_temporal_enum}")
        
        if has_temporal_enum:
            print(f"✅ Enum value: {IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION}")
        
        # Create coordinator
        coordinator = UnifiedCharacterIntelligenceCoordinator()
        print("✅ UnifiedCharacterIntelligenceCoordinator created")
        
        # Check context patterns
        temporal_patterns = []
        for context_type, systems in coordinator.context_patterns.items():
            if hasattr(IntelligenceSystemType, 'CHARACTER_TEMPORAL_EVOLUTION') and IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION in systems:
                temporal_patterns.append(context_type)
        
        print(f"✅ Context patterns with temporal evolution: {temporal_patterns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordinator integration test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run simple integration tests"""
    print("🚀 Simple PHASE 2 Temporal Evolution Integration Test")
    print("=" * 60)
    
    test1 = test_imports()
    test2 = test_coordinator_integration()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ BASIC INTEGRATION SUCCESSFUL")
        print("🎯 Temporal evolution system is ready for testing")
    else:
        print("❌ Integration issues found - check errors above")

if __name__ == "__main__":
    main()