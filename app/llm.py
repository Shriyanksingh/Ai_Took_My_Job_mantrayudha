from __future__ import annotations
from typing import Any, Dict, Optional
import json
import logging
import httpx
from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL

logger = logging.getLogger("novamart.gemini")

class GeminiLLM:
    """
    Adapter for Google's Gemini API (free tier via Google AI Studio).
    Replaces ChatGPT/OpenAI adapter.
    Default free tier model: gemini-1.5-flash (or gemini-2.0-flash).
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = (api_key or GEMINI_API_KEY).strip()
        self.model = (model or GEMINI_MODEL).strip()
        self.base_url = (base_url or GEMINI_BASE_URL).rstrip('/')
        self.provider = "Google Gemini (Free Tier)"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip()

    def set_model(self, model: str):
        self.model = model.strip()

    def complete(self, system: str, user: str, timeout: float = 12.0) -> Optional[str]:
        """Synchronous text completion using free Gemini API."""
        if not self.enabled:
            return None
        
        # Check if direct Gemini REST API
        if "generativelanguage.googleapis.com" in self.base_url:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user}]
                    }
                ],
                "system_instruction": {
                    "parts": [{"text": system}]
                },
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024
                }
            }
            try:
                with httpx.Client(timeout=timeout) as client:
                    r = client.post(url, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                logger.warning(f"Gemini API completion error: {e}")
                return None
        else:
            # Fallback for OpenAI-compatible endpoint
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': self.model,
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                'temperature': 0.2
            }
            try:
                with httpx.Client(timeout=timeout) as client:
                    r = client.post(f'{self.base_url}/chat/completions', headers=headers, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return data['choices'][0]['message']['content'].strip()
            except Exception as e:
                logger.warning(f"LLM API completion error: {e}")
                return None

    async def acomplete(self, system: str, user: str, timeout: float = 12.0) -> Optional[str]:
        """Asynchronous text completion using free Gemini API."""
        if not self.enabled:
            return None

        if "generativelanguage.googleapis.com" in self.base_url:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user}]
                    }
                ],
                "system_instruction": {
                    "parts": [{"text": system}]
                },
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024
                }
            }
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(url, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                logger.warning(f"Gemini API async error: {e}")
                return None
        else:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': self.model,
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                'temperature': 0.2
            }
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(f'{self.base_url}/chat/completions', headers=headers, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return data['choices'][0]['message']['content'].strip()
            except Exception as e:
                logger.warning(f"LLM API async error: {e}")
                return None

# Backwards compatibility alias
OptionalLLM = GeminiLLM
