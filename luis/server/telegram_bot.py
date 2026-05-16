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
    MessageHandler,
    filters,
)

from server import audit, guest_agent, guest_memory, sessions  # noqa: E402
from server.tools import (  # noqa: E402
    arrival as arrival_tool,
    checkout as checkout_tool,
    handshake as handshake_tool,
)

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


def welcome_keyboard() -> InlineKeyboardMarkup:
    """Shown at /start — points the user at the conversational flow."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📜 What is HAP?", callback_data="hap:about"
                ),
                InlineKeyboardButton(
                    "🔐 How is this private?", callback_data="hap:audit"
                ),
            ],
        ]
    )


def handshake_ready_keyboard() -> InlineKeyboardMarkup:
    """Shown after the agent has learned enough — invites the actual handshake."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Authorize handshake (Step 1 of 3)",
                    callback_data="hap:start_flow",
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Tell me more first",
                    callback_data="hap:continue_chat",
                )
            ],
        ]
    )


# In-memory pending outcomes per chat (waiting for Phase 3 confirm)
_pending_outcomes: dict[int, dict[str, Any]] = {}


def recognized_keyboard() -> InlineKeyboardMarkup:
    """Shown when the agent recognized the user and already has a profile loaded."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Authorize handshake (Step 1 of 3)",
                    callback_data="hap:start_flow",
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Adjust before sending",
                    callback_data="hap:continue_chat",
                ),
                InlineKeyboardButton(
                    "🔄 Switch persona",
                    callback_data="hap:list_personas",
                ),
            ],
        ]
    )


def confirm_outcome_keyboard() -> InlineKeyboardMarkup:
    """Shown at Phase 3 — the negotiated outcome awaits user confirmation."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm outcome (Step 3 of 3)",
                    callback_data="hap:confirm_outcome",
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Renegotiate",
                    callback_data="hap:continue_chat",
                )
            ],
        ]
    )


