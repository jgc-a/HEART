"use client";

import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";

const defaultScopes = [
  {
    id: "arrival",
    label: "Arrival date & flight",
    detail: "TTL: until check-out",
    required: false,
    on: true,
  },
  {
    id: "lodging",
    label: "Lodging preferences",
    detail: "firm mattress, dim lighting, jazz, Uji matcha",
    required: false,
    on: true,
  },
  {
    id: "calendar",
    label: "Calendar conflicts",
    detail: "block Patio Sur Wed 2–4 pm",
    required: false,
    on: true,
  },
  {
    id: "dietary",
    label: "Dietary restrictions",
    detail: "no shellfish",
    required: false,
    on: true,
  },
  {
    id: "health",
    label: "Health context",
    detail: "lower-back pain — optional",
    required: false,
    on: false,
  },
  {
    id: "cultural",
    label: "Cultural preferences",
    detail: "matcha, jazz, bilingual",
    required: false,
    on: true,
  },
  {
    id: "family",
    label: "Family signals",
    detail: "not relevant this trip",
    required: false,
    on: false,
  },
];

export function ConsentChecklist() {
  const [scopes, setScopes] = useState(defaultScopes);
  const approved = scopes.filter((s) => s.on).length;

  return (
    <div className="bg-card border border-bronze/15 rounded-lg p-7">
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze">
            Guest-side consent
          </div>
          <h4 className="font-serif text-2xl text-ink mt-1.5 leading-tight">
            Rosewood Sand Hill requests authorization
          </h4>
        </div>
        <div className="text-right">
          <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
            TTL
          </div>
          <div className="font-serif text-xl text-forest">72 h</div>
        </div>
      </div>

      <ul className="space-y-2.5">
        {scopes.map((s) => (
          <li
            key={s.id}
            className="flex items-start gap-3 py-1.5 cursor-pointer"
            onClick={() =>
              setScopes((prev) =>
                prev.map((p) => (p.id === s.id ? { ...p, on: !p.on } : p)),
              )
            }
          >
            <Checkbox
              checked={s.on}
              onCheckedChange={() =>
                setScopes((prev) =>
                  prev.map((p) =>
                    p.id === s.id ? { ...p, on: !p.on } : p,
                  ),
                )
              }
              className="mt-0.5 border-bronze/50 data-[state=checked]:bg-forest data-[state=checked]:border-forest"
            />
            <div className="flex-1 min-w-0">
              <div
                className={`text-[0.95rem] ${s.on ? "text-ink" : "text-ink/40"}`}
              >
                {s.label}
              </div>
              <div
                className={`text-xs ${s.on ? "text-ink/55" : "text-ink/30"}`}
              >
                {s.detail}
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-6 pt-4 hairline flex items-center justify-between text-xs">
        <span className="text-ink/55 tracking-wide uppercase">
          {approved} of {scopes.length} scopes approved
        </span>
        <span className="text-bronze tracking-[0.18em] uppercase">
          Awaiting approve & send →
        </span>
      </div>
    </div>
  );
}
