# Organizer Setup Guide

Complete these steps **before attendees start the workshop**. This document is for infrastructure/organizer use only.

## Phase 1: Configure Splunk Cloud Instance

These steps must be completed once per Splunk Cloud instance.

### 1. Enable Audit Trail Log v2

1. Log in to Splunk Web as an admin
2. Go to **Apps** → **Audit Trail** (or similar audit management UI)
3. Enable **Audit Trail Log v2**
   - This activates the structured audit format required for Exercise 3 (drift detection)

### 2. Enable Configuration API Auditing

Add this stanza to `/opt/splunk/etc/apps/search/local/server.conf`:

```ini
[config_api_audit]
disabled = false
```

This enables auditing of configuration changes made via REST APIs (required for Exercise 3).

### 3. Create Service Account for MCP Tool Registration

1. In Splunk Web, go to **Settings** → **Users and Authentication** → **Users**
2. Create a new user (e.g., `mcp-tool-admin`)
3. Go to **Settings** → **Users and Authentication** → **Roles**
4. Create or locate a role with the `mcp_tool_admin` capability
5. Assign that role to the `mcp-tool-admin` user

### 4. Generate MCP Tool Admin Token

1. Log in as the `mcp-tool-admin` user
2. Go to **Settings** → **Tokens** (or **Data Inputs** → **HTTP Event Collector**)
3. Create a new authentication token with a long expiration (e.g., 1 year)
4. Copy the token — it's only shown once
5. Store securely (you'll use it in Phase 2)

---

## Phase 2: Register MCP Tools

Run this **once after Phase 1 is complete**, before attendees start Exercise 4.

### Prerequisites

- Splunkd is running on the instance
- MCP Server is installed and running (`/services/mcp/v1/sse` endpoint is accessible)
- You have the `mcp-tool-admin` token from Phase 1, step 4

### Steps

1. Clone or access the workshop repo:
   ```bash
   cd conf26-gitops-workshop/mcp
   ```

2. Set environment variables:
   ```bash
   export STACK_NAME=<your-splunk-cloud-stack-hostname>
   export SPLUNK_TOKEN=<mcp-tool-admin-token>
   ```
   
   Example:
   ```bash
   export STACK_NAME=acme.splunkcloud.com
   export SPLUNK_TOKEN=eyJraWQiOiJkNjE5ZTk3ZC0wYzA2LTQ5YmMtODc0Ni1jZWM0ZTk5ZTM4MDMiLCJhbGciOiJIUzI1NiJ9...
   ```

3. Run the registration script:
   ```bash
   python3 register_mcp_tools.py
   ```

4. Expected output:
   - Batch registration response: `"registered_count": 9`
   - 9 separate enable confirmations
   - Tools registered as `search:list_stanzas`, `search:get_stanza`, etc.

5. Verify success:
   ```bash
   curl -k -X GET "https://$STACK_NAME:8089/services/mcp_tools?external_app_id=search" \
     -H "Authorization: Bearer $SPLUNK_TOKEN" | jq '.tools | length'
   ```
   Expected output: `9`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Authentication failed` | Verify `SPLUNK_TOKEN` is valid and has `mcp_tool_admin` capability |
| `Tool registration failed` | Confirm MCP Server is running (`curl https://<stack>:8089/services/mcp/v1/sse`) |
| `Endpoint not found` | Ensure Splunk Cloud instance version is 10.3.2512 or higher |

---

## Post-Setup Verification

Before attendees start:

1. **Exercise 1 (Health Check):** Run the health-check workflow manually to confirm CI connectivity
2. **Exercise 3 (Drift Detection):** Verify audit trail v2 is enabled by searching:
   ```spl
   index=_audit sourcetype=audittrailv2 | stats count
   ```
   Should return at least 0 events (empty is OK, just confirming the sourcetype exists)
3. **Exercise 4 (MCP Tools):** Confirm tools are registered (see "Verify success" above)

---

## Notes

- **Phase 1 is one-time** per Splunk Cloud instance
- **Phase 2 is one-time per MCP tool registration** (safe to re-run; it atomically replaces tools)
- All 9 tools are registered under the `search` app namespace
- Tools default to the search app scope; Claude can override with `app="props"` or other app names if needed