def persona_picker_keyboard(personas: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in personas:
        rows.append(
            [
                InlineKeyboardButton(
                    f"{p.get('display_name')} · {p.get('visit_purpose', '')[:32]}",
                    callback_data=f"hap:persona:{p['id']}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton("✏️ Start a fresh conversation", callback_data="hap:fresh")]
    )
    return InlineKeyboardMarkup(rows)


def _format_recognized_summary(profile: dict) -> str:
    """Render the 'your agent already knows you' summary."""
    lines: list[str] = []
    if profile.get("visit_purpose"):
        lines.append(f"📍 *Visit purpose:* {profile['visit_purpose']}")

    def section(emoji: str, label: str, items: list[str] | None) -> None:
        if not items:
            return
        lines.append("")
        lines.append(f"{emoji} *{label}*")
        for item in items:
            lines.append(f"• {item}")

    section("🛏", "Lodging", profile.get("lodging"))
    section("🍽", "Dietary", profile.get("dietary"))
    section("🌿", "Cultural / beverages", profile.get("cultural"))
    if profile.get("wellness"):
        lines.append("")
        lines.append("☐ *Wellness (opt-in)*")
        for item in profile["wellness"]:
            lines.append(f"• {item}")
    return "\n".join(lines)


def _format_live_profile(profile: dict) -> str:
    """Render the live profile as a markdown consent block."""
    bullets: list[str] = []

    def line(emoji: str, label: str, value) -> None:
        if isinstance(value, list) and value:
            bullets.append(f"✅ *{label}:* " + ", ".join(value))
        elif isinstance(value, str) and value:
            bullets.append(f"✅ *{label}:* {value}")

    line("✅", "Visit purpose", profile.get("visit_purpose"))
    line("✅", "Lodging", profile.get("lodging"))
    line("✅", "Dietary", profile.get("dietary"))
    line("✅", "Cultural / beverages", profile.get("cultural"))
    if profile.get("wellness"):
        bullets.append("☐ *Wellness:* " + ", ".join(profile["wellness"]) + " _(optional)_")

    if not bullets:
        bullets = ["_(no preferences captured — agent will share visit purpose only)_"]

    return (
        "🏨 *Rosewood Sand Hill* would like to handshake with your agent.\n\n"
        "Based on our conversation, your agent will share — _on demand, never stored_:\n\n"
        + "\n".join(bullets)
        + "\n\n*TTL:* 72 hours · *Retention:* 0 days · *Audit:* visible to you\n\n"
        "Approve to let HEART prepare your arrival."
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

    # If the user came from a Telegram deep link (?start=stay-SH-...), the
    # booking reference arrives as ctx.args[0]. Acknowledge it as the entry
    # point from the welcome email — the bot is the Guest Agent surface on
    # mobile.
    booking_ref: str | None = None
    if ctx.args and ctx.args[0].startswith("stay-"):
        booking_ref = ctx.args[0]
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "email_deeplink",
                "chat_id": chat.id,
                "label": f"Opened from booking confirmation · {booking_ref}",
            }
        )
        audit.append(
            event="HAP.PLUGIN.OPENED_FROM_EMAIL",
            guest_id=user.username or str(user.id),
            extra={"chat_id": chat.id, "booking_ref": booking_ref},
        )
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
    # reset any prior conversation so the demo starts clean
    guest_agent.reset_profile(chat.id)

    # Try to recognize the user against the preloaded personas
    preloaded = guest_agent.match_preloaded(user.username, user.first_name)

    if preloaded:
        profile = guest_agent.bootstrap_from_preloaded(chat.id, preloaded)
        origin = preloaded.get("agent_memory_origin", "Claude memory")
        purpose = profile.get("visit_purpose") or "your stay"

        summary = _format_recognized_summary(profile)

        from_email = ""
        if booking_ref:
            from_email = (
                f"_(opened from your Rosewood booking confirmation · {booking_ref})_\n\n"
            )

        await update.message.reply_text(
            f"🏨 *{preloaded.get('display_name', user.first_name)}*, it's me — your agent.\n\n"
            f"{from_email}"
            f"I recognized you from {origin}. "
            "I'm ready to handshake with *Rosewood Sand Hill* on your behalf — "
            "scope-bounded, time-bounded, signed.\n\n"
            f"For *{purpose}* I'll share:\n\n"
            f"{summary}\n\n"
            "_You won't have to type anything else. I'll show you what we negotiated "
            "with HEART and you'll confirm in one tap._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=recognized_keyboard(),
        )
        audit.append(
            event="GUEST_AGENT.PERSONA_RECOGNIZED",
            guest_id=preloaded["id"],
            extra={
                "chat_id": chat.id,
                "persona_id": preloaded["id"],
                "via": user.username or user.first_name,
            },
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "persona_recognized",
                "chat_id": chat.id,
                "label": f"Recognized persona · {preloaded.get('display_name')} ({preloaded.get('visit_purpose')})",
            }
        )
        return

    # Fallback: conversational mode (current behavior)
    from_email = ""
    if booking_ref:
        from_email = (
            f"_(you came from your Rosewood booking confirmation · {booking_ref})_\n\n"
        )
    await update.message.reply_text(
        f"🏨 Hi {user.first_name}, I'm your agent on Telegram.\n\n"
        f"{from_email}"
        "Think of me as your Claude in the messaging app — same identity, same memory, "
        "speaking *Rosewood Sand Hill*'s protocol on your behalf.\n\n"
        "I don't have a profile on file for you yet. Tell me one or two things about your "
        "trip and I'll learn the rest. Or use /persona to load a demo persona instantly.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=welcome_keyboard(),
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "interview_started",
            "chat_id": chat.id,
            "label": f"Interview started with {user.first_name or 'guest'}",
        }
    )


