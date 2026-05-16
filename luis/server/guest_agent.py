"""Guest Agent — the Claude-powered surface the traveler actually talks to.

This is the agent that lives "on the guest's side". In a real deployment
the guest brings their own Claude/ChatGPT/Gemini and our HAP MCP server
plugs in. For the live demo we proxy it through the Telegram bot, so a
real judge can have a real conversation with a real Claude that extracts
preferences and only THEN initiates the handshake with HEART.

Two responsibilities:
    1. Have a short, warm conversation that captures intent + preferences.
    2. Return structured preference extraction so HAP has real data to send.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from anthropic import Anthropic

MODEL = os.environ.get("HAP_CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
DATA_DIR = Path(__file__).parent / "data"
PROFILES_DIR = DATA_DIR / "live_profiles"


SYSTEM_PROMPT = """You are the traveler's personal AI agent — think of yourself as their Claude, talking to them through a Telegram bot.

Your job:
1. Have a short, warm conversation (max 3-4 turns) to learn about THEIR upcoming stay at Rosewood Sand Hill.
2. Extract structured preferences as you go.
3. When you have enough signal, offer to initiate a HAP handshake with the hotel.

Tone:
- Conversational, warm, brief. Never robotic. You are THEIR agent, not the hotel's.
- Ask one focused question at a time. Never give a menu.
- If the user says "ready" or "go ahead" or has given you enough info (purpose + at least one preference), set ready=true.
- Respect that some travelers want to share little. Don't push for health info, calendar contents, or family details unless they volunteer.

Extraction rules:
- visit_purpose: short phrase ("business", "hackathon", "leisure", "wellness retreat", "anniversary", etc.)
- lodging: list of lodging preferences ("firm mattress", "high floor", "quiet room", "garden view", "blackout curtains", etc.)
- dietary: list of dietary signals ("vegetarian", "no shellfish", "lighter dinners", "matcha lover", etc.)
- cultural: list of cultural/beverage preferences ("matcha", "espresso", "Spanish warmth", "jazz", "early riser", etc.)
- wellness: list of wellness signals ("recovering from jet lag", "back pain", "wants to hike", "deep tissue", etc.) — ONLY if user volunteers
- notes: free-text observations about the traveler in the third person

Hard rules:
- NEVER invent preferences the user didn't say or imply.
- NEVER ask for calendar specifics. Visit purpose is enough.
- NEVER ask for health info. Only capture it if the user shares it.

Always reply with a JSON object exactly matching this schema:
{
  "reply": "your conversational message to the user (markdown ok, keep under 60 words)",
  "extracted": {
    "visit_purpose": "string or null",
    "lodging": ["..."],
    "dietary": ["..."],
    "cultural": ["..."],
    "wellness": ["..."],
    "notes": "string or null"
  },
  "ready": false
}

Set ready=true ONLY when:
- visit_purpose is set, AND
- at least one of lodging/dietary/cultural has at least one item, AND
- the user has had at least one chance to add more

Do not narrate outside the JSON."""


def _client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _profile_path(chat_id: int) -> Path:
    return PROFILES_DIR / f"{chat_id}.json"


def _empty_profile() -> dict[str, Any]:
    return {
        "visit_purpose": None,
        "lodging": [],
        "dietary": [],
        "cultural": [],
        "wellness": [],
        "notes": None,
        "history": [],
        "ready": False,
        "updated_at": None,
    }


def get_profile(chat_id: int) -> dict[str, Any]:
    p = _profile_path(chat_id)
    if not p.exists():
        return _empty_profile()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_profile()


def save_profile(chat_id: int, profile: dict[str, Any]) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    _profile_path(chat_id).write_text(json.dumps(profile, indent=2), encoding="utf-8")


def reset_profile(chat_id: int) -> None:
    p = _profile_path(chat_id)
    if p.exists():
        p.unlink()


def _merge_extracted(profile: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    """Merge newly-extracted prefs into the existing profile (additive, never destructive)."""
    if extracted.get("visit_purpose") and not profile.get("visit_purpose"):
        profile["visit_purpose"] = extracted["visit_purpose"]
    for key in ("lodging", "dietary", "cultural", "wellness"):
        for item in extracted.get(key, []) or []:
            if item and item not in profile.get(key, []):
                profile.setdefault(key, []).append(item)
    if extracted.get("notes"):
        if profile.get("notes"):
            profile["notes"] = f"{profile['notes']} · {extracted['notes']}"
        else:
            profile["notes"] = extracted["notes"]
    return profile


def converse(chat_id: int, user_message: str) -> dict[str, Any]:
    """One turn of the conversation. Returns {reply, profile, ready, new_keys}.

    new_keys is the list of preference categories that gained an item this turn,
    for the dashboard to highlight.
    """
    profile = get_profile(chat_id)
    history: list[dict[str, str]] = profile.get("history", [])

    api_messages: list[dict[str, Any]] = []
    # rebuild the conversation in api format
    for h in history:
        api_messages.append({"role": h["role"], "content": h["content"]})
    api_messages.append({"role": "user", "content": user_message})

    extracted: dict[str, Any] = {}
    reply_text = ""
    ready = False

    if not os.environ.get("ANTHROPIC_API_KEY"):
        # Demo fallback if no key — extract nothing, just echo nicely.
        reply_text = "Got it. Tell me one more thing about your trip, then I'll ready the handshake."
    else:
        try:
            resp = _client().messages.create(
                model=MODEL,
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=api_messages,
            )
            raw = resp.content[0].text if resp.content else "{}"
            parsed = _parse_json(raw)
            reply_text = parsed.get("reply") or "Got it."
            extracted = parsed.get("extracted") or {}
            ready = bool(parsed.get("ready"))
        except Exception as exc:  # noqa: BLE001
            reply_text = "I had a hiccup. Could you say that again?"
            print(f"[guest_agent] error: {exc}")

    # snapshot for diff
    before = {
        k: list(profile.get(k, [])) if isinstance(profile.get(k), list) else profile.get(k)
        for k in ("visit_purpose", "lodging", "dietary", "cultural", "wellness")
    }
    profile = _merge_extracted(profile, extracted)
    after = {
        k: list(profile.get(k, [])) if isinstance(profile.get(k), list) else profile.get(k)
        for k in ("visit_purpose", "lodging", "dietary", "cultural", "wellness")
    }
    new_keys: list[str] = []
    for k in after:
        if before.get(k) != after.get(k):
            new_keys.append(k)

    # update history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply_text})
    profile["history"] = history[-12:]  # keep last 6 turns

    # ready logic — also enforce server-side
    has_purpose = bool(profile.get("visit_purpose"))
    has_pref = any(
        profile.get(k) for k in ("lodging", "dietary", "cultural", "wellness")
    )
    profile["ready"] = ready and has_purpose and has_pref

    save_profile(chat_id, profile)

    return {
        "reply": reply_text,
        "profile": profile,
        "ready": profile["ready"],
        "new_keys": new_keys,
    }


def _parse_json(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction. Tolerates code fences and prose."""
    raw = raw.strip()
    # strip code fences
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1] if "```" in raw[3:] else raw[3:]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    # find first { and last }
    if "{" in raw and "}" in raw:
        raw = raw[raw.index("{") : raw.rindex("}") + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
