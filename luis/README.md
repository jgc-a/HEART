# `luis/` — HAP + The View by Luis Vargas

This subfolder contains the **HAP MCP server**, **The View** operational dashboard, and the **demo / pitch deliverables** built by Luis Vargas for the Rosewood Sand Hill *Hospitality 2030* hackathon.

It is also mirrored as a standalone private repo at [`luisvargasfdz/rosewood-hackathon-aisociety`](https://github.com/luisvargasfdz/rosewood-hackathon-aisociety) for backup.

---

## What's in here

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project context, scope, architecture decisions, hackathon rules |
| `README.md` | This file |
| `docs/hap-spec.md` | **HAP Draft Specification v0.1** — RFC-style, 8 components |
| `docs/demo-storyboard.md` | Live 3-minute demo, timed second by second |
| `docs/pitch-script.md` | Exact words for the pitch (415 words, 2:46 spoken) |
| `docs/qa-cheatsheet.md` | 12 anticipated Q&A with 25-second answers |
| `docs/slides-outline.md` | 5 slides, Rosewood branded |
| `docs/10-flows.md` | The 10 guest flow profiles |
| `docs/architecture.md` | Technical architecture diagram and component map |
| `docs/12-hour-plan.md` | Hour-by-hour plan with status board and risk register |
| `docs/claude-desktop-setup.md` | How to wire the MCP server into Claude Desktop |
| `docs/guillermo-merge-protocol.md` | Rules for merging Guillermo's parallel work |
| `server/` | Python MCP server with 5 HAP tools, concierge agent, audit log |
| `dashboard/` | Next.js 16 "The View" — Today's Arrivals, HAP Console, Reputation Audit |
| `.claude/settings.local.json` | Pre-approved Claude Code permissions |

---

## The 5 HAP Tools

1. **`hap_handshake(guest_id, scope[], ttl_hours)`** — establishes session with consent checklist
2. **`hap_propose_arrival(guest_id, arrival_date)`** — returns orchestration JSON + staff brief
3. **`hap_in_stay_action(guest_id, intent, context)`** — generates staff brief, escalates if complaint/maintenance
4. **`hap_post_stay_memory(stay_id)`** — returns memory snapshot for the guest's agent
5. **`hap_generate_dispute_brief(stay_id, review_text)`** — cryptographically-signed reputation defense

---

## Quickstart

```bash
# 1. Install server
cd luis/server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY

# 2. Run the CLI demo (Plan B fallback)
python demo_runner.py

# 3. Wire into Claude Desktop
#    See ../docs/claude-desktop-setup.md

# 4. Start The View dashboard
cd ../dashboard
pnpm install
pnpm dev
# Opens http://localhost:3000
```

---

## Demo personas (mock data)

| Guest | Profile | Purpose |
|---|---|---|
| **Luis Vargas** | Bleisure (Corp Mon-Wed + Leisure Thu-Sat) | Live demo persona |
| **Guillermo Aldana** | Corporate / VC | Backup persona |
| **Marcus Chen** | Corporate / Founder | Slide example |
| **Family Johnson** | Family with Minors | Triggers HUMAN_REQUIRED check-in (rule demo) |

---

## Demo wow moments

1. **0:55–2:00 — The Handshake (live in Claude Desktop)**
   Luis types `"Voy a Rosewood Sand Hill el 18 de mayo"` → Consent Checklist with 7 scope items → approve → staff brief materializes on the right (The View) → ElevenLabs voice plays welcome line.

2. **2:00–2:30 — Reputation Defense**
   Click *"Simulate Tripadvisor 2-star review"* → click *"Generate dispute brief"* → cryptographically-signed timeline reconstructs the AC complaint with 11-minute dual-human resolution.

Both moments are live, screen-shared, no pre-recorded video.

---

## Naming discipline (locked for the pitch)

Public surfaces (pitch, slides, demo UI):
- **HAP** — central. The protocol.
- **HEART** — sparingly. Mentioned as "reference implementation".
- **AISociety** — team name. Footer.
- **Rosewood** — the property and brand.

Internal-only (not in pitch / not in demo UI): ARCA, B Drive IT, WARDEN, ECHO, KINDRED, ASC, ARP.

See `docs/guillermo-merge-protocol.md` for the full discipline.

---

## Status

Built (this folder):
- HAP MCP server with 5 tools
- The View dashboard with 3 views, Rosewood-branded
- 4 guest profiles + Sand Hill property + 10 flow profile rules + experiences inventory
- 10 documents (spec, pitch, storyboard, Q&A, slides, plan, setup, etc.)
- Cryptographically-signed audit log
- ElevenLabs voice integration point (line written, MP3 generation pending at hour 7)
- CLI fallback (`demo_runner.py`) for Plan B

TODO before pitch:
- Slide deck (Pitch.com or Keynote) — owner: Luis or Guillermo
- ElevenLabs voice generation (hour 7)
- Claude Desktop config installed and tested live (hour 3)
- Pitch rehearsal x3 minimum (hours 8, 10, 11)
- Vercel preview URL of The View (optional, for judges' link)