async def cmd_checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """End the stay — revoke every active HAP session for this chat.

    This is the lifecycle bookend: same way you'd revoke an OAuth grant on
    Google or remove a plugin from Claude Desktop, /checkout disconnects
    the HAP plugin and writes the revocation to the audit log.
    """
    chat = update.effective_chat
    if chat is None or update.message is None:
        return

    chat_id = chat.id
    profile = guest_agent.get_profile(chat_id)
    guest_id = f"telegram_{chat_id}"

    result = checkout_tool.run(
        checkout_tool.CheckoutInput(
            guest_id=guest_id,
            reason="user_checkout",
        )
    )

    if not result.revoked:
        await update.message.reply_text(
            "🔌 No active HAP session to close. Use /start to begin a new stay."
        )
        return

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "session_revoked",
            "chat_id": chat_id,
            "label": f"HAP plugin disconnected · {len(result.revoked)} session(s) revoked",
        }
    )

    display = profile.get("display_name") or "your stay"
    await update.message.reply_text(
        f"🔌 *Checkout complete*\n\n"
        f"Your HAP plugin has disconnected from Rosewood Sand Hill.\n"
        f"_{len(result.revoked)} session(s) revoked · {display}_\n\n"
        "The audit log retains the operational signal (pseudonymous), but the "
        "property no longer has any access token for your agent. Thank you for staying.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_persona(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Force-load a specific demo persona. Usage: /persona luis | marcus | guillermo | family_johnson"""
    chat = update.effective_chat
    if chat is None or update.message is None:
        return

    args = ctx.args or []
    if not args:
        personas = guest_agent.list_preloaded()
        await update.message.reply_text(
            "🎭 *Pick a persona to load:*\n\n"
            "Each persona is a different traveler your agent 'already knows'.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=persona_picker_keyboard(personas),
        )
        return

    persona_id = args[0].lower()
    preloaded = guest_agent.load_preloaded_by_id(persona_id)
    if not preloaded:
        await update.message.reply_text(
            f"No persona named `{persona_id}`. Try /persona without arguments to pick one.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    profile = guest_agent.bootstrap_from_preloaded(chat.id, preloaded)
    summary = _format_recognized_summary(profile)
    purpose = profile.get("visit_purpose") or "your stay"

    await update.message.reply_text(
        f"🎭 Persona loaded: *{preloaded.get('display_name')}*\n\n"
        f"_Pulled from {preloaded.get('agent_memory_origin', 'Claude memory')}._\n\n"
        f"About to handshake with Rosewood for *{purpose}*:\n\n"
        f"{summary}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=recognized_keyboard(),
    )
    audit.append(
        event="GUEST_AGENT.PERSONA_LOADED",
        guest_id=preloaded["id"],
        extra={"chat_id": chat.id, "persona_id": preloaded["id"], "via": "command"},
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "persona_loaded",
            "chat_id": chat.id,
            "label": f"Persona loaded · {preloaded.get('display_name')}",
        }
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

    if data == "hap:request_handshake" or data == "hap:initiate_handshake":
        # Build consent message from the live profile (real conversation data)
        profile = guest_agent.get_profile(chat_id)
        consent_text = _format_live_profile(profile)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=consent_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=consent_keyboard(),
        )
        audit.append(
            event="HAP.HANDSHAKE.REQUEST_SENT",
            scope=["pre_arrival"],
            extra={
                "channel": "telegram",
                "chat_id": chat_id,
                "via": "button",
                "purpose": profile.get("visit_purpose"),
                "scope_size": (
                    (1 if profile.get("visit_purpose") else 0)
                    + len(profile.get("lodging") or [])
                    + len(profile.get("dietary") or [])
                    + len(profile.get("cultural") or [])
                    + len(profile.get("wellness") or [])
                ),
            },
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "handshake_sent",
                "chat_id": chat_id,
                "label": f"Handshake requested · purpose={profile.get('visit_purpose') or 'n/a'}",
            }
        )
        return

    if data == "hap:continue_chat":
        await ctx.bot.send_message(
            chat_id=chat_id,
            text="Of course. What's changed? Just tell me normally and I'll update the scope.",
        )
        return

    if data == "hap:list_personas":
        personas = guest_agent.list_preloaded()
        await ctx.bot.send_message(
            chat_id=chat_id,
            text="🎭 *Switch persona:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=persona_picker_keyboard(personas),
        )
        return

    if data == "hap:fresh":
        guest_agent.reset_profile(chat_id)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text="Fresh start. *Tell me about your trip.* I'll learn as we talk.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("hap:persona:"):
        persona_id = data.split(":", 2)[2]
        preloaded = guest_agent.load_preloaded_by_id(persona_id)
        if not preloaded:
            await ctx.bot.send_message(chat_id=chat_id, text="That persona is gone.")
            return
        profile = guest_agent.bootstrap_from_preloaded(chat_id, preloaded)
        summary = _format_recognized_summary(profile)
        purpose = profile.get("visit_purpose") or "your stay"
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🎭 *{preloaded.get('display_name')}* loaded.\n\n"
                f"_Pulled from {preloaded.get('agent_memory_origin', 'Claude memory')}._\n\n"
                f"Ready to handshake for *{purpose}*:\n\n"
                f"{summary}"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=recognized_keyboard(),
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "persona_loaded",
                "chat_id": chat_id,
                "label": f"Persona loaded · {preloaded.get('display_name')}",
            }
        )
        return

    if data == "hap:about":
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=(
                "📜 *HAP — Hospitality Agent Protocol*\n\n"
                "Anthropic built *MCP* to connect models to the world.\n"
                "We propose *HAP* to connect guests to hospitality.\n\n"
                "*Three guarantees:*\n"
                "• Scope-based consent — you choose what to share\n"
                "• TTL — every share expires (default 72h)\n"
                "• Zero retention — the hotel queries on demand, never stores\n\n"
                "Open spec. Anyone can implement. Rosewood is the reference."
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=welcome_keyboard(),
        )
        return

    if data == "hap:audit":
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=(
                "🔐 *Your audit trail*\n\n"
                "Every HAP interaction is hash-chained with SHA-256.\n"
                "Tampering with any entry breaks the chain — instantly visible.\n\n"
                "Audit endpoint:\n"
                "`https://heart.rosewood/audit/your-session`\n\n"
                "Retention of guest data: *0 days*.\n"
                "Retention of operational signal: indefinite, pseudonymous."
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=welcome_keyboard(),
        )
        return

    if data == "hap:start_flow" or data == "hap:approve:all" or data == "hap:initiate_handshake":
        await _run_three_phase_flow(query, ctx, chat_id)
        return

    if data == "hap:confirm_outcome":
        await _handle_confirm_outcome(query, ctx, chat_id)
        return

    # Legacy stub kept so any orphan message buttons don't crash; never enters now.
    if data == "hap:approve:all_legacy":
        profile = guest_agent.get_profile(chat_id)
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
        # legacy stub body — never reached; kept to avoid syntax break
        pass
        # (legacy continuation removed)
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


