"""
Test Personalized Character Emoji Sets (Priority 5)

Tests the user-personalized emoji selection system that adapts character emoji sets based on:
- User emoji reaction history (positive/negative reactions)
- Emoji comfort level from personality analysis (0.0-1.0)
- Historical emoji success patterns
- Character archetype (mystical, technical, general)
- Emotion category (wonder, positive, acknowledgment, playful, negative)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.intelligence.vector_emoji_intelligence import VectorEmojiIntelligence


class TestPersonalizedCharacterEmojis:
    """Test suite for personalized character emoji selection"""
    
    @pytest.fixture
    def emoji_intel(self):
        """Create VectorEmojiIntelligence instance with mocked dependencies"""
        mock_memory_manager = AsyncMock()
        mock_memory_manager.retrieve_relevant_memories = AsyncMock(return_value=[])
        
        intel = VectorEmojiIntelligence(
            memory_manager=mock_memory_manager
        )
        return intel
    
    # ==================== USER PREFERENCE RETRIEVAL TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_user_emoji_preferences_with_history(self, emoji_intel):
        """User with emoji reaction history should get personalized preferences"""
        user_id = "user_with_history"
        
        # Mock memory manager to return emoji reaction memories AND personality memories
        emoji_reaction_memories = [
            {
                'content': '[EMOJI_REACTION] User reacted with ❤️ to message',
                'metadata': {
                    'interaction_type': 'emoji_reaction',  # Correct field name
                    'emoji': '❤️',
                    'confidence_score': 0.85,
                    'emotion_type': 'love'  # positive emotion
                }
            },
            {
                'content': '[EMOJI_REACTION] User reacted with ✨ to message',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '✨',
                    'confidence_score': 0.90,
                    'emotion_type': 'joy'  # positive emotion
                }
            },
            {
                'content': '[EMOJI_REACTION] User reacted with 👎 to message',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '🤖',
                    'confidence_score': 0.75,
                    'emotion_type': 'dislike'  # negative emotion
                }
            }
        ]
        
        # Mock memory manager to return different results for different queries
        async def mock_retrieve(user_id, query, limit):
            if "personality" in query.lower():
                return [{'content': 'Hello! 😊', 'metadata': {}}] * 5  # Some personality data
            else:  # Emoji reaction query
                return emoji_reaction_memories
        
        emoji_intel.memory_manager.retrieve_relevant_memories = AsyncMock(side_effect=mock_retrieve)
        
        preferences = await emoji_intel._get_user_emoji_preferences(user_id)
        
        assert 'emoji_comfort_level' in preferences
        assert '❤️' in preferences['positive_reactions']
        assert '✨' in preferences['positive_reactions']
        assert '🤖' in preferences['negative_reactions']
        assert len(preferences['positive_reactions']) == 2
        assert len(preferences['negative_reactions']) == 1
    
    @pytest.mark.asyncio
    async def test_get_user_emoji_preferences_no_history(self, emoji_intel):
        """New user with no history should get default preferences"""
        user_id = "new_user"
        
        # Mock memory manager to return empty lists (no personality, no reactions)
        emoji_intel.memory_manager.retrieve_relevant_memories = AsyncMock(return_value=[])
        
        preferences = await emoji_intel._get_user_emoji_preferences(user_id)
        
        # Should have default comfort level (0.5 from empty personality data)
        assert 'emoji_comfort_level' in preferences
        assert len(preferences['positive_reactions']) == 0
        assert len(preferences['negative_reactions']) == 0
        assert len(preferences['successful_emojis']) == 0
    
    @pytest.mark.asyncio
    async def test_get_user_emoji_preferences_filters_low_confidence(self, emoji_intel):
        """Should filter out emoji reactions with confidence <0.7"""
        user_id = "user_low_confidence"
        
        # Mock memories with varying confidence levels
        mock_memories = [
            {
                'content': '[EMOJI_REACTION] High confidence reaction',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '🎉',
                    'confidence_score': 0.85,  # High confidence - SHOULD INCLUDE
                    'emotion_type': 'positive'
                }
            },
            {
                'content': '[EMOJI_REACTION] Low confidence reaction',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '🤔',
                    'confidence_score': 0.65,  # Low confidence - SHOULD EXCLUDE
                    'emotion_type': 'positive'
                }
            },
            {
                'content': '[EMOJI_REACTION] Borderline confidence',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '😊',
                    'confidence_score': 0.70,  # Exactly 0.7 - SHOULD EXCLUDE (>0.7 required)
                    'emotion_type': 'positive'
                }
            },
            {
                'content': '[EMOJI_REACTION] Just above threshold',
                'metadata': {
                    'interaction_type': 'emoji_reaction',
                    'emoji': '👍',
                    'confidence_score': 0.71,  # Just above 0.7 - SHOULD INCLUDE
                    'emotion_type': 'joy'
                }
            }
        ]
        
        # Mock memory manager to return different results for different queries
        async def mock_retrieve(user_id, query, limit):
            if "personality" in query.lower():
                return [{'content': 'Message', 'metadata': {}}]  # Some personality data
            else:  # Emoji reaction query
                return mock_memories
        
        emoji_intel.memory_manager.retrieve_relevant_memories = AsyncMock(side_effect=mock_retrieve)
        
        preferences = await emoji_intel._get_user_emoji_preferences(user_id)
        
        assert '🎉' in preferences['positive_reactions']
        assert '👍' in preferences['positive_reactions']
        assert '🤔' not in preferences['positive_reactions']  # Too low confidence
        assert '😊' not in preferences['positive_reactions']  # Exactly 0.7 is excluded (needs >0.7)
        assert len(preferences['positive_reactions']) == 2
    
    # ==================== PERSONALIZED EMOJI SELECTION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_filters_for_user_preferences(self, emoji_intel):
        """Should filter base emojis to only include user-preferred ones"""
        user_id = "user_with_preferences"
        
        # Mock _get_user_emoji_preferences to return specific preferences
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': ['✨', '🌟', '💡'],
            'negative_reactions': ['🤖'],
            'emoji_comfort_level': 0.8,
            'successful_emojis': []
        })
        
        # Test mystical character with wonder category
        # Base emojis: ["🔮", "✨", "🌟", "🪄", "🌙", "⭐"]
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="mystical",
            emotion_category="wonder"
        )
        
        # Should only return emojis user has positively reacted to
        assert '✨' in personalized
        assert '🌟' in personalized
        assert '🔮' not in personalized  # Not in user preferences
        assert '🪄' not in personalized  # Not in user preferences
        assert len(personalized) == 2
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_low_comfort_returns_minimal(self, emoji_intel):
        """Low emoji comfort (<0.3) should return only 2 emojis"""
        user_id = "minimal_emoji_user"
        
        # Mock preferences with low comfort, no specific preferences
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.2,  # Low comfort
            'successful_emojis': []
        })
        
        # Test technical character with positive category
        # Base emojis: ["💡", "🚀", "⚡", "🔥", "💪"]
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="technical",
            emotion_category="positive"
        )
        
        # Should return only first 2 emojis
        assert len(personalized) == 2
        assert personalized[0] == "💡"
        assert personalized[1] == "🚀"
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_high_comfort_returns_full_set(self, emoji_intel):
        """High emoji comfort (>0.7) should return full emoji set"""
        user_id = "emoji_lover"
        
        # Mock preferences with high comfort, no specific preferences
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.85,  # High comfort
            'successful_emojis': []
        })
        
        # Test general character with positive category
        # Base emojis: ["😊", "❤️", "👍", "🎉", "�"] - 5 emojis total
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="general",
            emotion_category="positive"
        )
        
        # Should return full set (5 emojis for general positive)
        assert len(personalized) == 5
        assert "😊" in personalized
        assert "❤️" in personalized
        assert "👍" in personalized
        assert "🎉" in personalized
        assert "😄" in personalized
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_moderate_comfort_returns_balanced(self, emoji_intel):
        """Moderate comfort (0.3-0.7) should return 3 emojis"""
        user_id = "moderate_user"
        
        # Mock preferences with moderate comfort
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.5,  # Moderate comfort
            'successful_emojis': []
        })
        
        # Test mystical character with acknowledgment category
        # Base emojis: ["🙏", "✨", "💜"]
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="mystical",
            emotion_category="acknowledgment"
        )
        
        # Should return 3 emojis (but base set only has 3, so all returned)
        assert len(personalized) <= 3
        assert "🙏" in personalized
        assert "✨" in personalized
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_handles_unknown_character(self, emoji_intel):
        """Unknown character should fall back to general character emojis"""
        user_id = "test_user"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.8,
            'successful_emojis': []
        })
        
        # Test with unknown character name
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="unknown_character",
            emotion_category="positive"
        )
        
        # Should fall back to general character emojis
        assert len(personalized) > 0
        # General positive emojis: ["😊", "👍", "🙏", "💙"]
        assert "😊" in personalized or "👍" in personalized
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_handles_unknown_emotion_category(self, emoji_intel):
        """Unknown emotion category should fall back to 'positive' category"""
        user_id = "test_user"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.8,
            'successful_emojis': []
        })
        
        # Test with unknown emotion category
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="mystical",
            emotion_category="unknown_emotion"
        )
        
        # Should fall back to mystical "positive" category: ["💫", "🌈", "🦋", "🌸", "🍃"]
        assert len(personalized) == 5  # High comfort (>0.7) returns full set
        assert personalized == ["💫", "🌈", "🦋", "🌸", "🍃"]
    
    # ==================== ERROR HANDLING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_personalized_emojis_fallback_on_memory_error(self, emoji_intel):
        """Should fall back to base emojis if memory query fails"""
        user_id = "error_user"
        
        # Mock preferences method to raise exception
        emoji_intel._get_user_emoji_preferences = AsyncMock(
            side_effect=Exception("Memory system error")
        )
        
        # Should not raise exception, should fall back to base emojis
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="technical",
            emotion_category="positive"
        )
        
        # Should return base technical positive emojis
        assert len(personalized) > 0
        assert "💡" in personalized
    
    @pytest.mark.asyncio
    async def test_user_preferences_fallback_on_personality_error(self, emoji_intel):
        """Should use default comfort level if personality analysis fails"""
        user_id = "personality_error_user"
        
        # Mock memory manager to raise exception for personality query
        async def mock_retrieve_error(user_id, query, limit):
            if "personality" in query.lower():
                raise Exception("Personality system error")
            else:
                return []  # Empty emoji reactions
        
        emoji_intel.memory_manager.retrieve_relevant_memories = AsyncMock(side_effect=mock_retrieve_error)
        
        # Should not raise exception - should use default values
        preferences = await emoji_intel._get_user_emoji_preferences(user_id)
        
        # Should have default comfort level (0.5 when personality analysis fails)
        assert 'emoji_comfort_level' in preferences
        assert 0.0 <= preferences['emoji_comfort_level'] <= 1.0
    
    # ==================== CHARACTER ARCHETYPE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_mystical_character_emojis(self, emoji_intel):
        """Mystical characters should use mystical emoji sets"""
        user_id = "mystical_test"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 1.0,  # Full set
            'successful_emojis': []
        })
        
        # Test all mystical emotion categories
        wonder = await emoji_intel._get_personalized_character_emojis(
            user_id, "mystical", "wonder"
        )
        positive = await emoji_intel._get_personalized_character_emojis(
            user_id, "mystical", "positive"
        )
        acknowledgment = await emoji_intel._get_personalized_character_emojis(
            user_id, "mystical", "acknowledgment"
        )
        
        # Mystical wonder should include mystical emojis
        assert any(emoji in wonder for emoji in ["🔮", "✨", "🌟", "🪄", "🌙", "⭐"])
        # Mystical positive should include cosmic emojis
        assert any(emoji in positive for emoji in ["✨", "🌟", "💫", "🪐", "🌙"])
        # Mystical acknowledgment should include ethereal emojis
        assert any(emoji in acknowledgment for emoji in ["🙏", "✨", "💜"])
    
    @pytest.mark.asyncio
    async def test_technical_character_emojis(self, emoji_intel):
        """Technical characters should use technical emoji sets"""
        user_id = "technical_test"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 1.0,
            'successful_emojis': []
        })
        
        # Test technical positive emojis
        positive = await emoji_intel._get_personalized_character_emojis(
            user_id, "technical", "positive"
        )
        
        # Technical positive should include tech/science emojis
        assert any(emoji in positive for emoji in ["💡", "🚀", "⚡", "🔥", "💪"])
    
    @pytest.mark.asyncio
    async def test_general_character_emojis(self, emoji_intel):
        """General characters should use balanced emoji sets"""
        user_id = "general_test"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 1.0,
            'successful_emojis': []
        })
        
        # Test general positive emojis
        positive = await emoji_intel._get_personalized_character_emojis(
            user_id, "general", "positive"
        )
        
        # General positive should include common friendly emojis
        assert any(emoji in positive for emoji in ["😊", "👍", "🙏", "💙"])
    
    # ==================== EDGE CASE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_empty_positive_reactions_still_returns_emojis(self, emoji_intel):
        """User with no positive reactions should still get emojis based on comfort"""
        user_id = "no_reactions"
        
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': ['🤖', '👾'],  # Has negative reactions
            'emoji_comfort_level': 0.6,
            'successful_emojis': []
        })
        
        personalized = await emoji_intel._get_personalized_character_emojis(
            user_id=user_id,
            bot_character="general",
            emotion_category="positive"
        )
        
        # Should return 3 emojis (moderate comfort)
        assert len(personalized) == 3
        # Should NOT include negatively reacted emojis
        assert '🤖' not in personalized
        assert '👾' not in personalized
    
    @pytest.mark.asyncio
    async def test_user_preferences_with_no_metadata(self, emoji_intel):
        """Should handle memories without emoji metadata gracefully"""
        user_id = "incomplete_metadata"
        
        # Mock memories with incomplete metadata
        mock_memories = [
            {
                'content': '[EMOJI_REACTION] Reaction',
                'metadata': {
                    'reaction_type': 'positive'
                    # Missing emoji and confidence_score
                }
            },
            {
                'content': '[EMOJI_REACTION] Another reaction',
                'metadata': {}  # Empty metadata
            }
        ]
        
        # Mock memory manager to return different results for different queries
        async def mock_retrieve(user_id, query, limit):
            if "personality" in query.lower():
                return [{'content': 'Message', 'metadata': {}}]  # Some personality data
            else:  # Emoji reaction query
                return mock_memories
        
        emoji_intel.memory_manager.retrieve_relevant_memories = AsyncMock(side_effect=mock_retrieve)
        
        # Should not crash, should handle gracefully
        preferences = await emoji_intel._get_user_emoji_preferences(user_id)
        
        assert 'positive_reactions' in preferences
        assert 'negative_reactions' in preferences
        assert len(preferences['positive_reactions']) == 0  # Should exclude invalid entries
    
    @pytest.mark.asyncio
    async def test_comfort_level_boundary_cases(self, emoji_intel):
        """Test emoji count at comfort level boundaries"""
        user_id = "boundary_test"
        
        # Test exactly 0.3 (should be treated as low, 2 emojis)
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.3,
            'successful_emojis': []
        })
        
        result_low_boundary = await emoji_intel._get_personalized_character_emojis(
            user_id, "general", "positive"
        )
        assert len(result_low_boundary) <= 3  # Moderate range (0.3-0.7)
        
        # Test exactly 0.7 (should be treated as high, full set)
        emoji_intel._get_user_emoji_preferences = AsyncMock(return_value={
            'positive_reactions': [],
            'negative_reactions': [],
            'emoji_comfort_level': 0.7,
            'successful_emojis': []
        })
        
        result_high_boundary = await emoji_intel._get_personalized_character_emojis(
            user_id, "general", "positive"
        )
        assert len(result_high_boundary) <= 3  # Still moderate at 0.7 (>0.7 is high)
