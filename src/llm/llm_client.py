"""
Generic LLM Client for interacting with various LLM providers via HTTP API
Supports: LM Studio, OpenRouter, Ollama, and other OpenAI-compatible APIs
SECURITY ENHANCED: Includes API key validation and secure credential handling
"""

import json
import logging
import os
import re
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.exceptions import LLMConnectionError, LLMError, LLMRateLimitError, LLMTimeoutError
from src.utils.performance_monitor import monitor_performance


class LLMClient:
    """Generic client for connecting to various LLM services via HTTP API

    Supports multiple providers:
    - LM Studio (local server)
    - OpenRouter (cloud API)
    - Ollama (local server)
    - Any OpenAI-compatible API endpoint
    """

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        """
        Initialize the LLM client

        Args:
            api_url: URL of the LLM API (from environment if not provided)
            api_key: API key for services like OpenRouter (from environment if not provided)
        """
        # SECURITY ENHANCEMENT: Import API key security manager
        try:
            from src.security.api_key_security import APIKeyType, get_api_key_manager

            self.api_key_manager = get_api_key_manager()
        except ImportError:
            self.api_key_manager = None
            logging.warning("API key security module not available - using basic validation")

        # Load configuration from environment variables
        self.api_url = api_url or os.getenv("LLM_CHAT_API_URL", "http://localhost:1234/v1")
        raw_api_key = api_key or os.getenv("LLM_CHAT_API_KEY")

        # SECURITY ENHANCEMENT: Validate API key before using
        if raw_api_key and self.api_key_manager:
            key_info = self.api_key_manager.validate_api_key(raw_api_key, APIKeyType.OPENROUTER)
            if key_info.is_valid:
                self.api_key = raw_api_key
                logging.debug(f"Main API key validated: {key_info.masked_key}")
            else:
                self.api_key = None
                logging.error(
                    f"Invalid main API key rejected: {key_info.masked_key} - Threats: {[t.value for t in key_info.security_threats]}"
                )
        else:
            self.api_key = raw_api_key  # Fallback to basic handling

        # Load separate endpoint for emotion analysis
        self.emotion_api_url = os.getenv("LLM_EMOTION_API_URL")
        raw_emotion_key = os.getenv("LLM_EMOTION_API_KEY")

        # SECURITY ENHANCEMENT: Validate emotion API key
        if raw_emotion_key and self.api_key_manager:
            key_info = self.api_key_manager.validate_api_key(
                raw_emotion_key, APIKeyType.LLM_SENTIMENT
            )
            if key_info.is_valid:
                self.emotion_api_key = raw_emotion_key
                logging.debug(f"Emotion API key validated: {key_info.masked_key}")
            else:
                self.emotion_api_key = None
                logging.error(
                    f"Invalid emotion API key rejected: {key_info.masked_key} - Threats: {[t.value for t in key_info.security_threats]}"
                )
        else:
            self.emotion_api_key = raw_emotion_key  # Fallback

        # Load separate endpoint for facts analysis
        self.facts_api_url = os.getenv("LLM_FACTS_API_URL")
        raw_facts_key = os.getenv("LLM_FACTS_API_KEY")

        # SECURITY ENHANCEMENT: Validate facts API key
        if raw_facts_key and self.api_key_manager:
            key_info = self.api_key_manager.validate_api_key(
                raw_facts_key, APIKeyType.LLM_SENTIMENT
            )
            if key_info.is_valid:
                self.facts_api_key = raw_facts_key
                logging.debug(f"Facts API key validated: {key_info.masked_key}")
            else:
                self.facts_api_key = None
                logging.error(
                    f"Invalid facts API key rejected: {key_info.masked_key} - Threats: {[t.value for t in key_info.security_threats]}"
                )
        else:
            self.facts_api_key = raw_facts_key  # Fallback

        # Determine service type based on URL
        self.is_openrouter = "openrouter.ai" in self.api_url
        self.is_ollama = "11434" in self.api_url or "ollama" in self.api_url.lower()
        self.is_local_studio = self.api_url.startswith(
            "http://localhost:1234"
        ) or self.api_url.startswith("http://127.0.0.1:1234")
        self.is_local_llm = self.api_url.startswith("local://")
        self.is_llamacpp = self.api_url.startswith("llamacpp://")

        # Determine service name for logging and display
        if self.is_openrouter:
            self.service_name = "OpenRouter"
        elif self.is_ollama:
            self.service_name = "Ollama"
        elif self.is_local_studio:
            self.service_name = "LM Studio"
        elif self.is_local_llm:
            self.service_name = "Local Bundled LLM"
        elif self.is_llamacpp:
            self.service_name = "llama-cpp-python"
        else:
            self.service_name = "Custom LLM API"

        # Determine emotion service type
        if self.emotion_api_url:
            self.emotion_is_openrouter = "openrouter.ai" in self.emotion_api_url
            self.emotion_is_ollama = (
                "11434" in self.emotion_api_url or "ollama" in self.emotion_api_url.lower()
            )
            self.emotion_is_local_studio = self.emotion_api_url.startswith(
                "http://localhost:1234"
            ) or self.emotion_api_url.startswith("http://127.0.0.1:1234")

            if self.emotion_is_openrouter:
                self.emotion_service_name = "OpenRouter"
            elif self.emotion_is_ollama:
                self.emotion_service_name = "Ollama"
            elif self.emotion_is_local_studio:
                self.emotion_service_name = "LM Studio"
            else:
                self.emotion_service_name = "Custom LLM API"
        else:
            self.emotion_is_openrouter = False
            self.emotion_is_ollama = False
            self.emotion_is_local_studio = False
            self.emotion_service_name = "Not Configured"

        # Determine facts service type
        if self.facts_api_url:
            self.facts_is_openrouter = "openrouter.ai" in self.facts_api_url
            self.facts_is_ollama = (
                "11434" in self.facts_api_url or "ollama" in self.facts_api_url.lower()
            )
            self.facts_is_local_studio = self.facts_api_url.startswith(
                "http://localhost:1234"
            ) or self.facts_api_url.startswith("http://127.0.0.1:1234")

            if self.facts_is_openrouter:
                self.facts_service_name = "OpenRouter"
            elif self.facts_is_ollama:
                self.facts_service_name = "Ollama"
            elif self.facts_is_local_studio:
                self.facts_service_name = "LM Studio"
            else:
                self.facts_service_name = "Custom LLM API"
        else:
            self.facts_is_openrouter = False
            self.facts_is_ollama = False
            self.facts_is_local_studio = False
            self.facts_service_name = "Not Configured"

        # Initialize logger early for use in local LLM initialization
        self.logger = logging.getLogger(__name__)

        # Initialize local LLM if using local:// protocol
        self.local_model = None
        self.local_tokenizer = None
        if self.is_local_llm:
            self._initialize_local_llm()

        # Initialize llama-cpp-python if using llamacpp:// protocol
        self.llamacpp_model = None
        if self.is_llamacpp:
            self._initialize_llamacpp_llm()

        self.chat_endpoint = f"{self.api_url}/chat/completions"
        self.completions_endpoint = f"{self.api_url}/completions"
        self.emotion_chat_endpoint = (
            f"{self.emotion_api_url}/chat/completions" if self.emotion_api_url else None
        )
        self.facts_chat_endpoint = (
            f"{self.facts_api_url}/chat/completions" if self.facts_api_url else None
        )

        # Remove duplicate logger initialization that was here before

        # Load token limits from environment variables with sensible defaults
        self.default_max_tokens_chat = int(os.getenv("LLM_MAX_TOKENS_CHAT", "4096"))
        self.default_max_tokens_completion = int(os.getenv("LLM_MAX_TOKENS_COMPLETION", "1024"))

        # Load specific token limits for analysis functions
        self.max_tokens_emotion = int(os.getenv("LLM_MAX_TOKENS_EMOTION", "200"))
        self.max_tokens_fact_extraction = int(os.getenv("LLM_MAX_TOKENS_FACT_EXTRACTION", "500"))
        self.max_tokens_personal_info = int(os.getenv("LLM_MAX_TOKENS_PERSONAL_INFO", "400"))
        self.max_tokens_trust_detection = int(os.getenv("LLM_MAX_TOKENS_TRUST_DETECTION", "300"))
        self.max_tokens_user_facts = int(os.getenv("LLM_MAX_TOKENS_USER_FACTS", "400"))

        # Load model names from environment variables
        self.chat_model_name = os.getenv("LLM_CHAT_MODEL", "local-model")
        self.emotion_model_name = os.getenv("LLM_EMOTION_MODEL", self.chat_model_name)
        self.facts_model_name = os.getenv("LLM_FACTS_MODEL", self.chat_model_name)

        # Legacy compatibility
        self.default_model_name = self.chat_model_name

        # Load timeout configuration from environment variables with sensible defaults
        self.request_timeout = int(
            os.getenv("LLM_REQUEST_TIMEOUT", "90")
        )  # 90 seconds default for Discord bot (LM Studio can be slow)
        self.connection_timeout = int(
            os.getenv("LLM_CONNECTION_TIMEOUT", "10")
        )  # 10 seconds for initial connection

        # Load vision model support configuration
        self.supports_vision = os.getenv("LLM_SUPPORTS_VISION", "false").lower() in (
            "true",
            "1",
            "yes",
            "on",
        )
        self.vision_max_images = int(os.getenv("LLM_VISION_MAX_IMAGES", "5"))

        # Configure session with connection pooling and retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # SECURITY ENHANCEMENT: Use secure logging that masks sensitive information
        if self.api_key_manager:
            log_text = (
                f"Main LLM client initialized - Service: {self.service_name}, URL: {self.api_url}"
            )
            self.logger.debug(self.api_key_manager.sanitize_for_logging(log_text))

            log_text = f"Emotion LLM client - Service: {self.emotion_service_name}, URL: {self.emotion_api_url}"
            self.logger.debug(self.api_key_manager.sanitize_for_logging(log_text))

            log_text = (
                f"Facts LLM client - Service: {self.facts_service_name}, URL: {self.facts_api_url}"
            )
            self.logger.debug(self.api_key_manager.sanitize_for_logging(log_text))

            # Log API key status securely (masked keys only)
            main_key_status = (
                self.api_key_manager.mask_api_key(self.api_key) if self.api_key else "[NOT_SET]"
            )
            emotion_key_status = (
                self.api_key_manager.mask_api_key(self.emotion_api_key)
                if self.emotion_api_key
                else "[NOT_SET]"
            )
            facts_key_status = (
                self.api_key_manager.mask_api_key(self.facts_api_key)
                if self.facts_api_key
                else "[NOT_SET]"
            )
            self.logger.debug(
                f"API keys - Main: {main_key_status}, Emotion: {emotion_key_status}, Facts: {facts_key_status}"
            )
        else:
            # Fallback to basic logging
            self.logger.debug(
                f"Main LLM client initialized - Service: {self.service_name}, URL: {self.api_url}"
            )
            self.logger.debug(
                f"Emotion LLM client - Service: {self.emotion_service_name}, URL: {self.emotion_api_url}"
            )
            self.logger.debug(
                f"Facts LLM client - Service: {self.facts_service_name}, URL: {self.facts_api_url}"
            )
            self.logger.debug(
                f"API keys - Main: {bool(self.api_key)}, Emotion: {bool(self.emotion_api_key)}, Facts: {bool(self.facts_api_key)}"
            )

        self.logger.debug(
            f"Token limits - Chat: {self.default_max_tokens_chat}, Completion: {self.default_max_tokens_completion}"
        )
        self.logger.debug(
            f"Analysis token limits - Emotion: {self.max_tokens_emotion}, Facts: {self.max_tokens_fact_extraction}, Personal: {self.max_tokens_personal_info}, Trust: {self.max_tokens_trust_detection}, UserFacts: {self.max_tokens_user_facts}"
        )
        self.logger.debug(
            f"Timeout settings - Request: {self.request_timeout}s, Connection: {self.connection_timeout}s"
        )
        self.logger.debug(
            f"Vision support: {self.supports_vision}, Max images: {self.vision_max_images}"
        )

    def get_client_config(self) -> dict[str, Any]:
        """Get client configuration for debugging/testing"""
        return {
            "service_name": self.service_name,
            "api_url": self.api_url,
            "is_openrouter": self.is_openrouter,
            "is_ollama": self.is_ollama,
            "is_local_studio": self.is_local_studio,
            "supports_vision": self.supports_vision,
            "chat_model": self.chat_model_name,
            "emotion_model": self.emotion_model_name,
            "facts_model": self.facts_model_name,
            "max_tokens_chat": self.default_max_tokens_chat,
            "request_timeout": self.request_timeout,
        }

    def __del__(self):
        """Clean up session on deletion"""
        if hasattr(self, "session"):
            self.session.close()

    def _initialize_local_llm(self):
        """Initialize local LLM model for offline inference"""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Get model path from environment
            local_model_name = os.getenv("LOCAL_LLM_MODEL", "microsoft_Phi-3-mini-4k-instruct")
            models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
            model_path = os.path.join(models_dir, local_model_name)

            if not os.path.exists(model_path):
                self.logger.warning(
                    f"Local LLM model not found at {model_path}. Please run download_models.py"
                )
                return

            self.logger.info(f"Loading local LLM from {model_path}...")

            # Load tokenizer and model
            self.local_tokenizer = AutoTokenizer.from_pretrained(model_path)

            # Determine the best device for loading
            if torch.cuda.is_available():
                device = "cuda"
                self.logger.info("🔥 CUDA detected - loading model on CUDA")
            elif torch.backends.mps.is_available():
                device = "mps"
                self.logger.info("🍎 MPS (Apple Silicon) detected - loading model on MPS")
            else:
                device = "cpu"
                self.logger.info("💻 No GPU detected - loading model on CPU")

            # Load model and move to device
            self.local_model = AutoModelForCausalLM.from_pretrained(
                model_path, dtype=torch.float32  # Use float32 for better compatibility
            )

            # Move model to the target device
            self.local_model = self.local_model.to(device)
            self.logger.info(f"✅ Model loaded on device: {device}")

            # Ensure we have a pad token
            if self.local_tokenizer.pad_token is None:
                self.local_tokenizer.pad_token = self.local_tokenizer.eos_token

            self.logger.info(f"✅ Local LLM loaded successfully: {local_model_name}")

        except ImportError:
            self.logger.error("transformers or torch not available for local LLM")
        except Exception as e:
            self.logger.error(f"Failed to initialize local LLM: {e}")

    def _initialize_llamacpp_llm(self):
        """Initialize llama-cpp-python for optimized local inference"""
        try:
            from llama_cpp import Llama

            # Get model path from environment
            model_path = os.getenv("LLAMACPP_MODEL_PATH")
            if not model_path:
                # Try to find GGUF models in models directory
                models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
                import glob

                gguf_files = glob.glob(os.path.join(models_dir, "*.gguf"))
                if gguf_files:
                    model_path = gguf_files[0]  # Use first GGUF file found
                    self.logger.info(f"Auto-detected GGUF model: {model_path}")
                else:
                    self.logger.warning(
                        f"No GGUF models found in {models_dir} and LLAMACPP_MODEL_PATH not set"
                    )
                    return

            if not os.path.exists(model_path):
                self.logger.warning(f"llama-cpp-python model not found at {model_path}")
                return

            self.logger.info(f"Loading llama-cpp-python model from {model_path}...")

            # Configure based on available hardware
            n_gpu_layers = 0
            if os.getenv("LLAMACPP_USE_GPU", "auto").lower() == "true":
                n_gpu_layers = -1  # Use all GPU layers
            elif os.getenv("LLAMACPP_USE_GPU", "auto").lower() == "auto":
                # Auto-detect GPU support
                try:
                    import torch

                    if torch.cuda.is_available():
                        n_gpu_layers = -1
                        self.logger.info("🔥 CUDA detected - enabling GPU acceleration")
                    elif torch.backends.mps.is_available():
                        n_gpu_layers = 1  # Use some GPU layers for MPS
                        self.logger.info("🍎 MPS detected - enabling partial GPU acceleration")
                except ImportError:
                    pass  # No torch available, stay on CPU

            # Initialize llama-cpp-python model
            self.llamacpp_model = Llama(
                model_path=model_path,
                n_ctx=int(os.getenv("LLAMACPP_CONTEXT_SIZE", "4096")),
                n_threads=int(os.getenv("LLAMACPP_THREADS", "4")),
                n_gpu_layers=n_gpu_layers,
                verbose=False,
                chat_format="chatml",  # Use ChatML format by default
            )

            self.logger.info("✅ llama-cpp-python model loaded successfully")

        except ImportError:
            self.logger.error(
                "llama-cpp-python not available. Install with: pip install llama-cpp-python"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize llama-cpp-python model: {e}")

    def _generate_local_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate chat completion using local LLM"""
        try:
            import torch

            # Check if models are loaded
            if not self.local_model or not self.local_tokenizer:
                raise RuntimeError("Local LLM models not properly loaded")

            if max_tokens is None:
                max_tokens = self.default_max_tokens_chat

            # Get model name to determine format
            local_model_name = os.getenv("LOCAL_LLM_MODEL", "microsoft_Phi-3-mini-4k-instruct")

            # Use proper chat template for Phi-3 or fallback to DialoGPT format
            if "Phi-3" in local_model_name or "phi-3" in local_model_name:
                # Use Phi-3 chat template if available
                if hasattr(self.local_tokenizer, "apply_chat_template"):
                    prompt_text = self.local_tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                else:
                    # Fallback Phi-3 format
                    prompt_text = ""
                    for message in messages:
                        role = message.get("role", "")
                        content = message.get("content", "")

                        if role == "system":
                            prompt_text += f"<|system|>\n{content}<|end|>\n"
                        elif role == "user":
                            prompt_text += f"<|user|>\n{content}<|end|>\n"
                        elif role == "assistant":
                            prompt_text += f"<|assistant|>\n{content}<|end|>\n"

                    prompt_text += "<|assistant|>\n"
            else:
                # DialoGPT format (legacy)
                prompt_text = ""
                for message in messages:
                    role = message.get("role", "")
                    content = message.get("content", "")

                    if role == "system":
                        prompt_text += f"System: {content}\n"
                    elif role == "user":
                        prompt_text += f"User: {content}\n"
                    elif role == "assistant":
                        prompt_text += f"Assistant: {content}\n"

                # Add the final assistant prompt
                prompt_text += "Assistant:"

            # Tokenize input with proper handling and attention mask
            tokenized = self.local_tokenizer(
                prompt_text,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
                padding=False,
                return_attention_mask=True,
            )
            inputs = tokenized["input_ids"]
            attention_mask = tokenized["attention_mask"]

            # Move inputs to the same device as the model
            model_device = next(self.local_model.parameters()).device
            inputs = inputs.to(model_device)
            attention_mask = attention_mask.to(model_device)

            input_length = inputs.shape[1]

            # Generate response with improved parameters for Phi-3
            with torch.no_grad():
                outputs = self.local_model.generate(
                    inputs,
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,  # Use max_new_tokens instead of max_length for newer models
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=self.local_tokenizer.eos_token_id,
                    eos_token_id=self.local_tokenizer.eos_token_id,
                    repetition_penalty=1.1,  # Better for Phi-3
                    use_cache=True,
                )

            # Decode response
            response_text = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the new generated text
            generated_text = response_text[len(prompt_text) :].strip()

            # Clean up Phi-3 end tokens if present
            if "<|end|>" in generated_text:
                generated_text = generated_text.split("<|end|>")[0].strip()

            # Calculate token usage
            output_length = outputs[0].shape[0] if hasattr(outputs[0], "shape") else len(outputs[0])
            completion_tokens = max(0, output_length - input_length)

            # Format response to match OpenAI API structure
            return {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": generated_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": input_length,
                    "completion_tokens": completion_tokens,
                    "total_tokens": input_length + completion_tokens,
                },
                "model": "local-model",
            }

        except Exception as e:
            self.logger.error(f"Local LLM generation failed: {e}")
            # Fallback to error response
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": f"Sorry, I'm having trouble processing your request. Local LLM error: {str(e)}",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "error": str(e),
            }

    def _generate_llamacpp_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate chat completion using llama-cpp-python"""
        try:
            # Check if model is loaded
            if not self.llamacpp_model:
                raise RuntimeError("llama-cpp-python model not properly loaded")

            if max_tokens is None:
                max_tokens = self.default_max_tokens_chat

            # Use llama-cpp-python's chat completion
            response = self.llamacpp_model.create_chat_completion(
                messages=messages, temperature=temperature, max_tokens=max_tokens, stream=False
            )

            # llama-cpp-python returns OpenAI-compatible format, so we can return it directly
            return response

        except Exception as e:
            self.logger.error(f"llama-cpp-python generation failed: {e}")
            # Fallback to error response in OpenAI format
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": f"Sorry, I'm having trouble processing your request. llama-cpp-python error: {str(e)}",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "error": str(e),
            }

    def check_connection(self) -> bool:
        """Check if the LLM service is running and accessible"""
        try:
            # For local models, check if the model is loaded
            if self.is_local_llm:
                is_connected = self.local_model is not None and self.local_tokenizer is not None
                self.logger.debug(f"Local LLM connection check: {is_connected}")
                return is_connected

            # For llama-cpp-python models, check if the model is loaded
            if self.is_llamacpp:
                is_connected = self.llamacpp_model is not None
                self.logger.debug(f"llama-cpp-python connection check: {is_connected}")
                return is_connected

            self.logger.debug(f"Checking connection to {self.service_name} server...")

            # SECURITY ENHANCEMENT: Prepare headers with secure credential handling
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                if self.api_key_manager:
                    secure_headers = self.api_key_manager.secure_header_creation(
                        self.api_key, "Bearer"
                    )
                    headers.update(secure_headers)
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"  # Fallback

            # Try to make a simple request to the models endpoint
            response = self.session.get(
                f"{self.api_url}/models", headers=headers, timeout=self.connection_timeout
            )
            is_connected = response.status_code == 200
            self.logger.debug(
                f"Connection check result: {is_connected} (status: {response.status_code})"
            )
            return is_connected
        except requests.ConnectionError:
            self.logger.debug("Connection check failed: Connection error")
            return False
        except requests.Timeout:
            self.logger.debug("Connection check failed: Timeout")
            return False
        except Exception as e:
            self.logger.debug(f"Connection check failed: {e}")
            return False

    async def check_connection_async(self) -> bool:
        """Check if the LLM service is available asynchronously"""
        import asyncio

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self.check_connection),
                timeout=5.0,  # 5 second timeout for connection check
            )
        except TimeoutError:
            self.logger.debug("Async connection check timed out")
            return False
        except Exception as e:
            self.logger.debug(f"Async connection check failed: {e}")
            return False

    @monitor_performance("llm_request", timeout_ms=30000)
    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a chat completion response

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model (usually just use "local-model" for LM Studio)
            temperature: Randomness of the generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (defaults to environment config)
            stream: Whether to stream the response (not implemented yet)

        Returns:
            The response from the API
        """
        # Handle local LLM inference first
        if self.is_local_llm and self.local_model and self.local_tokenizer:
            return self._generate_local_chat_completion(messages, temperature, max_tokens)

        # Handle llama-cpp-python inference
        if self.is_llamacpp:
            if self.llamacpp_model:
                return self._generate_llamacpp_chat_completion(messages, temperature, max_tokens)
            else:
                # Return error response when llamacpp is configured but model not loaded
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Sorry, llama-cpp-python model is not loaded. Please check your LLAMACPP_MODEL_PATH or ensure a .gguf model exists in ./models/",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "error": "llama-cpp-python model not loaded",
                }

        # Use environment default if model not specified
        if model is None:
            model = self.default_model_name

        # Use environment default if max_tokens not specified
        if max_tokens is None:
            max_tokens = self.default_max_tokens_chat

        self.logger.debug(f"Generating chat completion with {len(messages)} messages")
        self.logger.debug(
            f"Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}"
        )

        # Debug: Log message structure to identify role alternation issues
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if isinstance(content, list):
                # For multimodal content, don't log the actual content (contains base64 images)
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                text_preview = " ".join(text_parts)[:50] if text_parts else "[no text]"
                self.logger.debug(
                    f"Message {i}: role='{msg.get('role', 'MISSING')}', text='{text_preview}...'"
                )
                self.logger.debug(
                    f"Message {i} contains multimodal content with {len(content)} parts"
                )
            else:
                # For text-only content, log first 50 characters as before
                self.logger.debug(
                    f"Message {i}: role='{msg.get('role', 'MISSING')}', content='{content[:50]}...'"
                )

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            self.logger.debug(f"Sending request to {self.chat_endpoint}")

            # SECURITY ENHANCEMENT: Prepare headers with secure credential handling
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                if self.api_key_manager:
                    secure_headers = self.api_key_manager.secure_header_creation(
                        self.api_key, "Bearer"
                    )
                    headers.update(secure_headers)
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"  # Fallback

            response = self.session.post(
                self.chat_endpoint,
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout),
            )
            response.raise_for_status()
            result = response.json()
            self.logger.debug("Successfully received chat completion response")

            # Debug: Log response structure for vision messages
            if any(isinstance(msg.get("content"), list) for msg in messages):
                self.logger.debug(f"Vision response keys: {list(result.keys())}")
                if "choices" in result:
                    self.logger.debug(
                        f"Choices structure: {list(result['choices'][0].keys()) if result['choices'] else 'empty choices'}"
                    )
                else:
                    self.logger.warning(
                        "Vision response missing 'choices' key - this may cause errors"
                    )
                    self.logger.debug(f"Full response structure: {result}")

            return result
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error generating chat completion: {e}")
            raise LLMConnectionError(
                f"Cannot connect to {self.service_name} server. Is it running?"
            )
        except requests.Timeout as e:
            self.logger.error(f"Timeout error generating chat completion: {e}")
            raise LLMTimeoutError(f"Request to {self.service_name} timed out")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.error("Rate limit exceeded")
                raise LLMRateLimitError(f"{self.service_name} rate limit exceeded")
            elif e.response.status_code >= 500:
                self.logger.error(f"Server error: {e.response.status_code}")
                raise LLMError(f"{self.service_name} server error: {e.response.status_code}")
            else:
                self.logger.error(f"HTTP error: {e.response.status_code}")
                raise LLMError(f"HTTP error: {e.response.status_code}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            raise LLMError(f"Invalid response from {self.service_name} server")
        except Exception as e:
            self.logger.error(f"Unexpected error generating chat completion: {e}")
            raise LLMError(f"Unexpected error: {str(e)}")

    def create_vision_message(self, text: str, images: list[str]) -> dict[str, Any]:
        """
        Create a message with both text and images for vision models

        Args:
            text: Text content of the message
            images: List of base64-encoded images (data URIs)

        Returns:
            Message dictionary formatted for vision models
        """
        if not self.supports_vision:
            self.logger.warning("Vision not supported, creating text-only message")
            return {"role": "user", "content": text}

        if not images:
            return {"role": "user", "content": text}

        # Limit number of images
        limited_images = images[: self.vision_max_images]
        if len(images) > self.vision_max_images:
            self.logger.warning(
                f"Too many images ({len(images)}), using only first {self.vision_max_images}"
            )

        # Create multimodal content
        content = []

        # Add text content if provided
        if text.strip():
            content.append({"type": "text", "text": text})

        # Add images
        for image_data in limited_images:
            content.append({"type": "image_url", "image_url": {"url": image_data}})

        self.logger.debug(
            f"Created vision message with {len(content)} content parts ({len(limited_images)} images)"
        )

        return {"role": "user", "content": content}

    def has_vision_support(self) -> bool:
        """
        Check if the current model supports vision input

        Returns:
            True if vision is supported
        """
        return self.supports_vision

    def get_vision_config(self) -> dict[str, Any]:
        """
        Get current vision configuration

        Returns:
            Dictionary with vision settings
        """
        return {"supports_vision": self.supports_vision, "max_images": self.vision_max_images}

    def generate_completion(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate a text completion response

        Args:
            prompt: The prompt text to complete
            model: Name of the model (usually just use "local-model" for LM Studio)
            temperature: Randomness of the generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (defaults to environment config)

        Returns:
            The response from the API
        """
        # Use environment default if model not specified
        if model is None:
            model = self.default_model_name

        # Use environment default if max_tokens not specified
        if max_tokens is None:
            max_tokens = self.default_max_tokens_completion

        self.logger.debug(f"Generating text completion for prompt: {prompt[:50]}...")
        self.logger.debug(
            f"Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}"
        )

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            self.logger.debug(f"Sending request to {self.completions_endpoint}")

            # SECURITY ENHANCEMENT: Prepare headers with secure credential handling
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                if self.api_key_manager:
                    secure_headers = self.api_key_manager.secure_header_creation(
                        self.api_key, "Bearer"
                    )
                    headers.update(secure_headers)
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"  # Fallback

            response = self.session.post(
                self.completions_endpoint,
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout),
            )
            response.raise_for_status()
            result = response.json()
            self.logger.debug("Successfully received text completion response")
            return result
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error generating completion: {e}")
            raise LLMConnectionError(
                f"Cannot connect to {self.service_name} server. Is it running?"
            )
        except requests.Timeout as e:
            self.logger.error(f"Timeout error generating completion: {e}")
            raise LLMTimeoutError(f"Request to {self.service_name} timed out")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"{self.service_name} rate limit exceeded")
            elif e.response.status_code >= 500:
                raise LLMError(f"{self.service_name} server error: {e.response.status_code}")
            else:
                raise LLMError(f"HTTP error: {e.response.status_code}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            raise LLMError(f"Invalid response from {self.service_name} server")
        except Exception as e:
            self.logger.error(f"Unexpected error generating completion: {e}")
            raise LLMError(f"Unexpected error: {str(e)}")

    @monitor_performance("emotion_analysis", timeout_ms=15000)
    def generate_emotion_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a chat completion response using the emotion analysis endpoint
        This allows using a different service/model for emotion analysis tasks

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model (uses emotion model if not specified)
            temperature: Randomness of the generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (defaults to emotion analysis limit)
            stream: Whether to stream the response (not implemented yet)

        Returns:
            The response from the emotion analysis API
        """
        # Use default model if not specified
        if model is None:
            model = self.default_model_name

        # Use emotion-specific token limit if not specified
        if max_tokens is None:
            max_tokens = self.max_tokens_emotion

        self.logger.debug(f"Generating emotion chat completion with {len(messages)} messages")
        self.logger.debug(f"Emotion endpoint: {self.emotion_chat_endpoint}")
        self.logger.debug(
            f"Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}"
        )

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            if not self.emotion_chat_endpoint:
                raise ValueError("Emotion API endpoint not configured")

            self.logger.debug(f"Sending request to emotion endpoint: {self.emotion_chat_endpoint}")

            # SECURITY ENHANCEMENT: Prepare headers for emotion endpoint with secure handling
            headers = {"Content-Type": "application/json"}
            if self.emotion_api_key:
                if self.api_key_manager:
                    secure_headers = self.api_key_manager.secure_header_creation(
                        self.emotion_api_key, "Bearer"
                    )
                    headers.update(secure_headers)
                else:
                    headers["Authorization"] = f"Bearer {self.emotion_api_key}"  # Fallback

            response = self.session.post(
                self.emotion_chat_endpoint,
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout),
            )
            response.raise_for_status()
            result = response.json()
            self.logger.debug("Successfully received emotion chat completion response")
            return result
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error generating emotion completion: {e}")
            raise LLMConnectionError(
                f"Cannot connect to {self.emotion_service_name} server. Is it running?"
            )
        except requests.Timeout as e:
            self.logger.error(f"Timeout error generating emotion completion: {e}")
            raise LLMTimeoutError(f"Request to {self.emotion_service_name} timed out")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.error("Rate limit exceeded")
                raise LLMRateLimitError(f"{self.emotion_service_name} rate limit exceeded")
            elif e.response.status_code >= 500:
                self.logger.error(f"Server error: {e.response.status_code}")
                raise LLMError(
                    f"{self.emotion_service_name} server error: {e.response.status_code}"
                )
            else:
                self.logger.error(f"HTTP error: {e.response.status_code}")
                raise LLMError(f"HTTP error: {e.response.status_code}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            raise LLMError(f"Invalid response from {self.emotion_service_name} server")

    @monitor_performance("facts_analysis", timeout_ms=15000)
    def generate_facts_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a chat completion response using the facts analysis endpoint
        This allows using a different service/model for fact extraction tasks

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model (uses facts model if not specified)
            temperature: Randomness of the generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (defaults to fact extraction limit)
            stream: Whether to stream the response (not implemented yet)

        Returns:
            The response from the facts analysis API
        """
        # Use facts model if not specified
        if model is None:
            model = self.facts_model_name

        # Use facts-specific token limit if not specified
        if max_tokens is None:
            max_tokens = self.max_tokens_fact_extraction

        self.logger.debug(f"Generating facts chat completion with {len(messages)} messages")
        self.logger.debug(f"Facts endpoint: {self.facts_chat_endpoint}")
        self.logger.debug(
            f"Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}"
        )

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            if not self.facts_chat_endpoint:
                raise ValueError("Facts API endpoint not configured")

            self.logger.debug(f"Sending request to facts endpoint: {self.facts_chat_endpoint}")

            # SECURITY ENHANCEMENT: Prepare headers for facts endpoint with secure handling
            headers = {"Content-Type": "application/json"}
            if self.facts_api_key:
                if self.api_key_manager:
                    secure_headers = self.api_key_manager.secure_header_creation(
                        self.facts_api_key, "Bearer"
                    )
                    headers.update(secure_headers)
                else:
                    headers["Authorization"] = f"Bearer {self.facts_api_key}"  # Fallback

            response = self.session.post(
                self.facts_chat_endpoint,
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout),
            )
            response.raise_for_status()
            result = response.json()
            self.logger.debug("Successfully received facts chat completion response")
            return result
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error generating facts completion: {e}")
            raise LLMConnectionError(
                f"Cannot connect to {self.facts_service_name} server. Is it running?"
            )
        except requests.Timeout as e:
            self.logger.error(f"Timeout error generating facts completion: {e}")
            raise LLMTimeoutError(f"Request to {self.facts_service_name} timed out")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.error("Rate limit exceeded")
                raise LLMRateLimitError(f"{self.facts_service_name} rate limit exceeded")
            elif e.response.status_code >= 500:
                self.logger.error(f"Server error: {e.response.status_code}")
                raise LLMError(f"{self.facts_service_name} server error: {e.response.status_code}")
            else:
                self.logger.error(f"HTTP error: {e.response.status_code}")
                raise LLMError(f"HTTP error: {e.response.status_code}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            raise LLMError(f"Invalid response from {self.facts_service_name} server")
        except Exception as e:
            self.logger.error(f"Unexpected error generating sentiment completion: {e}")
            raise LLMError(f"Unexpected error: {str(e)}")

    def get_chat_response(self, messages: list[dict[str, str]]) -> str:
        """
        Get a simple text response from a chat completion

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            The text of the response

        Raises:
            LLMError: If there's an error getting the response
        """
        self.logger.debug(f"Getting chat response for {len(messages)} messages")

        # Apply message alternation fix directly here to avoid import issues
        fixed_messages = self._fix_message_alternation(messages)
        self.logger.debug(
            f"Applied message alternation fix: {len(messages)} -> {len(fixed_messages)} messages"
        )

        try:
            response = self.generate_chat_completion(fixed_messages)

            # Validate response structure
            if not isinstance(response, dict):
                self.logger.error(f"Invalid response type: {type(response)}")
                raise LLMError("Invalid response format from LM Studio - not a dict")

            if "choices" not in response:
                self.logger.error(
                    f"Response missing 'choices' key. Available keys: {list(response.keys())}"
                )
                self.logger.error(f"Full response: {response}")
                raise LLMError("Invalid response format from LM Studio - missing 'choices'")

            if not response["choices"] or len(response["choices"]) == 0:
                self.logger.error("Response has empty choices array")
                raise LLMError("Invalid response format from LM Studio - empty choices")

            # Extract response content, handling both string and multimodal responses
            choice = response["choices"][0]
            if "message" not in choice:
                self.logger.error(
                    f"Choice missing 'message' key. Available keys: {list(choice.keys())}"
                )
                raise LLMError("Invalid response format from LM Studio - missing 'message'")

            message = choice["message"]
            if "content" not in message:
                self.logger.error(
                    f"Message missing 'content' key. Available keys: {list(message.keys())}"
                )
                raise LLMError("Invalid response format from LM Studio - missing 'content'")

            response_content = message["content"]

            # Handle different response content types
            if isinstance(response_content, str):
                # Standard text response
                response_text = response_content.strip()
            elif isinstance(response_content, list):
                # Multimodal response - extract text parts
                text_parts = []
                for part in response_content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                response_text = "\n".join(text_parts).strip()
            else:
                # Fallback - convert to string
                response_text = str(response_content).strip()

            self.logger.debug(f"Extracted response text: {len(response_text)} characters")
            return response_text
        except KeyError as e:
            self.logger.error(f"Invalid response format from LLM: {e}")
            raise LLMError("Invalid response format from LM Studio")
        except (LLMConnectionError, LLMTimeoutError, LLMRateLimitError):
            # Re-raise specific LLM errors
            raise
        except Exception as e:
            self.logger.error(f"Failed to get response from LLM: {e}")
            raise LLMError(f"Failed to get response from LLM: {str(e)}")

    def _fix_message_alternation(self, messages: list) -> list:
        """
        Ensure proper user/assistant alternation by filtering, not merging.
        This prevents content concatenation bugs while satisfying API requirements.
        SECURITY ENHANCEMENT: Completely eliminates content merging to prevent conversation history leakage.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Filtered list with proper role alternation (NO CONTENT MERGING)
        """
        if not messages:
            return messages

        # ENHANCED SECURITY: Apply comprehensive message role security processing
        try:
            from src.security.llm_message_role_security import secure_message_role_processing

            secure_messages = secure_message_role_processing(messages)
            self.logger.debug(
                f"Applied secure message role processing: {len(messages)} -> {len(secure_messages)} messages"
            )

            # If security processing returned messages, use them and skip old logic
            if secure_messages:
                return secure_messages

        except ImportError:
            self.logger.warning(
                "LLM message role security module not available - falling back to basic processing"
            )
        except Exception as e:
            self.logger.error(
                f"Error in secure message role processing: {e} - falling back to basic processing"
            )

        # FALLBACK: Legacy processing with basic security (if new security fails)
        # SECURITY ENHANCEMENT: Import and apply system message security
        try:
            from src.security.system_message_security import sanitize_system_messages

            messages = sanitize_system_messages(messages)
            self.logger.debug("Applied system message sanitization (fallback)")
        except ImportError:
            self.logger.warning(
                "System message security module not available - proceeding without sanitization"
            )
        except Exception as e:
            self.logger.error(f"Error applying system message sanitization: {e}")

        result = []
        system_messages = []

        # Extract system messages first
        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                result.append(msg)

        # SECURITY ENHANCEMENT: Limit combined system message size to prevent large exposure surface
        if system_messages:
            combined_system_content = "\n\n".join(
                msg.get("content", "") for msg in system_messages if msg.get("content")
            )

            # Calculate dynamic character limit based on token configuration
            # Reserve 50% of max tokens for system message, convert tokens to characters with 4:1 ratio
            import os

            max_tokens_for_system = self.default_max_tokens_chat // 2  # 50% allocation
            calculated_char_limit = (
                max_tokens_for_system * 4
            )  # 4 characters per token approximation

            # Allow environment override but use calculated limit as minimum
            env_limit = int(os.getenv("MAX_SYSTEM_MESSAGE_LENGTH", str(calculated_char_limit)))
            MAX_SYSTEM_MESSAGE_LENGTH = max(calculated_char_limit, env_limit)

            if len(combined_system_content) > MAX_SYSTEM_MESSAGE_LENGTH:
                combined_system_content = (
                    combined_system_content[:MAX_SYSTEM_MESSAGE_LENGTH]
                    + "\n[SYSTEM_CONTEXT_TRUNCATED]"
                )
                self.logger.warning(
                    f"System message truncated to {MAX_SYSTEM_MESSAGE_LENGTH} characters (calculated from {self.default_max_tokens_chat} max tokens)"
                )

            system_msg = {"role": "system", "content": combined_system_content}
            final_result = [system_msg]
        else:
            final_result = []

        # SECURITY FIX: Filter for proper alternation by SELECTION, not merging
        if not result:
            return final_result

        filtered_messages = []
        expected_role = "user"

        for msg in result:
            role = msg.get("role")
            content = msg.get("content", "")

            # Handle both string and list content (for vision messages)
            if isinstance(content, list):
                # For multimodal content, check if there's any text content
                has_content = any(
                    (
                        isinstance(part, dict)
                        and part.get("type") == "text"
                        and part.get("text", "").strip()
                    )
                    or (isinstance(part, str) and part.strip())
                    for part in content
                )
                if not has_content:  # Skip messages with no text content
                    self.logger.debug("Skipping multimodal message with no text content")
                    continue
            elif isinstance(content, str):
                if not content.strip():  # Skip empty messages
                    self.logger.debug(f"Skipping empty string message with role {role}")
                    continue
            else:
                # Convert other types to string for checking
                if not str(content).strip():
                    self.logger.debug(f"Skipping empty message with role {role}")
                    continue

            if role == expected_role:
                # Expected role - add message and flip expectation
                filtered_messages.append(msg)
                expected_role = "assistant" if role == "user" else "user"
                self.logger.debug(f"Added {role} message, expecting {expected_role} next")
            else:
                # Role doesn't match expectation - check for consecutive same-role messages first
                if filtered_messages and filtered_messages[-1]["role"] == role:
                    # Consecutive same-role messages - replace with most recent
                    self.logger.debug(f"Replacing previous {role} message with more recent one")
                    filtered_messages[-1] = msg  # Replace with newer message
                    # Keep same expected_role since we just replaced, don't flip
                elif role == "assistant" and expected_role == "user":
                    # Assistant message when expecting user - add minimal placeholder
                    placeholder = {"role": "user", "content": "[Continuing conversation]"}
                    filtered_messages.append(placeholder)
                    filtered_messages.append(msg)
                    expected_role = "user"
                    self.logger.debug("Added placeholder user message before assistant message")
                else:
                    # Other cases - just add the message
                    filtered_messages.append(msg)
                    expected_role = "assistant" if role == "user" else "user"

        final_result.extend(filtered_messages)

        # Log the filtering for debugging
        self.logger.debug(
            f"Message alternation filter: {len(messages)} -> {len(final_result)} messages (NO MERGING)"
        )

        return final_result

    def extract_facts(self, message: str) -> dict[str, Any]:
        """
        Use LLM to extract factual information from a message

        Args:
            message: The user message to analyze for facts

        Returns:
            Dict containing extracted facts and metadata
        """
        try:
            # Use chat completion for fact extraction
            messages = [
                {
                    "role": "system",
                    "content": "You are a fact extraction expert. Extract factual information from user messages and respond with valid JSON only.",
                },
                {
                    "role": "user",
                    "content": f"""Extract factual information from this message. Look for facts about:
- Relationships between people (family, work, friendship)
- Geographic locations and places
- Scientific or technical information
- Historical events and dates
- Company/organization information
- Personal information shared by the user
- General world knowledge
- Bot capabilities or features

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no other text.

Return this exact JSON structure:

{{{{
  "facts": [
    {{{{
      "fact": "concise factual statement",
      "category": "one of: relationship, geography, scientific, historical, business, personal, bot_capability, general_fact",
      "confidence": 0.85,
      "entities": ["entity1", "entity2"],
      "reasoning": "brief explanation"
    }}}}
  ]
}}}}

If no facts found, return: {{{{"facts": []}}}}

Message: "{message}"

JSON Response:""",
                },
            ]

            self.logger.debug("Sending fact extraction request to facts LLM...")
            self.logger.debug(
                f"Facts LLM parameters - service: {self.facts_service_name}, model: {self.facts_model_name}, max_tokens: {self.max_tokens_fact_extraction}, temperature: 0.1"
            )
            response = self.generate_facts_chat_completion(
                messages=messages,
                model=self.facts_model_name,  # Use dedicated facts model for fact extraction
                max_tokens=self.max_tokens_fact_extraction,
                temperature=0.1,  # Low temperature for consistent factual analysis
            )

            # Extract the text from the API response
            if (
                isinstance(response, dict)
                and "choices" in response
                and len(response["choices"]) > 0
            ):
                response_text = response["choices"][0]["message"]["content"].strip()
                self.logger.debug(
                    f"Received LLM fact extraction response: {len(response_text)} characters"
                )
            else:
                raise ValueError("Invalid response format from LLM")

            # Clean up markdown formatting if present
            if response_text.startswith("```json"):
                # Remove markdown code block formatting
                response_text = response_text[7:]  # Remove ```json
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove trailing ```
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                # Remove generic code block formatting
                lines = response_text.split("\n")
                if len(lines) > 2:
                    response_text = "\n".join(lines[1:-1])  # Remove first and last lines
                response_text = response_text.strip()

            # Remove JSON comments (// style comments) that some LLMs add
            # Use negative lookbehind to avoid matching URLs (http:// or https://)
            response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
            response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)

            # Remove trailing commas that make JSON invalid
            response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)

            # Advanced JSON cleanup and parsing
            response_text = self._robust_json_parse(response_text)

            # Parse the JSON response
            fact_data = json.loads(response_text)

            # Validate required fields
            if "facts" not in fact_data:
                raise ValueError("Missing required field: facts")

            if not isinstance(fact_data["facts"], list):
                raise ValueError("facts field must be a list")

            # Validate each fact entry
            valid_categories = [
                "relationship",
                "geography",
                "scientific",
                "historical",
                "business",
                "personal",
                "bot_capability",
                "general_fact",
            ]

            # Category mapping for common variations
            category_mapping = {
                "population": "geography",
                "location": "geography",
                "work": "relationship",
                "company/organization": "business",
                "organization": "business",
                "company": "business",
                "family": "relationship",
                "work_relationship": "relationship",
                "bot_purpose": "bot_capability",
                "bot_feature": "bot_capability",
                "causation": "general_fact",
            }

            validated_facts = []
            for fact in fact_data["facts"]:
                if not isinstance(fact, dict):
                    continue

                # Ensure required fields exist
                if "fact" not in fact or "category" not in fact:
                    continue

                # Map category to valid category
                category = str(fact["category"]).lower()
                if category in category_mapping:
                    category = category_mapping[category]

                # Validate and clean the fact entry
                validated_fact = {
                    "fact": str(fact["fact"]).strip(),
                    "category": category,
                    "confidence": max(0.0, min(1.0, float(fact.get("confidence", 0.5)))),
                    "entities": (
                        fact.get("entities", []) if isinstance(fact.get("entities"), list) else []
                    ),
                    "reasoning": str(fact.get("reasoning", "LLM fact extraction")),
                }

                # Only include facts with valid categories and non-empty fact text
                if validated_fact["category"] in valid_categories and validated_fact["fact"]:
                    validated_facts.append(validated_fact)

            result = {"facts": validated_facts}

            if validated_facts:
                self.logger.debug(f"LLM extracted {len(validated_facts)} facts")

            return result

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse LLM fact extraction response as JSON: {response_text if 'response_text' in locals() else 'No response'} - Error: {e}"
            )
            raise LLMError(f"Invalid JSON response from LLM fact extraction: {e}")
        except Exception as e:
            self.logger.error(f"Error in LLM fact extraction: {e}")
            raise LLMError(f"LLM fact extraction failed: {e}")

    def extract_personal_info(self, message: str) -> dict[str, Any]:
        """
        Use LLM to extract personal information from a message

        Args:
            message: The user message to analyze for personal information

        Returns:
            Dict containing extracted personal information
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a personal information extraction expert. Extract personal details shared by users and respond with valid JSON only.",
                },
                {
                    "role": "user",
                    "content": f"""Extract personal information from this message. Look for:
- Name (what the person calls themselves)
- Age (how old they are)
- Location (where they live/are from)
- Work (job, company, profession)
- Hobbies/Interests (what they like to do)
- Preferences (likes/dislikes)

Return only a JSON response with this exact structure:

{{
  "personal_info": {{
    "name": ["extracted names"],
    "age": ["extracted ages"],
    "location": ["extracted locations"],
    "work": ["extracted work info"],
    "hobbies": ["extracted hobbies/interests"],
    "preferences": ["extracted likes/dislikes"]
  }},
  "confidence": 0.85,
  "reasoning": "brief explanation of what was found"
}}

Only extract information that is clearly stated. If no personal info is found, return empty arrays.

Message to analyze: "{message}"

Respond only with valid JSON, no other text.""",
                },
            ]

            self.logger.debug("Sending personal info extraction request to facts LLM...")
            self.logger.debug(
                f"Facts LLM parameters - service: {self.facts_service_name}, model: {self.facts_model_name}, max_tokens: {self.max_tokens_personal_info}, temperature: 0.1"
            )
            response = self.generate_facts_chat_completion(
                messages=messages,
                model=self.facts_model_name,
                max_tokens=self.max_tokens_personal_info,
                temperature=0.1,
            )

            if (
                isinstance(response, dict)
                and "choices" in response
                and len(response["choices"]) > 0
            ):
                response_text = response["choices"][0]["message"]["content"].strip()
                self.logger.debug(
                    f"Received LLM personal info response: {len(response_text)} characters"
                )
            else:
                raise ValueError("Invalid response format from LLM")

            # Clean up markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                lines = response_text.split("\n")
                if len(lines) > 2:
                    response_text = "\n".join(lines[1:-1])
                response_text = response_text.strip()

            # Remove JSON comments (// style comments) that some LLMs add
            # Use negative lookbehind to avoid matching URLs (http:// or https://)
            response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
            response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)

            # Remove trailing commas that make JSON invalid
            response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)

            response_text = response_text.strip()

            # Extract first complete JSON object
            json_start = response_text.find("{")
            if json_start >= 0:
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_text[json_start:], json_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                if json_end > json_start:
                    response_text = response_text[json_start:json_end]

            info_data = json.loads(response_text)

            # Validate and clean the response
            if "personal_info" not in info_data:
                info_data["personal_info"] = {}

            # Ensure all expected fields exist
            for field in ["name", "age", "location", "work", "hobbies", "preferences"]:
                if field not in info_data["personal_info"]:
                    info_data["personal_info"][field] = []
                elif not isinstance(info_data["personal_info"][field], list):
                    info_data["personal_info"][field] = []

            # Ensure confidence exists and is valid
            info_data["confidence"] = max(0.0, min(1.0, float(info_data.get("confidence", 0.5))))

            if "reasoning" not in info_data:
                info_data["reasoning"] = "LLM personal info extraction"

            self.logger.debug(
                f"LLM extracted personal info with confidence: {info_data['confidence']:.2f}"
            )

            return info_data

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse LLM personal info response as JSON: {response_text if 'response_text' in locals() else 'No response'} - Error: {e}"
            )
            raise LLMError(f"Invalid JSON response from LLM personal info extraction: {e}")
        except Exception as e:
            self.logger.error(f"Error in LLM personal info extraction: {e}")
            raise LLMError(f"LLM personal info extraction failed: {e}")

    def detect_trust_indicators(self, message: str) -> dict[str, Any]:
        """
        Use LLM to detect trust indicators in a message

        Args:
            message: The user message to analyze for trust indicators

        Returns:
            Dict containing trust analysis results
        """
        # Check if trust detection is disabled
        if not os.getenv('ENABLE_LLM_TRUST_DETECTION', 'true').lower() in ['true', '1', 'yes']:
            self.logger.debug("Trust detection disabled via ENABLE_LLM_TRUST_DETECTION environment variable")
            return {
                "trust_indicators": [],
                "trust_level": "low",
                "confidence": 0.0,
                "reasoning": "Trust detection disabled"
            }
            
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a trust and relationship analysis expert. Detect indicators of trust, intimacy, and relationship building in messages.",
                },
                {
                    "role": "user",
                    "content": f"""Analyze this message for trust and relationship indicators. Look for:
- Expressions of trust ("I trust you", "you understand me")
- Sharing of personal/private information
- Vulnerability indicators ("between you and me", "don't tell anyone")
- Gratitude and appreciation ("thanks for listening", "you're helpful")
- Comfort expressions ("I feel safe", "you make me comfortable")
- Requests for confidentiality or personal advice

Return only a JSON response with this exact structure:

{{
  "trust_indicators": ["list of detected trust indicators"],
  "trust_level": "low|medium|high",
  "confidence": 0.85,
  "reasoning": "explanation of detected trust signals"
}}

If no trust indicators are found, return empty array and "low" trust level.

Message to analyze: "{message}"

Respond only with valid JSON, no other text.""",
                },
            ]

            self.logger.debug("Sending trust detection request to emotion LLM...")
            self.logger.debug(
                f"Emotion LLM parameters - service: {self.emotion_service_name}, model: {self.default_model_name}, max_tokens: {self.max_tokens_trust_detection}, temperature: 0.1"
            )
            response = self.generate_emotion_chat_completion(
                messages=messages,
                model=self.default_model_name,
                max_tokens=self.max_tokens_trust_detection,
                temperature=0.1,
            )

            if (
                isinstance(response, dict)
                and "choices" in response
                and len(response["choices"]) > 0
            ):
                response_text = response["choices"][0]["message"]["content"].strip()
                self.logger.debug(
                    f"Received LLM trust detection response: {len(response_text)} characters"
                )
            else:
                raise ValueError("Invalid response format from LLM")

            # Clean up markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                lines = response_text.split("\n")
                if len(lines) > 2:
                    response_text = "\n".join(lines[1:-1])
                response_text = response_text.strip()

            # Remove JSON comments (// style comments) that some LLMs add
            # Use negative lookbehind to avoid matching URLs (http:// or https://)
            response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
            response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)

            # Remove trailing commas that make JSON invalid
            response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)

            response_text = response_text.strip()

            # Extract first complete JSON object
            json_start = response_text.find("{")
            if json_start >= 0:
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_text[json_start:], json_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                if json_end > json_start:
                    response_text = response_text[json_start:json_end]

            trust_data = json.loads(response_text)

            # Validate and clean the response
            if "trust_indicators" not in trust_data:
                trust_data["trust_indicators"] = []
            elif not isinstance(trust_data["trust_indicators"], list):
                trust_data["trust_indicators"] = []

            # Validate trust level
            valid_levels = ["low", "medium", "high"]
            if "trust_level" not in trust_data or trust_data["trust_level"] not in valid_levels:
                trust_data["trust_level"] = "low"

            # Ensure confidence exists and is valid
            trust_data["confidence"] = max(0.0, min(1.0, float(trust_data.get("confidence", 0.5))))

            if "reasoning" not in trust_data:
                trust_data["reasoning"] = "LLM trust detection"

            self.logger.debug(
                f"LLM detected trust level: {trust_data['trust_level']} (confidence: {trust_data['confidence']:.2f})"
            )

            return trust_data

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse LLM trust detection response as JSON: {response_text if 'response_text' in locals() else 'No response'} - Error: {e}"
            )
            raise LLMError(f"Invalid JSON response from LLM trust detection: {e}")
        except Exception as e:
            self.logger.error(f"Error in LLM trust detection: {e}")
            raise LLMError(f"LLM trust detection failed: {e}")

    def extract_user_facts(self, message: str) -> dict[str, Any]:
        """
        Use LLM to extract user-specific facts from a message

        Args:
            message: The user message to analyze for personal facts

        Returns:
            Dict containing extracted user facts
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a user fact extraction expert. Extract personal facts, preferences, and information about the user from their messages.",
                },
                {
                    "role": "user",
                    "content": f"""Extract PERSISTENT user facts from this message. Categories: preference, personal_info, hobby, skill, history, goal, relationship, health, gaming, technology, other.

CRITICAL RULES:
1. ONLY extract facts that are EXPLICITLY stated in the message
2. DO NOT infer, assume, or hallucinate any information
3. EXCLUDE temporary emotional states (feeling happy, sad, angry, etc.)
4. EXCLUDE conversational context (asking questions, responding to something)
5. EXCLUDE immediate intentions/plans (going to do X, will do Y)
6. EXCLUDE temporary conditions (currently sick, tired right now, etc.)
7. ONLY INCLUDE stable, persistent facts about the user that are clearly stated

If the message is too short, vague, or contains no factual information about the user, return an empty list.

Examples of messages that should return NO facts:
- "testing..."
- "hmm"
- "maybe?"
- "ok"
- "hello"
- "thanks"
- "what?"

IMPORTANT: Return ONLY valid JSON in the exact format below. Do not add any comments, explanations, or markdown formatting.

{{
  "user_facts": [
    {{
      "fact": "exact persistent fact about the user from the message",
      "category": "category_name",
      "confidence": 0.85,
      "reasoning": "brief explanation of what in the message indicates this fact"
    }}
  ]
}}

If NO persistent facts are found in the message, return {{"user_facts": []}}.

Message: "{message}"

JSON response only (no markdown, no comments):""",
                },
            ]

            self.logger.debug("Sending user fact extraction request to facts LLM...")
            self.logger.debug(
                f"Facts LLM parameters - service: {self.facts_service_name}, model: {self.facts_model_name}, max_tokens: {self.max_tokens_user_facts}, temperature: 0.1"
            )
            response = self.generate_facts_chat_completion(
                messages=messages,
                model=self.facts_model_name,
                max_tokens=self.max_tokens_user_facts,
                temperature=0.1,
            )

            if (
                isinstance(response, dict)
                and "choices" in response
                and len(response["choices"]) > 0
            ):
                response_text = response["choices"][0]["message"]["content"].strip()
                self.logger.debug(
                    f"Received LLM user fact response: {len(response_text)} characters"
                )
            else:
                raise ValueError("Invalid response format from LLM")

            # Clean up markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                lines = response_text.split("\n")
                if len(lines) > 2:
                    response_text = "\n".join(lines[1:-1])
                response_text = response_text.strip()

            # Remove JSON comments (// style comments) that some LLMs add
            # Use negative lookbehind to avoid matching URLs (http:// or https://)
            response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
            response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)

            # Remove trailing commas that make JSON invalid
            response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)

            response_text = response_text.strip()

            # Extract first complete JSON object with better error handling
            json_start = response_text.find("{")
            if json_start >= 0:
                brace_count = 0
                json_end = json_start
                in_string = False
                escape_next = False

                for i, char in enumerate(response_text[json_start:], json_start):
                    if escape_next:
                        escape_next = False
                        continue

                    if char == "\\":
                        escape_next = True
                        continue

                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue

                    if not in_string:
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                if json_end > json_start and brace_count == 0:
                    response_text = response_text[json_start:json_end]
                else:
                    # If JSON is malformed, try to fix it by truncating at last valid closing brace
                    truncated_text = response_text[json_start:]
                    last_valid_end = json_start
                    temp_brace_count = 0
                    temp_in_string = False
                    temp_escape_next = False

                    for i, char in enumerate(truncated_text):
                        if temp_escape_next:
                            temp_escape_next = False
                            continue

                        if char == "\\":
                            temp_escape_next = True
                            continue

                        if char == '"' and not temp_escape_next:
                            temp_in_string = not temp_in_string
                            continue

                        if not temp_in_string:
                            if char == "{":
                                temp_brace_count += 1
                            elif char == "}":
                                temp_brace_count -= 1
                                if temp_brace_count == 0:
                                    last_valid_end = json_start + i + 1
                                    break

                    if last_valid_end > json_start:
                        response_text = response_text[json_start:last_valid_end]
                        self.logger.warning(
                            "Fixed malformed JSON by truncating at last valid closing brace"
                        )
                    else:
                        raise json.JSONDecodeError("Unable to extract valid JSON", response_text, 0)

            # Try to parse JSON with additional error recovery
            try:
                fact_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Failed to parse LLM user fact response as JSON: {response_text} - Error: {e}"
                )

                # Try to fix common JSON formatting issues
                try:
                    # Fix missing opening braces in array elements
                    fixed_text = response_text

                    # Look for pattern where array element is missing opening brace and fact field
                    # This handles cases like: ], "category": "relationship" instead of ], { "fact": "...", "category": "relationship"

                    # Pattern to detect malformed array elements missing opening brace
                    malformed_pattern = r'}\s*,\s*"(category|confidence|reasoning)":'
                    if re.search(malformed_pattern, fixed_text):
                        self.logger.warning(
                            "Detected malformed JSON array element with missing opening brace - attempting to fix"
                        )
                        # This is a complex fix, so for safety return empty facts
                        return {"user_facts": []}

                    # Pattern to detect array elements missing the "fact" field
                    # Look for objects that start with category/confidence/reasoning but no fact
                    pattern_no_fact = r'\{\s*"(?:category|confidence|reasoning)":'
                    if re.search(pattern_no_fact, fixed_text):
                        self.logger.warning(
                            "Detected JSON object missing required 'fact' field - attempting to fix"
                        )
                        # Extract only complete fact objects
                        facts_array_start = fixed_text.find('"user_facts": [')
                        if facts_array_start >= 0:
                            # Find all complete fact objects with required fields
                            complete_facts = []
                            fact_pattern = r'\{\s*"fact"\s*:\s*"[^"]*"[^}]*\}'
                            fact_matches = re.finditer(fact_pattern, fixed_text, re.DOTALL)

                            for match in fact_matches:
                                try:
                                    fact_json = match.group(0)
                                    # Validate this individual fact object
                                    fact_obj = json.loads(fact_json)
                                    if "fact" in fact_obj and "category" in fact_obj:
                                        complete_facts.append(fact_obj)
                                except json.JSONDecodeError:
                                    continue

                            if complete_facts:
                                return {"user_facts": complete_facts}
                            else:
                                return {"user_facts": []}

                    # Try other common fixes
                    fixed_text = re.sub(r",\s*}", "}", fixed_text)  # Remove trailing comma before }
                    fixed_text = re.sub(r",\s*]", "]", fixed_text)  # Remove trailing comma before ]

                    fact_data = json.loads(fixed_text)
                    self.logger.info("Successfully fixed malformed JSON")

                except json.JSONDecodeError:
                    self.logger.error("Unable to fix malformed JSON - returning empty facts")
                    return {"user_facts": []}

            # Validate required fields
            if "user_facts" not in fact_data:
                fact_data["user_facts"] = []
            elif not isinstance(fact_data["user_facts"], list):
                fact_data["user_facts"] = []

            # Validate each fact entry
            valid_categories = [
                "preference",
                "personal_info",
                "hobby",
                "skill",
                "history",
                "goal",
                "relationship",
                "health",
                "gaming",
                "technology",
                "other",
            ]

            validated_facts = []
            for fact in fact_data["user_facts"]:
                if not isinstance(fact, dict):
                    continue

                if "fact" not in fact or "category" not in fact:
                    continue

                validated_fact = {
                    "fact": str(fact["fact"]).strip(),
                    "category": str(fact["category"]).lower(),
                    "confidence": max(0.0, min(1.0, float(fact.get("confidence", 0.5)))),
                    "reasoning": str(fact.get("reasoning", "LLM user fact extraction")),
                }

                # Only include facts with valid categories
                if validated_fact["category"] in valid_categories and validated_fact["fact"]:
                    validated_facts.append(validated_fact)

            result = {"user_facts": validated_facts}

            if validated_facts:
                self.logger.debug(f"LLM extracted {len(validated_facts)} user facts")

            return result

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse LLM user fact response as JSON: {response_text if 'response_text' in locals() else 'No response'} - Error: {e}"
            )
            raise LLMError(f"Invalid JSON response from LLM user fact extraction: {e}")
        except Exception as e:
            self.logger.error(f"Error in LLM user fact extraction: {e}")
            raise LLMError(f"LLM user fact extraction failed: {e}")

    def _robust_json_parse(self, response_text: str) -> str:
        """Robust JSON parsing with multiple cleanup strategies"""

        # Strip whitespace
        response_text = response_text.strip()

        # Strategy 1: Find first complete JSON object
        json_start = response_text.find("{")
        if json_start >= 0:
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(response_text[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end > json_start:
                response_text = response_text[json_start:json_end]

        return response_text
