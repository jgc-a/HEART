"""hap_handshake — establishes a HAP session with a scope-based Consent Checklist."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from .. import audit  # type: ignore[relative-beyond-top-level]


class HandshakeInput(BaseModel):
    guest_id: str = Field(..., description="Local guest identifier (e.g. 'luis', 'guillermo').")
    scope_requested: list[str] = Field(
        default_factory=lambda: [
            "arrival.date_and_flight",
            "preferences.lodging",
            "preferences.dietary",
            "preferences.cultural",
            "calendar.conflicts",
            "health.context",
            "family.signals",
        ],
        description="HAP scopes the Guest Agent wishes to share.",
    )
    ttl_hours: int = Field(default=72, ge=1, le=720)
    property_id: str = Field(default="rosewood-sand-hill")


class HandshakeOutput(BaseModel):
    session_id: str
    scope_granted: list[str]
    ttl_expires_at: str
    consent_token: str
    audit_url: str
    consent_checklist_markdown: str


# Scope metadata for the Consent Checklist rendering.
SCOPE_LABELS: dict[str, dict[str, Any]] = {
    "arrival.date_and_flight": {
        "label": "Arrival date & flight",
        "detail": "TTL: until check-out",
        "optional": False,
    },
    "preferences.lodging": {
        "label": "Lodging preferences",
        "detail": "firm mattress, dim lighting",
        "optional": False,
    },
    "calendar.conflicts": {
        "label": "Calendar conflicts",
        "detail": "block patio Wed 2-4pm",
        "optional": False,
    },
    "preferences.dietary": {
        "label": "Dietary restrictions",
        "detail": "no shellfish",
        "optional": False,
    },
    "health.context": {
        "label": "Health context",
        "detail": "back pain — optional",
        "optional": True,
    },
    "preferences.cultural": {
        "label": "Cultural preferences",
        "detail": "matcha tea, jazz",
        "optional": False,
    },
    "family.signals": {
        "label": "Family signals",
        "detail": "not relevant this trip",
        "optional": True,
    },
    "preferences.wellness": {
        "label": "Wellness preferences",
        "detail": "spa, sleep",
        "optional": True,
    },
    "billing.method": {
        "label": "Billing method",
        "detail": "required for check-in",
        "optional": False,
    },
    "loyalty.programs": {
        "label": "Loyalty programs",
        "detail": "Rosewood Elite",
        "optional": True,
    },
}


def _signing_secret() -> bytes:
    return os.environ.get(
        "HAP_SIGNING_SECRET",
        "rosewood-heart-warden-demo-secret-do-not-use-in-prod",
    ).encode("utf-8")


def _mint_consent_token(session_id: str, guest_id: str, scope: list[str], expires_at: str) -> str:
    """JWT-shaped HMAC token (no real JWT lib needed for demo)."""
    payload = json.dumps(
        {"sid": session_id, "gid": guest_id, "scp": scope, "exp": expires_at},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    sig = hmac.new(_signing_secret(), payload, hashlib.sha256).hexdigest()
    return f"hap_ct_{sig[:32]}.{secrets.token_hex(8)}"


def _build_checklist(scope_requested: list[str], property_id: str) -> str:
    property_title = property_id.replace("-", " ").title()
    if not property_title.lower().startswith("rosewood"):
        property_title = f"Rosewood {property_title}"
    lines = [
        f"## {property_title} is requesting authorization.",
        "",
        "**What I can share with the hotel:**",
        "",
    ]
    # Preserve order requested, fall back to label dict ordering for any unknown scope.
    seen: set[str] = set()
    for s in scope_requested:
        seen.add(s)
        meta = SCOPE_LABELS.get(s, {"label": s, "detail": "", "optional": False})
        # Default state: optional scopes start unchecked, required scopes start checked.
        check = "☐" if meta["optional"] else "☑"
        detail = f" ({meta['detail']})" if meta.get("detail") else ""
        lines.append(f"  {check} {meta['label']}{detail}")
    lines.extend(
        [
            "",
            "[Approve & Send] [Customize] [Cancel]",
            "",
            "_Zero retention. Revocable at any time. Audit trail visible to you._",
        ]
    )
    return "\n".join(lines)


def run(payload: HandshakeInput) -> HandshakeOutput:
    session_id = f"hap-session-{secrets.token_hex(8)}"
    expires = datetime.now(timezone.utc) + timedelta(hours=payload.ttl_hours)
    expires_iso = expires.isoformat()

    # For the demo: grant everything except optional health/family scopes by default.
    scope_granted = [
        s for s in payload.scope_requested if not SCOPE_LABELS.get(s, {}).get("optional", False)
    ]

    consent_token = _mint_consent_token(
        session_id=session_id,
        guest_id=payload.guest_id,
        scope=scope_granted,
        expires_at=expires_iso,
    )

    audit.append(
        event="HAP.HANDSHAKE.RECEIVED",
        guest_id=payload.guest_id,
        session_id=session_id,
        scope=payload.scope_requested,
        extra={
            "property_id": payload.property_id,
            "ttl_hours": payload.ttl_hours,
            "scope_granted": scope_granted,
        },
    )

    checklist = _build_checklist(payload.scope_requested, payload.property_id)
    audit_url = f"https://heart.rosewood/audit/{session_id}"

    return HandshakeOutput(
        session_id=session_id,
        scope_granted=scope_granted,
        ttl_expires_at=expires_iso,
        consent_token=consent_token,
        audit_url=audit_url,
        consent_checklist_markdown=checklist,
    )
