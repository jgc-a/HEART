"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type Section = {
  label: string;
  items: string[];
};

const sections: Section[] = [
  {
    label: "Room Prep",
    items: [
      "Firm mattress. Replace pillows: 2 firm, 1 medium.",
      "Lighting scene 'Evening Calm' pre-set. Dim bias.",
      "Matcha (Uji, ceremonial grade) on welcome tray, 75°C.",
    ],
  },
  {
    label: "Calendar-Aware",
    items: [
      "Wed 14:00–16:00 · Patio Sur reserved for guest's external meeting.",
      "Thu evening · pivot to Discovery mode. Suggest Filoli Gardens.",
      "Sat · wine country day, driver pre-confirmed.",
    ],
  },
  {
    label: "Dietary",
    items: [
      "No shellfish. Sequoia restaurant menu flagged.",
      "Lighter dinners preferred. Mountain Valley still water.",
    ],
  },
  {
    label: "Sense of Place",
    items: [
      "Welcome amenity: olive oil tasting from Stanford Sierra grove.",
      "Jazz playlist, volume low, queued for arrival window.",
      "Stanford-bound matcha origin acknowledged in arrival note.",
    ],
  },
];

export function StaffBrief({ visible }: { visible: boolean }) {
  const [playing, setPlaying] = useState(false);

  if (!visible) {
    return (
      <div className="bg-card border border-bronze/15 rounded-lg p-10 h-[640px] flex flex-col items-center justify-center text-center">
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-4">
          Awaiting handshake
        </div>
        <p className="font-serif italic text-ink/55 text-xl max-w-md leading-relaxed">
          The Staff Brief will materialize the moment a guest's agent completes
          the consent exchange.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-bronze/25 rounded-lg shadow-[0_8px_24px_-12px_rgba(45,74,62,0.25)] flex flex-col h-[640px] overflow-hidden animate-fade-in-up">
      <div className="px-8 pt-8 pb-6 border-b border-bronze/15 bg-cream-soft/60">
        <div className="flex items-start justify-between gap-4 mb-4">
          <Badge
            variant="outline"
            className="border-bronze/40 text-bronze uppercase tracking-[0.2em] text-[0.65rem]"
          >
            Arrival Brief
          </Badge>
          <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
            Confidence 0.94
          </div>
        </div>
        <h3 className="font-serif text-4xl text-ink leading-tight">
          Luis Vargas
        </h3>
        <p className="text-ink/60 mt-1 text-sm">
          Bleisure · 6 nights · arriving May 18 at 17:45
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-7">
        {sections.map((s) => (
          <div key={s.label}>
            <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-2.5">
              {s.label}
            </div>
            <ul className="space-y-1.5">
              {s.items.map((item) => (
                <li
                  key={item}
                  className="text-ink/85 text-[0.95rem] leading-relaxed pl-4 relative before:absolute before:left-0 before:top-[0.7em] before:w-1.5 before:h-1.5 before:rounded-full before:bg-bronze/55"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className="pt-4 hairline">
          <p className="font-serif italic text-ink/70 text-[1.05rem] leading-relaxed">
            "Welcome ahead of time, Luis. Your room awaits at the temperature of
            an autumn evening, with matcha from Uji. Wednesday afternoon, the
            southern patio is yours alone."
          </p>
        </div>
      </div>

      <div className="px-8 py-5 border-t border-bronze/15 bg-cream-soft/40 flex items-center justify-between">
        <span className="text-[0.7rem] uppercase tracking-[0.22em] text-ink/55">
          No action required from guest
        </span>
        <Button
          size="sm"
          onClick={() => {
            setPlaying(true);
            setTimeout(() => setPlaying(false), 2400);
          }}
          className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.18em] text-[0.7rem] font-medium px-5"
        >
          {playing ? "Playing…" : "Play voice"}
        </Button>
      </div>
    </div>
  );
}
