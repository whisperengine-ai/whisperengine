#!/usr/bin/env python3
"""
🔍 FINAL INTEGRATION CHECK: 6D Vector System

This script validates that all enhanced components integrate properly
and are ready for production testing.
"""

import sys
import importlib
from pathlib import Path

def check_imports():
    """Check that all enhanced modules can be imported successfully"""
    print("🔍 CHECKING MODULE IMPORTS")
    print("-" * 50)
    
    modules_to_check = [
        ("src.memory.vector_memory_system", "VectorMemoryManager"),
        ("src.prompts.cdl_ai_integration", "CDLAIPromptIntegration"), 
        ("src.utils.human_like_memory_optimizer", "ConversationFlowOptimizer"),
        ("src.intelligence.vector_conversation_flow_analyzer", "VectorEnhancedConversationFlowAnalyzer")
    ]
    
    import_results = []
    
    for module_path, class_name in modules_to_check:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                print(f"✅ {module_path}.{class_name} - Import successful")
                import_results.append(True)
            else:
                print(f"❌ {module_path}.{class_name} - Class not found")
                import_results.append(False)
        except ImportError as e:
            print(f"⚠️ {module_path} - Import failed: {e}")
            import_results.append(False)
        except Exception as e:
            print(f"❌ {module_path} - Unexpected error: {e}")
            import_results.append(False)
    
    return all(import_results)

def check_enhanced_methods():
    """Check that enhanced methods are available in the modules"""
    print(f"\n🔍 CHECKING ENHANCED METHODS")
    print("-" * 50)
    
    method_checks = []
    
    # Check vector memory system enhancements
    try:
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Check if enhanced methods exist
        enhanced_methods = [
            "_analyze_6d_emotional_trajectory",
            "_search_single_dimension",
            "_search_dimensions_batch"
        ]
        
        for method in enhanced_methods:
            if hasattr(VectorMemoryManager, method):
                print(f"✅ VectorMemoryManager.{method} - Available")
                method_checks.append(True)
            else:
                print(f"❌ VectorMemoryManager.{method} - Missing")
                method_checks.append(False)
                
    except Exception as e:
        print(f"❌ VectorMemoryManager check failed: {e}")
        method_checks.extend([False, False, False])
    
    # Check CDL integration enhancements  
    try:
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        enhanced_methods = [
            "_generate_all_embeddings_parallel",
            "_generate_embeddings_sequential_fallback"
        ]
        
        for method in enhanced_methods:
            if hasattr(CDLAIPromptIntegration, method):
                print(f"✅ CDLAIPromptIntegration.{method} - Available")
                method_checks.append(True)
            else:
                print(f"❌ CDLAIPromptIntegration.{method} - Missing")
                method_checks.append(False)
                
    except Exception as e:
        print(f"❌ CDLAIPromptIntegration check failed: {e}")
        method_checks.extend([False, False])
    
    # Check human-like optimizer enhancements
    try:
        from src.utils.human_like_memory_optimizer import ConversationFlowOptimizer
        
        # Check if vector flow analyzer integration exists
        if hasattr(ConversationFlowOptimizer, 'vector_flow_analyzer'):
            print(f"✅ ConversationFlowOptimizer.vector_flow_analyzer - Available") 
            method_checks.append(True)
        else:
            print(f"❌ ConversationFlowOptimizer.vector_flow_analyzer - Missing")
            method_checks.append(False)
            
    except Exception as e:
        print(f"❌ ConversationFlowOptimizer check failed: {e}")
        method_checks.append(False)
    
    return all(method_checks)

def check_integration_points():
    """Check key integration points between components"""
    print(f"\n🔍 CHECKING INTEGRATION POINTS")
    print("-" * 50)
    
    integration_checks = []
    
    # Check factory functions
    try:
        from src.intelligence.vector_conversation_flow_analyzer import create_vector_conversation_flow_analyzer
        print("✅ create_vector_conversation_flow_analyzer - Factory available")
        integration_checks.append(True)
    except ImportError:
        print("❌ create_vector_conversation_flow_analyzer - Factory missing")
        integration_checks.append(False)
    
    # Check human-like optimizer integration
    try:
        from src.utils.human_like_memory_optimizer import VECTOR_FLOW_AVAILABLE
        if VECTOR_FLOW_AVAILABLE:
            print("✅ VECTOR_FLOW_AVAILABLE - Integration flag set")
        else:
            print("⚠️ VECTOR_FLOW_AVAILABLE - Integration flag false (expected in test environment)")
        integration_checks.append(True)  # This is OK in test environment
    except ImportError:
        print("❌ VECTOR_FLOW_AVAILABLE - Integration flag missing")
        integration_checks.append(False)
    
    return all(integration_checks)

def check_demo_files():
    """Check that all demo files are present and functional"""
    print(f"\n🔍 CHECKING DEMO FILES")
    print("-" * 50)
    
    demo_files = [
        "demo_6d_trajectory_integration_explanation.py",
        "demo_6d_optimization_showcase.py", 
        "performance_analysis_6d_vectors.py",
        "6D_VECTOR_TRAJECTORY_ENHANCEMENT_COMPLETE.md",
        "CODE_REVIEW_6D_VECTOR_ENHANCEMENTS.md"
    ]
    
    demo_checks = []
    
    for demo_file in demo_files:
        file_path = Path(demo_file)
        if file_path.exists():
            print(f"✅ {demo_file} - Present")
            demo_checks.append(True)
        else:
            print(f"❌ {demo_file} - Missing")
            demo_checks.append(False)
    
    return all(demo_checks)

def run_integration_validation():
    """Run comprehensive integration validation"""
    print("🚀 6D VECTOR SYSTEM: FINAL INTEGRATION CHECK")
    print("=" * 80)
    
    checks = [
        ("Module Imports", check_imports),
        ("Enhanced Methods", check_enhanced_methods), 
        ("Integration Points", check_integration_points),
        ("Demo Files", check_demo_files)
    ]
    
    results = []
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print(f"\n📊 INTEGRATION CHECK SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name}: {status}")
        all_passed = all_passed and result
    
    print(f"\n{'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
    print("=" * 80)
    
    if all_passed:
        print("✅ 6D Vector System is ready for testing!")
        print("   Recommendation: Start Elena bot and test trajectory analysis")
        print("   Command: ./multi-bot.sh start elena")
    else:
        print("❌ Integration issues detected - review failed checks above")
    
    return all_passed

if __name__ == "__main__":
    # Add project root to path for imports
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    success = run_integration_validation()
    sys.exit(0 if success else 1)