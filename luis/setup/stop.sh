#!/usr/bin/env bash
# stop.sh — apaga todo lo del lado Luis.

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }

bold "▶ Stopping Luis stack"

for pat in telegram_bot.py telegram_guest_bot.py "next dev"; do
  if pgrep -f "$pat" >/dev/null; then
    pkill -f "$pat"
    ok "killed: $pat"
  fi
done

sleep 2
remaining=$(pgrep -af "telegram_bot.py|telegram_guest_bot.py|next dev" 2>/dev/null | wc -l | tr -d ' ')
if [ "$remaining" = "0" ]; then
  ok "all stopped"
else
  printf "  \033[33m!\033[0m %s processes still running — try again or use 'kill -9 <pid>'\n" "$remaining"
fi
