import requests
from typing import List, Dict, Any, Optional
from ..llm_client import LLMClient


class OllamaClient(LLMClient):
    """Client for Ollama API."""

    def __init__(self, base_url: str, port: int):
        self.base_url = base_url.rstrip('/')
        self.port = port
        self.endpoint = f"{self.base_url}:{self.port}/api/chat"

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat request to Ollama."""
        return self.chat_with_tools(messages, tools=None, **kwargs)

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send chat request to Ollama (tools not supported)."""
        # Ollama doesn't support tools in the same way as OpenAI
        # For now, we'll ignore tools and just do regular chat
        if tools:
            # Log warning that tools are not supported
            pass

        # Convert messages to Ollama format
        # Ollama expects a single prompt, so we'll concatenate messages
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        payload = {
            "model": kwargs.get("model", "llama2"),
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            return {
                "content": data.get("response", ""),
                "done": data.get("done", True),
                "model": data.get("model", payload["model"])
            }
        except requests.RequestException as e:
            raise Exception(f"Ollama API request failed: {str(e)}")

    def models(self) -> List[str]:
        """Get available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}:{self.port}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.RequestException:
            # Fallback models
            return ["llama2", "codellama", "mistral"]