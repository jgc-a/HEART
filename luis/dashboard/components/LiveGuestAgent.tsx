"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

type LiveProfile = {
  chat_id: number;
  visit_purpose: string | null;
  lodging: string[];
  dietary: string[];
  cultural: string[];
  wellness: string[];
  notes: string | null;
  ready: boolean;
  updated_at: string | null;
  history?: { role: string; content: string }[];
  source?: string;
  agent_memory_origin?: string;
  persona_id?: string;
  display_name?: string;
};

type Resp = { profiles: LiveProfile[] };

function emptyArray(...arrs: string[][]) {
  return arrs.every((a) => a.length === 0);
}

export function LiveGuestAgent() {
  const [profiles, setProfiles] = useState<LiveProfile[]>([]);

  const poll = useCallback(async () => {
    try {
      const r = await fetch("/api/telegram/profiles", { cache: "no-store" });
      if (!r.ok) return;
      const data = (await r.json()) as Resp;
      setProfiles(data.profiles || []);
    } catch {
      /* swallow */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, [poll]);

  if (profiles.length === 0) {
    return (
      <div className="bg-card border border-bronze/20 rounded-lg p-7">
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-2">
          Live · Guest Agent (Claude behind the bot)
        </div>
        <p className="font-serif italic text-ink/55 text-lg leading-relaxed">
          Waiting for a guest to speak. Once they message the bot, every preference
          they share will appear here in real time — extracted live by Claude.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)]">
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-3 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5 flex items-center gap-2">
            Live · Guest Agent (Claude behind the bot)
            <span className="w-1.5 h-1.5 rounded-full bg-forest animate-pulse-dot" />
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            What the agent is learning
          </h3>
          <p className="text-ink/60 text-sm mt-1">
            Each new preference is extracted live from a real conversation in
            Telegram. Nothing is precooked — refresh, retry, and it will read
            differently every time.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
        >
          {profiles.length} active guest{profiles.length === 1 ? "" : "s"}
        </Badge>
      </div>

      <div className="divide-y divide-bronze/10">
        {profiles.map((p) => (
          <div key={p.chat_id} className="px-7 py-6">
            <div className="flex items-baseline justify-between mb-2">
              <div className="flex items-baseline gap-3">
                {p.display_name ? (
                  <span className="font-serif text-2xl text-ink leading-none">
                    {p.display_name}
                  </span>
                ) : (
                  <span className="font-mono text-[0.7rem] text-bronze">
                    chat {p.chat_id}
                  </span>
                )}
                {p.visit_purpose && (
                  <span className="text-ink/60 italic text-sm">
                    {p.visit_purpose}
                  </span>
                )}
              </div>
              {p.ready ? (
                <Badge className="bg-forest text-cream uppercase tracking-[0.18em] text-[0.65rem]">
                  Ready · Awaiting handshake tap
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
                >
                  Learning…
                </Badge>
              )}
            </div>

            {/* source pill: preloaded vs conversation */}
            <div className="mb-4 flex items-center gap-2 text-[0.7rem]">
              {p.source === "preloaded" ? (
                <>
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-forest/10 border border-forest/30 text-forest uppercase tracking-[0.16em]">
                    <span className="w-1 h-1 rounded-full bg-forest" /> preloaded
                  </span>
                  {p.agent_memory_origin && (
                    <span className="text-ink/55 italic">
                      {p.agent_memory_origin}
                    </span>
                  )}
                </>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-bronze/10 border border-bronze/30 text-bronze uppercase tracking-[0.16em]">
                  <span className="w-1 h-1 rounded-full bg-bronze" /> learned in conversation
                </span>
              )}
            </div>

            {emptyArray(p.lodging, p.dietary, p.cultural, p.wellness) ? (
              <p className="text-ink/55 italic text-sm">
                No preferences captured yet — guest is mid-conversation.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                {p.lodging.length > 0 && (
                  <Group label="Lodging" items={p.lodging} />
                )}
                {p.dietary.length > 0 && (
                  <Group label="Dietary" items={p.dietary} />
                )}
                {p.cultural.length > 0 && (
                  <Group label="Cultural / beverages" items={p.cultural} />
                )}
                {p.wellness.length > 0 && (
                  <Group label="Wellness (opt-in)" items={p.wellness} />
                )}
              </div>
            )}

            {p.notes && (
              <p className="font-serif italic text-ink/70 text-sm mt-4 pl-4 border-l border-bronze/30">
                {p.notes}
              </p>
            )}

            {p.updated_at && (
              <div className="text-[0.65rem] text-ink/40 mt-3 tracking-wide">
                last updated {new Date(p.updated_at).toLocaleTimeString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Group({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div className="text-[0.62rem] uppercase tracking-[0.22em] text-bronze mb-2">
        {label}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <span
            key={item}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cream-soft border border-bronze/25 text-[0.78rem] text-ink/80"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
