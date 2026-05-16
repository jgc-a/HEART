#!/usr/bin/env bash
# check.sh — health check del stack completo (luis + heart + platform si están).

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SERVER="$ROOT/server"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m" "$1"; }
red() { printf "\033[31m%s\033[0m" "$1"; }
yellow() { printf "\033[33m%s\033[0m" "$1"; }

bold "▶ Service health"
for entry in \
    "telegram_bot.py:HEART bot (Concierge)" \
    "telegram_guest_bot.py:Guest bot" \
    "next dev:Dashboard (port 3000)" \
    "heart/server.py:HEART runtime (port 5560)" \
    "platform/server.py:Platform shell (port 5570)"; do
  pat="${entry%%:*}"
  name="${entry#*:}"
  if pgrep -f "$pat" >/dev/null 2>&1; then
    printf "  %s %s\n" "$(green '●')" "$name"
  else
    printf "  %s %s\n" "$(red '○')" "$name"
  fi
done

echo
bold "▶ Endpoints"
check_url() {
  local url="$1" label="$2"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$url" 2>/dev/null)
  if [ "$code" = "200" ]; then
    printf "  %s %s  %s\n" "$(green "✓ $code")" "$url" "$label"
  elif [ -z "$code" ] || [ "$code" = "000" ]; then
    printf "  %s %s  %s\n" "$(red 'down ')" "$url" "$label"
  else
    printf "  %s %s  %s\n" "$(yellow "$code  ")" "$url" "$label"
  fi
}
check_url "http://localhost:3000/" "Luis dashboard root"
check_url "http://localhost:3000/hap-console" "HAP Console"
check_url "http://localhost:3000/install" "Plugin install page"
check_url "http://localhost:5560/ops" "HEART ops"
check_url "http://localhost:5570/" "Platform shell"

echo
bold "▶ Telegram bots"
if [ -f "$SERVER/.env" ]; then
  for var in TELEGRAM_BOT_TOKEN TELEGRAM_GUEST_BOT_TOKEN; do
    tok=$(grep "^$var=" "$SERVER/.env" | cut -d= -f2)
    if [ -n "$tok" ]; then
      r=$(curl -s --max-time 3 "https://api.telegram.org/bot${tok}/getMe")
      uname=$(printf '%s' "$r" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("result",{}).get("username","?"))' 2>/dev/null)
      if [ -n "$uname" ] && [ "$uname" != "?" ]; then
        printf "  %s @%s  (%s)\n" "$(green '✓')" "$uname" "$var"
      else
        printf "  %s %s rejected token\n" "$(red '✗')" "$var"
      fi
    fi
  done
fi

echo
bold "▶ Logs"
for log in /tmp/hap-bot.log /tmp/hap-guest-bot.log /tmp/hap-dashboard.log; do
  if [ -f "$log" ]; then
    printf "  tail -f %s\n" "$log"
  fi
done
