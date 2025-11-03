# 🧩 MCP Server — Production Implementation Guide

## Purpose
Design a **production-ready MCP server** that executes company tools (product lookup, expedite email, etc.) reliably for any LLM or client (LM Studio, Streamlit, etc.).

---

## Architecture Overview

**Container:** Dockerized Python service (stdio or HTTP mode)

**Responsibilities:**
- Host all company tool logic
- Handle validations, defaults, and error resilience
- Provide deterministic JSON responses
- Serve as the single source of truth for AI tool execution

---

## Folder Structure

```
mcp-server/
├── Dockerfile
├── requirements.txt
├── main.py              # entrypoint
├── tools/
│   ├── __init__.py
│   ├── base.py          # shared validators, utils
│   ├── product_details.py
│   ├── expedite_email.py
│   └── ... other tools ...
├── schemas/
│   ├── base_schemas.py
│   └── expedite_schema.py
├── utils/
│   ├── logging.py
│   ├── email_client.py
│   ├── http_client.py
│   └── ...
└── tests/
    └── test_tools.py
```

---

## Key Design Principles

### 1. Deterministic JSON Output

Each tool returns the same contract:

```json
{
  "status": "success" | "queued" | "error",
  "result_type": "expedite_email",
  "message_id": "EXP-2025-0001",
  "data": { ... },
  "preview": { "subject": "...", "body": "..." },
  "result_summary": "Expedite request queued for PO ZS-2322",
  "meta": { "version": "1.0.0", "locale": "pl" }
}
```

### 2. Input Validation (Pydantic)

```python
from pydantic import BaseModel, EmailStr, Field

class ExpediteEmailArgs(BaseModel):
    supplier_email: EmailStr
    po_number: str
    items: list[dict] = Field(default_factory=list)
    expected_ship_date: str | None = None
    requester_name: str
    requester_email: EmailStr
```

### 3. Error Handling

Wrap all tool logic with decorators:

```python
def safe_tool(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return [TextContent(text=json.dumps(result, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(text=json.dumps({
                "status":"error",
                "result_type":func.__name__,
                "message":str(e)
            }, ensure_ascii=False))]
    return wrapper
```

### 4. Logging & Metrics

- Log to stdout in JSON lines format (`tool`, `duration_ms`, `status`)
- Optional: export metrics to file or HTTP endpoint

### 5. Configuration & Secrets

Use `.env` + environment variables:
```
SMTP_HOST=smtp.gmail.com
SMTP_USER=ops@example.com
SMTP_PASS=****
ERP_API_KEY=****
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
```

---

## Testing Strategy

- **Unit tests** per tool with dummy data
- **Schema validation tests**
- **Integration tests** for email sending (mocked)
- **Load test** using 10 parallel expedite calls

---

## Acceptance Criteria

✅ Deterministic JSON contract  
✅ Strict Pydantic validation  
✅ Graceful error fallback  
✅ Docker image builds successfully  
✅ Works via LM Studio MCP integration  
✅ Logs contain latency & status per tool  
