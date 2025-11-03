from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


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
    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send a chat request with tool support and return the response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            tools: List of available tools
            tool_choice: Tool choice strategy ("none", "auto", or specific tool)
            **kwargs: Additional parameters like temperature, max_tokens, etc.

        Returns:
            Dict containing the response with 'content', 'tool_calls', and other metadata
        """
        pass

    @abstractmethod
    def models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List of model names
        """
        pass