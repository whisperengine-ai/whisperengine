"""
Memory Timing Attack Prevention System
Addresses CVSS 5.1 Memory System Timing Attacks Vulnerability

This module prevents timing-based information disclosure attacks by:
- Normalizing response times across different data states
- Adding controlled randomization to prevent timing correlation
- Implementing constant-time operations where possible
- Monitoring and alerting on suspicious timing patterns
- Providing secure caching strategies

SECURITY FEATURES:
- Response time normalization
- Timing jitter injection
- Constant-time memory operations
- Cache hit/miss timing protection
- Suspicious pattern detection
- Performance impact minimization
"""

import asyncio
import hashlib
import logging
import random
import statistics
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Import secure logging for timing security events
try:
    from secure_logging import DataSensitivity, LogLevel, get_secure_logger

    secure_logger = get_secure_logger("timing_attack_prevention")
    HAS_SECURE_LOGGING = True
except ImportError:
    secure_logger = logging.getLogger("timing_attack_prevention")
    HAS_SECURE_LOGGING = False

logger = logging.getLogger(__name__)


class TimingProfile(Enum):
    """Different timing profiles for various operations"""

    MEMORY_RETRIEVAL = "memory_retrieval"  # Memory lookup operations
    CACHE_OPERATION = "cache_operation"  # Cache hit/miss operations
    DATABASE_QUERY = "database_query"  # Database query operations
    LLM_PROCESSING = "llm_processing"  # LLM response generation
    USER_VALIDATION = "user_validation"  # User authentication/validation
    RELATIONSHIP_ANALYSIS = "relationship"  # Relationship state analysis


class TimingSensitivity(Enum):
    """Sensitivity levels for timing protection"""

    LOW = "low"  # Minimal timing protection needed
    MEDIUM = "medium"  # Moderate timing protection
    HIGH = "high"  # Strong timing protection required
    CRITICAL = "critical"  # Maximum timing protection


@dataclass
class TimingMeasurement:
    """Record of a timing measurement for analysis"""

    operation: str
    start_time: float
    end_time: float
    duration: float
    data_present: bool  # Whether data was found/available
    cache_hit: bool  # Whether operation was cache hit
    user_id_hash: str  # Hashed user ID for tracking
    sensitivity: TimingSensitivity
    timestamp: datetime


@dataclass
class TimingNormalizationConfig:
    """Configuration for timing normalization"""

    min_response_time: float = 0.1  # Minimum response time (seconds)
    max_response_time: float = 2.0  # Maximum response time (seconds)
    jitter_range: float = 0.05  # Random jitter range (±seconds)
    target_percentile: float = 0.95  # Target response time percentile
    enable_adaptive: bool = True  # Enable adaptive timing adjustment


