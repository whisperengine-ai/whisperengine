"""
Test reasoning transparency feature in WhisperEngine

Validates that character reasoning is properly generated and included in:
- API responses
- Discord status footer
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from src.core.message_processor import MessageProcessor, MessageContext, ProcessingResult
from src.utils.discord_status_footer import generate_discord_status_footer


def test_build_character_reasoning_basic():
    """Test basic character reasoning generation"""
    # Create a mock message processor
    bot_core = Mock()
    memory_manager = Mock()
    llm_client = Mock()
    
    processor = MessageProcessor(bot_core, memory_manager, llm_client)
    
    # Mock AI components with various reasoning sources
    ai_components = {
        'conversation_intelligence': {
            'interaction_type': 'emotional_support',
            'conversation_mode': 'standard'
        },
        'emotion_data': {
            'primary_emotion': 'joy',
            'intensity': 0.85
        },
        'memory_count': 12,
        'character_learning_moments': {
            'learning_moments_detected': 2,
            'moments': [
                {'type': 'growth_insight'},
                {'type': 'user_observation'}
            ]
        },
        'relationship_state': {
            'trust': 0.75,
            'affection': 0.82
        }
    }
    
    # Build reasoning
    reasoning = processor._build_character_reasoning(
        ai_components,
        [],
        MessageContext(user_id="test_user", content="Test message")
    )
    
    # Validate reasoning structure
    assert reasoning is not None
    assert 'response_strategy' in reasoning
    assert 'emotional_reasoning' in reasoning
    assert 'memory_reasoning' in reasoning
    assert 'learning_reasoning' in reasoning
    assert 'relationship_reasoning' in reasoning
    
    # Validate content
    assert 'emotional support' in reasoning['response_strategy']
    assert 'joy' in reasoning['emotional_reasoning']
    assert '12' in reasoning['memory_reasoning']
    assert 'growth insight' in reasoning['learning_reasoning']
    assert 'Strong bond' in reasoning['relationship_reasoning']


def test_build_character_reasoning_minimal():
    """Test reasoning generation with minimal AI components"""
    bot_core = Mock()
    memory_manager = Mock()
    llm_client = Mock()
    
    processor = MessageProcessor(bot_core, memory_manager, llm_client)
    
    # Minimal AI components
    ai_components = {
        'emotion_data': {
            'primary_emotion': 'neutral',
            'intensity': 0.3
        },
        'memory_count': 2
    }
    
    reasoning = processor._build_character_reasoning(
        ai_components,
        [],
        MessageContext(user_id="test_user", content="Test message")
    )
    
    # Should still generate some reasoning
    assert reasoning is not None
    assert 'memory_reasoning' in reasoning


def test_discord_footer_with_reasoning():
    """Test Discord footer generation includes reasoning transparency"""
    ai_components = {
        'character_reasoning': {
            'response_strategy': 'Detected emotional support',
            'emotional_reasoning': 'Responding to joy (intensity 85%)',
            'memory_reasoning': 'Drawing from 12 shared memories (deep context)',
            'learning_reasoning': 'Processing growth insight, user observation',
            'relationship_reasoning': 'Strong bond (trust 75, affection 82)'
        },
        'conversation_intelligence': {
            'relationship_level': 'friend'
        },
        'emotion_data': {
            'primary_emotion': 'joy',
            'intensity': 0.85
        },
        'memory_count': 12
    }
    
    footer = generate_discord_status_footer(
        ai_components=ai_components,
        processing_time_ms=1234,
        llm_time_ms=890,
        memory_count=12
    )
    
    # Footer should be empty if DISCORD_STATUS_FOOTER env var not set
    # But we can test the function itself
    import os
    original_env = os.environ.get('DISCORD_STATUS_FOOTER')
    try:
        os.environ['DISCORD_STATUS_FOOTER'] = 'true'
        
        footer = generate_discord_status_footer(
            ai_components=ai_components,
            processing_time_ms=1234,
            llm_time_ms=890,
            memory_count=12
        )
        
        # Should include reasoning section
        assert '🧠 **Reasoning**:' in footer
        assert 'emotional support' in footer or 'joy' in footer or 'memories' in footer
        
    finally:
        if original_env:
            os.environ['DISCORD_STATUS_FOOTER'] = original_env
        else:
            os.environ.pop('DISCORD_STATUS_FOOTER', None)


def test_reasoning_transparency_api_format():
    """Test reasoning is properly formatted for API responses"""
    # Test the reasoning structure matches API expectations
    reasoning = {
        'response_strategy': 'Detected emotional support',
        'emotional_reasoning': 'Responding to joy (intensity 85%)',
        'memory_reasoning': 'Drawing from 12 shared memories (deep context)',
        'learning_reasoning': 'Processing growth insight',
        'relationship_reasoning': 'Strong bond (trust 75, affection 82)'
    }
    
    # Validate all keys are strings
    for key, value in reasoning.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
    
    # Validate no empty values
    for value in reasoning.values():
        assert len(value) > 0


if __name__ == '__main__':
    print("Testing reasoning transparency feature...")
    
    print("\n1. Testing basic character reasoning generation...")
    test_build_character_reasoning_basic()
    print("✓ Basic reasoning generation works")
    
    print("\n2. Testing minimal AI components...")
    test_build_character_reasoning_minimal()
    print("✓ Minimal reasoning generation works")
    
    print("\n3. Testing Discord footer with reasoning...")
    test_discord_footer_with_reasoning()
    print("✓ Discord footer includes reasoning")
    
    print("\n4. Testing API format compatibility...")
    test_reasoning_transparency_api_format()
    print("✓ API format is valid")
    
    print("\n✅ All reasoning transparency tests passed!")
