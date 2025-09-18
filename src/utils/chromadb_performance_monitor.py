#!/usr/bin/env python3
"""
ChromaDB Performance Monitor (Local Embeddings Focus)

Purpose:
    Provide simple, actionable guidance for optimizing local embedding generation now that
    the system uses a single unified local embedding model (no external embedding API toggle).

What this module does NOT do anymore:
    - Recommend switching to external embedding APIs
    - Check deprecated USE_EXTERNAL_EMBEDDINGS or external embedding URLs

Key optimizations surfaced:
    - Batch sizing (LLM_EMBEDDING_BATCH_SIZE)
    - Concurrency limits (EMBEDDING_MAX_CONCURRENT)
    - Retry / backoff indicators
    - Hardware capability (CPU vs potential GPU inside container)

Historical Note:
    External embedding configuration was deprecated in September 2025 in favor of a
    single consistent local model to reduce complexity and eliminate dimension mismatch risk.
"""

import logging
import os
import platform
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)


class ChromaDBPerformanceMonitor:
    """Monitor ChromaDB container performance and GPU availability"""

    def __init__(self):
        self.system_info = self._get_system_info()
        self.docker_available = self._check_docker_available()

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.system(),
            "machine": platform.machine(),
            "release": platform.release(),
            "is_macos": platform.system() == "Darwin",
            "is_linux": platform.system() == "Linux",
            "is_windows": platform.system() == "Windows",
            "is_arm64": platform.machine() in ["arm64", "aarch64"],
            "is_x86_64": platform.machine() in ["x86_64", "AMD64"],
        }

    def _check_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5, check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_chromadb_container_running(self) -> bool:
        """Check if ChromaDB container is running"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=whisperengine-chromadb",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0 and "Up" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_running_in_container(self) -> bool:
        """Check if the current process is running inside a Docker container"""
        try:
            # Check for .dockerenv file (common Docker indicator)
            if os.path.exists("/.dockerenv"):
                return True

            # Check cgroup (another indicator)
            try:
                with open("/proc/1/cgroup", encoding="utf-8") as f:
                    content = f.read()
                    return "docker" in content or "containerd" in content
            except (FileNotFoundError, PermissionError):
                pass

            return False
        except OSError:
            return False

    def _deprecated_external_embedding_indicator(self) -> bool:
        """Return True if legacy external embedding env vars are still present (for warning)."""
        legacy_vars = [
            "LLM_EMBEDDING_API_URL",
            "LLM_EMBEDDING_MODEL",
            "USE_EXTERNAL_EMBEDDINGS",
            "EMBEDDING_API_URL",
        ]
        return any(os.getenv(v) for v in legacy_vars)

    def _check_container_gpu_access(self) -> dict[str, Any]:
        """Check if ChromaDB container has GPU access"""
        if not self._check_chromadb_container_running():
            return {"available": False, "reason": "ChromaDB container not running"}

        try:
            # Check if container was started with GPU access
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "whisperengine-chromadb",
                    "--format",
                    "{{.HostConfig.DeviceRequests}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            has_gpu_request = (
                result.returncode == 0
                and result.stdout.strip() != "[]"
                and result.stdout.strip() != ""
            )

            if has_gpu_request:
                # Try to detect GPU inside container
                gpu_test = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "whisperengine-chromadb",
                        "sh",
                        "-c",
                        "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'no-gpu'",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                if gpu_test.returncode == 0 and "no-gpu" not in gpu_test.stdout.lower():
                    return {
                        "available": True,
                        "gpu_info": gpu_test.stdout.strip(),
                        "reason": "GPU detected in container",
                    }

            return {"available": False, "reason": "No GPU access configured for container"}

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return {"available": False, "reason": "Unable to check container GPU access"}

    def _estimate_embedding_performance(self) -> dict[str, Any]:
        """Estimate local embedding throughput class (coarse heuristic)."""
        gpu_info = self._check_container_gpu_access()
        if self.system_info["is_macos"] and self.system_info["is_arm64"]:
            return {
                "class": "macos_arm64_cpu",
                "approx_embeddings_per_second": 55,
                "note": "Apple Silicon CPU baseline (no container GPU).",
            }
        if self.system_info["is_macos"]:
            return {
                "class": "macos_intel_cpu",
                "approx_embeddings_per_second": 25,
                "note": "Older Intel Mac; expect slower throughput.",
            }
        if self.system_info["is_linux"] and gpu_info["available"]:
            return {
                "class": "linux_gpu",
                "approx_embeddings_per_second": 400,
                "note": "Container GPU detected; good scaling potential.",
            }
        if self.system_info["is_linux"]:
            return {
                "class": "linux_cpu",
                "approx_embeddings_per_second": 80,
                "note": "General Linux CPU baseline.",
            }
        if self.system_info["is_windows"] and gpu_info["available"]:
            return {
                "class": "windows_gpu",
                "approx_embeddings_per_second": 300,
                "note": "Windows GPU path; ensure drivers are stable.",
            }
        if self.system_info["is_windows"]:
            return {
                "class": "windows_cpu",
                "approx_embeddings_per_second": 50,
                "note": "Windows CPU baseline.",
            }
        return {
            "class": "generic_cpu",
            "approx_embeddings_per_second": 60,
            "note": "Fallback heuristic.",
        }

    async def benchmark_embedding_performance(self, test_duration: float = 5.0) -> dict[str, Any]:
        """Benchmark actual embedding performance"""
        try:
            from src.utils.embedding_manager import embedding_manager
        except ImportError:
            return {"error": "Embedding manager not available for benchmarking"}

        test_texts = [
            "Short test.",
            "This is a medium length test sentence with more words.",
            "This is a longer test sentence that contains significantly more words and should take more time to process through the embedding system to get a better sense of performance characteristics.",
            " ".join(["Performance"] * 50),  # Very long text
        ]

        start_time = time.time()
        embeddings_generated = 0

        try:
            while time.time() - start_time < test_duration:
                embeddings = await embedding_manager.get_embeddings(test_texts)
                if embeddings:
                    embeddings_generated += len(test_texts)
        except Exception as e:  # Runtime benchmark failure
            logger.error("Embedding benchmark error: %s", e)
            return {"error": str(e)}

        elapsed_time = time.time() - start_time
        embeddings_per_second = embeddings_generated / elapsed_time if elapsed_time > 0 else 0

        return {
            "embeddings_per_second": embeddings_per_second,
            "total_embeddings": embeddings_generated,
            "duration": elapsed_time,
            "service": "local",
        }

    def get_performance_recommendations(self) -> dict[str, Any]:
        """Get performance recommendations based on system analysis"""
        gpu_info = self._check_container_gpu_access()
        performance_est = self._estimate_embedding_performance()

        warnings = []
        recommendations = []

        # Check conditions where we should suppress warnings
        running_in_container = self._check_running_in_container()
        legacy_external_detected = self._deprecated_external_embedding_indicator()
        chromadb_container_running = self._check_chromadb_container_running()

        # Show warnings primarily when running locally with container ChromaDB active
        should_show_warnings = (
            not running_in_container and chromadb_container_running
        )

        # macOS informational notes
        if self.system_info["is_macos"] and should_show_warnings:
            warnings.append("macOS containers have no GPU access; embeddings run on CPU.")
            if self.system_info["is_arm64"]:
                recommendations.append(
                    "Apple Silicon is usually sufficient for moderate conversational workloads."
                )
            else:
                recommendations.append(
                    "Older Intel Mac detected; consider reducing concurrency or using a Linux host for heavier loads."
                )

        # GPU absence info (non-macOS)
        if not gpu_info["available"] and not self.system_info["is_macos"] and should_show_warnings:
            warnings.append(f"No GPU detected in ChromaDB container: {gpu_info['reason']}")
            recommendations.append(
                "If high throughput is required, run ChromaDB on a GPU-enabled Linux host."
            )

        # Concurrency & batching optimization tips (always relevant)
        recommendations.append(
            "Tune LLM_EMBEDDING_BATCH_SIZE for larger batches (trade memory for throughput)."
        )
        recommendations.append(
            "Adjust EMBEDDING_MAX_CONCURRENT to avoid CPU contention (start 2-4 on CPU)."
        )
        recommendations.append(
            "Warm the embedding cache at startup for popular system prompts or frequent phrases."
        )
        recommendations.append(
            "Monitor average embedding latency; if outliers grow, reduce concurrency."
        )

        if legacy_external_detected:
            warnings.append(
                "Legacy external embedding environment variables detected (ignored by current system)."
            )
            recommendations.append(
                "Remove deprecated LLM_EMBEDDING_API_URL / USE_EXTERNAL_EMBEDDINGS vars from your .env."
            )

        return {
            "system_info": self.system_info,
            "gpu_info": gpu_info,
            "performance_estimate": performance_est,
            "warnings": warnings,
            "recommendations": recommendations,
            "legacy_external_vars_detected": legacy_external_detected,
            "running_in_container": running_in_container,
            "chromadb_container_running": chromadb_container_running,
            "should_show_warnings": should_show_warnings,
        }


# Global instance
performance_monitor = ChromaDBPerformanceMonitor()


async def check_chromadb_performance() -> dict[str, Any]:
    """Convenience function to check ChromaDB performance"""
    return performance_monitor.get_performance_recommendations()


def check_chromadb_performance_sync() -> dict[str, Any]:
    """Synchronous version of performance check"""
    return performance_monitor.get_performance_recommendations()
