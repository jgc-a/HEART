"""hap_in_stay_action — staff brief generator and escalation router."""
from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .. import audit, concierge  # type: ignore[relative-beyond-top-level]
from .arrival import _load_json, _mock_guest  # reuse loaders  # type: ignore[relative-beyond-top-level]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


COMPLAINT_KEYWORDS = (
    "complaint",
    "complain",
    "broken",
    "terrible",
    "worst",
    "awful",
    "freezing",
    "too hot",
    "too cold",
    "noise",
    "disappointed",
    "queja",
)

MAINTENANCE_KEYWORDS = (
    "maintenance",
    "ac ",
    "a/c",
    "air conditioning",
    "leak",
    "wifi",
    "tv broken",
    "tv won't",
    "shower",
    "plumbing",
    "light not",
    "door won't",
    "mantenimiento",
)


class InStayInput(BaseModel):
    guest_id: str
    intent: str = Field(..., description="High-level intent label or free text describing what the guest wants.")
    context: str = Field(default="", description="Free-text detail / verbatim message from the guest.")
    session_id: str | None = None
    stay_id: str | None = None


class InStayOutput(BaseModel):
    session_id: str
    intent: str
    escalation_required: bool
    escalation_targets: list[str]
    staff_brief: str
    guest_response: str
    hap_event: str


def _matches(text: str, needles: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(n in low for n in needles)


def run(payload: InStayInput) -> InStayOutput:
    session_id = payload.session_id or f"hap-session-{secrets.token_hex(8)}"
    stay_id = payload.stay_id

    combined = f"{payload.intent} {payload.context}"
    is_complaint = _matches(combined, COMPLAINT_KEYWORDS)
    is_maintenance = _matches(combined, MAINTENANCE_KEYWORDS)

    if is_complaint or is_maintenance:
        # HAP rule 4.1 / 4.2: silence the agent, dual escalation, no autonomous troubleshooting.
        # Complaint takes precedence: complaint language means silence first, regardless of cause.
        targets: list[str] = []
        rules: list[str] = []
        if is_complaint:
            targets.extend(["Duty Manager", "Guest Relations"])
            rules.append("HAP-RULE 4.1 (dual human escalation)")
        if is_maintenance:
            targets.append("Engineering")
            rules.append("HAP-RULE 4.2 (engineering, no autonomous troubleshooting)")
        rule = " + ".join(rules)
        event = (
            "HAP.IN_STAY.COMPLAINT_ESCALATED"
            if is_complaint
            else "HAP.IN_STAY.MAINTENANCE_REPORTED"
        )

        # Dedupe while preserving order.
        seen: set[str] = set()
        targets = [t for t in targets if not (t in seen or seen.add(t))]

        staff_brief = (
            f"### ESCALATION — {rule}\n\n"
            f"Guest: `{payload.guest_id}`\n"
            f"Intent: {payload.intent}\n"
            f"Context: {payload.context}\n\n"
            f"**Paged:** {', '.join(targets)}\n"
            "Agent silenced. No autonomous resolution. Awaiting human."
        )
        guest_response = (
            "We're on it. A member of our team is on the way. "
            "Thank you for letting us know."
        )

        audit.append(
            event=event,
            guest_id=payload.guest_id,
            session_id=session_id,
            scope=["in_stay.signal"],
            extra={
                "intent": payload.intent,
                "context": payload.context,
                "escalation_targets": targets,
                "rule": rule,
                "stay_id": stay_id,
            },
        )

        return InStayOutput(
            session_id=session_id,
            intent=payload.intent,
            escalation_required=True,
            escalation_targets=targets,
            staff_brief=staff_brief,
            guest_response=guest_response,
            hap_event=event,
        )

    # Non-escalation: generate a proactive offer via the concierge.
    guest_path = DATA_DIR / "guests" / f"{payload.guest_id}.json"
    guest_profile: dict[str, Any] = _load_json(guest_path) or _mock_guest(payload.guest_id)

    result = concierge.generate_in_stay_response(
        guest_profile=guest_profile,
        intent=payload.intent,
        context=payload.context,
    )

    audit.append(
        event="HAP.IN_STAY.PROACTIVE_OFFER",
        guest_id=payload.guest_id,
        session_id=session_id,
        scope=["in_stay.signal"],
        extra={"intent": payload.intent, "stay_id": stay_id},
    )

    return InStayOutput(
        session_id=session_id,
        intent=payload.intent,
        escalation_required=False,
        escalation_targets=[],
        staff_brief=result.get("staff_brief", ""),
        guest_response=result.get("guest_response", ""),
        hap_event="HAP.IN_STAY.PROACTIVE_OFFER",
    )
