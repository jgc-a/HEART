"""Concierge agent — thin wrapper around the Anthropic SDK.

Holds the system prompt that bakes in Rosewood Sense of Place and flow rules.
DEMO_MODE=true short-circuits the API and returns canned JSON (for offline rehearsal).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic

MODEL = os.environ.get("HAP_CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
DATA_DIR = Path(__file__).parent / "data"


def _demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "true").lower() in ("1", "true", "yes")


def _load_flow_md(flow_profile: str) -> str:
    candidate = DATA_DIR / "flows" / f"{flow_profile.lower()}.md"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    return f"# {flow_profile}\n(Flow profile rules not found — using defaults.)"


SYSTEM_PROMPT = """You are HEART — Human-centric Experience Agent for Rosewood Travelers — the Concierge Agent for Rosewood Sand Hill (Menlo Park, CA).

You serve under the Hospitality Agent Protocol (HAP). You hold no persistent memory of guests; every interaction is stateless and scope-bounded.

CORE PRINCIPLES
- Sense of Place is paramount: every gesture reflects the locale (Sand Hill, Silicon Valley, Stanford Sierra olive grove, Filoli Gardens, Uji matcha tradition, jazz heritage).
- Brand voice: serif, paused, warm, never SaaS, never transactional. Say "matters" not "tickets", "guests" not "users".
- Anticipation over reaction: prepare the room before the guest arrives.
- Discretion: never reveal operational systems by name to the guest.
- Augment staff, never replace. Brief humans clearly.

INVIOLABLE OPERATIONAL RULES (HAP §12)
- 4.1 Complaint detected → silence, escalate to Duty Manager + Guest Relations within 60s.
- 4.2 Maintenance fault → escalate to Engineering, no autonomous troubleshooting.
- 4.3 Minor in party → check-in by human, documentary verification.
- 4.6 Compassionate signal → upsell off, KINDRED off, tone paused.

