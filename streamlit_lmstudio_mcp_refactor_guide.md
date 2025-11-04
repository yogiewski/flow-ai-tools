# Refactor Guide – Streamlit Chat via LM Studio + MCP as Single Source of Truth

> Target audience: Coding Agent  
> Goal: Refactor the Streamlit app so **LM Studio** mediates all tool use, while **MCP server** remains the single source of truth. Add per‑prompt controls to decide **if** MCP tools are used and **which** tools (from the selected MCP server) are allowed.

---

## 0) High‑level architecture

- **LM Studio (host)** exposes an OpenAI‑compatible API (`/v1/responses`). It can call **MCP servers** you register in `~/.lmstudio/mcp.json`.
- **MCP Server (Docker)** implements all business tools. It may optionally expose a lightweight **read‑only /tools catalog endpoint** to list available tools for UI population.
- **Streamlit App (Docker)** = very thin client. It:
  - maintains chat history & prompt presets,
  - for each message calls **LM Studio** with a `tools: [{ type: "mcp", server_label: <label>, allowed_tools: [...] }]` block **only if enabled for the chosen prompt**, otherwise omits tools,
  - never calls tools directly.

**Why**: Tool logic lives in MCP. LM Studio routes tool calls. Streamlit stays simple.

---

## 1) User stories & acceptance criteria

1. **Prompt presets** (aka AI tools) have metadata:
   - `title`, `description`, `system/instructions`, `temperature` (optional),
   - `use_mcp` (bool),
   - `mcp_server_label` (string; must exist in LM Studio `mcp.json`),
   - `allowed_tools` (list of tool names; optional empty → allow all).

   **AC**: Admin can CRUD presets in a Prompts Manager page. Presets serialize to a persistent store (JSON, SQLite, or Supabase later).

2. **MCP discovery** for UI population:
   - App presents a **server selector** (dropdown) sourced from known labels (config/env) and (optionally) from a **catalog endpoint** on each MCP server (e.g., `GET http://<mcp>/tools`).
   - When a server is selected, the app loads tools list → presents a **multi‑select** to choose `allowed_tools`.

   **AC**: If discovery fails, show a warning and allow manual text input for tool names. Cache last known tool list.

3. **Chat**:
   - When user picks a preset, the chat page includes that preset’s options.
   - If `use_mcp=false` → call LM Studio without `tools`.
   - If `use_mcp=true` → include `{type:"mcp", server_label, allowed_tools}` in `tools`.
   - Display assistant reply from `output_text` (or last message content fallback).

   **AC**: Chat works with and without MCP tools. Errors are surfaced cleanly.

4. **Docker/Networking**:
   - Streamlit container reaches LM Studio via `http://host.docker.internal:1234`.
   - On Linux add `extra_hosts: ["host.docker.internal:host-gateway"]`.
   - MCP container exposes its HTTP port and is referenced by LM Studio `mcp.json`.

   **AC**: End‑to‑end works on Mac/Windows; Linux path tested with `extra_hosts`.

---

## 2) Data model (local JSON first; swappable later)

**Schema: `prompts.json`**
```json
{
  "version": 1,
  "presets": [
    {
      "id": "uuid",
      "title": "Support – Industrial Automation",
      "description": "B2B email support agent specialized in switchgear",
      "instructions": "<system prompt>",
      "temperature": 0.2,
      "use_mcp": true,
      "mcp_server_label": "my-mcp",
      "allowed_tools": ["lookup_order", "get_weather"]
    }
  ]
}
```

- Keep an in‑memory index: `{ id → preset }`.
- Later replace with SQLite or Supabase; keep the interface stable (repository pattern).

---

## 3) Configuration & environment variables

Create `.env` loaded by Streamlit:
```
LMSTUDIO_BASE_URL=http://host.docker.internal:1234
LMSTUDIO_ENDPOINT=/v1/responses
# Comma-separated MCP labels you expect LM Studio to know about (must match ~/.lmstudio/mcp.json)
MCP_SERVER_LABELS=my-mcp,analytics-mcp
# Optional: direct URLs for tool catalog if you implement /tools
MCP_CATALOG_my-mcp=http://mcp:8000/tools
MCP_CATALOG_analytics-mcp=http://analytics-mcp:8010/tools
```

**Note**: If you can’t expose a `/tools` endpoint, still list labels so the UI offers them; tools list can be typed manually.

