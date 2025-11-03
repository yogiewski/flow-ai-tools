# 💬 Streamlit App — AI Tool Orchestration Guide

## Purpose
Upgrade the existing Streamlit app into a **robust orchestration front-end** for MCP tools (via LM Studio).  
Focus: stability, session handling, and clear two-call pattern.

---

## Architecture

```
streamlit-app/
├── app.py
├── components/
│   ├── chat_ui.py
│   ├── tool_display.py
│   └── history.py
├── services/
│   ├── orchestrator.py
│   └── mcp_client.py
├── config/
│   ├── constants.py
│   └── theme.toml
└── prompts/
    ├── formatter_prompt_v2.md
    └── system_prompts/
```

---

## Core Logic Flow

### 1️⃣ Initialization

```python
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": PROMPT_V2}]
```

### 2️⃣ First Completion (allow tools)

```python
resp1 = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
```

### 3️⃣ Append tool calls

```python
messages.append({
  "role": "assistant",
  "tool_calls": [
    {"id": t.id, "type": t.type, "function": {
        "name": t.function.name, "arguments": t.function.arguments
    }} for t in tool_calls
  ]
})
```

### 4️⃣ Execute tools & append `role:"tool"`

Call MCP or LM Studio’s server automatically and append:

```python
messages.append({
  "role": "tool",
  "tool_call_id": t.id,
  "content": result_json_string
})
```

### 5️⃣ Second Completion (format-only)

```python
resp2 = client.chat.completions.create(
  model=MODEL,
  messages=messages,
  tools=TOOLS,
  tool_choice="none"
)
```

---

## UX Enhancements

- Use `st.chat_message(role)` for chat-like feel
- Collapsible panels for tool previews (`result_summary`, `preview`)
- Message history persisted in `st.session_state`
- Retry button for failed tool results

---

## Advanced Features

| Feature | Description |
|----------|--------------|
| **Tool chain depth guard** | prevent infinite loops (`max_tool_chain=3`) |
| **Language switcher** | use `locale` in tool results for formatting |
| **Auto slot filling** | extract PO, qty, email via regex before call |
| **Error panels** | show failed tool JSON with human hint |
| **Telemetry** | optional: log chat stats, tool durations |

---

## Acceptance Criteria

✅ Two-pass tool orchestration implemented  
✅ Messages persisted across reruns  
✅ Handles multiple tool results gracefully  
✅ UI shows formatted confirmations  
✅ Works with LM Studio MCP + local model  
