# Streamlit LLM Chat App — MVP Plan
### (For internal use & later FlowHub integration)

---

## 1. Objectives & Scope

- **Single-purpose Streamlit page-app** packaged in Docker.
- **Connect to a remote local LLM** via configurable **URL + port**.
- **Prompt presets**: view, select, edit, add, delete; stored locally as Markdown.
- **Chat UI** with message history and system prompt injection.
- **Nice-looking UI** (Streamlit theme + layout polish).
- **Future integration** with FlowHub (shared conventions: config, logging, API hooks).

---

## 2. Architecture Overview

| Component | Purpose |
|------------|----------|
| **Frontend** | Streamlit multi-page app |
| **Backend** | Internal LLM client adapters (OpenAI-like, Ollama, LM Studio) |
| **Storage** | Local prompt Markdown files + optional SQLite for metadata |
| **Containerization** | Dockerfile + docker-compose |
| **Config** | `.env` → environment vars → `.env.local` → Streamlit secrets |

---

## 3. Pages & UX

### 1️⃣ Chat
- **Inputs** (top bar / sidebar)
  - LLM Base URL (e.g. `http://192.168.1.23`)
  - Port (e.g. `1234`)
  - API Flavor (OpenAI-compatible / Ollama / LM Studio)
  - Model name
  - Prompt preset (dropdown)
- **Start Chat** → loads system prompt + session
- **Chat box** with message bubbles
- **Buttons:** Regenerate, Clear session
- **Advanced expander:** Temperature / Max tokens

### 2️⃣ Prompts Manager
- List presets (title + short description)
- **Create / Edit / Delete**
- Markdown editor with preview
- Metadata: `id`, `title`, `category`, `tags`, `updated_at`
- Saved to `/data/prompts/{kebab-title}.md`

### 3️⃣ Settings
- Persist defaults (base URL, port, flavor, model)
- Toggle **“Enable FlowHub hooks”**
- Save to `.env.local` or `.streamlit/secrets.toml`

---

## 4. Data & Storage

**Prompt Presets**
```
/app/data/prompts/
```

**Format**
```md
---
id: "client-qa-default"
title: "Client Q&A – Default"
category: "Sales"
tags: ["qna", "sales"]
version: "1.0.0"
---
You are a helpful sales assistant for industrial automation...
```

Optional index: `/app/data/prompts/index.json`

**Settings**
```
.env.local
```

Keys:
```
LLM_BASE_URL
LLM_PORT
LLM_API_FLAVOR
LLM_DEFAULT_MODEL
FLOWHUB_HOOKS_ENABLED
FLOWHUB_WEBHOOK_URL
```

**Chat History**  
Stored in-memory; optional JSONL at `/app/data/sessions/{uuid}.jsonl`

---

## 5. LLM Client Adapters

**Goal:** unify various API endpoints.

Structure:
```
app/services/adapters/
  openai_like.py
  ollama.py
  lmstudio.py
```

Interface:
```python
class LLMClient:
    def chat(self, messages: list[dict], **kwargs) -> dict: ...
    def models(self) -> list[str]: ...
```

- `openai_like`: POST `/v1/chat/completions`
- `ollama`: POST `/api/chat`
- `lmstudio`: OpenAI-compatible or local REST

---

## 6. Directory Structure

```
app/
  pages/
    1_Chat.py
    2_Prompts_Manager.py
    3_Settings.py
  services/
    llm_client.py
    adapters/
  storage/
    prompts_repo.py
    settings_repo.py
  ui/
    components.py
    theme.css
  utils/
    config.py
    logging.py
data/
  prompts/
.streamlit/
  config.toml
.env.example
Dockerfile
docker-compose.yml
README.md
```

---

## 7. Streamlit Config & Theme

`.streamlit/config.toml`
```toml
[theme]
base="light"
primaryColor="#365CCE"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F6F8FB"
textColor="#111827"
```

---

## 8. Docker Setup

**Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl tini && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
COPY .streamlit ./.streamlit
COPY .env.example ./.env
EXPOSE 8501
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["streamlit","run","app/pages/1_Chat.py","--server.port=8501","--server.address=0.0.0.0"]
```

**requirements.txt**
```
streamlit==1.39.0
python-dotenv==1.0.1
markdown==3.6
pydantic==2.9.2
requests==2.32.3
```

**docker-compose.yml**
```yaml
services:
  llm-chat:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./.env.local:/app/.env.local:ro
    environment:
      - LLM_BASE_URL=http://host.docker.internal
      - LLM_PORT=1234
      - LLM_API_FLAVOR=openai-compatible
      - LLM_DEFAULT_MODEL=gemma-2b
      - FLOWHUB_HOOKS_ENABLED=false
    restart: unless-stopped
```

Local run:
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/pages/1_Chat.py
```

---

## 9. FlowHub Integration Hooks

### Outbound events
- POST to `FLOWHUB_WEBHOOK_URL` on:
  - `chat_session_started`
  - `chat_message_sent`
  - `chat_message_received`
  - `prompt_used`

### Inbound bootstrap
- Fetch defaults from `FLOWHUB_CONFIG_URL` if present.

### Shared schema
```json
{
  "session_id": "uuid",
  "ts": "2025-11-02T18:55:00Z",
  "event": "chat_message_sent",
  "payload": {
    "user": "local_user",
    "model": "gemma-2b",
    "api_flavor": "openai-compatible",
    "base_url": "http://192.168.1.23:1234",
    "prompt_preset_id": "client-qa-default",
    "message": {"role":"user","content":"Hello"}
  }
}
```

---

## 10. Chat Logic Flow

1. Load config → init adapter.
2. User selects prompt → “Start Chat”.
3. Inject prompt as `system` message.
4. Append user input → call `.chat()`.
5. Stream assistant response → render.
6. Regenerate / Clear session buttons.

---

## 11. Error Handling

- Toasts for:
  - Connection errors
  - Bad responses
  - Invalid models
- Logs to stdout + `/data/logs/app.log` (optional)

---

## 12. Testing Strategy

- **Unit:** adapters, prompt repo.
- **Integration:** mock LLM API.
- **E2E:** Docker up → send message → receive response.

---

## 13. Security & Privacy

- No secrets in image.
- Use `.env.local` for overrides.
- No persistent chat content unless enabled.

---

## 14. Seed Prompts

Files in `/data/prompts/`:
- `client-qa-default.md`
- `discovery-call.md`
- `objection-handling-price.md`
- `tech-handoff-to-engineer.md`

---

## 15. Acceptance Criteria

✅ Runs via `docker-compose up`  
✅ Chat connects to remote LLM  
✅ Prompts editable & selectable  
✅ Messages flow correctly  
✅ UI clean & usable  
✅ Config persists correctly  

---

## 16. Stretch Goals

- Streaming token updates
- Multi-session history
- Prompt import/export
- Search & tagging
- Authentication (optional)
- Per-user defaults

---

## 17. Developer Notes

- Build adapters first, then Chat UI, then Prompts Manager.
- Keep `/data` for mutable storage.
- Test with LM Studio’s OpenAI-compatible port.
- Python 3.11 + Streamlit ≥1.39.

---

*End of document.*