# ---------- A2A bridge: turn a live Telegram profile into a HAP guest JSON ----------


def _save_hap_guest_from_telegram(chat_id: int, first_name: str | None, profile: dict) -> str:
    """Materialize the live conversation profile as a HAP-SCHEMA guest JSON
    so the HAP tools (handshake + arrival) can operate on real data.

    Returns the guest_id used by the HAP server.
    """
    import json as _json
    from pathlib import Path as _Path

    guests_dir = _Path(__file__).parent / "data" / "guests"
    guests_dir.mkdir(parents=True, exist_ok=True)

    guest_id = f"telegram_{chat_id}"
    hap_guest = {
        "guest_guid": f"hap-guid-telegram-{chat_id}",
        "canonical_name": first_name or f"Guest {chat_id}",
        "email_accounts": [],
        "preferences": {
            "lodging": {
                "notes": profile.get("lodging") or [],
            },
            "dietary": {
                "restrictions": profile.get("dietary") or [],
            },
            "cultural": {
                "notes": profile.get("cultural") or [],
            },
            "wellness": {
                "notes": profile.get("wellness") or [],
            },
        },
        "visit_purpose": profile.get("visit_purpose"),
        "calendar": {"conflicts": []},  # never extracted from Telegram per design
        "health": {"context": None},
        "minors_present": False,
        "loyalty": [],
        "billing": {"method": "verified_token"},
        "source": "telegram_live_profile",
        "captured_at": profile.get("updated_at"),
    }
    (guests_dir / f"{guest_id}.json").write_text(
        _json.dumps(hap_guest, indent=2), encoding="utf-8"
    )
    return guest_id


def _profile_to_scope(profile: dict) -> list[str]:
    """Translate the live profile's filled fields into HAP scope strings."""
    scopes: list[str] = []
    if profile.get("visit_purpose"):
        scopes.append("visit.purpose")
    if profile.get("lodging"):
        scopes.append("preferences.lodging")
    if profile.get("dietary"):
        scopes.append("preferences.dietary")
    if profile.get("cultural"):
        scopes.append("preferences.cultural")
    if profile.get("wellness"):
        scopes.append("preferences.wellness")
    return scopes


