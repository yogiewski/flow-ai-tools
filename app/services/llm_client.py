from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMClient(ABC):
    """Abstract base class for LLM API clients."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send a chat request and return the response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional parameters like temperature, max_tokens, etc.

        Returns:
            Dict containing the response with 'content' and other metadata
        """
        pass

    @abstractmethod
    def models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List of model names
        """
        pass