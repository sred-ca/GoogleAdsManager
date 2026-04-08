# Google Ads Manager Plugin

## What This Project Is

A distributable Cowork plugin that gives Claude full management capabilities over Google Ads accounts — monitoring performance, creating and optimizing campaigns, managing budgets, and handling keyword/audience targeting. Built on the Google Ads API (v23.x) with Python, designed so any Cowork user can install it and manage their Google Ads from Claude.

## Who's Involved

- **Jude (SRED.ca)** — Project creator and first user. Runs active Google Ads campaigns for SRED.ca. Primary use case: monitoring spend, optimizing campaigns, and managing keywords without constantly logging into the Google Ads UI.
- **End users** — Any Cowork user who manages Google Ads. Technical comfort level varies widely, so the plugin needs to handle complexity behind the scenes and present simple, actionable outputs.

## Architecture

This is a **Cowork plugin** that bundles:

1. **An MCP server** — Wraps the Google Ads API (Python client library) to expose campaign data, mutations, and reporting as MCP tools that Claude can call directly.
2. **Skills** — Four specialized skills that encode best-practice workflows for common Google Ads tasks (monitoring, optimization, budget management, keyword management). These give Claude the domain knowledge to be a competent ads manager, not just an API wrapper.
3. **OAuth2 authentication flow** — Handles Google Ads API credentials (OAuth2 + developer token) with secure storage and token refresh.

### Why an MCP Server + Skills (Not Just Browser Automation)

Browser automation through the Google Ads UI is fragile — Google changes the UI frequently, it's slow, and it can't handle bulk operations efficiently. The API approach is:
- **Faster**: Direct data access, no page loads
- **More reliable**: Structured responses, proper error handling
- **More capable**: Bulk operations, custom reporting, automated rules
- **Auditable**: Every action is logged with timestamps

### Key Design Decision: Build on Google's Official MCP Server

Google provides an official MCP developer toolkit that executes Python queries against the Google Ads API. Our plugin should **extend** this rather than building from scratch:
- Use the official MCP server as the data/mutation layer
- Add our custom skills on top for workflow intelligence
- Add our own reporting and alerting tools that go beyond what the base MCP offers

**Official Google Ads MCP**: https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server
**Community alternatives to evaluate**: cohnen/mcp-google-ads (GitHub), Composio, Adzviser, PPC.io

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Google Ads API | v23.x (current: v23.2) | ~12-month support window per version |
| Client library | `google-ads` Python package | Official, best-supported. Requires Python 3.9+ |
| MCP server | Python (FastMCP or similar) | Wraps Google Ads API as MCP tools |
| Authentication | OAuth2 + Developer Token | Developer token from API Center; OAuth2 scope: `https://www.googleapis.com/auth/adwords` |
| Plugin format | .plugin bundle | Distributable via Cowork marketplace |

### API Limits to Design Around

| Limit | Value | Impact |
|-------|-------|--------|
| QPS | Token Bucket per CID + dev token | Build in exponential backoff for `RESOURCE_TEMPORARILY_EXHAUSTED` |
| Daily operations (Basic) | 15,000/day | Sufficient for monitoring; tight for bulk optimization |
| Daily operations (Standard) | Unlimited | Target this access level for production |
| Mutate operations | Max 10,000/request | Batch mutations carefully |
| AudienceInsights | ~200 requests/day | Rate-limit audience research features |

## Skills Overview

### 1. Campaign Monitor (`skills/campaign-monitor/`)
**Purpose**: Pull performance data, generate reports, flag anomalies.
**Status**: To build
**Key capabilities**:
- Daily/weekly/monthly performance summaries (spend, clicks, conversions, CPA, ROAS)
- Anomaly detection (spend spikes, conversion drops, CTR changes beyond thresholds)
- Comparison reporting (this week vs last week, this month vs last month)
- Campaign health dashboard output (formatted for Cowork display)

### 2. Campaign Optimizer (`skills/campaign-optimizer/`)
**Purpose**: Create campaigns, adjust bids, pause/enable ads, A/B test copy.
**Status**: To build
**Key capabilities**:
- Create new campaigns from a brief (audience, budget, goals → campaign structure)
- Bid adjustment recommendations based on performance data
- Ad copy A/B testing setup and winner selection
- Pause underperforming ads, enable paused ads based on rules
- Quality Score analysis and improvement suggestions

### 3. Budget Manager (`skills/budget-manager/`)
**Purpose**: Track spend against budget, alert on overspend, adjust budgets.
**Status**: To build
**Key capabilities**:
- Daily budget pacing (are we on track to hit monthly budget?)
- Overspend alerts with automatic pause recommendations
- Budget reallocation between campaigns based on performance
- Monthly budget forecasting based on current trends
- Budget vs. actual reporting