---

## 4) MCP tool discovery contract (lightweight optional endpoint)

Add (or confirm) a **read‑only** endpoint in the MCP server:

- `GET /tools` → returns:
```json
{
  "server_label": "my-mcp",
  "tools": [
    { "name": "lookup_order", "description": "Finds order by ID" },
    { "name": "rfq_quote", "description": "Creates RFQ draft" }
  ]
}
```
- Keep it unauthenticated on a trusted network or secure with a header token.
- This does **not** execute tools—just lists metadata for UI.

If not feasible, maintain a static JSON config (fallback).

---

## 5) Streamlit UI/UX changes

### 5.1 Prompts Manager page
- Table of presets with actions (Edit, Duplicate, Delete).
- **Editor form** fields:
  - Title, Description
  - System Instructions (textarea)
  - Temperature (slider)
  - **Use MCP tools** (checkbox)
  - **MCP server** (select from `MCP_SERVER_LABELS`)
  - **Allowed tools** (multi‑select → populated from `/tools` for chosen server; fallback manual entry)
- Save validates: if `use_mcp=true` then `mcp_server_label` must be set.

### 5.2 Chat page
- Preset selector (dropdown by title; shows summary of MCP settings)
- Message list (Streamlit chat components)
- Input box
- On send: builds payload to LM Studio as per preset (section 6).

---

## 6) LM Studio request builder

Pseudo‑Python:
```python
payload = {
  "model": selected_model,  # e.g., "openai/gpt-oss-20b"
  "input": messages,        # list[ {role, content} ] including system/instructions
  "stream": False
}

if preset.use_mcp:
    tool_block = {
        "type": "mcp",
        "server_label": preset.mcp_server_label
    }
    if preset.allowed_tools:  # non-empty list
        tool_block["allowed_tools"] = preset.allowed_tools
    payload["tools"] = [tool_block]

# Optional: guidance
# payload["instructions"] = preset.instructions  (if you use responses API style)
# or prepend a system message in input.
```

**Note**: For the Responses API, you can pass `instructions` separately and keep `input` as chat history, or put a system message into `input`. Choose one and be consistent.

---

## 7) Error handling & observability

- Surface HTTP errors from LM Studio: status + body snippet.
- If MCP discovery fails: show non‑blocking warning; allow manual tool names.
- Log payloads (minus user PII) to a rolling file for debugging.
- Add a debug panel that prints the final payload sent to LM Studio (collapsible).

---

## 8) Docker & networking

### 8.1 docker-compose (sketch)
```yaml
version: '3.8'
services:
  streamlit:
    build: ./app
    ports: ["8501:8501"]
    env_file: .env
    volumes:
      - ./data:/app/data
    extra_hosts:
      - "host.docker.internal:host-gateway"  # needed on Linux
    depends_on:
      - mcp

  mcp:
    image: flow-mcp-server:latest
    ports: ["8000:8000"]
    stdin_open: true
    tty: true
    environment:
      - MCP_TRANSPORT=both  # Run both stdio (for LM Studio) and HTTP (for Streamlit)
    command: sleep infinity  # Keep container alive for docker exec
```

### 8.2 LM Studio Configuration
- Runs on host at `http://localhost:1234`.
- Streamlit accesses it as `http://host.docker.internal:1234`.
- LM Studio `~/.lmstudio/mcp.json` contains:
```json
{
  "mcpServers": {
    "local-mcp-tools": {
      "command": "docker",
      "args": ["exec", "-i", "local-mcp-tools", "python", "main.py"]
    }
  }
}
```
- **Note**: Container must be running (use docker-compose or manual `docker run` with `sleep infinity`)

---

## 9) Code skeleton

### 9.1 `services/lmstudio_client.py`
```python
import os, requests

BASE = os.getenv("LMSTUDIO_BASE_URL", "http://host.docker.internal:1234")
EP = os.getenv("LMSTUDIO_ENDPOINT", "/v1/responses")
URL = f"{BASE}{EP}"

def chat(model: str, messages: list, use_mcp: bool, server_label: str | None, allowed_tools: list[str] | None, instructions: str | None = None):
    payload = {
        "model": model,
        "input": messages,
        "stream": False,
    }
    if instructions:
        payload["instructions"] = instructions
    if use_mcp and server_label:
        block = {"type": "mcp", "server_label": server_label}
        if allowed_tools:
            block["allowed_tools"] = allowed_tools
        payload["tools"] = [block]
    r = requests.post(URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # prefer output_text; fallback
    text = data.get("output_text")
    if not text:
        # naive fallback; adapt to your exact response schema
        text = next((it.get("content") for it in data.get("output", []) if it.get("type") == "message"), "")
    return text, data
```

