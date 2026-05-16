# The 10 Guest Flow Profiles

> Each profile defines how HEART (the concierge agent) classifies a guest, sets defaults, and adapts service. This is the **unfair advantage** of the protocol: granular hospitality intelligence at the protocol level.

---

## 1. General (Fallback)

- **Trigger:** minimal data, first contact.
- **Tone:** Forbes baseline courtesy.
- **Defaults:** progressive preference capture, no assumptions.
- **Billing:** personal.

## 2. Corporate

- **Trigger:** corporate-domain email, EA booking, billing center configured, calendar with business meetings.
- **Adaptations:**
  - Executive setup: desk, filtered water, early espresso, sector-relevant press.
  - Smart wake-up calls before meetings.
  - Laundry / pressing express by default.
  - Car service pre-coordinated for external meetings.
  - Minimal lobby presence.
- **Billing:** corporate (pre-loaded).
- **Upsell:** essentials only (pressing, car, late check-out).

## 3. Bleisure

- **Trigger:** business booking + weekend extension OR mixed corporate/leisure calendar.
- **Adaptations:**
  - Corporate mode Mon-Fri.
  - Pivot to Discovery / Restorative mode on weekend.
  - Sense of Place recommendations activated at transition.
  - Companion (if declared) receives own travel identity.
- **Billing:** split corporate (business days) + personal (leisure days), with authorization.
- **Upsell:** local experiences in leisure window.

## 4. Special Dates

- **Sub-types:** Anniversary, Birthday, Honeymoon, Engagement, Milestone, **Bereavement** (inverse sensitivity).
- **Trigger:** date detected in HAP-SCHEMA Category D (opt-in) OR declared at booking OR inferred from companion + suite type.
- **Adaptations:**
  - Pre-orchestrated surprise gesture (never generic).
  - Local network coordination: florist, sommelier, chef.
  - Upgrade evaluated if loyalty + occasion justify.
  - Warm-elevated tone, never invasive.
  - **Bereavement exception:** paused tone, zero celebration, maximum privacy.
- **Billing:** usually personal.
- **Upsell:** memorable experiences, not transactional.

## 5. Wellness / Recovery

- **Trigger:** multi-day spa booking, declared post-surgical, sabbatical, retreat, burnout, treating physician in the property's city.
- **Adaptations:**
  - Quietest room, maximum natural light.
  - Diet and schedules synced with recovery protocol.
  - Wake-up calls disabled except emergency.
  - Spa and wellness pre-booked.
  - Zero intrusion, maximum silence-as-service.
  - Coordination with local practitioners network (authorized).
- **Billing:** personal (rarely corporate).
- **Upsell:** very selective, deep wellness only.

## 6. VIP-Discrete / Celebrity

- **Trigger:** high public exposure, NDA at booking, accompanying security, private route entry requested.
- **Adaptations:**
  - Check-in off-lobby.
  - Staff brief with reinforced discretion.
  - Operational alias used in all comms.
  - Zero photo, zero post, zero cross-staff mention.
  - Movement coordination with own security.
  - KINDRED (affective continuity) off by default.
- **Billing:** legal team / management handles.
- **Upsell:** disabled. Maximum invisible service.

## 7. Family with Minors

- **Trigger:** declared presence of minors at booking.
- **Adaptations (MANDATORY):**
  - **Check-in ALWAYS by human (HAP-RULE 4.3, inviolable).**
  - Documentary verification of each minor.
  - Connecting rooms or family suite.
  - Children amenities with parental consent.
  - Children menu activated.
  - Staff brief: lost child protocols, no alcohol to adults in pool/bar with minors present.
  - KIDS-aware Sense of Place: local family experiences.
- **Billing:** personal.
- **Upsell:** family experiences only, never to the minor.

## 8. Group / Wedding Party / Multi-Guest Event

- **Trigger:** block reservation, master reservation, associated event.
- **Adaptations:**
  - Lead guest identified (organizer).
  - Sub-agents per guest coordinated with master HAP session.
  - Shared logistics (transfers, catering, F&B).
  - Cross-guest signal: incidents notify master agent (with consent).
- **Billing:** master + incidentals per room.
- **Upsell:** group experiences, photography, coordinated late check-out.

## 9. Medical / Compassionate

- **Trigger:** medical declaration, nearby hospital in calendar, funeral / mourning, condition requiring adaptation.
- **Adaptations:**
  - Accessible room, medical equipment allowed.
  - Coordination with hospital / physician (authorized).
  - Medical diet absolutely respected.
  - **Zero upsell. Zero performative joy.**
  - Staff brief: compassionate care protocol.
  - Reinforced privacy.
- **Billing:** personal or medical insurance.
- **Upsell:** disabled.

## 10. Transit / Layover

- **Trigger:** stay < 24h, confirmed connecting flight.
- **Adaptations:**
  - Express check-in pre-completed.
  - Room ready for immediate rest.
  - Wake-up call linked to departure flight.
  - Zero itinerary proposed.
  - Simplified welcome amenity.
- **Billing:** personal or airline (delay compensation).
- **Upsell:** recovery only (shower + nap).

---

## Demo Coverage

For the live demo (12-hour scope), only **3 profiles are implemented** in code:

1. **Bleisure** (Luis Vargas — main demo persona)
2. **Corporate** (Marcus Chen, Guillermo — slide examples)
3. **Family with Minors** (Family Johnson — triggers human escalation in HAP Console)

The other 7 are mentioned in Slide 4 and defended in Q&A.

---

## Inviolable Operational Rules

These apply across ALL profiles and are enforced at the protocol level:

| Rule | Trigger | Required Action |
|---|---|---|
| **4.1** | Complaint detected | Silence agent. Escalate to Duty Manager + Guest Relations human within 60s. |
| **4.2** | Maintenance fault | Escalate to Engineering. No autonomous troubleshooting. |
| **4.3** | Minor in party | Check-in by human. Documentary verification. |
| **4.4** | Payment / pre-auth | Cannot complete check-in without verified method. |
| **4.5** | Biometric mismatch | Escalate to senior staff + supervisor. |
| **4.6** | Compassionate signal | Upsell off. KINDRED off. Tone paused. |
| **4.7** | Housekeeping early trigger | Confidence threshold + WARDEN audit + "stop" mechanism. |
| **4.8** | Room service sync | T-minus-20-minutes coordination with kitchen. |
| **4.9** | Audit trail | Every interaction logged immutably for reputation defense. |

**These rules are non-negotiable. Compliance with them is what makes a property HAP-compliant.**
