#!/usr/bin/env python3
"""
ChromaDB Performance Monitor
Detects GPU availability and provides performance recommendations for embedding generation.
"""

import os
import sys
import platform
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class ChromaDBPerformanceMonitor:
    """Monitor ChromaDB container performance and GPU availability"""

    def __init__(self):
        self.system_info = self._get_system_info()
        self.docker_available = self._check_docker_available()

    def _get_system_info(self) -> Dict[str, Any]:
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
                ["docker", "--version"], capture_output=True, text=True, timeout=5
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
                with open("/proc/1/cgroup", "r") as f:
                    content = f.read()
                    return "docker" in content or "containerd" in content
            except (FileNotFoundError, PermissionError):
                pass

            return False
        except Exception:
            return False

    def _check_external_embedding_configured(self) -> bool:
        """Check if external embedding API is configured"""
        from src.utils.embedding_manager import is_external_embedding_configured

        return is_external_embedding_configured()

    def _check_container_gpu_access(self) -> Dict[str, Any]:
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

    def _estimate_embedding_performance(self) -> Dict[str, Any]:
        """Estimate embedding performance based on system configuration"""
        # These are rough estimates based on typical performance
        performance_estimates = {
            "macos_arm64_cpu": {
                "tokens_per_second": 500,  # M1/M2 CPU is decent
                "warning_threshold": 1000,  # Warn if processing >1000 tokens
                "recommendation": "Consider external embedding API for better performance",
            },
            "macos_x86_cpu": {
                "tokens_per_second": 200,  # Intel Mac CPU slower
                "warning_threshold": 500,
                "recommendation": "Strongly recommend external embedding API",
            },
            "linux_gpu": {
                "tokens_per_second": 5000,  # GPU acceleration
                "warning_threshold": 10000,
                "recommendation": "GPU acceleration available - good performance expected",
            },
            "linux_cpu": {
                "tokens_per_second": 800,  # Linux CPU generally faster
                "warning_threshold": 2000,
                "recommendation": "Consider external embedding API for heavy usage",
            },
            "windows_gpu": {
                "tokens_per_second": 4500,  # Windows GPU
                "warning_threshold": 10000,
                "recommendation": "GPU acceleration available - good performance expected",
            },
            "windows_cpu": {
                "tokens_per_second": 600,  # Windows CPU
                "warning_threshold": 1500,
                "recommendation": "Consider external embedding API for heavy usage",
            },
        }

        # Determine configuration key
        gpu_info = self._check_container_gpu_access()

        if self.system_info["is_macos"]:
            if self.system_info["is_arm64"]:
                key = "macos_arm64_cpu"  # macOS Docker never has GPU
            else:
                key = "macos_x86_cpu"
        elif self.system_info["is_linux"]:
            key = "linux_gpu" if gpu_info["available"] else "linux_cpu"
        elif self.system_info["is_windows"]:
            key = "windows_gpu" if gpu_info["available"] else "windows_cpu"
        else:
            key = "linux_cpu"  # Default fallback

        return performance_estimates[key]

    async def benchmark_embedding_performance(self, test_duration: float = 5.0) -> Dict[str, Any]:
        """Benchmark actual embedding performance"""
        try:
            from src.utils.embedding_manager import embedding_manager

            # Test texts of varying lengths
            test_texts = [
                "Short test.",
                "This is a medium length test sentence with more words.",
                "This is a longer test sentence that contains significantly more words and should take more time to process through the embedding system to get a better sense of performance characteristics.",
                " ".join(["Performance"] * 50),  # Very long text
            ]

            start_time = time.time()
            embeddings_generated = 0

            # Run benchmark for specified duration
            while time.time() - start_time < test_duration:
                try:
                    embeddings = await embedding_manager.get_embeddings(test_texts)
                    if embeddings:
                        embeddings_generated += len(test_texts)
                except Exception as e:
                    logger.error(f"Embedding benchmark error: {e}")
                    break

            elapsed_time = time.time() - start_time
            embeddings_per_second = embeddings_generated / elapsed_time if elapsed_time > 0 else 0

            return {
                "embeddings_per_second": embeddings_per_second,
                "total_embeddings": embeddings_generated,
                "duration": elapsed_time,
                "service": "external" if embedding_manager.use_external else "local_chromadb",
            }

        except ImportError:
            return {"error": "Embedding manager not available for benchmarking"}
        except Exception as e:
            return {"error": f"Benchmark failed: {e}"}

    def get_performance_recommendations(self) -> Dict[str, Any]:
        """Get performance recommendations based on system analysis"""
        gpu_info = self._check_container_gpu_access()
        performance_est = self._estimate_embedding_performance()

        warnings = []
        recommendations = []

        # Check conditions where we should suppress warnings
        running_in_container = self._check_running_in_container()
        external_embedding_configured = self._check_external_embedding_configured()
        chromadb_container_running = self._check_chromadb_container_running()

        # Only show warnings if:
        # 1. Service is NOT running in a container AND
        # 2. External embedding API is NOT configured AND
        # 3. ChromaDB container is running (indicating we're using local ChromaDB)
        should_show_warnings = (
            not running_in_container
            and not external_embedding_configured
            and chromadb_container_running
        )

        # macOS specific warnings (only if conditions are met)
        if self.system_info["is_macos"] and should_show_warnings:
            warnings.append("⚠️  macOS Docker containers cannot access GPU acceleration")
            warnings.append("⚠️  ChromaDB embeddings will run on CPU only, which can be slow")
            if self.system_info["is_arm64"]:
                recommendations.append(
                    "✅ Apple Silicon CPU provides decent performance for small workloads"
                )
            recommendations.append(
                "🚀 Consider using external embedding API (LM Studio/Ollama) for better performance"
            )

        # GPU availability warnings (only if conditions are met)
        if not gpu_info["available"] and not self.system_info["is_macos"] and should_show_warnings:
            warnings.append(f"⚠️  No GPU detected in ChromaDB container: {gpu_info['reason']}")
            recommendations.append("🔧 Consider configuring GPU access for ChromaDB container")

        # Performance-based recommendations (only if conditions are met)
        if performance_est["tokens_per_second"] < 1000 and should_show_warnings:
            warnings.append(
                f"⚠️  Estimated performance: {performance_est['tokens_per_second']} tokens/sec (slow)"
            )
            recommendations.append(
                "🚀 Strongly recommend external embedding API for production use"
            )

        return {
            "system_info": self.system_info,
            "gpu_info": gpu_info,
            "performance_estimate": performance_est,
            "warnings": warnings,
            "recommendations": recommendations,
            "external_embedding_recommended": len(warnings) > 0
            or performance_est["tokens_per_second"] < 1000,
            "running_in_container": running_in_container,
            "external_embedding_configured": external_embedding_configured,
            "chromadb_container_running": chromadb_container_running,
            "should_show_warnings": should_show_warnings,
        }


# Global instance
performance_monitor = ChromaDBPerformanceMonitor()


async def check_chromadb_performance() -> Dict[str, Any]:
    """Convenience function to check ChromaDB performance"""
    return performance_monitor.get_performance_recommendations()


def check_chromadb_performance_sync() -> Dict[str, Any]:
    """Synchronous version of performance check"""
    return performance_monitor.get_performance_recommendations()
