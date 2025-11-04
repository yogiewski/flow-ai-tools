# FlowAI Chat - Refactor Plan for Next Session

**Status**: Ready for Phase 1 implementation
**Last Updated**: 2025-11-04
**Target Audience**: Coding Agent for next session

---

## Quick Start for Next Session

1. Review the **complete refactor guide** at: `./streamlit_lmstudio_mcp_refactor_guide.md`
2. Follow the **4-phase implementation plan** outlined below
3. Use the **20-item todo list** in this file to track progress
4. Start with **Phase 1 (MVP)** - should take 1-2 weeks

---

## Phase 1: Foundation & Prompts Manager (MVP)

**Objective**: Build the minimal working example for MCP tool orchestration with prompt presets.

### Task List for Phase 1

**Week 1: Core Services & Data**

1. ✅ **Create `app/repo/prompts_repo.py`**
   - JSON-based prompt storage at `data/prompts.json`
   - Schema with `id`, `title`, `description`, `instructions`, `temperature`, `use_mcp`, `mcp_server_label`, `allowed_tools`
   - CRUD operations: `list_presets()`, `get_preset(id)`, `upsert_preset()`, `delete_preset(id)`
   - In-memory index for quick lookups
   - Migrate existing Markdown prompts to JSON format

2. ✅ **Update `app/config/constants.py`**
   - Add MCP defaults:
     - `MCP_BASE_URL` = "http://host.docker.internal:8000"
     - `MCP_SERVER_LABELS` = "local-mcp-tools"
     - Catalog discovery defaults

3. ✅ **Update `.env.example`**
   ```
   LMSTUDIO_BASE_URL=http://host.docker.internal:1234
   LMSTUDIO_ENDPOINT=/v1/responses
   MCP_SERVER_LABELS=local-mcp-tools
   MCP_CATALOG_local-mcp-tools=http://mcp:8000/tools
   ```

4. ✅ **Create `app/services/mcp_catalog.py`**
   - `get_server_labels()` - Parse env variable
   - `get_tools_for_label(label)` - Query `MCP_CATALOG_*` endpoints
   - Fallback to empty list if discovery fails
   - Add 5-min caching for discovered tools

**Week 1-2: LM Studio & UI**

5. ✅ **Enhance `app/services/adapters/lmstudio.py`**
   - Update `chat()` method signature:
     ```python
     chat(model, messages, use_mcp, server_label, allowed_tools, instructions, temperature)
     ```
   - Build conditional `tools` block:
     ```python
     if use_mcp and server_label:
         payload["tools"] = [{
             "type": "mcp",
             "server_label": server_label
         }]
         if allowed_tools:
             payload["tools"][0]["allowed_tools"] = allowed_tools
     ```
   - Extract `output_text` from response with fallback
   - Handle errors gracefully

6. ✅ **Create `app/pages/01_Prompts_Manager.py`**
   - Preset list table with Edit/Duplicate/Delete buttons
   - Form fields:
     - Text: title, description
     - Textarea: instructions (height=200)
     - Slider: temperature (0.0–1.0)
     - Checkbox: "Use MCP tools"
     - Dropdown: MCP server (from env)
     - Multi-select: Allowed tools (from discovery or manual fallback)
   - Validation: if `use_mcp=true`, `mcp_server_label` must be set
   - Save/Cancel with confirmation dialogs

7. ✅ **Integrate into `app/FlowAI.py`**
   - Add preset selector dropdown (by title)
   - Show MCP settings summary when preset selected
   - Pass preset to chat orchestrator

8. ✅ **Update `app/services/orchestrator.py`**
   - Extract preset settings: `use_mcp`, `mcp_server_label`, `allowed_tools`, `temperature`, `instructions`
   - Call LM Studio client with MCP parameters when sending message
   - Handle responses with tool calls

### Acceptance Criteria for Phase 1

