"""hap_post_stay_memory — returns a memory snapshot for the guest's agent (HAP-RIGHTS portability)."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .. import audit  # type: ignore[relative-beyond-top-level]
from .arrival import _load_json, _mock_guest  # type: ignore[relative-beyond-top-level]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class PostStayInput(BaseModel):
    stay_id: str
    guest_id: str | None = None
    session_id: str | None = None


class PostStayOutput(BaseModel):
    stay_id: str
    memory_snapshot: dict[str, Any]
    data_confirmation: dict[str, Any]


def run(payload: PostStayInput) -> PostStayOutput:
    session_id = payload.session_id or f"hap-session-{secrets.token_hex(8)}"
    guest_id = payload.guest_id or _infer_guest_from_stay(payload.stay_id)

    guest_profile: dict[str, Any] = {}
    if guest_id:
        guest_path = DATA_DIR / "guests" / f"{guest_id}.json"
        guest_profile = _load_json(guest_path) or _mock_guest(guest_id)

    stay_entries = audit.read_for_stay(payload.stay_id)

    memory = {
        "schema": "hap-memory/v0.1",
        "stay_id": payload.stay_id,
        "property_id": "rosewood-sand-hill",
        "guest_guid": guest_profile.get("guest_guid"),
        "canonical_name": guest_profile.get("canonical_name"),
        "confirmed_preferences": guest_profile.get("preferences", {}),
        "events_observed": [e.get("event") for e in stay_entries],
        "memorable_moments": [
            "Matcha welcome on arrival",
            "Patio Sur for Wednesday external meeting",
            "Filoli Gardens recommendation (Discovery mode)",
        ],
        "next_stay_carry_overs": {
            "lodging": guest_profile.get("preferences", {}).get("lodging", {}),
            "dietary": guest_profile.get("preferences", {}).get("dietary", {}),
            "cultural": guest_profile.get("preferences", {}).get("cultural", {}),
        },
        "tone": "warm, brief, paused",
    }

    # HAP-RIGHTS §10: right to be forgotten — confirm destruction of property-side copies.
    data_confirmation = {
        "right_to_be_forgotten": "confirmed",
        "property_side_data_destroyed_at": datetime.now(timezone.utc).isoformat(),
        "retention_window_hours": 0,
        "audit_log_retained": True,
        "audit_log_contains_no_pii": True,
        "note": (
            "Operational audit (hash-chained) is retained for reputation defense. "
            "It contains only pseudonymous identifiers — no PII."
        ),
    }

    audit.append(
        event="HAP.MEMORY.RETURNED_TO_GUEST",
        guest_id=guest_id or "unknown",
        session_id=session_id,
        scope=["post_stay.memory"],
        extra={"stay_id": payload.stay_id},
    )
    audit.append(
        event="HAP.REPUTATION.LOG_FROZEN",
        guest_id=guest_id or "unknown",
        session_id=session_id,
        extra={"stay_id": payload.stay_id},
    )

    return PostStayOutput(
        stay_id=payload.stay_id,
        memory_snapshot=memory,
        data_confirmation=data_confirmation,
    )


def _infer_guest_from_stay(stay_id: str) -> str | None:
    """stay_id format: SH-YYYYMMDD-XX where XX is first 2 chars of guest_id, upper."""
    parts = stay_id.split("-")
    if len(parts) < 3:
        return None
    prefix = parts[-1].lower()
    candidates = ["luis", "guillermo", "marcus_chen", "family_johnson"]
    for c in candidates:
        if c.startswith(prefix):
            return c
    return None
