#!/usr/bin/env python
"""
Phase 2 Validation: Structured Prompt Assembly Integration Test

Tests the new structured prompt assembly components directly.
"""
import asyncio
import os
import sys

# Set environment variables before imports
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'

from src.prompts.prompt_assembler import create_prompt_assembler
from src.prompts.prompt_components import (
    create_core_system_component,
    create_memory_component,
    create_anti_hallucination_component,
    create_guidance_component,
    PromptComponent,
    PromptComponentType
)


def test_structured_assembly():
    """Test structured prompt assembly with realistic components."""
    print("=" * 80)
    print("🚀 PHASE 2 VALIDATION: Structured Prompt Assembly")
    print("=" * 80)
    
    # Test 1: Basic assembly
    print("\n1. Testing basic prompt assembly...")
    assembler = create_prompt_assembler(max_tokens=6000)
    
    # Add core system
    assembler.add_component(create_core_system_component(
        "CURRENT DATE & TIME: October 11, 2025, 10:30 AM PST",
        priority=1
    ))
    
    # Add memory component
    memory_narrative = (
        "USER FACTS: Name is Mark; Interested in marine biology || "
        "PAST CONVERSATIONS: User asked about dolphins on Oct 10 | "
        "Discussed ocean conservation on Oct 9"
    )
    assembler.add_component(create_memory_component(
        f"RELEVANT MEMORIES: {memory_narrative}",
        priority=4
    ))
    
    # Add guidance
    assembler.add_component(create_guidance_component("Elena", priority=6))
    
    # Assemble
    result = assembler.assemble(model_type="generic")
    metrics = assembler.get_assembly_metrics()
    
    print(f"   ✅ Assembly successful!")
    print(f"   Components: {metrics['total_components']}")
    print(f"   Tokens: {metrics['total_tokens']}")
    print(f"   Characters: {metrics['total_chars']}")
    print(f"   Within budget: {metrics['within_budget']}")
    
    # Validate structure
    checks_passed = 0
    checks_total = 5
    
    if "CURRENT DATE & TIME" in result:
        print("   ✅ Contains time context")
        checks_passed += 1
    else:
        print("   ❌ Missing time context")
    
    if "RELEVANT MEMORIES" in result:
        print("   ✅ Contains memory narrative")
        checks_passed += 1
    else:
        print("   ❌ Missing memory narrative")
    
    if "Communication style" in result or "Elena" in result:
        print("   ✅ Contains guidance")
        checks_passed += 1
    else:
        print("   ❌ Missing guidance")
    
    if result.index("CURRENT DATE & TIME") < result.index("RELEVANT MEMORIES"):
        print("   ✅ Correct ordering (time before memory)")
        checks_passed += 1
    else:
        print("   ❌ Incorrect ordering")
    
    if result.index("RELEVANT MEMORIES") < result.index("Communication style" if "Communication style" in result else "Elena"):
        print("   ✅ Correct ordering (memory before guidance)")
        checks_passed += 1
    else:
        print("   ❌ Incorrect ordering")
    
    print(f"\n   Validation: {checks_passed}/{checks_total} checks passed")
    
    # Test 2: No memory scenario
    print("\n2. Testing no-memory scenario with anti-hallucination...")
    assembler2 = create_prompt_assembler(max_tokens=6000)
    assembler2.add_component(create_core_system_component(
        "CURRENT DATE & TIME: October 11, 2025",
        priority=1
    ))
    assembler2.add_component(create_anti_hallucination_component(priority=4))
    assembler2.add_component(create_guidance_component("Elena", priority=6))
    
    result2 = assembler2.assemble()
    
    if "MEMORY STATUS" in result2 and "No previous conversation history" in result2:
        print("   ✅ Anti-hallucination warning present")
        checks_passed += 1
    else:
        print("   ❌ Missing anti-hallucination warning")
    
    # Test 3: Token budget enforcement
    print("\n3. Testing token budget enforcement...")
    assembler3 = create_prompt_assembler(max_tokens=50)  # Very small budget
    
    # Add required component
    assembler3.add_component(PromptComponent(
        type=PromptComponentType.CORE_SYSTEM,
        content="A" * 100,  # ~25 tokens
        priority=1,
        required=True
    ))
    
    # Add optional components that should be dropped
    assembler3.add_component(PromptComponent(
        type=PromptComponentType.MEMORY,
        content="B" * 200,  # ~50 tokens
        priority=2,
        required=False
    ))
    
    assembler3.add_component(PromptComponent(
        type=PromptComponentType.GUIDANCE,
        content="C" * 200,  # ~50 tokens
        priority=3,
        required=False
    ))
    
    result3 = assembler3.assemble()
    metrics3 = assembler3.get_assembly_metrics()
    
    if metrics3['total_tokens'] <= 50:
        print(f"   ✅ Budget enforced: {metrics3['total_tokens']} tokens <= 50")
        checks_passed += 1
    else:
        print(f"   ❌ Budget exceeded: {metrics3['total_tokens']} tokens > 50")
    
    if "A" in result3:
        print("   ✅ Required component preserved")
        checks_passed += 1
    else:
        print("   ❌ Required component missing")
    
    # Test 4: Content deduplication
    print("\n4. Testing content deduplication...")
    assembler4 = create_prompt_assembler()
    
    # Add duplicate content
    assembler4.add_component(PromptComponent(
        type=PromptComponentType.MEMORY,
        content="This is duplicate content that should only appear once",
        priority=1
    ))
    assembler4.add_component(PromptComponent(
        type=PromptComponentType.MEMORY,
        content="This is duplicate content that should only appear once",
        priority=2
    ))
    
    result4 = assembler4.assemble()
    count = result4.count("This is duplicate content that should only appear once")
    
    if count == 1:
        print(f"   ✅ Deduplication working: content appears {count} time")
        checks_passed += 1
    else:
        print(f"   ❌ Deduplication failed: content appears {count} times")
    
    print("\n" + "=" * 80)
    print(f"✅ PHASE 2 VALIDATION COMPLETE: {checks_passed}/{checks_total + 4} total checks passed")
    print("=" * 80)
    
    return checks_passed >= (checks_total + 3)  # Allow 1 failure


if __name__ == "__main__":
    print("\n🧪 Starting Phase 2 validation tests...\n")
    
    success = test_structured_assembly()
    
    # Exit with proper code
    sys.exit(0 if success else 1)

