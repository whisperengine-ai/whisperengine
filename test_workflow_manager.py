"""
Test Workflow Manager
======================

Simple test to verify workflow YAML loading and intent detection.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.roleplay.workflow_manager import WorkflowManager
from src.roleplay.transaction_manager import TransactionManager


async def test_workflow_loading():
    """Test loading workflow YAML file"""
    print("\n" + "="*60)
    print("TEST 1: Workflow YAML Loading")
    print("="*60)
    
    # Create mock components (no actual DB/LLM needed for loading test)
    workflow_manager = WorkflowManager(
        transaction_manager=None,  # Mock
        llm_client=None  # Mock
    )
    
    # Load Dotty workflows
    workflow_file = "characters/workflows/dotty_bartender.yaml"
    
    print(f"\n📂 Loading workflow file: {workflow_file}")
    
    try:
        # Manually load workflow file (bypass CDL loading for testing)
        await workflow_manager._load_workflow_file(workflow_file, "dotty")
        
        # Check if loaded
        if workflow_manager.is_loaded("dotty"):
            workflow_count = workflow_manager.get_workflow_count("dotty")
            print(f"✅ SUCCESS: Loaded {workflow_count} workflows for Dotty")
            
            # Print workflow names
            workflow_file_obj = workflow_manager.loaded_workflows["dotty"]
            print(f"\n📋 Workflows loaded:")
            for wf_name in workflow_file_obj.workflows.keys():
                print(f"   - {wf_name}")
            
            return True
        else:
            print("❌ FAILED: Workflows not loaded")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pattern_matching():
    """Test pattern matching for drink orders"""
    print("\n" + "="*60)
    print("TEST 2: Pattern Matching")
    print("="*60)
    
    # Create workflow manager
    workflow_manager = WorkflowManager(
        transaction_manager=None,  # Mock
        llm_client=None  # Mock
    )
    
    # Load Dotty workflows
    await workflow_manager._load_workflow_file("characters/workflows/dotty_bartender.yaml", "dotty")
    
    # Test messages
    test_cases = [
        ("I'll have a whiskey", True, "Standard drink order"),
        ("Give me a beer", True, "Direct drink request"),
        ("Can I get some wine?", True, "Polite drink request"),
        ("Make me something tropical", True, "Custom drink request"),
        ("What do you recommend?", True, "Recommendation request"),
        ("Hello there!", False, "Non-drink message"),
        ("How are you?", False, "Casual greeting"),
    ]
    
    print("\n🧪 Testing pattern matching:")
    
    passed = 0
    failed = 0
    
    for message, should_match, description in test_cases:
        workflow_file = workflow_manager.loaded_workflows["dotty"]
        
        # Check each workflow
        matched = False
        for wf_name, wf_def in workflow_file.workflows.items():
            result = await workflow_manager._check_workflow_trigger(
                wf_name, wf_def, workflow_file, message, "test_user", "dotty"
            )
            if result:
                matched = True
                match_info = f"{wf_name} (confidence: {result.match_confidence:.2f})"
                break
        
        status = "✅" if matched == should_match else "❌"
        result_str = f"Matched: {match_info}" if matched else "No match"
        
        print(f"\n{status} {description}")
        print(f"   Message: \"{message}\"")
        print(f"   Expected: {'Match' if should_match else 'No match'}")
        print(f"   Result: {result_str}")
        
        if matched == should_match:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Pattern Matching Results: {passed} passed, {failed} failed")
    return failed == 0


async def test_context_extraction():
    """Test context extraction from messages"""
    print("\n" + "="*60)
    print("TEST 3: Context Extraction")
    print("="*60)
    
    # Create workflow manager
    workflow_manager = WorkflowManager(
        transaction_manager=None,
        llm_client=None
    )
    
    # Load Dotty workflows
    await workflow_manager._load_workflow_file("characters/workflows/dotty_bartender.yaml", "dotty")
    
    workflow_file = workflow_manager.loaded_workflows["dotty"]
    drink_order_workflow = workflow_file.workflows["drink_order"]
    
    # Test context extraction
    test_cases = [
        ("I'll have a whiskey", {"drink_name": "whiskey", "price": 5}),
        ("Give me a beer", {"drink_name": "beer", "price": 4}),
        ("Can I get some wine?", {"drink_name": "wine", "price": 6}),
    ]
    
    print("\n🧪 Testing context extraction:")
    
    passed = 0
    failed = 0
    
    for message, expected_context in test_cases:
        # Find pattern match
        import re
        patterns = drink_order_workflow.get("triggers", {}).get("patterns", [])
        pattern_match = None
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                pattern_match = match
                break
        
        if not pattern_match:
            print(f"\n❌ No pattern match for: \"{message}\"")
            failed += 1
            continue
        
        # Extract context
        extracted = await workflow_manager._extract_context(
            drink_order_workflow, workflow_file, message, pattern_match
        )
        
        # Check if extracted context matches expected
        match = all(
            extracted.get(k) == v 
            for k, v in expected_context.items()
        )
        
        status = "✅" if match else "❌"
        print(f"\n{status} Message: \"{message}\"")
        print(f"   Expected: {expected_context}")
        print(f"   Extracted: {extracted}")
        
        if match:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Context Extraction Results: {passed} passed, {failed} failed")
    return failed == 0


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 WORKFLOW MANAGER TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Loading
    results.append(await test_workflow_loading())
    
    # Test 2: Pattern matching
    results.append(await test_pattern_matching())
    
    # Test 3: Context extraction
    results.append(await test_context_extraction())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
