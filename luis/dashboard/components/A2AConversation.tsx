"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

type TelegramEvent = {
  ts: string;
  kind: string;
  chat_id?: number;
  label: string;
  from?: "guest_agent" | "concierge";
  to?: "guest_agent" | "concierge";
  tool?: string;
};

type StateResp = {
  bot_configured: boolean;
  events: TelegramEvent[];
};

type PhaseState = "pending" | "active" | "complete";

function computePhases(events: TelegramEvent[]): [PhaseState, PhaseState, PhaseState] {
  // events arrive newest-first; flip to chronological
  const chrono = [...events].reverse();
  let p1: PhaseState = "pending";
  let p2: PhaseState = "pending";
  let p3: PhaseState = "pending";
  for (const e of chrono) {
    const l = e.label.toLowerCase();
    if (e.kind === "phase_start" && l.includes("phase 1")) p1 = "active";
    if (e.kind === "phase_complete" && l.includes("phase 1")) p1 = "complete";
    if (e.kind === "phase_start" && l.includes("phase 2")) {
      p2 = "active";
      p1 = "complete";
    }
    if (e.kind === "phase_complete" && l.includes("phase 2")) p2 = "complete";
    if (e.kind === "phase_complete" && l.includes("phase 3")) {
      p3 = "complete";
      p2 = "complete";
      p1 = "complete";
    }
    if (e.kind === "approved") {
      p3 = "complete";
      p2 = "complete";
      p1 = "complete";
    }
  }
  // Phase 3 becomes "active" when phase 2 is complete but phase 3 not yet
  if (p2 === "complete" && p3 === "pending") p3 = "active";
  return [p1, p2, p3];
}

function PhasePill({
  index,
  title,
  state,
}: {
  index: number;
  title: string;
  state: PhaseState;
}) {
  const base =
    "flex items-center gap-2.5 px-4 py-2.5 rounded-md border text-sm transition-all";
  const map: Record<PhaseState, string> = {
    pending: "border-bronze/20 bg-cream-soft/40 text-ink/40",
    active:
      "border-forest/40 bg-forest/8 text-forest shadow-[0_6px_18px_-10px_rgba(45,74,62,0.45)] animate-pulse-dot",
    complete: "border-forest/40 bg-forest text-cream",
  };
  return (
    <div className={`${base} ${map[state]}`}>
      <span className="font-mono text-[0.65rem] tracking-[0.2em] opacity-80">
        PHASE {index}
      </span>
      <span className="font-serif text-base leading-none">{title}</span>
      <span className="ml-auto text-[0.65rem] uppercase tracking-[0.18em]">
        {state === "complete" ? "✓ done" : state === "active" ? "in flight" : "pending"}
      </span>
    </div>
  );
}

