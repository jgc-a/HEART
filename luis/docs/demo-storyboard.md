# Demo Storyboard — 3 Minutes, Live

> Live demo for Hospitality 2030: A Rosewood Sand Hill Hackathon.
> Scoring: Impact 20% / **Live Demo 45%** / Creativity 35%.
> Everything below happens **on a single shared screen**. No pre-recorded video.

## Screen Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  [Phase: PRE-ARRIVAL | CHECK-IN | IN-STAY | POST-STAY]           │
├─────────────────────────────────┬────────────────────────────────┤
│                                 │                                │
│  GUEST SIDE                     │  ROSEWOOD — THE VIEW            │
│  Claude Desktop                 │  (Next.js dashboard)            │
│  with HAP MCP installed         │                                │
│                                 │  Panels:                       │
│  Chat with Claude               │   1. Today's Arrivals          │
│                                 │   2. HAP Console (live)        │
│                                 │   3. Staff Brief Generator     │
│  Consent Checklist UI           │   4. Audit Log (streaming)     │
│  (rendered as message)          │   5. Reputation Audit          │
│                                 │                                │
└─────────────────────────────────┴────────────────────────────────┘
```

---

## Cue Sheet (3:00 total)

### 0:00 — 0:15 — HOOK (Slide 1)
**Luis on stage. Slide visible. No demo yet.**

> *"In 2030, you won't convince humans to choose your hotel. You'll convince their agents. Agents are the new SEO. Rosewood is where agents bring their humans."*

Pause. Click to next slide.

### 0:15 — 0:40 — PROBLEM (Slide 2)
**Slide 2 visible.**

> *"Today hotels run on ERPs. Today guests run on apps. By 2030 both are dead. Hotels will run on Agentic Resource Platforms. Guests will run on personal agents — Claude, ChatGPT, the AI in their phone. The question isn't whether this happens. It's HOW agents talk to hotels. Today, they can't."*

Click to next.

### 0:40 — 0:55 — INTRODUCE HAP (Slide 3)
**Slide 3 visible — single sentence.**

> *"Anthropic built MCP to connect models to the world. We propose HAP — Hospitality Agent Protocol — to connect guests to hospitality. Open. Auditable. Zero retention. Let me show you."*

Switch to demo layout.

### 0:55 — 2:00 — DEMO #1: THE HANDSHAKE (LIVE)
**Split screen. Left: Claude Desktop. Right: The View dashboard.**

**0:55 — 1:00** — Luis (typing in Claude):

> `Voy a Rosewood Sand Hill el 18 de mayo, tengo reuniones en Sand Hill Road.`

**1:00 — 1:15** — Claude responds, detects HAP MCP, renders **Consent Checklist**:

```
🔐 Rosewood Sand Hill is requesting authorization.

What I can share with the hotel:
  ☑ Arrival date & flight (TTL: until check-out)
  ☑ Lodging preferences (firm mattress, dim lighting)
  ☑ Calendar conflicts (block patio Wed 2-4pm)
  ☑ Dietary restrictions (no shellfish)
  ☐ Health context (back pain — optional)
  ☑ Cultural preferences (matcha tea, jazz)
  ☐ Family signals (not relevant this trip)

[Approve & Send] [Customize] [Cancel]
```

Luis clicks one box off (`Health context`). Clicks **Approve & Send**.

**1:15 — 1:25** — Right side: **HAP Console** shows handshake live.

```
[10:42:13] HAP.HANDSHAKE.RECEIVED  guest=luis_v  scope=[6 items]  ttl=72h
[10:42:13] FLOW.CLASSIFIED        profile=Bleisure (Mon-Wed corporate, Thu-Sat leisure)
[10:42:14] SENSE_OF_PLACE.LOADED  rosewood-sand-hill
[10:42:14] CONCIERGE.GENERATING...
```

**1:25 — 1:50** — Right side: **Staff Brief** materializes (cream/bronze Rosewood styling, serif font):

```
ARRIVAL BRIEF — Luis Vargas
Profile: Bleisure  •  Confidence: 0.94

ROOM PREP
  • Firm mattress requested. Replace pillows: 2 firm, 1 medium.
  • Dim lighting bias. Pre-set scene "Evening Calm".
  • Matcha tea (Uji, ceremonial grade) on welcome tray.