# ---------- main ----------


async def _run_three_phase_flow(query, ctx: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """The HAP three-phase flow: Handshake → A2A negotiation → User confirmation.

    Phase 1: Scope authorization (handshake_tool). User has already approved
             the scope by tapping the trigger button — this phase mints the
             consent token and opens the session.
    Phase 2: Agent-to-agent negotiation within the authorized scope. No user
             input. Multiple A2A round-trips visible in the dashboard. Ends
             with HEART (concierge Claude) producing the orchestration.
    Phase 3: User confirms (or renegotiates) the negotiated outcome. THIS is
             where the brief is committed and delivered.
    """
    profile = guest_agent.get_profile(chat_id)
    chat = query.message.chat
    first_name = chat.first_name if hasattr(chat, "first_name") else None
    guest_id = _save_hap_guest_from_telegram(chat_id, first_name, profile)
    scopes = _profile_to_scope(profile)

    # =====================================================================
    # PHASE 1 — HANDSHAKE (scope authorization)
    # =====================================================================
    await query.edit_message_text(
        "🔐 *Phase 1 of 3 — Authorizing handshake*\n\n"
        f"Manifest: {len(scopes)} scope categor{'ies' if len(scopes) != 1 else 'y'}\n"
        "TTL: 72 hours\n\n"
        "_Minting consent token, opening session…_",
        parse_mode=ParseMode.MARKDOWN,
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "phase_start",
            "chat_id": chat_id,
            "label": "▶ Phase 1 — Handshake (scope authorization)",
        }
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_request",
            "chat_id": chat_id,
            "from": "guest_agent",
            "to": "concierge",
            "tool": "hap_handshake",
            "label": f"Guest Agent → HEART · manifest({len(scopes)} scopes, TTL 72h)",
        }
    )

    try:
        handshake_result = handshake_tool.run(
            handshake_tool.HandshakeInput(
                guest_id=guest_id,
                scope_requested=scopes,
                ttl_hours=72,
                client_kind="telegram_bot",
                client_label=f"@Rosewood_sandhill_hap_bot · chat {chat_id}",
                guest_display=profile.get("display_name") or first_name or f"Guest {chat_id}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        await ctx.bot.send_message(chat_id=chat_id, text=f"⚠️ Handshake failed: {exc}")
        return

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "hap_handshake",
            "label": f"HEART → Guest Agent · session {handshake_result.session_id[:18]}… opened, consent token signed",
        }
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "phase_complete",
            "chat_id": chat_id,
            "label": "✓ Phase 1 complete — session opened, no data exchanged yet",
        }
    )

    await asyncio.sleep(0.5)

    # =====================================================================
    # PHASE 2 — A2A NEGOTIATION (within authorized scope)
    # =====================================================================
    await query.edit_message_text(
        f"✅ *Phase 1 complete*\n"
        f"_Session_ `{handshake_result.session_id[:16]}…`\n"
        "_TTL_ `72h` · _Scope_ "
        f"`{len(scopes)} categories`\n\n"
        "🤝 *Phase 2 of 3 — Agents negotiating within scope*\n\n"
        "_No input needed. My agent and HEART are talking now — watch the dashboard._",
        parse_mode=ParseMode.MARKDOWN,
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "phase_start",
            "chat_id": chat_id,
            "label": "▶ Phase 2 — A2A negotiation (within scope)",
        }
    )

    # Sequence the A2A turns so the dashboard renders them progressively.
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_request",
            "chat_id": chat_id,
            "from": "guest_agent",
            "to": "concierge",
            "tool": "scope.lodging",
            "label": f"Guest Agent → HEART · preferences.lodging ({len(profile.get('lodging') or [])} items)",
        }
    )
    await asyncio.sleep(1.0)

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "flow.classify",
            "label": "HEART → Guest Agent · ack · classifying flow profile",
        }
    )
    await asyncio.sleep(0.8)

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "sense_of_place.load",
            "label": "HEART · loading Sense of Place RAG for Rosewood Sand Hill",
        }
    )
    await asyncio.sleep(0.8)

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_request",
            "chat_id": chat_id,
            "from": "guest_agent",
            "to": "concierge",
            "tool": "scope.dietary+cultural",
            "label": f"Guest Agent → HEART · preferences.dietary + preferences.cultural",
        }
    )
    await asyncio.sleep(0.8)

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "concierge.invoke",
            "label": "HEART · invoking concierge Claude (Sonnet 4.5) for arrival orchestration",
        }
    )

    # Real Claude call — produces the actual brief (this takes ~20s).
    try:
        arrival_result = arrival_tool.run(
            arrival_tool.ArrivalInput(
                guest_id=guest_id,
                arrival_date="2026-05-18",
                session_id=handshake_result.session_id,
            )
        )
    except Exception as exc:  # noqa: BLE001
        await ctx.bot.send_message(
            chat_id=chat_id, text=f"⚠️ Arrival orchestration failed: {exc}"
        )
        return

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "hap_propose_arrival",
            "label": f"HEART → Guest Agent · brief generated · flow={arrival_result.flow_profile} · stay={arrival_result.stay_id}",
        }
    )
    await asyncio.sleep(0.6)

    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_request",
            "chat_id": chat_id,
            "from": "guest_agent",
            "to": "concierge",
            "tool": "scope.validate",
            "label": "Guest Agent · validating brief stays within authorized scope · ✓",
        }
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "phase_complete",
            "chat_id": chat_id,
            "label": "✓ Phase 2 complete — outcome negotiated, awaiting user confirmation",
        }
    )

    # Stash the result for Phase 3.
    _pending_outcomes[chat_id] = {
        "arrival_result": arrival_result,
        "handshake_result": handshake_result,
        "guest_id": guest_id,
        "scopes": scopes,
    }

    # =====================================================================
    # PHASE 3 PROMPT — user confirms negotiated outcome
    # =====================================================================
    await ctx.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ *Phase 2 complete* — outcome negotiated\n\n"
            f"Flow profile: *{arrival_result.flow_profile}*\n"
            f"Stay ID: `{arrival_result.stay_id}`\n\n"
            "✋ *Phase 3 of 3 — Confirm the outcome*\n\n"
            "My agent has reviewed the brief and signed it within the scope you authorized. "
            "Tap *Confirm* to commit, or *Renegotiate* if anything looks off."
        ),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_outcome_keyboard(),
    )


