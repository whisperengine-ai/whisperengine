"""
Adaptive Configuration System for WhisperEngine
Automatically detects environment and optimizes configuration for available resources.
"""

import os
import platform
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class ResourceInfo:
    """System resource information"""

    cpu_cores: int
    memory_gb: float
    storage_gb: float
    platform: str
    architecture: str
    gpu_available: bool = False
    docker_available: bool = False
    kubernetes_available: bool = False


@dataclass
class PerformanceConfig:
    """Performance-related configuration"""

    cpu_threads: int
    memory_limit_gb: float
    cache_size_mb: int
    batch_size: int
    timeout_seconds: int
    enable_local_ai: bool
    enable_semantic_clustering: bool


@dataclass
class DatabaseConfig:
    """Database configuration"""

    primary_type: str  # sqlite, postgresql
    vector_type: str  # local_chromadb, http_chromadb, distributed_chromadb
    cache_type: str  # memory, redis, redis_cluster
    connection_pool_size: int
    backup_enabled: bool


@dataclass
class ScalingConfig:
    """Complete scaling configuration"""

    deployment_mode: str  # desktop, container, kubernetes, multi_tenant
    scale_tier: int  # 1-4
    environment: str  # development, production
    resources: ResourceInfo
    performance: PerformanceConfig
    database: DatabaseConfig
    features: Dict[str, bool]


