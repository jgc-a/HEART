"""CLI fallback that exercises all 5 HAP tools end-to-end without MCP.

Plan B for the pitch if Claude Desktop / MCP transport fails.
Run: `python demo_runner.py`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_HERE / ".env")

from server.tools import arrival, dispute, handshake, in_stay, post_stay  # noqa: E402


SEP = "=" * 72
SUB = "-" * 72


def hr(title: str) -> None:
    print()
    print(SEP)
    print(f"  {title}")
    print(SEP)


def sub(title: str) -> None:
    print()
    print(SUB)
    print(f"  {title}")
    print(SUB)


def pp(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main() -> int:
    hr("HAP DEMO RUNNER — HEART (Rosewood Sand Hill)")
    print("This exercises the 5 HAP tools end-to-end. No MCP transport required.")
    print("Output mirrors what Claude Desktop would receive.")

    # 1. HANDSHAKE
    hr("1. hap_handshake — Consent Checklist")
    h_out = handshake.run(
        handshake.HandshakeInput(
            guest_id="luis",
            scope_requested=[
                "arrival.date_and_flight",
                "preferences.lodging",
                "calendar.conflicts",
                "preferences.dietary",
                "health.context",
                "preferences.cultural",
                "family.signals",
            ],
            ttl_hours=72,
        )
    )
    print(h_out.consent_checklist_markdown)
    sub("session details")
    print(f"session_id     : {h_out.session_id}")
    print(f"scope_granted  : {h_out.scope_granted}")
    print(f"expires_at     : {h_out.ttl_expires_at}")
    print(f"consent_token  : {h_out.consent_token}")
    print(f"audit_url      : {h_out.audit_url}")

    # 2. PROPOSE ARRIVAL
    hr("2. hap_propose_arrival — Staff Brief + Voice Line")
    a_out = arrival.run(
        arrival.ArrivalInput(
            guest_id="luis",
            arrival_date="2026-05-18",
            session_id=h_out.session_id,
        )
    )
    print(f"flow_profile : {a_out.flow_profile}")
    print(f"stay_id      : {a_out.stay_id}")
    sub("staff brief (markdown)")
    print(a_out.staff_brief_markdown)
    sub("voice line (ElevenLabs)")
    print(f'"{a_out.voice_line}"')

    # 3. IN-STAY — COMPLAINT (triggers escalation)
    hr("3. hap_in_stay_action — AC complaint (triggers HAP-RULE 4.1 + 4.2)")
    is_out = in_stay.run(
        in_stay.InStayInput(
            guest_id="luis",
            intent="complaint",
            context="The AC is broken, the room is too hot.",
            session_id=h_out.session_id,
            stay_id=a_out.stay_id,
        )
    )
    print(f"event              : {is_out.hap_event}")
    print(f"escalation         : {is_out.escalation_required}")
    print(f"escalation_targets : {is_out.escalation_targets}")
    sub("staff brief")
    print(is_out.staff_brief)
    sub("guest response")
    print(is_out.guest_response)

    # 4. POST-STAY MEMORY
    hr("4. hap_post_stay_memory — Memory Snapshot (HAP-RIGHTS portability)")
    ps_out = post_stay.run(
        post_stay.PostStayInput(
            stay_id=a_out.stay_id,
            guest_id="luis",
            session_id=h_out.session_id,
        )
    )
    sub("memory snapshot")
    pp(ps_out.memory_snapshot)
    sub("data confirmation (right to be forgotten)")
    pp(ps_out.data_confirmation)

    # 5. DISPUTE BRIEF
    hr("5. hap_generate_dispute_brief — Reputation Defense (WARDEN-signed)")
    d_out = dispute.run(
        dispute.DisputeInput(
            stay_id=a_out.stay_id,
            review_text=(
                "Stayed at Rosewood Sand Hill — terrible AC, took forever to fix. "
                "Worst service. Will not return. — @anonguest_72"
            ),
        )
    )
    print(d_out.brief_markdown)
    sub("signature")
    print(f"signer            : {d_out.signer}")
    print(f"signed_at         : {d_out.signed_at}")
    print(f"signature (sha256): {d_out.signature}")
    print(f"audit entries used: {d_out.audit_entries_used}")

    hr("DEMO COMPLETE")
    print("Audit log: server/audit.jsonl")
    print("All 5 tools exercised. Plan B is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
