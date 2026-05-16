"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import type { Guest } from "@/lib/guests";

function Section({
  label,
  items,
}: {
  label: string;
  items: string[];
}) {
  return (
    <div>
      <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-3">
        {label}
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item}
            className="text-ink/85 text-[0.95rem] leading-relaxed pl-4 relative before:absolute before:left-0 before:top-[0.75em] before:w-1.5 before:h-1.5 before:rounded-full before:bg-bronze/60"
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function GuestDrawer({
  guest,
  open,
  onOpenChange,
}: {
  guest: Guest | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!guest) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="bg-cream border-l border-bronze/20 w-full sm:max-w-[640px] overflow-y-auto"
      >
        <SheetHeader className="px-10 pt-10 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <Badge
              variant="outline"
              className="border-bronze/40 text-bronze bg-transparent uppercase tracking-[0.18em] text-[0.65rem]"
            >
              {guest.flow}
            </Badge>
            {guest.humanCheckIn && (
              <Badge className="bg-forest text-cream uppercase tracking-[0.18em] text-[0.65rem]">
                Human Required
              </Badge>
            )}
          </div>
          <SheetTitle className="font-serif text-4xl text-ink leading-tight">
            {guest.name}
          </SheetTitle>
          <SheetDescription className="text-ink/65 mt-2 text-[0.95rem]">
            {guest.signal}
          </SheetDescription>
        </SheetHeader>

        <div className="px-10 pb-12 mt-8 space-y-8">
          <div className="grid grid-cols-2 gap-x-6 gap-y-4 pt-6 hairline text-sm">
            <div>
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                Arrival
              </div>
              <div className="text-ink/85 mt-1">
                {guest.arrivalDate} · {guest.arrivalTime}
              </div>
            </div>
            <div>
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                Stay
              </div>
              <div className="text-ink/85 mt-1">{guest.stay}</div>
            </div>
            <div>
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                Origin
              </div>
              <div className="text-ink/85 mt-1">{guest.origin}</div>
            </div>
            <div>
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                Party
              </div>
              <div className="text-ink/85 mt-1">{guest.party}</div>
            </div>
            <div className="col-span-2">
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                Loyalty
              </div>
              <div className="text-ink/85 mt-1">{guest.loyalty}</div>
            </div>
          </div>

          <div className="pt-6 hairline space-y-7">
            <Section label="Room Prep" items={guest.preferences.lodging} />
            <Section label="Dietary" items={guest.preferences.dietary} />
            <Section label="Sense of Place" items={guest.preferences.cultural} />
            <Section label="Visit Context" items={guest.preferences.calendar} />
          </div>

          <div className="pt-6 hairline">
            <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-3">
              Notes for Concierge
            </div>
            <p className="font-serif italic text-ink/85 text-[1.05rem] leading-relaxed">
              {guest.notes}
            </p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
