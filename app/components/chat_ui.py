import streamlit as st
import json
from typing import List, Dict, Any, Optional
from services.orchestrator import ChatOrchestrator
from services.mcp_client import MCPClient
from utils.translator import translator

class ChatUI:
    """Chat UI component with MCP tool support."""

    def __init__(self):
        self.orchestrator = ChatOrchestrator()
        self.mcp_client = MCPClient()

    def render_chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None):
        """Render the chat interface with tool support."""
        # Display chat messages
        for i, message in enumerate(messages):
            if message["role"] != "system":  # Don't display system messages
                self._render_message(message, i)

    def _render_message(self, message: Dict[str, Any], index: int):
        """Render a single message with tool support."""
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            if role == "assistant" and "tool_calls" in message:
                # Assistant message with tool calls
                st.markdown(content)
                self._render_tool_calls(message["tool_calls"])
            elif role == "tool":
                # Tool result message
                self._render_tool_result(message)
            else:
                # Regular message
                st.markdown(content)

    def _render_tool_calls(self, tool_calls: List[Dict[str, Any]]):
        """Render tool calls made by assistant."""
        with st.expander("🤖 Tool Calls", expanded=False):
            for tc in tool_calls:
                st.markdown(f"**{tc['function']['name']}**")
                try:
                    args = json.loads(tc['function']['arguments'])
                    st.json(args)
                except:
                    st.code(tc['function']['arguments'])

    def _render_tool_result(self, message: Dict[str, Any]):
        """Render tool execution result."""
        try:
            result = json.loads(message["content"])
            status = result.get("status", "unknown")

            if status == "success" or status == "queued" or status == "sent":
                self._render_success_tool_result(result)
            else:
                self._render_error_tool_result(result)
        except json.JSONDecodeError:
            # Raw content
            st.markdown(message["content"])

    def _render_success_tool_result(self, result: Dict[str, Any]):
        """Render successful tool result."""
        result_type = result.get("result_type", "tool")
        summary = result.get("result_summary", "Tool executed successfully")

        st.success(f"✅ {summary}")

        # Show details in expandable section
        with st.expander("📋 Details", expanded=False):
            if "data" in result:
                st.json(result["data"])

            if "preview" in result:
                preview = result["preview"]
                if "subject" in preview:
                    st.markdown(f"**Subject:** {preview['subject']}")
                if "body" in preview:
                    st.markdown("**Preview:**")
                    st.markdown(f"> {preview['body'][:200]}...")

            if "message_id" in result:
                st.markdown(f"**Message ID:** {result['message_id']}")

    def _render_error_tool_result(self, result: Dict[str, Any]):
        """Render error tool result."""
        error_msg = result.get("message", "Tool execution failed")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.error(f"⚠️ {error_msg}")
        with col2:
            if st.button("🔄 Retry", key=f"retry_{result.get('result_type', 'unknown')}"):
                st.rerun()

        # Show raw error details
        with st.expander("🔍 Error Details", expanded=False):
            st.json(result)

    def send_message(self, messages: List[Dict[str, Any]], user_input: str,
                    tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Send user message and get AI response with tool orchestration."""
        # Add user message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # Get AI response with tool orchestration
        with st.spinner(translator.get("status_messages.waiting_response")):
            response = self.orchestrator.chat_with_tools(messages, tools)

        # Add assistant response
        assistant_message = {
            "role": "assistant",
            "content": response["content"]
        }

        # Include tool calls if present
        if "tool_calls" in response:
            assistant_message["tool_calls"] = response["tool_calls"]

        messages.append(assistant_message)

        # Add tool results if any
        for tool_result in response.get("tool_results", []):
            messages.append({
                "role": "tool",
                "tool_call_id": tool_result["tool_call_id"],
                "content": tool_result["content"]
            })

        return messages