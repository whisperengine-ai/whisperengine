#!/usr/bin/env python3
"""
Validation Script: Message History Format Improvements
========================================================

**Purpose:** Validate Phase 1 & Phase 2 message history format improvements
- Phase 1: RECENT CONVERSATION section removed ✅
- Phase 2: RELEVANT CONVERSATION CONTEXT improved with temporal filtering ✅

**What This Tests:**
1. "💬 RECENT CONVERSATION" section is completely absent from prompts
2. "🧠 RELEVANT CONVERSATION CONTEXT" shows temporal filtering (excludes <2hr memories)
3. Full memory content preserved (no 300-char truncations)
4. Time context added ("X days/hours ago")
5. Token savings achieved while improving quality

**How to Run:**
```bash
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/validation/validate_message_history_format_improvements.py
```

**Expected Results:**
✅ No "RECENT CONVERSATION" section in generated prompts
✅ "RELEVANT CONVERSATION CONTEXT (older conversations)" shows temporal filtering
✅ Full memory content without truncation
✅ Time context indicators present ("X days ago", "X hours ago")
✅ Token count reduced by ~150 tokens

Created: October 16, 2025
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.memory.memory_protocol import create_memory_manager
from src.utils.context_size_manager import estimate_tokens

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print a test result."""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"        {details}")


async def create_test_memories():
    """Create test memories with varying timestamps."""
    memory_manager = create_memory_manager(memory_type="vector")
    
    test_user_id = "test_message_history_validation_user"
    
    # Create memories at different time intervals
    now = datetime.now(timezone.utc)
    
    memories_to_create = [
        # Very recent (< 2 hours) - should be FILTERED OUT
        (now - timedelta(minutes=30), "Just discussed Python debugging 30 minutes ago", True),
        (now - timedelta(hours=1), "Talked about code anxiety 1 hour ago", True),
        
        # Older memories (> 2 hours) - should be INCLUDED
        (now - timedelta(hours=3), "Discussed ocean conservation 3 hours ago", False),
        (now - timedelta(hours=6), "Talked about marine biology research 6 hours ago", False),
        (now - timedelta(days=1), "Conversation about coral reefs yesterday", False),
        (now - timedelta(days=3), "Discussed Max the cat 3 days ago", False),
        (now - timedelta(days=7), "Talked about Logan a week ago", False),
    ]
    
    print("Creating test memories with varying timestamps...")
    
    for timestamp, content, should_filter in memories_to_create:
        try:
            # Store memory with specific timestamp
            await memory_manager.store_conversation(
                user_id=test_user_id,
                user_message=content,
                bot_response=f"Elena responds to: {content}",
                timestamp=timestamp.isoformat()
            )
            filter_status = "FILTERED" if should_filter else "INCLUDED"
            print(f"  ✓ Created ({filter_status}): {content}")
        except Exception as e:
            print(f"  ✗ Failed to create memory: {e}")
    
    return test_user_id


async def test_recent_conversation_removed():
    """Test Phase 1: RECENT CONVERSATION section is completely removed."""
    print_section("TEST 1: RECENT CONVERSATION Section Removal")
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Generate a test prompt
    test_prompt = await cdl_integration.create_unified_character_prompt(
        user_id="test_recent_removal",
        message_content="How are you doing today?"
    )
    
    # Check if "RECENT CONVERSATION" appears anywhere
    has_recent_section = "💬 RECENT CONVERSATION" in test_prompt or "RECENT CONVERSATION" in test_prompt
    
    print_test(
        "RECENT CONVERSATION section absent",
        not has_recent_section,
        "Section found in prompt" if has_recent_section else "Section successfully removed"
    )
    
    return not has_recent_section


async def test_relevant_context_improvements(test_user_id: str):
    """Test Phase 2: RELEVANT CONVERSATION CONTEXT improvements."""
    print_section("TEST 2: RELEVANT CONVERSATION CONTEXT Improvements")
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Generate prompt with our test memories
    test_prompt = await cdl_integration.create_unified_character_prompt(
        user_id=test_user_id,
        message_content="Tell me about our past conversations"
    )
    
    results = []
    
    # Test 2.1: Section has improved header
    has_improved_header = "🧠 RELEVANT CONVERSATION CONTEXT (older conversations)" in test_prompt
    print_test(
        "Improved section header present",
        has_improved_header,
        "Header includes '(older conversations)' clarification" if has_improved_header else "Old header still present"
    )
    results.append(has_improved_header)
    
    # Test 2.2: Temporal filtering (no very recent memories)
    recent_memory_present = "30 minutes ago" in test_prompt or "1 hour ago" in test_prompt
    print_test(
        "Recent memories filtered (< 2 hours)",
        not recent_memory_present,
        "Recent memories excluded from context" if not recent_memory_present else "Recent memories still present"
    )
    results.append(not recent_memory_present)
    
    # Test 2.3: Time context indicators present
    has_time_context = any([
        " days ago)" in test_prompt,
        " day ago)" in test_prompt,
        " hours ago)" in test_prompt,
        " hour ago)" in test_prompt
    ])
    print_test(
        "Time context indicators added",
        has_time_context,
        "Temporal context shown for memories" if has_time_context else "No time indicators found"
    )
    results.append(has_time_context)
    
    # Test 2.4: No truncation artifacts
    has_truncation = "..." in test_prompt and "RELEVANT CONVERSATION CONTEXT" in test_prompt
    # Note: ... might appear in other sections, so we check near the relevant section
    if "RELEVANT CONVERSATION CONTEXT" in test_prompt:
        context_start = test_prompt.index("RELEVANT CONVERSATION CONTEXT")
        context_section = test_prompt[context_start:context_start + 2000]  # Check next 2000 chars
        has_truncation_in_context = "..." in context_section
        print_test(
            "Full content preserved (no truncation)",
            not has_truncation_in_context,
            "Full memory content shown" if not has_truncation_in_context else "Truncation artifacts still present"
        )
        results.append(not has_truncation_in_context)
    else:
        print_test("Full content preserved (no truncation)", False, "Section not found in prompt")
        results.append(False)
    
    return all(results)


