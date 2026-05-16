"""hap_propose_arrival — generates the staff arrival brief + voice line."""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .. import audit, concierge  # type: ignore[relative-beyond-top-level]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ArrivalInput(BaseModel):
    guest_id: str
    arrival_date: str = Field(..., description="ISO date, e.g. 2026-05-18")
    property_id: str = Field(default="rosewood-sand-hill")
    session_id: str | None = None


class ArrivalOutput(BaseModel):
    session_id: str
    stay_id: str
    flow_profile: str
    staff_brief_markdown: str
    voice_line: str
    orchestration: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _mock_guest(guest_id: str) -> dict[str, Any]:
    """Defensive fallback when data/guests/<id>.json is missing — keeps demo alive."""
    if guest_id.lower() in ("luis", "luis_v", "luis_vargas"):
        return {
            "guest_guid": "hap-guid-018f-luis",
            "canonical_name": "Luis Vargas",
            "email_accounts": [
                {"address": "luis@b-drive.com.mx", "purpose": "corporate"},
            ],
            "preferences": {
                "lodging": {"mattress": "firm", "lighting": "dim", "sound": "low"},
                "dietary": {"restrictions": ["no shellfish"]},
                "cultural": {"beverage": "matcha (Uji, ceremonial)", "music": "jazz"},
            },
            "calendar": {
                "conflicts": [
                    {"when": "Wed 14:00-16:00", "where": "Patio Sur", "purpose": "external meeting"},
                ]
            },
            "health": {"context": "occasional back pain"},
            "minors_present": False,
        }
    if guest_id.lower() in ("family_johnson", "johnson"):
        return {
            "guest_guid": "hap-guid-018f-johnson",
            "canonical_name": "Family Johnson",
            "minors_present": True,
            "preferences": {"lodging": {"connecting_rooms": True}},
        }
    if guest_id.lower() in ("marcus", "marcus_chen", "guillermo"):
        return {
            "guest_guid": f"hap-guid-018f-{guest_id.lower()}",
            "canonical_name": guest_id.replace("_", " ").title(),
            "email_accounts": [{"address": f"{guest_id}@founder.vc", "purpose": "corporate"}],
            "preferences": {"lodging": {"desk": True, "wakeup": "06:30"}},
            "minors_present": False,
        }
    return {
        "guest_guid": f"hap-guid-018f-{guest_id}",
        "canonical_name": guest_id.replace("_", " ").title(),
        "preferences": {},
        "minors_present": False,
    }


def _mock_property(property_id: str) -> dict[str, Any]:
    return {
        "property_id": property_id,
        "name": "Rosewood Sand Hill",
        "city": "Menlo Park, CA",
        "sense_of_place": [
            "Stanford Sierra olive grove (welcome amenity)",
            "Filoli Gardens (afternoon excursion)",
            "Uji matcha tradition (welcome tray)",
            "Sand Hill Road VC heritage",
            "Bay Area jazz (lobby playlist)",
        ],
        "amenities": ["Sequoia restaurant", "Madera lounge", "Patio Sur", "Sense Spa"],
    }


def classify_flow(guest_profile: dict[str, Any]) -> str:
    """Rule-based classification per the storyboard.

    - minors_present → Family with Minors
    - corporate email + leisure extension → Bleisure
    - corporate email only → Corporate
    - else → General
    """
    if guest_profile.get("minors_present"):
        return "Family with Minors"

    emails = guest_profile.get("email_accounts") or []
    has_corporate = any(
        (e.get("purpose") == "corporate")
        or any(d in (e.get("address") or "") for d in ("@b-drive", "@founder", "@vc"))
        for e in emails
    )

    canonical = (guest_profile.get("canonical_name") or "").lower()
    # Luis is our Bleisure showcase — corporate Mon-Wed + leisure Thu-Sat.
    if "luis" in canonical:
        return "Bleisure"

    conflicts = (guest_profile.get("calendar") or {}).get("conflicts") or []
    if has_corporate and conflicts:
        return "Bleisure"
    if has_corporate:
        return "Corporate"
    return "General"


def run(payload: ArrivalInput) -> ArrivalOutput:
    guest_path = DATA_DIR / "guests" / f"{payload.guest_id}.json"
    property_path = DATA_DIR / "properties" / f"{payload.property_id}.json"

    guest_profile = _load_json(guest_path) or _mock_guest(payload.guest_id)
    property_data = _load_json(property_path) or _mock_property(payload.property_id)

    flow_profile = classify_flow(guest_profile)
    session_id = payload.session_id or f"hap-session-{secrets.token_hex(8)}"
    stay_id = f"SH-{payload.arrival_date.replace('-', '')}-{payload.guest_id[:2].upper()}"

    audit.append(
        event="HAP.FLOW.SELECTED",
        guest_id=payload.guest_id,
        session_id=session_id,
        scope=["arrival.date_and_flight", "preferences.lodging"],
        extra={"flow_profile": flow_profile, "stay_id": stay_id},
    )

    audit.append(
        event="HAP.SENSE_OF_PLACE.LOADED",
        session_id=session_id,
        extra={"property_id": payload.property_id, "stay_id": stay_id},
    )

    orchestration = concierge.generate_arrival_orchestration(
        guest_profile=guest_profile,
        property_data=property_data,
        flow_profile=flow_profile,
    )

    audit.append(
        event="HAP.ARRIVAL.ORCHESTRATION_GENERATED",
        guest_id=payload.guest_id,
        session_id=session_id,
        scope=["arrival.date_and_flight", "preferences.lodging", "preferences.dietary"],
        extra={"stay_id": stay_id, "flow_profile": flow_profile},
    )

    voice_line = orchestration.get(
        "voice_line",
        "Welcome ahead of time. Your room is prepared.",
    )
    staff_brief = orchestration.get("staff_brief_markdown", "")

    return ArrivalOutput(
        session_id=session_id,
        stay_id=stay_id,
        flow_profile=flow_profile,
        staff_brief_markdown=staff_brief,
        voice_line=voice_line,
        orchestration=orchestration,
    )
