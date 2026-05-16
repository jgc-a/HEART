"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type TelegramUser = {
  chat_id: number;
  first_name?: string;
  username?: string;
  registered_at_iso?: string;
};

type TelegramEvent = {
  ts: string;
  kind: string;
  chat_id?: number;
  label: string;
};

type StateResp = {
  bot_configured: boolean;
  users_count: number;
  users: TelegramUser[];
  events: TelegramEvent[];
};

const KIND_COLOR: Record<string, string> = {
  register: "text-forest",
  handshake_sent: "text-bronze",
  broadcast: "text-bronze",
  approved: "text-forest",
  declined: "text-rose-700",
  brief_delivered: "text-forest",
  customize_clicked: "text-ink/60",
};

export function TelegramPanel() {
  const [state, setState] = useState<StateResp | null>(null);
  const [sending, setSending] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const res = await fetch("/api/telegram/state", { cache: "no-store" });
      if (!res.ok) return;
      setState((await res.json()) as StateResp);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, [poll]);

  const broadcast = async () => {
    setSending(true);
    setFlash(null);
    try {
      const res = await fetch("/api/telegram/broadcast", { method: "POST" });
      const json = (await res.json()) as { ok: boolean; sent?: number; reason?: string };
      if (json.ok) {
        setFlash(`Sent to ${json.sent} chats — check the phones.`);
      } else {
        setFlash(`Failed: ${json.reason || "unknown"}`);
      }
      poll();
    } finally {
      setSending(false);
      setTimeout(() => setFlash(null), 4500);
    }
  };

  const configured = state?.bot_configured ?? false;
  const users = state?.users ?? [];
  const events = state?.events ?? [];

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)]">
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-4 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5 flex items-center gap-2">
            Live channel · Telegram
            {configured ? (
              <span className="w-1.5 h-1.5 rounded-full bg-forest animate-pulse-dot" />
            ) : (
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
            )}
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            Real handshake, real device
          </h3>
          <p className="text-ink/60 text-sm mt-1">
            A real message hits a real phone. Approval flows back into the
            audit log within seconds.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant="outline"
            className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
          >
            {users.length} chat{users.length === 1 ? "" : "s"} registered
          </Badge>
          <Button
            size="sm"
            onClick={broadcast}
            disabled={!configured || users.length === 0 || sending}
            className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.18em] text-[0.7rem] font-medium px-5 disabled:opacity-40"
          >
            {sending ? "Sending…" : "Send handshake → phones"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-0">
        {/* registered chats */}
        <div className="border-r border-bronze/15 px-6 py-5">
          <div className="text-[0.6rem] uppercase tracking-[0.24em] text-bronze mb-3">
            Registered chats
          </div>
          {!configured ? (
            <div className="text-ink/50 text-sm italic">
              Bot not configured. Add{" "}
              <code className="font-mono text-bronze">TELEGRAM_BOT_TOKEN</code>{" "}
              to dashboard env.
            </div>
          ) : users.length === 0 ? (
            <div className="text-ink/50 text-sm italic">
              Awaiting first <code className="font-mono text-bronze">/start</code>{" "}
              from a Telegram chat.
            </div>
          ) : (
            <ul className="space-y-2.5">
              {users.map((u) => (
                <li
                  key={u.chat_id}
                  className="flex items-center gap-3 text-sm text-ink/85"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-forest" />
                  <span className="font-serif text-base leading-tight">
                    {u.first_name || u.username || `chat ${u.chat_id}`}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* live event log */}
        <div className="px-6 py-5 max-h-[280px] overflow-y-auto">
          <div className="text-[0.6rem] uppercase tracking-[0.24em] text-bronze mb-3">
            Live channel events
          </div>
          {events.length === 0 ? (
            <div className="text-ink/50 text-sm italic">
              No events yet. Press <span className="text-bronze">Send handshake</span> or wait
              for a chat to approve.
            </div>
          ) : (
            <ul className="space-y-2 font-mono text-[0.78rem]">
              {events.map((e, i) => (
                <li
                  key={i + e.ts}
                  className="flex gap-3 items-start animate-fade-in-up"
                >
                  <span className="text-ink/40 shrink-0 tabular-nums">
                    {new Date(e.ts).toLocaleTimeString([], {
                      hour12: false,
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                  <span
                    className={`${KIND_COLOR[e.kind] || "text-ink/75"} uppercase tracking-[0.12em] text-[0.7rem] shrink-0 w-32`}
                  >
                    {e.kind.replace(/_/g, ".")}
                  </span>
                  <span className="text-ink/80">{e.label}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {flash && (
        <div className="px-7 py-3 bg-forest/10 border-t border-forest/30 text-forest text-sm text-center animate-fade-in-up">
          {flash}
        </div>
      )}
    </div>
  );
}