class TimingAttackPrevention:
    """
    System to prevent timing-based information disclosure attacks.

    This class provides timing normalization and protection for sensitive operations
    to prevent attackers from inferring information based on response times.
    """

    def __init__(self, config: TimingNormalizationConfig | None = None):
        self.config = config or TimingNormalizationConfig()
        self.measurements = {}  # operation_type -> List[TimingMeasurement]
        self.baseline_times = {}  # operation_type -> baseline timing stats
        self.suspicious_patterns = {}  # user_id_hash -> suspicious timing patterns
        self.last_cleanup = datetime.now()

        # Initialize baseline measurements for different operations
        self._initialize_baselines()

    def _initialize_baselines(self):
        """Initialize baseline timing measurements for different operations"""

        self.baseline_times = {
            TimingProfile.MEMORY_RETRIEVAL: {
                "target_time": 0.2,
                "variance": 0.05,
                "measurements": [],
            },
            TimingProfile.CACHE_OPERATION: {
                "target_time": 0.05,
                "variance": 0.01,
                "measurements": [],
            },
            TimingProfile.DATABASE_QUERY: {"target_time": 0.3, "variance": 0.1, "measurements": []},
            TimingProfile.LLM_PROCESSING: {"target_time": 1.5, "variance": 0.3, "measurements": []},
            TimingProfile.USER_VALIDATION: {
                "target_time": 0.1,
                "variance": 0.02,
                "measurements": [],
            },
            TimingProfile.RELATIONSHIP_ANALYSIS: {
                "target_time": 0.15,
                "variance": 0.03,
                "measurements": [],
            },
        }

    async def secure_timing_wrapper(
        self,
        operation: Callable[..., Awaitable],
        profile: TimingProfile,
        sensitivity: TimingSensitivity,
        user_id: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Wrap an operation with timing attack protection.

        Args:
            operation: The async operation to protect
            profile: Timing profile for the operation type
            sensitivity: Security sensitivity level
            user_id: User ID for tracking (will be hashed)
            **kwargs: Arguments to pass to the operation

        Returns:
            Result of the operation
        """

        user_id_hash = self._hash_user_id(user_id) if user_id else "anonymous"
        start_time = time.time()

        try:
            # Execute the actual operation
            result = await operation(**kwargs)
            operation_end_time = time.time()
            operation_duration = operation_end_time - start_time

            # Determine if operation found data (for timing analysis)
            data_present = self._analyze_result_for_data_presence(result)

            # Record the measurement
            measurement = TimingMeasurement(
                operation=profile.value,
                start_time=start_time,
                end_time=operation_end_time,
                duration=operation_duration,
                data_present=data_present,
                cache_hit=False,  # Would need to be passed from operation
                user_id_hash=user_id_hash,
                sensitivity=sensitivity,
                timestamp=datetime.now(),
            )

            # Apply timing normalization
            await self._apply_timing_normalization(measurement, profile, sensitivity)

            # Update baselines and detect suspicious patterns
            self._update_baselines(measurement)
            self._detect_suspicious_patterns(measurement)

            return result

        except Exception as e:
            # Even on error, apply timing normalization to prevent info leakage
            error_end_time = time.time()
            error_duration = error_end_time - start_time

            measurement = TimingMeasurement(
                operation=profile.value,
                start_time=start_time,
                end_time=error_end_time,
                duration=error_duration,
                data_present=False,
                cache_hit=False,
                user_id_hash=user_id_hash,
                sensitivity=sensitivity,
                timestamp=datetime.now(),
            )

            await self._apply_timing_normalization(measurement, profile, sensitivity)
            raise e

    async def _apply_timing_normalization(
        self, measurement: TimingMeasurement, profile: TimingProfile, sensitivity: TimingSensitivity
    ):
        """Apply timing normalization to prevent timing attacks"""

        # Get target timing for this operation type
        baseline = self.baseline_times.get(profile, {})
        baseline.get("target_time", self.config.min_response_time)

        # Calculate how much additional delay is needed
        elapsed = measurement.duration
        time.time()

        # Determine minimum required time based on sensitivity
        min_time = self._calculate_minimum_time(profile, sensitivity)

        # Calculate required delay
        required_delay = max(0, min_time - elapsed)

        # Add randomized jitter to prevent timing correlation
        jitter = self._generate_timing_jitter(sensitivity)
        total_delay = required_delay + jitter

        # Apply the delay if needed
        if total_delay > 0:
            await asyncio.sleep(total_delay)

        # Log timing protection actions for monitoring
        self._log_timing_protection(measurement, total_delay, profile, sensitivity)

    def _calculate_minimum_time(
        self, profile: TimingProfile, sensitivity: TimingSensitivity
    ) -> float:
        """Calculate minimum required time based on operation and sensitivity"""

        base_time = self.baseline_times.get(profile, {}).get("target_time", 0.1)

        # Adjust based on sensitivity level
        sensitivity_multipliers = {
            TimingSensitivity.LOW: 0.5,
            TimingSensitivity.MEDIUM: 1.0,
            TimingSensitivity.HIGH: 1.5,
            TimingSensitivity.CRITICAL: 2.0,
        }

        multiplier = sensitivity_multipliers.get(sensitivity, 1.0)
        return base_time * multiplier

    def _generate_timing_jitter(self, sensitivity: TimingSensitivity) -> float:
        """Generate randomized timing jitter to prevent correlation"""

        # Jitter amount based on sensitivity
        jitter_amounts = {
            TimingSensitivity.LOW: 0.01,
            TimingSensitivity.MEDIUM: 0.025,
            TimingSensitivity.HIGH: 0.05,
            TimingSensitivity.CRITICAL: 0.1,
        }

        max_jitter = jitter_amounts.get(sensitivity, 0.025)

        # Generate random jitter (can be positive or negative)
        return random.uniform(-max_jitter, max_jitter)

    def _analyze_result_for_data_presence(self, result: Any) -> bool:
        """Analyze operation result to determine if data was present"""

        # This is operation-specific logic
        if result is None:
            return False
        elif isinstance(result, list):
            return len(result) > 0
        elif isinstance(result, dict):
            return len(result) > 0
        elif isinstance(result, str):
            return len(result.strip()) > 0
        else:
            return result is not None

    def _update_baselines(self, measurement: TimingMeasurement):
        """Update baseline timing measurements"""

        operation_type = measurement.operation
        if operation_type not in self.measurements:
            self.measurements[operation_type] = []

        self.measurements[operation_type].append(measurement)

        # Keep only recent measurements (last 1000 or 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.measurements[operation_type] = [
            m for m in self.measurements[operation_type][-1000:] if m.timestamp > cutoff_time
        ]

        # Update baseline statistics
        if len(self.measurements[operation_type]) >= 10:
            durations = [m.duration for m in self.measurements[operation_type]]

            # Find corresponding TimingProfile enum
            timing_profile = None
            for profile in TimingProfile:
                if profile.value == operation_type:
                    timing_profile = profile
                    break

            if timing_profile and timing_profile in self.baseline_times:
                baseline = self.baseline_times[timing_profile]
                baseline["measurements"] = durations
                baseline["mean"] = statistics.mean(durations)
                baseline["median"] = statistics.median(durations)
                baseline["stdev"] = statistics.stdev(durations) if len(durations) > 1 else 0

                # Adaptive adjustment of target times
                if self.config.enable_adaptive:
                    # Set target time to 95th percentile to handle most legitimate cases
                    sorted_durations = sorted(durations)
                    percentile_index = int(len(sorted_durations) * self.config.target_percentile)
                    baseline["target_time"] = sorted_durations[percentile_index]

                self.baseline_times[timing_profile] = baseline

    def _detect_suspicious_patterns(self, measurement: TimingMeasurement):
        """Detect suspicious timing patterns that might indicate probing"""

        user_hash = measurement.user_id_hash
        if user_hash not in self.suspicious_patterns:
            self.suspicious_patterns[user_hash] = {
                "measurements": [],
                "rapid_requests": 0,
                "timing_variance_low": 0,
                "last_request": None,
            }

        user_data = self.suspicious_patterns[user_hash]
        user_data["measurements"].append(measurement)

        # Keep only recent measurements
        cutoff_time = datetime.now() - timedelta(minutes=10)
        user_data["measurements"] = [
            m for m in user_data["measurements"] if m.timestamp > cutoff_time
        ]

        # Check for suspicious patterns
        self._check_rapid_requests(user_hash, user_data)
        self._check_timing_probing(user_hash, user_data)
        self._check_consistent_timing(user_hash, user_data)

    def _check_rapid_requests(self, user_hash: str, user_data: dict):
        """Check for rapid sequential requests (potential automated probing)"""

        recent_measurements = user_data["measurements"]
        if len(recent_measurements) < 5:
            return

        # Check if requests are coming too rapidly
        time_diffs = []
        for i in range(1, len(recent_measurements)):
            diff = recent_measurements[i].timestamp - recent_measurements[i - 1].timestamp
            time_diffs.append(diff.total_seconds())

        avg_interval = statistics.mean(time_diffs)

        # If average interval is less than 0.5 seconds, it's suspicious
        if avg_interval < 0.5:
            user_data["rapid_requests"] += 1

            if user_data["rapid_requests"] > 3:
                self._alert_suspicious_timing(
                    user_hash, "rapid_requests", f"Average request interval: {avg_interval:.3f}s"
                )

    def _check_timing_probing(self, user_hash: str, user_data: dict):
        """Check for timing-based probing attempts"""

        measurements = user_data["measurements"]
        if len(measurements) < 10:
            return

        # Analyze timing patterns for different data presence states
        with_data = [m for m in measurements if m.data_present]
        without_data = [m for m in measurements if not m.data_present]

        if len(with_data) >= 3 and len(without_data) >= 3:
            with_data_times = [m.duration for m in with_data]
            without_data_times = [m.duration for m in without_data]

            # Check if user is consistently measuring timing differences
            with_avg = statistics.mean(with_data_times)
            without_avg = statistics.mean(without_data_times)

            # If there's a consistent timing difference and user is probing both states
            if abs(with_avg - without_avg) > 0.05:  # 50ms difference
                self._alert_suspicious_timing(
                    user_hash,
                    "timing_probe_detected",
                    f"Data present avg: {with_avg:.3f}s, Data absent avg: {without_avg:.3f}s",
                )

    def _check_consistent_timing(self, user_hash: str, user_data: dict):
        """Check for unusually consistent timing (potential automation)"""

        measurements = user_data["measurements"]
        if len(measurements) < 5:
            return

        durations = [m.duration for m in measurements[-10:]]  # Last 10 measurements

        if len(durations) >= 5:
            stdev = statistics.stdev(durations)
            mean_duration = statistics.mean(durations)

            # If standard deviation is very low relative to mean, it's suspicious
            if stdev < (mean_duration * 0.1):  # Less than 10% variation
                user_data["timing_variance_low"] += 1

                if user_data["timing_variance_low"] > 2:
                    self._alert_suspicious_timing(
                        user_hash,
                        "consistent_timing_detected",
                        f"Very low timing variance: {stdev:.4f}s (mean: {mean_duration:.3f}s)",
                    )

    def _alert_suspicious_timing(self, user_hash: str, pattern_type: str, details: str):
        """Alert on suspicious timing patterns"""

        if HAS_SECURE_LOGGING:
            secure_logger.log_security_event(
                message=f"Suspicious timing pattern detected: {pattern_type} - {details}",
                user_id=None,  # Using hashed user ID in message instead
                threat_level="medium",
                event_type="timing_attack_attempt",
            )
        else:
            logger.warning(
                f"[TIMING_SECURITY] Suspicious pattern {pattern_type} for user {user_hash}: {details}"
            )

    def _log_timing_protection(
        self,
        measurement: TimingMeasurement,
        delay_applied: float,
        profile: TimingProfile,
        sensitivity: TimingSensitivity,
    ):
        """Log timing protection actions for monitoring"""

        if delay_applied > 0.01:  # Only log significant delays
            if HAS_SECURE_LOGGING:
                secure_logger.log_security_event(
                    message=f"Timing protection applied: {delay_applied:.3f}s delay for {profile.value} operation",
                    user_id=None,
                    threat_level="low",
                    event_type="timing_protection_applied",
                )
            else:
                logger.debug(
                    f"[TIMING_PROTECTION] Applied {delay_applied:.3f}s delay for {profile.value}"
                )

    def _hash_user_id(self, user_id: str) -> str:
        """Create a secure hash of user ID for tracking"""
        if not user_id:
            return "anonymous"
        return hashlib.sha256(f"timing_user_{user_id}".encode()).hexdigest()[:16]

    async def secure_memory_retrieval(
        self,
        retrieval_func: Callable,
        user_id: str,
        sensitivity: TimingSensitivity = TimingSensitivity.HIGH,
        **kwargs,
    ) -> Any:
        """Secure wrapper for memory retrieval operations"""

        return await self.secure_timing_wrapper(
            operation=retrieval_func,
            profile=TimingProfile.MEMORY_RETRIEVAL,
            sensitivity=sensitivity,
            user_id=user_id,
            **kwargs,
        )

    async def secure_cache_operation(
        self,
        cache_func: Callable,
        user_id: str,
        sensitivity: TimingSensitivity = TimingSensitivity.MEDIUM,
        **kwargs,
    ) -> Any:
        """Secure wrapper for cache operations"""

        return await self.secure_timing_wrapper(
            operation=cache_func,
            profile=TimingProfile.CACHE_OPERATION,
            sensitivity=sensitivity,
            user_id=user_id,
            **kwargs,
        )

    async def secure_database_query(
        self,
        query_func: Callable,
        user_id: str,
        sensitivity: TimingSensitivity = TimingSensitivity.HIGH,
        **kwargs,
    ) -> Any:
        """Secure wrapper for database query operations"""

        return await self.secure_timing_wrapper(
            operation=query_func,
            profile=TimingProfile.DATABASE_QUERY,
            sensitivity=sensitivity,
            user_id=user_id,
            **kwargs,
        )

    async def secure_user_validation(
        self,
        validation_func: Callable,
        user_id: str,
        sensitivity: TimingSensitivity = TimingSensitivity.CRITICAL,
        **kwargs,
    ) -> Any:
        """Secure wrapper for user validation operations"""

        return await self.secure_timing_wrapper(
            operation=validation_func,
            profile=TimingProfile.USER_VALIDATION,
            sensitivity=sensitivity,
            user_id=user_id,
            **kwargs,
        )

    def get_timing_statistics(self, operation_type: str | None = None) -> dict[str, Any]:
        """Get timing statistics for monitoring and analysis"""

        if operation_type:
            if operation_type in self.baseline_times:
                return self.baseline_times[operation_type].copy()
            else:
                return {}

        # Return all statistics
        stats = {}
        for op_type, baseline in self.baseline_times.items():
            stats[op_type] = baseline.copy()
            # Remove raw measurements to reduce data size
            if "measurements" in stats[op_type]:
                stats[op_type]["measurement_count"] = len(stats[op_type]["measurements"])
                del stats[op_type]["measurements"]

        return stats

    def cleanup_old_data(self):
        """Clean up old timing data to prevent memory leaks"""

        now = datetime.now()

        # Only cleanup every hour
        if now - self.last_cleanup < timedelta(hours=1):
            return

        cutoff_time = now - timedelta(hours=24)

        # Clean up measurements
        for operation_type in self.measurements:
            self.measurements[operation_type] = [
                m for m in self.measurements[operation_type] if m.timestamp > cutoff_time
            ]

        # Clean up suspicious patterns
        for user_hash in list(self.suspicious_patterns.keys()):
            user_data = self.suspicious_patterns[user_hash]
            user_data["measurements"] = [
                m for m in user_data["measurements"] if m.timestamp > cutoff_time
            ]

            # Remove users with no recent activity
            if not user_data["measurements"]:
                del self.suspicious_patterns[user_hash]

        self.last_cleanup = now


# Global instance for easy access
timing_protection = TimingAttackPrevention()


# Convenient wrapper functions
async def secure_memory_lookup(lookup_func: Callable, user_id: str, **kwargs) -> Any:
    """Convenient function for secure memory lookups"""
    return await timing_protection.secure_memory_retrieval(
        lookup_func, user_id, TimingSensitivity.HIGH, **kwargs
    )


async def secure_cache_lookup(cache_func: Callable, user_id: str, **kwargs) -> Any:
    """Convenient function for secure cache lookups"""
    return await timing_protection.secure_cache_operation(
        cache_func, user_id, TimingSensitivity.MEDIUM, **kwargs
    )


async def secure_user_check(validation_func: Callable, user_id: str, **kwargs) -> Any:
    """Convenient function for secure user validation"""
    return await timing_protection.secure_user_validation(
        validation_func, user_id, TimingSensitivity.CRITICAL, **kwargs
    )
