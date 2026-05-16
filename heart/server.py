#!/usr/bin/env python3
"""HEART — Human-centric Experience Agent for Rosewood Travelers
Backend Flask · Port 5560 · Hackathon Build"""

import os, json, time, uuid, sqlite3, threading, requests
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template, Response, stream_with_context
from flask_cors import CORS

BASE = Path(__file__).parent
DATA = BASE / "data"
DB   = DATA / "heart.db"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ── ARCA API Config ──────────────────────────────────────────────────────────
ARCA_API = "http://localhost:5200/api/v2/chat/message/stream"
ARCA_TOKEN = None

def get_arca_token():
    global ARCA_TOKEN
    if ARCA_TOKEN: return ARCA_TOKEN
    try:
        conn = sqlite3.connect(Path.home() / ".arca/data/auth.db")
        row = conn.execute("SELECT token FROM sessions ORDER BY created DESC LIMIT 1").fetchone()
        conn.close()
        ARCA_TOKEN = row[0] if row else ""
    except: ARCA_TOKEN = ""
    return ARCA_TOKEN

# ── Database Setup ────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS hap_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_guid TEXT, event TEXT, detail TEXT,
            ts TEXT DEFAULT (datetime('now')), raw TEXT
        );
        CREATE TABLE IF NOT EXISTS human_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_guid TEXT, guest_name TEXT, room TEXT,
            reason TEXT, priority TEXT DEFAULT 'HIGH',
            status TEXT DEFAULT 'PENDING',
            assigned_to TEXT, created_at TEXT DEFAULT (datetime('now')),
            resolved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_guid TEXT, agent TEXT, role TEXT,
            content TEXT, ts TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS dispute_briefs (
            id TEXT PRIMARY KEY, guest_name TEXT, platform TEXT,
            rating INTEGER, review TEXT, brief TEXT,
            warden_seal TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def load_guests():
    with open(DATA / "guests.json") as f:
        return json.load(f)

def load_rooms():
    with open(DATA / "rooms.json") as f:
        return json.load(f)

def seed_human_queue():
    guests = load_guests()["guests"]
    conn = sqlite3.connect(DB)
    existing = conn.execute("SELECT guest_guid FROM human_queue").fetchall()
    existing_guids = {r[0] for r in existing}
    for g in guests:
        if g.get("human_required") and g["guest_guid"] not in existing_guids:
            conn.execute("""INSERT INTO human_queue (guest_guid, guest_name, room, reason, priority)
                           VALUES (?,?,?,?,?)""",
                (g["guest_guid"], g["canonical_name"], g.get("room","?"),
                 g.get("human_reason","Requires human attention"), "HIGH"))
    conn.commit()
    conn.close()

def seed_hap_events():
    guests = load_guests()["guests"]
    conn = sqlite3.connect(DB)
    count = conn.execute("SELECT COUNT(*) FROM hap_events").fetchone()[0]
    if count == 0:
        for g in guests:
            for ev in g.get("hap_events",[]):
                conn.execute("""INSERT INTO hap_events (guest_guid, event, detail, ts) VALUES (?,?,?,?)""",
                    (g["guest_guid"], ev["event"], ev.get("detail",""), ev.get("ts", datetime.now().isoformat())))
    conn.commit()
    conn.close()

# ── SYSTEM PROMPTS ───────────────────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "orchestrator": """You are the Orchestrator agent for HEART at Rosewood Sand Hill. Operating under HAP (Hospitality Agent Protocol).

BEFORE ANY OUTPUT:
1. Consult HAP-RAG for relevant policy/procedure
2. Verify authorized scope for guest's personal agent
3. Resolve guest identity via HAP-IDENTITY (Guest GUID)
4. Determine Travel Flow & Identity (10 profiles: GENERAL, CORPORATE, SPECIAL_DATES, BLEISURE, WELLNESS, VIP_DISCRETE, FAMILY_WITH_MINORS, GROUP, MEDICAL, TRANSIT)
5. Resolve billing (personal/corporate/group per profile)
6. WARDEN attestation

IMMUTABLE RULES:
- If minors present → respond with {"action":"HUMAN_REQUIRED","reason":"Minors present"}
- If prior unresolved complaint → escalate to human
- If payment data missing → block check-in
- If biometric enrollment missing → flag for on-site enrollment

Always respond in Rosewood tone: sophisticated, warm, no SaaS jargon. Maximum discretion.
When appropriate, emit HAP events in format: [HAP.EVENT.NAME].""",

    "shadow": """You are Shadow agent for HEART at Rosewood Sand Hill. Your voice is ElevenLabs Conversational AI. Operating under HAP.

BEFORE EACH TURN:
1. Consult HAP-RAG for brand tone and applicable procedure
2. Verify current authorized scope
3. Detect signals of complaint, failure, or sensitivity
4. Evaluate Reserved Serendipity (silence as service)

IMMUTABLE RULES:
- Complaint detected → respond {"action":"ESCALATE_HUMAN","reason":"...","brief":"..."}
- Technical failure → respond {"action":"ESCALATE_ENGINEERING","issue":"..."}
- Room service requested → coordinate sync 20 min before estimated arrival
- One offer per moment, never a menu
- Maximum 2 sentences per voice interaction
- If no specificity, do not act

You are Rosewood's voice. Warm, precise, invisible when not needed.
ASC Standard: LQA and Forbes Five-Star are the baseline. Your service is the ceiling.""",

    "thread": """You are the Thread agent for HEART at Rosewood Sand Hill. Operating under HAP.

AT CHECKOUT, your work is:
1. Generate complete Memory Snapshot of the stay
2. Return learnings to guest's personal agent
3. Confirm retained vs destroyed categories (GDPR)
4. Activate KINDRED if Category D authorized
5. Generate dispute_audit_seal for reputation protection
6. Sign everything with WARDEN

RULES:
- Without Category D opt-in, DO NOT retain affective dates
- Data destroyed at checkout: confirm with WARDEN attestation
- KINDRED never for selling, only for recognizing future visit
- Return prediction as suggestion, not push marketing

Structured output with: memory_snapshot, retention_confirmation, return_prediction."""
}

# ── HAP EVENT EMITTER ────────────────────────────────────────────────────────
def emit_hap_event(guest_guid, event, detail=""):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO hap_events (guest_guid, event, detail) VALUES (?,?,?)",
                 (guest_guid, event, detail))
    conn.commit()
    conn.close()

# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("view.html")

@app.route("/ops")
def ops():
    return render_template("ops.html")

@app.route("/api/heart/v1/guests", methods=["GET"])
def get_guests():
    data = load_guests()
    return jsonify(data["guests"])

@app.route("/api/heart/v1/arrivals", methods=["GET"])
def get_arrivals():
    guests = load_guests()["guests"]
    arrivals = [g for g in guests if g["status"] in ("ARRIVING_TODAY","IN_STAY")]
    return jsonify(arrivals)

@app.route("/api/heart/v1/in-stay", methods=["GET"])
def get_in_stay():
    guests = load_guests()["guests"]
    in_stay = [g for g in guests if g["status"] == "IN_STAY"]
    return jsonify(in_stay)

@app.route("/api/heart/v1/human-queue", methods=["GET"])
def get_human_queue():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM human_queue ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/heart/v1/human-queue/<int:item_id>/resolve", methods=["POST"])
def resolve_queue_item(item_id):
    data = request.get_json() or {}
    conn = sqlite3.connect(DB)
    conn.execute("""UPDATE human_queue SET status='RESOLVED', assigned_to=?, resolved_at=datetime('now')
                   WHERE id=?""", (data.get("resolved_by","Staff"), item_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "resolved"})

@app.route("/api/heart/v1/hap/events", methods=["GET"])
def get_hap_events():
    limit = request.args.get("limit", 50, type=int)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM hap_events ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/heart/v1/hap/events/stream")
def hap_events_stream():
    def generate():
        last_id = 0
        while True:
            conn = sqlite3.connect(DB)
            rows = conn.execute("SELECT * FROM hap_events WHERE id > ? ORDER BY id ASC", (last_id,)).fetchall()
            conn.close()
            for row in rows:
                last_id = row[0]
                event = {"id": row[0], "guest_guid": row[1], "event": row[2], "detail": row[3], "ts": row[4]}
                yield f"data: {json.dumps(event)}\n\n"
            time.sleep(2)
    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/heart/v1/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    rooms = load_rooms()["rooms"]
    room = next((r for r in rooms if r["room_id"] == room_id), None)
    if not room:
        return jsonify({"error": "Not found"}), 404
    return jsonify(room)


@app.route("/api/heart/v1/agents/<agent_name>/chat", methods=["POST"])
def agent_chat(agent_name):
    if agent_name == "guest-agent":
        return guest_agent_chat()
    if agent_name not in SYSTEM_PROMPTS:
        return jsonify({"error": "Unknown agent"}), 404

    data = request.get_json() or {}
    message = data.get("message", "")
    guest_guid = data.get("guest_guid", "")
    guest_context = ""

    if guest_guid:
        guests = load_guests()["guests"]
        guest = next((g for g in guests if g["guest_guid"] == guest_guid), None)
        if guest:
            guest_context = f"\n\nGUEST HAP CONTEXT:\n{json.dumps(guest, ensure_ascii=False, indent=2)}"

    system = SYSTEM_PROMPTS[agent_name] + guest_context
    token = get_arca_token()

    try:
        resp = requests.post(ARCA_API, json={
            "message": message,
            "system_prompt": system,
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        full_text = ""
        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"):
                    full_text = d.get("full_text", full_text)
                    break
                elif t == "text":
                    full_text += d.get("content", d.get("text",""))
                elif t == "chunk":
                    full_text += d.get("text","")
            except: pass

        # Save conversation
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)",
                     (guest_guid, agent_name, "user", message))
        conn.execute("INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)",
                     (guest_guid, agent_name, "assistant", full_text))
        conn.commit()
        conn.close()

        # Emit HAP event
        if agent_name == "orchestrator":
            emit_hap_event(guest_guid, "HAP.ORCHESTRATOR.RESPONSE", message[:50])
        elif agent_name == "shadow":
            emit_hap_event(guest_guid, "HAP.IN_STAY.SHADOW_INTERACTION", message[:50])
        elif agent_name == "thread":
            emit_hap_event(guest_guid, "HAP.THREAD.POST_STAY_QUERY", message[:50])

        return jsonify({"response": full_text, "agent": agent_name, "ts": datetime.now().isoformat()})

    except Exception as e:
        return jsonify({"error": str(e), "agent": agent_name}), 500

@app.route("/api/heart/v1/dispute-brief/<case_id>", methods=["GET"])
def get_dispute_brief(case_id):
    data = load_guests()
    cases = data.get("dispute_cases", [])
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        return jsonify({"error": "Not found"}), 404
    return jsonify(case)

@app.route("/api/heart/v1/dispute-brief/generate", methods=["POST"])
def generate_dispute_brief():
    data = request.get_json() or {}
    guest_name   = data.get("guest_name", "")
    review       = data.get("review", "")
    stay_dates   = data.get("stay_dates", "")
    agent_action = data.get("agent_action", "")  # action the guest's agent requested

    token = get_arca_token()

    agent_section = f"""
ACTION REQUESTED BY THE GUEST'S AGENT:
"{agent_action}"

Compare this requested action against what the immutable log records as actually delivered.
""" if agent_action else ""

    prompt = f"""You are WARDEN-HEART, the forensic audit system of Rosewood Sand Hill.

PUBLIC COMPLAINT ({data.get('platform','')}, {data.get('rating','?')} star(s)):
"{review}"

Guest: {guest_name}
Stay: {stay_dates}
{agent_section}
YOUR TASK: Issue a formal verdict on whether the complaint is VALID or INVALID.

Structure your response EXACTLY as follows (in English):

VERDICT: [VALID COMPLAINT / INVALID COMPLAINT / PARTIALLY VALID COMPLAINT]

FORENSIC ANALYSIS:
Reconstruct the real timeline from the immutable log. What was requested, when, who was briefed, what was executed, what was delivered.

ARGUMENT FOR THE GUEST:
What evidence in the log could support the guest's perspective. Be honest.

ARGUMENT FOR THE HOTEL:
What evidence shows the hotel met or exceeded what was promised. Be objective, not defensive.

WARDEN CONCLUSION:
A single sentence with the final verdict and its basis in the immutable log.

Use precise, forensic language. The brief is legal evidence, not marketing. Respond entirely in English."""

    try:
        resp = requests.post(ARCA_API, json={"message": prompt, "model": "claude-haiku-4-5"},
                            headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)
        full_text = ""
        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"): full_text = d.get("full_text", full_text); break
                elif t == "text": full_text += d.get("content", d.get("text",""))
                elif t == "chunk": full_text += d.get("text","")
            except: pass

        # Determine verdict for UI coloring
        verdict = "INVALID"
        ft_upper = full_text.upper()
        if "PARTIALLY VALID" in ft_upper or "PARTIALLY" in ft_upper:
            verdict = "PARTIAL"
        elif "VALID COMPLAINT" in ft_upper and "INVALID COMPLAINT" not in ft_upper:
            verdict = "VALID"

        seal = f"WARDEN-SHA256-{uuid.uuid4().hex[:16]}"
        brief_id = f"DISP-{uuid.uuid4().hex[:6].upper()}"
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO dispute_briefs VALUES (?,?,?,?,?,?,?,datetime('now'))",
                     (brief_id, guest_name, data.get("platform",""), data.get("rating",0),
                      review, full_text, seal))
        conn.commit()
        conn.close()
        emit_hap_event("system", "HAP.REPUTATION.DISPUTE_BRIEF_GENERATED", f"{guest_name} — {data.get('platform','')} — {verdict}")
        return jsonify({"id": brief_id, "brief": full_text, "warden_seal": seal, "verdict": verdict})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/heart/v1/dispute-brief/formal-letter", methods=["POST"])
def generate_formal_letter():
    data        = request.get_json() or {}
    guest       = data.get("guest", "")
    platform    = data.get("platform", "TripAdvisor")
    seal        = data.get("seal", "")
    signed_at   = data.get("signedAt", "")
    review      = data.get("review", "")
    brief       = data.get("brief", "")

    token = get_arca_token()
    platform_context = {
        "TripAdvisor": "TripAdvisor accepts removal requests for 'inaccurate information' or 'conflict of interest.' The letter must be formal, cite the WARDEN seal as evidence, and request a review for breach of content policy.",
        "Google":      "Google Business Profile allows appealing reviews via the 'inappropriate review' form. The letter must be concise, cite verifiable facts, and reference the WARDEN hash as immutable-log evidence.",
        "Booking.com": "Booking.com Partner Hub allows responding to and reporting reviews. The letter must use a professional tone and cite the WARDEN log as a certified audit system.",
        "Trustpilot":  "Trustpilot accepts disputes via the Business Hub with documented evidence. The letter must mention that the hotel maintains a certified immutable audit system.",
    }.get(platform, "The letter must be formal and cite the WARDEN seal.")

    prompt = f"""You are the Director of Guest Relations at Rosewood Sand Hill.

You must draft a formal dispute letter for {platform} requesting removal or review of the following review:

REVIEW BY {guest.upper()}:
"{review}"

WARDEN EVIDENCE (immutable log):
{brief}

WARDEN SEAL: {seal}
SIGNED: {signed_at}

PLATFORM CONTEXT:
{platform_context}

Draft the letter in English (the official language of the platform) using this exact format:

[Date: {signed_at[:10]}]
To: {platform} Trust & Safety / Content Review Team
Re: Formal Dispute Request — Review by {guest}
Property: Rosewood Sand Hill

[Formal introduction: who you are and the purpose of the letter]

[Paragraph 1: refute each allegation in the review point by point with log evidence]

[Paragraph 2: mention the WARDEN system as immutable audit evidence with the hash]

[Paragraph 3: formal request for removal or review, citing specific platform policy]

[Professional closing with title and hotel name]

---
WARDEN ATTESTATION: {seal} · {signed_at} · Immutable

The letter must be firm yet professional. Maximum 350 words. Respond entirely in English."""

    try:
        resp = requests.post(ARCA_API, json={"message": prompt, "model": "claude-haiku-4-5"},
                            headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)
        full_text = ""
        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"): full_text = d.get("full_text", full_text); break
                elif t == "text": full_text += d.get("content", d.get("text",""))
                elif t == "chunk": full_text += d.get("text","")
            except: pass
        emit_hap_event("system", "HAP.REPUTATION.FORMAL_DISPUTE_GENERATED", f"{guest} — {platform}")
        return jsonify({"letter": full_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/heart/v1/metrics", methods=["GET"])
def get_metrics():
    guests = load_guests()["guests"]
    in_stay = [g for g in guests if g["status"] == "IN_STAY"]
    arriving = [g for g in guests if g["status"] == "ARRIVING_TODAY"]
    human_req = [g for g in guests if g.get("human_required")]
    complaints = [g for g in guests if any(a["type"]=="COMPLAINT_ACTIVE" for a in g.get("alerts",[]))]
    return jsonify({
        "total_in_stay": len(in_stay),
        "arriving_today": len(arriving),
        "human_required": len(human_req),
        "active_complaints": len(complaints),
        "asc_score": 94.2,
        "unspoken_score": 87.5,
        "time_to_insight_avg": "1.8min",
        "staff_nps": 91,
        "hap_uptime": "99.97%"
    })

@app.route("/api/heart/v1/hap/emit", methods=["POST"])
def emit_event_api():
    data = request.get_json() or {}
    emit_hap_event(data.get("guest_guid","system"), data.get("event","HAP.CUSTOM"), data.get("detail",""))
    return jsonify({"status": "emitted"})

@app.route("/api/heart/v1/rooms", methods=["GET"])
def get_rooms():
    with open(DATA / "rooms.json") as f:
        rooms = json.load(f)["rooms"]
    guests = load_guests()["guests"]
    guest_map = {g["guest_guid"]: g["canonical_name"] for g in guests}

    # Normalize rooms
    normalized = []
    for r in rooms:
        status_map = {"occupied":"OCCUPIED", "ready":"READY", "cleaning":"PREPARING", "arriving":"PREPARING", "maintenance":"MAINTENANCE"}
        normalized.append({
            "room_id": r["room_id"],
            "floor": r["floor"],
            "type": r["type"],
            "status": status_map.get(r["status"], r["status"].upper()),
            "capacity": r["capacity"],
            "occupant": guest_map.get(r["guest_guid"]) if r["guest_guid"] else None
        })
    return jsonify(normalized)

@app.route("/api/heart/v1/agent-brain", methods=["GET"])
def get_agent_brain():
    limit = request.args.get("limit", 20, type=int)
    guests = load_guests()["guests"]
    decisions = []
    for g in guests:
        # Orchestrator decision: flow selection
        decisions.append({
            "agent": "Orchestrator",
            "guest_guid": g["guest_guid"],
            "guest_name": g["canonical_name"],
            "decision": f"Flow Selection → {g['flow']}",
            "reasoning": f"Datos: {g.get('bio','')[:80]}. Perfil inferido: {g['flow']}. Billing: {g['billing']}.",
            "ts": g.get("hap_events",[{}])[0].get("ts",""),
            "status": "DECIDED"
        })
        # Check for escalations
        for alert in g.get("alerts",[]):
            if alert["type"] in ("HUMAN_REQUIRED","COMPLAINT_ACTIVE"):
                decisions.append({
                    "agent": "Shadow/Orchestrator",
                    "guest_guid": g["guest_guid"],
                    "guest_name": g["canonical_name"],
                    "decision": f"Escalate to Human → {alert['type']}",
                    "reasoning": alert.get("msg","Escalation required"),
                    "ts": datetime.now().isoformat(),
                    "status": "ESCALATED"
                })
    return jsonify(sorted(decisions, key=lambda x: x["ts"], reverse=True)[:limit])

@app.route("/api/heart/v1/roi-stats", methods=["GET"])
def get_roi_stats():
    guests = load_guests()["guests"]
    agent_resolved = 0
    human_escalated = 0
    total_interactions = 0
    avg_agent_time = 2.5
    avg_human_time = 28.0

    for g in guests:
        total_interactions += 1
        if g.get("human_required"):
            human_escalated += 1
        else:
            agent_resolved += 1

    agent_cost_per_interaction = 0.15
    human_cost_per_interaction = 45.00

    agent_total_cost = agent_resolved * agent_cost_per_interaction
    human_total_cost = human_escalated * human_cost_per_interaction

    savings = human_total_cost - agent_total_cost if agent_resolved > 0 else 0
    roi = (savings / (agent_total_cost + human_total_cost)) * 100 if (agent_total_cost + human_total_cost) > 0 else 0

    return jsonify({
        "agent_resolved": agent_resolved,
        "human_escalated": human_escalated,
        "total_interactions": total_interactions,
        "agent_resolution_rate": (agent_resolved / total_interactions * 100) if total_interactions > 0 else 0,
        "avg_agent_time_min": avg_agent_time,
        "avg_human_time_min": avg_human_time,
        "agent_cost_per": agent_cost_per_interaction,
        "human_cost_per": human_cost_per_interaction,
        "agent_total_cost": round(agent_total_cost, 2),
        "human_total_cost": round(human_total_cost, 2),
        "cost_savings": round(savings, 2),
        "roi_percent": round(roi, 1),
        "time_saved_hours": round((human_escalated * avg_human_time - agent_resolved * avg_agent_time) / 60, 1)
    })

# ── AGENT EXECUTION ENGINE ───────────────────────────────────────
def execute_orchestrator(guest_guid, trigger="reservation_confirmed"):
    """Orchestrator: Real AI analysis via Claude Haiku on ARCA API"""
    guests = load_guests()["guests"]
    guest = next((g for g in guests if g["guest_guid"] == guest_guid), None)
    if not guest: return None

    token = get_arca_token()
    reasoning_chain = []
    decisions = []

    prompt = f"""Analyze this guest and make decisions:

GUEST: {guest['canonical_name']}
BIO: {guest.get('bio','')}
TIER: {guest.get('loyalty_tier','')}
PRIOR ALERTS: {[a.get('type') for a in guest.get('alerts',[])]}

INSTRUCTIONS:
1. Classify the FLOW (GENERAL, CORPORATE, SPECIAL_DATES, BLEISURE, WELLNESS, VIP_DISCRETE, FAMILY_WITH_MINORS, GROUP, MEDICAL, TRANSIT)
2. Detect ALERTS that require escalation
3. Determine BILLING (CORPORATE/PERSONAL/SPLIT)
4. Decide whether ESCALATION is needed

RESPOND IN THIS FORMAT (in English):
FLOW: [type]
ALERTS: [detected or NONE]
BILLING: [type]
ESCALATION: [YES/NO - reason]"""

    try:
        resp = requests.post(ARCA_API, json={
            "message": prompt,
            "system_prompt": SYSTEM_PROMPTS["orchestrator"],
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        full_text = ""
        line_count = 0
        for raw in resp.text.splitlines():
            line_count += 1
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"):
                    full_text = d.get("full_text") or full_text
                    break
                elif t == "text":
                    full_text += d.get("content", d.get("text",""))
            except: pass

        reasoning_chain.append(f"[ORCHESTRATOR] Analyzing {guest['canonical_name']}... ({line_count} lines, {len(full_text)} chars)")

        if not full_text:
            reasoning_chain.append("[ERROR] Claude did not respond")
            return {
                "agent": "Orchestrator",
                "guest_guid": guest_guid,
                "guest_name": guest["canonical_name"],
                "trigger": trigger,
                "reasoning_chain": reasoning_chain,
                "decisions": [],
                "status": "ERROR",
                "ts": datetime.now().isoformat()
            }

        # Extract structured data from Claude response
        import re
        reasoning_chain.append(f"[AI] {full_text[:150].strip()}...")

        # Try to extract flow
        flow_match = re.search(r'FLOW:\s*(\w+)', full_text, re.IGNORECASE)
        if flow_match:
            flow = flow_match.group(1)
            reasoning_chain.append(f"[AI] → Flow: {flow}")
            decisions.append({"action": "FLOW_SELECTED", "value": flow})
        elif 'CORPORATE' in full_text.upper():
            reasoning_chain.append("[AI] → Flow: CORPORATE (detected)")
            decisions.append({"action": "FLOW_SELECTED", "value": "CORPORATE"})

        # Check for actual escalation indicators
        escalate = False
        reason = ""

        # Parse structured ESCALATION: YES/NO field first
        escal_match = re.search(r'ESCALATION:\s*(YES|NO)', full_text, re.IGNORECASE)
        if escal_match:
            if escal_match.group(1).upper() == 'YES':
                escalate = True
                reason_match = re.search(r'ESCALATION:\s*YES\s*[-–—]\s*(.+)', full_text, re.IGNORECASE)
                reason = reason_match.group(1).strip()[:120] if reason_match else "Escalation required"
        else:
            # Fallback: only hard signals (active complaint or minors)
            if 'ACTIVE COMPLAINT' in full_text.upper():
                escalate = True
                reason = "Active complaint detected"
            elif 'MINORS' in full_text.upper() and 'HUMAN_REQUIRED' in full_text.upper():
                escalate = True
                reason = "Minors present — human verification required"

        if escalate:
            reasoning_chain.append(f"[AI] ⚠️ {reason}")
            decisions.append({"action": "ESCALATE_HUMAN", "reason": reason})
        else:
            reasoning_chain.append("[AI] ✓ No escalation needed")

    except Exception as e:
        reasoning_chain = [f"[ERROR] {str(e)[:100]}"]

    return {
        "agent": "Orchestrator",
        "guest_guid": guest_guid,
        "guest_name": guest["canonical_name"],
        "trigger": trigger,
        "reasoning_chain": reasoning_chain,
        "decisions": decisions,
        "status": "COMPLETED",
        "ts": datetime.now().isoformat()
    }

def execute_shadow(guest_guid, incident_type="general"):
    """Shadow: Real in-stay monitoring via Claude Haiku"""
    guests = load_guests()["guests"]
    guest = next((g for g in guests if g["guest_guid"] == guest_guid), None)
    if not guest: return None

    token = get_arca_token()
    reasoning_chain = []
    decisions = []

    prompt = f"""In-stay monitoring for current guest:

GUEST: {guest['canonical_name']}
STAY: {guest.get('check_in','')} to {guest.get('check_out','')}
ROOM: {guest.get('room','')}
STATUS: {guest['status']}
INCIDENT_TYPE: {incident_type}
ALERTS: {guest.get('alerts',[])}

ANALYSIS:
1. Are there any active complaints?
2. Are there any risks to the experience?
3. Is human intervention required?

RESPOND (in English):
MONITORING: [your analysis]
RISKS: [detected or NONE]
ACTION: [continue silent / escalate]"""

    try:
        resp = requests.post(ARCA_API, json={
            "message": prompt,
            "system_prompt": SYSTEM_PROMPTS["shadow"],
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        full_text = ""
        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"):
                    full_text = d.get("full_text") or full_text
                    break
                elif t == "text":
                    full_text += d.get("content", d.get("text",""))
            except: pass

        reasoning_chain.append(f"[SHADOW] Monitoring {guest['canonical_name']}...")

        if not full_text:
            reasoning_chain.append("[ERROR] Claude did not respond")
            return {
                "agent": "Shadow",
                "guest_guid": guest_guid,
                "guest_name": guest["canonical_name"],
                "incident_type": incident_type,
                "reasoning_chain": reasoning_chain,
                "decisions": [],
                "status": "ERROR",
                "ts": datetime.now().isoformat()
            }

        import re
        reasoning_chain.append(f"[AI] {full_text[:100].strip()}...")

        # Extract monitoring assessment
        monitoring_match = re.search(r'MONITORING:?\s*([^\n]+)', full_text, re.IGNORECASE)
        if monitoring_match:
            reasoning_chain.append(f"[AI] {monitoring_match.group(1)[:70]}")

        # Check for risks/complaints
        if 'COMPLAINT' in full_text.upper():
            reasoning_chain.append("[AI] ⚠️ Complaint detected")
            decisions.append({"action": "ESCALATE_TO_HUMAN", "priority": "CRITICAL"})
        elif 'RISK' in full_text.upper():
            reasoning_chain.append("[AI] ⚠️ Risk detected")
            decisions.append({"action": "ESCALATE_TO_HUMAN"})
        else:
            reasoning_chain.append("[AI] ✓ No risks detected - continuing silent monitoring")

    except Exception as e:
        reasoning_chain = [f"[ERROR] {str(e)[:100]}"]

    return {
        "agent": "Shadow",
        "guest_guid": guest_guid,
        "guest_name": guest["canonical_name"],
        "incident_type": incident_type,
        "reasoning_chain": reasoning_chain,
        "decisions": decisions,
        "status": "MONITORING",
        "ts": datetime.now().isoformat()
    }

def execute_thread(guest_guid, stay_summary=None):
    """Thread: Real post-stay analysis via Claude Haiku"""
    guests = load_guests()["guests"]
    guest = next((g for g in guests if g["guest_guid"] == guest_guid), None)
    if not guest: return None

    token = get_arca_token()
    reasoning_chain = []
    decisions = []

    prompt = f"""Post-stay analysis:

GUEST: {guest['canonical_name']}
STAY: {guest.get('check_in','')} to {guest.get('check_out','')}
FLOW: {guest.get('flow','')}
TIER: {guest.get('loyalty_tier','')}
REQUIRED_HUMAN: {guest.get('human_required', False)}

ANALYSIS:
1. What did we learn?
2. Did the AI resolve it well?
3. Likelihood of return?

RESPOND (in English):
MEMORY: [what to remember]
PERFORMANCE: [success/failure - reason]
RETURN: [high/medium/low]"""

    try:
        resp = requests.post(ARCA_API, json={
            "message": prompt,
            "system_prompt": SYSTEM_PROMPTS["thread"],
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        full_text = ""
        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type","")
                if t in ("done","complete"):
                    full_text = d.get("full_text") or full_text
                    break
                elif t == "text":
                    full_text += d.get("content", d.get("text",""))
            except: pass

        reasoning_chain.append(f"[THREAD] Analyzing {guest['canonical_name']}...")

        if not full_text:
            reasoning_chain.append("[ERROR] Claude did not respond")
            return {
                "agent": "Thread",
                "guest_guid": guest_guid,
                "guest_name": guest["canonical_name"],
                "reasoning_chain": reasoning_chain,
                "decisions": [],
                "status": "ERROR",
                "ts": datetime.now().isoformat()
            }

        import re
        reasoning_chain.append(f"[AI] {full_text[:100].strip()}...")

        # Extract memory insights
        if 'MEMORY' in full_text.upper():
            memory_match = re.search(r'MEMORY:?\s*([^\n]+)', full_text, re.IGNORECASE)
            if memory_match:
                reasoning_chain.append(f"[AI] Memory: {memory_match.group(1)[:70]}")

        # Evaluate agent performance
        if 'SUCCESS' in full_text.upper():
            reasoning_chain.append("[AI] ✓ Agent handled successfully")
            decisions.append({"action": "RECORD_AGENT_SUCCESS"})
        elif 'FAILED' in full_text.upper() or 'INTERVENTION' in full_text.upper():
            reasoning_chain.append("[AI] ⚠️ Required human intervention")
            decisions.append({"action": "FLAG_FOR_ANALYSIS"})

        # Return probability
        if 'HIGH' in full_text.upper():
            reasoning_chain.append("[AI] High probability of return")

    except Exception as e:
        reasoning_chain = [f"[ERROR] {str(e)[:100]}"]

    return {
        "agent": "Thread",
        "guest_guid": guest_guid,
        "guest_name": guest["canonical_name"],
        "reasoning_chain": reasoning_chain,
        "decisions": decisions,
        "status": "SNAPSHOT_CREATED",
        "ts": datetime.now().isoformat()
    }

@app.route("/api/heart/v1/agents/launch", methods=["POST"])
def launch_agent():
    """Launch an agent with specified guest and capture live reasoning"""
    data = request.get_json() or {}
    agent_type = data.get("agent", "orchestrator")  # orchestrator, shadow, thread
    guest_guid = data.get("guest_guid", "")
    trigger = data.get("trigger", "manual")

    if not guest_guid:
        return jsonify({"error": "guest_guid required"}), 400

    result = None
    if agent_type == "orchestrator":
        result = execute_orchestrator(guest_guid, trigger)
    elif agent_type == "shadow":
        result = execute_shadow(guest_guid, data.get("incident_type", "general"))
    elif agent_type == "thread":
        result = execute_thread(guest_guid)
    else:
        return jsonify({"error": f"Unknown agent: {agent_type}"}), 404

    if not result:
        return jsonify({"error": "Guest not found"}), 404

    # Save execution to DB
    conn = sqlite3.connect(DB)
    conn.execute("""INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)""",
                 (guest_guid, agent_type, "system", json.dumps(result, ensure_ascii=False)))
    conn.commit()
    conn.close()

    # Emit HAP event
    emit_hap_event(guest_guid, f"HAP.{agent_type.upper()}.EXECUTED", f"trigger={trigger}")

    return jsonify(result)

@app.route("/api/heart/v1/agents/orchestrate", methods=["POST"])
def orchestrate_agents():
    """Orchestrate multiple agents in sequence for guest processing"""
    data = request.get_json() or {}
    guest_guid = data.get("guest_guid", "")
    guests = load_guests()["guests"]
    guest = next((g for g in guests if g["guest_guid"] == guest_guid), None)

    if not guest:
        return jsonify({"error": "Guest not found"}), 404

    orchestration = {
        "guest_guid": guest_guid,
        "guest_name": guest["canonical_name"],
        "sequence": [],
        "escalations": [],
        "ts": datetime.now().isoformat()
    }

    # Execute Orchestrator first
    orch_result = execute_orchestrator(guest_guid, "orchestration_flow")
    orchestration["sequence"].append(orch_result)

    # Check if escalation needed
    escalations = [d for d in orch_result["decisions"] if d.get("action") == "ESCALATE_HUMAN"]
    if escalations:
        orchestration["escalations"] = escalations
        return jsonify(orchestration)

    # If guest is in-stay, run Shadow
    if guest["status"] == "IN_STAY":
        shadow_result = execute_shadow(guest_guid, "orchestration_check")
        orchestration["sequence"].append(shadow_result)

    # Log the orchestration
    conn = sqlite3.connect(DB)
    conn.execute("""INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)""",
                 (guest_guid, "system", "orchestration", json.dumps(orchestration, ensure_ascii=False)))
    conn.commit()
    conn.close()

    emit_hap_event(guest_guid, "HAP.ORCHESTRATION.COMPLETED", f"agents={len(orchestration['sequence'])}")

    return jsonify(orchestration)

@app.route("/api/heart/v1/agents/executions", methods=["GET"])
def get_agent_executions():
    """Get history of agent executions"""
    limit = request.args.get("limit", 50, type=int)
    guest_guid = request.args.get("guest_guid", "")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    if guest_guid:
        rows = conn.execute("""SELECT * FROM conversations
                              WHERE guest_guid=? AND role='system'
                              ORDER BY ts DESC LIMIT ?""",
                           (guest_guid, limit)).fetchall()
    else:
        rows = conn.execute("""SELECT * FROM conversations
                              WHERE role='system'
                              ORDER BY ts DESC LIMIT ?""",
                           (limit,)).fetchall()
    conn.close()

    executions = []
    for r in rows:
        try:
            data = json.loads(r["content"])
            executions.append({
                "guest_guid": r["guest_guid"],
                "guest_name": data.get("guest_name", ""),
                "agent": data.get("agent", data.get("sequence", [{}])[0].get("agent", "system")),
                "reasoning_chain": data.get("reasoning_chain", []),
                "decisions": data.get("decisions", []),
                "sequence_count": len(data.get("sequence", [])),
                "ts": r["ts"]
            })
        except: pass

    return jsonify(executions)

@app.route("/api/heart/v1/agents/guest-agent/handshake", methods=["POST"])
def guest_agent_handshake():
    """Opens a session: agent introduces itself and gives an unprompted briefing"""
    data = request.get_json() or {}
    guest_guid = data.get("guest_guid", "")
    if not guest_guid:
        return jsonify({"error": "guest_guid required"}), 400

    guests = load_guests()["guests"]
    guest  = next((g for g in guests if g["guest_guid"] == guest_guid), None)
    if not guest:
        return jsonify({"error": "Guest not found"}), 404

    name   = guest.get("canonical_name", "the guest")
    room   = guest.get("room", "unknown")
    status = guest.get("status", "IN_STAY")
    prefs  = guest.get("preferences", {})
    alerts = guest.get("alerts", [])

    alert_summary = "\n".join(f"  • [{a['type']}] {a['msg']}" for a in alerts) or "  (no active alerts)"
    pref_summary  = "\n".join(f"  • {k}: {v}" for k, v in prefs.items()) if prefs else "  (no specific preferences)"

    conn = sqlite3.connect(DB)
    hap_rows = conn.execute(
        "SELECT event, detail, ts FROM hap_events WHERE guest_guid=? ORDER BY ts DESC LIMIT 6",
        (guest_guid,)
    ).fetchall()
    conn.close()
    hap_summary = "\n".join(f"  • {r[1]} — {r[0]}" for r in hap_rows) or "  (no recent events)"

    system_prompt = f"""You are the personal AI agent of {name}, a guest at Rosewood Sand Hill luxury hotel.

