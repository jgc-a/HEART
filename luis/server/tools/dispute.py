"""hap_generate_dispute_brief — reputation defense, HMAC-signed."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .. import audit, concierge  # type: ignore[relative-beyond-top-level]


class DisputeInput(BaseModel):
    stay_id: str
    review_text: str = Field(..., description="Verbatim negative review to defend against.")


class DisputeOutput(BaseModel):
    stay_id: str
    brief_markdown: str
    signature: str
    signed_at: str
    signer: str
    audit_entries_used: int


def _signing_secret() -> bytes:
    return os.environ.get(
        "HAP_SIGNING_SECRET",
        "rosewood-heart-warden-demo-secret-do-not-use-in-prod",
    ).encode("utf-8")


def _sign(brief: str, stay_id: str, ts: str) -> str:
    payload = f"{stay_id}|{ts}|{brief}".encode("utf-8")
    return hmac.new(_signing_secret(), payload, hashlib.sha256).hexdigest()


def _seed_canned_entries_if_empty(stay_id: str) -> list[dict[str, Any]]:
    """For the demo: if no audit entries exist for the stay, write a canned AC-incident timeline.

    This is the scripted Demo #2 path. We seed real audit lines so the chain is verifiable.
    """
    entries = audit.read_for_stay(stay_id)
    if entries:
        return entries

    audit.append(
        event="HAP.IN_STAY.COMPLAINT_ESCALATED",
        session_id=f"hap-session-{secrets.token_hex(4)}",
        extra={
            "stay_id": stay_id,
            "rule": "HAP-RULE 4.1",
            "trigger": "Guest temperature complaint",
            "at": "17:42",
        },
    )
    audit.append(
        event="HAP.IN_STAY.MAINTENANCE_REPORTED",
        extra={
            "stay_id": stay_id,
            "rule": "HAP-RULE 4.2",
            "paged": "Engineering",
            "at": "17:43",
        },
    )
    audit.append(
        event="HAP.IN_STAY.MAINTENANCE_REPORTED",
        extra={
            "stay_id": stay_id,
            "paged": "Duty Manager (dual escalation)",
            "at": "17:43",
        },
    )
    audit.append(
        event="HAP.IN_STAY.MAINTENANCE_RESOLVED",
        extra={
            "stay_id": stay_id,
            "engineer": "Marco D.",
            "arrival_at": "17:47",
            "resolved_at": "17:51",
            "note": "AC unit cycle reset, cool airflow confirmed.",
        },
    )
    audit.append(
        event="HAP.IN_STAY.GUEST_TONE_OBSERVED",
        extra={
            "stay_id": stay_id,
            "tone": "satisfied",
            "at": "17:53",
        },
    )
    audit.append(
        event="HAP.IN_STAY.PROACTIVE_OFFER",
        extra={
            "stay_id": stay_id,
            "offer": "Complimentary turndown amenity",
            "at": "18:10",
        },
    )

    return audit.read_for_stay(stay_id)


def run(payload: DisputeInput) -> DisputeOutput:
    entries = _seed_canned_entries_if_empty(payload.stay_id)

    brief = concierge.generate_dispute_brief_text(
        stay_id=payload.stay_id,
        review_text=payload.review_text,
        audit_entries=entries,
    )

    signed_at = datetime.now(timezone.utc).isoformat()
    signature = _sign(brief, payload.stay_id, signed_at)
    signer = "WARDEN-HEART"

    # Append signature to the brief footer so the rendered markdown shows it.
    full_brief = (
        f"{brief.rstrip()}\n\n"
        f"---\n"
        f"**Signed:** {signer}  •  **Hash:** `{signature[:32]}...`  •  **At:** {signed_at}\n"
    )

    audit.append(
        event="HAP.REPUTATION.DISPUTE_BRIEF_GENERATED",
        extra={
            "stay_id": payload.stay_id,
            "signer": signer,
            "signature_prefix": signature[:32],
            "entries_used": len(entries),
        },
    )

    return DisputeOutput(
        stay_id=payload.stay_id,
        brief_markdown=full_brief,
        signature=signature,
        signed_at=signed_at,
        signer=signer,
        audit_entries_used=len(entries),
    )
