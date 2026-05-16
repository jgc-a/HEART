# The Morning Brief

The single page a Rosewood Sand Hill General Manager opens at 7 AM with their
coffee. Six questions answered in thirty seconds:

1. Did anything serious happen overnight?
2. Who arrives today and who matters?
3. How are we tracking against LQA / Forbes this week?
4. What's our revenue position?
5. What new reviews need attention?
6. What human decisions need to be made today?

## Routes

- **`/view`** — landing page with the four operator views. Only the Morning
  Brief is wired today; the others (In-Stay Matters, Today's Arrivals detail,
  ECHO Matters) are marked *Next* / *Later*.
- **`/view/morning-brief`** — the GM's page. Mounted at
  `luis/dashboard/app/view/morning-brief/page.tsx`. Covers the full viewport
  (`position: fixed; inset: 0`) so it sits over the standard dashboard chrome
  with the GM's own minimal frame.

The new route is also wired into the unified platform shell at
`http://localhost:5570` as a sidebar module titled **Morning Brief**
(group: *Operator views*).

## Seven zones

| # | Zone | Source | Refresh |
|---|---|---|---|
| 1 | Brief sentence + 3 inline stats | `POST /api/heart/v1/brief/morning` (Claude Haiku 4.5 over property state) | 10 s |
| 2 | Matters (Attention Queue) | `GET /api/heart/v1/human-queue` | 10 s |
| 3 | Whom we welcome (Today's Arrivals) | `GET /api/heart/v1/arrivals/significant` (sorted: VIP > Celebratory > Family > Wellness > Bleisure > Corporate > General; VIP-Discrete masked unless `?reveal=1`) | 10 s |
| 4 | Pulse — Standard of Care | `GET /api/heart/v1/metrics` | 5 min |
| 5 | Revenue & flow | `GET /api/heart/v1/revenue/today` | 5 min |
| 6 | Reputation | `GET /api/heart/v1/reviews/recent` | 5 min |
| 7 | Staff amplification | `GET /api/heart/v1/staff/amplification` | 5 min |

"Attend to →" actions on Zone 2 open a slide-over with the matter's context
and an Acknowledge action. The full audit chain stays in the existing
`/care-protocol` and `/audit/roots` endpoints.

## What was built

**Backend (`heart/server.py`):**
- `POST /api/heart/v1/brief/morning` — Claude composes a single sentence
  (max 25 words, "Good morning."-opener, no SaaS vocabulary) from the
  current state of guests, the human-queue, and the last 12 h of HAP
  events. Falls back to a composed sentence if the API hiccups. Token
  usage logged through `log_arca_usage` so the ROI dashboard reflects it.
- `GET /api/heart/v1/arrivals/significant` — `ARRIVING_TODAY` guests
  sorted by the GM's significance order, with VIP-Discrete masked to
  initials by default.
- `GET /api/heart/v1/revenue/today` — coherent synthesized revenue
  anchored on the property's real 121-room footprint and flow-weighted
  ADR table; occupancy is derived from the seed plus a credible 78 %
  baseline.
- `GET /api/heart/v1/reviews/recent` — six-review feed across
  TripAdvisor / Google / Booking.com / Trustpilot / TrustYou. One
  negative review is flagged for dispute and links to any existing
  WARDEN brief in `dispute_briefs`.
- `GET /api/heart/v1/staff/amplification` — *briefs_delivered_yesterday*
  is **real** (counted from `hap_events`); acceptance rate, internal NPS,
  and the top-three staff recognition list are property-level stubs.

**Frontend (`luis/dashboard/app/view/`):**
- `page.tsx` — `/view` landing.
- `morning-brief/page.tsx` — the dashboard.
- `morning-brief/layout.tsx` — sets the browser title to
  *"The Morning Brief · Rosewood Sand Hill"*.

Pure SVG sparklines are inlined (no chart dependency). Skeleton states are
italic muted lines, never spinners. Slide-over is implemented inline (no
new dependency).

## What is stubbed and needs real wiring

- **Acceptance rate / internal NPS / top-three staff** — pulled from
  hardcoded values in `staff_amplification`. Replace with the staff-app
  tap-back signal once that's deployed.
- **Reviews feed** — `_REVIEW_FEED` is a hand-curated list of six. Real
  production should pull from the platform APIs (TripAdvisor partner,
  Booking Extranet, etc.). The dispute-brief linkage is real: when the
  GM clicks *Generate dispute brief →* on a flagged review they land in
  the existing `/reputation` page that calls
  `/api/heart/v1/dispute-brief/generate`.
- **Revenue numbers** — derived from the seeded guest count + flow
  weighting + a 78 % occupancy baseline. They are **coherent** rather
  than fabricated, but PMS integration is the right long-term source.
- **Lifetime Connection Score** in Zone 4 — derived as
  `asc_score * 0.78` as a placeholder. Real version should aggregate
  KINDRED returns / repeat-stay signal.
- **Acknowledge action** on the slide-over currently just closes the
  panel. To resolve the matter it should call
  `POST /api/heart/v1/human-queue/<id>/resolve` (already exists).

## Architectural decisions made (not in the prompt)

1. **Mounted in Luis's Next.js**, not a new project. The Rosewood
   typography and tokens already exist in `luis/dashboard/`. Spec
   palette is honoured — the existing tokens are within a few hex
   units of the spec values, and I added a new `--color-terracotta`
   (`#b85042`) token for negative deltas.
2. **Reused existing tokens**: `cream` (#f5f1e8), `bronze` (#8b6f47),
   `forest` (#2d4a3e), `ink` (#1a1a1a). Strict no-other-color rule
   respected throughout.
3. **No new dependencies.** No SWR, no charts, no spinner libraries.
   Refresh is plain `setInterval`; sparklines are inline SVG; the
   slide-over is a plain `<aside>` over a backdrop.
4. **Full-viewport overlay** (`position: fixed; inset: 0`) so the page
   covers the standard dashboard header/footer. The GM experience is
   the whole screen, not a panel inside a chrome.
5. **VIP-Discrete masking** at the API layer (not just the client). The
   only way to surface a name is `?reveal=1` on the endpoint, which
   maps to a future GM-role check.
6. **Synthesized data is coherent, never random.** Occupancy ties to the
   real seed; ADR per flow is anchored on actual Rosewood Sand Hill
   rate ranges; the 7-day sparkline trend is a deterministic
   sine/cosine micro-drift around the current value so it doesn't move
   every refresh.

## Follow-up tasks

The other operator views referenced from `/view`:
- **In-Stay Matters** — for the Duty Manager. Live shift view of every
  active reservation, with the Care Protocol Verifier inline.
- **Today's Arrivals (detail)** — for Front Office. Each arrival fully
  expanded with ETA + flight + traffic, brief, prepared room status.
- **ECHO Matters** — for Housekeeping & Concierge. Property restitution
  signals, pre-arrival staging.

And the existing modules that are already operational and could be
folded into `/view` once they get the Morning Brief treatment:
- **Reputation Audit** (`/reputation` + Care Protocol Verifier in
  `http://localhost:5570/#reputation`).
- **Human-Required Queue** (`#humanqueue`).
- **HAP Console** (`#hapconsole`).
- **PARLEY** — the live agent-to-agent negotiation surface (not yet
  built).
