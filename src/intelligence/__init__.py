"""
Unified Emotional Intelligence Module
====================================

Provides unified access to emotional intelligence systems.
Uses Enhanced Vector Emotion Analyzer as the primary system.
"""

import logging

logger = logging.getLogger(__name__)

# Primary emotion analysis system - vector-native
try:
    from .enhanced_vector_emotion_analyzer import (
        EnhancedVectorEmotionAnalyzer, 
        EmotionAnalysisResult,
        create_enhanced_emotion_analyzer
    )
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = True
except ImportError as e:
    logger.error("Enhanced Vector Emotion Analyzer not available: %s", e)
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = False
    EnhancedVectorEmotionAnalyzer = None
    EmotionAnalysisResult = None
    create_enhanced_emotion_analyzer = None

# Simplified emotion manager
try:
    from .simplified_emotion_manager import SimplifiedEmotionManager
    SIMPLIFIED_EMOTION_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.error("Simplified Emotion Manager not available: %s", e)
    SIMPLIFIED_EMOTION_MANAGER_AVAILABLE = False
    SimplifiedEmotionManager = None

if not ENHANCED_EMOTION_ANALYZER_AVAILABLE:
    logger.error("Enhanced Vector Emotion Analyzer not available - primary emotion system disabled")

if not SIMPLIFIED_EMOTION_MANAGER_AVAILABLE:
    logger.error("Simplified Emotion Manager not available - integration layer disabled")

# Export main components
__all__ = [
    "EnhancedVectorEmotionAnalyzer",
    "EmotionAnalysisResult", 
    "create_enhanced_emotion_analyzer",
    "SimplifiedEmotionManager",
    "ENHANCED_EMOTION_ANALYZER_AVAILABLE",
    "SIMPLIFIED_EMOTION_MANAGER_AVAILABLE"
]
