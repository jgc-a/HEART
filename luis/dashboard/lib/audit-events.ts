export type AuditSeverity = "info" | "ok" | "warn" | "rule";

export type AuditEvent = {
  id: string;
  ts: string;
  event: string;
  scope: string;
  severity: AuditSeverity;
  detail?: string;
};

// Demo handshake sequence for Luis Vargas — matches docs/demo-storyboard.md
export const luisHandshakeSequence: Omit<AuditEvent, "id" | "ts">[] = [
  {
    event: "HAP.HANDSHAKE.RECEIVED",
    scope: "guest=luis_v · scope=6 · ttl=72h",
    severity: "info",
    detail:
      "Consent token signed. 6 of 7 scopes approved (health.context declined).",
  },
  {
    event: "FLOW.CLASSIFIED",
    scope: "profile=Bleisure",
    severity: "ok",
    detail:
      "Confidence 0.94 — Mon–Wed corporate, Thu–Sat leisure. Companion=null.",
  },
  {
    event: "SENSE_OF_PLACE.LOADED",
    scope: "property=rosewood-sand-hill",
    severity: "info",
    detail:
      "Stanford Sierra olive oil grove, Filoli gardens, Sequoia & a16z proximity loaded.",
  },
  {
    event: "RULE.CHECK",
    scope: "HAP-RULE 4.3 family.minors",
    severity: "ok",
    detail: "No minors declared. Standard check-in flow permitted.",
  },
  {
    event: "CONCIERGE.GENERATING",
    scope: "agent=concierge-sonnet-4.5",
    severity: "info",
    detail: "Building arrival brief with 6 scoped fields + sense-of-place RAG.",
  },
  {
    event: "STAFF_BRIEF.READY",
    scope: "guest=luis_v",
    severity: "ok",
    detail:
      "Brief generated in 11.4s. Routed to Duty Manager + Housekeeping Lead.",
  },
  {
    event: "VOICE.SYNTHESIZED",
    scope: "channel=elevenlabs · voice=warm-paused",
    severity: "info",
    detail: "One welcome line, played at guest's preferred volume on arrival.",
  },
  {
    event: "AUDIT.SIGNED",
    scope: "hash=8f3c2a…e1",
    severity: "ok",
    detail: "Chain advanced. Tamper-evident. Retention=0d on guest scope.",
  },
];

// Idle filler events shown before / after the handshake plays
export const idleEvents: Omit<AuditEvent, "id" | "ts">[] = [
  {
    event: "HEARTBEAT",
    scope: "system",
    severity: "info",
    detail: "View synced. 4 arrivals pending in the next 14 days.",
  },
  {
    event: "SCOPE.EXPIRED",
    scope: "guest=anon · ttl=72h",
    severity: "info",
    detail: "Prior session purged from working memory.",
  },
  {
    event: "RULE.CHECK",
    scope: "HAP-RULE 4.9 audit.trail",
    severity: "ok",
    detail: "Continuous audit verified. No drift detected.",
  },
];

let counter = 0;
export function nextId() {
  counter += 1;
  return `evt_${Date.now().toString(36)}_${counter.toString(36)}`;
}

export function fmtTs(d = new Date()): string {
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
