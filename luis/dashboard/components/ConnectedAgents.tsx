"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";

type HapSession = {
  session_id: string;
  guest_id: string;
  guest_display: string;
  scope: string[];
  client_kind: string;
  client_label: string;
  opened_at_iso: string;
  ttl_hours: number;
  expires_at_iso: string;
  revoked_at_iso: string | null;
  checkout_initiated_at_iso: string | null;
  active: boolean;
  stay_id: string | null;
};

type Resp = { sessions: HapSession[]; active_count: number };

const CLIENT_ICON: Record<string, string> = {
  claude_desktop: "🖥",
  claude_code: "⌨️",
  telegram_bot: "✈️",
  web_claude: "🌐",
  custom: "🔌",
};

const CLIENT_DISPLAY: Record<string, string> = {
  claude_desktop: "Claude Desktop",
  claude_code: "Claude Code",
  telegram_bot: "Claude · Telegram-fronted",
  web_claude: "Claude · Web",
  custom: "Custom client",
};

function timeLeft(expires_iso: string): string {
  const ms = new Date(expires_iso).getTime() - Date.now();
  if (ms < 0) return "expired";
  const totalMin = Math.floor(ms / 60000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h === 0) return `${m}m left`;
  if (h < 24) return `${h}h ${m.toString().padStart(2, "0")}m left`;
  const d = Math.floor(h / 24);
  return `${d}d ${(h % 24).toString().padStart(2, "0")}h left`;
}

export function ConnectedAgents() {
  const [resp, setResp] = useState<Resp | null>(null);
  const [, setTick] = useState(0);

  const poll = useCallback(async () => {
    try {
      const r = await fetch("/api/sessions", { cache: "no-store" });
      if (!r.ok) return;
      setResp((await r.json()) as Resp);
    } catch {
      /* swallow */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 1500);
    const tickId = setInterval(() => setTick((x) => x + 1), 1000);
    return () => {
      clearInterval(id);
      clearInterval(tickId);
    };
  }, [poll]);

  const sessions = resp?.sessions ?? [];
  const active = sessions.filter((s) => s.active);
  const recent = sessions.filter((s) => !s.active).slice(0, 4);

  const headerCounter = useMemo(() => {
    if (active.length === 0) return "No HAP sessions";
    if (active.length === 1) return "1 HAP session active";
    return `${active.length} HAP sessions active`;
  }, [active.length]);

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)]">
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-3 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5 flex items-center gap-2">
            HAP plugin · connected agents
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                active.length > 0 ? "bg-forest animate-pulse-dot" : "bg-bronze/40"
              }`}
            />
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            Apps connected to Rosewood
          </h3>
          <p className="text-ink/60 text-sm mt-1 max-w-2xl">
            Each row is a Claude (Desktop, Code, web, or Telegram-fronted) that
            currently has the HAP plugin loaded and a scope-bounded session
            open. Sessions disconnect automatically when TTL expires or on
            checkout.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
        >
          {headerCounter}
        </Badge>
      </div>

      {active.length === 0 && recent.length === 0 ? (
        <div className="px-7 py-10 text-center">
          <p className="font-serif italic text-ink/55 text-lg leading-relaxed">
            No agent has opened a HAP session yet. Once a Claude (or the
            Telegram-fronted Guest Agent) authorizes a handshake, it appears
            here with a live TTL countdown.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-bronze/10">
          {[...active, ...recent].map((s) => (
            <div key={s.session_id} className="px-7 py-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 min-w-0">
                  <span className="text-2xl shrink-0 mt-0.5">
                    {CLIENT_ICON[s.client_kind] || "🔌"}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-3 flex-wrap">
                      <span className="font-serif text-xl text-ink leading-none">
                        {s.guest_display}
                      </span>
                      <span className="text-[0.7rem] uppercase tracking-[0.2em] text-bronze">
                        {CLIENT_DISPLAY[s.client_kind] || s.client_kind}
                      </span>
                    </div>
                    <div className="text-[0.7rem] text-ink/45 font-mono mt-1 truncate max-w-md">
                      session {s.session_id}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {s.scope.map((scp) => (
                        <span
                          key={scp}
                          className="inline-flex items-center px-2 py-0.5 rounded-full bg-cream-soft border border-bronze/20 text-[0.7rem] font-mono text-ink/70"
                        >
                          {scp}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  {s.active ? (
                    <>
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-forest/10 border border-forest/40 text-forest text-[0.7rem] uppercase tracking-[0.18em]">
                        <span className="w-1 h-1 rounded-full bg-forest animate-pulse-dot" />
                        Connected
                      </div>
                      <div className="text-[0.72rem] text-ink/55 mt-2 tabular-nums">
                        {timeLeft(s.expires_at_iso)}
                      </div>
                      <div className="text-[0.62rem] text-ink/35 mt-0.5">
                        TTL {s.ttl_hours}h
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-bronze/10 border border-bronze/30 text-bronze text-[0.7rem] uppercase tracking-[0.18em]">
                        <span className="w-1 h-1 rounded-full bg-bronze" />
                        Disconnected
                      </div>
                      {s.revoked_at_iso && (
                        <div className="text-[0.7rem] text-ink/50 mt-2">
                          revoked{" "}
                          {new Date(s.revoked_at_iso).toLocaleTimeString([], {
                            hour12: false,
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="px-7 py-3 border-t border-bronze/15 bg-cream-soft/40 text-[0.7rem] tracking-wide text-ink/55 text-center">
        Like any MCP plugin — install once, authorize per stay, auto-disconnect on checkout.
      </div>
    </div>
  );
}
