"""guest.md — portable, agent-readable memory owned by the GUEST.

This is the inverse of a CRM. CRMs are owned by the company. guest.md is
owned by the traveler. Hotels query on demand within authorized scope;
they never store. The file lives with the guest's agent (Claude, ChatGPT,
Gemini) and is refined after each stay.

Why this matters:
- Portable: same guest.md travels between Rosewood, Aman, Belmond.
- Compounding: every stay refines confidence and adds memorable moments.
- Multi-modal: a single guest.md contains several trip_modes (business,
  leisure, anniversary, wellness, family) — each with its own
  interaction intensity and channel preferences.
- Auditable: history of refinements is kept so the guest can see exactly
  what their agent learned and when.

Public API:
    generate_guest_md(profile, history=[]) -> str
    save_guest_md(chat_id, md) -> Path
    read_guest_md(chat_id) -> str | None
    derive_trip_modes(profile, history) -> list[dict]
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
MEMORY_DIR = DATA_DIR / "guest_memories"
FLOW_CONFIG = DATA_DIR / "flow_profiles_config.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_flow_config() -> dict[str, Any]:
    if not FLOW_CONFIG.exists():
        return {}
    try:
        return json.loads(FLOW_CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _md_section(title: str, body: str | list[str]) -> str:
    if isinstance(body, list):
        if not body:
            return ""
        body = "\n".join(f"- {item}" for item in body)
    return f"## {title}\n{body}\n"


def derive_trip_modes(profile: dict[str, Any], history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer up to 4 distinct trip modes from the profile + history.

    A trip mode bundles: a flow profile, an interaction intensity, preferred
    channels, an alert cap, and quiet hours. Each one is what the guest
    agent reaches for when planning a different KIND of trip.
    """
    flow_cfg = _load_flow_config()
    purpose = (profile.get("visit_purpose") or "").lower()

    modes: list[dict[str, Any]] = []

    # Mode 1 — derived from the current profile
    current_flow = None
    if "business" in purpose or "corp" in purpose or "vc" in purpose:
        current_flow = "Bleisure" if "leisure" in purpose or "weekend" in purpose else "Corporate"
    elif "anniversary" in purpose or "honeymoon" in purpose or "birthday" in purpose:
        current_flow = "Special Dates"
    elif "wellness" in purpose or "recovery" in purpose or "spa" in purpose or "retreat" in purpose:
        current_flow = "Wellness / Recovery"
    elif "family" in purpose or "kids" in purpose or "children" in purpose:
        current_flow = "Family with Minors"
    elif "founder" in purpose or "investor" in purpose:
        current_flow = "Corporate"
    else:
        current_flow = "General"

    def mode_from_flow(flow_name: str, label: str, when: str) -> dict[str, Any]:
        cfg = flow_cfg.get(flow_name, {})
        return {
            "label": label,
            "when_to_use": when,
            "flow": flow_name,
            "interaction_intensity": cfg.get("interaction_intensity", "standard"),
            "channels_preferred": cfg.get("channels_preferred", ["email"]),
            "channels_avoided": cfg.get("channels_avoided", []),
            "alert_cap_per_day": cfg.get("alert_cap_per_day", 3),
            "quiet_hours_local": cfg.get("quiet_hours_local", ["22:00", "07:00"]),
            "proactive_offers": cfg.get("proactive_offers", "selective"),
            "upsell_allowed": cfg.get("upsell_allowed", True),
            "human_required": cfg.get("human_required", []),
        }

    modes.append(
        mode_from_flow(
            current_flow,
            f"This-trip mode — {current_flow}",
            "Detected from current visit purpose",
        )
    )

    # Mode 2 — leisure inverse (always offer the leisure counterpart)
    if current_flow == "Corporate":
        modes.append(
            mode_from_flow(
                "Bleisure",
                "When I extend into the weekend",
                "Use when business trips have a leisure tail",
            )
        )
    elif current_flow == "Bleisure":
        modes.append(
            mode_from_flow(
                "Corporate",
                "When the trip is strictly business",
                "Use for back-to-back meeting trips with no leisure window",
            )
        )

    # Mode 3 — wellness (always present as escape hatch)
    if current_flow != "Wellness / Recovery":
        modes.append(
            mode_from_flow(
                "Wellness / Recovery",
                "Wellness retreat mode",
                "Use when the trip is recovery, sabbatical, or burnout-recovery",
            )
        )

    # Mode 4 — Special Dates if not already covered
    if current_flow != "Special Dates":
        modes.append(
            mode_from_flow(
                "Special Dates",
                "Anniversary / Honeymoon / Birthday",
                "Use when a significant date drives the trip",
            )
        )

    return modes


def _confidence_for(label: str, count: int) -> str:
    if count >= 3:
        return f"high (confirmed in {count} stays)"
    if count == 2:
        return f"medium (2 stays)"
    return f"observed once"


