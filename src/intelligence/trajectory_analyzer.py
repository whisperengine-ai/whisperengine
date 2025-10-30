"""
Emotional Trajectory Analysis System

Extracts emotional trends from stored EMA values in Qdrant memory.
Enables characters to understand and reference user's emotional arc over time.

Example:
    User: "Hi"
    Bot: "You seem calm today" ← knows trajectory is stable/low

    User: [frustrated message]
    Bot: "I've noticed you getting more frustrated lately..." ← knows trajectory is rising

Architecture:
    retrieve_trajectory() → extract_trajectory_vector() → generate_trajectory_description()
    
    Data Flow:
    1. Query Qdrant for last N emotional states (EMA values from payloads)
    2. Extract trend direction/magnitude as vector
    3. Compute statistics (mean, variance, acceleration)
    4. Generate natural language descriptions
    5. Return context for prompt injection
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

from src.memory.memory_protocol import create_memory_manager
from src.memory.vector_memory_system import VectorMemoryManager


logger = logging.getLogger(__name__)


class TrajectoryTrend(Enum):
    """Classification of emotional trajectory direction and magnitude."""
    STABLE_LOW = "stable_low"          # Consistent low emotion
    STABLE_NEUTRAL = "stable_neutral"  # Consistent neutral emotion
    STABLE_HIGH = "stable_high"        # Consistent high emotion
    RISING_STEADY = "rising_steady"    # Gradual increase
    RISING_SHARP = "rising_sharp"      # Rapid increase
    FALLING_STEADY = "falling_steady"  # Gradual decrease
    FALLING_SHARP = "falling_sharp"    # Rapid decrease
    VOLATILE = "volatile"              # High variance, no clear trend
    UNKNOWN = "unknown"                # Insufficient data


@dataclass
class TrajectoryPoint:
    """Single emotional state in trajectory."""
    timestamp: datetime
    ema_value: float
    raw_value: Optional[float] = None
    emotion_type: Optional[str] = None  # e.g., "joy", "frustration", "anxiety"


@dataclass
class TrajectoryVector:
    """Quantified emotional trajectory."""
    trend: TrajectoryTrend
    direction: float           # -1.0 (falling) to 1.0 (rising)
    magnitude: float           # 0.0 (stable) to 1.0 (extreme change)
    acceleration: float        # Rate of change acceleration
    mean_intensity: float      # Average emotional intensity
    variance: float            # Emotional stability (0=stable, 1=volatile)
    points_count: int          # Number of data points used
    time_span: timedelta       # Duration covered by trajectory


class TrajectoryAnalyzer:
    """
    Analyzes emotional trajectories from stored EMA values.
    
    Core Operations:
    1. extract_trajectory() - Retrieve emotional history from Qdrant
    2. compute_trajectory_vector() - Quantify trend as vector
    3. generate_trajectory_summary() - Natural language description
    """
    
    def __init__(self, memory_manager: Optional[VectorMemoryManager] = None):
        """
        Initialize trajectory analyzer.
        
        Args:
            memory_manager: VectorMemoryManager instance (will create if None)
        """
        self.memory_manager = memory_manager or create_memory_manager(memory_type="vector")
        self.logger = logger
    
    async def extract_trajectory(
        self,
        user_id: str,
        lookback_messages: int = 10,
        min_span_minutes: int = 5
    ) -> List[TrajectoryPoint]:
        """
        Extract emotional trajectory from Qdrant memory.
        
        Retrieves recent emotional states (EMA values) for a user and returns
        ordered list of trajectory points with timestamps and values.
        
        Args:
            user_id: User identifier
            lookback_messages: Number of recent messages to analyze (default: 10)
            min_span_minutes: Minimum time span required for analysis
        
        Returns:
            List of TrajectoryPoint objects ordered by timestamp
            Empty list if insufficient data
        
        Example:
            >>> analyzer = TrajectoryAnalyzer()
            >>> trajectory = await analyzer.extract_trajectory("user_123", lookback_messages=20)
            >>> print(f"Found {len(trajectory)} emotional states")
            >>> print(f"Trend: {trajectory[-1].ema_value:.2f} (latest)")
        """
        try:
            # Query memory for recent emotional states
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotion emotional feeling intensity",
                limit=lookback_messages
            )
            
            if not recent_memories or len(recent_memories) == 0:
                self.logger.debug(f"No emotional memories for user {user_id}")
                return []
            
            # Extract trajectory points from payloads
            trajectory_points = []
            for memory in recent_memories:
                payload = memory.get('payload', {})
                
                # Extract timestamp
                timestamp_str = payload.get('timestamp')
                if not timestamp_str:
                    continue
                
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    continue
                
                # Extract EMA value (or fall back to raw intensity)
                ema_value = payload.get('emotional_intensity_ema')
                if ema_value is None:
                    ema_value = payload.get('emotional_intensity')
                
                if ema_value is None:
                    continue
                
                ema_value = float(ema_value)
                raw_value = payload.get('emotional_intensity_raw')
                if raw_value is not None:
                    raw_value = float(raw_value)
                
                emotion_type = payload.get('emotion_type')
                
                point = TrajectoryPoint(
                    timestamp=timestamp,
                    ema_value=ema_value,
                    raw_value=raw_value,
                    emotion_type=emotion_type
                )
                trajectory_points.append(point)
            
            # Sort by timestamp (oldest first)
            trajectory_points.sort(key=lambda p: p.timestamp)
            
            # Validate minimum span
            if len(trajectory_points) >= 2:
                time_span = trajectory_points[-1].timestamp - trajectory_points[0].timestamp
                if time_span < timedelta(minutes=min_span_minutes):
                    self.logger.debug(
                        f"Trajectory span {time_span} too short for user {user_id}"
                    )
                    return trajectory_points  # Return anyway, analyzer will handle
            
            self.logger.debug(
                f"Extracted {len(trajectory_points)} trajectory points for {user_id}"
            )
            return trajectory_points
            
        except Exception as e:
            self.logger.warning(
                f"Failed to extract trajectory for {user_id}: {e}"
            )
            return []
    
    def compute_trajectory_vector(
        self,
        trajectory_points: List[TrajectoryPoint]
    ) -> TrajectoryVector:
        """
        Compute quantified emotional trajectory vector from points.
        
        Analyzes the emotional arc and produces a TrajectoryVector with:
        - Trend classification (rising, falling, stable, volatile)
        - Direction: -1.0 (falling) to 1.0 (rising)
        - Magnitude: 0.0 (stable) to 1.0 (extreme)
        - Acceleration: Rate of change
        - Statistics: mean, variance
        
        Args:
            trajectory_points: List of TrajectoryPoint objects
        
        Returns:
            TrajectoryVector with quantified trend information
        
        Example:
            >>> vector = analyzer.compute_trajectory_vector(trajectory_points)
            >>> print(f"Trend: {vector.trend.value}")
            >>> print(f"Direction: {vector.direction:.2f} (negative=falling)")
            >>> print(f"Magnitude: {vector.magnitude:.2f}")
        """
        if not trajectory_points:
            return TrajectoryVector(
                trend=TrajectoryTrend.UNKNOWN,
                direction=0.0,
                magnitude=0.0,
                acceleration=0.0,
                mean_intensity=0.0,
                variance=0.0,
                points_count=0,
                time_span=timedelta(0)
            )
        
        # Extract EMA values
        ema_values = np.array([p.ema_value for p in trajectory_points])
        
        # Calculate statistics
        mean_intensity = float(np.mean(ema_values))
        variance = float(np.var(ema_values))
        
        # Calculate direction (slope)
        if len(ema_values) >= 2:
            # Simple linear regression for direction
            x = np.arange(len(ema_values), dtype=float)
            coefficients = np.polyfit(x, ema_values, 1)
            slope = coefficients[0]
            
            # Normalize slope to [-1, 1] range
            max_possible_slope = 1.0 / max(1.0, len(ema_values) - 1)
            direction = np.clip(slope / max_possible_slope, -1.0, 1.0)
        else:
            direction = 0.0
        
        # Calculate magnitude (total change)
        if len(ema_values) >= 2:
            total_change = abs(ema_values[-1] - ema_values[0])
            magnitude = min(total_change, 1.0)  # Clip to [0, 1]
        else:
            magnitude = 0.0
        
        # Calculate acceleration (rate of change acceleration)
        if len(ema_values) >= 3:
            # First differences (velocity)
            diffs = np.diff(ema_values)
            # Second differences (acceleration)
            accel = np.diff(diffs)
            acceleration = float(np.mean(np.abs(accel)))
        else:
            acceleration = 0.0
        
        # Classify trend
        trend = self._classify_trend(
            direction=direction,
            magnitude=magnitude,
            variance=variance,
            acceleration=acceleration
        )
        
        time_span = trajectory_points[-1].timestamp - trajectory_points[0].timestamp
        
        return TrajectoryVector(
            trend=trend,
            direction=direction,
            magnitude=magnitude,
            acceleration=acceleration,
            mean_intensity=mean_intensity,
            variance=variance,
            points_count=len(trajectory_points),
            time_span=time_span
        )
    
    def _classify_trend(
        self,
        direction: float,
        magnitude: float,
        variance: float,
        acceleration: float
    ) -> TrajectoryTrend:
        """
        Classify trajectory trend based on computed metrics.
        
        Args:
            direction: -1.0 (falling) to 1.0 (rising)
            magnitude: 0.0 (stable) to 1.0 (extreme)
            variance: 0.0 (stable) to 1.0 (volatile)
            acceleration: Rate of change acceleration
        
        Returns:
            TrajectoryTrend classification
        """
        # High variance indicates volatility
        if variance > 0.15:
            return TrajectoryTrend.VOLATILE
        
        # Stable (low magnitude)
        if magnitude < 0.1:
            # Determine intensity level
            # This will be set based on mean_intensity in caller
            return TrajectoryTrend.STABLE_NEUTRAL
        
        # Rising trend (direction > 0.2 to catch smaller increases)
        if direction > 0.2:
            if magnitude > 0.5 or acceleration > 0.15:
                return TrajectoryTrend.RISING_SHARP
            else:
                return TrajectoryTrend.RISING_STEADY
        
        # Falling trend (direction < -0.2 to catch smaller decreases)
        if direction < -0.2:
            if magnitude > 0.5 or acceleration > 0.15:
                return TrajectoryTrend.FALLING_SHARP
            else:
                return TrajectoryTrend.FALLING_STEADY
        
        # Default to stable
        return TrajectoryTrend.STABLE_NEUTRAL
    
    def generate_trajectory_summary(
        self,
        trajectory_vector: TrajectoryVector,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate natural language description of emotional trajectory.
        
        Creates contextual text describing the emotional trend that can be
        injected into character prompts for awareness and responsiveness.
        
        Args:
            trajectory_vector: TrajectoryVector from compute_trajectory_vector()
            user_context: Optional context dict with user info
        
        Returns:
            Natural language trajectory description
            Empty string if insufficient data
        
        Example:
            >>> vector = analyzer.compute_trajectory_vector(trajectory)
            >>> summary = analyzer.generate_trajectory_summary(vector)
            >>> print(summary)
            "User has been progressively getting more frustrated over the last hour"
        """
        if trajectory_vector.points_count < 2:
            return ""
        
        # Build description based on trend
        descriptions = []
        
        # Add trend description
        if trajectory_vector.trend == TrajectoryTrend.RISING_SHARP:
            descriptions.append("rapidly escalating")
        elif trajectory_vector.trend == TrajectoryTrend.RISING_STEADY:
            descriptions.append("gradually increasing")
        elif trajectory_vector.trend == TrajectoryTrend.FALLING_SHARP:
            descriptions.append("rapidly de-escalating")
        elif trajectory_vector.trend == TrajectoryTrend.FALLING_STEADY:
            descriptions.append("gradually decreasing")
        elif trajectory_vector.trend == TrajectoryTrend.STABLE_HIGH:
            descriptions.append("consistently high")
        elif trajectory_vector.trend == TrajectoryTrend.STABLE_LOW:
            descriptions.append("consistently low")
        elif trajectory_vector.trend == TrajectoryTrend.VOLATILE:
            descriptions.append("fluctuating unpredictably")
        else:
            return ""
        
        # Add intensity context
        if trajectory_vector.mean_intensity > 0.7:
            descriptions.append("emotional state")
        elif trajectory_vector.mean_intensity > 0.4:
            descriptions.append("mood")
        else:
            descriptions.append("disposition")
        
        # Add time context
        minutes = trajectory_vector.time_span.total_seconds() / 60
        if minutes < 10:
            time_desc = "over the last few minutes"
        elif minutes < 60:
            time_desc = f"over the last {int(minutes)} minutes"
        elif minutes < 1440:
            hours = minutes / 60
            time_desc = f"over the last {int(hours)} hour{'s' if hours > 1 else ''}"
        else:
            days = minutes / 1440
            time_desc = f"over the last {int(days)} day{'s' if days > 1 else ''}"
        
        descriptions.append(time_desc)
        
        # Add confidence note if low point count
        confidence = ""
        if trajectory_vector.points_count < 3:
            confidence = " (based on limited data)"
        
        return " ".join(descriptions) + confidence
    
    async def retrieve_trajectory_context(
        self,
        user_id: str,
        lookback_messages: int = 15,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Complete trajectory analysis in one call.
        
        Retrieves trajectory, computes vector, and generates summary.
        Ready for prompt injection.
        
        Args:
            user_id: User identifier
            lookback_messages: Number of messages to analyze
            include_summary: Whether to generate natural language summary
        
        Returns:
            Dict with:
            {
                'trajectory_vector': TrajectoryVector,
                'has_trajectory': bool,
                'summary': str (if include_summary),
                'points_count': int,
                'trend': str,
                'direction': float,
                'magnitude': float,
                'variance': float
            }
        
        Example:
            >>> context = await analyzer.retrieve_trajectory_context("user_123")
            >>> if context['has_trajectory']:
            ...     print(f"Trend: {context['trend']}")
            ...     print(f"Summary: {context['summary']}")
        """
        try:
            # Extract trajectory from memory
            trajectory_points = await self.extract_trajectory(
                user_id=user_id,
                lookback_messages=lookback_messages
            )
            
            if not trajectory_points:
                return {
                    'trajectory_vector': None,
                    'has_trajectory': False,
                    'summary': '',
                    'points_count': 0,
                    'trend': None,
                    'direction': 0.0,
                    'magnitude': 0.0,
                    'variance': 0.0
                }
            
            # Compute trajectory vector
            trajectory_vector = self.compute_trajectory_vector(trajectory_points)
            
            # Generate summary if requested
            summary = ""
            if include_summary:
                summary = self.generate_trajectory_summary(trajectory_vector)
            
            return {
                'trajectory_vector': trajectory_vector,
                'has_trajectory': trajectory_vector.points_count >= 2,
                'summary': summary,
                'points_count': trajectory_vector.points_count,
                'trend': trajectory_vector.trend.value,
                'direction': trajectory_vector.direction,
                'magnitude': trajectory_vector.magnitude,
                'variance': trajectory_vector.variance
            }
            
        except Exception as e:
            self.logger.warning(
                f"Failed to retrieve trajectory context for {user_id}: {e}"
            )
            return {
                'trajectory_vector': None,
                'has_trajectory': False,
                'summary': '',
                'points_count': 0,
                'trend': None,
                'direction': 0.0,
                'magnitude': 0.0,
                'variance': 0.0
            }
