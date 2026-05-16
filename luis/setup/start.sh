#!/usr/bin/env bash
# start.sh — arranca los bots + dashboard del lado Luis.
# Para heart/server.py y platform/server.py, ver SETUP.md.

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SERVER="$ROOT/server"
DASH="$ROOT/dashboard"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }

bold "▶ Starting Luis stack"

# Avoid double-start
if pgrep -f telegram_bot.py >/dev/null; then
  echo "  (telegram_bot.py already running — skipping)"
else
  cd "$SERVER"
  # shellcheck disable=SC1091
  source venv/bin/activate
  nohup python -u telegram_bot.py > /tmp/hap-bot.log 2>&1 &
  disown
  ok "HEART bot         (log: /tmp/hap-bot.log)"
fi

if pgrep -f telegram_guest_bot.py >/dev/null; then
  echo "  (telegram_guest_bot.py already running — skipping)"
else
  cd "$SERVER"
  # shellcheck disable=SC1091
  source venv/bin/activate
  nohup python -u telegram_guest_bot.py > /tmp/hap-guest-bot.log 2>&1 &
  disown
  ok "Guest bot         (log: /tmp/hap-guest-bot.log)"
fi

if pgrep -f "next dev" >/dev/null; then
  echo "  (dashboard already running — skipping)"
else
  cd "$DASH"
  nohup pnpm dev > /tmp/hap-dashboard.log 2>&1 &
  disown
  ok "Dashboard         (log: /tmp/hap-dashboard.log)"
fi

sleep 3
echo
echo "Open:"
echo "    http://localhost:3000/hap-console     # luis dashboard"
echo "    http://localhost:3000/welcome-email   # email mock"
echo "    http://localhost:3000/install         # plugin install page"
echo
echo "For the unified platform shell (heart + platform must also be running):"
echo "    http://localhost:5570"
