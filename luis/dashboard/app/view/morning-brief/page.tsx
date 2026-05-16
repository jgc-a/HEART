"use client";

import { useEffect, useState, useCallback, ReactNode } from "react";

export const dynamic = "force-dynamic";

const HEART_API = "http://localhost:5560";

// ── Types ────────────────────────────────────────────────────────────────
type Brief = {
  sentence: string;
  stats: { in_house: number; arriving: number; needs_you: number };
};
type Arrival = {
  guest_guid: string;
  display_name: string;
  masked: boolean;
  flow: string;
  room: string;
  eta: string;
  human_required: boolean;
  loyalty_tier: string;
  context: string;
};
type QueueItem = {
  id: number;
  guest_guid: string;
  guest_name: string;
  room: string;
  reason: string;
  priority: string;
  status: string;
  created_at: string;
};
type Metrics = {
  asc_score: number;
  unspoken_score: number;
  time_to_insight_avg: string;
  staff_nps: number;
  hap_uptime: string;
};
type Revenue = {
  today: {
    occupancy_pct: number;
    occupied_rooms: number;
    total_rooms: number;
    adr: number;
    revpar: number;
    revenue: number;
    upsell: number;
  };
  week: { occupancy_pct: number; adr: number; revpar: number; revenue: number };
  flow_distribution: { flow: string; count: number }[];
  arrivals_today: number;
  departures_today: number;
};
type Review = {
  id: string;
  platform: string;
  rating: number;
  ts: string;
  guest: string;
  title: string;
  excerpt: string;
  sentiment: "positive" | "negative" | "mixed";
  flagged_for_dispute?: boolean;
  dispute_brief_id?: string | null;
};
type Reviews = {
  reviews: Review[];
  summary: {
    count_total: number;
    this_week_avg: number;
    last_week_avg: number;
    delta: number;
    by_platform: Record<string, number>;
    flagged_count: number;
  };
};
type Staff = {
  briefs_delivered_yesterday: number;
  agent_consults_total: number;
  acceptance_rate_pct: number;
  internal_nps: number;
  top_staff: { name: string; role: string; briefs_received: number; moment: string }[];
};

// ── Fetcher with quiet failures ──────────────────────────────────────────
async function fetchJson<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(HEART_API + path, { cache: "no-store", ...init });
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  }
}

// ── Small atoms ──────────────────────────────────────────────────────────
function ZoneCard({
  eyebrow, title, action, children, className = "",
}: {
  eyebrow: string; title: string; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`bg-cream border border-bronze/20 flex flex-col min-h-0 ${className}`}>
      <header className="flex items-start justify-between gap-3 px-5 pt-4 pb-3 border-b border-bronze/10">
        <div>
          <div className="text-[0.62rem] uppercase tracking-[0.24em] text-bronze">
            {eyebrow}
          </div>
          <h2 className="font-serif text-[1.35rem] leading-tight text-ink mt-0.5">{title}</h2>
        </div>
        {action && <div className="text-[0.7rem] tracking-wide text-bronze/80">{action}</div>}
      </header>
      <div className="px-5 py-4 flex-1 min-h-0 overflow-hidden">{children}</div>
    </section>
  );
}

function SkeletonLine({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`italic text-ink-soft/60 text-sm ${className}`}>{children}</div>
  );
}

function Sparkline({ values, color = "#8b6f47", height = 28, width = 88 }:{
  values: number[]; color?: string; height?: number; width?: number;
}) {
  if (!values.length) return null;
  const min = Math.min(...values), max = Math.max(...values);
  const range = Math.max(0.001, max - min);
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * (width - 2) + 1;
    const y = height - 1 - ((v - min) / range) * (height - 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg width={width} height={height} className="block">
      <polyline fill="none" stroke={color} strokeWidth="1.2" points={points} />
    </svg>
  );
}

function MetricBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-ink-soft/50 text-xs">—</span>;
  const up = delta > 0;
  return (
    <span className={up ? "text-forest text-xs" : "text-terracotta text-xs"}>
      {up ? "↑" : "↓"} {Math.abs(delta).toFixed(2)}
    </span>
  );
}

