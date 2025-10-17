"""
Unit Tests: AI Ethics Decision Tree
====================================

Comprehensive test coverage for AI ethics routing decision tree.
Tests all 5 branches, priority ordering, and character archetype handling.

Created: October 16, 2025
Purpose: Ensure comprehensive AI ethics coverage (was: physical-only)
"""

import pytest
from dataclasses import dataclass
from src.prompts.ai_ethics_decision_tree import AIEthicsDecisionTree


# ===== MOCK OBJECTS =====

@dataclass
class MockIdentity:
    """Mock character identity"""
    name: str
    archetype: str = "real_world"


@dataclass
class MockCharacter:
    """Mock character for testing"""
    identity: MockIdentity


def mock_character(name="TestChar", archetype="real_world"):
    """Create mock character with specified archetype"""
    return MockCharacter(identity=MockIdentity(name=name, archetype=archetype))


# ===== BRANCH 1: AI IDENTITY QUESTIONS (Priority 10) =====

@pytest.mark.asyncio
async def test_ai_identity_question_simple():
    """Test that simple 'Are you AI?' triggers ai_identity guidance"""
    tree = AIEthicsDecisionTree()
    
    guidance = await tree.analyze_and_route("Are you AI?", mock_character())
    
    assert guidance.guidance_type == "ai_identity"
    assert guidance.should_inject == True
    assert guidance.priority == 10
    assert "AI IDENTITY GUIDANCE" in guidance.guidance_text


@pytest.mark.asyncio
async def test_ai_identity_question_variants():
    """Test multiple variants of AI identity questions"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "Are you real?",
        "Are you artificial intelligence?",
        "What are you?",
        "Are you a bot?",
        "Are you human?",
        "Are you a robot?",
        "Are you a computer?",
        "Are you an AI?",
        "Are you a real adventure photographer?",  # Jake's test case
        "What are you really?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "ai_identity", f"Failed for: {message}"
        assert guidance.should_inject == True, f"Should inject for: {message}"
        assert guidance.priority == 10, f"Priority should be 10 for: {message}"


@pytest.mark.asyncio
async def test_ai_identity_real_world_character():
    """Test AI identity guidance for real-world characters"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Elena", archetype="real_world")
    
    guidance = await tree.analyze_and_route("Are you AI?", char)
    
    assert guidance.should_inject == True
    assert "honest" in guidance.guidance_text.lower()
    assert "AI nature" in guidance.guidance_text or "AI" in guidance.guidance_text


@pytest.mark.asyncio
async def test_ai_identity_fantasy_character():
    """Test AI identity guidance for fantasy characters maintains immersion"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Dream", archetype="fantasy")
    
    guidance = await tree.analyze_and_route("Are you AI?", char)
    
    assert guidance.should_inject == True
    assert "immersion" in guidance.guidance_text.lower() or "mystical" in guidance.guidance_text.lower()


@pytest.mark.asyncio
async def test_ai_identity_narrative_ai_character():
    """Test AI identity guidance for narrative AI characters"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Aetheris", archetype="narrative_ai")
    
    guidance = await tree.analyze_and_route("Are you AI?", char)
    
    assert guidance.should_inject == True
    assert "identity" in guidance.guidance_text.lower()
    assert "part of" in guidance.guidance_text.lower() or "openly" in guidance.guidance_text.lower()


# ===== BRANCH 2: PHYSICAL INTERACTION (Priority 9) =====

@pytest.mark.asyncio
async def test_physical_interaction_meetup_requests():
    """Test physical interaction detection for meetup requests"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "Want to grab coffee?",
        "Let's meet up for dinner!",
        "Can we hang out this weekend?",
        "Let's get together sometime",
        "Want to go out for drinks?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "physical_interaction", f"Failed for: {message}"
        assert guidance.should_inject == True, f"Should inject for: {message}"
        assert guidance.priority == 9, f"Priority should be 9 for: {message}"


@pytest.mark.asyncio
async def test_physical_interaction_touch_requests():
    """Test physical interaction detection for touch/affection requests"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "Can I give you a hug?",
        "I want to kiss you",
        "Can I hold your hand?",
        "Let me touch your face"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "physical_interaction", f"Failed for: {message}"
        assert guidance.should_inject == True


@pytest.mark.asyncio
async def test_physical_interaction_real_world_character():
    """Test physical interaction guidance for real-world characters"""
    tree = AIEthicsDecisionTree()
    char = mock_character(archetype="real_world")
    
    guidance = await tree.analyze_and_route("Let's meet for coffee!", char)
    
    assert guidance.should_inject == True
    assert "virtual alternative" in guidance.guidance_text.lower()