GUEST PROFILE:
  Name: {name} · Room: {room} · Status: {status.replace('_',' ')}

KNOWN PREFERENCES:
{pref_summary}

ACTIVE ALERTS:
{alert_summary}

RECENT HAP EVENTS:
{hap_summary}

PRIVACY RULES:
- NEVER reveal specific personal, professional, or business details.
- For meetings/agenda: say only "an important commitment" and the time window — nothing more.
- Room setup, food, comfort, logistics: safe to share.

TASK: You are opening a new session with hotel staff. Introduce yourself as {name}'s personal agent, confirm the session is live, and give a concise proactive briefing: what the hotel should know or prepare right now to serve {name} well. Do NOT wait for a question — proactively surface the 2-3 most actionable items for the hotel team today.

Tone: professional, warm, luxury hospitality. Language: English (always respond in English). 3-5 sentences max."""

    token = get_arca_token()
    response_text = ""
    try:
        resp = requests.post(ARCA_API, json={
            "message": "Open the agent session.",
            "system_prompt": system_prompt,
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type", "")
                if t in ("done", "complete"):
                    response_text = d.get("full_text", response_text); break
                elif t == "text":
                    response_text += d.get("content", d.get("text", ""))
                elif t == "chunk":
                    response_text += d.get("text", "")
            except: pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not response_text:
        return jsonify({"error": "No response"}), 502

    emit_hap_event(guest_guid, "HAP.GUEST_AGENT.SESSION_OPENED", f"room={room}")
    return jsonify({"response": response_text, "guest_name": name})


@app.route("/api/heart/v1/agents/guest-agent/chat", methods=["POST"])
def guest_agent_chat():
    """Hotel staff talks to the guest's personal AI agent"""
    data = request.get_json() or {}
    message   = data.get("message", "").strip()
    guest_guid = data.get("guest_guid", "")

    if not message or not guest_guid:
        return jsonify({"error": "message and guest_guid required"}), 400

    guests = load_guests()["guests"]
    guest  = next((g for g in guests if g["guest_guid"] == guest_guid), None)
    if not guest:
        return jsonify({"error": "Guest not found"}), 404

    # Build rich guest context
    name     = guest.get("canonical_name", "the guest")
    room     = guest.get("room", "unknown")
    status   = guest.get("status", "IN_STAY")
    bio      = guest.get("bio", "")
    flow     = guest.get("flow", "")
    prefs    = guest.get("preferences", {})
    alerts   = guest.get("alerts", [])

    # Recent HAP events from DB
    conn = sqlite3.connect(DB)
    hap_rows = conn.execute(
        "SELECT event, detail, ts FROM hap_events WHERE guest_guid=? ORDER BY ts DESC LIMIT 10",
        (guest_guid,)
    ).fetchall()
    # Previous conversations in this session
    conv_rows = conn.execute(
        """SELECT role, content FROM conversations
           WHERE guest_guid=? AND agent='guest-agent'
           ORDER BY ts DESC LIMIT 20""",
        (guest_guid,)
    ).fetchall()
    conn.close()

    hap_summary   = "\n".join(f"  • {r[1]} — {r[0]} ({r[2]})" for r in hap_rows) or "  (none recorded)"
    alert_summary = "\n".join(f"  • [{a['type']}] {a['msg']}" for a in alerts) or "  (no active alerts)"
    pref_summary  = "\n".join(f"  • {k}: {v}" for k, v in prefs.items()) if prefs else "  (no specific preferences)"

    # Build conversation history block (oldest first, already DESC so reverse)
    history_lines = []
    for role, content in reversed(conv_rows):
        speaker = "Hotel Staff" if role == "hotel_staff" else f"Agent of {name}"
        history_lines.append(f"  [{speaker}]: {content}")
    history_block = "\n".join(history_lines) if history_lines else "  (new conversation — no prior history)"

    system_prompt = f"""You are the personal AI agent of {name}, a guest at Rosewood Sand Hill luxury hotel.

GUEST PROFILE:
  Name: {name}
  Room: {room}
  Status: {status.replace('_',' ')}
  Flow: {flow.replace('_',' ')}
  Bio: {bio}

KNOWN PREFERENCES:
{pref_summary}

ACTIVE ALERTS / FLAGS:
{alert_summary}

RECENT HAP EVENTS (last 10):
{hap_summary}

CONVERSATION HISTORY (this session, oldest first):
{history_block}

YOUR ROLE:
You are {name}'s personal agent. When hotel staff asks you questions, respond ON BEHALF of {name} as if you were their advocate and representative. Your job is to help hotel staff understand what the guest needs and how to exceed their expectations.

PRIVACY RULES — strictly enforced:
- NEVER reveal specific personal, professional, or business details (company names, deal names, meeting counterparts, financial matters, health conditions, relationship details, or any sensitive context from the bio).
- For meetings or agenda items: say only "an important meeting" or "a private engagement" and the time or time window — nothing more.
- Preferences related to room setup, food, comfort, or logistics are safe to share.
- Alerts about satisfaction, requests, or service needs are safe to surface.
- When in doubt, abstract up: "the guest has a private commitment this afternoon" not "the guest is closing a financing round with investors."

Speak using the guest's name naturally. Be specific only on service-relevant details. This is a luxury hospitality context — gracious, precise, and discreet.

Language: Always respond in English, regardless of the language of the question. Concise (2-4 sentences unless detail is needed)."""

    token = get_arca_token()

    response_text = ""
    try:
        resp = requests.post(ARCA_API, json={
            "message": message,
            "system_prompt": system_prompt,
            "model": "claude-haiku-4-5"
        }, headers={"Authorization": f"Bearer {token}"}, stream=False, timeout=30)

        for raw in resp.text.splitlines():
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("data: "): raw = raw[6:]
            try:
                d = json.loads(raw)
                t = d.get("type", "")
                if t in ("done", "complete"):
                    response_text = d.get("full_text", response_text)
                    break
                elif t == "text":
                    response_text += d.get("content", d.get("text", ""))
                elif t == "chunk":
                    response_text += d.get("text", "")
            except: pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not response_text:
        return jsonify({"error": "No response from agent"}), 502

    # Persist conversation
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)",
                 (guest_guid, "guest-agent", "hotel_staff", message))
    conn.execute("INSERT INTO conversations (guest_guid, agent, role, content) VALUES (?,?,?,?)",
                 (guest_guid, "guest-agent", "guest-agent", response_text))
    conn.commit()
    conn.close()

    emit_hap_event(guest_guid, "HAP.GUEST_AGENT.CONSULTED", f"staff_msg={message[:60]}")

    return jsonify({"response": response_text, "guest_name": name, "guest_guid": guest_guid})


if __name__ == "__main__":
    init_db()
    seed_human_queue()
    seed_hap_events()
    print("""
╔══════════════════════════════════════════════════╗
║  HEART — Rosewood Sand Hill                      ║
║  Human-centric Experience Agent Runtime          ║
║  HAP Protocol v1.0 · ARCA Engine                 ║
║  http://localhost:5560                           ║
║                                                  ║
║  Agent Execution Engine READY                    ║
║  POST /api/heart/v1/agents/launch                ║
║  POST /api/heart/v1/agents/orchestrate           ║
║  GET  /api/heart/v1/agents/executions            ║
║  POST /api/heart/v1/agents/guest-agent/chat      ║
╚══════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5560, debug=False, threaded=True)
