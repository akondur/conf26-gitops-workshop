# System Architecture

## Exercise 1 & 2: GitHub Actions to Splunk Cloud

```
┌─────────────────────────────────────┐
│     GitHub Actions Runner          │
│  (triggered by workflow event)      │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   EXERCISE 1     EXERCISE 2a
   Health Check   Validate (PR)
        │             │
        │      ┌──────┴──────┐
        │      │             │
        │      ▼             ▼
        │   Pass         Fail
        │    │            │
        │    └────┬───────┘
        │         │
        ▼         ▼
   ┌────────────────────────────────┐
   │  Splunk Cloud Instance         │
   │  https://<stack>:8089          │
   │                                │
   │  GET /services/server/info     │
   │  (Exercise 1)                  │
   │                                │
   │  POST /services/properties/... │
   │  (Exercise 2a: validate)       │
   │                                │
   │  POST /configs/v1/conftypes/..│
   │  (Exercise 2b: deploy)         │
   │                                │
   └────────────┬───────────────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
      Success       Failure
    (green ✅)     (red ✖)
```

**Auth:** Bearer token (Exercise 1) or Basic auth (Exercise 2)

---

## Exercise 3: Manual API Call

```
┌──────────────────────────┐
│  Attendee's Terminal     │
│  (curl command)          │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────────────────┐
│    Splunk Cloud Instance             │
│                                      │
│ POST /servicesNS/nobody/search/...   │
│      /configs/v1/conftypes/...       │
│                                      │
│ Scope: app-level (nobody/search)     │
│                                      │
└──────────────┬───────────────────────┘
               │
         ┌─────┴─────┐
         │           │
         ▼           ▼
    Created      Audit Log
    stanza       1 event
                 (actor=bot)
                 
    Then:
    Attendee edits via Splunk Web UI
         ↓
    Creates user-level override
         ↓
    Audit Log
    2 events total
    (event 2: actor=user)
         ↓
    DRIFT DETECTED
    (same stanza, different scopes)
```

**Auth:** Basic auth (username:password)

---

## Exercise 4: Continue Agent to MCP Server

```
┌─────────────────────────────────────┐
│  Continue Extension (VSCode)        │
│                                     │
│  • Chat interface                   │
│  • Claude LLM (Haiku)               │
│  • MCP client                       │
│                                     │
│  Reads: ~/.continue/mcpServers/     │
│          splunk-conf.continue.yaml  │
│                                     │
└────────────┬────────────────────────┘
             │
             │ Spawns mcp-remote bridge
             │ (Bearer token)
             │
             ▼
┌─────────────────────────────────────────┐
│  Splunk's Native MCP Server             │
│  https://<stack>:8089/services/mcp/v1/sse
│                                         │
│  Registered Tools:                      │
│  • search_list_stanzas                  │
│  • search_get_stanza                    │
│  • search_create_setting                │
│  • search_replace_setting               │
│  • search_delete_setting                │
│  • ... (9 total)                        │
│                                         │
│  Registered by the organizer against    │
│  POST /services/mcp_tools before the    │
│  workshop starts (not part of this      │
│  repo — one-time per CO2 stack).        │
│                                         │
└────────────┬────────────────────────────┘
             │
             │ Attendee prompts Claude
             │ "Create a setting..."
             │
             ▼
┌──────────────────────────────────────┐
│  Claude (Haiku)                      │
│                                      │
│  1. Understands intent               │
│  2. Decides which tool to call       │
│  3. Calls tool with parameters       │
│  4. Receives result                  │
│  5. Responds to user                 │
│                                      │
└────────────┬─────────────────────────┘
             │
             │ Tool call relayed via
             │ mcp-remote bridge
             │
             ▼
┌──────────────────────────────────────┐
│  Splunk Cloud Instance               │
│                                      │
│  MCP Server translates tool call to: │
│  GET /configs/v1/conftypes/...       │
│  POST /configs/v1/conftypes/...      │
│  PUT /configs/v1/conftypes/...       │
│  etc.                                │
│                                      │
│  Executes → returns result           │
│                                      │
└──────────────┬───────────────────────┘
               │
               ▼
          Claude reads result,
          continues conversation
```

**Auth:** Bearer token (MCP token)

---

## MCP Tool Generation Pattern

This workshop uses Splunk's MCP Server with tool definitions mirroring the
Configuration Management API (`spec/configmgmt_openapi.json`):

```
Configuration Management API
(spec/configmgmt_openapi.json defines 12 operations)
        │
        │ • list_stanzas
        │ • get_stanza
        │ • create_stanza (array args - NOT registered)
        │ • replace_stanza (array args - NOT registered)
        │ • update_stanza (array args - NOT registered)
        │ • create_setting (scalar args - ✅ registered)
        │ • replace_setting (scalar args - ✅ registered)
        │ • delete_setting (scalar args - ✅ registered)
        │ • ... (3 more scalar-arg operations)
        │
        ▼
Organizer registers 9 tool definitions
(mirroring the scalar-arg operations above)
        │
        ▼
POST /services/mcp_tools
(Splunk MCP Server)
        │
        │ Registers 9 tools
        │ (only scalar-argument operations)
        │
        ▼
Continue UI
        │
        └─ Tools available to Claude
           search_list_stanzas
           search_create_setting
           search_replace_setting
           search_delete_setting
           ... etc.
```

**Why only 9 tools?**
MCP custom-tools framework only supports scalar arguments (string, int, bool). Operations requiring arrays (stanza creation with multiple settings) are registered as single-key operations instead.

**Reusable pattern:**
This approach works for any Splunk REST API with an OpenAPI spec. See [Splunk MCP Server documentation](https://help.splunk.com/en/splunk-cloud-platform/mcp-server-for-splunk-platform/1.1/about-mcp-server-for-splunk-platform) for details.

---

## Authentication Methods

| Flow | Auth Type | Example |
|------|-----------|---------|
| Health Check | Bearer Token | `Authorization: Bearer sk_abc123...` |
| Validate/Deploy | Basic Auth | `Authorization: Basic base64(user:pass)` |
| MCP Operations | Bearer Token (MCP) | `Authorization: Bearer mcp_token_...` |