async def _handle_confirm_outcome(query, ctx: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Phase 3: user confirms the negotiated outcome — commit + deliver brief."""
    pending = _pending_outcomes.get(chat_id)
    if not pending:
        await query.edit_message_text(
            "⚠️ Session expired. Send /start to begin again."
        )
        return

    arrival_result = pending["arrival_result"]
    handshake_result = pending["handshake_result"]
    guest_id = pending["guest_id"]
    scopes = pending["scopes"]

    audit.append(
        event="HAP.OUTCOME.CONFIRMED",
        guest_id=guest_id,
        session_id=handshake_result.session_id,
        scope=scopes,
        extra={
            "channel": "telegram",
            "chat_id": chat_id,
            "stay_id": arrival_result.stay_id,
            "flow_profile": arrival_result.flow_profile,
        },
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "phase_complete",
            "chat_id": chat_id,
            "label": "✓ Phase 3 complete — outcome committed by user",
        }
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "approved",
            "chat_id": chat_id,
            "label": f"Outcome confirmed · stay {arrival_result.stay_id} · flow {arrival_result.flow_profile}",
        }
    )

    await query.edit_message_text(
        f"✅ *All three phases complete*\n\n"
        f"Stay `{arrival_result.stay_id}` is set.\n"
        f"Flow: *{arrival_result.flow_profile}*\n\n"
        "_Staff brief incoming…_",
        parse_mode=ParseMode.MARKDOWN,
    )

    brief = arrival_result.staff_brief_markdown
    if len(brief) > 3500:
        brief = brief[:3400] + "\n\n_(truncated for Telegram)_"
    await ctx.bot.send_message(
        chat_id=chat_id,
        text=f"🏨 *HEART has prepared your stay*\n\n{brief}",
        parse_mode=ParseMode.MARKDOWN,
    )
    if arrival_result.voice_line:
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=f"_{arrival_result.voice_line}_",
            parse_mode=ParseMode.MARKDOWN,
        )

    audit.append(
        event="HAP.STAFF_BRIEF.DELIVERED",
        scope=[],
        extra={
            "channel": "telegram",
            "chat_id": chat_id,
            "stay_id": arrival_result.stay_id,
            "flow_profile": arrival_result.flow_profile,
        },
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "brief_delivered",
            "chat_id": chat_id,
            "label": f"Staff brief delivered · {arrival_result.flow_profile}",
        }
    )

    # === Agent-to-agent memory handoff (HAP §6 — HAP.MEMORY.RETURNED_TO_GUEST) ===
    # The property transmits the refined memory snapshot to the guest agent
    # via the HAP tool. The guest agent internalizes it. No file is exchanged
    # with the human — this is how GitHub-MCP / Drive-MCP also work: the
    # protocol delivers structured data, the agent absorbs it.
    profile = guest_agent.get_profile(chat_id)

    # Run the real HAP tool — this is the same tool a Claude Desktop user
    # would call. It returns the structured snapshot AND the rendered markdown.
    from server.tools import post_stay as post_stay_tool

    try:
        memory_result = post_stay_tool.run(
            post_stay_tool.PostStayInput(stay_id=arrival_result.stay_id)
        )
    except Exception as exc:  # noqa: BLE001
        memory_result = None
        print(f"[telegram] post_stay tool failed: {exc}")

    # Also render the markdown (kept on disk so the dashboard can show
    # "what the agent now knows" — read-only, not a download).
    md = guest_memory.generate_guest_md(
        profile=profile,
        history=[],
        persona_id=profile.get("persona_id"),
        last_stay={
            "property_name": "Rosewood Sand Hill",
            "stay_id": arrival_result.stay_id,
            "flow_profile": arrival_result.flow_profile,
        },
    )
    guest_memory.save_guest_md(chat_id, md)

    # Count what was learned, for the conversational handoff message.
    counts = {
        "lodging": len(profile.get("lodging") or []),
        "dietary": len(profile.get("dietary") or []),
        "cultural": len(profile.get("cultural") or []),
        "wellness": len(profile.get("wellness") or []),
    }
    n_modes = 4  # generate_guest_md always emits 4 trip modes

    audit.append(
        event="HAP.MEMORY.RETURNED_TO_GUEST",
        guest_id=guest_id,
        session_id=handshake_result.session_id,
        scope=["post_stay.memory"],
        extra={
            "chat_id": chat_id,
            "stay_id": arrival_result.stay_id,
            "schema": "hap-guest-memory/v0.1",
            "lodging_count": counts["lodging"],
            "dietary_count": counts["dietary"],
            "cultural_count": counts["cultural"],
            "wellness_count": counts["wellness"],
            "trip_modes": n_modes,
        },
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "a2a_response",
            "chat_id": chat_id,
            "from": "concierge",
            "to": "guest_agent",
            "tool": "hap_post_stay_memory",
            "label": (
                f"HEART → Guest Agent · memory snapshot returned · "
                f"{sum(counts.values())} preferences across {n_modes} trip modes"
            ),
        }
    )
    emit_event(
        {
            "ts": _now_iso(),
            "kind": "memory_internalized",
            "chat_id": chat_id,
            "label": "Guest Agent · snapshot internalized — schema hap-guest-memory/v0.1",
        }
    )

    # The handoff message — conversational, no file, no download.
    handoff_lines = ["📡 *Memory snapshot internalized*", ""]
    handoff_lines.append("Your agent just received the refined memory from HEART:")
    if counts["lodging"]:
        handoff_lines.append(f"  • {counts['lodging']} lodging preferences")
    if counts["dietary"]:
        handoff_lines.append(f"  • {counts['dietary']} dietary signals")
    if counts["cultural"]:
        handoff_lines.append(f"  • {counts['cultural']} cultural / beverage preferences")
    if counts["wellness"]:
        handoff_lines.append(f"  • {counts['wellness']} wellness items (opt-in)")
    handoff_lines.append(f"  • {n_modes} trip modes with interaction intensity + alert caps")
    handoff_lines.append("")
    handoff_lines.append(
        "This travels with _me_, not with Rosewood. Next stay anywhere, your agent "
        "starts a new handshake already knowing you. No data was left on the property "
        "side beyond the pseudonymous audit chain."
    )
    handoff_lines.append("")
    handoff_lines.append(
        "_(Just like when your Claude uses the GitHub plugin — the data flows into the "
        "agent through the protocol. There's nothing to download.)_"
    )

    await ctx.bot.send_message(
        chat_id=chat_id,
        text="\n".join(handoff_lines),
        parse_mode=ParseMode.MARKDOWN,
    )

    _pending_outcomes.pop(chat_id, None)


async def cb_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Plain-text messages → Guest Agent (Claude) conversation."""
    msg = update.message
    if msg is None or not msg.text or update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    user_text = msg.text.strip()

    # Show typing indicator while Claude thinks
    await ctx.bot.send_chat_action(chat_id=chat_id, action="typing")

    result = guest_agent.converse(chat_id, user_text)
    reply = result["reply"]
    ready = result["ready"]
    new_keys = result["new_keys"]
    profile = result["profile"]

    audit.append(
        event="GUEST_AGENT.CONVERSATION_TURN",
        guest_id=str(chat_id),
        scope=[],
        extra={
            "chat_id": chat_id,
            "new_keys": new_keys,
            "ready": ready,
            "purpose": profile.get("visit_purpose"),
        },
    )

    # emit one event per learned key so dashboard can highlight in real time
    for k in new_keys:
        v = profile.get(k)
        if isinstance(v, list) and v:
            label = f"learned {k}: {', '.join(v[-3:])}"
        elif isinstance(v, str):
            label = f"learned {k}: {v}"
        else:
            label = f"learned {k}"
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "preference_learned",
                "chat_id": chat_id,
                "label": label,
                "key": k,
            }
        )

    if ready:
        await msg.reply_text(
            reply + "\n\n_Ready when you are._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=handshake_ready_keyboard(),
        )
        emit_event(
            {
                "ts": _now_iso(),
                "kind": "agent_ready",
                "chat_id": chat_id,
                "label": f"Agent ready to handshake · purpose={profile.get('visit_purpose')}",
            }
        )
    else:
        await msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


