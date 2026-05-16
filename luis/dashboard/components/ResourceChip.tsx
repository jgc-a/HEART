"use client";

export function ResourceChip({ label, fresh = false }: { label: string; fresh?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[0.7rem] font-mono tracking-tight whitespace-nowrap transition-colors ${
        fresh
          ? "bg-bronze/15 border-bronze/45 text-bronze animate-fade-in-up"
          : "bg-cream-soft border-bronze/20 text-ink/65"
      }`}
    >
      {fresh && <span className="w-1 h-1 rounded-full bg-bronze animate-pulse-dot" />}
      {label}
    </span>
  );
}
