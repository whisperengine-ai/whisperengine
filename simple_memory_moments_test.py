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
                with open(file_path) as f:
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

    for name, _status in results.items():
        pass

    # Count successful integrations
    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    partial_count = sum(1 for status in results.values() if status.startswith("⚠️"))
    total_count = len(results)

    return success_count, partial_count, total_count


def test_file_imports():
    """Test that key integration files can be syntax-checked"""

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
                with open(file_path) as f:
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

    for file_path, _status in results.items():
        pass

    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    return success_count, len(results)


def test_component_registration():
    """Test that memory_moments component is properly registered"""

    try:
        # Check bot.py for memory_moments in get_components()
        with open("src/core/bot.py") as f:
            content = f.read()

        # Look for memory_moments in get_components return statement
        if "'memory_moments':" in content and "getattr(self, 'memory_moments'" in content:
            component_registration = True
        else:
            component_registration = False

        # Check for initialization code
        if "memory_moments = MemoryTriggeredMoments(" in content:
            initialization = True
        else:
            initialization = False

        return component_registration and initialization

    except Exception:
        return False


if __name__ == "__main__":

    # Test 1: Integration completeness
    success, partial, total = test_integration_completeness()

    # Test 2: File syntax
    syntax_success, syntax_total = test_file_imports()

    # Test 3: Component registration
    registration_success = test_component_registration()

    if success >= 5 and syntax_success >= 3 and registration_success:
        sys.exit(0)
    else:
        if success + partial < total:
            pass
        if syntax_success < syntax_total:
            pass
        if not registration_success:
            pass
        sys.exit(1)
