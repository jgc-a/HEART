import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "..", "server", "data");
const USERS_FILE = path.join(ROOT, "telegram_users.json");
const EVENTS_FILE = path.join(ROOT, "telegram_events.jsonl");

const CONSENT_TEXT = `🏨 *Rosewood Sand Hill* would like to handshake with your agent.

Authorization requested — _queried on demand, never stored_:

✅ Visit purpose (business / leisure / wellness)
✅ Lodging preferences (mattress, temperature, lighting)
✅ Dietary restrictions
✅ Cultural preferences (language, beverages)
✅ Loyalty status
☐ Health context _(optional)_

*TTL:* 72 hours · *Retention:* 0 days · *Audit:* visible to you

Approve to let HEART prepare your arrival.`;

const KEYBOARD = {
  inline_keyboard: [
    [
      { text: "✅ Approve all", callback_data: "hap:approve:all" },
      { text: "🛠 Customize", callback_data: "hap:customize" },
    ],
    [{ text: "✖ Decline", callback_data: "hap:decline" }],
  ],
};

type TelegramUser = {
  chat_id: number;
  first_name?: string;
  username?: string;
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

async function appendEvent(kind: string, label: string, chat_id?: number) {
  const line =
    JSON.stringify({
      ts: new Date().toISOString(),
      kind,
      chat_id,
      label,
    }) + "\n";
  try {
    await fs.appendFile(EVENTS_FILE, line, "utf-8");
  } catch {
    /* swallow */
  }
}

export async function POST() {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    return NextResponse.json(
      { ok: false, reason: "TELEGRAM_BOT_TOKEN not set in dashboard env" },
      { status: 400 }
    );
  }
  const users = await readUsers();
  if (!users.length) {
    return NextResponse.json(
      { ok: false, reason: "No registered users. Send /start to the bot first." },
      { status: 400 }
    );
  }

  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  let sent = 0;
  const errors: string[] = [];

  for (const u of users) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: u.chat_id,
          text: CONSENT_TEXT,
          parse_mode: "Markdown",
          reply_markup: KEYBOARD,
        }),
      });
      const json = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        description?: string;
      };
      if (res.ok && json.ok) {
        sent += 1;
        await appendEvent(
          "broadcast",
          `Consent sent → ${u.first_name || u.username || u.chat_id}`,
          u.chat_id
        );
      } else {
        errors.push(`${u.chat_id}: ${json.description || res.statusText}`);
      }
    } catch (e) {
      errors.push(`${u.chat_id}: ${(e as Error).message}`);
    }
  }

  return NextResponse.json({
    ok: sent > 0,
    sent,
    errors,
  });
}
