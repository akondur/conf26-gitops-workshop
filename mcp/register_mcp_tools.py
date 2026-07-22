#!/usr/bin/env python3
"""Registers the Configuration Management API as custom tools on Splunk's built-in
MCP Server (https://<stack>:8089/services/mcp_tools), so attendees can drive the API
through their existing MCP client instead of running a local bridge process.

Run once per attendee stack, after Exercise 1's health check passes.

Only 9 of the 12 OpenAPI operations are registered here. createStanza/replaceStanza/
updateStanza take a `settings` array in their request body, and the MCP Server's custom
tools framework only supports scalar (string/integer/number/boolean) tool arguments —
those three operations can't be represented as a single tool call. Use create_setting /
replace_setting per key instead (see README.md, Exercise 4).

Requires a Splunk auth token (not basic auth) for a user with the mcp_tool_admin
capability.
"""
import json
import os
import ssl
import urllib.error
import urllib.request

STACK_NAME = os.environ["STACK_NAME"]
SPLUNK_TOKEN = os.environ["SPLUNK_TOKEN"]
EXTERNAL_APP_ID = os.environ.get("MCP_EXTERNAL_APP_ID", "conf26_gitops")

CONF_TYPE_ARG = {
    "name": "confType", "type": "string",
    "description": "Configuration file name, e.g. 'props' or 'savedsearches'.",
}
STANZA_ARG = {
    "name": "stanza", "type": "string",
    "description": "Stanza name within the conf file (without brackets).",
}
SETTING_ARG = {"name": "setting", "type": "string", "description": "Setting key within the stanza."}
VALUE_ARG = {"name": "value", "type": "string", "description": "Value to write for the setting."}


def api_tool(name, title, description, method, endpoint, body_template=None, arguments=()):
    return {
        "name": f"{EXTERNAL_APP_ID}_{name}",
        "title": title,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {
                arg["name"]: {"type": arg["type"], "description": arg["description"]}
                for arg in arguments
            },
            "required": [arg["name"] for arg in arguments],
        },
        "_meta": {
            "execution": {
                "type": "api",
                "method": method,
                "endpoint": endpoint,
                **({"body": body_template} if body_template is not None else {}),
            }
        },
    }


TOOLS = [
    api_tool(
        "list_conf_types", "List conf types",
        "List the configuration file types (conf types) known to this Splunk instance.",
        "GET", "/services/configs/v1/conftypes",
    ),
    api_tool(
        "get_conf_type", "Get conf type",
        "Get details about a single conf type, e.g. 'props' or 'savedsearches'.",
        "POST", "/services/configs/v1/conftypes/$confType$:get",
        arguments=[CONF_TYPE_ARG],
    ),
    api_tool(
        "list_stanzas", "List stanzas",
        "List the stanzas defined in a given conf type.",
        "GET", "/services/configs/v1/conftypes/$confType$/stanzas",
        arguments=[CONF_TYPE_ARG],
    ),
    api_tool(
        "get_stanza", "Get stanza",
        "Read a single stanza's settings from a conf type.",
        "POST", "/services/configs/v1/conftypes/$confType$/stanzas:get",
        body_template={"stanza": "$stanza$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG],
    ),
    api_tool(
        "delete_stanza", "Delete stanza",
        "Delete an entire stanza from a conf type.",
        "POST", "/services/configs/v1/conftypes/$confType$/stanzas:delete",
        body_template={"stanza": "$stanza$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG],
    ),
    api_tool(
        "get_setting_value", "Get setting value",
        "Read a single setting's value from a stanza.",
        "POST", "/services/configs/v1/conftypes/$confType$/stanzas/settings:get",
        body_template={"stanza": "$stanza$", "setting": "$setting$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG, SETTING_ARG],
    ),
    api_tool(
        "create_setting", "Create setting",
        "Create a new setting in a stanza (creates the stanza if it doesn't exist yet). "
        "Fails if the setting already exists.",
        "POST", "/services/configs/v1/conftypes/$confType$/stanzas/settings",
        body_template={"stanza": "$stanza$", "setting": "$setting$", "value": "$value$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG, SETTING_ARG, VALUE_ARG],
    ),
    api_tool(
        "replace_setting", "Replace setting",
        "Create or overwrite a setting's value in a stanza.",
        "PUT", "/services/configs/v1/conftypes/$confType$/stanzas/settings",
        body_template={"stanza": "$stanza$", "setting": "$setting$", "value": "$value$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG, SETTING_ARG, VALUE_ARG],
    ),
    api_tool(
        "delete_setting", "Delete setting",
        "Delete a single setting from a stanza.",
        "POST", "/services/configs/v1/conftypes/$confType$/stanzas/settings:delete",
        body_template={"stanza": "$stanza$", "setting": "$setting$"},
        arguments=[CONF_TYPE_ARG, STANZA_ARG, SETTING_ARG],
    ),
]


def request(method, path, payload):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"https://{STACK_NAME}:8089{path}",
        data=json.dumps(payload).encode(),
        method=method,
        headers={
            "Authorization": f"Bearer {SPLUNK_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


def main():
    print(f"Batch-registering {len(TOOLS)} tools under external_app_id={EXTERNAL_APP_ID!r}...")
    result = request("POST", "/services/mcp_tools", {"external_app_id": EXTERNAL_APP_ID, "tools": TOOLS})
    print(json.dumps(result, indent=2))

    for tool in TOOLS:
        tool_id = f"{EXTERNAL_APP_ID}:{tool['name']}"
        try:
            enable_result = request("POST", "/services/mcp_tools", {
                "tool_id": tool_id, "enabled": True, "override": True,
            })
            print(f"enabled {tool_id}: {enable_result}")
        except urllib.error.HTTPError as e:
            print(f"FAILED to enable {tool_id}: {e.code} {e.read().decode()}")


if __name__ == "__main__":
    main()
