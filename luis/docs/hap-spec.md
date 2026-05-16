# HAP — Hospitality Agent Protocol

**Draft Specification v0.1**
**Status:** Pre-RFC / Draft
**Authors:** AISociety (Luis Vargas, Guillermo)
**Date:** May 16, 2026
**License:** Open, to be released under Apache 2.0 upon ratification.

---

## Abstract

HAP (Hospitality Agent Protocol) is an open application-layer protocol that defines how an arbitrary guest-controlled AI agent (the **Guest Agent**) communicates with a hotel-controlled AI agent (the **Concierge Agent**) on behalf of a guest, with explicit scope-based consent, time-bounded authorization, and zero-retention semantics.

HAP extends Anthropic's **Model Context Protocol (MCP)** as a transport for tool calls between agents and proposes additional protocol-level guarantees specific to hospitality.

## 1. Goals & Non-Goals

### 1.1 Goals
- Let a Guest Agent share preferences with a Concierge Agent **only with explicit authorization**.
- Enable on-demand queries from the hotel **without persistent guest data storage**.
- Define a **cross-property** identity layer that travels with the guest.
- Define **hospitality-specific events** (arrival, in-stay, post-stay, complaint, maintenance).
- Define **operational rules** that must escalate to humans (complaints, minors, maintenance).
- Provide **cryptographic auditability** for reputation defense.

### 1.2 Non-Goals
- HAP is not a CRM.
- HAP does not specify physical hotel systems (PMS, POS, key locks).
- HAP does not require a specific LLM provider.

## 2. Roles

| Role | Description |
|---|---|
| **Guest** | The human traveler. |
| **Guest Agent** | The AI agent acting on behalf of the Guest. Examples: Anthropic Claude, OpenAI ChatGPT, Google Gemini, custom. |
| **Concierge Agent** | The AI agent operated by the hotel. Includes the property's HAP server and the LLM behind it. |
| **Property** | The physical hotel and its operational systems. |
| **HAP Network** | The federation of HAP-compliant properties. |

## 3. Components

| Component | Purpose | Status |
|---|---|---|
| **HAP-AUTH** | Handshake, scope authorization, TTL | v0.1 |
| **HAP-SCHEMA** | Guest profile schema | v0.1 |
| **HAP-EVENTS** | Lifecycle events of the guest journey | v0.1 |
| **HAP-IDENTITY** | Universal Guest GUID across properties | v0.1 |
| **HAP-BIOMETRIC** | Hardware-anchored identity attestation at check-in | v0.1 |
| **HAP-RAG** | Property-side knowledge base (brand, SOPs, Sense of Place) | v0.1 |
| **HAP-RIGHTS** | Guest rights (GDPR-aligned, ARCO-compliant for MX) | v0.1 |
| **HAP-NETWORK** | Cross-property interoperability | v0.1 |

---

## 4. HAP-AUTH

### 4.1 Handshake

The Guest Agent initiates a handshake with a Concierge Agent:

```json
POST /hap/v1/handshake
{
  "guest_guid": "hap-guid-018f...",
  "agent_id": "claude-desktop-anthropic",
  "scope_requested": [
    "arrival.date_and_flight",
    "preferences.lodging",
    "preferences.dietary",
    "preferences.cultural",
    "calendar.conflicts",
    "health.context"
  ],
  "ttl_hours": 72,
  "intent": "pre_arrival_orchestration",
  "property_id": "rosewood-sand-hill"
}
```

The Concierge Agent responds with the **subset of scopes the property needs** plus a consent token:

```json
{
  "session_id": "hap-session-018f...",
  "scope_granted": [...],
  "ttl_expires_at": "2026-05-21T10:42:00Z",
  "consent_token": "hap_ct_signed_jwt",
  "audit_url": "https://heart.rosewood/audit/hap-session-018f..."
}
```

### 4.2 Scope Vocabulary

Top-level scopes:

- `arrival.*` — date, flight, transport, party size
- `preferences.lodging` — room temp, mattress, lighting, sound
- `preferences.dietary` — restrictions, preferences, allergies
- `preferences.cultural` — language, regional, beverage
- `preferences.wellness` — spa, fitness, sleep
- `calendar.*` — conflicts, meetings, occasions
- `health.context` — *opt-in only*, used for accessibility / dietary
- `family.signals` — *opt-in only*, used for kid-friendly amenities
- `billing.method` — *required for check-in*
- `loyalty.programs` — Rosewood Elite, partner programs
- `identity.verified` — HAP-Identity attestation

### 4.3 TTL

Default TTL: **72 hours** from check-out.
Max TTL: **30 days** (post-stay window).
Minimum TTL: **1 hour** (for transit / layover profiles).

### 4.4 Revocation

The Guest may revoke any scope at any time via `POST /hap/v1/revoke`. Effective immediately.

---

## 5. HAP-SCHEMA

The canonical Guest profile schema. The Guest Agent populates it; the Concierge Agent never persists it.

```json
{
  "guest_guid": "hap-guid-...",
  "canonical_name": "string",
  "arrival": { "date": "...", "flight": "...", "party_size": int },
  "preferences": {
    "lodging": { ... },
    "dietary": { ... },
    "cultural": { ... },
    "wellness": { ... }
  },
  "calendar": { "conflicts": [...] },
  "health": { "context": "optional, opt-in only" },
  "billing": { "method": "verified_token" },
  "loyalty": { ... }
}
```

---

## 6. HAP-EVENTS

