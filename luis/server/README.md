# HAP MCP Server — HEART

Reference implementation of the **Hospitality Agent Protocol (HAP)** for **Rosewood Sand Hill**.
Five tools exposed over MCP stdio. Zero retention. Hash-chained audit log.

## Quickstart

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set ANTHROPIC_API_KEY, or leave DEMO_MODE=true
```

## Plan B — run the demo without MCP

If Claude Desktop or the MCP transport breaks during the pitch, run the CLI fallback:

```bash
python demo_runner.py
```

This exercises all 5 tools end-to-end (handshake → arrival → in-stay complaint
escalation → post-stay memory → dispute brief) and prints every output that
Claude Desktop would receive.

## Install into Claude Desktop

Copy `claude_desktop_config.example.json` into Claude Desktop's config:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Then **restart Claude Desktop**. In a chat, type:

> Voy a Rosewood Sand Hill el 18 de mayo, tengo reuniones en Sand Hill Road.

Claude will discover the HAP MCP server and call `hap_handshake` first, which
returns the Consent Checklist markdown for the user to review.

## The 5 tools

| Tool | Purpose |
|---|---|
| `hap_handshake` | Establish session, return Consent Checklist + signed consent_token. |
| `hap_propose_arrival` | Classify flow profile, generate Sense of Place staff brief + voice line. |
| `hap_in_stay_action` | Handle in-stay signals. Complaints/maintenance trigger HAP-RULE 4.1/4.2 escalation (agent silenced, humans paged). |
| `hap_post_stay_memory` | Return memory snapshot for the Guest Agent. Confirms data destruction (HAP-RIGHTS). |
| `hap_generate_dispute_brief` | WARDEN-signed dispute brief from the audit chain. |

## Files

```
server/
  main.py                        # MCP entrypoint (FastMCP)
  demo_runner.py                 # Plan B — CLI fallback
  concierge.py                   # Anthropic SDK wrapper + system prompt
  audit.py                       # Hash-chained JSONL audit
  tools/
    handshake.py                 # hap_handshake
    arrival.py                   # hap_propose_arrival + flow classification
    in_stay.py                   # hap_in_stay_action + escalation rules
    post_stay.py                 # hap_post_stay_memory
    dispute.py                   # hap_generate_dispute_brief
  data/
    guests/{luis,guillermo,marcus_chen,family_johnson}.json
    properties/rosewood-sand-hill.json
    flows/*.md                   # 10 flow profile rules (HAP-RAG light)
  audit.jsonl                    # generated at runtime, append-only
  .env.example                   # ANTHROPIC_API_KEY, DEMO_MODE, signing secret
```

## Environment

```
ANTHROPIC_API_KEY=sk-ant-...        # required unless DEMO_MODE=true
ELEVENLABS_API_KEY=...              # optional, dashboard plays the line
ELEVENLABS_VOICE_ID=...             # optional
DEMO_MODE=true                      # short-circuits Claude calls, returns canned brief
HAP_SIGNING_SECRET=...              # HMAC for consent_token + dispute brief
```

## Architecture decisions

- **DEMO_MODE=true is the safe default for the pitch.** The canned brief matches the
  storyboard verbatim (matcha, firm mattress, Wed 2-4pm patio, no shellfish, olive oil
  from Stanford Sierra). The dispute brief also returns the scripted AC incident
  with 11-minute resolution.
- **Audit log is hash-chained.** Each entry includes `prev_hash` and its own `hash`.
  Tampering is detectable via `audit.verify_chain()`.
- **Guest data is pseudonymized in the audit.** `guest_guid` is a sha256-derived
  anon hash, never the raw guest_id. This is the "zero retention" story.
- **Mock data is loaded defensively.** If `data/guests/<id>.json` is missing the
  server uses an in-code fallback so the demo never crashes.
- **Pydantic** enforces tool input/output shapes.

## Verifying the audit chain

```bash
python3 -c "from server.audit import verify_chain; print('chain ok:', verify_chain())"
```

## Running tests / smoke

```bash
python demo_runner.py
# expect: 5 sections, exit code 0, audit.jsonl populated
```
