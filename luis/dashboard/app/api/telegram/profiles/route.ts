import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";

const PROFILES_DIR = path.resolve(
  process.cwd(),
  "..",
  "server",
  "data",
  "live_profiles"
);

type LiveProfile = {
  visit_purpose: string | null;
  lodging: string[];
  dietary: string[];
  cultural: string[];
  wellness: string[];
  notes: string | null;
  ready: boolean;
  updated_at: string | null;
  history?: { role: string; content: string }[];
};

type ProfileWithChat = LiveProfile & { chat_id: number };

export async function GET() {
  let entries: string[] = [];
  try {
    entries = await fs.readdir(PROFILES_DIR);
  } catch {
    return NextResponse.json({ profiles: [] });
  }
  const profiles: ProfileWithChat[] = [];
  for (const file of entries) {
    if (!file.endsWith(".json")) continue;
    const chatId = Number(file.replace(".json", ""));
    if (!Number.isFinite(chatId)) continue;
    try {
      const raw = await fs.readFile(path.join(PROFILES_DIR, file), "utf-8");
      const p = JSON.parse(raw) as LiveProfile;
      profiles.push({ chat_id: chatId, ...p });
    } catch {
      /* skip malformed */
    }
  }
  // newest first
  profiles.sort((a, b) =>
    (b.updated_at || "").localeCompare(a.updated_at || "")
  );
  return NextResponse.json({ profiles });
}
