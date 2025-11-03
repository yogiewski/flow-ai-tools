#!/usr/bin/env python3
"""Test script for MCP orchestration functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

from services.orchestrator import ChatOrchestrator
from services.mcp_client import MCPClient

def test_mcp_client():
    """Test MCP client functionality."""
    print("Testing MCP client...")
    client = MCPClient()

    # Test getting tools
    tools = client.get_available_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")

    # Test calling a tool
    result = client.call_tool("send_expedite_email", {
        "supplier_email": "test@example.com",
        "po_number": "TEST-123",
        "requester_name": "Test User",
        "requester_email": "user@example.com"
    })
    print(f"Tool result: {result}")

def test_orchestrator():
    """Test orchestrator functionality."""
    print("\nTesting orchestrator...")
    orchestrator = ChatOrchestrator()

    messages = [
        {"role": "user", "content": "Please expedite PO TEST-123 for supplier test@example.com"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_expedite_email",
                "description": "Send expedite request email to supplier",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "supplier_email": {"type": "string"},
                        "po_number": {"type": "string"},
                        "requester_name": {"type": "string"},
                        "requester_email": {"type": "string"}
                    },
                    "required": ["supplier_email", "po_number", "requester_name", "requester_email"]
                }
            }
        }
    ]

    # Note: This will fail without a real LLM, but tests the structure
    try:
        result = orchestrator.chat_with_tools(messages, tools)
        print(f"Orchestrator result: {result}")
    except Exception as e:
        print(f"Orchestrator test failed (expected without LLM): {e}")

if __name__ == "__main__":
    test_mcp_client()
    test_orchestrator()
    print("\nAll tests completed!")