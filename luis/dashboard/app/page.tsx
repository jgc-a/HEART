"use client";

import { useState } from "react";
import { GuestCard } from "@/components/GuestCard";
import { GuestDrawer } from "@/components/GuestDrawer";
import { guests, type Guest } from "@/lib/guests";

export default function TodaysArrivalsPage() {
  const [selected, setSelected] = useState<Guest | null>(null);
  const [open, setOpen] = useState(false);

  return (
    <div className="max-w-[1400px] mx-auto px-10 py-16">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.32em] text-bronze mb-3">
            Rosewood Sand Hill · The View
          </div>
          <h1 className="font-serif text-6xl text-ink leading-[1.05] tracking-tight max-w-3xl">
            Today&apos;s Arrivals
          </h1>
          <p className="text-ink/65 mt-5 max-w-2xl text-lg leading-relaxed">
            Four guests, four flow profiles, observed before the door opens.
            Their agents have spoken to ours.
          </p>
        </div>
        <div className="text-right text-sm text-ink/55 tracking-wide">
          <div>May 16, 2026</div>
          <div className="text-bronze uppercase tracking-[0.22em] text-[0.7rem] mt-1">
            4 arrivals · 14 days
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-7">
        {guests.map((guest) => (
          <GuestCard
            key={guest.id}
            guest={guest}
            onClick={() => {
              setSelected(guest);
              setOpen(true);
            }}
          />
        ))}
      </div>

      <GuestDrawer guest={selected} open={open} onOpenChange={setOpen} />
    </div>
  );
}
