"""
ML module for WhisperEngine.

Provides machine learning capabilities for response strategy optimization.
"""

from src.ml.response_strategy_predictor import (
    ResponseStrategyPredictor,
    StrategyPrediction,
    create_response_strategy_predictor
)
from src.ml.shadow_mode_logger import (
    MLShadowModeLogger,
    MLPredictionLog,
    create_ml_shadow_logger,
    ENABLE_ML_SHADOW_MODE
)

__all__ = [
    'ResponseStrategyPredictor',
    'StrategyPrediction',
    'create_response_strategy_predictor',
    'MLShadowModeLogger',
    'MLPredictionLog',
    'create_ml_shadow_logger',
    'ENABLE_ML_SHADOW_MODE'
]