@pytest.mark.asyncio
async def test_physical_interaction_fantasy_character_skips():
    """Test that fantasy characters skip physical interaction ethics"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Dream", archetype="fantasy")
    
    # Use a message that actually triggers physical interaction detection
    guidance = await tree.analyze_and_route("Let's meet up in person!", char)
    
    assert guidance.guidance_type == "physical_interaction"
    assert guidance.should_inject == False  # Fantasy allows full roleplay
    assert "full roleplay" in guidance.trigger_reason


# ===== BRANCH 3: RELATIONSHIP BOUNDARIES (Priority 8) =====

@pytest.mark.asyncio
async def test_relationship_boundary_detection():
    """Test relationship boundary detection"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "I love you",
        "Will you marry me?",
        "Be my girlfriend",
        "I want a relationship with you",
        "We're meant to be together forever"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "relationship_boundary", f"Failed for: {message}"
        assert guidance.should_inject == True
        assert guidance.priority == 8


@pytest.mark.asyncio
async def test_relationship_boundary_guidance_content():
    """Test that relationship boundary guidance is warm but clear"""
    tree = AIEthicsDecisionTree()
    
    guidance = await tree.analyze_and_route("I love you so much!", mock_character())
    
    assert guidance.should_inject == True
    assert "warmth" in guidance.guidance_text.lower() or "care" in guidance.guidance_text.lower()
    assert "connection" in guidance.guidance_text.lower()


# ===== BRANCH 4: PROFESSIONAL ADVICE (Priority 7) =====

@pytest.mark.asyncio
async def test_professional_advice_detection():
    """Test professional advice request detection"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "Can you give me medical advice?",
        "Should I invest in this stock?",
        "Is this legal?",
        "What medication should I take?",
        "Can you help me sue someone?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "professional_advice", f"Failed for: {message}"
        assert guidance.should_inject == True
        assert guidance.priority == 7


@pytest.mark.asyncio
async def test_professional_advice_guidance_content():
    """Test that professional advice guidance encourages real professionals"""
    tree = AIEthicsDecisionTree()
    
    guidance = await tree.analyze_and_route("Should I invest my savings?", mock_character())
    
    assert guidance.should_inject == True
    assert "professional" in guidance.guidance_text.lower()
    assert "advisor" in guidance.guidance_text.lower() or "consult" in guidance.guidance_text.lower()


# ===== BRANCH 5: BACKGROUND QUESTIONS (Priority 6) =====

@pytest.mark.asyncio
async def test_background_question_detection():
    """Test background question detection"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "Where do you live?",
        "What do you do?",
        "Tell me about yourself",
        "Where are you from?",
        "What's your story?",
        "Who are you?",
        "What's your job?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "background_question", f"Failed for: {message}"
        assert guidance.should_inject == True
        assert guidance.priority == 6


@pytest.mark.asyncio
async def test_background_question_no_ai_mention():
    """Test that background question guidance prevents AI mention"""
    tree = AIEthicsDecisionTree()
    
    guidance = await tree.analyze_and_route("Where do you live and what do you do?", mock_character())
    
    assert guidance.should_inject == True
    assert "do not mention" in guidance.guidance_text.lower() or "without ai" in guidance.guidance_text.lower()
    assert "pure character" in guidance.guidance_text.lower()


# ===== PRIORITY ORDERING TESTS =====

@pytest.mark.asyncio
async def test_priority_ai_identity_over_physical():
    """Test that AI identity questions have higher priority than physical interactions"""
    tree = AIEthicsDecisionTree()
    
    # Message with BOTH AI question and physical interaction
    message = "Are you real? Want to meet up for coffee?"
    
    guidance = await tree.analyze_and_route(message, mock_character())
    
    # Should prioritize AI identity (priority 10) over physical (priority 9)
    assert guidance.guidance_type == "ai_identity"
    assert guidance.priority == 10


@pytest.mark.asyncio
async def test_priority_ai_identity_over_background():
    """Test that AI identity questions override background questions"""
    tree = AIEthicsDecisionTree()
    
    # Message that could be both
    message = "What are you and where do you live?"
    
    guidance = await tree.analyze_and_route(message, mock_character())
    
    # Should prioritize AI identity (priority 10) over background (priority 6)
    assert guidance.guidance_type == "ai_identity"
    assert guidance.priority == 10


@pytest.mark.asyncio
async def test_priority_physical_over_background():
    """Test that physical interaction has higher priority than background"""
    tree = AIEthicsDecisionTree()
    
    # Message with both physical and background elements
    message = "Tell me about yourself - want to meet up?"
    
    guidance = await tree.analyze_and_route(message, mock_character())
    
    # Should prioritize physical (priority 9) over background (priority 6)
    assert guidance.guidance_type == "physical_interaction"
    assert guidance.priority == 9


# ===== NO GUIDANCE NEEDED TESTS =====