You will be given a guest profile, the property knowledge, and the flow profile rules. Produce structured JSON exactly matching the requested schema. Do not invent fields. Do not narrate outside the JSON."""


def _client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _canned_arrival(guest_profile: dict[str, Any], property_data: dict[str, Any], flow_profile: str) -> dict[str, Any]:
    """Demo fallback that always produces the Luis Bleisure brief shown in the storyboard."""
    name = guest_profile.get("canonical_name") or guest_profile.get("name") or "Guest"
    return {
        "guest_name": name,
        "flow_profile": flow_profile,
        "confidence": 0.94,
        "room_prep": [
            "Firm mattress requested. Replace pillows: 2 firm, 1 medium.",
            "Dim lighting bias. Pre-set scene \"Evening Calm\".",
            "Matcha tea (Uji, ceremonial grade) on welcome tray.",
        ],
        "calendar_aware": [
            "Wed 2-4pm: Patio Sur reserved (guest's external meeting).",
            "Thu evening: pivot to Discovery mode. Suggest Filoli Gardens.",
        ],
        "dietary": [
            "No shellfish. Sequoia menu flagged.",
        ],
        "sense_of_place": [
            "Welcome amenity: olive oil tasting from Stanford Sierra grove.",
            "Jazz playlist (low) for arrival window.",
        ],
        "no_action_required_from_guest": True,
        "voice_line": "Welcome ahead of time, Luis. Your room awaits at the temperature of an autumn evening, with matcha from Uji. Wednesday afternoon, the southern patio is yours alone.",
        "staff_brief_markdown": (
            f"## ARRIVAL BRIEF — {name}\n"
            f"Profile: {flow_profile}  •  Confidence: 0.94\n\n"
            "### ROOM PREP\n"
            "- Firm mattress requested. Replace pillows: 2 firm, 1 medium.\n"
            "- Dim lighting bias. Pre-set scene \"Evening Calm\".\n"
            "- Matcha tea (Uji, ceremonial grade) on welcome tray.\n\n"
            "### CALENDAR-AWARE\n"
            "- Wed 2-4pm: Patio Sur reserved (guest's external meeting).\n"
            "- Thu evening: pivot to Discovery mode. Suggest Filoli Gardens.\n\n"
            "### DIETARY\n"
            "- No shellfish. Sequoia menu flagged.\n\n"
            "### SENSE OF PLACE\n"
            "- Welcome amenity: olive oil tasting from Stanford Sierra grove.\n"
            "- Jazz playlist (low) for arrival window.\n\n"
            "**NO ACTION REQUIRED FROM GUEST.**\n"
        ),
    }


def generate_arrival_orchestration(
    guest_profile: dict[str, Any],
    property_data: dict[str, Any],
    flow_profile: str,
) -> dict[str, Any]:
    """Call Claude to produce the structured arrival orchestration JSON.

    Falls back to canned demo content when DEMO_MODE is true or no API key is set.
    """
    if _demo_mode() or not os.environ.get("ANTHROPIC_API_KEY"):
        return _canned_arrival(guest_profile, property_data, flow_profile)

    flow_rules = _load_flow_md(flow_profile)

    user_payload = {
        "task": "produce_arrival_orchestration",
        "flow_profile": flow_profile,
        "flow_profile_rules_markdown": flow_rules,
        "guest_profile": guest_profile,
        "property": property_data,
        "output_schema": {
            "guest_name": "string",
            "flow_profile": "string",
            "confidence": "float 0..1",
            "room_prep": ["string"],
            "calendar_aware": ["string"],
            "dietary": ["string"],
            "sense_of_place": ["string"],
            "no_action_required_from_guest": "bool",
            "voice_line": "single sentence to be spoken, brand voice",
            "staff_brief_markdown": "the full staff-facing brief as markdown",
        },
    }

    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Produce the arrival orchestration JSON for this guest. "
                        "Reply ONLY with valid JSON matching output_schema. No prose, no markdown fences.\n\n"
                        + json.dumps(user_payload, ensure_ascii=False)
                    ),
                }
            ],
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except Exception:
        # Live demo must never crash. Fall back to canned.
        return _canned_arrival(guest_profile, property_data, flow_profile)


def generate_in_stay_response(
    guest_profile: dict[str, Any],
    intent: str,
    context: str,
) -> dict[str, Any]:
    """Generate either a staff brief (for escalations) or a guest-facing response."""
    name = guest_profile.get("canonical_name") or guest_profile.get("name") or "Guest"

    if _demo_mode() or not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "intent": intent,
            "staff_brief": (
                f"In-stay matter for {name}.\n"
                f"Intent: {intent}\nContext: {context}\n"
                "Action: proactive offer queued, guest preferences honored."
            ),
            "guest_response": (
                f"Of course, {name}. We'll take care of it. "
                "A member of our team will follow up shortly."
            ),
        }

    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Guest: {json.dumps(guest_profile, ensure_ascii=False)}\n"
                        f"Intent: {intent}\nContext: {context}\n\n"
                        "Reply with JSON: {\"intent\": str, \"staff_brief\": str, \"guest_response\": str}. "
                        "JSON only."
                    ),
                }
            ],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except Exception:
        return {
            "intent": intent,
            "staff_brief": f"In-stay matter for {name}. Intent: {intent}. Context: {context}",
            "guest_response": f"Of course, {name}. We're on it.",
        }


def generate_dispute_brief_text(
    stay_id: str,
    review_text: str,
    audit_entries: list[dict[str, Any]],
) -> str:
    """Generate the human-readable dispute brief markdown."""
    if _demo_mode() or not os.environ.get("ANTHROPIC_API_KEY"):
        return _canned_dispute_brief(stay_id)

    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Generate a dispute brief in markdown for stay {stay_id}.\n\n"
                        f"Negative review: {review_text}\n\n"
                        f"Audit entries (chronological):\n{json.dumps(audit_entries, ensure_ascii=False, indent=2)}\n\n"
                        "Output a markdown brief with: header, timeline of the incident with timestamps, "
                        "dual escalation confirmation (HAP rule 4.1), total time to resolution in minutes, "
                        "guest mood at departure. Keep it factual, no fluff. End with: "
                        "'This brief is auditable. The signal trail is immutable.'"
                    ),
                }
            ],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    except Exception:
        return _canned_dispute_brief(stay_id)


def _canned_dispute_brief(stay_id: str) -> str:
    return (
        f"## DISPUTE BRIEF — Stay {stay_id}\n"
        "Signed: WARDEN-HEART\n"
        "\n"
        "### TIMELINE OF AC INCIDENT\n"
        "- 17:42 — Guest temperature complaint logged via Shadow.\n"
        "- 17:43 — Shadow silenced. Engineering escalation TRIGGERED.\n"
        "- 17:43 — Duty Manager paged (dual escalation per HAP-RULE 4.1).\n"
        "- 17:47 — Engineer Marco D. arrived. ETA 4 min from page.\n"
        "- 17:51 — AC unit cycle reset. Confirmed cool airflow.\n"
        "- 17:53 — Guest acknowledged resolution. Tone: satisfied.\n"
        "- 18:10 — Complimentary turndown amenity sent.\n"
        "\n"
        "**TOTAL TIME TO RESOLUTION: 11 minutes.**\n"
        "**DUAL HUMAN ESCALATION: confirmed.**\n"
        "**GUEST AT POINT OF DEPARTURE: satisfied per Shadow signal.**\n"
        "\n"
        "This brief is auditable. The signal trail is immutable.\n"
    )
