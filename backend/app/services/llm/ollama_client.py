"""Local Ollama LLM client — no API keys, no data leaves the device."""

import json
from typing import Optional

import httpx

from app.config import settings
from app.utils.logging import logger


class OllamaClient:
    """Async Ollama client for local LLM inference."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.default_model = default_model or settings.ollama_model

    async def chat_completion(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send a message to Ollama and return the response text."""
        payload = {
            "model": model or self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return data["message"]["content"]