def generate_guest_md(
    profile: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    persona_id: str | None = None,
    last_stay: dict[str, Any] | None = None,
) -> str:
    """Render the guest's portable memory file as markdown.

    `profile` is the live profile from guest_agent (live_profiles/<chat_id>.json
    or a freshly-loaded preloaded persona).
    `history` is a list of past stay records (for trip-mode inference and
    confidence scoring) — pass [] if none yet.
    """
    history = history or []
    flow_cfg = _load_flow_config()
    modes = derive_trip_modes(profile, history)

    name = profile.get("display_name") or profile.get("canonical_name") or "Guest"
    purpose = profile.get("visit_purpose") or "(none)"
    origin = profile.get("agent_memory_origin") or "agent live memory"

    stays_observed = len(history) + 1  # +1 for this stay
    last_stay_line = ""
    if last_stay:
        last_stay_line = (
            f"- Last stay: {last_stay.get('property_name','Rosewood Sand Hill')} · "
            f"{last_stay.get('stay_id','')} · flow={last_stay.get('flow_profile','')}\n"
        )

    out: list[str] = []

    # ---- header ----
    out.append(f"# Guest Memory · {name}\n")
    out.append(
        "> Portable, agent-readable. **Owned by the guest, not the property.**\n"
        "> Schema: `hap-guest-memory/v0.1`\n"
        "> This file is read by your AI agent (Claude, ChatGPT, Gemini, …) when\n"
        "> initiating a HAP handshake with any HAP-compliant property.\n"
    )

    # ---- identity ----
    out.append(
        _md_section(
            "Identity",
            [
                f"display_name: {name}",
                f"persona_id: {persona_id or 'derived from live profile'}",
                f"refined_at: {_now_iso()}",
                f"refined_by: claude-sonnet-4-5 (agent-side)",
                f"stays_observed: {stays_observed}",
            ],
        )
    )

    if last_stay_line:
        out.append(_md_section("Last Refinement", last_stay_line.strip()))

    # ---- stable preferences ----
    out.append(
        _md_section(
            "Lodging Preferences",
            [
                f"{item}  · {_confidence_for(item, 1)}"
                for item in (profile.get("lodging") or [])
            ]
            or ["(no lodging preferences captured yet)"],
        )
    )

    out.append(
        _md_section(
            "Dietary",
            [
                f"{item}  · {_confidence_for(item, 1)}"
                for item in (profile.get("dietary") or [])
            ]
            or ["(no dietary preferences captured yet)"],
        )
    )

    out.append(
        _md_section(
            "Cultural / Beverages",
            [
                f"{item}  · {_confidence_for(item, 1)}"
                for item in (profile.get("cultural") or [])
            ]
            or ["(no cultural preferences captured yet)"],
        )
    )

    if profile.get("wellness"):
        out.append(
            _md_section(
                "Wellness (opt-in)",
                [
                    f"{item}  · sensitive — only share when explicitly authorized"
                    for item in profile["wellness"]
                ],
            )
        )

    # ---- trip modes ----
    out.append("## Trip Modes\n")
    out.append(
        "Each mode bundles a flow profile, an interaction intensity, channel\n"
        "preferences, and an alert cap. Your agent picks the right mode at\n"
        "handshake time. Hotels respect them per HAP §6 (events) and §10 (rights).\n"
    )
    for i, m in enumerate(modes, 1):
        channels_pref = ", ".join(m["channels_preferred"]) or "(none)"
        channels_avoid = ", ".join(m["channels_avoided"]) or "(none)"
        quiet = (
            f"{m['quiet_hours_local'][0]}–{m['quiet_hours_local'][1]} local"
            if m.get("quiet_hours_local")
            else "(none)"
        )
        humans = ", ".join(m["human_required"]) if m["human_required"] else "(none)"
        out.append(
            f"### Mode {i} · {m['label']}\n"
            f"- when_to_use: {m['when_to_use']}\n"
            f"- flow: `{m['flow']}`\n"
            f"- interaction_intensity: **{m['interaction_intensity']}**\n"
            f"- alert_cap_per_day: {m['alert_cap_per_day']}\n"
            f"- channels_preferred: {channels_pref}\n"
            f"- channels_avoided: {channels_avoid}\n"
            f"- quiet_hours: {quiet}\n"
            f"- proactive_offers: {m['proactive_offers']}\n"
            f"- upsell_allowed: {m['upsell_allowed']}\n"
            f"- human_required_for: {humans}\n"
        )

    # ---- behavioral rules ----
    out.append(
        _md_section(
            "Don't",
            [
                "Don't push room service after the active mode's quiet hours.",
                "Don't recommend events on Wednesday afternoons (always blocked).",
                "Don't suggest items in dietary restrictions, ever.",
                "Don't share wellness or health context unless the active mode authorizes it.",
            ],
        )
    )

    if profile.get("notes"):
        out.append(_md_section("Agent notes (free text)", profile["notes"]))

    # ---- HAP trust ----
    out.append(
        _md_section(
            "HAP Trust History",
            [
                f"{stays_observed} HAP-compliant stay{'s' if stays_observed != 1 else ''} on record",
                "All handshakes signed with HMAC-SHA256",
                "Hash-chained audit · verification available at /audit",
                "Right-to-revoke at any time per HAP §10",
            ],
        )
    )

    # ---- ownership ----
    out.append(
        "---\n\n"
        "**This file is owned by the guest.** Hotels query it on demand within authorized\n"
        "scope. They cannot store it, copy it, or retain any field beyond the HAP TTL.\n"
        "If a hotel attempts to persist guest data, the audit chain captures the violation\n"
        "and the guest can revoke all future access.\n"
    )

    return "".join(out).strip() + "\n"


def save_guest_md(chat_id: int, md: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / f"{chat_id}.md"
    path.write_text(md, encoding="utf-8")
    return path


def read_guest_md(chat_id: int) -> str | None:
    path = MEMORY_DIR / f"{chat_id}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def list_memories() -> list[dict[str, Any]]:
    """List every guest memory file with a small preview for the dashboard."""
    if not MEMORY_DIR.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(MEMORY_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            md = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Pull the H1 (Guest Memory · <name>) as title
        first_line = md.splitlines()[0] if md else ""
        title = first_line.removeprefix("# ").strip() or path.stem
        out.append(
            {
                "chat_id": int(path.stem) if path.stem.isdigit() else None,
                "title": title,
                "updated_at_iso": datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "size_bytes": path.stat().st_size,
                "filename": path.name,
                "markdown": md,
            }
        )
    return out