CALENDAR-AWARE
  • Wed 2-4pm: Patio Sur reserved (guest's external meeting).
  • Thu evening: pivot to Discovery mode. Suggest Filoli Gardens.

DIETARY
  • No shellfish. Sequoia menu flagged.

SENSE OF PLACE
  • Welcome amenity: olive oil tasting from Stanford Sierra grove.
  • Jazz playlist (low) for arrival window.

NO ACTION REQUIRED FROM GUEST.
```

**1:50 — 2:00** — ElevenLabs voice plays (warm, paused, serif-equivalent):

> *"Welcome ahead of time, Luis. Your room awaits at the temperature of an autumn evening, with matcha from Uji. Wednesday afternoon, the southern patio is yours alone."*

### 2:00 — 2:30 — DEMO #2: REPUTATION DEFENSE (LIVE)
**Pivot screen to Reputation Audit panel.**

Luis narration:

> *"But HAP isn't only for the guest. It's also for Rosewood. Every interaction is logged with a cryptographic seal — zero retention of guest data, full retention of operational truth. Watch."*

Click button: **`Simulate Tripadvisor 2-star review`**

Dashboard shows simulated review:

```
"Stayed at Rosewood Sand Hill — terrible AC, took forever to fix.
Worst service. Will not return." — @anonguest_72
```

Click button: **`Generate dispute brief`**

Dashboard renders the **WARDEN-signed dispute brief**:

```
DISPUTE BRIEF — Stay #SH-2026-0518-LV
Signed: WARDEN-HEART  •  Hash: 8f3c2a...e1
Generated: 2026-05-22 14:33:09 UTC

TIMELINE OF AC INCIDENT
  17:42 — Guest temperature complaint logged via Shadow.
  17:43 — Shadow silenced. Engineering escalation TRIGGERED.
  17:43 — Duty Manager paged (dual escalation per HAP-RULE 4.1).
  17:47 — Engineer Marco D. arrived. ETA 4 min from page.
  17:51 — AC unit cycle reset. Confirmed cool airflow.
  17:53 — Guest acknowledged resolution. Tone: satisfied.
  18:10 — Complimentary turndown amenity sent.

TOTAL TIME TO RESOLUTION: 11 minutes.
DUAL HUMAN ESCALATION: confirmed.
GUEST AT POINT OF DEPARTURE: satisfied per Shadow signal.

This brief is auditable. The signal trail is immutable.
```

Luis:

> *"This brief saves the GM 4 hours every time a review like this lands. And gives Rosewood real legal standing with TrustYou, Tripadvisor, and Google. That's ROI."*

### 2:30 — 2:50 — SHOW SCOPE (Slide 4)
**Slide 4 visible: 10 flow profiles on one slide.**

> *"HAP covers 10 guest profiles. Bleisure. Wellness. Family with minors. Compassionate. VIP-Discrete. Each with operational rules. The biggest one: **complaints always escalate to a human. Children always check in with a human. The AI augments staff, never replaces them.** That's how ultra-luxury survives the agentic era."*

### 2:50 — 3:00 — CLOSE (Slide 5)
**Slide 5: just three words on screen.**

> *"Open protocol. Reference implementation. Rosewood defines the category. HAP is on GitHub today. Thank you."*

---

## What Has to Work Live (Non-Negotiable)

1. **Claude Desktop ↔ HAP MCP handshake** (the consent checklist must render).
2. **Staff brief generation** must complete in < 15 seconds.
3. **Dispute brief generation** must work and look credible.
4. **Audit log** must stream visibly during the demo.
5. **ElevenLabs voice** must play at 1:50. If it fails, skip silently — don't acknowledge.

## Plan B (if MCP fails)

- CLI fallback: `python demo_runner.py` runs the same flow with mocked Claude responses.
- The View dashboard runs independently and shows the same data via direct API calls.
- Pivot narration: *"Let me show you the dashboard side first..."* — never say the word "broken".

## Rehearsal Checklist

- [ ] Pitch run 1: cold (no warm-up). Time it. Target 2:55.
- [ ] Pitch run 2: emphasize the two wow moments.
- [ ] Pitch run 3: with potential interruption ("what if AC complaint scenario crashes?").
- [ ] Q&A: 10 questions rehearsed, 25 seconds each max.
- [ ] Final dress rehearsal at hour 11.

## Slide Cues (for slide-runner)

| Slide | When to advance | What's visible |
|---|---|---|
| 1 | 0:00 | Punchline only |
| 2 | 0:15 | ERPs vs Agentic Resource Platforms |
| 3 | 0:40 | HAP = MCP for hospitality |
| (live) | 0:55–2:30 | Demo layout |
| 4 | 2:30 | 10 flow profiles grid |
| 5 | 2:50 | "Open protocol. Reference implementation. Rosewood defines the category." |
