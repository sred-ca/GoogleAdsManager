# Google Ads Manager Plugin — Project Brief

**Status:** Active (Phase 1 of 3)  
**Owner:** Jude (SRED.ca) — primary user + stakeholder  
**Created:** 2026-04-08  

## What & Why

A Cowork plugin that gives Claude direct management of Google Ads accounts without UI login. Jude runs active Google Ads campaigns for SRED.ca and needs:
- Daily performance monitoring without logging into Google Ads
- Automated budget alerts and pacing checks
- Campaign optimization (A/B testing, bid adjustments)
- Keyword research and negative keyword discovery

**Why plugin architecture?** Faster, more reliable, bulk-capable, auditable. No browser automation fragility.

## Key Facts

**Stack:**
- MCP Base: **Adloop** (Python, via `.mcp.json`)
- Google Ads API: v23.x
- Auth: OAuth2 + Developer token
- Deployment: Cowork plugin (distributable)

**Four skills:**
1. **Campaign Monitor** — reporting, anomalies (priority 1)
2. **Budget Manager** — tracking, alerts, pacing (priority 2)
3. **Campaign Optimizer** — creation, bid adjustments, A/B test (priority 3)
4. **Keyword Manager** — research, negative keywords, audience targeting (priority 4)

**Dependencies:**
- Jude's Google Ads account with API access enabled
- Jude's OAuth2 credentials + developer token
- Adloop MCP server installed

**Integrations:**
- Pulls: Campaign performance data from Google Ads API
- Feeds: Lead quality data → SRED.ca prospecting pipeline (sred-weekly-prospecting)
- Reports: Ad spend → financial tracking (weekly-bookkeeping)

## How to Get Started

### Prerequisites
1. Google Ads account with API access enabled
2. Jude's developer token (apply at Google Ads API Center)
3. OAuth2 credentials (Client ID + Secret)
4. Python 3.9+ (for MCP server)

### Setup (First Time)
```bash
# Clone/open this project
cd google-ads-plugin

# Install dependencies
python -m pip install -r requirements.txt

# Run OAuth2 setup (follow prompts to auth with Google)
python scripts/setup-auth.py

# Verify connection
python scripts/test-connection.py

# Done! Skills are now available in Claude via Cowork
```

### Key Files
- `CLAUDE.md` — Full architecture, decisions, tech stack, open questions
- `skills/campaign-monitor/SKILL.md` — Monitor workflow + Adloop tool definitions
- `references/api-reference.md` — API patterns, GAQL queries, error codes
- `references/gaql-cheatsheet.md` — Google Ads Query Language quick ref
- `.mcp.json` — MCP server configuration

## Next Steps
1. Implement Campaign Monitor skill (3 workflows)
2. Test against live account
3. Build remaining skills in priority order
4. Research plugin packaging + distribution

## Questions / Contacts
- **"How do I run the daily check?"** → See Campaign Monitor SKILL.md
- **"Can this manage multiple accounts?"** → TBD (not yet scoped)
- **"What if I hit API quota limits?"** → See CLAUDE.md API limits section; configure access level (Test/Basic/Standard)
- **Contact:** Reach out if clarification needed on architecture or OAuth setup

---

**More Details:** See `CLAUDE.md` for full project brief, architecture decisions, API limits, and blocked questions.