### 9.2 `services/mcp_catalog.py`
```python
import os, requests

def get_server_labels() -> list[str]:
    raw = os.getenv("MCP_SERVER_LABELS", "")
    return [s.strip() for s in raw.split(",") if s.strip()]

def get_tools_for_label(label: str) -> list[dict]:
    # Try optional catalog URL first
    key = f"MCP_CATALOG_{label}"
    url = os.getenv(key)
    if not url:
        return []  # fallback → manual
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        tools = data.get("tools", [])
        return tools
    except Exception:
        return []
```

### 9.3 `repo/prompts_repo.py`
```python
import json, os, uuid
PATH = os.path.join("data", "prompts.json")

def load():
    if not os.path.exists(PATH):
        return {"version":1, "presets": []}
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save(doc):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

def upsert_preset(preset):
    doc = load()
    if not preset.get("id"):
        preset["id"] = str(uuid.uuid4())
    doc["presets"] = [p for p in doc["presets"] if p["id"] != preset["id"]] + [preset]
    save(doc)

def list_presets():
    return load().get("presets", [])
```

### 9.4 `pages/01_Prompts_Manager.py` (UI sketch)
```python
import streamlit as st
from repo.prompts_repo import list_presets, upsert_preset
from services.mcp_catalog import get_server_labels, get_tools_for_label

st.title("📝 Prompts Manager")

presets = {p["title"]: p for p in list_presets()}
selected = st.selectbox("Select preset", ["<New>"] + list(presets.keys()))

if selected != "<New>":
    preset = dict(presets[selected])
else:
    preset = {"title":"", "description":"", "instructions":"", "temperature":0.2, "use_mcp":False, "mcp_server_label":"", "allowed_tools":[]}

preset["title"] = st.text_input("Title", preset.get("title",""))
preset["description"] = st.text_area("Description", preset.get("description",""))
preset["instructions"] = st.text_area("System Instructions", preset.get("instructions",""), height=200)
preset["temperature"] = st.slider("Temperature", 0.0, 1.0, float(preset.get("temperature",0.2)))

preset["use_mcp"] = st.checkbox("Use MCP tools", value=bool(preset.get("use_mcp", False)))
labels = get_server_labels()
if preset["use_mcp"]:
    preset["mcp_server_label"] = st.selectbox("MCP server", labels, index=(labels.index(preset.get("mcp_server_label")) if preset.get("mcp_server_label") in labels else 0) if labels else 0)
    tools = get_tools_for_label(preset.get("mcp_server_label")) if labels else []
    tool_names = [t["name"] for t in tools]
    preset["allowed_tools"] = st.multiselect("Allowed tools (optional)", tool_names, default=[t for t in preset.get("allowed_tools", []) if t in tool_names])
    if not tools:
        st.info("No catalog found. You can still type tool names manually (comma-separated):")
        manual = st.text_input("Manual tool names", ", ".join(preset.get("allowed_tools", [])))
        preset["allowed_tools"] = [s.strip() for s in manual.split(",") if s.strip()]

if st.button("Save preset"):
    upsert_preset(preset)
    st.success("Saved.")
```

### 9.5 `Home.py` (Chat UI sketch)
```python
import streamlit as st
from repo.prompts_repo import list_presets
from services.lmstudio_client import chat

st.set_page_config(page_title="Flow Chat", layout="wide")
st.title("💬 Flow Chat")

presets = list_presets()
by_title = {p["title"]: p for p in presets}
choice = st.selectbox("Preset", list(by_title.keys())) if presets else None
preset = by_title.get(choice) if choice else None

if "history" not in st.session_state:
    st.session_state.history = []

user_text = st.chat_input("Type your message…")
if user_text:
    st.session_state.history.append({"role":"user","content": user_text})
    instructions = preset.get("instructions") if preset else None
    use_mcp = bool(preset.get("use_mcp")) if preset else False
    server_label = preset.get("mcp_server_label") if preset else None
    allowed = preset.get("allowed_tools") if preset else None

    reply, raw = chat(
        model="openai/gpt-oss-20b",
        messages=st.session_state.history,
        use_mcp=use_mcp,
        server_label=server_label,
        allowed_tools=allowed,
        instructions=instructions,
    )
    st.session_state.history.append({"role":"assistant","content": reply})

for msg in st.session_state.history:
    st.chat_message(msg["role"]).write(msg["content"])
```

