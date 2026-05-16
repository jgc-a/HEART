# Flow Profiles

The 10 flow profiles are documented in full in `../../../docs/10-flows.md`.

This directory will hold one markdown file per profile (`01-general.md` through `10-transit-layover.md`) used by HAP-RAG at runtime. For the hackathon demo, the consolidated `docs/10-flows.md` is the source of truth.

Profiles covered:

1. General (fallback)
2. Corporate
3. Bleisure
4. Special Dates (Anniversary, Birthday, Honeymoon, Engagement, Bereavement)
5. Wellness / Recovery
6. VIP-Discrete / Celebrity
7. Family with Minors *(triggers human-required check-in)*
8. Group / Wedding Party / Multi-Guest Event
9. Medical / Compassionate
10. Transit / Layover

Each profile defines: trigger criteria, service adaptations, operational rules, billing default, upsell policy, tone guidelines.

The inviolable rules (complaints → human, minors → human, maintenance → human) apply across all profiles.
