"""
Fallback LLM client using urllib instead of requests to avoid session conflicts
"""
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import os
from typing import Dict, List, Any

class FallbackLLMClient:
    """Fallback LLM client using urllib instead of requests"""
    
    def __init__(self):
        # Don't reload environment - it's already loaded in the main process
        self.api_url = os.getenv("LLM_CHAT_API_URL", "https://openrouter.ai/api/v1")
        self.api_key = os.getenv("LLM_CHAT_API_KEY")
        self.model = os.getenv("LLM_CHAT_MODEL", "openai/gpt-4o")
        self.chat_endpoint = f"{self.api_url}/chat/completions"
        self.logger = logging.getLogger(__name__)
        
        # Debug API key loading
        if self.api_key:
            self.logger.debug(f"Fallback LLM: API key loaded (first 10 chars): {self.api_key[:10]}")
        else:
            self.logger.error("Fallback LLM: No API key found!")
        
    def generate_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Dict[str, Any]:
        """Generate chat completion using urllib"""
        
        if not self.api_key:
            raise Exception("No API key available")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Prepare headers with proper OpenRouter format
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://whisperengine.local",
            "X-Title": "WhisperEngine Desktop"
        }
        
        # Convert payload to JSON
        json_data = json.dumps(payload).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(self.chat_endpoint, data=json_data, headers=headers, method='POST')
        
        try:
            self.logger.debug(f"Fallback LLM: Sending request to {self.chat_endpoint}")
            self.logger.debug(f"Fallback LLM: Headers (without auth): Content-Type, HTTP-Referer, X-Title")
            self.logger.debug(f"Fallback LLM: Has Authorization header: {bool(self.api_key)}")
            self.logger.debug(f"Fallback LLM: Model: {self.model}")
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                result = json.loads(response_data.decode('utf-8'))
                
                self.logger.debug("Fallback LLM: Successfully received response")
                return result
                
        except urllib.error.HTTPError as e:
            error_message = f"HTTP error: {e.code}"
            self.logger.error(f"Fallback LLM: {error_message}")
            # Try to read error response
            try:
                error_response = e.read().decode('utf-8')
                self.logger.error(f"Fallback LLM: Error response: {error_response}")
            except:
                pass
            raise Exception(error_message)
        except urllib.error.URLError as e:
            error_message = f"URL error: {e.reason}"
            self.logger.error(f"Fallback LLM: {error_message}")
            raise Exception(error_message)
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            self.logger.error(f"Fallback LLM: {error_message}")
            raise Exception(error_message)