---

## 10) Testing checklist

- [ ] MCP server `/tools` returns expected shape; otherwise manual mode works.
- [ ] Preset with `use_mcp=false` → model answers without calling tools.
- [ ] Preset with `use_mcp=true`, empty `allowed_tools` → tools allowed (server‑wide).
- [ ] Preset with `use_mcp=true`, non‑empty `allowed_tools` → model constrained.
- [ ] Linux path: `extra_hosts` present; Streamlit reaches LM Studio.
- [ ] Error surfaces properly when LM Studio is down.

---

## 11) Future improvements

- Add **prompt groups** and per‑group default MCP server.
- Persist chat transcripts (with tool metadata) for audit.
- Add **streaming** UI using SSE if LM Studio exposes streaming for `/v1/responses`.
- Role‑based presets (read‑only for users; editable for admins).
- Optional: migrate prompts to Supabase with RLS.

---

## 12) Handoff summary for the Coding Agent

1. Implement the data model and Prompts Manager.
2. Implement MCP catalog client (optional endpoint) with fallback manual entry.
3. Wire the LM Studio client with per‑preset tool block injection.
4. Confirm Docker networking and LM Studio config (`mcp.json`).
5. Validate all acceptance criteria and the testing checklist.

---

## 13) Implementation phases (incremental plan)

### Phase 1 — Minimal working example (MVP)
**Objective:** Ship a thin chat that always allows MCP tool use for the selected server; no per‑tool allow‑list yet.

**Scope:**
- Use existing **Chat page** and **LM Studio client**.
- For any preset with `use_mcp = true`, send a single `tools` block with `{ type: "mcp", server_label: <label> }` and **omit** `allowed_tools` (LM Studio then allows all tools from that server).
- Skip MCP catalog discovery and multi‑select (hardcode server label via preset).
- Add the **Tool‑first system prompt** (below) to every tool‑using preset.

**Acceptance:**
- User can select a preset → send a message → model invokes MCP tools and returns answer.
- If the job needs a tool that does not exist, the model **asks for clarifying details** (per the system prompt) instead of hallucinating.

**Recommended tool‑first system prompt (paste into preset.instructions):**
```
You are **Tool‑First Operations Assistant** for industrial automation workflows.

POLICY – TOOL USE ONLY
- You MUST rely exclusively on the MCP tools provided by the system. Use tools to obtain facts, perform actions, and generate results.
- Do NOT invent data, simulate tool outputs, or fabricate confirmations.
- If no suitable tool exists for the requested job, ask a single, precise clarifying question that helps pick the correct tool or gather the missing detail. Do not proceed without a tool result.

TASK CONTEXT (fill if available)
- Intended action: {{ACTION_PLACEHOLDER}} (e.g., "send email", "ask about product", "lookup order", "generate RFQ draft").
- Target/subject: {{TARGET_PLACEHOLDER}} (e.g., client email, SKU, order ID).
- Constraints: {{CONSTRAINTS_PLACEHOLDER}} (e.g., language, tone, compliance notes).

OUTPUT RULES
- Summarize outcomes strictly based on tool outputs. If the tool returns an ID, include it. If the tool indicates failure, report the failure and propose next steps.
- If no relevant tool is available, respond with: "I don’t have a tool for this yet. To proceed, please provide {{MISSING_DETAIL}} or choose an available tool." (Then list the closest matching available tools if known.)
- Never claim actions were done unless a tool confirmed completion.

SAFETY/CONFIRMATION
- For any destructive or externally visible action (e.g., sending an email), first prepare a draft and ask for human confirmation unless the user explicitly authorizes immediate execution.
```

