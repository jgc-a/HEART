import { NextResponse } from "next/server";
import {
  fmtTs,
  idleEvents,
  luisHandshakeSequence,
  nextId,
  type AuditEvent,
} from "@/lib/audit-events";
import { drainEvents, pushEvents } from "@/lib/event-bus";

// In-memory state, lives across requests in the same dev process.
type State = {
  primed: boolean;
  idleCursor: number;
};
const globalKey = Symbol.for("hap.demo.audit_state");
const g = globalThis as unknown as { [k: symbol]: State | undefined };
function getState(): State {
  if (!g[globalKey]) g[globalKey] = { primed: false, idleCursor: 0 };
  return g[globalKey]!;
}

export async function GET() {
  const state = getState();

  // Drain anything queued by /api/handshake/trigger (the full handshake replay)
  const triggered = drainEvents();

  // Always emit a single idle heartbeat each poll to keep the stream alive.
  const idle = idleEvents[state.idleCursor % idleEvents.length];
  state.idleCursor += 1;

  const idleEvent: AuditEvent = {
    ...idle,
    id: nextId(),
    ts: fmtTs(),
  };

  return NextResponse.json({
    events: triggered.length ? triggered : [idleEvent],
  });
}

// Bookkeeping: re-export pushEvents shape for the trigger route to use directly.
export { pushEvents, luisHandshakeSequence };
