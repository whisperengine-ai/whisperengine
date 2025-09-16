"""
NLP Service Configuration and Architecture Options

This file defines different deployment architectures for the NLP components
based on performance requirements and infrastructure constraints.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class DeploymentMode(Enum):
    """Deployment modes for NLP components."""

    NATIVE_INTEGRATED = "native_integrated"  # All in main bot process
    NATIVE_SERVICE = "native_service"  # Separate native NLP service
    DOCKER_CPU = "docker_cpu"  # Docker with CPU-only models
    EXTERNAL_API = "external_api"  # External API service


@dataclass
class NLPConfig:
    """Configuration for NLP components."""

    deployment_mode: DeploymentMode
    use_gpu: bool
    model_cache_dir: Optional[str] = None
    service_host: str = "localhost"
    service_port: int = 8080
    timeout_seconds: int = 30

    # Model configurations
    spacy_model: str = "en_core_web_sm"  # Smaller model for Docker
    sentence_transformer_model: str = "all-Mpnet-BASE-v2"

    # Performance settings
    batch_size: int = 1
    max_workers: int = 1


def get_nlp_config() -> NLPConfig:
    """Get NLP configuration based on environment."""

    # Detect environment
    deployment_mode = os.getenv("NLP_DEPLOYMENT_MODE", "native_integrated")

    # Check GPU availability
    use_gpu = False
    try:
        import torch

        use_gpu = (
            torch.backends.mps.is_available()
            if hasattr(torch.backends, "mps")
            else torch.cuda.is_available()
        )
    except ImportError:
        pass

    # Adjust models based on deployment
    if deployment_mode == "docker_cpu":
        # Use smaller models for Docker CPU deployment
        spacy_model = "en_core_web_sm"
        sentence_transformer_model = "all-Mpnet-BASE-v2"
    elif deployment_mode in ["native_integrated", "native_service"]:
        # Use larger models for native deployment with GPU
        spacy_model = "en_core_web_lg" if use_gpu else "en_core_web_sm"
        sentence_transformer_model = "all-Mpnet-BASE-v2"

    return NLPConfig(
        deployment_mode=DeploymentMode(deployment_mode),
        use_gpu=use_gpu,
        spacy_model=spacy_model,
        sentence_transformer_model=sentence_transformer_model,
        service_host=os.getenv("NLP_SERVICE_HOST", "localhost"),
        service_port=int(os.getenv("NLP_SERVICE_PORT", "8080")),
        timeout_seconds=int(os.getenv("NLP_TIMEOUT_SECONDS", "30")),
    )


# Architecture comparison
ARCHITECTURE_COMPARISON = {
    "native_integrated": {
        "description": "NLP components run in main bot process",
        "pros": [
            "Simple architecture",
            "No network overhead",
            "Uses Apple Silicon GPU (MPS)",
            "Easy debugging",
            "Fast initialization",
        ],
        "cons": [
            "Higher memory usage in main process",
            "Less scalable",
            "Single point of failure",
            "Model loading blocks bot startup",
        ],
        "best_for": "Single bot instance, development, small to medium load",
        "performance": "Excellent (native GPU)",
        "complexity": "Low",
    },
    "native_service": {
        "description": "Separate FastAPI service for NLP on native macOS",
        "pros": [
            "Uses Apple Silicon GPU (MPS)",
            "Scalable (multiple bot instances)",
            "Isolated failure domain",
            "Hot model reloading",
            "Can serve multiple applications",
        ],
        "cons": [
            "Additional service to manage",
            "Network latency (minimal on localhost)",
            "More complex deployment",
            "Requires service discovery",
        ],
        "best_for": "Production, multiple bots, high availability",
        "performance": "Excellent (native GPU)",
        "complexity": "Medium",
    },
    "docker_cpu": {
        "description": "NLP components in Docker with CPU-only models",
        "pros": [
            "Consistent deployment",
            "Easy scaling with orchestration",
            "Isolated environment",
            "Simple container management",
        ],
        "cons": [
            "No GPU acceleration on Docker for Mac",
            "Slower inference times",
            "Limited to smaller models",
            "Higher latency",
        ],
        "best_for": "Cloud deployment, CI/CD, when GPU not available",
        "performance": "Good (CPU-only)",
        "complexity": "Medium",
    },
    "external_api": {
        "description": "Use external APIs for NLP processing",
        "pros": [
            "No local resource usage",
            "Professional-grade models",
            "Always up-to-date",
            "No model management",
        ],
        "cons": [
            "API costs",
            "Network dependency",
            "Data privacy concerns",
            "Rate limiting",
            "Vendor lock-in",
        ],
        "best_for": "Production with budget, privacy-compliant use cases",
        "performance": "Variable (network dependent)",
        "complexity": "Low",
    },
}


def print_architecture_comparison():
    """Print comparison of architecture options."""
    print("🏗️  NLP Architecture Comparison")
    print("=" * 80)

    for mode, details in ARCHITECTURE_COMPARISON.items():
        print(f"\n📋 {mode.upper()}")
        print(f"Description: {details['description']}")
        print(f"Performance: {details['performance']}")
        print(f"Complexity: {details['complexity']}")
        print(f"Best for: {details['best_for']}")

        print("✅ Pros:")
        for pro in details["pros"]:
            print(f"   • {pro}")

        print("❌ Cons:")
        for con in details["cons"]:
            print(f"   • {con}")
        print("-" * 80)


if __name__ == "__main__":
    print_architecture_comparison()

    print(f"\n🔧 Current Configuration:")
    config = get_nlp_config()
    print(f"Deployment Mode: {config.deployment_mode.value}")
    print(f"GPU Available: {config.use_gpu}")
    print(f"spaCy Model: {config.spacy_model}")
    print(f"Sentence Transformer: {config.sentence_transformer_model}")
