# 🚀 Streamlit Chat App - MCP HTTP Integration Implementation Guide

## 🎯 Mission
Convert the Streamlit chat app from using LM Studio's MCP stdio integration to making direct HTTP calls to the MCP server, enabling both Streamlit and LM Studio to access the same server simultaneously.

## 📋 Current State Analysis

### MCP Server Changes (Already Completed)
- ✅ Server now supports both HTTP and stdio modes via `MCP_TRANSPORT` environment variable
- ✅ HTTP mode runs on port 8000 using FastMCP's `streamable_http_app`
- ✅ Stdio mode remains for LM Studio backward compatibility
- ✅ Tools: `get_product_details` and `send_expedite_email`

### Current Streamlit App Architecture
Based on `Streamlit_App_Improvement_Guide.md`, the app currently:
- Uses LM Studio's MCP integration for tool execution
- Implements two-call pattern: tool discovery → tool execution → formatting
- Has components: `chat_ui.py`, `tool_display.py`, `history.py`
- Has services: `orchestrator.py`, `mcp_client.py`

## 🔧 Required Changes

### 1. Replace MCP Client Service
**File:** `services/mcp_client.py`

**Current:** Uses LM Studio's MCP stdio integration
**New:** Direct HTTP client to MCP server

```python
import httpx
import json
from typing import Dict, Any, List
from mcp.types import CallToolRequest, CallToolResult

class MCPHTTPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server"""
        response = await self.client.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via HTTP"""
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )

        response = await self.client.post(
            f"{self.base_url}/tools/call",
            json=request.dict(),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        result = CallToolResult(**response.json())
        # Extract the actual tool result from MCP response
        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return {}

    async def close(self):
        await self.client.aclose()
```

### 2. Update Orchestrator Service
**File:** `services/orchestrator.py`

**Changes Needed:**
- Replace LM Studio MCP calls with HTTP client calls
- Maintain the same two-call pattern logic
- Handle HTTP errors gracefully
- Add connection retry logic

```python
# Before: LM Studio integration
# resp1 = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

# After: Direct HTTP tool calls
async def execute_tools_http(self, tool_calls: List[Dict]) -> List[Dict]:
    """Execute tools via HTTP instead of LM Studio"""
    results = []
    for tool_call in tool_calls:
        try:
            result = await self.mcp_client.call_tool(
                tool_call["function"]["name"],
                json.loads(tool_call["function"]["arguments"])
            )
            results.append({
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result)
            })
        except Exception as e:
            results.append({
                "tool_call_id": tool_call["id"],
                "content": json.dumps({"error": str(e)})
            })
    return results
```

### 3. Update App Configuration
**File:** `config/constants.py`

**Add:**
```python
# MCP Server Configuration
MCP_SERVER_URL = "http://localhost:8000"  # Or configurable via env var
MCP_TOOLS_CACHE_TTL = 300  # Cache tools list for 5 minutes
```

### 4. Update Main App Logic
**File:** `app.py`

**Changes:**
- Initialize HTTP MCP client instead of LM Studio client
- Update tool execution flow to use HTTP calls
- Add error handling for MCP server connectivity
- Maintain same UI/UX flow

### 5. Add Health Check Component
**New File:** `services/health_check.py`

```python
import httpx
import asyncio
from typing import Optional

class MCPHealthChecker:
    async def check_server_health(self, url: str) -> bool:
        """Check if MCP server is responding"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                return response.status_code == 200
        except:
            return False

    async def wait_for_server(self, url: str, max_attempts: int = 30) -> bool:
        """Wait for MCP server to become available"""
        for attempt in range(max_attempts):
            if await self.check_server_health(url):
                return True
            await asyncio.sleep(1)
        return False
```

## 🔄 MCP HTTP Protocol Details

### Tool Listing
```http
GET /tools
Response: {"tools": [{"name": "get_product_details", "description": "...", ...}]}
```

### Tool Execution
```http
POST /tools/call
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "get_product_details",
    "arguments": {"query": "switch"}
  }
}

Response:
{
  "content": [
    {
      "type": "text",
      "text": "{\"status\": \"success\", \"result_type\": \"product_details\", ...}"
    }
  ]
}
```

## 🧪 Testing Strategy

### Unit Tests
- Test MCP HTTP client connection
- Test tool execution with mock responses
- Test error handling (server down, invalid responses)

### Integration Tests
- Full chat flow with actual MCP server
- Tool execution verification
- Error scenarios (server restart, network issues)

### Acceptance Criteria
- ✅ Chat interface works without LM Studio dependency
- ✅ Tools execute via HTTP calls
- ✅ Same two-call pattern maintained
- ✅ Error handling for server connectivity issues
- ✅ UI shows tool results and formatting
- ✅ Session state preserved across server restarts

## 🚀 Deployment Considerations

### Docker Compose Setup
```yaml
version: '3.8'
services:
  mcp-server:
    image: local/mcp-tools:dev
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http

  streamlit-app:
    build: ./streamlit-app
    ports:
      - "8501:8501"
    depends_on:
      - mcp-server
    environment:
      - MCP_SERVER_URL=http://mcp-server:8000
```

### Environment Variables
- `MCP_SERVER_URL`: Configurable server endpoint
- `MCP_REQUEST_TIMEOUT`: HTTP request timeout
- `MCP_MAX_RETRIES`: Retry attempts for failed requests

## ⚠️ Migration Notes

### Backward Compatibility
- Keep LM Studio integration as fallback option
- Add feature flag to switch between HTTP and LM Studio modes

### Performance Considerations
- HTTP calls add latency vs stdio
- Implement connection pooling
- Cache tools list to reduce requests

### Error Handling
- Graceful degradation when MCP server is down
- User-friendly error messages
- Automatic retry logic for transient failures

## 📚 Reference Materials

- MCP HTTP Transport Spec: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports/
- Current Streamlit Guide: `Streamlit_App_Improvement_Guide.md`
- MCP Server Implementation: `mcp-tools/` directory
- Tool Response Format: See `utils/tool_utils.py`

## 🎯 Success Metrics

- Zero regression in chat functionality
- Tool execution works reliably over HTTP
- Improved error handling and user feedback
- Maintainable codebase with clear separation of concerns

---

**Priority Order:**
1. Implement HTTP MCP client (`services/mcp_client.py`)
2. Update orchestrator to use HTTP calls
3. Add health checks and error handling
4. Update configuration and deployment
5. Add comprehensive testing

**Estimated Effort:** 2-3 days for full implementation and testing.</content>
<parameter name="filePath">/Users/yogiewski/Projects/flow-mcp-server/STREAMLIT_MCP_HTTP_INTEGRATION_GUIDE.md