import type { AuditEvent } from "./audit-events";

// Single in-memory queue shared across API route invocations.
// Next.js dev shares module state on the server; this is fine for demo.

type Bus = {
  queue: AuditEvent[];
  seq: number;
};

const globalKey = Symbol.for("hap.demo.event_bus");
const g = globalThis as unknown as { [k: symbol]: Bus | undefined };

function getBus(): Bus {
  if (!g[globalKey]) {
    g[globalKey] = { queue: [], seq: 0 };
  }
  return g[globalKey]!;
}

export function pushEvents(events: AuditEvent[]) {
  const bus = getBus();
  bus.queue.push(...events);
}

export function drainEvents(): AuditEvent[] {
  const bus = getBus();
  const events = bus.queue;
  bus.queue = [];
  return events;
}

export function peekQueueLength(): number {
  return getBus().queue.length;
}
