"use client";

import { Badge } from "@/components/ui/badge";
import type { Guest } from "@/lib/guests";

export function GuestCard({
  guest,
  onClick,
}: {
  guest: Guest;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group text-left w-full bg-card border border-bronze/15 rounded-lg p-8 hover:border-bronze/40 hover:shadow-[0_8px_24px_-12px_rgba(45,74,62,0.25)] transition-all duration-300 animate-fade-in-up"
    >
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="font-serif text-3xl text-ink tracking-tight leading-tight">
            {guest.name}
          </h3>
          <div className="text-xs uppercase tracking-[0.22em] text-bronze mt-2">
            {guest.arrivalDate} · {guest.arrivalTime}
          </div>
        </div>
        <Badge
          variant="outline"
          className="border-bronze/40 text-bronze bg-transparent uppercase tracking-[0.16em] text-[0.65rem] font-medium shrink-0"
        >
          {guest.flow}
        </Badge>
      </div>

      <p className="text-ink/75 leading-relaxed text-[0.95rem]">
        {guest.signal}
      </p>

      <div className="mt-7 pt-5 hairline flex items-center justify-between text-xs">
        <span className="text-ink/55 tracking-wide">{guest.party}</span>
        <span className="text-bronze group-hover:text-forest transition-colors tracking-[0.18em] uppercase">
          {guest.humanCheckIn ? "Human required" : "Open snapshot"} →
        </span>
      </div>
    </button>
  );
}
