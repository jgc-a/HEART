import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";

const SESSIONS_FILE = path.resolve(
  process.cwd(),
  "..",
  "server",
  "data",
  "active_sessions.json"
);

type HapSession = {
  session_id: string;
  guest_id: string;
  guest_display: string;
  scope: string[];
  client_kind: string;
  client_label: string;
  opened_at_iso: string;
  ttl_hours: number;
  expires_at_iso: string;
  revoked_at_iso: string | null;
  checkout_initiated_at_iso: string | null;
  active: boolean;
  stay_id: string | null;
};

async function readSessions(): Promise<HapSession[]> {
  try {
    const raw = await fs.readFile(SESSIONS_FILE, "utf-8");
    const data = JSON.parse(raw) as HapSession[];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export async function GET() {
  const all = await readSessions();
  const now = Date.now();
  // mark anything past its TTL as inactive on the way out
  const projected = all.map((s) => {
    if (!s.active) return s;
    const exp = new Date(s.expires_at_iso).getTime();
    if (exp < now) return { ...s, active: false, revoked_at_iso: s.revoked_at_iso || new Date(now).toISOString() };
    return s;
  });
  projected.sort((a, b) => b.opened_at_iso.localeCompare(a.opened_at_iso));
  return NextResponse.json({
    sessions: projected,
    active_count: projected.filter((s) => s.active).length,
  });
}
