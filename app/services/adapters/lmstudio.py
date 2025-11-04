import requests
import json
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
        return self.chat_with_tools(messages, tools=None, **kwargs)

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send chat completion request with tool support to LM Studio."""
        headers = {"Content-Type": "application/json"}

        payload = {
            "messages": messages,
            "model": kwargs.get("model", "local-model"),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": False
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice
            print(f"DEBUG LMStudio: Sending {len(tools)} tools to LM Studio")
            for tool in tools[:2]:
                print(f"DEBUG LMStudio: Tool name: {tool['function']['name']}")

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            result = {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", payload["model"])
            }

            # Include tool calls if present
            message = data["choices"][0]["message"]
            if "tool_calls" in message and message["tool_calls"]:
                result["tool_calls"] = message["tool_calls"]
                print(f"DEBUG LMStudio: Received {len(message['tool_calls'])} tool calls from LM Studio")
                for tc in message["tool_calls"]:
                    print(f"DEBUG LMStudio: Tool call: {tc['function']['name']}")
            else:
                # Check for custom tool format in content
                content = message.get("content", "")
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
                            result["tool_calls"] = [{
                                "id": f"call_{hash(content)}",
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(args)
                                }
                            }]
                            # Remove the tool call from content
                            result["content"] = ""
                            print(f"DEBUG LMStudio: Parsed custom tool call from content: {tool_name} with args: {args}")
                    except (ValueError, json.JSONDecodeError) as e:
                        print(f"DEBUG LMStudio: Failed to parse custom tool format from content: {e}")

            return result
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