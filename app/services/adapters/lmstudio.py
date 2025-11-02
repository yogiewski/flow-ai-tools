import requests
from typing import List, Dict, Any, Optional
from ..llm_client import LLMClient


class LMStudioClient(LLMClient):
    """Client for LM Studio local server (OpenAI-compatible)."""

    def __init__(self, base_url: str, port: int):
        self.base_url = base_url.rstrip('/')
        self.port = port
        # LM Studio typically uses OpenAI-compatible endpoints
        self.endpoint = f"{self.base_url}:{self.port}/v1/chat/completions"

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request to LM Studio."""
        headers = {"Content-Type": "application/json"}

        payload = {
            "messages": messages,
            "model": kwargs.get("model", "local-model"),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": False
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", payload["model"])
            }
        except requests.RequestException as e:
            raise Exception(f"LM Studio API request failed: {str(e)}")

    def models(self) -> List[str]:
        """Get available models from LM Studio."""
        try:
            response = requests.get(f"{self.base_url}:{self.port}/v1/models", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except requests.RequestException:
            # LM Studio might not have models endpoint, return default
            return ["local-model"]