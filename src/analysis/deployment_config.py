"""
Adaptive NLP Configuration for Docker/Native Deployment

This module automatically configures NLP components based on the deployment environment:
- Native macOS: Uses larger models with GPU acceleration (MPS)
- Docker containers: Uses smaller CPU-optimized models
- External APIs: Offloads heavy processing to external services

Follows your existing pattern of external embeddings for GPU-intensive tasks.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Detected deployment environment."""

    NATIVE_MACOS = "native_macos"  # Native Python on macOS
    DOCKER_CONTAINER = "docker_container"  # Running inside Docker
    CLOUD_INSTANCE = "cloud_instance"  # Cloud deployment
    UNKNOWN = "unknown"


@dataclass
class NLPConfiguration:
    """NLP configuration optimized for deployment environment."""

    environment: DeploymentEnvironment
    spacy_model: str
    use_external_embeddings: bool
    use_gpu_acceleration: bool
    performance_mode: str  # 'fast', 'balanced', 'accurate'

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.environment == DeploymentEnvironment.DOCKER_CONTAINER and self.use_gpu_acceleration:
            logger.warning("GPU acceleration not available in Docker on macOS - disabling")
            self.use_gpu_acceleration = False


def detect_deployment_environment() -> DeploymentEnvironment:
    """Detect the current deployment environment."""

    # Check if running in Docker
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "true":
        return DeploymentEnvironment.DOCKER_CONTAINER

    # Check if running on macOS
    import platform

    if platform.system() == "Darwin":
        return DeploymentEnvironment.NATIVE_MACOS

    # Check for cloud instance indicators
    cloud_indicators = [
        "AWS_REGION",
        "GOOGLE_CLOUD_PROJECT",
        "AZURE_SUBSCRIPTION_ID",
        "KUBERNETES_SERVICE_HOST",
        "RENDER",
        "HEROKU",
    ]
    if any(os.getenv(indicator) for indicator in cloud_indicators):
        return DeploymentEnvironment.CLOUD_INSTANCE

    return DeploymentEnvironment.UNKNOWN


def get_optimal_nlp_config() -> NLPConfiguration:
    """Get optimal NLP configuration for current environment."""

    environment = detect_deployment_environment()

    # Base configuration
    config = {
        "use_external_embeddings": True,  # Always use external embeddings (your proven approach)
        "performance_mode": "balanced",
    }

    if environment == DeploymentEnvironment.NATIVE_MACOS:
        # Native macOS: Use large models with GPU acceleration
        config.update(
            {
                "spacy_model": os.getenv("NLP_SPACY_MODEL", "en_core_web_lg"),
                "use_gpu_acceleration": True,
                "performance_mode": "accurate",
            }
        )
        logger.info("Configured for native macOS with GPU acceleration")

    elif environment == DeploymentEnvironment.DOCKER_CONTAINER:
        # Docker: Use smaller CPU-optimized models
        config.update(
            {
                "spacy_model": "en_core_web_sm",  # Smaller model for Docker
                "use_gpu_acceleration": False,
                "performance_mode": "fast",
            }
        )
        logger.info("Configured for Docker container with CPU optimization")

    elif environment == DeploymentEnvironment.CLOUD_INSTANCE:
        # Cloud: Balanced approach, check for GPU availability
        try:
            import torch

            has_gpu = torch.cuda.is_available()
        except ImportError:
            has_gpu = False

        config.update(
            {
                "spacy_model": "en_core_web_md" if has_gpu else "en_core_web_sm",
                "use_gpu_acceleration": has_gpu,
                "performance_mode": "balanced",
            }
        )
        logger.info(f"Configured for cloud deployment (GPU: {has_gpu})")

    else:
        # Unknown environment: Conservative settings
        config.update(
            {
                "spacy_model": "en_core_web_sm",
                "use_gpu_acceleration": False,
                "performance_mode": "fast",
            }
        )
        logger.warning("Unknown deployment environment - using conservative settings")

    return NLPConfiguration(environment=environment, **config)


def get_deployment_recommendations() -> Dict[str, Any]:
    """Get deployment recommendations based on current environment."""

    config = get_optimal_nlp_config()

    recommendations = {
        "current_config": {
            "environment": config.environment.value,
            "spacy_model": config.spacy_model,
            "external_embeddings": config.use_external_embeddings,
            "gpu_acceleration": config.use_gpu_acceleration,
            "performance_mode": config.performance_mode,
        },
        "recommendations": [],
    }

    if config.environment == DeploymentEnvironment.NATIVE_MACOS:
        recommendations["recommendations"].extend(
            [
                "✅ Optimal setup detected - using GPU acceleration",
                "✅ External embeddings prevent Docker GPU limitations",
                "🚀 Can use large spaCy models for best accuracy",
                "💡 Consider native NLP service for multiple bot instances",
            ]
        )

    elif config.environment == DeploymentEnvironment.DOCKER_CONTAINER:
        recommendations["recommendations"].extend(
            [
                "⚠️  Docker on macOS cannot access GPU",
                "✅ Using CPU-optimized models for Docker",
                "✅ External embeddings maintain high quality",
                "💡 Consider hybrid deployment: Docker + native NLP service",
            ]
        )

    elif config.environment == DeploymentEnvironment.CLOUD_INSTANCE:
        recommendations["recommendations"].extend(
            [
                "☁️  Cloud deployment detected",
                "🔍 GPU availability checked automatically",
                "✅ External embeddings provide consistency",
                "💡 Consider managed NLP services for scale",
            ]
        )

    return recommendations


def create_docker_optimized_config() -> Dict[str, str]:
    """Create environment variables for Docker deployment."""
    return {
        "NLP_SPACY_MODEL": "en_core_web_sm",
        "ENABLE_ADVANCED_TOPIC_EXTRACTION": "true",
        "USE_EXTERNAL_EMBEDDINGS": "true",
        "NLP_PERFORMANCE_MODE": "fast",
        "DOCKER_CONTAINER": "true",
    }


def create_native_optimized_config() -> Dict[str, str]:
    """Create environment variables for native deployment."""
    return {
        "NLP_SPACY_MODEL": "en_core_web_lg",
        "ENABLE_ADVANCED_TOPIC_EXTRACTION": "true",
        "USE_EXTERNAL_EMBEDDINGS": "true",
        "NLP_PERFORMANCE_MODE": "accurate",
        "DOCKER_CONTAINER": "false",
    }


# Quick status check
def print_deployment_status():
    """Print current deployment status and recommendations."""
    recommendations = get_deployment_recommendations()

    print("🔧 NLP Deployment Configuration")
    print("=" * 50)

    config = recommendations["current_config"]
    print(f"Environment: {config['environment']}")
    print(f"spaCy Model: {config['spacy_model']}")
    print(f"External Embeddings: {config['external_embeddings']}")
    print(f"GPU Acceleration: {config['gpu_acceleration']}")
    print(f"Performance Mode: {config['performance_mode']}")

    print(f"\n📋 Recommendations:")
    for rec in recommendations["recommendations"]:
        print(f"  {rec}")

    print(f"\n💡 Your Current Approach (External Embeddings) is PERFECT for:")
    print(f"  • Avoiding Docker GPU limitations on macOS")
    print(f"  • Consistent performance across environments")
    print(f"  • Leveraging powerful external GPU resources")
    print(f"  • Keeping containers lightweight and portable")


if __name__ == "__main__":
    print_deployment_status()
