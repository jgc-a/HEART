"""HAP MCP Server entrypoint.

Exposes 5 HAP tools over MCP stdio. Designed to be added to Claude Desktop via
claude_desktop_config.json. Run directly with `python main.py` to launch the
stdio loop (Claude Desktop will spawn this on demand).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Bootstrap sys.path so `server.*` imports resolve when launched directly.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_HERE / ".env")

from mcp.server.fastmcp import FastMCP  # noqa: E402

from server.tools import arrival, dispute, handshake, in_stay, post_stay  # noqa: E402


mcp = FastMCP("hap-rosewood-sand-hill")


@mcp.tool()
def hap_handshake(
    guest_id: str,
    scope_requested: list[str] | None = None,
    ttl_hours: int = 72,
    property_id: str = "rosewood-sand-hill",
) -> dict:
    """Establish a HAP session and return a human-readable Consent Checklist.

    The Guest Agent presents this checklist to the human, who can uncheck
    optional scopes before approval. Returns session_id and a signed consent_token.
    """
    payload = handshake.HandshakeInput(
        guest_id=guest_id,
        scope_requested=scope_requested or [
            "arrival.date_and_flight",
            "preferences.lodging",
            "preferences.dietary",
            "preferences.cultural",
            "calendar.conflicts",
            "health.context",
            "family.signals",
        ],
        ttl_hours=ttl_hours,
        property_id=property_id,
    )
    return handshake.run(payload).model_dump()


@mcp.tool()
def hap_propose_arrival(
    guest_id: str,
    arrival_date: str,
    property_id: str = "rosewood-sand-hill",
    session_id: str | None = None,
) -> dict:
    """Generate the arrival orchestration: staff brief markdown + voice line.

    Classifies the guest's flow profile (Bleisure / Corporate / Family with Minors /
    General) and calls the Concierge Agent (Claude) for a Sense of Place-aware brief.
    """
    payload = arrival.ArrivalInput(
        guest_id=guest_id,
        arrival_date=arrival_date,
        property_id=property_id,
        session_id=session_id,
    )
    return arrival.run(payload).model_dump()


@mcp.tool()
def hap_in_stay_action(
    guest_id: str,
    intent: str,
    context: str = "",
    session_id: str | None = None,
    stay_id: str | None = None,
) -> dict:
    """Handle an in-stay signal. Complaints/maintenance trigger HAP rule 4.1/4.2 escalation.

    Returns a staff brief and a short guest-facing response. When escalation is
    required, the agent is silenced (no autonomous troubleshooting) and humans
    are paged.
    """
    payload = in_stay.InStayInput(
        guest_id=guest_id,
        intent=intent,
        context=context,
        session_id=session_id,
        stay_id=stay_id,
    )
    return in_stay.run(payload).model_dump()


@mcp.tool()
def hap_post_stay_memory(
    stay_id: str,
    guest_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Return a memory snapshot for the Guest Agent (HAP-RIGHTS portability).

    Confirms property-side data destruction. Audit trail (pseudonymous, hash-chained)
    is retained for reputation defense per HAP §10.
    """
    payload = post_stay.PostStayInput(
        stay_id=stay_id,
        guest_id=guest_id,
        session_id=session_id,
    )
    return post_stay.run(payload).model_dump()


@mcp.tool()
def hap_generate_dispute_brief(stay_id: str, review_text: str) -> dict:
    """Generate a WARDEN-signed dispute brief from the hash-chained audit log.

    For the demo: if no audit entries exist for the stay_id, a canned AC-incident
    timeline is seeded into the audit log first so the chain is verifiable.
    """
    payload = dispute.DisputeInput(stay_id=stay_id, review_text=review_text)
    return dispute.run(payload).model_dump()


if __name__ == "__main__":
    # FastMCP defaults to stdio transport when run() is called without args.
    mcp.run()
