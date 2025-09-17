import os
import asyncio
import logging
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)

class VisionSummarizer:
    """Hybrid vision summarizer that calls a secondary multimodal model API to produce
    concise natural-language scene summaries plus optional emotional/aesthetic hints.

    Expects an OpenAI-compatible /chat/completions endpoint accepting messages with image_url
    content, or a simplified LM Studio style POST /chat/completions with {model, messages}.
    """

    def __init__(self):
        self.enabled = os.getenv("VISION_SUMMARIZER_ENABLED", "false").lower() in ("1", "true", "yes", "on")
        self.api_url = os.getenv("VISION_SUMMARIZER_API_URL", "").rstrip("/")
        self.model = os.getenv("VISION_SUMMARIZER_MODEL", "")
        self.max_images = int(os.getenv("VISION_SUMMARIZER_MAX_IMAGES", "3"))
        self.timeout = int(os.getenv("VISION_SUMMARIZER_TIMEOUT", "25"))
        self.max_tokens = int(os.getenv("VISION_SUMMARIZER_MAX_TOKENS", "180"))
        self.temperature = float(os.getenv("VISION_SUMMARIZER_TEMPERATURE", "0.2"))
        self.api_key = os.getenv("VISION_SUMMARIZER_API_KEY", "")

    def is_available(self) -> bool:
        return self.enabled and bool(self.api_url) and bool(self.model)

    async def summarize_images(self, attachments: List[Dict[str, Any]], user_prompt: str = "") -> Optional[str]:
        if not self.is_available():
            logger.debug("Vision summarizer unavailable (enabled=%s, url=%s, model=%s)", self.enabled, bool(self.api_url), self.model)
            return None

        if not attachments:
            return None

        # Build messages for an OpenAI-compatible multimodal chat completion
        limited = attachments[: self.max_images]
        content: List[Dict[str, Any]] = []
        if user_prompt:
            content.append({"type": "text", "text": user_prompt[:300]})

        # We rely on upstream image processor to have produced either base64 or URLs; here we assume 'proxy_url' or 'url'
        for att in limited:
            url = getattr(att, 'proxy_url', None) or getattr(att, 'url', None) or att.get('url') if isinstance(att, dict) else None
            if not url:
                continue
            content.append({
                "type": "image_url",
                "image_url": {"url": url}
            })

        if len(content) == 0:
            return None

        system_prompt = (
            "You are a concise visual scene summarizer. Describe the salient concrete details,"
            " atmosphere, notable objects, and any gentle emotional undertone in <= 55 words."
            " Do NOT produce bullet lists, headings, or analysis labels. Single natural paragraph."
        )

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "stream": False,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.api_url}/chat/completions", json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning("Vision summarizer non-200 status: %s %s", resp.status_code, resp.text[:200])
                    return None
                data = resp.json()
                summary = data.get("choices", [{}])[0].get("message", {}).get("content")
                if not summary:
                    return None
                # Basic cleanliness: strip line breaks and headings
                summary = summary.replace("\n", " ").strip()
                if len(summary.split()) > 70:
                    summary = " ".join(summary.split()[:70])
                return summary
        except Exception as e:
            logger.error("Vision summarizer call failed: %s", e)
            return None

# Convenience module-level singleton pattern
_summarizer: Optional[VisionSummarizer] = None

def get_vision_summarizer() -> VisionSummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = VisionSummarizer()
    return _summarizer
