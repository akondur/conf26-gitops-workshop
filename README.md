# conf26-gitops-workshop

Template repository for **PLA1714 — GitOps Pipeline for Splunk Configuration** (conf26).

**For complete step-by-step instructions, see the official Lab Guide** (Word document provided separately).

This repo includes sample workflows, config files, and MCP tooling for the workshop exercises. Use `SPLUNK_ARCHITECTURE.md` for system architecture diagrams.

**For organizers:** Pre-workshop infrastructure setup (Audit Trail v2, config API auditing, MCP Server app install, MCP tool registration) is handled separately per CO2 stack and is not part of this repo.

## Exercises

1. **Exercise 1** — GitHub Actions health check to verify connectivity to Splunk Cloud
2. **Exercise 2** — Validate config changes in pull requests before deployment (shift-left pattern)
3. **Exercise 3** — Create config via API, then manually edit via UI to observe configuration drift
4. **Exercise 4** — Use an AI agent (Claude + Continue) to drive the Configuration Management API via MCP

See the Lab Guide for complete walkthroughs with screenshots and exact click paths.

## Repository Contents

| Path | Purpose |
|---|---|
| `.github/workflows/` | Three GitHub Actions workflows (health-check, validate, deploy) for Exercises 1–2 |
| `conf/savedsearches.conf` | Sample configuration file |
| `spec/configmgmt_openapi.json` | Configuration Management API OpenAPI specification |
| `mcp/splunk-conf.continue.yaml` | Continue MCP client config template for Exercise 4 (attendee use) |
| `SPLUNK_ARCHITECTURE.md` | System architecture diagrams showing data flows for all four exercises |
