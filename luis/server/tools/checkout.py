"""hap_checkout — revoke an active HAP session.

This is what makes the plugin disconnect at checkout. The guest's agent
loses access to the property's HAP tools immediately, and the audit log
records the revocation as a verifiable event.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .. import audit, sessions  # type: ignore[relative-beyond-top-level]


class CheckoutInput(BaseModel):
    session_id: str | None = Field(
        default=None, description="Specific session to revoke. If omitted, revoke all for guest_id."
    )
    guest_id: str | None = Field(
        default=None, description="Revoke every active session for this guest."
    )
    reason: str = Field(default="user_checkout")


class CheckoutOutput(BaseModel):
    revoked: list[str]
    reason: str


def run(payload: CheckoutInput) -> CheckoutOutput:
    revoked_ids: list[str] = []

    if payload.session_id:
        s = sessions.revoke_session(payload.session_id, reason=payload.reason)
        if s:
            revoked_ids.append(s["session_id"])
            audit.append(
                event="HAP.PLUGIN.SESSION_REVOKED",
                guest_id=s.get("guest_id"),
                session_id=s["session_id"],
                scope=[],
                extra={"reason": payload.reason, "client_kind": s.get("client_kind")},
            )
    elif payload.guest_id:
        revoked = sessions.revoke_all_for_guest(payload.guest_id, reason=payload.reason)
        for s in revoked:
            revoked_ids.append(s["session_id"])
            audit.append(
                event="HAP.PLUGIN.SESSION_REVOKED",
                guest_id=s.get("guest_id"),
                session_id=s["session_id"],
                scope=[],
                extra={"reason": payload.reason, "client_kind": s.get("client_kind")},
            )

    return CheckoutOutput(revoked=revoked_ids, reason=payload.reason)