**Minimal payload example (Phase‑1):**
```json
{
  "model": "openai/gpt-oss-20b",
  "instructions": "<Paste the Tool‑First prompt above>",
  "input": [
    {"role": "user", "content": "Please {{ACTION_PLACEHOLDER}} about {{TARGET_PLACEHOLDER}}."}
  ],
  "tools": [
    { "type": "mcp", "server_label": "my-mcp" }
  ],
  "stream": false
}
```

**UI note:** In Phase‑1, the Prompts Manager shows a checkbox **Use MCP tools** and a simple **Server label** dropdown. Hide the per‑tool allow‑list UI until Phase‑2.

---

### Phase 2 — Per‑tool allow‑lists & live discovery
**Objective:** Add the optional `/tools` catalog query and multi‑select **Allowed tools** for each preset.

**Scope:**
- Implement `services/mcp_catalog.get_tools_for_label(label)` against `MCP_CATALOG_*` URLs.
- Show a multi‑select to pick `allowed_tools`. Fallback to manual entry if discovery fails.
- Update LM Studio payload to include `allowed_tools` when non‑empty.

**Acceptance:**
- When `allowed_tools` is empty → all tools allowed (Phase‑1 behavior).
- When non‑empty → the model can only call those specific tools.

---

### Phase 3 — Persistence, streaming, and audit
**Objective:** Harden and enhance the system.

**Scope:**
- Swap JSON → SQLite/Supabase for presets.
- Add streaming UI (if `/v1/responses` streaming is enabled) and a debug panel that shows the final payload.
- Log transcripts with tool call summaries for audit.
- Optional: role‑based access (read‑only presets for standard users).

**Acceptance:**
- Data survives restarts; auditing available; streaming tested.

---

## 14) Prompt templates (ready to copy)

**A) Action‑oriented tool‑first preset (system instructions)**
```
You are **Tool‑First Operations Assistant** for industrial automation workflows.

POLICY – TOOL USE ONLY
- Rely exclusively on MCP tools provided by the system. Do NOT invent or simulate outputs.
- If no suitable tool exists, ask one precise clarifying question to identify the correct tool or missing detail, then wait.

TASK CONTEXT
- Intended action: {{ACTION_PLACEHOLDER}}
- Target/subject: {{TARGET_PLACEHOLDER}}
- Constraints: {{CONSTRAINTS_PLACEHOLDER}}

OUTPUT RULES
- Report only what tools return; include IDs and error messages verbatim when helpful.
- If no tool fits, respond: "I don’t have a tool for this yet. To proceed, please provide {{MISSING_DETAIL}} or select an available tool." Do not hallucinate.

SAFETY/CONFIRMATION
- For outward‑facing actions (e.g., sending email), prepare a draft and ask for approval unless the user granted explicit authorization.
```

**B) User message starter (Phase‑1, example)**
```
Please {{ACTION_PLACEHOLDER}} regarding {{TARGET_PLACEHOLDER}}. If additional details are required, ask me exactly what you need.
```

---

## 15) MCP Server – Implementation Status & Guide

> **Status**: ✅ **IMPLEMENTED & TESTED**
>
> The MCP server (`flow-mcp-server`) is production-ready and fully compatible with this refactor guide. See implementation checklist below.

### 15.0 Current Implementation Summary

**✅ Completed:**
- Dual transport support (stdio + HTTP via `MCP_TRANSPORT` environment variable)
- Registered tools: `get_product_details`, `send_expedite_email`
- `/health` endpoint: Returns server status
- `/tools` endpoint: Returns tool catalog with full metadata (names, descriptions, args, returns)
- Pydantic validation for all tool inputs
- Structured error responses with status codes
- Safe tool decorator with timeout protection (30s)
- Deterministic `request_id` and `timestamp` tracking
- Support for `dry_run` and `confirm` flags in email tool

**Ready for Streamlit Integration:**
- HTTP server on port 8000 accessible via `http://localhost:8000` or `http://mcp:8000` from Docker
- Full tool catalog available at `GET /mcp/tools` (with enhanced metadata)
- MCP protocol compatible with LM Studio at stdio/HTTP level

### 15.1 MCP Server – Implementation Guide (for the Coding Agent)

> Goal: Adjust the MCP server so it's the single source of truth, discoverable by the Streamlit UI, and robust for LM Studio tool calling. This section focuses on **non-invasive** additions (catalog, health, consistency, safety) and recommended conventions for the existing tool methods.

### 15.1 Capabilities & contracts