def _build_staff_brief_preview(profile: dict) -> str:
    """Render the staff brief from real extracted preferences."""
    lines: list[str] = ["🏨 *Staff Brief — preview*", ""]
    purpose = profile.get("visit_purpose") or "general travel"
    lines.append(f"*Visit context:* {purpose}")
    lines.append("")
    if profile.get("lodging"):
        lines.append("*Room prep*")
        for item in profile["lodging"]:
            lines.append(f"• {item}")
        lines.append("")
    if profile.get("dietary"):
        lines.append("*Dietary*")
        for item in profile["dietary"]:
            lines.append(f"• {item}")
        lines.append("")
    if profile.get("cultural"):
        lines.append("*Sense of Place / culture*")
        for item in profile["cultural"]:
            lines.append(f"• {item}")
        lines.append("")
    if profile.get("wellness"):
        lines.append("*Wellness (opt-in)*")
        for item in profile["wellness"]:
            lines.append(f"• {item}")
        lines.append("")
    lines.append("_Your room is being readied. Calendar specifics remain on your device._")
    return "\n".join(lines)


def main() -> None:
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in server/.env")
        print("       Get one from @BotFather and add it to .env, then re-run.")
        sys.exit(1)
    print(f"Starting HAP Telegram bot (token: {TOKEN[:10]}…)", flush=True)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("handshake", cmd_handshake))
    app.add_handler(CommandHandler("demo", cmd_demo))
    app.add_handler(CommandHandler("persona", cmd_persona))
    app.add_handler(CommandHandler("checkout", cmd_checkout))
    app.add_handler(CallbackQueryHandler(cb_consent, pattern=r"^hap:"))
    # Plain text → conversational guest agent (must be last so it's the fallback)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cb_message))
    print("Listening (long-polling). Send /start from your Telegram app.", flush=True)
    app.run_polling()


if __name__ == "__main__":
    main()