### 4. Keyword Manager (`skills/keyword-manager/`)
**Purpose**: Research keywords, manage negative keywords, adjust audience targeting.
**Status**: To build
**Key capabilities**:
- Keyword research using Keyword Planner API
- Search term report analysis → negative keyword recommendations
- Keyword performance analysis (which keywords drive conversions vs. waste spend)
- Audience targeting suggestions based on conversion data
- Competitor keyword gap analysis (where possible via API)

## Related Skills

These existing SRED.ca skills connect to this project:

| Skill | Relevance |
|-------|-----------|
| `sred-brand-icp` | ICP and brand info can inform ad targeting, copy tone, and audience definitions |
| `sred-weekly-prospecting` | Ads generate leads that flow into the HubSpot prospecting pipeline — this plugin's reporting should connect to lead quality metrics |
| `weekly-bookkeeping` | Ad spend shows up in Ramp/QuickBooks — budget reporting here should align with financial tracking |
| `sred-doc-creator` | May want to generate branded PDF reports of ad performance for clients or internal review |

## Folder Structure

```
google-ads-plugin/
├── CLAUDE.md                          # This file — project instructions
├── docs/
│   └── project-brief.docx            # Human-readable project overview
├── skills/
│   ├── campaign-monitor/
│   │   └── SKILL.md                   # Monitoring & reporting skill
│   ├── campaign-optimizer/
│   │   └── SKILL.md                   # Campaign creation & optimization skill
│   ├── budget-manager/
│   │   └── SKILL.md                   # Budget tracking & alerting skill
│   └── keyword-manager/
│       └── SKILL.md                   # Keyword & audience management skill
├── mcp-config/
│   └── google-ads-server.json         # MCP server configuration
├── scripts/
│   ├── setup-auth.py                  # OAuth2 setup helper
│   ├── test-connection.py             # Verify API connectivity
│   └── migrate-api-version.py         # Helper for API version upgrades
├── references/
│   ├── api-reference.md               # Key API endpoints and patterns
│   ├── gaql-cheatsheet.md             # Google Ads Query Language reference
│   └── error-codes.md                 # Common error codes and fixes
├── assets/
│   └── plugin-icon.png                # Plugin marketplace icon
└── plugin.json                        # Plugin manifest (when ready to package)
```

## How To Work On This Project

1. **Read this file first** — it has full context on architecture, decisions, and status.
2. **Check the skills/ folder** — each skill has its own SKILL.md with domain-specific instructions. Read the relevant one before working on that area.
3. **Reference references/** — API patterns, GAQL queries, and error codes live here.
4. **Before making API calls**, ensure auth is configured. Check `mcp-config/google-ads-server.json` for the current setup.
5. **When adding new features**, decide: does this belong in the MCP server (raw API capability) or in a skill (workflow intelligence)? MCP = data access. Skill = decision-making logic.
6. **Test against Jude's live account carefully** — use `LIMIT` clauses and read-only operations first. Never mutate campaigns without explicit confirmation.

## Open Questions

- [ ] **Which MCP server base to use?** Google's official MCP server vs. community alternatives (cohnen/mcp-google-ads, Composio). Need to evaluate: feature completeness, maintenance, ease of extension.
- [ ] **Plugin packaging format**: How exactly do .plugin files work? Need to research the Cowork plugin spec (manifest, bundling, distribution). Consider using the `cowork-plugin-management` plugin from the marketplace to help.
- [ ] **Developer token access level**: Jude's current access level (Test vs Basic vs Standard) determines API quota limits. Standard is needed for production use.
- [ ] **Multi-account support**: Should the plugin support managing multiple Google Ads accounts (MCC/manager account)? Important for agencies but adds complexity.
- [ ] **Scheduled automation**: Should budget alerts and anomaly detection run on a schedule (using Cowork's scheduled tasks), or only on-demand?
- [ ] **Reporting output format**: PDF reports (via sred-doc-creator), spreadsheets (xlsx), or both? What does the end user actually want to receive?
- [ ] **Conversion tracking scope**: Which conversions matter? Phone calls, form submissions, purchases? This affects how we calculate ROAS and CPA.
- [ ] **Historical data depth**: How far back should monitoring pull data? 30 days? 90 days? Affects API call volume.

## Project History

- **2026-04-08**: Project created. Researched Google Ads API (v23.2), discovered Google's official MCP server, evaluated community alternatives. Defined four-skill architecture (monitor, optimizer, budget, keywords). Created folder structure and CLAUDE.md. Identified key open questions around MCP base selection and plugin packaging.
