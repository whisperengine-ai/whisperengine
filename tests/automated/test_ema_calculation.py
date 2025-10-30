"""
Unit tests for EMA (Exponential Moving Average) calculation

Tests the core EMA smoothing functionality used for emotional trajectory analysis.
EMA is used to filter noise from conversations while preserving true emotional trends.
"""
import pytest
import numpy as np
from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector


class TestEMACalculation:
    """Test EMA calculation functionality"""
    
    @pytest.fixture
    def detector(self):
        """Create an AdvancedEmotionDetector instance for testing"""
        return AdvancedEmotionDetector()
    
    def test_ema_cold_start(self, detector):
        """First message: EMA equals raw intensity (no smoothing on first value)"""
        ema = detector._calculate_ema(current=0.75, previous_ema=None)
        assert ema == 0.75, "Cold start EMA should equal raw intensity"
    
    def test_ema_cold_start_zero(self, detector):
        """Cold start with zero intensity"""
        ema = detector._calculate_ema(current=0.0, previous_ema=None)
        assert ema == 0.0
    
    def test_ema_cold_start_one(self, detector):
        """Cold start with maximum intensity"""
        ema = detector._calculate_ema(current=1.0, previous_ema=None)
        assert ema == 1.0
    
    def test_ema_standard_calculation(self, detector):
        """Standard EMA formula: α×I_t + (1-α)×EMA_prev"""
        alpha = 0.3
        current = 0.8
        previous_ema = 0.75
        # Expected: 0.3 × 0.8 + 0.7 × 0.75 = 0.24 + 0.525 = 0.765
        expected = alpha * current + (1 - alpha) * previous_ema
        
        ema = detector._calculate_ema(
            current=current,
            previous_ema=previous_ema,
            alpha=alpha
        )
        
        assert abs(ema - expected) < 0.001, f"EMA calculation incorrect. Got {ema}, expected {expected}"
    
    def test_ema_alpha_light_smoothing(self, detector):
        """Higher alpha (0.4) = less smoothing, closer to current value"""
        ema = detector._calculate_ema(
            current=0.9,
            previous_ema=0.5,
            alpha=0.4
        )
        # Should be: 0.4×0.9 + 0.6×0.5 = 0.36 + 0.3 = 0.66
        expected = 0.66
        assert abs(ema - expected) < 0.001
        
        # Less smoothing means farther from 0.5, closer to 0.9
        assert ema > 0.5 + (0.9 - 0.5) * 0.2, "Light smoothing should favor current"
    
    def test_ema_alpha_heavy_smoothing(self, detector):
        """Lower alpha (0.2) = more smoothing, closer to previous value"""
        ema = detector._calculate_ema(
            current=0.9,
            previous_ema=0.5,
            alpha=0.2
        )
        # Should be: 0.2×0.9 + 0.8×0.5 = 0.18 + 0.4 = 0.58
        expected = 0.58
        assert abs(ema - expected) < 0.001
        
        # Heavy smoothing means closer to 0.5, farther from 0.9
        assert ema < 0.9 - (0.9 - 0.5) * 0.2, "Heavy smoothing should favor previous"
    
    def test_ema_default_alpha(self, detector):
        """Default alpha (0.3) is moderate smoothing"""
        current = 0.7
        previous_ema = 0.6
        # 0.3 × 0.7 + 0.7 × 0.6 = 0.21 + 0.42 = 0.63
        expected = 0.63
        
        ema = detector._calculate_ema(current=current, previous_ema=previous_ema)
        assert abs(ema - expected) < 0.001
    
    def test_ema_clipping_low(self, detector):
        """EMA clips to minimum 0.0"""
        ema = detector._calculate_ema(current=-0.5, previous_ema=0.3)
        assert ema >= 0.0, "EMA should be clipped to [0, 1]"
        assert ema <= 1.0
    
    def test_ema_clipping_high(self, detector):
        """EMA clips to maximum 1.0"""
        ema = detector._calculate_ema(current=1.5, previous_ema=0.8)
        assert ema >= 0.0, "EMA should be clipped to [0, 1]"
        assert ema <= 1.0
    
    def test_ema_clipping_range(self, detector):
        """EMA always stays in [0, 1] range"""
        test_cases = [
            (-1.0, 0.5),   # Negative current
            (2.0, 0.5),    # Over 1.0 current
            (0.5, -0.5),   # Negative previous
            (0.5, 1.5),    # Over 1.0 previous
            (-1.0, -1.0),  # Both negative
            (2.0, 2.0),    # Both over 1.0
        ]
        
        for current, previous_ema in test_cases:
            ema = detector._calculate_ema(current, previous_ema)
            assert 0.0 <= ema <= 1.0, f"EMA out of range for current={current}, previous={previous_ema}"
    
    def test_ema_sequence(self, detector):
        """Multiple messages: EMA smoothing effect compounds over time"""
        intensities = [0.3, 0.9, 0.2, 0.8, 0.7]
        ema_values = []
        current_ema = None
        
        for intensity in intensities:
            current_ema = detector._calculate_ema(
                current=intensity,
                previous_ema=current_ema,
                alpha=0.3
            )
            ema_values.append(current_ema)
        
        # First value should be raw
        assert ema_values[0] == 0.3, "First EMA should equal raw intensity"
        
        # EMA should be smoother than raw (lower variance)
        raw_variance = np.var(intensities)
        ema_variance = np.var(ema_values)
        assert ema_variance < raw_variance, "EMA variance should be less than raw variance"
        
        # All values should be in valid range
        for ema in ema_values:
            assert 0.0 <= ema <= 1.0
    
    def test_ema_converges_to_constant(self, detector):
        """If input becomes constant, EMA converges to that value"""
        alpha = 0.3
        constant_value = 0.6
        
        ema = 0.1  # Start somewhere different
        for _ in range(20):  # Multiple iterations
            ema = detector._calculate_ema(current=constant_value, previous_ema=ema, alpha=alpha)
        
        # Should converge to the constant value
        assert abs(ema - constant_value) < 0.01, f"EMA should converge to {constant_value}, got {ema}"
    
    def test_ema_follows_trend_upward(self, detector):
        """EMA follows upward trend"""
        alpha = 0.3
        upward_trend = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        ema_values = []
        current_ema = None
        
        for intensity in upward_trend:
            current_ema = detector._calculate_ema(
                current=intensity,
                previous_ema=current_ema,
                alpha=alpha
            )
            ema_values.append(current_ema)
        
        # Verify upward trend is preserved
        for i in range(len(ema_values) - 1):
            assert ema_values[i+1] >= ema_values[i], f"Upward trend broken at index {i}"
    
    def test_ema_follows_trend_downward(self, detector):
        """EMA follows downward trend"""
        alpha = 0.3
        downward_trend = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
        ema_values = []
        current_ema = None
        
        for intensity in downward_trend:
            current_ema = detector._calculate_ema(
                current=intensity,
                previous_ema=current_ema,
                alpha=alpha
            )
            ema_values.append(current_ema)
        
        # Verify downward trend is preserved
        for i in range(len(ema_values) - 1):
            assert ema_values[i+1] <= ema_values[i], f"Downward trend broken at index {i}"
    
    def test_ema_noisy_with_filler_messages(self, detector):
        """EMA smooths noisy data (like filler messages in conversation)"""
        # User: "amazing!" (joy=0.9) → "ok" (neutral=0.3) → "so cool!" (joy=0.8) → "lol" (joy=0.7)
        noisy_intensities = [0.9, 0.3, 0.8, 0.7]
        raw_variance = np.var(noisy_intensities)
        
        ema_values = []
        current_ema = None
        for intensity in noisy_intensities:
            current_ema = detector._calculate_ema(
                current=intensity,
                previous_ema=current_ema,
                alpha=0.3
            )
            ema_values.append(current_ema)
        
        ema_variance = np.var(ema_values)
        
        # EMA should smooth the noise
        assert ema_variance < raw_variance, "EMA should reduce variance from noisy data"
        
        # But preserve the general positive trend
        assert ema_values[-1] > 0.5, "EMA should still reflect positive trend"
