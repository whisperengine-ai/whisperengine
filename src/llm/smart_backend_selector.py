"""
Simplified backend selector for WhisperEngine.
Only supports remote API backends - no local model loading.
"""

import os
import logging
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BackendInfo:
    """Information about an available LLM backend"""
    name: str
    priority: int
    url_scheme: str
    description: str
    requirements: List[str]
    platform_optimized: bool = False
    gpu_accelerated: bool = False
    apple_silicon_optimized: bool = False


class SmartBackendSelector:
    """
    Simplified backend selector for remote APIs only.
    Removed all local model loading, transformers, llama-cpp-python, etc.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_available_backends(self) -> List[BackendInfo]:
        """Get list of available backends (remote APIs only)"""
        backends = []

        # Priority 1: OpenAI API (Primary choice)
        if os.getenv("OPENAI_API_KEY"):
            backends.append(
                BackendInfo(
                    name="OpenAI",
                    priority=1,
                    url_scheme="https://api.openai.com",
                    description="OpenAI API with GPT models",
                    requirements=["OPENAI_API_KEY"],
                    platform_optimized=True,
                    gpu_accelerated=True,
                )
            )

        # Priority 2: Anthropic Claude API
        if os.getenv("ANTHROPIC_API_KEY"):
            backends.append(
                BackendInfo(
                    name="Anthropic",
                    priority=2,
                    url_scheme="https://api.anthropic.com",
                    description="Anthropic Claude API",
                    requirements=["ANTHROPIC_API_KEY"],
                    platform_optimized=True,
                    gpu_accelerated=True,
                )
            )

        # Additional remote API endpoints can be added here
        # No local model backends - WhisperEngine uses remote APIs only

        return sorted(backends, key=lambda x: x.priority)

    def get_optimal_backend(
        self, prefer_local: bool = False, require_gpu: bool = False
    ) -> Optional[BackendInfo]:
        """Get the optimal backend (remote APIs only)"""
        
        candidates = self.get_available_backends()
        
        if not candidates:
            self.logger.error("❌ No LLM backends available - check API keys")
            return None

        # Since we only use remote APIs, just return the highest priority
        optimal = candidates[0]
        self.logger.info(f"🌐 Selected remote API backend: {optimal.name}")
        return optimal

    def validate_backend(self, backend: BackendInfo) -> bool:
        """Validate that a backend is properly configured"""
        if backend.name == "OpenAI":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif backend.name == "Anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        
        return False

    def get_backend_status(self) -> dict:
        """Get status of all backends"""
        backends = self.get_available_backends()
        status = {}
        
        for backend in backends:
            status[backend.name] = {
                "available": True,
                "configured": self.validate_backend(backend),
                "type": "remote_api",
                "requirements_met": self.validate_backend(backend)
            }
        
        return status