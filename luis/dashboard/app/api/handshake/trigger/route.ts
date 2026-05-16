import { NextResponse } from "next/server";
import {
  fmtTs,
  luisHandshakeSequence,
  nextId,
  type AuditEvent,
} from "@/lib/audit-events";
import { pushEvents } from "@/lib/event-bus";

export async function POST() {
  // Spread events out over a few seconds so the stream feels live, but emit
  // them all into the queue at once. The audit stream will pick them up on the
  // next poll. (Timestamps are spaced 700ms apart for visual cadence.)
  const start = Date.now();
  const events: AuditEvent[] = luisHandshakeSequence.map((tmpl, i) => ({
    ...tmpl,
    id: nextId(),
    ts: fmtTs(new Date(start + i * 700)),
  }));

  pushEvents(events);

  return NextResponse.json({
    ok: true,
    queued: events.length,
  });
}
