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