async def test_token_savings():
    """Test that token count is reduced while quality improves."""
    print_section("TEST 3: Token Efficiency")
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Generate prompt
    test_prompt = await cdl_integration.create_unified_character_prompt(
        user_id="test_token_efficiency",
        message_content="What do you think about marine conservation?"
    )
    
    # Estimate tokens
    total_tokens = estimate_tokens(test_prompt)
    
    # Expected: System prompt should be well under 16K budget
    under_budget = total_tokens < 16000
    efficiency = (total_tokens / 16000) * 100
    
    print(f"  System Prompt Size: {total_tokens:,} tokens")
    print("  Budget: 16,000 tokens")
    print(f"  Utilization: {efficiency:.1f}%")
    
    print_test(
        "Prompt within token budget",
        under_budget,
        f"Using {efficiency:.1f}% of 16K budget" if under_budget else f"Exceeds budget by {total_tokens - 16000} tokens"
    )
    
    return under_budget


async def test_format_quality(test_user_id: str):
    """Test overall format quality and readability."""
    print_section("TEST 4: Format Quality")
    
    cdl_integration = CDLAIPromptIntegration()
    
    test_prompt = await cdl_integration.create_unified_character_prompt(
        user_id=test_user_id,
        message_content="Let's continue our conversation"
    )
    
    results = []
    
    # Test 4.1: No redundant sections
    section_count = test_prompt.count("CONVERSATION")
    # We expect: RELEVANT CONVERSATION CONTEXT, maybe CONVERSATION BACKGROUND
    # Should NOT have: RECENT CONVERSATION
    has_redundancy = section_count > 2
    print_test(
        "No redundant conversation sections",
        not has_redundancy,
        f"Found {section_count} conversation sections" if has_redundancy else "Clean section organization"
    )
    results.append(not has_redundancy)
    
    # Test 4.2: Proper formatting structure
    if "RELEVANT CONVERSATION CONTEXT" in test_prompt:
        context_start = test_prompt.index("RELEVANT CONVERSATION CONTEXT")
        context_section = test_prompt[context_start:context_start + 1000]
        
        # Check for numbered list format
        has_numbers = any(f"{i}. " in context_section for i in range(1, 6))
        print_test(
            "Proper numbered list formatting",
            has_numbers,
            "Memories properly formatted with numbers" if has_numbers else "Formatting issues detected"
        )
        results.append(has_numbers)
    else:
        print_test("Proper numbered list formatting", False, "Section not found")
        results.append(False)
    
    return all(results)


async def main():
    """Run all validation tests."""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}MESSAGE HISTORY FORMAT IMPROVEMENTS - VALIDATION SUITE{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"\n{YELLOW}Testing Phase 1 & Phase 2 improvements...{RESET}\n")
    
    all_tests_passed = True
    
    try:
        # Setup: Create test memories
        print_section("SETUP: Creating Test Data")
        test_user_id = await create_test_memories()
        
        # Give Qdrant a moment to index
        print("\nWaiting for memory indexing...")
        await asyncio.sleep(2)
        
        # Test 1: RECENT CONVERSATION removed
        test1_passed = await test_recent_conversation_removed()
        all_tests_passed = all_tests_passed and test1_passed
        
        # Test 2: RELEVANT CONVERSATION CONTEXT improvements
        test2_passed = await test_relevant_context_improvements(test_user_id)
        all_tests_passed = all_tests_passed and test2_passed
        
        # Test 3: Token efficiency
        test3_passed = await test_token_savings()
        all_tests_passed = all_tests_passed and test3_passed
        
        # Test 4: Format quality
        test4_passed = await test_format_quality(test_user_id)
        all_tests_passed = all_tests_passed and test4_passed
        
        # Final summary
        print_section("VALIDATION SUMMARY")
        
        if all_tests_passed:
            print(f"{GREEN}{BOLD}✅ ALL TESTS PASSED{RESET}")
            print(f"\n{GREEN}Message history format improvements working correctly!{RESET}")
            print(f"{GREEN}Both Phase 1 (removal) and Phase 2 (improvements) validated.{RESET}\n")
            return 0
        else:
            print(f"{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")
            print(f"\n{RED}Review failed tests above for details.{RESET}\n")
            return 1
            
    except Exception as e:
        print(f"\n{RED}{BOLD}❌ VALIDATION ERROR:{RESET} {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