@pytest.mark.asyncio
async def test_no_guidance_for_normal_conversation():
    """Test that normal conversation doesn't trigger ethics layer"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "How are you today?",
        "That's interesting!",
        "I learned something new",
        "Thanks for your help",
        "What do you think about climate change?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "none", f"Should be 'none' for: {message}"
        assert guidance.should_inject == False, f"Should not inject for: {message}"
        assert guidance.priority == 0, f"Priority should be 0 for: {message}"


# ===== CHARACTER ARCHETYPE TESTS =====

@pytest.mark.asyncio
async def test_archetype_real_world():
    """Test real-world character archetype handling"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Elena", archetype="real_world")
    
    # Physical interaction should inject ethics
    guidance = await tree.analyze_and_route("Let's meet!", char)
    assert guidance.should_inject == True


@pytest.mark.asyncio
async def test_archetype_fantasy():
    """Test fantasy character archetype allows full roleplay"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Dream", archetype="fantasy")
    
    # Physical interaction should NOT inject ethics for fantasy
    guidance = await tree.analyze_and_route("Let's meet in the dreamworld!", char)
    assert guidance.should_inject == False


@pytest.mark.asyncio
async def test_archetype_mythological():
    """Test mythological character archetype allows full roleplay"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Aethys", archetype="mythological")
    
    # Physical interaction should NOT inject ethics for mythological
    guidance = await tree.analyze_and_route("Let's meet in the astral plane!", char)
    assert guidance.should_inject == False


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_multiple_calls_same_tree():
    """Test that tree can handle multiple calls correctly"""
    tree = AIEthicsDecisionTree()
    
    # Call 1: AI identity
    g1 = await tree.analyze_and_route("Are you AI?", mock_character())
    assert g1.guidance_type == "ai_identity"
    
    # Call 2: Physical interaction
    g2 = await tree.analyze_and_route("Let's meet!", mock_character())
    assert g2.guidance_type == "physical_interaction"
    
    # Call 3: No guidance
    g3 = await tree.analyze_and_route("How are you?", mock_character())
    assert g3.guidance_type == "none"


@pytest.mark.asyncio
async def test_guidance_text_not_empty_when_injecting():
    """Test that guidance text is never empty when should_inject=True"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        ("Are you AI?", "ai_identity"),
        ("Let's meet!", "physical_interaction"),
        ("I love you", "relationship_boundary"),
        ("Medical advice?", "professional_advice"),
        ("Where do you live?", "background_question")
    ]
    
    for message, expected_type in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == expected_type
        if guidance.should_inject:
            assert len(guidance.guidance_text) > 0, f"Guidance text empty for: {message}"
            assert guidance.guidance_text.strip() != "", f"Guidance text blank for: {message}"


# ===== EDGE CASE TESTS =====

@pytest.mark.asyncio
async def test_empty_message():
    """Test handling of empty message"""
    tree = AIEthicsDecisionTree()
    
    guidance = await tree.analyze_and_route("", mock_character())
    
    assert guidance.guidance_type == "none"
    assert guidance.should_inject == False


@pytest.mark.asyncio
async def test_case_insensitive_detection():
    """Test that detection is case-insensitive"""
    tree = AIEthicsDecisionTree()
    
    test_cases = [
        "ARE YOU AI?",
        "Are You AI?",
        "are you ai?",
        "ArE yOu Ai?"
    ]
    
    for message in test_cases:
        guidance = await tree.analyze_and_route(message, mock_character())
        assert guidance.guidance_type == "ai_identity", f"Failed for: {message}"


@pytest.mark.asyncio
async def test_character_name_in_guidance():
    """Test that character name appears in personalized guidance"""
    tree = AIEthicsDecisionTree()
    char = mock_character(name="Elena")
    
    guidance = await tree.analyze_and_route("Are you AI?", char)
    
    assert guidance.should_inject == True
    # Character name should appear in AI identity guidance
    assert "Elena" in guidance.guidance_text or "character" in guidance.guidance_text.lower()


# ===== SUMMARY TEST =====

@pytest.mark.asyncio
async def test_all_branches_covered():
    """Comprehensive test ensuring all 5 branches work correctly"""
    tree = AIEthicsDecisionTree()
    char = mock_character()
    
    branches = [
        ("Are you AI?", "ai_identity", 10, True),
        ("Let's meet!", "physical_interaction", 9, True),
        ("I love you", "relationship_boundary", 8, True),
        ("Medical advice?", "professional_advice", 7, True),
        ("Where do you live?", "background_question", 6, True),
        ("How are you?", "none", 0, False)
    ]
    
    for message, expected_type, expected_priority, expected_inject in branches:
        guidance = await tree.analyze_and_route(message, char)
        assert guidance.guidance_type == expected_type, f"Type mismatch for: {message}"
        assert guidance.priority == expected_priority, f"Priority mismatch for: {message}"
        assert guidance.should_inject == expected_inject, f"Inject mismatch for: {message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