class EnvironmentDetector:
    """Detects the current deployment environment"""

    @staticmethod
    def detect_environment() -> str:
        """Detect deployment environment"""
        if os.path.exists("/.dockerenv"):
            return "container"
        elif "KUBERNETES_SERVICE_HOST" in os.environ:
            return "kubernetes"
        elif os.environ.get("WHISPERENGINE_MODE") == "multi_bot":
            return "multi_bot"
        else:
            return "desktop"

    @staticmethod
    def detect_resources() -> ResourceInfo:
        """Detect available system resources"""
        if PSUTIL_AVAILABLE:
            # CPU information
            cpu_cores = psutil.cpu_count(logical=True) or 4  # Default fallback

            # Memory information
            memory_bytes = psutil.virtual_memory().total
            memory_gb = memory_bytes / (1024**3)

            # Storage information
            try:
                storage_bytes = psutil.disk_usage("/").total
                storage_gb = storage_bytes / (1024**3)
            except:
                storage_gb = 100.0  # Default fallback
        else:
            # Fallback detection without psutil
            cpu_cores = os.cpu_count() or 4
            memory_gb = 8.0  # Conservative default
            storage_gb = 100.0  # Conservative default

        # Platform information
        platform_name = platform.system()
        architecture = platform.machine()

        # GPU detection (basic)
        gpu_available = EnvironmentDetector._detect_gpu()

        # Container detection
        docker_available = EnvironmentDetector._detect_docker()
        kubernetes_available = EnvironmentDetector._detect_kubernetes()

        return ResourceInfo(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            platform=platform_name,
            architecture=architecture,
            gpu_available=gpu_available,
            docker_available=docker_available,
            kubernetes_available=kubernetes_available,
        )

    @staticmethod
    def _detect_gpu() -> bool:
        """Detect GPU availability"""
        try:
            # Check for NVIDIA GPU
            import subprocess

            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except:
            pass

        try:
            # Check for Apple Metal
            if platform.system() == "Darwin":
                import subprocess

                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True
                )
                if "Apple" in result.stdout and "GPU" in result.stdout:
                    return True
        except:
            pass

        return False

    @staticmethod
    def _detect_docker() -> bool:
        """Detect Docker availability"""
        try:
            import subprocess

            result = subprocess.run(["docker", "--version"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def _detect_kubernetes() -> bool:
        """Detect Kubernetes environment"""
        return "KUBERNETES_SERVICE_HOST" in os.environ


class ConfigurationOptimizer:
    """Optimizes configuration based on detected environment and resources"""

    def __init__(self):
        self.environment = EnvironmentDetector.detect_environment()
        self.resources = EnvironmentDetector.detect_resources()

    def generate_optimal_config(self) -> ScalingConfig:
        """Generate optimized configuration for current environment"""
        scale_tier = self._determine_scale_tier()

        return ScalingConfig(
            deployment_mode=self.environment,
            scale_tier=scale_tier,
            environment=os.environ.get("ENVIRONMENT", "development"),
            resources=self.resources,
            performance=self._generate_performance_config(scale_tier),
            database=self._generate_database_config(scale_tier),
            features=self._generate_feature_config(scale_tier),
        )

    def _determine_scale_tier(self) -> int:
        """Determine appropriate scale tier based on resources"""
        memory_gb = self.resources.memory_gb
        cpu_cores = self.resources.cpu_cores

        if self.environment == "kubernetes":
            return 4  # Enterprise/Cloud
        elif self.environment == "multi_bot":
            return 3  # Small business
        elif memory_gb >= 64 and cpu_cores >= 16:
            return 3  # High-performance single user
        elif memory_gb >= 32 and cpu_cores >= 8:
            return 2  # Balanced single user
        else:
            return 1  # Constrained single user

    def _generate_performance_config(self, scale_tier: int) -> PerformanceConfig:
        """Generate performance configuration based on scale tier"""
        memory_gb = self.resources.memory_gb
        cpu_cores = self.resources.cpu_cores

        if scale_tier == 1:  # Constrained
            return PerformanceConfig(
                cpu_threads=min(cpu_cores, 4),
                memory_limit_gb=min(memory_gb * 0.3, 4.0),
                cache_size_mb=256,
                batch_size=50,
                timeout_seconds=30,
                enable_local_ai=memory_gb >= 16,
                enable_semantic_clustering=False,
            )
        elif scale_tier == 2:  # Balanced
            return PerformanceConfig(
                cpu_threads=min(cpu_cores, 8),
                memory_limit_gb=min(memory_gb * 0.4, 8.0),
                cache_size_mb=512,
                batch_size=100,
                timeout_seconds=60,
                enable_local_ai=memory_gb >= 32,
                enable_semantic_clustering=memory_gb >= 32,
            )
        elif scale_tier == 3:  # High-performance
            return PerformanceConfig(
                cpu_threads=min(cpu_cores, 16),
                memory_limit_gb=min(memory_gb * 0.5, 16.0),
                cache_size_mb=1024,
                batch_size=200,
                timeout_seconds=90,
                enable_local_ai=True,
                enable_semantic_clustering=True,
            )
        else:  # Enterprise/Cloud
            return PerformanceConfig(
                cpu_threads=4,  # Per pod/container
                memory_limit_gb=4.0,  # Per pod/container
                cache_size_mb=512,
                batch_size=100,
                timeout_seconds=30,
                enable_local_ai=False,  # Use APIs for predictable scaling
                enable_semantic_clustering=False,
            )

    def _generate_database_config(self, scale_tier: int) -> DatabaseConfig:
        """Generate database configuration based on scale tier"""
        if scale_tier == 1:  # Desktop/Constrained
            return DatabaseConfig(
                primary_type="sqlite",
                vector_type="local_chromadb",
                cache_type="memory",
                connection_pool_size=2,
                backup_enabled=True,
            )
        elif scale_tier == 2:  # Balanced/Multi-bot
            return DatabaseConfig(
                primary_type="postgresql",
                vector_type="http_chromadb",
                cache_type="redis",
                connection_pool_size=5,
                backup_enabled=True,
            )
        elif scale_tier == 3:  # High-performance
            return DatabaseConfig(
                primary_type="postgresql",
                vector_type="http_chromadb",
                cache_type="redis",
                connection_pool_size=10,
                backup_enabled=True,
            )
        else:  # Enterprise/Cloud
            return DatabaseConfig(
                primary_type="postgresql_cluster",
                vector_type="distributed_chromadb",
                cache_type="redis_cluster",
                connection_pool_size=20,
                backup_enabled=True,
            )

    def _generate_feature_config(self, scale_tier: int) -> Dict[str, bool]:
        """Generate feature configuration based on scale tier"""
        base_features = {
            "enable_emotions": True,
            "enable_auto_facts": True,
            "enable_global_facts": scale_tier >= 3,
            "enable_phase3_memory": True,
            "enable_phase4_human_like": True,
            "enable_voice_features": scale_tier <= 3,  # Disable in cloud for complexity
            "enable_follow_up": True,
            "enable_job_scheduler": True,
            "enable_monitoring": scale_tier >= 3,
            "enable_logging": True,
            "enable_debug_mode": False,
        }

        return base_features


class AdaptiveConfigManager:
    """Main configuration manager that adapts to environment"""

    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.optimizer = ConfigurationOptimizer()
        self.config = self.optimizer.generate_optimal_config()
        self._apply_overrides(config_override)

    @property
    def scale_tier(self) -> int:
        """Get the current scale tier"""
        return self.config.scale_tier

    @property
    def environment(self) -> str:
        """Get the current environment"""
        return self.config.environment

    @property
    def deployment_mode(self) -> str:
        """Get the current deployment mode"""
        return self.config.deployment_mode

    def get_storage_configuration(self) -> Dict[str, Any]:
        """Get storage configuration details"""
        return {
            "primary_database": self.config.database.primary_type,
            "vector_database": self.config.database.vector_type,
            "cache_type": self.config.database.cache_type,
            "connection_pool_size": self.config.database.connection_pool_size,
            "backup_enabled": self.config.database.backup_enabled,
        }

    def _apply_overrides(self, overrides: Optional[Dict[str, Any]]):
        """Apply manual configuration overrides"""
        if not overrides:
            return

        # Apply environment variable overrides
        env_overrides = self._load_env_overrides()
        if env_overrides:
            overrides.update(env_overrides)

        # TODO: Implement deep merge of override configuration
        # This would allow fine-grained control over specific settings

    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables"""
        overrides = {}

        # Performance overrides
        if "WHISPERENGINE_CPU_THREADS" in os.environ:
            overrides["performance.cpu_threads"] = int(os.environ["WHISPERENGINE_CPU_THREADS"])

        if "WHISPERENGINE_MEMORY_LIMIT_GB" in os.environ:
            overrides["performance.memory_limit_gb"] = float(
                os.environ["WHISPERENGINE_MEMORY_LIMIT_GB"]
            )

        if "WHISPERENGINE_ENABLE_LOCAL_AI" in os.environ:
            overrides["performance.enable_local_ai"] = (
                os.environ["WHISPERENGINE_ENABLE_LOCAL_AI"].lower() == "true"
            )

        # Database overrides
        if "WHISPERENGINE_DATABASE_TYPE" in os.environ:
            overrides["database.primary_type"] = os.environ["WHISPERENGINE_DATABASE_TYPE"]

        # Feature overrides
        if "WHISPERENGINE_SCALE_TIER" in os.environ:
            overrides["scale_tier"] = int(os.environ["WHISPERENGINE_SCALE_TIER"])

        return overrides

    def get_env_vars(self) -> Dict[str, str]:
        """Generate environment variables from current configuration"""
        env_vars = {}

        # Core configuration
        env_vars["ENVIRONMENT"] = self.config.environment
        env_vars["DEPLOYMENT_MODE"] = self.config.deployment_mode
        env_vars["SCALE_TIER"] = str(self.config.scale_tier)

        # Performance configuration
        perf = self.config.performance
        env_vars["MEMORY_THREAD_POOL_SIZE"] = str(perf.cpu_threads)
        env_vars["MAX_PROCESSING_TIME"] = str(perf.timeout_seconds)
        env_vars["CONVERSATION_CACHE_TIMEOUT"] = str(perf.cache_size_mb // 10)  # Rough conversion
        env_vars["EMBEDDING_BATCH_SIZE"] = str(perf.batch_size)

        # AI/ML configuration
        env_vars["USE_EXTERNAL_EMBEDDINGS"] = str(not perf.enable_local_ai).lower()
        env_vars["ENABLE_SEMANTIC_CLUSTERING"] = str(perf.enable_semantic_clustering).lower()

        # Database configuration
        db = self.config.database
        if db.primary_type == "sqlite":
            env_vars["USE_POSTGRESQL"] = "false"
        else:
            env_vars["USE_POSTGRESQL"] = "true"

        if db.cache_type == "memory":
            env_vars["USE_REDIS_CACHE"] = "false"
        else:
            env_vars["USE_REDIS_CACHE"] = "true"

        # Feature flags
        features = self.config.features
        env_vars["ENABLE_EMOTIONS"] = str(features.get("enable_emotions", True)).lower()
        env_vars["ENABLE_AUTO_FACTS"] = str(features.get("enable_auto_facts", True)).lower()
        env_vars["ENABLE_GLOBAL_FACTS"] = str(features.get("enable_global_facts", False)).lower()
        env_vars["ENABLE_PHASE3_MEMORY"] = str(features.get("enable_phase3_memory", True)).lower()
        env_vars["ENABLE_PHASE4_HUMAN_LIKE"] = str(
            features.get("enable_phase4_human_like", True)
        ).lower()
        env_vars["FOLLOW_UP_ENABLED"] = str(features.get("enable_follow_up", True)).lower()
        env_vars["JOB_SCHEDULER_ENABLED"] = str(features.get("enable_job_scheduler", True)).lower()
        env_vars["DEBUG_MODE"] = str(features.get("enable_debug_mode", False)).lower()

        return env_vars

    def save_config(self, filepath: str):
        """Save current configuration to file"""
        config_dict = asdict(self.config)
        with open(filepath, "w") as f:
            json.dump(config_dict, f, indent=2)

    def load_config(self, filepath: str):
        """Load configuration from file"""
        with open(filepath, "r") as f:
            config_dict = json.load(f)

        # TODO: Implement proper deserialization from dict to ScalingConfig
        # This would require custom serialization/deserialization logic

    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information for monitoring/debugging"""
        return {
            "deployment_mode": self.config.deployment_mode,
            "scale_tier": self.config.scale_tier,
            "environment": self.config.environment,
            "cpu_cores": self.config.resources.cpu_cores,
            "memory_gb": self.config.resources.memory_gb,
            "platform": self.config.resources.platform,
            "architecture": self.config.resources.architecture,
            "gpu_available": self.config.resources.gpu_available,
            "local_ai_enabled": self.config.performance.enable_local_ai,
            "semantic_clustering_enabled": self.config.performance.enable_semantic_clustering,
            "database_type": self.config.database.primary_type,
            "cache_type": self.config.database.cache_type,
        }


# Example usage and testing
if __name__ == "__main__":
    # Create adaptive configuration manager
    config_manager = AdaptiveConfigManager()

    # Print deployment information
    print("=== WhisperEngine Adaptive Configuration ===")
    deployment_info = config_manager.get_deployment_info()
    for key, value in deployment_info.items():
        print(f"{key}: {value}")

    print("\n=== Generated Environment Variables ===")
    env_vars = config_manager.get_env_vars()
    for key, value in sorted(env_vars.items()):
        print(f"{key}={value}")

    # Save configuration for review
    config_path = Path("~/.whisperengine/adaptive_config.json").expanduser()
    config_path.parent.mkdir(exist_ok=True)
    config_manager.save_config(str(config_path))
    print(f"\nConfiguration saved to: {config_path}")
