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
        return self.chat_with_tools(messages, tools=None, **kwargs)

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send chat completion request with tool support."""
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

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()

            result = {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", payload["model"])
            }

            # Include tool calls if present
            message = data["choices"][0]["message"]
            if "tool_calls" in message:
                result["tool_calls"] = message["tool_calls"]

            return result
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