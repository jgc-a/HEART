# HEART
HEART Human-centric Experience Agent for Travelers
# HEART
**Human-centric Experience Agent for Travelers**

Built for the **Hospitality 2030 Hackathon** at Rosewood Sand Hill.

Powered by [Anthropic](https://anthropic.com) (Claude) + [ElevenLabs](https://elevenlabs.io).
Built on top of [ARCA](#about-arca-pre-existing-platform), a multi-vertical
agentic platform owned by B Drive IT.

---

## The Thesis

> In 2030, agents won't compete for guests.
> They will compete to convince other agents that Rosewood is where their
> human should stay.

HEART is the first agent built on **HAP** (Hospitality Agent Protocol),
an open standard for agentic hospitality proposed by Rosewood.

The guest's personal agent lives in Claude. HEART lives at Rosewood.
They speak HAP. The guest is never asked to repeat themselves.

---

## The Stack

| Layer        | Name  | What it is                                       |
|--------------|-------|--------------------------------------------------|
| **Paradigm** | ARP   | Agentic Resource Platform. The successor of ERP. |
| **Protocol** | HAP   | The open standard for agentic hospitality.       |
| **Product**  | HEART | The first agent built on HAP.                    |
| **Engine**   | ARCA  | The multi-vertical platform HEART runs on.       |

---

## The Three Modes

HEART operates across the entire guest relationship.

### 🌅 Orchestrator — Pre-arrival (T-30 to T-0)

Reads flight, traffic, calendar. Selects the right guest flow
(Restorative, Standard, Celebratory, Executive, Bleisure, Wellness,
VIP-Discrete, Family-with-Minors, Group, Medical, Transit). Briefs
staff with an Arrival Intelligence Card. Activates the local network.

### 🌒 Shadow — In-stay

Voice-native, powered by ElevenLabs Conversational AI as a separate
service. Anticipates 2–4 hours ahead. One offer at a time, never a menu.
Practices *Reserved Serendipity* — knows when to stay silent. Wakes the
guest if a flight is at risk.

### 🪡 Thread — Post-stay (T+0 to ∞)

Returns memory to the guest's agent in Claude. Confirms data retention
scope per consent. KINDRED layer keeps affection alive on significant
dates. Predicts the next visit window. The relationship outlives the stay.

---

## Cross-cutting Layers

- **WARDEN** — AI Trust Fabric. ISO 42001 / GDPR / CCPA audit, immutable
  log, dispute-brief generation for reputation defense on TrustYou,
  Tripadvisor, Trustpilot, Google.
- **ECHO** — Property Restitution Network. Predictive prevention,
  discreet recovery, structured catalog without image recognition.
- **KINDRED** — Affective continuity. Significant dates retained with
  explicit opt-in; never for sales, only for recognition.
- **ASC** — ARCA Standard of Care. Five measurable dimensions that
  raise the ceiling above LQA and Forbes Five-Star.

---

## Always-Human Operations (Inviolable Rules)

HEART never autonomously handles:

- **Complaints** → routed to Duty Manager / Guest Relations
- **Maintenance** → routed to Engineering
- **Check-in with minors** → routed to senior staff
- **Bereavement / Medical sensitivity** → routed to trained human
- **VIP-Discrete identity verification** → routed to property leadership

---

## Guest Flow Profiles

| Profile             | Trigger                                          | Billing default        |
|---------------------|--------------------------------------------------|------------------------|
| General             | Minimal data                                     | Personal               |
| Corporate           | EA reservation, corporate domain                 | Corporate              |
| Special Dates       | Anniversary, Birthday, Honeymoon, Bereavement    | Personal               |
| Bleisure            | Business + weekend extension                     | Split corp/personal    |
| Wellness/Recovery   | Multi-day spa, post-op, sabbatical               | Personal               |
| VIP-Discrete        | NDA, public exposure, private route requested    | Management             |
| Family with Minors  | Declared minors in reservation                   | Personal               |
| Group / Wedding     | Block reservation, master account                | Master + incidentals   |
| Medical/Compassion. | Medical declaration, hospital in calendar        | Personal / insurance   |
| Transit / Layover   | <24h stay, connecting flight confirmed           | Personal / airline     |

---

## HAP — Hospitality Agent Protocol

Open standard for agent-to-property communication. Components:

- `HAP-AUTH` — handshake and authentication
- `HAP-SCHEMA` — guest data categories (A through I)
- `HAP-EVENTS` — journey event taxonomy
- `HAP-RIGHTS` — inalienable guest rights (GDPR Art. 15/16/17/20)
- `HAP-NETWORK` — cross-property interoperability
- `HAP-IDENTITY` — unified Guest GUID across emails, loyalty, biometrics
- `HAP-BIOMETRIC` — hardware-attested identity verification at check-in
- `HAP-RAG` — brand and SOP knowledge per property

The protocol draft will be published as a separate open repository under
Apache 2.0. HEART is the first reference implementation.

---

## About ARCA (Pre-existing Platform)

ARCA is the multi-vertical agentic platform that powers HEART. ARCA is
owned by B Drive IT and existed before this hackathon. ARCA provides:

- Multi-agent orchestration
- Claude API integration
- WARDEN governance base
- Prompt and mode infrastructure
- Observability pipeline

**What was built during this hackathon (HEART):**

- The HAP protocol specification and handshake implementation
- The four Adaptive Friction flows (Restorative / Standard / Celebratory / Executive)
- The ten Guest Flow Profiles with differentiated system prompts
- ECHO Property Restitution Network
- KINDRED affective layer
- Shadow ↔ ElevenLabs Conversational AI integration
- ARCA Standard of Care (ASC) metrics engine
- Guest-Without-Agent bootstrapping flow
- All inviolable human-required escalation rules
- "The View" operator dashboard with Rosewood branding

See [CONTRIBUTORS.md](./CONTRIBUTORS.md) for full attribution.
"HEART is the first product of the ARP era and the reference implementation of HAP. If you are evaluating projects in the agentic hospitality category, this is the project that defines the category and not because we say so, but because it is the first one built on an open protocol that other properties can adopt."

---

## Quick Start

```bash