1) **Stable tool names & semantics**
- Keep tool names short, kebab/snake case (e.g., `lookup_order`, `rfq_create`).
- Each tool should have a single, clear responsibility and return a single result shape.
- Avoid breaking changes; instead, version tools (e.g., `rfq_create_v2`).

2) **Structured outputs**
- Prefer deterministic JSON objects: include `status` ("ok"|"error"), a `data` object, and an `error` object when relevant.
- Include stable fields like `tool`, `timestamp`, `request_id`.

3) **Idempotency & safety**
- Actions that cause side effects (email send, create order) should support a `dry_run` boolean and return a draft payload when `true`.
- Require an explicit `confirm=true` flag for destructive or externally visible actions; otherwise return a draft and a confirmation prompt.

4) **Errors**
- Normalize error responses: `{ "status": "error", "error": { "code": "…", "message": "…", "details": {…} } }`.
- Avoid HTTP 200 for failures; use appropriate status codes and include the JSON error body.

5) **Timeouts**
- Bound tool execution times; fail fast with actionable error messages.

6) **Audit logging**
- Log: tool name, args (with PII redaction), status, duration, request_id, and caller (if available).

---

### 15.2 Discovery endpoints (read‑only, optional but recommended)

Add a **catalog** and **health** endpoint (no tool execution):

- `GET /health` → `{ "status": "ok" }` (plus build/version).
- `GET /tools` → lists available tools with minimal metadata so the Streamlit UI can populate selectors.

**Example response (`/tools`):**
```json
{
  "server_label": "my-mcp",
  "version": "2025-11-04",
  "tools": [
    {
      "name": "lookup_order",
      "description": "Find order by its ID and return summary.",
      "args": {
        "order_id": {"type": "string", "required": true}
      },
      "returns": {"type": "object", "fields": ["order_id", "status", "customer", "lines"]},
      "category": "orders"
    },
    {
      "name": "rfq_create",
      "description": "Create RFQ draft from structured items.",
      "args": {
        "items": {"type": "array", "items": {"sku": "string", "qty": "number"}, "required": true},
        "dry_run": {"type": "boolean", "required": false}
      },
      "returns": {"type": "object", "fields": ["rfq_id", "draft", "warnings"]},
      "category": "sales"
    }
  ]
}
```

Security: Keep the catalog read‑only; if needed, require a simple header token.

---

### 15.3 FastAPI snippet (catalog + health)

```python
# app_catalog.py – add alongside your MCP server
from fastapi import FastAPI, Header, HTTPException
from typing import Optional

app = FastAPI(title="MCP Catalog")

CATALOG_TOKEN = None  # or os.getenv("CATALOG_TOKEN")
SERVER_LABEL = "my-mcp"

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Find order by its ID and return summary.",
        "args": {"order_id": {"type": "string", "required": True}},
        "returns": {"type": "object", "fields": ["order_id", "status", "customer", "lines"]},
        "category": "orders",
    },
    {
        "name": "rfq_create",
        "description": "Create RFQ draft from structured items.",
        "args": {
            "items": {"type": "array", "items": {"sku": "string", "qty": "number"}, "required": True},
            "dry_run": {"type": "boolean", "required": False},
        },
        "returns": {"type": "object", "fields": ["rfq_id", "draft", "warnings"]},
        "category": "sales",
    },
]

@app.get("/health")
def health():
    return {"status": "ok", "server_label": SERVER_LABEL}

@app.get("/tools")
def list_tools(authorization: Optional[str] = Header(default=None)):
    if CATALOG_TOKEN and authorization != f"Bearer {CATALOG_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"server_label": SERVER_LABEL, "version": "2025-11-04", "tools": TOOLS}
```

**Dockerfile (snippet):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app_catalog.py ./
RUN pip install fastapi uvicorn
CMD ["uvicorn", "app_catalog:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then expose `8000` and point the Streamlit app’s `MCP_CATALOG_my-mcp` env var to `http://mcp:8000/tools`.

---

### 15.4 Tool implementation recommendations

1) **Request schema validation**
- Validate arguments rigorously; return `400` with structured error JSON on invalid input.

2) **Action confirmation**
- For outward actions, implement `dry_run` and `confirm` flags. When `dry_run=true`, return the draft and an explicit message instructing the client to confirm.

3) **Pagination for list‑style tools**
- If a tool can return many items, support `page`, `page_size`, and include a `next_page_token` in the result.