export function A2AConversation() {
  const [events, setEvents] = useState<TelegramEvent[]>([]);
  const [allEvents, setAllEvents] = useState<TelegramEvent[]>([]);

  const poll = useCallback(async () => {
    try {
      const r = await fetch("/api/telegram/state", { cache: "no-store" });
      if (!r.ok) return;
      const data = (await r.json()) as StateResp;
      const all = data.events || [];
      setAllEvents(all);
      const a2a = all
        .filter((e) => e.kind === "a2a_request" || e.kind === "a2a_response")
        .reverse(); // newest events come reversed; flip back to chronological
      setEvents(a2a);
    } catch {
      /* swallow */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, [poll]);

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)]">
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-3 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5 flex items-center gap-2">
            Live · Agent-to-Agent
            <span className="w-1.5 h-1.5 rounded-full bg-forest animate-pulse-dot" />
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            Two Claudes, one protocol
          </h3>
          <p className="text-ink/60 text-sm mt-1">
            The Guest Agent (Claude behind Telegram) calls real HAP tools on
            HEART (Claude on the property side). The conversation below is the
            HAP traffic itself, not a re-enactment.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
        >
          {events.length} message{events.length === 1 ? "" : "s"}
        </Badge>
      </div>

      {/* Phase progress bar */}
      <div className="px-7 py-4 border-b border-bronze/15 grid grid-cols-1 md:grid-cols-3 gap-3">
        {(() => {
          const [p1, p2, p3] = computePhases(allEvents);
          return (
            <>
              <PhasePill index={1} title="Handshake (scope auth)" state={p1} />
              <PhasePill index={2} title="A2A negotiation" state={p2} />
              <PhasePill index={3} title="User confirmation" state={p3} />
            </>
          );
        })()}
      </div>

      <div className="grid grid-cols-[1fr_2px_1fr] min-h-[280px]">
        {/* GUEST AGENT column */}
        <div className="px-6 py-5 flex flex-col gap-3">
          <div className="text-[0.6rem] uppercase tracking-[0.24em] text-bronze">
            Guest Agent · Claude (Telegram-fronted)
          </div>
          {events.filter((e) => e.from === "guest_agent").length === 0 ? (
            <div className="text-ink/40 italic text-xs mt-4">
              Standing by — the guest hasn't approved yet.
            </div>
          ) : (
            <ul className="space-y-3">
              {events
                .filter((e) => e.from === "guest_agent")
                .map((e, i) => (
                  <li
                    key={i + e.ts}
                    className="bg-cream-soft border border-bronze/20 rounded-md px-3.5 py-2.5 animate-fade-in-up self-start max-w-[95%]"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[0.6rem] uppercase tracking-[0.2em] text-bronze font-medium">
                        → calls
                      </span>
                      {e.tool && (
                        <span className="font-mono text-[0.65rem] text-forest">
                          {e.tool}
                        </span>
                      )}
                    </div>
                    <div className="text-ink/85 text-[0.82rem] leading-snug">
                      {e.label}
                    </div>
                    <div className="text-[0.62rem] text-ink/40 mt-1.5 tabular-nums">
                      {new Date(e.ts).toLocaleTimeString()}
                    </div>
                  </li>
                ))}
            </ul>
          )}
        </div>

        {/* divider */}
        <div className="bg-bronze/20" />

        {/* CONCIERGE column */}
        <div className="px-6 py-5 flex flex-col gap-3">
          <div className="text-[0.6rem] uppercase tracking-[0.24em] text-bronze text-right">
            HEART · Concierge Claude (property side)
          </div>
          {events.filter((e) => e.from === "concierge").length === 0 ? (
            <div className="text-ink/40 italic text-xs mt-4 text-right">
              Awaiting first request.
            </div>
          ) : (
            <ul className="space-y-3">
              {events
                .filter((e) => e.from === "concierge")
                .map((e, i) => (
                  <li
                    key={i + e.ts}
                    className="bg-forest/8 border border-forest/30 rounded-md px-3.5 py-2.5 animate-fade-in-up self-end max-w-[95%]"
                  >
                    <div className="flex items-center justify-between mb-1">
                      {e.tool && (
                        <span className="font-mono text-[0.65rem] text-forest">
                          {e.tool}
                        </span>
                      )}
                      <span className="text-[0.6rem] uppercase tracking-[0.2em] text-bronze font-medium">
                        returns ←
                      </span>
                    </div>
                    <div className="text-ink/85 text-[0.82rem] leading-snug text-right">
                      {e.label}
                    </div>
                    <div className="text-[0.62rem] text-ink/40 mt-1.5 tabular-nums text-right">
                      {new Date(e.ts).toLocaleTimeString()}
                    </div>
                  </li>
                ))}
            </ul>
          )}
        </div>
      </div>

      <div className="px-7 py-3 border-t border-bronze/15 bg-cream-soft/40 text-[0.7rem] tracking-wide text-ink/55 text-center">
        Each message is logged in the hash-chained audit. Tampering breaks the chain.
      </div>
    </div>
  );
}
