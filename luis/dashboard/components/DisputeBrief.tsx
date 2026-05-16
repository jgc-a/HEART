"use client";

import { Badge } from "@/components/ui/badge";

export type DisputeTimelineEntry = {
  time: string;
  text: string;
};

export type DisputeData = {
  stay_id: string;
  signed_by: string;
  hash: string;
  generated_at: string;
  timeline: DisputeTimelineEntry[];
  total_minutes: number;
  dual_escalation: boolean;
  guest_mood: string;
  summary: string;
};

export function DisputeBrief({ data }: { data: DisputeData }) {
  return (
    <div className="bg-card border border-bronze/25 rounded-lg shadow-[0_12px_32px_-16px_rgba(45,74,62,0.25)] overflow-hidden animate-fade-in-up">
      <div className="px-10 pt-10 pb-7 border-b border-bronze/15 bg-cream-soft/60">
        <div className="flex items-start justify-between gap-6 mb-5">
          <Badge
            variant="outline"
            className="border-forest/40 text-forest uppercase tracking-[0.22em] text-[0.65rem]"
          >
            Dispute Brief
          </Badge>
          <div className="flex items-center gap-2.5 text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-forest" />
            Signed · WARDEN-HEART
          </div>
        </div>
        <h3 className="font-serif text-4xl text-ink leading-tight tracking-tight">
          Stay {data.stay_id}
        </h3>
        <p className="text-ink/65 mt-3 max-w-2xl text-[0.95rem] leading-relaxed">
          {data.summary}
        </p>
        <div className="grid grid-cols-3 gap-6 mt-7 pt-6 border-t border-bronze/15 text-sm">
          <div>
            <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
              Time to resolution
            </div>
            <div className="font-serif text-2xl text-ink mt-1">
              {data.total_minutes} min
            </div>
          </div>
          <div>
            <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
              Dual escalation
            </div>
            <div className="font-serif text-2xl text-forest mt-1">
              {data.dual_escalation ? "Confirmed" : "—"}
            </div>
          </div>
          <div>
            <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
              Mood at departure
            </div>
            <div className="font-serif text-2xl text-ink mt-1 capitalize">
              {data.guest_mood}
            </div>
          </div>
        </div>
      </div>

      <div className="px-10 py-8">
        <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-5">
          Timeline of AC incident
        </div>
        <ol className="relative pl-6 border-l border-bronze/30 space-y-4">
          {data.timeline.map((entry) => (
            <li key={entry.time + entry.text} className="relative">
              <span className="absolute -left-[1.65rem] top-1.5 w-2 h-2 rounded-full bg-bronze" />
              <div className="flex gap-5 items-baseline">
                <span className="font-mono text-[0.78rem] text-bronze tabular-nums shrink-0 w-14">
                  {entry.time}
                </span>
                <span className="text-ink/85 text-[0.95rem] leading-relaxed">
                  {entry.text}
                </span>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="px-10 py-6 border-t border-bronze/15 bg-cream-soft/40 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
          This brief is auditable. The signal trail is immutable.
        </div>
        <div className="font-mono text-[0.75rem] text-ink/60">
          hash <span className="text-forest">{data.hash}</span> · {data.generated_at}
        </div>
      </div>
    </div>
  );
}