4) **Localization**
- Accept a `locale` parameter and echo it back. Keep content language consistent.

5) **Deterministic IDs**
- Return stable `request_id` (e.g., ULID) and any created resource IDs.

6) **Rate limiting / backpressure**
- Consider minimal token bucket or 429 responses with `Retry-After` for protection.

7) **Observability**
- Add latency histograms and error counters (e.g., Prometheus) to monitor tool health.

8) **Long‑running jobs**
- Return `status=pending` + `job_id` quickly; add a `job_status(job_id)` tool to poll; avoid keeping the model waiting.

---

### 15.5 Consistency with the Streamlit prompts

- Ensure tool names listed by `/tools` **match exactly** those callable via MCP.
- Keep the descriptions short and action‑oriented; the Streamlit UI will show them next to the multi‑select.
- When a tool cannot perform a requested job, return a clear error payload with a suggested next step. This pairs with the app’s **tool‑first** prompt that forbids hallucination and encourages clarifying questions.

---

### 15.6 Test plan for MCP server

- **Unit tests** for argument validation (happy/edge cases).
- **Contract tests** for `/health` and `/tools` shapes.
- **Integration test**: run LM Studio against the MCP and call a trivial tool from the Streamlit app (Phase‑1: all tools allowed).
- **Failure modes**: simulate timeouts, 4xx/5xx, and verify the assistant surfaces actionable messages to the user.

---

### 15.7 Handoff checklist (MCP Server Implementation)

**✅ All items completed:**
- [x] `/health` and `/tools` endpoints live, documented, and reachable from Streamlit.
- [x] Tool names, args, and return shapes documented; alignment with UI placeholders.
- [x] Side‑effect tools support `dry_run` and `confirm` (email_expedite).
- [x] Error format standardized; timeouts and logging enabled.
- [x] Versioning strategy in place for future changes.

**Additional verifications:**
- [x] Dual transport mode (stdio for LM Studio, HTTP for Streamlit) working
- [x] All unit tests passing (5/5)
- [x] No deprecation warnings
- [x] Docker container runs with both modes simultaneously
- [x] LM Studio can discover and call tools via `docker exec`
- [x] Response format compatible with LM Studio expectations

---

## 16) Example: Side‑effect tool with `dry_run` / `confirm` (send_email)

This pattern prevents unintended actions and aligns the assistant’s **Tool‑First** policy.

### 16.1 Contract (request/response)

**Request**
```json
{
  "to": "client@example.com",
  "subject": "Order status",
  "body_markdown": "Hello...",
  "cc": ["sales@example.com"],
  "dry_run": true,
  "confirm": false,
  "locale": "en"
}
```

**Response (dry run)**
```json
{
  "status": "ok",
  "tool": "send_email",
  "request_id": "01JBN8M8M9K0A1NJQZ0A1WFH9B",
  "draft": {
    "to": "client@example.com",
    "subject": "Order status",
    "body_markdown": "Hello...",
    "cc": ["sales@example.com"],
    "attachments": []
  },
  "confirmation_hint": "Set confirm=true to send."
}
```

**Response (confirmed send)**
```json
{
  "status": "ok",
  "tool": "send_email",
  "request_id": "01JBN8M8M9K0A1NJQZ0A1WFH9B",
  "sent": true,
  "message_id": "<20251104.12345@mail.example.com>",
  "provider": "smtp"
}
```

**Response (error)**
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_RECIPIENT",
    "message": "Domain not allowed",
    "details": {"to": "client@bad-domain"}
  }
}
```

### 16.2 FastAPI tool implementation (simplified)

```python
# app_send_email.py – add to MCP server codebase
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

class SendEmailReq(BaseModel):
    to: EmailStr
    subject: str
    body_markdown: str
    cc: List[EmailStr] = []
    attachments: List[str] = []  # paths or IDs
    dry_run: bool = True
    confirm: bool = False
    locale: Optional[str] = None

