from typing import List, Dict, Any, Optional
import json
from services.llm_factory import get_llm_client
from .mcp_client import MCPClient
from utils.logging import get_logger
from utils.config import get_config

logger = get_logger(__name__)

class ChatOrchestrator:
    """Orchestrates chat interactions with MCP tool support using two-call pattern."""

    def __init__(self):
        self.config = get_config()
        self.mcp_client = MCPClient()
        self.max_tool_chain = 3  # Prevent infinite loops

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute chat with MCP tool orchestration using two-call pattern.

        Args:
            messages: Chat messages
            tools: Available MCP tools

        Returns:
            Dict with response content and tool results
        """
        tool_chain_count = 0
        current_messages = messages.copy()
        all_tool_results = []

        while tool_chain_count < self.max_tool_chain:
            # First call: allow tools
            response1 = self._first_completion(current_messages, tools)

            if not response1.get("tool_calls"):
                # No tools called, return final response
                return {
                    "content": response1["content"],
                    "tool_results": all_tool_results,
                    "final_response": True
                }

            # Execute tools
            tool_results = self._execute_tools(response1["tool_calls"])
            all_tool_results.extend(tool_results)

            # Append assistant message with tool calls
            current_messages.append({
                "role": "assistant",
                "content": response1["content"],
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    } for tc in response1["tool_calls"]
                ]
            })

            # Append tool results
            for result in tool_results:
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": result["content"]
                })

            tool_chain_count += 1

            # Check if we should continue the chain
            if not self._should_continue_chain(tool_results):
                break

        # Second call: format-only with tool_choice="none"
        response2 = self._second_completion(current_messages, tools)

        return {
            "content": response2["content"],
            "tool_results": all_tool_results,
            "final_response": True
        }

    def _first_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """First completion that allows tool usage."""
        client = get_llm_client(
            self.config['llm_api_flavor'],
            self.config['llm_base_url'],
            self.config['llm_port']
        )

        return client.chat_with_tools(
            messages=messages,
            model=self.config['llm_default_model'],
            temperature=0.7,
            max_tokens=2048,
            tools=tools
        )

    def _second_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Second completion for formatting with tool_choice='none'."""
        client = get_llm_client(
            self.config['llm_api_flavor'],
            self.config['llm_base_url'],
            self.config['llm_port']
        )

        return client.chat_with_tools(
            messages=messages,
            model=self.config['llm_default_model'],
            temperature=0.7,
            max_tokens=2048,
            tools=tools,
            tool_choice="none"
        )

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute MCP tools and return results."""
        results = []
        for tool_call in tool_calls:
            try:
                result = self.mcp_client.call_tool(
                    tool_call["function"]["name"],
                    json.loads(tool_call["function"]["arguments"])
                )
                results.append({
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                    "success": result.get("status") in ["success", "queued", "sent"]
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                results.append({
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps({
                        "status": "error",
                        "message": str(e)
                    }, ensure_ascii=False),
                    "success": False
                })
        return results

    def _should_continue_chain(self, tool_results: List[Dict[str, Any]]) -> bool:
        """Determine if tool chain should continue based on results."""
        # Continue if any tool returned an error that might be recoverable
        return any(not result["success"] for result in tool_results)