# Rosewood Hackathon — HAP (Hospitality Agent Protocol)

## Overview

Hackathon project for **Hospitality 2030: A Rosewood Sand Hill Hackathon** (May 16, 2026).
Building a demonstrable proof-of-concept for **HAP — Hospitality Agent Protocol**, an open standard that lets a guest's personal AI agent (Claude, ChatGPT, Gemini) handshake with a hotel's concierge agent, with scope-based consent, TTL, and zero retention.

**Team:** Luis Vargas (lead dev + pitch), Guillermo (support).
**Pitch:** *"Agents are the new SEO. Rosewood is where agents bring their humans."*
**Time budget:** 12 hours total. Feature freeze at hour 8. Total freeze at hour 11.

## Working Directory & Repo

- **Working directory:** `~/Documents/GitHub/HEART/luis/`
- **Repo:** [`jgc-a/HEART`](https://github.com/jgc-a/HEART) (public, Guillermo's). Luis has push permission.
- **Branch policy:** work directly on `main`. Changes only inside `luis/` subfolder. Guillermo owns repo root.
- **Mirror (private backup, archived):** `luisvargasfdz/rosewood-hackathon-aisociety`. Not used anymore — all active work lives here.
- **Second Brain:** `~/Documents/GitHub/Second-Brain/01_WIKI/proyectos/rosewood-hackathon-aisociety.md`

## Stack

- **HAP MCP Server:** Python 3.13 + `mcp` SDK (Anthropic). Exposes 5 tools.
- **Concierge Agent:** Claude API (Sonnet 4.5 / Opus 4.7) wrapped in server.
- **Dashboard (The View):** Next.js 16 App Router + Tailwind + shadcn/ui.
- **Mock data:** JSON + Markdown files (no DB).
- **Audio (optional, late):** ElevenLabs Conversational AI for one strategic voice line (sponsor gesture).
- **Deploy:** Vercel for dashboard (preview URL for judges if needed). MCP server runs local against Claude Desktop.

## Directory Structure

```
HEART/                           # Guillermo's repo root (DO NOT touch root files)
├── README.md                    # Guillermo's (do not edit)
├── LICENSE                      # Guillermo's
└── luis/                        # ← all our work goes here
    ├── CLAUDE.md                # This file
    ├── README.md                # luis/-scoped README
├── docs/
│   ├── hap-spec.md              # HAP Draft Specification v0.1 (RFC-style)
│   ├── demo-storyboard.md       # 3-min live demo, timed second-by-second
│   ├── pitch-script.md          # Exact words for the pitch
│   ├── qa-cheatsheet.md         # 10 anticipated Q&A
│   ├── slides-outline.md        # 5 slides content
│   ├── architecture.md          # Technical architecture
│   └── 10-flows.md              # The 10 guest flow profiles
├── server/                      # HAP MCP Server (Python)
│   ├── main.py                  # MCP server entrypoint
│   ├── tools/                   # 5 HAP tools
│   ├── data/                    # JSON mock data
│   │   ├── guests/              # luis, guillermo, marcus_chen, family_johnson
│   │   ├── properties/          # rosewood-sand-hill.json
│   │   └── flows/               # 10 flow profile markdown files
│   ├── audit.jsonl              # Generated at runtime
│   └── requirements.txt
├── dashboard/                   # The View (Next.js)
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Today's Arrivals
│   │   ├── hap-console/         # HAP handshake live
│   │   └── reputation/          # Dispute brief generator
│   ├── components/
│   └── lib/
└── .claude/
    └── settings.local.json      # Local permissions
```

## Architecture Decisions (locked, do not revisit)

1. **HAP is the protocol. HEART is the reference implementation. ARCA/B-Drive-IT do NOT appear in pitch or demo.**
2. **Pitch language: Spanish OK in conversation, but slides + demo UI + spec in English.** Audience is English-speaking.
3. **Scope cut aggressively:** no biometric tap demo (defended in Q&A only), no real vector DB (markdown RAG), no Postgres (JSON files), no 10 perfiles built (only 3 hardcoded), only 3 dashboard views (not 8).
4. **Live demo is non-negotiable for the handshake.** Video pre-recorded is penalized — show everything live.
5. **Two wow moments in 3 minutes:** (a) the A2A handshake with consent checklist, (b) the dispute brief generator for negative reviews.
6. **ElevenLabs gesture:** one voice line from the concierge agent during the arrival orchestration. Sponsor mention in Q&A or implicit.
7. **Zero retention is the privacy story.** Audit log streams visibly. Guest controls scope + TTL.
8. **Rosewood Sand Hill is the ONLY property in demo.** Cross-property is described in Q&A, not demoed.

## Demo Personas (mock data)

| Guest | Flow Profile | Purpose in demo |
|---|---|---|
| Luis Vargas | Bleisure (Corp Mon-Wed + Leisure Thu-Sat) | Live demo, real preferences |
| Guillermo | Corporate / VC | Backup persona |
| Marcus Chen | Corporate / Founder | The doc reference, slide example |
| Family Johnson | Family with Minors | Triggers HUMAN_REQUIRED check-in (rule demo) |

## Development Commands

```bash
# Server (HAP MCP)
cd server
pip install -r requirements.txt
python main.py

# Dashboard
cd dashboard
pnpm install
pnpm dev

# Test MCP locally
# Configure Claude Desktop with claude_desktop_config.json (in docs/)

# Deploy dashboard
vercel deploy --prod
```

## The 5 HAP Tools (MCP Server exposes)

1. `hap_handshake(guest_id, scope[], ttl_hours)` — establishes session with consent
2. `hap_propose_arrival(guest_id, arrival_date)` — returns orchestration JSON
3. `hap_in_stay_action(guest_id, intent, context)` — generates staff brief or guest response
4. `hap_post_stay_memory(stay_id)` — returns memory snapshot for guest's agent
5. `hap_generate_dispute_brief(stay_id, review_text)` — reputation defense, signed

## Rules for Claude (this session)

- **No scope creep.** If a feature isn't in the locked list above, don't build it.
- **Feature freeze at hour 8.** After that: only bugs.
- **Total freeze at hour 11.** After that: only rehearsing the pitch.
- **No biometric, no voice cloning training, no Postgres setup, no auth/oauth.**
- **Use parallel agents for independent components.** Don't serialize.
- **Commits in English. Code in English. Variable names in English.**
- **Don't push to GitHub unless explicitly asked.** First push will be after MVP works.
- **All names of internal components stay internal:** ARCA, WARDEN, ECHO, KINDRED never appear in user-facing surfaces.
- **HEART can appear** (it's the implementation name).
- **Audit log is visible. ALWAYS.** It's the privacy proof.

## Key Files

- `docs/demo-storyboard.md` — what happens minute-by-minute in the live demo
- `docs/pitch-script.md` — exact words to say
- `docs/hap-spec.md` — HAP Draft v0.1, RFC-style, 2 pages
- `server/main.py` — MCP server entrypoint
- `server/data/properties/rosewood-sand-hill.json` — Sense of Place anchor

## Branding (Rosewood)

- Cream: `#F5F1E8`
- Bronze: `#8B6F47`
- Forest: `#2D4A3E`
- Ink: `#1A1A1A`
- Serif headings: Cormorant Garamond or Playfair Display
- Sans body: Inter
- Language is non-SaaS: "matters" not "tickets", "guests" not "users", "The View" not "Dashboard".

## Pitch Logistics

- **Round 1:** 3 min demo + 1-2 min Q&A (judging in rooms)
- **Round 2 (top 6):** 3 min demo + 1-2 min Q&A on stage
- **Scoring R1:** Impact 20% / Live Demo 45% / Creativity 35%
- **Scoring R2:** Equal weighting
- **Date:** May 16, 2026 (TODAY)
- **Venue:** Rosewood Sand Hill, Menlo Park, CA