@router.post("/tool/send_email")
def send_email(req: SendEmailReq):
    req_id = uuid.uuid7().hex  # or ulid

    # validation example
    if req.to.endswith("@bad-domain"):
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "error": {"code": "INVALID_RECIPIENT", "message": "Domain not allowed", "details": {"to": req.to}}
        })

    draft = {
        "to": req.to,
        "subject": req.subject,
        "body_markdown": req.body_markdown,
        "cc": req.cc,
        "attachments": req.attachments
    }

    if req.dry_run or not req.confirm:
        return {
            "status": "ok",
            "tool": "send_email",
            "request_id": req_id,
            "draft": draft,
            "confirmation_hint": "Set confirm=true to send."
        }

    # send via provider (SMTP/API). On success:
    message_id = f"<{datetime.utcnow().isoformat()}@mail.example.com>"
    return {
        "status": "ok",
        "tool": "send_email",
        "request_id": req_id,
        "sent": True,
        "message_id": message_id,
        "provider": "smtp"
    }
```

Mount the router in your FastAPI app and include it in the MCP server’s tool map.

### 16.3 Assistant + LM Studio usage (Phase‑1 all tools allowed)

**Preset system instructions (excerpt already provided in §14):**
> For outward‑facing actions (e.g., sending an email), prepare a draft and ask for approval unless explicitly authorized.

**User message**
```
Please {{ACTION_PLACEHOLDER}} regarding {{TARGET_PLACEHOLDER}}.
```

**LM Studio payload (excerpt)**
```json
{
  "model": "openai/gpt-oss-20b",
  "instructions": "<Tool-First prompt>",
  "input": [
    {"role":"user","content":"Please send email about order 123 to client@example.com"}
  ],
  "tools": [ {"type":"mcp", "server_label":"my-mcp"} ]
}
```

**Expected behavior**
- Model calls `send_email` with `dry_run=true` first, returns a draft.
- Assistant presents the draft and asks user to confirm.
- On user confirmation, assistant calls the tool again with `confirm=true` and reports the `message_id`.

---

## 17) Getting Started – Complete Setup Walkthrough

### 17.1 Prerequisites
- Docker installed and running
- LM Studio running on `localhost:1234`
- Python 3.11+ (for local development)

### 17.2 Quick Start – 5 Steps

**Step 1: Start the MCP Server Container**
```bash
cd /Users/yogiewski/Projects/flow-mcp-server/mcp-tools

# Build the image (if not already built)
docker build -t flow-mcp-server .

# Start container with both stdio + HTTP modes
docker run -d \
  -e MCP_TRANSPORT=both \
  -p 8000:8000 \
  --name local-mcp-tools \
  flow-mcp-server:latest \
  sleep infinity
```

**Step 2: Configure LM Studio**

Edit `~/.lmstudio/mcp.json`:
```json
{
  "mcpServers": {
    "local-mcp-tools": {
      "command": "docker",
      "args": ["exec", "-i", "local-mcp-tools", "python", "main.py"]
    }
  }
}
```

Then reload LM Studio to pick up the new config.

**Step 3: Verify Tools are Available**

In LM Studio, check that `local-mcp-tools` is listed and tools are discoverable:
- Open a chat
- Model should be able to see `get_product_details` and `send_expedite_email` tools

**Step 4: Verify HTTP Endpoint (for Streamlit)**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tools
```

**Step 5: Build & Start Streamlit App**

```bash
cd /path/to/streamlit-app
docker build -t flow-ai-chat .
docker run -d \
  -p 8501:8501 \
  -e LMSTUDIO_BASE_URL=http://host.docker.internal:1234 \
  -e MCP_SERVER_LABELS=local-mcp-tools \
  -e MCP_CATALOG_local-mcp-tools=http://localhost:8000/tools \
  --add-host=host.docker.internal:host-gateway \
  flow-ai-chat
```

Then open http://localhost:8501 in browser.

### 17.3 Troubleshooting

**LM Studio says "Connection closed"**
- Verify container is running: `docker ps | grep local-mcp-tools`
- Check container logs: `docker logs local-mcp-tools --tail 20`
- Ensure MCP_TRANSPORT=both or MCP_TRANSPORT=stdio (not http)

**Streamlit can't reach MCP**
- Check HTTP endpoint: `curl http://localhost:8000/tools`
- Verify container port mapping: `docker port local-mcp-tools`
- From Docker, use `http://mcp:8000` if using docker-compose

**Tools not showing in Streamlit UI**
- Verify `/tools` endpoint returns proper format: `curl http://localhost:8000/tools | jq`
- Check Streamlit logs for MCP discovery errors
- Fallback to manual tool name entry in Prompts Manager
