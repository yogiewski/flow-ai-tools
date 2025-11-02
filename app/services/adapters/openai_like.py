import requests
from typing import List, Dict, Any, Optional
from ..llm_client import LLMClient


class OpenAILikeClient(LLMClient):
    """Client for OpenAI-compatible APIs (OpenAI, LM Studio, etc.)."""

    def __init__(self, base_url: str, port: int, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.port = port
        self.api_key = api_key
        self.endpoint = f"{self.base_url}:{self.port}/v1/chat/completions"

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "messages": messages,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": False
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", payload["model"])
            }
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def models(self) -> List[str]:
        """Get available models."""
        try:
            response = requests.get(f"{self.base_url}:{self.port}/v1/models", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except requests.RequestException:
            # Fallback to common models if endpoint not available
            return ["gpt-3.5-turbo", "gpt-4", "gemma-2b"]