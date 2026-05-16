# Claude Desktop Setup — HAP MCP Server

> How to wire the HAP MCP server into Claude Desktop so the demo handshake works.

## Prerequisites

- Claude Desktop installed (latest)
- Python 3.13+
- `ANTHROPIC_API_KEY` available
- This repo cloned to `~/Documents/GitHub/rosewood-hackathon-aisociety/`

## Step 1 — Install Python dependencies

```bash
cd ~/Documents/GitHub/rosewood-hackathon-aisociety/server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2 — Set environment variables

Copy `server/.env.example` to `server/.env` and fill in:

```bash
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=el-...     # optional
ELEVENLABS_VOICE_ID=...        # optional
DEMO_MODE=true                 # use canned responses if API fails
```

## Step 3 — Test the server standalone

```bash
cd server
python demo_runner.py
```

You should see a full end-to-end run: handshake → arrival → in-stay → post-stay → dispute brief.

If this works, the MCP integration will work.

## Step 4 — Add to Claude Desktop config

Open (or create) `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hap-rosewood-sand-hill": {
      "command": "/Users/luisvargasfdz/Documents/GitHub/rosewood-hackathon-aisociety/server/venv/bin/python",
      "args": [
        "/Users/luisvargasfdz/Documents/GitHub/rosewood-hackathon-aisociety/server/main.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DEMO_MODE": "true"
      }
    }
  }
}
```

**Note:** use the absolute path to the venv's python. This avoids dependency conflicts.

## Step 5 — Restart Claude Desktop

Quit Claude Desktop completely (cmd-Q, not just close window) and re-open.

You should see "hap-rosewood-sand-hill" listed in the MCP servers (settings → developer).

## Step 6 — Verify with a test prompt

In Claude Desktop, say:

```
What HAP tools are available?
```

Claude should list the 5 HAP tools.

Then:

```
Voy a Rosewood Sand Hill el 18 de mayo, tengo reuniones en Sand Hill Road.
```

Claude should:
1. Call `hap_handshake` with proposed scope
2. Render the Consent Checklist
3. (You approve)
4. Call `hap_propose_arrival`
5. Display the staff brief

If the Consent Checklist renders as a structured markdown list with checkboxes, the demo is ready.

## Troubleshooting

### "Tool failed" in Claude Desktop
- Check that the Python path is correct.
- Check that `requirements.txt` is fully installed.
- Run `demo_runner.py` standalone first.

### "API key not found"
- Confirm `ANTHROPIC_API_KEY` is in the `env` block of the config.
- Or set `DEMO_MODE=true` to use canned responses.

### MCP server doesn't show up after restart
- Check `~/Library/Logs/Claude/mcp.log` for errors.
- Make sure the JSON config is valid (no trailing commas).

### Server starts but tools time out
- Concierge agent may be calling Claude API which can be slow.
- Set `DEMO_MODE=true` to bypass for the live pitch.

## Pre-Demo Smoke Test (DO THIS 30 MIN BEFORE PITCH)

```bash
# 1. Server starts cleanly
cd server && python demo_runner.py

# 2. Claude Desktop sees the server
# (open Claude Desktop, check Settings → Developer)

# 3. Dashboard runs
cd ../dashboard && pnpm dev
# Open http://localhost:3000

# 4. Trigger demo handshake from dashboard
# Click "Trigger demo" button on /hap-console

# 5. Type the demo prompt in Claude Desktop
# "Voy a Rosewood Sand Hill el 18 de mayo, tengo reuniones en Sand Hill Road."

# 6. Confirm:
#    - Consent Checklist renders
#    - Approving sends scope
#    - Staff brief generates within 15s
#    - Dashboard audit log streams events
#    - ElevenLabs voice plays (if enabled)
```

If all 6 pass → you're demo-ready.
If any fail → fix it, or fall back to Plan B (CLI demo + dashboard).