- [ ] Prompts Manager page: Full CRUD (Create, Read, Update, Delete)
- [ ] Chat page: Can select preset and send message
- [ ] Preset with `use_mcp=false` → No tools block sent to LM Studio
- [ ] Preset with `use_mcp=true` → Tools block included in payload
- [ ] Tool discovery: `/tools` endpoint queried OR manual entry as fallback
- [ ] Error handling: LM Studio down/network error surfaces cleanly
- [ ] Chat receives response and displays properly
- [ ] All existing functionality still works (bilingual support, etc.)

### Testing Checklist for Phase 1

- [ ] Create a new preset with `use_mcp=false` → chat works without tools
- [ ] Create a preset with `use_mcp=true` → select tool(s) → LM Studio receives tools block
- [ ] Delete preset → confirms deletion
- [ ] Edit preset → changes persist
- [ ] Tool discovery fails → fallback to manual entry works
- [ ] LM Studio connection fails → error message displays
- [ ] Language switching still works on all pages

---

## Phase 2: Advanced Tool Filtering & Discovery

**Objective**: Add dynamic tool discovery and per-tool allow-lists.

### High-Level Tasks

1. Enhance `mcp_catalog.py` with:
   - Query `MCP_CATALOG_*` URLs
   - Parse response: `{server_label, tools: [{name, description, args, returns}]}`
   - Add error handling with warnings
   - Implement caching with TTL

2. Update Prompts Manager UI:
   - On server selection: Load tools asynchronously
   - Display loading spinner
   - Show tool descriptions
   - Fallback text input for manual entry

3. Verify LM Studio payload:
   - Empty `allowed_tools` → all tools allowed
   - Non-empty `allowed_tools` → constrained to list

---

## Phase 3: Hardening & Observability

**Objective**: Persist data, add logging, optional streaming.

### High-Level Tasks

1. Data persistence:
   - Validate `prompts.json` on startup
   - Atomic save (temp file + rename)
   - Migration support for schema changes

2. Audit logging:
   - Log all tool calls (tool name, args redacted, status, duration)
   - Persist transcripts with metadata

3. Debug panel (optional):
   - Collapsible section in chat page
   - Show final payload sent to LM Studio
   - Show MCP discovery status

---

## Phase 4: Docker & Deployment

**Objective**: End-to-end containerization and networking.

### High-Level Tasks

1. Create/update `docker-compose.yml`:
   - Streamlit service on 8501
   - MCP service on 8000 (both stdio + HTTP)
   - Extra hosts for Linux

2. Configure LM Studio `~/.lmstudio/mcp.json`:
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

3. Test networking:
   - Streamlit → LM Studio: `http://host.docker.internal:1234`
   - Streamlit → MCP: `http://mcp:8000/health`

---

## Files to Create/Modify

### ✅ To Create (Phase 1)
- `app/repo/prompts_repo.py`
- `app/services/mcp_catalog.py`
- `app/pages/01_Prompts_Manager.py`
- `data/prompts.json` (migrated from Markdown)

### ✅ To Modify (Phase 1)
- `app/FlowAI.py`
- `app/components/chat_ui.py`
- `app/services/orchestrator.py`
- `app/services/adapters/lmstudio.py`
- `app/config/constants.py`
- `.env.example`

### ⚠️ Deprecated (Archived)
- Old test files → `archive/tests/`
- Old guides → `archive/docs/`
- UI components.py → `archive/unused_helpers/`
- Old session resources → `archive/session-resources/`

---

## Key Design Decisions

1. **JSON storage first** → SQLite migration later
2. **Tool-first system prompt** → Prevents hallucination
3. **MCP catalog caching** → Reduce network calls
4. **Environment-driven config** → No hardcoded values
5. **Fallback UI modes** → Graceful degradation if discovery fails
6. **Orchestrator unchanged** → Reuse existing tool execution logic

---

## Example Prompt Preset Schema

