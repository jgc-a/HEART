# SETUP — full system on a single Mac

This is the end-to-end runbook to make HAP run on **one** Mac from scratch.
Designed for the hackathon: clone the repo, run two commands, demo works.

## What runs on the Mac

| Component | Port | Owns | Purpose |
|---|---|---|---|
| `luis/dashboard` (Next.js) | 3000 | Luis | "The View" — guest-facing & protocol UI |
| `luis/server` HAP MCP server | (stdio) | Luis | 5 HAP tools exposed to Claude Desktop / Code |
| `luis/server/telegram_bot.py` | (long-poll) | Luis | HEART/Concierge bot · 3-phase flow handler |
| `luis/server/telegram_guest_bot.py` | (long-poll) | Luis | Guest bot · voice A2A in the demo group |
| `heart/server.py` (Flask) | 5560 | Guillermo | HEART operational runtime · SQLite, agents, ROI |
| `platform/server.py` (Flask) | 5570 | Guillermo | Unified shell that iframes :3000 + :5560 |

## 0 · Prerequisites

```bash
# macOS — Homebrew installed
brew install python@3.13 pnpm gh
```

Plus accounts and keys:
- Anthropic API key (`console.anthropic.com`)
- ElevenLabs API key (`elevenlabs.io`)
- Two Telegram bots from `@BotFather`:
  - HEART/Concierge bot
  - Guest Agent bot
- One Telegram group with both bots added (admin), and its `chat_id`
  (negative integer — use `/chatid` once the bots are running)
- Claude Desktop installed (recommended) and/or Claude Code

## 1 · Clone the repo

```bash
gh repo clone jgc-a/HEART ~/HEART
cd ~/HEART
```

## 2 · Configure Luis env

```bash
cd luis/server
cp .env.example .env
# Edit .env and fill ALL the values:
#   ANTHROPIC_API_KEY
#   HAP_SIGNING_SECRET          (any random string)
#   TELEGRAM_BOT_TOKEN          (HEART bot)
#   TELEGRAM_GUEST_BOT_TOKEN    (Guest bot)
#   HAP_VOICE_GROUP_CHAT_ID     (negative integer — group chat_id)
#   ELEVENLABS_API_KEY
#   ELEVENLABS_VOICE_ID_GUEST=ErXwobaYiN019PkySvjV       (Antoni)
#   ELEVENLABS_VOICE_ID_CONCIERGE=XB0fDUnXU5powFXDhCwa   (Charlotte)
#   DEMO_MODE=false
```

## 3 · Bootstrap (one-time)

```bash
cd luis
bash setup/bootstrap.sh
```

Creates `server/venv`, installs Python deps, installs the HAP plugin into
Claude Desktop + Claude Code, installs dashboard `node_modules`, creates
`dashboard/.env.local` from the server env so the dashboard can also
broadcast to Telegram.

## 4 · Heart + Platform deps (one-time)

These run as plain Flask servers — no venv needed if you already have
flask globally, but it's cleaner to use one:

```bash
cd ~/HEART/heart
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors requests
deactivate

cd ../platform
python3 -m venv venv
source venv/bin/activate
pip install flask requests
deactivate
```

Or share one venv across both — same dependencies, your call.

## 5 · Start everything

```bash
# Terminal A — Luis stack (bots + dashboard, all in background)
cd ~/HEART/luis
bash setup/start.sh

# Terminal B — HEART runtime
cd ~/HEART/heart
source venv/bin/activate
python server.py        # prints banner, runs on :5560

# Terminal C — Platform shell
cd ~/HEART/platform
source venv/bin/activate
python server.py        # prints banner, runs on :5570
```

The HEART SQLite database (`heart/data/heart.db`) is created automatically
on first run via `init_db()` + `seed_human_queue()` + `seed_hap_events()`.
There's no separate migration step.

## 6 · Verify

```bash
cd ~/HEART/luis
bash setup/check.sh
```

Expect:
```
▶ Service health
  ● HEART bot (Concierge)
  ● Guest bot
  ● Dashboard (port 3000)
  ● HEART runtime (port 5560)
  ● Platform shell (port 5570)

▶ Endpoints
  ✓ 200  http://localhost:3000/
  ✓ 200  http://localhost:3000/hap-console
  ✓ 200  http://localhost:3000/install
  ✓ 200  http://localhost:5560/ops
  ✓ 200  http://localhost:5570/

▶ Telegram bots
  ✓ @Rosewood_sandhill_hap_bot   (TELEGRAM_BOT_TOKEN)
  ✓ @Rosewood_sandhill_guest_bot  (TELEGRAM_GUEST_BOT_TOKEN)
```

