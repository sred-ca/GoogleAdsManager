# Project Status

**Project:** Google Ads Manager Plugin (Cowork Distributable)  
**Purpose:** Give Claude full Google Ads account management — campaign monitoring, optimization, budget management, keyword research  
**Owner:** Jude (SRED.ca)  
**Last Updated:** 2026-04-08  

## Current Phase
Phase 1 of 3: Architecture definition & MVP skill foundation (Campaign Monitor)

## Completed (To Date)
- ✅ Project brief + architecture defined (CLAUDE.md)
- ✅ Confirmed MCP base: **Adloop** (vs. Google official, community alternatives)
- ✅ Folder structure initialized
- ✅ Four skills scoped (Monitor, Optimizer, Budget, Keyword)
- ✅ `.mcp.json` configured with Adloop

## In Progress
- 🟡 Campaign Monitor skill — workflows + Adloop tool integration (estimat: 60 min)

## Next Up (Priority Order)
1. **Finish Campaign Monitor skill** — implement 3 workflows (daily check, weekly summary, anomaly detection)
2. **Test against live account** — verify tool calls + reporting format with Jude's account
3. **Budget Manager skill** — build tracking + pacing logic
4. **Campaign Optimizer skill** — campaign creation + bid management
5. **Keyword Manager skill** — keyword research + negative keyword workflow
6. **Plugin packaging** — research .plugin manifest format + Cowork distribution

## Blockers / Open Questions
- ❓ **Jude's API access level** — Test/Basic/Standard? (affects quota + feature availability)
- ❓ **Multi-account support** — Single account or MCC support? (adds complexity)
- ❓ **Scheduled automation** — Run alerts on schedule or on-demand only?
- ❓ **Plugin packaging spec** — Need to research Cowork .plugin format + delivery mechanism

## Architecture Notes
- **MCP Base:** Adloop (Python, via `.mcp.json`)
- **Skills:** 4 specialized workflows (Monitor, Optimizer, Budget, Keyword)
- **API:** Google Ads API v23.x, OAuth2 + developer token
- **Related Projects:** Feeds into `sred-weekly-prospecting`, aligns with `weekly-bookkeeping`

## Tech Stack
| Component | Choice |
|-----------|--------|
| Google Ads API | v23.x (current: v23.2) |
| Client Library | google-ads (Python) |
| MCP Server | Adloop |
| Auth | OAuth2 + Developer Token |
| Target Access | Standard (unlimited daily ops) |

## Key Files
- `CLAUDE.md` — Full project brief, architecture, decisions, tech stack
- `.mcp.json` — MCP server configuration (Adloop)
- `skills/campaign-monitor/SKILL.md` — Monitoring skill definition
- `references/api-reference.md` — API patterns, GAQL cheatsheet, error codes
- `scripts/setup-auth.py` — OAuth2 helper
- `scripts/test-connection.py` — API connectivity verification

## Session History
- **2026-04-08**: Project initialized. Confirmed Adloop MCP base. Prioritized Campaign Monitor. Created project closure skill and status templates.
