# 12-Hour Plan — Hackathon Day

> **Target:** Demo-ready by hour 11. Pitch at hour 12.
> **Team:** Luis (lead dev + pitch), Guillermo (support).
> **Hard rules:** Feature freeze at hour 8. UI freeze at hour 10. Total freeze at hour 11.

---

## Hour-by-Hour

### Hour 0 — Setup ✅
- [x] Project structure
- [x] CLAUDE.md, README, docs
- [x] GitHub repo created (private)
- [x] 3 parallel agents launched: MCP server, dashboard, mock data
- [x] Linked to Second Brain
- [ ] First commit pushed

### Hour 1 — Foundation builds
**Luis:**
- Verify agent outputs and integrate
- Fix any obvious issues
- Set up local environment (.env, dependencies)

**Guillermo:**
- Review the pitch script and slides outline
- Confirm or revise the punchline
- Start work on Pitch.com / Keynote slides

### Hour 2 — First end-to-end run
**Luis:**
- Run `python server/main.py` and verify it starts
- Run `pnpm dev` in dashboard and verify it renders
- Wire mock data into both
- Manual test: handshake → arrival → brief

**Guillermo:**
- Build slides 1-3 (hook, problem, HAP intro)
- Source typography (Cormorant Garamond, Inter)

### Hour 3 — Claude Desktop integration
**Luis:**
- Add MCP server to `~/Library/Application Support/Claude/claude_desktop_config.json`
- Restart Claude Desktop
- Test handshake from Claude Desktop
- Capture screenshots for backup

**Guillermo:**
- Build slides 4-5 (10 profiles, close)
- Light typography pass

### Hour 4 — Concierge agent polish
**Luis:**
- Tune the system prompt for the concierge
- Verify staff brief output matches storyboard
- Make sure response time is < 15s

**Guillermo:**
- First end-to-end watch-and-time pitch run

### Hour 5 — Dashboard polish
**Luis:**
- Verify all 3 dashboard views render correctly
- Fix branding inconsistencies
- Audit log animation polish

**Guillermo:**
- Q&A rehearsal — read through cheatsheet, internalize

### Hour 6 — Dispute brief feature
**Luis:**
- Verify dispute brief generator works
- Style the WARDEN-signed brief output
- Tune the markdown

**Guillermo:**
- Identify weak Q&A answers, suggest improvements

### Hour 7 — ElevenLabs voice
**Luis:**
- Generate the welcome voice line for Luis arrival scenario
- Cache the MP3 to play in dashboard
- Test playback timing in demo

**Guillermo:**
- Backup capture: record short video of working demo (for self-reference, NOT for pitch)

### Hour 8 — FEATURE FREEZE
**Both:**
- Full demo run #1 (cold). Time it.
- Identify breakages, fix in next hour
- After this hour: only bug fixes allowed

### Hour 9 — Bug squashing
**Luis:**
- Fix anything that broke in demo run #1
- Implement Plan B (CLI fallback) just in case

**Guillermo:**
- Update slides if anything in demo changed
- Print Q&A cheatsheet, study

### Hour 10 — UI FREEZE
**Both:**
- Demo run #2. Time it. Target 2:55.
- Final visual polish (Rosewood branding consistency check)
- After this hour: NO more code changes

### Hour 11 — TOTAL FREEZE
**Both:**
- Demo run #3 — full performance with slide changes
- Pitch run-through #4 — with Q&A practice
- Pitch run-through #5 — with adversarial questions

### Hour 12 — Pitch
- Final breath
- On stage
- Eye contact at 0:08 and 2:53 (the two "Rosewood" lines)
- Smile at 3:00. Wait one full second.

---

## Status Board (update in real time)

### Components

| Component | Owner | Status | Notes |
|---|---|---|---|
| HAP MCP Server (Python) | Luis + Agent | 🟡 In progress | Agent building |
| Next.js Dashboard (The View) | Luis + Agent | 🟡 In progress | Agent building |
| Mock data (JSON + MD) | Agent | 🟡 In progress | Agent building |
| Pitch script | Luis | ✅ Done | docs/pitch-script.md |
| Slides | Guillermo | ⬜ Not started | docs/slides-outline.md |
| Q&A cheatsheet | Luis | ✅ Done | docs/qa-cheatsheet.md |
| Demo storyboard | Luis | ✅ Done | docs/demo-storyboard.md |
| HAP Spec v0.1 | Luis | ✅ Done | docs/hap-spec.md |
| 10 flow profiles | Luis | ✅ Done | docs/10-flows.md |
| ElevenLabs voice line | Luis | ⬜ Not started | Hour 7 |
| Claude Desktop integration | Luis | ⬜ Not started | Hour 3 |
| Plan B (CLI fallback) | Luis | ⬜ Not started | Hour 9 |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MCP integration fails in Claude Desktop | Medium | High | CLI fallback (Plan B) |
| Concierge response too slow live | Medium | Medium | Pre-cache responses for demo |
| Dashboard doesn't render correctly on demo laptop | Low | High | Vercel deploy + URL backup |
| ElevenLabs API quota / latency | Low | Low | Pre-generate MP3 file |
| Pitch goes over 3 min | Medium | Medium | Rehearse 5+ times with timer |
| Q&A blind-sided | Medium | Medium | Cheatsheet + practice |
| Network fails at venue | Low | High | Local server, USB backup of demo video (self-reference only) |

### Decisions Locked

- HAP is the protocol. HEART is the implementation. ARCA never mentioned.
- 3 dashboard views (not 8). 3 flow profiles implemented (not 10).
- No biometric demo (Q&A only). No real RAG (markdown files).
- Single-screen demo (no video segments mid-pitch).
- ElevenLabs gesture: one voice line in arrival sequence.
- Pitch script in English. Demo UI in English. Spec in English.

### Open Questions

- [ ] Guillermo's additional work — to be merged in (he'll share it)
- [ ] Final voice ID for ElevenLabs (warm female mid-pitch, or warm male?)
- [ ] Slide app: Pitch.com or Keynote?
- [ ] Live demo on Luis's laptop or external screen?

---

## Commands Reference

```bash
# Start MCP server
cd server && python main.py

# Start dashboard
cd dashboard && pnpm dev

# Run CLI fallback (Plan B)
cd server && python demo_runner.py

# Deploy dashboard to Vercel (if needed)
cd dashboard && vercel deploy --prod

# Commit and push (when ready)
git add . && git commit -m "..." && git push origin main
```
