# 🧰 MCP Server — Adding New Tools Guide

## Purpose
Guide for developers integrating new tools into the MCP server safely and consistently.

---

## Workflow Summary

1. Create new tool module in `tools/`
2. Define validated input & output schemas
3. Implement core logic + safe error handling
4. Register tool in `main.py`
5. Add unit tests

---

## Example — Add a “Check Order Status” Tool

### 1️⃣ Schema

```python
# schemas/order_status_schema.py
from pydantic import BaseModel

class OrderStatusArgs(BaseModel):
    po_number: str
```

### 2️⃣ Tool Implementation

```python
# tools/order_status.py
from mcp.types import TextContent
from schemas.order_status_schema import OrderStatusArgs
from utils.http_client import fetch_order_status
import json

def run_order_status(args: dict):
    validated = OrderStatusArgs(**args)
    status_data = fetch_order_status(validated.po_number)
    result = {
        "status": "success",
        "result_type": "order_status",
        "data": status_data,
        "result_summary": f"Order {validated.po_number} status: {status_data['status']}",
        "meta": {"version": "1.0.0"}
    }
    return [TextContent(text=json.dumps(result, ensure_ascii=False))]
```

### 3️⃣ Register Tool

```python
# main.py
from tools import order_status

@server.tool()
def check_order_status(args: dict):
    return order_status.run_order_status(args)
```

### 4️⃣ Test It

```python
def test_check_order_status():
    result = check_order_status({"po_number": "ZO-2025-12"})
    data = json.loads(result[0].text)
    assert data["status"] == "success"
```

---

## Tool Template

```python
def run_toolname(args: dict):
    try:
        validated = InputSchema(**args)
        ...  # core logic
        return [TextContent(text=json.dumps(result, ensure_ascii=False))]
    except ValidationError as e:
        return [TextContent(text=json.dumps({"status":"error","message":str(e)}, ensure_ascii=False))]
    except Exception as e:
        return [TextContent(text=json.dumps({"status":"error","message":str(e)}, ensure_ascii=False))]
```

---

## Acceptance Criteria

✅ Follows JSON output contract  
✅ Validated inputs (Pydantic)  
✅ Handles exceptions gracefully  
✅ Unit tested with sample data  
✅ Appears automatically in MCP tool registry  
