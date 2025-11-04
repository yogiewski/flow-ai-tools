import requests
import json
from typing import Dict, Any, List
from utils.logging import get_logger
from config.constants import MCP_SERVER_URL

logger = get_logger(__name__)

class MCPHTTPClient:
    """HTTP client for communicating with MCP server using JSON-RPC over HTTP."""

    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url.rstrip('/')
        self.session_id: str = ""

    def _initialize_session(self):
        """Initialize session with MCP server"""
        if self.session_id:
            return

        try:
            # Initialize MCP session via POST
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "flow-ai-chat", "version": "1.0"}
                }
            }
            response = requests.post(
                f"{self.base_url}/mcp",
                json=init_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10
            )
            response.raise_for_status()

            # Get session ID from header
            session_id = response.headers.get("mcp-session-id")
            if session_id:
                self.session_id = session_id
                logger.info(f"Initialized MCP session: {self.session_id}")
            else:
                logger.warning("No session ID in initialize response")

        except Exception as e:
            logger.warning(f"Failed to initialize MCP session: {e}")

    def _jsonrpc_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        if not self.session_id:
            self._initialize_session()

        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        if self.session_id:
            headers["X-Session-ID"] = self.session_id

        try:
            response = requests.post(
                f"{self.base_url}/mcp",
                json=request_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"JSON-RPC request failed: {e}")
            raise

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server"""
        try:
            result = self._jsonrpc_request("tools/list", {})
            tools = result.get("result", {}).get("tools", [])

            # Convert MCP tool format to OpenAI format
            openai_tools = []
            for tool in tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                }
                openai_tools.append(openai_tool)

            logger.info(f"Retrieved {len(openai_tools)} tools from MCP server")
            return openai_tools

        except Exception as e:
            logger.warning(f"Failed to fetch tools from MCP server: {e}. Using mock tools.")
            return self._get_mock_tools()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via MCP JSON-RPC"""
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            result = self._jsonrpc_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            # Extract the actual tool result from MCP response
            if result.get("result", {}).get("content"):
                content = result["result"]["content"]
                if len(content) > 0 and content[0].get("text"):
                    return json.loads(content[0]["text"])
            return {}

        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return self._fallback_to_mock(tool_name, arguments)

    def _get_mock_tools(self) -> List[Dict[str, Any]]:
        """Get mock tools as fallback"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_product_details",
                    "description": "Get detailed information about a product",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Product name or identifier to search for"}
                        },
                        "required": ["query"]
                    }
                }
            },
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
                            "items": {"type": "array"},
                            "expected_ship_date": {"type": "string"},
                            "requester_name": {"type": "string"},
                            "requester_email": {"type": "string"}
                        },
                        "required": ["supplier_email", "po_number", "requester_name", "requester_email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_order_status",
                    "description": "Check the status of an order",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "po_number": {"type": "string"}
                        },
                        "required": ["po_number"]
                    }
                }
            }
        ]

    def _fallback_to_mock(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to mock implementation"""
        if tool_name == "get_product_details":
            return self._mock_get_product_details(arguments)
        elif tool_name == "send_expedite_email":
            return self._mock_expedite_email(arguments)
        elif tool_name == "check_order_status":
            return self._mock_order_status(arguments)
        else:
            return {
                "status": "error",
                "result_type": tool_name,
                "message": "Tool not available"
            }

    def _mock_expedite_email(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock expedite email tool."""
        import uuid
        message_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"

        return {
            "status": "queued",
            "result_type": "expedite_email",
            "message_id": message_id,
            "data": {
                "supplier_email": args.get("supplier_email"),
                "po_number": args.get("po_number"),
                "items": args.get("items", []),
                "expected_ship_date": args.get("expected_ship_date")
            },
            "preview": {
                "subject": f"EXPEDITE REQUEST – PO {args.get('po_number', 'Unknown')}",
                "body": f"Dear Supplier,\n\nWe kindly request expediting the shipment for PO {args.get('po_number')}.\nRequested ship date: {args.get('expected_ship_date', 'ASAP')}.\n\nLine items:\n" + "\n".join([f"- {item.get('name', 'Unknown')} x{item.get('quantity', 1)}" for item in args.get('items', [])])
            },
            "result_summary": f"Expedite request queued for PO {args.get('po_number', 'Unknown')}",
            "meta": {"version": "1.0.0", "locale": "en"}
        }

    def _mock_get_product_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock product details tool."""
        query = args.get("query", "").lower()

        # Mock product database
        products = {
            "switch": {
                "name": "Network Switch",
                "sku": "SW-1000",
                "description": "24-port Gigabit Ethernet switch",
                "price": 299.99,
                "stock": 15,
                "category": "Networking"
            },
            "router": {
                "name": "Wireless Router",
                "sku": "RT-2000",
                "description": "Dual-band WiFi 6 router",
                "price": 149.99,
                "stock": 8,
                "category": "Networking"
            },
            "cable": {
                "name": "Ethernet Cable",
                "sku": "CB-500",
                "description": "Cat6 Ethernet cable, 10ft",
                "price": 12.99,
                "stock": 50,
                "category": "Cabling"
            }
        }

        # Find matching product
        for key, product in products.items():
            if key in query or query in product["name"].lower():
                return {
                    "status": "success",
                    "result_type": "product_details",
                    "data": product,
                    "result_summary": f"Found product: {product['name']} (SKU: {product['sku']})",
                    "meta": {"version": "1.0.0", "locale": "en"}
                }

        # No match found
        return {
            "status": "not_found",
            "result_type": "product_details",
            "data": {"query": query},
            "result_summary": f"No product found matching: {query}",
            "meta": {"version": "1.0.0", "locale": "en"}
        }

    def _mock_order_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock order status tool."""
        po_number = args.get("po_number", "Unknown")

        # Mock different statuses
        import random
        statuses = ["processing", "shipped", "delivered", "delayed"]
        status = random.choice(statuses)

        return {
            "status": "success",
            "result_type": "order_status",
            "data": {
                "po_number": po_number,
                "status": status,
                "last_updated": "2025-11-03",
                "estimated_delivery": "2025-11-10" if status != "delivered" else None
            },
            "result_summary": f"Order {po_number} status: {status}",
            "meta": {"version": "1.0.0", "locale": "en"}
        }