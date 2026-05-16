"""ElevenLabs-powered A2A voice conversation in a Telegram group.

Two bots (@Rosewood_sandhill_guest_bot and @Rosewood_sandhill_hap_bot)
take turns posting voice messages in a shared group, with distinct
ElevenLabs voices. The audience literally hears two agents negotiate.

Anti-loop guarantees:
    - Script is a fixed list of (speaker, text) turns. When the list
      ends, the function returns. There is no recursive callback.
    - asyncio.sleep between turns prevents rate-limit issues and makes
      the cadence feel conversational (not machine-gun).
    - If a conversation is already running for a stay_id, a second
      attempt is rejected (single-flight per stay).

Public API:
    async play_conversation(chat_id, profile, flow_profile, stay_id) -> dict
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
TELEGRAM_BASE = "https://api.telegram.org"

# Single-flight registry: stay_id → asyncio.Task
_running: dict[str, asyncio.Task] = {}


def _api_key() -> str:
    return os.environ.get("ELEVENLABS_API_KEY", "")


def _voice_guest() -> str:
    return os.environ.get(
        "ELEVENLABS_VOICE_ID_GUEST", "ErXwobaYiN019PkySvjV"  # Antoni
    )


def _voice_concierge() -> str:
    return os.environ.get(
        "ELEVENLABS_VOICE_ID_CONCIERGE", "XB0fDUnXU5powFXDhCwa"  # Charlotte
    )


def _heart_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _guest_token() -> str:
    return os.environ.get("TELEGRAM_GUEST_BOT_TOKEN", "")


def _group_chat_id() -> int | None:
    raw = os.environ.get("HAP_VOICE_GROUP_CHAT_ID", "")
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


# ---------- script builder ----------


def build_script(
    profile: dict[str, Any], flow_profile: str
) -> list[tuple[str, str]]:
    """Build a short, varied script from the live profile.

    The conversation is *anchored on real data* — whatever was extracted
    or pre-loaded into the profile becomes the substance of the chat.
    """
    name = profile.get("display_name") or "the guest"
    first_name = name.split()[0] if name else "the guest"
    purpose = profile.get("visit_purpose") or "their stay"
    lodging = profile.get("lodging") or []
    dietary = profile.get("dietary") or []
    cultural = profile.get("cultural") or []

    lines: list[tuple[str, str]] = []

    # Turn 1 — guest agent opens with purpose + the first lodging signal
    opening = (
        f"Hi HEART, this is {first_name}'s agent. "
        f"Visit purpose: {purpose}. "
    )
    if lodging:
        opening += f"{first_name} prefers {lodging[0].lower()}."
    else:
        opening += f"{first_name}'s preferences are standard for now."
    lines.append(("guest_agent", opening))

    # Turn 2 — concierge acknowledges + introduces sense of place
    ack = (
        f"Acknowledged. We'll prep accordingly. "
        f"Welcome amenity: Stanford Sierra olive oil tasting, queued for arrival. "
        f"Anything to flag on dietary?"
    )
    lines.append(("concierge", ack))

    # Turn 3 — guest agent gives dietary + a small surprise enrichment
    diet_text = (
        ", ".join(dietary[:2]).lower() if dietary else "no strict restrictions"
    )
    enrichment = ""
    if cultural:
        enrichment = f" And {first_name} would appreciate {cultural[0].lower()}."
    diet_line = (
        f"Dietary: {diet_text}. Lighter dinners preferred.{enrichment}"
    )
    lines.append(("guest_agent", diet_line))

    # Turn 4 — concierge confirms and wraps
    flow_label = flow_profile or "General"
    wrap = (
        f"Updated. Flow classified as {flow_label}. "
        f"Staff brief routed to the duty manager and housekeeping. "
        f"{first_name}'s stay is ready. Out."
    )
    lines.append(("concierge", wrap))

    return lines


# ---------- audio generation & telegram delivery ----------


async def _generate_audio(client: httpx.AsyncClient, text: str, voice_id: str) -> bytes:
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"
    r = await client.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.25,
                "use_speaker_boost": True,
            },
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.content


async def _send_voice(
    client: httpx.AsyncClient,
    bot_token: str,
    chat_id: int,
    audio_mp3: bytes,
    caption: str,
) -> None:
    """Send audio as a voice message. Telegram accepts MP3 here in practice."""
    url = f"{TELEGRAM_BASE}/bot{bot_token}/sendVoice"
    # Truncate caption to Telegram's 1024-char limit
    caption_short = caption[:1000] + ("…" if len(caption) > 1000 else "")
    r = await client.post(
        url,
        data={"chat_id": chat_id, "caption": caption_short},
        files={"voice": ("turn.mp3", audio_mp3, "audio/mpeg")},
        timeout=30,
    )
    if r.status_code >= 400:
        # Fallback to sendAudio for clients that reject mp3-as-voice
        url2 = f"{TELEGRAM_BASE}/bot{bot_token}/sendAudio"
        await client.post(
            url2,
            data={"chat_id": chat_id, "caption": caption_short},
            files={"audio": ("turn.mp3", audio_mp3, "audio/mpeg")},
            timeout=30,
        )


# ---------- orchestrator ----------


async def play_conversation(
    chat_id: int,
    profile: dict[str, Any],
    flow_profile: str,
    stay_id: str,
    *,
    pause_between_turns_s: float = 2.0,
) -> dict[str, Any]:
    """Play a fixed, finite voice conversation in the given Telegram group.

    Returns a summary dict. Never raises if a step inside fails — emits a
    partial result so callers can fall back gracefully.
    """
    if stay_id in _running and not _running[stay_id].done():
        return {"ok": False, "reason": "already_running", "stay_id": stay_id}

    script = build_script(profile, flow_profile)
    guest_token = _guest_token()
    heart_token = _heart_token()
    voice_guest = _voice_guest()
    voice_heart = _voice_concierge()
    delivered: list[str] = []
    errors: list[str] = []

    async with httpx.AsyncClient() as client:
        for speaker, text in script:
            try:
                if speaker == "guest_agent":
                    audio = await _generate_audio(client, text, voice_guest)
                    await _send_voice(
                        client,
                        bot_token=guest_token,
                        chat_id=chat_id,
                        audio_mp3=audio,
                        caption=f"🤖 Guest Agent · {text}",
                    )
                    delivered.append(f"guest:{text[:60]}…")
                else:
                    audio = await _generate_audio(client, text, voice_heart)
                    await _send_voice(
                        client,
                        bot_token=heart_token,
                        chat_id=chat_id,
                        audio_mp3=audio,
                        caption=f"🏨 HEART · {text}",
                    )
                    delivered.append(f"concierge:{text[:60]}…")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{speaker}: {exc}")
            await asyncio.sleep(pause_between_turns_s)

    return {
        "ok": len(delivered) > 0,
        "stay_id": stay_id,
        "turns_delivered": len(delivered),
        "errors": errors,
    }


def kick_off_conversation_task(
    profile: dict[str, Any],
    flow_profile: str,
    stay_id: str,
) -> asyncio.Task | None:
    """Fire-and-forget launcher — schedules the conversation without awaiting it.

    Returns the Task so callers can attach a done-callback, or None if the
    group chat / tokens / api key aren't configured.
    """
    chat_id = _group_chat_id()
    if not chat_id or not _api_key() or not _guest_token() or not _heart_token():
        return None
    if stay_id in _running and not _running[stay_id].done():
        return _running[stay_id]
    task = asyncio.create_task(
        play_conversation(chat_id, profile, flow_profile, stay_id)
    )
    _running[stay_id] = task
    return task
