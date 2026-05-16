"""HAP session tracker — what agents currently have an active session.

A HAP session represents a Guest Agent connected to the property's HAP
server with an authorized scope and a live TTL. Sessions are tracked
here so the dashboard can show "Apps with access" — like an OAuth
consent screen, but live, with hash-chained audit.

This is what makes HAP feel like a plugin: it's connected when there's
an active session, disconnected when the session is revoked or its TTL
expires.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
SESSIONS_FILE = DATA_DIR / "active_sessions.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _load_all() -> list[dict[str, Any]]:
    if not SESSIONS_FILE.exists():
        return []
    try:
        data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _save_all(sessions: list[dict[str, Any]]) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")


def open_session(
    session_id: str,
    guest_id: str,
    scope: list[str],
    ttl_hours: int,
    client_kind: str = "claude",
    client_label: str | None = None,
    guest_display: str | None = None,
) -> dict[str, Any]:
    """Record a freshly-opened HAP session.

    client_kind: 'claude_desktop' | 'claude_code' | 'telegram_bot' | 'web_claude' | 'custom'
    """
    now = _now()
    expires = now + timedelta(hours=ttl_hours)
    record = {
        "session_id": session_id,
        "guest_id": guest_id,
        "guest_display": guest_display or guest_id,
        "scope": scope,
        "client_kind": client_kind,
        "client_label": client_label or client_kind,
        "opened_at_iso": now.isoformat(),
        "ttl_hours": ttl_hours,
        "expires_at_iso": expires.isoformat(),
        "revoked_at_iso": None,
        "checkout_initiated_at_iso": None,
        "active": True,
        "stay_id": None,
    }
    sessions = _load_all()
    # If a session with the same id already exists, replace it.
    sessions = [s for s in sessions if s.get("session_id") != session_id]
    sessions.append(record)
    _save_all(sessions)
    return record


def update_session_stay(session_id: str, stay_id: str) -> None:
    sessions = _load_all()
    for s in sessions:
        if s.get("session_id") == session_id:
            s["stay_id"] = stay_id
    _save_all(sessions)


def revoke_session(session_id: str, reason: str = "user_checkout") -> dict[str, Any] | None:
    sessions = _load_all()
    revoked: dict[str, Any] | None = None
    for s in sessions:
        if s.get("session_id") == session_id and s.get("active"):
            s["active"] = False
            s["revoked_at_iso"] = _now_iso()
            s["revoked_reason"] = reason
            revoked = s
    _save_all(sessions)
    return revoked


def revoke_all_for_guest(guest_id: str, reason: str = "user_checkout") -> list[dict[str, Any]]:
    sessions = _load_all()
    revoked: list[dict[str, Any]] = []
    for s in sessions:
        if s.get("guest_id") == guest_id and s.get("active"):
            s["active"] = False
            s["revoked_at_iso"] = _now_iso()
            s["revoked_reason"] = reason
            revoked.append(s)
    _save_all(sessions)
    return revoked


def mark_checkout_initiated(session_id: str) -> None:
    sessions = _load_all()
    for s in sessions:
        if s.get("session_id") == session_id:
            s["checkout_initiated_at_iso"] = _now_iso()
    _save_all(sessions)


def expire_due_sessions() -> list[dict[str, Any]]:
    """Auto-revoke any session whose TTL passed."""
    sessions = _load_all()
    now_iso = _now_iso()
    expired: list[dict[str, Any]] = []
    for s in sessions:
        if s.get("active") and s.get("expires_at_iso") and s["expires_at_iso"] < now_iso:
            s["active"] = False
            s["revoked_at_iso"] = now_iso
            s["revoked_reason"] = "ttl_expired"
            expired.append(s)
    if expired:
        _save_all(sessions)
    return expired


def list_active() -> list[dict[str, Any]]:
    expire_due_sessions()
    return [s for s in _load_all() if s.get("active")]


def list_all(limit: int = 50) -> list[dict[str, Any]]:
    sessions = _load_all()
    sessions.sort(key=lambda s: s.get("opened_at_iso", ""), reverse=True)
    return sessions[:limit]
