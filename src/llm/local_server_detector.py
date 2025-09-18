#!/usr/bin/env python3
"""
Local LLM Server Detection and Setup Assistant
Automatically detects and configures local LLM servers (LM Studio, Ollama, etc.)
for seamless WhisperEngine integration.
"""

import asyncio
import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Any

import aiohttp
import psutil

logger = logging.getLogger(__name__)


@dataclass
class ServerInfo:
    """Information about a detected LLM server"""

    name: str
    url: str
    status: str  # 'available', 'no_models', 'unreachable'
    models: list[str]
    recommended: bool = False
    setup_required: bool = False
    error_message: str | None = None


@dataclass
class SetupRecommendation:
    """Recommended setup based on system resources"""

    preferred_server: str
    recommended_models: list[str]
    setup_url: str
    memory_note: str
    installation_steps: list[str]


@dataclass
class ResourceInfo:
    """System resource information"""

    memory_gb: float
    cpu_cores: int
    gpu_available: bool
    platform: str = "Unknown"
    architecture: str = "Unknown"
    apple_silicon: bool = False
    mlx_available: bool = False
    platform: str
    architecture: str


class LocalLLMDetector:
    """Automatically detect and configure local LLM servers"""

    def __init__(self):
        self.timeout = 5.0  # Connection timeout in seconds
        self.detected_servers = {}

    async def detect_available_servers(self) -> dict[str, ServerInfo]:
        """Scan for LM Studio, Ollama, and other local servers"""
        servers = {}

        # Test common local LLM server endpoints
        server_configs = [
            {
                "name": "LM Studio",
                "url": "http://localhost:1234/v1",
                "health_endpoint": "/models",
                "process_names": ["LM Studio", "lmstudio"],
            },
            {
                "name": "Ollama",
                "url": "http://localhost:11434/v1",
                "health_endpoint": "/models",
                "process_names": ["ollama"],
            },
            {
                "name": "text-generation-webui",
                "url": "http://localhost:5000/v1",
                "health_endpoint": "/models",
                "process_names": ["text-generation-webui", "gradio"],
            },
        ]

        # Test each server configuration
        for config in server_configs:
            logger.debug(f"Testing {config['name']} at {config['url']}")
            server_info = await self._test_server(config)
            servers[config["name"].lower().replace(" ", "_")] = server_info

        self.detected_servers = servers
        return servers

    async def _test_server(self, config: dict[str, Any]) -> ServerInfo:
        """Test if a specific server is available and get its models"""
        name = config["name"]
        url = config["url"]
        health_endpoint = config.get("health_endpoint", "/models")

        try:
            # First check if process is running
            process_running = self._is_process_running(config.get("process_names", []))

            # Test HTTP connection
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                try:
                    async with session.get(f"{url}{health_endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            models = self._extract_models(data, name)

                            if models:
                                logger.info(f"✅ {name} detected with {len(models)} models")
                                return ServerInfo(
                                    name=name,
                                    url=url,
                                    status="available",
                                    models=models,
                                    recommended=True,
                                )
                            else:
                                logger.info(f"⚠️ {name} running but no models loaded")
                                return ServerInfo(
                                    name=name,
                                    url=url,
                                    status="no_models",
                                    models=[],
                                    setup_required=True,
                                    error_message="Server running but no models loaded",
                                )
                        else:
                            logger.debug(f"❌ {name} HTTP error: {response.status}")
                            return ServerInfo(
                                name=name,
                                url=url,
                                status="unreachable",
                                models=[],
                                error_message=f"HTTP error: {response.status}",
                            )

                except aiohttp.ClientError as e:
                    logger.debug(f"❌ {name} connection failed: {e}")

                    # If process is running but HTTP fails, it might be starting up
                    if process_running:
                        return ServerInfo(
                            name=name,
                            url=url,
                            status="starting",
                            models=[],
                            setup_required=True,
                            error_message="Process running but HTTP not responding (may be starting up)",
                        )
                    else:
                        return ServerInfo(
                            name=name,
                            url=url,
                            status="unreachable",
                            models=[],
                            setup_required=True,
                            error_message=f"Connection failed: {str(e)}",
                        )

        except Exception as e:
            logger.debug(f"❌ {name} detection error: {e}")
            return ServerInfo(
                name=name,
                url=url,
                status="unreachable",
                models=[],
                setup_required=True,
                error_message=f"Detection error: {str(e)}",
            )

    def _is_process_running(self, process_names: list[str]) -> bool:
        """Check if any of the given process names are running"""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    proc_name = proc_info.get("name", "").lower()
                    cmdline = " ".join(proc_info.get("cmdline", [])).lower()

                    for target_name in process_names:
                        if target_name.lower() in proc_name or target_name.lower() in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.debug(f"Process detection error: {e}")
            return False

    def _extract_models(self, response_data: dict[str, Any], server_name: str) -> list[str]:
        """Extract model names from server response"""
        models = []

        try:
            # Handle different response formats
            if "data" in response_data:
                # OpenAI-compatible format
                for model in response_data["data"]:
                    if isinstance(model, dict) and "id" in model:
                        models.append(model["id"])
                    elif isinstance(model, str):
                        models.append(model)
            elif "models" in response_data:
                # Alternative format
                for model in response_data["models"]:
                    if isinstance(model, dict) and "name" in model:
                        models.append(model["name"])
                    elif isinstance(model, str):
                        models.append(model)
            elif isinstance(response_data, list):
                # Direct list format
                for model in response_data:
                    if isinstance(model, dict) and "id" in model:
                        models.append(model["id"])
                    elif isinstance(model, str):
                        models.append(model)

            logger.debug(f"{server_name} models: {models}")
            return models

        except Exception as e:
            logger.warning(f"Failed to extract models from {server_name}: {e}")
            return []

    def get_system_resources(self) -> ResourceInfo:
        """Detect system resources for recommendations"""
        try:
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_cores = psutil.cpu_count(logical=True) or 4  # Default to 4 if None
            gpu_available = self._detect_gpu()
            platform_name = platform.system()
            architecture = platform.machine()

            # Check for Apple Silicon
            apple_silicon = platform_name == "Darwin" and architecture == "arm64"

            # Check MLX availability
            mlx_available = self._detect_mlx_availability()

            return ResourceInfo(
                memory_gb=memory_gb,
                cpu_cores=cpu_cores,
                gpu_available=gpu_available,
                platform=platform_name,
                architecture=architecture,
                apple_silicon=apple_silicon,
                mlx_available=mlx_available,
            )
        except Exception as e:
            logger.warning(f"Resource detection failed: {e}")
            return ResourceInfo(
                memory_gb=8.0,  # Conservative default
                cpu_cores=4,
                gpu_available=False,
                platform="Unknown",
                architecture="Unknown",
                apple_silicon=False,
                mlx_available=False,
            )

    def _detect_mlx_availability(self) -> bool:
        """Check if MLX is available on Apple Silicon"""
        # DISABLED: MLX backend not implemented
        # TODO: Re-enable when MLX backend is implemented
        return False
        # try:
        #     # Only available on Apple Silicon
        #     if platform.system() != "Darwin" or platform.machine() != "arm64":
        #         return False
        # 
        #     # Try to import MLX
        #     import mlx.core  # type: ignore
        #     from mlx_lm import load  # type: ignore
        # 
        #     return True
        # except ImportError:
        #     return False

    def _detect_gpu(self) -> bool:
        """Detect GPU availability"""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        try:
            # Check for Apple Metal on macOS
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "Apple" in result.stdout and (
                    "M1" in result.stdout or "M2" in result.stdout or "M3" in result.stdout
                ):
                    return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False

    def get_setup_recommendation(self, resources: ResourceInfo) -> SetupRecommendation:
        """Provide setup recommendations based on system resources"""

        # Apple Silicon with MLX gets special treatment
        if resources.apple_silicon and resources.mlx_available:
            if resources.memory_gb >= 16:
                return SetupRecommendation(
                    preferred_server="MLX (Apple Silicon Optimized)",
                    recommended_models=["llama-3.1-8b-instruct-mlx", "mistral-7b-instruct-mlx"],
                    setup_url="https://github.com/ml-explore/mlx-examples",
                    memory_note="🍎 MLX provides optimal performance on Apple Silicon with unified memory",
                    installation_steps=[
                        "1. MLX is already installed and detected",
                        "2. Download MLX-optimized models to ./models/mlx/",
                        "3. Use: python -m mlx_lm.convert --hf-path <model> --mlx-path ./models/mlx/<model>",
                        "4. MLX models will be automatically preferred on Apple Silicon",
                        "5. Fallback to Ollama/LM Studio if MLX models unavailable",
                    ],
                )
            else:
                return SetupRecommendation(
                    preferred_server="MLX + Ollama (Hybrid)",
                    recommended_models=["llama3.2:3b", "phi3:mini"],
                    setup_url="https://ollama.ai/",
                    memory_note="🍎 MLX preferred for local models, Ollama for convenience",
                    installation_steps=[
                        "1. MLX detected for optimal Apple Silicon performance",
                        "2. Install Ollama as backup: brew install ollama",
                        "3. Start Ollama: ollama serve",
                        "4. Pull model: ollama pull llama3.2:3b",
                        "5. WhisperEngine will prefer MLX when models available",
                    ],
                )

        # Apple Silicon without MLX
        elif resources.apple_silicon:
            return SetupRecommendation(
                preferred_server="LM Studio (Apple Silicon)",
                recommended_models=["llama-3.1-8b-instruct", "mistral-7b-instruct"],
                setup_url="https://lmstudio.ai/",
                memory_note="🍎 LM Studio optimized for Apple Silicon with Metal acceleration",
                installation_steps=[
                    "1. Download LM Studio from https://lmstudio.ai/",
                    "2. Install and launch LM Studio (Apple Silicon native)",
                    "3. Browse models and download Apple Silicon optimized models",
                    "4. Enable Metal GPU acceleration in settings",
                    "5. Start the local server (click 'Start Server' tab)",
                    # MLX disabled until backend implementation is complete
                    # "6. Optional: Install MLX for even better performance: pip install mlx-lm",
                ],
            )

        # High-end systems
        elif resources.memory_gb >= 32 and resources.gpu_available:
            return SetupRecommendation(
                preferred_server="LM Studio",
                recommended_models=["llama-3.1-8b-instruct", "mistral-7b-instruct", "codellama-7b"],
                setup_url="https://lmstudio.ai/",
                memory_note="Your system can handle larger models (7B-13B) with good performance",
                installation_steps=[
                    "1. Download LM Studio from https://lmstudio.ai/",
                    "2. Install and launch LM Studio",
                    "3. Browse models and download Llama 3.1 8B Instruct",
                    "4. Start the local server (click 'Start Server' tab)",
                    "5. Verify it's running on port 1234",
                    "6. Return to WhisperEngine - it will auto-detect the server",
                ],
            )
        elif resources.memory_gb >= 16:
            return SetupRecommendation(
                preferred_server="LM Studio",
                recommended_models=["llama-3.2-3b-instruct", "phi-3-mini", "mistral-7b-instruct"],
                setup_url="https://lmstudio.ai/",
                memory_note="Recommend 3B-7B models for optimal performance on your system",
                installation_steps=[
                    "1. Download LM Studio from https://lmstudio.ai/",
                    "2. Install and launch LM Studio",
                    "3. Browse models and download Llama 3.2 3B Instruct (smaller, faster)",
                    "4. Start the local server (click 'Start Server' tab)",
                    "5. Verify it's running on port 1234",
                    "6. Return to WhisperEngine - it will auto-detect the server",
                ],
            )
        elif resources.memory_gb >= 8:
            return SetupRecommendation(
                preferred_server="Ollama",
                recommended_models=["llama3.2:3b", "phi3:mini", "qwen2:1.5b"],
                setup_url="https://ollama.ai/",
                memory_note="Recommend smaller models (1.5B-3B) for your system constraints",
                installation_steps=[
                    "1. Download Ollama from https://ollama.ai/",
                    "2. Install Ollama (command-line tool)",
                    "3. Run: ollama pull llama3.2:3b",
                    "4. Run: ollama serve (starts server on port 11434)",
                    "5. Test with: ollama run llama3.2:3b",
                    "6. Return to WhisperEngine - it will auto-detect the server",
                ],
            )
        else:
            return SetupRecommendation(
                preferred_server="Cloud API",
                recommended_models=["Via OpenRouter"],
                setup_url="https://openrouter.ai/",
                memory_note="Your system may struggle with local models - cloud API recommended",
                installation_steps=[
                    "1. Sign up at https://openrouter.ai/",
                    "2. Get your API key from the dashboard",
                    "3. Set LLM_CHAT_API_URL=https://openrouter.ai/api/v1",
                    "4. Set LLM_CHAT_API_KEY=your_api_key_here",
                    "5. Choose a model like meta-llama/llama-3.1-8b-instruct",
                    "6. Restart WhisperEngine",
                ],
            )

    async def auto_configure_llm(self) -> dict[str, Any]:
        """Automatically detect and configure the best available LLM"""
        logger.info("🔍 Auto-detecting local LLM servers...")

        # Detect system resources
        resources = self.get_system_resources()
        logger.info(
            f"💻 System: {resources.memory_gb:.1f}GB RAM, {resources.cpu_cores} cores, GPU: {resources.gpu_available}"
        )

        # Detect available servers
        servers = await self.detect_available_servers()

        # Find best available server
        available_servers = [s for s in servers.values() if s.status == "available"]

        result = {
            "servers_detected": servers,
            "system_resources": resources,
            "configuration_applied": False,
            "recommended_action": None,
        }

        if available_servers:
            # Use the first available server (priority: LM Studio, Ollama, others)
            best_server = None
            for preference in ["LM Studio", "Ollama", "text-generation-webui"]:
                for server in available_servers:
                    if server.name == preference:
                        best_server = server
                        break
                if best_server:
                    break

            if not best_server:
                best_server = available_servers[0]

            logger.info(f"✅ Using {best_server.name} at {best_server.url}")
            logger.info(
                f"📊 Available models: {', '.join(best_server.models[:3])}{'...' if len(best_server.models) > 3 else ''}"
            )

            result["configuration_applied"] = True
            result["selected_server"] = best_server
            result["recommended_action"] = "ready"

        else:
            # No servers available - provide setup guidance
            recommendation = self.get_setup_recommendation(resources)
            logger.info("⚠️ No local LLM servers detected")
            logger.info(f"💡 Recommended: {recommendation.preferred_server}")

            result["setup_recommendation"] = recommendation
            result["recommended_action"] = "setup_required"

        return result


# Factory function for easy integration
async def detect_and_configure_local_llm() -> dict[str, Any]:
    """Convenience function to detect and configure local LLM"""
    detector = LocalLLMDetector()
    return await detector.auto_configure_llm()


# Sync wrapper for environments that need it
def detect_local_llm_sync() -> dict[str, Any]:
    """Synchronous wrapper for local LLM detection"""
    return asyncio.run(detect_and_configure_local_llm())
