# Merge Protocol — Integrating Guillermo's Work

> Guillermo has been working in parallel on the ARCA/HEART architecture and concept documents.
> This doc defines how to merge his work into this repo without scope creep or jargon overload.

## Naming Discipline (locked)

Public-facing surfaces (pitch, slides, demo UI, GitHub README, HAP spec):

| Name | Use? | Where |
|---|---|---|
| **HAP** | ✅ Yes — central | All public surfaces. The protocol. |
| **HEART** | ✅ Yes — sparingly | Mentioned as "reference implementation". Once or twice max in pitch. |
| **AISociety** | ✅ Yes | Team name. Footer of slides. |
| **Rosewood** | ✅ Yes | Property name. Brand. |
| **ARCA** | ❌ NO | Internal motor. Never mentioned. |
| **B Drive IT** | ❌ NO | Parent company. Never mentioned. |
| **WARDEN** | ❌ NO publicly | Internal audit name. Use "audit log" or "cryptographic signature" externally. |
| **ECHO** | ❌ NO | Internal restitution. Not in pitch. |
| **KINDRED** | ❌ NO | Internal affective continuity. Not in pitch. |
| **ASC** | ❌ NO | Internal standard of care metric. Not in pitch. |
| **ARP** | ⚠️ Maybe | "Agentic Resource Platform" — soundbite. Use only if confidence is high it lands. |
| **Sense of Place** | ✅ Yes | Rosewood's own brand phrase. Always credit them implicitly. |

## What to merge IN

When Guillermo shares his work, integrate the following:

- **HAP-IDENTITY GUID schema** — already in `docs/hap-spec.md` section 7. Verify and enrich.
- **HAP-BIOMETRIC** — already in spec. Just enhance the Q&A defense.
- **HAP-RAG** — already mentioned. Make sure flow files are robust (in `server/data/flows/`).
- **10 flow profiles** — already in `docs/10-flows.md`. Verify each is correctly described.
- **Operational rules** — already in spec and flows. Cross-check exhaustively.
- **Dispute brief** — already in storyboard. Verify the WARDEN signature concept survives without the WARDEN name.
- **The View dashboard 8 vistas** — collapse to **3 for demo** (Today's Arrivals, HAP Console, Reputation Audit). Mention the other 5 in Q&A if asked.

## What to KEEP OUT (or rename)

- **HEART** as a heavy product narrative — soft-pedal. The pitch is about HAP, not HEART.
- **WARDEN/ECHO/KINDRED** as branded components — rename in any docs intended for external eyes.
- **ARCA as the motor** — entirely out.
- **ARP as paradigm** — only one mention max, as a soundbite. Don't dwell.
- **Subagent names (Orchestrator/Shadow/Thread)** — fine internally, but in the pitch say "pre-arrival agent", "in-stay agent", "post-stay agent" — simpler language.

## How to handle Guillermo's docs

When he shares a doc:

1. Read it for content.
2. Identify the parts that strengthen HAP (the protocol).
3. Strip the internal naming (ARCA, WARDEN, etc.).
4. Integrate the strengthened content into:
   - `docs/hap-spec.md` (if it's protocol-level)
   - `docs/10-flows.md` (if it's flow profiles)
   - `docs/qa-cheatsheet.md` (if it's defense logic)
   - `server/data/flows/*.md` (if it's per-flow operational detail)
5. Commit with a clear message: `merge: Guillermo's [topic] integrated as [where]`

## Conflict resolution

If Guillermo's narrative pushes toward HEART/ARCA as the headline:

> **Push back firmly.** The hackathon scoring rewards a clean, original positioning. "HAP is an open protocol" is a stronger pitch than "HEART is our SaaS for hotels."

If Guillermo pushes for more features in 12 hours:

> **Push back firmly.** Scope freeze at hour 8 is non-negotiable. Quality > quantity.

If Guillermo pushes for a different punchline:

> **Bring it to Luis.** Two opinions on a punchline mean we test both with a stopwatch and pick the one that lands cleaner.

## Coordination

- Each major merge gets a commit.
- Each commit message starts with `merge:` if it's integrating Guillermo's work.
- Each contribution is logged in `docs/12-hour-plan.md` status board.
- No silent merges — Luis reviews before committing.
