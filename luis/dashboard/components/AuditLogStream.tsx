"use client";

import { useEffect, useRef, useState } from "react";
import type { AuditEvent, AuditSeverity } from "@/lib/audit-events";

const severityColor: Record<AuditSeverity, string> = {
  info: "text-bronze",
  ok: "text-forest",
  warn: "text-amber-700",
  rule: "text-rose-700",
};

const severityDot: Record<AuditSeverity, string> = {
  info: "bg-bronze",
  ok: "bg-forest",
  warn: "bg-amber-600",
  rule: "bg-rose-600",
};

export function AuditLogStream({
  onStaffBriefReady,
}: {
  onStaffBriefReady?: () => void;
}) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const seenBriefRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const res = await fetch("/api/audit/stream", { cache: "no-store" });
        if (!res.ok) return;
        const data = (await res.json()) as { events: AuditEvent[] };
        if (cancelled || !data.events?.length) return;

        setEvents((prev) => {
          const seen = new Set(prev.map((e) => e.id));
          const fresh = data.events.filter((e) => !seen.has(e.id));
          if (!fresh.length) return prev;
          return [...prev, ...fresh].slice(-60);
        });

        if (
          !seenBriefRef.current &&
          data.events.some((e) => e.event === "STAFF_BRIEF.READY")
        ) {
          seenBriefRef.current = true;
          onStaffBriefReady?.();
        }
      } catch {
        /* swallow */
      }
    }

    poll();
    const id = setInterval(poll, 1500);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [onStaffBriefReady]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="bg-ink text-cream/90 rounded-lg border border-bronze/20 flex flex-col h-[640px] shadow-[0_8px_24px_-12px_rgba(0,0,0,0.35)] overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-cream/10">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-forest animate-pulse-dot" />
          <span className="text-[0.7rem] uppercase tracking-[0.28em] text-cream/70">
            Audit Stream · Live
          </span>
        </div>
        <span className="text-[0.65rem] uppercase tracking-[0.22em] text-cream/40">
          Retention 0d · Hash-chained
        </span>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-5 font-mono text-[0.78rem] leading-relaxed space-y-2.5"
      >
        {events.length === 0 ? (
          <div className="text-cream/40 italic font-sans">
            Awaiting protocol traffic. Trigger a handshake to begin.
          </div>
        ) : (
          events.map((e) => (
            <div
              key={e.id}
              className="animate-fade-in-up flex gap-3 items-start"
            >
              <span
                className={`shrink-0 w-1.5 h-1.5 rounded-full ${severityDot[e.severity]} mt-2`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-x-3 gap-y-0.5 items-baseline">
                  <span className="text-cream/40">[{e.ts}]</span>
                  <span className={`${severityColor[e.severity]} font-semibold`}>
                    {e.event}
                  </span>
                  <span className="text-cream/55">{e.scope}</span>
                </div>
                {e.detail && (
                  <div className="text-cream/55 mt-1 pl-0">{e.detail}</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
