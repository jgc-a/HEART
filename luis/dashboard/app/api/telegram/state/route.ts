import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";

// Shared data files written by server/telegram_bot.py
const ROOT = path.resolve(process.cwd(), "..", "server", "data");
const USERS_FILE = path.join(ROOT, "telegram_users.json");
const EVENTS_FILE = path.join(ROOT, "telegram_events.jsonl");

type TelegramUser = {
  chat_id: number;
  first_name?: string;
  username?: string;
  registered_at_iso?: string;
};

type TelegramEvent = {
  ts: string;
  kind: string;
  chat_id?: number;
  label: string;
};

async function readUsers(): Promise<TelegramUser[]> {
  try {
    const raw = await fs.readFile(USERS_FILE, "utf-8");
    const obj = JSON.parse(raw) as Record<string, TelegramUser>;
    return Object.values(obj);
  } catch {
    return [];
  }
}

async function readEvents(limit = 25): Promise<TelegramEvent[]> {
  try {
    const raw = await fs.readFile(EVENTS_FILE, "utf-8");
    const lines = raw.split("\n").filter(Boolean);
    return lines
      .slice(-limit)
      .map((l) => JSON.parse(l) as TelegramEvent)
      .reverse();
  } catch {
    return [];
  }
}

export async function GET() {
  const [users, events] = await Promise.all([readUsers(), readEvents()]);
  return NextResponse.json({
    bot_configured: Boolean(process.env.TELEGRAM_BOT_TOKEN),
    users_count: users.length,
    users,
    events,
  });
}
