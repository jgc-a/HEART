// The 5-lane handshake choreography for the live demo.
// Each step animates a message between lanes. ARP steps may reserve resources.
//
// Lanes:
//   human         — Luis (the traveler)
//   guest_agent   — Luis's personal AI (Claude)
//   hotel         — Rosewood's outbound trigger (booking email + HAP invite)
//   concierge     — HEART, the property's concierge agent
//   arp           — Agentic Resource Planner (operational plane, replaces ERP)

export type Lane = "human" | "guest_agent" | "hotel" | "concierge" | "arp";

export type FlowStepType = "message" | "action" | "consent" | "event";

export type FlowStep = {
  id: string;
  from: Lane;
  to: Lane | "self"; // 'self' = internal action, no arrow
  type: FlowStepType;
  label: string; // headline shown in the bubble
  detail?: string; // smaller subtitle inside the bubble
  resources?: string[]; // for ARP lane: chips that get appended
  durationMs: number; // time the bubble lingers before the next step fires
};

export const LANES: { id: Lane; title: string; subtitle: string; tone: "ink" | "forest" | "bronze" }[] = [
  { id: "human", title: "Human", subtitle: "Luis Vargas", tone: "ink" },
  { id: "guest_agent", title: "Guest Agent", subtitle: "Claude (personal)", tone: "forest" },
  { id: "hotel", title: "Hotel", subtitle: "Booking + HAP invite", tone: "bronze" },
  { id: "concierge", title: "Concierge Agent", subtitle: "HEART", tone: "forest" },
  { id: "arp", title: "ARP", subtitle: "Agentic Resource Planner", tone: "bronze" },
];

// Luis's pre-arrival handshake — 15 steps, ~35 seconds end-to-end.
// Calendar contents stay local. Only visit purpose is shared.
export const luisHandshakeFlow: FlowStep[] = [
  {
    id: "f1",
    from: "human",
    to: "guest_agent",
    type: "message",
    label: "\"Voy a Rosewood Sand Hill el 18 de mayo, viaje de negocios.\"",
    detail: "Visit purpose only — calendar contents stay local.",
    durationMs: 2400,
  },
  {
    id: "f2",
    from: "guest_agent",
    to: "self",
    type: "action",
    label: "Ingests purpose + lodging + dietary + cultural prefs",
    detail: "Nothing shared yet. Agent reasons over the guest's local profile.",
    durationMs: 1800,
  },
  {
    id: "f3",
    from: "hotel",
    to: "guest_agent",
    type: "message",
    label: "Booking confirmation + HAP handshake invite",
    detail: "Email subject: \"Welcome ahead of time — Rosewood Sand Hill\". One-click HAP link.",
    durationMs: 2400,
  },
  {
    id: "f4",
    from: "guest_agent",
    to: "human",
    type: "consent",
    label: "Consent Checklist — 6 items",
    detail: "Visit purpose · Lodging · Dietary · Cultural · Loyalty · (Health = optional)",
    durationMs: 3000,
  },
  {
    id: "f5",
    from: "human",
    to: "guest_agent",
    type: "message",
    label: "Approve 5 (declined Health)",
    detail: "Adds one enrichment: \"ceremonial matcha matters this trip\".",
    durationMs: 2200,
  },
  {
    id: "f6",
    from: "guest_agent",
    to: "concierge",
    type: "message",
    label: "HAP.HANDSHAKE.SENT — scope[5], TTL 72h",
    detail: "Signed consent token. Audit URL attached. Zero retention guaranteed.",
    durationMs: 2400,
  },
  {
    id: "f7",
    from: "concierge",
    to: "self",
    type: "action",
    label: "Classify flow → corporate-leaning · Load Sense of Place",
    detail: "Visit purpose = business. Sand Hill VC context, Stanford Sierra grove, Filoli pivot loaded.",
    durationMs: 2200,
  },
  {
    id: "f8",
    from: "concierge",
    to: "arp",
    type: "message",
    label: "Reserve resources for SH-20260518-LU",
    detail: "Room prep, F&B, staff brief routing.",
    resources: [
      "room.temp = 68°F",
      "room.lighting = Evening Calm",
      "f&b.matcha = Uji ceremonial",
      "f&b.sequoia = no shellfish",
      "staff.brief → Duty Mgr + Housekeeping",
    ],
    durationMs: 2600,
  },
  {
    id: "f9",
    from: "concierge",
    to: "guest_agent",
    type: "message",
    label: "Arrival suggestions (5)",
    detail: "Matcha welcome · firm mattress · Evening Calm lighting · low jazz · Stanford Sierra olive oil amenity",
    durationMs: 2600,
  },
  {
    id: "f10",
    from: "guest_agent",
    to: "human",
    type: "message",
    label: "\"¿Quieres confirmar o agregar algo?\"",
    detail: "Shows the 5 suggestions. Each can be accepted, modified, or removed.",
    durationMs: 2800,
  },
  {
    id: "f11",
    from: "human",
    to: "guest_agent",
    type: "message",
    label: "Accept all + add: \"running shoes staged\"",
    detail: "Luis enriches with one extra signal — morning runs on Windy Hill.",
    durationMs: 2400,
  },
  {
    id: "f12",
    from: "guest_agent",
    to: "concierge",
    type: "message",
    label: "Confirmed + 1 enrichment",
    detail: "Final orchestration approved. New item: morning wellness staging.",
    durationMs: 2200,
  },
  {
    id: "f13",
    from: "concierge",
    to: "arp",
    type: "message",
    label: "ARP update: add wellness.morning_run",
    resources: ["wellness.run_gear = staged", "wellness.route = Windy Hill trail map"],
    durationMs: 2200,
  },
  {
    id: "f14",
    from: "arp",
    to: "self",
    type: "event",
    label: "All resources reserved. Stay is ready.",
    detail: "Staff briefs dispatched. Audit log frozen. Voice line synthesized.",
    durationMs: 2200,
  },
  {
    id: "f15",
    from: "concierge",
    to: "guest_agent",
    type: "message",
    label: "Welcome line + arrival ready",
    detail: "ElevenLabs voice: warm, paused. Stay ahead of time.",
    durationMs: 2400,
  },
];
