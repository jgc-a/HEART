# Architecture — HAP Reference Implementation (HEART)

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  GUEST AGENT (Claude Desktop, ChatGPT, Gemini, any LLM)              │
│                                                                       │
│  Has: guest profile, calendar, prefs                                  │
│  Knows: when guest wants to travel                                    │
│  Decides: what to share, what TTL, what scope                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ HAP-AUTH handshake (MCP transport)
                         │ scope[], ttl_hours, consent_token
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  HAP MCP SERVER (Python, this repo)                                  │
│                                                                       │
│  Exposes 5 tools:                                                     │
│    1. hap_handshake                                                   │
│    2. hap_propose_arrival                                             │
│    3. hap_in_stay_action                                              │
│    4. hap_post_stay_memory                                            │
│    5. hap_generate_dispute_brief                                      │
│                                                                       │
│  Zero retention: every tool call is stateless from guest data         │
│  Audit: every call → audit.jsonl (signed)                             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ internal API
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CONCIERGE AGENT (Claude API call)                                   │
│                                                                       │
│  System prompt includes:                                              │
│    - HAP-RAG (sense of place, brand voice, SOPs)                      │
│    - 10 flow profile rules                                            │
│    - Operational rules (escalate complaints to humans)                │
│                                                                       │
│  Output: arrival orchestration, staff brief, in-stay action           │
└────────────────────────┬────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────────┐
        ▼                ▼                ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Staff Brief │  │ ElevenLabs  │  │ Cross-channel│  │ The View    │
│ (markdown)  │  │ voice line  │  │ notify       │  │ dashboard   │
│             │  │             │  │ (stub)       │  │ (Next.js)   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

## Components

### 1. HAP MCP Server (`server/`)

**Tech:** Python 3.13, `mcp` SDK from Anthropic.

**Files:**
- `server/main.py` — MCP server entrypoint, registers tools
- `server/tools/handshake.py` — HAP-AUTH handshake logic
- `server/tools/arrival.py` — propose_arrival → concierge agent call
- `server/tools/in_stay.py` — in_stay_action → staff brief generator
- `server/tools/post_stay.py` — post_stay_memory → memory snapshot
- `server/tools/dispute.py` — generate_dispute_brief → cryptographic timeline
- `server/audit.py` — write to audit.jsonl, signed
- `server/concierge.py` — Claude API wrapper with system prompt

**Mock data:**
- `server/data/guests/*.json` — 4 guest profiles
- `server/data/properties/rosewood-sand-hill.json` — sense of place + amenities
- `server/data/flows/*.md` — 10 flow profile definitions (HAP-RAG light)
- `server/data/inventory/experiences.json` — what Rosewood can offer

**Audit:**
- `server/audit.jsonl` — append-only, hash-chained for tamper detection

### 2. The View Dashboard (`dashboard/`)

**Tech:** Next.js 16 App Router, Tailwind, shadcn/ui, deployed to Vercel.

**Pages:**
- `/` — Today's Arrivals (the 4 guests with their flow profiles)
- `/hap-console` — Live HAP traffic (server-sent events from the MCP server)
- `/reputation` — Dispute brief generator with simulated negative review

**Branding tokens:**
- `tailwind.config.ts` extends with Rosewood palette + serif font
- Layout uses generous whitespace, never feels like SaaS

**Backend:** simple API routes that read `server/audit.jsonl` and stream updates.

### 3. Voice (`server/voice.py`)

**Tech:** ElevenLabs Conversational AI.

**Use:** ONE line during arrival orchestration. Generated server-side, played in browser via dashboard or directly in Claude Desktop response.

Voice profile: warm, paused, mid-pitch. Voice ID locked.

### 4. Data Flow (Pre-Arrival Example)

```
1. Guest types in Claude Desktop:
   "Voy a Rosewood Sand Hill el 18 de mayo"

2. Claude detects HAP MCP server, calls hap_handshake
   with proposed scope.

3. Server returns Consent Checklist (rendered as markdown
   with formatted options).

4. Guest reviews, unchecks one, approves.

5. Claude calls hap_propose_arrival(guest_id, arrival_date).

6. Server:
   - Loads guest profile from data/guests/luis.json
   - Classifies flow profile (Bleisure)
   - Loads sense_of_place for sand-hill property
   - Loads flow profile rules
   - Calls Claude API with full context → orchestration JSON

7. Server:
   - Writes to audit.jsonl
   - Returns orchestration to Claude Desktop
   - Pushes update to dashboard (SSE)

8. Dashboard:
   - HAP Console shows handshake events
   - Staff Brief panel renders the brief
   - Audit Log streams the entries

9. ElevenLabs voice plays the welcome line.
```

### 5. Dispute Brief Flow

```
1. User clicks "Simulate Tripadvisor 2-star review" in dashboard.
2. Dashboard sends review text to server.
3. Server retrieves audit log for the stay (simulated past stay).
4. Server calls Claude API with timeline + review.
5. Claude generates a reconstruction with:
   - Timeline of events
   - Briefings emitted
   - Staff actions
   - Resolution time
   - Guest mood at departure (from in-stay signals)
6. Server signs the brief (HMAC for demo, would be Ed25519 in prod).
7. Dashboard renders the WARDEN-signed brief.
```

## What We Are NOT Building (12-hour scope)

- Real biometric capture (defended in Q&A)
- Vector database (markdown files work for demo)
- Postgres (JSON files)
- Real OAuth / auth (single mock guest session)
- Cross-property federation (described in Q&A)
- Real PMS / POS integration (stubbed)
- Full 10 flow profiles implementation (3 hardcoded)
- 8 dashboard views (3 only)
- Real-time biometric face match
- KINDRED, ECHO as separate services (audit log subsumes)

## Critical Path

```
Hour 0:  Repo + docs (DONE before agents launch)
Hour 1:  MCP server scaffold + first tool stub
Hour 2:  All 5 tools stub-functional
Hour 3:  Concierge agent generates first arrival brief
Hour 4:  Claude Desktop integration verified live
Hour 5:  Dashboard MVP (3 views) renders
Hour 6:  Dispute brief generator works
Hour 7:  ElevenLabs voice integrated
Hour 8:  FEATURE FREEZE. Polish only.
Hour 9:  End-to-end demo rehearsal
Hour 10: UI polish, branding application
Hour 11: TOTAL FREEZE. Pitch rehearsal only.
Hour 12: Pitch.
```

## Environment

```
.env.local
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=el-...
ELEVENLABS_VOICE_ID=...
DEMO_MODE=true
```
