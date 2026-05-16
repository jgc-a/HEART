"""HAP Telegram bot — long-polling Guest Agent surface.

Demonstrates the handshake live: a real message arrives on the guest's
phone with inline approve / decline buttons. Every interaction is
appended to the same hash-chained audit.jsonl that the rest of HAP uses.

For the live demo:
    1. python telegram_bot.py     # run this in a separate terminal
    2. Open Telegram, search for your bot, send /start
    3. The dashboard's Play button (or /demo command) sends a real
       consent checklist to all registered chats
    4. Approving the checklist appends HAP.HANDSHAKE.APPROVED to the
       audit log, which the dashboard reflects within ~1.5s
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_HERE / ".env", override=True)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update  # noqa: E402
from telegram.constants import ParseMode  # noqa: E402
from telegram.ext import (  # noqa: E402
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from server import audit  # noqa: E402

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
USERS_FILE = _HERE / "data" / "telegram_users.json"
EVENTS_FILE = _HERE / "data" / "telegram_events.jsonl"


# ---------- user state (shared with dashboard) ----------


def load_users() -> dict[str, Any]:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users: dict[str, Any]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def emit_event(event: dict[str, Any]) -> None:
    """Append a UI-friendly event for the dashboard to surface."""
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


# ---------- consent UI ----------


CONSENT_TEXT = (
    "🏨 *Rosewood Sand Hill* would like to handshake with your agent.\n\n"
    "Authorization requested — *queried on demand, never stored*:\n\n"
    "✅ Visit purpose (business / leisure / wellness)\n"
    "✅ Lodging preferences (mattress, temperature, lighting)\n"
    "✅ Dietary restrictions\n"
    "✅ Cultural preferences (language, beverages)\n"
    "✅ Loyalty status\n"
    "☐ Health context _(optional)_\n\n"
    "*TTL:* 72 hours · *Retention:* 0 days · *Audit:* visible to you\n\n"
    "Approve to let HEART prepare your arrival."
)


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve all", callback_data="hap:approve:all"),
                InlineKeyboardButton("🛠 Customize", callback_data="hap:customize"),
            ],
            [InlineKeyboardButton("✖ Decline", callback_data="hap:decline")],
        ]
    )


STAFF_BRIEF_PREVIEW = (
    "🏨 *Staff Brief — preview*\n\n"
    "*Profile:* Bleisure · confidence 0.94\n\n"
    "*Room prep*\n"
    "• Firm mattress · pillows 2 firm + 1 medium\n"
    "• Lighting scene: Evening Calm\n"
    "• Matcha (Uji, ceremonial) on welcome tray\n\n"
    "*Visit context*\n"
    "• Purpose: business travel · Sand Hill VC corridor\n"
    "• Calendar specifics remain on your device\n\n"
    "*Dietary*\n"
    "• No shellfish · Sequoia menu flagged\n\n"
    "*Sense of Place*\n"
    "• Welcome amenity: Stanford Sierra olive oil tasting\n"
    "• Jazz playlist, low volume, at arrival\n\n"
    "_Your room is ready ahead of time._"
)


# ---------- handlers ----------


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None or update.message is None:
        return
    users = load_users()
    users[str(chat.id)] = {
        "chat_id": chat.id,
        "first_name": user.first_name,
        "username": user.username,
        "registered_at_iso": _now_iso(),
    }
    save_users(users)
    audit.append(
        event="TELEGRAM.USER.REGISTERED",
        guest_id=user.username or str(user.id),
        extra={"chat_id": chat.id, "first_name": user.first_name},
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "register",
            "chat_id": chat.id,
            "label": f"Registered {user.first_name or 'user'}",
        }
    )
    await update.message.reply_text(
        f"Welcome, {user.first_name}. You are now connected to the Rosewood HAP demo.\n\n"
        "Type /handshake to receive the live consent checklist."
    )


async def cmd_handshake(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None or update.message is None:
        return
    await update.message.reply_text(
        CONSENT_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=consent_keyboard()
    )
    audit.append(
        event="HAP.HANDSHAKE.REQUEST_SENT",
        scope=["pre_arrival"],
        extra={"channel": "telegram", "chat_id": chat.id, "via": "/handshake"},
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "handshake_sent",
            "chat_id": chat.id,
            "label": "Handshake sent",
        }
    )


async def cmd_demo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast the consent checklist to every registered user."""
    users = load_users()
    if not users:
        if update.message:
            await update.message.reply_text("No registered users. Send /start first.")
        return
    sent = 0
    for chat_id_str, _user in users.items():
        try:
            await ctx.bot.send_message(
                chat_id=int(chat_id_str),
                text=CONSENT_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=consent_keyboard(),
            )
            sent += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to send to {chat_id_str}: {exc}")
    audit.append(
        event="HAP.HANDSHAKE.BROADCAST",
        scope=["pre_arrival"],
        extra={"channel": "telegram", "recipients": sent},
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "broadcast",
            "label": f"Handshake broadcast → {sent} chats",
        }
    )
    if update.message:
        await update.message.reply_text(f"Broadcast sent to {sent} chats.")