## 7 · Open

| URL | What it is |
|---|---|
| **`http://localhost:5570`** | **Unified Platform shell — use this for the live demo** |
| `http://localhost:3000/hap-console` | Luis dashboard only |
| `http://localhost:3000/welcome-email` | Email mock with one-click install + Telegram QR |
| `http://localhost:3000/install` | Plugin install page |
| `http://localhost:5560/ops` | HEART ops dashboard |

## 8 · Run the demo

1. Open `http://localhost:5570` — Platform shell.
2. In Telegram, open `@Rosewood_sandhill_hap_bot`.
3. Send `/persona luis` (or `/persona marcus` / `guillermo` / `family_johnson`).
4. Tap **🔐 Authorize handshake (Step 1 of 3)**.
5. While Phase 2 runs, open the demo group on your phone — the two bots
   negotiate with ElevenLabs voices in real time.
6. Watch the dashboard fill up: ConnectedAgents, A2AConversation, etc.
7. Tap **✅ Confirm outcome (Step 3 of 3)** when prompted.
8. When done, send `/checkout` — fires the Departing Threads event sequence.

## 9 · Stop

```bash
cd ~/HEART/luis
bash setup/stop.sh

# Then Ctrl+C the heart and platform terminals.
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pnpm: command not found` | `npm install -g pnpm` |
| Phase 3 stuck on "Staff brief incoming…" | Already patched (commit 86946e4). Update repo: `git pull`. |
| `Can't parse entities` in Telegram | Restart the bot after pull — `_safe_send_message` falls back to plain text. |
| Voice messages don't arrive in group | `tail /tmp/hap-bot.log` — look for `[voice] kick_off skipped: …` |
| `ConnectedAgents` always empty | The bot wasn't restarted after install_mcp.py. Run `setup/stop.sh && setup/start.sh`. |
| HEART /ops iframe blank inside HAP Console | `heart/server.py` not running on :5560. |
| Bots polling errors `409 Conflict` | Two processes using the same bot token. Stop one. |
| ElevenLabs `401` in log | ELEVENLABS_API_KEY wrong or out of quota. Free tier has ~10k chars/month. |

## Reset

To clear runtime data and start over:

```bash
cd ~/HEART/luis/server
rm -f audit.jsonl data/telegram_users.json data/telegram_events.jsonl \
      data/active_sessions.json
rm -rf data/live_profiles/ data/guest_memories/
rm -f data/guests/telegram_*.json 2>/dev/null

cd ~/HEART/heart
rm -f data/heart.db         # will be re-seeded on next start
```

## File map

```
~/HEART/
├── README.md                              (Guillermo · thesis)
├── LICENSE
├── heart/                                  (Guillermo)
│   ├── server.py                           Flask :5560, 12+ APIs, 3 agents
│   ├── templates/{ops,view}.html           Operator dashboard
│   ├── data/{guests,rooms}.json            Seed data
│   └── data/heart.db                       SQLite (auto-generated)
├── platform/                               (Guillermo)
│   ├── server.py                           Flask :5570, unified shell
│   └── templates/platform.html             Sidebar with 8 modules
└── luis/                                   (Luis)
    ├── SETUP.md                            (this file)
    ├── CLAUDE.md                           Project rules
    ├── server/
    │   ├── main.py                         MCP server (5 HAP tools)
    │   ├── telegram_bot.py                 HEART bot · 3-phase flow
    │   ├── telegram_guest_bot.py           Guest bot · voice A2A
    │   ├── voice_conversation.py           ElevenLabs orchestrator
    │   ├── guest_agent.py                  Claude behind the bot
    │   ├── concierge.py                    Server-side HEART agent
    │   ├── audit.py                        Hash-chained audit log
    │   ├── sessions.py                     Active HAP sessions
    │   ├── install_mcp.py                  Claude Desktop + Code installer
    │   ├── tools/                          5 HAP tools (handshake, etc.)
    │   └── data/                           Guest profiles, flows, preloaded personas
    ├── dashboard/                          Next.js, port 3000
    │   ├── app/{,/hap-console,/install,/welcome-email,/reputation}
    │   ├── app/api/{audit,dispute,guest-memory,handshake,install,sessions,telegram}
    │   └── components/                     ConnectedAgents, A2AConversation, etc.
    ├── docs/                               10 markdown docs (pitch, spec, storyboard…)
    └── setup/                              {bootstrap,start,stop,check}.sh
```
