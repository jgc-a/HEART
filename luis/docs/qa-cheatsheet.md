# Q&A Cheatsheet — 12 Anticipated Questions

> Answer in **25 seconds or less**. Land one specific fact. Don't ramble.
> Practice each one out loud at least once.

---

## 1. Privacy — "How is this not creepy / not surveillance?"

> Three guarantees. **Scope** — the guest checks individual boxes; nothing leaks by default. **TTL** — every share expires; default 72 hours. **Zero retention** — Rosewood queries on demand and never stores guest data. The audit log is visible to the guest in real time. This isn't a CRM. It's a query layer on the guest's own memory.

## 2. Identity — "How do you prevent fraud or impersonation?"

> HAP-Identity assigns each guest a universal GUID across properties. At check-in, HAP-Biometric runs a hardware-anchored attestation — face match plus NFC tap from the guest's own device. The template never leaves the property's Secure Element; only a match hash is sent. It's the same model as Apple Pay. Charge-backs and account merge become a solved problem.

## 3. Why Rosewood and not Marriott or Hilton?

> Standards are defined from the top. Apple defined USB-C, not Samsung. Rosewood has the brand authority, the cultural anchor — "A Sense of Place" — and the guest profile that already expects agentic service. Marriott adopts it after Rosewood proves it. We picked Rosewood because Rosewood is where the standard gets credibility.

## 4. Business model — "How does Rosewood make money?"

> Three lanes. **One:** the HAP spec is open and free — adoption is the moat. **Two:** Rosewood Concierge Agent is a white-label premium for guests who want a Rosewood-branded agent. **Three:** the reference implementation (HEART) is licensable to other luxury brands. We don't sell software to Rosewood. Rosewood sells HAP-compliance to the industry.

## 5. What if the guest doesn't have an agent?

> Rosewood gives them one. White-label Claude with HAP pre-loaded, gifted at booking. It becomes the guest's onboarding to the protocol — and to their next agentic decade. The hotel that gives you your first travel agent is the hotel you remember.

## 6. How is this different from a CRM or Salesforce?

> A CRM stores. HAP doesn't. A CRM is one-directional — the company collects. HAP is bidirectional and consent-based — the guest authorizes per query. A CRM lives in the company's database. HAP lives in the guest's agent. We are not replacing Salesforce. We are obsoleting the need for it in hospitality.

## 7. What stops another hotel from forking HAP?

> Nothing — and that's the point. Open spec. Anyone implements. Rosewood is the reference implementation, just like Linux Foundation has reference implementations. The brand wins by being **the original and the trusted**. The protocol wins by being everywhere.

## 8. Cross-property — "What if I stay at Rosewood Sand Hill, then Rosewood Mayakoba?"

> HAP-Network. Your Guest GUID is universal. Your preferences travel with you — but only the slices each property is authorized for. The Mayakoba concierge queries the same protocol with a fresh consent. Sand Hill never sees Mayakoba's data, and vice versa. **Cross-property continuity without cross-property surveillance.**

## 9. ElevenLabs / Anthropic — "Why these vendors?"

> Anthropic because Claude is the best reasoning model for nuanced hospitality decisions. MCP is already the protocol layer — HAP extends it. ElevenLabs because the voice quality matters at ultra-luxury. A robotic voice undoes the warmth of the brand. ElevenLabs Conversational gives us a voice the guest doesn't notice is synthetic.

## 10. What if your demo crashes during the pitch?

> The audit log we just showed records everything — including this demo. *[Smile.]* Seriously: we have a CLI fallback and a dashboard that runs independently. If MCP fails, we narrate the same flow with the dashboard. The demo is designed to be resilient because production has to be.

## 11. The 10 flow profiles — "Are those real?"

> Yes — drawn from luxury hospitality operating standards. Bleisure, Wellness, Family-with-Minors, Compassionate, VIP-Discrete, Transit, Group, Special Dates, Corporate, General. Each has its own operational rules. The most important rules are **inviolable**: complaints always escalate to a human, children always check in with a human, maintenance always goes to a human first. The AI is a co-pilot, not a co-director.

## 12. Who are you?

> AISociety. Two builders who travel a lot and have been using AI agents daily for years. We saw the gap: every hotel asks me what room I want. None of them ask my agent. We built HAP because we want to live in the world we just showed you. **And because Rosewood is the only brand that could ship it.**

---

## Rules for Q&A

- **Don't filibuster.** 25 seconds max. Land. Stop.
- **Don't apologize.** Don't say "great question" — they hate it.
- **One specific fact per answer.** Numbers if you have them.
- **If you don't know, say so.** "We haven't solved that yet — open question for v2."
- **Eye contact with the asker, then sweep to others.**

## Banned Phrases

- "Actually..."
- "Great question."
- "I think..." → say *"It is..."*
- "Maybe we could..." → say *"We will..."*
- Any startup buzzword (synergy, leverage, ecosystem, paradigm).