```json
{
  "version": 1,
  "presets": [
    {
      "id": "uuid-string",
      "title": "Support – Industrial Automation",
      "description": "B2B email support agent specialized in switchgear",
      "instructions": "You are **Tool-First Operations Assistant**...",
      "temperature": 0.2,
      "use_mcp": true,
      "mcp_server_label": "local-mcp-tools",
      "allowed_tools": ["lookup_order", "get_product_details"]
    }
  ]
}
```

---

## Tool-First System Prompt (for presets with use_mcp=true)

Include this in `preset.instructions`:

```
You are **Tool-First Operations Assistant** for industrial automation workflows.

POLICY – TOOL USE ONLY
- You MUST rely exclusively on the MCP tools provided by the system. Use tools to obtain facts, perform actions, and generate results.
- Do NOT invent data, simulate tool outputs, or fabricate confirmations.
- If no suitable tool exists for the requested job, ask a single, precise clarifying question that helps pick the correct tool or gather the missing detail. Do not proceed without a tool result.

TASK CONTEXT (fill if available)
- Intended action: {{ACTION_PLACEHOLDER}} (e.g., "send email", "lookup order", "generate RFQ draft").
- Target/subject: {{TARGET_PLACEHOLDER}} (e.g., client email, SKU, order ID).
- Constraints: {{CONSTRAINTS_PLACEHOLDER}} (e.g., language, tone, compliance notes).

OUTPUT RULES
- Summarize outcomes strictly based on tool outputs. If the tool returns an ID, include it. If the tool indicates failure, report the failure and propose next steps.
- If no relevant tool is available, respond with: "I don't have a tool for this yet. To proceed, please provide {{MISSING_DETAIL}} or choose an available tool."
- Never claim actions were done unless a tool confirmed completion.

SAFETY/CONFIRMATION
- For any destructive or externally visible action (e.g., sending an email), first prepare a draft and ask for human confirmation unless the user explicitly authorizes immediate execution.
```

---

## Environment Variables Summary

**Required for Phase 1:**
```bash
LMSTUDIO_BASE_URL=http://host.docker.internal:1234
LMSTUDIO_ENDPOINT=/v1/responses
MCP_SERVER_LABELS=local-mcp-tools
```

**Optional (for tool discovery):**
```bash
MCP_CATALOG_local-mcp-tools=http://localhost:8000/tools
```

---

## Debugging Tips

**If LM Studio can't find tools:**
- Verify MCP server is running: `curl http://localhost:8000/health`
- Check LM Studio `~/.lmstudio/mcp.json` has correct `docker exec` command
- Ensure Docker container is running: `docker ps | grep local-mcp-tools`

**If tool discovery fails in Streamlit:**
- Check URL in `MCP_CATALOG_*` env var
- Manually query the endpoint: `curl http://mcp:8000/tools`
- Fall back to manual tool entry in Prompts Manager

**If chat not working:**
- Verify LM Studio is running on port 1234
- Check `.env.local` has correct `LMSTUDIO_BASE_URL`
- Review app logs: `tail -f data/logs/app.log`

---

## Success Metrics

- ✅ MVP works end-to-end (preset → message → tool execution → response)
- ✅ All 8 Phase 1 tasks completed
- ✅ All acceptance criteria met
- ✅ Testing checklist passed
- ✅ Zero tool hallucination (via Tool-First prompt)
- ✅ Clean error messages for all failure modes

---

## Next Steps After Phase 1

1. **Phase 2**: Per-tool allow-lists and live discovery
2. **Phase 3**: Persistence, streaming, audit logs
3. **Phase 4**: Docker orchestration and deployment

See `./streamlit_lmstudio_mcp_refactor_guide.md` for complete details.

---

## Questions Before Starting?

If anything is unclear, review:
1. The **active refactor guide**: `streamlit_lmstudio_mcp_refactor_guide.md` (Sections 0-9)
2. The **MCP server guide** in refactor guide (Sections 15)
3. This plan document again for quick reference

Good luck! 🚀