| Event | When | Emitted by |
|---|---|---|
| `HAP.RESERVATION.CONFIRMED` | Booking complete | Property |
| `HAP.PRE_ARRIVAL.HANDSHAKE_INITIATED` | Guest Agent reaches out | Guest Agent |
| `HAP.GUEST_STATE.ASSESSED` | Flow profile classified | Concierge Agent |
| `HAP.FLOW.SELECTED` | Profile locked (one of 10) | Concierge Agent |
| `HAP.IDENTITY.RESOLVED` | GUID validated | Concierge Agent |
| `HAP.CHECK_IN.COMPLETED` | After biometric + payment | Property |
| `HAP.IN_STAY.PROACTIVE_OFFER` | Concierge offers something | Concierge Agent |
| `HAP.IN_STAY.COMPLAINT_ESCALATED` | **Mandatory human escalation** | Concierge Agent |
| `HAP.IN_STAY.MAINTENANCE_REPORTED` | **Mandatory human escalation** | Concierge Agent |
| `HAP.IN_STAY.ROOM_SERVICE_SYNC` | T-20min coordination | Concierge Agent |
| `HAP.CHECK_OUT.COMPLETED` | Departure | Property |
| `HAP.MEMORY.RETURNED_TO_GUEST` | Memory snapshot sent back to Guest Agent | Concierge Agent |
| `HAP.REPUTATION.LOG_FROZEN` | Stay timeline sealed for dispute use | Concierge Agent |

---

## 7. HAP-IDENTITY

Universal Guest GUID. One identity across the HAP Network.

```json
{
  "guest_guid": "hap-guid-{uuid-v7}",
  "canonical_name": "verified by passport",
  "name_variants": ["aliases", "transliterations"],
  "email_accounts": [{ "address": "...", "purpose": "personal|corporate" }],
  "loyalty_accounts": [...],
  "phone_numbers": [...],
  "biometric_enrollment": { "template_hash": "...", "enrolled_property": "..." },
  "merge_history": [...]
}
```

**Rule:** Two GUIDs for the same person SHALL NOT exist. Auto-merge with confidence threshold ≥ 0.95; human verification required below.

---

## 8. HAP-BIOMETRIC

At check-in, hardware-anchored identity attestation.

- Face match (1:1, against enrolled template)
- NFC tap from guest's device
- Liveness detection (anti-spoof)
- Template stored only in property Secure Element
- **Only a match hash** transmitted in HAP
- Comparable trust model to Apple Pay / Secure Enclave

Use case beyond identity: **charge-back protection, fraud prevention, legal evidence for disputes**.

---

## 9. HAP-RAG

Property-side Retrieval-Augmented Generation knowledge base. Includes:

- Property operations manual
- Service SOPs
- Cancellation, no-show, late check-out policies
- LQA / Forbes Five-Star applicable standards
- Brand voice (tone, vocabulary, "no-go" verbal)
- F&B menus with sommelier notes
- Spa catalog
- Local cultural map (the Sense of Place anchor)
- Emergency / medical / evacuation protocols
- Accessibility, pets, minors policies

The Concierge Agent **consults HAP-RAG before any output**. Deviations from brand voice are corrected pre-emission.

---

## 10. HAP-RIGHTS

Inalienable guest rights, enforced at protocol level.

- **Right to know** what has been authorized (audit URL always accessible)
- **Right to revoke** any scope at any time
- **Right to be forgotten** post-checkout (data destruction confirmation)
- **Right to portability** (memory snapshot returned to Guest Agent at checkout)
- **Right to dispute** any HAP-mediated decision (logged for review)

Aligned with: **GDPR (EU)**, **CCPA (US)**, **LFPDPPP / ARCO (Mexico)**.

---

## 11. HAP-NETWORK

Cross-property semantics.

- Guest GUID is universal.
- Each property session is independent: handshake, scope, TTL.
- No cross-property data leakage by default.
- Optional **opt-in cross-property continuity** (e.g., loyalty programs, repeat preferences) — explicit per-property opt-in required.

---

## 12. Operational Rules (Inviolable)

The protocol mandates the following escalations:

| Trigger | Required Action |
|---|---|
| Complaint detected (tone or content) | Concierge Agent SHALL silence and escalate to Duty Manager + Guest Relations human within 60 seconds. |
| Maintenance fault reported | Concierge Agent SHALL escalate to Engineering human. No autonomous troubleshooting. |
| Check-in with minors | Check-in SHALL be performed by a human, with documentary verification. |
| Biometric mismatch | Concierge Agent SHALL escalate to senior staff + supervisor. |
| Compassionate / bereavement signal | Upsell SHALL be disabled. Tone SHALL be paused. KINDRED (affective continuity) SHALL be off by default. |

Violations of these rules invalidate HAP compliance.

---

## 13. Reference Implementation

**HEART** — Human-centric Experience Agent for Rosewood Travelers.

Repository: `github.com/luisvargasfdz/rosewood-hackathon-aisociety`

Includes:
- MCP server with the five HAP tools
- Mock data for four guests, one property, ten flow profiles
- "The View" operational dashboard (Next.js)
- Cryptographically signed audit log

---

## 14. Open Questions for v0.2

- Standardization body (IETF? W3C? Open Travel Alliance?)
- Industry coalition for cross-vendor implementation (Rosewood + Aman + Belmond?)
- Certification process for HAP-compliance
- Pricing of reference implementation
- Conformance test suite

---

## Appendix A — Glossary

- **A2A** — Agent-to-Agent communication
- **MCP** — Model Context Protocol (Anthropic)
- **Sense of Place** — Rosewood's brand philosophy: each property reflects its locale
- **LQA** — Leading Quality Assurance (luxury hospitality standard)
- **ARCO** — Mexican personal data rights (Access, Rectify, Cancel, Oppose)

---

*This is a draft. Comments welcome via GitHub issues.*