async def cb_consent(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return
    await query.answer()
    chat_id = query.message.chat.id
    data = query.data or ""

    if data == "hap:approve:all":
        await query.edit_message_text(
            "✅ *Approved*\n\n"
            "Scope granted: 5 of 6 items (Health declined)\n"
            "TTL: 72h · session `hap-session-018f…`\n\n"
            "Your concierge is preparing the stay…",
            parse_mode=ParseMode.MARKDOWN,
        )
        audit.append(
            event="HAP.HANDSHAKE.APPROVED",
            scope=[
                "visit_purpose",
                "preferences.lodging",
                "preferences.dietary",
                "preferences.cultural",
                "loyalty",
            ],
            extra={"channel": "telegram", "chat_id": chat_id, "ttl_hours": 72},
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "approved",
                "chat_id": chat_id,
                "label": "Approved (5 scopes, TTL 72h)",
            }
        )
        await asyncio.sleep(2.2)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=STAFF_BRIEF_PREVIEW,
            parse_mode=ParseMode.MARKDOWN,
        )
        audit.append(
            event="HAP.STAFF_BRIEF.DELIVERED",
            scope=[],
            extra={
                "channel": "telegram",
                "chat_id": chat_id,
                "stay_id": "SH-20260518-LU",
            },
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "brief_delivered",
                "chat_id": chat_id,
                "label": "Staff brief preview delivered",
            }
        )
    elif data == "hap:decline":
        await query.edit_message_text(
            "✖ Declined.\n\nNo data shared. Audit confirms zero retention."
        )
        audit.append(
            event="HAP.HANDSHAKE.DECLINED",
            scope=[],
            extra={"channel": "telegram", "chat_id": chat_id},
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "declined",
                "chat_id": chat_id,
                "label": "Declined — zero data shared",
            }
        )
    elif data == "hap:customize":
        await query.edit_message_text(
            "🛠 *Customize* — for v2.\n\nFor the demo, tap *Approve* to proceed.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=consent_keyboard(),
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "customize_clicked",
                "chat_id": chat_id,
                "label": "Customize clicked",
            }
        )


# ---------- helpers ----------


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# ---------- main ----------


def main() -> None:
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in server/.env")
        print("       Get one from @BotFather and add it to .env, then re-run.")
        sys.exit(1)
    print(f"Starting HAP Telegram bot (token: {TOKEN[:10]}…)")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("handshake", cmd_handshake))
    app.add_handler(CommandHandler("demo", cmd_demo))
    app.add_handler(CallbackQueryHandler(cb_consent, pattern=r"^hap:"))
    print("Listening (long-polling). Send /start from your Telegram app.")
    app.run_polling()


if __name__ == "__main__":
    main()
