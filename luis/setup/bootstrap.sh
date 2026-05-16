#!/usr/bin/env bash
# bootstrap.sh — one-time setup for the Luis stack on a fresh Mac.
# Idempotent: run as many times as you want.

set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SERVER="$ROOT/server"
DASH="$ROOT/dashboard"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
err()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }

bold "▶ Bootstrap · Luis stack (HAP MCP + bots + dashboard)"
echo

# 1 · Python venv
bold "1 · Python venv"
if [ ! -d "$SERVER/venv" ]; then
  if command -v python3.13 >/dev/null 2>&1; then
    python3.13 -m venv "$SERVER/venv"
  else
    python3 -m venv "$SERVER/venv"
  fi
  ok "venv created at $SERVER/venv"
else
  ok "venv exists"
fi
# shellcheck disable=SC1091
source "$SERVER/venv/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$SERVER/requirements.txt"
ok "Python deps installed: $(pip list --format=freeze | grep -E '^(mcp|anthropic|python-telegram-bot)' | tr '\n' ' ')"

# 2 · .env
echo
bold "2 · server/.env"
if [ ! -f "$SERVER/.env" ]; then
  if [ -f "$SERVER/.env.example" ]; then
    cp "$SERVER/.env.example" "$SERVER/.env"
    warn ".env created from .env.example — FILL IN REAL VALUES BEFORE STARTING:"
    echo "         vi $SERVER/.env"
    echo
    echo "    Required:"
    echo "      ANTHROPIC_API_KEY        from console.anthropic.com"
    echo "      HAP_SIGNING_SECRET       any long random string"
    echo "      TELEGRAM_BOT_TOKEN       HEART bot from @BotFather"
    echo "      TELEGRAM_GUEST_BOT_TOKEN Guest bot from @BotFather"
    echo "      HAP_VOICE_GROUP_CHAT_ID  chat_id of demo group (negative integer)"
    echo "      ELEVENLABS_API_KEY       from elevenlabs.io"
    echo
    exit 1
  else
    err "No .env and no .env.example — can't bootstrap server config."
    exit 1
  fi
else
  ok "$SERVER/.env present"
fi

# 3 · Install MCP into Claude Desktop + Claude Code
echo
bold "3 · Claude plugin install (Desktop + Code)"
python "$SERVER/install_mcp.py" | sed 's/^/    /'

# 4 · Dashboard deps
echo
bold "4 · Dashboard (Next.js, pnpm)"
if ! command -v pnpm >/dev/null 2>&1; then
  warn "pnpm not found. Install with: npm install -g pnpm"
  exit 1
fi
if [ ! -d "$DASH/node_modules" ]; then
  cd "$DASH"
  pnpm install --silent
fi
ok "node_modules installed"

# 5 · Dashboard env
if [ ! -f "$DASH/.env.local" ]; then
  cat > "$DASH/.env.local" <<EOF
# Mirrors server/.env value so the dashboard can call Telegram for broadcasts.
TELEGRAM_BOT_TOKEN=$(grep ^TELEGRAM_BOT_TOKEN "$SERVER/.env" | cut -d= -f2)
EOF
  ok ".env.local created in dashboard (TELEGRAM_BOT_TOKEN mirror)"
else
  ok "dashboard/.env.local present"
fi

echo
bold "✅ Bootstrap complete."
echo "Next:"
echo "    bash $HERE/start.sh         # arranca bots + dashboard"
echo "    bash $HERE/check.sh         # verifica que todo respira"
echo "    bash $HERE/stop.sh          # apaga todo"
