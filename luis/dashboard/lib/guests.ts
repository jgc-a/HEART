export type Guest = {
  id: string;
  name: string;
  flow: string;
  arrivalDate: string;
  arrivalDateISO: string;
  arrivalTime: string;
  signal: string;
  party: string;
  origin: string;
  flight: string;
  stay: string;
  loyalty: string;
  preferences: {
    lodging: string[];
    dietary: string[];
    cultural: string[];
    calendar: string[];
  };
  notes: string;
  humanCheckIn?: boolean;
};

export const guests: Guest[] = [
  {
    id: "luis_vargas",
    name: "Luis Vargas",
    flow: "Bleisure",
    arrivalDate: "May 18, 2026",
    arrivalDateISO: "2026-05-18",
    arrivalTime: "17:45 local",
    signal: "VC meetings on Sand Hill Road. Weekend extension to Filoli & wine country.",
    party: "Single traveler",
    origin: "Mexico City via SFO — AA1234",
    flight: "AA1234 · lands SFO Terminal 2 at 16:30",
    stay: "May 18 — May 24 · 6 nights",
    loyalty: "Rosewood Elite · Gold (RE-018F-LV)",
    preferences: {
      lodging: [
        "Firm mattress · 2 firm + 1 medium pillow",
        "Lighting scene: Evening Calm, dim bias",
        "Room temperature 20°C / 68°F · high floor, garden view",
      ],
      dietary: [
        "No shellfish — flag the Sequoia menu",
        "Matcha from Uji, ceremonial grade, whisked at 75°C",
        "Lighter dinners · Mountain Valley still water",
      ],
      cultural: [
        "Bilingual ES/EN — formal English for business, warm Spanish for arrival",
        "Jazz playlist, volume low, queued at door",
        "Welcome amenity: Stanford Sierra grove olive oil tasting",
      ],
      calendar: [
        "Visit purpose: business travel, Sand Hill VC corridor.",
        "Discovery mode pre-warmed for end-of-week (Filoli, wine country) if guest opts in.",
        "Calendar specifics remain on the guest's device — never shared with the property.",
      ],
    },
    notes:
      "Calm arrival with jazz, low light, and matcha. Optional health-context disclosure (chronic lower back) — guest may toggle at handshake. Itinerary remains the guest's domain.",
  },
  {
    id: "guillermo_aldana",
    name: "Guillermo Aldana",
    flow: "Corporate",
    arrivalDate: "May 22, 2026",
    arrivalDateISO: "2026-05-22",
    arrivalTime: "15:10 local",
    signal: "Two-day strategy offsite. Pre-loaded corporate billing.",
    party: "Single traveler · EA booked",
    origin: "Mexico City via SFO",
    flight: "AM58 · lands SFO Terminal A at 13:40",
    stay: "May 22 — May 24 · 2 nights",
    loyalty: "Rosewood Elite · Silver",
    preferences: {
      lodging: [
        "Executive desk setup, filtered still water",
        "Early espresso ready at 06:30",
        "Pressing service standard, late check-out held",
      ],
      dietary: [
        "Coffee — espresso double, ristretto if available",
        "Light breakfast, no dairy",
      ],
      cultural: [
        "Sector-relevant press at door · Wired, The Information",
        "Spanish for warmth, English for the brief",
      ],
      calendar: [
        "Visit purpose: two-day strategy offsite.",
        "Off-property meetings declared (no specifics shared). Car service standing by.",
        "Discretion in lobby. Minimal staff visibility requested.",
      ],
    },
    notes:
      "Corporate flow. Minimal lobby presence preferred. Car service pre-coordinated. The guest sets the itinerary — we set the readiness.",
  },
  {
    id: "marcus_chen",
    name: "Marcus Chen",
    flow: "Corporate",
    arrivalDate: "May 25, 2026",
    arrivalDateISO: "2026-05-25",
    arrivalTime: "19:20 local",
    signal: "Founder, Silicon Valley. Series B in active negotiation.",
    party: "Single traveler",
    origin: "Local — Atherton residence",
    flight: "Ground transport (driver, confirmed)",
    stay: "May 25 — May 27 · 2 nights",
    loyalty: "Rosewood Elite · Platinum",
    preferences: {
      lodging: [
        "Suite with adjoining workspace",
        "Phone calls routed to silent — late-night focus block",
        "Bose noise-cancelling on request",
      ],
      dietary: [
        "Vegetarian-leaning. Tasting menu pacing slow",
        "Single-origin coffee at 06:00 sharp",
      ],
      cultural: [
        "Anglophone register, terse, technical",
        "Sense of Place — Filoli book on desk",
      ],
      calendar: [
        "Visit purpose: founder offsite, Series B in active negotiation.",
        "On-property dinners possible (no times shared). Tasting menu pacing set to slow.",
        "Off-property obligations expected — discreetly accommodated, never inferred.",
      ],
    },
    notes:
      "Discretion paramount. No staff name-drop in any channel. Suite turndown only after explicit guest cue.",
  },
  {
    id: "family_johnson",
    name: "Family Johnson",
    flow: "Family with Minors",
    arrivalDate: "May 30, 2026",
    arrivalDateISO: "2026-05-30",
    arrivalTime: "16:00 local",
    signal: "Two children (ages 6, 9). Human check-in required per HAP-RULE 4.3.",
    party: "Four travelers · two adults, two minors",
    origin: "Seattle SEA · Alaska Airlines",
    flight: "AS3304 · lands SFO Terminal 2 at 14:05",
    stay: "May 30 — June 3 · 4 nights",
    loyalty: "Rosewood Elite · Member",
    preferences: {
      lodging: [
        "Connecting rooms · garden-facing",
        "Cribs not required. Bed rails for younger child",
        "Pool floats and kids amenities (with parental consent)",
      ],
      dietary: [
        "Children's menu activated",
        "Adults — Pacific Northwest seasonal, no nuts for younger child",
      ],
      cultural: [
        "English only. Soft, warm register.",
        "Sense of Place — local family experience pre-curated (Hidden Villa farm)",
      ],
      calendar: [
        "Visit purpose: first international family trip in two years.",
        "Family experiences pre-warmed (Filoli, Hidden Villa). Activated only on parental consent.",
        "Daily schedule remains the family's — we stand by, never lead.",
      ],
    },
    humanCheckIn: true,
    notes:
      "MANDATORY human check-in. Documentary verification of both minors at front desk. No alcohol service to adults in pool zones while children present.",
  },
];

export function getGuest(id: string): Guest | undefined {
  return guests.find((g) => g.id === id);
}
