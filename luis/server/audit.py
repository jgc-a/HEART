"""Append-only JSONL audit log with sha256 hash chaining.

Every entry includes prev_hash and hash so the chain is tamper-evident.
The dispute brief tool reads this file to reconstruct timelines.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).parent / "audit.jsonl"
GENESIS_HASH = "0" * 64


def _hash_entry(entry: dict[str, Any]) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _last_hash() -> str:
    if not AUDIT_PATH.exists():
        return GENESIS_HASH
    last = GENESIS_HASH
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                last = rec.get("hash", last)
            except json.JSONDecodeError:
                continue
    return last


def anon_guid(guest_id: str) -> str:
    """Pseudonymize a guest_id for the audit log (zero-retention story)."""
    digest = hashlib.sha256(f"hap-anon::{guest_id}".encode("utf-8")).hexdigest()
    return f"anon-{digest[:16]}"


def append(
    event: str,
    guest_id: str | None = None,
    session_id: str | None = None,
    scope: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a hash-chained entry and return it.

    Side effects: writes one line to audit.jsonl. Idempotent across runs.
    """
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev = _last_hash()
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "guest_guid": anon_guid(guest_id) if guest_id else None,
        "session_id": session_id,
        "scope": scope or [],
        "prev_hash": prev,
    }
    if extra:
        entry["extra"] = extra
    entry["hash"] = _hash_entry({k: v for k, v in entry.items() if k != "hash"})

    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read_for_session(session_id: str) -> list[dict[str, Any]]:
    if not AUDIT_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("session_id") == session_id:
                    out.append(rec)
            except json.JSONDecodeError:
                continue
    return out


def read_for_stay(stay_id: str) -> list[dict[str, Any]]:
    """Read all entries whose extra.stay_id matches."""
    if not AUDIT_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if (rec.get("extra") or {}).get("stay_id") == stay_id:
                    out.append(rec)
            except json.JSONDecodeError:
                continue
    return out


def verify_chain() -> bool:
    """Recompute the chain and confirm no tampering."""
    if not AUDIT_PATH.exists():
        return True
    prev = GENESIS_HASH
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("prev_hash") != prev:
                return False
            recomputed = _hash_entry({k: v for k, v in rec.items() if k != "hash"})
            if recomputed != rec.get("hash"):
                return False
            prev = rec["hash"]
    return True
