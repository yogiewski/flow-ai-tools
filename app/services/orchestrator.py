from typing import List, Dict, Any, Optional
import json
from .llm_factory import get_llm_client
from .mcp_client import MCPHTTPClient
from utils.logging import get_logger
from utils.config import get_config

logger = get_logger(__name__)

class ChatOrchestrator:
    """Orchestrates chat interactions with MCP tool support using two-call pattern."""

    def __init__(self):
        self.config = get_config()
        self.mcp_client = MCPHTTPClient(self.config['mcp_base_url'])
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

    def _build_tool_descriptions(self, tools: List[Dict[str, Any]]) -> str:
        """Build tool descriptions for prompting."""
        descriptions = []
        for tool in tools:
            func = tool["function"]
            desc = f"- {func['name']}: {func['description']}\n  Parameters: {json.dumps(func['parameters'], indent=2)}"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def _parse_tool_calls_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse tool calls from LLM response when using prompting."""
        content = response.get("content", "").strip()
        print(f"DEBUG: Parsing tool calls from response: {content[:200]}...")

        # Check for custom tool format: <|start|>assistant<|channel|>commentary to=functions.{tool_name} <|constrain|>json<|message|>{json}
        if content.startswith("<|start|>assistant<|channel|>commentary to=functions."):
            try:
                # Extract tool name
                start_tool = content.find("functions.") + len("functions.")
                end_tool = content.find(" <|constrain|>")
                tool_name = content[start_tool:end_tool]

                # Extract JSON args
                start_json = content.find("<|message|>") + len("<|message|>")
                json_str = content[start_json:].strip()
                if json_str.startswith("{") and json_str.endswith("}"):
                    args = json.loads(json_str)

                    # Convert to OpenAI format
                    response["tool_calls"] = [{
                        "id": f"call_{hash(content)}",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(args)
                        }
                    }]
                    # Remove the tool call from content
                    response["content"] = ""
                    print(f"DEBUG: Parsed custom tool call: {tool_name} with args: {args}")
                    return response
            except (ValueError, json.JSONDecodeError) as e:
                print(f"DEBUG: Failed to parse custom tool format: {e}")

        # Fallback to original JSON parsing
        try:
            # Look for JSON object in the content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                tool_call = json.loads(json_str)
                if "tool" in tool_call and "arguments" in tool_call:
                    # Convert to OpenAI format
                    response["tool_calls"] = [{
                        "id": f"call_{hash(json_str)}",
                        "type": "function",
                        "function": {
                            "name": tool_call["tool"],
                            "arguments": json.dumps(tool_call["arguments"])
                        }
                    }]
                    # Remove the tool call from content
                    response["content"] = content[:start] + content[end:]
                    print(f"DEBUG: Parsed tool call: {tool_call['tool']}")
        except json.JSONDecodeError:
            print("DEBUG: No valid tool call JSON found in response")

        return response

    def _first_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """First completion that allows tool usage."""
        # Get available tools if not provided
        if tools is None:
            tools = self.mcp_client.list_tools()

        print(f"DEBUG: Making first completion with {len(tools)} tools")
        for tool in tools[:2]:  # Log first 2 tools
            print(f"DEBUG: Tool: {tool['function']['name']}")

        # For models that don't support native tool calling, add tool descriptions to messages
        messages_for_llm = messages.copy()
        if tools:
            tool_descriptions = self._build_tool_descriptions(tools)
            messages_for_llm.insert(0, {
                "role": "system",
                "content": f"You have access to the following tools:\n{tool_descriptions}\n\nIMPORTANT: You must use the appropriate tool to answer questions. Do not provide information from your training data. When you need to use a tool, respond ONLY with: <|start|>assistant<|channel|>commentary to=functions.{{tool_name}} <|constrain|>json<|message|>{{json_arguments}}"
            })

        client = get_llm_client(
            self.config['llm_api_flavor'],
            self.config['llm_base_url'],
            self.config['llm_port']
        )

        # Use prompting for tool calling
        result = client.chat(
            messages=messages_for_llm,
            model=self.config['llm_default_model'],
            temperature=0.7,
            max_tokens=2048
        )
        result = self._parse_tool_calls_from_response(result)

        print(f"DEBUG: First completion result has tool_calls: {'tool_calls' in result}")
        if 'tool_calls' in result:
            print(f"DEBUG: Tool calls count: {len(result['tool_calls'])}")

        return result

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