function flowLabel(flow: string) {
  const m: Record<string, string> = {
    CORPORATE: "Corporate", BLEISURE: "Bleisure", SPECIAL_DATES: "Celebratory",
    FAMILY_WITH_MINORS: "Family", VIP_DISCRETE: "VIP-Discrete", WELLNESS: "Wellness",
    GENERAL: "Standard", GROUP: "Group", MEDICAL: "Medical", TRANSIT: "Transit",
  };
  return m[flow] || flow.toLowerCase().replace(/_/g, " ");
}

// Synthesize a 7-day micro-trend around a current value (for the sparklines).
function trend7(current: number, variance = 0.08): number[] {
  const out: number[] = [];
  for (let i = 6; i >= 0; i--) {
    const drift = (Math.sin((i + 0.7) * 1.3) + Math.cos((i + 2) * 0.9)) * variance * 0.5;
    out.push(Math.max(0, current * (1 - variance / 2 + drift)));
  }
  out.push(current);
  return out;
}

// ── Side panel for "Attend to" ───────────────────────────────────────────
function SidePanel({
  open, onClose, item,
}: { open: boolean; onClose: () => void; item: QueueItem | null }) {
  if (!open || !item) return null;
  return (
    <div className="fixed inset-0 z-50">
      <button
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-ink/30 cursor-default"
      />
      <aside className="absolute right-0 top-0 h-full w-[440px] bg-cream border-l border-bronze/30 p-8 overflow-y-auto">
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-2">
          {item.priority === "CRITICAL" ? "Critical · open matter" : "Open matter"}
        </div>
        <h3 className="font-serif text-3xl text-ink leading-tight">{item.guest_name}</h3>
        <div className="text-ink-soft text-sm mt-1.5">Room {item.room || "—"}</div>

        <div className="mt-7 border-l-2 border-terracotta/70 pl-4 py-1">
          <div className="text-[0.62rem] uppercase tracking-[0.22em] text-bronze">Why this needs you</div>
          <div className="text-ink text-[0.95rem] mt-1 leading-relaxed">{item.reason}</div>
        </div>

        <div className="mt-8">
          <div className="text-[0.62rem] uppercase tracking-[0.22em] text-bronze mb-2">Recommended next move</div>
          <p className="text-ink-soft text-sm leading-relaxed">
            HEART has held the guest agent silent until this matter is acknowledged.
            Attend to it from the floor, then mark it resolved from the In-Stay
            Matters view. The full audit chain is preserved.
          </p>
        </div>

        <div className="mt-10 flex items-center gap-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-[0.72rem] uppercase tracking-[0.2em] text-cream bg-forest hover:bg-forest-soft transition-colors"
          >
            Acknowledge
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-[0.72rem] uppercase tracking-[0.2em] text-ink-soft hover:text-ink"
          >
            Close
          </button>
        </div>
      </aside>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────
export default function MorningBriefPage() {
  const [brief, setBrief]       = useState<Brief | null>(null);
  const [arrivals, setArrivals] = useState<Arrival[] | null>(null);
  const [queue, setQueue]       = useState<QueueItem[] | null>(null);
  const [metrics, setMetrics]   = useState<Metrics | null>(null);
  const [revenue, setRevenue]   = useState<Revenue | null>(null);
  const [reviews, setReviews]   = useState<Reviews | null>(null);
  const [staff, setStaff]       = useState<Staff | null>(null);
  const [now, setNow]           = useState<Date>(new Date());
  const [selected, setSelected] = useState<QueueItem | null>(null);

  // Fast pulse: brief, arrivals, queue every 10s
  const refreshFast = useCallback(async () => {
    const [b, a, q] = await Promise.all([
      fetchJson<Brief>("/api/heart/v1/brief/morning", { method: "POST" }),
      fetchJson<Arrival[]>("/api/heart/v1/arrivals/significant"),
      fetchJson<QueueItem[]>("/api/heart/v1/human-queue"),
    ]);
    if (b) setBrief(b);
    if (a) setArrivals(a);
    if (q) setQueue(q);
  }, []);

  // Slow pulse: metrics/revenue/reviews/staff every 5 min
  const refreshSlow = useCallback(async () => {
    const [m, rev, rv, st] = await Promise.all([
      fetchJson<Metrics>("/api/heart/v1/metrics"),
      fetchJson<Revenue>("/api/heart/v1/revenue/today"),
      fetchJson<Reviews>("/api/heart/v1/reviews/recent"),
      fetchJson<Staff>("/api/heart/v1/staff/amplification"),
    ]);
    if (m)   setMetrics(m);
    if (rev) setRevenue(rev);
    if (rv)  setReviews(rv);
    if (st)  setStaff(st);
  }, []);

  useEffect(() => {
    refreshFast();
    refreshSlow();
  }, [refreshFast, refreshSlow]);

  const openMatters = (queue || []).filter(q => q.status === "PENDING");

  return (
    <div className="fixed inset-0 bg-cream overflow-hidden flex flex-col font-sans text-ink">
      {/* Header */}
      <div className="px-10 pt-7 pb-4 flex items-end justify-between border-b border-bronze/15">
        <div>
          <div className="text-[0.65rem] uppercase tracking-[0.32em] text-bronze">
            Rosewood Sand Hill · The View
          </div>
          <h1 className="font-serif text-[2.4rem] leading-none text-ink mt-1.5 tracking-tight">
            The Morning Brief
          </h1>
        </div>
        <div className="text-right text-ink-soft text-sm">
          <div>{now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</div>
          <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze mt-1">
            {now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })} · PST
          </div>
        </div>
      </div>

      {/* ZONE 1 — Brief sentence + stats */}
      <div className="px-10 py-5 border-b border-bronze/10">
        {brief ? (
          <>
            <p className="font-serif text-[1.6rem] leading-snug text-ink max-w-5xl">
              {brief.sentence}
            </p>
            <div className="mt-3 flex items-baseline gap-9 text-sm">
              <span><span className="font-serif text-2xl text-ink mr-2">{brief.stats.in_house}</span><span className="text-ink-soft text-[0.78rem] uppercase tracking-[0.18em]">in-house</span></span>
              <span><span className="font-serif text-2xl text-ink mr-2">{brief.stats.arriving}</span><span className="text-ink-soft text-[0.78rem] uppercase tracking-[0.18em]">arriving today</span></span>
              <span><span className={`font-serif text-2xl mr-2 ${brief.stats.needs_you > 0 ? "text-terracotta" : "text-ink"}`}>{brief.stats.needs_you}</span><span className="text-ink-soft text-[0.78rem] uppercase tracking-[0.18em]">need{brief.stats.needs_you === 1 ? "s" : ""} you</span></span>
            </div>
          </>
        ) : (
          <SkeletonLine>Composing your morning brief…</SkeletonLine>
        )}
      </div>

      {/* ZONES 2-4 */}
      <div className="grid grid-cols-3 gap-px bg-bronze/15 border-b border-bronze/15 min-h-0 flex-1">
        {/* ZONE 2 — Attention Queue */}
        <ZoneCard
          eyebrow="Need your attention"
          title="Matters"
          action={<span>{openMatters.length} open</span>}
        >
          {!queue ? (
            <SkeletonLine>Listening for matters…</SkeletonLine>
          ) : openMatters.length === 0 ? (
            <div className="italic text-ink-soft/70 text-sm pt-2">
              Nothing pending. The night was quiet.
            </div>
          ) : (
            <ul className="space-y-3.5 overflow-y-auto h-full">
              {openMatters.slice(0, 4).map((m) => {
                const elapsed = humanElapsed(m.created_at);
                return (
                  <li key={m.id} className="border-l-2 border-terracotta/80 pl-3.5">
                    <div className="flex items-baseline justify-between gap-3">
                      <div className="font-serif text-[1.05rem] text-ink leading-tight">
                        {m.guest_name}
                      </div>
                      <div className="text-[0.68rem] uppercase tracking-[0.18em] text-bronze/80 shrink-0">
                        {elapsed}
                      </div>
                    </div>
                    <div className="text-[0.78rem] text-ink-soft mt-0.5">Room {m.room || "—"}</div>
                    <div className="text-[0.82rem] text-ink-soft/90 mt-1 leading-snug line-clamp-2">
                      {m.reason}
                    </div>
                    <button
                      onClick={() => setSelected(m)}
                      className="mt-1.5 text-[0.7rem] uppercase tracking-[0.2em] text-forest hover:text-forest-soft"
                    >
                      Attend to →
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </ZoneCard>

        {/* ZONE 3 — Today's Arrivals */}
        <ZoneCard
          eyebrow="Arriving today"
          title="Whom we welcome"
          action={arrivals ? <span>{arrivals.length}</span> : null}
        >
          {!arrivals ? (
            <SkeletonLine>Reading the day's reservations…</SkeletonLine>
          ) : arrivals.length === 0 ? (
            <div className="italic text-ink-soft/70 text-sm pt-2">No arrivals today.</div>
          ) : (
            <ul className="space-y-3 overflow-y-auto h-full">
              {arrivals.slice(0, 5).map((a) => (
                <li key={a.guest_guid} className="border-l-2 border-bronze/40 pl-3.5">
                  <div className="flex items-baseline justify-between gap-3">
                    <div className="font-serif text-[1.05rem] text-ink leading-tight">
                      {a.display_name}
                    </div>
                    <div className="text-[0.68rem] uppercase tracking-[0.18em] text-bronze/80 shrink-0">
                      {a.eta || "—"}
                    </div>
                  </div>
                  <div className="text-[0.7rem] uppercase tracking-[0.18em] text-bronze mt-0.5">
                    {flowLabel(a.flow)}{a.human_required ? " · human check-in" : ""}
                  </div>
                  <div className="text-[0.82rem] text-ink-soft/90 mt-1 leading-snug line-clamp-2">
                    {a.context}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </ZoneCard>

        {/* ZONE 4 — Pulse */}
        <ZoneCard
          eyebrow="Standard of Care"
          title="Pulse"
          action={<span>this week</span>}
        >
          {!metrics ? (
            <SkeletonLine>Reading the property's vital signs…</SkeletonLine>
          ) : (
            <ul className="space-y-2.5 overflow-y-auto h-full">
              <PulseRow label="Unspoken Score"        current={metrics.unspoken_score}  target={40}  unit="%" trend={trend7(metrics.unspoken_score, 0.06)} />
              <PulseRow label="Time to Insight"       current={parseFloat(metrics.time_to_insight_avg) || 1.8} target={2.0} unit=" min" trend={trend7(parseFloat(metrics.time_to_insight_avg) || 1.8, 0.10)} invert />
              <PulseRow label="Data Sovereignty"      current={100}                     target={100} unit="%" trend={[100,100,100,100,100,100,100,100]} />
              <PulseRow label="Staff Amplification"   current={metrics.staff_nps}       target={80}  unit=" NPS" trend={trend7(metrics.staff_nps, 0.04)} />
              <PulseRow label="Lifetime Connection"   current={Math.round((metrics.asc_score || 94) * 0.78)} target={70} unit="%" trend={trend7(73, 0.05)} />
            </ul>
          )}
          <div className="text-[0.66rem] uppercase tracking-[0.18em] text-ink-soft/55 pt-2 mt-2 border-t border-bronze/10">
            vs LQA / Forbes baseline
          </div>
        </ZoneCard>
      </div>

      {/* ZONES 5-7 */}
      <div className="grid grid-cols-3 gap-px bg-bronze/15 min-h-0 flex-1">
        {/* ZONE 5 — Revenue & Flow */}
        <ZoneCard
          eyebrow="Position"
          title="Revenue & flow"
          action={revenue ? <span>today</span> : null}
        >
          {!revenue ? (
            <SkeletonLine>Pricing the day…</SkeletonLine>
          ) : (
            <div className="h-full flex flex-col">
              <div className="grid grid-cols-3 gap-3">
                <RevStat label="Occupancy" value={`${revenue.today.occupancy_pct}%`}    sub={`${revenue.week.occupancy_pct}% wk`}    />
                <RevStat label="ADR"       value={`$${revenue.today.adr.toFixed(0)}`}   sub={`$${revenue.week.adr.toFixed(0)} wk`}   />
                <RevStat label="RevPAR"    value={`$${revenue.today.revpar.toFixed(0)}`} sub={`$${revenue.week.revpar.toFixed(0)} wk`} />
              </div>
              <div className="mt-3 flex items-baseline justify-between text-sm">
                <span className="text-[0.68rem] uppercase tracking-[0.2em] text-bronze">Upsell today</span>
                <span className="font-serif text-[1.4rem] text-forest">${revenue.today.upsell.toLocaleString()}</span>
              </div>
              <div className="mt-3 flex-1 min-h-0">
                <div className="text-[0.66rem] uppercase tracking-[0.18em] text-ink-soft/60 mb-1.5">
                  Flow distribution · this week
                </div>
                <FlowBar distribution={revenue.flow_distribution} />
              </div>
            </div>
          )}
        </ZoneCard>

        {/* ZONE 6 — Reputation */}
        <ZoneCard
          eyebrow="Voice of guest"
          title="Reputation"
          action={reviews ? <span>{reviews.summary.count_total} this week</span> : null}
        >
          {!reviews ? (
            <SkeletonLine>Listening for new voices…</SkeletonLine>
          ) : (
            <div className="h-full flex flex-col">
              <div className="flex items-baseline gap-4">
                <div className="font-serif text-[2.2rem] text-ink leading-none">{reviews.summary.this_week_avg.toFixed(2)}</div>
                <div className="text-[0.7rem] uppercase tracking-[0.2em] text-bronze">avg this week</div>
                <MetricBadge delta={reviews.summary.delta} />
              </div>
              <ul className="mt-3 space-y-2.5 overflow-y-auto flex-1 min-h-0">
                {reviews.reviews.slice(0, 4).map((r) => (
                  <li key={r.id} className={`border-l-2 pl-3 ${r.flagged_for_dispute ? "border-terracotta/80" : "border-bronze/30"}`}>
                    <div className="flex items-baseline justify-between gap-2">
                      <div className="text-[0.78rem] text-ink">
                        <span className="font-medium">{r.platform}</span> · {"★".repeat(r.rating)}<span className="text-ink-soft/40">{"★".repeat(5 - r.rating)}</span>
                      </div>
                      {r.flagged_for_dispute && (
                        <a
                          href="/reputation"
                          className="text-[0.66rem] uppercase tracking-[0.18em] text-terracotta hover:text-terracotta/80"
                        >
                          Generate dispute brief →
                        </a>
                      )}
                    </div>
                    <div className="text-[0.78rem] text-ink-soft mt-0.5 line-clamp-1 italic">
                      "{r.excerpt}"
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </ZoneCard>

        {/* ZONE 7 — Staff Amplification */}
        <ZoneCard
          eyebrow="Team"
          title="Staff amplification"
          action={staff ? <span>yesterday</span> : null}
        >
          {!staff ? (
            <SkeletonLine>Counting briefs delivered…</SkeletonLine>
          ) : (
            <div className="h-full flex flex-col">
              <div className="grid grid-cols-2 gap-3">
                <RevStat label="Briefs delivered" value={String(staff.briefs_delivered_yesterday)} sub="yesterday" />
                <RevStat label="Acceptance"       value={`${staff.acceptance_rate_pct.toFixed(0)}%`} sub={`${staff.internal_nps} NPS`} />
              </div>
              <div className="text-[0.66rem] uppercase tracking-[0.18em] text-ink-soft/60 mt-3 mb-1.5">
                Recognized this morning
              </div>
              <ul className="space-y-2 flex-1 min-h-0 overflow-y-auto">
                {staff.top_staff.map((s) => (
                  <li key={s.name} className="border-l-2 border-forest/40 pl-3">
                    <div className="flex items-baseline justify-between gap-2">
                      <div className="font-serif text-[1rem] text-ink leading-tight">{s.name}</div>
                      <div className="text-[0.66rem] uppercase tracking-[0.18em] text-bronze">{s.role}</div>
                    </div>
                    <div className="text-[0.78rem] text-ink-soft/90 leading-snug mt-0.5 line-clamp-2">
                      {s.moment}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </ZoneCard>
      </div>

      <SidePanel
        open={selected !== null}
        item={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

// ── Smaller stat components ─────────────────────────────────────────────
function RevStat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="text-[0.62rem] uppercase tracking-[0.18em] text-bronze">{label}</div>
      <div className="font-serif text-[1.4rem] text-ink leading-none mt-0.5">{value}</div>
      {sub && <div className="text-[0.66rem] uppercase tracking-[0.16em] text-ink-soft/55 mt-0.5">{sub}</div>}
    </div>
  );
}

function PulseRow({
  label, current, target, unit, trend, invert = false,
}: { label: string; current: number; target: number; unit: string; trend: number[]; invert?: boolean }) {
  const meeting = invert ? current <= target : current >= target;
  return (
    <li className="flex items-center justify-between gap-2">
      <div className="min-w-0 flex-1">
        <div className="text-[0.78rem] text-ink leading-tight">{label}</div>
        <div className="text-[0.66rem] uppercase tracking-[0.16em] text-ink-soft/55">
          target {target}{unit}
        </div>
      </div>
      <Sparkline values={trend} color={meeting ? "#2d4a3e" : "#b85042"} />
      <div className="text-right shrink-0 w-[60px]">
        <div className={`font-serif text-[1.15rem] leading-none ${meeting ? "text-forest" : "text-terracotta"}`}>
          {typeof current === "number" ? (current % 1 === 0 ? current : current.toFixed(1)) : current}
          <span className="text-[0.7rem] ml-0.5 text-ink-soft/70">{unit}</span>
        </div>
      </div>
    </li>
  );
}

function FlowBar({ distribution }: { distribution: { flow: string; count: number }[] }) {
  const total = distribution.reduce((s, d) => s + d.count, 0) || 1;
  const colors: Record<string, string> = {
    CORPORATE: "#2d4a3e", BLEISURE: "#4a6d5e", SPECIAL_DATES: "#a07b5c",
    FAMILY_WITH_MINORS: "#b89a76", VIP_DISCRETE: "#1a1a1a", WELLNESS: "#7a9d8c",
    GENERAL: "#8b6f47", GROUP: "#6b5e4a", MEDICAL: "#7a7268", TRANSIT: "#9a8c75",
  };
  return (
    <div>
      <div className="flex h-3 w-full overflow-hidden">
        {distribution.map((d) => (
          <div
            key={d.flow}
            title={`${flowLabel(d.flow)} · ${d.count}`}
            className="h-full"
            style={{
              width: `${(d.count / total * 100).toFixed(2)}%`,
              background: colors[d.flow] || "#8b6f47",
            }}
          />
        ))}
      </div>
      <ul className="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5">
        {distribution.slice(0, 4).map((d) => (
          <li key={d.flow} className="flex items-center gap-1.5 text-[0.7rem] text-ink-soft">
            <span className="inline-block w-2 h-2" style={{ background: colors[d.flow] || "#8b6f47" }} />
            <span className="truncate">{flowLabel(d.flow)}</span>
            <span className="text-ink-soft/60">· {d.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function humanElapsed(iso: string): string {
  if (!iso) return "";
  const t = new Date(iso.replace(" ", "T") + (iso.endsWith("Z") ? "" : "Z"));
  const diff = (Date.now() - t.getTime()) / 1000;
  if (isNaN(diff) || diff < 0) return "";
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
  return `${Math.floor(diff / 86400)} d`;
}
