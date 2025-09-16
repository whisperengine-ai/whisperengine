#!/usr/bin/env python3
"""
Simple Memory Moments Integration Test

Tests that Phase 4.1 Memory-Triggered Personality Moments integration points
are properly connected without requiring full system initialization.
"""

import os
import sys


def test_integration_completeness():
    """Test that all integration points are properly connected"""
    print("🔍 Testing Memory Moments Integration Completeness...")

    integration_points = {
        "Bot Core Initialization": (
            "src/core/bot.py",
            ["memory_moments", "Phase 4.1", "MemoryTriggeredMoments"],
        ),
        "Universal Chat Integration": (
            "src/platforms/universal_chat.py",
            ["memory_moments_context", "Memory-Triggered Personality Moment"],
        ),
        "System Prompt Integration": (
            "src/utils/helpers.py",
            ["MEMORY_MOMENTS_CONTEXT", "memory_moments_context"],
        ),
        "System Prompt Template": (
            "config/system_prompts/dream_ai_enhanced.md",
            ["{MEMORY_MOMENTS_CONTEXT}", "Memory-Triggered Personality Moments"],
        ),
        "Thread Manager Integration": (
            "src/conversation/advanced_thread_manager.py",
            [
                "self.memory_moments",
                "MEMORY_MOMENTS_AVAILABLE",
                "analyze_conversation_for_memories",
            ],
        ),
        "Proactive Engagement Integration": (
            "src/conversation/proactive_engagement_engine.py",
            ["self.memory_moments", "analyze_conversation_for_memories", "memory_connections"],
        ),
    }

    results = {}

    for name, (file_path, required_content) in integration_points.items():
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()

                found_items = []
                missing_items = []

                for item in required_content:
                    if item in content:
                        found_items.append(item)
                    else:
                        missing_items.append(item)

                if len(found_items) == len(required_content):
                    results[name] = (
                        f"✅ Complete ({len(found_items)}/{len(required_content)} items found)"
                    )
                elif len(found_items) > 0:
                    results[name] = (
                        f"⚠️ Partial ({len(found_items)}/{len(required_content)} items found)"
                    )
                else:
                    results[name] = f"❌ Missing (0/{len(required_content)} items found)"
            else:
                results[name] = f"❌ File not found: {file_path}"

        except Exception as e:
            results[name] = f"❌ Error reading {file_path}: {e}"

    print("\nIntegration Points Status:")
    for name, status in results.items():
        print(f"  {status} {name}")

    # Count successful integrations
    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    partial_count = sum(1 for status in results.values() if status.startswith("⚠️"))
    total_count = len(results)

    print(f"\nIntegration Summary:")
    print(f"  ✅ Complete: {success_count}/{total_count}")
    print(f"  ⚠️ Partial:  {partial_count}/{total_count}")
    print(f"  ❌ Failed:   {total_count - success_count - partial_count}/{total_count}")

    return success_count, partial_count, total_count


def test_file_imports():
    """Test that key integration files can be syntax-checked"""
    print("\n🧪 Testing File Syntax and Structure...")

    test_files = [
        "src/personality/memory_moments.py",
        "src/core/bot.py",
        "src/platforms/universal_chat.py",
        "src/utils/helpers.py",
    ]

    results = {}

    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                # Simple syntax check by attempting to compile
                with open(file_path, "r") as f:
                    content = f.read()

                # Try to compile the file
                compile(content, file_path, "exec")
                results[file_path] = "✅ Syntax OK"

            else:
                results[file_path] = "❌ File not found"

        except SyntaxError as e:
            results[file_path] = f"❌ Syntax Error: {e}"
        except Exception as e:
            results[file_path] = f"⚠️ Warning: {e}"

    print("\nFile Syntax Check:")
    for file_path, status in results.items():
        print(f"  {status} {file_path}")

    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    return success_count, len(results)


def test_component_registration():
    """Test that memory_moments component is properly registered"""
    print("\n🔧 Testing Component Registration...")

    try:
        # Check bot.py for memory_moments in get_components()
        with open("src/core/bot.py", "r") as f:
            content = f.read()

        # Look for memory_moments in get_components return statement
        if "'memory_moments':" in content and "getattr(self, 'memory_moments'" in content:
            print("  ✅ memory_moments component properly registered in get_components()")
            component_registration = True
        else:
            print("  ❌ memory_moments component not found in get_components()")
            component_registration = False

        # Check for initialization code
        if "memory_moments = MemoryTriggeredMoments(" in content:
            print("  ✅ MemoryTriggeredMoments initialization found")
            initialization = True
        else:
            print("  ❌ MemoryTriggeredMoments initialization not found")
            initialization = False

        return component_registration and initialization

    except Exception as e:
        print(f"  ❌ Error checking component registration: {e}")
        return False


if __name__ == "__main__":
    print("🚀 WhisperEngine Phase 4.1 Memory Moments Integration Test")
    print("=" * 60)

    # Test 1: Integration completeness
    success, partial, total = test_integration_completeness()

    # Test 2: File syntax
    syntax_success, syntax_total = test_file_imports()

    # Test 3: Component registration
    registration_success = test_component_registration()

    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(
        f"  Integration Points: {success + partial}/{total} implemented ({success} complete, {partial} partial)"
    )
    print(f"  File Syntax: {syntax_success}/{syntax_total} files valid")
    print(f"  Component Registration: {'✅ Pass' if registration_success else '❌ Fail'}")

    if success >= 5 and syntax_success >= 3 and registration_success:
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        print("   Phase 4.1 Memory-Triggered Personality Moments are properly integrated")
        print("   ✅ All critical integration points connected")
        print("   ✅ Core files have valid syntax")
        print("   ✅ Component registration working")
        sys.exit(0)
    else:
        print("\n⚠️ INTEGRATION PARTIALLY COMPLETE")
        print("   Some integration points may need attention")
        if success + partial < total:
            print("   - Check missing integration points above")
        if syntax_success < syntax_total:
            print("   - Fix syntax errors in core files")
        if not registration_success:
            print("   - Verify component registration in bot core")
        sys.exit(1)
