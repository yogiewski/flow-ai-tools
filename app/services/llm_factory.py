from typing import Optional
from .adapters.openai_like import OpenAILikeClient
from .adapters.ollama import OllamaClient
from .adapters.lmstudio import LMStudioClient
from .llm_client import LLMClient


def get_llm_client(api_flavor: str, base_url: str, port: int, api_key: Optional[str] = None) -> LLMClient:
    """Factory function to create the appropriate LLM client.

    Args:
        api_flavor: Type of API ('openai-compatible', 'ollama', 'lmstudio')
        base_url: Base URL for the API
        port: Port number
        api_key: Optional API key for authenticated APIs

    Returns:
        Configured LLMClient instance
    """
    if api_flavor == "openai-compatible":
        return OpenAILikeClient(base_url, port, api_key)
    elif api_flavor == "ollama":
        return OllamaClient(base_url, port)
    elif api_flavor == "lmstudio":
        return LMStudioClient(base_url, port)
    else:
        raise ValueError(f"Unsupported API flavor: {api_flavor}")